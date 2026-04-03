"""
Import ESPN 300 recruit CSVs into Supabase recruit_ratings table.
Usage: python data/recruits/import_recruits.py
"""
import csv
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from dotenv import load_dotenv
load_dotenv()

from supabase import create_client

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

RECRUIT_DIR = os.path.dirname(__file__)

def import_class_year(year: int):
    """Import a single class year CSV."""
    filepath = os.path.join(RECRUIT_DIR, f"espn300_{year}.csv")
    if not os.path.exists(filepath):
        print(f"  ⚠️  No file for {year}, skipping")
        return 0

    rows = []
    seen = set()
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = (row["name"].strip(), row["position"].strip())
            if key in seen:
                print(f"    ⚠️  Duplicate in {year}: {key[0]} ({key[1]}), keeping first")
                continue
            seen.add(key)
            rows.append({
                "recruit_class": year,
                "national_rank": int(row["rank"]),
                "player_name": row["name"].strip(),
                "position": row["position"].strip(),
                "stars": int(row["stars"]),
                "espn_grade": float(row["grade"]),
                "school_committed": row["school"].strip(),
                "source": "ESPN 300"
            })

    if not rows:
        print(f"  ⚠️  Empty file for {year}")
        return 0

    # Upsert in batches of 100
    batch_size = 100
    total = 0
    for i in range(0, len(rows), batch_size):
        batch = rows[i:i+batch_size]
        result = supabase.table("recruit_ratings").upsert(
            batch,
            on_conflict="recruit_class,player_name,position"
        ).execute()
        total += len(batch)

    print(f"  ✅ {year}: {total} recruits imported")
    return total

def main():
    print("🏈 ESPN 300 Recruit Import")
    print("=" * 40)

    grand_total = 0
    for year in range(2019, 2027):  # 2019-2026 (no 2018 yet)
        grand_total += import_class_year(year)

    print("=" * 40)
    print(f"🎯 Total: {grand_total} recruits across {8} class years")

    # Quick verification
    result = supabase.table("recruit_ratings").select("recruit_class", count="exact").execute()
    print(f"📊 Database count: {result.count} rows")

if __name__ == "__main__":
    main()
