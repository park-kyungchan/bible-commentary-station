"""
Unit and Integration Test Harness for BSKorea Web Collector.
Verifies book resolution, rate limiting, DOM parsing accuracy,
verse ID formula integrity, and SQLite FTS5 synchronization.
"""

import os
import sys
import unittest
import sqlite3
import tempfile

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_DIR = os.path.dirname(CURRENT_DIR)
DATA_PIPELINE_DIR = os.path.join(SCRIPTS_DIR, "data_pipeline")

if DATA_PIPELINE_DIR not in sys.path:
    sys.path.insert(0, DATA_PIPELINE_DIR)

from schema import SQLITE_DDL_STATEMENTS, BIBLE_BOOKS_MASTER, calculate_verse_id
from collectors.bskorea_collector import BskoreaCollector, BSKOREA_BOOKS_CONFIG


class BskoreaCollectorHarness(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.collector = BskoreaCollector(default_version="GAE", delay_seconds=0.1)

    def test_01_book_resolution_and_mappings(self):
        """Test resolving all 66 books by various identifiers."""
        # 1. By ID
        gen_meta = self.collector.resolve_book(1)
        self.assertEqual(gen_meta["osis_code"], "GEN")
        self.assertEqual(gen_meta["bskorea_code"], "gen")

        # 2. By OSIS code
        mat_meta = self.collector.resolve_book("MAT")
        self.assertEqual(mat_meta["book_id"], 40)
        self.assertEqual(mat_meta["name_kr"], "마태복음")

        # 3. By Korean abbreviation
        rom_meta = self.collector.resolve_book("롬")
        self.assertEqual(rom_meta["osis_code"], "ROM")
        self.assertEqual(rom_meta["book_id"], 45)

        # 4. By Korean full name
        jhn_meta = self.collector.resolve_book("요한복음")
        self.assertEqual(jhn_meta["book_id"], 43)

        # 5. By bskorea code
        jnh_meta = self.collector.resolve_book("jnh")
        self.assertEqual(jnh_meta["osis_code"], "JON")
        self.assertEqual(jnh_meta["book_id"], 32)

        # 6. Verify total 66 books in master config
        self.assertEqual(len(BSKOREA_BOOKS_CONFIG), 66)

    def test_02_html_parsing_integrity(self):
        """Test parsing HTML snippet for pure text, verse IDs, footnotes, and cross-refs."""
        sample_html = """
        <div id="tdBible1" class="bible_read">
            <font class="chapNum">제 1 장</font><br/>
            <font class="smallTitle">예수 그리스도의 계보</font><br/>
            <span><span class="number">1&nbsp;&nbsp;&nbsp;</span>아브라함과 다윗의 자손 예수 그리스도의 계보라</span><br/>
            <span><span class="number">2&nbsp;&nbsp;&nbsp;</span>땅이 <font size="2"><a class="comment" href="#" onclick="return clickPopUp('D_001_1', event)"><font size="2">1)</font></a></font>혼돈하고 공허하며
                <div id="D_001_1" class="D2" onclick="popDown2('D_001_1')" style="display:none;z-index:100">또는 형체가 없는 </div>
            </span><br/>
            <span><span class="number">23&nbsp;&nbsp;&nbsp;</span><font size="2"><a class="comment" href="#" onclick="return clickPopUp('D_001_2', event)"><font size="2">ㄱ)</font></a></font>보라 처녀가 잉태하여 아들을 낳을 것이요
                <div id="D_001_2" class="D2" onclick="popDown2('D_001_2')" style="display:none;z-index:100"><a tar="BGAEisa007014">사 7:14</a></div>
            </span>
        </div>
        """
        parsed = self.collector.parse_chapter_html(sample_html, book_id=40, chapter=1, version_code="GAE")
        self.assertEqual(len(parsed), 3)

        # Verse 1 check
        v1 = parsed[0]
        self.assertEqual(v1["verse_id"], 40001001)
        self.assertEqual(v1["verse"], 1)
        self.assertEqual(v1["text"], "아브라함과 다윗의 자손 예수 그리스도의 계보라")
        self.assertEqual(v1["section_title"], "예수 그리스도의 계보")
        self.assertEqual(len(v1["footnotes"]), 0)
        self.assertEqual(len(v1["cross_refs"]), 0)

        # Verse 2 footnote check
        v2 = parsed[1]
        self.assertEqual(v2["verse_id"], 40001002)
        self.assertEqual(v2["text"], "땅이 혼돈하고 공허하며")
        self.assertEqual(len(v2["footnotes"]), 1)
        self.assertEqual(v2["footnotes"][0]["marker"], "1)")
        self.assertEqual(v2["footnotes"][0]["text"], "또는 형체가 없는")

        # Verse 23 cross-ref check
        v23 = parsed[2]
        self.assertEqual(v23["verse_id"], 40001023)
        self.assertEqual(v23["text"], "보라 처녀가 잉태하여 아들을 낳을 것이요")
        self.assertEqual(len(v23["cross_refs"]), 1)
        self.assertEqual(v23["cross_refs"][0]["marker"], "ㄱ)")
        self.assertEqual(v23["cross_refs"][0]["target_ref"], "사 7:14")
        self.assertEqual(v23["cross_refs"][0]["target_tar"], "BGAEisa007014")

    def test_03_database_ingest_and_fts5_sync(self):
        """Test database insertion and FTS5 search index synchronization."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            tmp_db_path = tmp.name

        try:
            # Create schema
            conn = sqlite3.connect(tmp_db_path)
            with conn:
                for ddl in SQLITE_DDL_STATEMENTS:
                    conn.execute(ddl)
                conn.executemany(
                    """
                    INSERT OR REPLACE INTO bible_books 
                    (book_id, osis_code, name_kr, name_kr_abbr, name_en, testament, category, total_chapters, total_verses)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                    BIBLE_BOOKS_MASTER
                )
            conn.close()

            sample_verses = [
                {
                    "verse_id": 1001001,
                    "book_id": 1,
                    "chapter": 1,
                    "verse": 1,
                    "version_code": "GAE",
                    "text": "태초에 하나님이 천지를 창조하시니라",
                    "text_with_strong": None,
                },
                {
                    "verse_id": 40001023,
                    "book_id": 40,
                    "chapter": 1,
                    "verse": 23,
                    "version_code": "GAE",
                    "text": "보라 처녀가 잉태하여 아들을 낳을 것이요 그의 이름은 임마누엘이라 하리라",
                    "text_with_strong": None,
                }
            ]

            count = BskoreaCollector.ingest_into_db(sample_verses, tmp_db_path, sync_fts=True)
            self.assertEqual(count, 2)

            # Verify in SQLite
            conn = sqlite3.connect(tmp_db_path)
            try:
                conn.row_factory = sqlite3.Row
                c = conn.cursor()

                c.execute("SELECT * FROM bible_verses WHERE version_code='GAE';")
                rows = c.fetchall()
                self.assertEqual(len(rows), 2)

                # Test FTS5 unicode61 full-text search (prefix matching for Korean postpositions)
                c.execute("SELECT verse_id, text FROM fts_bible_verses WHERE fts_bible_verses MATCH '천지*';")
                fts_rows = c.fetchall()
                self.assertEqual(len(fts_rows), 1)
                self.assertEqual(fts_rows[0]["verse_id"], 1001001)

                c.execute("SELECT verse_id, text FROM fts_bible_verses WHERE fts_bible_verses MATCH '임마누엘*';")
                fts_rows2 = c.fetchall()
                self.assertEqual(len(fts_rows2), 1)
                self.assertEqual(fts_rows2[0]["verse_id"], 40001023)
            finally:
                conn.close()

        finally:
            if os.path.exists(tmp_db_path):
                try:
                    os.remove(tmp_db_path)
                except OSError:
                    pass

    def test_04_live_genesis_1_and_matthew_1(self):
        """End-to-end live fetch and verification of Genesis 1 and Matthew 1 from BSKorea."""
        # Genesis 1
        gen1 = self.collector.fetch_chapter("GEN", 1, "GAE")
        self.assertEqual(len(gen1), 31, "Genesis 1 must have 31 verses")
        self.assertEqual(gen1[0]["verse_id"], 1001001)
        self.assertEqual(gen1[0]["text"], "태초에 하나님이 천지를 창조하시니라")
        self.assertEqual(gen1[30]["verse_id"], 1001031)

        # Matthew 1
        mat1 = self.collector.fetch_chapter("MAT", 1, "GAE")
        self.assertEqual(len(mat1), 25, "Matthew 1 must have 25 verses")
        self.assertEqual(mat1[0]["verse_id"], 40001001)
        self.assertEqual(mat1[0]["text"], "아브라함과 다윗의 자손 예수 그리스도의 계보라")
        self.assertEqual(mat1[24]["verse_id"], 40001025)


if __name__ == "__main__":
    unittest.main()
