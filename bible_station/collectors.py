"""
Clean, Zero-Dependency Collectors & Modular Catalog Re-exports.
Uses Python stdlib html.parser only (zero third-party runtime dependencies).
"""

from __future__ import annotations

import re
import time
import urllib.error
import urllib.request
from html.parser import HTMLParser
from typing import Any, Callable, Dict, List, Optional, Tuple

from . import __version__
from .canon import BibleBookMeta, calculate_verse_id, resolve_book
from .catalog_commentaries import build_expanded_exegesis_dataset
from .catalog_worship import build_expanded_worship_catalog


class _BskoreaChapterParser(HTMLParser):
    """Stdlib HTMLParser for bskorea.or.kr chapter pages."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._in_container = False
        self._has_td_bible = False
        self._container_depth = 0
        self._capture_title = False
        self._title_buf: List[str] = []
        self.current_section_title: Optional[str] = None

        self._in_verse_span = False
        self._verse_depth = 0
        self._in_number_span = False
        self._number_buf: List[str] = []

        self._in_comment_a = False
        self._comment_id: str = ""
        self._comment_buf: List[str] = []

        self._in_d2_div = False
        self._d2_depth = 0
        self._d2_id: str = ""
        self._d2_buf: List[str] = []
        self._d2_ref_links: List[Tuple[str, str]] = []
        self._in_tar_a = False
        self._tar_val = ""
        self._tar_buf: List[str] = []

        self._verse_text_buf: List[str] = []
        self._marker_by_id: Dict[str, str] = {}
        self._footnotes: List[Dict[str, str]] = []
        self._cross_refs: List[Dict[str, str]] = []

        self.raw_verses: List[Dict[str, Any]] = []

    @staticmethod
    def _attrs_dict(attrs: List[Tuple[str, Optional[str]]]) -> Dict[str, str]:
        return {k.lower(): (v or "") for k, v in attrs}

    @staticmethod
    def _classes(attrs_map: Dict[str, str]) -> set[str]:
        return set(attrs_map.get("class", "").split())

    def _begin_verse_span(self) -> None:
        self._in_verse_span = True
        self._verse_depth = 1
        self._in_number_span = False
        self._number_buf = []
        self._in_comment_a = False
        self._in_d2_div = False
        self._d2_depth = 0
        self._verse_text_buf = []
        self._marker_by_id = {}
        self._footnotes = []
        self._cross_refs = []

    def _finish_verse_span(self) -> None:
        self._in_verse_span = False
        num_str = "".join(self._number_buf)
        m = re.search(r"\d+", num_str)
        if not m:
            return
        verse_num = int(m.group())
        clean_text = re.sub(r"\s+", " ", "".join(self._verse_text_buf)).strip()
        self.raw_verses.append({
            "verse": verse_num,
            "text": clean_text,
            "section_title": self.current_section_title,
            "footnotes": self._footnotes,
            "cross_refs": self._cross_refs,
        })

    _VOID_TAGS = frozenset({"br", "hr", "img", "input", "meta", "link", "area", "base", "col", "embed", "param", "source", "track", "wbr"})

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        tag = tag.lower()
        amap = self._attrs_dict(attrs)
        classes = self._classes(amap)

        if tag == "div" and amap.get("id") == "tdBible1":
            self._in_container = True
            self._has_td_bible = True
            self._container_depth = 1
            return

        if self._has_td_bible and not self._in_container:
            return

        if tag in self._VOID_TAGS:
            return

        if self._in_container:
            self._container_depth += 1

        # Top-level child inside container (or root if no tdBible1)
        at_child_level = (not self._has_td_bible and not self._in_verse_span) or (
            self._in_container and self._container_depth == 2 and not self._in_verse_span
        )

        if at_child_level and tag == "font" and "smallTitle" in classes:
            self._capture_title = True
            self._title_buf = []
            return

        if at_child_level and tag == "span":
            self._begin_verse_span()
            return

        if self._in_verse_span:
            self._verse_depth += 1
            if tag == "span" and "number" in classes:
                self._in_number_span = True
                self._number_buf = []
                return
            if tag == "a" and "comment" in classes:
                self._in_comment_a = True
                m = re.search(r"clickPopUp\('([^']+)'", amap.get("onclick", ""))
                self._comment_id = m.group(1) if m else ""
                self._comment_buf = []
                return
            if tag == "div" and "D2" in classes:
                self._in_d2_div = True
                self._d2_depth = 1
                self._d2_id = amap.get("id", "")
                self._d2_buf = []
                self._d2_ref_links = []
                return
            if self._in_d2_div:
                self._d2_depth += 1
                if tag == "a" and "tar" in amap:
                    self._in_tar_a = True
                    self._tar_val = amap["tar"]
                    self._tar_buf = []
                    return

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in self._VOID_TAGS:
            return
        if self._has_td_bible and not self._in_container:
            return

        if self._capture_title and tag == "font":
            self._capture_title = False
            self.current_section_title = "".join(self._title_buf).strip()

        if self._in_verse_span:
            if self._in_tar_a and tag == "a":
                self._in_tar_a = False
                self._d2_ref_links.append(("".join(self._tar_buf).strip(), self._tar_val))
            elif self._in_comment_a and tag == "a":
                self._in_comment_a = False
                if self._comment_id:
                    self._marker_by_id[self._comment_id] = "".join(self._comment_buf).strip()
            elif self._in_number_span and tag == "span":
                self._in_number_span = False

            if self._in_d2_div:
                self._d2_depth -= 1
                if self._d2_depth <= 0:
                    self._in_d2_div = False
                    marker = self._marker_by_id.get(self._d2_id, "")
                    if self._d2_ref_links:
                        for ref_text, tar_val in self._d2_ref_links:
                            self._cross_refs.append({
                                "marker": marker,
                                "target_ref": ref_text,
                                "target_tar": tar_val,
                            })
                    else:
                        note_text = "".join(self._d2_buf).strip()
                        if note_text:
                            self._footnotes.append({"marker": marker, "text": note_text})

            self._verse_depth -= 1
            if self._verse_depth <= 0:
                self._finish_verse_span()

        if self._in_container:
            self._container_depth -= 1
            if self._container_depth <= 0:
                self._in_container = False

    def handle_data(self, data: str) -> None:
        if self._capture_title:
            self._title_buf.append(data)
            return
        if not self._in_verse_span:
            return
        if self._in_number_span:
            self._number_buf.append(data)
        elif self._in_comment_a:
            self._comment_buf.append(data)
        elif self._in_tar_a:
            self._tar_buf.append(data)
        elif self._in_d2_div:
            self._d2_buf.append(data)
        else:
            self._verse_text_buf.append(data)


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
        self._last_request_ts: Optional[float] = None

    @staticmethod
    def _default_http_get(url: str) -> str:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": f"BibleCommentaryStation/{__version__} (Educational Read-Only Research)"},
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            charset = resp.headers.get_content_charset() or "utf-8"
            raw_bytes = resp.read()
        text = raw_bytes.decode(charset, errors="strict")
        if "\ufffd" in text:
            raise ValueError(f"Decoded response from {url} contains replacement character U+FFFD")
        return text

    @staticmethod
    def resolve_book(identifier: int | str) -> Optional[BibleBookMeta]:
        return resolve_book(identifier)

    def build_url(self, book_identifier: int | str, chapter: int, version: Optional[str] = None) -> str:
        meta = resolve_book(book_identifier)
        if not meta:
            raise ValueError(f"Unknown book identifier: {book_identifier}")
        ver = version or self.default_version
        return f"{self.BASE_URL}?version={ver}&book={meta.bskorea_code}&chap={chapter}&sec=1"

    def _enforce_rate_limit(self) -> None:
        if self.delay_seconds <= 0:
            return
        now = time.monotonic()
        if self._last_request_ts is not None:
            elapsed = now - self._last_request_ts
            if elapsed < self.delay_seconds:
                time.sleep(self.delay_seconds - elapsed)
        self._last_request_ts = time.monotonic()

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
            self._enforce_rate_limit()
            try:
                html = self._http_getter(url)
                return self.parse_chapter_html(html, meta.book_id, chapter, ver)
            except (UnicodeDecodeError, ValueError):
                raise
            except urllib.error.HTTPError as exc:
                last_err = exc
                if 400 <= exc.code < 500 and exc.code != 429:
                    raise RuntimeError(f"HTTP {exc.code} fetching {url}: {exc}") from exc
                if attempt + 1 < retries and self.delay_seconds > 0:
                    time.sleep(self.delay_seconds)
            except (urllib.error.URLError, TimeoutError, OSError) as exc:
                last_err = exc
                if attempt + 1 < retries and self.delay_seconds > 0:
                    time.sleep(self.delay_seconds)
        raise RuntimeError(f"Failed to fetch {url}: {last_err}") from last_err

    @staticmethod
    def parse_chapter_html(
        html: str, book_id: int, chapter: int, version_code: str = "GAE"
    ) -> List[Dict[str, Any]]:
        if "\ufffd" in html:
            raise ValueError("HTML payload contains Unicode replacement character U+FFFD (decode corruption)")

        parser = _BskoreaChapterParser()
        parser.feed(html)
        parser.close()

        verses: List[Dict[str, Any]] = []
        for item in parser.raw_verses:
            verse_num = item["verse"]
            verses.append({
                "verse_id": calculate_verse_id(book_id, chapter, verse_num),
                "book_id": book_id,
                "chapter": chapter,
                "verse": verse_num,
                "version_code": version_code,
                "text": item["text"],
                "section_title": item["section_title"],
                "footnotes": item["footnotes"],
                "cross_refs": item["cross_refs"],
            })
        return verses


def get_curated_exegesis_dataset() -> Dict[str, Any]:
    return build_expanded_exegesis_dataset()


def get_worship_catalog() -> Dict[str, Any]:
    return build_expanded_worship_catalog()
