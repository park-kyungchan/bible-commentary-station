"""
Hybrid Korean Full-Text Search Engine for SQLite FTS5 (v3.0).

Senior-pastor forgiving 4-step pipeline for BOTH verses and commentaries:
0. Automatic scripture reference detection ("요 3:16", "시 23편 1절", "창22:2", "창세기 1장")
1. FTS5 `trigram` O(log N) substring match (tokens >= 3 chars)
2. FTS5 `unicode61` prefix token match (handles 1-2 char Korean roots like '사랑')
3. Space-stripped normalized fallback (`REPLACE(text, ' ', '')`) for spacing mistakes
   ("여호와는나의목자", "복있는 사람") and 1-2 char mid-word substrings ("생자").
"""

from __future__ import annotations

import re
import sqlite3
from typing import Any, Dict, List

from .parsers import ScriptureRefNormalizer

_PUNCT_PATTERN = re.compile(r'[.,?!;:/\\{}\[\]()"\'*^~+\-·…「」『』‘’“”<>]+')


def sanitize_fts_phrase(raw_query: str) -> str:
    """Strip punctuation and FTS5 syntax characters safely for phrase matching."""
    cleaned = _PUNCT_PATTERN.sub(" ", raw_query or "").strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned


class HybridBibleSearch:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
        self.conn.row_factory = sqlite3.Row
        self._ref_normalizer = ScriptureRefNormalizer()

    def search_verses(
        self,
        query: str,
        version_code: str = "KRV",
        limit: int = 25,
    ) -> List[Dict[str, Any]]:
        if not query or not query.strip():
            return []

        cur = self.conn.cursor()

        # Route 0: Automatic scripture-reference detection ("요 3:16", "창22:2", "시 23편 1절")
        ref_range = self._ref_normalizer.parse_range_reference(query)
        if ref_range is not None:
            _b, _c1, _v1, _c2, _v2, start_id, end_id = ref_range
            rows = cur.execute(
                """
                SELECT v.verse_id, v.book_id, b.name_kr, v.chapter, v.verse, v.text,
                       -100.0 AS rank_score
                FROM bible_verses v
                JOIN bible_books b ON v.book_id = b.book_id
                WHERE v.version_code = ? AND v.verse_id BETWEEN ? AND ?
                ORDER BY v.verse_id ASC
                LIMIT ?;
                """,
                (version_code, start_id, end_id, limit),
            ).fetchall()
            if rows:
                return [dict(r) for r in rows]

        cleaned = sanitize_fts_phrase(query)
        if not cleaned:
            return []

        tokens = cleaned.split()

        # Route 1: All tokens >= 3 chars -> true FTS5 trigram substring match
        if all(len(t) >= 3 for t in tokens):
            trigram_expr = " ".join(f'"{t}"' for t in tokens)
            rows = cur.execute(
                """
                SELECT v.verse_id, v.book_id, b.name_kr, v.chapter, v.verse, v.text,
                       bm25(fts_bible_verses_trigram) AS rank_score
                FROM fts_bible_verses_trigram f
                JOIN bible_verses v ON f.rowid = v.id
                JOIN bible_books b ON v.book_id = b.book_id
                WHERE fts_bible_verses_trigram MATCH ? AND v.version_code = ?
                ORDER BY rank_score ASC, v.verse_id ASC
                LIMIT ?;
                """,
                (trigram_expr, version_code, limit),
            ).fetchall()
            if rows:
                return [dict(r) for r in rows]

        # Route 2: Prefix unicode61 match (handles 1-2 char Korean stems like '사랑' -> '사랑하사')
        prefix_expr = " ".join(f'"{t}"*' for t in tokens)
        rows = cur.execute(
            """
            SELECT v.verse_id, v.book_id, b.name_kr, v.chapter, v.verse, v.text,
                   bm25(fts_bible_verses_unicode) AS rank_score
            FROM fts_bible_verses_unicode f
            JOIN bible_verses v ON f.rowid = v.id
            JOIN bible_books b ON v.book_id = b.book_id
            WHERE fts_bible_verses_unicode MATCH ? AND v.version_code = ?
            ORDER BY rank_score ASC, v.verse_id ASC
            LIMIT ?;
            """,
            (prefix_expr, version_code, limit),
        ).fetchall()
        if rows:
            return [dict(r) for r in rows]

        # Route 3: Space-stripped fallback (handles missing/extra spaces & 1-2 char mid-word substrings)
        where_clauses = " AND ".join("INSTR(REPLACE(v.text, ' ', ''), ?) > 0" for _ in tokens)
        rows = cur.execute(
            f"""
            SELECT v.verse_id, v.book_id, b.name_kr, v.chapter, v.verse, v.text,
                   0.0 AS rank_score
            FROM bible_verses v
            JOIN bible_books b ON v.book_id = b.book_id
            WHERE v.version_code = ? AND {where_clauses}
            ORDER BY v.verse_id ASC
            LIMIT ?;
            """,
            (version_code, *tokens, limit),
        ).fetchall()
        return [dict(r) for r in rows]

    def search_commentaries(
        self,
        query: str,
        source_code: str | None = None,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        if not query or not query.strip():
            return []

        cur = self.conn.cursor()

        # Route 0: Automatic scripture-reference lookup for commentaries ("창 22:2", "요 3:16")
        ref_range = self._ref_normalizer.parse_range_reference(query)
        if ref_range is not None:
            _b, _c1, _v1, _c2, _v2, start_id, end_id = ref_range
            sql = """
                SELECT c.commentary_id, c.source_code, s.name_kr AS source_name,
                       c.passage_display, c.title, c.content_markdown, c.theological_tags,
                       -100.0 AS rank_score
                FROM commentaries c
                JOIN commentary_sources s ON c.source_code = s.source_code
                WHERE c.verse_start_id <= ? AND c.verse_end_id >= ?
            """
            params: List[Any] = [end_id, start_id]
            if source_code:
                sql += " AND c.source_code = ?"
                params.append(source_code.upper())
            sql += " ORDER BY s.sort_order ASC, c.commentary_id ASC LIMIT ?;"
            params.append(limit)
            rows = cur.execute(sql, params).fetchall()
            if rows:
                return [dict(r) for r in rows]

        cleaned = sanitize_fts_phrase(query)
        if not cleaned:
            return []
        tokens = cleaned.split()

        # Route 1: FTS5 trigram match (all tokens >= 3 chars)
        if all(len(t) >= 3 for t in tokens):
            trigram_expr = " ".join(f'"{t}"' for t in tokens)
            sql = """
                SELECT c.commentary_id, c.source_code, s.name_kr AS source_name,
                       c.passage_display, c.title, c.content_markdown, c.theological_tags,
                       bm25(fts_commentaries_trigram) AS rank_score
                FROM fts_commentaries_trigram f
                JOIN commentaries c ON f.rowid = c.commentary_id
                JOIN commentary_sources s ON c.source_code = s.source_code
                WHERE fts_commentaries_trigram MATCH ?
            """
            params = [trigram_expr]
            if source_code:
                sql += " AND c.source_code = ?"
                params.append(source_code.upper())
            sql += " ORDER BY rank_score ASC, c.commentary_id ASC LIMIT ?;"
            params.append(limit)
            rows = cur.execute(sql, params).fetchall()
            if rows:
                return [dict(r) for r in rows]

        # Route 2: FTS5 unicode61 prefix match
        prefix_expr = " ".join(f'"{t}"*' for t in tokens)
        sql = """
            SELECT c.commentary_id, c.source_code, s.name_kr AS source_name,
                   c.passage_display, c.title, c.content_markdown, c.theological_tags,
                   bm25(fts_commentaries_unicode) AS rank_score
            FROM fts_commentaries_unicode f
            JOIN commentaries c ON f.rowid = c.commentary_id
            JOIN commentary_sources s ON c.source_code = s.source_code
            WHERE fts_commentaries_unicode MATCH ?
        """
        params = [prefix_expr]
        if source_code:
            sql += " AND c.source_code = ?"
            params.append(source_code.upper())
        sql += " ORDER BY rank_score ASC, c.commentary_id ASC LIMIT ?;"
        params.append(limit)
        rows = cur.execute(sql, params).fetchall()
        if rows:
            return [dict(r) for r in rows]

        # Route 3: Space-stripped normalized fallback (handles "생자", spacing variants)
        haystack = "REPLACE(COALESCE(c.passage_display,'') || COALESCE(c.title,'') || COALESCE(c.content_markdown,'') || COALESCE(c.theological_tags,''), ' ', '')"
        where_clauses = " AND ".join(f"INSTR({haystack}, ?) > 0" for _ in tokens)
        sql = f"""
            SELECT c.commentary_id, c.source_code, s.name_kr AS source_name,
                   c.passage_display, c.title, c.content_markdown, c.theological_tags,
                   0.0 AS rank_score
            FROM commentaries c
            JOIN commentary_sources s ON c.source_code = s.source_code
            WHERE {where_clauses}
        """
        params = list(tokens)
        if source_code:
            sql += " AND c.source_code = ?"
            params.append(source_code.upper())
        sql += " ORDER BY s.sort_order ASC, c.commentary_id ASC LIMIT ?;"
        params.append(limit)
        return [dict(r) for r in cur.execute(sql, params).fetchall()]
