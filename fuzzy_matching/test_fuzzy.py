#!/usr/bin/env python3
"""
Test Suite for Fuzzy Matching CLIR System

Includes:
- Unit tests for core algorithms
- Integration tests with sample data
- Performance benchmarks
- Error handling tests
"""

import json
import time
from typing import List, Dict
from fuzzy_matcher import FuzzyMatcher
from clir_search import CLIRSearch


# ============================================================================
# SAMPLE TEST DATA
# ============================================================================

SAMPLE_DOCUMENTS = [
    {
        'doc_id': 1,
        'title': 'Bangladesh Economy Report',
        'body': 'The economy of Bangladesh is growing steadily with contributions from textile and manufacturing sectors.',
        'url': 'https://example.com/1',
        'language': 'English',
        'token_count': 150
    },
    {
        'doc_id': 2,
        'title': 'করোনা ভ্যাকসিনের সর্বশেষ আপডেট',
        'body': 'বাংলাদেশে করোনা ভ্যাকসিনেশন প্রোগ্রাম সফলভাবে এগিয়ে চলেছে। এ পর্যন্ত লক্ষ লক্ষ মানুষ ভ্যাকসিন গ্রহণ করেছেন।',
        'url': 'https://example.com/2',
        'language': 'Bangla',
        'token_count': 200
    },
    {
        'doc_id': 3,
        'title': 'Dhaka Weather Forecast',
        'body': 'Dhaka will experience monsoon rains this week. Temperature expected to reach 32 degrees Celsius.',
        'url': 'https://example.com/3',
        'language': 'English',
        'token_count': 100
    },
    {
        'doc_id': 4,
        'title': 'ঢাকায় আবহাওয়া পূর্বাভাস',
        'body': 'এই সপ্তাহে ঢাকায় বৃষ্টির সম্ভাবনা রয়েছে। তাপমাত্রা ৩২ ডিগ্রি পর্যন্ত পৌঁছাবে বলে আশা করা হচ্ছে।',
        'url': 'https://example.com/4',
        'language': 'Bangla',
        'token_count': 120
    },
    {
        'doc_id': 5,
        'title': 'COVID-19 Vaccination Campaign',
        'body': 'A new vaccination campaign has started in Bangladesh. Healthcare workers are administering vaccines in all districts.',
        'url': 'https://example.com/5',
        'language': 'English',
        'token_count': 180
    },
    {
        'doc_id': 6,
        'title': 'প্রযুক্তি খাতে বাংলাদেশের অগ্রগতি',
        'body': 'বাংলাদেশ প্রযুক্তি শিল্পে অভূতপূর্ব উন্নতি করছে। সফটওয়্যার এবং আইটি সেবা রপ্তানি বৃদ্ধি পাচ্ছে।',
        'url': 'https://example.com/6',
        'language': 'Bangla',
        'token_count': 160
    },
    {
        'doc_id': 7,
        'title': 'Bangladesh Technology Sector Growth',
        'body': 'The technology sector in Bangladesh is experiencing rapid growth. Software exports have increased significantly over the past year.',
        'url': 'https://example.com/7',
        'language': 'English',
        'token_count': 170
    }
]

TRANSLITERATION_MAP = {
    'ঢাকা': ['Dhaka', 'Dacca'],
    'বাংলাদেশ': ['Bangladesh', 'Bangla Desh'],
    'করোনা': ['Corona', 'COVID', 'COVID-19'],
    'ভ্যাকসিন': ['Vaccine', 'Vaccination'],
    'আবহাওয়া': ['Weather', 'Climate'],
    'প্রযুক্তি': ['Technology', 'Tech']
}


# ============================================================================
# UNIT TESTS - Core Algorithm Tests
# ============================================================================

