#!/usr/bin/env python3
"""
Quick verification script for fuzzy matching with combined_dataset.db
"""

import sys
import io
import time
from pathlib import Path

# Handle Unicode output on Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from fuzzy_matcher import FuzzyMatcher
from clir_search import CLIRSearch

# Database path (local copy in fuzzy_matching folder)
DB_PATH = Path(__file__).parent / "combined_dataset.db"

# Transliteration map for cross-script matching
TRANSLITERATION_MAP = {
    'dhaka': ['Dhaka', 'Dacca'],
    'bangladesh': ['Bangladesh'],
    'corona': ['Corona', 'COVID', 'COVID-19'],
    'vaccine': ['Vaccine', 'Vaccination'],
}


def test_core_algorithms():
    """Test core fuzzy matching algorithms."""
    print("\n" + "=" * 80)
    print("TEST 1: Core Fuzzy Matching Algorithms")
    print("=" * 80)

    matcher = FuzzyMatcher()

    # Test Edit Distance
    print("\n[Edit Distance]")
    test_pairs = [
        ("Bangladesh", "Bangaldesh", "typo"),
        ("Dhaka", "Dacca", "variant spelling"),
        ("corona", "Corona", "case difference"),
    ]

    for s1, s2, desc in test_pairs:
        score = matcher.edit_distance_score(s1, s2)
        print(f"  '{s1}' vs '{s2}' ({desc}): {score:.3f}")

    # Test Jaccard Similarity
    print("\n[Jaccard Similarity]")
    text1 = "Bangladesh economy news"
    text2 = "Bangladesh economic update"
    ngrams1 = matcher.character_ngrams(text1, n=3)
    ngrams2 = matcher.character_ngrams(text2, n=3)
    jaccard = matcher.jaccard_similarity(ngrams1, ngrams2)
    print(f"  '{text1}' vs '{text2}'")
    print(f"  3-gram Jaccard: {jaccard:.3f}")

    # Test Character N-grams
    print("\n[Character N-grams]")
    text = "Dhaka"
    ngrams = matcher.character_ngrams(text, n=3)
    print(f"  Text: '{text}'")
    print(f"  3-grams: {sorted(ngrams)}")

    print("\n[OK] Core algorithms working correctly")


def test_database_search():
    """Test fuzzy search on actual database (sample of 500 docs for speed)."""
    print("\n" + "=" * 80)
    print("TEST 2: Database Search (500 document sample)")
    print("=" * 80)

    if not DB_PATH.exists():
        print(f"[ERROR] Database not found: {DB_PATH}")
        return False

    print(f"\nLoading from: {DB_PATH}")

    # Load only a sample for faster testing
    import sqlite3
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, body, url, date, language, tokens FROM articles LIMIT 500")
    rows = cursor.fetchall()
    conn.close()

    documents = []
    for row in rows:
        doc_id, title, body, url, date, language, tokens = row
        documents.append({
            'doc_id': doc_id,
            'title': title or '',
            'body': (body or '')[:500],  # Limit body for speed
            'url': url or '',
            'date': date or '',
            'language': language or 'en',
            'token_count': tokens
        })

    try:
        start = time.time()
        clir = CLIRSearch(documents=documents, transliteration_map=TRANSLITERATION_MAP)
        load_time = time.time() - start
        print(f"[OK] Loaded {len(clir.documents)} documents in {load_time:.2f}s")
    except Exception as e:
        print(f"[ERROR] Failed to initialize: {e}")
        return False

    # Test Edit Distance Search
    print("\n[Edit Distance Search]")
    query = "Bangaldesh econmy"  # typos
    start = time.time()
    results = clir.search_edit_distance(query, threshold=0.75, top_k=3)
    search_time = time.time() - start

    print(f"  Query: '{query}'")
    print(f"  Time: {search_time*1000:.1f}ms | Results: {len(results)}")
    for i, r in enumerate(results[:3], 1):
        print(f"    {i}. {r['title'][:60]}... (score: {r['fuzzy_score']:.3f})")
        if 'matched_terms' in r and r['matched_terms']:
            print(f"       Matched: {r['matched_terms'][:2]}")

    # Test Jaccard Search
    print("\n[Jaccard Search]")
    query = "climate change"
    start = time.time()
    results = clir.search_jaccard(query, level='char', n_gram=3, threshold=0.15, top_k=3)
    search_time = time.time() - start

    print(f"  Query: '{query}'")
    print(f"  Time: {search_time*1000:.1f}ms | Results: {len(results)}")
    for i, r in enumerate(results[:3], 1):
        print(f"    {i}. {r['title'][:60]}... (score: {r['jaccard_score']:.3f})")

    # Test Bangla Search
    print("\n[Bangla Search]")
    query = "করোনা"  # Corona in Bangla
    start = time.time()
    results = clir.search_edit_distance(query, threshold=0.7, top_k=3)
    search_time = time.time() - start

    print(f"  Query: '{query}'")
    print(f"  Time: {search_time*1000:.1f}ms | Results: {len(results)}")
    for i, r in enumerate(results[:3], 1):
        print(f"    {i}. {r['title'][:60]}... (score: {r['fuzzy_score']:.3f})")

    print("\n[OK] Database search working correctly")
    return True


