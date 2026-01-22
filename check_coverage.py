import csv
import sqlite3
import os

csv_path = r'f:\CLIR\CLIR\labeled_queries.csv'
db_path = r'f:\CLIR\CLIR\BM25\combined_dataset.db'

# Load URLs from CSV
urls = []
with open(csv_path, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row['doc_url']:
            urls.append(row['doc_url'].strip())

print(f"Total URLs in CSV: {len(urls)}")

# Check coverage in DB
found_count = 0
missing_urls = []

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    for url in urls:
        cursor.execute("SELECT 1 FROM articles WHERE url = ?", (url,))
        if cursor.fetchone():
            found_count += 1
        else:
            missing_urls.append(url)
            
    conn.close()
    
print(f"Found in DB: {found_count}")
print(f"Missing: {len(missing_urls)}")
if missing_urls:
    print("First 5 missing URLs:")
    for u in missing_urls[:5]:
        print(u)
else:
    print("All URLs found!")
