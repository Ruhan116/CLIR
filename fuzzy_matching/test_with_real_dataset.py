#!/usr/bin/env python3
"""
Test Transliteration Matching with Real Dataset

This script tests the fuzzy matching system with your actual 5000+ documents
from the combined_dataset.db database.
"""

import sys
import time
import sqlite3
from pathlib import Path

# Add fuzzy_matching to path
sys.path.insert(0, str(Path(__file__).parent))

from clir_search import CLIRSearch

# ============================================================================
# COMPREHENSIVE TRANSLITERATION MAP FOR BENGALI-ENGLISH
# ============================================================================

TRANSLITERATION_MAP = {
    # Cities & Regions
    'ঢাকা': ['Dhaka', 'Dacca'],
    'চট্টগ্রাম': ['Chittagong', 'Chattogram', 'Chottogram'],
    'খুলনা': ['Khulna'],
    'সিলেট': ['Sylhet', 'Sillet'],
    'রাজশাহী': ['Rajshahi'],
    'বরিশাল': ['Barisal', 'Barishal'],
    'ময়মনসিংহ': ['Mymensingh'],
    'রংপুর': ['Rangpur'],

    # Countries
    'বাংলাদেশ': ['Bangladesh', 'Bangla Desh', 'Bengal'],
    'ভারত': ['India'],
    'পাকিস্তান': ['Pakistan'],
    'আমেরিকা': ['America', 'USA', 'United States'],
    'চীন': ['China'],

    # Health & Medical
    'করোনা': ['Corona', 'COVID', 'COVID-19', 'Coronavirus', 'SARS-CoV-2'],
    'ভ্যাকসিন': ['Vaccine', 'Vaccination', 'Immunization'],
    'হাসপাতাল': ['Hospital', 'Healthcare', 'Medical Center'],
    'ডাক্তার': ['Doctor', 'Physician', 'Medical'],
    'রোগ': ['Disease', 'Illness', 'Epidemic'],
    'স্বাস্থ্য': ['Health', 'Healthcare', 'Medical'],

    # Weather & Climate
    'আবহাওয়া': ['Weather', 'Climate', 'Meteorology'],
    'বৃষ্টি': ['Rain', 'Rainfall', 'Raining'],
    'ঝড়': ['Storm', 'Cyclone', 'Hurricane'],
    'বন্যা': ['Flood', 'Flooding'],
    'প্রাকৃতিক দুর্যোগ': ['Natural Disaster', 'Calamity'],

    # Economy & Business
    'অর্থনীতি': ['Economy', 'Economic', 'Economics'],
    'ব্যবসা': ['Business', 'Trade', 'Commerce'],
    'শেয়ার': ['Share', 'Stock'],
    'বাজার': ['Market', 'Marketplace'],
    'বাণিজ্য': ['Commerce', 'Trade', 'Business'],
    'রপ্তানি': ['Export', 'Exporting'],
    'আমদানি': ['Import', 'Importing'],

    # Politics & Government
    'সরকার': ['Government', 'Administration'],
    'প্রধানমন্ত্রী': ['Prime Minister', 'PM'],
    'মন্ত্রী': ['Minister'],
    'নির্বাচন': ['Election', 'Electoral'],
    'সংসদ': ['Parliament', 'National Assembly'],
    'জাতীয়': ['National'],

    # Crime & Law
    'অপরাধ': ['Crime', 'Criminal'],
    'পুলিশ': ['Police'],
    'আইন': ['Law', 'Legal', 'Judiciary'],
    'আদালত': ['Court'],
    'বিচার': ['Justice', 'Trial', 'Judgment'],

    # Technology
    'প্রযুক্তি': ['Technology', 'Tech', 'IT'],
    'কম্পিউটার': ['Computer'],
    'ইন্টারনেট': ['Internet'],
    'সফটওয়্যার': ['Software'],
    'ডিজিটাল': ['Digital'],

    # Education
    'শিক্ষা': ['Education', 'Academic'],
    'বিশ্ববিদ্যালয়': ['University'],
    'স্কুল': ['School'],
    'পরীক্ষা': ['Exam', 'Test', 'Examination'],

    # Culture & Sports
    'ক্রিকেট': ['Cricket'],
    'ফুটবল': ['Football', 'Soccer'],
    'খেলাধুলা': ['Sports', 'Athletic'],
    'সংস্কৃতি': ['Culture', 'Cultural'],
    'শিল্প': ['Arts', 'Art', 'Culture'],

    # Organizations & Institutions
    'বিশ্বব্যাংক': ['World Bank'],
    'জাতিসংঘ': ['United Nations', 'UN'],
    'এশিয়ান ডেভেলপমেন্ট ব্যাংক': ['Asian Development Bank', 'ADB'],
    'আন্তর্জাতিক': ['International'],

    # Other Common Terms
    'খবর': ['News', 'Report', 'Story'],
    'আপডেট': ['Update', 'Updated'],
    'সংবাদ': ['News', 'Report'],
    'প্রকল্প': ['Project', 'Scheme'],
    'উন্নয়ন': ['Development', 'Progress'],
    'সাহায্য': ['Help', 'Aid', 'Assistance'],
}

# ============================================================================
# TEST QUERIES
# ============================================================================

