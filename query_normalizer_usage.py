#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Usage Examples for Query Normalization Module
Phase 2: Query Processing - Normalization Examples

Demonstrates how to use query normalization in CLIR pipeline.
"""

import sys
import io

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from query_normalizer import QueryNormalizer, normalize_query, normalize_for_search


def example_1_basic_normalization():
    """Example 1: Basic query normalization."""
    print("=" * 80)
    print("Example 1: Basic Query Normalization")
    print("=" * 80)
    
    normalizer = QueryNormalizer()
    
    queries = [
        "  COVID-19   Latest   News  ",
        "BANGLADESH   CRICKET   TEAM",
        "করোনা   ভ্যাকসিন   সংবাদ",
        "Election\tResults\n2024",
    ]
    
    for query in queries:
        normalized = normalizer.normalize(query)
        print(f"\nOriginal:   '{query}'")
        print(f"Normalized: '{normalized}'")


def example_2_component_normalization():
    """Example 2: Using individual normalization components."""
    print("\n" + "=" * 80)
    print("Example 2: Individual Normalization Components")
    print("=" * 80)
    
    normalizer = QueryNormalizer()
    
    query = "  COVID-19   VACCINE   NEWS  "
    
    print(f"\nOriginal query: '{query}'")
    print(f"Lowercase only: '{normalizer.normalize_lowercase(query)}'")
    print(f"Whitespace only: '{normalizer.normalize_whitespace(query)}'")
    print(f"Full normalize: '{normalizer.normalize(query)}'")


def example_3_custom_configuration():
    """Example 3: Custom normalization configuration."""
    print("\n" + "=" * 80)
    print("Example 3: Custom Normalization Configuration")
    print("=" * 80)
    
    query = "  COVID-19, Latest News!  "
    
    # Default: lowercase + whitespace
    norm1 = QueryNormalizer()
    print(f"\nOriginal: '{query}'")
    print(f"Default (lowercase + whitespace): '{norm1.normalize(query)}'")
    
    # Only whitespace, preserve case
    norm2 = QueryNormalizer(lowercase=False, normalize_whitespace=True)
    print(f"Whitespace only: '{norm2.normalize(query)}'")
    
    # Strip punctuation too
    norm3 = QueryNormalizer(lowercase=True, normalize_whitespace=True, strip_punctuation=True)
    print(f"With punctuation stripping: '{norm3.normalize(query)}'")


def example_4_batch_processing():
    """Example 4: Batch normalization of multiple queries."""
    print("\n" + "=" * 80)
    print("Example 4: Batch Query Normalization")
    print("=" * 80)
    
    normalizer = QueryNormalizer()
    
    queries = [
        "  COVID-19  ",
        "  করোনা  ভ্যাকসিন  ",
        "BANGLADESH   cricket",
        "  নির্বাচন   ফলাফল  ",
    ]
    
    print("\nNormalizing multiple queries:")
    normalized_queries = normalizer.batch_normalize(queries)
    
    for original, normalized in zip(queries, normalized_queries):
        print(f"'{original}' → '{normalized}'")


def example_5_convenience_functions():
    """Example 5: Using convenience functions."""
    print("\n" + "=" * 80)
    print("Example 5: Convenience Functions")
    print("=" * 80)
    
    queries = [
        "  COVID-19   VACCINE  ",
        "  Bangladesh   Cricket  ",
    ]
    
    print("\nUsing normalize_query():")
    for query in queries:
        normalized = normalize_query(query)
        print(f"'{query}' → '{normalized}'")
    
    print("\nUsing normalize_for_search():")
    for query in queries:
        normalized = normalize_for_search(query)
        print(f"'{query}' → '{normalized}'")


def example_6_clir_pipeline_integration():
    """Example 6: Integration with CLIR query pipeline."""
    print("\n" + "=" * 80)
    print("Example 6: CLIR Query Pipeline Integration")
    print("=" * 80)
    
    # Try to import language detector
    try:
        from language_detector import LanguageDetector
        has_detector = True
    except ImportError:
        print("\n⚠ Language detector not available. Install it to see full pipeline.")
        has_detector = False
        return
    
    # Initialize components
    normalizer = QueryNormalizer()
    detector = LanguageDetector()
    
    queries = [
        "  COVID-19   Latest   News  ",
        "  করোনা   ভ্যাকসিন   সংবাদ  ",
        "  Bangladesh   Cricket   Team  ",
    ]
    
    print("\nComplete Query Processing Pipeline:")
    print("(1) Normalize → (2) Detect Language → (3) Ready for Search")
    print("-" * 80)
    
    for query in queries:
        # Step 1: Normalize
        normalized = normalizer.normalize(query)
        
        # Step 2: Detect language
        language = detector.detect(normalized)
        lang_name = "Bangla" if language == "bn" else "English"
        
        print(f"\nOriginal:   '{query}'")
        print(f"Normalized: '{normalized}'")
        print(f"Language:   {lang_name} ({language})")
        print(f"→ Ready for {lang_name} search index")


def example_7_real_world_queries():
    """Example 7: Real-world query normalization scenarios."""
    print("\n" + "=" * 80)
    print("Example 7: Real-World Query Scenarios")
    print("=" * 80)
    
    normalizer = QueryNormalizer()
    
    # Simulate real user queries with various formatting issues
    scenarios = [
        {
            "query": "   coronavirus    vaccine   bangladesh   ",
            "description": "Extra spaces from voice input"
        },
        {
            "query": "COVID-19\nlatest\nnews",
            "description": "Multi-line paste"
        },
        {
            "query": "ELECTION\tRESULTS\t2024",
            "description": "Tab-separated from spreadsheet"
        },
        {
            "query": "  করোনা  \n  ভ্যাকসিন  ",
            "description": "Bangla with newlines"
        },
    ]
    
    print("\nHandling Various Input Scenarios:")
    print("-" * 80)
    
    for scenario in scenarios:
        query = scenario["query"]
        description = scenario["description"]
        normalized = normalizer.normalize(query)
        
        print(f"\nScenario: {description}")
        print(f"Input:      '{repr(query)}'")
        print(f"Normalized: '{normalized}'")


def example_8_integration_with_search():
    """Example 8: Preparing queries for BM25 search."""
    print("\n" + "=" * 80)
    print("Example 8: Query Preparation for BM25 Search")
    print("=" * 80)
    
    normalizer = QueryNormalizer()
    
    # Simulate user search queries
    user_queries = [
        "  Find articles about COVID-19 vaccine  ",
        "  করোনা ভ্যাকসিন সম্পর্কে তথ্য  ",
        "BANGLADESH   cricket   latest   match",
    ]
    
    print("\nPreparing Queries for BM25 Search:")
    print("-" * 80)
    
    for query in user_queries:
        # Normalize for search
        search_query = normalize_for_search(query)
        
        print(f"\nUser input:    '{query}'")
        print(f"Search query:  '{search_query}'")
        print(f"→ Ready for BM25 tokenization and search")


def main():
    """Run all examples."""
    print("Query Normalization Module - Usage Examples")
    print("Phase 2: Query Processing - Normalization\n")
    
    examples = [
        example_1_basic_normalization,
        example_2_component_normalization,
        example_3_custom_configuration,
        example_4_batch_processing,
        example_5_convenience_functions,
        example_6_clir_pipeline_integration,
        example_7_real_world_queries,
        example_8_integration_with_search,
    ]
    
    for example in examples:
        try:
            example()
        except Exception as e:
            print(f"\n⚠ Error in {example.__name__}: {e}")
    
    print("\n" + "=" * 80)
    print("✓ All examples completed!")
    print("=" * 80)
    
    print("\nNext Steps:")
    print("  1. Run test suite: python test_query_normalizer.py")
    print("  2. Integrate with language detection: from language_detector import LanguageDetector")
    print("  3. Use in BM25 search pipeline: normalize before search")
    print("  4. Implement query translation (next phase)")


if __name__ == "__main__":
    main()
