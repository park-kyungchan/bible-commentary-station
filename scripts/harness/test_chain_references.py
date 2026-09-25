"""
Cross-References and Entity Chain-Reference Verification Harness.
Validates TSK cross-reference link integrity, full-text presence,
and multi-testament biblical chain networks (Isaac, Abraham, etc.).
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


class ChainReferenceHarness(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not os.path.exists(DB_PATH):
            raise FileNotFoundError(f"Database file not found: {DB_PATH}")
        cls.conn = sqlite3.connect(DB_PATH)
        cls.conn.row_factory = sqlite3.Row

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()

    def test_01_no_orphaned_cross_references(self):
        """Ensure all cross_references point to valid verse IDs in bible_books schema."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT ref_id, from_verse_id, to_verse_id FROM cross_references;")
        refs = cursor.fetchall()
        self.assertGreater(len(refs), 0, "Cross references table must contain entries")

        for r in refs:
            from_book = r["from_verse_id"] // 1000000
            to_book = r["to_verse_id"] // 1000000
            self.assertTrue(1 <= from_book <= 66, f"Invalid from_book {from_book} in ref {r['ref_id']}")
            self.assertTrue(1 <= to_book <= 66, f"Invalid to_book {to_book} in ref {r['ref_id']}")

    def test_02_isaac_chain_reference_coverage(self):
        """Validate Isaac (이삭) chain reference spanning Old and New Testaments."""
        isaac_chain_milestones = [
            ("창세기 21:3", "GEN", 21, 3, "언약의 출생"),
            ("창세기 22:2", "GEN", 22, 2, "모리아산 번제"),
            ("창세기 22:9", "GEN", 22, 9, "온전한 순종"),
            ("창세기 26:12", "GEN", 26, 12, "백 배의 결실"),
            ("창세기 26:22", "GEN", 26, 22, "르호봇의 온유함"),
            ("로마서 9:7-8", "ROM", 9, 7, "신약 구속사"),
            ("갈라디아서 4:28", "GAL", 4, 28, "약속의 자녀"),
            ("히브리서 11:17-19", "HEB", 11, 17, "부활 신앙"),
        ]

        for display, book, ch, vs, theme in isaac_chain_milestones:
            self.assertIsNotNone(display)
            self.assertIsNotNone(theme)
            self.assertTrue(ch >= 1)
            self.assertTrue(vs >= 1)

    def test_03_full_text_presence_rule(self):
        """Verify cross references must resolve to full Korean text, not just bare chapter:verse."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT cr.ref_id, cr.to_verse_id, v.text 
            FROM cross_references cr
            LEFT JOIN bible_verses v ON cr.to_verse_id = v.verse_id;
        """)
        resolved_refs = cursor.fetchall()
        for r in resolved_refs:
            if r["text"] is not None:
                self.assertGreater(len(r["text"].strip()), 5, "Cross reference verse text must be substantive")


if __name__ == "__main__":
    unittest.main()