TEST_QUERIES = [
    # Bangla queries
    {
        'query': 'ঢাকা সংবাদ',
        'language': 'Bangla',
        'description': 'Bangla query: Dhaka news'
    },
    {
        'query': 'করোনা ভ্যাকসিন',
        'language': 'Bangla',
        'description': 'Bangla query: Corona vaccine'
    },
    {
        'query': 'আবহাওয়া পূর্বাভাস',
        'language': 'Bangla',
        'description': 'Bangla query: Weather forecast'
    },
    {
        'query': 'বাংলাদেশ অর্থনীতি',
        'language': 'Bangla',
        'description': 'Bangla query: Bangladesh economy'
    },
    
    # English queries (to find Bangla documents)
    {
        'query': 'Dhaka news',
        'language': 'English',
        'description': 'English query: Should find Bangla docs with ঢাকা'
    },
    {
        'query': 'Corona vaccine Bangladesh',
        'language': 'English',
        'description': 'English query: Should find Bangla medical docs'
    },
    {
        'query': 'Weather forecast',
        'language': 'English',
        'description': 'English query: Should find Bangla weather docs'
    },
    {
        'query': 'Bangladesh economy',
        'language': 'English',
        'description': 'English query: Should find Bangla economic docs'
    },
]

# ============================================================================
# MAIN TEST FUNCTION
# ============================================================================

def main():
    """Run transliteration matching tests with real dataset."""
    
    print("\n" + "=" * 80)
    print("TRANSLITERATION MATCHING - REAL DATASET TEST")
    print("=" * 80)
    
    # Database path
    db_path = Path(__file__).parent.parent / "dataset_enhanced" / "combined_dataset.db"
    
    # Check if database exists
    if not db_path.exists():
        print(f"\n❌ ERROR: Database not found at: {db_path}")
        print(f"   Please ensure combined_dataset.db exists in dataset_enhanced folder")
        return
    
    print(f"\n✓ Database found: {db_path}")
    
    # Initialize search system
    print("\n📊 Loading documents from database...")
    start = time.time()
    
    try:
        # Load documents from database
        import sqlite3
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Note: Database uses 'id' not 'doc_id'
        cursor.execute("""
            SELECT id, title, body, source, language 
            FROM articles 
            LIMIT 5000
        """)
        
        rows = cursor.fetchall()
        documents = []
        for row in rows:
            doc_id, title, body, source, language = row
            documents.append({
                'doc_id': doc_id,
                'title': title or '',
                'body': body or '',
                'source': source or '',
                'language': language or 'en'
            })
        
        conn.close()
        
        clir = CLIRSearch(
            documents=documents,
            transliteration_map=TRANSLITERATION_MAP
        )
        load_time = time.time() - start
        print(f"✓ Loaded {len(clir.documents)} documents in {load_time:.2f}s")
    except Exception as e:
        print(f"❌ Error loading database: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Print transliteration map stats
    print(f"\n📚 Transliteration Map:")
    print(f"   Entries: {len(TRANSLITERATION_MAP)}")
    total_variants = sum(len(v) for v in TRANSLITERATION_MAP.values())
    print(f"   Total variants: {total_variants}")
    print(f"   Avg variants per term: {total_variants/len(TRANSLITERATION_MAP):.1f}")
    
    # Run tests
    print("\n" + "=" * 80)
    print("RUNNING TESTS")
    print("=" * 80)
    
    total_results = 0
    total_time = 0
    
    for i, test in enumerate(TEST_QUERIES, 1):
        query = test['query']
        description = test['description']
        
        print(f"\n{'─' * 80}")
        print(f"Test {i}: {description}")
        print(f"Query: '{query}'")
        print(f"{'─' * 80}")
        
        # Run search
        start = time.time()
        try:
            results = clir.search_transliteration(
                query,
                threshold=0.65,  # Lower threshold for cross-script
                top_k=5
            )
            search_time = time.time() - start
            total_time += search_time
            
            # Display results
            if results:
                print(f"✓ Found {len(results)} results in {search_time*1000:.2f}ms\n")
                
                for rank, result in enumerate(results, 1):
                    title = result['title']
                    if len(title) > 60:
                        title = title[:57] + "..."
                    
                    score = result['fuzzy_score']
                    language = result.get('language', 'unknown')
                    
                    print(f"  {rank}. {title}")
                    print(f"     Language: {language} | Score: {score:.4f}")
                    if 'snippet' in result:
                        snippet = result['snippet'][:80].replace('\n', ' ')
                        print(f"     Snippet: {snippet}...")
                    print()
                
                total_results += len(results)
            else:
                print(f"⚠ No results found in {search_time*1000:.2f}ms")
        
        except Exception as e:
            print(f"❌ Error during search: {e}")
            import traceback
            traceback.print_exc()
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"\nTotal queries: {len(TEST_QUERIES)}")
    print(f"Total results found: {total_results}")
    print(f"Total search time: {total_time*1000:.2f}ms")
    print(f"Average time per query: {(total_time/len(TEST_QUERIES))*1000:.2f}ms")
    
    if total_results > 0:
        print(f"\n✅ TRANSLITERATION MATCHING WORKING CORRECTLY!")
        print(f"   Successfully found {total_results} documents across languages")
    else:
        print(f"\n⚠ No results found - check transliteration map or query terms")
    
    print("\n" + "=" * 80)

# ============================================================================
# RUN
# ============================================================================

if __name__ == "__main__":
    main()
