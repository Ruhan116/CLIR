#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Query Expansion Module for Cross-Lingual Information Retrieval (CLIR)
Implements query expansion using synonyms and root words.

Phase 2: Query Processing - Query Expansion (Advanced)
"""

import sys
from typing import List, Set, Dict, Optional
import re

# Try to import NLTK for English processing
try:
    import nltk
    from nltk.corpus import wordnet
    from nltk.stem import PorterStemmer, WordNetLemmatizer
    HAS_NLTK = True
except ImportError:
    HAS_NLTK = False


class QueryExpander:
    """
    Expand queries using synonyms and root words.
    
    Features:
    - Synonym expansion using WordNet
    - Stemming (root word extraction)
    - Lemmatization (word normalization)
    - Configurable expansion strategies
    """
    
    def __init__(self, 
                 use_synonyms: bool = True,
                 use_stemming: bool = True,
                 use_lemmatization: bool = True,
                 max_synonyms: int = 3):
        """
        Initialize query expander.
        
        Args:
            use_synonyms: Enable synonym expansion
            use_stemming: Enable stemming
            use_lemmatization: Enable lemmatization
            max_synonyms: Maximum synonyms per word
        """
        self.use_synonyms = use_synonyms
        self.use_stemming = use_stemming
        self.use_lemmatization = use_lemmatization
        self.max_synonyms = max_synonyms
        
        # Initialize NLTK tools if available
        if HAS_NLTK:
            self.stemmer = PorterStemmer() if use_stemming else None
            self.lemmatizer = WordNetLemmatizer() if use_lemmatization else None
            
            # Try to download required NLTK data
            self._ensure_nltk_data()
        else:
            self.stemmer = None
            self.lemmatizer = None
    
    def _ensure_nltk_data(self):
        """Ensure required NLTK data is downloaded."""
        required_data = ['wordnet', 'omw-1.4', 'averaged_perceptron_tagger']
        
        for data in required_data:
            try:
                nltk.data.find(f'corpora/{data}')
            except LookupError:
                try:
                    nltk.download(data, quiet=True)
                except:
                    pass
    
    def expand(self, query: str, language: str = 'en') -> Dict[str, List[str]]:
        """
        Expand query with synonyms and root words.
        
        Args:
            query: Input query string
            language: Language code ('en' or 'bn')
            
        Returns:
            Dictionary with expansion results
        """
        if not query or not query.strip():
            return {
                'original': query,
                'terms': [],
                'synonyms': {},
                'stems': {},
                'lemmas': {},
                'expanded_terms': []
            }
        
        # Only expand English queries (Bangla expansion needs different tools)
        if language != 'en':
            return {
                'original': query,
                'terms': query.split(),
                'synonyms': {},
                'stems': {},
                'lemmas': {},
                'expanded_terms': query.split()
            }
        
        # Tokenize query
        terms = self._tokenize(query)
        
        result = {
            'original': query,
            'terms': terms,
            'synonyms': {},
            'stems': {},
            'lemmas': {},
            'expanded_terms': set(terms)
        }
        
        # Process each term
        for term in terms:
            # Get synonyms
            if self.use_synonyms and HAS_NLTK:
                syns = self._get_synonyms(term)
                if syns:
                    result['synonyms'][term] = syns
                    result['expanded_terms'].update(syns)
            
            # Get stem
            if self.use_stemming and self.stemmer:
                stem = self.stemmer.stem(term)
                if stem != term:
                    result['stems'][term] = stem
                    result['expanded_terms'].add(stem)
            
            # Get lemma
            if self.use_lemmatization and self.lemmatizer:
                lemma = self.lemmatizer.lemmatize(term)
                if lemma != term:
                    result['lemmas'][term] = lemma
                    result['expanded_terms'].add(lemma)
        
        result['expanded_terms'] = sorted(list(result['expanded_terms']))
        
        return result
    
    def expand_to_query(self, query: str, language: str = 'en', 
                        separator: str = ' OR ') -> str:
        """
        Expand query and return as search query string.
        
        Args:
            query: Input query
            language: Language code
            separator: Separator for expanded terms
            
        Returns:
            Expanded query string
        """
        result = self.expand(query, language)
        return separator.join(result['expanded_terms'])
    
    def get_synonyms(self, word: str, max_count: Optional[int] = None) -> List[str]:
        """
        Get synonyms for a word.
        
        Args:
            word: Input word
            max_count: Maximum number of synonyms (default: self.max_synonyms)
            
        Returns:
            List of synonyms
        """
        if max_count is None:
            max_count = self.max_synonyms
        
        return self._get_synonyms(word)[:max_count]
    
    def get_stem(self, word: str) -> str:
        """
        Get stem (root form) of a word.
        
        Args:
            word: Input word
            
        Returns:
            Stemmed word
        """
        if self.stemmer:
            return self.stemmer.stem(word)
        return word
    
    def get_lemma(self, word: str) -> str:
        """
        Get lemma (normalized form) of a word.
        
        Args:
            word: Input word
            
        Returns:
            Lemmatized word
        """
        if self.lemmatizer:
            return self.lemmatizer.lemmatize(word)
        return word
    
    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization."""
        # Remove special characters, keep alphanumeric and hyphens
        text = re.sub(r'[^\w\s-]', ' ', text.lower())
        return [t for t in text.split() if t]
    
    def _get_synonyms(self, word: str) -> List[str]:
        """Get synonyms using WordNet."""
        if not HAS_NLTK:
            return []
        
        synonyms = set()
        
        try:
            for syn in wordnet.synsets(word):
                for lemma in syn.lemmas():
                    synonym = lemma.name().replace('_', ' ').lower()
                    if synonym != word.lower():
                        synonyms.add(synonym)
                        if len(synonyms) >= self.max_synonyms:
                            break
                if len(synonyms) >= self.max_synonyms:
                    break
        except:
            pass
        
        return sorted(list(synonyms))[:self.max_synonyms]


