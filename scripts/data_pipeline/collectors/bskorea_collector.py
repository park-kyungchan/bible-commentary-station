"""
BSKorea (대한성서공회) Web Collector for Biblical Exegesis Pastoral Workstation.
Uses Scrapling Fetcher with strict read-only compliance, rate-limiting,
and standard SQLite FTS5 database schema compatibility.
"""

import os
import sys
import re
import time
import random
import json
import sqlite3
import copy
from typing import List, Dict, Any, Optional, Union, Tuple
from bs4 import BeautifulSoup

# Ensure stdout/stderr are UTF-8 compliant in Windows consoles
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

try:
    from scrapling import Fetcher
except ImportError:
    raise ImportError(
        "scrapling is required. Please install or use the dedicated python runtime at "
        r"C:\Users\packr\Desktop\scrapling\.venv\Scripts\python.exe"
    )

try:
    from ..schema import calculate_verse_id, BIBLE_BOOKS_MASTER
except (ImportError, ValueError):
    # Fallback if executed directly or in standalone context
    CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_PIPELINE_DIR = os.path.dirname(CURRENT_DIR)
    if DATA_PIPELINE_DIR not in sys.path:
        sys.path.insert(0, DATA_PIPELINE_DIR)
    from schema import calculate_verse_id, BIBLE_BOOKS_MASTER


