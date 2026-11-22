"""
Expanded Curated Exegesis Dataset (v3.0) across 12 Commentary Perspectives:
- Classic Devotional (4): Matthew Henry, John Calvin, John Wesley, JFB
- Academic / Original Language (4): Oxford, NICOT/NICNT, WBC, Baker Background
- Expository / Pastoral (4): Constable (SonicLight), ESV Expository, Hokma, Grand

Provenance Policy (D-03 Option A):
All 55 Korean study notes are explicitly tagged with provenance="EDITORIAL_SUMMARY"
and attributionLabel="핵심 말씀 참고 요약" (editorial reference summaries, never
represented as verbatim quotes from copyrighted editions).
"""

from __future__ import annotations

from typing import Any, Dict, List

from .canon import calculate_verse_id

EDITORIAL_PROVENANCE = "EDITORIAL_SUMMARY"
EDITORIAL_ATTRIBUTION_LABEL = "핵심 말씀 참고 요약"


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
        "provenance_id": "editorial_study_summary_v3",
        "provenance": EDITORIAL_PROVENANCE,
        "attributionLabel": EDITORIAL_ATTRIBUTION_LABEL,
    }


def build_expanded_exegesis_dataset() -> Dict[str, Any]:
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
            "source_id": "editorial_study_summary_v3",
            "category": "COMMENTARY",
            "title": "핵심 말씀 참고 요약 (12대 주석 관점)",
            "rights_status": "SAMPLE_EXEGESIS",
            "attribution": "핵심 말씀 참고 요약 — 고전·학술·강해 주석의 핵심 관점을 목회 참고용으로 정리한 편집 요약 노트",
            "source_url": None,
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

    commentaries: List[Dict[str, Any]] = [
        # 1. 창세기 22:2 (12종 전체 완비)
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

        # 2. 창세기 1:1
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
           "바벨론 신화가 신들의 폭력적 투쟁으로 세상을 설명한 반면, 창세기 1:1은 유일하신 하나님이 말씀으로 질서와 생명을 지으신 평화의 창조를 선포한다.",
           "국제학술, 고대근동, 창조", "세상은 투쟁의 산물이 아니라 선하신 하나님의 말씀으로 지어졌다."),

        # 3. 창세기 12:1
        _c("CALVIN", 1, 12, 1, "창세기 12:1", "익숙한 땅을 떠나 약속을 향해 걷는 믿음",
           "아브라함은 갈 바를 미리 지도로 받지 못했다. 하나님이 '내가 네게 보여 줄 땅'이라 하심은 매일 하나님의 인도하심에 눈을 고정하게 하려는 은혜의 훈련이다.",
           "종교개혁, 소명, 순례", "미래가 다 보이지 않아도 오늘 부르시는 말씀에 한 걸음 순종하라."),
        _c("CONSTABLE", 1, 12, 1, "창세기 12:1", "창세기 대전환: 인류사(1-11장)에서 구속사(12-50장)로",
           "창세기 12:1-3은 성경 전체 언약 신학의 초석이다. 한 사람 아브라함의 부르심은 결국 열방이 복을 받게 하려는 하나님의 선교적 계획(12:3)으로 이어진다.",
           "강해노트, 언약, 복의통로", "성도는 복을 쌓아두는 저수지가 아니라 흘려보내는 통로다."),

        # 4. 출애굽기 3:14
        _c("OXFORD", 2, 3, 14, "출애굽기 3:14", "원어 강해: 에흐예 아쉐르 에흐예(אֶהְיֶה אֲשֶׁר אֶהְיֶה)",
           "'스스로 있는 자'는 정적인 존재론을 넘어 '내가 너와 함께 있겠다'는 역동적 임재와 언약의 신실하심을 뜻한다. 여호와(יהוה) 이름의 어근이다.",
           "원어강해, 여호와, 임재", "변하는 세상 속에서 어제나 오늘이나 영원히 동일하신 하나님을 의지하라."),
        _c("NICOT_NICNT", 2, 3, 14, "출애굽기 3:14", "인간의 통제를 초월하는 언약의 주권자",
           "고대 근동에서 신의 이름을 아는 것은 주술적 통제를 의미했으나, 하나님은 스스로 존재하시고 자유롭게 구원하시는 주권자이심을 밝히신다.",
           "국제학술, 주권, 구원", "하나님은 우리의 계산에 갇히지 않으시며 친히 구원의 길을 여신다."),

        # 5. 여호수아 1:9
        _c("MATTHEW_HENRY", 6, 1, 9, "여호수아 1:9", "강하고 담대하라: 두려움을 이기는 유일한 근거",
           "여호수아가 담대할 수 있는 이유는 자신의 군사력이나 지혜가 아니라 '네가 어디로 가든지 네 하나님 여호와가 너와 함께 하느니라'는 임마누엘 약속 때문이다.",
           "경건묵상, 담대함, 동행", "두려움이 클수록 내 힘이 아니라 함께 계신 하나님을 바라보라."),
        _c("GRAND", 6, 1, 9, "여호수아 1:9", "설교 3대지: 명령 · 근거 · 동행",
           "I. 마음을 강하게 하고 극히 담대히 하라\nII. 두려워 말며 놀라지 말라\nIII. 어디로 가든지 여호와가 함께 하시리라",
           "설교대지, 격려, 동행", "새 출발이나 시련 앞에 선 성도들에게 가장 힘 있는 격려의 말씀."),

        # 6. 시편 1:1
        _c("MATTHEW_HENRY", 19, 1, 1, "시편 1:1", "복 있는 사람의 거룩한 분별(걷고·서고·앉는 단계)",
           "악인의 꾀를 '따르고'(걷기), 죄인의 길에 '서고', 오만한 자의 자리에 '앉는' 것은 죄가 습관화되는 3단계 타락을 경고한다. 복 있는 사람은 첫걸음부터 말씀을 택한다.",
           "경건묵상, 복있는사람, 분별", "작은 타협을 경계하고 매일 말씀 묵상으로 하루를 시작하라."),
        _c("CONSTABLE", 19, 1, 1, "시편 1:1", "시편 전체 150편의 대문(Gateway Psalm)",
           "시편 1편은 두 길(의인의 길 vs 악인의 길)을 대조하며 시편 전체를 여는 서문 역할을 한다. 히브리어 '아쉬레'(복이 있도다)는 감탄사로 하나님과의 바른 관계에서 오는 충만한 기쁨을 뜻한다.",
           "강해노트, 두길, 시편서문", "세상의 성공 기준이 아니라 말씀에 뿌리내린 시냇가 나무가 되라."),

        # 7. 시편 23:1 & 23:4
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
        _c("BAKER", 19, 23, 4, "시편 23:4", "목자의 '지팡이'(셰베트)와 '막대기'(미쉬에네트)",
           "고대 이스라엘 목자는 두 도구를 지녔다. 짧은 곤봉(지팡이)은 맹수로부터 양을 지키고, 끝이 굽은 긴 막대기는 웅덩이에 빠진 양을 건져 인도한다. 보호와 인도의 이중 은혜다.",
           "배경사, 지팡이, 위로", "어두운 골짜기에서 주님은 우리를 지키시며 바른 길로 붙드신다."),

        # 8. 시편 121:1
        _c("JFB", 19, 121, 1, "시편 121:1", "성전에 올라가는 노래: 산 너머 창조주를 바라봄",
           "순례자는 험준한 유다 산길을 오르며 '나의 도움이 어디서 올까' 묻고, 산 자체가 아니라 '천지를 지으신 여호와'에게서 도움이 옴을 선포한다(121:2).",
           "간결주해, 순례자, 도움", "눈앞의 문제(산)보다 크신 천지의 창조주를 향해 눈을 들라."),
        _c("HOKMA", 19, 121, 1, "시편 121:1", "졸지도 주무시지도 않으시는 지킴의 약속",
           "시편 121편 전체에 '지키신다'(샤마르)라는 동사가 6번 반복된다. 낮의 해와 밤의 달, 지금부터 영원까지 성도의 출입을 완벽히 보호하시는 약속이다.",
           "종합주해, 보호, 샤마르", "우리가 잠든 밤에도 하나님은 깨어 우리와 가정을 지키신다."),

        # 9. 잠언 3:5
        _c("WESLEY", 20, 3, 5, "잠언 3:5", "마음을 다하여 신뢰하고 네 명철을 의지하지 말라",
           "참된 지혜는 자신의 계산과 경험을 절대화하지 않고 범사에 하나님을 인정하는 데서 시작된다. 그때 주께서 굽은 길을 친히 평탄하게 지도하신다(3:6).",
           "웨슬리안, 신뢰, 인도", "크고 작은 모든 결정 앞에 먼저 주님의 뜻을 구하라."),

        # 10. 이사야 40:31 & 41:10 & 53:5
        _c("MATTHEW_HENRY", 23, 40, 31, "이사야 40:31", "여호와를 앙망하는 자의 새 힘",
           "기다림(앙망)은 아무것도 안 하는 무기력이 아니라, 지친 마음을 하나님께 온전히 기대어 새 힘을 공급받는 영적 호흡이다. 독수리의 날개침처럼 일상을 넉넉히 이기게 하신다.",
           "경건묵상, 새힘, 앙망", "몸과 마음이 지칠 때 억지로 버티지 말고 주님 앞에 머물러 새 힘을 얻으라."),
        _c("ESV_EXPOSITORY", 23, 41, 10, "이사야 41:10", "포로기 백성을 향한 다섯 가지 언약 동사",
           "하나님은 두려움에 떨던 이스라엘에게 '함께 함 - 네 하나님이 됨 - 굳세게 함 - 도와줌 - 의로운 오른손으로 붙듦'이라는 다섯 겹의 약속으로 위로하신다.",
           "구속사강해, 위로, 오른손", "불안이 밀려올 때 주님의 의로운 오른손이 나를 붙들고 계심을 기억하라."),
        _c("NICOT_NICNT", 23, 53, 5, "이사야 53:5", "고난받는 종의 대속적 형벌과 평화(샬롬)",
           "본문은 구약 복음의 심장부다. '그가 찔림은 우리의 허물을 인함이요'에서 대속의 원리가 선명히 드러나며, 그가 징계를 받음으로 우리가 누리게 된 '평화'(샬롬)는 하나님과의 완전한 화목이다.",
           "국제학술, 대속, 샬롬", "십자가의 고난이 우리에게 영원한 평안과 치유를 선물했다."),

        # 11. 마태복음 5:3 & 11:28
        _c("CALVIN", 40, 5, 3, "마태복음 5:3", "심령이 가난한 자: 은혜를 담는 빈 그릇",
           "심령의 가난함은 자기 의와 교만을 비우고 오직 하나님의 자비만을 구하는 상태다. 스스로 가득 찬 자는 천국을 받을 공간이 없으나, 빈 손으로 나오는 자에게 천국이 주어진다.",
           "종교개혁, 팔복, 겸손", "내 공로가 없음을 인정하는 자리가 은혜가 시작되는 복된 자리다."),
        _c("MATTHEW_HENRY", 40, 11, 28, "마태복음 11:28", "수고하고 무거운 짐 진 자들을 향한 초청",
           "예수님은 율법의 짐과 죄책감, 삶의 근심에 눌린 모든 이들을 부르신다. 주님이 주시는 쉼은 영혼의 깊은 안식이며, 주님의 멍에는 함께 메어주시는 사랑의 멍에다.",
           "경건묵상, 안식, 초청", "혼자 짊어지려 애쓰던 무거운 짐을 오늘 주님 발 앞에 내려놓으라."),

        # 12. 요한복음 1:1 & 3:16 & 14:6
        _c("WBC", 43, 1, 1, "요한복음 1:1", "말씀(로고스)의 선재성과 신성",
           "창세기 1:1을 의도적으로 메아리치는 '태초에'(엔 아르케)는 그리스도의 영원한 선재성을 선언한다. '하나님과 함께 계셨다'(프로스 톤 테온)는 인격적 친밀함을, '하나님이시니라'는 완전한 신성을 확증한다.",
           "학술주해, 로고스, 기독론", "예수 그리스도는 피조물이 아니라 태초부터 계신 영원한 하나님이시다."),
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
        _c("JFB", 43, 14, 6, "요한복음 14:6", "내가 곧 길이요 진리요 생명이니",
           "그리스도는 단순히 길을 안내하는 선생이 아니라 친히 하나님 아버지께로 나아가는 '길' 자체이시며, 참된 '진리'요 영원한 '생명'이시다.",
           "간결주해, 길진리생명", "인생의 방황을 끝내고 참 길 되신 예수님과 동행하라."),

        # 13. 로마서 8:28 & 8:32
        _c("MATTHEW_HENRY", 45, 8, 28, "로마서 8:28", "모든 것이 합력하여 선을 이루는 섭리",
           "개별 사건 하나하나는 쓰라린 약초 같을 수 있으나, 위대한 의사 되시는 하나님께서 그것들을 조화롭게 배합하시어 성도에게 가장 유익한 선을 빚어내신다.",
           "경건묵상, 섭리, 위로", "지금 겪는 아픔이 끝이 아니라 선을 빚으시는 과정임을 믿으라."),
        _c("NICOT_NICNT", 45, 8, 28, "로마서 8:28", "합력하여 이루시는 '선'의 궁극적 목표(29절)",
           "본문이 약속하는 '선'은 단순한 세상적 형통이 아니라 29절이 밝히듯 '그 아들의 형상을 본받게 하는 것'이다. 하나님은 모든 고난마저 우리를 그리스도 닮게 하는 도구로 쓰신다.",
           "국제학술, 성화, 섭리", "모든 상황 속에서 주님을 더 닮아가는 것이 가장 큰 선이다."),
        _c("CALVIN", 45, 8, 32, "로마서 8:32", "자기 아들을 아끼지 아니하신 이의 보증",
           "가장 큰 선물인 독생자를 이미 주신 하나님께서 어찌 우리에게 필요한 작은 은혜들을 아끼시겠는가? 십자가는 하나님의 모든 약속을 보증하는 영원한 인장이다.",
           "종교개혁, 확신, 은혜", "하나님의 사랑을 의심하게 될 때마다 십자가를 다시 바라보라."),

        # 14. 고린도전서 13:4 & 갈라디아서 2:20 & 에베소서 2:8
        _c("CONSTABLE", 46, 13, 4, "고린도전서 13:4", "감정이 아니라 인격적 행동으로 나타나는 아가페 사랑",
           "바울은 사랑을 추상적 감정이 아니라 15개의 동사(오래 참고, 온유하며, 시기하지 아니하며…)로 묘사한다. 첫 덕목인 '오래 참음'은 공동체를 세우는 사랑의 기초다.",
           "강해노트, 사랑장, 공동체", "사랑은 말의 화려함이 아니라 상대방을 오래 기다려주는 온유함이다."),
        _c("HOKMA", 48, 2, 20, "갈라디아서 2:20", "그리스도와 함께 십자가에 못 박힌 새 생명",
           "옛 자아는 그리스도와 함께 십자가에서 끝났고, 이제 내 안에 사시는 그리스도의 믿음으로 살아가는 것이 신앙생활의 본질이다.",
           "종합주해, 연합, 새생명", "내 고집을 내려놓을 때 내 안에서 그리스도의 생명이 나타난다."),
        _c("ESV_EXPOSITORY", 49, 2, 8, "에베소서 2:8", "은혜로 인하여 믿음으로 말미암은 구원",
           "구원은 인간의 선행에 대한 보상이 아니라 전적인 '하나님의 선물'이다. 그러므로 누구도 자랑할 수 없으며, 구원받은 성도는 2:10의 선한 일을 위해 지음받은 존재로 감사하며 산다.",
           "구속사강해, 오직은혜, 선물", "구원은 행위의 대가가 아니라 감사로 응답하는 하나님의 선물이다."),

        # 15. 빌립보서 4:6 & 4:13
        _c("CONSTABLE", 50, 4, 6, "빌립보서 4:6", "염려를 감사 기도로 바꾸는 영적 처방",
           "바울은 '아무 것도 염려하지 말라'는 금지 명령에 그치지 않고, 염려를 내려놓을 구체적 자리인 '기도와 간구와 감사'를 제시한다. 감사는 아직 응답받지 못한 미래까지 주께 맡기는 신뢰다.",
           "강해노트, 기도, 평안", "염려가 찾아올 때마다 그것을 기도 제목으로 바꾸어 감사함으로 아뢰라."),
        _c("BAKER", 50, 4, 13, "빌립보서 4:13", "로마 감옥에서 고백한 자족의 능력",
           "본문은 만사형통의 주문이 아니라 4:11-12 문맥 속 '풍부에도 비천에도 처할 줄 아는 자족의 비결'이다. 그리스도께서 주시는 힘으로 어떠한 형편에서도 무너지지 않는 내면의 강건함이다.",
           "배경사, 자족, 능력", "환경이 바뀔 때가 아니라 주님이 힘 주실 때 참된 평안과 자족을 누린다."),

        # 16. 데살로니가전서 5:23 & 히브리서 11:1 & 요한계시록 21:4
        _c("OXFORD", 52, 5, 23, "데살로니가전서 5:23", "원어 강해: 홀로텔레이스(ὁλοτελεῖς, 온전히)",
           "신약에 단 한 번 나오는 '홀로텔레이스'는 전체(홀로스)와 완성(텔로스)의 합성어로, 영과 혼과 몸 전 인격이 평강의 하나님 안에서 흠 없이 보전되기를 구하는 축도다.",
           "원어강해, 거룩, 평강", "거룩은 내 힘으로 쌓는 짐이 아니라 평강의 하나님이 이루시는 선물이다."),
        _c("WESLEY", 52, 5, 23, "데살로니가전서 5:23", "전인적 거룩과 미쁘신 하나님의 보증",
           "24절의 '너희를 부르시는 이는 미쁘시니 그가 또한 이루시리라'는 말씀이 성도의 성화를 보증한다. 하나님은 부르신 자녀를 끝까지 책임지신다.",
           "웨슬리안, 성화, 약속", "우리를 부르신 신실하신 하나님께서 오늘도 선한 일을 이루신다."),
        _c("WBC", 58, 11, 1, "히브리서 11:1", "믿음의 정의: 실상(휘포스타시스)과 증거(엘렝코스)",
           "헬라어 '휘포스타시스'는 법적 소유권 증서나 단단한 기초를 뜻한다. 믿음은 막연한 낙관주의가 아니라 하나님의 약속을 이미 실재하는 확신으로 붙드는 영적 시력이다.",
           "학술주해, 믿음, 확신", "눈에 보이는 현실보다 변치 않는 하나님의 약속을 더 확실한 기초로 삼으라."),
        _c("GRAND", 66, 21, 4, "요한계시록 21:4", "모든 눈물을 씻기시는 새 하늘과 새 땅",
           "I. 다시 사망이 없는 영원한 생명\nII. 애통과 곡하는 것과 아픔이 사라진 치유\nIII. 하나님이 친히 눈물을 닦아주시는 영원한 위로",
           "설교대지, 천국소망, 위로", "장례와 슬픔의 자리에서 가장 깊은 소망을 전하는 영원한 약속."),
    ]

    strongs = [
        {"strong_id": "H7225", "language": "HEBREW", "lemma": "רֵאשִׁית", "transliteration": "rêshîyth", "pronunciation": "레쉬트", "part_of_speech": "명사", "definition_kr": "태초, 시작, 첫 열매, 으뜸", "definition_en": "beginning, chief", "occurrence_count": 51},
        {"strong_id": "H1254", "language": "HEBREW", "lemma": "בָּרָא", "transliteration": "bârâʼ", "pronunciation": "바라", "part_of_speech": "동사", "definition_kr": "창조하다 (오직 하나님만을 주어로 하는 무에서의 창조)", "definition_en": "to create", "occurrence_count": 54},
        {"strong_id": "H0430", "language": "HEBREW", "lemma": "אֱלֹהִים", "transliteration": "ʼĕlôhîym", "pronunciation": "엘로힘", "part_of_speech": "명사", "definition_kr": "하나님, 전능하신 창조주", "definition_en": "God", "occurrence_count": 2606},
        {"strong_id": "H3068", "language": "HEBREW", "lemma": "יְהוָה", "transliteration": "YHWH", "pronunciation": "여호와", "part_of_speech": "고유명사", "definition_kr": "스스로 계신 언약의 하나님, 구원자", "definition_en": "LORD (covenant name of God)", "occurrence_count": 6519},
        {"strong_id": "H3173", "language": "HEBREW", "lemma": "יָחִיד", "transliteration": "yâchîyd", "pronunciation": "야히드", "part_of_speech": "형용사", "definition_kr": "유일한, 독자, 생명처럼 귀한 하나뿐인 존재", "definition_en": "only, unique, precious", "occurrence_count": 12},
        {"strong_id": "H3327", "language": "HEBREW", "lemma": "יִצְחָק", "transliteration": "Yitschâq", "pronunciation": "이츠하크", "part_of_speech": "고유명사", "definition_kr": "이삭 ('그가 웃는다', 약속의 아들)", "definition_en": "Isaac (he laughs)", "occurrence_count": 112},
        {"strong_id": "H7462", "language": "HEBREW", "lemma": "רָעָה", "transliteration": "râʻâh", "pronunciation": "라아(로이)", "part_of_speech": "동사/분사", "definition_kr": "목자, 양 떼를 먹이고 돌보며 지키는 이", "definition_en": "to pasture, shepherd", "occurrence_count": 173},
        {"strong_id": "H2617", "language": "HEBREW", "lemma": "חֶסֶד", "transliteration": "checed", "pronunciation": "헤세드", "part_of_speech": "명사", "definition_kr": "변치 않는 언약적 사랑, 인자하심, 자비", "definition_en": "steadfast love, mercy", "occurrence_count": 248},
        {"strong_id": "H7965", "language": "HEBREW", "lemma": "שָׁלוֹם", "transliteration": "shâlôm", "pronunciation": "샬롬", "part_of_speech": "명사", "definition_kr": "평안, 온전함, 하나님과의 화목과 충만한 복", "definition_en": "peace, wholeness", "occurrence_count": 237},
        {"strong_id": "H0543", "language": "HEBREW", "lemma": "אָמֵן", "transliteration": "ʼâmên", "pronunciation": "아멘", "part_of_speech": "부사", "definition_kr": "진실로, 진정으로 그러합니다 (신실함에 대한 동의)", "definition_en": "truly, so be it", "occurrence_count": 30},
        {"strong_id": "G3056", "language": "GREEK", "lemma": "λόγος", "transliteration": "lógos", "pronunciation": "로고스", "part_of_speech": "명사", "definition_kr": "말씀, 태초부터 계신 성자 예수 그리스도", "definition_en": "word, Logos", "occurrence_count": 330},
        {"strong_id": "G0025", "language": "GREEK", "lemma": "ἀγαπάω", "transliteration": "agapáō", "pronunciation": "아가파오", "part_of_speech": "동사", "definition_kr": "무조건적으로 사랑하다, 언약적·희생적 사랑", "definition_en": "to love unconditionally", "occurrence_count": 143},
        {"strong_id": "G3439", "language": "GREEK", "lemma": "μονογενής", "transliteration": "monogenḗs", "pronunciation": "모노게네스", "part_of_speech": "형용사", "definition_kr": "독생자, 유일무이한 외아들", "definition_en": "only begotten, one and only", "occurrence_count": 9},
        {"strong_id": "G5485", "language": "GREEK", "lemma": "χάρις", "transliteration": "cháris", "pronunciation": "카리스", "part_of_speech": "명사", "definition_kr": "은혜, 자격 없는 자에게 값없이 베푸시는 하나님의 호의", "definition_en": "grace, unmerited favor", "occurrence_count": 155},
        {"strong_id": "G4102", "language": "GREEK", "lemma": "πίστις", "transliteration": "pístis", "pronunciation": "피스티스", "part_of_speech": "명사", "definition_kr": "믿음, 신뢰, 하나님의 신실하심에 의탁함", "definition_en": "faith, trust", "occurrence_count": 243},
        {"strong_id": "G1515", "language": "GREEK", "lemma": "εἰρήνη", "transliteration": "eirḗnē", "pronunciation": "에이레네", "part_of_speech": "명사", "definition_kr": "평강, 그리스도 안에서 누리는 하나님과의 화평", "definition_en": "peace, harmony", "occurrence_count": 92},
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
        {"from_verse_id": calculate_verse_id(19, 23, 1), "to_verse_id": calculate_verse_id(23, 40, 11), "score": 0.94, "relationship_type": "PARALLEL", "note": "어린 양을 그 팔로 모아 품에 안으시는 목자 하나님"},
        {"from_verse_id": calculate_verse_id(23, 53, 5), "to_verse_id": calculate_verse_id(60, 2, 24), "score": 0.99, "relationship_type": "PROPHECY_FULFILLMENT", "note": "친히 나무에 달려 우리 죄를 담당하심으로 나음을 얻게 하신 그리스도"},
        {"from_verse_id": calculate_verse_id(43, 3, 16), "to_verse_id": calculate_verse_id(45, 5, 8), "score": 0.98, "relationship_type": "THEMATIC", "note": "우리가 아직 죄인 되었을 때 그리스도께서 죽으심으로 확증된 사랑"},
        {"from_verse_id": calculate_verse_id(43, 3, 16), "to_verse_id": calculate_verse_id(62, 4, 9), "score": 0.96, "relationship_type": "PARALLEL", "note": "하나님의 독생자를 세상에 보내심으로 나타난 사랑"},
        {"from_verse_id": calculate_verse_id(45, 8, 28), "to_verse_id": calculate_verse_id(1, 50, 20), "score": 0.96, "relationship_type": "PARALLEL", "note": "악을 선으로 바꾸시는 하나님의 섭리(요셉의 고백)"},
        {"from_verse_id": calculate_verse_id(50, 4, 6), "to_verse_id": calculate_verse_id(60, 5, 7), "score": 0.97, "relationship_type": "PARALLEL", "note": "너희 염려를 다 주께 맡겨 버리라 이는 저가 너희를 권고하심이니라"},
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
        {
            "topic_key": "david",
            "title": "다윗 (David — '사랑받는 자')",
            "meaning": "목동에서 왕으로 · 하나님 마음에 합한 자 · 메시아 언약의 조상",
            "summary": "베들레헴 목동 시절의 기름부음부터 골리앗 앞의 믿음, 시편의 찬양과 참회, 그리고 영원한 다윗 언약의 성취까지 이어지는 구속사 사슬망.",
            "links": [
                (calculate_verse_id(9, 16, 7), "사무엘상 16:7", "중심을 보시는 하나님", "외모가 아니라 마음의 중심을 보시고 목동 다윗을 택하심."),
                (calculate_verse_id(9, 17, 45), "사무엘상 17:45", "만군의 여호와의 이름", "칼과 단창이 아니라 여호와의 이름으로 나아간 믿음의 담대함."),
                (calculate_verse_id(10, 7, 16), "사무엘하 7:16", "영원한 다윗 언약", "네 집과 네 나라가 내 앞에서 영원히 보전되리라는 메시아 약속."),
                (calculate_verse_id(19, 23, 1), "시편 23:1", "목자의 노래", "왕이 되어서도 스스로를 주님의 양으로 고백한 겸손한 신앙."),
                (calculate_verse_id(19, 51, 10), "시편 51:10", "정한 마음을 창조하소서", "죄 앞에서 변명하지 않고 상한 심령으로 회개한 회복의 본."),
                (calculate_verse_id(40, 1, 1), "마태복음 1:1", "다윗의 자손 예수", "다윗 언약이 예수 그리스도 안에서 영원히 성취됨."),
            ],
        },
        {
            "topic_key": "moses",
            "title": "모세 (Moses — '물에서 건져냄')",
            "meaning": "출애굽의 인도자 · 율법의 중보자 · 온유한 종",
            "summary": "호렙산 떨기나무의 부르심에서 홍해의 구원, 시내산 언약, 백성을 위한 중보기도, 신약 히브리서 11장의 믿음 평가까지 이어지는 생애 사슬망.",
            "links": [
                (calculate_verse_id(2, 3, 14), "출애굽기 3:14", "스스로 있는 자의 소명", "광야 40년 끝에 떨기나무 불꽃 가운데 부르신 하나님."),
                (calculate_verse_id(2, 14, 13), "출애굽기 14:13", "홍해 앞의 구원", "두려워 말고 가만히 서서 여호와의 구원을 보라."),
                (calculate_verse_id(2, 32, 32), "출애굽기 32:32", "생명을 건 중보기도", "죄 지은 백성을 위해 자기 이름을 생명책에서 지워달라 간구한 목자의 심정."),
                (calculate_verse_id(4, 12, 3), "민수기 12:3", "지상의 모든 사람보다 온유함", "비난 앞에서도 스스로 변명하지 않고 하나님께 맡긴 온유한 리더십."),
                (calculate_verse_id(5, 34, 5), "신명기 34:5", "여호와의 종의 완주", "약속의 땅을 바라보며 사명을 마친 충성된 종."),
                (calculate_verse_id(58, 11, 24), "히브리서 11:24", "그리스도를 위한 수모", "애굽의 보화보다 하나님의 백성과 고난받기를 택한 믿음."),
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
