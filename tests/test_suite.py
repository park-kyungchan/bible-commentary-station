"""
Non-Tautological Engineering Verification Suite for Bible Commentary Station v3.0.
Covers R-BE-01..13, R-WR-01/03/04/05, SQLite .db.gz read-only restore + 5-table FTS5 + open-WAL,
senior-pastor Korean search/parser regressions, corpus/worship/provenance/PII invariants,
and health_check mocked probes. Zero third-party dependencies (stdlib only).
"""

from __future__ import annotations

import filecmp
import gzip
import importlib.util
import json
import os
import re
import shutil
import sqlite3
import tempfile
import time
import unittest
from pathlib import Path
from typing import Optional

from bible_station import __version__
from bible_station.builder import (
    ALLOWED_COUNT_TABLES,
    BibleDatabaseBuilder,
    export_zero_cost_bundle,
    validate_table_name,
    validate_web_corpus,
)
from bible_station.canon import (
    BIBLE_BOOKS,
    BOOKS_BY_OSIS,
    COMMENTARY_SOURCES_MASTER,
    get_chapter_verse_count,
    parse_verse_id,
)
from bible_station.catalog_worship import get_worship_catalog
from bible_station.collectors import BskoreaCollector
from bible_station.health_check import HttpResponse, render_sanitized_markdown, run_health_checks
from bible_station.parsers import ScriptureRefNormalizer, extract_strong_tags
from bible_station.schema import SCHEMA_VERSION, generate_drift_schema
from bible_station.search import HybridBibleSearch, sanitize_fts_phrase

REPO_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = REPO_ROOT / "data" / "bible_pastoral_core.db"
KRV_RAW_PATH = REPO_ROOT / "data" / "raw" / "bible_1961_krv.json"
WEB_DIR = REPO_ROOT / "web"
LIB_DIR = REPO_ROOT / "lib"

_DRIVE_ID_RE = re.compile(r"^[A-Za-z0-9_-]{10,64}$")
_BANNED_PII_TERMS = ("복령교회", "박우호", "cwy0675")


def _ensure_test_db() -> tuple[Path, Optional[tempfile.TemporaryDirectory]]:
    """Use built DB if present, else build cleanly in a temporary directory."""
    if DB_PATH.exists():
        return DB_PATH, None
    tmp = tempfile.TemporaryDirectory(prefix="bcs-test-db-")
    tmp_db = Path(tmp.name) / "bible_pastoral_core.db"
    with BibleDatabaseBuilder(tmp_db) as b:
        b.initialize_schema()
        b.seed_master_data()
        b.ingest_full_krv(KRV_RAW_PATH)
        b.ingest_curated_exegesis()
        b.optimize()
    return tmp_db, tmp


