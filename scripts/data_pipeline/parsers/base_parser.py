"""
Base Parser and Scripture Reference Normalizer for Bible Data Pipeline.
"""

from abc import ABC, abstractmethod
from typing import Tuple, Optional, Dict, Any, List
import re
try:
    from ..schema import BIBLE_BOOKS_MASTER, calculate_verse_id
except (ImportError, ValueError):
    from schema import BIBLE_BOOKS_MASTER, calculate_verse_id

class BaseParser(ABC):
    """Abstract Base Parser for data ingestion."""
    
    @abstractmethod
    def parse_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Parse source data file into structured dictionaries."""
        pass


class ScriptureRefNormalizer:
    """
    성경 장/절 표기(한글 축약형, 한글 완제형, 영문 OSIS, 영문 표준)를 
    표준화된 (book_id, chapter, verse, verse_id) 튜플로 변환하는 정규화 엔진.
    """
    
    def __init__(self):
        self.abbr_to_book: Dict[str, Tuple[int, str, str]] = {}
        self.name_to_book: Dict[str, Tuple[int, str, str]] = {}
        self.id_to_book: Dict[int, Tuple[str, str, str]] = {}
        self._build_lookup_tables()
        
    def _build_lookup_tables(self):
        for book in BIBLE_BOOKS_MASTER:
            b_id, osis, name_kr, abbr_kr, name_en, _, _, _, _ = book
            self.id_to_book[b_id] = (osis, name_kr, abbr_kr)
            # 한글 약어 (창, 출, 레, ...)
            self.abbr_to_book[abbr_kr] = (b_id, osis, name_kr)
            # 한글 완제명 (창세기, 출애굽기, ...)
            self.name_to_book[name_kr] = (b_id, osis, name_kr)
            # 영문 OSIS (GEN, EXO, ...)
            self.abbr_to_book[osis.upper()] = (b_id, osis, name_kr)
            # 영문 이름 (Genesis, Exodus, ...)
            self.name_to_book[name_en.lower()] = (b_id, osis, name_kr)
            
        # 추가적인 비표준 약어 별칭 등록
        aliases = {
            "창세": 1, "출애": 2, "레위": 3, "민수": 4, "신명": 5, "여호": 6, "사사": 7,
            "삼상": 9, "삼하": 10, "왕상": 11, "왕하": 12, "대상": 13, "대하": 14,
            "에스": 15, "느헤": 16, "시": 19, "잠": 20, "전": 21, "아": 22,
            "사": 23, "렘": 24, "애": 25, "겔": 26, "단": 27, "마": 40, "막": 41,
            "눅": 42, "요": 43, "행": 44, "롬": 45, "고전": 46, "고후": 47, "갈": 48,
            "엡": 49, "빌": 50, "골": 51, "살전": 52, "살후": 53, "딤전": 54, "딤후": 55,
            "딛": 56, "몬": 57, "히": 58, "약": 59, "벧전": 60, "벧후": 61,
            "요일": 62, "요이": 63, "요삼": 64, "유": 65, "계": 66
        }
        for alias, b_id in aliases.items():
            book = BIBLE_BOOKS_MASTER[b_id - 1]
            self.abbr_to_book[alias] = (b_id, book[1], book[2])

    def get_book_name(self, book_id: int) -> str:
        """Returns Korean book name from book_id."""
        return self.id_to_book.get(book_id, ("", "미상", ""))[1]

    def parse_reference(self, ref_str: str) -> Optional[Tuple[int, int, int, int]]:
        """
        '창세기 1:1', '창 1:1', 'GEN 1:1', '창 1장 1절', '요한복음 3:16' 등의 텍스트를 파싱하여
        (book_id, chapter, verse, verse_id) 반환.
        """
        ref_clean = ref_str.strip()
        # 패턴 1: 책이름 1:1 또는 책이름 1장 1절
        match = re.match(r'^([가-힣a-zA-Z0-9\s]+?)[\s:]*?(\d+)[\s:장]+(\d+)[절]?$', ref_clean)
        if not match:
            # 패턴 2: 공백 분리형 (예: '창 1 1')
            match = re.match(r'^([가-힣a-zA-Z0-9\s]+?)\s+(\d+)\s+(\d+)$', ref_clean)
            
        if not match:
            return None
            
        raw_book, raw_chap, raw_verse = match.groups()
        book_key = raw_book.strip()
        
        # 책 조회
        book_id = None
        if book_key in self.name_to_book:
            book_id = self.name_to_book[book_key][0]
        elif book_key in self.abbr_to_book:
            book_id = self.abbr_to_book[book_key][0]
        elif book_key.upper() in self.abbr_to_book:
            book_id = self.abbr_to_book[book_key.upper()][0]
        elif book_key.lower() in self.name_to_book:
            book_id = self.name_to_book[book_key.lower()][0]
            
        if not book_id:
            return None
            
        chapter = int(raw_chap)
        verse = int(raw_verse)
        verse_id = calculate_verse_id(book_id, chapter, verse)
        return (book_id, chapter, verse, verse_id)

    def parse_range_reference(self, ref_str: str) -> Optional[Tuple[int, int, int, int, int, int, int]]:
        """
        '창 1:1-5' 또는 '마태복음 5:1-12' 또는 '창 1:1'을 파싱하여
        (book_id, chapter_start, verse_start, chapter_end, verse_end, start_verse_id, end_verse_id) 반환.
        """
        ref_clean = ref_str.strip()
        # 범위 매칭: 책 장:시작절-끝절
        range_match = re.match(r'^([가-힣a-zA-Z0-9\s]+?)[\s:]*?(\d+)[\s:장]+(\d+)\s*[-~]\s*(\d+)[절]?$', ref_clean)
        if range_match:
            raw_book, raw_chap, start_vs, end_vs = range_match.groups()
            book_key = raw_book.strip()
            book_id = self._lookup_book_id(book_key)
            if not book_id:
                return None
            chapter = int(raw_chap)
            v_start = int(start_vs)
            v_end = int(end_vs)
            start_id = calculate_verse_id(book_id, chapter, v_start)
            end_id = calculate_verse_id(book_id, chapter, v_end)
            return (book_id, chapter, v_start, chapter, v_end, start_id, end_id)
            
        # 단일 절 매칭
        single = self.parse_reference(ref_clean)
        if single:
            b_id, chap, vs, v_id = single
            return (b_id, chap, vs, chap, vs, v_id, v_id)
            
        return None

    def _lookup_book_id(self, book_key: str) -> Optional[int]:
        if book_key in self.name_to_book:
            return self.name_to_book[book_key][0]
        if book_key in self.abbr_to_book:
            return self.abbr_to_book[book_key][0]
        if book_key.upper() in self.abbr_to_book:
            return self.abbr_to_book[book_key.upper()][0]
        if book_key.lower() in self.name_to_book:
            return self.name_to_book[book_key.lower()][0]
        return None
