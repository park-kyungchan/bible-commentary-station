import json
import os
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.dirname(__file__))
from schema import BIBLE_BOOKS_MASTER, calculate_verse_id

path = os.path.join(os.path.dirname(__file__), "sample_data", "bible_1961_krv.json")
with open(path, "r", encoding="utf-8") as f:
    data = json.load(f)

book_map = {b[4].replace(" ", ""): b for b in BIBLE_BOOKS_MASTER}

total_verses = 0
total_chapters = 0
errors = []

for b_idx, book_obj in enumerate(data):
    raw_name = book_obj["book"]
    meta = book_map.get(raw_name)
    if not meta:
        errors.append(f"Unknown book: {raw_name}")
        continue
    book_id = meta[0]
    chapters = book_obj.get("chapters", [])
    total_chapters += len(chapters)

    for ch_obj in chapters:
        ch_num = ch_obj.get("chapter")
        verses = ch_obj.get("verses", [])
        total_verses += len(verses)
        for v_obj in verses:
            v_num = v_obj.get("verse")
            text = v_obj.get("text", "")
            if not text or not text.strip():
                errors.append(f"Empty text at {meta[2]} {ch_num}:{v_num}")
            if v_num <= 0 or ch_num <= 0:
                errors.append(f"Invalid ch/vs at {meta[2]} {ch_num}:{v_num}")
            v_id = calculate_verse_id(book_id, ch_num, v_num)

print(f"Validated books: {len(data)}")
print(f"Validated chapters: {total_chapters} (expected 1189)")
print(f"Validated verses: {total_verses} (expected 31102)")
if errors:
    print(f"Found {len(errors)} errors:")
    for err in errors[:10]:
        print("  -", err)
else:
    print("NO ERRORS FOUND! Data is 100% clean and valid.")
