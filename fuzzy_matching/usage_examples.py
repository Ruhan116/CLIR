"""
Practical Usage Examples - Fuzzy Matching CLIR System

This file contains practical examples for different use cases.
"""

# ============================================================================
# EXAMPLE 1: Basic Typo Correction
# ============================================================================

def example_typo_correction():
    """Handle queries with typos."""
    from fuzzy_matcher import FuzzyMatcher
    
    documents = [
        {
            'doc_id': 1,
            'title': 'Bangladesh Economy Report',
            'body': 'Economic growth in Bangladesh...',
            'language': 'English'
        },
        # Add more documents
    ]
    
    matcher = FuzzyMatcher()
    
    # Query with typo: "Bangaldesh" instead of "Bangladesh"
    results = matcher.search_with_edit_distance(
        query='Bangaldesh econmy',
        documents=documents,
        threshold=0.75,
        top_k=10
    )
    
    print("Results for typo query 'Bangaldesh econmy':")
    for result in results:
        print(f"  {result['title']} ({result['fuzzy_score']:.3f})")


# ============================================================================
# EXAMPLE 2: Cross-Script Matching with Transliteration
# ============================================================================

def example_cross_script_matching():
    """Match English queries to Bangla documents."""
    from fuzzy_matching import CLIRSearch
    
    documents = [
        {
            'doc_id': 1,
            'title': 'ঢাকায় আবহাওয়া পূর্বাভাস',
            'body': 'এই সপ্তাহে ঢাকায় বৃষ্টি হবে...',
            'language': 'Bangla'
        },
        {
            'doc_id': 2,
            'title': 'Dhaka Weather Forecast',
            'body': 'Rain expected in Dhaka...',
            'language': 'English'
        }
    ]
    
    # Set up transliteration map
    transliteration_map = {
        'ঢাকা': ['Dhaka', 'Dacca'],
        'আবহাওয়া': ['Weather', 'Climate']
    }
    
    # Create search system
    clir = CLIRSearch(
        documents=documents,
        transliteration_map=transliteration_map
    )
    
    # English query for Bangla content
    results = clir.search_transliteration(
        query='Dhaka weather',
        top_k=10
    )
    
    print("Cross-script results for 'Dhaka weather':")
    for result in results:
        print(f"  {result['title']} ({result['language']})")


# ============================================================================
# EXAMPLE 3: Hybrid Search with Weighted Scoring
# ============================================================================

def example_hybrid_search():
    """Combine multiple search methods."""
    from fuzzy_matching import CLIRSearch
    
    documents = [
        {
            'doc_id': 1,
            'title': 'Bangladesh Technology Growth',
            'body': 'The tech sector in BD is booming...',
            'language': 'English'
        },
        {
            'doc_id': 2,
            'title': 'প্রযুক্তি খাতে বাংলাদেশের অগ্রগতি',
            'body': 'প্রযুক্তি শিল্প দ্রুত বৃদ্ধি পাচ্ছে...',
            'language': 'Bangla'
        }
    ]
    
    clir = CLIRSearch(documents=documents)
    
    # Hybrid search with custom weights
    results, timing = clir.hybrid_search(
        query='Bangladesh technology sector',
        weights={
            'bm25': 0.5,      # 50% exact matching
            'edit': 0.25,     # 25% typo tolerance
            'jaccard': 0.25   # 25% character overlap
        },
        top_k=5,
        verbose=True
    )
    
    print(f"\nHybrid search results (took {timing['total']*1000:.1f}ms):")
    for result in results:
        print(f"  {result['title']} ({result['hybrid_score']:.3f})")


# ============================================================================
# EXAMPLE 4: Performance Comparison
# ============================================================================

def example_performance_comparison():
    """Compare different search methods."""
    from fuzzy_matching import CLIRSearch
    import time
    
    documents = [
        {
            'doc_id': i,
            'title': f'Document {i}',
            'body': f'Content for document {i}...',
            'language': 'English'
        }
        for i in range(1000)  # 1000 documents
    ]
    
    clir = CLIRSearch(documents=documents)
    
    query = "Bangladesh"
    
    # Time edit distance search
    start = time.time()
    edit_results = clir.search_edit_distance(query)
    edit_time = time.time() - start
    
    # Time Jaccard search
    start = time.time()
    jaccard_results = clir.search_jaccard(query)
    jaccard_time = time.time() - start
    
    # Time hybrid search
    start = time.time()
    hybrid_results, timing = clir.hybrid_search(query)
    hybrid_time = time.time() - start
    
    print("Performance Comparison:")
    print(f"  Edit Distance:  {len(edit_results)} results in {edit_time*1000:.2f}ms")
    print(f"  Jaccard:        {len(jaccard_results)} results in {jaccard_time*1000:.2f}ms")
    print(f"  Hybrid:         {len(hybrid_results)} results in {hybrid_time*1000:.2f}ms")


