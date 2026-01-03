#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Usage Examples for Query Translation Module
Phase 2: Query Processing - Translation Examples

Demonstrates how to use query translation for cross-lingual search.
"""

import sys
import io

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

try:
    from query_translator import (
        QueryTranslator,
        translate_query,
        english_to_bangla,
        bangla_to_english
    )
    HAS_TRANSLATOR = True
except ImportError as e:
    HAS_TRANSLATOR = False
    print(f"⚠ Translation module not available: {e}")
    print("\nInstall a translation library:")
    print("  pip install deep-translator")
    print("  or")
    print("  pip install googletrans==4.0.0-rc1")


def example_1_basic_translation():
    """Example 1: Basic query translation."""
    if not HAS_TRANSLATOR:
        return
    
    print("=" * 80)
    print("Example 1: Basic Query Translation")
    print("=" * 80)
    
    try:
        translator = QueryTranslator()
        
        # English to Bangla
        print("\nEnglish → Bangla:")
        en_query = "coronavirus vaccine news"
        bn_query = translator.english_to_bangla(en_query)
        print(f"  EN: {en_query}")
        print(f"  BN: {bn_query}")
        
        # Bangla to English
        print("\nBangla → English:")
        bn_query = "করোনা ভ্যাকসিন সংবাদ"
        en_query = translator.bangla_to_english(bn_query)
        print(f"  BN: {bn_query}")
        print(f"  EN: {en_query}")
        
    except Exception as e:
        print(f"Error: {e}")


def example_2_convenience_functions():
    """Example 2: Using convenience functions."""
    if not HAS_TRANSLATOR:
        return
    
    print("\n" + "=" * 80)
    print("Example 2: Convenience Functions")
    print("=" * 80)
    
    try:
        # Direct translation
        print("\nUsing convenience functions:")
        
        result = english_to_bangla("cricket match")
        print(f"english_to_bangla('cricket match') = '{result}'")
        
        result = bangla_to_english("ক্রিকেট খেলা")
        print(f"bangla_to_english('ক্রিকেট খেলা') = '{result}'")
        
        result = translate_query("election results", "en", "bn")
        print(f"translate_query('election results', 'en', 'bn') = '{result}'")
        
    except Exception as e:
        print(f"Error: {e}")


def example_3_batch_translation():
    """Example 3: Batch translation of multiple queries."""
    if not HAS_TRANSLATOR:
        return
    
    print("\n" + "=" * 80)
    print("Example 3: Batch Translation")
    print("=" * 80)
    
    try:
        translator = QueryTranslator()
        
        # Batch translate English to Bangla
        en_queries = [
            "coronavirus vaccine",
            "cricket match",
            "election results",
            "weather forecast"
        ]
        
        print("\nBatch translating English → Bangla:")
        bn_queries = translator.batch_translate(en_queries, "en", "bn")
        
        for en, bn in zip(en_queries, bn_queries):
            print(f"  {en:20s} → {bn}")
        
    except Exception as e:
        print(f"Error: {e}")


def example_4_caching():
    """Example 4: Translation caching for performance."""
    if not HAS_TRANSLATOR:
        return
    
    print("\n" + "=" * 80)
    print("Example 4: Translation Caching")
    print("=" * 80)
    
    try:
        translator = QueryTranslator(use_cache=True)
        
        print("\nCache enabled:")
        print(f"Initial cache size: {translator.get_cache_size()}")
        
        # Translate same query multiple times
        query = "coronavirus vaccine"
        print(f"\nTranslating '{query}' three times:")
        
        for i in range(3):
            result = translator.english_to_bangla(query)
            print(f"  {i+1}. {result}")
            print(f"     Cache size: {translator.get_cache_size()}")
        
        # Clear cache
        translator.clear_cache()
        print(f"\nAfter clearing: {translator.get_cache_size()}")
        
    except Exception as e:
        print(f"Error: {e}")


def example_5_clir_pipeline():
    """Example 5: Integration with CLIR query pipeline."""
    if not HAS_TRANSLATOR:
        return
    
    print("\n" + "=" * 80)
    print("Example 5: CLIR Pipeline Integration")
    print("=" * 80)
    
    try:
        # Try to import other modules
        try:
            from query_normalizer import QueryNormalizer
            from language_detector import LanguageDetector
            has_pipeline = True
        except ImportError:
            has_pipeline = False
            print("\n⚠ Full pipeline not available (missing normalizer/detector)")
            return
        
        # Initialize pipeline components
        normalizer = QueryNormalizer()
        detector = LanguageDetector()
        translator = QueryTranslator()
        
        print("\nComplete CLIR Query Pipeline:")
        print("1. Normalize → 2. Detect Language → 3. Translate → 4. Search")
        print("-" * 80)
        
        # Example: English query for cross-lingual search
        user_query = "  COVID-19   vaccine   news  "
        
        # Step 1: Normalize
        normalized = normalizer.normalize(user_query)
        
        # Step 2: Detect language
        source_lang = detector.detect(normalized)
        
        # Step 3: Translate to other language
        target_lang = 'bn' if source_lang == 'en' else 'en'
        translated = translator.translate(normalized, source_lang, target_lang)
        
        print(f"\nUser input:    '{user_query}'")
        print(f"Normalized:    '{normalized}'")
        print(f"Detected lang: {source_lang}")
        print(f"Translated:    '{translated}' ({target_lang})")
        print(f"\n→ Can now search both {source_lang} and {target_lang} indexes")
        
    except Exception as e:
        print(f"Error: {e}")


def example_6_cross_lingual_search():
    """Example 6: Cross-lingual search scenario."""
    if not HAS_TRANSLATOR:
        return
    
    print("\n" + "=" * 80)
    print("Example 6: Cross-Lingual Search Scenario")
    print("=" * 80)
    
    try:
        translator = QueryTranslator()
        
        scenarios = [
            {
                'query': 'coronavirus vaccine',
                'source': 'en',
                'description': 'English query searching Bangla docs'
            },
            {
                'query': 'করোনা ভ্যাকসিন',
                'source': 'bn',
                'description': 'Bangla query searching English docs'
            }
        ]
        
        for scenario in scenarios:
            query = scenario['query']
            source = scenario['source']
            target = 'bn' if source == 'en' else 'en'
            
            translated = translator.translate(query, source, target)
            
            print(f"\n{scenario['description']}:")
            print(f"  Original ({source}):  {query}")
            print(f"  Translated ({target}): {translated}")
            print(f"  → Search {target} index with '{translated}'")
        
    except Exception as e:
        print(f"Error: {e}")


def example_7_translation_with_original():
    """Example 7: Keeping both original and translation."""
    if not HAS_TRANSLATOR:
        return
    
    print("\n" + "=" * 80)
    print("Example 7: Bilingual Search Results")
    print("=" * 80)
    
    try:
        translator = QueryTranslator()
        
        query = "cricket match"
        original, translated = translator.translate_with_original(query, "en", "bn")
        
        print(f"\nOriginal query:    {original}")
        print(f"Translated query:  {translated}")
        print(f"\nCan search both:")
        print(f"  - English index with: '{original}'")
        print(f"  - Bangla index with:  '{translated}'")
        print(f"  - Merge and rank results")
        
    except Exception as e:
        print(f"Error: {e}")


def example_8_backend_selection():
    """Example 8: Selecting translation backend."""
    if not HAS_TRANSLATOR:
        return
    
    print("\n" + "=" * 80)
    print("Example 8: Translation Backend Selection")
    print("=" * 80)
    
    try:
        # Auto-select backend
        translator = QueryTranslator(backend='auto')
        info = translator.get_backend_info()
        
        print(f"\nBackend information:")
        print(f"  Backend:       {info['backend']}")
        print(f"  Cache enabled: {info['cache_enabled']}")
        print(f"  Cache size:    {info['cache_size']}")
        
        # Test translation
        result = translator.english_to_bangla("test")
        print(f"\nTest translation: 'test' → '{result}'")
        
    except Exception as e:
        print(f"Error: {e}")


def example_9_real_world_queries():
    """Example 9: Real-world query translation."""
    if not HAS_TRANSLATOR:
        return
    
    print("\n" + "=" * 80)
    print("Example 9: Real-World Query Translations")
    print("=" * 80)
    
    try:
        translator = QueryTranslator()
        
        real_queries = [
            "COVID-19 vaccine latest news",
            "Bangladesh cricket team",
            "election results 2024",
            "weather forecast Dhaka",
        ]
        
        print("\nTranslating real user queries:")
        print("-" * 80)
        
        for query in real_queries:
            try:
                translated = translator.english_to_bangla(query)
                print(f"\nEN: {query}")
                print(f"BN: {translated}")
            except Exception as e:
                print(f"\nError translating '{query}': {e}")
        
    except Exception as e:
        print(f"Error: {e}")


def main():
    """Run all examples."""
    if not HAS_TRANSLATOR:
        print("\n" + "=" * 80)
        print("Translation module not available")
        print("=" * 80)
        print("\nPlease install a translation library:")
        print("  pip install deep-translator")
        print("  or")
        print("  pip install googletrans==4.0.0-rc1")
        return
    
    print("Query Translation Module - Usage Examples")
    print("Phase 2: Query Processing - Translation\n")
    
    examples = [
        example_1_basic_translation,
        example_2_convenience_functions,
        example_3_batch_translation,
        example_4_caching,
        example_5_clir_pipeline,
        example_6_cross_lingual_search,
        example_7_translation_with_original,
        example_8_backend_selection,
        example_9_real_world_queries,
    ]
    
    for example in examples:
        try:
            example()
        except Exception as e:
            print(f"\n⚠ Error in {example.__name__}: {e}")
    
    print("\n" + "=" * 80)
    print("✓ All Examples Completed!")
    print("=" * 80)
    
    print("\nNext Steps:")
    print("  1. Install translation library if not already installed")
    print("  2. Test with real queries: python query_translator.py")
    print("  3. Run test suite: python test_query_translator.py")
    print("  4. Integrate with BM25 search for cross-lingual retrieval")


if __name__ == "__main__":
    main()