# 66 Bible Books definition with BSKorea URL codes
# (book_id, osis_code, name_kr, abbr_kr, name_en, testament, category, total_chapters, total_verses, bskorea_code)
BSKOREA_BOOKS_CONFIG = [
    (1, "GEN", "창세기", "창", "Genesis", "OT", "율법서", 50, 1533, "gen"),
    (2, "EXO", "출애굽기", "출", "Exodus", "OT", "율법서", 40, 1213, "exo"),
    (3, "LEV", "레위기", "레", "Leviticus", "OT", "율법서", 27, 859, "lev"),
    (4, "NUM", "민수기", "민", "Numbers", "OT", "율법서", 36, 1288, "num"),
    (5, "DEU", "신명기", "신", "Deuteronomy", "OT", "율법서", 34, 959, "deu"),
    (6, "JOS", "여호수아", "수", "Joshua", "OT", "역사서", 24, 658, "jos"),
    (7, "JDG", "사사기", "삿", "Judges", "OT", "역사서", 21, 618, "jdg"),
    (8, "RUT", "룻기", "룻", "Ruth", "OT", "역사서", 4, 85, "rut"),
    (9, "1SA", "사무엘상", "삼상", "1 Samuel", "OT", "역사서", 31, 810, "1sa"),
    (10, "2SA", "사무엘하", "삼하", "2 Samuel", "OT", "역사서", 24, 695, "2sa"),
    (11, "1KI", "열왕기상", "왕상", "1 Kings", "OT", "역사서", 22, 816, "1ki"),
    (12, "2KI", "열왕기하", "왕하", "2 Kings", "OT", "역사서", 25, 719, "2ki"),
    (13, "1CH", "역대상", "대상", "1 Chronicles", "OT", "역사서", 29, 942, "1ch"),
    (14, "2CH", "역대하", "대하", "2 Chronicles", "OT", "역사서", 36, 822, "2ch"),
    (15, "EZR", "에스라", "스", "Ezra", "OT", "역사서", 10, 280, "ezr"),
    (16, "NEH", "느헤미야", "느", "Nehemiah", "OT", "역사서", 13, 406, "neh"),
    (17, "EST", "에스더", "에", "Esther", "OT", "역사서", 10, 167, "est"),
    (18, "JOB", "욥기", "욥", "Job", "OT", "시가서", 42, 1070, "job"),
    (19, "PSA", "시편", "시", "Psalms", "OT", "시가서", 150, 2461, "psa"),
    (20, "PRO", "잠언", "잠", "Proverbs", "OT", "시가서", 31, 915, "pro"),
    (21, "ECC", "전도서", "전", "Ecclesiastes", "OT", "시가서", 12, 222, "ecc"),
    (22, "SNG", "아가", "아", "Song of Solomon", "OT", "시가서", 8, 117, "sng"),
    (23, "ISA", "이사야", "사", "Isaiah", "OT", "대예언서", 66, 1292, "isa"),
    (24, "JER", "예레미야", "렘", "Jeremiah", "OT", "대예언서", 52, 1364, "jer"),
    (25, "LAM", "예레미야애가", "애", "Lamentations", "OT", "대예언서", 5, 66, "lam"),
    (26, "EZK", "에스겔", "겔", "Ezekiel", "OT", "대예언서", 48, 1273, "ezk"),
    (27, "DAN", "다니엘", "단", "Daniel", "OT", "대예언서", 12, 357, "dan"),
    (28, "HOS", "호세아", "호", "Hosea", "OT", "소예언서", 14, 197, "hos"),
    (29, "JOL", "요엘", "욜", "Joel", "OT", "소예언서", 3, 73, "jol"),
    (30, "AMO", "아모스", "암", "Amos", "OT", "소예언서", 9, 146, "amo"),
    (31, "OBA", "오바댜", "옵", "Obadiah", "OT", "소예언서", 1, 21, "oba"),
    (32, "JON", "요나", "욘", "Jonah", "OT", "소예언서", 4, 48, "jnh"),
    (33, "MIC", "미가", "미", "Micah", "OT", "소예언서", 7, 105, "mic"),
    (34, "NAM", "나훔", "나", "Nahum", "OT", "소예언서", 3, 47, "nam"),
    (35, "HAB", "하박국", "합", "Habakkuk", "OT", "소예언서", 3, 56, "hab"),
    (36, "ZEP", "스바냐", "습", "Zephaniah", "OT", "소예언서", 3, 53, "zep"),
    (37, "HAG", "학개", "학", "Haggai", "OT", "소예언서", 2, 38, "hag"),
    (38, "ZEC", "스가랴", "슥", "Zechariah", "OT", "소예언서", 14, 211, "zec"),
    (39, "MAL", "말라기", "말", "Malachi", "OT", "소예언서", 4, 55, "mal"),
    (40, "MAT", "마태복음", "마", "Matthew", "NT", "복음서", 28, 1071, "mat"),
    (41, "MRK", "마가복음", "막", "Mark", "NT", "복음서", 16, 678, "mrk"),
    (42, "LUK", "누가복음", "눅", "Luke", "NT", "복음서", 24, 1151, "luk"),
    (43, "JHN", "요한복음", "요", "John", "NT", "복음서", 21, 879, "jhn"),
    (44, "ACT", "사도행전", "행", "Acts", "NT", "역사서", 28, 1007, "act"),
    (45, "ROM", "로마서", "롬", "Romans", "NT", "바울서신", 16, 433, "rom"),
    (46, "1CO", "고린도전서", "고전", "1 Corinthians", "NT", "바울서신", 16, 437, "1co"),
    (47, "2CO", "고린도후서", "고후", "2 Corinthians", "NT", "바울서신", 13, 257, "2co"),
    (48, "GAL", "갈라디아서", "갈", "Galatians", "NT", "바울서신", 6, 149, "gal"),
    (49, "EPH", "에베소서", "엡", "Ephesians", "NT", "바울서신", 6, 155, "eph"),
    (50, "PHP", "빌립보서", "빌", "Philippians", "NT", "바울서신", 4, 104, "php"),
    (51, "COL", "골로새서", "골", "Colossians", "NT", "바울서신", 4, 95, "col"),
    (52, "1TH", "데살로니가전서", "살전", "1 Thessalonians", "NT", "바울서신", 5, 89, "1th"),
    (53, "2TH", "데살로니가후서", "살후", "2 Thessalonians", "NT", "바울서신", 3, 47, "2th"),
    (54, "1TI", "디모데전서", "딤전", "1 Timothy", "NT", "바울서신", 6, 113, "1ti"),
    (55, "2TI", "디모데후서", "딤후", "2 Timothy", "NT", "바울서신", 4, 83, "2ti"),
    (56, "TIT", "디도서", "딛", "Titus", "NT", "바울서신", 3, 46, "tit"),
    (57, "PHM", "빌레몬서", "몬", "Philemon", "NT", "바울서신", 1, 25, "phm"),
    (58, "HEB", "히브리서", "히", "Hebrews", "NT", "공동서신", 13, 303, "heb"),
    (59, "JAS", "야고보서", "약", "James", "NT", "공동서신", 5, 108, "jas"),
    (60, "1PE", "베드로전서", "벧전", "1 Peter", "NT", "공동서신", 5, 105, "1pe"),
    (61, "2PE", "베드로후서", "벧후", "2 Peter", "NT", "공동서신", 3, 61, "2pe"),
    (62, "1JN", "요한일서", "요일", "1 John", "NT", "공동서신", 5, 105, "1jn"),
    (63, "2JN", "요한이서", "요이", "2 John", "NT", "공동서신", 1, 13, "2jn"),
    (64, "3JN", "요한삼서", "요삼", "3 John", "NT", "공동서신", 1, 14, "3jn"),
    (65, "JUD", "유다서", "유", "Jude", "NT", "공동서신", 1, 25, "jud"),
    (66, "REV", "요한계시록", "계", "Revelation", "NT", "예언서", 22, 404, "rev"),
]

