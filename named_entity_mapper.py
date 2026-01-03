#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Named Entity Mapping Module for Cross-Lingual Information Retrieval (CLIR)
Maps named entities (places, people, organizations) between English and Bangla.

Phase 2: Query Processing - Named Entity Mapping
"""

import re
from typing import Dict, List, Optional, Tuple, Set
import json
import os


class NamedEntityMapper:
    """
    Map named entities between English and Bangla.
    
    Features:
    - Bidirectional mapping (English ↔ Bangla)
    - Multiple categories: Places, People, Organizations, Events
    - Extensible dictionary system
    - Case-insensitive matching
    - Multi-word entity support
    """
    
    # Built-in entity mappings
    ENTITY_MAPPINGS = {
        # Places - Cities
        'dhaka': 'ঢাকা',
        'chittagong': 'চট্টগ্রাম',
        'sylhet': 'সিলেট',
        'rajshahi': 'রাজশাহী',
        'khulna': 'খুলনা',
        'barisal': 'বরিশাল',
        'rangpur': 'রংপুর',
        'mymensingh': 'ময়মনসিংহ',
        'comilla': 'কুমিল্লা',
        'narayanganj': 'নারায়ণগঞ্জ',
        'cox\'s bazar': 'কক্সবাজার',
        'jessore': 'যশোর',
        'bogra': 'বগুড়া',
        'dinajpur': 'দিনাজপুর',
        'tangail': 'টাঙ্গাইল',
        
        # Countries
        'bangladesh': 'বাংলাদেশ',
        'india': 'ভারত',
        'pakistan': 'পাকিস্তান',
        'china': 'চীন',
        'usa': 'যুক্তরাষ্ট্র',
        'united states': 'যুক্তরাষ্ট্র',
        'america': 'আমেরিকা',
        'united kingdom': 'যুক্তরাজ্য',
        'britain': 'ব্রিটেন',
        'russia': 'রাশিয়া',
        'japan': 'জাপান',
        'australia': 'অস্ট্রেলিয়া',
        'canada': 'কানাডা',
        'germany': 'জার্মানি',
        'france': 'ফ্রান্স',
        
        # People - Political Figures
        'sheikh mujibur rahman': 'শেখ মুজিবুর রহমান',
        'sheikh hasina': 'শেখ হাসিনা',
        'khaleda zia': 'খালেদা জিয়া',
        'ziaur rahman': 'জিয়াউর রহমান',
        'hussain muhammad ershad': 'হুসেইন মুহাম্মদ এরশাদ',
        'narendra modi': 'নরেন্দ্র মোদী',
        'joe biden': 'জো বাইডেন',
        
        # People - Cultural/Sports Figures
        'shakib al hasan': 'শাকিব আল হাসান',
        'mashrafe mortaza': 'মাশরাফি বিন মর্তুজা',
        'mushfiqur rahim': 'মুশফিকুর রহিম',
        'tamim iqbal': 'তামিম ইকবাল',
        'rabindranath tagore': 'রবীন্দ্রনাথ ঠাকুর',
        'kazi nazrul islam': 'কাজী নজরুল ইসলাম',
        
        # Organizations
        'awami league': 'আওয়ামী লীগ',
        'bnp': 'বিএনপি',
        'bangladesh nationalist party': 'বাংলাদেশ জাতীয়তাবাদী দল',
        'bcb': 'বিসিবি',
        'bangladesh cricket board': 'বাংলাদেশ ক্রিকেট বোর্ড',
        'fifa': 'ফিফা',
        'who': 'ডব্লিউএইচও',
        'world health organization': 'বিশ্ব স্বাস্থ্য সংস্থা',
        'un': 'জাতিসংঘ',
        'united nations': 'জাতিসংঘ',
        'unesco': 'ইউনেস্কো',
        
        # Events/Occasions
        'independence day': 'স্বাধীনতা দিবস',
        'victory day': 'বিজয় দিবস',
        'language movement': 'ভাষা আন্দোলন',
        'liberation war': 'মুক্তিযুদ্ধ',
        'international mother language day': 'আন্তর্জাতিক মাতৃভাষা দিবস',
        
        # Common Terms
        'bengali': 'বাংলা',
        'bangla': 'বাংলা',
        'bengal': 'বাংলা',
        'bay of bengal': 'বঙ্গোপসাগর',
        'river padma': 'পদ্মা নদী',
        'river jamuna': 'যমুনা নদী',
        'river meghna': 'মেঘনা নদী',
        
        # Sports Terms
        'cricket': 'ক্রিকেট',
        'football': 'ফুটবল',
        'world cup': 'বিশ্বকাপ',
        'olympics': 'অলিম্পিক',
        
        # Institutions
        'dhaka university': 'ঢাকা বিশ্ববিদ্যালয়',
        'buet': 'বুয়েট',
        'medical college': 'মেডিকেল কলেজ',
    }
    
    def __init__(self, custom_mappings: Optional[Dict[str, str]] = None):
        """
        Initialize named entity mapper.
        
        Args:
            custom_mappings: Additional entity mappings to add
        """
        # Combine built-in and custom mappings
        self.en_to_bn = self.ENTITY_MAPPINGS.copy()
        
        if custom_mappings:
            self.en_to_bn.update(custom_mappings)
        
        # Create reverse mapping (Bangla to English)
        self.bn_to_en = {v: k for k, v in self.en_to_bn.items()}
        
        # Compile regex patterns for efficient matching
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile regex patterns for entity detection."""
        # Sort by length (longest first) to match multi-word entities first
        en_entities = sorted(self.en_to_bn.keys(), key=len, reverse=True)
        bn_entities = sorted(self.bn_to_en.keys(), key=len, reverse=True)
        
        # Escape special regex characters
        en_patterns = [re.escape(entity) for entity in en_entities]
        bn_patterns = [re.escape(entity) for entity in bn_entities]
        
        # Create patterns with word boundaries
        self.en_pattern = re.compile(
            r'\b(' + '|'.join(en_patterns) + r')\b',
            re.IGNORECASE
        )
        
        self.bn_pattern = re.compile(
            '(' + '|'.join(bn_patterns) + ')'
        )
    
    def map_english_to_bangla(self, text: str) -> str:
        """
        Map English entities to Bangla in text.
        
        Args:
            text: Input text with English entities
            
        Returns:
            Text with entities mapped to Bangla
        """
        def replace_entity(match):
            entity = match.group(1).lower()
            return self.en_to_bn.get(entity, match.group(1))
        
        return self.en_pattern.sub(replace_entity, text)
    
    def map_bangla_to_english(self, text: str) -> str:
        """
        Map Bangla entities to English in text.
        
        Args:
            text: Input text with Bangla entities
            
        Returns:
            Text with entities mapped to English
        """
        def replace_entity(match):
            entity = match.group(1)
            return self.bn_to_en.get(entity, match.group(1))
        
        return self.bn_pattern.sub(replace_entity, text)
    
    def get_entity_mapping(self, entity: str, source_lang: str = 'auto') -> Optional[str]:
        """
        Get mapping for a specific entity.
        
        Args:
            entity: Entity to map
            source_lang: Source language ('en', 'bn', or 'auto')
            
        Returns:
            Mapped entity or None if not found
        """
        entity_lower = entity.lower() if source_lang != 'bn' else entity
        
        if source_lang == 'en':
            return self.en_to_bn.get(entity_lower)
        elif source_lang == 'bn':
            return self.bn_to_en.get(entity)
        else:  # auto-detect
            # Try English first
            result = self.en_to_bn.get(entity_lower)
            if result:
                return result
            # Try Bangla
            return self.bn_to_en.get(entity)
    
    def extract_entities(self, text: str, language: str = 'auto') -> List[Tuple[str, str]]:
        """
        Extract all named entities from text with their mappings.
        
        Args:
            text: Input text
            language: Text language ('en', 'bn', or 'auto')
            
        Returns:
            List of (original_entity, mapped_entity) tuples
        """
        entities = []
        
        if language in ('en', 'auto'):
            # Extract English entities
            for match in self.en_pattern.finditer(text):
                original = match.group(1)
                mapped = self.en_to_bn.get(original.lower())
                if mapped:
                    entities.append((original, mapped))
        
        if language in ('bn', 'auto'):
            # Extract Bangla entities
            for match in self.bn_pattern.finditer(text):
                original = match.group(1)
                mapped = self.bn_to_en.get(original)
                if mapped:
                    entities.append((original, mapped))
        
        return entities
    
    def add_mapping(self, english: str, bangla: str):
        """
        Add a new entity mapping.
        
        Args:
            english: English entity
            bangla: Bangla entity
        """
        english_lower = english.lower()
        self.en_to_bn[english_lower] = bangla
        self.bn_to_en[bangla] = english_lower
        
        # Recompile patterns
        self._compile_patterns()
    
    def add_mappings(self, mappings: Dict[str, str]):
        """
        Add multiple entity mappings.
        
        Args:
            mappings: Dictionary of English -> Bangla mappings
        """
        for english, bangla in mappings.items():
            english_lower = english.lower()
            self.en_to_bn[english_lower] = bangla
            self.bn_to_en[bangla] = english_lower
        
        # Recompile patterns
        self._compile_patterns()
    
    def load_from_file(self, filepath: str):
        """
        Load entity mappings from JSON file.
        
        Args:
            filepath: Path to JSON file with mappings
        """
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                mappings = json.load(f)
                self.add_mappings(mappings)
    
    def save_to_file(self, filepath: str):
        """
        Save entity mappings to JSON file.
        
        Args:
            filepath: Path to save mappings
        """
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.en_to_bn, f, ensure_ascii=False, indent=2)
    
    def get_all_entities(self, language: str = 'both') -> List[str]:
        """
        Get all mapped entities.
        
        Args:
            language: 'en', 'bn', or 'both'
            
        Returns:
            List of entities
        """
        if language == 'en':
            return list(self.en_to_bn.keys())
        elif language == 'bn':
            return list(self.bn_to_en.keys())
        else:  # both
            return list(self.en_to_bn.keys()) + list(self.bn_to_en.keys())
    
    def get_mapping_count(self) -> int:
        """Get total number of entity mappings."""
        return len(self.en_to_bn)
    
    def search_entities(self, query: str, language: str = 'auto') -> List[Tuple[str, str]]:
        """
        Search for entities matching a query.
        
        Args:
            query: Search query
            language: Search language ('en', 'bn', or 'auto')
            
        Returns:
            List of (english, bangla) tuples matching query
        """
        query_lower = query.lower()
        results = []
        
        if language in ('en', 'auto'):
            for en, bn in self.en_to_bn.items():
                if query_lower in en.lower():
                    results.append((en, bn))
        
        if language in ('bn', 'auto'):
            for bn, en in self.bn_to_en.items():
                if query in bn:
                    results.append((en, bn))
        
        return results


