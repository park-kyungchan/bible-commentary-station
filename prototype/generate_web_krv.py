import json
import os
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts", "data_pipeline"))
from schema import BIBLE_BOOKS_MASTER

krv_path = os.path.join(os.path.dirname(__file__), "..", "scripts", "data_pipeline", "sample_data", "bible_1961_krv.json")
out_path = os.path.join(os.path.dirname(__file__), "bible_krv.json")

print(f"Reading KRV from {krv_path}...")
with open(krv_path, "r", encoding="utf-8") as f:
    raw = json.load(f)

book_map = {b[4].replace(" ", ""): b for b in BIBLE_BOOKS_MASTER}

compact = {}
total_verses = 0
total_chapters = 0

for b in raw:
    raw_name = b["book"]
    meta = book_map[raw_name]
    osis = meta[1]
    compact[osis] = {}

    for ch in b["chapters"]:
        ch_num = str(ch["chapter"])
        verses = [v["text"].strip() for v in ch["verses"]]
        compact[osis][ch_num] = verses
        total_verses += len(verses)
        total_chapters += 1

print(f"Total Books: {len(compact)}")
print(f"Total Chapters: {total_chapters}")
print(f"Total Verses: {total_verses}")

print(f"Writing compact JSON to {out_path}...")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(compact, f, ensure_ascii=False, separators=(',', ':'))

size = os.path.getsize(out_path)
print(f"Done! File size: {size:,} bytes ({size / 1024 / 1024:.2f} MB)")
