"""Unified CLI Entrypoint for Bible Commentary Station v2.0."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .builder import BibleDatabaseBuilder, export_zero_cost_bundle
from .schema import generate_drift_schema

REPO_ROOT = Path(__file__).resolve().parent.parent


def cmd_build(args: argparse.Namespace) -> None:
    db_path = Path(args.db_path)
    krv_path = Path(args.krv_json)

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
            web_stats = builder.export_web_chunks(Path(args.web_data_dir))
            print(f"[build] Exported 66 lazy-load web chunks: {web_stats}")

    if args.export_bundle:
        manifest = export_zero_cost_bundle(db_path, Path(args.bundle_dir))
        print(f"[build] Zero-cost bundle exported: {manifest['compressed_file_name']} "
              f"({manifest['compression_ratio_pct']}% reduction)")


def cmd_sync_drift(args: argparse.Namespace) -> None:
    out = generate_drift_schema(Path(args.output))
    print(f"[sync-drift] Generated Drift schema from SSOT -> {out}")


def main() -> None:
    parser = argparse.ArgumentParser(prog="bible-station", description="Bible Commentary Station v2.0 CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p_build = sub.add_parser("build", help="Build SQLite FTS5 DB, web chunks, and zero-cost bundle")
    p_build.add_argument("--db-path", default=str(REPO_ROOT / "data" / "bible_pastoral_core.db"))
    p_build.add_argument("--krv-json", default=str(REPO_ROOT / "data" / "raw" / "bible_1961_krv.json"))
    p_build.add_argument("--export-web", action="store_true", help="Export 66 per-book JSON chunks for PWA")
    p_build.add_argument("--web-data-dir", default=str(REPO_ROOT / "web" / "data"))
    p_build.add_argument("--export-bundle", action="store_true", help="Export gzip + SHA-256 manifest bundle")
    p_build.add_argument("--bundle-dir", default=str(REPO_ROOT / "dist"))
    p_build.set_defaults(func=cmd_build)

    p_drift = sub.add_parser("sync-drift", help="Generate Flutter Drift schema from Python SSOT")
    p_drift.add_argument("--output", default=str(REPO_ROOT / "lib" / "data" / "local" / "database_schema.drift"))
    p_drift.set_defaults(func=cmd_sync_drift)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