# Supported BSKorea translation codes & mapping to project version_code
BSKOREA_VERSION_MAP = {
    "GAE": "GAE",       # 개역개정 (Korean Revised Version 4th Ed)
    "HAN": "KRV",       # 개역한글 (Korean Revised Version 1961) -> Maps to KRV in db
    "KRV": "KRV",       # 개역한글 alias
    "SAENEW": "SAENEW", # 새번역
    "SAE": "SAE",       # 표준새번역
    "COGNEW": "COGNEW", # 공동번역개정판
    "COG": "COG",       # 공동번역
    "CEV": "CEV",       # Contemporary English Version
}


class BskoreaCollector:
    """
    Polite, read-only web collector for Bible text from 대한성서공회 (BSKorea).
    Integrates directly with the Pastoral Workstation SQLite FTS5 pipeline.
    """

    BASE_URL = "https://www.bskorea.or.kr/bible/korbibReadpage.php"

    def __init__(
        self,
        default_version: str = "GAE",
        delay_seconds: float = 1.5,
        max_retries: int = 3,
        backoff_factor: float = 2.0,
        timeout: int = 15,
    ):
        """
        :param default_version: Bible version code ('GAE', 'KRV'/'HAN', etc.)
        :param delay_seconds: Polite sleep interval between consecutive HTTP requests.
        :param max_retries: Maximum retry attempts on transient network or server errors.
        :param backoff_factor: Multiplier for exponential backoff delay.
        :param timeout: Request timeout in seconds.
        """
        self.default_version = default_version.upper()
        self.delay_seconds = delay_seconds
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.timeout = timeout
        self.last_request_time = 0.0

        # Build index lookups for books
        self._book_by_id: Dict[int, Dict[str, Any]] = {}
        self._book_by_osis: Dict[str, Dict[str, Any]] = {}
        self._book_by_name: Dict[str, Dict[str, Any]] = {}
        self._book_by_abbr: Dict[str, Dict[str, Any]] = {}
        self._book_by_bs_code: Dict[str, Dict[str, Any]] = {}

        self._init_book_indexes()

    def _init_book_indexes(self):
        """Builds multi-key resolution indexes for all 66 Bible books."""
        for item in BSKOREA_BOOKS_CONFIG:
            (
                book_id, osis_code, name_kr, abbr_kr, name_en,
                testament, category, total_chapters, total_verses, bskorea_code
            ) = item
            meta = {
                "book_id": book_id,
                "osis_code": osis_code,
                "name_kr": name_kr,
                "abbr_kr": abbr_kr,
                "name_en": name_en,
                "testament": testament,
                "category": category,
                "total_chapters": total_chapters,
                "total_verses": total_verses,
                "bskorea_code": bskorea_code,
            }
            self._book_by_id[book_id] = meta
            self._book_by_osis[osis_code.upper()] = meta
            self._book_by_name[name_kr] = meta
            self._book_by_abbr[abbr_kr] = meta
            self._book_by_bs_code[bskorea_code.lower()] = meta

        # Additional alias mappings for alternative Korean spellings
        aliases = {
            "요한1서": "1JN", "요한2서": "2JN", "요한3서": "3JN",
            "요한일서": "1JN", "요한이서": "2JN", "요한삼서": "3JN",
        }
        for alias, osis in aliases.items():
            self._book_by_name[alias] = self._book_by_osis[osis]

    def resolve_book(self, identifier: Union[int, str]) -> Dict[str, Any]:
        """
        Resolves a book identifier (book_id, OSIS code, Korean name, abbreviation, or BS code)
        to the standard book metadata dictionary.
        """
        if isinstance(identifier, int):
            if identifier in self._book_by_id:
                return self._book_by_id[identifier]
            raise ValueError(f"Invalid Bible book_id: {identifier} (must be 1-66)")

        s = str(identifier).strip()
        if s.isdigit():
            b_id = int(s)
            if b_id in self._book_by_id:
                return self._book_by_id[b_id]
            raise ValueError(f"Invalid Bible book_id: {b_id} (must be 1-66)")

        s_upper = s.upper()
        if s_upper in self._book_by_osis:
            return self._book_by_osis[s_upper]

        if s in self._book_by_name:
            return self._book_by_name[s]

        if s in self._book_by_abbr:
            return self._book_by_abbr[s]

        s_lower = s.lower()
        if s_lower in self._book_by_bs_code:
            return self._book_by_bs_code[s_lower]

        raise ValueError(f"Unrecognized Bible book identifier: '{identifier}'")

    def _enforce_rate_limit(self):
        """Enforces polite rate limiting with random jitter to prevent server strain."""
        elapsed = time.time() - self.last_request_time
        target_delay = self.delay_seconds + random.uniform(-0.1, 0.25)
        if elapsed < target_delay:
            sleep_duration = max(0.1, target_delay - elapsed)
            time.sleep(sleep_duration)
        self.last_request_time = time.time()

    def fetch_chapter_html(
        self,
        bskorea_code: str,
        chapter: int,
        version_code: str = "GAE"
    ) -> str:
        """
        Fetches the raw HTML content for a specific chapter from BSKorea.
        Implements read-only GET requests with retry and backoff.
        """
        # Map version for BSKorea query parameter
        bs_ver = "HAN" if version_code.upper() in ("KRV", "HAN") else version_code.upper()
        url = f"{self.BASE_URL}?version={bs_ver}&book={bskorea_code}&chap={chapter}&sec=1"

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36 (BiblicalExegesis/1.0 Pastoral Research)"
            ),
            "Referer": "https://www.bskorea.or.kr/bible/korbibReadpage.php",
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }

        last_error = None
        for attempt in range(1, self.max_retries + 1):
            try:
                self._enforce_rate_limit()
                response = Fetcher.get(url, headers=headers, timeout=self.timeout)

                if response.status == 200:
                    raw_bytes = response.body
                    # BSKorea sends UTF-8 encoded text
                    html_text = raw_bytes.decode('utf-8', errors='replace')
                    if "tdBible1" in html_text or "bible_read" in html_text:
                        return html_text
                    else:
                        raise ValueError(f"BSKorea returned 200 but tdBible1 container missing for {url}")
                elif response.status in (429, 500, 502, 503, 504):
                    sleep_time = (self.backoff_factor ** attempt) + random.uniform(0.5, 1.5)
                    print(
                        f"[WARN] BSKorea HTTP {response.status} on attempt {attempt}/{self.max_retries}. "
                        f"Backing off for {sleep_time:.2f}s...",
                        file=sys.stderr
                    )
                    time.sleep(sleep_time)
                else:
                    raise RuntimeError(f"BSKorea HTTP {response.status}: Failed to fetch {url}")

            except Exception as e:
                last_error = e
                sleep_time = (self.backoff_factor ** attempt) + random.uniform(0.5, 1.5)
                print(
                    f"[WARN] Error fetching {url} on attempt {attempt}/{self.max_retries}: {e}. "
                    f"Retrying in {sleep_time:.2f}s...",
                    file=sys.stderr
                )
                time.sleep(sleep_time)

        raise RuntimeError(
            f"Failed to fetch chapter from BSKorea after {self.max_retries} attempts: {url}. "
            f"Last error: {last_error}"
        )

    def parse_chapter_html(
        self,
        html_content: str,
        book_id: int,
        chapter: int,
        version_code: str = "GAE"
    ) -> List[Dict[str, Any]]:
        """
        Parses BSKorea chapter HTML into standard Bible schema records.
        Removes footnote markers, cross-reference anchors, and popup divs
        to ensure pure canonical Scripture text, while indexing metadata.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        td_bible = soup.find(id='tdBible1')
        if not td_bible:
            # Fallback search for class
            td_bible = soup.find('div', class_='bible_read')
        if not td_bible:
            return []

        # Canonical database version code
        db_version = "KRV" if version_code.upper() in ("KRV", "HAN") else version_code.upper()

        current_section: Optional[str] = None
        verses: List[Dict[str, Any]] = []

        for child in td_bible.children:
            if not child.name:
                continue

            cls = child.get('class', [])

            # 1. Section Title / Paragraph Subtitle (소제목)
            if 'smallTitle' in cls:
                current_section = child.get_text().strip()
                continue

            # 2. Verse span block contains <span class="number">
            num_span = child.find('span', class_='number')
            if not num_span:
                continue

            v_num_str = num_span.get_text().strip()
            if not v_num_str.isdigit():
                continue
            v_num = int(v_num_str)

            # 3. Extract footnotes (각주) and cross references (관주)
            footnotes = []
            cross_refs = []

            comment_links = child.find_all('a', class_='comment')
            for a in comment_links:
                marker = a.get_text().strip()
                onclick = a.get('onclick', '')
                m = re.search(r"clickPopUp\('([^']+)'", onclick)
                popup_id = m.group(1) if m else None

                popup_div = child.find('div', id=popup_id) if popup_id else None
                if not popup_div and popup_id:
                    popup_div = td_bible.find('div', id=popup_id)

                content = ""
                tar = None
                if popup_div:
                    tar_a = popup_div.find('a', attrs={'tar': True})
                    if tar_a:
                        tar = tar_a.get('tar')
                    content = popup_div.get_text().strip()

                # Distinguish Korean cross-ref (ㄱ, ㄴ, ...) from footnotes (1, 2, ...)
                is_cross_ref = bool(re.search(r'^[ㄱ-ㅎ]\)', marker)) or bool(tar)
                if is_cross_ref:
                    cross_refs.append({
                        "marker": marker,
                        "target_ref": content,
                        "target_tar": tar,
                    })
                else:
                    footnotes.append({
                        "marker": marker,
                        "text": content,
                    })

            # 4. Extract pure, uncorrupted canonical Scripture text
            elem_clone = copy.copy(child)
            # Remove verse number, footnote/ref links, popup divs
            for tag in elem_clone.find_all(['span', 'div', 'a']):
                tag.decompose()

            raw_text = elem_clone.get_text()
            # Normalize whitespace: replace non-breaking spaces and linebreaks
            clean_text = raw_text.replace('\xa0', ' ')
            clean_text = re.sub(r'[\r\n\t]+', ' ', clean_text)
            clean_text = re.sub(r'\s{2,}', ' ', clean_text).strip()

            # Calculate deterministic verse_id: book*1000000 + chapter*1000 + verse
            verse_id = calculate_verse_id(book_id, chapter, v_num)

            verse_record = {
                "verse_id": verse_id,
                "book_id": book_id,
                "chapter": chapter,
                "verse": v_num,
                "version_code": db_version,
                "text": clean_text,
                "text_with_strong": None,
                "section_title": current_section,
                "footnotes": footnotes,
                "cross_refs": cross_refs,
            }
            verses.append(verse_record)

        return verses

    def fetch_chapter(
        self,
        book_ident: Union[int, str],
        chapter: int,
        version_code: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        High-level method to fetch and parse a specific chapter.
        :param book_ident: Book number (1..66), OSIS code ('GEN'), Korean name ('창세기'), etc.
        :param chapter: Chapter number (1-indexed).
        :param version_code: Bible version code ('GAE', 'KRV', etc.). Defaults to self.default_version.
        :return: List of parsed verse dictionaries.
        """
        book_meta = self.resolve_book(book_ident)
        ver = (version_code or self.default_version).upper()

        if chapter < 1 or chapter > book_meta["total_chapters"]:
            raise ValueError(
                f"Chapter {chapter} is out of range for {book_meta['name_kr']} "
                f"(max {book_meta['total_chapters']} chapters)"
            )

        html = self.fetch_chapter_html(
            bskorea_code=book_meta["bskorea_code"],
            chapter=chapter,
            version_code=ver
        )

        return self.parse_chapter_html(
            html_content=html,
            book_id=book_meta["book_id"],
            chapter=chapter,
            version_code=ver
        )

    def fetch_book(
        self,
        book_ident: Union[int, str],
        version_code: Optional[str] = None,
        on_chapter_done=None
    ) -> List[Dict[str, Any]]:
        """
        Fetches all chapters of an entire book with polite rate limiting.
        :param book_ident: Book identifier (1..66, 'GEN', '창세기', etc.)
        :param version_code: Bible version ('GAE', etc.)
        :param on_chapter_done: Optional callback called after each chapter is fetched.
        :return: List of all verses in the book.
        """
        book_meta = self.resolve_book(book_ident)
        ver = (version_code or self.default_version).upper()
        total_chaps = book_meta["total_chapters"]

        all_verses = []
        for ch in range(1, total_chaps + 1):
            verses = self.fetch_chapter(book_meta["book_id"], ch, ver)
            all_verses.extend(verses)
            if on_chapter_done:
                on_chapter_done(book_meta, ch, len(verses))

        return all_verses

    def fetch_range(
        self,
        start_book: Union[int, str],
        end_book: Union[int, str],
        version_code: Optional[str] = None,
        on_chapter_done=None
    ) -> List[Dict[str, Any]]:
        """
        Fetches all chapters in a range of books (e.g. 40 to 43 for the 4 Gospels).
        """
        b_start = self.resolve_book(start_book)["book_id"]
        b_end = self.resolve_book(end_book)["book_id"]

        if b_start > b_end:
            b_start, b_end = b_end, b_start

        all_verses = []
        for b_id in range(b_start, b_end + 1):
            book_verses = self.fetch_book(b_id, version_code, on_chapter_done)
            all_verses.extend(book_verses)

        return all_verses

    @staticmethod
    def save_to_json(verses: List[Dict[str, Any]], output_path: str):
        """Saves parsed verses to a UTF-8 JSON file."""
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(verses, f, ensure_ascii=False, indent=2)
        print(f"Saved {len(verses)} verses to: {output_path}")

    @staticmethod
    def ingest_into_db(
        verses: List[Dict[str, Any]],
        db_path: str,
        sync_fts: bool = True
    ) -> int:
        """
        Ingests parsed verses directly into the SQLite database (`bible_verses` table)
        and synchronizes with `fts_bible_verses` full-text search index.
        :param verses: List of verse dictionaries generated by BskoreaCollector.
        :param db_path: Path to `bible_pastoral_core.db`.
        :param sync_fts: Whether to insert/update FTS5 virtual table.
        :return: Count of verses ingested.
        """
        if not os.path.exists(db_path):
            raise FileNotFoundError(f"Database not found at {db_path}. Build DB schema first.")

        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA synchronous = NORMAL;")
        conn.execute("PRAGMA foreign_keys = ON;")

        ingested_count = 0
        try:
            with conn:
                for v in verses:
                    # 1. Ensure version is registered in bible_versions
                    conn.execute(
                        """
                        INSERT OR IGNORE INTO bible_versions 
                        (version_code, name_kr, name_en, language, is_original_lang, is_default, copyright_notice)
                        VALUES (?, ?, ?, ?, ?, ?, ?);
                        """,
                        (
                            v["version_code"],
                            "개역개정" if v["version_code"] == "GAE" else v["version_code"],
                            "Korean Revised Version (4th Ed)" if v["version_code"] == "GAE" else v["version_code"],
                            "KOREAN", 0, 0, "대한성서공회 저작권"
                        )
                    )

                    # 2. Insert into bible_verses
                    conn.execute(
                        """
                        INSERT OR REPLACE INTO bible_verses 
                        (verse_id, book_id, chapter, verse, version_code, text, text_with_strong)
                        VALUES (?, ?, ?, ?, ?, ?, ?);
                        """,
                        (
                            v["verse_id"],
                            v["book_id"],
                            v["chapter"],
                            v["verse"],
                            v["version_code"],
                            v["text"],
                            v.get("text_with_strong")
                        )
                    )

                    # 3. Synchronize with FTS5 index
                    if sync_fts:
                        # Delete existing row in FTS if any to prevent duplicate matches
                        conn.execute(
                            """
                            DELETE FROM fts_bible_verses 
                            WHERE verse_id = ? AND version_code = ?;
                            """,
                            (v["verse_id"], v["version_code"])
                        )
                        conn.execute(
                            """
                            INSERT INTO fts_bible_verses (verse_id, version_code, text)
                            VALUES (?, ?, ?);
                            """,
                            (v["verse_id"], v["version_code"], v["text"])
                        )

                    ingested_count += 1
        finally:
            conn.close()

        print(f"Successfully ingested {ingested_count} verses into {db_path} (FTS sync={sync_fts})")
        return ingested_count


