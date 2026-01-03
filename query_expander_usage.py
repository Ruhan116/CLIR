#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Query Expansion Usage Examples
Phase 2: Query Processing - Expansion Module
"""

from query_expander import (
    QueryExpander,
    expand_query,
    get_synonyms,
    get_root_words
)


def example_1_basic_expansion():
    """Example 1: Basic query expansion with synonyms."""
    print("\n" + "=" * 80)
    print("Example 1: Basic Query Expansion")
    print("=" * 80)
    
    expander = QueryExpander()
    
    queries = [
        "coronavirus vaccine",
        "cricket match results",
        "election news"
    ]
    
    for query in queries:
        result = expander.expand(query)
        print(f"\nQuery: '{query}'")
        print(f"  Original terms: {result['terms']}")
        print(f"  Expanded terms: {result['expanded_terms'][:8]}...")  # Show first 8


def example_2_synonym_only():
    """Example 2: Get synonyms for individual words."""
    print("\n" + "=" * 80)
    print("Example 2: Synonym Expansion Only")
    print("=" * 80)
    
    expander = QueryExpander()
    
    words = ["vaccine", "match", "news", "good", "fast", "large"]
    
    for word in words:
        syns = expander.get_synonyms(word, max_synonyms=3)
        print(f"\n{word:15s} → {syns}")


def example_3_stemming():
    """Example 3: Get root words using stemming."""
    print("\n" + "=" * 80)
    print("Example 3: Stemming (Root Words)")
    print("=" * 80)
    
    expander = QueryExpander()
    
    words = [
        "running", "played", "matches",
        "vaccination", "studying", "elections"
    ]
    
    for word in words:
        stem = expander.get_stem(word)
        print(f"{word:15s} → {stem}")


def example_4_expanded_query_string():
    """Example 4: Generate expanded query string for search."""
    print("\n" + "=" * 80)
    print("Example 4: Expanded Query String (OR format)")
    print("=" * 80)
    
    expander = QueryExpander()
    
    queries = [
        "coronavirus vaccine",
        "cricket match",
        "election results"
    ]
    
    for query in queries:
        expanded = expander.expand_to_query(query, separator=" OR ")
        print(f"\nOriginal:  {query}")
        print(f"Expanded:  {expanded[:80]}...")  # Show first 80 chars


def example_5_custom_config():
    """Example 5: Custom expansion configuration."""
    print("\n" + "=" * 80)
    print("Example 5: Custom Expansion Configuration")
    print("=" * 80)
    
    # Aggressive expansion (more synonyms, include lemmas)
    expander_aggressive = QueryExpander(
        max_synonyms=5,
        include_stems=True,
        include_lemmas=True
    )
    
    # Conservative expansion (fewer synonyms, stems only)
    expander_conservative = QueryExpander(
        max_synonyms=2,
        include_stems=True,
        include_lemmas=False
    )
    
    query = "good news"
    
    result_agg = expander_aggressive.expand(query)
    result_con = expander_conservative.expand(query)
    
    print(f"\nQuery: '{query}'")
    print(f"\nAggressive expansion ({len(result_agg['expanded_terms'])} terms):")
    print(f"  {result_agg['expanded_terms'][:10]}...")
    
    print(f"\nConservative expansion ({len(result_con['expanded_terms'])} terms):")
    print(f"  {result_con['expanded_terms'][:10]}...")


def example_6_convenience_functions():
    """Example 6: Using convenience functions."""
    print("\n" + "=" * 80)
    print("Example 6: Convenience Functions")
    print("=" * 80)
    
    # Quick expansion without creating expander object
    print("\n1. expand_query() - Quick expansion:")
    terms = expand_query("vaccine test")
    print(f"   {terms}")
    
    # Get synonyms directly
    print("\n2. get_synonyms() - Direct synonym lookup:")
    syns = get_synonyms("good", max_synonyms=3)
    print(f"   Synonyms for 'good': {syns}")
    
    # Get root words directly
    print("\n3. get_root_words() - Direct stemming:")
    roots = get_root_words("running vaccination matches")
    print(f"   Root words: {roots}")


def example_7_integration_with_clir():
    """Example 7: Integration with CLIR pipeline."""
    print("\n" + "=" * 80)
    print("Example 7: Integration with CLIR Pipeline")
    print("=" * 80)
    
    try:
        from query_normalizer import QueryNormalizer
        from language_detector import LanguageDetector
        
        normalizer = QueryNormalizer()
        detector = LanguageDetector()
        expander = QueryExpander()
        
        query = "  CORONAVIRUS Vaccine NEWS  "
        
        print(f"\nOriginal query: '{query}'")
        
        # Step 1: Normalize
        normalized = normalizer.normalize(query)
        print(f"1. Normalized:  '{normalized}'")
        
        # Step 2: Detect language
        lang = detector.detect(normalized)
        print(f"2. Language:    {lang}")
        
        # Step 3: Expand (only for English)
        if lang == 'en':
            result = expander.expand(normalized)
            expanded = expander.expand_to_query(normalized)
            print(f"3. Expanded terms: {result['expanded_terms'][:8]}...")
            print(f"4. Query string:   {expanded[:80]}...")
        else:
            print("3. Skipping expansion (not English)")
        
    except ImportError as e:
        print(f"\nNote: Some modules not available: {e}")


def example_8_batch_expansion():
    """Example 8: Batch query expansion."""
    print("\n" + "=" * 80)
    print("Example 8: Batch Query Expansion")
    print("=" * 80)
    
    expander = QueryExpander()
    
    queries = [
        "coronavirus vaccine",
        "cricket match",
        "election results",
        "weather forecast"
    ]
    
    print("\nExpanding multiple queries:")
    for query in queries:
        result = expander.expand(query)
        num_terms = len(result['expanded_terms'])
        print(f"\n  '{query}' → {num_terms} expanded terms")
    
    # Show cache stats
    print(f"\nCache info:")
    print(f"  Total queries processed: {len(queries)}")


def main():
    """Run all examples."""
    print("\n" + "#" * 80)
    print("Query Expansion Module - Usage Examples")
    print("#" * 80)
    
    examples = [
        example_1_basic_expansion,
        example_2_synonym_only,
        example_3_stemming,
        example_4_expanded_query_string,
        example_5_custom_config,
        example_6_convenience_functions,
        example_7_integration_with_clir,
        example_8_batch_expansion
    ]
    
    for example_func in examples:
        try:
            example_func()
        except Exception as e:
            print(f"\n⚠ Error in {example_func.__name__}: {e}")
    
    print("\n" + "#" * 80)
    print("Examples completed!")
    print("#" * 80 + "\n")


if __name__ == "__main__":
    main()
