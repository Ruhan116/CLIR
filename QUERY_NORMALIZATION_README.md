# Query Normalization Module

**Phase 2: Query Processing - Normalization (lowercase, whitespace)**

## Overview

The Query Normalization module provides text normalization functionality for the CLIR (Cross-Lingual Information Retrieval) system. It handles both English and Bangla text, ensuring consistent query processing across languages.

## Features

✅ **Lowercase Conversion**
- Converts English text to lowercase
- Preserves Bangla characters (no case in Bangla)

✅ **Whitespace Normalization**
- Removes multiple spaces
- Converts tabs and newlines to spaces
- Strips leading/trailing whitespace

✅ **Optional Features**
- Punctuation stripping
- Unicode normalization (NFC)

✅ **Batch Processing**
- Normalize multiple queries at once

## Quick Start

### Basic Usage

```python
from query_normalizer import normalize_query

# Normalize a query
query = "  COVID-19   VACCINE   NEWS  "
normalized = normalize_query(query)
print(normalized)  # Output: 'covid-19 vaccine news'

# Works with Bangla too
bangla_query = "  করোনা   ভ্যাকসিন  "
normalized = normalize_query(bangla_query)
print(normalized)  # Output: 'করোনা ভ্যাকসিন'
```

### Advanced Usage

```python
from query_normalizer import QueryNormalizer

# Create normalizer with custom settings
normalizer = QueryNormalizer(
    lowercase=True,
    normalize_whitespace=True,
    strip_punctuation=False,
    unicode_normalize=False
)

# Normalize text
result = normalizer.normalize("  HELLO   WORLD  ")
print(result)  # Output: 'hello world'

# Batch normalization
queries = ["  Query 1  ", "  Query 2  "]
results = normalizer.batch_normalize(queries)
```

## Integration with CLIR Pipeline

The normalization module integrates seamlessly with the language detection module:

```python
from query_normalizer import QueryNormalizer
from language_detector import LanguageDetector

# Initialize components
normalizer = QueryNormalizer()
detector = LanguageDetector()

# Process query
query = "  COVID-19   Latest   News  "

# Step 1: Normalize
normalized = normalizer.normalize(query)

# Step 2: Detect language
language = detector.detect(normalized)

# Step 3: Ready for search
print(f"Normalized: {normalized}")
print(f"Language: {language}")
# Output:
# Normalized: covid-19 latest news
# Language: en
```

## API Reference

### `QueryNormalizer` Class

#### Constructor

```python
QueryNormalizer(
    lowercase: bool = True,
    normalize_whitespace: bool = True,
    strip_punctuation: bool = False,
    unicode_normalize: bool = False
)
```

#### Methods

- `normalize(text: str) -> str`: Apply all configured normalizations
- `normalize_lowercase(text: str) -> str`: Convert to lowercase only
- `normalize_whitespace(text: str) -> str`: Normalize whitespace only
- `batch_normalize(texts: list) -> list`: Normalize multiple texts

### Convenience Functions

- `normalize_query(text, lowercase=True, whitespace=True)`: Quick normalization
- `normalize_for_search(text)`: Optimize for search operations

## Testing

Run the test suite:

```bash
# Run all tests
python test_query_normalizer.py

# Run specific test class
python -m unittest test_query_normalizer.TestQueryNormalizer -v
```

## Usage Examples

See complete examples:

```bash
python query_normalizer_usage.py
```

## Implementation Status

| Feature | Status | Notes |
|---------|--------|-------|
| Lowercase conversion | ✅ Done | Works with English and Bangla |
| Whitespace normalization | ✅ Done | Handles spaces, tabs, newlines |
| Empty input handling | ✅ Done | Returns empty string |
| Punctuation stripping | ✅ Done | Optional feature |
| Unicode normalization | ✅ Done | Optional feature |
| Batch processing | ✅ Done | Process multiple queries |
| Integration tests | ✅ Done | Tests with language detection |

## Files

- `query_normalizer.py` - Main normalization module
- `test_query_normalizer.py` - Test suite
- `query_normalizer_usage.py` - Usage examples
- `QUERY_NORMALIZATION_README.md` - This file

## Next Steps

1. ✅ Language Detection - Already implemented
2. ✅ Normalization - **COMPLETED**
3. ⏭️ Query Translation - Next phase
4. ⏭️ Query Expansion - Future enhancement

## Performance Notes

- Normalization is very fast (< 1ms per query)
- Batch processing recommended for large datasets
- No external dependencies required
- Thread-safe for concurrent use

## Examples

### English Queries

```python
"  COVID-19   VACCINE  "  →  "covid-19 vaccine"
"BANGLADESH   CRICKET"   →  "bangladesh cricket"
"Election\tResults"      →  "election results"
```

### Bangla Queries

```python
"  করোনা   ভ্যাকসিন  "  →  "করোনা ভ্যাকসিন"
"বাংলাদেশ\tক্রিকেট"     →  "বাংলাদেশ ক্রিকেট"
```

### Mixed Language

```python
"  Bangladesh  করোনা  Vaccine  "  →  "bangladesh করোনা vaccine"
```

## Author

**Phase 2: Query Processing** - Nowshin  
**Date**: January 2026