# Convenience functions
def expand_query(query: str, language: str = 'en') -> List[str]:
    """
    Quick query expansion.
    
    Args:
        query: Input query
        language: Language code
        
    Returns:
        List of expanded terms
    
    Example:
        >>> expand_query("coronavirus vaccine")
        ['coronavirus', 'vaccine', 'vaccinum', 'vaccination']
    """
    expander = QueryExpander()
    result = expander.expand(query, language)
    return result['expanded_terms']


def get_synonyms(word: str, max_count: int = 3) -> List[str]:
    """
    Get synonyms for a word.
    
    Args:
        word: Input word
        max_count: Maximum synonyms to return
        
    Returns:
        List of synonyms
    """
    expander = QueryExpander(max_synonyms=max_count)
    return expander.get_synonyms(word)


def get_root_words(query: str) -> Dict[str, str]:
    """
    Get root words (stems) for query terms.
    
    Args:
        query: Input query
        
    Returns:
        Dictionary mapping words to their stems
    """
    expander = QueryExpander(use_synonyms=False, use_lemmatization=False)
    result = expander.expand(query)
    return result['stems']


if __name__ == "__main__":
    print("Query Expansion Module - Quick Test")
    print("=" * 80)
    
    if not HAS_NLTK:
        print("\n⚠ NLTK not installed. Install it with:")
        print("  pip install nltk")
        print("\nQuery expansion requires NLTK for English processing.")
        sys.exit(1)
    
    expander = QueryExpander()
    
    # Test 1: Basic expansion
    print("\n1. Basic Query Expansion")
    print("-" * 80)
    
    test_queries = [
        "coronavirus vaccine",
        "cricket match",
        "election results"
    ]
    
    for query in test_queries:
        result = expander.expand(query)
        print(f"\nQuery: '{query}'")
        print(f"Original terms: {result['terms']}")
        print(f"Synonyms: {result['synonyms']}")
        print(f"Stems: {result['stems']}")
        print(f"Expanded terms: {result['expanded_terms']}")
    
    # Test 2: Synonyms only
    print("\n\n2. Synonym Expansion")
    print("-" * 80)
    
    words = ["vaccine", "match", "news"]
    for word in words:
        syns = expander.get_synonyms(word)
        print(f"{word:15s} → {syns}")
    
    # Test 3: Stemming
    print("\n\n3. Stemming (Root Words)")
    print("-" * 80)
    
    words = ["running", "played", "vaccination", "matches"]
    for word in words:
        stem = expander.get_stem(word)
        print(f"{word:15s} → {stem}")
    
    # Test 4: Expanded query string
    print("\n\n4. Expanded Query String")
    print("-" * 80)
    
    query = "coronavirus vaccine news"
    expanded = expander.expand_to_query(query)
    print(f"Original:  {query}")
    print(f"Expanded:  {expanded}")
    
    print("\n" + "=" * 80)
    print("✓ Query expansion module ready!")
    print("=" * 80)
