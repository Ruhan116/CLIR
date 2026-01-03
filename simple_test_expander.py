#!/usr/bin/env python3
"""Simple test for query expander without encoding wrappers."""

from query_expander import QueryExpander, expand_query, get_synonyms, get_root_words

def test_basic():
    """Test basic functionality."""
    print("Testing Query Expander...")
    
    expander = QueryExpander()
    
    # Test 1: Basic expansion
    print("\n1. Basic expansion:")
    result = expander.expand("vaccine test")
    print(f"   Original: {result['original']}")
    print(f"   Terms: {result['terms']}")
    print(f"   Expanded: {result['expanded_terms'][:5]}...")  # Show first 5
    assert result['original'] == "vaccine test"
    assert len(result['terms']) == 2
    assert len(result['expanded_terms']) > 0
    print("   ✓ Passed")
    
    # Test 2: Synonyms
    print("\n2. Synonym expansion:")
    syns = expander.get_synonyms("vaccine")
    print(f"   Synonyms for 'vaccine': {syns}")
    assert isinstance(syns, list)
    print("   ✓ Passed")
    
    # Test 3: Stemming
    print("\n3. Stemming:")
    stem = expander.get_stem("running")
    print(f"   Stem of 'running': {stem}")
    assert len(stem) <= len("running")
    print("   ✓ Passed")
    
    # Test 4: Lemmatization
    print("\n4. Lemmatization:")
    lemma = expander.get_lemma("running")
    print(f"   Lemma of 'running': {lemma}")
    assert isinstance(lemma, str)
    print("   ✓ Passed")
    
    # Test 5: Query string format
    print("\n5. Expanded query string:")
    expanded = expander.expand_to_query("news vaccine")
    print(f"   Original: news vaccine")
    print(f"   Expanded: {expanded[:100]}...")  # Show first 100 chars
    assert "news" in expanded.lower() or "new" in expanded.lower()
    assert "vaccine" in expanded.lower() or "vaccin" in expanded.lower()
    print("   ✓ Passed")
    
    # Test 6: Convenience functions
    print("\n6. Convenience functions:")
    terms = expand_query("test")
    print(f"   expand_query('test'): {terms}")
    assert isinstance(terms, list)
    print("   ✓ Passed")
    
    syns = get_synonyms("good")
    print(f"   get_synonyms('good'): {syns}")
    assert isinstance(syns, list)
    print("   ✓ Passed")
    
    roots = get_root_words("running")
    print(f"   get_root_words('running'): {roots}")
    assert isinstance(roots, dict)
    print("   ✓ Passed")
    
    print("\n" + "="*60)
    print("All tests passed! ✓")
    print("="*60)

if __name__ == "__main__":
    test_basic()
