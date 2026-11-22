"""
Unified, Idempotent Database Builder, Web Chunk Exporter, Worship Exporter, and Zero-Cost Packager.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from .canon import (
    BIBLE_BOOKS,
    BIBLE_VERSIONS_MASTER,
    COMMENTARY_SOURCES_MASTER,
)
from .collectors import get_curated_exegesis_dataset, get_worship_catalog
from .parsers import parse_krv_corpus_json
from .schema import SCHEMA_VERSION, SQLITE_DDL_STATEMENTS


class BibleDatabaseBuilder:
    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.conn: Optional[sqlite3.Connection] = None

    def __enter__(self) -> "BibleDatabaseBuilder":
        self.connect()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def connect(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode = WAL;")
        self.conn.execute("PRAGMA synchronous = NORMAL;")
        self.conn.execute("PRAGMA page_size = 4096;")
        self.conn.execute("PRAGMA cache_size = -64000;")
        self.conn.execute("PRAGMA foreign_keys = ON;")

    def close(self) -> None:
        if self.conn:
            self.conn.close()
            self.conn = None

    def initialize_schema(self) -> None:
        assert self.conn is not None
        with self.conn:
            for ddl in SQLITE_DDL_STATEMENTS:
                self.conn.execute(ddl)
            self.conn.execute(
                "INSERT OR IGNORE INTO schema_migrations (version, description) VALUES (?, ?);",
                (SCHEMA_VERSION, "SSOT v2.3 with Dual FTS5 (unicode61+trigram), 12 Official Commentaries & Worship Catalog"),
            )

    def seed_master_data(self) -> None:
        assert self.conn is not None
        with self.conn:
            self.conn.executemany(
                """
                INSERT INTO bible_books
                (book_id, osis_code, name_kr, name_kr_abbr, name_en, testament, category, total_chapters, total_verses)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(book_id) DO UPDATE SET
                    osis_code=excluded.osis_code, name_kr=excluded.name_kr,
                    name_kr_abbr=excluded.name_kr_abbr, name_en=excluded.name_en,
                    testament=excluded.testament, category=excluded.category,
                    total_chapters=excluded.total_chapters, total_verses=excluded.total_verses;
                """,
                [b.as_db_tuple() for b in BIBLE_BOOKS],
            )
            self.conn.executemany(
                """
                INSERT INTO bible_versions
                (version_code, name_kr, name_en, language, is_original_lang, is_default, copyright_notice)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(version_code) DO UPDATE SET
                    name_kr=excluded.name_kr, name_en=excluded.name_en, copyright_notice=excluded.copyright_notice;
                """,
                BIBLE_VERSIONS_MASTER,
            )
            self.conn.executemany(
                """
                INSERT INTO commentary_sources
                (source_code, name_kr, name_en, author, description, theological_stance, is_public_domain, access_type, sort_order)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(source_code) DO UPDATE SET
                    name_kr=excluded.name_kr, description=excluded.description,
                    theological_stance=excluded.theological_stance, is_public_domain=excluded.is_public_domain,
                    access_type=excluded.access_type, sort_order=excluded.sort_order;
                """,
                [
                    (
                        s["code"], s["name_kr"], s["name_en"], s["author"],
                        s["description"], s["theological_stance"],
                        1 if s["is_public_domain"] else 0,
                        s["access_type"], s["sort_order"],
                    )
                    for s in COMMENTARY_SOURCES_MASTER
                ],
            )

    def ingest_provenance(self, records: List[Dict[str, Any]]) -> None:
        assert self.conn is not None
        with self.conn:
            self.conn.executemany(
                """
                INSERT INTO source_provenance (source_id, category, title, rights_status, attribution, source_url)
                VALUES (:source_id, :category, :title, :rights_status, :attribution, :source_url)
                ON CONFLICT(source_id) DO UPDATE SET
                    title=excluded.title, rights_status=excluded.rights_status,
                    attribution=excluded.attribution, source_url=excluded.source_url;
                """,
                records,
            )

    def ingest_verses(self, verses: List[Dict[str, Any]]) -> int:
        assert self.conn is not None
        with self.conn:
            self.conn.executemany(
                """
                INSERT INTO bible_verses
                (verse_id, book_id, chapter, verse, version_code, text, text_with_strong, provenance_id)
                VALUES (:verse_id, :book_id, :chapter, :verse, :version_code, :text, :text_with_strong, :provenance_id)
                ON CONFLICT(version_code, verse_id) DO UPDATE SET
                    text=excluded.text,
                    text_with_strong=COALESCE(excluded.text_with_strong, bible_verses.text_with_strong),
                    provenance_id=COALESCE(excluded.provenance_id, bible_verses.provenance_id);
                """,
                [
                    {
                        "verse_id": v["verse_id"], "book_id": v["book_id"], "chapter": v["chapter"],
                        "verse": v["verse"], "version_code": v["version_code"], "text": v["text"],
                        "text_with_strong": v.get("text_with_strong"), "provenance_id": v.get("provenance_id"),
                    }
                    for v in verses
                ],
            )
        return len(verses)

    def ingest_curated_exegesis(self) -> Dict[str, int]:
        assert self.conn is not None
        ds = get_curated_exegesis_dataset()
        self.ingest_provenance(ds["provenance"])
        with self.conn:
            self.conn.executemany(
                """
                INSERT INTO commentaries
                (source_code, book_id, chapter_start, verse_start, chapter_end, verse_end,
                 verse_start_id, verse_end_id, passage_display, title, content_markdown,
                 theological_tags, practical_points, provenance_id)
                VALUES (:source_code, :book_id, :chapter_start, :verse_start, :chapter_end, :verse_end,
                        :verse_start_id, :verse_end_id, :passage_display, :title, :content_markdown,
                        :theological_tags, :practical_points, :provenance_id)
                ON CONFLICT(source_code, verse_start_id, verse_end_id, title) DO UPDATE SET
                    content_markdown=excluded.content_markdown,
                    theological_tags=excluded.theological_tags,
                    practical_points=excluded.practical_points;
                """,
                ds["commentaries"],
            )
            self.conn.executemany(
                """
                INSERT INTO strong_lexicon
                (strong_id, language, lemma, transliteration, pronunciation, part_of_speech,
                 definition_kr, definition_en, occurrence_count)
                VALUES (:strong_id, :language, :lemma, :transliteration, :pronunciation, :part_of_speech,
                        :definition_kr, :definition_en, :occurrence_count)
                ON CONFLICT(strong_id) DO UPDATE SET
                    definition_kr=excluded.definition_kr,
                    definition_en=excluded.definition_en,
                    occurrence_count=excluded.occurrence_count;
                """,
                ds["strongs"],
            )
            self.conn.executemany(
                """
                INSERT INTO cross_references (from_verse_id, to_verse_id, score, relationship_type, note)
                VALUES (:from_verse_id, :to_verse_id, :score, :relationship_type, :note)
                ON CONFLICT(from_verse_id, to_verse_id, relationship_type) DO UPDATE SET
                    score=excluded.score, note=excluded.note;
                """,
                ds["cross_refs"],
            )
            for topic in ds["chain_topics"]:
                self.conn.execute(
                    """
                    INSERT INTO chain_topics (topic_key, title, meaning, summary)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(topic_key) DO UPDATE SET
                        title=excluded.title, meaning=excluded.meaning, summary=excluded.summary;
                    """,
                    (topic["topic_key"], topic["title"], topic["meaning"], topic["summary"]),
                )
                for idx, (v_id, disp, stage, pt) in enumerate(topic["links"], start=1):
                    self.conn.execute(
                        """
                        INSERT INTO chain_links (topic_key, verse_id, passage_display, stage_label, sermon_point, sort_order)
                        VALUES (?, ?, ?, ?, ?, ?)
                        ON CONFLICT(topic_key, verse_id) DO UPDATE SET
                            stage_label=excluded.stage_label, sermon_point=excluded.sermon_point, sort_order=excluded.sort_order;
                        """,
                        (topic["topic_key"], v_id, disp, stage, pt, idx),
                    )
        return {
            "commentaries": len(ds["commentaries"]),
            "strongs": len(ds["strongs"]),
            "cross_refs": len(ds["cross_refs"]),
            "chain_topics": len(ds["chain_topics"]),
        }

    def ingest_full_krv(self, krv_json_path: Path) -> int:
        ds = get_curated_exegesis_dataset()
        self.ingest_provenance(ds["provenance"])
        verses = parse_krv_corpus_json(krv_json_path)
        return self.ingest_verses(verses)

    def optimize(self) -> None:
        assert self.conn is not None
        with self.conn:
            for tbl in (
                "fts_bible_verses_unicode",
                "fts_bible_verses_trigram",
                "fts_commentaries_unicode",
                "fts_commentaries_trigram",
                "fts_strong_lexicon",
            ):
                self.conn.execute(f"INSERT INTO {tbl}({tbl}) VALUES('optimize');")
            self.conn.execute("PRAGMA optimize;")

    def get_table_counts(self) -> Dict[str, int]:
        assert self.conn is not None
        tables = [
            "bible_books", "bible_versions", "bible_verses", "commentary_sources",
            "commentaries", "strong_lexicon", "cross_references", "chain_topics",
            "chain_links", "source_provenance",
        ]
        return {t: self.conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in tables}

    def export_web_chunks(self, web_data_dir: Path) -> Dict[str, Any]:
        assert self.conn is not None
        krv_dir = web_data_dir / "krv"
        krv_dir.mkdir(parents=True, exist_ok=True)

        book_manifest: List[Dict[str, Any]] = []
        total_verses = 0
        chunk_sizes: Dict[str, int] = {}

        for b in BIBLE_BOOKS:
            rows = self.conn.execute(
                "SELECT chapter, verse, text FROM bible_verses WHERE version_code='KRV' AND book_id=? ORDER BY chapter, verse;",
                (b.book_id,),
            ).fetchall()
            chapters: Dict[str, List[str]] = {}
            for r in rows:
                chapters.setdefault(str(r["chapter"]), []).append(r["text"])
                total_verses += 1
            chunk_payload = {
                "bookId": b.book_id, "osis": b.osis_code, "nameKr": b.name_kr,
                "nameEn": b.name_en, "version": "KRV", "chapters": chapters,
            }
            encoded = json.dumps(chunk_payload, ensure_ascii=False, separators=(",", ":"))
            (krv_dir / f"{b.osis_code}.json").write_text(encoded, encoding="utf-8")
            chunk_sizes[b.osis_code] = len(encoded.encode("utf-8"))
            book_manifest.append({
                "bookId": b.book_id, "id": b.osis_code, "name": b.name_kr, "abbr": b.name_kr_abbr,
                "nameEn": b.name_en, "testament": b.testament, "category": b.category,
                "totalChapters": len(chapters) or b.total_chapters,
                "totalVerses": sum(len(v) for v in chapters.values()),
            })

        # Enrich commentary sources with category & official_url from SSOT
        extra_meta = {s["code"]: s for s in COMMENTARY_SOURCES_MASTER}
        sources = []
        for r in self.conn.execute("SELECT * FROM commentary_sources ORDER BY sort_order").fetchall():
            d = dict(r)
            meta = extra_meta.get(d["source_code"], {})
            d["category"] = meta.get("category", "EXPOSITORY")
            d["category_kr"] = meta.get("category_kr", "강해·설교")
            d["official_url"] = meta.get("official_url", "")
            sources.append(d)

        provenance = {r["source_id"]: dict(r) for r in self.conn.execute("SELECT * FROM source_provenance").fetchall()}
        commentaries = [dict(r) for r in self.conn.execute("SELECT * FROM commentaries ORDER BY verse_start_id, source_code").fetchall()]
        strongs = {r["strong_id"]: dict(r) for r in self.conn.execute("SELECT * FROM strong_lexicon").fetchall()}
        cross_refs_rows = self.conn.execute(
            """
            SELECT cr.from_verse_id, cr.to_verse_id, cr.score, cr.relationship_type, cr.note,
                   b.osis_code AS to_osis, b.name_kr AS to_book_name,
                   (cr.to_verse_id % 1000000) / 1000 AS to_chapter,
                   cr.to_verse_id % 1000 AS to_verse, v.text AS to_text
            FROM cross_references cr
            JOIN bible_books b ON (cr.to_verse_id / 1000000) = b.book_id
            LEFT JOIN bible_verses v ON cr.to_verse_id = v.verse_id AND v.version_code = 'KRV'
            ORDER BY cr.from_verse_id, cr.score DESC;
            """
        ).fetchall()
        cross_refs_by_verse: Dict[str, List[Dict[str, Any]]] = {}
        for r in cross_refs_rows:
            d = dict(r)
            cross_refs_by_verse.setdefault(str(d["from_verse_id"]), []).append(d)

        chains: Dict[str, Any] = {}
        for t in self.conn.execute("SELECT * FROM chain_topics").fetchall():
            links = self.conn.execute(
                """
                SELECT cl.verse_id, cl.passage_display, cl.stage_label, cl.sermon_point,
                       b.osis_code, (cl.verse_id % 1000000) / 1000 AS chapter, cl.verse_id % 1000 AS verse,
                       v.text AS verse_text
                FROM chain_links cl
                JOIN bible_books b ON (cl.verse_id / 1000000) = b.book_id
                LEFT JOIN bible_verses v ON cl.verse_id = v.verse_id AND v.version_code = 'KRV'
                WHERE cl.topic_key = ? ORDER BY cl.sort_order ASC;
                """,
                (t["topic_key"],),
            ).fetchall()
            chains[t["topic_key"]] = {**dict(t), "links": [dict(l) for l in links]}

        (web_data_dir / "manifest.json").write_text(
            json.dumps({
                "schemaVersion": SCHEMA_VERSION,
                "generatedAt": datetime.now(timezone.utc).isoformat(),
                "versionCode": "KRV",
                "totalBooks": len(book_manifest),
                "totalVerses": total_verses,
                "attribution": "Korean Revised Version © Korean Bible Society 1961 (저작권 보호기간 만료)",
                "books": book_manifest,
            }, ensure_ascii=False, separators=(",", ":")),
            encoding="utf-8",
        )

        (web_data_dir / "exegesis.json").write_text(
            json.dumps({
                "schemaVersion": SCHEMA_VERSION,
                "provenance": provenance,
                "sources": sources,
                "commentaries": commentaries,
                "strongs": strongs,
                "crossReferences": cross_refs_by_verse,
                "chains": chains,
            }, ensure_ascii=False, separators=(",", ":")),
            encoding="utf-8",
        )

        # Export Korean Hymn & Responsive Reading (새찬송가 · 교독문) catalog
        worship = get_worship_catalog()
        (web_data_dir / "worship.json").write_text(
            json.dumps(worship, ensure_ascii=False, separators=(",", ":")),
            encoding="utf-8",
        )

        return {
            "total_verses": total_verses,
            "chunk_count": len(chunk_sizes),
            "avg_chunk_bytes": sum(chunk_sizes.values()) // max(len(chunk_sizes), 1),
            "hymns": len(worship["hymns"]),
            "responsive_readings": len(worship["responsiveReadings"]),
        }


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def export_zero_cost_bundle(db_path: Path, out_dir: Path, version: str = "2.3.0") -> Dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    gz_path = out_dir / f"{db_path.name}.gz"
    with db_path.open("rb") as f_in, gzip.open(gz_path, "wb", compresslevel=9) as f_out:
        for chunk in iter(lambda: f_in.read(65536), b""):
            f_out.write(chunk)

    conn = sqlite3.connect(str(db_path))
    counts = {
        t: conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        for t in ("bible_books", "bible_verses", "commentary_sources", "commentaries", "strong_lexicon", "cross_references", "chain_links")
    }
    conn.close()

    uncompressed_size = db_path.stat().st_size
    compressed_size = gz_path.stat().st_size
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "version": version,
        "release_date": datetime.now(timezone.utc).isoformat(),
        "distribution_policy": "ZERO_COST_STATIC_CDN",
        "database_name": db_path.name,
        "uncompressed_size_bytes": uncompressed_size,
        "uncompressed_sha256": sha256_file(db_path),
        "compressed_file_name": gz_path.name,
        "compressed_size_bytes": compressed_size,
        "compressed_sha256": sha256_file(gz_path),
        "compression_ratio_pct": round((1.0 - compressed_size / max(uncompressed_size, 1)) * 100.0, 2),
        "actual_record_counts": counts,
    }
    (out_dir / "release_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest
