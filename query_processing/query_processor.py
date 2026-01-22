#!/usr/bin/env python3
"""
Query Processing Pipeline for Cross-Lingual Information Retrieval (CLIR)

Implements Module B requirements:
1. Language Detection - Identify if query is Bangla or English
2. Normalization - Lowercase, remove whitespace, optional stopword removal
3. Query Translation - Translate query to target language
4. Query Expansion - Add synonyms, morphological variants
5. Named-Entity Mapping - Map NEs across languages

Usage:
    processor = QueryProcessor()
    result = processor.process("coronavirus vaccine", target_lang="bn")
"""

import re
import csv
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

# Try to import translation libraries
try:
    from deep_translator import GoogleTranslator
    HAS_DEEP_TRANSLATOR = True
except ImportError:
    HAS_DEEP_TRANSLATOR = False

try:
    from googletrans import Translator as GoogletransTranslator
    HAS_GOOGLETRANS = True
except ImportError:
    HAS_GOOGLETRANS = False

TRANSLATOR_AVAILABLE = HAS_DEEP_TRANSLATOR or HAS_GOOGLETRANS
if not TRANSLATOR_AVAILABLE:
    print("Warning: No translation library installed. Translation will be disabled.")

# Try to import NLTK WordNet for English synonyms
try:
    from nltk.corpus import wordnet
    WORDNET_AVAILABLE = True
except ImportError:
    WORDNET_AVAILABLE = False
    print("Warning: NLTK WordNet not available. Using fallback English synonyms.")

# Try to import transformers for NER
try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    print("Warning: transformers not installed. Using fallback NE mapping.")


def load_bangla_synonyms_from_csv() -> Dict[str, List[str]]:
    """Load Bangla synonyms from the cleaned CSV file."""
    csv_path = Path(__file__).parent / "bangla_synonyms_cleaned.csv"
    synonyms_dict = {}

    if not csv_path.exists():
        return {}

    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                word = row['word'].strip()
                synonyms = [s.strip() for s in row['synonyms'].split(',') if s.strip()]
                if word and synonyms:
                    synonyms_dict[word] = synonyms
    except Exception as e:
        print(f"Warning: Failed to load Bangla synonyms from CSV: {e}")

    return synonyms_dict


# Load Bangla synonyms from CSV at module load time
BANGLA_SYNONYMS_CSV = load_bangla_synonyms_from_csv()


@dataclass
class ProcessedQuery:
    """Container for processed query results."""
    original: str
    detected_language: str
    normalized: str
    tokens: List[str]
    translated: Optional[str] = None
    translation_language: Optional[str] = None
    expanded_terms: List[str] = field(default_factory=list)
    named_entities: List[Tuple[str, str]] = field(default_factory=list)  # (entity, mapped_entity)
    processing_steps: List[str] = field(default_factory=list)


