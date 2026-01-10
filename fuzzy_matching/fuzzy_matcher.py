#!/usr/bin/env python3
"""
Fuzzy Matching Module for Cross-Lingual Information Retrieval (CLIR)

Implements:
- Edit Distance (Levenshtein Distance) for typo correction
- Jaccard Similarity for character/word overlap matching
- Transliteration-based fuzzy matching for cross-script retrieval
"""

import re
from typing import List, Dict, Set, Tuple, Optional
from collections import defaultdict
import math
import time

try:
    from Levenshtein import distance as levenshtein_distance
except ImportError:
    # Fallback to pure Python implementation
    def levenshtein_distance(s1: str, s2: str) -> int:
        """Calculate Levenshtein distance between two strings."""
        if len(s1) < len(s2):
            return levenshtein_distance(s2, s1)
        if len(s2) == 0:
            return len(s1)

        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row

        return previous_row[-1]


class FuzzyMatcher:
    """
    Core fuzzy matching class for CLIR system.
    
    Provides methods for:
    - Edit distance similarity
    - Jaccard similarity
    - Character n-gram generation
    - Token-level and document-level matching
    """

    def __init__(self, language: str = 'en'):
        """
        Initialize FuzzyMatcher.
        
        Args:
            language (str): 'en' for English, 'bn' for Bangla. Used for tokenization.
        """
        self.language = language
        self.ngram_cache = {}  # Cache for n-gram computations

    def tokenize(self, text: str) -> List[str]:
        """
        Tokenize text into words.
        
        Args:
            text (str): Text to tokenize
            
        Returns:
            list: List of tokens (lowercase)
        """
        # Remove special characters and split by whitespace
        text = text.lower()
        # Keep alphanumeric and some special chars for Bangla
        tokens = re.findall(r'\w+', text, re.UNICODE)
        return [t for t in tokens if len(t) > 0]

    def edit_distance_score(self, s1: str, s2: str) -> float:
        """
        Calculate normalized edit distance similarity score.
        
        Score = 1 - (distance / max_length)
        
        Args:
            s1 (str): First string
            s2 (str): Second string
            
        Returns:
            float: Similarity score in range [0, 1], where 1 is identical
        """
        s1 = s1.lower()
        s2 = s2.lower()

        max_len = max(len(s1), len(s2))
        if max_len == 0:
            return 1.0

        distance = levenshtein_distance(s1, s2)
        return 1.0 - (distance / max_len)

    def character_ngrams(self, text: str, n: int = 3) -> Set[str]:
        """
        Generate character n-grams from text.
        
        Args:
            text (str): Text to generate n-grams from
            n (int): Size of n-gram (default: 3)
            
        Returns:
            set: Set of character n-grams
        """
        text = text.lower().replace(' ', '')

        # Use cache to avoid recomputing
        cache_key = (text, n)
        if cache_key in self.ngram_cache:
            return self.ngram_cache[cache_key]

        ngrams = set()
        for i in range(len(text) - n + 1):
            ngrams.add(text[i:i + n])

        self.ngram_cache[cache_key] = ngrams
        return ngrams

    def word_ngrams(self, tokens: List[str], n: int = 2) -> Set[str]:
        """
        Generate word n-grams (phrases) from tokens.
        
        Args:
            tokens (list): List of tokens
            n (int): Size of n-gram (default: 2)
            
        Returns:
            set: Set of word n-grams
        """
        ngrams = set()
        for i in range(len(tokens) - n + 1):
            ngrams.add(' '.join(tokens[i:i + n]))
        return ngrams

    def jaccard_similarity(self, set1: Set[str], set2: Set[str]) -> float:
        """
        Calculate Jaccard similarity between two sets.
        
        Jaccard = |intersection| / |union|
        
        Args:
            set1 (set): First set
            set2 (set): Second set
            
        Returns:
            float: Jaccard similarity in range [0, 1]
        """
        if not set1 and not set2:
            return 1.0
        if not set1 or not set2:
            return 0.0

        intersection = len(set1 & set2)
        union = len(set1 | set2)

        if union == 0:
            return 0.0

        return intersection / union

    def search_with_edit_distance(
        self,
        query: str,
        documents: List[Dict],
        fields: List[str] = ['title', 'body'],
        threshold: float = 0.75,
        top_k: Optional[int] = None,
        include_snippet: bool = True
    ) -> List[Dict]:
        """
        Search documents using edit distance for fuzzy matching.
        
        Args:
            query (str): Search query
            documents (list): List of documents with 'title', 'body', etc.
            fields (list): Which document fields to search
            threshold (float): Minimum similarity score [0, 1]
            top_k (int): Return top-k results (None = all above threshold)
            include_snippet (bool): Include text snippet in results
            
        Returns:
            list: Ranked results with edit distance scores
            
        Example:
            >>> matcher = FuzzyMatcher()
            >>> results = matcher.search_with_edit_distance(
            ...     "Bangaldesh econmy",
            ...     documents,
            ...     threshold=0.75
            ... )
        """
        query_tokens = self.tokenize(query)
        results = []

        for doc_idx, doc in enumerate(documents):
            best_matches = []
            max_score = 0.0

            for query_token in query_tokens:
                token_scores = []

                # Search in specified fields
                for field in fields:
                    field_text = str(doc.get(field, '')).lower()
                    doc_tokens = self.tokenize(field_text)

                    # Find best match for this query token
                    best_field_score = 0.0
                    best_doc_token = None

                    for doc_token in doc_tokens:
                        score = self.edit_distance_score(query_token, doc_token)
                        if score > best_field_score:
                            best_field_score = score
                            best_doc_token = doc_token

                    if best_field_score >= threshold:
                        token_scores.append((query_token, best_doc_token, best_field_score))
                        best_matches.append((query_token, best_doc_token, best_field_score))

                max_score = max(max_score, best_field_score)

            if best_matches:
                # Average score of all matched tokens
                avg_score = sum(m[2] for m in best_matches) / len(best_matches)

                result = {
                    'doc_id': doc.get('doc_id', doc_idx),
                    'title': doc.get('title', ''),
                    'url': doc.get('url', ''),
                    'language': doc.get('language', 'unknown'),
                    'fuzzy_score': avg_score,
                    'matched_terms': best_matches,
                    'num_matches': len(best_matches)
                }

                if include_snippet:
                    body = str(doc.get('body', ''))[:200]
                    result['snippet'] = body + ('...' if len(body) == 200 else '')

                results.append(result)

        # Sort by score descending
        results.sort(key=lambda x: x['fuzzy_score'], reverse=True)

        if top_k:
            results = results[:top_k]

        return results

    def search_with_jaccard(
        self,
        query: str,
        documents: List[Dict],
        fields: List[str] = ['title', 'body'],
        level: str = 'char',
        n_gram: int = 3,
        threshold: float = 0.3,
        top_k: Optional[int] = None,
        include_snippet: bool = True
    ) -> List[Dict]:
        """
        Search documents using Jaccard similarity.
        
        Args:
            query (str): Search query
            documents (list): List of documents
            fields (list): Which document fields to search
            level (str): 'char' for character n-grams, 'word' for word-level
            n_gram (int): Size of n-gram
            threshold (float): Minimum Jaccard score [0, 1]
            top_k (int): Return top-k results
            include_snippet (bool): Include text snippet
            
        Returns:
            list: Ranked results with Jaccard scores
            
        Example:
            >>> results = matcher.search_with_jaccard(
            ...     "Dhaka weather",
            ...     documents,
            ...     level='char',
            ...     n_gram=3,
            ...     threshold=0.3
            ... )
        """
        results = []

        if level == 'char':
            query_ngrams = self.character_ngrams(query, n=n_gram)
        else:
            query_tokens = self.tokenize(query)
            query_ngrams = self.word_ngrams(query_tokens, n=n_gram)

        for doc_idx, doc in enumerate(documents):
            max_jaccard = 0.0
            common_ngrams = set()

            # Search in specified fields
            for field in fields:
                field_text = str(doc.get(field, ''))

                if level == 'char':
                    doc_ngrams = self.character_ngrams(field_text, n=n_gram)
                else:
                    doc_tokens = self.tokenize(field_text)
                    doc_ngrams = self.word_ngrams(doc_tokens, n=n_gram)

                jaccard = self.jaccard_similarity(query_ngrams, doc_ngrams)

                if jaccard > max_jaccard:
                    max_jaccard = jaccard
                    common_ngrams = query_ngrams & doc_ngrams

            if max_jaccard >= threshold:
                result = {
                    'doc_id': doc.get('doc_id', doc_idx),
                    'title': doc.get('title', ''),
                    'url': doc.get('url', ''),
                    'language': doc.get('language', 'unknown'),
                    'jaccard_score': max_jaccard,
                    'common_ngrams': sorted(list(common_ngrams))[:10],  # Top 10
                    'num_common': len(common_ngrams)
                }

                if include_snippet:
                    body = str(doc.get('body', ''))[:200]
                    result['snippet'] = body + ('...' if len(body) == 200 else '')

                results.append(result)

        # Sort by score descending
        results.sort(key=lambda x: x['jaccard_score'], reverse=True)

        if top_k:
            results = results[:top_k]

        return results

    def search_with_transliteration(
        self,
        query: str,
        documents: List[Dict],
        transliteration_map: Dict[str, List[str]],
        fields: List[str] = ['title', 'body'],
        threshold: float = 0.75,
        top_k: Optional[int] = None
    ) -> List[Dict]:
        """
        Search using transliteration-aware fuzzy matching.
        
        Expands query with transliteration variants and searches.
        
        Args:
            query (str): Search query
            documents (list): Document list
            transliteration_map (dict): Mapping of terms to transliterations
                Example: {'ঢাকা': ['Dhaka', 'Dacca'], ...}
            fields (list): Document fields to search
            threshold (float): Similarity threshold
            top_k (int): Return top-k results
            
        Returns:
            list: Ranked results combining original and transliterated matches
        """
        query_tokens = self.tokenize(query)
        expanded_queries = [set(query_tokens)]  # Start with original

        # Generate transliteration variants
        for token in query_tokens:
            if token in transliteration_map:
                variants = transliteration_map[token]
                expanded_queries.append(set([token] + variants))
            else:
                # Also check if this token is a transliteration variant
                for original, variants in transliteration_map.items():
                    if token in variants:
                        expanded_queries.append(set([original] + variants))
                        break

        results_by_doc = defaultdict(lambda: {'scores': [], 'doc': None})

        # Search with each query variant
        for query_variant in expanded_queries:
            variant_query = ' '.join(query_variant)
            variant_results = self.search_with_edit_distance(
                variant_query,
                documents,
                fields=fields,
                threshold=threshold,
                include_snippet=False
            )

            for result in variant_results:
                doc_id = result['doc_id']
                results_by_doc[doc_id]['scores'].append(result['fuzzy_score'])
                results_by_doc[doc_id]['doc'] = result

        # Combine scores
        final_results = []
        for doc_id, data in results_by_doc.items():
            avg_score = sum(data['scores']) / len(data['scores'])
            result = data['doc'].copy()
            result['fuzzy_score'] = avg_score
            result['variant_matches'] = len(data['scores'])
            final_results.append(result)

        final_results.sort(key=lambda x: x['fuzzy_score'], reverse=True)

        if top_k:
            final_results = final_results[:top_k]

        return final_results

    def batch_compute_ngrams(
        self,
        documents: List[Dict],
        fields: List[str] = ['title', 'body'],
        level: str = 'char',
        n_gram: int = 3
    ) -> Dict[int, Set[str]]:
        """
        Pre-compute n-grams for all documents (for performance).
        
        Args:
            documents (list): Document list
            fields (list): Document fields to process
            level (str): 'char' or 'word'
            n_gram (int): N-gram size
            
        Returns:
            dict: Mapping of doc_id to n-gram sets
        """
        doc_ngrams = {}

        for doc_idx, doc in enumerate(documents):
            doc_id = doc.get('doc_id', doc_idx)
            ngrams = set()

            for field in fields:
                field_text = str(doc.get(field, ''))

                if level == 'char':
                    ngrams.update(self.character_ngrams(field_text, n=n_gram))
                else:
                    tokens = self.tokenize(field_text)
                    ngrams.update(self.word_ngrams(tokens, n=n_gram))

            doc_ngrams[doc_id] = ngrams

        return doc_ngrams

    def clear_cache(self):
        """Clear n-gram cache to free memory."""
        self.ngram_cache.clear()
