#!/usr/bin/env python3
"""Complete CLIR pipeline demo without encoding wrappers."""

def demo():
    from query_normalizer import QueryNormalizer
    from language_detector import LanguageDetector
    from query_translator import QueryTranslator
    from query_expander import QueryExpander
    
    print("="*60)
    print("Complete CLIR Pipeline - Phase 2 Integration")
    print("="*60)
    
    # Initialize components
    normalizer = QueryNormalizer()
    detector = LanguageDetector()
    translator = QueryTranslator()
    expander = QueryExpander()
    
    # Test English query
    query = "  CORONAVIRUS Vaccine NEWS  "
    print(f"\n1. English Query: '{query}'")
    print("-"*60)
    
    # Step 1: Normalize
    normalized = normalizer.normalize(query)
    print(f"Normalized: '{normalized}'")
    
    # Step 2: Detect
    lang = detector.detect(normalized)
    print(f"Language: {lang}")
    
    # Step 3: Expand
    if lang == 'en':
        expansion = expander.expand(normalized)
        print(f"Original terms: {expansion['terms']}")
        print(f"Expanded terms: {expansion['expanded_terms'][:5]}...")
        expanded_query = expander.expand_to_query(normalized)
        print(f"Query string: {expanded_query[:70]}...")
    
    # Step 4: Translate for cross-lingual search
    if lang == 'en':
        translated = translator.english_to_bangla(normalized)
        print(f"Translation (en->bn): {translated}")
    
    # Test Bangla query
    print(f"\n2. Bangla Query Test")
    print("-"*60)
    bn_query = "করোনা ভ্যাকসিন"
    print(f"Query: '{bn_query}'")
    
    normalized_bn = normalizer.normalize(bn_query)
    lang_bn = detector.detect(normalized_bn)
    print(f"Language: {lang_bn}")
    
    if lang_bn == 'bn':
        translated_en = translator.bangla_to_english(normalized_bn)
        print(f"Translation (bn->en): {translated_en}")
    
    print("\n" + "="*60)
    print("All Phase 2 components working! ✓")
    print("="*60)

if __name__ == "__main__":
    demo()
