#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Suite for Named Entity Mapping Module
Phase 2: Query Processing - Named Entity Mapping
"""

import unittest
from named_entity_mapper import (
    NamedEntityMapper,
    map_entities,
    get_entity_mapping
)


class TestNamedEntityMapper(unittest.TestCase):
    """Test cases for NamedEntityMapper class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mapper = NamedEntityMapper()
    
    def test_initialization(self):
        """Test mapper initialization."""
        self.assertIsNotNone(self.mapper)
        self.assertGreater(self.mapper.get_mapping_count(), 0)
    
    def test_english_to_bangla_cities(self):
        """Test mapping English cities to Bangla."""
        test_cases = [
            ("Dhaka", "ঢাকা"),
            ("Chittagong", "চট্টগ্রাম"),
            ("Sylhet", "সিলেট"),
            ("Rajshahi", "রাজশাহী")
        ]
        
        for english, expected_bangla in test_cases:
            text = f"I visited {english}"
            result = self.mapper.map_english_to_bangla(text)
            self.assertIn(expected_bangla, result)
    
    def test_english_to_bangla_countries(self):
        """Test mapping English countries to Bangla."""
        text = "Bangladesh and India are neighbors"
        result = self.mapper.map_english_to_bangla(text)
        
        self.assertIn("বাংলাদেশ", result)
        self.assertIn("ভারত", result)
    
    def test_bangla_to_english_mapping(self):
        """Test mapping Bangla entities to English."""
        text = "ঢাকা বাংলাদেশের রাজধানী"
        result = self.mapper.map_bangla_to_english(text)
        
        self.assertIn("dhaka", result.lower())
        self.assertIn("bangladesh", result.lower())
    
    def test_multi_word_entities(self):
        """Test mapping multi-word entities."""
        text = "Sheikh Hasina is the Prime Minister"
        result = self.mapper.map_english_to_bangla(text)
        
        self.assertIn("শেখ হাসিনা", result)
    
    def test_case_insensitive_matching(self):
        """Test case-insensitive matching."""
        test_cases = [
            "Dhaka is great",
            "dhaka is great",
            "DHAKA is great"
        ]
        
        for text in test_cases:
            result = self.mapper.map_english_to_bangla(text)
            self.assertIn("ঢাকা", result)
    
    def test_entity_extraction(self):
        """Test entity extraction."""
        text = "Dhaka and Chittagong are in Bangladesh"
        entities = self.mapper.extract_entities(text)
        
        self.assertGreater(len(entities), 0)
        
        # Check that entities were found
        entity_names = [orig for orig, mapped in entities]
        self.assertTrue(any("Dhaka" in e for e in entity_names))
    
    def test_single_entity_lookup(self):
        """Test single entity lookup."""
        # English lookup
        result = self.mapper.get_entity_mapping("Dhaka", "en")
        self.assertEqual(result, "ঢাকা")
        
        # Bangla lookup
        result = self.mapper.get_entity_mapping("ঢাকা", "bn")
        self.assertEqual(result, "dhaka")
    
    def test_auto_language_detection(self):
        """Test auto language detection in lookup."""
        # Should work without specifying language
        result1 = self.mapper.get_entity_mapping("Dhaka", "auto")
        self.assertEqual(result1, "ঢাকা")
        
        result2 = self.mapper.get_entity_mapping("ঢাকা", "auto")
        self.assertEqual(result2, "dhaka")
    
    def test_add_custom_mapping(self):
        """Test adding custom mappings."""
        self.mapper.add_mapping("Gazipur", "গাজীপুর")
        
        result = self.mapper.get_entity_mapping("Gazipur")
        self.assertEqual(result, "গাজীপুর")
    
    def test_add_multiple_mappings(self):
        """Test adding multiple mappings at once."""
        custom = {
            "Narayangonj": "নারায়ণগঞ্জ",
            "Jamalpur": "জামালপুর"
        }
        
        self.mapper.add_mappings(custom)
        
        result1 = self.mapper.get_entity_mapping("Narayangonj")
        self.assertEqual(result1, "নারায়ণগঞ্জ")
    
    def test_get_all_entities(self):
        """Test getting all entities."""
        en_entities = self.mapper.get_all_entities('en')
        bn_entities = self.mapper.get_all_entities('bn')
        
        self.assertGreater(len(en_entities), 0)
        self.assertGreater(len(bn_entities), 0)
        # Note: Counts may differ if multiple EN entities map to same BN entity
    
    def test_search_entities(self):
        """Test searching for entities."""
        # Search in English
        results = self.mapper.search_entities("dhaka", "en")
        self.assertGreater(len(results), 0)
        
        # Search in Bangla
        results = self.mapper.search_entities("ঢাকা", "bn")
        self.assertGreater(len(results), 0)


