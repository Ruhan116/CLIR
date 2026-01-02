# BM25 Cross-Lingual Information Retrieval (CLIR) System

Complete BM25 implementation for searching English and Bangla news articles.

## Dataset Organization

### 1. **Raw Text Files** (Legacy format)
Located in `bangla_dataset/` and `english_dataset/`:
```
bangla_dataset/
├── banglanews24_stories.txt    # Articles in text format
├── dhakapost_stories.txt
├── jugantor_stories.txt
├── kalerkantho_stories.txt
└── prothomalo_stories.txt

english_dataset/
├── stories.txt                 # Combined English articles
├── bss_stories.txt
├── dhaka_stories.txt
├── newage_stories.txt
└── tbs_stories.txt
```

**Format:** Each article separated by `=== Article N ===` with URL, Title, Date, and Body.

### 2. **SQLite Databases** (Recommended)
The structured database format for easy querying:

```
bangla_dataset/bangla_articles.db      # 2,500 Bangla articles
english_dataset/english_articles.db    # 2,500 English articles
dataset_enhanced/combined_dataset.db   # 5,000 combined articles
```

**Schema:**
```sql
CREATE TABLE articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT,           -- e.g., "BanglaNews24", "The Daily Star"
    title TEXT,            -- Article title
    body TEXT,             -- Full article text
    url TEXT UNIQUE,       -- Article URL
    date TEXT,             -- Publication date (ISO format)
    language TEXT,         -- "en" or "bn"
    tokens INTEGER,        -- Token count (optional)
    word_embeddings TEXT,  -- Reserved for future use
    named_entities TEXT    -- Reserved for future use
);
```

### 3. **Combined Dataset** (Best for BM25)
The `combined_dataset.db` contains all articles in one database:
- **Total:** 5,000 articles
- **English:** 2,500 articles from 5 sources
- **Bangla:** 2,500 articles from 5 sources

## Quick Start

### Installation

```bash
pip install rank-bm25 numpy
```

### Basic Usage

```python
from BM25.bm25_clir import BM25CLIR

# Initialize
clir = BM25CLIR()

# Build index (do this once)
clir.build_index("both")  # or "en" or "bn"

# Search English
results = clir.search("cricket match", language="en", top_k=5)
clir.print_results(results)

# Search Bangla
results = clir.search("করোনা ভাইরাস", language="bn", top_k=5)
clir.print_results(results)
```

## API Reference

### BM25CLIR Class

#### Constructor
```python
BM25CLIR(db_path: str = None)
```
- `db_path`: Path to SQLite database (defaults to `combined_dataset.db`)

#### Methods

##### `build_index(language: str = "both")`
Build BM25 index for specified language(s).
- `language`: `"en"`, `"bn"`, or `"both"`

```python
clir = BM25CLIR()
clir.build_index("both")  # Index English and Bangla
```

##### `search(query: str, language: str = "en", top_k: int = 10)`
Search for articles using BM25.
- `query`: Search query string
- `language`: `"en"` or `"bn"`
- `top_k`: Number of results to return
- Returns: List of `(Article, score)` tuples

```python
results = clir.search("economy growth", language="en", top_k=10)
for article, score in results:
    print(f"{article.title} (score: {score:.2f})")
```

##### `search_multilingual(query, query_lang, top_k=10, results_per_lang=None)`
Search across both languages.
- `query`: Search query
- `query_lang`: Language of query (`"en"` or `"bn"`)
- `top_k`: Total results (if `results_per_lang` is None)
- `results_per_lang`: Results per language
- Returns: Dictionary with `"en"` and `"bn"` keys

```python
# Get 5 results from each language
results = clir.search_multilingual(
    query="health",
    query_lang="en",
    results_per_lang=5
)

print(f"English: {len(results['en'])} results")
print(f"Bangla: {len(results['bn'])} results")
```

##### `get_article_by_id(article_id: int, language: str)`
Retrieve a specific article.
```python
article = clir.get_article_by_id(42, "en")
print(article.title)
```

##### `get_statistics()`
Get dataset statistics.
```python
stats = clir.get_statistics()
print(f"Total: {stats['total_articles']}")
```

##### `print_results(results, max_body_length=200, show_url=True)`
Pretty print search results.

### Article Dataclass

