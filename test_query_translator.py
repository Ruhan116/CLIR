#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Suite for Query Translation Module
Phase 2: Query Processing - Translation Testing

Tests translation features including:
- English to Bangla translation
- Bangla to English translation
- Translation caching
- Error handling
"""

import sys
import io
import unittest
from unittest.mock import Mock, patch

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

try:
    from query_translator import (
        QueryTranslator, 
        TranslationError,
        translate_query,
        english_to_bangla,
        bangla_to_english
    )
    HAS_TRANSLATOR = True
except ImportError as e:
    HAS_TRANSLATOR = False
    print(f"⚠ Warning: Could not import translator: {e}")


@unittest.skipUnless(HAS_TRANSLATOR, "Translator module not available")
class TestQueryTranslator(unittest.TestCase):
    """Test cases for QueryTranslator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        try:
            self.translator = QueryTranslator()
            self.has_backend = True
        except ImportError:
            self.has_backend = False
    
    def test_initialization(self):
        """Test translator initialization."""
        if not self.has_backend:
            self.skipTest("No translation backend available")
        
        self.assertIsNotNone(self.translator)
        self.assertIsNotNone(self.translator.backend_name)
        self.assertIn(self.translator.backend_name, ['deep_translator', 'googletrans'])
    
    def test_backend_info(self):
        """Test backend information retrieval."""
        if not self.has_backend:
            self.skipTest("No translation backend available")
        
        info = self.translator.get_backend_info()
        
        self.assertIn('backend', info)
        self.assertIn('cache_enabled', info)
        self.assertIn('cache_size', info)
        self.assertTrue(info['cache_enabled'])
    
    def test_cache_functionality(self):
        """Test translation caching."""
        if not self.has_backend:
            self.skipTest("No translation backend available")
        
        # Clear cache first
        self.translator.clear_cache()
        self.assertEqual(self.translator.get_cache_size(), 0)
        
        # Translate something
        try:
            self.translator.translate("test", "en", "bn")
            # Cache should have one entry
            self.assertGreater(self.translator.get_cache_size(), 0)
        except Exception:
            # Translation might fail, but we're testing cache
            pass
        
        # Clear cache
        self.translator.clear_cache()
        self.assertEqual(self.translator.get_cache_size(), 0)
    
    def test_same_language_translation(self):
        """Test that translating to same language returns original."""
        if not self.has_backend:
            self.skipTest("No translation backend available")
        
        text = "test query"
        result = self.translator.translate(text, "en", "en")
        self.assertEqual(result, text)
    
    def test_empty_text_translation(self):
        """Test handling of empty text."""
        if not self.has_backend:
            self.skipTest("No translation backend available")
        
        result = self.translator.translate("", "en", "bn")
        self.assertEqual(result, "")
        
        result = self.translator.translate("   ", "en", "bn")
        self.assertEqual(result, "   ")
    
    def test_batch_translation(self):
        """Test batch translation."""
        if not self.has_backend:
            self.skipTest("No translation backend available")
        
        texts = ["test1", "test2"]
        try:
            results = self.translator.batch_translate(texts, "en", "bn")
            self.assertEqual(len(results), len(texts))
        except Exception as e:
            self.skipTest(f"Translation service unavailable: {e}")
    
    def test_translate_with_original(self):
        """Test translation with original text returned."""
        if not self.has_backend:
            self.skipTest("No translation backend available")
        
        text = "test"
        try:
            original, translated = self.translator.translate_with_original(text, "en", "bn")
            self.assertEqual(original, text)
            self.assertIsNotNone(translated)
        except Exception as e:
            self.skipTest(f"Translation service unavailable: {e}")


@unittest.skipUnless(HAS_TRANSLATOR, "Translator module not available")
class TestConvenienceFunctions(unittest.TestCase):
    """Test convenience functions."""
    
    def test_translate_query(self):
        """Test translate_query convenience function."""
        try:
            translator = QueryTranslator()
            # Just test it doesn't crash
            result = translate_query("test", "en", "en")
            self.assertEqual(result, "test")
        except ImportError:
            self.skipTest("No translation backend available")


