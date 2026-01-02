import sqlite3
from pathlib import Path

db_path = Path(__file__).parent.parent / "dataset_enhanced" / "combined_dataset.db"
conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

# Get all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print('Tables:', tables)

for table in tables:
    t = table[0]
    cursor.execute(f'PRAGMA table_info({t})')
    cols = cursor.fetchall()
    print(f'\n{t} columns:')
    for col in cols:
        print(f'  - {col[1]} ({col[2]})')
    
    # Get sample row
    cursor.execute(f'SELECT * FROM {t} LIMIT 1')
    sample = cursor.fetchone()
    print(f'  Sample row: {sample}')

conn.close()
