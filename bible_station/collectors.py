"""
Clean, Portable Collectors & Curated Sample Exegesis Provider.
- Zero hardcoded personal paths or machine-specific virtualenvs.
- Built-in urllib fallback when optional scrapling is not installed.
- Injectable HTTP fetcher for deterministic offline unit testing.
"""

from __future__ import annotations

import re
import time
import urllib.request
from typing import Any, Callable, Dict, List, Optional

from bs4 import BeautifulSoup

from .canon import BibleBookMeta, calculate_verse_id, resolve_book


class BskoreaCollector:
    """Read-only, rate-limited HTML parser & collector for BSKorea scripture pages."""

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
            headers={"User-Agent": "BibleCommentaryStation/2.0 (Educational Read-Only Research)"},
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
        self,
        book_identifier: int | str,
        chapter: int,
        version: Optional[str] = None,
        retries: int = 2,
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
        """Parse BSKorea chapter HTML cleanly, separating verse text, footnotes, and cross-refs."""
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

            # Extract popup notes & cross-refs before removing them from clean text
            marker_by_id: Dict[str, str] = {}
            for a_tag in elem.find_all("a", class_="comment"):
                onclick = a_tag.get("onclick", "")
                m = re.search(r"clickPopUp\('([^']+)'", onclick)
                marker = a_tag.get_text(strip=True)
                if m:
                    marker_by_id[m.group(1)] = marker
                a_tag.decompose()

            for div_tag in elem.find_all("div", class_="D2"):
                div_id = div_tag.get("id", "")
                marker = marker_by_id.get(div_id, "")
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
    """
    Structured, non-sectarian pastoral exegesis sample dataset covering all 8 commentaries,
    Strong's Hebrew/Greek lexicon, TSK cross-references, and multi-testament chain references.
    Explicitly tagged with provenance so UI renders transparent source badges.
    """
    provenance = [
        {
            "source_id": "krv_1961_public_domain",
            "category": "BIBLE",
            "title": "개역한글판 (1961)",
            "rights_status": "PUBLIC_DOMAIN",
            "attribution": "Korean Revised Version © Korean Bible Society 1961 (저작권 보호기간 만료)",
            "source_url": "https://bible.bskorea.or.kr/copyright_notice",
        },
        {
            "source_id": "sample_exegesis_v2",
            "category": "COMMENTARY",
            "title": "8대 주석 구조화 연구 샘플",
            "rights_status": "SAMPLE_EXEGESIS",
            "attribution": "로컬 연구용 구조화 주석 샘플 (실제 저작권 완본 DB 교체 가능)",
            "source_url": None,
        },
        {
            "source_id": "strongs_public_domain",
            "category": "LEXICON",
            "title": "Strong's Hebrew & Greek Lexicon",
            "rights_status": "PUBLIC_DOMAIN",
            "attribution": "Public Domain Strong's Exhaustive Concordance + 한글 번역",
            "source_url": "https://github.com/openscriptures/strongs",
        },
        {
            "source_id": "tsk_public_domain",
            "category": "CROSS_REF",
            "title": "Treasury of Scripture Knowledge (TSK)",
            "rights_status": "PUBLIC_DOMAIN",
            "attribution": "Public Domain TSK Cross-Reference Corpus",
            "source_url": "https://github.com/scrollmapper/bible_databases",
        },
    ]

    # All 8 commentary sources represented across key pastoral passages (Gen 1:1, Gen 22:2, Jhn 3:16, 1Th 5:23)
    commentaries = [
        # Genesis 22:2 — All 8 sources
        {
            "source_code": "OXFORD", "book_id": 1, "chapter_start": 22, "verse_start": 2,
            "chapter_end": 22, "verse_end": 2, "passage_display": "창세기 22:2",
            "title": "원어 형태론 분해: 카흐-나(קַח־נָא)와 야히드(יָחִיד)",
            "content_markdown": "히브리어 'קַח־נָא'(카흐-나)는 칼 명령형에 간청의 불변사 '나'가 결합되어 강압이 아닌 깊은 신뢰의 요청을 나타낸다. '네 사랑하는 독자'(יְחִידְךָ אֲשֶׁר־אָהַבְתָּ)의 '야히드'는 유일무이하고 생명처럼 귀한 존재를 뜻한다.",
            "theological_tags": "원어강해, 순종, 야히드",
            "practical_points": "하나님은 가장 소중한 것을 통해 믿음의 중심을 점검하신다.",
        },
        {
            "source_code": "WESLEY", "book_id": 1, "chapter_start": 22, "verse_start": 2,
            "chapter_end": 22, "verse_end": 2, "passage_display": "창세기 22:2",
            "title": "존 웨슬리 주석: 온전한 헌신과 믿음의 시험",
            "content_markdown": "아브라함에게 요구된 시험은 자신의 뜻을 비우고 하나님의 선하심에 전적으로 의탁하는 성화의 절정이다. 약속의 선물보다 약속을 주신 하나님 자신을 더 사랑하는지 확증하는 자리이다.",
            "theological_tags": "웨슬리안, 성화, 헌신",
            "practical_points": "선물보다 선물을 주신 하나님을 앞세우는 성숙한 믿음.",
        },
        {
            "source_code": "HOKMA", "book_id": 1, "chapter_start": 22, "verse_start": 2,
            "chapter_end": 22, "verse_end": 2, "passage_display": "창세기 22:2",
            "title": "호크마 종합주석: 모리아 땅의 구속사적 의미",
            "content_markdown": "모리아 산은 훗날 솔로몬 성전이 세워진 장소(대하 3:1)이자 인류 구속의 대속 제사가 성취될 예루살렘 언덕과 연결된다. 이삭의 번제 사건은 구약 전체에서 가장 선명한 대속의 예표이다.",
            "theological_tags": "종합주해, 모리아산, 구속사",
            "practical_points": "구약의 그림자는 신약의 십자가 은혜로 완성된다.",
        },
        {
            "source_code": "GRAND", "book_id": 1, "chapter_start": 22, "verse_start": 2,
            "chapter_end": 22, "verse_end": 2, "passage_display": "창세기 22:2",
            "title": "그랜드 종합주석: 3대지 설교 구조",
            "content_markdown": "I. 내려놓음의 시험: 가장 귀한 애착을 주님께 드리는 결단\nII. 사흘 길의 동행: 질문보다 순종으로 걷는 침묵의 믿음\nIII. 여호와 이레의 공급: 순종의 끝에서 예비하시는 하나님",
            "theological_tags": "설교대지, 여호와이레",
            "practical_points": "순종의 고난과 여호와 이레의 공급을 균형 있게 선포할 것.",
        },
        {
            "source_code": "CHARISMA", "book_id": 1, "chapter_start": 22, "verse_start": 2,
            "chapter_end": 22, "verse_end": 2, "passage_display": "창세기 22:2",
            "title": "카리스마 주석: 즉각적 순종과 영적 돌파",
            "content_markdown": "아브라함은 다음 날 아침 일찍 일어나 순종했다(22:3). 망설임 없는 순종이 영적 정체를 돌파하고 여호와 이레의 기적을 열어젖힌다.",
            "theological_tags": "성령론, 즉각순종, 돌파",
            "practical_points": "지체된 순종은 불순종이 될 수 있다; 오늘의 작은 순종부터 시작하라.",
        },
        {
            "source_code": "MATTHEW_HENRY", "book_id": 1, "chapter_start": 22, "verse_start": 2,
            "chapter_end": 22, "verse_end": 2, "passage_display": "창세기 22:2",
            "title": "매튜 헨리 주석: 시험의 깊이와 은혜의 깊이",
            "content_markdown": "하나님께서 '네 아들, 네 독자, 네 사랑하는 이삭'이라 거듭 부르심은 시험의 고통을 덜어주시려는 것이 아니라, 그 희생의 가치를 하나님께서 온전히 알고 계심을 보여준다.",
            "theological_tags": "경건묵상, 희생, 은혜",
            "practical_points": "하나님은 우리의 눈물과 희생의 무게를 정확히 헤아리신다.",
        },
        {
            "source_code": "BAKER", "book_id": 1, "chapter_start": 22, "verse_start": 2,
            "chapter_end": 22, "verse_end": 2, "passage_display": "창세기 22:2",
            "title": "베이커 배경주석: 고대 근동의 인신제사와 하나님의 차별성",
            "content_markdown": "가나안 주변 민족들은 신의 노여움을 달래기 위해 자녀를 제물로 바쳤으나, 여호와 하나님은 22:12에서 손을 멈추게 하시고 숫양을 예비하심으로써 인신제사를 단호히 배격하는 언약의 하나님이심을 드러내신다.",
            "theological_tags": "배경사, 고대근동, 언약",
            "practical_points": "하나님은 생명을 빼앗는 우상이 아니라 생명을 대신 내어주시는 구원자이시다.",
        },
        {
            "source_code": "ESV_EXPOSITORY", "book_id": 1, "chapter_start": 22, "verse_start": 2,
            "chapter_end": 22, "verse_end": 2, "passage_display": "창세기 22:2",
            "title": "ESV 해설주석: 창세기 언약의 절정과 복음의 예표",
            "content_markdown": "창세기 12장의 부르심('떠나라', 레크 레카)과 22장의 명령('가라', 레크 레카)은 동일한 히브리어 표현으로 수미쌍관을 이룬다. 아브라함의 여정은 하나님이 친히 어린 양을 준비하시는 복음으로 귀결된다.",
            "theological_tags": "구속사강해, 레크레카, 복음",
            "practical_points": "부르심의 시작과 절정 모두 하나님의 신실하심에 달려 있다.",
        },
        # Genesis 1:1
        {
            "source_code": "OXFORD", "book_id": 1, "chapter_start": 1, "verse_start": 1,
            "chapter_end": 1, "verse_end": 1, "passage_display": "창세기 1:1",
            "title": "원어 강해: 베레쉬트(בְּרֵאשִׁית)와 바라(בָּרָא)",
            "content_markdown": "동사 '바라(בָּרָא)'는 구약에서 오직 하나님만을 주어로 취하는 무(無)에서의 창조(creatio ex nihilo)를 가리킨다. 복수형 명사 '엘로힘'이 단수 동사 '바라'와 결합하여 유일하신 하나님의 충만한 권능을 선포한다.",
            "theological_tags": "원어강해, 창조, 바라",
            "practical_points": "모든 역사와 인생의 출발점은 무에서 유를 창조하시는 하나님이다.",
        },
        {
            "source_code": "MATTHEW_HENRY", "book_id": 1, "chapter_start": 1, "verse_start": 1,
            "chapter_end": 1, "verse_end": 1, "passage_display": "창세기 1:1",
            "title": "매튜 헨리 주석: 시간과 우주의 시작",
            "content_markdown": "성경의 첫 문장은 무신론과 범신론과 영원물질론을 단숨에 논파한다. 세상은 우연의 산물이 아니라 영원하신 창조주의 지혜로운 뜻으로 시작되었다.",
            "theological_tags": "경건묵상, 창조주",
            "practical_points": "창조주를 경외하는 것이 모든 지혜와 평안의 근본이다.",
        },
        # John 3:16
        {
            "source_code": "WESLEY", "book_id": 43, "chapter_start": 3, "verse_start": 16,
            "chapter_end": 43, "verse_end": 16, "passage_display": "요한복음 3:16",
            "title": "존 웨슬리 주석: 세상을 향한 보편적 사랑",
            "content_markdown": "'이처럼 사랑하사'는 인간의 언어로 측량할 수 없는 하나님의 자비를 가리킨다. 복음의 초대장은 특정 소수가 아닌 '누구든지 믿는 자' 모두에게 열려 있다.",
            "theological_tags": "웨슬리안, 사랑, 복음",
            "practical_points": "복음은 누구에게나 열려 있는 하나님의 은혜의 선물이다.",
        },
        {
            "source_code": "ESV_EXPOSITORY", "book_id": 43, "chapter_start": 3, "verse_start": 16,
            "chapter_end": 43, "verse_end": 16, "passage_display": "요한복음 3:16",
            "title": "ESV 해설주석: 독생자(모노게네스)와 창세기 22장의 성취",
            "content_markdown": "헬라어 '모노게네스'(μονογενής, 독생자)는 70인역(LXX)에서 창세기 22장 이삭의 '야히드'와 공명한다. 아브라함이 멈춘 자리에서 하나님 아버지는 친히 독생자를 내어주셨다.",
            "theological_tags": "구속사강해, 독생자, 사랑",
            "practical_points": "십자가는 하나님의 사랑이 역사 속에서 확증된 최고의 증거이다.",
        },
        # 1 Thessalonians 5:23 (for multi-source join benchmark & pastoral holiness)
        {
            "source_code": "OXFORD", "book_id": 52, "chapter_start": 5, "verse_start": 23,
            "chapter_end": 52, "verse_end": 23, "passage_display": "데살로니가전서 5:23",
            "title": "원어 강해: 홀로텔레이스(ὁλοτελεῖς, 온전히)",
            "content_markdown": "신약 유일어(hapax legomenon) '홀로텔레이스'는 '전체(홀로스)'와 '완성(텔로스)'의 합성어로, 영과 혼과 몸 전 인격이 하나님의 평강 안에서 온전히 거룩하게 보존되기를 구하는 축도이다.",
            "theological_tags": "원어강해, 거룩, 평강",
            "practical_points": "거룩은 인간의 노력이 아니라 평강의 하나님이 친히 이루시는 은혜다.",
        },
        {
            "source_code": "WESLEY", "book_id": 52, "chapter_start": 5, "verse_start": 23,
            "chapter_end": 52, "verse_end": 23, "passage_display": "데살로니가전서 5:23",
            "title": "존 웨슬리 주석: 전인적 거룩과 미쁘신 하나님",
            "content_markdown": "사도 바울은 성도의 영과 혼과 몸 전체가 흠 없게 보전되기를 기도한다. 24절의 '너희를 부르시는 이는 미쁘시니 그가 또한 이루시리라'는 약속이 이 기도의 확실한 보증이다.",
            "theological_tags": "웨슬리안, 성화, 약속",
            "practical_points": "우리를 부르신 분이 또한 우리 안에서 선한 일을 이루신다.",
        },
    ]

    for c in commentaries:
        c["verse_start_id"] = calculate_verse_id(c["book_id"], c["chapter_start"], c["verse_start"])
        c["verse_end_id"] = calculate_verse_id(c["book_id"], c["chapter_end"], c["verse_end"])
        c["provenance_id"] = "sample_exegesis_v2"

    strongs = [
        {
            "strong_id": "H7225", "language": "HEBREW", "lemma": "רֵאשִׁית",
            "transliteration": "rêshîyth", "pronunciation": "레쉬트", "part_of_speech": "명사(여성)",
            "definition_kr": "태초, 시작, 첫 열매, 으뜸", "definition_en": "beginning, chief, firstfruits",
            "occurrence_count": 51,
        },
        {
            "strong_id": "H1254", "language": "HEBREW", "lemma": "בָּרָא",
            "transliteration": "bârâʼ", "pronunciation": "바라", "part_of_speech": "동사",
            "definition_kr": "창조하다 (오직 하나님을 주어로 하는 무에서의 창조)", "definition_en": "to create, shape, form",
            "occurrence_count": 54,
        },
        {
            "strong_id": "H0430", "language": "HEBREW", "lemma": "אֱלֹהִים",
            "transliteration": "ʼĕlôhîym", "pronunciation": "엘로힘", "part_of_speech": "명사(남성복수)",
            "definition_kr": "하나님, 전능하신 창조주", "definition_en": "God, rulers, judges",
            "occurrence_count": 2606,
        },
        {
            "strong_id": "H3173", "language": "HEBREW", "lemma": "יָחִיד",
            "transliteration": "yâchîyd", "pronunciation": "야히드", "part_of_speech": "형용사",
            "definition_kr": "유일한, 독자, 생명처럼 귀한 하나뿐인 존재", "definition_en": "only, unique, solitary, precious",
            "occurrence_count": 12,
        },
        {
            "strong_id": "H3327", "language": "HEBREW", "lemma": "יִצְחָק",
            "transliteration": "Yitschâq", "pronunciation": "이츠하크", "part_of_speech": "고유명사",
            "definition_kr": "이삭 ('그가 웃는다', 약속의 아들)", "definition_en": "Isaac (he laughs)",
            "occurrence_count": 112,
        },
        {
            "strong_id": "G0025", "language": "GREEK", "lemma": "ἀγαπάω",
            "transliteration": "agapáō", "pronunciation": "아가파오", "part_of_speech": "동사",
            "definition_kr": "무조건적으로 사랑하다, 언약적·희생적 사랑", "definition_en": "to love unconditionally",
            "occurrence_count": 143,
        },
        {
            "strong_id": "G3439", "language": "GREEK", "lemma": "μονογενής",
            "transliteration": "monogenḗs", "pronunciation": "모노게네스", "part_of_speech": "형용사",
            "definition_kr": "독생자, 유일무이한 외아들", "definition_en": "only begotten, one and only, unique",
            "occurrence_count": 9,
        },
    ]

    cross_refs = [
        # Gen 22:2 cross references
        {"from_verse_id": calculate_verse_id(1, 22, 2), "to_verse_id": calculate_verse_id(43, 3, 16), "score": 0.99, "relationship_type": "PROPHECY_FULFILLMENT", "note": "독자 이삭의 제사는 독생자 예수 그리스도를 내어주신 하나님의 사랑의 예표"},
        {"from_verse_id": calculate_verse_id(1, 22, 2), "to_verse_id": calculate_verse_id(45, 8, 32), "score": 0.97, "relationship_type": "EXPLANATORY", "note": "자기 아들을 아끼지 아니하신 하나님의 절대적 은혜"},
        {"from_verse_id": calculate_verse_id(1, 22, 2), "to_verse_id": calculate_verse_id(58, 11, 17), "score": 0.96, "relationship_type": "EXPLANATORY", "note": "시험을 받을 때 믿음으로 이삭을 드린 부활 신앙"},
        {"from_verse_id": calculate_verse_id(1, 22, 2), "to_verse_id": calculate_verse_id(59, 2, 21), "score": 0.92, "relationship_type": "THEMATIC", "note": "행함으로 온전해진 믿음의 본보기"},
        {"from_verse_id": calculate_verse_id(1, 22, 2), "to_verse_id": calculate_verse_id(14, 3, 1), "score": 0.91, "relationship_type": "PARALLEL", "note": "솔로몬 성전이 세워진 모리아 산"},
        # Gen 1:1 cross references
        {"from_verse_id": calculate_verse_id(1, 1, 1), "to_verse_id": calculate_verse_id(43, 1, 1), "score": 0.99, "relationship_type": "PARALLEL", "note": "태초에 계신 말씀(로고스)의 창조 사역"},
        {"from_verse_id": calculate_verse_id(1, 1, 1), "to_verse_id": calculate_verse_id(58, 11, 3), "score": 0.95, "relationship_type": "EXPLANATORY", "note": "믿음으로 모든 세계가 하나님의 말씀으로 지어진 줄 아나니"},
        {"from_verse_id": calculate_verse_id(1, 1, 1), "to_verse_id": calculate_verse_id(19, 33, 6), "score": 0.93, "relationship_type": "THEMATIC", "note": "여호와의 말씀으로 하늘이 지음이 되었음"},
        # John 3:16 cross references
        {"from_verse_id": calculate_verse_id(43, 3, 16), "to_verse_id": calculate_verse_id(45, 5, 8), "score": 0.98, "relationship_type": "THEMATIC", "note": "우리가 아직 죄인 되었을 때 그리스도께서 죽으심으로 확증된 사랑"},
        {"from_verse_id": calculate_verse_id(43, 3, 16), "to_verse_id": calculate_verse_id(62, 4, 9), "score": 0.96, "relationship_type": "PARALLEL", "note": "하나님의 독생자를 세상에 보내심으로 나타난 사랑"},
        # 1 Thess 5:23
        {"from_verse_id": calculate_verse_id(52, 5, 23), "to_verse_id": calculate_verse_id(58, 13, 20), "score": 0.95, "relationship_type": "PARALLEL", "note": "평강의 하나님의 축도와 온전케 하심"},
    ]

    chain_topics = [
        {
            "topic_key": "isaac",
            "title": "이삭 (Isaac — '웃음')",
            "meaning": "약속의 자녀 · 순종의 번제물 · 온유한 승리자",
            "summary": "창세기 21장의 초자연적 출생부터 모리아산의 순종, 르호봇의 양보, 그리고 신약 로마서·갈라디아서·히브리서의 구속사적 성취까지 이어지는 생애 연쇄 관주.",
            "links": [
                (calculate_verse_id(1, 21, 3), "창세기 21:3", "언약의 출생", "인간의 가능성이 끝난 100세에 약속으로 태어난 웃음의 아들."),
                (calculate_verse_id(1, 22, 2), "창세기 22:2", "모리아산 번제", "십자가에 죽기까지 복종하신 그리스도를 예표하는 순종."),
                (calculate_verse_id(1, 22, 9), "창세기 22:9", "자발적 순종", "청년 이삭이 제단 나무 위에 묵묵히 결박당한 온유한 복종."),
                (calculate_verse_id(1, 26, 12), "창세기 26:12", "백 배의 결실", "흉년 속에서도 약속의 땅에 머물며 순종할 때 주시는 공급."),
                (calculate_verse_id(1, 26, 22), "창세기 26:22", "르호봇의 온유함", "우물을 양보할 때 하나님이 지경을 넓히시는 온유의 승리."),
                (calculate_verse_id(45, 9, 7), "로마서 9:7", "언약의 계승", "육신의 자녀가 아닌 약속의 자녀로 세워지는 구속사 원리."),
                (calculate_verse_id(48, 4, 28), "갈라디아서 4:28", "약속의 자녀", "성령을 따라 난 자유한 성도의 정체성."),
                (calculate_verse_id(58, 11, 17), "히브리서 11:17", "부활 신앙", "죽은 자 가운데서도 다시 살리실 하나님을 신뢰한 믿음."),
            ],
        },
        {
            "topic_key": "abraham",
            "title": "아브라함 (Abraham — '열국의 아버지')",
            "meaning": "믿음의 조상 · 언약의 순례자 · 여호와 이레의 증인",
            "summary": "갈대아 우르의 소명(창 12장)에서 이신칭의(창 15:6), 모리아산 순종(창 22장), 신약 로마서 4장의 믿음의 본보기까지 관통하는 사슬망.",
            "links": [
                (calculate_verse_id(1, 12, 1), "창세기 12:1", "소명과 떠남", "본토와 친척을 떠나 말씀만 의지해 출발한 순례의 시작."),
                (calculate_verse_id(1, 15, 6), "창세기 15:6", "믿음과 의", "하나님을 믿으매 이를 의로 여기신 구약 이신칭의의 초석."),
                (calculate_verse_id(1, 22, 14), "창세기 22:14", "여호와 이레", "순종의 산에서 친히 예비하시는 하나님을 경험한 고백."),
                (calculate_verse_id(45, 4, 3), "로마서 4:3", "신약의 확증", "바울이 복음의 핵심으로 인용한 아브라함의 믿음."),
                (calculate_verse_id(58, 11, 8), "히브리서 11:8", "갈 바를 알지 못하나", "보이지 않는 약속의 도성을 바라본 순종의 발걸음."),
            ],
        },
    ]

    return {
        "provenance": provenance,
        "commentaries": commentaries,
        "strongs": strongs,
        "cross_refs": cross_refs,
        "chain_topics": chain_topics,
    }
