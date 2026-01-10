"""
Fuzzy Matching Module for Cross-Lingual Information Retrieval (CLIR)

This module provides fuzzy matching techniques including:
- Edit Distance (Levenshtein) for typo correction
- Jaccard Similarity for character/word overlap matching
- Transliteration support for cross-script retrieval
- Hybrid search combining multiple methods with BM25

Main Classes:
- FuzzyMatcher: Core fuzzy matching algorithms
- CLIRSearch: Integrated search interface

Example Usage:
    >>> from fuzzy_matching import FuzzyMatcher, CLIRSearch
    >>> 
    >>> clir = CLIRSearch(documents=docs)
    >>> results = clir.hybrid_search("Bangaldesh", top_k=10)
"""

__version__ = "1.0.0"
__author__ = "CLIR System"

from .fuzzy_matcher import FuzzyMatcher
from .clir_search import CLIRSearch

__all__ = ['FuzzyMatcher', 'CLIRSearch']
