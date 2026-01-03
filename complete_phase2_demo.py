#!/usr/bin/env python3
"""
Complete Phase 2 Pipeline with Named Entity Mapping
Demonstrates all 5 components working together
"""

from language_detector import LanguageDetector
from query_normalizer import QueryNormalizer
from query_translator import QueryTranslator
from query_expander import QueryExpander
from named_entity_mapper import NamedEntityMapper


def process_query_complete(query: str, enable_expansion: bool = True):
    """
    Process query through complete Phase 2 pipeline with NE mapping.
    
    Args:
        query: Input query string
        enable_expansion: Enable query expansion
    
    Returns:
        Dictionary with all processing results
    """
    # Initialize all components
    normalizer = QueryNormalizer()
    detector = LanguageDetector()
    ne_mapper = NamedEntityMapper()
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
    results['steps'].append(f"2. Language: {lang}")
    
    # Step 3: Map named entities
    if lang == 'en':
        entity_mapped = ne_mapper.map_english_to_bangla(normalized)
        entities = ne_mapper.extract_entities(normalized, 'en')
    else:
        entity_mapped = ne_mapper.map_bangla_to_english(normalized)
        entities = ne_mapper.extract_entities(normalized, 'bn')
    
    results['entity_mapped'] = entity_mapped
    results['entities'] = entities
    results['steps'].append(f"3. Entity mapping: {len(entities)} entities found")
    
    # Step 4: Expand (English only)
    if enable_expansion and lang == 'en':
        expansion_result = expander.expand(normalized)
        results['expansion'] = expansion_result
        results['expanded_query'] = expander.expand_to_query(normalized)
        results['steps'].append(f"4. Expanded: {len(expansion_result['expanded_terms'])} terms")
        query_for_translation = normalized  # Translate original, not expanded
    else:
        results['expansion'] = None
        results['expanded_query'] = None
        results['steps'].append(f"4. Expansion: skipped")
        query_for_translation = normalized
    
    # Step 5: Translate for cross-lingual search
    if lang == 'bn':
        translated = translator.bangla_to_english(query_for_translation)
        results['translation'] = translated
        results['steps'].append(f"5. Translated (bn→en): '{translated}'")
    elif lang == 'en':
        translated = translator.english_to_bangla(query_for_translation)
        results['translation'] = translated
        results['steps'].append(f"5. Translated (en→bn): '{translated[:50]}...'")
    else:
        results['translation'] = None
        results['steps'].append(f"5. Translation: skipped")
    
    return results


def demo_complete_pipeline():
    """Demonstrate the complete pipeline with all 5 components."""
    print("#" * 80)
    print("Complete Phase 2 Pipeline Demonstration")
    print("All 5 Components: Detection, Normalization, NE Mapping, Expansion, Translation")
    print("#" * 80)
    
    test_queries = [
        "  Cricket Match in Dhaka Bangladesh  ",
        "Sheikh Hasina visits India",
        "Shakib Al Hasan world record",
        "করোনা ভ্যাকসিন ঢাকা",
        "বাংলাদেশ ক্রিকেট শেখ হাসিনা"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{'=' * 80}")
        print(f"Test Query {i}: '{query}'")
        print('=' * 80)
        
        # Process with all components
        results = process_query_complete(query, enable_expansion=True)
        
        # Display results
        for step in results['steps']:
            print(step)
        
        # Show entity mapping details
        if results['entities']:
            print(f"\nEntities Found ({len(results['entities'])}):")
            for orig, mapped in results['entities'][:5]:
                print(f"  {orig:25s} → {mapped}")
        
        # Show expansion if available
        if results['expansion']:
            print(f"\nExpansion:")
            print(f"  Original: {results['expansion']['terms']}")
            print(f"  Expanded: {results['expansion']['expanded_terms'][:8]}...")
        
        # Show final queries for search
        print(f"\nFinal Queries:")
        print(f"  Entity-mapped: {results['entity_mapped'][:60]}...")
        if results['translation']:
            print(f"  Translated:    {results['translation'][:60]}...")
        if results['expanded_query']:
            print(f"  Expanded:      {results['expanded_query'][:60]}...")
    
    print(f"\n{'#' * 80}")
    print("Pipeline Demonstration Complete!")
    print("All 5 Phase 2 Components Working! ✓")
    print("#" * 80)


def quick_component_test():
    """Quick test of all 5 components."""
    print("\nQuick Component Test - All 5 Phase 2 Modules:")
    print("-" * 80)
    
    # Test 1: Language Detection
    detector = LanguageDetector()
    lang = detector.detect("Dhaka")
    print(f"✓ Language Detection: 'Dhaka' → {lang}")
    
    # Test 2: Normalization
    normalizer = QueryNormalizer()
    norm = normalizer.normalize("  TEST  ")
    print(f"✓ Normalization: '  TEST  ' → '{norm}'")
    
    # Test 3: Named Entity Mapping
    ne_mapper = NamedEntityMapper()
    mapped = ne_mapper.get_entity_mapping("Dhaka", "en")
    print(f"✓ NE Mapping: 'Dhaka' → '{mapped}'")
    
    # Test 4: Query Expansion
    expander = QueryExpander()
    exp = expander.expand("test")
    print(f"✓ Query Expansion: 'test' → {len(exp['expanded_terms'])} terms")
    
    # Test 5: Translation
    translator = QueryTranslator()
    trans = translator.english_to_bangla("test")
    print(f"✓ Translation: 'test' → '{trans}'")
    
    print("-" * 80)
    print("All 5 components loaded and working! ✓\n")


def show_statistics():
    """Show statistics for all components."""
    print("\nPhase 2 Components Statistics:")
    print("-" * 80)
    
    ne_mapper = NamedEntityMapper()
    print(f"Named Entity Mappings: {ne_mapper.get_mapping_count()} entities")
    print(f"  - Cities: {len([e for e in ne_mapper.get_all_entities('en') if any(c in e for c in ['dhaka', 'chitt', 'sylhet', 'khulna'])])}")
    print(f"  - Countries: {len([e for e in ne_mapper.get_all_entities('en') if any(c in e for c in ['bangladesh', 'india', 'pakistan', 'china'])])}")
    print(f"  - People: {len([e for e in ne_mapper.get_all_entities('en') if any(c in e for c in ['sheikh', 'shakib', 'biden'])])}")
    
    print("\nPipeline Features:")
    print("  ✓ Language Detection (Bangla/English)")
    print("  ✓ Query Normalization")
    print("  ✓ Named Entity Mapping (73 entities)")
    print("  ✓ Query Expansion (English only)")
    print("  ✓ Query Translation (English ↔ Bangla)")
    
    print("-" * 80 + "\n")


if __name__ == "__main__":
    # Quick test first
    quick_component_test()
    
    # Show statistics
    show_statistics()
    
    # Full demonstration
    demo_complete_pipeline()
