import json
import os
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.dirname(__file__))
from schema import BIBLE_BOOKS_MASTER

# Create lookup dict from normalized name to BIBLE_BOOKS_MASTER tuple
# (book_id, osis_code, name_kr, name_kr_abbr, name_en, testament, category, total_chapters, total_verses)
canonical_by_clean_en = {b[4].replace(" ", ""): b for b in BIBLE_BOOKS_MASTER}

path = os.path.join(os.path.dirname(__file__), "sample_data", "bible_1961_krv.json")
with open(path, "r", encoding="utf-8") as f:
    data = json.load(f)

unmatched = []
matched = []
for b in data:
    raw_name = b["book"]
    if raw_name in canonical_by_clean_en:
        matched.append((raw_name, canonical_by_clean_en[raw_name]))
    else:
        unmatched.append(raw_name)

print(f"Matched: {len(matched)} / 66")
if unmatched:
    print(f"Unmatched: {unmatched}")
else:
    print("ALL 66 BOOKS MATCH PERFECTLY!")

# Now verify chapter counts and verse counts per book
print("\nVerifying chapters and verses per book:")
mismatch_count = 0
for raw_name, meta in sorted(matched, key=lambda x: x[1][0]):
    b_data = next(x for x in data if x["book"] == raw_name)
    json_chaps = len(b_data["chapters"])
    json_verses = sum(len(c["verses"]) for c in b_data["chapters"])

    expected_chaps = meta[7]
    expected_verses = meta[8]

    if json_chaps != expected_chaps or json_verses != expected_verses:
        print(f"NOTE: Book {meta[0]} {meta[2]} ({meta[1]}): JSON has {json_chaps} chs, {json_verses} vs. Schema has {expected_chaps} chs, {expected_verses} vs.")
        mismatch_count += 1

print(f"\nTotal differences in chapter/verse counts compared to schema defaults: {mismatch_count}")
