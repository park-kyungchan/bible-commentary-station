"""
Single Source of Truth (SSOT) for the 66-Book Protestant Canon,
8 Commentary Sources (strictly non-sectarian), Bible Versions, and Verse ID Math.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


@dataclass(frozen=True)
class BibleBookMeta:
    book_id: int
    osis_code: str
    name_kr: str
    name_kr_abbr: str
    name_en: str
    testament: str  # "OT" | "NT"
    category: str
    total_chapters: int
    total_verses: int
    bskorea_code: str

    def as_db_tuple(self) -> Tuple[int, str, str, str, str, str, str, int, int]:
        return (
            self.book_id,
            self.osis_code,
            self.name_kr,
            self.name_kr_abbr,
            self.name_en,
            self.testament,
            self.category,
            self.total_chapters,
            self.total_verses,
        )


# Verified 66-book Protestant Canon (39 OT + 27 NT = 66 books, 1,189 chapters, 31,102 verses)
BIBLE_BOOKS: Tuple[BibleBookMeta, ...] = (
    # Old Testament (39)
    BibleBookMeta(1, "GEN", "창세기", "창", "Genesis", "OT", "율법서", 50, 1533, "gen"),
    BibleBookMeta(2, "EXO", "출애굽기", "출", "Exodus", "OT", "율법서", 40, 1213, "exo"),
    BibleBookMeta(3, "LEV", "레위기", "레", "Leviticus", "OT", "율법서", 27, 859, "lev"),
    BibleBookMeta(4, "NUM", "민수기", "민", "Numbers", "OT", "율법서", 36, 1288, "num"),
    BibleBookMeta(5, "DEU", "신명기", "신", "Deuteronomy", "OT", "율법서", 34, 959, "deu"),
    BibleBookMeta(6, "JOS", "여호수아", "수", "Joshua", "OT", "역사서", 24, 658, "jos"),
    BibleBookMeta(7, "JDG", "사사기", "삿", "Judges", "OT", "역사서", 21, 618, "jdg"),
    BibleBookMeta(8, "RUT", "룻기", "룻", "Ruth", "OT", "역사서", 4, 85, "rut"),
    BibleBookMeta(9, "1SA", "사무엘상", "삼상", "1 Samuel", "OT", "역사서", 31, 810, "1sa"),
    BibleBookMeta(10, "2SA", "사무엘하", "삼하", "2 Samuel", "OT", "역사서", 24, 695, "2sa"),
    BibleBookMeta(11, "1KI", "열왕기상", "왕상", "1 Kings", "OT", "역사서", 22, 816, "1ki"),
    BibleBookMeta(12, "2KI", "열왕기하", "왕하", "2 Kings", "OT", "역사서", 25, 719, "2ki"),
    BibleBookMeta(13, "1CH", "역대상", "대상", "1 Chronicles", "OT", "역사서", 29, 942, "1ch"),
    BibleBookMeta(14, "2CH", "역대하", "대하", "2 Chronicles", "OT", "역사서", 36, 822, "2ch"),
    BibleBookMeta(15, "EZR", "에스라", "스", "Ezra", "OT", "역사서", 10, 280, "ezr"),
    BibleBookMeta(16, "NEH", "느헤미야", "느", "Nehemiah", "OT", "역사서", 13, 406, "neh"),
    BibleBookMeta(17, "EST", "에스더", "에", "Esther", "OT", "역사서", 10, 167, "est"),
    BibleBookMeta(18, "JOB", "욥기", "욥", "Job", "OT", "시가서", 42, 1070, "job"),
    BibleBookMeta(19, "PSA", "시편", "시", "Psalms", "OT", "시가서", 150, 2461, "psa"),
    BibleBookMeta(20, "PRO", "잠언", "잠", "Proverbs", "OT", "시가서", 31, 915, "pro"),
    BibleBookMeta(21, "ECC", "전도서", "전", "Ecclesiastes", "OT", "시가서", 12, 222, "ecc"),
    BibleBookMeta(22, "SNG", "아가", "아", "Song of Solomon", "OT", "시가서", 8, 117, "sng"),
    BibleBookMeta(23, "ISA", "이사야", "사", "Isaiah", "OT", "대예언서", 66, 1292, "isa"),
    BibleBookMeta(24, "JER", "예레미야", "렘", "Jeremiah", "OT", "대예언서", 52, 1364, "jer"),
    BibleBookMeta(25, "LAM", "예레미야애가", "애", "Lamentations", "OT", "대예언서", 5, 154, "lam"),
    BibleBookMeta(26, "EZK", "에스겔", "겔", "Ezekiel", "OT", "대예언서", 48, 1273, "ezk"),
    BibleBookMeta(27, "DAN", "다니엘", "단", "Daniel", "OT", "대예언서", 12, 357, "dan"),
    BibleBookMeta(28, "HOS", "호세아", "호", "Hosea", "OT", "소예언서", 14, 197, "hos"),
    BibleBookMeta(29, "JOL", "요엘", "욜", "Joel", "OT", "소예언서", 3, 73, "jol"),
    BibleBookMeta(30, "AMO", "아모스", "암", "Amos", "OT", "소예언서", 9, 146, "amo"),
    BibleBookMeta(31, "OBA", "오바댜", "옵", "Obadiah", "OT", "소예언서", 1, 21, "oba"),
    BibleBookMeta(32, "JON", "요나", "욘", "Jonah", "OT", "소예언서", 4, 48, "jnh"),
    BibleBookMeta(33, "MIC", "미가", "미", "Micah", "OT", "소예언서", 7, 105, "mic"),
    BibleBookMeta(34, "NAM", "나훔", "나", "Nahum", "OT", "소예언서", 3, 47, "nam"),
    BibleBookMeta(35, "HAB", "하박국", "합", "Habakkuk", "OT", "소예언서", 3, 56, "hab"),
    BibleBookMeta(36, "ZEP", "스바냐", "습", "Zephaniah", "OT", "소예언서", 3, 53, "zep"),
    BibleBookMeta(37, "HAG", "학개", "학", "Haggai", "OT", "소예언서", 2, 38, "hag"),
    BibleBookMeta(38, "ZEC", "스가랴", "슥", "Zechariah", "OT", "소예언서", 14, 211, "zec"),
    BibleBookMeta(39, "MAL", "말라기", "말", "Malachi", "OT", "소예언서", 4, 55, "mal"),
    # New Testament (27)
    BibleBookMeta(40, "MAT", "마태복음", "마", "Matthew", "NT", "복음서", 28, 1071, "mat"),
    BibleBookMeta(41, "MRK", "마가복음", "막", "Mark", "NT", "복음서", 16, 678, "mrk"),
    BibleBookMeta(42, "LUK", "누가복음", "눅", "Luke", "NT", "복음서", 24, 1151, "luk"),
    BibleBookMeta(43, "JHN", "요한복음", "요", "John", "NT", "복음서", 21, 879, "jhn"),
    BibleBookMeta(44, "ACT", "사도행전", "행", "Acts", "NT", "역사서", 28, 1007, "act"),
    BibleBookMeta(45, "ROM", "로마서", "롬", "Romans", "NT", "바울서신", 16, 433, "rom"),
    BibleBookMeta(46, "1CO", "고린도전서", "고전", "1 Corinthians", "NT", "바울서신", 16, 437, "1co"),
    BibleBookMeta(47, "2CO", "고린도후서", "고후", "2 Corinthians", "NT", "바울서신", 13, 256, "2co"),
    BibleBookMeta(48, "GAL", "갈라디아서", "갈", "Galatians", "NT", "바울서신", 6, 149, "gal"),
    BibleBookMeta(49, "EPH", "에베소서", "엡", "Ephesians", "NT", "바울서신", 6, 155, "eph"),
    BibleBookMeta(50, "PHP", "빌립보서", "빌", "Philippians", "NT", "바울서신", 4, 104, "php"),
    BibleBookMeta(51, "COL", "골로새서", "골", "Colossians", "NT", "바울서신", 4, 95, "col"),
    BibleBookMeta(52, "1TH", "데살로니가전서", "살전", "1 Thessalonians", "NT", "바울서신", 5, 89, "1th"),
    BibleBookMeta(53, "2TH", "데살로니가후서", "살후", "2 Thessalonians", "NT", "바울서신", 3, 47, "2th"),
    BibleBookMeta(54, "1TI", "디모데전서", "딤전", "1 Timothy", "NT", "바울서신", 6, 113, "1ti"),
    BibleBookMeta(55, "2TI", "디모데후서", "딤후", "2 Timothy", "NT", "바울서신", 4, 83, "2ti"),
    BibleBookMeta(56, "TIT", "디도서", "딛", "Titus", "NT", "바울서신", 3, 46, "tit"),
    BibleBookMeta(57, "PHM", "빌레몬서", "몬", "Philemon", "NT", "바울서신", 1, 25, "phm"),
    BibleBookMeta(58, "HEB", "히브리서", "히", "Hebrews", "NT", "공동서신", 13, 303, "heb"),
    BibleBookMeta(59, "JAS", "야고보서", "약", "James", "NT", "공동서신", 5, 108, "jas"),
    BibleBookMeta(60, "1PE", "베드로전서", "벧전", "1 Peter", "NT", "공동서신", 5, 105, "1pe"),
    BibleBookMeta(61, "2PE", "베드로후서", "벧후", "2 Peter", "NT", "공동서신", 3, 61, "2pe"),
    BibleBookMeta(62, "1JN", "요한일서", "요일", "1 John", "NT", "공동서신", 5, 105, "1jn"),
    BibleBookMeta(63, "2JN", "요한이서", "요이", "2 John", "NT", "공동서신", 1, 13, "2jn"),
    BibleBookMeta(64, "3JN", "요한삼서", "요삼", "3 John", "NT", "공동서신", 1, 15, "3jn"),
    BibleBookMeta(65, "JUD", "유다서", "유", "Jude", "NT", "공동서신", 1, 25, "jud"),
    BibleBookMeta(66, "REV", "요한계시록", "계", "Revelation", "NT", "예언서", 22, 404, "rev"),
)

BOOKS_BY_ID: Dict[int, BibleBookMeta] = {b.book_id: b for b in BIBLE_BOOKS}
BOOKS_BY_OSIS: Dict[str, BibleBookMeta] = {b.osis_code: b for b in BIBLE_BOOKS}
BOOKS_BY_CLEAN_EN: Dict[str, BibleBookMeta] = {b.name_en.replace(" ", ""): b for b in BIBLE_BOOKS}

# 8 Commentary Sources — strictly scholarly & non-sectarian descriptions
COMMENTARY_SOURCES_MASTER: List[Dict[str, object]] = [
    {
        "code": "OXFORD",
        "name_kr": "옥스포드 원어성경대전",
        "name_en": "Oxford Original Language Commentary",
        "author": "제자원",
        "description": "구절별 히브리어·헬라어 원어 정밀 분해, 어근, 문법 분석 및 원어 강해",
        "theological_stance": "원어 문법·역사 강해",
        "is_public_domain": False,
        "access_type": "LICENSED_LOCAL",
        "sort_order": 1,
    },
    {
        "code": "WESLEY",
        "name_kr": "존 웨슬리 성경 주석",
        "name_en": "John Wesley's Explanatory Notes",
        "author": "존 웨슬리 (John Wesley)",
        "description": "18세기 복음주의 부흥운동의 관점에서 본문의 성화, 은혜, 실천적 경건을 간결하게 해설",
        "theological_stance": "웨슬리안 / 실천적 성화",
        "is_public_domain": True,
        "access_type": "PUBLIC_DOMAIN",
        "sort_order": 2,
    },
    {
        "code": "HOKMA",
        "name_kr": "호크마 종합주석",
        "name_en": "Hokma Comprehensive Commentary",
        "author": "호크마 편집위원회",
        "description": "구절별 문맥, 원어 참고, 신구약 병행 구절을 종합적으로 정리한 주석",
        "theological_stance": "복음주의 종합 주해",
        "is_public_domain": False,
        "access_type": "LICENSED_LOCAL",
        "sort_order": 3,
    },
    {
        "code": "GRAND",
        "name_kr": "그랜드 종합주석",
        "name_en": "Grand Expository Commentary",
        "author": "그랜드 편찬위원회",
        "description": "강해 설교 대지 구성(서론-본론-결론)과 목회적 적용에 초점을 맞춘 주석",
        "theological_stance": "강해 설교학 / 목회 적용",
        "is_public_domain": False,
        "access_type": "LICENSED_LOCAL",
        "sort_order": 4,
    },
    {
        "code": "CHARISMA",
        "name_kr": "카리스마 성경 주석",
        "name_en": "Charisma Study Commentary",
        "author": "카리스마 편집부",
        "description": "성령의 사역, 기도와 영적 분별, 공동체 세움의 관점에서 본문을 조명하는 주석",
        "theological_stance": "성령론 / 실천 목회",
        "is_public_domain": False,
        "access_type": "LICENSED_LOCAL",
        "sort_order": 5,
    },
    {
        "code": "MATTHEW_HENRY",
        "name_kr": "매튜 헨리 신구약 주석",
        "name_en": "Matthew Henry's Complete Commentary",
        "author": "매튜 헨리 (Matthew Henry)",
        "description": "경건과 묵상, 설교적 적용이 풍부한 18세기 고전 완역 주석",
        "theological_stance": "청교도 경건·묵상 주해",
        "is_public_domain": True,
        "access_type": "PUBLIC_DOMAIN",
        "sort_order": 6,
    },
    {
        "code": "BAKER",
        "name_kr": "베이커 성경배경주석",
        "name_en": "Baker Illustrated Bible Background Commentary",
        "author": "Baker Academic",
        "description": "고대 근동(ANE) 문화, 제2성전기 유대교 풍습, 로마-그리스 고고학 및 지리 배경",
        "theological_stance": "역사·문화·고고학 배경",
        "is_public_domain": False,
        "access_type": "LICENSED_LOCAL",
        "sort_order": 7,
    },
    {
        "code": "ESV_EXPOSITORY",
        "name_kr": "ESV 성경해설주석",
        "name_en": "ESV Expository Commentary",
        "author": "Crossway / 복음주의 신학자 공저",
        "description": "성경신학적·구속사적 흐름 속에서 각 책의 구조와 본문을 명쾌하게 해설",
        "theological_stance": "구속사적 성경신학",
        "is_public_domain": False,
        "access_type": "LICENSED_LOCAL",
        "sort_order": 8,
    },
]

BIBLE_VERSIONS_MASTER: List[Tuple[str, str, str, str, int, int, str]] = [
    ("KRV", "개역한글", "Korean Revised Version (1961)", "KOREAN", 0, 1, "Korean Revised Version © Korean Bible Society 1961 (저작권 보호기간 만료, 출처 및 동일성 유지권 존중)"),
    ("GAE", "개역개정", "Korean Revised Version (4th Ed)", "KOREAN", 0, 0, "대한성서공회 저작권 (로컬 개인 연구용)"),
    ("KJV", "킹제임스 흠정역", "King James Version (1611)", "ENGLISH", 0, 0, "Public Domain"),
    ("ASV", "미국표준역", "American Standard Version (1901)", "ENGLISH", 0, 0, "Public Domain"),
    ("BHS", "히브리어 맛소라", "Biblia Hebraica Stuttgartensia", "HEBREW", 1, 0, "Public Domain / Open Morphology"),
    ("GNT", "신약 헬라어 원전", "Greek New Testament", "GREEK", 1, 0, "Public Domain / SBLGNT"),
]


def calculate_verse_id(book_id: int, chapter: int, verse: int) -> int:
    """Calculate canonical 7-8 digit integer Verse ID: book*1,000,000 + chapter*1,000 + verse."""
    if not (1 <= book_id <= 66):
        raise ValueError(f"book_id out of range (1..66): {book_id}")
    if not (1 <= chapter <= 150):
        raise ValueError(f"chapter out of range (1..150): {chapter}")
    if not (1 <= verse <= 200):
        raise ValueError(f"verse out of range (1..200): {verse}")
    return (book_id * 1_000_000) + (chapter * 1_000) + verse


def parse_verse_id(verse_id: int) -> Tuple[int, int, int]:
    """Decode canonical integer Verse ID into (book_id, chapter, verse)."""
    book_id = verse_id // 1_000_000
    chapter = (verse_id % 1_000_000) // 1_000
    verse = verse_id % 1_000
    return book_id, chapter, verse


def resolve_book(identifier: int | str) -> Optional[BibleBookMeta]:
    """Resolve a book by book_id, OSIS, Korean full/abbr name, English name, or BSKorea code."""
    if isinstance(identifier, int):
        return BOOKS_BY_ID.get(identifier)
    raw = str(identifier).strip()
    if not raw:
        return None
    if raw.isdigit():
        return BOOKS_BY_ID.get(int(raw))
    upper = raw.upper()
    lower = raw.lower()
    clean_en = raw.replace(" ", "")
    if upper in BOOKS_BY_OSIS:
        return BOOKS_BY_OSIS[upper]
    if clean_en in BOOKS_BY_CLEAN_EN:
        return BOOKS_BY_CLEAN_EN[clean_en]
    for b in BIBLE_BOOKS:
        if raw in (b.name_kr, b.name_kr_abbr) or lower in (b.bskorea_code, b.name_en.lower()):
            return b
    return None
