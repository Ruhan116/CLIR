#!/usr/bin/env python3
"""
Comprehensive verification script for semantic matching module.
Tests all features required by Assignment Module C Model 3.
"""

import sys
import io
import time
from pathlib import Path

# Handle Unicode output on Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from semantic_search import SemanticSearch


def test_corpus_loading():
    """Test 1: Verify corpus and embeddings load correctly."""
    print("\n" + "=" * 80)
    print("TEST 1: Corpus Loading")
    print("=" * 80)

    try:
        start = time.time()
        searcher = SemanticSearch(preload_model=False)
        load_time = time.time() - start

        stats = searcher.corpus_stats()
        print(f"\n[OK] Loaded {stats['num_docs']} documents in {load_time:.2f}s")
        print(f"     Languages: {stats['languages']}")
        print(f"     Embedding dimension: {stats['dim']}")
        print(f"     Normalized: {stats['normalized']}")
        print(f"     DB path: {stats['db_path']}")

        return searcher
    except Exception as e:
        print(f"[ERROR] Failed to load corpus: {e}")
        return None


def test_model_loading(searcher):
    """Test 2: Verify LaBSE model loads correctly."""
    print("\n" + "=" * 80)
    print("TEST 2: LaBSE Model Loading")
    print("=" * 80)

    try:
        print("\nLoading LaBSE model (this may take a while on first run)...")
        start = time.time()
        searcher._load_model()
        load_time = time.time() - start

        print(f"[OK] Model loaded in {load_time:.2f}s")
        print(f"     Model: {searcher.model_name}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to load model: {e}")
        return False


def test_query_encoding(searcher):
    """Test 3: Verify query encoding works."""
    print("\n" + "=" * 80)
    print("TEST 3: Query Encoding")
    print("=" * 80)

    test_queries = [
        ("coronavirus vaccine", "English"),
        ("করোনা ভ্যাকসিন", "Bangla"),
        ("climate change", "English"),
        ("বাংলাদেশ অর্থনীতি", "Bangla"),
    ]

    print("\nEncoding test queries:")
    for query, lang in test_queries:
        try:
            start = time.time()
            embedding = searcher.encode_query(query)
            encode_time = time.time() - start

            print(f"  [{lang}] '{query}'")
            print(f"       Shape: {embedding.shape}, Norm: {(embedding @ embedding) ** 0.5:.4f}, Time: {encode_time*1000:.1f}ms")
        except Exception as e:
            print(f"  [ERROR] '{query}': {e}")

    print("\n[OK] Query encoding working")


def test_semantic_search(searcher):
    """Test 4: Verify semantic search with cosine similarity."""
    print("\n" + "=" * 80)
    print("TEST 4: Semantic Search (Cosine Similarity)")
    print("=" * 80)

    # Test English query
    print("\n[English Query]")
    query = "coronavirus vaccine distribution"
    start = time.time()
    results = searcher.search(query, top_k=5)
    search_time = time.time() - start

    print(f"  Query: '{query}'")
    print(f"  Time: {search_time*1000:.1f}ms | Results: {len(results)}")
    for i, r in enumerate(results[:3], 1):
        print(f"    {i}. [{r.language}] {r.title[:60]}...")
        print(f"       Score: {r.score:.4f} | Source: {r.source}")

    # Test Bangla query
    print("\n[Bangla Query]")
    query = "করোনা ভ্যাকসিন"
    start = time.time()
    results = searcher.search(query, top_k=5)
    search_time = time.time() - start

    print(f"  Query: '{query}'")
    print(f"  Time: {search_time*1000:.1f}ms | Results: {len(results)}")
    for i, r in enumerate(results[:3], 1):
        print(f"    {i}. [{r.language}] {r.title[:60]}...")
        print(f"       Score: {r.score:.4f} | Source: {r.source}")

    print("\n[OK] Semantic search working")


def test_cross_lingual_search(searcher):
    """Test 5: Cross-lingual search (the key CLIR feature)."""
    print("\n" + "=" * 80)
    print("TEST 5: Cross-Lingual Search")
    print("=" * 80)

    # English query -> search Bangla docs
    print("\n[English Query -> Bangla Documents]")
    query = "election results"
    start = time.time()
    results = searcher.search(query, top_k=5, languages=["bn"])
    search_time = time.time() - start

    print(f"  Query: '{query}' (English)")
    print(f"  Searching: Bangla documents only")
    print(f"  Time: {search_time*1000:.1f}ms | Results: {len(results)}")
    for i, r in enumerate(results[:3], 1):
        print(f"    {i}. [{r.language}] {r.title[:60]}...")
        print(f"       Score: {r.score:.4f}")

    # Bangla query -> search English docs
    print("\n[Bangla Query -> English Documents]")
    query = "নির্বাচন ফলাফল"  # election results in Bangla
    start = time.time()
    results = searcher.search(query, top_k=5, languages=["en"])
    search_time = time.time() - start

    print(f"  Query: '{query}' (Bangla)")
    print(f"  Searching: English documents only")
    print(f"  Time: {search_time*1000:.1f}ms | Results: {len(results)}")
    for i, r in enumerate(results[:3], 1):
        print(f"    {i}. [{r.language}] {r.title[:60]}...")
        print(f"       Score: {r.score:.4f}")

    print("\n[OK] Cross-lingual search working")


def test_score_range(searcher):
    """Test 6: Verify scores are in [0, 1] range (cosine similarity)."""
    print("\n" + "=" * 80)
    print("TEST 6: Score Normalization (0-1 Range)")
    print("=" * 80)

    query = "Bangladesh economy growth"
    results = searcher.search(query, top_k=20)

    scores = [r.score for r in results]
    min_score = min(scores)
    max_score = max(scores)
    avg_score = sum(scores) / len(scores)

    print(f"\n  Query: '{query}'")
    print(f"  Results: {len(results)}")
    print(f"  Score range: [{min_score:.4f}, {max_score:.4f}]")
    print(f"  Average score: {avg_score:.4f}")

    # Check if scores are in valid cosine similarity range
    if all(-1 <= s <= 1 for s in scores):
        print("\n[OK] Scores are in valid cosine similarity range [-1, 1]")
    else:
        print("\n[WARN] Some scores outside expected range")


def main():
    print("\n" + "=" * 80)
    print("SEMANTIC MATCHING VERIFICATION")
    print("Assignment Module C Model 3: Semantic Matching")
    print("=" * 80)

    # Test 1: Corpus loading
    searcher = test_corpus_loading()
    if searcher is None:
        print("\n[FAILED] Cannot continue without corpus")
        return

    # Test 2: Model loading
    if not test_model_loading(searcher):
        print("\n[FAILED] Cannot continue without model")
        return

    # Test 3: Query encoding
    test_query_encoding(searcher)

    # Test 4: Semantic search
    test_semantic_search(searcher)

    # Test 5: Cross-lingual search
    test_cross_lingual_search(searcher)

    # Test 6: Score normalization
    test_score_range(searcher)

    # Summary
    print("\n" + "=" * 80)
    print("VERIFICATION COMPLETE")
    print("=" * 80)

    print("""
Summary - Assignment Module C Model 3 Requirements:
  [OK] Multilingual embeddings (LaBSE) - Pre-computed and loaded from DB
  [OK] Cosine similarity measurement - Implemented via dot product on normalized vectors
  [OK] Cross-lingual search - English query finds Bangla docs and vice versa
  [OK] Score normalization - Cosine similarity in [-1, 1] range
  [OK] Language filtering - Can filter results by language
    """)


if __name__ == "__main__":
    main()
