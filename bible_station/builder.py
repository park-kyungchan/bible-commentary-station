"""
Unified, Idempotent Database Builder, Deterministic Web Exporter, Corpus Validator,
and Atomic WAL-Free Zero-Cost Bundle Packager (v3.0).
"""

from __future__ import annotations

import gzip
import hashlib
import json
import re
import sqlite3
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from . import __version__
from .canon import (
    BIBLE_BOOKS,
    BIBLE_VERSIONS_MASTER,
    COMMENTARY_SOURCES_MASTER,
)
from .catalog_commentaries import (
    EDITORIAL_ATTRIBUTION_LABEL,
    EDITORIAL_PROVENANCE,
    build_expanded_exegesis_dataset,
)
from .catalog_worship import get_worship_catalog
from .parsers import parse_krv_corpus_json
from .schema import SCHEMA_VERSION, SQLITE_DDL_STATEMENTS

WEB_MANIFEST_SCHEMA_VERSION = 3

ALLOWED_FTS_TABLES = frozenset({
    "fts_bible_verses_unicode",
    "fts_bible_verses_trigram",
    "fts_commentaries_unicode",
    "fts_commentaries_trigram",
    "fts_strong_lexicon",
})

ALLOWED_COUNT_TABLES = frozenset({
    "bible_books",
    "bible_versions",
    "bible_verses",
    "commentary_sources",
    "commentaries",
    "strong_lexicon",
    "cross_references",
    "chain_topics",
    "chain_links",
    "source_provenance",
    "sermons",
    "sermon_clips",
})

_INLINE_FOOTNOTE_RE = re.compile(r"\s*/\s*[㉠-㉻①-⑮]")

# Genuine critical-text (Nestle-Aland/UBS) variant omissions in Korean 새번역 (RNKSV)
DOCUMENTED_VARIANT_OMISSIONS: Dict[str, frozenset[tuple[str, str, int]]] = {
    "rnksv": frozenset({
        ("MAT", "17", 21), ("MAT", "18", 11), ("MAT", "23", 14),
        ("MRK", "9", 44), ("MRK", "9", 46), ("MRK", "11", 26), ("MRK", "15", 28),
        ("LUK", "23", 17),
        ("ACT", "8", 37), ("ACT", "15", 34), ("ACT", "24", 7), ("ACT", "28", 29),
    }),
}

_EXTRA_WEB_VERSIONS: Tuple[Dict[str, Any], ...] = (
    {
        "id": "nkrv",
        "code": "NKRV",
        "nameKr": "개역개정",
        "default": True,
        "attribution": "대한성서공회 개역개정판 (개인 목회 연구용)",
        "license": "PERSONAL_PASTORAL",
    },
    {
        "id": "rnksv",
        "code": "RNKSV",
        "nameKr": "새번역",
        "default": False,
        "attribution": "대한성서공회 새번역 (개인 목회 연구용)",
        "license": "PERSONAL_PASTORAL",
    },
)


