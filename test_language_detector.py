#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test suite for Language Detection Module
Phase 2: Query Processing - Language Detection (Bangla/English)
"""

import sys
import io
from pathlib import Path

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from language_detector import LanguageDetector, detect_language


def test_basic_detection():
    """Test basic language detection functionality."""
    print("="*80)
    print("Test 1: Basic Detection")
    print("="*80)
    
    detector = LanguageDetector()
    
    test_cases = [
        # (text, expected_language)
        ("Hello World", "en"),
        ("আসসালামু আলাইকুম", "bn"),
        ("The quick brown fox jumps over the lazy dog", "en"),
        ("বাংলা ভাষা পৃথিবীর সপ্তম বৃহত্তম ভাষা", "bn"),
        ("Python programming language", "en"),
        ("ঢাকা বিশ্ববিদ্যালয়", "bn"),
        ("", "en"),  # Empty string defaults to English
        ("123456", "en"),  # Numbers default to English
    ]
    
    passed = 0
    failed = 0
    
    for text, expected in test_cases:
        result = detector.detect(text)
        status = "✓" if result == expected else "✗"
        if result == expected:
            passed += 1
        else:
            failed += 1
        
        display_text = text if text else "[empty]"
        print(f"{status} '{display_text[:50]}' → {result} (expected: {expected})")
    
    print(f"\nResults: {passed} passed, {failed} failed")
    return failed == 0


def test_confidence_scores():
    """Test detection with confidence scores."""
    print("\n" + "="*80)
    print("Test 2: Confidence Scores")
    print("="*80)
    
    detector = LanguageDetector()
    
    test_cases = [
        ("Pure English text without any other characters", "en", 1.0),
        ("সম্পূর্ণ বাংলা টেক্সট অন্য কোন অক্ষর ছাড়া", "bn", 1.0),
        ("Mixed করোনা and virus", "en", 0.5),  # Roughly balanced
    ]
    
    for text, expected_lang, min_confidence in test_cases:
        lang, confidence, stats = detector.detect_with_confidence(text)
        status = "✓" if lang == expected_lang and confidence >= min_confidence else "✗"
        
        print(f"{status} '{text}'")
        print(f"   Language: {lang}, Confidence: {confidence:.2%}")
        print(f"   Stats: BN={stats['bangla']}, EN={stats['english']}, Other={stats['other']}")


def test_mixed_language():
    """Test mixed language detection."""
    print("\n" + "="*80)
    print("Test 3: Mixed Language Detection")
    print("="*80)
    
    detector = LanguageDetector()
    
    # These should be detected as mixed
    mixed_texts = [
        "করোনা ভাইরাস pandemic situation",
        "Bangladesh এর রাজধানী Dhaka",
        "Cricket খেলা very popular",
    ]
    
    # These should NOT be mixed
    pure_texts = [
        "Completely English sentence here",
        "সম্পূর্ণ বাংলা বাক্য এখানে",
    ]
    
    print("\nShould be detected as MIXED:")
    for text in mixed_texts:
        is_mixed = detector.is_mixed(text)
        distribution = detector.get_language_distribution(text)
        status = "✓" if is_mixed else "✗"
        print(f"{status} '{text}'")
        print(f"   BN: {distribution['bangla']:.1f}%, EN: {distribution['english']:.1f}%")
    
    print("\nShould NOT be mixed:")
    for text in pure_texts:
        is_mixed = detector.is_mixed(text)
        status = "✓" if not is_mixed else "✗"
        print(f"{status} '{text}' → Mixed: {is_mixed}")


def test_utility_functions():
    """Test utility functions."""
    print("\n" + "="*80)
    print("Test 4: Utility Functions")
    print("="*80)
    
    detector = LanguageDetector()
    
    # Test is_bangla and is_english
    print("\nTesting is_bangla() and is_english():")
    
    test_cases = [
        ("Hello", False, True),
        ("হ্যালো", True, False),
        ("Mixed করোনা", False, True),  # English dominant
    ]
    
    for text, should_be_bangla, should_be_english in test_cases:
        is_bn = detector.is_bangla(text)
        is_en = detector.is_english(text)
        
        bn_status = "✓" if is_bn == should_be_bangla else "✗"
        en_status = "✓" if is_en == should_be_english else "✗"
        
        print(f"'{text}':")
        print(f"  {bn_status} is_bangla: {is_bn} (expected: {should_be_bangla})")
        print(f"  {en_status} is_english: {is_en} (expected: {should_be_english})")


def test_batch_detection():
    """Test batch detection."""
    print("\n" + "="*80)
    print("Test 5: Batch Detection")
    print("="*80)
    
    detector = LanguageDetector()
    
    texts = [
        "First English text",
        "প্রথম বাংলা টেক্সট",
        "Second English text",
        "দ্বিতীয় বাংলা টেক্সট",
    ]
    
    expected = ["en", "bn", "en", "bn"]
    
    results = detector.batch_detect(texts)
    
    all_correct = True
    for text, result, exp in zip(texts, results, expected):
        status = "✓" if result == exp else "✗"
        if result != exp:
            all_correct = False
        print(f"{status} '{text[:30]}' → {result} (expected: {exp})")
    
    return all_correct


def test_comprehensive_analysis():
    """Test comprehensive text analysis."""
    print("\n" + "="*80)
    print("Test 6: Comprehensive Analysis")
    print("="*80)
    
    detector = LanguageDetector()
    
    test_text = "বাংলাদেশ দক্ষিণ এশিয়ার একটি সার্বভৌম রাষ্ট্র"
    
    analysis = detector.analyze_text(test_text)
    
    print(f"Text: {test_text}")
    print(f"\nAnalysis Results:")
    print(f"  Language: {analysis['language_name']} ({analysis['language']})")
    print(f"  Confidence: {analysis['confidence']:.2%}")
    print(f"  Is Mixed: {analysis['is_mixed']}")
    print(f"  Word Count: {analysis['word_count']}")
    print(f"  Character Count: {analysis['character_count']}")
    print(f"  Text Length: {analysis['text_length']}")
    print(f"\nCharacter Statistics:")
    print(f"  Bangla: {analysis['statistics']['bangla']}")
    print(f"  English: {analysis['statistics']['english']}")
    print(f"  Other: {analysis['statistics']['other']}")
    print(f"  Total: {analysis['statistics']['total']}")


def test_convenience_function():
    """Test the convenience function."""
    print("\n" + "="*80)
    print("Test 7: Convenience Function")
    print("="*80)
    
    test_cases = [
        ("Quick test", "en"),
        ("দ্রুত পরীক্ষা", "bn"),
    ]
    
    for text, expected in test_cases:
        result = detect_language(text)
        status = "✓" if result == expected else "✗"
        print(f"{status} detect_language('{text}') → {result} (expected: {expected})")


def test_real_queries():
    """Test with real CLIR queries."""
    print("\n" + "="*80)
    print("Test 8: Real CLIR Queries")
    print("="*80)
    
    detector = LanguageDetector()
    
    real_queries = [
        # English queries
        "coronavirus vaccine",
        "election results",
        "cricket match",
        "climate change",
        "economic growth",
        
        # Bangla queries
        "করোনা ভ্যাকসিন",
        "নির্বাচন ফলাফল",
        "ক্রিকেট খেলা",
        "জলবায়ু পরিবর্তন",
        "অর্থনৈতিক উন্নয়ন",
    ]
    
    print("\nDetecting language for real CLIR queries:")
    for query in real_queries:
        lang, confidence, _ = detector.detect_with_confidence(query)
        lang_name = "Bangla" if lang == "bn" else "English"
        print(f"'{query:30s}' → {lang_name:7s} ({confidence:.0%} confidence)")


def integration_test_with_bm25():
    """Test integration with existing BM25 CLIR system."""
    print("\n" + "="*80)
    print("Test 9: Integration with BM25 CLIR")
    print("="*80)
    
    try:
        # Add BM25 directory to path
        bm25_path = Path(__file__).parent / "BM25"
        sys.path.insert(0, str(bm25_path))
        from bm25_clir import BM25CLIR
        
        # Initialize both systems
        detector = LanguageDetector()
        clir = BM25CLIR()
        
        test_queries = [
            "coronavirus",
            "করোনা",
        ]
        
        print("\nComparing language detection results:")
        print(f"{'Query':<20} {'Our Detector':<15} {'BM25 Detector':<15} {'Match':<10}")
        print("-" * 65)
        
        for query in test_queries:
            our_result = detector.detect(query)
            bm25_result = clir.detect_language(query)
            match = "✓" if our_result == bm25_result else "✗"
            
            our_name = "Bangla" if our_result == "bn" else "English"
            bm25_name = "Bangla" if bm25_result == "bn" else "English"
            
            print(f"{query:<20} {our_name:<15} {bm25_name:<15} {match:<10}")
        
        print("\n✓ Integration test completed successfully!")
        
    except ImportError:
        print("⚠ BM25 module not available, skipping integration test")
    except Exception as e:
        print(f"⚠ Integration test error: {e}")


def main():
    """Run all tests."""
    print("=" * 80)
    print(" " * 20 + "Language Detection Test Suite")
    print(" " * 15 + "Phase 2: Query Processing - Language Detection")
    print("=" * 80)
    
    tests = [
        test_basic_detection,
        test_confidence_scores,
        test_mixed_language,
        test_utility_functions,
        test_batch_detection,
        test_comprehensive_analysis,
        test_convenience_function,
        test_real_queries,
        integration_test_with_bm25,
    ]
    
    for test_func in tests:
        try:
            test_func()
        except Exception as e:
            print(f"\n✗ Test failed with error: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*80)
    print("All Tests Completed!")
    print("="*80)


if __name__ == "__main__":
    main()
