"""
Unified Scripture Reference Normalizer & Structured Data Parsers (v3.0).
Senior-pastor forgiving Korean/English/OSIS reference parser with strict bounds validation.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .canon import (
    BIBLE_BOOKS,
    BOOKS_BY_ID,
    calculate_verse_id,
    get_chapter_verse_count,
    resolve_book,
)


class ScriptureRefNormalizer:
    """Normalizes Korean/English/OSIS scripture citations into canonical verse coordinates."""

    # Note: ambiguous "에스" is intentionally omitted (collides with 에스라/에스더/에스겔).
    ALIASES: Dict[str, int] = {
        # Korean short/variant names (spaces stripped during lookup)
        "창세": 1, "출애": 2, "출애굽": 2, "레위": 3, "민수": 4, "신명": 5,
        "여호": 6, "사사": 7, "느헤": 16, "애가": 25, "아가서": 22,
        "사무엘상": 9, "사무엘하": 10, "삼상": 9, "삼하": 10,
        "열왕기상": 11, "열왕기하": 12, "왕상": 11, "왕하": 12,
        "역대상": 13, "역대하": 14, "대상": 13, "대하": 14,
        "고린도전": 46, "고린도후": 47, "고전": 46, "고후": 47,
        "데살로니가전": 52, "데살로니가후": 53, "살전": 52, "살후": 53,
        "디모데전": 54, "디모데후": 55, "딤전": 54, "딤후": 55,
        "베드로전": 60, "베드로후": 61, "벧전": 60, "벧후": 61,
        "요한1서": 62, "요한2서": 63, "요한3서": 64,
        "요한1": 62, "요한2": 63, "요한3": 64,
        "요1서": 62, "요2서": 63, "요3서": 64,
        "요1": 62, "요2": 63, "요3": 64,
        "계시록": 66, "요한계시": 66,
        # English abbreviations (lowercased, spaces/dots stripped during lookup)
        "gen": 1, "ge": 1, "gn": 1,
        "ex": 2, "exo": 2, "exod": 2,
        "lev": 3, "le": 3, "lv": 3,
        "num": 4, "nu": 4, "nm": 4,
        "deu": 5, "deut": 5, "dt": 5,
        "jos": 6, "josh": 6,
        "jdg": 7, "judg": 7,
        "rut": 8, "ruth": 8,
        "1sa": 9, "1sam": 9, "1samuel": 9,
        "2sa": 10, "2sam": 10, "2samuel": 10,
        "1ki": 11, "1kgs": 11, "1kings": 11,
        "2ki": 12, "2kgs": 12, "2kings": 12,
        "1ch": 13, "1chr": 13, "1chron": 13, "1chronicles": 13,
        "2ch": 14, "2chr": 14, "2chron": 14, "2chronicles": 14,
        "ezr": 15, "ezra": 15,
        "neh": 16, "nehemiah": 16,
        "est": 17, "esth": 17, "esther": 17,
        "job": 18,
        "ps": 19, "psa": 19, "psalm": 19, "psalms": 19,
        "pro": 20, "prov": 20, "pr": 20,
        "ecc": 21, "eccl": 21, "eccles": 21,
        "sng": 22, "song": 22, "sos": 22, "songofsongs": 22,
        "isa": 23, "is": 23,
        "jer": 24,
        "lam": 25,
        "ezk": 26, "ezek": 26, "eze": 26,
        "dan": 27, "dn": 27,
        "hos": 28,
        "jol": 29, "joel": 29,
        "amo": 30, "amos": 30,
        "oba": 31, "obad": 31,
        "jon": 32, "jonah": 32, "jnh": 32,
        "mic": 33,
        "nam": 34, "nah": 34,
        "hab": 35,
        "zep": 36, "zeph": 36,
        "hag": 37,
        "zec": 38, "zech": 38,
        "mal": 39,
        "mat": 40, "matt": 40, "mt": 40,
        "mrk": 41, "mark": 41, "mk": 41,
        "luk": 42, "luke": 42, "lk": 42,
        "jhn": 43, "john": 43, "jn": 43,
        "act": 44, "acts": 44,
        "rom": 45, "ro": 45, "rm": 45,
        "1co": 46, "1cor": 46, "1corinthians": 46,
        "2co": 47, "2cor": 47, "2corinthians": 47,
        "gal": 48, "ga": 48,
        "eph": 49,
        "php": 50, "phil": 50,
        "col": 51,
        "1th": 52, "1thess": 52, "1thessalonians": 52,
        "2th": 53, "2thess": 53, "2thessalonians": 53,
        "1ti": 54, "1tim": 54, "1timothy": 54,
        "2ti": 55, "2tim": 55, "2timothy": 55,
        "tit": 56, "titus": 56,
        "phm": 57, "phlm": 57, "philem": 57,
        "heb": 58,
        "jas": 59, "jam": 59, "james": 59,
        "1pe": 60, "1pet": 60, "1peter": 60,
        "2pe": 61, "2pet": 61, "2peter": 61,
        "1jn": 62, "1john": 62, "1jo": 62,
        "2jn": 63, "2john": 63, "2jo": 63,
        "3jn": 64, "3john": 64, "3jo": 64,
        "jud": 65, "jude": 65,
        "rev": 66, "re": 66,
    }

    def lookup_book_id(self, book_key: str) -> Optional[int]:
        raw = book_key.strip()
        if not raw:
            return None
        # Reject pure digits so numeric queries like "305" aren't confused with book IDs
        if raw.isdigit():
            return None
        compact = re.sub(r"[\s.]+", "", raw)
        lower_compact = compact.lower()
        if compact in self.ALIASES:
            return self.ALIASES[compact]
        if lower_compact in self.ALIASES:
            return self.ALIASES[lower_compact]
        meta = resolve_book(compact) or resolve_book(raw)
        return meta.book_id if meta else None

    def get_book_name(self, book_id: int) -> str:
        meta = resolve_book(book_id)
        return meta.name_kr if meta else "미상"

    @staticmethod
    def _validate_coords(book_id: int, ch: int, vs: int) -> bool:
        meta = BOOKS_BY_ID.get(book_id)
        if not meta:
            return False
        if not (1 <= ch <= meta.total_chapters):
            return False
        max_vs = get_chapter_verse_count(meta.osis_code, ch)
        if max_vs is None:
            return 1 <= vs <= 200
        return 1 <= vs <= max_vs

    def parse_reference(self, ref_str: str) -> Optional[Tuple[int, int, int, int]]:
        if not ref_str or not isinstance(ref_str, str):
            return None
        ref_clean = ref_str.strip()
        if not ref_clean:
            return None

        # 1) Explicit book + chapter (:|장|편) + verse (절?)
        # Uses non-greedy book match supporting Korean digits like "요한1서" and English "1 Cor"
        match = re.match(
            r"^([1-3]?\s*[가-힣a-zA-Z]+(?:[1-3]서)?(?:\s+[가-힣a-zA-Z]+)?)\s*(\d+)\s*(?:[:장편]\s*)(\d+)\s*절?$",
            ref_clean,
        )
        if not match:
            # 2) Space-separated: "시편 23 1" or "창세기 1 1"
            match = re.match(
                r"^([1-3]?\s*[가-힣a-zA-Z]+(?:[1-3]서)?(?:\s+[가-힣a-zA-Z]+)?)\s+(\d+)\s+(\d+)$",
                ref_clean,
            )

        if match:
            raw_book, raw_chap, raw_verse = match.groups()
            book_id = self.lookup_book_id(raw_book)
            if not book_id:
                return None
            ch, vs = int(raw_chap), int(raw_verse)
            if not self._validate_coords(book_id, ch, vs):
                return None
            return (book_id, ch, vs, calculate_verse_id(book_id, ch, vs))

        # 3) Chapter-only: "창세기 1장", "고린도 전서 13장", "시편 23편"
        chap_match = re.match(
            r"^([1-3]?\s*[가-힣a-zA-Z]+(?:[1-3]서)?(?:\s+[가-힣a-zA-Z]+)?)\s*(\d+)\s*[장편]$",
            ref_clean,
        )
        if chap_match:
            raw_book, raw_chap = chap_match.groups()
            book_id = self.lookup_book_id(raw_book)
            if not book_id:
                return None
            ch = int(raw_chap)
            if not self._validate_coords(book_id, ch, 1):
                return None
            return (book_id, ch, 1, calculate_verse_id(book_id, ch, 1))

        return None

    def parse_range_reference(
        self, ref_str: str
    ) -> Optional[Tuple[int, int, int, int, int, int, int]]:
        if not ref_str or not isinstance(ref_str, str):
            return None
        ref_clean = ref_str.strip()
        if not ref_clean:
            return None

        range_match = re.match(
            r"^([1-3]?\s*[가-힣a-zA-Z]+(?:[1-3]서)?(?:\s+[가-힣a-zA-Z]+)?)\s*(\d+)\s*(?:[:장편]\s*)(\d+)\s*[-~]\s*(\d+)\s*절?$",
            ref_clean,
        )
        if range_match:
            raw_book, raw_chap, start_vs, end_vs = range_match.groups()
            book_id = self.lookup_book_id(raw_book)
            if not book_id:
                return None
            ch, v1, v2 = int(raw_chap), int(start_vs), int(end_vs)
            if v1 > v2:
                return None
            if not (self._validate_coords(book_id, ch, v1) and self._validate_coords(book_id, ch, v2)):
                return None
            return (
                book_id,
                ch,
                v1,
                ch,
                v2,
                calculate_verse_id(book_id, ch, v1),
                calculate_verse_id(book_id, ch, v2),
            )

        # Chapter-only range: "시편 23편" -> entire chapter 1..max_vs
        chap_match = re.match(
            r"^([1-3]?\s*[가-힣a-zA-Z]+(?:[1-3]서)?(?:\s+[가-힣a-zA-Z]+)?)\s*(\d+)\s*[장편]$",
            ref_clean,
        )
        if chap_match:
            raw_book, raw_chap = chap_match.groups()
            book_id = self.lookup_book_id(raw_book)
            if not book_id:
                return None
            ch = int(raw_chap)
            meta = BOOKS_BY_ID.get(book_id)
            if not meta or not (1 <= ch <= meta.total_chapters):
                return None
            max_vs = get_chapter_verse_count(meta.osis_code, ch) or 1
            return (
                book_id,
                ch,
                1,
                ch,
                max_vs,
                calculate_verse_id(book_id, ch, 1),
                calculate_verse_id(book_id, ch, max_vs),
            )

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
                if "\ufffd" in text:
                    raise ValueError(f"Mojibake U+FFFD at {meta.osis_code} {ch_num}:{v_num}")
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
