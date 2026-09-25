"""
Commentary Parser supporting the 8 Core Pastoral Commentaries:
1. OXFORD (옥스포드 원어성경대전)
2. WESLEY (존 웨슬리 성경 주석)
3. HOKMA (호크마 종합주석)
4. GRAND (그랜드 종합주석)
5. CHARISMA (카리스마 성경/주석)
6. MATTHEW_HENRY (매튜 헨리 주석)
7. BAKER (베이커 성경배경주석)
8. ESV_EXPOSITORY (ESV 성경해설주석)
"""

import json
import re
from typing import List, Dict, Any, Optional
from .base_parser import BaseParser, ScriptureRefNormalizer
try:
    from ..schema import calculate_verse_id
except (ImportError, ValueError):
    from schema import calculate_verse_id

class CommentaryParser(BaseParser):
    """
    Unified Commentary Parser with dedicated normalization for 8 commentary sources.
    """
    
    SUPPORTED_SOURCES = {
        "OXFORD", "WESLEY", "HOKMA", "GRAND", 
        "CHARISMA", "MATTHEW_HENRY", "BAKER", "ESV_EXPOSITORY"
    }

    def __init__(self):
        self.ref_normalizer = ScriptureRefNormalizer()

    def parse_file(self, file_path: str, source_code: Optional[str] = None) -> List[Dict[str, Any]]:
        """Parses a commentary file (.json, .md, .txt)."""
        if file_path.endswith('.json'):
            return self.parse_json(file_path, source_code)
        elif file_path.endswith('.md') or file_path.endswith('.txt'):
            return self.parse_markdown_file(file_path, source_code)
        else:
            raise ValueError(f"Unsupported file format: {file_path}")

    def parse_json(self, file_path: str, default_source: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Loads structured JSON commentary entries.
        Expected format: list of dicts or {"source": "WESLEY", "entries": [...]}
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        src = default_source
        if isinstance(data, dict):
            src = data.get("source_code") or data.get("source") or default_source
            items = data.get("entries") or data.get("commentaries") or []
        else:
            items = data
        parsed_list = []
        for item in items:
            item_src = item.get("source_code") or item.get("source") or src
            if not item_src:
                continue
            entry = self._normalize_entry(item, item_src)
            if entry:
                parsed_list.append(entry)
        return parsed_list

    def parse_markdown_file(self, file_path: str, source_code: str) -> List[Dict[str, Any]]:
        """
        Parses Markdown formatted commentary files.
        Entries are typically separated by level 2 or 3 headers:
        ## [창 1:1] 태초의 창조
        내용...
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        entries = []
        # 정규표현식으로 헤더 섹션 분리 (예: ## [창 1:1-3] 제목 또는 ## 창 1:1 제목)
        pattern = re.compile(r'^(#{2,3})\s+(?:\[([^\]]+)\]|([가-힣a-zA-Z0-9\s:~\-]+?))(?:\s*[-–:]\s*|\s+)(.*)$', re.MULTILINE)
        
        splits = list(pattern.finditer(content))
        if not splits:
            return entries

        for i, match in enumerate(splits):
            ref_part = match.group(2) or match.group(3)
            title = match.group(4).strip() if match.group(4) else ""
            
            start_pos = match.end()
            end_pos = splits[i+1].start() if i + 1 < len(splits) else len(content)
            body = content[start_pos:end_pos].strip()

            raw_item = {
                "reference": ref_part.strip(),
                "title": title,
                "content": body
            }
            entry = self._normalize_entry(raw_item, source_code)
            if entry:
                entries.append(entry)

        return entries

    def _normalize_entry(self, item: Dict[str, Any], source_code: str) -> Optional[Dict[str, Any]]:
        """Normalizes an individual commentary item into a DB row structure."""
        source_code = source_code.upper()
        if source_code not in self.SUPPORTED_SOURCES:
            # 기본 허용하되 경고 로그 가능
            pass

        ref_str = item.get("reference") or item.get("ref") or item.get("passage")
        book_id = item.get("book_id")
        chap_start = item.get("chapter_start") or item.get("chapter")
        vs_start = item.get("verse_start") or item.get("verse")
        chap_end = item.get("chapter_end") or chap_start
        vs_end = item.get("verse_end") or vs_start

        if ref_str:
            parsed_range = self.ref_normalizer.parse_range_reference(ref_str)
            if parsed_range:
                book_id, chap_start, vs_start, chap_end, vs_end, start_id, end_id = parsed_range
            else:
                return None
        else:
            if not (book_id and chap_start and vs_start):
                return None
            start_id = calculate_verse_id(int(book_id), int(chap_start), int(vs_start))
            end_id = calculate_verse_id(int(book_id), int(chap_end), int(vs_end))

        passage_display = item.get("passage_display")
        if not passage_display:
            b_name = self.ref_normalizer.get_book_name(int(book_id))
            if vs_start == vs_end:
                passage_display = f"{b_name} {chap_start}:{vs_start}"
            else:
                passage_display = f"{b_name} {chap_start}:{vs_start}-{vs_end}"

        raw_content = item.get("content_markdown") or item.get("content") or item.get("text", "")
        title = item.get("title", "")
        practical_points = item.get("practical_points") or item.get("outline") or ""

        tags = set(item.get("theological_tags", "").split(',')) if item.get("theological_tags") else set()
        tags.discard("")

        # 주석 소스별 특화 태그
        if source_code == "OXFORD":
            tags.add("원어강해")
        elif source_code == "WESLEY":
            tags.add("웨슬리안")
            tags.add("성화")
        elif source_code == "GRAND":
            tags.add("설교대지")
        elif source_code == "CHARISMA":
            tags.add("성령론")
        elif source_code == "MATTHEW_HENRY":
            tags.add("경건묵상")
        elif source_code == "BAKER":
            tags.add("배경사")
        elif source_code == "ESV_EXPOSITORY":
            tags.add("구속사강해")

        theological_tags_str = ", ".join(sorted(tags))

        return {
            "source_code": source_code,
            "book_id": int(book_id),
            "chapter_start": int(chap_start),
            "verse_start": int(vs_start),
            "chapter_end": int(chap_end),
            "verse_end": int(vs_end),
            "verse_start_id": start_id,
            "verse_end_id": end_id,
            "passage_display": passage_display,
            "title": title,
            "content_markdown": raw_content,
            "content_html": item.get("content_html"),
            "theological_tags": theological_tags_str,
            "practical_points": practical_points
        }
