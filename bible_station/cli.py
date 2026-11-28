"""Unified CLI Entrypoint for Bible Commentary Station v4.0."""

from __future__ import annotations

import argparse
import functools
import http.server
import os
import sqlite3
from pathlib import Path
from typing import Optional

from . import __version__
from .builder import BibleDatabaseBuilder, validate_web_corpus
from .graph import export_scripture_graph
from .pipeline import BuildContext, BuildPipeline, StageResult, ZeroCostBundleStage, default_db_stages
from .schema import generate_drift_schema

REPO_ROOT = Path(__file__).resolve().parent.parent


def _log_stage(res: StageResult) -> None:
    if res.status == "skipped":
        print(f"[pipeline:{res.name}] skipped")
    else:
        print(f"[pipeline:{res.name}] ok ({res.duration_ms:.1f}ms) -> {res.details}")


def cmd_build(args: argparse.Namespace) -> None:
    source_date_epoch: Optional[int] = args.source_date_epoch
    if source_date_epoch is None and os.environ.get("SOURCE_DATE_EPOCH"):
        source_date_epoch = int(os.environ["SOURCE_DATE_EPOCH"])

    ctx = BuildContext(
        db_path=Path(args.db_path),
        krv_json=Path(args.krv_json),
        web_data_dir=Path(args.web_data_dir),
        bundle_dir=Path(args.bundle_dir),
        export_web=bool(args.export_web),
        export_bundle=bool(args.export_bundle),
        export_graph=not bool(args.no_graph),
        source_date_epoch=source_date_epoch,
        version=__version__,
    )

    with BibleDatabaseBuilder(ctx.db_path) as builder:
        ctx.builder = builder
        BuildPipeline(default_db_stages(), on_stage_complete=_log_stage).run(ctx)

    ctx.builder = None
    BuildPipeline([ZeroCostBundleStage()], on_stage_complete=_log_stage).run(ctx)


def cmd_graph(args: argparse.Namespace) -> None:
    stats = export_scripture_graph(Path(args.web_data_dir))
    print(f"[graph] Exported deterministic knowledge graph -> {Path(args.web_data_dir) / 'graph.json'} ({stats})")


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


def cmd_serve(args: argparse.Namespace) -> None:
    directory = Path(args.web_dir).resolve()
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(directory))
    with http.server.ThreadingHTTPServer((args.host, args.port), handler) as httpd:
        print(f"[serve] Bible Commentary Station v{__version__} serving {directory} at http://{args.host}:{args.port}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n[serve] Stopped.")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="bible-station",
        description=f"Bible Commentary Station v{__version__} CLI",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    p_build = sub.add_parser("build", help="Run modular build pipeline (SQLite FTS5, web chunks, graph, bundle)")
    p_build.add_argument("--db-path", default=str(REPO_ROOT / "data" / "bible_pastoral_core.db"))
    p_build.add_argument("--krv-json", default=str(REPO_ROOT / "data" / "raw" / "bible_1961_krv.json"))
    p_build.add_argument("--export-web", action="store_true", help="Export 66 per-book JSON chunks & search index")
    p_build.add_argument("--web-data-dir", default=str(REPO_ROOT / "web" / "data"))
    p_build.add_argument("--export-bundle", action="store_true", help="Export WAL-free gzip + SHA-256 manifest bundle")
    p_build.add_argument("--bundle-dir", default=str(REPO_ROOT / "dist"))
    p_build.add_argument("--no-graph", action="store_true", help="Skip generating web/data/graph.json")
    p_build.add_argument("--source-date-epoch", type=int, default=None, help="Optional Unix epoch for manifest timestamp")
    p_build.set_defaults(func=cmd_build)

    p_graph = sub.add_parser("graph", help="Build deterministic scripture knowledge graph (web/data/graph.json)")
    p_graph.add_argument("--web-data-dir", default=str(REPO_ROOT / "web" / "data"))
    p_graph.set_defaults(func=cmd_graph)

    p_drift = sub.add_parser("sync-drift", help="Generate Flutter Drift schema from Python SSOT")
    p_drift.add_argument("--output", default=str(REPO_ROOT / "lib" / "data" / "local" / "database_schema.drift"))
    p_drift.set_defaults(func=cmd_sync_drift)

    p_val = sub.add_parser("validate", help="Validate web/data corpus allowlist, checksums, and invariants")
    p_val.add_argument("--web-data-dir", default=str(REPO_ROOT / "web" / "data"))
    p_val.add_argument("--db-path", default=str(REPO_ROOT / "data" / "bible_pastoral_core.db"))
    p_val.set_defaults(func=cmd_validate)

    p_serve = sub.add_parser("serve", help="Run zero-dependency local web server for v4.0 workstation")
    p_serve.add_argument("--web-dir", default=str(REPO_ROOT / "web"))
    p_serve.add_argument("--host", default="127.0.0.1")
    p_serve.add_argument("--port", type=int, default=8090)
    p_serve.set_defaults(func=cmd_serve)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
