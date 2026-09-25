"""
Database Schema Definition and DDL for Biblical Exegesis & Commentary Pastoral Workstation.
Designed for Drift (Flutter ORM) and SQLite FTS5.
Optimized for 8 Commentaries, Multi-Bible Versions, Strong's Lexicon,
Treasury of Scripture Knowledge (TSK) Cross References, and Entity Chain References.
"""

from typing import List, Dict, Any

# Bible 66 Books Master Definition (1-indexed, OT: 1-39, NT: 40-66)
BIBLE_BOOKS_MASTER = [
    # 구약 (Old Testament 39권)
    (1, "GEN", "창세기", "창", "Genesis", "OT", "율법서", 50, 1533),
    (2, "EXO", "출애굽기", "출", "Exodus", "OT", "율법서", 40, 1213),
    (3, "LEV", "레위기", "레", "Leviticus", "OT", "율법서", 27, 859),
    (4, "NUM", "민수기", "민", "Numbers", "OT", "율법서", 36, 1288),
    (5, "DEU", "신명기", "신", "Deuteronomy", "OT", "율법서", 34, 959),
    (6, "JOS", "여호수아", "수", "Joshua", "OT", "역사서", 24, 658),
    (7, "JDG", "사사기", "삿", "Judges", "OT", "역사서", 21, 618),
    (8, "RUT", "룻기", "룻", "Ruth", "OT", "역사서", 4, 85),
    (9, "1SA", "사무엘상", "삼상", "1 Samuel", "OT", "역사서", 31, 810),
    (10, "2SA", "사무엘하", "삼하", "2 Samuel", "OT", "역사서", 24, 695),
    (11, "1KI", "열왕기상", "왕상", "1 Kings", "OT", "역사서", 22, 816),
    (12, "2KI", "열왕기하", "왕하", "2 Kings", "OT", "역사서", 25, 719),
    (13, "1CH", "역대상", "대상", "1 Chronicles", "OT", "역사서", 29, 942),
    (14, "2CH", "역대하", "대하", "2 Chronicles", "OT", "역사서", 36, 822),
    (15, "EZR", "에스라", "스", "Ezra", "OT", "역사서", 10, 280),
    (16, "NEH", "느헤미야", "느", "Nehemiah", "OT", "역사서", 13, 406),
    (17, "EST", "에스더", "에", "Esther", "OT", "역사서", 10, 167),
    (18, "JOB", "욥기", "욥", "Job", "OT", "시가서", 42, 1070),
    (19, "PSA", "시편", "시", "Psalms", "OT", "시가서", 150, 2461),
    (20, "PRO", "잠언", "잠", "Proverbs", "OT", "시가서", 31, 915),
    (21, "ECC", "전도서", "전", "Ecclesiastes", "OT", "시가서", 12, 222),
    (22, "SNG", "아가", "아", "Song of Solomon", "OT", "시가서", 8, 117),
    (23, "ISA", "이사야", "사", "Isaiah", "OT", "대예언서", 66, 1292),
    (24, "JER", "예레미야", "렘", "Jeremiah", "OT", "대예언서", 52, 1364),
    (25, "LAM", "예레미야애가", "애", "Lamentations", "OT", "대예언서", 5, 66),
    (26, "EZK", "에스겔", "겔", "Ezekiel", "OT", "대예언서", 48, 1273),
    (27, "DAN", "다니엘", "단", "Daniel", "OT", "대예언서", 12, 357),
    (28, "HOS", "호세아", "호", "Hosea", "OT", "소예언서", 14, 197),
    (29, "JOL", "요엘", "욜", "Joel", "OT", "소예언서", 3, 73),
    (30, "AMO", "아모스", "암", "Amos", "OT", "소예언서", 9, 146),
    (31, "OBA", "오바댜", "옵", "Obadiah", "OT", "소예언서", 1, 21),
    (32, "JON", "요나", "욘", "Jonah", "OT", "소예언서", 4, 48),
    (33, "MIC", "미가", "미", "Micah", "OT", "소예언서", 7, 105),
    (34, "NAM", "나훔", "나", "Nahum", "OT", "소예언서", 3, 47),
    (35, "HAB", "하박국", "합", "Habakkuk", "OT", "소예언서", 3, 56),
    (36, "ZEP", "스바냐", "습", "Zephaniah", "OT", "소예언서", 3, 53),
    (37, "HAG", "학개", "학", "Haggai", "OT", "소예언서", 2, 38),
    (38, "ZEC", "스가랴", "슥", "Zechariah", "OT", "소예언서", 14, 211),
    (39, "MAL", "말라기", "말", "Malachi", "OT", "소예언서", 4, 55),
    # 신약 (New Testament 27권)
    (40, "MAT", "마태복음", "마", "Matthew", "NT", "복음서", 28, 1071),
    (41, "MRK", "마가복음", "막", "Mark", "NT", "복음서", 16, 678),
    (42, "LUK", "누가복음", "눅", "Luke", "NT", "복음서", 24, 1151),
    (43, "JHN", "요한복음", "요", "John", "NT", "복음서", 21, 879),
    (44, "ACT", "사도행전", "행", "Acts", "NT", "역사서", 28, 1007),
    (45, "ROM", "로마서", "롬", "Romans", "NT", "바울서신", 16, 433),
    (46, "1CO", "고린도전서", "고전", "1 Corinthians", "NT", "바울서신", 16, 437),
    (47, "2CO", "고린도후서", "고후", "2 Corinthians", "NT", "바울서신", 13, 257),
    (48, "GAL", "갈라디아서", "갈", "Galatians", "NT", "바울서신", 6, 149),
    (49, "EPH", "에베소서", "엡", "Ephesians", "NT", "바울서신", 6, 155),
    (50, "PHP", "빌립보서", "빌", "Philippians", "NT", "바울서신", 4, 104),
    (51, "COL", "골로새서", "골", "Colossians", "NT", "바울서신", 4, 95),
    (52, "1TH", "데살로니가전서", "살전", "1 Thessalonians", "NT", "바울서신", 5, 89),
    (53, "2TH", "데살로니가후서", "살후", "2 Thessalonians", "NT", "바울서신", 3, 47),
    (54, "1TI", "디모데전서", "딤전", "1 Timothy", "NT", "바울서신", 6, 113),
    (55, "2TI", "디모데후서", "딤후", "2 Timothy", "NT", "바울서신", 4, 83),
    (56, "TIT", "디도서", "딛", "Titus", "NT", "바울서신", 3, 46),
    (57, "PHM", "빌레몬서", "몬", "Philemon", "NT", "바울서신", 1, 25),
    (58, "HEB", "히브리서", "히", "Hebrews", "NT", "공동서신", 13, 303),
    (59, "JAS", "야고보서", "약", "James", "NT", "공동서신", 5, 108),
    (60, "1PE", "베드로전서", "벧전", "1 Peter", "NT", "공동서신", 5, 105),
    (61, "2PE", "베드로후서", "벧후", "2 Peter", "NT", "공동서신", 3, 61),
    (62, "1JN", "요한일서", "요일", "1 John", "NT", "공동서신", 5, 105),
    (63, "2JN", "요한이서", "요이", "2 John", "NT", "공동서신", 1, 13),
    (64, "3JN", "요한삼서", "요삼", "3 John", "NT", "공동서신", 1, 14),
    (65, "JUD", "유다서", "유", "Jude", "NT", "공동서신", 1, 25),
    (66, "REV", "요한계시록", "계", "Revelation", "NT", "예언서", 22, 404),
]

