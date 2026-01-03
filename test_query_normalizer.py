#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Suite for Query Normalization Module
Phase 2: Query Processing - Normalization Testing

Tests all normalization features including:
- Lowercase conversion
- Whitespace normalization
- Bangla text handling
- Mixed language queries
"""

import sys
import io
import unittest

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from query_normalizer import QueryNormalizer, normalize_query, normalize_for_search


class TestQueryNormalizer(unittest.TestCase):
    """Test cases for QueryNormalizer class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.normalizer = QueryNormalizer()
    
    def test_lowercase_english(self):
        """Test lowercase conversion for English text."""
        test_cases = [
            ("HELLO WORLD", "hello world"),
            ("COVID-19 Vaccine", "covid-19 vaccine"),
            ("Bangladesh Cricket", "bangladesh cricket"),
        ]
        
        for input_text, expected in test_cases:
            with self.subTest(input=input_text):
                result = self.normalizer.normalize_lowercase(input_text)
                self.assertEqual(result, expected)
    
    def test_lowercase_bangla(self):
        """Test lowercase conversion preserves Bangla characters."""
        # Bangla doesn't have uppercase/lowercase distinction
        # Should remain unchanged
        bangla_text = "করোনা ভ্যাকসিন সংবাদ"
        result = self.normalizer.normalize_lowercase(bangla_text)
        self.assertEqual(result, bangla_text)
    
    def test_whitespace_normalization(self):
        """Test whitespace normalization."""
        test_cases = [
            ("hello   world", "hello world"),
            ("hello\tworld", "hello world"),
            ("hello\nworld", "hello world"),
            ("  hello  world  ", "hello world"),
            ("multiple   spaces    here", "multiple spaces here"),
        ]
        
        for input_text, expected in test_cases:
            with self.subTest(input=input_text):
                result = self.normalizer.normalize_whitespace(input_text)
                self.assertEqual(result, expected)
    
    def test_whitespace_bangla(self):
        """Test whitespace normalization for Bangla text."""
        test_cases = [
            ("করোনা   ভ্যাকসিন", "করোনা ভ্যাকসিন"),
            ("বাংলাদেশ\t\tক্রিকেট", "বাংলাদেশ ক্রিকেট"),
            ("  নির্বাচন  ফলাফল  ", "নির্বাচন ফলাফল"),
        ]
        
        for input_text, expected in test_cases:
            with self.subTest(input=input_text):
                result = self.normalizer.normalize_whitespace(input_text)
                self.assertEqual(result, expected)
    
    def test_full_normalization_english(self):
        """Test full normalization pipeline for English."""
        test_cases = [
            ("  COVID-19   VACCINE  ", "covid-19 vaccine"),
            ("Bangladesh\tCricket\nTeam", "bangladesh cricket team"),
            ("ELECTION   Results   2024", "election results 2024"),
        ]
        
        for input_text, expected in test_cases:
            with self.subTest(input=input_text):
                result = self.normalizer.normalize(input_text)
                self.assertEqual(result, expected)
    
    def test_full_normalization_bangla(self):
        """Test full normalization pipeline for Bangla."""
        test_cases = [
            ("  করোনা   ভ্যাকসিন  ", "করোনা ভ্যাকসিন"),
            ("বাংলাদেশ\tক্রিকেট", "বাংলাদেশ ক্রিকেট"),
            ("  নির্বাচন  ফলাফল  ২০২৪  ", "নির্বাচন ফলাফল ২০২৪"),
        ]
        
        for input_text, expected in test_cases:
            with self.subTest(input=input_text):
                result = self.normalizer.normalize(input_text)
                self.assertEqual(result, expected)
    
    def test_mixed_language(self):
        """Test normalization with mixed language queries."""
        test_cases = [
            ("  Bangladesh  করোনা  Vaccine  ", "bangladesh করোনা vaccine"),
            ("COVID-19  ভ্যাকসিন   NEWS", "covid-19 ভ্যাকসিন news"),
        ]
        
        for input_text, expected in test_cases:
            with self.subTest(input=input_text):
                result = self.normalizer.normalize(input_text)
                self.assertEqual(result, expected)
    
    def test_empty_input(self):
        """Test handling of empty input."""
        self.assertEqual(self.normalizer.normalize(""), "")
        self.assertEqual(self.normalizer.normalize("   "), "")
        self.assertEqual(self.normalizer.normalize(None), "")
    
    def test_special_characters(self):
        """Test handling of special characters and punctuation."""
        # Default normalizer doesn't strip punctuation
        result = self.normalizer.normalize("COVID-19")
        self.assertEqual(result, "covid-19")
        
        result = self.normalizer.normalize("Hello, World!")
        self.assertEqual(result, "hello, world!")
    
    def test_punctuation_stripping(self):
        """Test optional punctuation stripping."""
        normalizer = QueryNormalizer(strip_punctuation=True)
        
        test_cases = [
            ("Hello, World!", "hello world"),
            ("COVID-19 (coronavirus)", "covid 19 coronavirus"),
            ("What's happening?", "what s happening"),
        ]
        
        for input_text, expected in test_cases:
            with self.subTest(input=input_text):
                result = normalizer.normalize(input_text)
                # Normalize whitespace in expected result
                self.assertEqual(result, " ".join(expected.split()))
    
    def test_batch_normalization(self):
        """Test batch processing of multiple queries."""
        queries = [
            "  COVID-19  ",
            "  করোনা  ভ্যাকসিন  ",
            "BANGLADESH   cricket",
        ]
        
        expected = [
            "covid-19",
            "করোনা ভ্যাকসিন",
            "bangladesh cricket",
        ]
        
        results = self.normalizer.batch_normalize(queries)
        self.assertEqual(results, expected)
    
    def test_custom_configuration(self):
        """Test normalizer with custom configuration."""
        # Only whitespace normalization, no lowercase
        normalizer = QueryNormalizer(lowercase=False, normalize_whitespace=True)
        
        result = normalizer.normalize("  COVID-19   Vaccine  ")
        self.assertEqual(result, "COVID-19 Vaccine")
    
    def test_convenience_functions(self):
        """Test convenience functions."""
        # Test normalize_query
        result = normalize_query("  COVID-19   VACCINE  ")
        self.assertEqual(result, "covid-19 vaccine")
        
        # Test normalize_for_search
        result = normalize_for_search("  Bangladesh   Cricket  ")
        self.assertEqual(result, "bangladesh cricket")


