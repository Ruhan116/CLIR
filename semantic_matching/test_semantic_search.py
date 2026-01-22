#!/usr/bin/env python3
"""Smoke test for semantic matching with LaBSE embeddings.

This test intentionally avoids heavy assertions and exits gracefully if the
database or embeddings are missing. It is meant for local verification, not CI.
"""

import sys
import io
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from semantic_search import SemanticSearch  # noqa: E402


def main() -> int:
    db_path = Path(__file__).parent / "combined_dataset.db"
    if not db_path.exists():
        print(f"Skipping: database not found at {db_path}")
        return 0

    try:
        searcher = SemanticSearch(db_path=db_path, preload_model=False)
    except Exception as exc:  # noqa: BLE001
        print(f"Failed to load searcher: {exc}")
        return 1

    # Lazy load model for the first query
    try:
        results = searcher.search("coronavirus vaccine", top_k=3)
    except Exception as exc:  # noqa: BLE001
        print(f"Search failed: {exc}")
        return 1

    print(f"Retrieved {len(results)} results")
    for i, res in enumerate(results, 1):
        print(f"{i}. [{res.language}] {res.title[:60]}... (score={res.score:.4f})")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
