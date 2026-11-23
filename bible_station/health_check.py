"""
Periodic Operational Health Check CLI (`python3 -m bible_station.health_check`).

Probes:
1. HelloAO Live API (BSB/GEN/1.json, c/matthew-henry/GEN/1.json)
2. Official non-null commentary URLs in canon.py
3. Google Drive worship PPT link accessibility (bounded concurrency & backoff)
4. Live GitHub Pages manifest.json & SHA-256 verification

Writes a sanitized Markdown report (status codes, URLs/IDs, UTC timestamp — NEVER raw
external HTTP response bodies or credentials) for safe `--body-file` issue reporting.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from . import __version__
from .canon import COMMENTARY_SOURCES_MASTER

DEFAULT_PAGES_BASE = "https://park-kyungchan.github.io/bible-commentary-station"
HELLOAO_PROBES = (
    ("HelloAO BSB GEN 1", "https://bible.helloao.org/api/BSB/GEN/1.json"),
    ("HelloAO Matthew Henry GEN 1", "https://bible.helloao.org/api/c/matthew-henry/GEN/1.json"),
)
USER_AGENT = f"BibleCommentaryStation-HealthCheck/{__version__}"


@dataclass(frozen=True)
class HttpResponse:
    status: int
    body: bytes
    final_url: str


@dataclass(frozen=True)
class CheckResult:
    group: str
    target: str
    ok: bool
    status: int
    detail: str


HttpFetcher = Callable[[str, str, float], HttpResponse]


def default_http_fetch(url: str, method: str = "GET", timeout: float = 15.0) -> HttpResponse:
    req = urllib.request.Request(url, method=method, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = b"" if method == "HEAD" else resp.read()
            return HttpResponse(status=int(resp.status), body=body, final_url=resp.geturl())
    except urllib.error.HTTPError as exc:
        return HttpResponse(status=int(exc.code), body=b"", final_url=url)
    except (urllib.error.URLError, TimeoutError, OSError):
        return HttpResponse(status=0, body=b"", final_url=url)


def _sanitize_text(text: str, max_len: int = 160) -> str:
    """Keep only safe single-line ASCII/Korean diagnostic characters for report output."""
    cleaned = "".join(ch if (ch.isprintable() and ch not in "`\r\n") else " " for ch in text)
    cleaned = " ".join(cleaned.split())
    return cleaned[:max_len]


def check_helloao(fetcher: HttpFetcher = default_http_fetch) -> List[CheckResult]:
    results: List[CheckResult] = []
    for label, url in HELLOAO_PROBES:
        resp = fetcher(url, "GET", 15.0)
        if resp.status != 200:
            results.append(CheckResult("helloao", url, False, resp.status, f"{label}: HTTP {resp.status}"))
            continue
        try:
            payload = json.loads(resp.body.decode("utf-8"))
            has_expected = isinstance(payload, dict) and ("chapter" in payload or "book" in payload)
            if has_expected:
                results.append(CheckResult("helloao", url, True, resp.status, f"{label}: OK"))
            else:
                results.append(CheckResult("helloao", url, False, resp.status, f"{label}: unexpected JSON shape"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            results.append(CheckResult("helloao", url, False, resp.status, f"{label}: invalid JSON"))
    return results


def check_official_urls(fetcher: HttpFetcher = default_http_fetch) -> List[CheckResult]:
    results: List[CheckResult] = []
    for src in COMMENTARY_SOURCES_MASTER:
        url = src.get("official_url")
        if not url:
            continue
        url_str = str(url)
        resp = fetcher(url_str, "HEAD", 15.0)
        if resp.status in (403, 405, 0):
            resp = fetcher(url_str, "GET", 15.0)
        ok = 200 <= resp.status < 400
        results.append(
            CheckResult(
                "official_urls",
                url_str,
                ok,
                resp.status,
                f"{src['code']}: HTTP {resp.status}" if not ok else f"{src['code']}: OK",
            )
        )
    return results


def _probe_single_drive_id(
    drive_id: str,
    label: str,
    fetcher: HttpFetcher,
    retries: int = 2,
    backoff: float = 0.25,
) -> CheckResult:
    url = f"https://drive.google.com/file/d/{drive_id}/preview"
    status = 0
    final_url = url
    for attempt in range(retries):
        resp = fetcher(url, "HEAD", 15.0)
        if resp.status == 405:
            resp = fetcher(url, "GET", 15.0)
        status, final_url = resp.status, resp.final_url
        if status in (200, 302) and "accounts.google.com" not in final_url:
            return CheckResult("drive_links", drive_id, True, status, f"{label}: OK")
        if status == 429 or status >= 500 or status == 0:
            if attempt + 1 < retries and backoff > 0:
                time.sleep(backoff * (attempt + 1))
            continue
        break
    reason = "login-wall redirect" if "accounts.google.com" in final_url else f"HTTP {status}"
    return CheckResult("drive_links", drive_id, False, status, f"{label} ({drive_id}): {reason}")


def check_drive_links(
    fetcher: HttpFetcher = default_http_fetch,
    max_workers: int = 6,
    sample_limit: int = 20,
    backoff: float = 0.25,
) -> List[CheckResult]:
    pkg_dir = Path(__file__).resolve().parent
    targets: List[Tuple[str, str]] = []
    for fname, prefix in (("responsive_drive_ppts.json", "RR"), ("hymns_drive_ppts.json", "Hymn")):
        p = pkg_dir / fname
        if not p.exists():
            continue
        data = json.loads(p.read_text(encoding="utf-8"))
        keys = sorted(data.keys(), key=lambda x: int(x) if x.isdigit() else 9999)
        if sample_limit > 0 and len(keys) > sample_limit:
            step = max(len(keys) // sample_limit, 1)
            keys = keys[::step][:sample_limit]
        for k in keys:
            targets.append((data[k]["id"], f"{prefix} #{k}"))

    results: List[CheckResult] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, max_workers)) as pool:
        futs = [
            pool.submit(_probe_single_drive_id, drive_id, label, fetcher, 2, backoff)
            for drive_id, label in targets
        ]
        for fut in futs:
            results.append(fut.result())
    return results


def check_live_pages(
    pages_base: str = DEFAULT_PAGES_BASE,
    fetcher: HttpFetcher = default_http_fetch,
) -> List[CheckResult]:
    base = pages_base.rstrip("/")
    manifest_url = f"{base}/data/manifest.json"
    resp = fetcher(manifest_url, "GET", 15.0)
    if resp.status != 200:
        return [CheckResult("live_pages", manifest_url, False, resp.status, f"manifest.json HTTP {resp.status}")]
    try:
        manifest = json.loads(resp.body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return [CheckResult("live_pages", manifest_url, False, resp.status, "manifest.json invalid JSON")]

    results: List[CheckResult] = []
    schema_ver = manifest.get("schemaVersion")
    checksums = manifest.get("checksums", {})
    if schema_ver != 3 or not isinstance(checksums, dict):
        results.append(
            CheckResult("live_pages", manifest_url, False, resp.status, f"Unexpected schemaVersion={schema_ver}")
        )
        return results
    results.append(CheckResult("live_pages", manifest_url, True, resp.status, "manifest.json schema v3 OK"))

    for rel_path in ("exegesis.json", "worship.json", "nkrv/GEN.json", "krv/GEN.json", "rnksv/GEN.json", "search/nkrv.json", "search/krv.json", "search/rnksv.json"):
        expected = checksums.get(rel_path)
        asset_url = f"{base}/data/{rel_path}"
        if not expected:
            results.append(CheckResult("live_pages", asset_url, False, 0, f"Missing checksum for {rel_path}"))
            continue
        r = fetcher(asset_url, "GET", 15.0)
        if r.status != 200:
            results.append(CheckResult("live_pages", asset_url, False, r.status, f"{rel_path}: HTTP {r.status}"))
            continue
        actual = hashlib.sha256(r.body).hexdigest()
        if actual != expected:
            results.append(CheckResult("live_pages", asset_url, False, r.status, f"{rel_path}: SHA-256 mismatch"))
        else:
            results.append(CheckResult("live_pages", asset_url, True, r.status, f"{rel_path}: SHA-256 verified"))
    return results


def render_sanitized_markdown(results: List[CheckResult], timestamp_utc: Optional[str] = None) -> str:
    ts = timestamp_utc or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    passed = sum(1 for r in results if r.ok)
    failed = [r for r in results if not r.ok]
    status_word = "HEALTHY" if not failed else "DEGRADED"

    lines = [
        f"# Bible Commentary Station Operational Health Report ({status_word})",
        "",
        f"- **Checked At (UTC)**: `{_sanitize_text(ts, 40)}`",
        f"- **Version**: `{__version__}`",
        f"- **Summary**: **{passed}/{len(results)} passed**, **{len(failed)} failed**",
        "",
    ]

    if failed:
        lines.extend([
            "## Failed Checks",
            "",
            "| Group | Target | HTTP Status | Diagnostic |",
            "|---|---|---:|---|",
        ])
        for r in failed:
            lines.append(
                f"| `{_sanitize_text(r.group, 32)}` | `{_sanitize_text(r.target, 120)}` | {int(r.status)} | {_sanitize_text(r.detail, 140)} |"
            )
        lines.append("")
    else:
        lines.append("All operational probes passed cleanly.")
        lines.append("")

    groups = sorted({r.group for r in results})
    lines.extend([
        "## Group Breakdown",
        "",
        "| Group | Passed | Total |",
        "|---|---:|---:|",
    ])
    for g in groups:
        g_items = [r for r in results if r.group == g]
        g_ok = sum(1 for r in g_items if r.ok)
        lines.append(f"| `{_sanitize_text(g, 32)}` | {g_ok} | {len(g_items)} |")
    lines.append("")
    return "\n".join(lines)


def run_health_checks(
    fetcher: HttpFetcher = default_http_fetch,
    pages_base: str = DEFAULT_PAGES_BASE,
    drive_sample_limit: int = 20,
    drive_backoff: float = 0.25,
    skip_pages: bool = False,
    skip_drive: bool = False,
) -> Tuple[bool, List[CheckResult]]:
    results: List[CheckResult] = []
    results.extend(check_helloao(fetcher=fetcher))
    results.extend(check_official_urls(fetcher=fetcher))
    if not skip_drive:
        results.extend(check_drive_links(fetcher=fetcher, sample_limit=drive_sample_limit, backoff=drive_backoff))
    if not skip_pages:
        results.extend(check_live_pages(pages_base=pages_base, fetcher=fetcher))
    all_ok = all(r.ok for r in results)
    return all_ok, results


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="bible-station-health",
        description=f"Bible Commentary Station v{__version__} Operational Health Check",
    )
    parser.add_argument("--report-out", type=Path, help="Write sanitized Markdown report to this path")
    parser.add_argument("--pages-base", default=DEFAULT_PAGES_BASE, help="Base URL of live GitHub Pages deployment")
    parser.add_argument("--drive-sample", type=int, default=20, help="Max Drive links sampled per catalog (0=all)")
    parser.add_argument("--skip-pages", action="store_true", help="Skip live GitHub Pages probe")
    parser.add_argument("--skip-drive", action="store_true", help="Skip Google Drive link probes")
    args = parser.parse_args(argv)

    all_ok, results = run_health_checks(
        pages_base=args.pages_base,
        drive_sample_limit=args.drive_sample,
        skip_pages=args.skip_pages,
        skip_drive=args.skip_drive,
    )
    report_md = render_sanitized_markdown(results)
    if args.report_out:
        args.report_out.parent.mkdir(parents=True, exist_ok=True)
        args.report_out.write_text(report_md, encoding="utf-8")
    print(report_md)
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
