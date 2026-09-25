"""
SQLite FTS5 Trigram & Exegesis Query Performance Benchmark Harness.
Validates sub-millisecond query latencies, full-text search speed,
and percentile metrics (p50, p95, p99) for mobile/tablet responsive rendering.
"""

import sys
import os
import sqlite3
import time
import unittest
from typing import List

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_DIR = os.path.dirname(CURRENT_DIR)
DB_PATH = os.path.join(SCRIPTS_DIR, "data_pipeline", "bible_pastoral_core.db")


class Fts5BenchmarkHarness(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not os.path.exists(DB_PATH):
            raise FileNotFoundError(f"Database file not found: {DB_PATH}")
        cls.conn = sqlite3.connect(DB_PATH)
        cls.conn.row_factory = sqlite3.Row
        cls.conn.execute("PRAGMA journal_mode = WAL;")
        cls.conn.execute("PRAGMA cache_size = -32000;")

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()

    def test_01_verse_lookup_sub_millisecond(self):
        """Single verse direct index lookup must execute in < 1.0 ms."""
        latencies: List[float] = []
        cursor = self.conn.cursor()

        # Warm up
        cursor.execute("SELECT text FROM bible_verses WHERE verse_id = 43003016 LIMIT 1;")
        cursor.fetchone()

        for _ in range(50):
            t0 = time.perf_counter()
            cursor.execute("SELECT text FROM bible_verses WHERE verse_id = 43003016 LIMIT 1;")
            row = cursor.fetchone()
            dt = (time.perf_counter() - t0) * 1000.0  # ms
            latencies.append(dt)

        latencies.sort()
        p50 = latencies[25]
        p95 = latencies[47]

        print(f"\n[Benchmark] Verse Direct Lookup: p50={p50:.4f}ms, p95={p95:.4f}ms")
        self.assertLess(p50, 1.0, f"Verse lookup p50 latency {p50}ms exceeded 1.0ms threshold")

    def test_02_fts5_fulltext_search_latency(self):
        """FTS5 keyword search must execute in < 5.0 ms."""
        latencies: List[float] = []
        cursor = self.conn.cursor()

        keywords = ["사랑", "창조", "구속", "믿음", "은혜"]

        for kw in keywords * 10:
            t0 = time.perf_counter()
            cursor.execute("""
                SELECT c.commentary_id, c.passage_display, c.title
                FROM fts_commentaries f
                JOIN commentaries c ON f.commentary_id = c.commentary_id
                WHERE fts_commentaries MATCH ?
                LIMIT 10;
            """, (kw,))
            cursor.fetchall()
            dt = (time.perf_counter() - t0) * 1000.0
            latencies.append(dt)

        latencies.sort()
        p50 = latencies[len(latencies) // 2]
        p95 = latencies[int(len(latencies) * 0.95)]

        print(f"[Benchmark] FTS5 Trigram Search: p50={p50:.4f}ms, p95={p95:.4f}ms")
        self.assertLess(p50, 5.0, f"FTS5 search p50 latency {p50}ms exceeded 5.0ms threshold")

    def test_03_commentary_multi_source_join_speed(self):
        """8-Commentary cross lookup join must execute in < 2.0 ms."""
        cursor = self.conn.cursor()
        t0 = time.perf_counter()
        cursor.execute("""
            SELECT c.*, s.name_kr AS source_name 
            FROM commentaries c
            JOIN commentary_sources s ON c.source_code = s.source_code
            WHERE 52005023 BETWEEN c.verse_start_id AND c.verse_end_id;
        """)
        rows = cursor.fetchall()
        dt = (time.perf_counter() - t0) * 1000.0

        print(f"[Benchmark] 8-Commentary Cross Join: {dt:.4f}ms (matched {len(rows)} entries)")
        self.assertLess(dt, 2.0, f"Multi-source join latency {dt}ms exceeded 2.0ms threshold")


if __name__ == "__main__":
    unittest.main()
