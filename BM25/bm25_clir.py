#!/usr/bin/env python3
"""BM25 Implementation for Cross-Lingual Information Retrieval (CLIR).

This module provides comprehensive BM25 search functionality for the combined
English and Bangla news dataset. It supports:
- Mono-lingual search (English-to-English, Bangla-to-Bangla)
- Cross-lingual search with translation (English-to-Bangla, Bangla-to-English)
- Automatic language detection
- Query translation
- Score normalization across languages
- Result merging from multiple languages
"""

import sqlite3
import re
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from rank_bm25 import BM25Okapi
import numpy as np

# Try to import translation libraries
try:
    from googletrans import Translator
    HAS_GOOGLETRANS = True
except ImportError:
    HAS_GOOGLETRANS = False

try:
    from deep_translator import GoogleTranslator
    HAS_DEEP_TRANSLATOR = True
except ImportError:
    HAS_DEEP_TRANSLATOR = False


@dataclass
class Article:
    """Article data structure."""
    id: int
    source: str
    title: str
    body: str
    url: str
    date: str
    language: str


class BM25CLIR:
    """BM25-based Cross-Lingual Information Retrieval System with full CLIR features."""
    
    def __init__(self, db_path: str = None, enable_translation: bool = True):
        """Initialize the BM25 CLIR system.
        
        Args:
            db_path: Path to the SQLite database. Defaults to combined_dataset.db
            enable_translation: Enable automatic query translation (requires translation library)
        """
        if db_path is None:
            script_dir = Path(__file__).parent.parent
            db_path = script_dir / "dataset_enhanced" / "combined_dataset.db"
        
        self.db_path = Path(db_path)
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found: {self.db_path}")
        
        # Storage for articles and BM25 models
        self.articles: Dict[str, List[Article]] = {"en": [], "bn": []}
        self.tokenized_docs: Dict[str, List[List[str]]] = {"en": [], "bn": []}
        self.bm25_models: Dict[str, BM25Okapi] = {}
        
        # Translation settings
        self.enable_translation = enable_translation and (HAS_GOOGLETRANS or HAS_DEEP_TRANSLATOR)
        self.translator = None
        
        if self.enable_translation:
            if HAS_DEEP_TRANSLATOR:
                # Preferred: deep_translator (more reliable)
                self.translator = "deep_translator"
                print("✓ Using deep_translator for query translation")
            elif HAS_GOOGLETRANS:
                # Fallback: googletrans
                self.translator = Translator()
                print("✓ Using googletrans for query translation")
        else:
            if enable_translation:
                print("⚠ Translation disabled: Install 'deep-translator' or 'googletrans' for cross-lingual search")
        
        # Load articles from database
        self._load_articles()
        self.tokenized_docs: Dict[str, List[List[str]]] = {"en": [], "bn": []}
        self.bm25_models: Dict[str, BM25Okapi] = {}
        
        # Load articles from database
        self._load_articles()
    
    def _load_articles(self):
        """Load articles from the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Load English articles
        cursor.execute("""
            SELECT id, source, title, body, url, date, language
            FROM articles
            WHERE language = 'en' AND body IS NOT NULL AND body != ''
        """)
        for row in cursor.fetchall():
            self.articles["en"].append(Article(*row))
        
        # Load Bangla articles
        cursor.execute("""
            SELECT id, source, title, body, url, date, language
            FROM articles
            WHERE language = 'bn' AND body IS NOT NULL AND body != ''
        """)
        for row in cursor.fetchall():
            self.articles["bn"].append(Article(*row))
        
        conn.close()
        
        print(f"Loaded {len(self.articles['en'])} English articles")
        print(f"Loaded {len(self.articles['bn'])} Bangla articles")
    
    def detect_language(self, text: str) -> str:
        """Detect if text is Bangla or English.
        
        Uses Unicode ranges to detect Bangla script (U+0980 to U+09FF).
        
        Args:
            text: Text to analyze
            
        Returns:
            "bn" for Bangla, "en" for English
        """
        # Count Bangla Unicode characters
        bangla_chars = sum(1 for char in text if '\u0980' <= char <= '\u09FF')
        # Count English alphabetic characters
        english_chars = sum(1 for char in text if char.isalpha() and ord(char) < 128)
        
        # Determine language based on character count
        if bangla_chars > english_chars:
            return "bn"
        else:
            return "en"
    
    def translate_query(self, query: str, target_lang: str) -> Optional[str]:
        """Translate query to target language.
        
        Args:
            query: Query text to translate
            target_lang: Target language code ("en" or "bn")
            
        Returns:
            Translated query or None if translation fails
        """
        if not self.enable_translation:
            return None
        
        try:
            source_lang = "bn" if target_lang == "en" else "en"
            
            if self.translator == "deep_translator":
                # Use deep_translator
                translator = GoogleTranslator(source=source_lang, target=target_lang)
                return translator.translate(query)
            elif isinstance(self.translator, object):
                # Use googletrans
                result = self.translator.translate(query, src=source_lang, dest=target_lang)
                return result.text
        except Exception as e:
            print(f"⚠ Translation failed: {e}")
            return None
    
    def _tokenize_english(self, text: str) -> List[str]:
        """Tokenize English text.
        
        Args:
            text: English text to tokenize
            
        Returns:
            List of tokens (lowercase, alphanumeric)
        """
        # Convert to lowercase and split on non-alphanumeric
        tokens = re.findall(r'\b[a-z0-9]+\b', text.lower())
        # Filter out very short tokens
        return [t for t in tokens if len(t) > 1]
    
    def _tokenize_bangla(self, text: str) -> List[str]:
        """Tokenize Bangla text.
        
        Args:
            text: Bangla text to tokenize
            
        Returns:
            List of tokens (split on whitespace and cleaned)
        """
        import re
        
        # Remove only specific punctuation, keep all Bangla Unicode characters
        # Remove: periods, commas, quotes, brackets, etc. but keep Bangla text intact
        punctuation = r'[।॥,.;:!?\'\"()\[\]{}<>@#$%^&*+=|\\\/\-_—–''""…\n\r\t]'
        text = re.sub(punctuation, ' ', text)
        
        # Split on whitespace
        tokens = text.strip().split()
        
        # Filter out very short tokens, empty tokens, and pure numbers
        tokens = [t.strip() for t in tokens if len(t) > 1 and not t.isdigit()]
        
        return tokens
    
    def build_index(self, language: str = "both"):
        """Build BM25 index for specified language(s).
        
        Args:
            language: "en", "bn", or "both" (default)
        """
        languages = ["en", "bn"] if language == "both" else [language]
        
        for lang in languages:
            print(f"\nBuilding BM25 index for {lang}...")
            
            # Tokenize all documents
            tokenizer = self._tokenize_english if lang == "en" else self._tokenize_bangla
            self.tokenized_docs[lang] = []
            
            for article in self.articles[lang]:
                # Combine title and body for richer context
                full_text = f"{article.title} {article.body}"
                tokens = tokenizer(full_text)
                self.tokenized_docs[lang].append(tokens)
            
            # Build BM25 model
            self.bm25_models[lang] = BM25Okapi(self.tokenized_docs[lang])
            print(f"✓ Indexed {len(self.tokenized_docs[lang])} {lang} documents")
    
    def _normalize_scores(self, scores: np.ndarray) -> np.ndarray:
        """Normalize BM25 scores to [0, 1] range using min-max normalization.
        
        Args:
            scores: Array of BM25 scores
            
        Returns:
            Normalized scores
        """
        if len(scores) == 0:
            return scores
        
        max_score = np.max(scores)
        min_score = np.min(scores)
        
        if max_score == min_score:
            return np.ones_like(scores)
        
        return (scores - min_score) / (max_score - min_score)
    
    def search(self, 
               query: str, 
               language: str = "en",
               top_k: int = 10,
               normalize_scores: bool = False) -> List[Tuple[Article, float]]:
        """Search for articles using BM25.
        
        Args:
            query: Search query
            language: Language to search in ("en" or "bn")
            top_k: Number of top results to return
            normalize_scores: Whether to normalize scores to [0, 1] range
            
        Returns:
            List of (Article, score) tuples, sorted by relevance
        """
        if language not in self.bm25_models:
            raise ValueError(f"BM25 index not built for language: {language}")
        
        # Tokenize query
        tokenizer = self._tokenize_english if language == "en" else self._tokenize_bangla
        query_tokens = tokenizer(query)
        
        if not query_tokens:
            print("Warning: Query produced no tokens")
            return []
        
        # Get BM25 scores
        scores = self.bm25_models[language].get_scores(query_tokens)
        
        # Normalize scores if requested
        if normalize_scores:
            scores = self._normalize_scores(scores)
        
        # Get top-k results, but get more candidates to filter
        top_indices = np.argsort(scores)[::-1][:top_k * 5]  # Get 5x results for filtering
        
        results = []
        seen_urls = set()  # Track URLs to avoid duplicates
        
        for idx in top_indices:
            if scores[idx] > 0:  # Only return positive scores
                article = self.articles[language][idx]
                
                # Skip duplicate URLs
                if article.url in seen_urls:
                    continue
                seen_urls.add(article.url)
                
                # Verify article actually contains at least one query term
                article_text = f"{article.title} {article.body}".lower()
                article_tokens = set(tokenizer(article_text))
                query_tokens_set = set(query_tokens)
                
                # Check if any query token appears in article
                if query_tokens_set & article_tokens:  # Set intersection
                    results.append((article, float(scores[idx])))
                    
                    # Stop when we have enough results
                    if len(results) >= top_k:
                        break
        
        return results
    
    def search_cross_lingual(self,
                            query: str,
                            auto_detect: bool = True,
                            top_k: int = 10,
                            merge_results: bool = True) -> Dict[str, any]:
        """Search across both languages with automatic translation (CLIR).
        
        This is the main CLIR search function that:
        1. Detects query language automatically (if enabled)
        2. Searches in the same language
        3. Translates query and searches in the other language
        4. Merges and normalizes results from both languages
        
        Args:
            query: Search query
            auto_detect: Automatically detect query language
            top_k: Total number of results to return
            merge_results: Merge and sort results by normalized scores
            
        Returns:
            Dictionary with:
                - query_language: Detected language
                - translated_query: Translation (if available)
                - results: Merged results or separate results by language
                - same_lang_count: Number of results in query language
                - cross_lang_count: Number of cross-lingual results
        """
        # Detect query language
        query_lang = self.detect_language(query) if auto_detect else "en"
        target_lang = "en" if query_lang == "bn" else "bn"
        
        print(f"🔍 Query language detected: {'Bangla' if query_lang == 'bn' else 'English'}")
        
        # Search in same language
        same_lang_results = self.search(query, language=query_lang, top_k=top_k, normalize_scores=True)
        print(f"✓ Found {len(same_lang_results)} {query_lang.upper()} results")
        
        # Translate and search in other language
        cross_lang_results = []
        translated_query = None
        
        if self.enable_translation:
            translated_query = self.translate_query(query, target_lang)
            if translated_query:
                print(f"📝 Translated query: {translated_query}")
                cross_lang_results = self.search(translated_query, language=target_lang, top_k=top_k, normalize_scores=True)
                print(f"✓ Found {len(cross_lang_results)} {target_lang.upper()} results (cross-lingual)")
            else:
                print(f"⚠ Could not translate query to {target_lang.upper()}")
        else:
            print("⚠ Translation disabled - cross-lingual search not available")
        
        # Merge results if requested
        if merge_results:
            # Combine all results with language tags
            all_results = []
            for article, score in same_lang_results:
                all_results.append((article, score, query_lang))
            for article, score in cross_lang_results:
                all_results.append((article, score, target_lang))
            
            # Sort by normalized score
            all_results.sort(key=lambda x: x[1], reverse=True)
            all_results = all_results[:top_k]
            
            # Convert back to (article, score) format
            merged_results = [(article, score) for article, score, _ in all_results]
            
            return {
                "query_language": query_lang,
                "translated_query": translated_query,
                "results": merged_results,
                "same_lang_count": sum(1 for _, _, lang in all_results if lang == query_lang),
                "cross_lang_count": sum(1 for _, _, lang in all_results if lang == target_lang),
            }
        else:
            return {
                "query_language": query_lang,
                "translated_query": translated_query,
                "results": {query_lang: same_lang_results, target_lang: cross_lang_results},
                "same_lang_count": len(same_lang_results),
                "cross_lang_count": len(cross_lang_results),
            }
    
    def search_multilingual(self,
                           query: str,
                           query_lang: str = None,
                           top_k: int = 10,
                           results_per_lang: Optional[int] = None) -> Dict[str, List[Tuple[Article, float]]]:
        """Search across both languages.
        
        Args:
            query: Search query
            query_lang: Language of the query ("en" or "bn")
            top_k: Total number of results to return
            results_per_lang: Number of results per language (if None, returns top_k total)
            
        Returns:
            Dictionary with language keys and list of (Article, score) results
        """
        results = {}
        
        if results_per_lang is not None:
            # Get specified number from each language
            results["en"] = self.search(query, "en", results_per_lang)
            results["bn"] = self.search(query, "bn", results_per_lang)
        else:
            # Get all results and merge
            en_results = self.search(query, "en", top_k * 2)
            bn_results = self.search(query, "bn", top_k * 2)
            
            # Merge and sort by score
            all_results = []
            for article, score in en_results:
                all_results.append(("en", article, score))
            for article, score in bn_results:
                all_results.append(("bn", article, score))
            
            all_results.sort(key=lambda x: x[2], reverse=True)
            all_results = all_results[:top_k]
            
            # Split back into languages
            results = {"en": [], "bn": []}
            for lang, article, score in all_results:
                results[lang].append((article, score))
        
        return results
    
    def get_article_by_id(self, article_id: int, language: str) -> Optional[Article]:
        """Retrieve a specific article by ID.
        
        Args:
            article_id: Article ID
            language: Article language
            
        Returns:
            Article object or None if not found
        """
        for article in self.articles[language]:
            if article.id == article_id:
                return article
        return None
    
    def get_statistics(self) -> Dict:
        """Get dataset statistics.
        
        Returns:
            Dictionary containing various statistics
        """
        stats = {
            "total_articles": len(self.articles["en"]) + len(self.articles["bn"]),
            "english_articles": len(self.articles["en"]),
            "bangla_articles": len(self.articles["bn"]),
            "indexed_languages": list(self.bm25_models.keys()),
        }
        
        # Source distribution
        sources = {}
        for lang in ["en", "bn"]:
            for article in self.articles[lang]:
                sources[article.source] = sources.get(article.source, 0) + 1
        stats["sources"] = sources
        
        return stats
    
    def print_results(self, 
                     results: List[Tuple[Article, float]], 
                     max_body_length: int = 150,
                     show_url: bool = True,
                     show_snippet: bool = True,
                     highlight_terms: List[str] = None):
        """Pretty print search results with language indicators.
        
        Args:
            results: List of (Article, score) tuples
            max_body_length: Maximum body text length to display
            show_url: Whether to show article URLs
            show_snippet: Whether to show article snippet
            highlight_terms: Optional list of terms to find in article
        """
        if not results:
            print("No results found.")
            return
        
        print(f"\n{'='*80}")
        print(f"Found {len(results)} results")
        print(f"{'='*80}\n")
        
        for i, (article, score) in enumerate(results, 1):
            lang_name = "Bangla" if article.language == "bn" else "English"
            print(f"{i}. [{lang_name}] {article.title}")
            print(f"   Score: {score:.4f}")
            print(f"   Source: {article.source}")
            
            if show_url:
                print(f"   URL: {article.url}")
            
            if show_snippet:
                # If highlight terms provided, show context around them
                if highlight_terms:
                    article_text = article.body
                    found_term = False
                    
                    for term in highlight_terms:
                        if term in article_text:
                            idx = article_text.find(term)
                            start = max(0, idx - 75)
                            end = min(len(article_text), idx + 75)
                            snippet = article_text[start:end]
                            
                            # Mark where we started from middle
                            if start > 0:
                                snippet = "..." + snippet
                            if end < len(article_text):
                                snippet = snippet + "..."
                            
                            print(f"   Context ('{term}'): {snippet}")
                            found_term = True
                            break
                    
                    # If no term found in body, show regular snippet
                    if not found_term:
                        snippet = article.body[:max_body_length].strip()
                        if len(article.body) > max_body_length:
                            snippet += "..."
                        print(f"   Snippet: {snippet}")
                else:
                    # Regular snippet
                    snippet = article.body[:max_body_length].strip()
                    if len(article.body) > max_body_length:
                        snippet += "..."
                    print(f"   Snippet: {snippet}")
            
            print(f"   {'-'*76}")


def main():
    """Example usage with full CLIR features."""
    print("="*80)
    print("BM25 Cross-Lingual Information Retrieval System")
    print("With Language Detection, Translation & Score Normalization")
    print("="*80)
    
    # Initialize the system
    clir = BM25CLIR(enable_translation=True)
    
    # Build indexes
    clir.build_index("both")
    
    # Print statistics
    print("\n" + "="*80)
    print("Dataset Statistics")
    print("="*80)
    stats = clir.get_statistics()
    print(f"Total articles: {stats['total_articles']}")
    print(f"English: {stats['english_articles']}, Bangla: {stats['bangla_articles']}")
    print(f"Indexed languages: {stats['indexed_languages']}")
    
    # Test 1: Bangla Query with Cross-Lingual Search
    print("\n" + "="*80)
    print("TEST 1: Bangla Query with Cross-Lingual Search")
    print("="*80)
    bangla_query = "করোনা ভ্যাকসিন"
    result = clir.search_cross_lingual(bangla_query, auto_detect=True, top_k=5, merge_results=True)
    
    print(f"\nQuery: {bangla_query}")
    print(f"Detected language: {'Bangla' if result['query_language'] == 'bn' else 'English'}")
    if result['translated_query']:
        print(f"Translated to: {result['translated_query']}")
    print(f"Same language results: {result['same_lang_count']}")
    print(f"Cross-lingual results: {result['cross_lang_count']}")
    
    # Show results with context highlighting
    results_to_show = result['results'][:5]
    highlight_terms = [bangla_query] + ([result['translated_query']] if result['translated_query'] else [])
    
    print(f"\n{'='*80}")
    print(f"Found {len(results_to_show)} results")
    print(f"{'='*80}\n")
    
    for i, (article, score) in enumerate(results_to_show, 1):
        lang_name = "Bangla" if article.language == "bn" else "English"
        print(f"{i}. [{lang_name}] {article.title}")
        print(f"   Score: {score:.4f}")
        print(f"   Source: {article.source}")
        
        # Find and show context for query terms
        article_text = article.body
        found = False
        
        # Check for Bangla terms
        if article.language == "bn":
            for term in ["করোনা", "ভ্যাকসিন"]:
                if term in article_text:
                    idx = article_text.find(term)
                    context = article_text[max(0, idx-60):min(len(article_text), idx+90)]
                    if idx > 60:
                        context = "..." + context
                    if idx + 90 < len(article_text):
                        context = context + "..."
                    print(f"   Contains '{term}': {context}")
                    found = True
                    break
        else:
            # Check for English terms
            for term in ["corona", "vaccine", "covid"]:
                if term.lower() in article_text.lower():
                    idx = article_text.lower().find(term.lower())
                    context = article_text[max(0, idx-60):min(len(article_text), idx+90)]
                    if idx > 60:
                        context = "..." + context
                    if idx + 90 < len(article_text):
                        context = context + "..."
                    print(f"   Contains '{term}': {context}")
                    found = True
                    break
        
        if not found:
            snippet = article.body[:120]
            if len(article.body) > 120:
                snippet += "..."
            print(f"   Snippet: {snippet}")
        
        print(f"   {'-'*76}")
    
    # Test 2: English Query with Cross-Lingual Search
    print("\n" + "="*80)
    print("TEST 2: English Query with Cross-Lingual Search")
    print("="*80)
    english_query = "election results"
    result = clir.search_cross_lingual(english_query, auto_detect=True, top_k=5, merge_results=True)
    
    print(f"\nQuery: {english_query}")
    print(f"Detected language: {'Bangla' if result['query_language'] == 'bn' else 'English'}")
    if result['translated_query']:
        print(f"Translated to: {result['translated_query']}")
    print(f"Same language results: {result['same_lang_count']}")
    print(f"Cross-lingual results: {result['cross_lang_count']}")
    
    # Show results with context
    results_to_show = result['results'][:5]
    
    print(f"\n{'='*80}")
    print(f"Found {len(results_to_show)} results")
    print(f"{'='*80}\n")
    
    for i, (article, score) in enumerate(results_to_show, 1):
        lang_name = "Bangla" if article.language == "bn" else "English"
        print(f"{i}. [{lang_name}] {article.title}")
        print(f"   Score: {score:.4f}")
        print(f"   Source: {article.source}")
        
        # Show snippet with first 120 chars
        snippet = article.body[:120]
        if len(article.body) > 120:
            snippet += "..."
        print(f"   Snippet: {snippet}")
        print(f"   {'-'*76}")
    
    # Test 3: Language Detection Demo
    print("\n" + "="*80)
    print("TEST 3: Language Detection Demo")
    print("="*80)
    test_queries = [
        "climate change",
        "শিক্ষা ব্যবস্থা",
        "cricket match",
        "অর্থনীতি",
    ]
    
    for query in test_queries:
        detected = clir.detect_language(query)
        lang_name = "Bangla" if detected == "bn" else "English"
        print(f"'{query}' → Detected: {lang_name}")
    
    print("\n" + "="*80)
    print("All CLIR features demonstrated!")
    print("="*80)
    print("\nFeatures included:")
    print("✓ 1. Dual Language Support (separate BM25 indexes)")
    print("✓ 2. Automatic Language Detection")
    print("✓ 3. Query Translation (EN ↔ BN)")
    print("✓ 4. Proper Tokenization (different for EN and BN)")
    print("✓ 5. Score Normalization (comparable across languages)")
    print("✓ 6. Result Merging (combined and sorted by score)")
    print("\nNote: Install 'deep-translator' for translation:")
    print("  pip install deep-translator")


if __name__ == "__main__":
    main()
