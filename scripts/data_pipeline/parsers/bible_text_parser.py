"""
Multi-Version Bible Text Parser with Strong's Tag Extraction.
Supports Korean (KRV, GAE), English (KJV, ASV), Original (BHS, GNT) formats.
"""

import re
import json
from typing import List, Dict, Any, Optional
from .base_parser import BaseParser, ScriptureRefNormalizer
try:
    from ..schema import calculate_verse_id
except (ImportError, ValueError):
    from schema import calculate_verse_id

class BibleTextParser(BaseParser):
    """
    Bible Text Parser for text files, JSON files, and Strong-annotated formats.
    """
    
    def __init__(self, default_version_code: str = "KRV"):
        self.default_version = default_version_code
        self.ref_normalizer = ScriptureRefNormalizer()

    def parse_file(self, file_path: str, version_code: Optional[str] = None) -> List[Dict[str, Any]]:
        """Parses a file based on its extension (.json, .txt, .csv)."""
        ver = version_code or self.default_version
        if file_path.endswith('.json'):
            return self.parse_json(file_path, ver)
        else:
            return self.parse_text_lines(file_path, ver)

    def parse_text_lines(self, file_path: str, version_code: str) -> List[Dict[str, Any]]:
        """
        Parses line-by-line format:
        Example lines:
        창 1:1 태초에 하나님이 천지를 창조하시니라
        Gen 1:1 In the beginning God created the heaven and the earth.
        1|1|1|태초에<H7225> 하나님이<H430>...
        """
        verses = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                parsed_verse = self.parse_line(line, version_code)
                if parsed_verse:
                    verses.append(parsed_verse)
        return verses

    def parse_line(self, line: str, version_code: str) -> Optional[Dict[str, Any]]:
        """Parses a single line of scripture."""
        # 1. 파이프(|) 구분 포맷: book_id|chapter|verse|text
        if '|' in line:
            parts = line.split('|', 3)
            if len(parts) >= 4 and parts[0].strip().isdigit():
                b_id = int(parts[0].strip())
                chap = int(parts[1].strip())
                vs = int(parts[2].strip())
                raw_text = parts[3].strip()
                v_id = calculate_verse_id(b_id, chap, vs)
                clean_text, with_strong = self._extract_strongs(raw_text)
                return {
                    "verse_id": v_id,
                    "book_id": b_id,
                    "chapter": chap,
                    "verse": vs,
                    "version_code": version_code,
                    "text": clean_text,
                    "text_with_strong": with_strong
                }

        # 2. 공백 또는 탭 구분 포맷: '창세기 1:1 본문내용...' or '창 1:1 본문...'
        # 참조 부분과 본문 분리
        tokens = line.split(maxsplit=2)
        if len(tokens) >= 2:
            # 케이스 A: "창 1:1 태초에..." -> tokens[0]="창", tokens[1]="1:1", tokens[2]="태초에..."
            potential_ref = f"{tokens[0]} {tokens[1]}"
            res = self.ref_normalizer.parse_reference(potential_ref)
            if res:
                b_id, chap, vs, v_id = res
                raw_text = tokens[2] if len(tokens) > 2 else ""
                clean_text, with_strong = self._extract_strongs(raw_text)
                return {
                    "verse_id": v_id,
                    "book_id": b_id,
                    "chapter": chap,
                    "verse": vs,
                    "version_code": version_code,
                    "text": clean_text,
                    "text_with_strong": with_strong
                }

            # 케이스 B: "창1:1 태초에..." -> tokens[0]="창1:1", tokens[1]="태초에..."
            res_b = self.ref_normalizer.parse_reference(tokens[0])
            if res_b:
                b_id, chap, vs, v_id = res_b
                raw_text = line[len(tokens[0]):].strip()
                clean_text, with_strong = self._extract_strongs(raw_text)
                return {
                    "verse_id": v_id,
                    "book_id": b_id,
                    "chapter": chap,
                    "verse": vs,
                    "version_code": version_code,
                    "text": clean_text,
                    "text_with_strong": with_strong
                }

        return None

    def parse_json(self, file_path: str, version_code: str) -> List[Dict[str, Any]]:
        """Parses JSON-structured Bible files."""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        verses = []
        raw_list = data if isinstance(data, list) else data.get("verses", [])
        for item in raw_list:
            b_id = item.get("book") or item.get("book_id")
            chap = item.get("chapter")
            vs = item.get("verse")
            raw_text = item.get("text", "")
            
            if not b_id or not chap or not vs:
                # reference 문자열 시도
                if "ref" in item:
                    res = self.ref_normalizer.parse_reference(item["ref"])
                    if res:
                        b_id, chap, vs, _ = res

            if b_id and chap and vs:
                v_id = calculate_verse_id(int(b_id), int(chap), int(vs))
                clean_text, with_strong = self._extract_strongs(raw_text)
                verses.append({
                    "verse_id": v_id,
                    "book_id": int(b_id),
                    "chapter": int(chap),
                    "verse": int(vs),
                    "version_code": item.get("version", version_code),
                    "text": clean_text,
                    "text_with_strong": with_strong or item.get("text_with_strong")
                })
        return verses

    def _extract_strongs(self, text: str) -> tuple[str, Optional[str]]:
        """
        인라인 스트롱 태그(예: <H7225>, <G3056>, {H7225})를 검출하여
        (순수_텍스트, 스트롱포함_텍스트)를 분리 반환합니다.
        """
        has_strongs = bool(re.search(r'[<{][HG]\d+[>}]', text))
        if not has_strongs:
            return text.strip(), None
            
        # 순수 텍스트 추출: 태그 제거 및 중복 공백 정돈
        clean = re.sub(r'[<{][HG]\d+[>}]', '', text)
        clean = re.sub(r'\s+', ' ', clean).strip()
        
        # 표준 통일 태그 형식: <H7225>
        standardized_strong = re.sub(r'\{([HG]\d+)\}', r'<\1>', text)
        return clean, standardized_strong