# Convenience functions
def map_entities(text: str, direction: str = 'en_to_bn', 
                 custom_mappings: Optional[Dict[str, str]] = None) -> str:
    """
    Quick entity mapping.
    
    Args:
        text: Input text
        direction: 'en_to_bn' or 'bn_to_en'
        custom_mappings: Optional custom mappings
        
    Returns:
        Text with mapped entities
    """
    mapper = NamedEntityMapper(custom_mappings)
    
    if direction == 'en_to_bn':
        return mapper.map_english_to_bangla(text)
    else:
        return mapper.map_bangla_to_english(text)


def get_entity_mapping(entity: str, source_lang: str = 'auto') -> Optional[str]:
    """
    Get mapping for a single entity.
    
    Args:
        entity: Entity to map
        source_lang: Source language
        
    Returns:
        Mapped entity or None
    """
    mapper = NamedEntityMapper()
    return mapper.get_entity_mapping(entity, source_lang)


if __name__ == "__main__":
    print("Named Entity Mapping Module - Quick Test")
    print("=" * 80)
    
    mapper = NamedEntityMapper()
    
    # Test 1: English to Bangla
    print("\n1. English to Bangla Mapping")
    print("-" * 80)
    
    en_texts = [
        "Dhaka is the capital of Bangladesh",
        "Sheikh Hasina met with Joe Biden",
        "Cricket match between Bangladesh and India",
        "Shakib Al Hasan scored century at Dhaka"
    ]
    
    for text in en_texts:
        mapped = mapper.map_english_to_bangla(text)
        print(f"Original:  {text}")
        print(f"Mapped:    {mapped}\n")
    
    # Test 2: Bangla to English
    print("\n2. Bangla to English Mapping")
    print("-" * 80)
    
    bn_texts = [
        "ঢাকা বাংলাদেশের রাজধানী",
        "শেখ হাসিনা এবং নরেন্দ্র মোদী",
        "বাংলাদেশ ক্রিকেট বোর্ড"
    ]
    
    for text in bn_texts:
        mapped = mapper.map_bangla_to_english(text)
        print(f"Original:  {text}")
        print(f"Mapped:    {mapped}\n")
    
    # Test 3: Entity extraction
    print("\n3. Entity Extraction")
    print("-" * 80)
    
    text = "Dhaka and Chittagong are major cities in Bangladesh"
    entities = mapper.extract_entities(text)
    print(f"Text: {text}")
    print(f"Extracted entities:")
    for orig, mapped in entities:
        print(f"  {orig:20s} → {mapped}")
    
    # Test 4: Single entity lookup
    print("\n\n4. Single Entity Lookup")
    print("-" * 80)
    
    entities_to_test = ["Dhaka", "ঢাকা", "Bangladesh", "শেখ হাসিনা"]
    for entity in entities_to_test:
        mapped = mapper.get_entity_mapping(entity)
        print(f"{entity:25s} → {mapped}")
    
    # Test 5: Statistics
    print("\n\n5. Mapper Statistics")
    print("-" * 80)
    print(f"Total entity mappings: {mapper.get_mapping_count()}")
    
    print("\n" + "=" * 80)
    print("✓ Named Entity Mapping module ready!")
    print("=" * 80)