```python
@dataclass
class Article:
    id: int
    source: str
    title: str
    body: str
    url: str
    date: str
    language: str
```

## Usage Examples

### Example 1: Simple English Search
```python
from BM25.bm25_clir import BM25CLIR

clir = BM25CLIR()
clir.build_index("en")

results = clir.search("climate change policy", language="en", top_k=5)
for i, (article, score) in enumerate(results, 1):
    print(f"{i}. {article.title} (score: {score:.4f})")
    print(f"   Source: {article.source}, Date: {article.date}")
    print(f"   {article.body[:150]}...\n")
```

### Example 2: Bangla Search
```python
clir = BM25CLIR()
clir.build_index("bn")

# Search for articles about "cricket"
results = clir.search("ক্রিকেট খেলা", language="bn", top_k=5)
clir.print_results(results)
```

### Example 3: Compare Search Across Languages
```python
clir = BM25CLIR()
clir.build_index("both")

# Search the same topic in both languages
en_results = clir.search("election", language="en", top_k=3)
bn_results = clir.search("নির্বাচন", language="bn", top_k=3)

print("English Results:")
clir.print_results(en_results)

print("\nBangla Results:")
clir.print_results(bn_results)
```

### Example 4: Batch Query Processing
```python
clir = BM25CLIR()
clir.build_index("both")

queries = [
    ("en", "sports football"),
    ("en", "economy gdp"),
    ("bn", "শিক্ষা"),
    ("bn", "স্বাস্থ্য"),
]

for lang, query in queries:
    results = clir.search(query, language=lang, top_k=1)
    if results:
        article, score = results[0]
        print(f"[{lang}] '{query}' → {article.title[:50]}...")
```

### Example 5: Custom Score Processing
```python
clir = BM25CLIR()
clir.build_index("en")

results = clir.search("technology innovation", language="en", top_k=20)

# Filter by score threshold
high_quality = [(art, sc) for art, sc in results if sc >= 15.0]
print(f"High quality matches: {len(high_quality)}")

# Score statistics
scores = [score for _, score in results]
print(f"Average score: {sum(scores)/len(scores):.2f}")
print(f"Max score: {max(scores):.2f}")
```

### Example 6: Access Raw Data
```python
clir = BM25CLIR()

# Get article counts
print(f"English articles: {len(clir.articles['en'])}")
print(f"Bangla articles: {len(clir.articles['bn'])}")

# Access a specific article
article = clir.articles["en"][0]
print(f"Title: {article.title}")
print(f"Body length: {len(article.body)} chars")
print(f"URL: {article.url}")
```

## Running Examples

### Run All Examples
```bash
cd BM25
python bm25_usage_examples.py
```

### Interactive Mode
```bash
python bm25_usage_examples.py interactive
```

In interactive mode:
- Type queries directly for English search
- Prefix with `bn:` for Bangla (e.g., `bn:করোনা`)
- Type `stats` for statistics
- Type `quit` to exit

## How to Load and Use the Dataset

### Method 1: Using BM25CLIR (Recommended)
```python
from BM25.bm25_clir import BM25CLIR

# Automatically loads from combined_dataset.db
clir = BM25CLIR()

# Access articles
for article in clir.articles["en"][:5]:
    print(article.title)
```

### Method 2: Direct SQLite Access
```python
import sqlite3

conn = sqlite3.connect("dataset_enhanced/combined_dataset.db")
cursor = conn.cursor()

# Get all English articles
cursor.execute("SELECT title, body FROM articles WHERE language = 'en'")
for title, body in cursor.fetchall():
    print(title)

conn.close()
```

### Method 3: Load by Language
```python
import sqlite3

def load_articles_by_language(language: str):
    conn = sqlite3.connect("dataset_enhanced/combined_dataset.db")
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, source, title, body, url, date
        FROM articles
        WHERE language = ? AND body IS NOT NULL
    """, (language,))
    
    articles = cursor.fetchall()
    conn.close()
    return articles

# Load English articles
en_articles = load_articles_by_language("en")
print(f"Loaded {len(en_articles)} English articles")
```

### Method 4: Load by Source
```python
import sqlite3

def load_articles_by_source(source: str):
    conn = sqlite3.connect("dataset_enhanced/combined_dataset.db")
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT title, body FROM articles WHERE source = ?
    """, (source,))
    
    articles = cursor.fetchall()
    conn.close()
    return articles

# Load from specific source
articles = load_articles_by_source("The Daily Star")
print(f"Found {len(articles)} articles from The Daily Star")
```

