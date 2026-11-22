"""
Unified Scripture Reference Normalizer & Structured Data Parsers.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .canon import BIBLE_BOOKS, calculate_verse_id, resolve_book


class ScriptureRefNormalizer:
    """Normalizes Korean/English/OSIS scripture citations into canonical verse coordinates."""

    ALIASES: Dict[str, int] = {
        "창세": 1, "출애": 2, "레위": 3, "민수": 4, "신명": 5, "여호": 6, "사사": 7,
        "에스": 15, "느헤": 16,
    }

    def lookup_book_id(self, book_key: str) -> Optional[int]:
        key = book_key.strip()
        if key in self.ALIASES:
            return self.ALIASES[key]
        meta = resolve_book(key)
        return meta.book_id if meta else None

    def get_book_name(self, book_id: int) -> str:
        meta = resolve_book(book_id)
        return meta.name_kr if meta else "미상"

    def parse_reference(self, ref_str: str) -> Optional[Tuple[int, int, int, int]]:
        ref_clean = ref_str.strip()
        match = re.match(r"^([가-힣a-zA-Z0-9\s]+?)[\s:]*?(\d+)[\s:장]+(\d+)[절]?$", ref_clean)
        if not match:
            match = re.match(r"^([가-힣a-zA-Z0-9\s]+?)\s+(\d+)\s+(\d+)$", ref_clean)
        if not match:
            return None

        raw_book, raw_chap, raw_verse = match.groups()
        book_id = self.lookup_book_id(raw_book)
        if not book_id:
            return None
        ch, vs = int(raw_chap), int(raw_verse)
        return (book_id, ch, vs, calculate_verse_id(book_id, ch, vs))

    def parse_range_reference(
        self, ref_str: str
    ) -> Optional[Tuple[int, int, int, int, int, int, int]]:
        ref_clean = ref_str.strip()
        range_match = re.match(
            r"^([가-힣a-zA-Z0-9\s]+?)[\s:]*?(\d+)[\s:장]+(\d+)\s*[-~]\s*(\d+)[절]?$",
            ref_clean,
        )
        if range_match:
            raw_book, raw_chap, start_vs, end_vs = range_match.groups()
            book_id = self.lookup_book_id(raw_book)
            if not book_id:
                return None
            ch, v1, v2 = int(raw_chap), int(start_vs), int(end_vs)
            return (book_id, ch, v1, ch, v2, calculate_verse_id(book_id, ch, v1), calculate_verse_id(book_id, ch, v2))

        single = self.parse_reference(ref_clean)
        if single:
            b_id, ch, vs, v_id = single
            return (b_id, ch, vs, ch, vs, v_id, v_id)
        return None


def extract_strong_tags(text: str) -> Tuple[str, Optional[str]]:
    """Separate inline Strong's tags (<H7225> / {G3056}) into (clean_text, tagged_text)."""
    if not re.search(r"[<{][HG]\d+[>}]", text):
        return text.strip(), None
    clean = re.sub(r"[<{][HG]\d+[>}]", "", text)
    clean = re.sub(r"\s+", " ", clean).strip()
    standardized = re.sub(r"\{([HG]\d+)\}", r"<\1>", text).strip()
    return clean, standardized


def parse_krv_corpus_json(json_path: Path) -> List[Dict[str, Any]]:
    """Parse canonical 66-book bible_1961_krv.json into normalized verse rows."""
    raw = json.loads(json_path.read_text(encoding="utf-8"))
    records: List[Dict[str, Any]] = []
    for book_obj in raw:
        meta = resolve_book(book_obj["book"])
        if not meta:
            raise ValueError(f"Unrecognized book name in KRV JSON: {book_obj['book']}")
        for ch_obj in book_obj.get("chapters", []):
            ch_num = int(ch_obj["chapter"])
            for v_obj in ch_obj.get("verses", []):
                v_num = int(v_obj["verse"])
                text = v_obj["text"].strip()
                if not text:
                    raise ValueError(f"Empty verse text at {meta.osis_code} {ch_num}:{v_num}")
                records.append({
                    "verse_id": calculate_verse_id(meta.book_id, ch_num, v_num),
                    "book_id": meta.book_id,
                    "chapter": ch_num,
                    "verse": v_num,
                    "version_code": "KRV",
                    "text": text,
                    "text_with_strong": None,
                    "provenance_id": "krv_1961_public_domain",
                })
    return records
