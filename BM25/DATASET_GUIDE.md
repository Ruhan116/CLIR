# Dataset Organization Summary

## 📊 Overview

Your dataset is organized in **3 layers**:

```
┌─────────────────────────────────────────────────────────────┐
│                    Layer 1: Raw Text Files                  │
│  bangla_dataset/*.txt  +  english_dataset/*.txt             │
│  Format: Plain text with separator markers                  │
│  Usage: Legacy/backup, not recommended for coding           │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│               Layer 2: Individual SQLite DBs                │
│  bangla_articles.db (2,500)  + english_articles.db (2,500)  │
│  Format: Structured SQL database                            │
│  Usage: Language-specific operations                        │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│            Layer 3: Combined Database (BEST!)               │
│            dataset_enhanced/combined_dataset.db             │
│            5,000 articles (EN: 2,500 + BN: 2,500)           │
│  Format: Unified SQL database with language field           │
│  Usage: BM25, CLIR, Cross-lingual search (RECOMMENDED)      │
└─────────────────────────────────────────────────────────────┘
```

## 🗂️ Database Schema

```sql
articles (
    id         INTEGER PRIMARY KEY,
    source     TEXT,        -- "The Daily Star", "Prothom Alo", etc.
    title      TEXT,        -- Article headline
    body       TEXT,        -- Full article content
    url        TEXT UNIQUE, -- Source URL
    date       TEXT,        -- ISO format (2025-12-29T00:00:00+06:00)
    language   TEXT,        -- "en" or "bn"
    tokens     INTEGER,     -- Reserved for future
    word_embeddings TEXT,   -- Reserved for future
    named_entities  TEXT    -- Reserved for future
)
```

## 📈 Dataset Statistics

| Metric              | Count |
|---------------------|-------|
| Total Articles      | 5,000 |
| English Articles    | 2,500 |
| Bangla Articles     | 2,500 |
| Total Sources       | 10    |

### Articles by Source

| Source          | Language | Count |
|-----------------|----------|-------|
| Prothom Alo     | Bangla   | 1,356 |
| New Age         | English  | 622   |
| Dhaka Tribune   | English  | 500   |
| TBS News        | English  | 500   |
| The Daily Star  | English  | 500   |
| Dhaka Post      | Bangla   | 500   |
| Jugantor        | Bangla   | 496   |
| BSS News        | English  | 378   |
| Bangla News 24  | Bangla   | 139   |
| Kalerkantho     | Bangla   | 9     |

## 💻 How to Use in Code

### ⭐ Method 1: Using BM25CLIR Class (EASIEST)

```python
from BM25.bm25_clir import BM25CLIR

# Initialize - automatically loads combined_dataset.db
clir = BM25CLIR()

# Build search index
clir.build_index("both")

# Search English articles
results = clir.search("cricket match", language="en", top_k=5)
for article, score in results:
    print(f"{article.title} (score: {score:.2f})")

# Search Bangla articles
results = clir.search("নির্বাচন", language="bn", top_k=5)
for article, score in results:
    print(article.title)

# Access raw articles
all_english = clir.articles["en"]
all_bangla = clir.articles["bn"]
```

### Method 2: Direct SQLite Access

```python
import sqlite3

conn = sqlite3.connect("dataset_enhanced/combined_dataset.db")
cursor = conn.cursor()

# Get all English articles
cursor.execute("""
    SELECT title, body FROM articles 
    WHERE language = 'en'
""")
articles = cursor.fetchall()

# Get articles from specific source
cursor.execute("""
    SELECT title, body FROM articles 
    WHERE source = ? AND language = ?
""", ("The Daily Star", "en"))
articles = cursor.fetchall()

conn.close()
```

### Method 3: Pandas DataFrame

```python
import sqlite3
import pandas as pd

conn = sqlite3.connect("dataset_enhanced/combined_dataset.db")

# Load all articles into DataFrame
df = pd.read_sql_query("SELECT * FROM articles", conn)

# Filter by language
df_english = df[df['language'] == 'en']
df_bangla = df[df['language'] == 'bn']

# Filter by source
df_daily_star = df[df['source'] == 'The Daily Star']

conn.close()
```

## 🚀 Quick Start Commands

```bash
# Navigate to BM25 directory
cd BM25

# Run quick start demo
python quick_start.py

# Run all usage examples
python bm25_usage_examples.py

# Interactive search mode
python bm25_usage_examples.py interactive

# Run main BM25 demo
python bm25_clir.py
```

