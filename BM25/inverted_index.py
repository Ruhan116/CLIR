#!/usr/bin/env python3
"""Inverted Index Implementation for BM25 CLIR System.

This module provides a persistent SQLite-based inverted index for efficient
BM25 retrieval. It stores term frequencies, document frequencies, and document
lengths to enable fast scoring without rebuilding the index on each startup.

Schema:
    - terms: vocabulary with document frequency per language
    - postings: term -> document mappings with term frequency
    - doc_lengths: document lengths for BM25 normalization
    - metadata: BM25 parameters and statistics (avgdl, total_docs, etc.)
"""

import sqlite3
import math
import re
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from collections import defaultdict
from dataclasses import dataclass


@dataclass
class IndexStats:
    """Statistics about the inverted index."""
    total_docs_en: int
    total_docs_bn: int
    avgdl_en: float
    avgdl_bn: float
    unique_terms_en: int
    unique_terms_bn: int
    total_postings: int


class InvertedIndex:
    """SQLite-based inverted index for BM25 retrieval.

    This class provides:
    - Index building from a source database
    - BM25 scoring and retrieval
    - Persistent storage (no rebuild needed on restart)

    BM25 Parameters:
        k1 = 1.5 (term frequency saturation)
        b = 0.75 (length normalization)
    """

    # BM25 parameters
    K1 = 1.5
    B = 0.75

    def __init__(self, index_path: str = None, source_db_path: str = None):
        """Initialize the inverted index.

        Args:
            index_path: Path to the index SQLite file. Defaults to BM25/bm25_index.sqlite
            source_db_path: Path to the source database. Defaults to BM25/combined_dataset.db
        """
        script_dir = Path(__file__).parent

        if index_path is None:
            index_path = script_dir / "bm25_index.sqlite"
        if source_db_path is None:
            source_db_path = script_dir / "combined_dataset.db"

        self.index_path = Path(index_path)
        self.source_db_path = Path(source_db_path)

        # Cached metadata for fast scoring
        self._metadata_cache: Dict[str, any] = {}
        self._doc_lengths_cache: Dict[int, int] = {}

    def exists(self) -> bool:
        """Check if the index file exists and is valid."""
        if not self.index_path.exists():
            return False

        # Check if tables exist
        try:
            conn = sqlite3.connect(self.index_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = {row[0] for row in cursor.fetchall()}
            conn.close()
            return {'terms', 'postings', 'doc_lengths', 'metadata'}.issubset(tables)
        except:
            return False

    def _create_schema(self, conn: sqlite3.Connection):
        """Create the index schema."""
        cursor = conn.cursor()

        # Terms table: vocabulary with document frequency
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS terms (
                term TEXT NOT NULL,
                df INTEGER NOT NULL,
                language TEXT NOT NULL,
                PRIMARY KEY (term, language)
            )
        """)

        # Postings table: term -> document mappings
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS postings (
                term TEXT NOT NULL,
                article_id INTEGER NOT NULL,
                tf INTEGER NOT NULL,
                language TEXT NOT NULL,
                PRIMARY KEY (term, article_id)
            )
        """)

        # Document lengths for BM25 normalization
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS doc_lengths (
                article_id INTEGER PRIMARY KEY,
                length INTEGER NOT NULL,
                language TEXT NOT NULL
            )
        """)

        # Metadata table for BM25 parameters and statistics
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)

        conn.commit()

    def _create_indexes(self, conn: sqlite3.Connection):
        """Create database indexes for fast lookups."""
        cursor = conn.cursor()

        # Index on postings.term for fast term lookups
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_postings_term ON postings(term)")

        # Index on postings.language for language-specific queries
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_postings_lang ON postings(language)")

        # Index on doc_lengths.language
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_doc_lengths_lang ON doc_lengths(language)")

        # Index on terms.language
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_terms_lang ON terms(language)")

        conn.commit()

    def _tokenize_english(self, text: str) -> List[str]:
        """Tokenize English text (same as bm25_clir.py)."""
        tokens = re.findall(r'\b[a-z0-9]+\b', text.lower())
        return [t for t in tokens if len(t) > 1]

    def _tokenize_bangla(self, text: str) -> List[str]:
        """Tokenize Bangla text (same as bm25_clir.py)."""
        punctuation = r'[।॥,.;:!?\'\"()\[\]{}<>@#$%^&*+=|\\\/\-_—–''""…\n\r\t]'
        text = re.sub(punctuation, ' ', text)
        tokens = text.strip().split()
        return [t.strip() for t in tokens if len(t) > 1 and not t.isdigit()]

    def _tokenize(self, text: str, language: str) -> List[str]:
        """Tokenize text based on language."""
        if language == "en":
            return self._tokenize_english(text)
        else:
            return self._tokenize_bangla(text)

    def build(self, language: str = "both", show_progress: bool = True):
        """Build the inverted index from the source database.

        Args:
            language: "en", "bn", or "both" (default)
            show_progress: Print progress messages
        """
        if not self.source_db_path.exists():
            raise FileNotFoundError(f"Source database not found: {self.source_db_path}")

        languages = ["en", "bn"] if language == "both" else [language]

        # Connect to source database
        source_conn = sqlite3.connect(self.source_db_path)
        source_cursor = source_conn.cursor()

        # Create/connect to index database
        # Remove existing index if rebuilding
        if self.index_path.exists():
            self.index_path.unlink()

        index_conn = sqlite3.connect(self.index_path)
        self._create_schema(index_conn)
        index_cursor = index_conn.cursor()

        for lang in languages:
            if show_progress:
                print(f"\nBuilding index for {lang.upper()}...")

            # Fetch articles
            source_cursor.execute("""
                SELECT id, title, body
                FROM articles
                WHERE language = ? AND body IS NOT NULL AND body != ''
            """, (lang,))

            articles = source_cursor.fetchall()

            if show_progress:
                print(f"  Processing {len(articles)} articles...")

            # Data structures for batch insert
            term_df: Dict[str, int] = defaultdict(int)  # term -> document frequency
            postings_data: List[Tuple[str, int, int, str]] = []  # (term, article_id, tf, lang)
            doc_lengths_data: List[Tuple[int, int, str]] = []  # (article_id, length, lang)

            total_length = 0

            for i, (article_id, title, body) in enumerate(articles):
                # Combine title and body
                full_text = f"{title} {body}"
                tokens = self._tokenize(full_text, lang)

                # Calculate term frequencies for this document
                tf_map: Dict[str, int] = defaultdict(int)
                for token in tokens:
                    tf_map[token] += 1

                # Track document frequency (each term counted once per doc)
                for term in tf_map:
                    term_df[term] += 1

                # Store postings
                for term, tf in tf_map.items():
                    postings_data.append((term, article_id, tf, lang))

                # Store document length
                doc_length = len(tokens)
                doc_lengths_data.append((article_id, doc_length, lang))
                total_length += doc_length

                if show_progress and (i + 1) % 500 == 0:
                    print(f"    Processed {i + 1}/{len(articles)} articles...")

            # Calculate average document length
            avgdl = total_length / len(articles) if articles else 0

            if show_progress:
                print(f"  Inserting {len(term_df)} terms...")

            # Batch insert terms
            terms_data = [(term, df, lang) for term, df in term_df.items()]
            index_cursor.executemany(
                "INSERT OR REPLACE INTO terms (term, df, language) VALUES (?, ?, ?)",
                terms_data
            )

            if show_progress:
                print(f"  Inserting {len(postings_data)} postings...")

            # Batch insert postings
            index_cursor.executemany(
                "INSERT OR REPLACE INTO postings (term, article_id, tf, language) VALUES (?, ?, ?, ?)",
                postings_data
            )

            # Batch insert document lengths
            index_cursor.executemany(
                "INSERT OR REPLACE INTO doc_lengths (article_id, length, language) VALUES (?, ?, ?)",
                doc_lengths_data
            )

            # Store metadata
            index_cursor.execute(
                "INSERT OR REPLACE INTO metadata (key, value) VALUES (?, ?)",
                (f"avgdl_{lang}", str(avgdl))
            )
            index_cursor.execute(
                "INSERT OR REPLACE INTO metadata (key, value) VALUES (?, ?)",
                (f"total_docs_{lang}", str(len(articles)))
            )

            if show_progress:
                print(f"  {lang.upper()} index built: {len(articles)} docs, {len(term_df)} terms, avgdl={avgdl:.2f}")

        # Store BM25 parameters
        index_cursor.execute(
            "INSERT OR REPLACE INTO metadata (key, value) VALUES (?, ?)",
            ("k1", str(self.K1))
        )
        index_cursor.execute(
            "INSERT OR REPLACE INTO metadata (key, value) VALUES (?, ?)",
            ("b", str(self.B))
        )

        # Create indexes for fast lookups
        if show_progress:
            print("\nCreating database indexes...")
        self._create_indexes(index_conn)

        index_conn.commit()
        index_conn.close()
        source_conn.close()

        # Clear caches
        self._metadata_cache.clear()
        self._doc_lengths_cache.clear()

        if show_progress:
            print("Index build complete!")

    def _load_metadata(self):
        """Load metadata into cache."""
        if self._metadata_cache:
            return

        conn = sqlite3.connect(self.index_path)
        cursor = conn.cursor()
        cursor.execute("SELECT key, value FROM metadata")

        for key, value in cursor.fetchall():
            if key.startswith("avgdl_") or key in ("k1", "b"):
                self._metadata_cache[key] = float(value)
            elif key.startswith("total_docs_"):
                self._metadata_cache[key] = int(value)
            else:
                self._metadata_cache[key] = value

        conn.close()

    def _load_doc_lengths(self, language: str):
        """Load document lengths for a language into cache."""
        cache_key = f"_loaded_{language}"
        if self._metadata_cache.get(cache_key):
            return

        conn = sqlite3.connect(self.index_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT article_id, length FROM doc_lengths WHERE language = ?",
            (language,)
        )

        for article_id, length in cursor.fetchall():
            self._doc_lengths_cache[article_id] = length

        conn.close()
        self._metadata_cache[cache_key] = True

    def _compute_idf(self, df: int, N: int) -> float:
        """Compute IDF score using BM25 formula."""
        return math.log((N - df + 0.5) / (df + 0.5) + 1)

    def search(self, query: str, language: str, top_k: int = 10) -> List[Tuple[int, float]]:
        """Search the index and return ranked results.

        Args:
            query: Search query
            language: Language to search in ("en" or "bn")
            top_k: Number of top results to return

        Returns:
            List of (article_id, score) tuples, sorted by score descending
        """
        if not self.exists():
            raise RuntimeError("Index not found. Call build() first.")

        # Load metadata and doc lengths
        self._load_metadata()
        self._load_doc_lengths(language)

        # Tokenize query
        query_tokens = self._tokenize(query, language)

        if not query_tokens:
            return []

        # Get BM25 parameters
        k1 = self._metadata_cache.get("k1", self.K1)
        b = self._metadata_cache.get("b", self.B)
        avgdl = self._metadata_cache.get(f"avgdl_{language}", 1.0)
        N = self._metadata_cache.get(f"total_docs_{language}", 1)

        conn = sqlite3.connect(self.index_path)
        cursor = conn.cursor()

        # Get term statistics and postings for query terms
        doc_scores: Dict[int, float] = defaultdict(float)

        for term in query_tokens:
            # Get document frequency
            cursor.execute(
                "SELECT df FROM terms WHERE term = ? AND language = ?",
                (term, language)
            )
            result = cursor.fetchone()

            if result is None:
                continue

            df = result[0]
            idf = self._compute_idf(df, N)

            # Get postings for this term
            cursor.execute(
                "SELECT article_id, tf FROM postings WHERE term = ? AND language = ?",
                (term, language)
            )

            for article_id, tf in cursor.fetchall():
                # Get document length
                doc_length = self._doc_lengths_cache.get(article_id, avgdl)

                # BM25 score contribution for this term
                numerator = tf * (k1 + 1)
                denominator = tf + k1 * (1 - b + b * (doc_length / avgdl))
                score = idf * (numerator / denominator)

                doc_scores[article_id] += score

        conn.close()

        # Sort by score and return top-k
        sorted_results = sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_results[:top_k]

    def get_stats(self) -> Optional[IndexStats]:
        """Get statistics about the index."""
        if not self.exists():
            return None

        conn = sqlite3.connect(self.index_path)
        cursor = conn.cursor()

        # Load metadata
        self._load_metadata()

        # Count unique terms per language
        cursor.execute("SELECT COUNT(*) FROM terms WHERE language = 'en'")
        unique_terms_en = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM terms WHERE language = 'bn'")
        unique_terms_bn = cursor.fetchone()[0]

        # Count total postings
        cursor.execute("SELECT COUNT(*) FROM postings")
        total_postings = cursor.fetchone()[0]

        conn.close()

        return IndexStats(
            total_docs_en=self._metadata_cache.get("total_docs_en", 0),
            total_docs_bn=self._metadata_cache.get("total_docs_bn", 0),
            avgdl_en=self._metadata_cache.get("avgdl_en", 0.0),
            avgdl_bn=self._metadata_cache.get("avgdl_bn", 0.0),
            unique_terms_en=unique_terms_en,
            unique_terms_bn=unique_terms_bn,
            total_postings=total_postings
        )

    def drop(self):
        """Delete the index file."""
        if self.index_path.exists():
            self.index_path.unlink()
            self._metadata_cache.clear()
            self._doc_lengths_cache.clear()
            print(f"Index deleted: {self.index_path}")


def main():
    """Build and test the inverted index."""
    import sys
    import io

    # Handle Unicode output on Windows
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

    print("=" * 60)
    print("Inverted Index Builder")
    print("=" * 60)

    # Create index
    index = InvertedIndex()

    # Build index
    print("\nBuilding index...")
    index.build(language="both", show_progress=True)

    # Show stats
    stats = index.get_stats()
    if stats:
        print("\n" + "=" * 60)
        print("Index Statistics")
        print("=" * 60)
        print(f"English documents: {stats.total_docs_en}")
        print(f"Bangla documents: {stats.total_docs_bn}")
        print(f"English avg doc length: {stats.avgdl_en:.2f}")
        print(f"Bangla avg doc length: {stats.avgdl_bn:.2f}")
        print(f"English unique terms: {stats.unique_terms_en}")
        print(f"Bangla unique terms: {stats.unique_terms_bn}")
        print(f"Total postings: {stats.total_postings}")

    # Test search
    print("\n" + "=" * 60)
    print("Test Searches")
    print("=" * 60)

    # English search
    print("\nEnglish query: 'election results'")
    results = index.search("election results", "en", top_k=5)
    print(f"Found {len(results)} results:")
    for article_id, score in results:
        print(f"  Article {article_id}: score={score:.4f}")

    # Bangla search
    bangla_query = "করোনা ভ্যাকসিন"
    print(f"\nBangla query: '{bangla_query}'")
    results = index.search(bangla_query, "bn", top_k=5)
    print(f"Found {len(results)} results:")
    for article_id, score in results:
        print(f"  Article {article_id}: score={score:.4f}")

    print("\n" + "=" * 60)
    print("Index build and test complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