class TestCanonAndDatabaseIntegrity(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.db_path, cls._tmp_ctx = _ensure_test_db()
        cls.conn = sqlite3.connect(str(cls.db_path))
        cls.conn.row_factory = sqlite3.Row

    @classmethod
    def tearDownClass(cls) -> None:
        cls.conn.close()
        if cls._tmp_ctx is not None:
            cls._tmp_ctx.cleanup()

    def test_01_zero_bs4_dependency_and_version_ssot(self) -> None:
        self.assertIsNone(importlib.util.find_spec("bs4"))
        self.assertEqual(__version__, "3.0.0")

    def test_02_canon_66_books_and_krv_versification_alignment(self) -> None:
        self.assertEqual(len(BIBLE_BOOKS), 66)
        self.assertEqual(len([b for b in BIBLE_BOOKS if b.testament == "OT"]), 39)
        self.assertEqual(len([b for b in BIBLE_BOOKS if b.testament == "NT"]), 27)
        self.assertEqual(sum(b.total_verses for b in BIBLE_BOOKS), 31102)
        self.assertEqual(BOOKS_BY_OSIS["1SA"].total_verses, 809)
        self.assertEqual(BOOKS_BY_OSIS["SNG"].total_verses, 118)
        self.assertEqual(BOOKS_BY_OSIS["LAM"].total_verses, 154)

    def test_03_full_krv_31102_verses_and_per_book_counts_match(self) -> None:
        cnt = self.conn.execute("SELECT COUNT(*) FROM bible_verses WHERE version_code='KRV'").fetchone()[0]
        self.assertEqual(cnt, 31102)
        mismatches = self.conn.execute(
            "SELECT COUNT(*) FROM bible_verses WHERE verse_id != (book_id * 1000000 + chapter * 1000 + verse)"
        ).fetchone()[0]
        self.assertEqual(mismatches, 0)
        book_mismatches = self.conn.execute(
            """
            SELECT b.osis_code, b.total_verses, COUNT(v.id)
            FROM bible_books b
            LEFT JOIN bible_verses v ON v.book_id = b.book_id AND v.version_code = 'KRV'
            GROUP BY b.book_id
            HAVING b.total_verses != COUNT(v.id)
            """
        ).fetchall()
        self.assertEqual(book_mismatches, [])

    def test_04_twelve_commentary_sources_and_valid_official_urls(self) -> None:
        rows = self.conn.execute(
            "SELECT source_code, name_kr, description, theological_stance FROM commentary_sources"
        ).fetchall()
        codes = {r["source_code"] for r in rows}
        self.assertEqual(
            codes,
            {
                "MATTHEW_HENRY", "CALVIN", "WESLEY", "JFB",
                "OXFORD", "NICOT_NICNT", "WBC", "BAKER",
                "CONSTABLE", "ESV_EXPOSITORY", "HOKMA", "GRAND",
            },
        )
        for r in rows:
            blob = f"{r['name_kr']} {r['description']} {r['theological_stance']}"
            self.assertNotIn("기독교대한성결교회", blob)
            self.assertNotIn("사중복음", blob)
            self.assertNotIn("배타적", blob)

        src_by_code = {s["code"]: s for s in COMMENTARY_SOURCES_MASTER}
        self.assertIsNone(src_by_code["OXFORD"]["official_url"])
        self.assertIsNone(src_by_code["HOKMA"]["official_url"])
        self.assertIsNone(src_by_code["GRAND"]["official_url"])
        for s in COMMENTARY_SOURCES_MASTER:
            if s["official_url"] is not None:
                self.assertTrue(str(s["official_url"]).startswith("https://"))

    def test_05_cross_refs_and_chains_resolve_to_real_full_korean_text(self) -> None:
        rows = self.conn.execute(
            """
            SELECT cr.ref_id, v.text
            FROM cross_references cr
            JOIN bible_verses v ON cr.to_verse_id = v.verse_id AND v.version_code = 'KRV'
            """
        ).fetchall()
        total_refs = self.conn.execute("SELECT COUNT(*) FROM cross_references").fetchone()[0]
        self.assertGreater(total_refs, 0)
        self.assertEqual(len(rows), total_refs)
        for r in rows:
            self.assertGreater(len(r["text"].strip()), 5)

        isaac_links = self.conn.execute(
            """
            SELECT cl.verse_id, v.text
            FROM chain_links cl
            JOIN bible_verses v ON cl.verse_id = v.verse_id AND v.version_code = 'KRV'
            WHERE cl.topic_key = 'isaac'
            """
        ).fetchall()
        self.assertGreaterEqual(len(isaac_links), 8)
        book_ids = {parse_verse_id(r["verse_id"])[0] for r in isaac_links}
        self.assertTrue(any(b <= 39 for b in book_ids))
        self.assertTrue(any(b >= 40 for b in book_ids))


class TestHybridKoreanSearchParserAndBundle(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.db_path, cls._tmp_ctx = _ensure_test_db()
        cls.conn = sqlite3.connect(str(cls.db_path))
        cls.search = HybridBibleSearch(cls.conn)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.conn.close()
        if cls._tmp_ctx is not None:
            cls._tmp_ctx.cleanup()

    def test_01_senior_pastor_forgiving_verse_and_commentary_search(self) -> None:
        # 2-char, 3-char, space-stripped, and scripture-reference verse queries (R-BE-05)
        self.assertGreater(len(self.search.search_verses("사랑", limit=50)), 0)
        self.assertIn(43003016, {r["verse_id"] for r in self.search.search_verses("독생자", limit=20)})
        self.assertIn(1022002, {r["verse_id"] for r in self.search.search_verses("모리아", limit=10)})
        self.assertIn(19023001, {r["verse_id"] for r in self.search.search_verses("여호와는나의목자", limit=10)})
        self.assertIn(19001001, {r["verse_id"] for r in self.search.search_verses("복있는 사람", limit=10)})
        self.assertIn(43003016, {r["verse_id"] for r in self.search.search_verses("요 3:16", limit=10)})
        self.assertIn(1022002, {r["verse_id"] for r in self.search.search_verses("창22:2", limit=10)})

        # Commentary search with punctuation and 2-char mid-word substring (R-BE-05)
        self.assertGreaterEqual(len(self.search.search_commentaries("사랑?")), 1)
        self.assertGreaterEqual(len(self.search.search_commentaries("하나님.")), 1)
        self.assertGreaterEqual(len(self.search.search_commentaries("생자")), 1)
        self.assertGreaterEqual(len(self.search.search_commentaries("창 22:2")), 12)
        self.assertEqual(sanitize_fts_phrase("사랑?!.,;:/\\{}[]()\"'*^~"), "사랑")

    def test_02_scripture_ref_normalizer_and_strong_tags(self) -> None:
        norm = ScriptureRefNormalizer()
        cases = {
            "시 23편 1절": (19, 23, 1, 19023001),
            "시편 23편 4절": (19, 23, 4, 19023004),
            "계시록 21:4": (66, 21, 4, 66021004),
            "요한1서 4:9": (62, 4, 9, 62004009),
            "요한3서 1:2": (64, 1, 2, 64001002),
            "고린도 전서 13장": (46, 13, 1, 46013001),
            "창세기 1장": (1, 1, 1, 1001001),
            "창22:2": (1, 22, 2, 1022002),
            "Ps 23:1": (19, 23, 1, 19023001),
            "1 Cor 13:4": (46, 13, 4, 46013004),
            "요 3:16": (43, 3, 16, 43003016),
        }
        for raw, expected in cases.items():
            self.assertEqual(norm.parse_reference(raw), expected, f"Failed parsing {raw!r}")

        # Out-of-bounds, reversed ranges, and ambiguous "에스" must safely return None
        self.assertIsNone(norm.parse_reference("창세기 1:999"))
        self.assertIsNone(norm.parse_reference("창세기 1:0"))
        self.assertIsNone(norm.parse_reference("창세기 0:1"))
        self.assertIsNone(norm.parse_reference("에스 1:1"))
        self.assertIsNone(norm.parse_range_reference("요한복음 3:16-10"))
        self.assertEqual(
            norm.parse_range_reference("시 23편 1-6절"),
            (19, 23, 1, 23, 6, 19023001, 19023006),
        )

        clean, tagged = extract_strong_tags("태초에<H7225> 말씀{G3056}이")
        self.assertEqual(clean, "태초에 말씀이")
        self.assertEqual(tagged, "태초에<H7225> 말씀<G3056>이")

    def test_03_fts5_injection_safety(self) -> None:
        for hostile in ['"OR*', "AND NOT ()", "'; DROP TABLE bible_verses; --", "   ", ":::", "NEAR/3 (text:사랑)"]:
            self.assertIsInstance(self.search.search_verses(hostile), list)
            self.assertIsInstance(self.search.search_commentaries(hostile), list)

    def test_04_sub_millisecond_benchmarks(self) -> None:
        latencies = []
        for _ in range(30):
            t0 = time.perf_counter()
            self.conn.execute("SELECT text FROM bible_verses WHERE version_code='KRV' AND verse_id=43003016").fetchone()
            latencies.append((time.perf_counter() - t0) * 1000.0)
        latencies.sort()
        self.assertLess(latencies[len(latencies) // 2], 1.0)

        fts_lat = []
        for kw in ["독생자", "모리아", "여호와", "하나님이", "창조하"] * 4:
            t0 = time.perf_counter()
            self.search.search_verses(kw, limit=10)
            fts_lat.append((time.perf_counter() - t0) * 1000.0)
        fts_lat.sort()
        self.assertLess(fts_lat[len(fts_lat) // 2], 5.0)

    def test_05_idempotency_wal_free_readonly_bundle_and_open_wal_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            tmp_db = tmp_root / "idempotent.db"
            sample_verses = [
                {"verse_id": 1001001, "book_id": 1, "chapter": 1, "verse": 1, "version_code": "KRV", "text": "태초에 하나님이 천지를 창조하시니라"},
                {"verse_id": 43003016, "book_id": 43, "chapter": 3, "verse": 16, "version_code": "KRV", "text": "하나님이 세상을 이처럼 사랑하사 독생자를 주셨으니"},
            ]
            # Open-WAL-connection snapshot test (R-BE-02 & NB-R2-01)
            with BibleDatabaseBuilder(tmp_db) as b:
                b.initialize_schema()
                b.seed_master_data()
                b.ingest_verses(sample_verses)
                b.ingest_verses(sample_verses)
                b.ingest_curated_exegesis()
                b.ingest_curated_exegesis()
                b.conn.execute(
                    "INSERT OR REPLACE INTO bible_verses(verse_id,book_id,chapter,verse,version_code,text) "
                    "VALUES(19023001,19,23,1,'KRV','여호와는 나의 목자시니 내가 부족함이 없으리로다')"
                )
                b.conn.commit()
                self.assertEqual(b.conn.execute("SELECT COUNT(*) FROM bible_verses").fetchone()[0], 3)
                self.assertEqual(b.conn.execute("SELECT COUNT(*) FROM fts_bible_verses_unicode").fetchone()[0], 3)
                self.assertEqual(b.conn.execute("SELECT COUNT(*) FROM fts_bible_verses_trigram").fetchone()[0], 3)
                manifest = export_zero_cost_bundle(tmp_db, tmp_root / "dist")
                self.assertEqual(manifest["actual_record_counts"]["bible_verses"], 3)

            # Decompress into 0555 read-only dir + verify header, integrity, freelist, and 5-table FTS5
            ro_dir = tmp_root / "ro"
            rw_dir = tmp_root / "rw"
            ro_dir.mkdir()
            rw_dir.mkdir()
            out_ro = ro_dir / "core.db"
            out_rw = rw_dir / "core.db"
            with gzip.open(tmp_root / "dist" / manifest["compressed_file_name"], "rb") as f_in, out_ro.open("wb") as f_out:
                shutil.copyfileobj(f_in, f_out)
            shutil.copy2(out_ro, out_rw)

            self.assertEqual(out_ro.read_bytes()[18:20], b"\x01\x01")
            os.chmod(out_ro, 0o444)
            os.chmod(ro_dir, 0o555)
            try:
                con_ro = sqlite3.connect(f"file:{out_ro}?mode=ro", uri=True)
                self.assertEqual(con_ro.execute("PRAGMA integrity_check").fetchone()[0], "ok")
                self.assertEqual(con_ro.execute("PRAGMA freelist_count").fetchone()[0], 0)
                self.assertEqual(con_ro.execute("SELECT COUNT(*) FROM bible_verses").fetchone()[0], 3)
                con_ro.close()
            finally:
                os.chmod(ro_dir, 0o755)
                os.chmod(out_ro, 0o644)

            con_rw = sqlite3.connect(str(out_rw))
            for fts in (
                "fts_bible_verses_unicode",
                "fts_bible_verses_trigram",
                "fts_commentaries_unicode",
                "fts_commentaries_trigram",
                "fts_strong_lexicon",
            ):
                con_rw.execute(f"INSERT INTO {fts}({fts}) VALUES('integrity-check')")
            con_rw.close()

    def test_06_table_allowlist_and_future_schema_guard(self) -> None:
        with self.assertRaises(ValueError):
            validate_table_name("bible_verses; DROP TABLE bible_books", ALLOWED_COUNT_TABLES)

        with tempfile.TemporaryDirectory() as tmp:
            future_db = Path(tmp) / "future.db"
            con = sqlite3.connect(str(future_db))
            con.execute(
                "CREATE TABLE schema_migrations (version INTEGER PRIMARY KEY, applied_at TEXT, description TEXT);"
            )
            con.execute(
                "INSERT INTO schema_migrations(version, applied_at, description) VALUES (?, '2099-01-01', 'future');",
                (SCHEMA_VERSION + 10,),
            )
            con.commit()
            con.close()
            with BibleDatabaseBuilder(future_db) as b:
                with self.assertRaises(RuntimeError):
                    b.initialize_schema()


class TestCorpusWorshipProvenanceAndSecurity(unittest.TestCase):
    def test_01_web_data_corpus_allowlist_checksums_and_search_index(self) -> None:
        web_data_dir = WEB_DIR / "data"
        report = validate_web_corpus(web_data_dir)
        self.assertEqual(len(report["versions"]), 23)
        self.assertEqual(report["versions"][:3], ["nkrv", "krv", "rnksv"])
        self.assertIn("easy", report["versions"])
        self.assertIn("dob", report["versions"])
        self.assertIn("nkcb", report["versions"])
        self.assertIn("esv", report["versions"])
        self.assertIn("tniv", report["versions"])
        self.assertGreaterEqual(report["total_checked_verses"], 31102 * 23)
        self.assertFalse((web_data_dir / "nrsv").exists(), "Legacy mislabeled nrsv/ must remain removed")

        manifest = json.loads((web_data_dir / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["schemaVersion"], 3)
        self.assertEqual(manifest["appVersion"], __version__)
        self.assertEqual(manifest["defaultVersion"], "nkrv")
        self.assertEqual(len(manifest["versions"]), 23)
        self.assertTrue(manifest["versions"][0]["default"])
        self.assertEqual(manifest["versions"][0]["nameKr"], "개역개정")
        self.assertEqual(manifest["versions"][1]["nameKr"], "개역한글")
        self.assertEqual(manifest["versions"][2]["nameKr"], "새번역")
        self.assertEqual(len(manifest["books"]), 66)
        self.assertEqual(len(manifest["checksums"]), 66 * 23 + 23 + 2)

        for vid in ("nkrv", "krv", "rnksv", "easy", "esv"):
            search_idx = json.loads((web_data_dir / "search" / f"{vid}.json").read_text(encoding="utf-8"))
            self.assertEqual(search_idx["version"], vid)
            self.assertEqual(len(search_idx["books"]), 66)
            self.assertGreaterEqual(len(search_idx["verses"]), 31100)

        # Verify NKRV repaired empty verses (GEN 29:28, DAN 3:19) and RNKSV separated footnotes
        nkrv_gen = json.loads((web_data_dir / "nkrv" / "GEN.json").read_text(encoding="utf-8"))
        nkrv_dan = json.loads((web_data_dir / "nkrv" / "DAN.json").read_text(encoding="utf-8"))
        self.assertTrue(nkrv_gen["chapters"]["29"][27].startswith("야곱이 그대로"))
        self.assertTrue(nkrv_dan["chapters"]["3"][18].startswith("느부갓네살이 분이 가득하여"))

        rnksv_gen = json.loads((web_data_dir / "rnksv" / "GEN.json").read_text(encoding="utf-8"))
        self.assertNotIn(" / ㉠", rnksv_gen["chapters"]["1"][0])
        self.assertIn("footnotes", rnksv_gen)
        self.assertGreaterEqual(len(rnksv_gen["footnotes"]["1"]["1"]), 1)

    def test_02_exegesis_provenance_and_coverage_stats(self) -> None:
        exegesis = json.loads((WEB_DIR / "data" / "exegesis.json").read_text(encoding="utf-8"))
        self.assertEqual(len(exegesis["sources"]), 12)
        self.assertEqual(len(exegesis["commentaries"]), 292)
        self.assertEqual(len(exegesis["chains"]), 8)
        self.assertEqual(len(exegesis["strongs"]), 26)
        self.assertEqual({s["category"] for s in exegesis["sources"]}, {"CLASSIC", "ACADEMIC", "EXPOSITORY"})

        distinct_verses = set()
        distinct_books = set()
        for c in exegesis["commentaries"]:
            self.assertIn(c["provenance"], ("EDITORIAL_SUMMARY", "PUBLIC_DOMAIN"))
            self.assertEqual(c["attributionLabel"], "핵심 말씀 참고 요약")
            self.assertNotIn("created_at", c)
            distinct_verses.add(c["verse_start_id"])
            distinct_books.add(c["book_id"])

        stats = exegesis["coverageStats"]
        self.assertEqual(stats["commentaryEntries"], 292)
        self.assertEqual(stats["coveredVerses"], len(distinct_verses))
        self.assertEqual(stats["coveredVerses"], 172)
        self.assertEqual(stats["coveredBooks"], len(distinct_books))
        self.assertEqual(stats["coveredBooks"], 66)
        self.assertEqual(stats["totalVerses"], 31102)

        src_by_code = {s["source_code"]: s for s in exegesis["sources"]}
        self.assertIsNone(src_by_code["OXFORD"]["official_url"])
        self.assertIsNone(src_by_code["HOKMA"]["official_url"])
        self.assertIsNone(src_by_code["GRAND"]["official_url"])

        # DEF-UX-03 / R-UX-07 regression: zero banned jargon acronyms in user-visible Korean fields
        banned_ui_jargon = (
            "HelloAO", "API", "PPT", "GAE", "BSB", "KJV", "WLC", "SBL",
            "JFB", "TSK", "JSON", ".txt", "HTTP 404", "FTS5", "PWA", "PROPHECY_FULFILLMENT",
        )
        for s in exegesis["sources"]:
            for field in ("name_kr", "description", "theological_stance", "category_kr"):
                val = str(s.get(field) or "")
                for term in banned_ui_jargon:
                    self.assertNotIn(term, val, f"Banned UI jargon {term!r} in source {s['source_code']}.{field}: {val!r}")
        for c in exegesis["commentaries"]:
            for field in ("passage_display", "title", "content_markdown", "theological_tags", "practical_points", "attributionLabel"):
                val = str(c.get(field) or "")
                for term in banned_ui_jargon:
                    self.assertNotIn(term, val, f"Banned UI jargon {term!r} in commentary {c['source_code']}.{field}: {val!r}")

    def test_03_worship_hymns_responsive_liturgies_templates_and_zero_pii(self) -> None:
        worship = json.loads((WEB_DIR / "data" / "worship.json").read_text(encoding="utf-8"))
        h645 = json.loads((REPO_ROOT / "bible_station" / "hymns_645.json").read_text(encoding="utf-8"))

        # 645 hymns: exact numbering, 0 title diffs, 0 duplicate non-zero old IDs, valid Drive IDs
        hymns = worship["hymns"]
        self.assertEqual(len(hymns), 645)
        self.assertEqual([h["num"] for h in hymns], list(range(1, 646)))
        seen_old: set[int] = set()
        for h in hymns:
            self.assertEqual(h["title"], h645[str(h["num"])])
            if h["old"] > 0:
                self.assertNotIn(h["old"], seen_old, f"Duplicate old={h['old']} on hymn #{h['num']}")
                seen_old.add(h["old"])
            if h["driveId"]:
                self.assertRegex(h["driveId"], _DRIVE_ID_RE)

        # 137 responsive readings: 0 OOB ranges, 0 offline-empty, all segments valid
        readings = worship["responsiveReadings"]
        self.assertEqual(len(readings), 137)
        self.assertEqual([r["num"] for r in readings], list(range(1, 138)))
        for r in readings:
            if r["driveId"]:
                self.assertRegex(r["driveId"], _DRIVE_ID_RE)
            if r["osis"]:
                mx = get_chapter_verse_count(r["osis"], r["ch"])
                self.assertIsNotNone(mx)
                self.assertTrue(1 <= r["start_vs"] <= r["end_vs"] <= mx, f"OOB RR #{r['num']}")
            segs = r.get("segments", [])
            self.assertGreater(len(segs), 0, f"Offline-empty RR #{r['num']}")
            for seg in segs:
                self.assertIn(seg["role"], ("leader", "congregation", "unison"))
                mx = get_chapter_verse_count(seg["osis"], seg["ch"])
                self.assertIsNotNone(mx)
                self.assertTrue(1 <= seg["start_vs"] <= seg["end_vs"] <= mx, f"OOB segment in RR #{r['num']}")

        # Liturgies (12, typo fixed 권능와 -> 권능과), 8 templates, and 95 CCM with full offline publicLyrics
        liturgies = worship["liturgies"]
        self.assertEqual(len(liturgies), 12)
        lit_blob = json.dumps(liturgies, ensure_ascii=False)
        self.assertIn("권능과", lit_blob)
        self.assertNotIn("권능와", lit_blob)
        self.assertIn("심판하러 오십니다.", lit_blob)
        self.assertEqual(len(worship["templates"]), 8)
        self.assertEqual(len(worship.get("ccm", [])), 95)
        for song in worship["ccm"]:
            self.assertRegex(song["driveId"], r"^[A-Za-z0-9_-]{10,64}$")
            self.assertTrue(song["pptPreviewUrl"].startswith("https://drive.google.com/file/d/"))
            self.assertTrue(bool(song.get("publicLyrics", "").strip()), f"CCM {song['id']} missing publicLyrics")
            self.assertTrue(bool(song.get("usageTiming", "").strip()), f"CCM {song['id']} missing usageTiming")
            self.assertTrue(bool(song.get("pastoralNote", "").strip()), f"CCM {song['id']} missing pastoralNote")

        # Zero PII / watermark strings across bible_station/ and web/data/ (R-WR-05)
        for root in (REPO_ROOT / "bible_station", WEB_DIR / "data"):
            for path in root.rglob("*"):
                if path.is_file() and path.suffix in (".py", ".json"):
                    text = path.read_text(encoding="utf-8")
                    for banned in _BANNED_PII_TERMS:
                        self.assertNotIn(banned, text, f"Banned PII/watermark {banned!r} found in {path}")

    def test_04_deterministic_web_export_byte_identical(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            troot = Path(tmp)
            db = troot / "det.db"
            exp1 = troot / "exp1"
            exp2 = troot / "exp2"
            with BibleDatabaseBuilder(db) as b:
                b.initialize_schema()
                b.seed_master_data()
                b.ingest_verses([
                    {"verse_id": 1001001, "book_id": 1, "chapter": 1, "verse": 1, "version_code": "KRV", "text": "태초에 하나님이 천지를 창조하시니라"}
                ])
                b.ingest_curated_exegesis()
                b.export_web_chunks(exp1)
                b.export_web_chunks(exp2)

            def _assert_dirs_equal(d1: Path, d2: Path) -> None:
                cmp = filecmp.dircmp(d1, d2)
                self.assertEqual(cmp.left_only, [])
                self.assertEqual(cmp.right_only, [])
                self.assertEqual(cmp.diff_files, [])
                for sub in cmp.common_dirs:
                    _assert_dirs_equal(d1 / sub, d2 / sub)

            _assert_dirs_equal(exp1, exp2)

    def test_05_web_security_and_dynamic_js_css_scan(self) -> None:
        index_html = (WEB_DIR / "index.html").read_text(encoding="utf-8")
        self.assertNotIn("onclick=", index_html)
        self.assertIn('data-theme="light"', index_html)
        self.assertNotIn("btnReadAloud", index_html)

        js_files = sorted((WEB_DIR / "js").rglob("*.js"))
        self.assertGreater(len(js_files), 0)
        for js_file in js_files:
            content = js_file.read_text(encoding="utf-8")
            self.assertNotIn("innerHTML", content, f"innerHTML forbidden in {js_file}")
            self.assertNotIn("speechSynthesis", content, f"speechSynthesis forbidden in {js_file}")

        css_files = sorted((WEB_DIR / "css").rglob("*.css"))
        self.assertGreater(len(css_files), 0)
        all_css = "\n".join(f.read_text(encoding="utf-8") for f in css_files)
        self.assertIn("@media print", all_css)

    def test_06_flutter_static_regression_and_drift_parity(self) -> None:
        dart_files = list(LIB_DIR.rglob("*.dart"))
        self.assertGreaterEqual(len(dart_files), 8)
        all_dart = "\n".join(f.read_text(encoding="utf-8") for f in dart_files)
        self.assertNotIn("Colors.emerald", all_dart)
        self.assertNotIn("storage.googleapis.com/pastoral-", all_dart)
        gdrive = (LIB_DIR / "data" / "services" / "gdrive_service.dart").read_text(encoding="utf-8")
        self.assertIn("encodedBytes.length", gdrive)
        with tempfile.TemporaryDirectory() as tmp:
            fresh = generate_drift_schema(Path(tmp) / "check.drift").read_text(encoding="utf-8")
            committed = (LIB_DIR / "data" / "local" / "database_schema.drift").read_text(encoding="utf-8")
            self.assertEqual(committed, fresh)

    def test_07_bskorea_collector_stdlib_html_parser_and_ufffd_rejection(self) -> None:
        sample_html = """
        <div id="tdBible1" class="bible_read">
            <font class="smallTitle">예수 그리스도의 계보</font><br/>
            <span><span class="number">1&nbsp;</span>아브라함과 다윗의 자손 예수 그리스도의 계보라</span><br/>
            <span><span class="number">23&nbsp;</span><a class="comment" onclick="return clickPopUp('D_1', event)">ㄱ)</a>보라 처녀가 잉태하여
                <div id="D_1" class="D2"><a tar="BGAEisa007014">사 7:14</a></div>
                <div id="D_2" class="D2">임마누엘 번역 주석</div>
            </span>
        </div>
        """
        collector = BskoreaCollector(delay_seconds=0.0, http_getter=lambda _url: sample_html)
        parsed = collector.fetch_chapter("MAT", 1, "GAE")
        self.assertEqual(len(parsed), 2)
        self.assertEqual(parsed[0]["verse_id"], 40001001)
        self.assertEqual(parsed[0]["section_title"], "예수 그리스도의 계보")
        self.assertEqual(parsed[0]["text"], "아브라함과 다윗의 자손 예수 그리스도의 계보라")
        self.assertEqual(parsed[1]["cross_refs"][0]["target_ref"], "사 7:14")
        self.assertEqual(parsed[1]["footnotes"][0]["text"], "임마누엘 번역 주석")
        self.assertNotIn("사 7:14", parsed[1]["text"])

        with self.assertRaises(ValueError):
            collector.parse_chapter_html("<span><span class='number'>1</span>깨진\ufffd문자</span>", 1, 1)

    def test_08_health_check_mocked_healthy_and_failing_reports(self) -> None:
        web_data_dir = WEB_DIR / "data"
        manifest_bytes = (web_data_dir / "manifest.json").read_bytes()
        asset_bytes = {
            "exegesis.json": (web_data_dir / "exegesis.json").read_bytes(),
            "worship.json": (web_data_dir / "worship.json").read_bytes(),
            "nkrv/GEN.json": (web_data_dir / "nkrv" / "GEN.json").read_bytes(),
            "krv/GEN.json": (web_data_dir / "krv" / "GEN.json").read_bytes(),
            "rnksv/GEN.json": (web_data_dir / "rnksv" / "GEN.json").read_bytes(),
            "search/nkrv.json": (web_data_dir / "search" / "nkrv.json").read_bytes(),
            "search/krv.json": (web_data_dir / "search" / "krv.json").read_bytes(),
            "search/rnksv.json": (web_data_dir / "search" / "rnksv.json").read_bytes(),
        }

        def healthy_fetcher(url: str, method: str, timeout: float) -> HttpResponse:
            if "helloao.org" in url:
                return HttpResponse(200, json.dumps({"chapter": {"number": 1}}).encode("utf-8"), url)
            if url.endswith("/data/manifest.json"):
                return HttpResponse(200, manifest_bytes, url)
            for rel, body in asset_bytes.items():
                if url.endswith(f"/data/{rel}"):
                    return HttpResponse(200, body, url)
            return HttpResponse(200, b"", url)

        ok, results = run_health_checks(fetcher=healthy_fetcher, drive_sample_limit=2, drive_backoff=0.0)
        self.assertTrue(ok)
        self.assertGreater(len(results), 8)
        md_ok = render_sanitized_markdown(results, timestamp_utc="2026-11-22T02:00:00Z")
        self.assertIn("HEALTHY", md_ok)

        def failing_fetcher(url: str, method: str, timeout: float) -> HttpResponse:
            if "drive.google.com" in url:
                return HttpResponse(302, b"$(rm -rf /)`evil`", "https://accounts.google.com/ServiceLogin")
            if "helloao.org" in url:
                return HttpResponse(503, b"RAW_UNTRUSTED_BODY_SECRET", url)
            return healthy_fetcher(url, method, timeout)

        ok2, results2 = run_health_checks(fetcher=failing_fetcher, drive_sample_limit=1, drive_backoff=0.0)
        self.assertFalse(ok2)
        md_fail = render_sanitized_markdown(results2, timestamp_utc="2026-11-22T02:00:00Z")
        self.assertIn("DEGRADED", md_fail)
        self.assertNotIn("RAW_UNTRUSTED_BODY_SECRET", md_fail)
        self.assertNotIn("$(rm -rf /)", md_fail)


if __name__ == "__main__":
    unittest.main()
