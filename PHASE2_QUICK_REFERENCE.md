# Phase 2: Query Processing - Quick Reference Card

## 🎯 Quick Start

```python
# Import all Phase 2 components
from language_detector import LanguageDetector
from query_normalizer import QueryNormalizer
from query_translator import QueryTranslator
from query_expander import QueryExpander

# Initialize
detector = LanguageDetector()
normalizer = QueryNormalizer()
translator = QueryTranslator()
expander = QueryExpander()

# Process a query
query = "  CORONAVIRUS Vaccine  "
query = normalizer.normalize(query)          # → "coronavirus vaccine"
lang = detector.detect(query)                # → "en"
expanded = expander.expand_to_query(query)   # → "coronaviru OR coronavirus OR ..."
translated = translator.english_to_bangla(query)  # → "করোনাভাইরাস টিকা"
```

---

## 📚 Component Reference

### 1️⃣ Language Detection

**Import:**
```python
from language_detector import LanguageDetector, detect_language
```

**Quick Use:**
```python
# Method 1: Class
detector = LanguageDetector()
lang = detector.detect("করোনা")  # → "bn"
result = detector.detect_with_confidence("test")  
# → {'language': 'en', 'confidence': 1.0, 'method': 'unicode'}

# Method 2: Function
lang = detect_language("coronavirus")  # → "en"
```

**Supports:**
- `'en'` - English
- `'bn'` - Bangla
- `'mixed'` - Mixed content
- `'unknown'` - Unrecognized

---

### 2️⃣ Query Normalization

**Import:**
```python
from query_normalizer import QueryNormalizer, normalize_query
```

**Quick Use:**
```python
# Method 1: Class
normalizer = QueryNormalizer()
clean = normalizer.normalize("  TEST  ")  # → "test"
batch = normalizer.batch_normalize(["A", "B"])  # → ["a", "b"]

# Method 2: Function
clean = normalize_query("  CORONAVIRUS  ")  # → "coronavirus"
```

**Operations:**
- Lowercase conversion
- Whitespace normalization
- Leading/trailing space removal
- Multiple spaces → single space

---

### 3️⃣ Query Translation

**Import:**
```python
from query_translator import QueryTranslator, translate_query
```

**Quick Use:**
```python
# Method 1: Class
translator = QueryTranslator()

# English → Bangla
bn = translator.english_to_bangla("vaccine")  # → "টিকা"

# Bangla → English  
en = translator.bangla_to_english("করোনা")  # → "Corona"

# Generic
result = translator.translate("test", "en", "bn")

# Batch
results = translator.batch_translate(["a", "b"], "en", "bn")

# Method 2: Function
bn = translate_query("vaccine", "en", "bn")
```

**Features:**
- Automatic caching (MD5-based)
- Batch translation support
- Multiple backends (deep-translator, googletrans)
- Cache management

---

### 4️⃣ Query Expansion

**Import:**
```python
from query_expander import QueryExpander, expand_query, get_synonyms, get_root_words
```

**Quick Use:**
```python
# Method 1: Class
expander = QueryExpander(max_synonyms=3)

# Full expansion
result = expander.expand("vaccine test")
# → {'original': ..., 'terms': ..., 'expanded_terms': [...]}

# Query string
expanded = expander.expand_to_query("news")  
# → "intelligence OR news OR tidings OR word"

# Individual operations
syns = expander.get_synonyms("good")  # → ['commodity', 'goodness', ...]
stem = expander.get_stem("running")   # → "run"
lemma = expander.get_lemma("running") # → "running"

# Method 2: Functions
terms = expand_query("test")  # → ['test', 'trial', ...]
syns = get_synonyms("good", max_count=3)
roots = get_root_words("running matches")  # → {'running': 'run', 'matches': 'match'}
```

**Configuration:**
```python
# High recall (more expansions)
expander = QueryExpander(max_synonyms=5, use_stemming=True, use_lemmatization=True)

# High precision (fewer expansions)
expander = QueryExpander(max_synonyms=1, use_stemming=True, use_lemmatization=False)
```

---

## 🔄 Complete Pipeline

