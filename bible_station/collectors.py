"""
Clean, Portable Collectors, Expanded 12-Source Official Commentary Dataset,
and Korean Hymn / Responsive Reading (새찬송가 · 교독문) Quick-Lookup Catalog.
"""

from __future__ import annotations

import re
import time
import urllib.request
from typing import Any, Callable, Dict, List, Optional

from bs4 import BeautifulSoup

from .canon import BibleBookMeta, calculate_verse_id, resolve_book


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
            headers={"User-Agent": "BibleCommentaryStation/2.3 (Educational Read-Only Research)"},
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


def _c(src: str, b: int, ch: int, vs: int, disp: str, title: str, md: str, tags: str, pt: str) -> Dict[str, Any]:
    vid = calculate_verse_id(b, ch, vs)
    return {
        "source_code": src,
        "book_id": b,
        "chapter_start": ch,
        "verse_start": vs,
        "chapter_end": ch,
        "verse_end": vs,
        "verse_start_id": vid,
        "verse_end_id": vid,
        "passage_display": disp,
        "title": title,
        "content_markdown": md,
        "theological_tags": tags,
        "practical_points": pt,
        "provenance_id": "official_commentary_synthesis_v23",
    }


def get_curated_exegesis_dataset() -> Dict[str, Any]:
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
            "source_id": "official_commentary_synthesis_v23",
            "category": "COMMENTARY",
            "title": "12대 공식 권위 주석 핵심 강해",
            "rights_status": "SAMPLE_EXEGESIS",
            "attribution": "CCEL 공공도메인 고전(매튜 헨리·칼빈·웨슬리·JFB), SonicLight(컨스터블) 및 학술·설교 표준 주석 관점 요약",
            "source_url": "https://www.ccel.org/",
        },
        {
            "source_id": "strongs_public_domain",
            "category": "LEXICON",
            "title": "Strong's Hebrew & Greek Lexicon",
            "rights_status": "PUBLIC_DOMAIN",
            "attribution": "Public Domain Strong's Exhaustive Concordance + 한글 풀이",
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

    commentaries = [
        # --- 창세기 22:2 (12종 공식 주석 완비!) ---
        _c("MATTHEW_HENRY", 1, 22, 2, "창세기 22:2", "시험의 깊이와 하나님의 세심한 헤아리심",
           "하나님께서 '네 아들, 네 독자, 네 사랑하는 이삭'이라 거듭 부르심은 아브라함의 고통을 가볍게 보신 것이 아니라, 그 희생의 무게를 하나님께서 누구보다 깊이 알고 계심을 보여준다.",
           "경건묵상, 희생, 사랑", "하나님은 우리가 내려놓는 눈물의 무게를 정확히 아신다."),
        _c("CALVIN", 1, 22, 2, "창세기 22:2", "이성의 한계를 넘어 약속을 붙드는 순종",
           "이삭은 단순한 혈육이 아니라 '이삭에게서 나는 자라야 네 씨라 부르리라'는 구원 약속 그 자체였다. 아브라함은 자기 이성으로 모순처럼 보이는 명령 앞에서도 하나님의 신실하심을 붙들었다.",
           "종교개혁, 약속, 믿음", "이해가 다 되지 않아도 약속하신 하나님의 성품을 신뢰하라."),
        _c("WESLEY", 1, 22, 2, "창세기 22:2", "온전한 헌신과 성화의 절정",
           "하나님이 이삭을 요구하신 것은 그를 해치려 함이 아니라, 아브라함의 마음 중심에 하나님보다 앞선 것이 없음을 온전히 증명하고 성숙한 사랑으로 세우시기 위함이었다.",
           "성화, 헌신, 순종", "선물보다 선물을 주신 하나님 자신을 더 사랑하는 믿음."),
        _c("JFB", 1, 22, 2, "창세기 22:2", "모리아 땅과 점층적 부르심",
           "'네 아들 - 네 독자 - 네 사랑하는 이삭'으로 이어지는 점층법은 히브리 문학에서 가장 깊은 정서적 절정을 나타낸다. 모리아 산은 훗날 예루살렘 성전산(대하 3:1)과 이어진다.",
           "간결주해, 점층법, 모리아", "가장 소중한 자리에서 가장 큰 구원의 역사가 시작된다."),
        _c("OXFORD", 1, 22, 2, "창세기 22:2", "원어 분해: 카흐-나(קַח־נָא)와 야히드(יָחִיד)",
           "히브리어 '카흐-나'는 칼 명령형에 간청의 불변사 '나'가 붙어 강압이 아닌 깊은 신뢰의 요청을 담는다. '야히드'는 유일무이하고 생명처럼 귀한 독자를 뜻한다.",
           "원어강해, 야히드, 카흐나", "하나님은 강압이 아니라 사랑의 신뢰로 순종을 부르신다."),
        _c("NICOT_NICNT", 1, 22, 2, "창세기 22:2", "창세기 12장과 22장의 수미쌍관(레크 레카)",
           "창세기 12:1의 '너는 떠나라'(레크 레카)와 22:2의 '가라'(레크 레카)는 구약 전체에서 오직 이 두 곳에만 등장한다. 과거를 내려놓은 소명이 미래(이삭)마저 맡기는 순종으로 완성된다.",
           "국제학술, 레크레카, 구조", "신앙의 시작(과거)과 성숙(미래) 모두 하나님께 맡김에서 완성된다."),
        _c("WBC", 1, 22, 2, "창세기 22:2", "내러티브 구조와 '시험'(나사)의 신학",
           "독자는 22:1에서 이미 이것이 '시험'(נִסָּה)임을 알지만 아브라함은 모른 채 침묵 속에 순종한다. 이 극적 긴장 구조는 참된 경외('하나님을 경외하는 줄 아노라', 22:12)의 본질을 드러낸다.",
           "학술주해, 문학구조, 경외", "하나님을 경외함은 말이 아니라 삶의 순종으로 입증된다."),
        _c("BAKER", 1, 22, 2, "창세기 22:2", "고대 근동의 인신제사와 여호와 신앙의 차별성",
           "가나안 주변 민족들은 신의 노여움을 달래려 자녀를 제물로 바쳤으나, 여호와 하나님은 아브라함의 손을 멈추시고 숫양을 대신 예비하심으로써 생명을 살리시는 언약의 하나님이심을 선포하셨다.",
           "배경사, 고대근동, 생명", "하나님은 생명을 빼앗는 신이 아니라 대신 내어주시는 구원자이시다."),
        _c("CONSTABLE", 1, 22, 2, "창세기 22:2", "강해 개요: 믿음의 최고 시험과 여호와 이레",
           "1) 시험의 명령(1-2절) 2) 즉각적 순종(3-8절) 3) 대속의 예비(9-14절) 4) 언약의 재확증(15-19절). 아브라함은 히브리서 11:19대로 하나님이 죽은 자도 살리실 줄 믿고 나아갔다.",
           "강해노트, 부활신앙, 개요", "순종의 자리는 언제나 하나님의 예비하심을 만나는 자리다."),
        _c("ESV_EXPOSITORY", 1, 22, 2, "창세기 22:2", "구속사적 성취: 독자 이삭에서 하나님의 독생자로",
           "70인역(LXX)은 이삭의 '야히드'를 헬라어 '아가페토스'(사랑하는 자)로 옮겼고, 이는 복음서의 '내 사랑하는 아들'(막 1:11)과 요한복음 3:16의 독생자 예수 그리스도로 성취된다.",
           "구속사강해, 독생자, 복음", "아브라함이 멈춘 자리에서 하나님 아버지는 친히 독생자를 내어주셨다."),
        _c("HOKMA", 1, 22, 2, "창세기 22:2", "호크마 종합 해설: 모리아 산의 예표적 의미",
           "모리아 산은 다윗이 번제단을 쌓고 솔로몬이 성전을 세운 곳이며(대하 3:1), 구약의 모든 희생 제사가 가리키는 예수 그리스도의 십자가 대속을 예표한다.",
           "종합주해, 모리아산, 대속", "구약의 그림자는 신약의 십자가 은혜에서 완전히 성취된다."),
        _c("GRAND", 1, 22, 2, "창세기 22:2", "설교 3대지: 내려놓음 · 동행 · 여호와 이레",
           "I. 가장 귀한 것을 내려놓는 믿음의 결단\nII. 사흘 길을 묵묵히 걷는 순종의 동행\nIII. 순종의 끝에서 예비하시는 여호와 이레의 축복",
           "설교대지, 3대지, 여호와이레", "순종의 고난과 여호와 이레의 공급을 균형 있게 선포하라."),

        # --- 창세기 1:1 (대표 주석) ---
        _c("MATTHEW_HENRY", 1, 1, 1, "창세기 1:1", "만물의 유일한 출발점이신 창조주",
           "성경의 첫 선언은 우연론과 범신론을 단숨에 논파한다. 시간과 하늘과 땅은 영원하신 하나님의 선하신 뜻에서 비롯되었다.",
           "경건묵상, 창조주", "내 인생의 시작과 방향도 창조주 하나님의 손안에 있다."),
        _c("CALVIN", 1, 1, 1, "창세기 1:1", "하나님의 영광이 비치는 무대(Theatrum Gloriae Dei)",
           "하나님은 무(無)에서 온 우주를 지으시어 창조 세계 전체를 당신의 지혜와 선하심을 드러내는 영광의 무대로 삼으셨다.",
           "종교개혁, 창조, 영광", "피조 세계 속에서 매일 하나님의 선하심을 묵상하라."),
        _c("OXFORD", 1, 1, 1, "창세기 1:1", "원어 강해: 베레쉬트(בְּרֵאשִׁית)와 바라(בָּרָא)",
           "동사 '바라'는 구약에서 오직 하나님만을 주어로 취하는 무에서의 창조를 뜻한다. 복수형 '엘로힘'이 단수 동사 '바라'와 결합해 유일하신 전능자를 선포한다.",
           "원어강해, 바라, 엘로힘", "불가능해 보이는 자리에서도 새롭게 창조하시는 하나님을 의지하라."),
        _c("NICOT_NICNT", 1, 1, 1, "창세기 1:1", "고대 근동 창조 신화와의 극명한 대조",
           "바벨론 신화(에누마 엘리시)가 신들의 폭력적 투쟁으로 세상을 설명한 반면, 창세기 1:1은 유일하신 하나님이 말씀으로 질서와 생명을 지으신 평화의 창조를 선포한다.",
           "국제학술, 고대근동, 창조", "세상은 투쟁의 산물이 아니라 선하신 하나님의 말씀으로 지어졌다."),

        # --- 시편 23:1 (한국 성도 최다 애송 구절) ---
        _c("MATTHEW_HENRY", 19, 23, 1, "시편 23:1", "나의 목자이신 여호와와 부족함 없는 만족",
           "다윗은 '여호와는 목자시다'라고 객관적으로 말하지 않고 '나의 목자시니'라고 고백한다. 양이 목자를 소유한 순간 모든 결핍의 두려움이 사라진다.",
           "경건묵상, 목자, 만족", "환경이 넉넉해서가 아니라 목자가 나와 함께 계시기에 부족함이 없다."),
        _c("CALVIN", 19, 23, 1, "시편 23:1", "왕이었던 다윗이 스스로를 양으로 낮춘 겸손",
           "이스라엘의 왕이자 용사였던 다윗이 스스로를 연약한 양으로 고백하며 오직 하나님의 돌보심에만 기대는 참된 신앙의 본을 보여준다.",
           "종교개혁, 겸손, 돌보심", "내가 내 삶의 주인이 아니라 주님의 돌보심을 받는 양임을 인정하라."),
        _c("WBC", 19, 23, 1, "시편 23:1", "고대 근동의 '선한 목자' 왕권 은유",
           "히브리어 '로이'(רֹעִי, 나의 목자)는 고대 근동에서 백성을 보호하고 인도하는 참된 왕의 칭호였다. 시인은 세상 권력이 아닌 여호와만을 참 왕으로 모신다.",
           "학술주해, 로이, 왕권", "인생의 방향을 잃을 때 참 왕이신 주님의 음성에 귀 기울이라."),
        _c("CONSTABLE", 19, 23, 1, "시편 23:1", "강해 개요: 목자(1-4절)와 잔치의 주인(5-6절)",
           "시편 23편은 전반부에서 푸른 초장과 사망의 음침한 골짜기를 함께 걷는 목자를, 후반부에서 원수의 목전에서 상을 차려주시는 환대의 주인을 노래한다.",
           "강해노트, 위로, 동행", "평탄할 때뿐 아니라 어두운 골짜기에서도 목자는 한 걸음도 떠나지 않으신다."),

        # --- 요한복음 3:16 ---
        _c("CALVIN", 43, 3, 16, "요한복음 3:16", "구원의 유일한 근원은 하나님의 사랑",
           "하나님께서 우리를 사랑하신 것은 우리 안에 사랑받을 자격이 있어서가 아니라, 오직 당신의 넘치는 자비에서 비롯되었다. 믿음은 이 선물을 받아들이는 빈 손이다.",
           "종교개혁, 은혜, 사랑", "구원은 나의 공로가 아니라 하나님의 선물을 믿음으로 받는 것이다."),
        _c("WESLEY", 43, 3, 16, "요한복음 3:16", "누구든지 믿는 자에게 열린 보편적 복음",
           "'이처럼 사랑하사'는 인간의 말로 다 측량할 수 없는 사랑의 깊이다. '저를 믿는 자마다'는 어느 누구도 제외하지 않는 하나님의 넓은 초대장이다.",
           "웨슬리안, 보편은혜, 복음", "복음의 문은 나이와 형편을 넘어 누구에게나 열려 있다."),
        _c("NICOT_NICNT", 43, 3, 16, "요한복음 3:16", "'세상'(코스모스)과 '독생자'(모노게네스)",
           "요한복음에서 '세상'은 하나님께 등을 돌린 인류를 뜻한다. 하나님은 선한 세상이 아니라 죄로 깨어진 세상을 사랑하시어 유일하신 아들(모노게네스)을 내어주셨다.",
           "국제학술, 코스모스, 독생자", "하나님의 사랑은 우리가 온전할 때가 아니라 연약할 때 먼저 찾아오셨다."),
        _c("ESV_EXPOSITORY", 43, 3, 16, "요한복음 3:16", "창세기 22장 모리아 산의 최종 성취",
           "아브라함이 독자 이삭을 바치려 했던 모리아 산의 그림자가 예수 그리스도의 십자가에서 완전히 성취되었다. 영생은 죽음 이후만이 아니라 지금 주님과 누리는 생명이다.",
           "구속사강해, 영생, 십자가", "오늘 이 자리에서 영생의 기쁨과 평안을 누리며 살아가라."),

        # --- 로마서 8:28 ---
        _c("MATTHEW_HENRY", 45, 8, 28, "로마서 8:28", "모든 것이 합력하여 선을 이루는 섭리",
           "개별 사건 하나하나는 쓰라린 약초 같을 수 있으나, 위대한 의사 되시는 하나님께서 그것들을 조화롭게 배합하시어 성도에게 가장 유익한 선을 빚어내신다.",
           "경건묵상, 섭리, 위로", "지금 겪는 아픔이 끝이 아니라 선을 빚으시는 과정임을 믿으라."),
        _c("NICOT_NICNT", 45, 8, 28, "로마서 8:28", "합력하여 이루시는 '선'의 궁극적 목표(29절)",
           "본문이 약속하는 '선'은 단순한 세상적 형통이 아니라 29절이 밝히듯 '그 아들의 형상을 본받게 하는 것'이다. 하나님은 모든 고난마저 우리를 그리스도 닮게 하는 도구로 쓰신다.",
           "국제학술, 성화, 섭리", "모든 상황 속에서 주님을 더 닮아가는 것이 가장 큰 선이다."),

        # --- 빌립보서 4:6 ---
        _c("CONSTABLE", 50, 4, 6, "빌립보서 4:6", "염려를 감사 기도로 바꾸는 영적 처방",
           "바울은 '아무 것도 염려하지 말라'는 금지 명령에 그치지 않고, 염려를 내려놓을 구체적 자리인 '기도와 간구와 감사'를 제시한다. 감사는 아직 응답받지 못한 미래까지 주께 맡기는 신뢰다.",
           "강해노트, 기도, 평안", "염려가 찾아올 때마다 그것을 기도 제목으로 바꾸어 감사함으로 아뢰라."),

        # --- 데살로니가전서 5:23 ---
        _c("OXFORD", 52, 5, 23, "데살로니가전서 5:23", "원어 강해: 홀로텔레이스(ὁλοτελεῖς, 온전히)",
           "신약에 단 한 번 나오는 '홀로텔레이스'는 전체(홀로스)와 완성(텔로스)의 합성어로, 영과 혼과 몸 전 인격이 평강의 하나님 안에서 흠 없이 보전되기를 구하는 축도다.",
           "원어강해, 거룩, 평강", "거룩은 내 힘으로 쌓는 짐이 아니라 평강의 하나님이 이루시는 선물이다."),
        _c("WESLEY", 52, 5, 23, "데살로니가전서 5:23", "전인적 거룩과 미쁘신 하나님의 보증",
           "24절의 '너희를 부르시는 이는 미쁘시니 그가 또한 이루시리라'는 말씀이 성도의 성화를 보증한다. 하나님은 부르신 자녀를 끝까지 책임지신다.",
           "웨슬리안, 성화, 약속", "우리를 부르신 신실하신 하나님께서 오늘도 선한 일을 이루신다."),
    ]

    strongs = [
        {"strong_id": "H7225", "language": "HEBREW", "lemma": "רֵאשִׁית", "transliteration": "rêshîyth", "pronunciation": "레쉬트", "part_of_speech": "명사", "definition_kr": "태초, 시작, 첫 열매, 으뜸", "definition_en": "beginning, chief, firstfruits", "occurrence_count": 51},
        {"strong_id": "H1254", "language": "HEBREW", "lemma": "בָּרָא", "transliteration": "bârâʼ", "pronunciation": "바라", "part_of_speech": "동사", "definition_kr": "창조하다 (오직 하나님만을 주어로 하는 무에서의 창조)", "definition_en": "to create", "occurrence_count": 54},
        {"strong_id": "H0430", "language": "HEBREW", "lemma": "אֱלֹהִים", "transliteration": "ʼĕlôhîym", "pronunciation": "엘로힘", "part_of_speech": "명사", "definition_kr": "하나님, 전능하신 창조주", "definition_en": "God", "occurrence_count": 2606},
        {"strong_id": "H3173", "language": "HEBREW", "lemma": "יָחִיד", "transliteration": "yâchîyd", "pronunciation": "야히드", "part_of_speech": "형용사", "definition_kr": "유일한, 독자, 생명처럼 귀한 하나뿐인 존재", "definition_en": "only, unique, precious", "occurrence_count": 12},
        {"strong_id": "H3327", "language": "HEBREW", "lemma": "יִצְחָק", "transliteration": "Yitschâq", "pronunciation": "이츠하크", "part_of_speech": "고유명사", "definition_kr": "이삭 ('그가 웃는다', 약속의 아들)", "definition_en": "Isaac (he laughs)", "occurrence_count": 112},
        {"strong_id": "H7462", "language": "HEBREW", "lemma": "רָעָה", "transliteration": "râʻâh", "pronunciation": "라아(로이)", "part_of_speech": "동사/분사", "definition_kr": "목자, 양 떼를 먹이고 돌보며 지키는 이", "definition_en": "to pasture, shepherd", "occurrence_count": 173},
        {"strong_id": "G0025", "language": "GREEK", "lemma": "ἀγαπάω", "transliteration": "agapáō", "pronunciation": "아가파오", "part_of_speech": "동사", "definition_kr": "무조건적으로 사랑하다, 언약적·희생적 사랑", "definition_en": "to love unconditionally", "occurrence_count": 143},
        {"strong_id": "G3439", "language": "GREEK", "lemma": "μονογενής", "transliteration": "monogenḗs", "pronunciation": "모노게네스", "part_of_speech": "형용사", "definition_kr": "독생자, 유일무이한 외아들", "definition_en": "only begotten, one and only", "occurrence_count": 9},
    ]

    cross_refs = [
        {"from_verse_id": calculate_verse_id(1, 22, 2), "to_verse_id": calculate_verse_id(43, 3, 16), "score": 0.99, "relationship_type": "PROPHECY_FULFILLMENT", "note": "독자 이삭의 제사는 독생자 예수 그리스도를 내어주신 하나님의 사랑의 예표"},
        {"from_verse_id": calculate_verse_id(1, 22, 2), "to_verse_id": calculate_verse_id(45, 8, 32), "score": 0.97, "relationship_type": "EXPLANATORY", "note": "자기 아들을 아끼지 아니하신 하나님의 절대적 은혜"},
        {"from_verse_id": calculate_verse_id(1, 22, 2), "to_verse_id": calculate_verse_id(58, 11, 17), "score": 0.96, "relationship_type": "EXPLANATORY", "note": "시험을 받을 때 믿음으로 이삭을 드린 부활 신앙"},
        {"from_verse_id": calculate_verse_id(1, 22, 2), "to_verse_id": calculate_verse_id(59, 2, 21), "score": 0.92, "relationship_type": "THEMATIC", "note": "행함으로 온전해진 믿음의 본보기"},
        {"from_verse_id": calculate_verse_id(1, 22, 2), "to_verse_id": calculate_verse_id(14, 3, 1), "score": 0.91, "relationship_type": "PARALLEL", "note": "솔로몬 성전이 세워진 모리아 산"},
        {"from_verse_id": calculate_verse_id(1, 1, 1), "to_verse_id": calculate_verse_id(43, 1, 1), "score": 0.99, "relationship_type": "PARALLEL", "note": "태초에 계신 말씀(로고스)의 창조 사역"},
        {"from_verse_id": calculate_verse_id(1, 1, 1), "to_verse_id": calculate_verse_id(58, 11, 3), "score": 0.95, "relationship_type": "EXPLANATORY", "note": "믿음으로 모든 세계가 하나님의 말씀으로 지어진 줄 아나니"},
        {"from_verse_id": calculate_verse_id(19, 23, 1), "to_verse_id": calculate_verse_id(43, 10, 11), "score": 0.99, "relationship_type": "PROPHECY_FULFILLMENT", "note": "양들을 위하여 목숨을 버리시는 선한 목자 예수 그리스도"},
        {"from_verse_id": calculate_verse_id(43, 3, 16), "to_verse_id": calculate_verse_id(45, 5, 8), "score": 0.98, "relationship_type": "THEMATIC", "note": "우리가 아직 죄인 되었을 때 그리스도께서 죽으심으로 확증된 사랑"},
        {"from_verse_id": calculate_verse_id(43, 3, 16), "to_verse_id": calculate_verse_id(62, 4, 9), "score": 0.96, "relationship_type": "PARALLEL", "note": "하나님의 독생자를 세상에 보내심으로 나타난 사랑"},
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


def get_worship_catalog() -> Dict[str, Any]:
    """
    21세기 새찬송가 핵심 빠른 찾기 색인(장 번호·구찬송가·제목·예배주제·관련 성구) 및
    21세기 새교독문 주요 편(번호·제목·절기·연결 성경 장절 -> 앱 내 개역한글 본문으로 즉시 교독 렌더링).
    """
    hymns = [
        {"num": 1, "old": 1, "title": "만복의 근원 하나님", "category": "송영·경배", "ref": {"osis": "PSA", "ch": 100, "vs": 1, "label": "시편 100:1"}},
        {"num": 8, "old": 31, "title": "거룩 거룩 거룩 전능하신 주님", "category": "송영·경배", "ref": {"osis": "ISA", "ch": 6, "vs": 3, "label": "이사야 6:3"}},
        {"num": 9, "old": 53, "title": "하늘에 가득 찬 영광의 하나님", "category": "송영·경배", "ref": {"osis": "PSA", "ch": 19, "vs": 1, "label": "시편 19:1"}},
        {"num": 21, "old": 21, "title": "다 찬양하여라 전능왕 창조주", "category": "송영·경배", "ref": {"osis": "PSA", "ch": 103, "vs": 1, "label": "시편 103:1"}},
        {"num": 23, "old": 23, "title": "만 입이 내게 있으면", "category": "송영·경배", "ref": {"osis": "PSA", "ch": 51, "vs": 15, "label": "시편 51:15"}},
        {"num": 28, "old": 28, "title": "복의 근원 강림하사", "category": "은혜·사랑", "ref": {"osis": "1SA", "ch": 7, "vs": 12, "label": "사무엘상 7:12"}},
        {"num": 31, "old": 10, "title": "찬양하라 복되신 구세주 예수", "category": "송영·경배", "ref": {"osis": "PSA", "ch": 96, "vs": 1, "label": "시편 96:1"}},
        {"num": 79, "old": 40, "title": "주 하나님 지으신 모든 세계", "category": "창조·섭리", "ref": {"osis": "GEN", "ch": 1, "vs": 1, "label": "창세기 1:1"}},
        {"num": 88, "old": 88, "title": "내 진정 사모하는", "category": "예수 그리스도", "ref": {"osis": "SNG", "ch": 2, "vs": 1, "label": "아가 2:1"}},
        {"num": 94, "old": 102, "title": "주 예수보다 더 귀한 것은 없네", "category": "헌신·결단", "ref": {"osis": "PHP", "ch": 3, "vs": 8, "label": "빌립보서 3:8"}},
        {"num": 109, "old": 109, "title": "고요한 밤 거룩한 밤", "category": "성탄절", "ref": {"osis": "LUK", "ch": 2, "vs": 7, "label": "누가복음 2:7"}},
        {"num": 115, "old": 115, "title": "기쁘다 구주 오셨네", "category": "성탄절", "ref": {"osis": "PSA", "ch": 98, "vs": 4, "label": "시편 98:4"}},
        {"num": 150, "old": 135, "title": "갈보리산 위에", "category": "고난·십자가", "ref": {"osis": "LUK", "ch": 23, "vs": 33, "label": "누가복음 23:33"}},
        {"num": 151, "old": 138, "title": "만왕의 왕 내 주께서", "category": "고난·십자가", "ref": {"osis": "ISA", "ch": 53, "vs": 5, "label": "이사야 53:5"}},
        {"num": 160, "old": 150, "title": "무덤에 머물러", "category": "부활절", "ref": {"osis": "MAT", "ch": 28, "vs": 6, "label": "마태복음 28:6"}},
        {"num": 165, "old": 151, "title": "주님께 영광", "category": "부활절", "ref": {"osis": "1CO", "ch": 15, "vs": 20, "label": "고린도전서 15:20"}},
        {"num": 184, "old": 173, "title": "불길 같은 주 성령", "category": "성령", "ref": {"osis": "ACT", "ch": 2, "vs": 3, "label": "사도행전 2:3"}},
        {"num": 191, "old": 427, "title": "내가 매일 기쁘게", "category": "성령·기쁨", "ref": {"osis": "GAL", "ch": 5, "vs": 22, "label": "갈라디아서 5:22"}},
        {"num": 204, "old": 379, "title": "주의 말씀 듣고서", "category": "말씀·순종", "ref": {"osis": "MAT", "ch": 7, "vs": 24, "label": "마태복음 7:24"}},
        {"num": 252, "old": 184, "title": "나의 죄를 씻기는", "category": "속죄·구원", "ref": {"osis": "1JN", "ch": 1, "vs": 7, "label": "요한일서 1:7"}},
        {"num": 288, "old": 204, "title": "예수를 나의 구주 삼고", "category": "구원·확신", "ref": {"osis": "JHN", "ch": 3, "vs": 16, "label": "요한복음 3:16"}},
        {"num": 301, "old": 460, "title": "지금까지 지내온 것", "category": "감사·은혜", "ref": {"osis": "1CO", "ch": 15, "vs": 10, "label": "고린도전서 15:10"}},
        {"num": 304, "old": 404, "title": "그 크신 하나님의 사랑", "category": "은혜·사랑", "ref": {"osis": "ROM", "ch": 8, "vs": 39, "label": "로마서 8:39"}},
        {"num": 305, "old": 405, "title": "나 같은 죄인 살리신", "category": "은혜·사랑", "ref": {"osis": "EPH", "ch": 2, "vs": 8, "label": "에베소서 2:8"}},
        {"num": 310, "old": 410, "title": "아 하나님의 은혜로", "category": "은혜·사랑", "ref": {"osis": "2TI", "ch": 1, "vs": 12, "label": "디모데후서 1:12"}},
        {"num": 338, "old": 364, "title": "내 주를 가까이 하게 함은", "category": "위로·동행", "ref": {"osis": "GEN", "ch": 28, "vs": 11, "label": "창세기 28:11"}},
        {"num": 364, "old": 482, "title": "내 기도하는 그 시간", "category": "기도", "ref": {"osis": "PHP", "ch": 4, "vs": 6, "label": "빌립보서 4:6"}},
        {"num": 369, "old": 487, "title": "죄짐 맡은 우리 구주", "category": "기도·위로", "ref": {"osis": "MAT", "ch": 11, "vs": 28, "label": "마태복음 11:28"}},
        {"num": 370, "old": 455, "title": "주 안에 있는 나에게", "category": "위로·평안", "ref": {"osis": "ROM", "ch": 8, "vs": 28, "label": "로마서 8:28"}},
        {"num": 384, "old": 434, "title": "나의 갈 길 다 가도록", "category": "인도·동행", "ref": {"osis": "PSA", "ch": 23, "vs": 1, "label": "시편 23:1"}},
        {"num": 405, "old": 458, "title": "주의 친절한 팔에 안기세", "category": "위로·평안", "ref": {"osis": "DEU", "ch": 33, "vs": 27, "label": "신명기 33:27"}},
        {"num": 413, "old": 470, "title": "내 평생에 가는 길", "category": "위로·평안", "ref": {"osis": "PSA", "ch": 23, "vs": 4, "label": "시편 23:4"}},
        {"num": 429, "old": 489, "title": "세상 모든 풍파 너를 흔들어", "category": "감사·은혜", "ref": {"osis": "1TH", "ch": 5, "vs": 18, "label": "데살로니가전서 5:18"}},
        {"num": 430, "old": 456, "title": "주와 같이 길 가는 것", "category": "인도·동행", "ref": {"osis": "GEN", "ch": 22, "vs": 2, "label": "창세기 22:2"}},
        {"num": 435, "old": 492, "title": "나의 영원하신 기업", "category": "인도·동행", "ref": {"osis": "PSA", "ch": 73, "vs": 26, "label": "시편 73:26"}},
        {"num": 438, "old": 495, "title": "내 영혼이 은총 입어", "category": "위로·평안", "ref": {"osis": "PSA", "ch": 121, "vs": 1, "label": "시편 121:1"}},
        {"num": 455, "old": 507, "title": "주님의 마음을 본받는 자", "category": "헌신·결단", "ref": {"osis": "PHP", "ch": 2, "vs": 5, "label": "빌립보서 2:5"}},
        {"num": 542, "old": 340, "title": "구주 예수 의지함이", "category": "믿음·확신", "ref": {"osis": "HEB", "ch": 11, "vs": 1, "label": "히브리서 11:1"}},
        {"num": 569, "old": 453, "title": "선한 목자 되신 우리 주", "category": "인도·동행", "ref": {"osis": "JHN", "ch": 10, "vs": 11, "label": "요한복음 10:11"}},
        {"num": 589, "old": 308, "title": "넓은 들에 익은 곡식", "category": "감사절", "ref": {"osis": "PSA", "ch": 126, "vs": 5, "label": "시편 126:5"}},
        {"num": 592, "old": 309, "title": "산마다 불이 탄다 고운 단풍에", "category": "감사절", "ref": {"osis": "PSA", "ch": 100, "vs": 4, "label": "시편 100:4"}},
        {"num": 608, "old": 534, "title": "후일에 생명 그칠 때", "category": "장례·천국", "ref": {"osis": "REV", "ch": 21, "vs": 4, "label": "요한계시록 21:4"}},
        {"num": 620, "old": 420, "title": "여기에 모인 우리", "category": "파송·축복", "ref": {"osis": "1TH", "ch": 5, "vs": 23, "label": "데살로니가전서 5:23"}},
    ]

    # 21세기 새교독문 주요 편 — 앱 내 31,102절 개역한글 본문을 즉시 '사회자 / 회중 / 다같이'로 렌더링
    responsive_readings = [
        {"num": 1, "title": "시편 1편 (복 있는 사람)", "season": "주일예배", "osis": "PSA", "ch": 1, "start_vs": 1, "end_vs": 6},
        {"num": 5, "title": "시편 8편 (주의 이름이 어찌 그리 아름다운지요)", "season": "주일예배", "osis": "PSA", "ch": 8, "start_vs": 1, "end_vs": 9},
        {"num": 9, "title": "시편 19편 (하늘이 하나님의 영광을 선포하고)", "season": "주일예배", "osis": "PSA", "ch": 19, "start_vs": 1, "end_vs": 14},
        {"num": 11, "title": "시편 23편 (여호와는 나의 목자시니)", "season": "주일·위로", "osis": "PSA", "ch": 23, "start_vs": 1, "end_vs": 6},
        {"num": 12, "title": "시편 24편 (영광의 왕이 들어가시리로다)", "season": "주일예배", "osis": "PSA", "ch": 24, "start_vs": 1, "end_vs": 10},
        {"num": 14, "title": "시편 27편 (여호와는 나의 빛이요 나의 구원이시니)", "season": "주일·위로", "osis": "PSA", "ch": 27, "start_vs": 1, "end_vs": 8},
        {"num": 18, "title": "시편 34편 (내가 여호와를 항상 송축함이여)", "season": "주일·감사", "osis": "PSA", "ch": 34, "start_vs": 1, "end_vs": 10},
        {"num": 22, "title": "시편 42편 (사슴이 시냇물을 찾기에 갈급함 같이)", "season": "주일·기도", "osis": "PSA", "ch": 42, "start_vs": 1, "end_vs": 11},
        {"num": 23, "title": "시편 46편 (하나님은 우리의 피난처시요)", "season": "주일·위로", "osis": "PSA", "ch": 46, "start_vs": 1, "end_vs": 11},
        {"num": 25, "title": "시편 51편 (내 속에 정한 마음을 창조하시고)", "season": "참회·사순절", "osis": "PSA", "ch": 51, "start_vs": 1, "end_vs": 12},
        {"num": 36, "title": "시편 84편 (주의 궁정에서의 한 날이)", "season": "주일예배", "osis": "PSA", "ch": 84, "start_vs": 1, "end_vs": 12},
        {"num": 39, "title": "시편 90편 (주는 대대에 우리의 거처가 되셨나이다)", "season": "송구영신·장례", "osis": "PSA", "ch": 90, "start_vs": 1, "end_vs": 12},
        {"num": 40, "title": "시편 91편 (지존자의 은밀한 곳에 거주하는 자)", "season": "주일·위로", "osis": "PSA", "ch": 91, "start_vs": 1, "end_vs": 12},
        {"num": 44, "title": "시편 100편 (감사함으로 그의 문에 들어가며)", "season": "추수감사·주일", "osis": "PSA", "ch": 100, "start_vs": 1, "end_vs": 5},
        {"num": 45, "title": "시편 103편 (내 영혼아 여호와를 송축하라)", "season": "감사·주일", "osis": "PSA", "ch": 103, "start_vs": 1, "end_vs": 12},
        {"num": 52, "title": "시편 121편 (내가 산을 향하여 눈을 들리라)", "season": "주일·위로", "osis": "PSA", "ch": 121, "start_vs": 1, "end_vs": 8},
        {"num": 55, "title": "시편 127편 (여호와께서 집을 세우지 아니하시면)", "season": "가정·어린이주일", "osis": "PSA", "ch": 127, "start_vs": 1, "end_vs": 5},
        {"num": 59, "title": "시편 139편 (여호와여 주께서 나를 살펴 보셨으므로)", "season": "주일예배", "osis": "PSA", "ch": 139, "start_vs": 1, "end_vs": 12},
        {"num": 64, "title": "시편 150편 (호흡이 있는 자마다 여호와를 찬양할지어다)", "season": "찬양·주일", "osis": "PSA", "ch": 150, "start_vs": 1, "end_vs": 6},
        {"num": 92, "title": "이사야 53장 (고난주간 · 그가 찔림은 우리의 허물을 인함이요)", "season": "고난주간", "osis": "ISA", "ch": 53, "start_vs": 1, "end_vs": 6},
        {"num": 95, "title": "고린도전서 15장 (부활절 · 그리스도께서 다시 살아나사)", "season": "부활절", "osis": "1CO", "ch": 15, "start_vs": 20, "end_vs": 28},
        {"num": 105, "title": "누가복음 2장 (성탄절 · 지극히 높은 곳에서는 하나님께 영광)", "season": "성탄절", "osis": "LUK", "ch": 2, "start_vs": 8, "end_vs": 14},
        {"num": 115, "title": "로마서 8장 (하나님의 사랑에서 끊을 수 없으리라)", "season": "주일·장례", "osis": "ROM", "ch": 8, "start_vs": 31, "end_vs": 39},
        {"num": 120, "title": "고린도전서 13장 (사랑장 · 믿음 소망 사랑)", "season": "헌신·결혼", "osis": "1CO", "ch": 13, "start_vs": 1, "end_vs": 13},
    ]

    return {
        "hymns": hymns,
        "responsiveReadings": responsive_readings,
    }
