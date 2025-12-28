#!/usr/bin/env python3
"""Combine Bangla and English article databases into a single database.

Reads from:
- ../english_dataset/english_articles.db
- ../bangla_dataset/bangla_articles.db

Writes to:
- combined_dataset.db (in the current directory)
"""
import sqlite3
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
ENGLISH_DB = SCRIPT_DIR.parent / "english_dataset" / "english_articles.db"
BANGLA_DB = SCRIPT_DIR.parent / "bangla_dataset" / "bangla_articles.db"
COMBINED_DB = SCRIPT_DIR / "combined_dataset.db"


def init_combined_db(conn: sqlite3.Connection) -> None:
    """Initialize the combined database schema."""
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT,
            title TEXT,
            body TEXT,
            url TEXT UNIQUE,
            date TEXT,
            language TEXT,
            tokens INTEGER,
            word_embeddings TEXT,
            named_entities TEXT
        );
        """
    )
    conn.commit()


def copy_articles(source_db_path: Path, dest_conn: sqlite3.Connection, dataset_name: str) -> tuple[int, int]:
    """Copy articles from source database to destination database.

    Returns:
        (inserted_count, skipped_count): Number of articles inserted and skipped
    """
    if not source_db_path.exists():
        print(f"Warning: {source_db_path} not found. Skipping {dataset_name}.", file=sys.stderr)
        return 0, 0

    source_conn = sqlite3.connect(source_db_path)
    source_cursor = source_conn.cursor()

    # Get all articles from source
    source_cursor.execute(
        """
        SELECT source, title, body, url, date, language, tokens, word_embeddings, named_entities
        FROM articles
        """
    )
    articles = source_cursor.fetchall()
    source_conn.close()

    if not articles:
        print(f"No articles found in {dataset_name}")
        return 0, 0

    print(f"Found {len(articles)} articles in {dataset_name}")

    inserted = 0
    skipped = 0

    for article in articles:
        try:
            dest_conn.execute(
                """
                INSERT INTO articles (source, title, body, url, date, language, tokens, word_embeddings, named_entities)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                article,
            )
            inserted += 1
        except sqlite3.IntegrityError:
            # URL already exists (duplicate)
            skipped += 1
        except Exception as e:
            print(f"Error inserting article from {dataset_name}: {e}", file=sys.stderr)
            skipped += 1

    dest_conn.commit()
    return inserted, skipped


def main() -> int:
    """Main execution function."""
    print(f"Combining databases into {COMBINED_DB}")
    print("=" * 60)

    # Create or connect to combined database
    combined_conn = sqlite3.connect(COMBINED_DB)
    init_combined_db(combined_conn)

    total_inserted = 0
    total_skipped = 0

    # Copy English articles
    print("\n1. Processing English articles...")
    eng_inserted, eng_skipped = copy_articles(ENGLISH_DB, combined_conn, "English dataset")
    print(f"   Inserted: {eng_inserted}")
    print(f"   Skipped: {eng_skipped}")
    total_inserted += eng_inserted
    total_skipped += eng_skipped

    # Copy Bangla articles
    print("\n2. Processing Bangla articles...")
    bn_inserted, bn_skipped = copy_articles(BANGLA_DB, combined_conn, "Bangla dataset")
    print(f"   Inserted: {bn_inserted}")
    print(f"   Skipped: {bn_skipped}")
    total_inserted += bn_inserted
    total_skipped += bn_skipped

    # Get statistics from combined database
    cursor = combined_conn.cursor()

    # Total count
    cursor.execute("SELECT COUNT(*) FROM articles")
    total_count = cursor.fetchone()[0]

    # Count by language
    cursor.execute("SELECT language, COUNT(*) FROM articles GROUP BY language")
    lang_stats = cursor.fetchall()

    # Count by source
    cursor.execute("SELECT source, COUNT(*) FROM articles GROUP BY source ORDER BY COUNT(*) DESC")
    source_stats = cursor.fetchall()

    # Count with dates
    cursor.execute("SELECT COUNT(*) FROM articles WHERE date IS NOT NULL AND date != ''")
    with_dates = cursor.fetchone()[0]

    # Count without dates
    cursor.execute("SELECT COUNT(*) FROM articles WHERE date IS NULL OR date = ''")
    without_dates = cursor.fetchone()[0]

    combined_conn.close()

    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total articles in combined database: {total_count}")
    print(f"Total inserted: {total_inserted}")
    print(f"Total skipped (duplicates/errors): {total_skipped}")

    print(f"\nBy Language:")
    for lang, count in lang_stats:
        lang_name = "Bangla" if lang == "bn" else "English" if lang == "en" else lang
        print(f"  {lang_name} ({lang}): {count}")

    print(f"\nBy Source:")
    for source, count in source_stats:
        print(f"  {source}: {count}")

    print(f"\nDate Coverage:")
    print(f"  With dates: {with_dates} ({with_dates/total_count*100:.1f}%)")
    print(f"  Without dates: {without_dates} ({without_dates/total_count*100:.1f}%)")

    print(f"\nCombined database created at: {COMBINED_DB}")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