# ============================================================================
# EXAMPLE 5: Using Different Jaccard Parameters
# ============================================================================

def example_jaccard_parameters():
    """Explore Jaccard similarity with different parameters."""
    from fuzzy_matching import CLIRSearch
    
    documents = [
        {
            'doc_id': 1,
            'title': 'Corona Virus News',
            'body': 'Latest updates on coronavirus...',
            'language': 'English'
        },
        {
            'doc_id': 2,
            'title': 'করোনা ভাইরাস সংবাদ',
            'body': 'করোনা ভাইরাসের সর্বশেষ খবর...',
            'language': 'Bangla'
        }
    ]
    
    clir = CLIRSearch(documents=documents)
    
    query = "Corona"
    
    # Character-level n-grams (good for cross-script)
    char_results = clir.search_jaccard(
        query,
        level='char',
        n_gram=3,
        threshold=0.2,
        top_k=10
    )
    
    # Word-level n-grams (good for phrases)
    word_results = clir.search_jaccard(
        query,
        level='word',
        n_gram=2,
        threshold=0.3,
        top_k=10
    )
    
    print("Character-level Jaccard:")
    for r in char_results:
        print(f"  {r['title']} ({r['jaccard_score']:.3f})")
    
    print("\nWord-level Jaccard:")
    for r in word_results:
        print(f"  {r['title']} ({r['jaccard_score']:.3f})")


# ============================================================================
# EXAMPLE 6: Custom Threshold Tuning
# ============================================================================

def example_threshold_tuning():
    """Find optimal thresholds for your data."""
    from fuzzy_matching import CLIRSearch
    
    documents = [
        {
            'doc_id': 1,
            'title': 'Bangladesh News',
            'body': '...',
            'language': 'English'
        },
        # More documents
    ]
    
    clir = CLIRSearch(documents=documents)
    
    # Test different thresholds
    thresholds = [0.5, 0.6, 0.7, 0.75, 0.8, 0.85, 0.9]
    query = "Bangaldesh"
    
    print(f"Testing query: '{query}'")
    print("Threshold | Results | Avg Score")
    print("-" * 40)
    
    for threshold in thresholds:
        results = clir.search_edit_distance(
            query,
            threshold=threshold,
            top_k=100
        )
        avg_score = sum(r['fuzzy_score'] for r in results) / len(results) if results else 0
        print(f"{threshold:9.2f} | {len(results):7} | {avg_score:9.3f}")


# ============================================================================
# EXAMPLE 7: Real-time Index Updates
# ============================================================================

def example_dynamic_updates():
    """Add new documents to search index dynamically."""
    from fuzzy_matching import CLIRSearch
    
    # Start with initial documents
    documents = [
        {
            'doc_id': 1,
            'title': 'Initial Document',
            'body': '...',
            'language': 'English'
        }
    ]
    
    clir = CLIRSearch(documents=documents)
    
    # Add new documents
    new_documents = [
        {
            'doc_id': 2,
            'title': 'Bangladesh Updates',
            'body': '...',
            'language': 'English'
        },
        {
            'doc_id': 3,
            'title': 'বাংলাদেশ সংবাদ',
            'body': '...',
            'language': 'Bangla'
        }
    ]
    
    # Reinitialize with updated documents
    clir.documents.extend(new_documents)
    
    # Search will now include new documents
    results = clir.search_edit_distance("Bangladesh")
    print(f"Found {len(results)} results after adding new documents")


# ============================================================================
# EXAMPLE 8: Error Handling and Edge Cases
# ============================================================================

def example_error_handling():
    """Handle edge cases gracefully."""
    from fuzzy_matching import CLIRSearch
    
    documents = [
        {
            'doc_id': 1,
            'title': 'Bangladesh',
            'body': 'Content...',
            'language': 'English'
        }
    ]
    
    clir = CLIRSearch(documents=documents)
    
    # Empty query
    try:
        results = clir.search_edit_distance('')
        print(f"Empty query: {len(results)} results")
    except Exception as e:
        print(f"Empty query error: {e}")
    
    # Very short query
    results = clir.search_edit_distance('a')
    print(f"Single char query: {len(results)} results")
    
    # Special characters
    results = clir.search_edit_distance('!@#$%')
    print(f"Special chars: {len(results)} results")
    
    # Very high threshold
    results = clir.search_edit_distance('Bangladesh', threshold=0.99)
    print(f"High threshold: {len(results)} results")
    
    # Very low threshold
    results = clir.search_edit_distance('xyz', threshold=0.01)
    print(f"Low threshold: {len(results)} results")


