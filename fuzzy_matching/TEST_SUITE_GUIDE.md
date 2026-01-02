# Fuzzy Matching Test Suite - Complete Guide

## Available Tests

You now have **4 different test files** for validating the transliteration matching system:

---

## 1️⃣ Original Unit & Integration Tests

### File: `test_fuzzy.py`
**Status**: ✅ All 13+ test cases passing (Exit Code: 0)

**What it tests**:
- Edit distance score calculation
- N-gram generation and caching
- Jaccard similarity computation
- Tokenization functions
- Fuzzy search with edit distance
- Fuzzy search with Jaccard similarity
- Fuzzy search with transliteration
- Hybrid search combining methods
- Error handling for edge cases
- Performance benchmarking
- Cross-script matching
- Typo handling

**How to run**:
```bash
python test_fuzzy.py
```

**Output**: Verbose test output showing all test results with ✓ for passed tests

**Best for**: Development and regression testing

---

## 2️⃣ Real Dataset Tests (Comprehensive)

### File: `test_with_real_dataset.py`
**Status**: ✅ Working with 5,000 documents

**What it tests**:
- Loading all 5,000 documents from database
- 8 different queries (4 Bangla + 4 English)
- Cross-lingual search capability
- Search performance with real data
- Document snippets and ranking
- Transliteration effectiveness

**Database Stats**:
- Total documents: 5,000
- English: 2,500
- Bangla: 2,500
- Languages detected: Both

**Transliteration Map**:
- Entries: 66
- Total variants: 136
- Average variants per term: 2.1

**How to run**:
```bash
python test_with_real_dataset.py
```

**Output**: 
- Full test results for 8 queries
- Document titles with scores
- Language distribution
- Performance metrics
- Summary statistics

**Duration**: ~6 minutes (testing 5,000 documents)

**Best for**: Complete validation before deployment

---

## 3️⃣ Optimized Real Dataset Tests (Interactive)

### File: `test_real_dataset_optimized.py`
**Status**: ✅ Interactive menu with 4 options

**Option A: Fast Test (500 documents)**
```bash
echo "A" | python test_real_dataset_optimized.py
```
- Documents: 500
- Queries: 3
- Duration: 2-5 seconds
- Best for: Quick verification

**Option B: Performance Analysis**
```bash
echo "B" | python test_real_dataset_optimized.py
```
- Documents: 100, 500, 1000, 2000
- Tests: Scalability across sizes
- Duration: 1 minute
- Shows: Search time vs document count
- Best for: Performance optimization

**Performance Chart Output**:
```
Documents | Search Time | Speed
100       |   33.3ms    | 3 docs/ms ██
500       |  158.7ms    | 3 docs/ms ████████
1000      |  313.1ms    | 3 docs/ms ███████████████
2000      |  640.4ms    | 3 docs/ms ████████████████████████████
```

**Option C: Cross-Lingual Demo**
```bash
echo "C" | python test_real_dataset_optimized.py
```
- Documents: 1000
- Test pairs: 3 cross-lingual terms
- Language: Mixed English + Bangla
- Best for: Demonstrating CLIR capability

**Option D: Run All Tests**
```bash
echo "D" | python test_real_dataset_optimized.py
```
- Runs A + B + C sequentially
- Duration: ~8 minutes
- Best for: Complete system validation

**How to run interactively**:
```bash
python test_real_dataset_optimized.py
# Then select: A, B, C, or D
```

**Best for**: Custom testing scenarios

---

## 4️⃣ Mixed Language Verification

### File: `test_mixed_languages.py`
**Status**: ✅ Best for quick validation

**What it tests**:
- Balanced dataset (250 English + 250 Bangla)
- 4 cross-lingual search pairs
- Language distribution in results
- Cross-lingual match rates
- Sample result display

**Cross-Lingual Test Pairs**:
```
English     Bangla          Topic       Results
Dhaka       ঢাকা            City        3+3
Corona      করোনা          Health      3+3
Bangladesh  বাংলাদেশ       Country     3+3
News        খবর             General     3+3
```

**How to run**:
```bash
python test_mixed_languages.py
```

**Output**: 
- Language distribution
- Cross-lingual match table
- Sample results with language tags
- Success confirmation

**Duration**: ~30 seconds

**Best for**: Daily verification and demos

---

## 5️⃣ Utility: Database Schema

### File: `check_schema.py`
**Status**: ✅ Utility for database inspection

**What it does**:
- Displays all tables in database
- Shows column names and types
- Displays sample row data
- Useful for debugging

**How to run**:
```bash
python check_schema.py
```