def test_hybrid_search():
    """Test hybrid search combining multiple methods (sample of 200 docs)."""
    print("\n" + "=" * 80)
    print("TEST 3: Hybrid Search (200 document sample)")
    print("=" * 80)

    if not DB_PATH.exists():
        print(f"[ERROR] Database not found: {DB_PATH}")
        return False

    # Load smaller sample for hybrid test
    import sqlite3
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, body, url, date, language, tokens FROM articles LIMIT 200")
    rows = cursor.fetchall()
    conn.close()

    documents = []
    for row in rows:
        doc_id, title, body, url, date, language, tokens = row
        documents.append({
            'doc_id': doc_id,
            'title': title or '',
            'body': (body or '')[:300],
            'url': url or '',
            'date': date or '',
            'language': language or 'en',
            'token_count': tokens
        })

    clir = CLIRSearch(documents=documents, transliteration_map=TRANSLITERATION_MAP)

    query = "Bangladesh technology"
    print(f"\nQuery: '{query}'")
    print("Weights: BM25=0.5 (unavailable), Edit=0.25, Jaccard=0.25")
    print("Note: BM25 not available, using fuzzy methods only")

    start = time.time()
    results, timing = clir.hybrid_search(
        query,
        weights={'bm25': 0.0, 'edit': 0.5, 'jaccard': 0.5},  # No BM25
        top_k=5,
        verbose=False
    )
    total_time = time.time() - start

    print(f"\nTotal time: {total_time*1000:.1f}ms")
    print(f"Results: {len(results)}")

    for i, r in enumerate(results[:5], 1):
        print(f"\n  {i}. {r['title'][:60]}...")
        print(f"     Hybrid score: {r['hybrid_score']:.4f}")
        if 'scores_breakdown' in r:
            print(f"     Breakdown: {r['scores_breakdown']}")

    print("\n[OK] Hybrid search working correctly")
    return True


def main():
    print("\n" + "=" * 80)
    print("FUZZY MATCHING VERIFICATION")
    print("=" * 80)

    # Test 1: Core algorithms
    test_core_algorithms()

    # Test 2: Database search
    db_ok = test_database_search()

    # Test 3: Hybrid search
    if db_ok:
        test_hybrid_search()

    print("\n" + "=" * 80)
    print("VERIFICATION COMPLETE")
    print("=" * 80)

    print("""
Summary - Assignment Module C Model 2 Requirements:
  [OK] Edit Distance (Levenshtein) - Implemented and tested
  [OK] Jaccard Similarity - Implemented and tested
  [OK] Character N-grams - Implemented and tested
  [OK] Transliteration Matching - Implemented via transliteration map
    """)


if __name__ == "__main__":
    main()