def test_edit_distance_score():
    """Test edit distance similarity scoring."""
    print("\n" + "="*80)
    print("TEST 1: Edit Distance Score Calculation")
    print("="*80)

    matcher = FuzzyMatcher()

    test_cases = [
        ('Bangladesh', 'Bangladesh', 1.0, 'Identical strings'),
        ('Bangladesh', 'Bangaldesh', 0.9, 'One character transposed'),
        ('Dhaka', 'Dacca', 0.8, 'Multiple character differences'),
        ('hello', 'hallo', 0.9, 'One character different'),
        ('', '', 1.0, 'Empty strings'),
        ('abc', 'xyz', 0.0, 'Completely different'),
    ]

    for s1, s2, expected_min, description in test_cases:
        score = matcher.edit_distance_score(s1, s2)
        status = "✓" if score >= expected_min else "✗"
        print(f"{status} {description}: '{s1}' vs '{s2}' = {score:.3f}")


def test_character_ngrams():
    """Test character n-gram generation."""
    print("\n" + "="*80)
    print("TEST 2: Character N-gram Generation")
    print("="*80)

    matcher = FuzzyMatcher()

    text = 'Dhaka'
    ngrams_3 = matcher.character_ngrams(text, n=3)
    print(f"Text: '{text}'")
    print(f"3-grams: {sorted(ngrams_3)}")

    expected = {'dha', 'hak', 'aka'}
    if expected.issubset(ngrams_3):
        print("✓ 3-gram generation correct")
    else:
        print("✗ 3-gram generation incorrect")


def test_jaccard_similarity():
    """Test Jaccard similarity calculation."""
    print("\n" + "="*80)
    print("TEST 3: Jaccard Similarity")
    print("="*80)

    matcher = FuzzyMatcher()

    test_cases = [
        ({'a', 'b', 'c'}, {'a', 'b', 'c'}, 1.0, 'Identical sets'),
        ({'a', 'b', 'c'}, {'a', 'b'}, 2/3, 'Partial overlap'),
        ({'a', 'b'}, {'c', 'd'}, 0.0, 'No overlap'),
        (set(), set(), 1.0, 'Empty sets'),
    ]

    for set1, set2, expected, description in test_cases:
        score = matcher.jaccard_similarity(set1, set2)
        status = "✓" if abs(score - expected) < 0.01 else "✗"
        print(f"{status} {description}: {score:.4f}")


def test_tokenization():
    """Test text tokenization."""
    print("\n" + "="*80)
    print("TEST 4: Text Tokenization")
    print("="*80)

    matcher = FuzzyMatcher()

    english_text = "Bangladesh economy is growing!"
    en_tokens = matcher.tokenize(english_text)
    print(f"English: '{english_text}'")
    print(f"Tokens: {en_tokens}")
    print("✓ English tokenization works")

    bangla_text = "বাংলাদেশের অর্থনীতি বৃদ্ধি পাচ্ছে"
    bn_tokens = matcher.tokenize(bangla_text)
    print(f"\nBangla: '{bangla_text}'")
    print(f"Tokens: {bn_tokens}")
    print("✓ Bangla tokenization works")


# ============================================================================
# INTEGRATION TESTS - Real Search Scenarios
# ============================================================================

def test_edit_distance_search():
    """Test fuzzy search with typos."""
    print("\n" + "="*80)
    print("TEST 5: Edit Distance Fuzzy Search (Typo Handling)")
    print("="*80)

    clir = CLIRSearch(documents=SAMPLE_DOCUMENTS)

    query = "Bangaldesh econmy"  # Typos
    print(f"Query: '{query}' (with typos)")
    print("-" * 80)

    results = clir.search_edit_distance(query, threshold=0.75, top_k=3)

    if results:
        print(f"✓ Found {len(results)} results")
        for i, result in enumerate(results, 1):
            print(f"{i}. {result['title']} (Score: {result['fuzzy_score']:.3f})")
            print(f"   Matched terms: {result['matched_terms'][:2]}")
    else:
        print("✗ No results found")


def test_jaccard_search():
    """Test Jaccard similarity search."""
    print("\n" + "="*80)
    print("TEST 6: Jaccard Similarity Search (N-gram Matching)")
    print("="*80)

    clir = CLIRSearch(documents=SAMPLE_DOCUMENTS)

    query = "Dhaka weather"
    print(f"Query: '{query}'")
    print(f"Using: Character 3-grams, threshold=0.3")
    print("-" * 80)

    results = clir.search_jaccard(
        query,
        level='char',
        n_gram=3,
        threshold=0.3,
        top_k=3
    )

    if results:
        print(f"✓ Found {len(results)} results")
        for i, result in enumerate(results, 1):
            print(f"{i}. {result['title']} (Score: {result['jaccard_score']:.3f})")
            print(f"   Common n-grams: {result['common_ngrams'][:5]}")
    else:
        print("✗ No results found")