class QueryProcessor:
    """
    Complete query processing pipeline for CLIR.

    Features:
    - Language detection (Bangla vs English)
    - Text normalization (lowercase, whitespace, stopwords)
    - Query translation (EN <-> BN)
    - Query expansion with synonyms
    - Named entity mapping across languages
    """

    # Bangla Unicode range
    BANGLA_RANGE = (0x0980, 0x09FF)

    # English stopwords (common words to optionally remove)
    ENGLISH_STOPWORDS = {
        'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been',
        'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
        'could', 'should', 'may', 'might', 'must', 'shall', 'can', 'need',
        'it', 'its', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she',
        'we', 'they', 'what', 'which', 'who', 'whom', 'when', 'where', 'why', 'how'
    }

    # Bangla stopwords
    BANGLA_STOPWORDS = {
        'এবং', 'ও', 'কিন্তু', 'তবে', 'যে', 'যা', 'এই', 'সেই', 'তার', 'তাদের',
        'আমি', 'আমরা', 'তুমি', 'তোমরা', 'সে', 'তারা', 'এটি', 'এটা', 'ওটা',
        'কি', 'কে', 'কেন', 'কোথায়', 'কখন', 'কিভাবে', 'হয়', 'হচ্ছে', 'ছিল',
        'আছে', 'নেই', 'করে', 'করা', 'হবে', 'থেকে', 'জন্য', 'সাথে', 'মধ্যে'
    }

    # Fallback English synonyms dictionary (used if WordNet unavailable)
    ENGLISH_SYNONYMS_FALLBACK = {
        'coronavirus': ['covid', 'covid-19', 'corona', 'pandemic', 'virus'],
        'vaccine': ['vaccination', 'immunization', 'shot', 'jab'],
        'election': ['vote', 'voting', 'poll', 'ballot'],
        'government': ['administration', 'authority', 'regime', 'state'],
        'economy': ['economic', 'financial', 'fiscal', 'market'],
        'education': ['school', 'learning', 'academic', 'university'],
        'health': ['medical', 'healthcare', 'wellness', 'hospital'],
        'climate': ['weather', 'environment', 'atmospheric'],
        'technology': ['tech', 'digital', 'innovation', 'software'],
        'business': ['commerce', 'trade', 'corporate', 'enterprise'],
        'politics': ['political', 'government', 'policy'],
        'sports': ['athletics', 'games', 'tournament', 'match'],
        'crime': ['criminal', 'offense', 'illegal', 'law'],
        'agriculture': ['farming', 'crop', 'harvest', 'agricultural'],
    }

    # Extended Bangla synonyms dictionary for news/newspaper domain
    # Organized by category for comprehensive coverage
    BANGLA_SYNONYMS = {
        # Health & Medical
        'করোনা': ['কোভিড', 'মহামারী', 'ভাইরাস', 'সংক্রমণ', 'রোগ'],
        'ভ্যাকসিন': ['টিকা', 'প্রতিষেধক', 'ইমিউনাইজেশন'],
        'স্বাস্থ্য': ['চিকিৎসা', 'হাসপাতাল', 'স্বাস্থ্যসেবা', 'রোগী', 'ডাক্তার'],
        'রোগ': ['অসুস্থতা', 'ব্যাধি', 'সংক্রমণ', 'জ্বর'],
        'চিকিৎসা': ['স্বাস্থ্যসেবা', 'হাসপাতাল', 'ডাক্তার', 'ওষুধ'],
        'মৃত্যু': ['মারা', 'নিহত', 'প্রাণহানি', 'শহীদ'],

        # Politics & Government
        'নির্বাচন': ['ভোট', 'নির্বাচনী', 'ব্যালট', 'পোলিং'],
        'সরকার': ['প্রশাসন', 'কর্তৃপক্ষ', 'মন্ত্রিসভা', 'শাসন'],
        'রাজনীতি': ['রাজনৈতিক', 'দল', 'সংসদ', 'আইনসভা'],
        'প্রধানমন্ত্রী': ['সরকারপ্রধান', 'পিএম', 'নেতা'],
        'বিরোধী': ['বিরোধীদল', 'প্রতিপক্ষ', 'বিরোধিতা'],
        'সংসদ': ['জাতীয় সংসদ', 'আইনসভা', 'পার্লামেন্ট'],

        # Economy & Business
        'অর্থনীতি': ['আর্থিক', 'বাণিজ্য', 'অর্থনৈতিক', 'ব্যবসা'],
        'ব্যবসা': ['বাণিজ্য', 'ব্যবসায়', 'কোম্পানি', 'শিল্প'],
        'বাজার': ['মার্কেট', 'বাণিজ্য', 'হাট', 'দোকান'],
        'মূল্য': ['দাম', 'খরচ', 'মূল্যবৃদ্ধি', 'দর'],
        'ব্যাংক': ['আর্থিক প্রতিষ্ঠান', 'ঋণ', 'সুদ'],
        'রপ্তানি': ['বিদেশে বিক্রি', 'রপ্তানিকারক', 'বৈদেশিক বাণিজ্য'],
        'আমদানি': ['বিদেশ থেকে', 'আমদানিকারক'],

        # Education
        'শিক্ষা': ['পড়াশোনা', 'বিদ্যালয়', 'বিশ্ববিদ্যালয়', 'স্কুল', 'শিক্ষার্থী'],
        'স্কুল': ['বিদ্যালয়', 'মাধ্যমিক', 'প্রাথমিক'],
        'বিশ্ববিদ্যালয়': ['বিশ্ববিদ্যালয়ের', 'ভার্সিটি', 'উচ্চশিক্ষা'],
        'পরীক্ষা': ['এক্সাম', 'মূল্যায়ন', 'পরীক্ষার্থী'],
        'শিক্ষক': ['শিক্ষিকা', 'অধ্যাপক', 'প্রশিক্ষক'],

        # Weather & Environment
        'আবহাওয়া': ['জলবায়ু', 'পরিবেশ', 'তাপমাত্রা', 'বৃষ্টি'],
        'বন্যা': ['প্লাবন', 'জলাবদ্ধতা', 'পানি'],
        'ঝড়': ['ঘূর্ণিঝড়', 'সাইক্লোন', 'তুফান', 'বাতাস'],
        'বৃষ্টি': ['বর্ষা', 'বৃষ্টিপাত', 'জল'],
        'পরিবেশ': ['প্রকৃতি', 'জলবায়ু', 'বাস্তুসংস্থান'],

        # Technology
        'প্রযুক্তি': ['প্রযুক্তিগত', 'ডিজিটাল', 'তথ্যপ্রযুক্তি', 'আইটি'],
        'ইন্টারনেট': ['অনলাইন', 'নেটওয়ার্ক', 'ওয়েব'],
        'মোবাইল': ['ফোন', 'স্মার্টফোন', 'হ্যান্ডসেট'],

        # Crime & Law
        'অপরাধ': ['অপরাধী', 'দোষ', 'আইনবিরোধী'],
        'পুলিশ': ['আইনশৃঙ্খলা', 'থানা', 'গ্রেফতার'],
        'আদালত': ['বিচার', 'আইন', 'মামলা', 'কোর্ট'],
        'হত্যা': ['খুন', 'নিহত', 'মৃত্যু'],
        'গ্রেফতার': ['আটক', 'ধরা', 'বন্দী'],

        # Sports
        'ক্রিকেট': ['ম্যাচ', 'খেলা', 'টুর্নামেন্ট'],
        'ফুটবল': ['সকার', 'খেলা', 'ম্যাচ'],
        'খেলা': ['ম্যাচ', 'টুর্নামেন্ট', 'প্রতিযোগিতা', 'ক্রীড়া'],

        # Accidents & Disasters
        'দুর্ঘটনা': ['এক্সিডেন্ট', 'ঘটনা', 'আঘাত'],
        'আগুন': ['অগ্নিকাণ্ড', 'দাবানল', 'আগুনে'],
        'সড়ক': ['রাস্তা', 'পথ', 'মহাসড়ক'],

        # Agriculture
        'কৃষি': ['চাষ', 'ফসল', 'কৃষক', 'চাষাবাদ'],
        'ফসল': ['শস্য', 'উৎপাদন', 'চাষ'],
        'ধান': ['চাল', 'শস্য', 'ফসল'],

        # Society
        'সমাজ': ['সামাজিক', 'জনগণ', 'মানুষ'],
        'পরিবার': ['পরিবারের', 'সংসার', 'গৃহস্থ'],
        'নারী': ['মহিলা', 'মেয়ে', 'নারীদের'],
        'শিশু': ['বাচ্চা', 'শিশুদের', 'ছেলেমেয়ে'],
    }

    # Fallback Named Entity mapping (Bangla <-> English) - used when transformers unavailable
    NAMED_ENTITY_MAP_FALLBACK = {
        # Countries
        'বাংলাদেশ': 'Bangladesh',
        'ভারত': 'India',
        'পাকিস্তান': 'Pakistan',
        'চীন': 'China',
        'আমেরিকা': 'America',
        'যুক্তরাষ্ট্র': 'United States',
        'যুক্তরাজ্য': 'United Kingdom',
        'জাপান': 'Japan',

        # Cities
        'ঢাকা': 'Dhaka',
        'চট্টগ্রাম': 'Chittagong',
        'খুলনা': 'Khulna',
        'সিলেট': 'Sylhet',
        'রাজশাহী': 'Rajshahi',
        'কলকাতা': 'Kolkata',
        'দিল্লি': 'Delhi',

        # Organizations
        'জাতিসংঘ': 'United Nations',
        'বিশ্বব্যাংক': 'World Bank',
        'আইএমএফ': 'IMF',
        'বিশ্ব স্বাস্থ্য সংস্থা': 'WHO',

        # People (common titles)
        'প্রধানমন্ত্রী': 'Prime Minister',
        'রাষ্ট্রপতি': 'President',

        # Sports
        'ক্রিকেট': 'Cricket',
        'ফুটবল': 'Football',
    }

    # Bangla NER label mapping (from mbert-bengali-ner model)
    BANGLA_LABEL_MAP = {
        'LABEL_1': 'PER',  # Person (first part)
        'LABEL_2': 'PER',  # Person (continuation)
        'LABEL_3': 'ORG',  # Organization (first part)
        'LABEL_4': 'ORG',  # Organization (continuation)
        'LABEL_5': 'LOC',  # Location (first part)
        'LABEL_6': 'LOC',  # Location (continuation)
        'LABEL_0': 'O'     # Outside entity
    }

    def __init__(
        self,
        remove_stopwords: bool = False,
        enable_expansion: bool = True,
        enable_translation: bool = True,
        enable_ne_mapping: bool = True,
        use_ml_ner: bool = True,
        translation_backend: str = 'auto',
        use_translation_cache: bool = True,
    ):
        """
        Initialize QueryProcessor.

        Args:
            remove_stopwords: Whether to remove stopwords during normalization
            enable_expansion: Whether to expand query with synonyms
            enable_translation: Whether to enable query translation
            enable_ne_mapping: Whether to enable named entity mapping
            use_ml_ner: Whether to use ML-based NER (requires transformers)
            translation_backend: Translation backend ('deep_translator', 'googletrans', or 'auto')
            use_translation_cache: Enable translation caching for performance
        """
        self.remove_stopwords = remove_stopwords
        self.enable_expansion = enable_expansion
        self.enable_translation = enable_translation and TRANSLATOR_AVAILABLE
        self.enable_ne_mapping = enable_ne_mapping
        self.use_ml_ner = use_ml_ner and TRANSFORMERS_AVAILABLE
        self.use_translation_cache = use_translation_cache

        # Initialize translation backend
        self.translator_backend = None
        self.translator_backend_name = None
        if self.enable_translation:
            self._initialize_translation_backend(translation_backend)
        
        # Translation cache
        self._translation_cache = {} if use_translation_cache else None

        # Build reverse NE map for fallback (English -> Bangla)
        self.ne_map_en_to_bn = {v.lower(): k for k, v in self.NAMED_ENTITY_MAP_FALLBACK.items()}
        self.ne_map_bn_to_en = {k: v for k, v in self.NAMED_ENTITY_MAP_FALLBACK.items()}

        # Lazy-loaded NER models (initialized on first use)
        self._english_ner = None
        self._bangla_ner = None

    def _initialize_translation_backend(self, backend: str):
        """Initialize the translation backend."""
        if backend == 'auto':
            # Auto-select best available backend
            if HAS_DEEP_TRANSLATOR:
                self.translator_backend = 'deep_translator'
                self.translator_backend_name = 'deep_translator'
            elif HAS_GOOGLETRANS:
                self.translator_backend = GoogletransTranslator()
                self.translator_backend_name = 'googletrans'
        elif backend == 'deep_translator':
            if not HAS_DEEP_TRANSLATOR:
                print("Warning: deep-translator not installed. Falling back to available backend.")
                if HAS_GOOGLETRANS:
                    self.translator_backend = GoogletransTranslator()
                    self.translator_backend_name = 'googletrans'
            else:
                self.translator_backend = 'deep_translator'
                self.translator_backend_name = 'deep_translator'
        elif backend == 'googletrans':
            if not HAS_GOOGLETRANS:
                print("Warning: googletrans not installed. Falling back to available backend.")
                if HAS_DEEP_TRANSLATOR:
                    self.translator_backend = 'deep_translator'
                    self.translator_backend_name = 'deep_translator'
            else:
                self.translator_backend = GoogletransTranslator()
                self.translator_backend_name = 'googletrans'

    def _load_english_ner(self):
        """Lazy load English NER model."""
        if self._english_ner is None and TRANSFORMERS_AVAILABLE:
            try:
                self._english_ner = pipeline(
                    "ner",
                    model="xlm-roberta-large-finetuned-conll03-english",
                    tokenizer="xlm-roberta-large-finetuned-conll03-english",
                    aggregation_strategy="simple"
                )
            except Exception as e:
                print(f"Warning: Failed to load English NER model: {e}")
                self._english_ner = False  # Mark as failed
        return self._english_ner if self._english_ner else None

    def _load_bangla_ner(self):
        """Lazy load Bangla NER model."""
        if self._bangla_ner is None and TRANSFORMERS_AVAILABLE:
            try:
                self._bangla_ner = pipeline(
                    "ner",
                    model="sagorsarker/mbert-bengali-ner",
                    aggregation_strategy="simple"
                )
            except Exception as e:
                print(f"Warning: Failed to load Bangla NER model: {e}")
                self._bangla_ner = False  # Mark as failed
        return self._bangla_ner if self._bangla_ner else None

    def detect_language(self, text: str) -> str:
        """
        Detect if text is Bangla or English based on Unicode character ranges.

        Args:
            text: Input text

        Returns:
            'bn' for Bangla, 'en' for English
        """
        if not text:
            return 'en'

        bangla_count = 0
        total_alpha = 0

        for char in text:
            if char.isalpha():
                total_alpha += 1
                code_point = ord(char)
                if self.BANGLA_RANGE[0] <= code_point <= self.BANGLA_RANGE[1]:
                    bangla_count += 1

        if total_alpha == 0:
            return 'en'

        # If more than 30% Bangla characters, consider it Bangla
        bangla_ratio = bangla_count / total_alpha
        return 'bn' if bangla_ratio > 0.3 else 'en'

    def normalize(self, text: str, language: str) -> Tuple[str, List[str]]:
        """
        Normalize query text.

        Steps:
        1. Unicode normalization (NFC)
        2. Lowercase
        3. Remove extra whitespace
        4. Tokenize
        5. Optional stopword removal

        Args:
            text: Input text
            language: 'en' or 'bn'

        Returns:
            Tuple of (normalized_text, tokens)
        """
        # Unicode normalization
        text = unicodedata.normalize('NFC', text)

        # Lowercase
        text = text.lower()

        # Remove extra whitespace
        text = ' '.join(text.split())

        # Tokenize based on language
        if language == 'bn':
            # Bangla tokenization - split on whitespace and punctuation
            tokens = re.findall(r'[\u0980-\u09FF]+', text)
        else:
            # English tokenization
            tokens = re.findall(r'[a-zA-Z0-9]+', text)

        # Optional stopword removal
        if self.remove_stopwords:
            stopwords = self.BANGLA_STOPWORDS if language == 'bn' else self.ENGLISH_STOPWORDS
            tokens = [t for t in tokens if t not in stopwords]

        normalized_text = ' '.join(tokens)
        return normalized_text, tokens

    def _get_translation_cache_key(self, text: str, source_lang: str, target_lang: str) -> str:
        """Generate cache key for translation."""
        import hashlib
        key_string = f"{text}|{source_lang}|{target_lang}"
        return hashlib.md5(key_string.encode('utf-8')).hexdigest()

    def translate(self, text: str, source_lang: str, target_lang: str) -> Optional[str]:
        """
        Translate query to target language with caching and multiple backend support.

        Args:
            text: Text to translate
            source_lang: Source language ('en' or 'bn')
            target_lang: Target language ('en' or 'bn')

        Returns:
            Translated text or None if translation fails
        """
        if not self.enable_translation:
            return None

        if not text or not text.strip():
            return text

        if source_lang == target_lang:
            return text

        # Check cache first
        if self.use_translation_cache and self._translation_cache is not None:
            cache_key = self._get_translation_cache_key(text, source_lang, target_lang)
            if cache_key in self._translation_cache:
                return self._translation_cache[cache_key]

        try:
            # Convert language codes
            src = 'en' if source_lang == 'en' else 'bn'
            tgt = 'en' if target_lang == 'en' else 'bn'

            # Perform translation based on backend
            if self.translator_backend_name == 'deep_translator':
                translator = GoogleTranslator(source=src, target=tgt)
                translated = translator.translate(text)
            elif self.translator_backend_name == 'googletrans':
                result = self.translator_backend.translate(text, src=src, dest=tgt)
                translated = result.text
            else:
                return None

            # Cache the result
            if self.use_translation_cache and self._translation_cache is not None:
                self._translation_cache[cache_key] = translated

            return translated
        except Exception as e:
            print(f"Translation failed: {e}")
            return None

    def expand_query(self, tokens: List[str], language: str, max_synonyms: int = 5) -> List[str]:
        """
        Expand query with synonyms.

        For English: Uses NLTK WordNet (155,000+ words) if available
        For Bangla: Uses CSV dictionary + domain-specific fallback dictionary

        Args:
            tokens: List of query tokens
            language: 'en' or 'bn'
            max_synonyms: Maximum synonyms per token (default 5)

        Returns:
            List of expanded terms (synonyms not in original)
        """
        if not self.enable_expansion:
            return []

        expanded = []
        tokens_lower = [t.lower() for t in tokens]

        if language == 'bn':
            # Use Bangla synonyms: first check CSV, then fallback dictionary
            for token in tokens:
                synonyms_found = []

                # First check CSV-loaded synonyms (primary source)
                if token in BANGLA_SYNONYMS_CSV:
                    synonyms_found.extend(BANGLA_SYNONYMS_CSV[token])

                # Then check fallback dictionary for domain-specific terms
                if token in self.BANGLA_SYNONYMS:
                    for syn in self.BANGLA_SYNONYMS[token]:
                        if syn not in synonyms_found:
                            synonyms_found.append(syn)

                # Add unique synonyms up to max_synonyms
                for synonym in synonyms_found[:max_synonyms]:
                    if synonym not in tokens and synonym not in expanded:
                        expanded.append(synonym)
        else:
            # Use NLTK WordNet for English if available
            if WORDNET_AVAILABLE:
                for token in tokens:
                    token_lower = token.lower()
                    synonyms_found = set()

                    # Get all synsets for the word
                    for syn in wordnet.synsets(token_lower):
                        for lemma in syn.lemmas():
                            lemma_name = lemma.name().lower().replace('_', ' ')
                            # Only add if different from original and not already in query
                            if lemma_name != token_lower and lemma_name not in tokens_lower:
                                synonyms_found.add(lemma_name)

                    # Add top synonyms
                    for synonym in list(synonyms_found)[:max_synonyms]:
                        if synonym not in expanded:
                            expanded.append(synonym)
            else:
                # Fallback to preset dictionary
                for token in tokens:
                    token_lower = token.lower()
                    if token_lower in self.ENGLISH_SYNONYMS_FALLBACK:
                        for synonym in self.ENGLISH_SYNONYMS_FALLBACK[token_lower][:max_synonyms]:
                            if synonym.lower() not in tokens_lower and synonym not in expanded:
                                expanded.append(synonym)

        return expanded

    def extract_named_entities(self, text: str, language: str) -> List[Dict]:
        """
        Extract named entities from text using ML models.

        Args:
            text: Input text
            language: 'en' or 'bn'

        Returns:
            List of dicts with 'text', 'type', and 'score' keys
        """
        if not self.use_ml_ner:
            return []

        entities = []

        try:
            if language == 'en':
                ner_model = self._load_english_ner()
                if ner_model:
                    raw_entities = ner_model(text)
                    for entity in raw_entities:
                        entities.append({
                            'text': entity['word'],
                            'type': entity['entity_group'],
                            'score': float(entity['score'])
                        })
            elif language == 'bn':
                ner_model = self._load_bangla_ner()
                if ner_model:
                    raw_entities = ner_model(text)
                    for entity in raw_entities:
                        # Map Bangla labels to standard labels
                        entity_type = self.BANGLA_LABEL_MAP.get(
                            entity['entity_group'], entity['entity_group']
                        )
                        if entity_type != 'O':  # Skip 'Outside' entities
                            entities.append({
                                'text': entity['word'],
                                'type': entity_type,
                                'score': float(entity['score'])
                            })
        except Exception as e:
            print(f"NER extraction failed: {e}")

        return entities

    def map_named_entities(self, tokens: List[str], source_lang: str, target_lang: str) -> List[Tuple[str, str]]:
        """
        Map named entities across languages.

        Uses ML-based NER models (xlm-roberta for English, mbert for Bangla)
        to extract entities, then translates them to the target language.

        Args:
            tokens: List of query tokens
            source_lang: Source language
            target_lang: Target language

        Returns:
            List of (original_entity, mapped_entity) tuples
        """
        if not self.enable_ne_mapping:
            return []

        if source_lang == target_lang:
            return []

        mappings = []
        text = ' '.join(tokens)

        # Try ML-based NER first
        if self.use_ml_ner and TRANSFORMERS_AVAILABLE:
            entities = self.extract_named_entities(text, source_lang)

            for entity in entities:
                entity_text = entity['text']

                # Try to translate the entity
                if self.enable_translation:
                    translated = self.translate(entity_text, source_lang, target_lang)
                    if translated and translated.lower() != entity_text.lower():
                        mappings.append((entity_text, translated))
                else:
                    # Check fallback dictionary
                    if source_lang == 'bn':
                        if entity_text in self.ne_map_bn_to_en:
                            mappings.append((entity_text, self.ne_map_bn_to_en[entity_text]))
                    else:
                        entity_lower = entity_text.lower()
                        if entity_lower in self.ne_map_en_to_bn:
                            mappings.append((entity_text, self.ne_map_en_to_bn[entity_lower]))

            if mappings:
                return mappings

        # Fallback to dictionary-based mapping
        if source_lang == 'bn' and target_lang == 'en':
            # Bangla to English
            for bn_entity, en_entity in self.ne_map_bn_to_en.items():
                if bn_entity in text:
                    mappings.append((bn_entity, en_entity))
        else:
            # English to Bangla
            text_lower = text.lower()
            for en_entity, bn_entity in self.ne_map_en_to_bn.items():
                if en_entity in text_lower:
                    mappings.append((en_entity, bn_entity))

        return mappings

    def process(
        self,
        query: str,
        target_lang: Optional[str] = None,
        expand: Optional[bool] = None,
    ) -> ProcessedQuery:
        """
        Process query through the complete pipeline.

        Pipeline:
        1. Language Detection
        2. Normalization
        3. Query Translation (if target_lang specified)
        4. Query Expansion
        5. Named Entity Mapping

        Args:
            query: Raw query text
            target_lang: Target language for translation (None = no translation)
            expand: Override expansion setting (None = use default)

        Returns:
            ProcessedQuery object with all processing results
        """
        steps = []

        # Step 1: Language Detection
        detected_lang = self.detect_language(query)
        steps.append(f"Language detected: {detected_lang}")

        # Step 2: Normalization
        normalized, tokens = self.normalize(query, detected_lang)
        steps.append(f"Normalized: '{normalized}'")
        if self.remove_stopwords:
            steps.append("Stopwords removed")

        # Step 3: Translation
        translated = None
        trans_lang = None
        if target_lang and target_lang != detected_lang:
            translated = self.translate(query, detected_lang, target_lang)
            trans_lang = target_lang
            if translated:
                steps.append(f"Translated to {target_lang}: '{translated}'")
            else:
                steps.append(f"Translation to {target_lang} failed")

        # Step 4: Query Expansion
        should_expand = expand if expand is not None else self.enable_expansion
        expanded_terms = []
        if should_expand:
            expanded_terms = self.expand_query(tokens, detected_lang)
            if expanded_terms:
                steps.append(f"Expanded with: {expanded_terms}")

        # Step 5: Named Entity Mapping
        ne_mappings = []
        if target_lang and self.enable_ne_mapping:
            ne_mappings = self.map_named_entities(tokens, detected_lang, target_lang)
            if ne_mappings:
                steps.append(f"NE mappings: {ne_mappings}")

        return ProcessedQuery(
            original=query,
            detected_language=detected_lang,
            normalized=normalized,
            tokens=tokens,
            translated=translated,
            translation_language=trans_lang,
            expanded_terms=expanded_terms,
            named_entities=ne_mappings,
            processing_steps=steps,
        )

    def process_for_search(
        self,
        query: str,
        search_both_languages: bool = True,
    ) -> Dict[str, ProcessedQuery]:
        """
        Process query for cross-lingual search.

        Returns processed queries for both languages if search_both_languages=True.

        Args:
            query: Raw query text
            search_both_languages: Whether to prepare queries for both EN and BN

        Returns:
            Dict with 'original' and optionally 'translated' ProcessedQuery objects
        """
        # Process original query
        detected_lang = self.detect_language(query)
        original_processed = self.process(query)

        result = {'original': original_processed}

        if search_both_languages:
            # Translate to the other language
            target_lang = 'bn' if detected_lang == 'en' else 'en'
            translated_processed = self.process(query, target_lang=target_lang)
            result['translated'] = translated_processed

        return result

    def clear_translation_cache(self):
        """Clear the translation cache."""
        if self._translation_cache is not None:
            self._translation_cache.clear()

    def get_translation_cache_size(self) -> int:
        """Get the number of cached translations."""
        return len(self._translation_cache) if self._translation_cache is not None else 0

    def english_to_bangla(self, text: str) -> Optional[str]:
        """Translate English text to Bangla.
        
        Args:
            text: English text
            
        Returns:
            Bangla translation or None if translation fails
        """
        return self.translate(text, 'en', 'bn')

    def bangla_to_english(self, text: str) -> Optional[str]:
        """Translate Bangla text to English.
        
        Args:
            text: Bangla text
            
        Returns:
            English translation or None if translation fails
        """
        return self.translate(text, 'bn', 'en')


