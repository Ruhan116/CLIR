# Semantic Matching (LaBSE)

Semantic search over the combined CLIR dataset using precomputed LaBSE embeddings stored in `combined_dataset.db`.

## Contents
- `semantic_search.py` — core semantic search API (loads embeddings from SQLite, encodes queries, cosine ranking)
- `quick_start.py` — minimal example runner
- `test_semantic_search.py` — smoke test (skips gracefully if DB missing)
- `combined_dataset.db` — copy of the dataset for convenience (LFS-backed; use a single source of truth if you prefer)

## Usage
```bash
python semantic_matching/quick_start.py
python semantic_matching/semantic_search.py "coronavirus vaccine" --top_k 5 --language en
```

## Notes
- Embeddings: stored in `articles.word_embeddings` as JSON vectors (LaBSE, float32).
- Cosine similarity: by default embeddings and queries are normalized; scores are in [0,1].
- Cross-lingual: LaBSE is multilingual; no translation step is needed for semantic search.
- If you want to avoid duplicate DB copies, pass `--db` to point at `dataset_enhanced/combined_dataset.db` or `BM25/combined_dataset.db`.
- Large files are managed via Git LFS; keep `.gitattributes` consistent.