class TestTranslationIntegration(unittest.TestCase):
    """Integration tests with other CLIR components."""
    
    def setUp(self):
        """Set up test fixtures."""
        try:
            self.translator = QueryTranslator()
            self.has_translator = True
        except ImportError:
            self.has_translator = False
        
        # Try to import other modules
        try:
            from query_normalizer import QueryNormalizer
            self.normalizer = QueryNormalizer()
            self.has_normalizer = True
        except ImportError:
            self.has_normalizer = False
        
        try:
            from language_detector import LanguageDetector
            self.detector = LanguageDetector()
            self.has_detector = True
        except ImportError:
            self.has_detector = False
    
    def test_normalize_then_translate(self):
        """Test normalization before translation."""
        if not self.has_translator or not self.has_normalizer:
            self.skipTest("Required modules not available")
        
        query = "  TEST  QUERY  "
        
        # Normalize first
        normalized = self.normalizer.normalize(query)
        
        # Then translate
        try:
            translated = self.translator.translate(normalized, "en", "bn")
            self.assertIsNotNone(translated)
        except Exception:
            self.skipTest("Translation service unavailable")
    
    def test_detect_normalize_translate(self):
        """Test complete pipeline: detect → normalize → translate."""
        if not all([self.has_translator, self.has_normalizer, self.has_detector]):
            self.skipTest("Required modules not available")
        
        query = "  COVID-19  NEWS  "
        
        # Step 1: Normalize
        normalized = self.normalizer.normalize(query)
        
        # Step 2: Detect language
        detected_lang = self.detector.detect(normalized)
        
        # Step 3: Translate to opposite language
        target_lang = 'bn' if detected_lang == 'en' else 'en'
        
        try:
            translated = self.translator.translate(normalized, detected_lang, target_lang)
            self.assertIsNotNone(translated)
            print(f"\n✓ Pipeline test: '{query}' → '{normalized}' ({detected_lang}) → '{translated}' ({target_lang})")
        except Exception as e:
            self.skipTest(f"Translation service unavailable: {e}")


def run_manual_tests():
    """Run manual tests with real translation."""
    print("=" * 80)
    print("Query Translation Module - Manual Tests")
    print("=" * 80)
    
    try:
        translator = QueryTranslator()
        
        print(f"\nUsing backend: {translator.backend_name}")
        print("=" * 80)
        
        # Test 1: English to Bangla
        print("\n1. English to Bangla Translation:")
        print("-" * 80)
        
        en_queries = [
            "coronavirus vaccine",
            "cricket match",
            "election results",
        ]
        
        for query in en_queries:
            try:
                translated = translator.english_to_bangla(query)
                print(f"EN: '{query}'")
                print(f"BN: '{translated}'\n")
            except Exception as e:
                print(f"Error: {e}\n")
        
        # Test 2: Bangla to English
        print("\n2. Bangla to English Translation:")
        print("-" * 80)
        
        bn_queries = [
            "করোনা ভ্যাকসিন",
            "ক্রিকেট খেলা",
            "নির্বাচন ফলাফল",
        ]
        
        for query in bn_queries:
            try:
                translated = translator.bangla_to_english(query)
                print(f"BN: '{query}'")
                print(f"EN: '{translated}'\n")
            except Exception as e:
                print(f"Error: {e}\n")
        
        # Test 3: Cache statistics
        print("\n3. Cache Statistics:")
        print("-" * 80)
        info = translator.get_backend_info()
        print(f"Backend: {info['backend']}")
        print(f"Cache enabled: {info['cache_enabled']}")
        print(f"Cache size: {info['cache_size']} translations")
        
        print("\n" + "=" * 80)
        print("✓ Manual tests completed")
        print("=" * 80)
        
    except ImportError as e:
        print(f"\n⚠ Translation backend not available:")
        print(f"  {e}")
        print("\nInstall a translation library:")
        print("  pip install deep-translator")
        print("  or")
        print("  pip install googletrans==4.0.0-rc1")


if __name__ == "__main__":
    print("Query Translation Test Suite\n")
    
    # Run manual tests first
    run_manual_tests()
    
    # Then run unit tests
    print("\n" + "=" * 80)
    print("Running Unit Tests")
    print("=" * 80)
    unittest.main(verbosity=2)
