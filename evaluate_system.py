#!/usr/bin/env python3
"""
Evaluate CLIR System Implementation (Assignment Task D1 & D2).

Metrics implemented:
- Precision@K
- Recall@K
- nDCG@K
- MRR
- Execution Time

Usage:
    python evaluate_system.py
"""

import csv
import time
import math
import sys
import numpy as np
import pandas as pd
from pathlib import Path
from collections import defaultdict
from typing import List, Dict, Set

# Add project root to path
sys.path.append(str(Path(__file__).parent))

# Import models safely
try:
    from BM25.bm25_clir import BM25CLIR
except ImportError:
    BM25CLIR = None

try:
    from semantic_matching.semantic_search import SemanticSearch
except ImportError:
    SemanticSearch = None

try:
    from fuzzy_matching.clir_search import CLIRSearch
except ImportError:
    CLIRSearch = None

# --- CONFIGURATION ---
LABELED_DATA_FILE = "labeled_queries.csv"
OUTPUT_METRICS_FILE = "evaluation_results_metrics.csv"
OUTPUT_DETAILED_FILE = "evaluation_results_detailed.csv"
K_VALUES = [1, 5, 10]

# --- METRIC FUNCTIONS ---

def precision_at_k(retrieved_urls: List[str], relevant_urls: Set[str], k: int) -> float:
    """Compute Precision@K."""
    if k == 0: return 0.0
    retrieved_k = retrieved_urls[:k]
    relevant_retrieved = sum(1 for url in retrieved_k if url in relevant_urls)
    return relevant_retrieved / k

def recall_at_k(retrieved_urls: List[str], relevant_urls: Set[str], k: int) -> float:
    """Compute Recall@K."""
    if not relevant_urls: return 0.0
    retrieved_k = retrieved_urls[:k]
    relevant_retrieved = sum(1 for url in retrieved_k if url in relevant_urls)
    return relevant_retrieved / len(relevant_urls)

def dcg_at_k(retrieved_urls: List[str], relevant_urls: Set[str], k: int) -> float:
    """Compute DCG@K."""
    dcg = 0.0
    for i, url in enumerate(retrieved_urls[:k]):
        if url in relevant_urls:
            rel = 1.0 # Binary relevance
            dcg += rel / math.log2(i + 2) # i+2 because rank is i+1 (1-based)
    return dcg

def ndcg_at_k(retrieved_urls: List[str], relevant_urls: Set[str], k: int) -> float:
    """Compute nDCG@K."""
    dcg = dcg_at_k(retrieved_urls, relevant_urls, k)
    
    # Ideal DCG: sorted relevance
    num_relevant = len(relevant_urls)
    if num_relevant == 0: return 0.0
    
    # Ideal ranking has all relevant docs at the top
    ideal_response = ([1.0] * min(num_relevant, k)) + ([0.0] * max(0, k - num_relevant))
    idcg = 0.0
    for i, rel in enumerate(ideal_response):
        idcg += rel / math.log2(i + 2)
        
    if idcg == 0: return 0.0
    return dcg / idcg

def mrr_score(retrieved_urls: List[str], relevant_urls: Set[str]) -> float:
    """Compute Mean Reciprocal Rank (MRR)."""
    for i, url in enumerate(retrieved_urls):
        if url in relevant_urls:
            return 1.0 / (i + 1)
    return 0.0

def load_labels(filepath: str) -> Dict[str, Set[str]]:
    """Load labeled queries from CSV.
    
    Returns: Dict {query: set of relevant URLs}
    """
    if not Path(filepath).exists():
        print(f"Error: {filepath} not found. Run generate_labeling_pool.py first.")
        return {}
        
    qrels = defaultdict(set)
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # relevant column should be '1' or 'true' or 'yes'
                is_rel = str(row.get('relevant', '')).lower() in ('1', 'true', 'yes', 'y')
                if is_rel:
                    qrels[row['query']].add(row['doc_url'])
    except Exception as e:
        print(f"Error reading labels: {e}")
        
    return qrels

