"""
Full Bible (66 Books, 1,189 Chapters, 31,102 Verses) Ingestion Script.
Populates bible_pastoral_core.db with complete KRV text and synchronizes FTS5 index.
"""

import os
import sys
import json
import time
import sqlite3

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from schema import (
    BIBLE_BOOKS_MASTER,
    COMMENTARY_SOURCES_MASTER,
    SQLITE_DDL_STATEMENTS,
    calculate_verse_id
)
from parsers.commentary_parser import CommentaryParser
from parsers.strong_parser import StrongParser
from parsers.cross_ref_parser import CrossRefParser
from collectors.open_data_collector import OpenDataCollector


def ingest_full_bible(db_path: str = os.path.join(CURRENT_DIR, "bible_pastoral_core.db")):
    print(f"=== Starting Full Bible Ingestion into: {db_path} ===")
    t_start = time.perf_counter()

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    conn.execute("PRAGMA page_size = 4096;")
    conn.execute("PRAGMA cache_size = -64000;")
    conn.execute("PRAGMA foreign_keys = ON;")

    # 1. Initialize schema
    print("1. Initializing schema...")
    with conn:
        for ddl in SQLITE_DDL_STATEMENTS:
            conn.execute(ddl)

    # 2. Seed Master Data (66 Books, Versions, 8 Commentaries)
    print("2. Seeding Master Data...")
    with conn:
        conn.executemany(
            """
            INSERT OR REPLACE INTO bible_books
            (book_id, osis_code, name_kr, name_kr_abbr, name_en, testament, category, total_chapters, total_verses)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            BIBLE_BOOKS_MASTER
        )

        versions = [
            ("KRV", "개역한글", "Korean Revised Version (1961)", "KOREAN", 0, 1, "Copyright term expired; attribution and integrity rights remain"),
            ("GAE", "개역개정", "Korean Revised Version (4th Ed)", "KOREAN", 0, 0, "대한성서공회 저작권"),
            ("KJV", "킹제임스 흠정역", "King James Version (1611)", "ENGLISH", 0, 0, "Public Domain"),
            ("ASV", "미국표준역", "American Standard Version (1901)", "ENGLISH", 0, 0, "Public Domain"),
            ("BHS", "히브리어 맛소라", "Biblia Hebraica Stuttgartensia", "HEBREW", 1, 0, "Public Domain Text"),
            ("GNT", "신약 헬라어 원전", "Greek New Testament", "GREEK", 1, 0, "Public Domain Text")
        ]
        conn.executemany(
            """
            INSERT OR REPLACE INTO bible_versions
            (version_code, name_kr, name_en, language, is_original_lang, is_default, copyright_notice)
            VALUES (?, ?, ?, ?, ?, ?, ?);
            """,
            versions
        )

        source_tuples = [
            (
                s["code"], s["name_kr"], s["name_en"], s["author"],
                s["description"], s["theological_stance"],
                1 if s["is_public_domain"] else 0,
                s["access_type"], s["sort_order"]
            )
            for s in COMMENTARY_SOURCES_MASTER
        ]
        conn.executemany(
            """
            INSERT OR REPLACE INTO commentary_sources
            (source_code, name_kr, name_en, author, description, theological_stance, is_public_domain, access_type, sort_order)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            source_tuples
        )

    # 3. Load & Ingest 66 Books KRV JSON
    json_path = os.path.join(CURRENT_DIR, "sample_data", "bible_1961_krv.json")
    print(f"3. Loading KRV JSON from: {json_path}")
    with open(json_path, "r", encoding="utf-8") as f:
        krv_data = json.load(f)

    book_map = {b[4].replace(" ", ""): b for b in BIBLE_BOOKS_MASTER}

    verses_records = []
    fts_records = []

    for book_obj in krv_data:
        raw_name = book_obj["book"]
        meta = book_map[raw_name]
        book_id = meta[0]

        for ch_obj in book_obj.get("chapters", []):
            ch_num = ch_obj["chapter"]
            for v_obj in ch_obj.get("verses", []):
                v_num = v_obj["verse"]
                text = v_obj["text"].strip()
                v_id = calculate_verse_id(book_id, ch_num, v_num)

                verses_records.append((v_id, book_id, ch_num, v_num, "KRV", text, None))
                fts_records.append((v_id, "KRV", text))

    print(f"Total parsed verses to insert: {len(verses_records)}")
    assert len(verses_records) == 31102, f"Expected 31,102 verses, got {len(verses_records)}"

    # Clear existing KRV verses and FTS index for idempotency
    print("Clearing prior KRV entries from bible_verses and fts_bible_verses...")
    with conn:
        conn.execute("DELETE FROM bible_verses WHERE version_code = 'KRV';")
        conn.execute("DELETE FROM fts_bible_verses WHERE version_code = 'KRV';")

    print(f"Executing batch insert of 31,102 verses into bible_verses...")
    t_ins0 = time.perf_counter()
    with conn:
        conn.executemany(
            """
            INSERT INTO bible_verses
            (verse_id, book_id, chapter, verse, version_code, text, text_with_strong)
            VALUES (?, ?, ?, ?, ?, ?, ?);
            """,
            verses_records
        )
    print(f"bible_verses insert completed in {(time.perf_counter() - t_ins0):.3f}s")

    print(f"Executing batch insert of 31,102 records into fts_bible_verses...")
    t_fts0 = time.perf_counter()
    with conn:
        conn.executemany(
            """
            INSERT INTO fts_bible_verses (verse_id, version_code, text)
            VALUES (?, ?, ?);
            """,
            fts_records
        )
    print(f"fts_bible_verses insert completed in {(time.perf_counter() - t_fts0):.3f}s")

    # 4. Check and preserve/seed sample commentaries, Strongs, and Cross References
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM commentaries")
    comm_count = cur.fetchone()[0]
    sample_dir = os.path.join(CURRENT_DIR, "sample_data")
    if comm_count == 0:
        print("Seeding sample commentaries, strongs, and cross-references for harness tests...")
        OpenDataCollector.generate_pastoral_sample_dataset(sample_dir)

        cp = CommentaryParser()
        sample_comms = cp.parse_json(os.path.join(sample_dir, "sample_commentaries.json"))
        with conn:
            for c in sample_comms:
                cursor = conn.execute(
                    """
                    INSERT INTO commentaries
                    (source_code, book_id, chapter_start, verse_start, chapter_end, verse_end,
                     verse_start_id, verse_end_id, passage_display, title, content_markdown,
                     content_html, theological_tags, practical_points)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                    (
                        c["source_code"], c["book_id"], c["chapter_start"], c["verse_start"],
                        c["chapter_end"], c["verse_end"], c["verse_start_id"], c["verse_end_id"],
                        c["passage_display"], c.get("title", ""), c["content_markdown"],
                        c.get("content_html"), c.get("theological_tags"), c.get("practical_points")
                    )
                )
                comm_id = cursor.lastrowid
                conn.execute(
                    """
                    INSERT INTO fts_commentaries (commentary_id, source_code, passage_display, title, content_markdown, theological_tags)
                    VALUES (?, ?, ?, ?, ?, ?);
                    """,
                    (comm_id, c["source_code"], c["passage_display"], c.get("title", ""), c["content_markdown"], c.get("theological_tags"))
                )

        sp = StrongParser()
        sample_strongs = sp.parse_file(os.path.join(sample_dir, "sample_strongs.json"))
        with conn:
            for s in sample_strongs:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO strong_lexicon
                    (strong_id, language, lemma, transliteration, pronunciation, part_of_speech,
                     definition_kr, definition_en, root_id, derivation, occurrence_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                    (
                        s["strong_id"], s["language"], s["lemma"], s["transliteration"],
                        s["pronunciation"], s["part_of_speech"], s["definition_kr"],
                        s["definition_en"], s.get("root_id"), s.get("derivation"),
                        s.get("occurrence_count", 0)
                    )
                )
                conn.execute(
                    """
                    INSERT INTO fts_strong_lexicon (strong_id, lemma, transliteration, definition_kr, definition_en)
                    VALUES (?, ?, ?, ?, ?);
                    """,
                    (s["strong_id"], s["lemma"], s["transliteration"], s["definition_kr"], s["definition_en"])
                )

        crp = CrossRefParser()
        sample_cross = crp.parse_file(os.path.join(sample_dir, "sample_cross_refs.json"))
        with conn:
            conn.executemany(
                """
                INSERT INTO cross_references
                (from_verse_id, to_verse_id, score, relationship_type, note)
                VALUES (:from_verse_id, :to_verse_id, :score, :relationship_type, :note);
                """,
                sample_cross
            )

    # 5. Optimize FTS5 and Database
    print("5. Optimizing FTS5 indices and SQLite DB...")
    t_opt0 = time.perf_counter()
    with conn:
        conn.execute("INSERT INTO fts_bible_verses(fts_bible_verses) VALUES('optimize');")
        conn.execute("INSERT INTO fts_commentaries(fts_commentaries) VALUES('optimize');")
        conn.execute("INSERT INTO fts_strong_lexicon(fts_strong_lexicon) VALUES('optimize');")
        conn.execute("PRAGMA optimize;")
    print(f"Optimization completed in {(time.perf_counter() - t_opt0):.3f}s")

    # 6. Verification
    print("\n=== VERIFICATION REPORT ===")
    cur.execute("SELECT COUNT(*) FROM bible_verses WHERE version_code = 'KRV'")
    krv_cnt = cur.fetchone()[0]
    print(f"[Record Count] bible_verses (KRV): {krv_cnt} (Target: 31,102)")

    cur.execute("SELECT COUNT(*) FROM fts_bible_verses WHERE version_code = 'KRV'")
    fts_cnt = cur.fetchone()[0]
    print(f"[Record Count] fts_bible_verses (KRV): {fts_cnt} (Target: 31,102)")

    cur.execute("SELECT COUNT(DISTINCT book_id) FROM bible_verses WHERE version_code = 'KRV'")
    books_cnt = cur.fetchone()[0]
    print(f"[Books Count] distinct books: {books_cnt} (Target: 66)")

    cur.execute("SELECT COUNT(DISTINCT book_id || '_' || chapter) FROM bible_verses WHERE version_code = 'KRV'")
    chap_cnt = cur.fetchone()[0]
    print(f"[Chapters Count] distinct chapters: {chap_cnt} (Target: 1,189)")

    # Test FTS query
    t_q0 = time.perf_counter()
    cur.execute(
        """
        SELECT v.verse_id, b.name_kr, v.chapter, v.verse, v.text
        FROM fts_bible_verses f
        JOIN bible_verses v ON f.verse_id = v.verse_id AND f.version_code = v.version_code
        JOIN bible_books b ON v.book_id = b.book_id
        WHERE fts_bible_verses MATCH '하나님이 세상을'
        LIMIT 5;
        """
    )
    search_results = cur.fetchall()
    search_dt = (time.perf_counter() - t_q0) * 1000.0
    print(f"\n[FTS5 Test Query] '하나님이 세상을' ({len(search_results)} matches, {search_dt:.3f} ms):")
    for r in search_results:
        print(f"  - {r['name_kr']} {r['chapter']}:{r['verse']} | {r['text']}")

    # First and last verse check
    cur.execute("SELECT b.name_kr, v.chapter, v.verse, v.text FROM bible_verses v JOIN bible_books b ON v.book_id = b.book_id WHERE v.verse_id = 1001001 AND v.version_code = 'KRV'")
    gen11 = cur.fetchone()
    print(f"\n[First Verse] {gen11['name_kr']} {gen11['chapter']}:{gen11['verse']} | {gen11['text']}")

    cur.execute("SELECT b.name_kr, v.chapter, v.verse, v.text FROM bible_verses v JOIN bible_books b ON v.book_id = b.book_id WHERE v.verse_id = 66022021 AND v.version_code = 'KRV'")
    rev2221 = cur.fetchone()
    print(f"[Last Verse] {rev2221['name_kr']} {rev2221['chapter']}:{rev2221['verse']} | {rev2221['text']}")

    file_size = os.path.getsize(db_path)
    print(f"\n[Database File Size] {file_size:,} bytes ({file_size / 1024 / 1024:.2f} MB)")
    print(f"Total time elapsed: {(time.perf_counter() - t_start):.3f}s")
    print("=== INGESTION SUCCESSFUL ===\n")

    conn.close()


if __name__ == "__main__":
    ingest_full_bible()
