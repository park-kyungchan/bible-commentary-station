"""
Clean, Portable Collectors & Modular Catalog Re-exports.
"""

from __future__ import annotations

import re
import time
import urllib.request
from typing import Any, Callable, Dict, List, Optional

from bs4 import BeautifulSoup

from .canon import BibleBookMeta, calculate_verse_id, resolve_book
from .catalog_commentaries import build_expanded_exegesis_dataset
from .catalog_worship import build_expanded_worship_catalog


class BskoreaCollector:
    BASE_URL = "https://www.bskorea.or.kr/bible/korbibReadpage.php"

    def __init__(
        self,
        default_version: str = "GAE",
        delay_seconds: float = 1.0,
        http_getter: Optional[Callable[[str], str]] = None,
    ):
        self.default_version = default_version
        self.delay_seconds = delay_seconds
        self._http_getter = http_getter or self._default_http_get

    @staticmethod
    def _default_http_get(url: str) -> str:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "BibleCommentaryStation/2.4 (Educational Read-Only Research)"},
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.read().decode("utf-8", errors="replace")

    @staticmethod
    def resolve_book(identifier: int | str) -> Optional[BibleBookMeta]:
        return resolve_book(identifier)

    def build_url(self, book_identifier: int | str, chapter: int, version: Optional[str] = None) -> str:
        meta = resolve_book(book_identifier)
        if not meta:
            raise ValueError(f"Unknown book identifier: {book_identifier}")
        ver = version or self.default_version
        return f"{self.BASE_URL}?version={ver}&book={meta.bskorea_code}&chap={chapter}&sec=1"

    def fetch_chapter(
        self, book_identifier: int | str, chapter: int, version: Optional[str] = None, retries: int = 2
    ) -> List[Dict[str, Any]]:
        meta = resolve_book(book_identifier)
        if not meta:
            raise ValueError(f"Unknown book identifier: {book_identifier}")
        ver = version or self.default_version
        url = self.build_url(meta.book_id, chapter, ver)
        last_err: Optional[Exception] = None
        for attempt in range(retries):
            try:
                html = self._http_getter(url)
                return self.parse_chapter_html(html, meta.book_id, chapter, ver)
            except Exception as exc:
                last_err = exc
                if attempt + 1 < retries and self.delay_seconds > 0:
                    time.sleep(self.delay_seconds)
        raise RuntimeError(f"Failed to fetch {url}: {last_err}") from last_err

    @staticmethod
    def parse_chapter_html(
        html: str, book_id: int, chapter: int, version_code: str = "GAE"
    ) -> List[Dict[str, Any]]:
        soup = BeautifulSoup(html, "html.parser")
        container = soup.find("div", id="tdBible1") or soup
        current_section_title: Optional[str] = None
        verses: List[Dict[str, Any]] = []

        for elem in container.find_all(["font", "span"], recursive=False):
            if elem.name == "font" and "smallTitle" in (elem.get("class") or []):
                current_section_title = elem.get_text(strip=True)
                continue
            if elem.name != "span":
                continue
            num_span = elem.find("span", class_="number")
            if not num_span:
                continue
            num_match = re.search(r"\d+", num_span.get_text())
            if not num_match:
                continue
            verse_num = int(num_match.group())

            footnotes: List[Dict[str, str]] = []
            cross_refs: List[Dict[str, str]] = []
            marker_by_id: Dict[str, str] = {}
            for a_tag in elem.find_all("a", class_="comment"):
                m = re.search(r"clickPopUp\('([^']+)'", a_tag.get("onclick", ""))
                if m:
                    marker_by_id[m.group(1)] = a_tag.get_text(strip=True)
                a_tag.decompose()
            for div_tag in elem.find_all("div", class_="D2"):
                marker = marker_by_id.get(div_tag.get("id", ""), "")
                ref_links = div_tag.find_all("a", attrs={"tar": True})
                if ref_links:
                    for link in ref_links:
                        cross_refs.append({
                            "marker": marker,
                            "target_ref": link.get_text(strip=True),
                            "target_tar": link.get("tar", ""),
                        })
                else:
                    note_text = div_tag.get_text(strip=True)
                    if note_text:
                        footnotes.append({"marker": marker, "text": note_text})
                div_tag.decompose()

            num_span.decompose()
            clean_text = re.sub(r"\s+", " ", elem.get_text()).strip()
            verses.append({
                "verse_id": calculate_verse_id(book_id, chapter, verse_num),
                "book_id": book_id,
                "chapter": chapter,
                "verse": verse_num,
                "version_code": version_code,
                "text": clean_text,
                "section_title": current_section_title,
                "footnotes": footnotes,
                "cross_refs": cross_refs,
            })
        return verses


def get_curated_exegesis_dataset() -> Dict[str, Any]:
    return build_expanded_exegesis_dataset()


def get_worship_catalog() -> Dict[str, Any]:
    return build_expanded_worship_catalog()
