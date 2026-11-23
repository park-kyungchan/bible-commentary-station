"""
Single Source of Truth (SSOT) for the 66-Book Protestant Canon,
12 Official Authoritative Commentary Sources (grouped into 3 clear categories),
Bible Versions, and Verse ID Math.
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
    BibleBookMeta(9, "1SA", "사무엘상", "삼상", "1 Samuel", "OT", "역사서", 31, 809, "1sa"),
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
    BibleBookMeta(22, "SNG", "아가", "아", "Song of Solomon", "OT", "시가서", 8, 118, "sng"),
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

# 12 Official Authoritative Commentary Sources across 3 clear categories:
# - CLASSIC (고전·경건 주석)
# - ACADEMIC (원어·역사·학술 주석)
# - EXPOSITORY (강해·설교·종합 주석)
COMMENTARY_SOURCES_MASTER: List[Dict[str, object]] = [
    # 1. 고전·경건 주석 (Public Domain Official Classics)
    {
        "code": "MATTHEW_HENRY",
        "category": "CLASSIC",
        "category_kr": "고전·경건",
        "name_kr": "매튜 헨리 완역 주석",
        "name_en": "Matthew Henry's Complete Commentary (1706)",
        "author": "매튜 헨리 (Matthew Henry)",
        "description": "300년 넘게 전 세계 목회자와 성도가 사랑한 경건·묵상 주석의 고전 (CCEL 공공도메인)",
        "theological_stance": "청교도 경건·묵상 주해",
        "official_url": "https://www.ccel.org/ccel/henry/mhc",
        "is_public_domain": True,
        "access_type": "PUBLIC_DOMAIN",
        "sort_order": 1,
    },
    {
        "code": "CALVIN",
        "category": "CLASSIC",
        "category_kr": "고전·경건",
        "name_kr": "존 칼빈 성경 주석",
        "name_en": "John Calvin's Commentaries (45 Vols)",
        "author": "존 칼빈 (John Calvin)",
        "description": "성경 본문의 간결하고 명료한 역사-문법적 해석의 기준을 세운 종교개혁 고전 주석 (CCEL 공공도메인)",
        "theological_stance": "종교개혁·성경신학 고전",
        "official_url": "https://www.ccel.org/ccel/calvin",
        "is_public_domain": True,
        "access_type": "PUBLIC_DOMAIN",
        "sort_order": 2,
    },
    {
        "code": "WESLEY",
        "category": "CLASSIC",
        "category_kr": "고전·경건",
        "name_kr": "존 웨슬리 성경 주석",
        "name_en": "John Wesley's Explanatory Notes (1765)",
        "author": "존 웨슬리 (John Wesley)",
        "description": "은혜와 거룩한 삶, 실천적 성화를 명쾌하게 풀어낸 복음주의 고전 주석 (CCEL 공공도메인)",
        "theological_stance": "웨슬리안·실천적 성화",
        "official_url": "https://www.ccel.org/ccel/wesley/notes",
        "is_public_domain": True,
        "access_type": "PUBLIC_DOMAIN",
        "sort_order": 3,
    },
    {
        "code": "JFB",
        "category": "CLASSIC",
        "category_kr": "고전·경건",
        "name_kr": "제이미슨-포셋-브라운 주석",
        "name_en": "Jamieson-Fausset-Brown Commentary (1871)",
        "author": "R. Jamieson, A.R. Fausset, D. Brown",
        "description": "군더더기 없이 구절의 핵심 뜻과 병행 구절을 짚어주는 19세기 대표 간결 주석 (공공도메인)",
        "theological_stance": "보수 복음주의 간결 주해",
        "official_url": "https://biblehub.com/commentaries/jfb/",
        "is_public_domain": True,
        "access_type": "PUBLIC_DOMAIN",
        "sort_order": 4,
    },
    # 2. 원어·역사·학술 주석 (Exegetical & Historical Academic Series)
    {
        "code": "OXFORD",
        "category": "ACADEMIC",
        "category_kr": "원어·학술",
        "name_kr": "옥스포드 원어성경대전",
        "name_en": "Oxford Original Language Commentary",
        "author": "제자원 편찬",
        "description": "히브리어·헬라어 원어 어근, 문법 형태론 분해 및 구문 강해",
        "theological_stance": "원어 문법·어근 강해",
        "official_url": None,
        "is_public_domain": False,
        "access_type": "LICENSED_LOCAL",
        "sort_order": 5,
    },
    {
        "code": "NICOT_NICNT",
        "category": "ACADEMIC",
        "category_kr": "원어·학술",
        "name_kr": "NICOT / NICNT 신국제 주석",
        "name_en": "New International Commentary (OT/NT, Eerdmans)",
        "author": "Eerdmans 국제 신학자 공저",
        "description": "세계 복음주의권에서 가장 신뢰받는 표준 학술·목회 균형 주석 시리즈",
        "theological_stance": "국제 복음주의 표준 주해",
        "official_url": "https://bestcommentaries.com/series/new-international-commentary-on-the-new-testament-nicnt/",
        "is_public_domain": False,
        "access_type": "LICENSED_LOCAL",
        "sort_order": 6,
    },
    {
        "code": "WBC",
        "category": "ACADEMIC",
        "category_kr": "원어·학술",
        "name_kr": "WBC 워드 성경주석",
        "name_en": "Word Biblical Commentary (Zondervan)",
        "author": "Zondervan 국제 학자 공저",
        "description": "번역·본문비평·문학구조·구절주해·신학설명을 체계적으로 제시하는 최고급 학술 주석",
        "theological_stance": "원어·구조·본문비평 학술",
        "official_url": "https://bestcommentaries.com/series/word-biblical-commentary-wbc/",
        "is_public_domain": False,
        "access_type": "LICENSED_LOCAL",
        "sort_order": 7,
    },
    {
        "code": "BAKER",
        "category": "ACADEMIC",
        "category_kr": "원어·학술",
        "name_kr": "베이커 성경배경주석",
        "name_en": "Baker Illustrated Bible Background Commentary",
        "author": "Baker Academic",
        "description": "고대 근동 풍습, 제2성전기 유대교, 로마-그리스 역사·지리·고고학 배경 해설",
        "theological_stance": "역사·문화·고고학 배경",
        "official_url": "https://bakerpublishinggroup.com/",
        "is_public_domain": False,
        "access_type": "LICENSED_LOCAL",
        "sort_order": 8,
    },
    # 3. 강해·설교·종합 주석 (Expository & Pastoral Series)
    {
        "code": "CONSTABLE",
        "category": "EXPOSITORY",
        "category_kr": "강해·설교",
        "name_kr": "컨스터블 성경 강해 노트",
        "name_en": "Dr. Thomas Constable's Expository Notes (SonicLight)",
        "author": "토마스 컨스터블 (달라스 신학교)",
        "description": "전 66권의 문맥 흐름과 강해 대지를 쉽고 명쾌하게 정리한 공식 무료 공개 강해 주석",
        "theological_stance": "문맥 중심 강해 설교",
        "official_url": "https://planobiblechapel.org/constable-notes/",
        "is_public_domain": True,
        "access_type": "PUBLIC_DOMAIN",
        "sort_order": 9,
    },
    {
        "code": "ESV_EXPOSITORY",
        "category": "EXPOSITORY",
        "category_kr": "강해·설교",
        "name_kr": "ESV 성경해설주석",
        "name_en": "ESV Expository Commentary (Crossway)",
        "author": "Crossway 복음주의 학자 공저",
        "description": "구약에서 신약으로 이어지는 구속사적 성경신학 흐름 속에서 본문을 명쾌하게 해설",
        "theological_stance": "구속사적 성경신학 강해",
        "official_url": "https://www.crossway.org/",
        "is_public_domain": False,
        "access_type": "LICENSED_LOCAL",
        "sort_order": 10,
    },
    {
        "code": "HOKMA",
        "category": "EXPOSITORY",
        "category_kr": "강해·설교",
        "name_kr": "호크마 종합주석",
        "name_en": "Hokma Comprehensive Commentary",
        "author": "호크마 편집위원회",
        "description": "한국 교회에서 널리 쓰이는 구절별 종합 해설, 원어 참고 및 병행 구절 정리",
        "theological_stance": "한국 목회 종합 주해",
        "official_url": None,
        "is_public_domain": False,
        "access_type": "LICENSED_LOCAL",
        "sort_order": 11,
    },
    {
        "code": "GRAND",
        "category": "EXPOSITORY",
        "category_kr": "강해·설교",
        "name_kr": "그랜드 종합주석",
        "name_en": "Grand Expository Commentary",
        "author": "그랜드 편찬위원회",
        "description": "서론-본론-결론 3대지 설교 구성과 목회 현장 적용에 특화된 설교자용 주석",
        "theological_stance": "강해 설교 3대지·적용",
        "official_url": None,
        "is_public_domain": False,
        "access_type": "LICENSED_LOCAL",
        "sort_order": 12,
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
    if not (1 <= book_id <= 66):
        raise ValueError(f"book_id out of range (1..66): {book_id}")
    if not (1 <= chapter <= 150):
        raise ValueError(f"chapter out of range (1..150): {chapter}")
    if not (1 <= verse <= 200):
        raise ValueError(f"verse out of range (1..200): {verse}")
    return (book_id * 1_000_000) + (chapter * 1_000) + verse


def parse_verse_id(verse_id: int) -> Tuple[int, int, int]:
    book_id = verse_id // 1_000_000
    chapter = (verse_id % 1_000_000) // 1_000
    verse = verse_id % 1_000
    return book_id, chapter, verse


def resolve_book(identifier: int | str) -> Optional[BibleBookMeta]:
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


# Exact KRV (1961) per-chapter verse counts (66 books, 1,189 chapters, 31,102 verses).
KRV_CHAPTER_VERSE_COUNTS: Dict[str, Tuple[int, ...]] = {
    "1CH": (54, 55, 24, 43, 26, 81, 40, 40, 44, 14, 47, 40, 14, 17, 29, 43, 27, 17, 19, 8, 30, 19, 32, 31, 31, 32, 34, 21, 30),
    "1CO": (31, 16, 23, 21, 13, 20, 40, 13, 27, 33, 34, 31, 13, 40, 58, 24),
    "1JN": (10, 29, 24, 21, 21),
    "1KI": (53, 46, 28, 34, 18, 38, 51, 66, 28, 29, 43, 33, 34, 31, 34, 34, 24, 46, 21, 43, 29, 53),
    "1PE": (25, 25, 22, 19, 14),
    "1SA": (28, 36, 21, 22, 12, 21, 17, 22, 27, 27, 15, 25, 23, 52, 35, 23, 58, 30, 24, 42, 15, 23, 29, 22, 44, 25, 12, 25, 11, 30, 13),
    "1TH": (10, 20, 13, 18, 28),
    "1TI": (20, 15, 16, 16, 25, 21),
    "2CH": (17, 18, 17, 22, 14, 42, 22, 18, 31, 19, 23, 16, 22, 15, 19, 14, 19, 34, 11, 37, 20, 12, 21, 27, 28, 23, 9, 27, 36, 27, 21, 33, 25, 33, 27, 23),
    "2CO": (24, 17, 18, 18, 21, 18, 16, 24, 15, 18, 33, 21, 13),
    "2JN": (13,),
    "2KI": (18, 25, 27, 44, 27, 33, 20, 29, 37, 36, 21, 21, 25, 29, 38, 20, 41, 37, 37, 21, 26, 20, 37, 20, 30),
    "2PE": (21, 22, 18),
    "2SA": (27, 32, 39, 12, 25, 23, 29, 18, 13, 19, 27, 31, 39, 33, 37, 23, 29, 33, 43, 26, 22, 51, 39, 25),
    "2TH": (12, 17, 18),
    "2TI": (18, 26, 17, 22),
    "3JN": (15,),
    "ACT": (26, 47, 26, 37, 42, 15, 60, 40, 43, 48, 30, 25, 52, 28, 41, 40, 34, 28, 41, 38, 40, 30, 35, 27, 27, 32, 44, 31),
    "AMO": (15, 16, 15, 13, 27, 14, 17, 14, 15),
    "COL": (29, 23, 25, 18),
    "DAN": (21, 49, 30, 37, 31, 28, 28, 27, 27, 21, 45, 13),
    "DEU": (46, 37, 29, 49, 33, 25, 26, 20, 29, 22, 32, 32, 18, 29, 23, 22, 20, 22, 21, 20, 23, 30, 25, 22, 19, 19, 26, 68, 29, 20, 30, 52, 29, 12),
    "ECC": (18, 26, 22, 16, 20, 12, 29, 17, 18, 20, 10, 14),
    "EPH": (23, 22, 21, 32, 33, 24),
    "EST": (22, 23, 15, 17, 14, 14, 10, 17, 32, 3),
    "EXO": (22, 25, 22, 31, 23, 30, 25, 32, 35, 29, 10, 51, 22, 31, 27, 36, 16, 27, 25, 26, 36, 31, 33, 18, 40, 37, 21, 43, 46, 38, 18, 35, 23, 35, 35, 38, 29, 31, 43, 38),
    "EZK": (28, 10, 27, 17, 17, 14, 27, 18, 11, 22, 25, 28, 23, 23, 8, 63, 24, 32, 14, 49, 32, 31, 49, 27, 17, 21, 36, 26, 21, 26, 18, 32, 33, 31, 15, 38, 28, 23, 29, 49, 26, 20, 27, 31, 25, 24, 23, 35),
    "EZR": (11, 70, 13, 24, 17, 22, 28, 36, 15, 44),
    "GAL": (24, 21, 29, 31, 26, 18),
    "GEN": (31, 25, 24, 26, 32, 22, 24, 22, 29, 32, 32, 20, 18, 24, 21, 16, 27, 33, 38, 18, 34, 24, 20, 67, 34, 35, 46, 22, 35, 43, 55, 32, 20, 31, 29, 43, 36, 30, 23, 23, 57, 38, 34, 34, 28, 34, 31, 22, 33, 26),
    "HAB": (17, 20, 19),
    "HAG": (15, 23),
    "HEB": (14, 18, 19, 16, 14, 20, 28, 13, 28, 39, 40, 29, 25),
    "HOS": (11, 23, 5, 19, 15, 11, 16, 14, 17, 15, 12, 14, 16, 9),
    "ISA": (31, 22, 26, 6, 30, 13, 25, 22, 21, 34, 16, 6, 22, 32, 9, 14, 14, 7, 25, 6, 17, 25, 18, 23, 12, 21, 13, 29, 24, 33, 9, 20, 24, 17, 10, 22, 38, 22, 8, 31, 29, 25, 28, 28, 25, 13, 15, 22, 26, 11, 23, 15, 12, 17, 13, 12, 21, 14, 21, 22, 11, 12, 19, 12, 25, 24),
    "JAS": (27, 26, 18, 17, 20),
    "JER": (19, 37, 25, 31, 31, 30, 34, 22, 26, 25, 23, 17, 27, 22, 21, 21, 27, 23, 15, 18, 14, 30, 40, 10, 38, 24, 22, 17, 32, 24, 40, 44, 26, 22, 19, 32, 21, 28, 18, 16, 18, 22, 13, 30, 5, 28, 7, 47, 39, 46, 64, 34),
    "JOB": (22, 13, 26, 21, 27, 30, 21, 22, 35, 22, 20, 25, 28, 22, 35, 22, 16, 21, 29, 29, 34, 30, 17, 25, 6, 14, 23, 28, 25, 31, 40, 22, 33, 37, 16, 33, 24, 41, 30, 24, 34, 17),
    "JOL": (20, 32, 21),
    "JHN": (51, 25, 36, 54, 47, 71, 53, 59, 41, 42, 57, 50, 38, 31, 27, 33, 26, 40, 42, 31, 25),
    "JON": (17, 10, 10, 11),
    "JOS": (18, 24, 17, 24, 15, 27, 26, 35, 27, 43, 23, 24, 33, 15, 63, 10, 18, 28, 51, 9, 45, 34, 16, 33),
    "JUD": (25,),
    "JDG": (36, 23, 31, 24, 31, 40, 25, 35, 57, 18, 40, 15, 25, 20, 20, 31, 13, 31, 30, 48, 25),
    "LAM": (22, 22, 66, 22, 22),
    "LEV": (17, 16, 17, 35, 19, 30, 38, 36, 24, 20, 47, 8, 59, 57, 33, 34, 16, 30, 37, 27, 24, 33, 44, 23, 55, 46, 34),
    "LUK": (80, 52, 38, 44, 39, 49, 50, 56, 62, 42, 54, 59, 35, 35, 32, 31, 37, 43, 48, 47, 38, 71, 56, 53),
    "MAL": (14, 17, 18, 6),
    "MRK": (45, 28, 35, 41, 43, 56, 37, 38, 50, 52, 33, 44, 37, 72, 47, 20),
    "MAT": (25, 23, 17, 25, 48, 34, 29, 34, 38, 42, 30, 50, 58, 36, 39, 28, 27, 35, 30, 34, 46, 46, 39, 51, 46, 75, 66, 20),
    "MIC": (16, 13, 12, 13, 15, 16, 20),
    "NAM": (15, 13, 19),
    "NEH": (11, 20, 32, 23, 19, 19, 73, 18, 38, 39, 36, 47, 31),
    "NUM": (54, 34, 51, 49, 31, 27, 89, 26, 23, 36, 35, 16, 33, 45, 41, 50, 13, 32, 22, 29, 35, 41, 30, 25, 18, 65, 23, 31, 40, 16, 54, 42, 56, 29, 34, 13),
    "OBA": (21,),
    "PHM": (25,),
    "PHP": (30, 30, 21, 23),
    "PRO": (33, 22, 35, 27, 23, 35, 27, 36, 18, 32, 31, 28, 25, 35, 33, 33, 28, 24, 29, 30, 31, 29, 35, 34, 28, 28, 27, 28, 27, 33, 31),
    "PSA": (6, 12, 8, 8, 12, 10, 17, 9, 20, 18, 7, 8, 6, 7, 5, 11, 15, 50, 14, 9, 13, 31, 6, 10, 22, 12, 14, 9, 11, 12, 24, 11, 22, 22, 28, 12, 40, 22, 13, 17, 13, 11, 5, 26, 17, 11, 9, 14, 20, 23, 19, 9, 6, 7, 23, 13, 11, 11, 17, 12, 8, 12, 11, 10, 13, 20, 7, 35, 36, 5, 24, 20, 28, 23, 10, 12, 20, 72, 13, 19, 16, 8, 18, 12, 13, 17, 7, 18, 52, 17, 16, 15, 5, 23, 11, 13, 12, 9, 9, 5, 8, 28, 22, 35, 45, 48, 43, 13, 31, 7, 10, 10, 9, 8, 18, 19, 2, 29, 176, 7, 8, 9, 4, 8, 5, 6, 5, 6, 8, 8, 3, 18, 3, 3, 21, 26, 9, 8, 24, 13, 10, 7, 12, 15, 21, 10, 20, 14, 9, 6),
    "REV": (20, 29, 22, 11, 14, 17, 17, 13, 21, 11, 19, 17, 18, 20, 8, 21, 18, 24, 21, 15, 27, 21),
    "ROM": (32, 29, 31, 25, 21, 23, 25, 39, 33, 21, 36, 21, 14, 23, 33, 27),
    "RUT": (22, 23, 18, 22),
    "SNG": (17, 17, 11, 16, 16, 14, 13, 14),
    "TIT": (16, 15, 15),
    "ZEC": (21, 13, 10, 14, 11, 15, 14, 23, 17, 12, 17, 14, 9, 21),
    "ZEP": (18, 15, 20),
}


def get_chapter_verse_count(book_identifier: int | str, chapter: int) -> Optional[int]:
    """Return exact KRV (1961) verse count for a given book and 1-based chapter."""
    meta = resolve_book(book_identifier)
    if not meta:
        return None
    counts = KRV_CHAPTER_VERSE_COUNTS.get(meta.osis_code)
    if not counts or not (1 <= chapter <= len(counts)):
        return None
    return counts[chapter - 1]
