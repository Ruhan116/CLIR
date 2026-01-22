#!/usr/bin/env python3
"""
CLIR Search Integration Module

Combines BM25 lexical matching with fuzzy matching techniques
(edit distance, Jaccard similarity, transliteration) for robust
cross-lingual information retrieval.
"""

import json
import sqlite3
import sys
import time
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from collections import defaultdict

from fuzzy_matcher import FuzzyMatcher

# Try to import BM25 from existing module
try:
    from BM25.bm25_clir import BM25Retriever
    BM25_AVAILABLE = True
except ImportError:
    BM25_AVAILABLE = False
    print("Warning: BM25 module not found. Hybrid search will work with fuzzy matching only.")


class CLIRSearch:
    """
    Unified CLIR search system combining multiple retrieval methods.
    
    Methods:
    - BM25: Lexical matching (if available)
    - Edit Distance: Fuzzy matching for typo correction
    - Jaccard: Character/word overlap matching
    - Transliteration: Cross-script matching
    - Hybrid: Combines all methods with weighted scoring
    """

    def __init__(
        self,
        db_path: Optional[str] = None,
        documents: Optional[List[Dict]] = None,
        transliteration_map: Optional[Dict] = None
    ):
        """
        Initialize CLIR Search system.
        
        Args:
            db_path (str): Path to SQLite database with documents
            documents (list): In-memory document list
            transliteration_map (dict): Mapping of terms to transliterations
        """
        self.documents = []
        self.fuzzy_matcher = FuzzyMatcher()
        self.bm25_retriever = None
        self.transliteration_map = transliteration_map or {}

        # Load documents from database or memory
        if db_path:
            self.load_from_database(db_path)
        elif documents:
            self.documents = documents
        else:
            raise ValueError("Provide either db_path or documents list")

        # Initialize BM25 if available
        if BM25_AVAILABLE:
            try:
                self.bm25_retriever = BM25Retriever(
                    documents=self.documents,
                    language='en'
                )
            except Exception as e:
                print(f"Warning: Could not initialize BM25 retriever: {e}")

    def load_from_database(self, db_path: str) -> None:
        """
        Load documents from SQLite database.

        Args:
            db_path (str): Path to database file
        """
        if not Path(db_path).exists():
            raise FileNotFoundError(f"Database not found: {db_path}")

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Get all documents (using actual column names from combined_dataset.db)
        cursor.execute("""
            SELECT id, title, body, url, date, language, tokens
            FROM articles
            ORDER BY id
        """)

        for row in cursor.fetchall():
            doc_id, title, body, url, date, language, token_count = row
            self.documents.append({
                'doc_id': doc_id,
                'title': title,
                'body': body,
                'url': url,
                'date': date,
                'language': language,
                'token_count': token_count
            })

        conn.close()
        print(f"[OK] Loaded {len(self.documents)} documents from database")

    def search_bm25(
        self,
        query: str,
        top_k: int = 10,
        language: str = 'en'
    ) -> List[Dict]:
        """
        Search using BM25 lexical matching.
        
        Args:
            query (str): Search query
            top_k (int): Number of results
            language (str): 'en' or 'bn'
            
        Returns:
            list: Top-k results with BM25 scores
        """
        if not self.bm25_retriever:
            return []

        try:
            results = self.bm25_retriever.search(
                query=query,
                top_k=top_k,
                language=language
            )
            return results
        except Exception as e:
            print(f"Error in BM25 search: {e}")
            return []

    def search_edit_distance(
        self,
        query: str,
        threshold: float = 0.75,
        top_k: int = 10,
        fields: List[str] = ['title', 'body']
    ) -> List[Dict]:
        """
        Search using edit distance fuzzy matching.
        
        Args:
            query (str): Search query
            threshold (float): Minimum similarity [0, 1]
            top_k (int): Number of results
            fields (list): Document fields to search
            
        Returns:
            list: Top-k results with edit distance scores
        """
        return self.fuzzy_matcher.search_with_edit_distance(
            query=query,
            documents=self.documents,
            fields=fields,
            threshold=threshold,
            top_k=top_k,
            include_snippet=True
        )

    def search_jaccard(
        self,
        query: str,
        level: str = 'char',
        n_gram: int = 3,
        threshold: float = 0.3,
        top_k: int = 10,
        fields: List[str] = ['title', 'body']
    ) -> List[Dict]:
        """
        Search using Jaccard similarity.
        
        Args:
            query (str): Search query
            level (str): 'char' or 'word' level n-grams
            n_gram (int): Size of n-gram
            threshold (float): Minimum Jaccard score [0, 1]
            top_k (int): Number of results
            fields (list): Document fields to search
            
        Returns:
            list: Top-k results with Jaccard scores
        """
        return self.fuzzy_matcher.search_with_jaccard(
            query=query,
            documents=self.documents,
            fields=fields,
            level=level,
            n_gram=n_gram,
            threshold=threshold,
            top_k=top_k,
            include_snippet=True
        )

    def search_transliteration(
        self,
        query: str,
        threshold: float = 0.75,
        top_k: int = 10,
        fields: List[str] = ['title', 'body']
    ) -> List[Dict]:
        """
        Search using transliteration-aware fuzzy matching.
        
        Args:
            query (str): Search query
            threshold (float): Minimum similarity [0, 1]
            top_k (int): Number of results
            fields (list): Document fields to search
            
        Returns:
            list: Top-k results with transliteration-aware scores
        """
        if not self.transliteration_map:
            # Fall back to edit distance if no transliteration map
            return self.search_edit_distance(query, threshold, top_k, fields)

        return self.fuzzy_matcher.search_with_transliteration(
            query=query,
            documents=self.documents,
            transliteration_map=self.transliteration_map,
            fields=fields,
            threshold=threshold,
            top_k=top_k
        )

    def _normalize_scores(self, results: List[Dict], score_field: str) -> List[Dict]:
        """
        Normalize scores to [0, 1] range.
        
        Args:
            results (list): Results with scores
            score_field (str): Name of score field
            
        Returns:
            list: Results with normalized scores
        """
        if not results:
            return results

        scores = [r.get(score_field, 0) for r in results]
        min_score = min(scores) if scores else 0
        max_score = max(scores) if scores else 1

        if max_score == min_score:
            normalized_results = results
            for r in normalized_results:
                r[f'{score_field}_normalized'] = 1.0
        else:
            normalized_results = []
            for r in results:
                r_copy = r.copy()
                score = r.get(score_field, 0)
                normalized = (score - min_score) / (max_score - min_score)
                r_copy[f'{score_field}_normalized'] = normalized
                normalized_results.append(r_copy)

        return normalized_results

    def hybrid_search(
        self,
        query: str,
        weights: Optional[Dict[str, float]] = None,
        top_k: int = 10,
        thresholds: Optional[Dict[str, float]] = None,
        verbose: bool = False
    ) -> Tuple[List[Dict], Dict]:
        """
        Hybrid search combining BM25 + Edit Distance + Jaccard.
        
        Args:
            query (str): Search query
            weights (dict): Scoring weights
                Default: {'bm25': 0.5, 'edit': 0.25, 'jaccard': 0.25}
            top_k (int): Number of results to return
            thresholds (dict): Minimum thresholds for each method
                Default: {'edit': 0.75, 'jaccard': 0.3}
            verbose (bool): Print detailed timing info
            
        Returns:
            tuple: (ranked_results, timing_info)
            
        Example:
            >>> clir = CLIRSearch(documents=docs)
            >>> results, timing = clir.hybrid_search(
            ...     "Bangaldesh economy",
            ...     top_k=10,
            ...     verbose=True
            ... )
        """
        if weights is None:
            weights = {'bm25': 0.5, 'edit': 0.25, 'jaccard': 0.25}

        if thresholds is None:
            thresholds = {'edit': 0.75, 'jaccard': 0.3}

        timing = {}
        results_by_method = {}

        # Normalize weights
        total_weight = sum(weights.values())
        weights = {k: v / total_weight for k, v in weights.items()}

        # BM25 search
        if weights.get('bm25', 0) > 0 and self.bm25_retriever:
            start = time.time()
            bm25_results = self.search_bm25(query, top_k=top_k * 2)
            timing['bm25'] = time.time() - start
            bm25_results = self._normalize_scores(bm25_results, 'bm25_score')
            results_by_method['bm25'] = {r['doc_id']: r for r in bm25_results}
            if verbose:
                print(f"BM25: {len(bm25_results)} results in {timing['bm25']:.3f}s")
        else:
            results_by_method['bm25'] = {}

        # Edit distance search
        if weights.get('edit', 0) > 0:
            start = time.time()
            edit_results = self.search_edit_distance(
                query,
                threshold=thresholds.get('edit', 0.75),
                top_k=top_k * 2
            )
            timing['edit'] = time.time() - start
            edit_results = self._normalize_scores(edit_results, 'fuzzy_score')
            results_by_method['edit'] = {r['doc_id']: r for r in edit_results}
            if verbose:
                print(f"Edit Distance: {len(edit_results)} results in {timing['edit']:.3f}s")
        else:
            results_by_method['edit'] = {}

        # Jaccard similarity search
        if weights.get('jaccard', 0) > 0:
            start = time.time()
            jaccard_results = self.search_jaccard(
                query,
                threshold=thresholds.get('jaccard', 0.3),
                top_k=top_k * 2
            )
            timing['jaccard'] = time.time() - start
            jaccard_results = self._normalize_scores(jaccard_results, 'jaccard_score')
            results_by_method['jaccard'] = {r['doc_id']: r for r in jaccard_results}
            if verbose:
                print(f"Jaccard: {len(jaccard_results)} results in {timing['jaccard']:.3f}s")
        else:
            results_by_method['jaccard'] = {}

        # Combine results
        combined_scores = defaultdict(float)
        doc_details = {}

        for method, method_weight in weights.items():
            if method not in results_by_method:
                continue

            for doc_id, result in results_by_method[method].items():
                score_field = {
                    'bm25': 'bm25_score_normalized',
                    'edit': 'fuzzy_score_normalized',
                    'jaccard': 'jaccard_score_normalized'
                }.get(method)

                normalized_score = result.get(score_field, 0)
                combined_scores[doc_id] += method_weight * normalized_score

                if doc_id not in doc_details:
                    # Get document details from any result
                    doc_details[doc_id] = {
                        'doc_id': result['doc_id'],
                        'title': result['title'],
                        'url': result['url'],
                        'language': result['language'],
                        'snippet': result.get('snippet', '')
                    }

                # Store individual scores
                if 'scores_breakdown' not in doc_details[doc_id]:
                    doc_details[doc_id]['scores_breakdown'] = {}

                doc_details[doc_id]['scores_breakdown'][method] = normalized_score

        # Sort by combined score
        final_results = []
        for doc_id, combined_score in sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]:
            result = doc_details[doc_id].copy()
            result['hybrid_score'] = combined_score
            final_results.append(result)

        timing['total'] = sum(timing.values())

        if verbose:
            print(f"\nTotal time: {timing['total']:.3f}s")
            print(f"Weights: {weights}")

        return final_results, timing

    def compare_methods(
        self,
        query: str,
        top_k: int = 5,
        verbose: bool = True
    ) -> Dict:
        """
        Compare results from all search methods.
        
        Args:
            query (str): Search query
            top_k (int): Number of results per method
            verbose (bool): Print detailed comparison
            
        Returns:
            dict: Comparison results from all methods
        """
        results = {
            'query': query,
            'methods': {}
        }

        # BM25
        if self.bm25_retriever:
            start = time.time()
            bm25_results = self.search_bm25(query, top_k=top_k)
            results['methods']['bm25'] = {
                'results': bm25_results,
                'time': time.time() - start,
                'count': len(bm25_results)
            }
        else:
            results['methods']['bm25'] = {
                'results': [],
                'time': 0,
                'count': 0,
                'note': 'BM25 not available'
            }

        # Edit Distance
        start = time.time()
        edit_results = self.search_edit_distance(query, top_k=top_k)
        results['methods']['edit_distance'] = {
            'results': edit_results,
            'time': time.time() - start,
            'count': len(edit_results)
        }

        # Jaccard
        start = time.time()
        jaccard_results = self.search_jaccard(query, top_k=top_k)
        results['methods']['jaccard'] = {
            'results': jaccard_results,
            'time': time.time() - start,
            'count': len(jaccard_results)
        }

        # Hybrid
        start = time.time()
        hybrid_results, hybrid_timing = self.hybrid_search(query, top_k=top_k)
        results['methods']['hybrid'] = {
            'results': hybrid_results,
            'time': time.time() - start,
            'count': len(hybrid_results)
        }

        if verbose:
            self._print_comparison(results, top_k)

        return results

    def _print_comparison(self, results: Dict, top_k: int = 5) -> None:
        """Pretty print comparison results."""
        print(f"\n{'='*80}")
        print(f"Query: {results['query']}")
        print(f"{'='*80}")

        for method, data in results['methods'].items():
            print(f"\n{method.upper()} ({data['count']} results, {data['time']:.3f}s)")
            print(f"{'-'*80}")

            for i, result in enumerate(data['results'][:top_k], 1):
                print(f"{i}. {result['title']}")
                score_key = list(k for k in result.keys() if 'score' in k)[0]
                print(f"   Score: {result[score_key]:.4f}")
                print(f"   URL: {result['url'][:60]}...")
                print()

    def set_transliteration_map(self, transliteration_map: Dict) -> None:
        """
        Set or update the transliteration map.
        
        Args:
            transliteration_map (dict): Mapping of terms to variants
        """
        self.transliteration_map = transliteration_map
