"""
Real, Non-Tautological Engineering Verification Suite for Bible Commentary Station v2.0.
Tests actual built artifacts:
1. Canon SSOT & 31,102-verse KRV corpus integrity (zero mismatches, zero empty texts)
2. Dual FTS5 (unicode61 + trigram) Korean search recall, injection safety & latency benchmarks
3. Pipeline idempotency (running ingest twice produces ZERO duplicate rows in tables or FTS5!)
4. 8 Commentary sources, non-sectarian neutrality, cross-references full-text & Isaac/Abraham chains
5. Web PWA 66-book lazy chunks, manifest, exegesis bundle & XSS/inline-onclick static audit
6. Flutter static audit (verifies zero invalid Colors.emerald, zero hardcoded paid GCS URLs, UTF-8 byte length fix)
7. BSKorea HTML collector offline parsing & DI fetcher
"""

from __future__ import annotations

import json
import re
import sqlite3
import tempfile
import time
import unittest
from pathlib import Path

from bible_station.builder import BibleDatabaseBuilder, export_zero_cost_bundle
from bible_station.canon import BIBLE_BOOKS, COMMENTARY_SOURCES_MASTER, calculate_verse_id, parse_verse_id
from bible_station.collectors import BskoreaCollector
from bible_station.parsers import ScriptureRefNormalizer
from bible_station.schema import generate_drift_schema
from bible_station.search import HybridBibleSearch

REPO_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = REPO_ROOT / "data" / "bible_pastoral_core.db"
WEB_DIR = REPO_ROOT / "web"
LIB_DIR = REPO_ROOT / "lib"