def main():
    """Demo of query processing pipeline."""
    import sys
    import io

    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

    processor = QueryProcessor(remove_stopwords=False)

    print("=" * 80)
    print("Query Processing Pipeline Demo")
    print("=" * 80)

    # Test queries
    test_queries = [
        ("coronavirus vaccine", "en", "bn"),
        ("Bangladesh election results", "en", "bn"),
        ("করোনা ভ্যাকসিন", "bn", "en"),
        ("ঢাকা আবহাওয়া", "bn", "en"),
        ("climate change impact", "en", "bn"),
    ]

    for query, expected_lang, target_lang in test_queries:
        print(f"\n{'─' * 80}")
        print(f"Query: '{query}'")
        print(f"{'─' * 80}")

        result = processor.process(query, target_lang=target_lang)

        print(f"  Detected Language: {result.detected_language}")
        print(f"  Normalized: '{result.normalized}'")
        print(f"  Tokens: {result.tokens}")

        if result.translated:
            print(f"  Translated ({result.translation_language}): '{result.translated}'")

        if result.expanded_terms:
            print(f"  Expanded Terms: {result.expanded_terms}")

        if result.named_entities:
            print(f"  Named Entities: {result.named_entities}")

        print(f"\n  Processing Steps:")
        for step in result.processing_steps:
            print(f"    - {step}")


if __name__ == "__main__":
    main()
