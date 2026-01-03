#!/usr/bin/env python3
"""
Complete Phase 2 Integration Test
Tests all components working together without UTF-8 wrapper issues
"""

def test_all_components():
    """Test all Phase 2 components."""
    
    print("="*70)
    print("Phase 2: Complete Integration Test")
    print("="*70)
    
    # Test 1: Import all modules
    print("\n1. Testing Module Imports...")
    print("-"*70)
    
    try:
        from language_detector import LanguageDetector, detect_language
        print("✓ language_detector imported")
    except Exception as e:
        print(f"✗ language_detector failed: {e}")
        return False
    
    try:
        from query_normalizer import QueryNormalizer, normalize_query
        print("✓ query_normalizer imported")
    except Exception as e:
        print(f"✗ query_normalizer failed: {e}")
        return False
    
    try:
        from query_translator import QueryTranslator, translate_query
        print("✓ query_translator imported")
    except Exception as e:
        print(f"✗ query_translator failed: {e}")
        return False
    
    try:
        from query_expander import QueryExpander, expand_query
        print("✓ query_expander imported")
    except Exception as e:
        print(f"✗ query_expander failed: {e}")
        return False
    
    # Test 2: Initialize all components
    print("\n2. Testing Component Initialization...")
    print("-"*70)
    
    try:
        detector = LanguageDetector()
        print("✓ LanguageDetector initialized")
    except Exception as e:
        print(f"✗ LanguageDetector failed: {e}")
        return False
    
    try:
        normalizer = QueryNormalizer()
        print("✓ QueryNormalizer initialized")
    except Exception as e:
        print(f"✗ QueryNormalizer failed: {e}")
        return False
    
    try:
        translator = QueryTranslator()
        print("✓ QueryTranslator initialized")
    except Exception as e:
        print(f"✗ QueryTranslator failed: {e}")
        return False
    
    try:
        expander = QueryExpander()
        print("✓ QueryExpander initialized")
    except Exception as e:
        print(f"✗ QueryExpander failed: {e}")
        return False
    
    # Test 3: English query processing
    print("\n3. Testing English Query Processing...")
    print("-"*70)
    
    en_query = "  CORONAVIRUS Vaccine NEWS  "
    print(f"Original: '{en_query}'")
    
    # Normalize
    normalized = normalizer.normalize(en_query)
    print(f"Normalized: '{normalized}'")
    assert normalized == "coronavirus vaccine news", "Normalization failed"
    
    # Detect
    lang = detector.detect(normalized)
    print(f"Language: {lang}")
    assert lang == "en", "Detection failed"
    
    # Expand
    expanded = expander.expand(normalized)
    print(f"Expanded terms: {len(expanded['expanded_terms'])} terms")
    assert len(expanded['expanded_terms']) > 0, "Expansion failed"
    
    # Translate
    translated = translator.english_to_bangla(normalized)
    print(f"Translated: {translated[:50]}...")
    assert len(translated) > 0, "Translation failed"
    
    print("✓ English query processing successful")
    
    # Test 4: Bangla query processing
    print("\n4. Testing Bangla Query Processing...")
    print("-"*70)
    
    bn_query = "করোনা ভ্যাকসিন"
    print(f"Original: '{bn_query}'")
    
    # Normalize
    normalized_bn = normalizer.normalize(bn_query)
    print(f"Normalized: '{normalized_bn}'")
    
    # Detect
    lang_bn = detector.detect(normalized_bn)
    print(f"Language: {lang_bn}")
    assert lang_bn == "bn", "Bangla detection failed"
    
    # Translate
    translated_en = translator.bangla_to_english(normalized_bn)
    print(f"Translated: {translated_en}")
    assert len(translated_en) > 0, "Bangla translation failed"
    
    print("✓ Bangla query processing successful")
    
    # Test 5: Convenience functions
    print("\n5. Testing Convenience Functions...")
    print("-"*70)
    
    # Language detection
    lang_quick = detect_language("test")
    print(f"detect_language('test'): {lang_quick}")
    assert lang_quick == "en", "Quick detection failed"
    
    # Normalization
    norm_quick = normalize_query("  TEST  ")
    print(f"normalize_query('  TEST  '): '{norm_quick}'")
    assert norm_quick == "test", "Quick normalization failed"
    
    # Translation
    trans_quick = translate_query("hello", "en", "bn")
    print(f"translate_query('hello', 'en', 'bn'): {trans_quick}")
    assert len(trans_quick) > 0, "Quick translation failed"
    
    # Expansion
    expand_quick = expand_query("test")
    print(f"expand_query('test'): {len(expand_quick)} terms")
    assert len(expand_quick) > 0, "Quick expansion failed"
    
    print("✓ Convenience functions working")
    
    # Test 6: Multiple imports (test for wrapper conflicts)
    print("\n6. Testing Multiple Import Scenario...")
    print("-"*70)
    
    try:
        # Reimport all modules
        import importlib
        import language_detector
        import query_normalizer
        import query_translator
        import query_expander
        
        importlib.reload(language_detector)
        importlib.reload(query_normalizer)
        importlib.reload(query_translator)
        importlib.reload(query_expander)
        
        print("✓ Multiple imports successful (no wrapper conflicts)")
    except Exception as e:
        print(f"✗ Multiple imports failed: {e}")
        return False
    
    # Test 7: Pipeline integration
    print("\n7. Testing Full Pipeline Integration...")
    print("-"*70)
    
    test_queries = [
        "vaccine news",
        "করোনা ভ্যাকসিন",
        "cricket match"
    ]
    
    for query in test_queries:
        try:
            normalized = normalizer.normalize(query)
            lang = detector.detect(normalized)
            
            if lang == 'en':
                expanded = expander.expand(normalized)
                translated = translator.english_to_bangla(normalized)
            else:
                translated = translator.bangla_to_english(normalized)
            
            print(f"✓ Processed: '{query}' ({lang})")
        except Exception as e:
            print(f"✗ Failed to process '{query}': {e}")
            return False
    
    print("✓ Pipeline integration successful")
    
    # Final summary
    print("\n" + "="*70)
    print("ALL TESTS PASSED! ✓")
    print("="*70)
    print("\nPhase 2 Components Status:")
    print("  ✓ Language Detection - Working")
    print("  ✓ Query Normalization - Working")
    print("  ✓ Query Translation - Working")
    print("  ✓ Query Expansion - Working")
    print("  ✓ No UTF-8 wrapper conflicts")
    print("  ✓ All imports successful")
    print("  ✓ Pipeline integration working")
    print("\nPhase 2: 100% Complete and Fully Functional! 🎉")
    print("="*70)
    
    return True


if __name__ == "__main__":
    success = test_all_components()
    exit(0 if success else 1)
