#!/usr/bin/env python3
"""
Generate Labeling Pool (Pooled Relevance Feedback).

This script:
1. Takes a set of queries.
2. Runs them against BM25, Semantic, and Hybrid models.
3. Collects the top K results from each model.
4. Pools them (removes duplicates).
5. Exports a CSV for the user to manually label (0 or 1).

Usage:
    python generate_labeling_pool.py
"""

import csv
import sys
import os
from pathlib import Path

# Add project root to path for imports
sys.path.append(str(Path(__file__).parent))

try:
    from BM25.bm25_clir import BM25CLIR
except ImportError:
    BM25CLIR = None
    print("Warning: could not import BM25CLIR")

try:
    from semantic_matching.semantic_search import SemanticSearch
except ImportError:
    SemanticSearch = None
    print("Warning: could not import SemanticSearch (sentence_transformers likely missing)")

try:
    from fuzzy_matching.clir_search import CLIRSearch
except ImportError:
    CLIRSearch = None
    print("Warning: could not import CLIRSearch")

# --- CONFIGURATION ---
TOP_K_POOL = 10  # Number of docs to take from each model per query
OUTPUT_FILE = "labeled_queries.csv"

# List of queries to generate pool for (Mix of English and Bangla)
QUERIES = [
    "coronavirus vaccine",
    "করোনা ভ্যাকসিন",
    "flood situation in sylhet",
    "সিলেটে বন্যা পরিস্থিতি",
    "padma bridge inauguration",
    "পদ্মা সেতু উদ্বোধন",
    "cricket world cup 2023",
    "বিশ্বকাপ ক্রিকেট ২০২৩",
    "inflation rate in bangladesh",
    "বাংলাদেশে মুদ্রাস্ফীতি",
    "rohingya refugee crisis",
    "রোহিঙ্গা শরণার্থী সংকট",
    "metro rail dhaka",
    "মেট্রোরেল ঢাকা",
    "dengue outbreak",
    "ডেঙ্গু প্রকোপ",
    "national election 2024",
    "জাতীয় নির্বাচন ২০২৪"
]

def main():
    # Handle Unicode output on Windows
    if sys.platform == 'win32':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

    print("="*80)
    print("Generating Labeling Pool for Evaluation")
    print("="*80)

    # 1. Initialize Models
    print("\n[1/4] Initializing Retrieval Models...")
    
    # BM25
    print("  - Loading BM25...")
    try:
        bm25 = BM25CLIR(enable_translation=True)
        # Ensure index exists
        if not bm25.use_inverted_index and not bm25.bm25_models['en']:
             bm25.build_index("both")
    except Exception as e:
        print(f"    Error loading BM25: {e}")
        bm25 = None

    # Semantic
    print("  - Loading Semantic Search (LaBSE)...")
    try:
        semantic = SemanticSearch(preload_model=True)
    except Exception as e:
        print(f"    Error loading Semantic Search: {e}")
        semantic = None

    # Hybrid (Fuzzy + BM25)
    print("  - Loading Hybrid Search...")
    try:
        hybrid = CLIRSearch(db_path=str(bm25.db_path) if bm25 else None)
    except Exception as e:
        print(f"    Error loading Hybrid Search: {e}")
        hybrid = None

    if not any([bm25, semantic, hybrid]):
        print("CRITICAL: No models loaded. Exiting.")
        return

    # 2. Process Queries
    print(f"\n[2/4] Processing {len(QUERIES)} queries...")
    
    pool_data = [] # List of (query, doc_url, title, language) tuples
    seen_pairs = set() # (query, doc_url) to avoid duplicates

    for q_idx, query in enumerate(QUERIES, 1):
        print(f"  [{q_idx}/{len(QUERIES)}] Query: {query}")
        
        # --- BM25 ---
        if bm25:
            # Auto-detect language and search cross-lingual
            res = bm25.search_cross_lingual(query, top_k=TOP_K_POOL, merge_results=True)
            for art, score in res['results']:
                if (query, art.url) not in seen_pairs:
                    pool_data.append({
                        'query': query, 
                        'doc_url': art.url, 
                        'language': art.language,
                        'title': art.title,
                        'source': 'BM25'
                    })
                    seen_pairs.add((query, art.url))

        # --- Semantic ---
        if semantic:
            # Semantic search handles languages, we can just pass the query
            res = semantic.search(query, top_k=TOP_K_POOL)
            for item in res:
                if (query, item.url) not in seen_pairs:
                    pool_data.append({
                        'query': query,
                        'doc_url': item.url,
                        'language': item.language,
                        'title': item.title,
                        'source': 'Semantic'
                    })
                    seen_pairs.add((query, item.url))

        # --- Hybrid ---
        if hybrid:
            # Using hybrid search (BM25 + Fuzzy)
            # weights={'bm25': 0.4, 'edit': 0.3, 'jaccard': 0.3} (default-ish)
            res, _ = hybrid.hybrid_search(query, top_k=TOP_K_POOL)
            for item in res:
                if (query, item['url']) not in seen_pairs:
                    pool_data.append({
                        'query': query,
                        'doc_url': item['url'],
                        'language': item['language'],
                        'title': item['title'],
                        'source': 'Hybrid'
                    })
                    seen_pairs.add((query, item['url']))

    # 3. Export to CSV
    print(f"\n[3/4] Exporting {len(pool_data)} unique pairs to {OUTPUT_FILE}...")
    
    file_exists = os.path.isfile(OUTPUT_FILE)
    
    with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        # Header
        writer.writerow(['query', 'doc_url', 'language', 'relevant', 'annotator', 'title', 'notes'])
        
        for row in pool_data:
            writer.writerow([
                row['query'],
                row['doc_url'],
                row['language'],
                '',  # relevant (to be filled by user)
                '',  # annotator
                row['title'],
                f"Source: {row['source']}" # notes
            ])

    print("\n[4/4] Done!")
    print(f"\nACTION REQUIRED: Open '{OUTPUT_FILE}' and fill the 'relevant' column.")
    print("  - 1 = Relevant")
    print("  - 0 = Not Relevant")
    print("  - Leave empty if unsure (will be treated as not relevant)")

if __name__ == "__main__":
    main()