# ============================================================================
# EXAMPLE 9: Building Comprehensive Transliteration Map
# ============================================================================

def example_comprehensive_transliteration_map():
    """Create and use a comprehensive transliteration mapping."""
    from fuzzy_matching import CLIRSearch
    
    # Extensive transliteration map for Bengali-English
    transliteration_map = {
        # Cities
        'ঢাকা': ['Dhaka', 'Dacca'],
        'চট্টগ্রাম': ['Chittagong', 'Chattogram'],
        'খুলনা': ['Khulna'],
        'সিলেট': ['Sylhet', 'Sillet'],
        
        # Countries
        'বাংলাদেশ': ['Bangladesh', 'Bangla Desh', 'Bengal'],
        'ভারত': ['India'],
        'পাকিস্তান': ['Pakistan'],
        
        # Topics
        'করোনা': ['Corona', 'COVID', 'COVID-19', 'Coronavirus'],
        'ভ্যাকসিন': ['Vaccine', 'Vaccination', 'Immunization'],
        'আবহাওয়া': ['Weather', 'Climate'],
        'প্রযুক্তি': ['Technology', 'Tech'],
        'অর্থনীতি': ['Economy', 'Economic'],
        
        # Named entities
        'বিশ্বব্যাংক': ['World Bank'],
        'জাতিসংঘ': ['United Nations', 'UN'],
    }
    
    documents = [
        {
            'doc_id': 1,
            'title': 'ঢাকায় করোনা ভ্যাকসিন প্রচারণা',
            'body': '...',
            'language': 'Bangla'
        },
        {
            'doc_id': 2,
            'title': 'Dhaka COVID-19 Vaccination Drive',
            'body': '...',
            'language': 'English'
        }
    ]
    
    clir = CLIRSearch(
        documents=documents,
        transliteration_map=transliteration_map
    )
    
    # Query in English for Bangla documents
    results = clir.search_transliteration("Dhaka Corona vaccine")
    print(f"Found {len(results)} results with transliteration mapping")


# ============================================================================
# EXAMPLE 10: Full Integration with Production Setup
# ============================================================================

def example_production_setup():
    """Complete production-ready setup."""
    from fuzzy_matching import CLIRSearch
    import json
    
    # Load documents from database or file
    with open('documents.json', 'r') as f:
        documents = json.load(f)
    
    # Load transliteration map
    with open('transliteration_map.json', 'r') as f:
        trans_map = json.load(f)
    
    # Initialize with production parameters
    clir = CLIRSearch(
        documents=documents,
        transliteration_map=trans_map
    )
    
    # Define search parameters for production
    search_params = {
        'weights': {'bm25': 0.5, 'edit': 0.25, 'jaccard': 0.25},
        'thresholds': {'edit': 0.75, 'jaccard': 0.3},
        'top_k': 10
    }
    
    # Example production query
    query = "Bangladesh technology news"
    
    # Run search with error handling
    try:
        results, timing = clir.hybrid_search(
            query,
            **search_params,
            verbose=False
        )
        
        # Format results for API response
        response = {
            'status': 'success',
            'query': query,
            'results': results,
            'timing_ms': timing['total'] * 1000,
            'result_count': len(results)
        }
        
        # Return or save response
        print(json.dumps(response, indent=2, ensure_ascii=False))
        
    except Exception as e:
        response = {
            'status': 'error',
            'query': query,
            'error': str(e)
        }
        print(json.dumps(response, indent=2))


# ============================================================================
# Run Examples
# ============================================================================

if __name__ == "__main__":
    print("Example 1: Typo Correction")
    print("-" * 50)
    # example_typo_correction()
    
    print("\nExample 2: Cross-Script Matching")
    print("-" * 50)
    # example_cross_script_matching()
    
    print("\nExample 3: Hybrid Search")
    print("-" * 50)
    # example_hybrid_search()
    
    print("\nExample 4: Performance Comparison")
    print("-" * 50)
    # example_performance_comparison()
    
    print("\nExample 5: Jaccard Parameters")
    print("-" * 50)
    # example_jaccard_parameters()
    
    print("\nExample 6: Threshold Tuning")
    print("-" * 50)
    # example_threshold_tuning()
    
    print("\nExample 8: Error Handling")
    print("-" * 50)
    # example_error_handling()
    
    print("\nExample 9: Comprehensive Transliteration")
    print("-" * 50)
    # example_comprehensive_transliteration_map()
    
    print("\nAll examples are ready to use!")
