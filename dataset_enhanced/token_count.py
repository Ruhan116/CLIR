#!/usr/bin/env python3
"""Add token counts to all articles in combined_dataset.db.

Uses NLTK for English and BanglaBERT tokenizer for Bangla.
"""

import sqlite3
import sys
from pathlib import Path

import nltk
from transformers import AutoTokenizer

SCRIPT_DIR = Path(__file__).parent
DB_PATH = SCRIPT_DIR / "combined_dataset.db"


def load_tokenizers():
    """Load NLTK and BanglaBERT tokenizers."""
    print("Loading tokenizers...")

    # Download NLTK punkt tokenizer if needed
    try:
        nltk.data.find('tokenizers/punkt_tab')
    except LookupError:
        print("Downloading NLTK punkt_tab tokenizer...")
        nltk.download('punkt_tab', quiet=True)

    # Load BanglaBERT tokenizer
    print("Loading BanglaBERT tokenizer...")
    bangla_tokenizer = AutoTokenizer.from_pretrained("csebuetnlp/banglabert")

    print("✓ NLTK tokenizer ready (English)")
    print("✓ BanglaBERT tokenizer ready (Bangla)")

    return bangla_tokenizer


def tokenize_bangla(text: str, tokenizer) -> int:
    """
    Tokenize Bangla text using BanglaBERT tokenizer.
    Returns word-level token count (not subword tokens).
    """
    if not text or not text.strip():
        return 0

    # Use encode to get token IDs, which represents word pieces
    # For word count, we tokenize and count unique word boundaries
    tokens = tokenizer.tokenize(text)

    # Count word-level tokens by counting tokens that don't start with '##'
    # (## indicates continuation of previous word in WordPiece tokenization)
    word_count = sum(1 for token in tokens if not token.startswith('##'))
    return word_count


def tokenize_english(text: str) -> int:
    """
    Tokenize English text using NLTK.
    """
    if not text or not text.strip():
        return 0

    tokens = nltk.word_tokenize(text)
    return len(tokens)


def count_tokens(text: str, language: str, bangla_tokenizer) -> int:
    """
    Count tokens in text.

    Args:
        text: The text to tokenize (title + body)
        language: 'en' or 'bn'
        bangla_tokenizer: BanglaBERT tokenizer instance

    Returns:
        Token count
    """
    if not text or not text.strip():
        return 0

    try:
        if language == "bn":
            # Use BanglaBERT for Bangla
            return tokenize_bangla(text.strip(), bangla_tokenizer)
        else:
            # Use NLTK for English
            return tokenize_english(text.strip())
    except Exception as e:
        print(f"  Warning: Error tokenizing text: {e}")
        return 0


def process_database():
    """Process all articles in the database and add token counts."""
    if not DB_PATH.exists():
        print(f"Error: Database not found at {DB_PATH}")
        print("Run combined_dataset.py first to create the database.")
        sys.exit(1)

    # Load tokenizers
    bangla_tokenizer = load_tokenizers()

    # Connect to database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Clear existing token counts
    print("\n2. Clearing existing token counts...")
    cursor.execute("UPDATE articles SET tokens = NULL")
    conn.commit()
    print("✓ Token counts cleared")

    # Get total count
    cursor.execute("SELECT COUNT(*) FROM articles")
    total = cursor.fetchone()[0]

    print(f"\n3. Processing all {total} articles...")
    print("=" * 60)

    # Get articles that need processing
    cursor.execute("""
        SELECT id, title, body, language
        FROM articles
        WHERE tokens IS NULL OR tokens = 0
        ORDER BY id
    """)

    processed = 0
    for row in cursor.fetchall():
        doc_id, title, body, language = row

        # Combine title and body
        full_text = f"{title or ''}\n\n{body or ''}"

        # Count tokens
        token_count = count_tokens(full_text, language, bangla_tokenizer)

        # Update database
        conn.execute("UPDATE articles SET tokens = ? WHERE id = ?", (token_count, doc_id))

        processed += 1
        if processed % 10 == 0:
            conn.commit()
            print(f"  Processed {processed}/{total} articles... (ID: {doc_id}, Tokens: {token_count})")

    conn.commit()

    # Show statistics
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    cursor.execute("SELECT COUNT(*), MIN(tokens), MAX(tokens), AVG(tokens) FROM articles WHERE tokens > 0")
    count, min_tok, max_tok, avg_tok = cursor.fetchone()

    cursor.execute("SELECT COUNT(*), AVG(tokens) FROM articles WHERE language = 'en' AND tokens > 0")
    en_count, en_avg = cursor.fetchone()

    cursor.execute("SELECT COUNT(*), AVG(tokens) FROM articles WHERE language = 'bn' AND tokens > 0")
    bn_count, bn_avg = cursor.fetchone()

    print(f"Total articles processed: {processed}")
    print(f"\nToken Statistics:")
    print(f"  Articles with tokens: {count}")
    print(f"  Min tokens: {min_tok}")
    print(f"  Max tokens: {max_tok}")
    print(f"  Avg tokens: {avg_tok:.1f}")

    print(f"\nBy Language:")
    print(f"  English: {en_count} articles, avg {en_avg:.1f} tokens")
    print(f"  Bangla:  {bn_count} articles, avg {bn_avg:.1f} tokens")

    conn.close()
    print("\n✓ Token counts added to database!")


if __name__ == "__main__":
    process_database()
