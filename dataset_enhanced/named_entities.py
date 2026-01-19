#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Extract Named Entities for all articles and store in database."""

import sys
import json
import sqlite3
import time
from pathlib import Path
from transformers import pipeline

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

SCRIPT_DIR = Path(__file__).parent
DB_PATH = SCRIPT_DIR / "combined_dataset.db"
BATCH_SIZE = 100  # Process and commit every 100 articles

print("=" * 80)
print("EXTRACTING NAMED ENTITIES FOR ALL ARTICLES")
print("=" * 80)

# Load NER models
print("\n1. Loading NER models...")
print("   - Loading English model (xlm-roberta-large-finetuned-conll03-english)...", flush=True)
english_ner = pipeline(
    "ner",
    model="xlm-roberta-large-finetuned-conll03-english",
    tokenizer="xlm-roberta-large-finetuned-conll03-english",
    aggregation_strategy="simple"
)
print("   ✓ English NER model loaded")

print("   - Loading Bangla model (sagorsarker/mbert-bengali-ner)...", flush=True)
bangla_ner = pipeline(
    "ner",
    model="sagorsarker/mbert-bengali-ner",
    aggregation_strategy="simple"
)
print("   ✓ Bangla NER model loaded")

# Connect to database
print("\n2. Connecting to database...", flush=True)
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Get total count
cursor.execute("SELECT COUNT(*) FROM articles")
total_count = cursor.fetchone()[0]
print(f"   ✓ Found {total_count} articles")

# Get articles without named entities
cursor.execute("SELECT COUNT(*) FROM articles WHERE named_entities IS NULL OR named_entities = ''")
pending_count = cursor.fetchone()[0]
print(f"   ✓ {pending_count} articles need named entity extraction")

if pending_count == 0:
    print("\n✓ All articles already have named entities!")
    conn.close()
    exit(0)

print(f"\n3. Extracting named entities...")
print(f"   Processing in batches of {BATCH_SIZE}")

# Fetch articles that need NER
cursor.execute("""
    SELECT id, title, body, language
    FROM articles
    WHERE named_entities IS NULL OR named_entities = ''
""")
articles = cursor.fetchall()

processed = 0
errors = 0
start_time = time.time()

# Entity label mapping for Bangla model
BANGLA_LABEL_MAP = {
    'LABEL_1': 'PER',  # Person (first part)
    'LABEL_2': 'PER',  # Person (continuation)
    'LABEL_3': 'ORG',  # Organization (first part)
    'LABEL_4': 'ORG',  # Organization (continuation)
    'LABEL_5': 'LOC',  # Location (first part)
    'LABEL_6': 'LOC',  # Location (continuation)
    'LABEL_0': 'O'     # Outside entity
}

for i, (doc_id, title, body, language) in enumerate(articles, 1):
    try:
        # Combine title and body for NER
        full_text = f"{title}\n\n{body}"

        # Choose appropriate model based on language
        if language == 'en':
            entities = english_ner(full_text[:5000])  # Limit to 5000 chars to avoid memory issues
        elif language == 'bn':
            entities = bangla_ner(full_text[:5000])
            # Map Bangla labels to standard labels
            for entity in entities:
                original_label = entity['entity_group']
                entity['entity_group'] = BANGLA_LABEL_MAP.get(original_label, 'O')
        else:
            # Unknown language, skip
            print(f"   ⚠ Unknown language '{language}' for article {doc_id}, skipping", flush=True)
            continue

        # Filter out 'O' (outside entity) labels
        entities = [e for e in entities if e['entity_group'] != 'O']

        # Group entities by type for better organization
        entities_by_type = {}
        for entity in entities:
            entity_type = entity['entity_group']
            if entity_type not in entities_by_type:
                entities_by_type[entity_type] = []

            # Store entity with its text and confidence score
            entities_by_type[entity_type].append({
                'text': entity['word'],
                'score': float(round(entity['score'], 3))  # Convert float32 to float
            })

        # Convert to JSON string
        entities_json = json.dumps(entities_by_type, ensure_ascii=False)

        # Update database
        cursor.execute(
            "UPDATE articles SET named_entities = ? WHERE id = ?",
            (entities_json, doc_id)
        )

        processed += 1

        # Show progress
        if i % 10 == 0 or i == len(articles):
            elapsed = time.time() - start_time
            rate = processed / elapsed if elapsed > 0 else 0
            remaining = (len(articles) - i) / rate if rate > 0 else 0
            print(f"   Progress: {i}/{len(articles)} ({i/len(articles)*100:.1f}%) - "
                  f"{rate:.1f} articles/sec - "
                  f"ETA: {remaining/60:.1f} min - "
                  f"Lang: {language}",
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
print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"Total articles processed: {processed}")
print(f"Errors: {errors}")
print(f"Total time: {total_time/60:.1f} minutes")
print(f"Average rate: {processed/total_time:.1f} articles/second")
print(f"Average time per article: {total_time/processed:.2f} seconds")
print("\n✓ All named entities extracted and stored!")
