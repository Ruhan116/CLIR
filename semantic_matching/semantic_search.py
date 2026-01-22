#!/usr/bin/env python3
"""Semantic search over LaBSE embeddings stored in combined_dataset.db.

Features:
- Loads precomputed document embeddings from SQLite (word_embeddings column)
- Encodes queries with LaBSE at search time
- Cosine similarity ranking with optional language filter
- Small, dependency-light API to integrate with the existing CLIR stack

Usage (see quick_start.py):
    searcher = SemanticSearch()
    results = searcher.search("coronavirus vaccine", top_k=5)

Notes:
- Default database path: semantic_matching/combined_dataset.db (copied LFS file)
- If you prefer to reference a single source of truth, pass db_path pointing to
  dataset_enhanced/combined_dataset.db or BM25/combined_dataset.db.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence

import numpy as np
from sentence_transformers import SentenceTransformer


@dataclass
class SemanticResult:
    """Container for a ranked semantic result."""

    article_id: int
    source: str
    title: str
    body: str
    url: str
    date: str
    language: str
    score: float


class SemanticSearch:
    """Semantic retrieval using LaBSE embeddings and cosine similarity."""

    def __init__(
        self,
        db_path: Optional[str] = None,
        model_name: str = "sentence-transformers/LaBSE",
        device: Optional[str] = None,
        preload_model: bool = True,
        normalize_embeddings: bool = True,
    ) -> None:
        """
        Args:
            db_path: Path to SQLite DB with `articles.word_embeddings` JSON arrays.
            model_name: SentenceTransformer model name (defaults to LaBSE).
            device: Optional device string for SentenceTransformer (e.g., "cpu", "cuda").
            preload_model: Load the model immediately. Set False to lazy-load on first query.
            normalize_embeddings: If True, store normalized doc embeddings and use cosine via dot product.
        """
        self.db_path = Path(db_path) if db_path else Path(__file__).parent / "combined_dataset.db"
        self.model_name = model_name
        self.device = device
        self.normalize_embeddings = normalize_embeddings

        self._model: Optional[SentenceTransformer] = None
        self._articles: List[Dict] = []
        self._embeddings: Optional[np.ndarray] = None
        self._embedding_norms: Optional[np.ndarray] = None

        self._load_corpus()
        if preload_model:
            self._load_model()

    def _load_model(self) -> None:
        if self._model is None:
            self._model = SentenceTransformer(self.model_name, device=self.device)

    def _load_corpus(self) -> None:
        """Load articles and embeddings from SQLite into memory."""
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found: {self.db_path}")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, source, title, body, url, date, language, word_embeddings
            FROM articles
            WHERE word_embeddings IS NOT NULL AND word_embeddings != ''
            """
        )
        rows = cursor.fetchall()
        conn.close()

        articles: List[Dict] = []
        vectors: List[np.ndarray] = []

        for row in rows:
            article_id, source, title, body, url, date, language, embedding_json = row
            try:
                vec = np.array(json.loads(embedding_json), dtype=np.float32)
                if vec.ndim != 1:
                    continue
                articles.append(
                    {
                        "article_id": article_id,
                        "source": source or "",
                        "title": title or "",
                        "body": body or "",
                        "url": url or "",
                        "date": date or "",
                        "language": language or "",
                    }
                )
                vectors.append(vec)
            except Exception:
                # Skip malformed embeddings
                continue

        if not vectors:
            raise RuntimeError("No valid embeddings loaded from database.")

        emb = np.vstack(vectors)
        if self.normalize_embeddings:
            norms = np.linalg.norm(emb, axis=1, keepdims=True)
            norms[norms == 0] = 1.0
            emb = emb / norms
            self._embedding_norms = None
        else:
            self._embedding_norms = np.linalg.norm(emb, axis=1)
        self._embeddings = emb
        self._articles = articles

    def encode_query(self, query: str) -> np.ndarray:
        """Encode a query to a normalized embedding."""
        if not query or not query.strip():
            raise ValueError("Query is empty")
        if self._model is None:
            self._load_model()
        qvec = self._model.encode(query)
        qvec = np.array(qvec, dtype=np.float32)
        if self.normalize_embeddings:
            norm = np.linalg.norm(qvec)
            if norm == 0:
                norm = 1.0
            qvec = qvec / norm
        return qvec

    def search(
        self,
        query: str,
        top_k: int = 10,
        languages: Optional[Sequence[str]] = None,
        min_score: Optional[float] = None,
    ) -> List[SemanticResult]:
        """Semantic search using cosine similarity.

        Args:
            query: Query text.
            top_k: Number of results to return.
            languages: Optional language filter (e.g., ["en"], ["bn"], or ["en","bn"]).
            min_score: Optional minimum cosine similarity threshold (0-1 when normalized).
        """
        if self._embeddings is None:
            raise RuntimeError("Embeddings not loaded.")

        qvec = self.encode_query(query)

        # Compute cosine similarity (dot product if normalized)
        scores = self._embeddings @ qvec
        if not self.normalize_embeddings:
            qnorm = np.linalg.norm(qvec)
            if qnorm == 0:
                qnorm = 1.0
            denom = self._embedding_norms * qnorm
            denom[denom == 0] = 1.0
            scores = scores / denom

        mask = None
        if languages:
            allowed = set(languages)
            mask = np.array([a["language"] in allowed for a in self._articles], dtype=bool)
            scores = np.where(mask, scores, -np.inf)

        # Get top-k indices
        top_k = max(1, top_k)
        top_idx = np.argpartition(-scores, range(min(top_k, len(scores))))[:top_k]
        top_idx = top_idx[np.argsort(scores[top_idx])[::-1]]

        results: List[SemanticResult] = []
        for idx in top_idx:
            score = float(scores[idx])
            if min_score is not None and score < min_score:
                continue
            meta = self._articles[idx]
            results.append(
                SemanticResult(
                    article_id=meta["article_id"],
                    source=meta["source"],
                    title=meta["title"],
                    body=meta["body"],
                    url=meta["url"],
                    date=meta["date"],
                    language=meta["language"],
                    score=score,
                )
            )
        return results

    def corpus_stats(self) -> Dict[str, int]:
        """Return basic corpus statistics."""
        langs = {}
        for a in self._articles:
            lang = a["language"] or ""
            langs[lang] = langs.get(lang, 0) + 1
        return {
            "num_docs": len(self._articles),
            "languages": langs,
            "dim": int(self._embeddings.shape[1]) if self._embeddings is not None else 0,
            "normalized": bool(self.normalize_embeddings),
            "db_path": str(self.db_path),
        }


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Semantic search with LaBSE embeddings")
    parser.add_argument("query", help="Query text")
    parser.add_argument("--top_k", type=int, default=5, help="Number of results to return")
    parser.add_argument(
        "--language",
        action="append",
        dest="languages",
        help="Filter languages (can be repeated, e.g., --language en --language bn)",
    )
    parser.add_argument("--db", dest="db_path", help="Path to combined_dataset.db")
    parser.add_argument("--model", dest="model_name", default="sentence-transformers/LaBSE")
    parser.add_argument("--cpu", action="store_true", help="Force CPU")
    args = parser.parse_args()

    device = "cpu" if args.cpu else None
    searcher = SemanticSearch(
        db_path=args.db_path,
        model_name=args.model_name,
        device=device,
        preload_model=True,
    )

    stats = searcher.corpus_stats()
    print(f"Loaded {stats['num_docs']} docs | langs={stats['languages']} | dim={stats['dim']} | normalized={stats['normalized']}")

    results = searcher.search(args.query, top_k=args.top_k, languages=args.languages)
    print(f"\nTop {len(results)} results:\n")
    for i, res in enumerate(results, 1):
        print(f"{i}. [{res.language}] {res.title[:80]}")
        print(f"   Score: {res.score:.4f}")
        print(f"   Source: {res.source}")
        print(f"   URL: {res.url}")
        print()


if __name__ == "__main__":
    main()
