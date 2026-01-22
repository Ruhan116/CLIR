import sqlite3
import os

db_paths = [
    r"f:\CLIR\CLIR\english_dataset\english_articles.db",
    r"f:\CLIR\CLIR\bangla_dataset\bangla_articles.db",
    r"f:\CLIR\CLIR\BM25\combined_dataset.db",
    r"f:\CLIR\CLIR\dataset_enhanced\combined_dataset.db"
]

for db_path in db_paths:
    print(f"Checking {db_path}...")
    if not os.path.exists(db_path):
        print("  File not found.")
        continue
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"  Tables: {tables}")
        
        for table in tables:
            table_name = table[0]
            print(f"  Schema for {table_name}:")
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            for col in columns:
                print(f"    {col}")
            
            # Count rows
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"    Row count: {count}")
            
            # Sample row
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 1")
            sample = cursor.fetchone()
            print(f"    Sample: {sample}")

        conn.close()
    except Exception as e:
        print(f"  Error: {e}")
    print("-" * 20)