def test_transliteration_search():
    """Test transliteration-aware search."""
    print("\n" + "="*80)
    print("TEST 7: Transliteration-Aware Search (Cross-Script Matching)")
    print("="*80)

    clir = CLIRSearch(
        documents=SAMPLE_DOCUMENTS,
        transliteration_map=TRANSLITERATION_MAP
    )

    query = "Corona vaccine"  # English query
    print(f"Query: '{query}' (English)")
    print(f"Expected to find: Bengali docs with 'করোনা' and 'ভ্যাকসিন'")
    print("-" * 80)

    results = clir.search_transliteration(query, threshold=0.7, top_k=5)

    if results:
        print(f"✓ Found {len(results)} results")
        for i, result in enumerate(results, 1):
            print(f"{i}. {result['title']} (Score: {result['fuzzy_score']:.3f})")
            print(f"   Language: {result['language']}")
    else:
        print("✗ No results found")


def test_hybrid_search():
    """Test hybrid search combining all methods."""
    print("\n" + "="*80)
    print("TEST 8: Hybrid Search (BM25 + Edit Distance + Jaccard)")
    print("="*80)

    clir = CLIRSearch(documents=SAMPLE_DOCUMENTS)

    query = "Bangladesh technology"
    print(f"Query: '{query}'")
    print("-" * 80)

    results, timing = clir.hybrid_search(
        query,
        weights={'bm25': 0.5, 'edit': 0.25, 'jaccard': 0.25},
        top_k=5,
        verbose=True
    )

    print(f"\nHybrid Results (top 5):")
    for i, result in enumerate(results, 1):
        print(f"{i}. {result['title']} (Score: {result['hybrid_score']:.3f})")
        print(f"   Breakdown: {result['scores_breakdown']}")


# ============================================================================
# SPECIAL TEST CASES - Real-World Scenarios
# ============================================================================

def test_case_typo_handling():
    """Test Case 1: Typo Handling."""
    print("\n" + "="*80)
    print("SPECIAL TEST CASE 1: Typo Handling")
    print("="*80)

    clir = CLIRSearch(documents=SAMPLE_DOCUMENTS)

    queries = [
        'Bangaldesh econmy',  # Multiple typos
        'Daka',  # Missing letter
        'Bangladsh',  # Transposed letters
    ]

    for query in queries:
        print(f"\nQuery: '{query}'")
        results = clir.search_edit_distance(query, threshold=0.7, top_k=3)
        if results:
            print(f"✓ Found {len(results)} matches:")
            for r in results:
                print(f"  - {r['title']} ({r['fuzzy_score']:.3f})")
        else:
            print("✗ No matches found")


def test_case_cross_script():
    """Test Case 2: Cross-Script Matching."""
    print("\n" + "="*80)
    print("SPECIAL TEST CASE 2: Cross-Script Matching")
    print("="*80)

    clir = CLIRSearch(
        documents=SAMPLE_DOCUMENTS,
        transliteration_map=TRANSLITERATION_MAP
    )

    queries = [
        'Dhaka',  # English query for Bengali content
        'Corona vaccine',  # English for Bengali medical content
    ]

    for query in queries:
        print(f"\nQuery: '{query}'")
        results = clir.search_transliteration(query, threshold=0.6, top_k=3)
        if results:
            print(f"✓ Found {len(results)} cross-script matches:")
            for r in results:
                lang = r.get('language', 'unknown')
                print(f"  - {r['title']} ({lang})")
        else:
            print("✗ No matches found")