# 8 Commentary Sources Metadata
COMMENTARY_SOURCES_MASTER = [
    {
        "code": "OXFORD",
        "name_kr": "옥스포드 원어성경대전",
        "name_en": "Oxford Original Language Commentary",
        "author": "제자원",
        "description": "구절별 히브리어·헬라어 원어 정밀 분해, 어근, 문법 분석 및 심층 원어 강해",
        "theological_stance": "보수 복음주의 / 원어 문법 강해",
        "is_public_domain": False,
        "access_type": "PROPRIETARY_MEMBER",
        "sort_order": 1,
    },
    {
        "code": "WESLEY",
        "name_kr": "존 웨슬리 성경 주석",
        "name_en": "John Wesley's Explanatory Notes",
        "author": "존 웨슬리 (John Wesley)",
        "description": "기독교대한성결교회의 뿌리인 아르미니안-웨슬리안 성결 신학의 정수, 성화와 완전성결 강조",
        "theological_stance": "웨슬리안 / 성결 신학",
        "is_public_domain": True,
        "access_type": "PUBLIC_DOMAIN",
        "sort_order": 2,
    },
    {
        "code": "HOKMA",
        "name_kr": "호크마 종합주석",
        "name_en": "Hokma Comprehensive Commentary",
        "author": "호크마 편집위원회",
        "description": "한국 목회 현장에서 가장 광범위하게 검증된 구절별 종합 해설, 문맥 및 역사적 조명",
        "theological_stance": "정통 보수 복음주의",
        "is_public_domain": False,
        "access_type": "PROPRIETARY_MEMBER",
        "sort_order": 3,
    },
    {
        "code": "GRAND",
        "name_kr": "그랜드 종합주석",
        "name_en": "Grand Expository Commentary",
        "author": "그랜드 편찬위원회",
        "description": "설교 대지 구성(서론-본론-결론) 및 목회적 실천 적용에 특화된 설교자용 주석",
        "theological_stance": "복음주의 목회 설교학",
        "is_public_domain": False,
        "access_type": "PROPRIETARY_MEMBER",
        "sort_order": 4,
    },
    {
        "code": "CHARISMA",
        "name_kr": "카리스마 성경/주석",
        "name_en": "Charisma Study Commentary",
        "author": "카리스마 편집부",
        "description": "성령의 임재, 신유, 은사와 영적 전쟁, 성결의 능력 사역에 초점을 둔 주석",
        "theological_stance": "오순절 / 성령론 / 은사주의 / 성결 실천",
        "is_public_domain": False,
        "access_type": "PROPRIETARY_MEMBER",
        "sort_order": 5,
    },
    {
        "code": "MATTHEW_HENRY",
        "name_kr": "매튜 헨리 신구약 주석",
        "name_en": "Matthew Henry's Complete Commentary",
        "author": "매튜 헨리 (Matthew Henry)",
        "description": "경건과 묵상, 설교적 감화력이 탁월하여 수세기 동안 전세계 목회자들에게 사랑받은 고전",
        "theological_stance": "개혁주의 청교도 / 실천적 경건",
        "is_public_domain": True,
        "access_type": "PUBLIC_DOMAIN",
        "sort_order": 6,
    },
    {
        "code": "BAKER",
        "name_kr": "베이커 성경배경주석",
        "name_en": "Baker Illustrated Bible Background Commentary",
        "author": "Baker Academic",
        "description": "고대 근동(ANE) 문화, 제2성전기 유대교 풍습, 로마-그리스 고고학적 배경과 지리",
        "theological_stance": "역사-문법적 배경학",
        "is_public_domain": False,
        "access_type": "PROPRIETARY_MEMBER",
        "sort_order": 7,
    },
    {
        "code": "ESV_EXPOSITORY",
        "name_kr": "ESV 성경해설주석",
        "name_en": "ESV Expository Commentary",
        "author": "Crossway / 복음주의 신학자 공저",
        "description": "현대 복음주의 학자들의 명쾌한 본문 강해 및 구속사적 성경신학 적용",
        "theological_stance": "현대 복음주의 / 구속사적 성경신학",
        "is_public_domain": False,
        "access_type": "PROPRIETARY_MEMBER",
        "sort_order": 8,
    },
]
# SQLite DDL Statements
SQLITE_DDL_STATEMENTS = [
    # 1. 성경 66권 메타데이터 테이블
    """
    CREATE TABLE IF NOT EXISTS bible_books (
        book_id INTEGER PRIMARY KEY,
        osis_code TEXT NOT NULL UNIQUE,
        name_kr TEXT NOT NULL,
        name_kr_abbr TEXT NOT NULL,
        name_en TEXT NOT NULL,
        testament TEXT NOT NULL CHECK(testament IN ('OT', 'NT')),
        category TEXT NOT NULL,
        total_chapters INTEGER NOT NULL,
        total_verses INTEGER NOT NULL
    );
    """,
    # 2. 성경 역본 메타데이터 테이블
    """
    CREATE TABLE IF NOT EXISTS bible_versions (
        version_code TEXT PRIMARY KEY,
        name_kr TEXT NOT NULL,
        name_en TEXT NOT NULL,
        language TEXT NOT NULL,
        is_original_lang INTEGER NOT NULL DEFAULT 0,
        is_default INTEGER NOT NULL DEFAULT 0,
        copyright_notice TEXT
    );
    """,
    # 3. 성경 구절 본문 테이블 (verse_id = book*1000000 + ch*1000 + vs)
    """
    CREATE TABLE IF NOT EXISTS bible_verses (
        verse_id INTEGER NOT NULL,
        book_id INTEGER NOT NULL,
        chapter INTEGER NOT NULL,
        verse INTEGER NOT NULL,
        version_code TEXT NOT NULL,
        text TEXT NOT NULL,
        text_with_strong TEXT,
        created_at TEXT DEFAULT (datetime('now')),
        PRIMARY KEY (version_code, verse_id),
        FOREIGN KEY (book_id) REFERENCES bible_books(book_id),
        FOREIGN KEY (version_code) REFERENCES bible_versions(version_code)
    );
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_bible_verses_nav 
    ON bible_verses(version_code, book_id, chapter, verse);
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_bible_verses_range 
    ON bible_verses(version_code, verse_id);
    """,
    # 4. 성경 본문 FTS5 가상 테이블 (전문 검색용, unicode61 토크나이저)
    """
    CREATE VIRTUAL TABLE IF NOT EXISTS fts_bible_verses USING fts5(
        verse_id UNINDEXED,
        version_code UNINDEXED,
        text,
        tokenize = 'unicode61 remove_diacritics 2'
    );
    """,
    # 5. 8종 주석 출처 메타데이터 테이블
    """
    CREATE TABLE IF NOT EXISTS commentary_sources (
        source_code TEXT PRIMARY KEY,
        name_kr TEXT NOT NULL,
        name_en TEXT NOT NULL,
        author TEXT,
        description TEXT,
        theological_stance TEXT,
        is_public_domain INTEGER NOT NULL DEFAULT 0,
        access_type TEXT NOT NULL,
        sort_order INTEGER NOT NULL DEFAULT 99
    );
    """,
    # 6. 주석 본문 테이블 (단일 절 또는 여러 절 범위 포괄 지원)
    """
    CREATE TABLE IF NOT EXISTS commentaries (
        commentary_id INTEGER PRIMARY KEY AUTOINCREMENT,
        source_code TEXT NOT NULL,
        book_id INTEGER NOT NULL,
        chapter_start INTEGER NOT NULL,
        verse_start INTEGER NOT NULL,
        chapter_end INTEGER NOT NULL,
        verse_end INTEGER NOT NULL,
        verse_start_id INTEGER NOT NULL,
        verse_end_id INTEGER NOT NULL,
        passage_display TEXT NOT NULL,
        title TEXT,
        content_markdown TEXT NOT NULL,
        content_html TEXT,
        theological_tags TEXT,
        practical_points TEXT,
        created_at TEXT DEFAULT (datetime('now')),
        FOREIGN KEY (source_code) REFERENCES commentary_sources(source_code),
        FOREIGN KEY (book_id) REFERENCES bible_books(book_id)
    );
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_commentary_lookup 
    ON commentaries(source_code, verse_start_id, verse_end_id);
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_commentary_book_chap 
    ON commentaries(source_code, book_id, chapter_start);
    """,
    # 7. 주석 전문 검색 FTS5 테이블
    """
    CREATE VIRTUAL TABLE IF NOT EXISTS fts_commentaries USING fts5(
        commentary_id UNINDEXED,
        source_code UNINDEXED,
        passage_display,
        title,
        content_markdown,
        theological_tags,
        tokenize = 'unicode61 remove_diacritics 2'
    );
    """,
    # 8. 원어 스트롱코드 사전 테이블 (히브리어 H / 헬라어 G)
    """
    CREATE TABLE IF NOT EXISTS strong_lexicon (
        strong_id TEXT PRIMARY KEY,
        language TEXT NOT NULL CHECK(language IN ('HEBREW', 'GREEK', 'ARAMAIC')),
        lemma TEXT NOT NULL,
        transliteration TEXT,
        pronunciation TEXT,
        part_of_speech TEXT,
        definition_kr TEXT NOT NULL,
        definition_en TEXT,
        root_id TEXT,
        derivation TEXT,
        occurrence_count INTEGER DEFAULT 0
    );
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_strong_lang ON strong_lexicon(language);
    """,
    """
    CREATE VIRTUAL TABLE IF NOT EXISTS fts_strong_lexicon USING fts5(
        strong_id UNINDEXED,
        lemma,
        transliteration,
        definition_kr,
        definition_en,
        tokenize = 'unicode61 remove_diacritics 2'
    );
    """,
    # 9. 교차 관주 테이블 (TSK - Treasury of Scripture Knowledge 기반)
    """
    CREATE TABLE IF NOT EXISTS cross_references (
        ref_id INTEGER PRIMARY KEY AUTOINCREMENT,
        from_verse_id INTEGER NOT NULL,
        to_verse_id INTEGER NOT NULL,
        score REAL DEFAULT 1.0,
        relationship_type TEXT DEFAULT 'THEMATIC' CHECK(relationship_type IN ('QUOTATION', 'PARALLEL', 'THEMATIC', 'PROPHECY_FULFILLMENT', 'EXPLANATORY')),
        note TEXT
    );
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_cross_ref_from ON cross_references(from_verse_id, score DESC);
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_cross_ref_to ON cross_references(to_verse_id);
    """,
    # 10. 목회자 설교문 & 아카이브 테이블 (Drift 로컬 캐시 + Google Drive 동기화)
    """
    CREATE TABLE IF NOT EXISTS sermons (
        sermon_id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        preacher TEXT NOT NULL DEFAULT '박우호 목사',
        sermon_date TEXT NOT NULL,
        service_type TEXT NOT NULL DEFAULT '주일대예배',
        scripture_ref TEXT NOT NULL,
        passage_start_id INTEGER,
        passage_end_id INTEGER,
        series_title TEXT,
        target_duration_mins INTEGER DEFAULT 30,
        outline_json TEXT,
        full_text_markdown TEXT,
        pulpit_slides_json TEXT,
        tags TEXT,
        gdrive_file_id TEXT,
        sync_status TEXT DEFAULT 'SYNCED' CHECK(sync_status IN ('SYNCED', 'PENDING_UPLOAD', 'PENDING_DOWNLOAD', 'CONFLICT')),
        local_updated_at TEXT DEFAULT (datetime('now')),
        gdrive_synced_at TEXT
    );
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_sermons_date ON sermons(sermon_date DESC);
    """,
    # 13. 주석 스크랩 클립보드 (설교 준비 중 8종 주석에서 클릭 한 번으로 대지 스크랩)
    """
    CREATE TABLE IF NOT EXISTS sermon_clips (
        clip_id INTEGER PRIMARY KEY AUTOINCREMENT,
        sermon_id TEXT NOT NULL,
        source_type TEXT NOT NULL CHECK(source_type IN ('COMMENTARY', 'BIBLE', 'STRONG', 'CROSS_REF')),
        source_code TEXT,
        quote_text TEXT NOT NULL,
        commentary_title TEXT,
        pastor_note TEXT,
        target_outline_section TEXT,
        order_index INTEGER DEFAULT 0,
        created_at TEXT DEFAULT (datetime('now')),
        FOREIGN KEY (sermon_id) REFERENCES sermons(sermon_id) ON DELETE CASCADE
    );
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_sermon_clips ON sermon_clips(sermon_id, order_index);
    """
]

def calculate_verse_id(book_id: int, chapter: int, verse: int) -> int:
    """Calculate 7-8 digit unique integer Verse ID: (book * 1,000,000) + (chap * 1,000) + verse."""
    return (book_id * 1_000_000) + (chapter * 1_000) + verse

def parse_verse_id(verse_id: int) -> tuple[int, int, int]:
    """Parse integer Verse ID back into (book_id, chapter, verse)."""
    book_id = verse_id // 1_000_000
    chapter = (verse_id % 1_000_000) // 1_000
    verse = verse_id % 1_000
    return book_id, chapter, verse