## Dataset Sources

### English Sources
1. **The Daily Star** - Leading English daily
2. **Dhaka Tribune** - English news portal
3. **New Age** - Independent newspaper
4. **TBS News** - The Business Standard
5. **BSS News** - Bangladesh Sangbad Sangstha

### Bangla Sources
1. **Prothom Alo** (প্রথম আলো) - Most popular Bangla daily
2. **Kalerkantho** (কালের কণ্ঠ) - Daily newspaper
3. **Jugantor** (যুগান্তর) - Daily newspaper
4. **Bangla News 24** - Online news portal
5. **Dhaka Post** - News portal

## Performance Tips

1. **Build index once**: Building the BM25 index takes time. Do it once and reuse.
   ```python
   clir = BM25CLIR()
   clir.build_index("both")  # Takes ~30 seconds
   
   # Then do multiple searches (fast)
   results1 = clir.search("query1", "en")
   results2 = clir.search("query2", "en")
   results3 = clir.search("query3", "bn")
   ```

2. **Language-specific indexes**: If you only need one language, build only that index.
   ```python
   clir.build_index("en")  # Faster than "both"
   ```

3. **Batch processing**: Load the system once for multiple queries.

4. **Score thresholding**: Filter low-scoring results for better quality.
   ```python
   results = clir.search(query, "en", top_k=50)
   good_results = [(a, s) for a, s in results if s > 10.0]
   ```

## Advanced Customization

### Custom Tokenization
You can subclass `BM25CLIR` and override tokenization methods:

```python
class CustomBM25CLIR(BM25CLIR):
    def _tokenize_english(self, text: str) -> List[str]:
        # Your custom English tokenizer
        # e.g., stemming, lemmatization, stopword removal
        from nltk.stem import PorterStemmer
        stemmer = PorterStemmer()
        
        tokens = super()._tokenize_english(text)
        return [stemmer.stem(t) for t in tokens]
    
    def _tokenize_bangla(self, text: str) -> List[str]:
        # Your custom Bangla tokenizer
        # e.g., using bnlp library
        return text.split()

clir = CustomBM25CLIR()
```

### Custom BM25 Parameters
The `BM25Okapi` class uses default parameters `k1=1.5` and `b=0.75`. You can modify these:

```python
from rank_bm25 import BM25Okapi

# After tokenization, create custom BM25
tokenized_docs = clir.tokenized_docs["en"]
custom_bm25 = BM25Okapi(tokenized_docs, k1=2.0, b=0.5)
clir.bm25_models["en"] = custom_bm25
```

## File Structure

```
CLIR/
├── BM25/
│   ├── bm25_clir.py              # Main BM25CLIR class
│   ├── bm25_usage_examples.py    # Usage examples
│   ├── bm25_demo.py              # Original simple demo
│   └── README.md                 # This file
├── dataset_enhanced/
│   ├── combined_dataset.db       # Combined English + Bangla (5,000 articles)
│   └── combined_dataset.py       # Script to create combined DB
├── english_dataset/
│   ├── english_articles.db       # 2,500 English articles
│   └── *.txt                     # Raw text files
└── bangla_dataset/
    ├── bangla_articles.db        # 2,500 Bangla articles
    └── *.txt                     # Raw text files
```

## Troubleshooting

### "Database not found" error
Make sure you're running from the correct directory or provide the full path:
```python
clir = BM25CLIR(db_path="d:/path/to/combined_dataset.db")
```

### No results returned
- Check if the index is built: `clir.build_index("both")`
- Try broader queries
- Check language matches query

### Slow performance
- Build index only once per session
- Use `top_k` to limit results
- Consider building single-language index if not needed both

## Next Steps

1. **Translation Integration**: Add translation API (Google Translate, LibreTranslate) for true cross-lingual search
2. **Better Tokenization**: Use NLTK for English, bnlp for Bangla
3. **Query Expansion**: Add synonyms and related terms
4. **Relevance Feedback**: Implement pseudo-relevance feedback
5. **Evaluation**: Add precision/recall metrics with ground truth

## License

This is an academic project for Data Mining coursework.
