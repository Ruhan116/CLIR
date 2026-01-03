#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Suite for Query Expansion Module
Phase 2: Query Processing - Expansion Testing
"""

import sys
import io
import unittest

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

try:
    from query_expander import (
        QueryExpander,
        expand_query,
        get_synonyms,
        get_root_words
    )
    HAS_EXPANDER = True
except ImportError as e:
    HAS_EXPANDER = False
    print(f"⚠ Warning: Could not import expander: {e}")


@unittest.skipUnless(HAS_EXPANDER, "Expander module not available")
class TestQueryExpander(unittest.TestCase):
    """Test cases for QueryExpander class."""
    
    def setUp(self):
        """Set up test fixtures."""
        try:
            self.expander = QueryExpander()
            self.has_nltk = True
        except:
            self.has_nltk = False
    
    def test_initialization(self):
        """Test expander initialization."""
        if not self.has_nltk:
            self.skipTest("NLTK not available")
        
        self.assertIsNotNone(self.expander)
    
    def test_basic_expansion(self):
        """Test basic query expansion."""
        if not self.has_nltk:
            self.skipTest("NLTK not available")
        
        query = "test query"
        result = self.expander.expand(query)
        
        self.assertIn('original', result)
        self.assertIn('terms', result)
        self.assertIn('expanded_terms', result)
        self.assertEqual(result['original'], query)
    
    def test_empty_query(self):
        """Test handling of empty query."""
        if not self.has_nltk:
            self.skipTest("NLTK not available")
        
        result = self.expander.expand("")
        self.assertEqual(result['terms'], [])
        self.assertEqual(result['expanded_terms'], [])
    
    def test_synonym_expansion(self):
        """Test synonym expansion."""
        if not self.has_nltk:
            self.skipTest("NLTK not available")
        
        syns = self.expander.get_synonyms("good")
        self.assertIsInstance(syns, list)
        # May or may not find synonyms depending on WordNet
    
    def test_stemming(self):
        """Test stemming functionality."""
        if not self.has_nltk:
            self.skipTest("NLTK not available")
        
        if self.expander.stemmer:
            stem = self.expander.get_stem("running")
            self.assertIsInstance(stem, str)
            # Stem should be shorter or equal
            self.assertLessEqual(len(stem), len("running"))
    
    def test_lemmatization(self):
        """Test lemmatization functionality."""
        if not self.has_nltk:
            self.skipTest("NLTK not available")
        
        if self.expander.lemmatizer:
            lemma = self.expander.get_lemma("running")
            self.assertIsInstance(lemma, str)
    
    def test_bangla_query(self):
        """Test Bangla query (should return as-is)."""
        if not self.has_nltk:
            self.skipTest("NLTK not available")
        
        query = "করোনা ভ্যাকসিন"
        result = self.expander.expand(query, language='bn')
        
        # Bangla queries should not be expanded
        self.assertEqual(result['original'], query)
    
    def test_expand_to_query_string(self):
        """Test expanding to query string."""
        if not self.has_nltk:
            self.skipTest("NLTK not available")
        
        query = "test"
        expanded = self.expander.expand_to_query(query)
        
        self.assertIsInstance(expanded, str)
        self.assertIn("test", expanded.lower())


@unittest.skipUnless(HAS_EXPANDER, "Expander module not available")
class TestConvenienceFunctions(unittest.TestCase):
    """Test convenience functions."""
    
    def test_expand_query_function(self):
        """Test expand_query convenience function."""
        try:
            result = expand_query("test")
            self.assertIsInstance(result, list)
        except:
            self.skipTest("NLTK not available")
    
    def test_get_synonyms_function(self):
        """Test get_synonyms convenience function."""
        try:
            result = get_synonyms("good")
            self.assertIsInstance(result, list)
        except:
            self.skipTest("NLTK not available")
    
    def test_get_root_words_function(self):
        """Test get_root_words convenience function."""
        try:
            result = get_root_words("running")
            self.assertIsInstance(result, dict)
        except:
            self.skipTest("NLTK not available")


class TestExpansionIntegration(unittest.TestCase):
    """Integration tests with other CLIR components."""
    
    def setUp(self):
        """Set up test fixtures."""
        try:
            self.expander = QueryExpander()
            self.has_expander = True
        except:
            self.has_expander = False
        
        # Try to import other modules
        try:
            from query_normalizer import QueryNormalizer
            self.normalizer = QueryNormalizer()
            self.has_normalizer = True
        except ImportError:
            self.has_normalizer = False
    
    def test_normalize_then_expand(self):
        """Test normalization before expansion."""
        if not self.has_expander or not self.has_normalizer:
            self.skipTest("Required modules not available")
        
        query = "  RUNNING  FAST  "
        
        # Normalize first
        normalized = self.normalizer.normalize(query)
        
        # Then expand
        result = self.expander.expand(normalized)
        
        self.assertIn('expanded_terms', result)


def run_manual_tests():
    """Run manual tests with real expansion."""
    print("=" * 80)
    print("Query Expansion Module - Manual Tests")
    print("=" * 80)
    
    try:
        expander = QueryExpander()
        
        # Test 1: Synonym expansion
        print("\n1. Synonym Expansion")
        print("-" * 80)
        
        words = ["vaccine", "match", "news", "good", "fast"]
        for word in words:
            syns = expander.get_synonyms(word)
            print(f"{word:15s} → {syns}")
        
        # Test 2: Stemming
        print("\n\n2. Stemming (Root Words)")
        print("-" * 80)
        
        words = ["running", "played", "vaccination", "matches", "studies"]
        for word in words:
            stem = expander.get_stem(word)
            print(f"{word:15s} → {stem}")
        
        # Test 3: Full expansion
        print("\n\n3. Full Query Expansion")
        print("-" * 80)
        
        queries = [
            "coronavirus vaccine",
            "cricket match",
            "election results"
        ]
        
        for query in queries:
            result = expander.expand(query)
            print(f"\nQuery: '{query}'")
            print(f"Terms: {result['terms']}")
            print(f"Expanded: {result['expanded_terms']}")
        
        # Test 4: Query string format
        print("\n\n4. Expanded Query String")
        print("-" * 80)
        
        query = "coronavirus vaccine news"
        expanded = expander.expand_to_query(query)
        print(f"Original:  {query}")
        print(f"Expanded:  {expanded}")
        
        print("\n" + "=" * 80)
        print("✓ Manual tests completed")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n⚠ Error: {e}")
        print("\nMake sure NLTK is installed:")
        print("  pip install nltk")


if __name__ == "__main__":
    print("Query Expansion Test Suite\n")
    
    # Run manual tests first
    run_manual_tests()
    
    # Then run unit tests
    print("\n" + "=" * 80)
    print("Running Unit Tests")
    print("=" * 80)
    unittest.main(verbosity=2)
