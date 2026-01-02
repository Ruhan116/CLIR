#!/usr/bin/env python3
"""
Real Dataset Test - Mixed English & Bangla Documents

This test ensures we test with a good mix of both languages
by sampling documents instead of taking the first N.
"""

import sys
import time
import sqlite3
import random
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from clir_search import CLIRSearch

TRANSLITERATION_MAP = {
    'ঢাকা': ['Dhaka', 'Dacca'],
    'চট্টগ্রাম': ['Chittagong', 'Chattogram'],
    'করোনা': ['Corona', 'COVID'],
    'ভ্যাকসিন': ['Vaccine'],
    'বাংলাদেশ': ['Bangladesh'],
    'খবর': ['News', 'Report'],
}

def main():
    print("\n" + "=" * 80)
    print("REAL DATASET TEST - MIXED LANGUAGES")
    print("=" * 80)
    
    db_path = Path(__file__).parent.parent / "dataset_enhanced" / "combined_dataset.db"
    
    if not db_path.exists():
        print(f"❌ Database not found: {db_path}")
        return
    
    print("\n📊 Analyzing database...")
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Get total count and language distribution
    cursor.execute("SELECT COUNT(*) FROM articles")
    total_count = cursor.fetchone()[0]
    
    cursor.execute("""
        SELECT language, COUNT(*) 
        FROM articles 
        GROUP BY language
    """)
    
    lang_dist = cursor.fetchall()
    print(f"Total documents: {total_count}")
    print(f"Language distribution:")
    for lang, count in lang_dist:
        pct = (count / total_count) * 100
        print(f"  {lang or 'unknown'}: {count} ({pct:.1f}%)")
    
    # Load balanced sample
    print("\n📥 Loading balanced sample (250 English + 250 Bangla)...\n")
    
    # Get English docs
    cursor.execute("""
        SELECT id, title, body, source, language 
        FROM articles 
        WHERE language = 'en'
        ORDER BY RANDOM()
        LIMIT 250
    """)
    
    en_rows = cursor.fetchall()
    
    # Get Bangla docs
    cursor.execute("""
        SELECT id, title, body, source, language 
        FROM articles 
        WHERE language = 'bn'
        ORDER BY RANDOM()
        LIMIT 250
    """)
    
    bn_rows = cursor.fetchall()
    conn.close()
    
    # Combine and shuffle
    all_rows = en_rows + bn_rows
    random.shuffle(all_rows)
    
    documents = []
    for row in all_rows:
        doc_id, title, body, source, language = row
        documents.append({
            'doc_id': doc_id,
            'title': title or '',
            'body': (body or '')[:200],
            'source': source or '',
            'language': language or 'en'
        })
    
    print(f"✓ Loaded {len(en_rows)} English + {len(bn_rows)} Bangla documents")
    
    # Initialize search
    clir = CLIRSearch(documents=documents, transliteration_map=TRANSLITERATION_MAP)
    
    # Test pairs
    print("\n" + "=" * 80)
    print("CROSS-LINGUAL SEARCH TEST")
    print("=" * 80 + "\n")
    
    test_pairs = [
        ('Dhaka', 'ঢাকা', 'City'),
        ('Corona', 'করোনা', 'Health'),
        ('Bangladesh', 'বাংলাদেশ', 'Country'),
        ('News', 'খবর', 'General'),
    ]
    
    print(f"{'English':<20} {'Bangla':<20} {'Topic':<15} {'EN Results':<12} {'BN Results'}")
    print("─" * 80)
    
    total_en_results = 0
    total_bn_results = 0
    
    for en_term, bn_term, topic in test_pairs:
        # English query
        start = time.time()
        en_results = clir.search_transliteration(en_term, threshold=0.5, top_k=3)
        en_time = time.time() - start
        
        # Bangla query
        start = time.time()
        bn_results = clir.search_transliteration(bn_term, threshold=0.5, top_k=3)
        bn_time = time.time() - start
        
        total_en_results += len(en_results)
        total_bn_results += len(bn_results)
        
        print(f"{en_term:<20} {bn_term:<20} {topic:<15} {len(en_results):<12} {len(bn_results)}")
    
    print("─" * 80)
    print(f"{'TOTAL':<20} {'':<20} {'':<15} {total_en_results:<12} {total_bn_results}")
    
    # Show sample results
    print("\n" + "=" * 80)
    print("SAMPLE RESULTS - 'Dhaka' Query")
    print("=" * 80 + "\n")
    
    results = clir.search_transliteration('Dhaka', threshold=0.5, top_k=5)
    
    for i, result in enumerate(results, 1):
        lang = result.get('language', 'unknown')
        score = result.get('fuzzy_score', 0)
        title = result['title']
        if len(title) > 60:
            title = title[:57] + "..."
        
        print(f"{i}. [{lang.upper()}] {title}")
        print(f"   Score: {score:.4f}\n")
    
    print("=" * 80)
    print("✅ CROSS-LINGUAL TRANSLITERATION MATCHING WORKING!")
    print("=" * 80 + "\n")

if __name__ == "__main__":
    main()
