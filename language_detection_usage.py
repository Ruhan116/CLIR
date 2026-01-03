#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Usage Examples for Language Detection Module
Phase 2: Query Processing - Language Detection (Bangla/English)

Demonstrates integration with CLIR system for automatic query processing.
"""

import sys
import io

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from language_detector import LanguageDetector, detect_language


def example_1_basic_usage():
    """Example 1: Basic language detection"""
    print("="*80)
    print("Example 1: Basic Language Detection")
    print("="*80)
    
    detector = LanguageDetector()
    
    queries = [
        "coronavirus vaccine latest news",
        "করোনা ভ্যাকসিন সর্বশেষ খবর",
        "cricket match Bangladesh vs India",
        "ক্রিকেট ম্যাচ বাংলাদেশ বনাম ভারত",
    ]
    
    for query in queries:
        lang = detector.detect(query)
        lang_name = "Bangla" if lang == "bn" else "English"
        print(f"Query: {query}")
        print(f"Language: {lang_name} ({lang})\n")


def example_2_query_pipeline():
    """Example 2: Query pipeline with language detection"""
    print("\n" + "="*80)
    print("Example 2: Query Pipeline Integration")
    print("="*80)
    
    detector = LanguageDetector()
    
    # Simulate CLIR query processing pipeline
    queries = [
        "election results 2024",
        "নির্বাচন ফলাফল ২০২৪",
    ]
    
    for query in queries:
        print(f"\n{'─'*80}")
        print(f"Processing Query: {query}")
        print(f"{'─'*80}")
        
        # Step 1: Detect language
        lang, confidence, stats = detector.detect_with_confidence(query)
        lang_name = "Bangla" if lang == "bn" else "English"
        
        print(f"1. Language Detection:")
        print(f"   - Detected: {lang_name} ({lang})")
        print(f"   - Confidence: {confidence:.1%}")
        
        # Step 2: Determine search strategy
        if lang == "en":
            search_strategy = "Search English index, optionally translate to Bangla"
            target_index = "english_articles.db"
        else:
            search_strategy = "Search Bangla index, optionally translate to English"
            target_index = "bangla_articles.db"
        
        print(f"2. Search Strategy:")
        print(f"   - {search_strategy}")
        print(f"   - Primary Index: {target_index}")
        
        # Step 3: Query normalization
        normalized_query = query.lower().strip()
        print(f"3. Normalized Query: '{normalized_query}'")
        
        print(f"{'─'*80}")


def example_3_confidence_based_routing():
    """Example 3: Confidence-based query routing"""
    print("\n" + "="*80)
    print("Example 3: Confidence-Based Query Routing")
    print("="*80)
    
    detector = LanguageDetector()
    
    queries = [
        ("Pure English query text", "en", 1.0),
        ("সম্পূর্ণ বাংলা কোয়েরি টেক্সট", "bn", 1.0),
        ("Mixed করোনা query", "mixed", 0.5),
    ]
    
    for query, expected_type, _ in queries:
        lang, confidence, _ = detector.detect_with_confidence(query)
        
        print(f"\nQuery: {query}")
        print(f"Detected: {'Bangla' if lang == 'bn' else 'English'} (confidence: {confidence:.1%})")
        
        # Route based on confidence
        if confidence > 0.8:
            route = f"Direct search in {lang} index"
        elif confidence > 0.5:
            route = f"Primary: {lang} index, Secondary: cross-lingual search"
        else:
            route = "Search both indexes with equal weight"
        
        print(f"Routing: {route}")


def example_4_batch_processing():
    """Example 4: Batch query processing"""
    print("\n" + "="*80)
    print("Example 4: Batch Query Processing")
    print("="*80)
    
    detector = LanguageDetector()
    
    # Simulate a batch of user queries
    user_queries = [
        "weather forecast Dhaka",
        "ঢাকার আবহাওয়ার পূর্বাভাস",
        "stock market news",
        "শেয়ার বাজার খবর",
        "sports cricket update",
        "খেলাধুলা ক্রিকেট আপডেট",
    ]
    
    print("\nProcessing batch of queries:")
    
    # Detect languages for all queries
    languages = detector.batch_detect(user_queries)
    
    # Group by language
    english_queries = []
    bangla_queries = []
    
    for query, lang in zip(user_queries, languages):
        if lang == "en":
            english_queries.append(query)
        else:
            bangla_queries.append(query)
    
    print(f"\nEnglish Queries ({len(english_queries)}):")
    for q in english_queries:
        print(f"  - {q}")
    
    print(f"\nBangla Queries ({len(bangla_queries)}):")
    for q in bangla_queries:
        print(f"  - {q}")
    
    print(f"\nBatch Statistics:")
    print(f"  Total queries: {len(user_queries)}")
    print(f"  English: {len(english_queries)} ({len(english_queries)/len(user_queries)*100:.1f}%)")
    print(f"  Bangla: {len(bangla_queries)} ({len(bangla_queries)/len(user_queries)*100:.1f}%)")


def example_5_mixed_language_handling():
    """Example 5: Mixed language query handling"""
    print("\n" + "="*80)
    print("Example 5: Mixed Language Query Handling")
    print("="*80)
    
    detector = LanguageDetector()
    
    mixed_queries = [
        "Bangladesh করোনা virus update",
        "Dhaka ঢাকা city guide",
        "cricket ক্রিকেট match schedule",
    ]
    
    for query in mixed_queries:
        is_mixed = detector.is_mixed(query)
        distribution = detector.get_language_distribution(query)
        lang = detector.detect(query)
        
        print(f"\nQuery: {query}")
        print(f"Mixed Language: {is_mixed}")
        print(f"Distribution: Bangla={distribution['bangla']:.1f}%, English={distribution['english']:.1f}%")
        print(f"Primary Language: {'Bangla' if lang == 'bn' else 'English'}")
        
        if is_mixed:
            print(f"Strategy: Search both indexes and merge results")
        else:
            print(f"Strategy: Search {lang} index primarily")


def example_6_complete_analysis():
    """Example 6: Complete text analysis"""
    print("\n" + "="*80)
    print("Example 6: Complete Query Analysis")
    print("="*80)
    
    detector = LanguageDetector()
    
    test_query = "বাংলাদেশের অর্থনৈতিক উন্নয়ন এবং ভবিষ্যৎ পরিকল্পনা"
    
    analysis = detector.analyze_text(test_query)
    
    print(f"\nQuery: {test_query}")
    print(f"\nComplete Analysis:")
    print(f"  Language: {analysis['language_name']} ({analysis['language']})")
    print(f"  Confidence: {analysis['confidence']:.1%}")
    print(f"  Is Mixed: {analysis['is_mixed']}")
    print(f"  Word Count: {analysis['word_count']}")
    print(f"  Character Count: {analysis['character_count']}")
    print(f"\nCharacter Statistics:")
    print(f"  Bangla: {analysis['statistics']['bangla']}")
    print(f"  English: {analysis['statistics']['english']}")
    print(f"  Other: {analysis['statistics']['other']}")
    print(f"  Total: {analysis['statistics']['total']}")


def example_7_convenience_functions():
    """Example 7: Quick convenience functions"""
    print("\n" + "="*80)
    print("Example 7: Quick Convenience Functions")
    print("="*80)
    
    queries = [
        "Hello World",
        "হ্যালো ওয়ার্ল্ড",
    ]
    
    print("\nUsing quick detect_language() function:")
    for query in queries:
        lang = detect_language(query)
        print(f"'{query}' → {lang}")
    
    print("\nUsing is_bangla() and is_english() methods:")
    detector = LanguageDetector()
    
    for query in queries:
        is_bn = detector.is_bangla(query)
        is_en = detector.is_english(query)
        print(f"'{query}':")
        print(f"  is_bangla: {is_bn}, is_english: {is_en}")


def main():
    """Run all examples"""
    print("\n" + "="*80)
    print("Language Detection - Usage Examples")
    print("Phase 2: Query Processing - Language Detection (Bangla/English)")
    print("="*80)
    
    examples = [
        example_1_basic_usage,
        example_2_query_pipeline,
        example_3_confidence_based_routing,
        example_4_batch_processing,
        example_5_mixed_language_handling,
        example_6_complete_analysis,
        example_7_convenience_functions,
    ]
    
    for example in examples:
        example()
    
    print("\n" + "="*80)
    print("All Examples Completed!")
    print("="*80)
    print("\nNext Steps:")
    print("  1. Integrate with BM25 search system")
    print("  2. Add query translation (Phase 2)")
    print("  3. Implement query normalization (Phase 2)")
    print("  4. Build complete query processing pipeline")
    print("="*80)


if __name__ == "__main__":
    main()