def validate_table_name(table_name: str, allowlist: frozenset[str]) -> str:
    """Validate SQL table identifier against an explicit allowlist before interpolation."""
    if table_name not in allowlist:
        raise ValueError(f"SQL table name not in allowlist: {table_name!r}")
    return table_name


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
        # Check existing schema version before applying DDL (R-BE-12)
        has_mig = self.conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='schema_migrations';"
        ).fetchone()
        if has_mig:
            row = self.conn.execute("SELECT MAX(version) AS max_ver FROM schema_migrations;").fetchone()
            max_ver = row["max_ver"] if row and row["max_ver"] is not None else 0
            if max_ver > SCHEMA_VERSION:
                raise RuntimeError(
                    f"Database schema version {max_ver} is newer than supported SCHEMA_VERSION {SCHEMA_VERSION}"
                )

        with self.conn:
            for ddl in SQLITE_DDL_STATEMENTS:
                self.conn.execute(ddl)
            self.conn.execute(
                "INSERT OR IGNORE INTO schema_migrations (version, description) VALUES (?, ?);",
                (
                    SCHEMA_VERSION,
                    f"SSOT v{__version__} with Dual FTS5 (unicode61+trigram), 12 Commentary Perspectives & Worship/Liturgy Catalog",
                ),
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
        ds = build_expanded_exegesis_dataset()
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
                    practical_points=excluded.practical_points,
                    provenance_id=excluded.provenance_id;
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
        ds = build_expanded_exegesis_dataset()
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
                safe_tbl = validate_table_name(tbl, ALLOWED_FTS_TABLES)
                self.conn.execute(f"INSERT INTO {safe_tbl}({safe_tbl}) VALUES('optimize');")
            self.conn.execute("PRAGMA optimize;")
        # Reclaim freelist pages on re-builds (must execute outside transaction)
        self.conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")
        self.conn.execute("VACUUM;")

    def get_table_counts(self, tables: Optional[List[str]] = None) -> Dict[str, int]:
        assert self.conn is not None
        target_tables = tables or [
            "bible_books", "bible_versions", "bible_verses", "commentary_sources",
            "commentaries", "strong_lexicon", "cross_references", "chain_topics",
            "chain_links", "source_provenance",
        ]
        result: Dict[str, int] = {}
        for t in target_tables:
            safe_t = validate_table_name(t, ALLOWED_COUNT_TABLES)
            result[safe_t] = self.conn.execute(f"SELECT COUNT(*) FROM {safe_t}").fetchone()[0]
        return result

    def export_web_chunks(
        self,
        web_data_dir: Path,
        source_date_epoch: Optional[int] = None,
        extra_versions_source_dir: Optional[Path] = None,
    ) -> Dict[str, Any]:
        """Export deterministic v3 web data artifacts matching SPEC.md §3.5."""
        assert self.conn is not None
        web_data_dir = Path(web_data_dir)
        krv_dir = web_data_dir / "krv"
        search_dir = web_data_dir / "search"
        krv_dir.mkdir(parents=True, exist_ok=True)
        search_dir.mkdir(parents=True, exist_ok=True)

        book_manifest: List[Dict[str, Any]] = []
        search_books: List[str] = []
        search_verses: List[List[Any]] = []
        total_verses = 0
        chunk_sizes: Dict[str, int] = {}
        checksums: Dict[str, str] = {}

        for book_idx, b in enumerate(BIBLE_BOOKS):
            search_books.append(b.osis_code)
            rows = self.conn.execute(
                "SELECT chapter, verse, text FROM bible_verses WHERE version_code='KRV' AND book_id=? ORDER BY chapter, verse;",
                (b.book_id,),
            ).fetchall()
            chapters: Dict[str, List[str]] = {}
            for r in rows:
                ch_int = int(r["chapter"])
                vs_int = int(r["verse"])
                txt = r["text"]
                chapters.setdefault(str(ch_int), []).append(txt)
                search_verses.append([book_idx, ch_int, vs_int, txt])
                total_verses += 1
            chunk_payload = {
                "bookId": b.book_id,
                "osis": b.osis_code,
                "nameKr": b.name_kr,
                "nameEn": b.name_en,
                "version": "KRV",
                "chapters": chapters,
            }
            encoded = json.dumps(chunk_payload, ensure_ascii=False, separators=(",", ":"))
            chunk_path = krv_dir / f"{b.osis_code}.json"
            chunk_path.write_text(encoded, encoding="utf-8")
            chunk_sizes[b.osis_code] = len(encoded.encode("utf-8"))
            checksums[f"krv/{b.osis_code}.json"] = sha256_file(chunk_path)
            book_manifest.append({
                "bookId": b.book_id,
                "id": b.osis_code,
                "name": b.name_kr,
                "abbr": b.name_kr_abbr,
                "nameEn": b.name_en,
                "testament": b.testament,
                "category": b.category,
                "totalChapters": len(chapters) or b.total_chapters,
                "totalVerses": sum(len(v) for v in chapters.values()),
            })

        # Export compact single-fetch web search index for KRV (R-BE-05, SPEC.md §3.5)
        search_payload = {
            "version": "krv",
            "books": search_books,
            "verses": search_verses,
        }
        search_path = search_dir / "krv.json"
        search_path.write_text(
            json.dumps(search_payload, ensure_ascii=False, separators=(",", ":")),
            encoding="utf-8",
        )
        checksums["search/krv.json"] = sha256_file(search_path)

        # Export built-in additional Korean translations (nkrv [default], rnksv) deterministically
        src_root = (
            Path(extra_versions_source_dir)
            if extra_versions_source_dir is not None
            else Path(__file__).resolve().parent.parent / "web" / "data"
        )
        extra_version_entries: Dict[str, Dict[str, Any]] = {}
        for vcfg in _EXTRA_WEB_VERSIONS:
            vid = vcfg["id"]
            vsrc_dir = src_root / vid
            if not vsrc_dir.is_dir():
                continue
            # Read all 66 normalized books in memory first (safe for in-place web_data_dir == src_root)
            loaded_books: List[Tuple[int, Any, Dict[str, Any]]] = []
            for book_idx, b in enumerate(BIBLE_BOOKS):
                src_file = vsrc_dir / f"{b.osis_code}.json"
                if not src_file.is_file():
                    loaded_books = []
                    break
                loaded_books.append((book_idx, b, json.loads(src_file.read_text(encoding="utf-8"))))
            if len(loaded_books) != len(BIBLE_BOOKS):
                continue

            vout_dir = web_data_dir / vid
            vout_dir.mkdir(parents=True, exist_ok=True)
            v_search_verses: List[List[Any]] = []
            v_total_verses = 0
            for book_idx, b, raw_doc in loaded_books:
                chapters_raw = raw_doc.get("chapters", {})
                norm_chapters: Dict[str, List[str]] = {}
                for ch_k in sorted(chapters_raw.keys(), key=lambda x: int(x)):
                    ch_int = int(ch_k)
                    vs_list = list(chapters_raw[ch_k])
                    norm_chapters[str(ch_int)] = vs_list
                    for vs_idx, txt in enumerate(vs_list, start=1):
                        v_search_verses.append([book_idx, ch_int, vs_idx, txt])
                        v_total_verses += 1
                out_doc: Dict[str, Any] = {
                    "bookId": b.book_id,
                    "osis": b.osis_code,
                    "nameKr": b.name_kr,
                    "nameEn": b.name_en,
                    "version": vcfg["code"],
                    "chapters": norm_chapters,
                }
                if raw_doc.get("footnotes"):
                    out_doc["footnotes"] = raw_doc["footnotes"]
                out_path = vout_dir / f"{b.osis_code}.json"
                out_path.write_text(
                    json.dumps(out_doc, ensure_ascii=False, separators=(",", ":")),
                    encoding="utf-8",
                )
                checksums[f"{vid}/{b.osis_code}.json"] = sha256_file(out_path)

            v_search_path = search_dir / f"{vid}.json"
            v_search_path.write_text(
                json.dumps(
                    {"version": vid, "books": search_books, "verses": v_search_verses},
                    ensure_ascii=False,
                    separators=(",", ":"),
                ),
                encoding="utf-8",
            )
            checksums[f"search/{vid}.json"] = sha256_file(v_search_path)
            extra_version_entries[vid] = {
                "id": vid,
                "nameKr": vcfg["nameKr"],
                "default": bool(vcfg["default"]),
                "attribution": vcfg["attribution"],
                "license": vcfg["license"],
                "pathPrefix": f"./data/{vid}/",
                "searchIndexPath": f"./data/search/{vid}.json",
                "totalBooks": len(BIBLE_BOOKS),
                "totalVerses": v_total_verses,
            }

        # Enrich commentary sources with category & fixed official_url (None where invalid)
        extra_meta = {s["code"]: s for s in COMMENTARY_SOURCES_MASTER}
        sources = []
        for r in self.conn.execute("SELECT * FROM commentary_sources ORDER BY sort_order").fetchall():
            d = dict(r)
            meta = extra_meta.get(d["source_code"], {})
            d["category"] = meta.get("category", "EXPOSITORY")
            d["category_kr"] = meta.get("category_kr", "강해·설교")
            d["official_url"] = meta.get("official_url")
            sources.append(d)

        # Omit volatile timestamps (`verified_at`, `created_at`) for byte-identical determinism (R-BE-09)
        provenance = {}
        for r in self.conn.execute("SELECT * FROM source_provenance ORDER BY source_id").fetchall():
            d = dict(r)
            d.pop("verified_at", None)
            provenance[d["source_id"]] = d

        commentaries = []
        covered_verse_ids = set()
        covered_book_ids = set()
        for r in self.conn.execute(
            "SELECT * FROM commentaries ORDER BY verse_start_id, source_code, title"
        ).fetchall():
            d = dict(r)
            d.pop("created_at", None)
            d["provenance"] = EDITORIAL_PROVENANCE
            d["attributionLabel"] = EDITORIAL_ATTRIBUTION_LABEL
            covered_verse_ids.add(d["verse_start_id"])
            covered_book_ids.add(d["book_id"])
            commentaries.append(d)

        strongs = {
            r["strong_id"]: dict(r)
            for r in self.conn.execute("SELECT * FROM strong_lexicon ORDER BY strong_id").fetchall()
        }
        cross_refs_rows = self.conn.execute(
            """
            SELECT cr.from_verse_id, cr.to_verse_id, cr.score, cr.relationship_type, cr.note,
                   b.osis_code AS to_osis, b.name_kr AS to_book_name,
                   (cr.to_verse_id % 1000000) / 1000 AS to_chapter,
                   cr.to_verse_id % 1000 AS to_verse, v.text AS to_text
            FROM cross_references cr
            JOIN bible_books b ON (cr.to_verse_id / 1000000) = b.book_id
            LEFT JOIN bible_verses v ON cr.to_verse_id = v.verse_id AND v.version_code = 'KRV'
            ORDER BY cr.from_verse_id, cr.score DESC, cr.to_verse_id ASC;
            """
        ).fetchall()
        cross_refs_by_verse: Dict[str, List[Dict[str, Any]]] = {}
        for r in cross_refs_rows:
            d = dict(r)
            cross_refs_by_verse.setdefault(str(d["from_verse_id"]), []).append(d)

        chains: Dict[str, Any] = {}
        for t in self.conn.execute("SELECT * FROM chain_topics ORDER BY topic_key").fetchall():
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

        exegesis_payload = {
            "schemaVersion": WEB_MANIFEST_SCHEMA_VERSION,
            "coverageStats": {
                "commentaryEntries": len(commentaries),
                "coveredVerses": len(covered_verse_ids),
                "coveredBooks": len(covered_book_ids),
                "totalVerses": total_verses or 31102,
            },
            "provenance": provenance,
            "sources": sources,
            "commentaries": commentaries,
            "strongs": strongs,
            "crossReferences": cross_refs_by_verse,
            "chains": chains,
        }
        exegesis_path = web_data_dir / "exegesis.json"
        exegesis_path.write_text(
            json.dumps(exegesis_payload, ensure_ascii=False, separators=(",", ":")),
            encoding="utf-8",
        )
        checksums["exegesis.json"] = sha256_file(exegesis_path)

        # Export Korean Worship, Liturgy & Templates catalog
        worship = get_worship_catalog()
        worship_path = web_data_dir / "worship.json"
        worship_path.write_text(
            json.dumps(worship, ensure_ascii=False, separators=(",", ":")),
            encoding="utf-8",
        )
        checksums["worship.json"] = sha256_file(worship_path)

        has_nkrv = "nkrv" in extra_version_entries
        krv_entry = {
            "id": "krv",
            "nameKr": "개역한글",
            "default": not has_nkrv,
            "attribution": "대한성서공회 1961 (저작권 보호기간 만료)",
            "license": "PUBLIC_DOMAIN",
            "pathPrefix": "./data/krv/",
            "searchIndexPath": "./data/search/krv.json",
            "totalBooks": len(book_manifest),
            "totalVerses": total_verses,
        }
        versions_list: List[Dict[str, Any]] = []
        if has_nkrv:
            versions_list.append(extra_version_entries["nkrv"])
        versions_list.append(krv_entry)
        if "rnksv" in extra_version_entries:
            versions_list.append(extra_version_entries["rnksv"])

        default_ver = next((v["id"] for v in versions_list if v.get("default")), "krv")
        manifest_payload: Dict[str, Any] = {
            "schemaVersion": WEB_MANIFEST_SCHEMA_VERSION,
            "appVersion": __version__,
            "defaultVersion": default_ver,
            "versions": versions_list,
            "books": book_manifest,
            "checksums": dict(sorted(checksums.items())),
        }
        if source_date_epoch is not None:
            manifest_payload["generatedAt"] = datetime.fromtimestamp(
                int(source_date_epoch), tz=timezone.utc
            ).isoformat()

        (web_data_dir / "manifest.json").write_text(
            json.dumps(manifest_payload, ensure_ascii=False, separators=(",", ":")),
            encoding="utf-8",
        )

        return {
            "versions": [v["id"] for v in versions_list],
            "total_verses": total_verses,
            "chunk_count": len(chunk_sizes),
            "avg_chunk_bytes": sum(chunk_sizes.values()) // max(len(chunk_sizes), 1),
            "hymns": len(worship["hymns"]),
            "responsive_readings": len(worship["responsiveReadings"]),
            "liturgies": len(worship["liturgies"]),
            "templates": len(worship["templates"]),
        }


def validate_web_corpus(web_data_dir: Path, conn: Optional[sqlite3.Connection] = None) -> Dict[str, Any]:
    """Strict corpus validator enforcing R-BE-03 invariants across all registered versions in web/data/."""
    web_data_dir = Path(web_data_dir)
    manifest_path = web_data_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    versions = manifest.get("versions", [])
    allowed_dirs = {v["id"] for v in versions} | {"search"}
    actual_dirs = {p.name for p in web_data_dir.iterdir() if p.is_dir()}
    extra_dirs = actual_dirs - allowed_dirs
    if extra_dirs:
        raise ValueError(f"Unlisted web/data directories violate allowlist: {sorted(extra_dirs)}")

    checksums = manifest.get("checksums", {})
    if not checksums:
        raise ValueError("manifest.json missing checksums map")
    for rel_path, expected_hash in checksums.items():
        fp = web_data_dir / rel_path
        if not fp.exists():
            raise ValueError(f"Checksum target missing on disk: {rel_path}")
        actual_hash = sha256_file(fp)
        if actual_hash != expected_hash:
            raise ValueError(f"SHA-256 mismatch for {rel_path}: expected {expected_hash}, got {actual_hash}")

    total_checked_verses = 0
    for v in versions:
        vid = v["id"]
        vdir = web_data_dir / vid
        allowed_empty = DOCUMENTED_VARIANT_OMISSIONS.get(vid, frozenset())
        files = sorted(vdir.glob("*.json"))
        if len(files) != 66:
            raise ValueError(f"Version {vid} expected 66 book files, found {len(files)}")
        chapters_count = 0
        verses_count = 0
        for f in files:
            data = json.loads(f.read_text(encoding="utf-8"))
            for key in ("bookId", "osis", "nameKr", "nameEn", "version", "chapters"):
                if key not in data:
                    raise ValueError(f"{vid}/{f.name} missing required schema key {key!r}")
            osis = data["osis"]
            for ch_str, verse_list in data["chapters"].items():
                if not isinstance(verse_list, list):
                    raise ValueError(f"{vid}/{f.name} chapter {ch_str} must be list[str]")
                chapters_count += 1
                for idx, txt in enumerate(verse_list, start=1):
                    if not isinstance(txt, str):
                        raise ValueError(f"Non-string verse in {vid}/{f.name} {ch_str}:{idx}")
                    if not txt.strip():
                        if (osis, ch_str, idx) not in allowed_empty:
                            raise ValueError(f"Unexpected empty verse in {vid}/{f.name} {ch_str}:{idx}")
                    else:
                        if "\ufffd" in txt:
                            raise ValueError(f"Mojibake U+FFFD in {vid}/{f.name} {ch_str}:{idx}")
                        if _INLINE_FOOTNOTE_RE.search(txt):
                            raise ValueError(f"Inline footnote pollution in {vid}/{f.name} {ch_str}:{idx}")
                    verses_count += 1
        if chapters_count != 1189:
            raise ValueError(f"Version {vid} expected 1,189 chapters, got {chapters_count}")
        if verses_count != v["totalVerses"]:
            raise ValueError(f"Version {vid} verse count mismatch: {verses_count} vs manifest {v['totalVerses']}")
        search_file = web_data_dir / "search" / f"{vid}.json"
        if not search_file.is_file():
            raise ValueError(f"Missing search index for {vid}: {search_file}")
        sdata = json.loads(search_file.read_text(encoding="utf-8"))
        if len(sdata.get("books", [])) != 66 or len(sdata.get("verses", [])) != v["totalVerses"]:
            raise ValueError(f"Invalid search index counts for {vid}")
        total_checked_verses += verses_count

    if conn is not None:
        mismatches = conn.execute(
            """
            SELECT b.osis_code, b.total_verses, COUNT(v.id) AS actual
            FROM bible_books b
            LEFT JOIN bible_verses v ON v.book_id = b.book_id AND v.version_code = 'KRV'
            GROUP BY b.book_id
            HAVING b.total_verses != COUNT(v.id);
            """
        ).fetchall()
        if mismatches:
            raise ValueError(f"bible_books.total_verses mismatches: {[tuple(m) for m in mismatches]}")

    return {
        "versions": [v["id"] for v in versions],
        "checksum_files": len(checksums),
        "total_checked_verses": total_checked_verses,
    }


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def export_zero_cost_bundle(
    db_path: Path,
    out_dir: Path,
    version: str = __version__,
) -> Dict[str, Any]:
    """
    Create an atomic, WAL-free, VACUUMed, read-only-safe SQLite bundle (.db.gz).
    Uses SQLite Online Backup API so live open WAL connections snapshot cleanly (R-BE-02).
    """
    db_path = Path(db_path)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    gz_path = out_dir / f"{db_path.name}.gz"

    with tempfile.TemporaryDirectory(prefix="bcs-bundle-") as tmpdir:
        staging_db = Path(tmpdir) / db_path.name

        # 1. Consistent online backup (captures uncommitted WAL frames from any open WAL connection)
        src_conn = sqlite3.connect(str(db_path))
        dst_conn = sqlite3.connect(str(staging_db))
        try:
            src_conn.backup(dst_conn)
        finally:
            src_conn.close()

        # 2. Checkpoint WAL, switch to DELETE journal mode, VACUUM to 0 freelist pages
        try:
            dst_conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")
            dst_conn.execute("PRAGMA journal_mode = DELETE;")
            dst_conn.execute("VACUUM;")

            integrity = dst_conn.execute("PRAGMA integrity_check;").fetchone()[0]
            if integrity != "ok":
                raise RuntimeError(f"Staged bundle failed PRAGMA integrity_check: {integrity}")
            freelist = dst_conn.execute("PRAGMA freelist_count;").fetchone()[0]
            if freelist != 0:
                raise RuntimeError(f"Staged bundle has non-zero freelist_count: {freelist}")

            count_tables = (
                "bible_books",
                "bible_verses",
                "commentary_sources",
                "commentaries",
                "strong_lexicon",
                "cross_references",
                "chain_links",
            )
            counts = {
                t: dst_conn.execute(
                    f"SELECT COUNT(*) FROM {validate_table_name(t, ALLOWED_COUNT_TABLES)}"
                ).fetchone()[0]
                for t in count_tables
            }
        finally:
            dst_conn.close()

        # 3. Verify SQLite file format header bytes 18:20 == (1, 1) (DELETE journal mode, read-only safe)
        with staging_db.open("rb") as f_hdr:
            header = f_hdr.read(20)
        if len(header) < 20 or header[18:20] != b"\x01\x01":
            raise RuntimeError(f"Invalid SQLite journal header in bundle: {header[18:20]!r}")

        # 4. Compress closed staging file only
        with staging_db.open("rb") as f_in, gz_path.open("wb") as raw_out:
            with gzip.GzipFile(filename=db_path.name, mode="wb", compresslevel=9, fileobj=raw_out, mtime=0) as f_out:
                for chunk in iter(lambda: f_in.read(65536), b""):
                    f_out.write(chunk)

        uncompressed_size = staging_db.stat().st_size
        uncompressed_sha256 = sha256_file(staging_db)

    compressed_size = gz_path.stat().st_size
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "version": version,
        "release_date": datetime.now(timezone.utc).isoformat(),
        "distribution_policy": "ZERO_COST_STATIC_CDN",
        "database_name": db_path.name,
        "uncompressed_size_bytes": uncompressed_size,
        "uncompressed_sha256": uncompressed_sha256,
        "compressed_file_name": gz_path.name,
        "compressed_size_bytes": compressed_size,
        "compressed_sha256": sha256_file(gz_path),
        "compression_ratio_pct": round((1.0 - compressed_size / max(uncompressed_size, 1)) * 100.0, 2),
        "actual_record_counts": counts,
    }
    (out_dir / "release_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest
