#!/usr/bin/env python3
"""
Quick Start Guide for BM25 CLIR
================================
This script shows the simplest way to get started with BM25 search.
"""

import sys
import io

# Handle Unicode output on Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from bm25_clir import BM25CLIR


def main():
    print("Quick Start: BM25 Cross-Lingual Information Retrieval")
    print("=" * 70)
    
    # Step 1: Initialize the system
    print("\n1. Initializing BM25CLIR...")
    clir = BM25CLIR()
    print("   [OK] System initialized")
    
    # Step 2: Build the search index
    print("\n2. Building search index (this takes ~30 seconds)...")
    clir.build_index("both")  # Build for both English and Bangla
    print("   [OK] Index built successfully")
    
    # Step 3: Try some searches
    print("\n3. Running example searches...")
    print("-" * 70)
    
    # English search
    print("\n[SEARCH] ENGLISH SEARCH: 'climate change'")
    results = clir.search("climate change", language="en", top_k=3)
    for i, (article, score) in enumerate(results, 1):
        print(f"\n{i}. {article.title}")
        print(f"   Score: {score:.2f} | Source: {article.source}")
        print(f"   {article.body[:120]}...")
    
    # Bangla search
    print("\n\n[SEARCH] BANGLA SEARCH: 'shikkha' (education)")
    results = clir.search("শিক্ষা", language="bn", top_k=3)
    for i, (article, score) in enumerate(results, 1):
        print(f"\n{i}. {article.title}")
        print(f"   Score: {score:.2f} | Source: {article.source}")
        print(f"   {article.body[:120]}...")
    
    # Statistics
    print("\n\n4. Dataset Statistics")
    print("-" * 70)
    stats = clir.get_statistics()
    print(f"Total articles: {stats['total_articles']}")
    print(f"English: {stats['english_articles']}, Bangla: {stats['bangla_articles']}")
    
    print("\n\n[DONE] Quick start completed!")
    print("\nNext steps:")
    print("  - See bm25_usage_examples.py for more examples")
    print("  - Run 'python bm25_usage_examples.py interactive' for interactive mode")
    print("  - Check README.md for full documentation")
    

if __name__ == "__main__":
    main()
