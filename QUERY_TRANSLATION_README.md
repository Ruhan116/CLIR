# Query Translation Module

**Phase 2: Query Processing - Query Translation (English ↔ Bangla)**

## Overview

The Query Translation module provides bidirectional translation between English and Bangla for cross-lingual information retrieval. It enables users to search documents in one language using queries in another language.

## Features

✅ **Bidirectional Translation**
- English to Bangla
- Bangla to English

✅ **Multiple Backends**
- deep-translator (recommended)
- googletrans (fallback)
- Auto-selection of best available backend

✅ **Performance Optimization**
- Translation caching for repeated queries
- Batch translation support

✅ **Error Handling**
- Graceful fallback on translation errors
- Clear error messages

✅ **Integration**
- Seamless integration with language detection
- Works with query normalization
- Full CLIR pipeline support

## Installation

Install a translation library:

```bash
# Recommended: deep-translator (more reliable)
pip install deep-translator

# Alternative: googletrans
pip install googletrans==4.0.0-rc1
```

## Quick Start

### Basic Usage

```python
from query_translator import QueryTranslator

# Initialize translator
translator = QueryTranslator()

# Translate English to Bangla
query_bn = translator.english_to_bangla("coronavirus vaccine")
print(query_bn)  # করোনাভাইরাস ভ্যাকসিন

# Translate Bangla to English
query_en = translator.bangla_to_english("করোনা ভ্যাকসিন")
print(query_en)  # Corona vaccine
```

### Convenience Functions

```python
from query_translator import translate_query, english_to_bangla, bangla_to_english

# Quick translation
result = english_to_bangla("cricket match")
result = bangla_to_english("ক্রিকেট খেলা")
result = translate_query("test", "en", "bn")
```

## Integration with CLIR Pipeline

Complete query processing with translation:

```python
from query_normalizer import QueryNormalizer
from language_detector import LanguageDetector
from query_translator import QueryTranslator

# Initialize components
normalizer = QueryNormalizer()
detector = LanguageDetector()
translator = QueryTranslator()

# Process query
user_query = "  COVID-19   vaccine   news  "

# Step 1: Normalize
normalized = normalizer.normalize(user_query)
# Result: 'covid-19 vaccine news'

# Step 2: Detect language
source_lang = detector.detect(normalized)
# Result: 'en'

# Step 3: Translate for cross-lingual search
target_lang = 'bn' if source_lang == 'en' else 'en'
translated = translator.translate(normalized, source_lang, target_lang)
# Result: 'করোনা-১৯ ভ্যাকসিনের খবর'

# Step 4: Search both indexes
# - Search English index with: 'covid-19 vaccine news'
# - Search Bangla index with: 'করোনা-১৯ ভ্যাকসিনের খবর'
# - Merge and rank results
```

## API Reference

### `QueryTranslator` Class

#### Constructor

```python
QueryTranslator(backend='auto', use_cache=True)
```

**Parameters:**
- `backend`: Translation backend ('deep_translator', 'googletrans', or 'auto')
- `use_cache`: Enable translation caching for performance

#### Methods

**Core Translation:**
- `translate(text, source_lang, target_lang) -> str`
- `english_to_bangla(text) -> str`
- `bangla_to_english(text) -> str`

**Batch Processing:**
- `batch_translate(texts, source_lang, target_lang) -> List[str]`

**Utilities:**
- `translate_with_original(text, source_lang, target_lang) -> Tuple[str, str]`
- `auto_translate(text, target_lang) -> str`
- `clear_cache()` - Clear translation cache
- `get_cache_size() -> int` - Get number of cached translations
- `get_backend_info() -> Dict` - Get backend information

### Convenience Functions

```python
translate_query(text: str, source_lang: str, target_lang: str) -> str
english_to_bangla(text: str) -> str
bangla_to_english(text: str) -> str
```

## Usage Examples

### Example 1: Cross-Lingual Search

```python
translator = QueryTranslator()

# English query searching Bangla documents
en_query = "coronavirus vaccine"
bn_query = translator.english_to_bangla(en_query)

# Search both indexes
search_engine.search(en_query, lang='en')  # English docs
search_engine.search(bn_query, lang='bn')  # Bangla docs
```

### Example 2: Batch Translation

```python
queries = [
    "coronavirus vaccine",
    "cricket match",
    "election results"
]

translations = translator.batch_translate(queries, "en", "bn")
```

### Example 3: Translation Caching

```python
translator = QueryTranslator(use_cache=True)

# First call - translates and caches
result1 = translator.english_to_bangla("test")

# Second call - uses cache (faster)
result2 = translator.english_to_bangla("test")

print(f"Cache size: {translator.get_cache_size()}")  # 1
```

