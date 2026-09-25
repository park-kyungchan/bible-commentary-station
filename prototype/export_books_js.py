import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts", "data_pipeline"))
from schema import BIBLE_BOOKS_MASTER

js_lines = []
js_lines.append("  // 성경 66권 전체 메타데이터 (OSIS코드, 한글명, 약어, 영문명, 구약/신약, 분류, 전체 장수, 전체 절수, 장 배열)")
js_lines.append("  books: [")
for b in BIBLE_BOOKS_MASTER:
    osis = b[1]
    name_kr = b[2]
    abbr = b[3]
    name_en = b[4]
    test = b[5]
    cat = b[6]
    ch_count = b[7]
    vs_count = b[8]
    js_lines.append(f'    {{ id: "{osis}", name: "{name_kr}", abbr: "{abbr}", name_en: "{name_en}", test: "{test}", category: "{cat}", total_ch: {ch_count}, total_vs: {vs_count}, chapters: Array.from({{ length: {ch_count} }}, (_, i) => i + 1) }},')
js_lines.append("  ],")

output = "\n".join(js_lines)

# Let's read bible_data.js and replace books: [...]
bible_data_path = os.path.join(os.path.dirname(__file__), "bible_data.js")
with open(bible_data_path, "r", encoding="utf-8") as f:
    content = f.read()

# Locate books: [ ... ]
import re
pattern = r"  // 성경 66권 메타데이터\s+books:\s*\[[\s\S]*?\],\n"
match = re.search(pattern, content)
if not match:
    # Try alternate pattern
    pattern = r"  books:\s*\[[\s\S]*?\],\n"
    match = re.search(pattern, content)

if match:
    new_content = content[:match.start()] + output + "\n" + content[match.end():]
    with open(bible_data_path, "w", encoding="utf-8") as f:
        f.write(new_content)
    print("Successfully updated prototype/bible_data.js with all 66 books!")
else:
    print("Could not match books array in bible_data.js")
