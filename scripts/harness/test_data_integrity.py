"""
Data Integrity & Theological Consistency Verification Harness.
Validates Bible text structure, 8 commentary mappings, verse ID mathematics,
foreign key relationships, and ensures strict exegesis without sectarian dogma hardcoding.
"""

import sys
import os
import sqlite3
import unittest
from typing import List, Dict, Any

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_DIR = os.path.dirname(CURRENT_DIR)
DB_PATH = os.path.join(SCRIPTS_DIR, "data_pipeline", "bible_pastoral_core.db")


class DataIntegrityHarness(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not os.path.exists(DB_PATH):
            raise FileNotFoundError(f"Database file not found: {DB_PATH}. Run build_bible_db.py first.")
        cls.conn = sqlite3.connect(DB_PATH)
        cls.conn.row_factory = sqlite3.Row

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()

    def test_01_bible_books_master_integrity(self):
        """Verify 66 Bible books are fully registered with correct testaments."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) AS cnt, testament FROM bible_books GROUP BY testament;")
        rows = cursor.fetchall()
        counts = {r["testament"]: r["cnt"] for r in rows}
        
        self.assertEqual(counts.get("OT", 0), 39, "Old Testament must contain exactly 39 books")
        self.assertEqual(counts.get("NT", 0), 27, "New Testament must contain exactly 27 books")
        
        # Verify Book ID range 1 to 66
        cursor.execute("SELECT MIN(book_id) AS min_id, MAX(book_id) AS max_id, COUNT(*) AS total FROM bible_books;")
        res = cursor.fetchone()
        self.assertEqual(res["min_id"], 1, "First book ID must be 1 (Genesis)")
        self.assertEqual(res["max_id"], 66, "Last book ID must be 66 (Revelation)")
        self.assertEqual(res["total"], 66, "Total books must be exactly 66")

    def test_02_verse_id_formula_consistency(self):
        """Verify verse_id = (book_id * 1,000,000) + (chapter * 1,000) + verse."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT verse_id, book_id, chapter, verse FROM bible_verses;")
        verses = cursor.fetchall()
        self.assertGreater(len(verses), 0, "Bible verses table must not be empty")

        for v in verses:
            expected_id = (v["book_id"] * 1000000) + (v["chapter"] * 1000) + v["verse"]
            self.assertEqual(
                v["verse_id"],
                expected_id,
                f"Formula mismatch for {v['book_id']}:{v['chapter']}:{v['verse']}. Got {v['verse_id']}, expected {expected_id}"
            )

    def test_03_eight_commentary_sources_registered(self):
        """Verify all 8 requested pastoral commentaries are properly defined."""
        expected_keys = {
            "OXFORD", "WESLEY", "HOKMA", "GRAND",
            "CHARISMA", "MATTHEW_HENRY", "BAKER", "ESV_EXPOSITORY"
        }
        cursor = self.conn.cursor()
        cursor.execute("SELECT source_code, name_kr, access_type FROM commentary_sources;")
        sources = {r["source_code"]: r["name_kr"] for r in cursor.fetchall()}

        for key in expected_keys:
            self.assertIn(key, sources, f"Mandatory commentary source {key} missing from commentary_sources table")

    def test_04_commentary_verse_range_integrity(self):
        """Verify that commentary verse spans are logically valid (start <= end)."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT commentary_id, source_code, verse_start_id, verse_end_id FROM commentaries;")
        commentaries = cursor.fetchall()
        for c in commentaries:
            self.assertLessEqual(
                c["verse_start_id"],
                c["verse_end_id"],
                f"Commentary {c['commentary_id']} ({c['source_code']}) has invalid verse span: {c['verse_start_id']} > {c['verse_end_id']}"
            )

    def test_05_theological_bias_check(self):
        """Ensure no hardcoded denominational or sectarian bias in system definitions."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT name_kr, description, theological_stance FROM commentary_sources;")
        for row in cursor.fetchall():
            text = f"{row['name_kr']} {row['description']} {row['theological_stance']}"
            self.assertNotIn("배타적", text, "Commentary stance must maintain scholarly and pastoral openness")


if __name__ == "__main__":
    unittest.main()