### Example 4: Backend Selection

```python
# Auto-select best available
translator = QueryTranslator(backend='auto')

# Specific backend
translator = QueryTranslator(backend='deep_translator')

# Check backend info
info = translator.get_backend_info()
print(info)
# {'backend': 'deep_translator', 'cache_enabled': True, 'cache_size': 0}
```

## Testing

Run the test suite:

```bash
# Run all tests
python test_query_translator.py

# Run specific test class
python -m unittest test_query_translator.TestQueryTranslator -v
```

## Usage Examples

See complete examples:

```bash
python query_translator_usage.py
```

## Implementation Status

| Feature | Status | Notes |
|---------|--------|-------|
| English → Bangla translation | ✅ Done | Using Google Translate API |
| Bangla → English translation | ✅ Done | Using Google Translate API |
| Translation caching | ✅ Done | MD5-based cache keys |
| Batch translation | ✅ Done | Process multiple queries |
| Multiple backends | ✅ Done | deep-translator, googletrans |
| Error handling | ✅ Done | TranslationError exception |
| Integration with pipeline | ✅ Done | CLIRQueryPipeline updated |
| Tests | ✅ Done | Unit and integration tests |

## Files

- `query_translator.py` - Main translation module
- `test_query_translator.py` - Test suite
- `query_translator_usage.py` - Usage examples
- `QUERY_TRANSLATION_README.md` - This file
- `clir_query_pipeline.py` - Updated with translation support

## Performance

### Translation Speed
- **First translation**: ~500-1000ms (API call)
- **Cached translation**: <1ms (cache lookup)
- **Batch translation**: ~500-1000ms per batch (parallel processing possible)

### Caching
- Cache key: MD5 hash of `text|source_lang|target_lang`
- Memory efficient for typical query lengths
- Can be cleared with `clear_cache()`

## Error Handling

```python
from query_translator import TranslationError

try:
    result = translator.translate("test", "en", "bn")
except TranslationError as e:
    print(f"Translation failed: {e}")
    # Handle error (use original query, log error, etc.)
```

## Integration with BM25 Search

```python
from query_translator import QueryTranslator
from bm25_clir import BM25CLIR

translator = QueryTranslator()
bm25 = BM25CLIR()

# User query in English
query = "coronavirus vaccine"

# Translate for cross-lingual search
query_bn = translator.english_to_bangla(query)

# Search both language indexes
results_en = bm25.search(query, language='en', top_k=10)
results_bn = bm25.search(query_bn, language='bn', top_k=10)

# Merge and rank results
all_results = merge_and_rank(results_en, results_bn)
```

## Troubleshooting

### Translation Library Not Found

**Error:** `ImportError: No translation library available`

**Solution:**
```bash
pip install deep-translator
# or
pip install googletrans==4.0.0-rc1
```

### Translation Fails

**Error:** `TranslationError: Translation failed`

**Possible causes:**
- No internet connection
- API rate limiting
- Invalid text encoding

**Solutions:**
- Check internet connection
- Implement retry logic
- Use cache to reduce API calls
- Consider fallback to original query

### Cache Issues

If cache grows too large:
```python
# Clear cache periodically
translator.clear_cache()

# Or disable caching
translator = QueryTranslator(use_cache=False)
```

## Best Practices

1. **Enable caching** for repeated queries
2. **Use batch translation** for multiple queries
3. **Handle errors gracefully** - fall back to original query
4. **Clear cache periodically** to free memory
5. **Integrate with normalization** for best results
6. **Monitor API usage** to avoid rate limits

## Next Steps

1. ✅ **Query Translation** - COMPLETED
2. ⏭️ **Query Expansion** (Optional)
   - Synonyms
   - Related terms
   - Root words
3. ⏭️ **Result Merging**
   - Combine results from both languages
   - Rank by relevance
   - Remove duplicates

## Examples

### English to Bangla

```python
"coronavirus vaccine"    → "করোনাভাইরাস ভ্যাকসিন"
"cricket match"          → "ক্রিকেট ম্যাচ"
"election results"       → "নির্বাচনের ফলাফল"
"weather forecast"       → "আবহাওয়ার পূর্বাভাস"
```

### Bangla to English

```python
"করোনা ভ্যাকসিন"        → "Corona vaccine"
"ক্রিকেট খেলা"         → "Cricket match"
"নির্বাচন ফলাফল"       → "Election results"
"আবহাওয়া"             → "Weather"
```

## Author

**Phase 2: Query Processing** - Nowshin  
**Date**: January 2026  
**Task**: Query Translation (English ↔ Bangla)