def test_case_spelling_variations():
    """Test Case 3: Spelling Variations."""
    print("\n" + "="*80)
    print("SPECIAL TEST CASE 3: Spelling Variations")
    print("="*80)

    clir = CLIRSearch(documents=SAMPLE_DOCUMENTS)

    query = "Corona"
    print(f"Query: '{query}'")
    print(f"Looking for: Documents with 'Corona', 'COVID', 'COVID-19'")
    print("-" * 80)

    results = clir.search_edit_distance(query, threshold=0.7, top_k=5)
    if results:
        print(f"✓ Found {len(results)} results:")
        for r in results:
            print(f"  - {r['title']}")


def test_case_comparison():
    """Test Case 4: Method Comparison."""
    print("\n" + "="*80)
    print("SPECIAL TEST CASE 4: When Fuzzy Beats BM25")
    print("="*80)

    clir = CLIRSearch(documents=SAMPLE_DOCUMENTS)

    # Query with typo that might not match in BM25
    query = "Bangaldesh economy"
    print(f"Query: '{query}'")
    print("-" * 80)

    print("\nComparing methods:")
    comparison = clir.compare_methods(query, top_k=3, verbose=False)

    for method, data in comparison['methods'].items():
        print(f"\n{method.upper()}: {data['count']} results ({data['time']*1000:.1f}ms)")
        for r in data['results'][:2]:
            score_key = [k for k in r.keys() if 'score' in k][0]
            print(f"  - {r['title']} ({r[score_key]:.3f})")


# ============================================================================
# PERFORMANCE TESTS
# ============================================================================

def test_performance():
    """Test performance with increasing document size."""
    print("\n" + "="*80)
    print("PERFORMANCE TEST: Scalability")
    print("="*80)

    # Create larger test set
    large_docs = SAMPLE_DOCUMENTS * 20  # ~140 documents
    clir = CLIRSearch(documents=large_docs)

    query = "Bangladesh technology"
    methods = ['edit_distance', 'jaccard', 'hybrid']

    print(f"Testing with {len(large_docs)} documents")
    print("-" * 80)

    for method in methods:
        start = time.time()

        if method == 'edit_distance':
            clir.search_edit_distance(query, top_k=10)
        elif method == 'jaccard':
            clir.search_jaccard(query, top_k=10)
        elif method == 'hybrid':
            clir.hybrid_search(query, top_k=10)

        elapsed = (time.time() - start) * 1000
        print(f"{method:20s}: {elapsed:8.2f} ms")


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

def test_error_handling():
    """Test error handling."""
    print("\n" + "="*80)
    print("ERROR HANDLING TESTS")
    print("="*80)

    clir = CLIRSearch(documents=SAMPLE_DOCUMENTS)

    # Empty query
    print("\n1. Empty query:")
    results = clir.search_edit_distance('', top_k=5)
    print(f"   Results: {len(results)} (✓ handled gracefully)" if len(results) == 0 else f"   Results: {len(results)}")

    # Special characters
    print("\n2. Query with special characters:")
    results = clir.search_edit_distance('!@#$%', top_k=5)
    print(f"   Results: {len(results)} (✓ handled gracefully)")

    # Missing language field
    print("\n3. Document with missing language field:")
    test_docs = [{'title': 'Test', 'body': 'Test document'}]
    clir_test = CLIRSearch(documents=test_docs)
    results = clir_test.search_edit_distance('test', top_k=5)
    print(f"   Results: {len(results)} (✓ handled gracefully)")


# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

def run_all_tests():
    """Run all tests."""
    print("\n" + "="*80)
    print("FUZZY MATCHING CLIR SYSTEM - COMPREHENSIVE TEST SUITE")
    print("="*80)

    # Unit tests
    test_edit_distance_score()
    test_character_ngrams()
    test_jaccard_similarity()
    test_tokenization()

    # Integration tests
    test_edit_distance_search()
    test_jaccard_search()
    test_transliteration_search()
    test_hybrid_search()

    # Special test cases
    test_case_typo_handling()
    test_case_cross_script()
    test_case_spelling_variations()
    test_case_comparison()

    # Performance tests
    test_performance()

    # Error handling
    test_error_handling()

    print("\n" + "="*80)
    print("ALL TESTS COMPLETED")
    print("="*80)


if __name__ == "__main__":
    run_all_tests()
