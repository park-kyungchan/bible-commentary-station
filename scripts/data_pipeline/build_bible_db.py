"""
Master Database Builder for Biblical Exegesis & Commentary Pastoral Workstation.
Compiles 8 Commentaries, Multi-Bible Versions, Strong's Lexicon,
and TSK Deep Cross References into an optimized SQLite FTS5 Database.
"""

import os
import sys
import sqlite3
import argparse
import time
from typing import Optional, List, Dict, Any

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

# Add parent directory to sys.path to allow execution directly from command line
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURRENT_DIR)
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

from schema import (
    BIBLE_BOOKS_MASTER,
    COMMENTARY_SOURCES_MASTER,
    SQLITE_DDL_STATEMENTS,
    calculate_verse_id
)
from parsers.bible_text_parser import BibleTextParser
from parsers.commentary_parser import CommentaryParser
from parsers.strong_parser import StrongParser
from parsers.cross_ref_parser import CrossRefParser
from collectors.open_data_collector import OpenDataCollector
from export.gcp_storage_exporter import GcpStorageExporter


class BibleDbBuilder:
    """
    Orchestrates schema creation, data ingestion, FTS5 indexing,
    and packaging of the pastoral workstation database.
    """

    def __init__(self, db_path: str = "bible_pastoral_core.db"):
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None

    def connect(self):
        """Opens SQLite connection with performance PRAGMAs."""
        print(f"Connecting to SQLite database: {self.db_path}")
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        
        # High performance settings for bulk building & fast mobile reads
        self.conn.execute("PRAGMA journal_mode = WAL;")
        self.conn.execute("PRAGMA synchronous = NORMAL;")
        self.conn.execute("PRAGMA page_size = 4096;")
        self.conn.execute("PRAGMA cache_size = -64000;")  # 64MB memory cache
        self.conn.execute("PRAGMA foreign_keys = ON;")

    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None

    def initialize_schema(self):
        """Creates all relational tables, FTS5 virtual tables, and indexes."""
        print("Executing DDL statements...")
        with self.conn:
            for ddl in SQLITE_DDL_STATEMENTS:
                self.conn.execute(ddl)
        print("Schema successfully initialized.")

    def seed_master_data(self):
        """Inserts Bible books and commentary sources master definitions."""
        print("Seeding Bible 66 Books and 8 Commentary Sources...")
        with self.conn:
            # 1. Bible Books (66권)
            self.conn.executemany(
                """
                INSERT OR REPLACE INTO bible_books 
                (book_id, osis_code, name_kr, name_kr_abbr, name_en, testament, category, total_chapters, total_verses)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                BIBLE_BOOKS_MASTER
            )

            # 2. Bible Versions
            versions = [
                ("KRV", "개역한글", "Korean Revised Version (1961)", "KOREAN", 0, 1, "공공도메인"),
                ("GAE", "개역개정", "Korean Revised Version (4th Ed)", "KOREAN", 0, 0, "대한성서공회 저작권"),
                ("KJV", "킹제임스 흠정역", "King James Version (1611)", "ENGLISH", 0, 0, "Public Domain"),
                ("ASV", "미국표준역", "American Standard Version (1901)", "ENGLISH", 0, 0, "Public Domain"),
                ("BHS", "히브리어 맛소라", "Biblia Hebraica Stuttgartensia", "HEBREW", 1, 0, "Public Domain Text"),
                ("GNT", "신약 헬라어 원전", "Greek New Testament", "GREEK", 1, 0, "Public Domain Text")
            ]
            self.conn.executemany(
                """
                INSERT OR REPLACE INTO bible_versions 
                (version_code, name_kr, name_en, language, is_original_lang, is_default, copyright_notice)
                VALUES (?, ?, ?, ?, ?, ?, ?);
                """,
                versions
            )

            # 3. Commentary Sources (8종 주석)
            source_tuples = [
                (
                    s["code"], s["name_kr"], s["name_en"], s["author"],
                    s["description"], s["theological_stance"],
                    1 if s["is_public_domain"] else 0,
                    s["access_type"], s["sort_order"]
                )
                for s in COMMENTARY_SOURCES_MASTER
            ]
            self.conn.executemany(
                """
                INSERT OR REPLACE INTO commentary_sources 
                (source_code, name_kr, name_en, author, description, theological_stance, is_public_domain, access_type, sort_order)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                source_tuples
            )
        print("Master data seeded successfully.")

    def ingest_verses(self, verses: List[Dict[str, Any]]):
        """Inserts verse records and synchronizes with FTS5 virtual table."""
        print(f"Ingesting {len(verses)} Bible verses...")
        with self.conn:
            for v in verses:
                self.conn.execute(
                    """
                    INSERT OR REPLACE INTO bible_verses 
                    (verse_id, book_id, chapter, verse, version_code, text, text_with_strong)
                    VALUES (?, ?, ?, ?, ?, ?, ?);
                    """,
                    (
                        v["verse_id"], v["book_id"], v["chapter"], v["verse"],
                        v["version_code"], v["text"], v.get("text_with_strong")
                    )
                )
                # FTS5 인덱싱
                self.conn.execute(
                    """
                    INSERT INTO fts_bible_verses (verse_id, version_code, text)
                    VALUES (?, ?, ?);
                    """,
                    (v["verse_id"], v["version_code"], v["text"])
                )
        print("Bible verses ingested.")

    def ingest_commentaries(self, commentaries: List[Dict[str, Any]]):
        """Inserts commentary records and synchronizes with FTS5 virtual table."""
        print(f"Ingesting {len(commentaries)} commentary entries...")
        with self.conn:
            for c in commentaries:
                cursor = self.conn.execute(
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
                # FTS5 인덱싱
                self.conn.execute(
                    """
                    INSERT INTO fts_commentaries (commentary_id, source_code, passage_display, title, content_markdown, theological_tags)
                    VALUES (?, ?, ?, ?, ?, ?);
                    """,
                    (
                        comm_id, c["source_code"], c["passage_display"],
                        c.get("title", ""), c["content_markdown"], c.get("theological_tags")
                    )
                )
        print("Commentary entries ingested.")

    def ingest_strongs(self, strong_entries: List[Dict[str, Any]]):
        """Inserts Strong lexicon entries and updates FTS5."""
        print(f"Ingesting {len(strong_entries)} Strong's lexicon entries...")
        with self.conn:
            for s in strong_entries:
                self.conn.execute(
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
                # FTS5
                self.conn.execute(
                    """
                    INSERT INTO fts_strong_lexicon (strong_id, lemma, transliteration, definition_kr, definition_en)
                    VALUES (?, ?, ?, ?, ?);
                    """,
                    (s["strong_id"], s["lemma"], s["transliteration"], s["definition_kr"], s["definition_en"])
                )
        print("Strong's entries ingested.")

    def ingest_cross_references(self, cross_refs: List[Dict[str, Any]]):
        """Inserts cross references."""
        print(f"Ingesting {len(cross_refs)} cross references...")
        with self.conn:
            self.conn.executemany(
                """
                INSERT INTO cross_references 
                (from_verse_id, to_verse_id, score, relationship_type, note)
                VALUES (:from_verse_id, :to_verse_id, :score, :relationship_type, :note);
                """,
                cross_refs
            )
        print("Cross references ingested.")

    def optimize_database(self):
        """Optimizes SQLite FTS5 indices and runs VACUUM."""
        print("Optimizing SQLite FTS5 search indices and running PRAGMA optimize...")
        with self.conn:
            self.conn.execute("INSERT INTO fts_bible_verses(fts_bible_verses) VALUES('optimize');")
            self.conn.execute("INSERT INTO fts_commentaries(fts_commentaries) VALUES('optimize');")
            self.conn.execute("INSERT INTO fts_strong_lexicon(fts_strong_lexicon) VALUES('optimize');")
            self.conn.execute("PRAGMA optimize;")
        print("FTS5 indices optimized.")

    def verify_and_benchmark(self) -> Dict[str, Any]:
        """
        Runs automated test queries and benchmarks performance:
        1. Verse retrieval
        2. 8 commentaries lookup for a passage
        3. Strong code popup lookup
        4. FTS5 Korean text search
        5. Deep Cross-References (관주) & Entity Chain query
        """
        print("\n" + "="*60)
        print("AUTOMATED VERIFICATION & BENCHMARK SUITE")
        print("="*60)

        report = {}

        # 1. Total counts
        cur = self.conn.cursor()
        counts = {}
        for table in ["bible_books", "bible_versions", "bible_verses", "commentary_sources", 
                      "commentaries", "strong_lexicon", "cross_references"]:
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            counts[table] = cur.fetchone()[0]
        report["counts"] = counts
        print(f"[Record Counts] {counts}")

        # 2. Verse retrieval test (요한복음 3:16 -> 43003016)
        t0 = time.perf_counter()
        cur.execute("SELECT * FROM bible_verses WHERE verse_id = 43003016 AND version_code = 'KRV'")
        row = cur.fetchone()
        t1 = time.perf_counter()
        verse_time_ms = (t1 - t0) * 1000.0
        print(f"[Verse Query] 요 3:16: '{row['text']}' (Latency: {verse_time_ms:.3f} ms)")
        report["verse_query_ms"] = verse_time_ms

        # 3. 8 Commentaries lookup for 데살로니가전서 5:23 (52005023)
        t0 = time.perf_counter()
        cur.execute(
            """
            SELECT source_code, title, theological_tags, substr(content_markdown, 1, 80) as preview 
            FROM commentaries 
            WHERE 52005023 BETWEEN verse_start_id AND verse_end_id
            """
        )
        comm_rows = cur.fetchall()
        t1 = time.perf_counter()
        comm_time_ms = (t1 - t0) * 1000.0
        print(f"[Commentary Query] 살전 5:23 matched {len(comm_rows)} entries (Latency: {comm_time_ms:.3f} ms):")
        for cr in comm_rows:
            print(f"  - [{cr['source_code']}] {cr['title']} (태그: {cr['theological_tags']})")
        report["commentary_lookup_ms"] = comm_time_ms

        # 4. FTS5 Korean Full-Text Search ("구속" OR "창조")
        t0 = time.perf_counter()
        cur.execute(
            """
            SELECT c.source_code, c.passage_display, c.title, snippet(fts_commentaries, 4, '<b>', '</b>', '...', 10) as snip
            FROM fts_commentaries f
            JOIN commentaries c ON f.commentary_id = c.commentary_id
            WHERE fts_commentaries MATCH '창조'
            """
        )
        fts_rows = cur.fetchall()
        t1 = time.perf_counter()
        fts_time_ms = (t1 - t0) * 1000.0
        print(f"[FTS5 Search] Keyword '창조' matched {len(fts_rows)} results (Latency: {fts_time_ms:.3f} ms):")
        for fr in fts_rows[:3]:
            print(f"  - [{fr['source_code']}] {fr['passage_display']} : {fr['title']}")
        report["fts5_search_ms"] = fts_time_ms

        # 5. Deep Cross-Reference (관주) & Chain-Reference Lookup
        t0 = time.perf_counter()
        cur.execute(
            """
            SELECT cr.relationship_type, cr.score, b.name_kr, cr.to_verse_id, cr.note,
                   COALESCE(v.text, cr.note) AS display_text
            FROM cross_references cr
            JOIN bible_books b ON (cr.to_verse_id / 1000000) = b.book_id
            LEFT JOIN bible_verses v ON cr.to_verse_id = v.verse_id AND v.version_code = 'KRV'
            WHERE cr.from_verse_id = 1001001 OR cr.from_verse_id = 52005023
            ORDER BY cr.score DESC
            """
        )
        cross_rows = cur.fetchall()
        t1 = time.perf_counter()
        cr_time_ms = (t1 - t0) * 1000.0
        print(f"[Cross-Reference Query] Deep Cross-References matched {len(cross_rows)} scriptures (Latency: {cr_time_ms:.3f} ms):")
        for crr in cross_rows[:3]:
            ch = (crr['to_verse_id'] % 1000000) // 1000
            vs = crr['to_verse_id'] % 1000
            print(f"  - [{crr['relationship_type']}] {crr['name_kr']} {ch}:{vs} : '{crr['display_text'][:45]}...'")
        report["cross_ref_query_ms"] = cr_time_ms

        print("="*60 + "\n")
        return report


def main():
    parser = argparse.ArgumentParser(description="Biblical Exegesis & Commentary Pastoral Workstation DB Builder")
    parser.add_argument("--db-path", default="bible_pastoral_core.db", help="Target SQLite database file path")
    parser.add_argument("--sample", action="store_true", help="Generate and ingest sample dataset (Genesis 1, 1Thess 5, etc.)")
    parser.add_argument("--export-gcp", action="store_true", help="Package, compress, and create GCP release manifest")
    parser.add_argument("--gcs-bucket", default="pastoral-workstation-assets", help="GCS bucket name for manifest")
    parser.add_argument("--input-dir", default=None, help="Directory containing custom JSON/text files for ingestion")
    args = parser.parse_args()

    builder = BibleDbBuilder(args.db_path)
    try:
        builder.connect()
        builder.initialize_schema()
        builder.seed_master_data()

        sample_dir = os.path.join(CURRENT_DIR, "sample_data")
        if args.sample or not args.input_dir:
            print("Generating and using rich pastoral sample dataset...")
            OpenDataCollector.generate_pastoral_sample_dataset(sample_dir)
            
            # Ingest Sample Verses
            bp = BibleTextParser()
            sample_verses = bp.parse_json(os.path.join(sample_dir, "sample_verses.json"), "KRV")
            builder.ingest_verses(sample_verses)

            # Ingest Sample 8 Commentaries
            cp = CommentaryParser()
            sample_comms = cp.parse_json(os.path.join(sample_dir, "sample_commentaries.json"))
            builder.ingest_commentaries(sample_comms)

            # Ingest Strongs
            sp = StrongParser()
            sample_strongs = sp.parse_file(os.path.join(sample_dir, "sample_strongs.json"))
            builder.ingest_strongs(sample_strongs)

            # Ingest Cross Refs
            crp = CrossRefParser()
            sample_cross = crp.parse_file(os.path.join(sample_dir, "sample_cross_refs.json"))
            builder.ingest_cross_references(sample_cross)

        builder.optimize_database()
        builder.verify_and_benchmark()

    finally:
        builder.close()

    if args.export_gcp:
        print("\nStarting GCP packaging pipeline...")
        exporter = GcpStorageExporter(gcs_bucket=args.gcs_bucket)
        comp_path = exporter.compress_db(args.db_path)
        manifest = exporter.generate_release_manifest(args.db_path, comp_path)
        script_path = exporter.generate_gcp_upload_script(comp_path, os.path.join(os.path.dirname(comp_path), "release_manifest.json"))
        print(f"GCP Deployment Bundle Ready: {comp_path} and {script_path}")


if __name__ == "__main__":
    main()
