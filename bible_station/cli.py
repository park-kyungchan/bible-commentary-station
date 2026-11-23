"""Unified CLI Entrypoint for Bible Commentary Station."""

from __future__ import annotations

import argparse
import os
import sqlite3
from pathlib import Path
from typing import Optional

from . import __version__
from .builder import BibleDatabaseBuilder, export_zero_cost_bundle, validate_web_corpus
from .schema import generate_drift_schema

REPO_ROOT = Path(__file__).resolve().parent.parent


def cmd_build(args: argparse.Namespace) -> None:
    db_path = Path(args.db_path)
    krv_path = Path(args.krv_json)
    source_date_epoch: Optional[int] = args.source_date_epoch
    if source_date_epoch is None and os.environ.get("SOURCE_DATE_EPOCH"):
        source_date_epoch = int(os.environ["SOURCE_DATE_EPOCH"])

    with BibleDatabaseBuilder(db_path) as builder:
        builder.initialize_schema()
        builder.seed_master_data()
        if krv_path.exists():
            count = builder.ingest_full_krv(krv_path)
            print(f"[build] Ingested {count:,} KRV verses (idempotent upsert).")
        else:
            print(f"[build] Warning: KRV JSON not found at {krv_path}; skipping full corpus.")

        stats = builder.ingest_curated_exegesis()
        print(f"[build] Ingested curated exegesis: {stats}")
        builder.optimize()
        print(f"[build] Actual DB counts: {builder.get_table_counts()}")

        if args.export_web:
            web_stats = builder.export_web_chunks(
                Path(args.web_data_dir),
                source_date_epoch=source_date_epoch,
            )
            print(f"[build] Exported 66 lazy-load web chunks & search index: {web_stats}")

    if args.export_bundle:
        manifest = export_zero_cost_bundle(db_path, Path(args.bundle_dir), version=__version__)
        print(
            f"[build] Zero-cost bundle exported: {manifest['compressed_file_name']} "
            f"({manifest['compression_ratio_pct']}% reduction)"
        )


def cmd_sync_drift(args: argparse.Namespace) -> None:
    out = generate_drift_schema(Path(args.output))
    print(f"[sync-drift] Generated Drift schema from SSOT -> {out}")


def cmd_validate(args: argparse.Namespace) -> None:
    conn = sqlite3.connect(str(args.db_path)) if args.db_path and Path(args.db_path).exists() else None
    try:
        report = validate_web_corpus(Path(args.web_data_dir), conn=conn)
    finally:
        if conn is not None:
            conn.close()
    print(f"[validate] Corpus OK: {report}")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="bible-station",
        description=f"Bible Commentary Station v{__version__} CLI",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    p_build = sub.add_parser("build", help="Build SQLite FTS5 DB, deterministic web chunks, and zero-cost bundle")
    p_build.add_argument("--db-path", default=str(REPO_ROOT / "data" / "bible_pastoral_core.db"))
    p_build.add_argument("--krv-json", default=str(REPO_ROOT / "data" / "raw" / "bible_1961_krv.json"))
    p_build.add_argument("--export-web", action="store_true", help="Export 66 per-book JSON chunks & search index")
    p_build.add_argument("--web-data-dir", default=str(REPO_ROOT / "web" / "data"))
    p_build.add_argument("--export-bundle", action="store_true", help="Export WAL-free gzip + SHA-256 manifest bundle")
    p_build.add_argument("--bundle-dir", default=str(REPO_ROOT / "dist"))
    p_build.add_argument("--source-date-epoch", type=int, default=None, help="Optional Unix epoch for manifest timestamp")
    p_build.set_defaults(func=cmd_build)

    p_drift = sub.add_parser("sync-drift", help="Generate Flutter Drift schema from Python SSOT")
    p_drift.add_argument("--output", default=str(REPO_ROOT / "lib" / "data" / "local" / "database_schema.drift"))
    p_drift.set_defaults(func=cmd_sync_drift)

    p_val = sub.add_parser("validate", help="Validate web/data corpus allowlist, checksums, and invariants")
    p_val.add_argument("--web-data-dir", default=str(REPO_ROOT / "web" / "data"))
    p_val.add_argument("--db-path", default=str(REPO_ROOT / "data" / "bible_pastoral_core.db"))
    p_val.set_defaults(func=cmd_validate)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
