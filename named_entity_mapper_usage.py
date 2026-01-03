#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Named Entity Mapping Usage Examples
Phase 2: Query Processing - Named Entity Mapping
"""

from named_entity_mapper import (
    NamedEntityMapper,
    map_entities,
    get_entity_mapping
)


def example_1_basic_mapping():
    """Example 1: Basic entity mapping."""
    print("\n" + "=" * 80)
    print("Example 1: Basic Named Entity Mapping")
    print("=" * 80)
    
    mapper = NamedEntityMapper()
    
    # English to Bangla
    print("\nEnglish to Bangla:")
    print("-" * 80)
    
    texts = [
        "Dhaka is beautiful",
        "I visited Bangladesh",
        "Sheikh Hasina is the Prime Minister"
    ]
    
    for text in texts:
        mapped = mapper.map_english_to_bangla(text)
        print(f"EN: {text}")
        print(f"BN: {mapped}\n")


def example_2_reverse_mapping():
    """Example 2: Bangla to English mapping."""
    print("\n" + "=" * 80)
    print("Example 2: Bangla to English Mapping")
    print("=" * 80)
    
    mapper = NamedEntityMapper()
    
    bn_texts = [
        "ঢাকা একটি সুন্দর শহর",
        "বাংলাদেশ দক্ষিণ এশিয়ায়",
        "শেখ হাসিনা প্রধানমন্ত্রী"
    ]
    
    for text in bn_texts:
        mapped = mapper.map_bangla_to_english(text)
        print(f"BN: {text}")
        print(f"EN: {mapped}\n")


def example_3_news_headlines():
    """Example 3: Real news headline mapping."""
    print("\n" + "=" * 80)
    print("Example 3: News Headlines Mapping")
    print("=" * 80)
    
    mapper = NamedEntityMapper()
    
    headlines = [
        "Cricket match: Bangladesh vs Pakistan in Dhaka",
        "Sheikh Hasina meets Narendra Modi in India",
        "Shakib Al Hasan breaks world record",
        "Bangladesh wins against Australia in World Cup",
        "Awami League announces election manifesto"
    ]
    
    print("\nMapped Headlines:")
    print("-" * 80)
    
    for headline in headlines:
        mapped = mapper.map_english_to_bangla(headline)
        print(f"Original:  {headline}")
        print(f"Mapped:    {mapped}\n")


def example_4_entity_extraction():
    """Example 4: Extract entities from text."""
    print("\n" + "=" * 80)
    print("Example 4: Entity Extraction")
    print("=" * 80)
    
    mapper = NamedEntityMapper()
    
    texts = [
        "Cricket match between Bangladesh and India at Dhaka stadium",
        "Sheikh Hasina visited USA and met Joe Biden",
        "Shakib Al Hasan plays for Bangladesh Cricket Board"
    ]
    
    for text in texts:
        entities = mapper.extract_entities(text)
        print(f"\nText: {text}")
        print(f"Found {len(entities)} entities:")
        for orig, mapped in entities:
            print(f"  {orig:25s} → {mapped}")


def example_5_single_entity_lookup():
    """Example 5: Look up individual entities."""
    print("\n" + "=" * 80)
    print("Example 5: Single Entity Lookup")
    print("=" * 80)
    
    mapper = NamedEntityMapper()
    
    # Cities
    print("\nCities:")
    print("-" * 80)
    cities = ["Dhaka", "Chittagong", "Sylhet", "Rajshahi", "Khulna", "Barisal"]
    for city in cities:
        mapped = mapper.get_entity_mapping(city, 'en')
        print(f"{city:15s} → {mapped}")
    
    # Countries
    print("\nCountries:")
    print("-" * 80)
    countries = ["Bangladesh", "India", "Pakistan", "China", "USA"]
    for country in countries:
        mapped = mapper.get_entity_mapping(country, 'en')
        print(f"{country:15s} → {mapped}")
    
    # People
    print("\nPeople:")
    print("-" * 80)
    people = ["Sheikh Hasina", "Shakib Al Hasan", "Rabindranath Tagore"]
    for person in people:
        mapped = mapper.get_entity_mapping(person, 'en')
        print(f"{person:25s} → {mapped}")


def example_6_custom_mappings():
    """Example 6: Add custom entity mappings."""
    print("\n" + "=" * 80)
    print("Example 6: Custom Entity Mappings")
    print("=" * 80)
    
    mapper = NamedEntityMapper()
    
    # Add single mapping
    print("\nAdding custom mappings...")
    mapper.add_mapping("Gazipur", "গাজীপুর")
    mapper.add_mapping("Narayanganj", "নারায়ণগঞ্জ")
    
    # Add multiple mappings
    custom_cities = {
        "Jamalpur": "জামালপুর",
        "Pabna": "পাবনা",
        "Sirajganj": "সিরাজগঞ্জ"
    }
    mapper.add_mappings(custom_cities)
    
    # Test custom mappings
    print("\nTesting custom mappings:")
    print("-" * 80)
    text = "I visited Gazipur, Narayanganj, and Jamalpur"
    mapped = mapper.map_english_to_bangla(text)
    print(f"Original: {text}")
    print(f"Mapped:   {mapped}")


def example_7_convenience_functions():
    """Example 7: Using convenience functions."""
    print("\n" + "=" * 80)
    print("Example 7: Convenience Functions")
    print("=" * 80)
    
    # Quick mapping without creating mapper object
    print("\n1. map_entities() - Quick mapping:")
    print("-" * 80)
    
    text = "Cricket match in Dhaka between Bangladesh and India"
    mapped = map_entities(text, direction='en_to_bn')
    print(f"Original: {text}")
    print(f"Mapped:   {mapped}")
    
    # Single entity lookup
    print("\n2. get_entity_mapping() - Quick lookup:")
    print("-" * 80)
    
    entities = ["Dhaka", "Bangladesh", "Sheikh Hasina"]
    for entity in entities:
        mapped = get_entity_mapping(entity)
        print(f"{entity:20s} → {mapped}")


def example_8_search_entities():
    """Example 8: Search for entities."""
    print("\n" + "=" * 80)
    print("Example 8: Search for Entities")
    print("=" * 80)
    
    mapper = NamedEntityMapper()
    
    # Search for cities containing "dh"
    print("\nSearching for 'dh':")
    print("-" * 80)
    results = mapper.search_entities("dh", "en")
    for en, bn in results[:5]:
        print(f"{en:20s} → {bn}")
    
    # Search for "বাংলা"
    print("\nSearching for 'বাংলা':")
    print("-" * 80)
    results = mapper.search_entities("বাংলা", "bn")
    for en, bn in results[:5]:
        print(f"{en:20s} → {bn}")


def example_9_integration_with_clir():
    """Example 9: Integration with CLIR pipeline."""
    print("\n" + "=" * 80)
    print("Example 9: Integration with CLIR Pipeline")
    print("=" * 80)
    
    try:
        from query_normalizer import QueryNormalizer
        from language_detector import LanguageDetector
        from query_translator import QueryTranslator
        
        normalizer = QueryNormalizer()
        detector = LanguageDetector()
        translator = QueryTranslator()
        mapper = NamedEntityMapper()
        
        query = "  Cricket Match Dhaka Bangladesh  "
        
        print(f"\nOriginal query: '{query}'")
        print("-" * 80)
        
        # Step 1: Normalize
        normalized = normalizer.normalize(query)
        print(f"1. Normalized:     '{normalized}'")
        
        # Step 2: Detect language
        lang = detector.detect(normalized)
        print(f"2. Language:       {lang}")
        
        # Step 3: Map entities
        if lang == 'en':
            entity_mapped = mapper.map_english_to_bangla(normalized)
            print(f"3. Entity mapped:  '{entity_mapped}'")
            
            # Step 4: Translate
            translated = translator.english_to_bangla(normalized)
            print(f"4. Translated:     '{translated}'")
        
    except ImportError as e:
        print(f"\nNote: Some modules not available: {e}")


def example_10_sports_queries():
    """Example 10: Sports-specific queries."""
    print("\n" + "=" * 80)
    print("Example 10: Sports Query Mapping")
    print("=" * 80)
    
    mapper = NamedEntityMapper()
    
    sports_queries = [
        "Shakib Al Hasan century against India",
        "Bangladesh Cricket Board announces squad",
        "World Cup match at Dhaka stadium",
        "Mashrafe Mortaza retires from cricket",
        "FIFA World Cup 2026 qualifiers"
    ]
    
    print("\nSports Queries:")
    print("-" * 80)
    
    for query in sports_queries:
        mapped = mapper.map_english_to_bangla(query)
        entities = mapper.extract_entities(query)
        
        print(f"\nQuery:    {query}")
        print(f"Mapped:   {mapped}")
        print(f"Entities: {len(entities)} found - {[e[0] for e in entities]}")


def main():
    """Run all examples."""
    print("\n" + "#" * 80)
    print("Named Entity Mapping Module - Usage Examples")
    print("#" * 80)
    
    examples = [
        example_1_basic_mapping,
        example_2_reverse_mapping,
        example_3_news_headlines,
        example_4_entity_extraction,
        example_5_single_entity_lookup,
        example_6_custom_mappings,
        example_7_convenience_functions,
        example_8_search_entities,
        example_9_integration_with_clir,
        example_10_sports_queries
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