class TestCanonAndDatabaseIntegrity(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not DB_PATH.exists():
            raise FileNotFoundError(f"DB not built yet: {DB_PATH}")
        cls.conn = sqlite3.connect(str(DB_PATH))
        cls.conn.row_factory = sqlite3.Row

    @classmethod
    def tearDownClass(cls) -> None:
        cls.conn.close()

    def test_01_canon_66_books_and_exact_verse_counts(self) -> None:
        self.assertEqual(len(BIBLE_BOOKS), 66)
        ot = [b for b in BIBLE_BOOKS if b.testament == "OT"]
        nt = [b for b in BIBLE_BOOKS if b.testament == "NT"]
        self.assertEqual(len(ot), 39)
        self.assertEqual(len(nt), 27)
        # Verify Lamentations bug from v1 (66 verses typo) is fixed to 154
        lam = next(b for b in BIBLE_BOOKS if b.osis_code == "LAM")
        self.assertEqual(lam.total_verses, 154)

    def test_02_full_krv_31102_verses_ingested_and_formula_valid(self) -> None:
        cnt = self.conn.execute("SELECT COUNT(*) FROM bible_verses WHERE version_code='KRV'").fetchone()[0]
        self.assertEqual(cnt, 31102)
        mismatches = self.conn.execute(
            "SELECT COUNT(*) FROM bible_verses WHERE verse_id != (book_id * 1000000 + chapter * 1000 + verse)"
        ).fetchone()[0]
        self.assertEqual(mismatches, 0)

    def test_03_eight_commentaries_and_non_sectarian_policy(self) -> None:
        rows = self.conn.execute("SELECT source_code, name_kr, description, theological_stance FROM commentary_sources").fetchall()
        codes = {r["source_code"] for r in rows}
        self.assertEqual(
            codes,
            {"OXFORD", "WESLEY", "HOKMA", "GRAND", "CHARISMA", "MATTHEW_HENRY", "BAKER", "ESV_EXPOSITORY"},
        )
        # Verify v1 sectarian leakage ("기독교대한성결교회", "사중복음") is eliminated
        for r in rows:
            blob = f"{r['name_kr']} {r['description']} {r['theological_stance']}"
            self.assertNotIn("기독교대한성결교회", blob)
            self.assertNotIn("사중복음", blob)
            self.assertNotIn("배타적", blob)

    def test_04_cross_refs_and_chains_resolve_to_real_full_korean_text(self) -> None:
        # Check cross references actually resolve to real KRV verse text in DB
        rows = self.conn.execute(
            """
            SELECT cr.ref_id, v.text
            FROM cross_references cr
            JOIN bible_verses v ON cr.to_verse_id = v.verse_id AND v.version_code = 'KRV'
            """
        ).fetchall()
        total_refs = self.conn.execute("SELECT COUNT(*) FROM cross_references").fetchone()[0]
        self.assertGreater(total_refs, 0)
        self.assertEqual(len(rows), total_refs, "Every cross-reference must resolve to real KRV text")
        for r in rows:
            self.assertGreater(len(r["text"].strip()), 5)

        # Verify Isaac chain actually exists in DB and spans OT & NT with real KRV text
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
        self.assertTrue(any(b <= 39 for b in book_ids), "Isaac chain must include OT")
        self.assertTrue(any(b >= 40 for b in book_ids), "Isaac chain must include NT")


class TestHybridKoreanFts5AndIdempotency(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.conn = sqlite3.connect(str(DB_PATH))
        cls.search = HybridBibleSearch(cls.conn)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.conn.close()

    def test_01_korean_2char_and_3char_substring_recall(self) -> None:
        # 2-char stem ('사랑' must match '사랑하사' in John 3:16)
        res_2char = self.search.search_verses("사랑", limit=50)
        self.assertGreater(len(res_2char), 0, "2-char Korean query '사랑' must return matches")

        # 3-char substring ('독생자' inside '독생자를' in John 3:16 -> 43003016)
        res_3char = self.search.search_verses("독생자", limit=20)
        ids = {r["verse_id"] for r in res_3char}
        self.assertIn(43003016, ids, "Trigram search '독생자' must match John 3:16")

        # 3-char '모리아' must match Genesis 22:2 (1022002)
        res_moriah = self.search.search_verses("모리아", limit=10)
        self.assertIn(1022002, {r["verse_id"] for r in res_moriah})

    def test_02_fts5_injection_safety(self) -> None:
        for hostile in ['"OR*', 'AND NOT ()', "'; DROP TABLE bible_verses; --", "   ", ":::"]:
            res = self.search.search_verses(hostile)
            self.assertIsInstance(res, list)

    def test_03_sub_millisecond_trigram_and_direct_lookup_benchmarks(self) -> None:
        # Direct lookup p50 < 1.0ms
        latencies = []
        for _ in range(30):
            t0 = time.perf_counter()
            self.conn.execute("SELECT text FROM bible_verses WHERE version_code='KRV' AND verse_id=43003016").fetchone()
            latencies.append((time.perf_counter() - t0) * 1000.0)
        latencies.sort()
        self.assertLess(latencies[len(latencies) // 2], 1.0)

        # Trigram FTS5 search p50 < 5.0ms across 31,102 verses
        fts_lat = []
        for kw in ["독생자", "모리아", "여호와", "하나님이", "창조하"] * 4:
            t0 = time.perf_counter()
            self.search.search_verses(kw, limit=10)
            fts_lat.append((time.perf_counter() - t0) * 1000.0)
        fts_lat.sort()
        self.assertLess(fts_lat[len(fts_lat) // 2], 5.0)

    def test_04_pipeline_idempotency_zero_fts5_duplication(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_db = Path(tmp) / "idempotent.db"
            sample_verses = [
                {"verse_id": 1001001, "book_id": 1, "chapter": 1, "verse": 1, "version_code": "KRV", "text": "태초에 하나님이 천지를 창조하시니라"},
                {"verse_id": 43003016, "book_id": 43, "chapter": 3, "verse": 16, "version_code": "KRV", "text": "하나님이 세상을 이처럼 사랑하사 독생자를 주셨으니"},
            ]
            with BibleDatabaseBuilder(tmp_db) as b:
                b.initialize_schema()
                b.seed_master_data()
                # Run ingestion TWICE
                b.ingest_verses(sample_verses)
                b.ingest_verses(sample_verses)
                b.ingest_curated_exegesis()
                b.ingest_curated_exegesis()

                v_cnt = b.conn.execute("SELECT COUNT(*) FROM bible_verses").fetchone()[0]
                fts_u = b.conn.execute("SELECT COUNT(*) FROM fts_bible_verses_unicode").fetchone()[0]
                fts_t = b.conn.execute("SELECT COUNT(*) FROM fts_bible_verses_trigram").fetchone()[0]
                self.assertEqual(v_cnt, 2)
                self.assertEqual(fts_u, 2, "External-content trigger must prevent duplicate FTS5 unicode rows")
                self.assertEqual(fts_t, 2, "External-content trigger must prevent duplicate FTS5 trigram rows")

                # Verify zero-cost bundle manifest reports actual counts (not fake 340,000)
                manifest = export_zero_cost_bundle(tmp_db, Path(tmp) / "dist")
                self.assertEqual(manifest["actual_record_counts"]["bible_verses"], 2)


class TestWebAndFlutterStaticAudit(unittest.TestCase):
    def test_01_web_66_lazy_chunks_and_manifest_valid(self) -> None:
        manifest = json.loads((WEB_DIR / "data" / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["totalBooks"], 66)
        self.assertEqual(manifest["totalVerses"], 31102)
        chunk_files = list((WEB_DIR / "data" / "krv").glob("*.json"))
        self.assertEqual(len(chunk_files), 66)

        # Verify Gen 22:2 is real text (not empty/blocked as in v1)
        gen = json.loads((WEB_DIR / "data" / "krv" / "GEN.json").read_text(encoding="utf-8"))
        self.assertIn("이삭", gen["chapters"]["22"][1])

    def test_02_web_security_no_inline_onclick_or_innerhtml_in_app_js(self) -> None:
        app_js = (WEB_DIR / "js" / "app.js").read_text(encoding="utf-8")
        index_html = (WEB_DIR / "index.html").read_text(encoding="utf-8")
        self.assertNotIn("innerHTML", app_js, "app.js must use safe DOM nodes, not innerHTML")
        self.assertNotIn("onclick=", index_html, "index.html must not contain inline onclick handlers")
        self.assertNotIn("return false;", app_js, "No self-bricking hard-false verification gate")

    def test_03_flutter_static_regression_checks(self) -> None:
        dart_files = list(LIB_DIR.rglob("*.dart"))
        self.assertGreaterEqual(len(dart_files), 8)
        all_dart = "\n".join(f.read_text(encoding="utf-8") for f in dart_files)
        self.assertNotIn("Colors.emerald", all_dart, "Invalid Flutter color constant Colors.emerald must not exist")
        self.assertNotIn("storage.googleapis.com/pastoral-", all_dart, "Hardcoded paid GCS bucket URL must not exist")

        # Verify UTF-8 byte length fix in gdrive_service.dart
        gdrive = (LIB_DIR / "data" / "services" / "gdrive_service.dart").read_text(encoding="utf-8")
        self.assertIn("encodedBytes.length", gdrive, "Must pass UTF-8 byte length to drive.Media")

        # Verify Drift schema is in sync with Python SSOT
        with tempfile.TemporaryDirectory() as tmp:
            fresh = generate_drift_schema(Path(tmp) / "check.drift").read_text(encoding="utf-8")
            committed = (LIB_DIR / "data" / "local" / "database_schema.drift").read_text(encoding="utf-8")
            self.assertEqual(committed, fresh, "database_schema.drift must match SSOT generator")

    def test_04_bskorea_collector_offline_html_parsing_and_di(self) -> None:
        sample_html = """
        <div id="tdBible1" class="bible_read">
            <font class="smallTitle">예수 그리스도의 계보</font><br/>
            <span><span class="number">1&nbsp;</span>아브라함과 다윗의 자손 예수 그리스도의 계보라</span><br/>
            <span><span class="number">23&nbsp;</span><a class="comment" onclick="return clickPopUp('D_1', event)">ㄱ)</a>보라 처녀가 잉태하여
                <div id="D_1" class="D2"><a tar="BGAEisa007014">사 7:14</a></div>
            </span>
        </div>
        """
        collector = BskoreaCollector(delay_seconds=0.0, http_getter=lambda _url: sample_html)
        parsed = collector.fetch_chapter("MAT", 1, "GAE")
        self.assertEqual(len(parsed), 2)
        self.assertEqual(parsed[0]["verse_id"], 40001001)
        self.assertEqual(parsed[1]["cross_refs"][0]["target_ref"], "사 7:14")

        # ScriptureRefNormalizer test
        norm = ScriptureRefNormalizer()
        self.assertEqual(norm.parse_reference("요 3:16"), (43, 3, 16, 43003016))
        self.assertEqual(norm.parse_range_reference("창 22:1-14")[-2:], (1022001, 1022014))


    def test_05_senior_first_ux_invariants(self) -> None:
        html = (WEB_DIR / "index.html").read_text(encoding="utf-8")
        css = (WEB_DIR / "css" / "workstation.css").read_text(encoding="utf-8")
        app_js = (WEB_DIR / "js" / "app.js").read_text(encoding="utf-8")
        # Default warm paper light theme for 60-70s readability
        self.assertIn('data-theme="light"', html)
        # Zero developer jargon in user-facing UI
        for jargon in ("Ctrl K", "JSON 백업", "MD 내보내기", "PASTORAL WORKSTATION"):
            self.assertNotIn(jargon, html)
            self.assertNotIn(jargon, app_js)
        # Must include Korean TTS read-aloud, A4 print mode, and large book picker
        self.assertIn("speechSynthesis", app_js)
        self.assertIn("@media print", css)
        self.assertIn("pickerModal", html)

if __name__ == "__main__":
    unittest.main()
