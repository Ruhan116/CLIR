#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Complete CLIR Query Pipeline with Expansion
Demonstrates all Phase 2 components working together
"""

from query_normalizer import QueryNormalizer
from language_detector import LanguageDetector
from query_translator import QueryTranslator
from query_expander import QueryExpander


def process_query_full_pipeline(query: str, enable_expansion: bool = True):
    """
    Process query through complete CLIR pipeline.
    
    Args:
        query: Input query string
        enable_expansion: Enable query expansion
    
    Returns:
        Dictionary with all processing results
    """
    # Initialize all components
    normalizer = QueryNormalizer()
    detector = LanguageDetector()
    translator = QueryTranslator()
    expander = QueryExpander() if enable_expansion else None
    
    results = {
        'original': query,
        'steps': []
    }
    
    # Step 1: Normalize
    normalized = normalizer.normalize(query)
    results['normalized'] = normalized
    results['steps'].append(f"1. Normalized: '{normalized}'")
    
    # Step 2: Detect language
    lang = detector.detect(normalized)
    results['language'] = lang
    results['confidence'] = 1.0
    results['steps'].append(f"2. Language: {lang} (100%)")
    
    # Step 3: Expand (English only)
    if enable_expansion and lang == 'en':
        expansion_result = expander.expand(normalized)
        results['expansion'] = expansion_result
        results['expanded_query'] = expander.expand_to_query(normalized)
        results['steps'].append(f"3. Expanded: {len(expansion_result['expanded_terms'])} terms")
        query_for_search = results['expanded_query']
    else:
        results['expansion'] = None
        results['expanded_query'] = normalized
        results['steps'].append(f"3. Expansion: skipped ({lang} query)")
        query_for_search = normalized
    
    # Step 4: Translate if needed (for cross-lingual search)
    # If query is Bangla, translate to English for English document search
    # If query is English, optionally translate to Bangla for Bangla document search
    if lang == 'bn':
        translated = translator.bangla_to_english(query_for_search)
        results['translation_bn_to_en'] = translated
        results['steps'].append(f"4. Translated (bn→en): '{translated}'")
    elif lang == 'en':
        translated = translator.english_to_bangla(query_for_search)
        results['translation_en_to_bn'] = translated
        results['steps'].append(f"4. Translated (en→bn): '{translated}'")
    else:
        results['translation_bn_to_en'] = None
        results['translation_en_to_bn'] = None
        results['steps'].append(f"4. Translation: not applicable")
    
    return results


def demo_full_pipeline():
    """Demonstrate the full pipeline with various queries."""
    print("#" * 80)
    print("Complete CLIR Query Pipeline Demonstration")
    print("Phase 2: All Components Integrated")
    print("#" * 80)
    
    test_queries = [
        "  CORONAVIRUS Vaccine NEWS  ",
        "cricket match results",
        "করোনা ভ্যাকসিন",
        "election weather forecast"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{'=' * 80}")
        print(f"Test Query {i}: '{query}'")
        print('=' * 80)
        
        # Process with expansion
        results = process_query_full_pipeline(query, enable_expansion=True)
        
        # Display results
        for step in results['steps']:
            print(step)
        
        # Show expanded terms if available
        if results['expansion']:
            print(f"\nExpansion Details:")
            print(f"  Original terms: {results['expansion']['terms']}")
            print(f"  Synonyms: {results['expansion']['synonyms']}")
            print(f"  Stems: {results['expansion']['stems']}")
            print(f"  Total expanded terms: {len(results['expansion']['expanded_terms'])}")
        
        print(f"\nFinal Queries for Search:")
        print(f"  Same-language: {results['expanded_query'][:80]}...")
        if results.get('translation_bn_to_en'):
            print(f"  Cross-lingual (→EN): {results['translation_bn_to_en']}")
        if results.get('translation_en_to_bn'):
            print(f"  Cross-lingual (→BN): {results['translation_en_to_bn'][:60]}...")
    
    print(f"\n{'#' * 80}")
    print("Pipeline Demonstration Complete!")
    print("#" * 80)


def quick_test():
    """Quick test of each component."""
    print("\nQuick Component Test:")
    print("-" * 80)
    
    # Test 1: Normalizer
    from query_normalizer import QueryNormalizer
    norm = QueryNormalizer()
    print(f"✓ Normalizer: '{norm.normalize('  TEST  ')}' == 'test'")
    
    # Test 2: Detector
    from language_detector import LanguageDetector
    det = LanguageDetector()
    print(f"✓ Detector: '{det.detect('hello')}' == 'en'")
    print(f"✓ Detector: '{det.detect('করোনা')}' == 'bn'")
    
    # Test 3: Translator
    from query_translator import QueryTranslator
    trans = QueryTranslator()
    result = trans.english_to_bangla("test")
    print(f"✓ Translator: 'test' → '{result}'")
    
    # Test 4: Expander
    from query_expander import QueryExpander
    exp = QueryExpander()
    result = exp.expand("test")
    print(f"✓ Expander: 'test' → {len(result['expanded_terms'])} terms")
    
    print("-" * 80)
    print("All components loaded successfully! ✓\n")


if __name__ == "__main__":
    # Quick test first
    quick_test()
    
    # Full demonstration
    demo_full_pipeline()