**Output**:
```
Tables: [('articles',), ('sqlite_sequence',)]

articles columns:
  - id (INTEGER)
  - source (TEXT)
  - title (TEXT)
  - body (TEXT)
  - url (TEXT)
  - date (TEXT)
  - language (TEXT)
  - tokens (INTEGER)
  - word_embeddings (TEXT)
  - named_entities (TEXT)
```

**Best for**: Database troubleshooting

---

## Recommended Testing Workflow

### Daily Verification (30 seconds)
```bash
python test_mixed_languages.py
```
✅ Shows cross-lingual search working

### Before Deployment (6 minutes)
```bash
python test_with_real_dataset.py
```
✅ Full validation with all 5,000 documents

### Performance Optimization (1 minute)
```bash
echo "B" | python test_real_dataset_optimized.py
```
✅ Verify scalability remains linear

### Quick Demo (2-5 seconds)
```bash
echo "A" | python test_real_dataset_optimized.py
```
✅ Show system working to stakeholders

### Development Testing (Continuous)
```bash
python test_fuzzy.py
```
✅ Run after code changes for regression testing

---

## Test Comparison Matrix

| Test | Docs | Time | Best For | Key Output |
|------|------|------|----------|-----------|
| test_fuzzy.py | N/A | ~1s | Unit testing | ✓ Pass/Fail |
| test_mixed_languages.py | 500 | 30s | Daily check | Cross-lingual match rate |
| test_real_dataset_optimized.py A | 500 | 5s | Quick demo | Search results |
| test_real_dataset_optimized.py B | 2000 | 1m | Performance | Scaling chart |
| test_real_dataset_optimized.py C | 1000 | 2m | CLIR demo | Language distribution |
| test_with_real_dataset.py | 5000 | 6m | Full validation | Comprehensive results |

---

## Expected Results Summary

### ✅ All Tests Should Show:
1. **Successful database load**
   - "✓ Loaded X documents in Y.XXs"

2. **Cross-lingual matches**
   - English queries finding results
   - Bangla queries finding results

3. **Linear performance**
   - ~3 docs/ms throughput
   - ~0.3ms per document

4. **No errors**
   - Exit Code: 0 (success)
   - No exceptions or tracebacks

5. **Language detection**
   - Documents labeled 'en' or 'bn'
   - Mixed results for cross-lingual queries

---

## Troubleshooting Tests

### Test crashes with "module not found"
```bash
cd fuzzy_matching
python test_mixed_languages.py
```
Make sure you're in the fuzzy_matching directory!

### Test shows "No results found"
This is normal for some edge cases. Check:
- Transliteration map has the term
- Threshold is not too high (try 0.5-0.65)
- Database has documents in that language

### Test runs very slowly
- First run loads database (~10-15 seconds)
- Subsequent runs are faster
- If still slow, use test_real_dataset_optimized.py Option A

### Database not found error
Check path is relative to script location:
```python
# In fuzzy_matching/
db_path = Path(__file__).parent.parent / "dataset_enhanced" / "combined_dataset.db"
```

---

## CI/CD Integration

### Continuous Integration Suggestion
Add to your CI pipeline:

```bash
#!/bin/bash
cd fuzzy_matching

# Unit tests (fast)
python test_fuzzy.py
if [ $? -ne 0 ]; then exit 1; fi

# Quick integration test (fast)
python test_mixed_languages.py
if [ $? -ne 0 ]; then exit 1; fi

# Performance check (once daily)
echo "B" | python test_real_dataset_optimized.py
if [ $? -ne 0 ]; then exit 1; fi

echo "All tests passed!"
```

---

## Documentation Files

Located in fuzzy_matching/:

1. **TESTING_SUMMARY.md** ← You are here
2. **QUICK_START_REAL_DATA.md** - Usage examples
3. **REAL_DATASET_TEST_RESULTS.md** - Detailed test results
4. **README.md** - API documentation
5. **START_HERE.md** - Getting started guide

---

## Success Indicators

When all tests pass, you'll see:

```
✓ Loaded 5000 documents
✓ Found X results
✅ TRANSLITERATION MATCHING WORKING CORRECTLY!
✅ CROSS-LINGUAL TRANSLITERATION MATCHING WORKING!
```

**Exit Code: 0** = SUCCESS ✅

---

## Quick Test Commands

```bash
# Quick check (30 seconds)
python test_mixed_languages.py

# Full validation (6 minutes)
python test_with_real_dataset.py

# Unit tests (1 second)
python test_fuzzy.py

# Interactive options (select A/B/C/D)
python test_real_dataset_optimized.py

# Check database schema
python check_schema.py
```

---

**Last Updated**: January 3, 2026  
**All Tests**: ✅ PASSING  
**Status**: Production Ready 🚀
