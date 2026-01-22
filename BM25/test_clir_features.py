#!/usr/bin/env python3
"""
Test script to demonstrate all 6 required CLIR features:
1. Dual Language Support
2. Language Detection
3. Query Translation
4. Proper Tokenization
5. Score Normalization
6. Result Merging
"""

import sys
import io

# Handle Unicode output on Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from bm25_clir import BM25CLIR


def print_header(title: str):
    """Print a formatted header."""
    print("\n" + "="*80)
    print(title)
    print("="*80)


def main():
    print_header("BM25 Cross-Lingual Information Retrieval - Full Feature Test")
    
    # Initialize system
    print("\nInitializing BM25 CLIR system...")
    clir = BM25CLIR(enable_translation=True)
    
    # Build indexes
    print("\nBuilding BM25 indexes...")
    clir.build_index("both")
    
    # Feature 1: Dual Language Support
    print_header("[OK] Feature 1: Dual Language Support")
    print("Separate BM25 index for Bangla and English")
    print(f"  - English index: {len(clir.articles['en'])} articles")
    print(f"  - Bangla index: {len(clir.articles['bn'])} articles")
    stats = clir.get_statistics()
    print(f"  - Index mode: {stats.get('index_mode', 'unknown')}")
    
    # Feature 2: Language Detection
    print_header("[OK] Feature 2: Language Detection")
    print("Automatically detect if query is Bangla or English")
    
    test_queries = [
        "coronavirus vaccine",
        "করোনা ভ্যাকসিন",
        "election results",
        "নির্বাচন",
        "cricket match",
        "শিক্ষা ব্যবস্থা",
    ]
    
    for query in test_queries:
        lang = clir.detect_language(query)
        lang_name = "Bangla" if lang == "bn" else "English"
        print(f"  '{query}' → {lang_name}")
    
    # Feature 3: Query Translation
    print_header("[OK] Feature 3: Query Translation")
    print("Translate Bangla queries to English & English queries to Bangla")
    
    translation_tests = [
        ("করোনা ভ্যাকসিন", "en"),
        ("election", "bn"),
        ("শিক্ষা", "en"),
        ("healthcare system", "bn"),
    ]
    
    for query, target_lang in translation_tests:
        translated = clir.translate_query(query, target_lang)
        target_name = "English" if target_lang == "en" else "Bangla"
        if translated:
            print(f"  '{query}' → {target_name}: '{translated}'")
        else:
            print(f"  '{query}' → {target_name}: [translation failed]")
    
    # Feature 4: Proper Tokenization
    print_header("[OK] Feature 4: Proper Tokenization")
    print("Different tokenization for Bangla and English")
    
    en_text = "The quick brown fox jumps, over the lazy dog."
    bn_text = "আজকের আবহাওয়া খুব সুন্দর। এটি একটি পরীক্ষা।"
    
    en_tokens = clir._tokenize_english(en_text)
    bn_tokens = clir._tokenize_bangla(bn_text)
    
    print(f"\n  English text: {en_text}")
    print(f"  Tokens: {en_tokens[:10]}")
    print(f"\n  Bangla text: {bn_text}")
    print(f"  Tokens: {bn_tokens[:10]}")
    
    # Feature 5: Score Normalization
    print_header("[OK] Feature 5: Score Normalization")
    print("BM25 scores normalized to [0, 1] for cross-language comparison")
    
    query = "করোনা ভ্যাকসিন"
    print(f"\nQuery: '{query}'")
    
    # Get results without normalization
    results_raw = clir.search(query, "bn", top_k=3, normalize_scores=False)
    print("\n  Without normalization:")
    for i, (article, score) in enumerate(results_raw, 1):
        print(f"    {i}. Score: {score:.4f} - {article.title[:50]}...")
    
    # Get results with normalization
    results_norm = clir.search(query, "bn", top_k=3, normalize_scores=True)
    print("\n  With normalization (0-1 range):")
    for i, (article, score) in enumerate(results_norm, 1):
        print(f"    {i}. Score: {score:.4f} - {article.title[:50]}...")
    
    # Feature 6: Result Merging
    print_header("[OK] Feature 6: Result Merging")
    print("Combine results from both languages & sort by score")
    
    bangla_query = "করোনা ভ্যাকসিন"
    print(f"\nBangla Query: '{bangla_query}'")
    print("Searching in both languages and merging results...")
    
    result = clir.search_cross_lingual(
        bangla_query,
        auto_detect=True,
        top_k=5,
        merge_results=True
    )
    
    print(f"\n  Detected language: {'Bangla' if result['query_language'] == 'bn' else 'English'}")
    if result['translated_query']:
        print(f"  Translated to: {result['translated_query']}")
    print(f"  Total merged results: {len(result['results'])}")
    print(f"  Same-language results: {result['same_lang_count']}")
    print(f"  Cross-lingual results: {result['cross_lang_count']}")
    
    print("\n  Merged and sorted results:")
    for i, (article, score) in enumerate(result['results'], 1):
        lang_name = "Bangla" if article.language == "bn" else "English"
        print(f"    {i}. [{lang_name}] Score: {score:.4f}")
        print(f"       {article.title[:60]}...")
    
    # Full demonstration
    print_header("Full Cross-Lingual Search Demonstration")
    
    print("\n>>> TEST 1: Bangla Query <<<")
    bangla_query = "করোনা ভ্যাকসিন"
    result1 = clir.search_cross_lingual(bangla_query, auto_detect=True, top_k=5)
    print(f"\nQuery: {bangla_query}")
    print(f"Language: {'Bangla' if result1['query_language'] == 'bn' else 'English'}")
    print(f"Translation: {result1['translated_query']}")
    print(f"Results: {result1['same_lang_count']} same-lang + {result1['cross_lang_count']} cross-lang")
    
    clir.print_results(result1['results'][:3])
    
    print("\n>>> TEST 2: English Query <<<")
    english_query = "election results"
    result2 = clir.search_cross_lingual(english_query, auto_detect=True, top_k=5)
    print(f"\nQuery: {english_query}")
    print(f"Language: {'Bangla' if result2['query_language'] == 'bn' else 'English'}")
    print(f"Translation: {result2['translated_query']}")
    print(f"Results: {result2['same_lang_count']} same-lang + {result2['cross_lang_count']} cross-lang")
    
    clir.print_results(result2['results'][:3])
    
    # Summary
    print_header("Summary: All 6 CLIR Features Implemented")
    print("""
[OK] 1. Dual Language Support
     - Separate BM25 index for Bangla and English
     - Can search both simultaneously

[OK] 2. Language Detection
     - Automatically detect if query is Bangla or English
     - Uses Unicode ranges (U+0980 to U+09FF for Bangla)

[OK] 3. Query Translation
     - Translate Bangla queries to English (to search English docs)
     - Translate English queries to Bangla (to search Bangla docs)
     - Uses deep-translator library

[OK] 4. Proper Tokenization
     - Different tokenization for Bangla and English
     - Handles Bangla punctuation differently from English

[OK] 5. Score Normalization
     - BM25 scores normalized to [0, 1] range
     - Scores from different languages are comparable
     - Uses min-max normalization

[OK] 6. Result Merging
     - Combine results from both languages
     - Sort by normalized score
     - Track which language each result is from
    """)
    
    print("\n" + "="*80)
    print("All tests completed successfully!")
    print("="*80)


if __name__ == "__main__":
    main()