```python
def process_query(user_query):
    """Complete query processing pipeline."""
    
    # Initialize components
    normalizer = QueryNormalizer()
    detector = LanguageDetector()
    expander = QueryExpander()
    translator = QueryTranslator()
    
    # Step 1: Normalize
    query = normalizer.normalize(user_query)
    
    # Step 2: Detect language
    lang = detector.detect(query)
    
    # Step 3: Expand (English only)
    if lang == 'en':
        expanded = expander.expand_to_query(query)
    else:
        expanded = query
    
    # Step 4: Translate for cross-lingual search
    if lang == 'bn':
        en_query = translator.bangla_to_english(query)
    elif lang == 'en':
        bn_query = translator.english_to_bangla(query)
    
    return {
        'normalized': query,
        'language': lang,
        'expanded': expanded,
        'translated': en_query if lang == 'bn' else bn_query
    }
```

---

## 📊 Testing Commands

```bash
# Language Detection
python language_detector.py
python test_language_detector.py

# Normalization
python query_normalizer.py
python test_query_normalizer.py

# Translation
python query_translator.py
python -c "from query_translator import QueryTranslator; t=QueryTranslator(); print(t.english_to_bangla('test'))"

# Expansion
python query_expander.py
python simple_test_expander.py
```

---

## 🎨 Example Outputs

### Detection
```python
detect_language("coronavirus")       # → "en"
detect_language("করোনা")           # → "bn"
detect_language("test করোনা")      # → "mixed"
```

### Normalization
```python
normalize_query("  TEST  ")                    # → "test"
normalize_query("CORONAVIRUS   VACCINE")       # → "coronavirus vaccine"
normalize_query("করোনা  ভ্যাকসিন")           # → "করোনা ভ্যাকসিন"
```

### Translation
```python
translate_query("coronavirus", "en", "bn")     # → "করোনাভাইরাস"
translate_query("vaccine", "en", "bn")         # → "টিকা"
translate_query("করোনা", "bn", "en")         # → "Corona"
```

### Expansion
```python
expand_query("vaccine")                        
# → ["vaccin", "vaccine", "vaccinum"]

expand_query("coronavirus vaccine")            
# → ["coronaviru", "coronavirus", "vaccin", "vaccine", "vaccinum"]

get_synonyms("good")                           
# → ["commodity", "goodness", "trade good"]

get_root_words("running matches vaccination")  
# → {"running": "run", "matches": "match", "vaccination": "vaccin"}
```

---

## 🛠️ Troubleshooting

### Issue: NLTK data not found
```python
import nltk
nltk.download('wordnet')
nltk.download('omw-1.4')
nltk.download('averaged_perceptron_tagger')
```

### Issue: Translation fails
```bash
# Install deep-translator
pip install deep-translator

# Or use googletrans fallback
pip install googletrans==4.0.0-rc1
```

### Issue: Encoding errors (Windows)
```powershell
# Set UTF-8 in PowerShell
chcp 65001
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
```

---

## 📦 Dependencies

```bash
# Install all Phase 2 dependencies
pip install -r requirements.txt

# Individual packages
pip install deep-translator  # Translation
pip install nltk             # Query expansion
```

---

## ✅ Quick Checks

**All components installed?**
```python
import language_detector  # ✓
import query_normalizer   # ✓
import query_translator   # ✓
import query_expander     # ✓
```

**NLTK data ready?**
```python
import nltk
nltk.data.find('corpora/wordnet')  # Should not raise error
```

**Translation backend working?**
```python
from query_translator import QueryTranslator
t = QueryTranslator()
print(t.backend)  # Should show 'deep_translator' or 'googletrans'
```

---

## 🎯 Common Patterns

### Pattern 1: English Query Search
```python
query = "coronavirus vaccine"
query = normalize_query(query)
lang = detect_language(query)
expanded = expand_query(query)  # For better recall
# Use 'expanded' for searching English documents
```

### Pattern 2: Bangla Query Search
```python
query = "করোনা ভ্যাকসিন"
query = normalize_query(query)
lang = detect_language(query)
translated = translate_query(query, "bn", "en")
# Use 'translated' for searching English documents
```

### Pattern 3: Cross-Lingual Search
```python
query = normalize_query(user_input)
lang = detect_language(query)

if lang == 'en':
    # Search English docs with expansion
    en_query = expand_query(query)
    # Search Bangla docs with translation
    bn_query = translate_query(query, "en", "bn")
elif lang == 'bn':
    # Search Bangla docs as-is
    bn_query = query
    # Search English docs with translation
    en_query = translate_query(query, "bn", "en")
```

---

**Phase 2 Complete!** All components ready for use. ✅