## 📝 Common Tasks

### Task 1: Load All English Articles

```python
from BM25.bm25_clir import BM25CLIR

clir = BM25CLIR()
english_articles = clir.articles["en"]

for article in english_articles[:10]:
    print(article.title)
```

### Task 2: Search and Get Top Results

```python
from BM25.bm25_clir import BM25CLIR

clir = BM25CLIR()
clir.build_index("en")

results = clir.search("economy", language="en", top_k=10)
for article, score in results:
    print(f"{score:.2f}: {article.title}")
```

### Task 3: Filter Articles by Date

```python
import sqlite3

conn = sqlite3.connect("dataset_enhanced/combined_dataset.db")
cursor = conn.cursor()

cursor.execute("""
    SELECT title, date FROM articles 
    WHERE date >= '2025-01-01' AND language = 'en'
    ORDER BY date DESC
""")
recent_articles = cursor.fetchall()

conn.close()
```

### Task 4: Get Article Count by Source

```python
import sqlite3

conn = sqlite3.connect("dataset_enhanced/combined_dataset.db")
cursor = conn.cursor()

cursor.execute("""
    SELECT source, COUNT(*) as count 
    FROM articles 
    GROUP BY source 
    ORDER BY count DESC
""")

for source, count in cursor.fetchall():
    print(f"{source}: {count} articles")

conn.close()
```

### Task 5: Extract Just Titles and Bodies

```python
from BM25.bm25_clir import BM25CLIR

clir = BM25CLIR()

# English corpus for training
en_corpus = [(article.title, article.body) for article in clir.articles["en"]]

# Bangla corpus
bn_corpus = [(article.title, article.body) for article in clir.articles["bn"]]

print(f"English corpus: {len(en_corpus)} articles")
print(f"Bangla corpus: {len(bn_corpus)} articles")
```

## 🎯 BM25 Implementation Features

✅ **Implemented:**
- [x] BM25Okapi ranking algorithm
- [x] English and Bangla tokenization
- [x] Mono-lingual search (EN→EN, BN→BN)
- [x] Multi-lingual result merging
- [x] SQLite database integration
- [x] Article retrieval and display
- [x] Score-based ranking
- [x] Statistics and analytics

🔜 **Future Enhancements:**
- [ ] Cross-lingual search with translation (EN↔BN)
- [ ] Advanced tokenization (stemming, lemmatization)
- [ ] Query expansion
- [ ] Relevance feedback
- [ ] Evaluation metrics (Precision, Recall, MAP)
- [ ] Word embeddings integration
- [ ] Named entity recognition

## 📚 File Reference

```
BM25/
├── bm25_clir.py              # Main class (USE THIS!)
├── bm25_usage_examples.py    # Comprehensive examples
├── quick_start.py            # Minimal demo
├── bm25_demo.py              # Original simple demo
├── README.md                 # Full documentation
└── DATASET_GUIDE.md          # This file
```

## 🔧 Dependencies

```bash
pip install rank-bm25 numpy
```

Optional for advanced features:
```bash
pip install pandas nltk bnlp
```

## 💡 Best Practices

1. **Use combined_dataset.db** - It's the most organized and easy to work with
2. **Build index once** - BM25 index building takes time, do it once per session
3. **Filter by language** - Specify "en" or "bn" for better results
4. **Set reasonable top_k** - Don't retrieve more results than needed
5. **Handle empty results** - Always check if results list is empty

## 🆘 Troubleshooting

**Q: Where is the database?**
A: `dataset_enhanced/combined_dataset.db` (relative to project root)

**Q: How do I know if my code is working?**
A: Run `python BM25/quick_start.py` to test

**Q: Can I use just English or just Bangla?**
A: Yes! Use `clir.build_index("en")` or `clir.build_index("bn")`

**Q: How do I see what's in the database?**
A: Use `clir.get_statistics()` or a SQLite viewer

**Q: Results seem irrelevant?**
A: Try broader queries, check tokenization, or adjust BM25 parameters

## 📞 Need Help?

- See [README.md](README.md) for detailed API documentation
- Check [bm25_usage_examples.py](bm25_usage_examples.py) for code examples
- Run `python bm25_usage_examples.py interactive` for hands-on testing
