#!/usr/bin/env python3
"""Examples of using the BM25CLIR system for various search tasks."""

from bm25_clir import BM25CLIR


def example_1_basic_english_search():
    """Example 1: Basic English search."""
    print("\n" + "="*80)
    print("EXAMPLE 1: Basic English Search")
    print("="*80)
    
    # Initialize and build index
    clir = BM25CLIR()
    clir.build_index("en")  # Only English index
    
    # Search
    query = "cricket match Bangladesh"
    print(f"\nQuery: '{query}'")
    results = clir.search(query, language="en", top_k=5)
    clir.print_results(results, max_body_length=150)


def example_2_basic_bangla_search():
    """Example 2: Basic Bangla search."""
    print("\n" + "="*80)
    print("EXAMPLE 2: Basic Bangla Search")
    print("="*80)
    
    # Initialize and build index
    clir = BM25CLIR()
    clir.build_index("bn")  # Only Bangla index
    
    # Search
    query = "নির্বাচন"
    print(f"\nQuery: '{query}'")
    results = clir.search(query, language="bn", top_k=5)
    clir.print_results(results, max_body_length=150)


def example_3_compare_languages():
    """Example 3: Compare search results across languages."""
    print("\n" + "="*80)
    print("EXAMPLE 3: Compare Search Across Languages")
    print("="*80)
    
    # Initialize and build both indexes
    clir = BM25CLIR()
    clir.build_index("both")
    
    # Same query in both languages
    queries = {
        "en": "government policy economic",
        "bn": "সরকার নীতি অর্থনীতি"
    }
    
    for lang, query in queries.items():
        print(f"\n{lang.upper()} Query: '{query}'")
        results = clir.search(query, language=lang, top_k=3)
        clir.print_results(results, max_body_length=100)


def example_4_multilingual_search():
    """Example 4: Multilingual search (search both languages)."""
    print("\n" + "="*80)
    print("EXAMPLE 4: Multilingual Search")
    print("="*80)
    
    # Initialize
    clir = BM25CLIR()
    clir.build_index("both")
    
    # Search across both languages
    query = "health"
    print(f"\nQuery: '{query}' (searching both EN and BN)")
    
    results = clir.search_multilingual(
        query=query,
        query_lang="en",
        results_per_lang=3  # Get 3 results from each language
    )
    
    print(f"\nEnglish Results ({len(results['en'])}):")
    clir.print_results(results['en'], max_body_length=100)
    
    print(f"\nBangla Results ({len(results['bn'])}):")
    clir.print_results(results['bn'], max_body_length=100)


def example_5_custom_scoring():
    """Example 5: Get raw scores and do custom processing."""
    print("\n" + "="*80)
    print("EXAMPLE 5: Custom Score Processing")
    print("="*80)
    
    # Initialize
    clir = BM25CLIR()
    clir.build_index("en")
    
    # Search
    query = "technology innovation"
    print(f"\nQuery: '{query}'")
    results = clir.search(query, language="en", top_k=10)
    
    # Custom processing
    print("\nScore distribution:")
    if results:
        scores = [score for _, score in results]
        print(f"  Max score: {max(scores):.4f}")
        print(f"  Min score: {min(scores):.4f}")
        print(f"  Average: {sum(scores)/len(scores):.4f}")
        
        # Filter by score threshold
        threshold = 10.0
        filtered = [(art, sc) for art, sc in results if sc >= threshold]
        print(f"\nArticles with score >= {threshold}: {len(filtered)}")


def example_6_batch_queries():
    """Example 6: Process multiple queries efficiently."""
    print("\n" + "="*80)
    print("EXAMPLE 6: Batch Query Processing")
    print("="*80)
    
    # Initialize once
    clir = BM25CLIR()
    clir.build_index("both")
    
    # Multiple queries
    queries = [
        ("en", "sports football"),
        ("en", "climate change"),
        ("bn", "শিক্ষা"),
        ("bn", "খেলাধুলা"),
    ]
    
    print("\nProcessing multiple queries:")
    for lang, query in queries:
        results = clir.search(query, language=lang, top_k=1)
        if results:
            article, score = results[0]
            print(f"\n[{lang.upper()}] '{query}' → {article.title[:60]}... (score: {score:.2f})")
        else:
            print(f"\n[{lang.upper()}] '{query}' → No results")


def example_7_get_article_details():
    """Example 7: Retrieve specific article details."""
    print("\n" + "="*80)
    print("EXAMPLE 7: Retrieve Article by ID")
    print("="*80)
    
    # Initialize
    clir = BM25CLIR()
    clir.build_index("en")
    
    # First search to get an article ID
    results = clir.search("education", language="en", top_k=1)
    if results:
        article, score = results[0]
        article_id = article.id
        
        print(f"\nRetrieving article ID: {article_id}")
        retrieved = clir.get_article_by_id(article_id, "en")
        
        if retrieved:
            print(f"\nTitle: {retrieved.title}")
            print(f"Source: {retrieved.source}")
            print(f"Date: {retrieved.date}")
            print(f"URL: {retrieved.url}")
            print(f"Body length: {len(retrieved.body)} characters")


def example_8_statistics():
    """Example 8: Get dataset statistics."""
    print("\n" + "="*80)
    print("EXAMPLE 8: Dataset Statistics")
    print("="*80)
    
    # Initialize
    clir = BM25CLIR()
    stats = clir.get_statistics()
    
    print("\nDataset Overview:")
    print(f"  Total articles: {stats['total_articles']}")
    print(f"  English articles: {stats['english_articles']}")
    print(f"  Bangla articles: {stats['bangla_articles']}")
    
    print("\nArticles by source:")
    for source, count in sorted(stats['sources'].items(), key=lambda x: x[1], reverse=True):
        print(f"  {source:25s}: {count:4d} articles")


def interactive_search():
    """Interactive search mode."""
    print("\n" + "="*80)
    print("INTERACTIVE SEARCH MODE")
    print("="*80)
    
    # Initialize
    clir = BM25CLIR()
    clir.build_index("both")
    
    print("\nSystem ready! Enter your queries.")
    print("Commands:")
    print("  - Type your query to search")
    print("  - Prefix with 'bn:' for Bangla search (e.g., 'bn:করোনা')")
    print("  - Type 'stats' to see statistics")
    print("  - Type 'quit' to exit")
    
    while True:
        try:
            query = input("\n> ").strip()
            
            if query.lower() == "quit":
                break
            elif query.lower() == "stats":
                stats = clir.get_statistics()
                print(f"\nTotal: {stats['total_articles']} | EN: {stats['english_articles']} | BN: {stats['bangla_articles']}")
            elif query.startswith("bn:"):
                # Bangla search
                bn_query = query[3:].strip()
                results = clir.search(bn_query, language="bn", top_k=5)
                clir.print_results(results, max_body_length=150)
            elif query:
                # English search
                results = clir.search(query, language="en", top_k=5)
                clir.print_results(results, max_body_length=150)
                
        except KeyboardInterrupt:
            print("\nExiting...")
            break


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "interactive":
        # Run interactive mode
        interactive_search()
    else:
        # Run all examples
        print("\nBM25 CLIR Usage Examples")
        print("=" * 80)
        print("\nRunning all examples...")
        print("(Run with 'interactive' argument for interactive mode)")
        
        example_1_basic_english_search()
        example_2_basic_bangla_search()
        example_3_compare_languages()
        example_4_multilingual_search()
        example_5_custom_scoring()
        example_6_batch_queries()
        example_7_get_article_details()
        example_8_statistics()
        
        print("\n" + "="*80)
        print("All examples completed!")
        print("="*80)