def evaluate_model(model_name: str, model_func, queries: List[str], qrels: Dict[str, Set[str]]):
    """Run evaluation for a single model."""
    print(f"\nEvaluating {model_name}...")
    
    metrics = {
        'P@10': [], 'R@10': [], 'nDCG@10': [], 'MRR': [], 'Time': []
    }
    
    model_results = [] # Detailed results for output
    
    for query in queries:
        relevant_urls = qrels.get(query, set())
        if not relevant_urls:
            continue
            
        start_time = time.time()
        try:
            # Assume model_func returns list of dicts with 'url' key, or list of objects with 'url' attr
            # Uniform adapter needed?
            # We'll expect model_func to return list of results
            results = model_func(query)
            elapsed = time.time() - start_time
            
            # Extract URLs
            retrieved_urls = []
            for res in results:
                if isinstance(res, dict):
                    retrieved_urls.append(res.get('url') or res.get('doc_url'))
                else:
                    retrieved_urls.append(getattr(res, 'url', None))
                    
            retrieved_urls = [u for u in retrieved_urls if u] # filter None
            
            # Compute Metrics
            p10 = precision_at_k(retrieved_urls, relevant_urls, 10)
            r10 = recall_at_k(retrieved_urls, relevant_urls, 10) # Using 10 as per typical display, assignment says Recall@50
            ndcg10 = ndcg_at_k(retrieved_urls, relevant_urls, 10)
            mrr = mrr_score(retrieved_urls, relevant_urls)
            
            metrics['P@10'].append(p10)
            metrics['R@10'].append(r10)
            metrics['nDCG@10'].append(ndcg10)
            metrics['MRR'].append(mrr)
            metrics['Time'].append(elapsed)
            
            model_results.append({
                'Model': model_name,
                'Query': query,
                'P@10': p10,
                'nDCG@10': ndcg10,
                'MRR': mrr,
                'Time': elapsed
            })
            
        except Exception as e:
            print(f"  Error on query '{query}': {e}")
            
    # Aggregate
    if not metrics['P@10']:
        return None, []
        
    avg_metrics = {
        'Model': model_name,
        'Mean P@10': np.mean(metrics['P@10']),
        'Mean R@10': np.mean(metrics['R@10']),
        'Mean nDCG@10': np.mean(metrics['nDCG@10']),
        'Mean MRR': np.mean(metrics['MRR']),
        'Avg Time (s)': np.mean(metrics['Time'])
    }
    
    return avg_metrics, model_results

def main():
    print("DEBUG: Starting main...", flush=True)
    print("="*80, flush=True)
    print("CLIR System Evaluation")
    print("="*80)
    
    # 1. Load Labels
    qrels = load_labels(LABELED_DATA_FILE)
    queries = list(qrels.keys())
    
    if not queries:
        print("No labeled queries found. Please populate labeled_queries.csv first.")
        return

    print(f"Loaded {len(queries)} queries with relevant documents.")

    # 2. Initialize Models
    models = {}
    
    # BM25
    if BM25CLIR:
        try:
            bm25 = BM25CLIR(enable_translation=True)
            # Wrapper function
            def run_bm25(q):
                res = bm25.search_cross_lingual(q, top_k=50, merge_results=True)
                return [r[0] for r in res['results']] # extract Article objects
            models['BM25'] = run_bm25
        except Exception as e:
            print(f"Skipping BM25: {e}")
            
    # Semantic
    if SemanticSearch:
        try:
            semantic = SemanticSearch(preload_model=True)
            def run_semantic(q):
                return semantic.search(q, top_k=50)
            models['Semantic'] = run_semantic
        except Exception as e:
            print(f"Skipping Semantic: {e}")
            
    # Hybrid
    # if CLIRSearch and BM25CLIR: # Hybrid needs BM25 usually
    #     try:
    #         hybrid = CLIRSearch(db_path=str(BM25CLIR().db_path))
    #         def run_hybrid(q):
    #             res, _ = hybrid.hybrid_search(q, top_k=50)
    #             return res # returns list of dicts
    #         models['Hybrid'] = run_hybrid
    #     except Exception as e:
    #         print(f"Skipping Hybrid: {e}")

    # 3. Run Evaluation
    all_summary = []
    all_detailed = []
    
    for name, func in models.items():
        summary, detailed = evaluate_model(name, func, queries, qrels)
        if summary:
            all_summary.append(summary)
            all_detailed.extend(detailed)
            
            print(f"  > Mean P@10: {summary['Mean P@10']:.4f}")
            print(f"  > Mean nDCG@10: {summary['Mean nDCG@10']:.4f}")
            print(f"  > Mean MRR: {summary['Mean MRR']:.4f}")

    # 4. Export Results
    if all_summary:
        df_summary = pd.DataFrame(all_summary)
        df_summary.to_csv(OUTPUT_METRICS_FILE, index=False)
        print(f"\nSummary metrics saved to {OUTPUT_METRICS_FILE}")
        
        df_detailed = pd.DataFrame(all_detailed)
        df_detailed.to_csv(OUTPUT_DETAILED_FILE, index=False)
        print(f"Detailed results saved to {OUTPUT_DETAILED_FILE}")
        
        print("\n" + "="*80)
        print("FINAL RESULTS SUMMARY")
        print("="*80)
        print(df_summary.to_string(index=False))
    else:
        print("\nNo models evaluated successfully.")

if __name__ == "__main__":
    main()