class TestConvenienceFunctions(unittest.TestCase):
    """Test convenience functions."""
    
    def test_map_entities_function(self):
        """Test map_entities convenience function."""
        text = "Dhaka is in Bangladesh"
        result = map_entities(text, direction='en_to_bn')
        
        self.assertIn("ঢাকা", result)
        self.assertIn("বাংলাদেশ", result)
    
    def test_get_entity_mapping_function(self):
        """Test get_entity_mapping convenience function."""
        result = get_entity_mapping("Dhaka")
        self.assertEqual(result, "ঢাকা")


class TestRealWorldScenarios(unittest.TestCase):
    """Test real-world CLIR scenarios."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mapper = NamedEntityMapper()
    
    def test_news_headline_mapping(self):
        """Test mapping news headlines."""
        headlines = [
            "Cricket match in Dhaka stadium",
            "Sheikh Hasina visits India",
            "Bangladesh wins against Pakistan"
        ]
        
        for headline in headlines:
            result = self.mapper.map_english_to_bangla(headline)
            # Should contain at least one Bangla entity
            self.assertTrue(
                any(char in result for char in "অআইঈউঊএঐওঔকখগঘঙচছজঝঞটঠডঢণতথদধনপফবভমযরলশষসহড়ঢ়য়ৎংঃঁ")
            )
    
    def test_sports_query_mapping(self):
        """Test sports-related queries."""
        query = "Shakib Al Hasan cricket match Bangladesh"
        result = self.mapper.map_english_to_bangla(query)
        
        self.assertIn("শাকিব আল হাসান", result)
        self.assertIn("ক্রিকেট", result)
        self.assertIn("বাংলাদেশ", result)
    
    def test_political_query_mapping(self):
        """Test political queries."""
        query = "Awami League and BNP election in Bangladesh"
        result = self.mapper.map_english_to_bangla(query)
        
        self.assertIn("আওয়ামী লীগ", result)
        self.assertIn("বিএনপি", result)
        self.assertIn("বাংলাদেশ", result)


def run_manual_tests():
    """Run manual tests with real examples."""
    print("=" * 80)
    print("Named Entity Mapping - Manual Tests")
    print("=" * 80)
    
    mapper = NamedEntityMapper()
    
    # Test 1: City mapping
    print("\n1. City Name Mapping")
    print("-" * 80)
    
    cities = ["Dhaka", "Chittagong", "Sylhet", "Rajshahi", "Khulna"]
    for city in cities:
        mapped = mapper.get_entity_mapping(city, 'en')
        print(f"{city:20s} → {mapped}")
    
    # Test 2: Full sentence mapping
    print("\n\n2. Full Sentence Mapping")
    print("-" * 80)
    
    sentences = [
        "Dhaka is the capital of Bangladesh",
        "Sheikh Hasina met Joe Biden in USA",
        "Shakib Al Hasan plays cricket for Bangladesh",
        "Bangladesh and India are in South Asia"
    ]
    
    for sentence in sentences:
        mapped = mapper.map_english_to_bangla(sentence)
        print(f"EN: {sentence}")
        print(f"BN: {mapped}\n")
    
    # Test 3: Entity extraction
    print("\n3. Entity Extraction")
    print("-" * 80)
    
    text = "Cricket match between Bangladesh and Pakistan in Dhaka"
    entities = mapper.extract_entities(text)
    print(f"Text: {text}")
    print(f"Extracted {len(entities)} entities:")
    for orig, mapped in entities:
        print(f"  {orig:20s} → {mapped}")
    
    # Test 4: Reverse mapping
    print("\n\n4. Bangla to English Mapping")
    print("-" * 80)
    
    bn_texts = [
        "ঢাকা বাংলাদেশের রাজধানী",
        "শেখ হাসিনা এবং নরেন্দ্র মোদী",
        "বাংলাদেশ ক্রিকেট দল"
    ]
    
    for text in bn_texts:
        mapped = mapper.map_bangla_to_english(text)
        print(f"BN: {text}")
        print(f"EN: {mapped}\n")
    
    print("=" * 80)
    print("✓ Manual tests completed")
    print("=" * 80)


if __name__ == "__main__":
    print("Named Entity Mapping Test Suite\n")
    
    # Run manual tests first
    run_manual_tests()
    
    # Then run unit tests
    print("\n" + "=" * 80)
    print("Running Unit Tests")
    print("=" * 80)
    unittest.main(verbosity=2)