# Standalone CLI and verification harness
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="BSKorea Bible Data Collector")
    parser.add_argument("--version", default="GAE", help="Bible version code (GAE, KRV, etc.)")
    parser.add_argument("--book", default="GEN", help="Book identifier (e.g., GEN, MAT, 1, 창세기)")
    parser.add_argument("--chapter", type=int, default=1, help="Chapter number (default: 1)")
    parser.add_argument("--all-chapters", action="store_true", help="Fetch all chapters in the specified book")
    parser.add_argument("--save-json", help="Path to save output JSON file")
    parser.add_argument("--db-path", help="Path to SQLite database to ingest into")
    parser.add_argument("--test", action="store_true", help="Run automated integrity test on Genesis 1 and Matthew 1")
    parser.add_argument("--delay", type=float, default=1.5, help="Rate limit delay in seconds (default: 1.5)")

    args = parser.parse_args()

    collector = BskoreaCollector(default_version=args.version, delay_seconds=args.delay)

    if args.test:
        print("=== BSKorea Collector Automated Verification Test ===")
        print("\n1. Fetching Genesis 1 (OT)...")
        gen1 = collector.fetch_chapter("GEN", 1, "GAE")
        print(f"-> Genesis 1 verses: {len(gen1)}")
        assert len(gen1) == 31, f"Expected 31 verses, got {len(gen1)}"
        assert gen1[0]["text"] == "태초에 하나님이 천지를 창조하시니라", f"Verse 1 text mismatch: {gen1[0]['text']}"
        assert gen1[1]["footnotes"][0]["text"] == "또는 형체가 없는", "Genesis 1:2 footnote missing"
        print("✓ Genesis 1 passed with 100% precision.")

        print("\n2. Fetching Matthew 1 (NT)...")
        mat1 = collector.fetch_chapter("MAT", 1, "GAE")
        print(f"-> Matthew 1 verses: {len(mat1)}")
        assert len(mat1) == 25, f"Expected 25 verses, got {len(mat1)}"
        assert mat1[0]["text"] == "아브라함과 다윗의 자손 예수 그리스도의 계보라", f"Verse 1 text mismatch: {mat1[0]['text']}"
        assert len(mat1[22]["cross_refs"]) > 0, "Matthew 1:23 cross reference missing"
        assert mat1[22]["cross_refs"][0]["target_ref"] == "사 7:14", "Matthew 1:23 Isaiah 7:14 ref mismatch"
        print("✓ Matthew 1 passed with 100% precision.")

        print("\nAll verification tests completed successfully!")
        sys.exit(0)

    # Normal fetch execution
    if args.all_chapters:
        book_meta = collector.resolve_book(args.book)
        print(f"Fetching all {book_meta['total_chapters']} chapters of {book_meta['name_kr']} ({args.version})...")
        def _on_ch_done(meta, ch, cnt):
            print(f"  [{meta['name_kr']} {ch}/{meta['total_chapters']}] Fetched {cnt} verses.")
        verses = collector.fetch_book(args.book, args.version, on_chapter_done=_on_ch_done)
    else:
        print(f"Fetching {args.book} chapter {args.chapter} ({args.version})...")
        verses = collector.fetch_chapter(args.book, args.chapter, args.version)

    print(f"Total verses collected: {len(verses)}")

    if args.save_json:
        collector.save_to_json(verses, args.save_json)

    if args.db_path:
        collector.ingest_into_db(verses, args.db_path)
