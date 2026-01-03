#!/usr/bin/env python3
"""
Query Normalization Module for Cross-Lingual Information Retrieval (CLIR)
Implements text normalization including lowercase conversion and whitespace handling.

Phase 2: Query Processing - Normalization (lowercase, whitespace)
"""

import re
from typing import Optional


class QueryNormalizer:
    """
    Normalize text queries for consistent processing.
    
    Normalization steps:
    1. Lowercase conversion (preserves Bangla characters)
    2. Whitespace normalization (remove extra spaces, tabs, newlines)
    3. Punctuation handling (optional)
    4. Unicode normalization (optional)
    """
    
    def __init__(self, 
                 lowercase: bool = True,
                 normalize_whitespace: bool = True,
                 strip_punctuation: bool = False,
                 unicode_normalize: bool = False):
        """
        Initialize query normalizer with configuration options.
        
        Args:
            lowercase: Convert text to lowercase
            normalize_whitespace: Normalize whitespace (multiple spaces to single)
            strip_punctuation: Remove punctuation marks
            unicode_normalize: Apply unicode normalization (NFC/NFKC)
        """
        self.do_lowercase = lowercase
        self.do_normalize_whitespace = normalize_whitespace
        self.do_strip_punctuation = strip_punctuation
        self.do_unicode_normalize = unicode_normalize
    
    def normalize(self, text: str) -> str:
        """
        Normalize text query with all configured options.
        
        Args:
            text: Input text to normalize
            
        Returns:
            Normalized text
        """
        if not text:
            return ""
        
        result = text
        
        # Step 1: Unicode normalization (if enabled)
        if self.do_unicode_normalize:
            result = self._normalize_unicode(result)
        
        # Step 2: Lowercase conversion
        if self.do_lowercase:
            result = result.lower()
        
        # Step 3: Punctuation stripping (if enabled) - before whitespace normalization
        if self.do_strip_punctuation:
            result = self._strip_punctuation(result)
        
        # Step 4: Whitespace normalization (always do this if punctuation was stripped or if enabled)
        if self.do_normalize_whitespace or self.do_strip_punctuation:
            result = self._normalize_whitespace(result)
        
        return result.strip()
    
    def normalize_lowercase(self, text: str) -> str:
        """
        Convert text to lowercase.
        Works with both English and Bangla text.
        
        Args:
            text: Input text
            
        Returns:
            Lowercase text
        """
        return text.lower() if text else ""
    
    def normalize_whitespace(self, text: str) -> str:
        """
        Normalize whitespace in text:
        - Replace multiple spaces with single space
        - Replace tabs with spaces
        - Replace newlines with spaces
        - Strip leading/trailing whitespace
        
        Args:
            text: Input text
            
        Returns:
            Text with normalized whitespace
        """
        if not text:
            return ""
        
        return self._normalize_whitespace(text).strip()
    
    def _normalize_whitespace(self, text: str) -> str:
        """Internal whitespace normalization."""
        # Replace tabs and newlines with spaces
        text = text.replace('\t', ' ').replace('\n', ' ').replace('\r', ' ')
        
        # Replace multiple spaces with single space
        text = re.sub(r'\s+', ' ', text)
        
        return text
    
    def _normalize_unicode(self, text: str) -> str:
        """
        Normalize Unicode characters.
        Uses NFC (Canonical Decomposition, followed by Canonical Composition).
        """
        import unicodedata
        return unicodedata.normalize('NFC', text)
    
    def _strip_punctuation(self, text: str) -> str:
        """
        Remove common punctuation marks.
        Preserves Bangla punctuation and diacritics.
        """
        # Common English punctuation
        punctuation = r'[.,;:!?"\'\-_()[\]{}]'
        return re.sub(punctuation, ' ', text)
    
    def batch_normalize(self, texts: list) -> list:
        """
        Normalize multiple text queries.
        
        Args:
            texts: List of text strings
            
        Returns:
            List of normalized text strings
        """
        return [self.normalize(text) for text in texts]


# Convenience function for quick normalization
def normalize_query(text: str, 
                    lowercase: bool = True, 
                    whitespace: bool = True) -> str:
    """
    Quick normalization function for single queries.
    
    Args:
        text: Input text to normalize
        lowercase: Apply lowercase conversion
        whitespace: Apply whitespace normalization
        
    Returns:
        Normalized text
    
    Example:
        >>> normalize_query("  COVID-19   Vaccine  ")
        'covid-19 vaccine'
        
        >>> normalize_query("করোনা   ভ্যাকসিন  ")
        'করোনা ভ্যাকসিন'
    """
    normalizer = QueryNormalizer(lowercase=lowercase, normalize_whitespace=whitespace)
    return normalizer.normalize(text)


def normalize_for_search(text: str) -> str:
    """
    Normalize query specifically for search operations.
    Applies lowercase and whitespace normalization.
    
    Args:
        text: Input query text
        
    Returns:
        Search-ready normalized text
    
    Example:
        >>> normalize_for_search("   Bangladesh   Cricket  Team   ")
        'bangladesh cricket team'
    """
    return normalize_query(text, lowercase=True, whitespace=True)


if __name__ == "__main__":
    # Quick test
    print("Query Normalization Module - Quick Test")
    print("=" * 60)
    
    normalizer = QueryNormalizer()
    
    test_queries = [
        "  COVID-19   Latest   News  ",
        "করোনা  ভ্যাকসিন   সংবাদ",
        "Bangladesh\tCricket\nTeam",
        "  ELECTION  results  2024  ",
    ]
    
    print("\nTest Normalization:")
    for query in test_queries:
        normalized = normalizer.normalize(query)
        print(f"Original:   '{query}'")
        print(f"Normalized: '{normalized}'")
        print()