class TestIntegrationWithLanguageDetection(unittest.TestCase):
    """Test normalization integration with language detection."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.normalizer = QueryNormalizer()
        
        # Try to import language detector
        try:
            from language_detector import LanguageDetector
            self.detector = LanguageDetector()
            self.has_detector = True
        except ImportError:
            self.has_detector = False
    
    def test_normalize_then_detect(self):
        """Test normalization followed by language detection."""
        if not self.has_detector:
            self.skipTest("Language detector not available")
        
        test_cases = [
            ("  COVID-19   VACCINE   NEWS  ", "en"),
            ("  করোনা   ভ্যাকসিন   সংবাদ  ", "bn"),
            ("  Bangladesh   Cricket   Team  ", "en"),
        ]
        
        for query, expected_lang in test_cases:
            with self.subTest(query=query):
                # Normalize first
                normalized = self.normalizer.normalize(query)
                
                # Then detect language
                detected = self.detector.detect(normalized)
                
                self.assertEqual(detected, expected_lang)
                print(f"✓ '{query.strip()}' → '{normalized}' → {detected}")


def run_basic_tests():
    """Run basic tests and display results."""
    print("=" * 80)
    print("Query Normalization Module - Basic Tests")
    print("=" * 80)
    
    normalizer = QueryNormalizer()
    
    test_queries = [
        # English queries
        ("  COVID-19   Latest   News  ", "English"),
        ("BANGLADESH   CRICKET   TEAM", "English"),
        ("Election\tResults\n2024", "English"),
        
        # Bangla queries
        ("  করোনা   ভ্যাকসিন   সংবাদ  ", "Bangla"),
        ("বাংলাদেশ\tক্রিকেট\tদল", "Bangla"),
        ("  নির্বাচন  ফলাফল  ", "Bangla"),
        
        # Mixed language
        ("  Bangladesh  করোনা  Vaccine  ", "Mixed"),
    ]
    
    print("\n1. Basic Normalization Tests")
    print("-" * 80)
    
    for query, lang_type in test_queries:
        normalized = normalizer.normalize(query)
        print(f"\n{lang_type} Query:")
        print(f"  Original:   '{query}'")
        print(f"  Normalized: '{normalized}'")
    
    print("\n" + "=" * 80)
    print("2. Component Tests")
    print("-" * 80)
    
    test_text = "  COVID-19   VACCINE   NEWS  "
    print(f"\nOriginal: '{test_text}'")
    print(f"Lowercase only: '{normalizer.normalize_lowercase(test_text)}'")
    print(f"Whitespace only: '{normalizer.normalize_whitespace(test_text)}'")
    print(f"Full normalize: '{normalizer.normalize(test_text)}'")
    
    print("\n" + "=" * 80)
    print("✓ All basic tests completed successfully!")
    print("=" * 80)


if __name__ == "__main__":
    print("Query Normalization Test Suite\n")
    
    # Run basic tests first
    run_basic_tests()
    
    # Run unit tests
    print("\n" + "=" * 80)
    print("Running Unit Tests")
    print("=" * 80)
    unittest.main(verbosity=2)
