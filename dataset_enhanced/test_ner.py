#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test Named Entity Recognition on sample English and Bangla articles."""

import sys
import sqlite3
from pathlib import Path
from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

SCRIPT_DIR = Path(__file__).parent
DB_PATH = SCRIPT_DIR / "combined_dataset.db"

print("=" * 80)
print("TESTING NAMED ENTITY RECOGNITION")
print("=" * 80)

# Load models
print("\n1. Loading NER models...")
print("   - Loading English model (xlm-roberta-large-finetuned-conll03-english)...", flush=True)
english_ner = pipeline(
    "ner",
    model="xlm-roberta-large-finetuned-conll03-english",
    tokenizer="xlm-roberta-large-finetuned-conll03-english",
    aggregation_strategy="simple"  # Groups subword tokens together
)
print("   ✓ English NER model loaded")

print("   - Loading Bangla/Multilingual model (sagorsarker/mbert-bengali-ner)...", flush=True)
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

# Get one English article
print("\n3. Fetching sample articles...", flush=True)
cursor.execute("""
    SELECT id, title, body, language, url
    FROM articles
    WHERE language = 'en'
    LIMIT 1
""")
english_article = cursor.fetchone()

# Get one Bangla article
cursor.execute("""
    SELECT id, title, body, language, url
    FROM articles
    WHERE language = 'bn'
    LIMIT 1
""")
bangla_article = cursor.fetchone()

conn.close()

if not english_article:
    print("✗ No English articles found in database!")
    exit(1)

if not bangla_article:
    print("✗ No Bangla articles found in database!")
    exit(1)

print("   ✓ Sample articles retrieved")

# Process English article
print("\n" + "=" * 80)
print("ENGLISH ARTICLE")
print("=" * 80)
en_id, en_title, en_body, en_lang, en_url = english_article
print(f"\nID: {en_id}")
print(f"Language: {en_lang}")
print(f"URL: {en_url}")
print(f"\nTitle: {en_title}")
print(f"\nBody (first 500 chars):\n{en_body[:500]}...")

# Combine title and body for NER
en_full_text = f"{en_title}\n\n{en_body}"

print("\n" + "-" * 80)
print("EXTRACTING NAMED ENTITIES (English)...")
print("-" * 80)

# Run NER on English text
en_entities = english_ner(en_full_text[:1000])  # Limit to 1000 chars for testing

print(f"\nFound {len(en_entities)} entities:\n")
for entity in en_entities:
    print(f"  • {entity['word']:30} | {entity['entity_group']:8} | Score: {entity['score']:.3f}")

# Group entities by type
en_entity_groups = {}
for entity in en_entities:
    entity_type = entity['entity_group']
    if entity_type not in en_entity_groups:
        en_entity_groups[entity_type] = []
    en_entity_groups[entity_type].append(entity['word'])

print("\n" + "-" * 80)
print("ENTITIES BY TYPE (English):")
print("-" * 80)
for entity_type, words in sorted(en_entity_groups.items()):
    print(f"\n{entity_type}:")
    for word in words:
        print(f"  - {word}")

# Process Bangla article
print("\n" + "=" * 80)
print("BANGLA ARTICLE")
print("=" * 80)
bn_id, bn_title, bn_body, bn_lang, bn_url = bangla_article
print(f"\nID: {bn_id}")
print(f"Language: {bn_lang}")
print(f"URL: {bn_url}")
print(f"\nTitle: {bn_title}")
print(f"\nBody (first 500 chars):\n{bn_body[:500]}...")

# Combine title and body for NER
bn_full_text = f"{bn_title}\n\n{bn_body}"

print("\n" + "-" * 80)
print("EXTRACTING NAMED ENTITIES (Bangla)...")
print("-" * 80)

# Run NER on Bangla text
bn_entities = bangla_ner(bn_full_text[:1000])  # Limit to 1000 chars for testing

print(f"\nFound {len(bn_entities)} entities:\n")
for entity in bn_entities:
    print(f"  • {entity['word']:30} | {entity['entity_group']:8} | Score: {entity['score']:.3f}")

# Group entities by type
bn_entity_groups = {}
for entity in bn_entities:
    entity_type = entity['entity_group']
    if entity_type not in bn_entity_groups:
        bn_entity_groups[entity_type] = []
    bn_entity_groups[entity_type].append(entity['word'])

print("\n" + "-" * 80)
print("ENTITIES BY TYPE (Bangla):")
print("-" * 80)
for entity_type, words in sorted(bn_entity_groups.items()):
    print(f"\n{entity_type}:")
    for word in words:
        print(f"  - {word}")

# Summary
print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"\nEnglish Article:")
print(f"  - Total entities: {len(en_entities)}")
print(f"  - Entity types: {', '.join(sorted(en_entity_groups.keys()))}")

print(f"\nBangla Article:")
print(f"  - Total entities: {len(bn_entities)}")
print(f"  - Entity types: {', '.join(sorted(bn_entity_groups.keys()))}")

print("\n✓ NER testing complete!")
