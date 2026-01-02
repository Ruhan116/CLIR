# Quick Start Guide - Real Dataset Testing

## The Tests You Just Ran

You successfully tested the transliteration matching system with your **real database** containing 5,000 documents (2,500 English + 2,500 Bangla).

---

## Test Files Available

### 1. **test_mixed_languages.py** ⭐ RECOMMENDED
```bash
python test_mixed_languages.py
```
**What it does:**
- Loads 250 English + 250 Bangla documents
- Tests 4 cross-lingual pairs (Dhaka/ঢাকা, Corona/করোনা, etc.)
- Shows results with language tags
- Runs in ~30 seconds

**Best for:** Quick verification that transliteration works

---

### 2. **test_real_dataset_optimized.py**
```bash
python test_real_dataset_optimized.py
```
Then select:
- **A** → Fast test (500 documents, 2-5 seconds)
- **B** → Performance analysis (scalability testing)
- **C** → Cross-lingual demo (detailed results)
- **D** → All tests

**Best for:** Understanding performance characteristics

---

### 3. **test_with_real_dataset.py**
```bash
python test_with_real_dataset.py
```

**What it does:**
- Tests all 5,000 documents
- 8 different queries (Bangla + English)
- Comprehensive transliteration map (66 terms)
- Full results with document titles

**Best for:** Complete validation (takes ~6 minutes)

---

## What the Tests Show

| Test | Documents | Time | Purpose |
|------|-----------|------|---------|
| Mixed Languages | 500 | 30s | Quick verification |
| Optimized (Option A) | 500 | 2-5s | Very fast demo |
| Optimized (Option B) | 100-2000 | 1m | Performance scaling |
| Full Dataset | 5000 | 6m | Comprehensive test |

---

## Key Results from Your Tests ✅

### Cross-Lingual Matching Works!
```
Query          Language    Found Documents    Example
────────────────────────────────────────────────────
Dhaka          English     3 results         ✓
ঢাকা            Bangla      3 results         ✓
Corona         English     3 results         ✓
করোনা          Bangla      3 results         ✓
Bangladesh     English     3 results         ✓
বাংলাদেশ       Bangla      3 results         ✓
```

### Performance is Excellent!
```
Documents    Search Time    Speed
100          33ms          3 docs/ms
500          159ms         3 docs/ms
1000         313ms         3 docs/ms
2000         640ms         3 docs/ms
```

---

## Using in Your Code

```python
from clir_search import CLIRSearch
import sqlite3

# Load your documents
conn = sqlite3.connect('../dataset_enhanced/combined_dataset.db')
cursor = conn.cursor()
cursor.execute("""
    SELECT id, title, body, source, language 
    FROM articles 
    LIMIT 5000
""")

documents = []
for row in cursor.fetchall():
    documents.append({
        'doc_id': row[0],
        'title': row[1],
        'body': row[2],
        'source': row[3],
        'language': row[4]
    })
conn.close()

# Initialize CLIR system
clir = CLIRSearch(
    documents=documents,
    transliteration_map=YOUR_TRANSLITERATION_MAP
)

# Search with transliteration
results = clir.search_transliteration(
    query='Dhaka',           # Can be English or Bangla
    threshold=0.65,          # Adjust for relevance
    top_k=5                  # Number of results
)

# Display results
for doc in results:
    print(f"{doc['title']}")
    print(f"  Language: {doc['language']}")
    print(f"  Score: {doc['fuzzy_score']:.4f}")
```

---

## Customizing the Transliteration Map

Add your own terms:
```python
TRANSLITERATION_MAP = {
    'ঢাকা': ['Dhaka', 'Dacca'],
    'আপনার_নতুন_শব্দ': ['Your', 'New', 'Variants'],
}
```

Test with:
```bash
python test_mixed_languages.py
```

---

## Performance Tips

### For Faster Searches (Optional)
Install the optional C library:
```bash
pip install python-Levenshtein
```
This gives **10-100x speedup** on Edit Distance calculations!

### For Large Datasets
- Use lower threshold (0.5-0.65) for broader matches
- Limit top_k to 5-10 for faster results
- Pre-process long document bodies

### Database Optimization
Add index on frequently searched language:
```python
cursor.execute("CREATE INDEX idx_language ON articles(language)")
```

---

## Troubleshooting

### "No results found"
- Lower the threshold: `threshold=0.5`
- Check transliteration map has the term
- Verify database has documents in that language

### "Very slow searches"
- Reduce number of documents: `LIMIT 500` instead of 5000
- Use python-Levenshtein: `pip install python-Levenshtein`
- Profile the code: Use `test_real_dataset_optimized.py` Option B

### "Database not found"
- Verify path: `../dataset_enhanced/combined_dataset.db`
- Adjust path based on where your script is located

---

## Success Checklist

After running the tests, verify:
- ✅ No errors during execution
- ✅ Results found for cross-lingual queries
- ✅ Search times < 1 second per query
- ✅ Both English and Bangla documents in results

All tests passing? **You're ready for production!** 🚀

---

## Next: Integrate with Your CLIR Pipeline

Now that you've validated transliteration matching works:

1. **Add to main search flow**
   ```python
   # In your main CLIR application
   results = clir.hybrid_search(user_query)
   ```

2. **Customize weights**
   ```python
   results = clir.hybrid_search(
       query,
       weights={'bm25': 0.5, 'edit_distance': 0.25, 'jaccard': 0.25}
   )
   ```

3. **Monitor performance**
   - Run performance tests weekly
   - Adjust thresholds based on user feedback
   - Expand transliteration map with new terms

---

**Questions?** Check the documentation files:
- [README.md](README.md) - Complete API reference
- [REAL_DATASET_TEST_RESULTS.md](REAL_DATASET_TEST_RESULTS.md) - Detailed results
- [usage_examples.py](usage_examples.py) - 10 practical examples
