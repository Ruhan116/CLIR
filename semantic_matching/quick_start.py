#!/usr/bin/env python3
"""Quick start for semantic search using LaBSE embeddings."""

from semantic_search import SemanticSearch


def main() -> None:
    searcher = SemanticSearch()
    stats = searcher.corpus_stats()
    print(f"Loaded {stats['num_docs']} docs | langs={stats['languages']} | dim={stats['dim']}")

    query = "coronavirus vaccine"
    results = searcher.search(query, top_k=5)

    print(f"\nQuery: {query}")
    for i, res in enumerate(results, 1):
        print(f"{i}. [{res.language}] {res.title[:80]}")
        print(f"   Score: {res.score:.4f}")
        print(f"   Source: {res.source}")
        print(f"   URL: {res.url}")
        print()


if __name__ == "__main__":
    main()
