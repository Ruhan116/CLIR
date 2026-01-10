#!/usr/bin/env python3
"""Generate LaBSE embeddings for all articles and store in database."""

import json
import sqlite3
import time
from pathlib import Path
from sentence_transformers import SentenceTransformer

SCRIPT_DIR = Path(__file__).parent
DB_PATH = SCRIPT_DIR / "combined_dataset.db"
BATCH_SIZE = 100  # Process and commit every 100 articles

print("=" * 60)
print("GENERATING EMBEDDINGS FOR ALL ARTICLES")
print("=" * 60)

# Load model once
print("\n1. Loading LaBSE model...", flush=True)
start_time = time.time()
model = SentenceTransformer('sentence-transformers/LaBSE')
load_time = time.time() - start_time
print(f"✓ Model loaded in {load_time:.1f}s! Dimension: {model.get_sentence_embedding_dimension()}", flush=True)

# Connect to database
print("\n2. Connecting to database...", flush=True)
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Get total count
cursor.execute("SELECT COUNT(*) FROM articles")
total_count = cursor.fetchone()[0]
print(f"✓ Found {total_count} articles", flush=True)

# Get articles without embeddings
cursor.execute("SELECT COUNT(*) FROM articles WHERE word_embeddings IS NULL OR word_embeddings = ''")
pending_count = cursor.fetchone()[0]
print(f"✓ {pending_count} articles need embeddings", flush=True)

if pending_count == 0:
    print("\n✓ All articles already have embeddings!")
    conn.close()
    exit(0)

print(f"\n3. Generating embeddings...", flush=True)
print(f"   Processing in batches of {BATCH_SIZE}", flush=True)

# Fetch articles that need embeddings
cursor.execute("""
    SELECT id, title, body, language
    FROM articles
    WHERE word_embeddings IS NULL OR word_embeddings = ''
""")
articles = cursor.fetchall()

processed = 0
errors = 0
start_time = time.time()

for i, (doc_id, title, body, language) in enumerate(articles, 1):
    try:
        # Generate embedding
        full_text = f"{title}\n\n{body}"
        embedding = model.encode(full_text)

        # Convert to JSON string
        embedding_json = json.dumps(embedding.tolist())

        # Update database
        cursor.execute(
            "UPDATE articles SET word_embeddings = ? WHERE id = ?",
            (embedding_json, doc_id)
        )

        processed += 1

        # Show progress
        if i % 10 == 0 or i == len(articles):
            elapsed = time.time() - start_time
            rate = processed / elapsed if elapsed > 0 else 0
            remaining = (len(articles) - i) / rate if rate > 0 else 0
            print(f"   Progress: {i}/{len(articles)} ({i/len(articles)*100:.1f}%) - "
                  f"{rate:.1f} articles/sec - "
                  f"ETA: {remaining/60:.1f} min",
                  flush=True)

        # Commit in batches
        if i % BATCH_SIZE == 0:
            conn.commit()
            print(f"   ✓ Committed batch (up to article {i})", flush=True)

    except Exception as e:
        errors += 1
        print(f"   ✗ Error processing article {doc_id}: {e}", flush=True)

# Final commit
conn.commit()
conn.close()

total_time = time.time() - start_time

# Show summary
print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print(f"Total articles processed: {processed}")
print(f"Errors: {errors}")
print(f"Total time: {total_time/60:.1f} minutes")
print(f"Average rate: {processed/total_time:.1f} articles/second")
print(f"Average time per article: {total_time/processed:.2f} seconds")
print("\n✓ All embeddings generated and stored!")
