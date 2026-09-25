"""
Open Data Collector and Sample Dataset Generator for Pastoral Workstation.
Handles public domain repositories and generates rich offline sample data
for the 8 core commentaries, Strong's Greek/Hebrew lexicon, and TSK cross references.
"""

import os
import json
from typing import Dict, Any, List

class OpenDataCollector:
    """
    Collector and generator for open/public domain Bible data.
    """

    @staticmethod
    def get_public_domain_sources_metadata() -> List[Dict[str, Any]]:
        """Returns catalogue of accessible public domain and open datasets."""
        return [
            {
                "id": "wesley_notes",
                "name": "John Wesley's Notes on the Bible (1765)",
                "license": "Public Domain",
                "url": "https://www.ccel.org/ccel/wesley/notes.html",
                "format": "HTML / TEI XML / Plain Text",
                "scope": "OT & NT Complete (Special emphasis on NT & Holiness)"
            },
            {
                "id": "matthew_henry",
                "name": "Matthew Henry's Complete Commentary on the Whole Bible (1706)",
                "license": "Public Domain",
                "url": "https://www.ccel.org/ccel/henry/mhc.html",
                "format": "HTML / XML / Plain Text",
                "scope": "OT & NT Complete 6 Volumes"
            },
            {
                "id": "strongs_lexicon",
                "name": "Strong's Exhaustive Concordance of the Bible (Hebrew & Greek)",
                "license": "Public Domain",
                "url": "https://github.com/openscriptures/strongs",
                "format": "JSON / XML",
                "scope": "Hebrew (H1-H8674), Greek (G1-G5624)"
            },
            {
                "id": "tsk_cross_references",
                "name": "Treasury of Scripture Knowledge (TSK)",
                "license": "Public Domain",
                "url": "https://github.com/scrollmapper/bible_databases",
                "format": "CSV / SQL / JSON (~340,000 links)",
                "scope": "Entire 66 Books"
            },
            {
                "id": "korean_krv",
                "name": "개역한글 성경 (Korean Revised Version - 1961)",
                "license": "Public Domain (Copyright expired >50 years)",
                "format": "Text / JSON",
                "scope": "창세기 ~ 요한계시록 66권 완간"
            }
        ]

    @staticmethod
    def generate_pastoral_sample_dataset(output_dir: str):
        """
        Creates ready-to-ingest JSON files containing high-quality sample data
        covering Genesis 1, John 3, 1 Thessalonians 4-5, Isaiah 53, and Romans 6 & 8
        with all 8 commentaries represented.
        """
        os.makedirs(output_dir, exist_ok=True)

        # 1. 샘플 성경 본문 (개역한글 KRV + 개역개정 GAE 스타일 + 스트롱 태그)
        sample_verses = [
            # 창세기 1:1-3
            {
                "verse_id": 1001001, "book_id": 1, "chapter": 1, "verse": 1,
                "version_code": "KRV",
                "text": "태초에 하나님이 천지를 창조하시니라",
                "text_with_strong": "태초에<H7225> 하나님이<H430> 천지를<H8064><H776> 창조하시니라<H1254>"
            },
            {
                "verse_id": 1001002, "book_id": 1, "chapter": 1, "verse": 2,
                "version_code": "KRV",
                "text": "땅이 혼돈하고 공허하며 흑암이 깊음 위에 있고 하나님의 영은 수면 위에 운행하시니라",
                "text_with_strong": "땅이<H776> 혼돈하고<H8414> 공허하며<H922> 흑암이<H2822> 깊음<H8415> 위에 있고 하나님의<H430> 영은<H7307> 수면<H4325> 위에 운행하시니라<H7363>"
            },
            {
                "verse_id": 1001003, "book_id": 1, "chapter": 1, "verse": 3,
                "version_code": "KRV",
                "text": "하나님이 이르시되 빛이 있으라 하시니 빛이 있었고",
                "text_with_strong": "하나님이<H430> 이르시되<H559> 빛이<H216> 있으라<H1961> 하시니 빛이<H216> 있었고"
            },
            # 요한복음 3:3, 3:5, 3:16
            {
                "verse_id": 43003003, "book_id": 43, "chapter": 3, "verse": 3,
                "version_code": "KRV",
                "text": "예수께서 대답하여 이르시되 진실로 진실로 네게 이르노니 사람이 거듭나지 아니하면 하나님의 나라를 볼 수 없느니라",
                "text_with_strong": "예수께서<G2424> 대답하여<G611> 이르시되 진실로<G281> 진실로<G281> 네게 이르노니 사람이 거듭나지<G509><G1080> 아니하면 하나님의<G2316> 나라를<G932> 볼<G1492> 수 없느니라"
            },
            {
                "verse_id": 43003005, "book_id": 43, "chapter": 3, "verse": 5,
                "version_code": "KRV",
                "text": "예수께서 대답하시되 진실로 진실로 네게 이르노니 사람이 물과 성령으로 나지 아니하면 하나님의 나라에 들어갈 수 없느니라",
                "text_with_strong": "예수께서<G2424> 대답하시되 진실로 진실로 네게 이르노니 사람이 물과<G5204> 성령으로<G4151> 나지<G1080> 아니하면 하나님의 나라에 들어갈<G1525> 수 없느니라"
            },
            {
                "verse_id": 43003016, "book_id": 43, "chapter": 3, "verse": 16,
                "version_code": "KRV",
                "text": "하나님이 세상을 이처럼 사랑하사 독생자를 주셨으니 이는 그를 믿는 자마다 멸망하지 않고 영생을 얻게 하려 하심이라",
                "text_with_strong": "하나님이<G2316> 세상을<G2889> 이처럼 사랑하사<G25> 독생자를<G3439> 주셨으니 이는 그를 믿는<G4100> 자마다 멸망하지<G622> 않고 영생을<G166><G2222> 얻게 하려 하심이라"
            },
            # 데살로니가전서 5:23 (성결 핵심)
            {
                "verse_id": 52005023, "book_id": 52, "chapter": 5, "verse": 23,
                "version_code": "KRV",
                "text": "평강의 하나님이 친히 너희를 온전히 거룩하게 하시고 또 너희의 온 영과 혼과 몸이 우리 주 예수 그리스도께서 강림하실 때에 흠 없게 보존되기를 원하노라",
                "text_with_strong": "평강의<G1515> 하나님이<G2316> 친히 너희를 온전히<G3651> 거룩하게<G37> 하시고 또 너희의 온<G3648> 영과<G4151> 혼과<G5590> 몸이<G4983> 우리 주 예수 그리스도께서 강림하실<G3952> 때에 흠 없게<G274> 보존되기를<G5083> 원하노라"
            },
            # 이사야 53:5 (신유 핵심)
            {
                "verse_id": 23053005, "book_id": 23, "chapter": 53, "verse": 5,
                "version_code": "KRV",
                "text": "그가 찔림은 우리의 허물 때문이요 그가 상함은 우리의 죄악 때문이라 그가 징계를 받으므로 우리는 평화를 누리고 그가 채찍에 맞으므로 우리는 나음을 받았도다",
                "text_with_strong": "그가 찔림은<H2490> 우리의 허물<H6588> 때문이요 그가 상함은<H1792> 우리의 죄악<H5771> 때문이라 그가 징계를<H4148> 받으므로 우리는 평화를<H7965> 누리고 그가 채찍에<H2250> 맞으므로 우리는 나음을<H7495> 받았도다"
            },
            # 데살로니가전서 4:16-17 (재림 핵심)
            {
                "verse_id": 52004016, "book_id": 52, "chapter": 4, "verse": 16,
                "version_code": "KRV",
                "text": "주께서 호령과 천사장의 소리와 하나님의 나팔 소리로 친히 하늘로부터 강림하시리니 그리스도 안에서 죽은 자들이 먼저 일어나고",
                "text_with_strong": "주께서<G2962> 호령과<G2752> 천사장의<G743> 소리와<G5456> 하나님의 나팔 소리로<G4536> 친히 하늘로부터<G3772> 강림하시리니<G2597> 그리스도 안에서 죽은<G3498> 자들이 먼저 일어나고<G450>"
            },
            {
                "verse_id": 52004017, "book_id": 52, "chapter": 4, "verse": 17,
                "version_code": "KRV",
                "text": "그 후에 우리 살아 남은 자들도 그들과 함께 구름 속으로 끌어 올려 공중에서 주를 영접하게 하시리니 그리하여 우리가 항상 주와 함께 있으리라",
                "text_with_strong": "그 후에 우리 살아 남은<G2198> 자들도 그들과 함께 구름<G3507> 속으로 끌어 올려<G726> 공중에서<G109> 주를 영접하게<G529> 하시리니 그리하여 우리가 항상 주와 함께 있으리라"
            }
        ]

        with open(os.path.join(output_dir, "sample_verses.json"), "w", encoding="utf-8") as f:
            json.dump(sample_verses, f, ensure_ascii=False, indent=2)

        # 2. 8종 주석 샘플 데이터셋 (창 1:1 및 살전 5:23 대상)
        sample_commentaries = [
            # 1. OXFORD (옥스포드 원어성경대전)
            {
                "source": "OXFORD",
                "reference": "창세기 1:1",
                "title": "원어 분해 및 심층 강해: 베레쉬트와 바라",
                "content": """### [원어 형태론적 분해]
1. **בְּרֵאשִׁית (베레쉬트, H7225)**:
   - 전치사 בְּ(베, '~안에, ~에') + 명사 רֵאשִׁית(레쉬트, '시작, 첫 열매, 으뜸').
   - 시간의 절대적 기원을 가리키며, 피조 세계의 시작이 하나님의 영원한 작정 속에 존재했음을 시사한다.
2. **בָּרָא (바라, H1254)**:
   - 동사 칼(Qal) 완료 3인칭 남성 단수.
   - 성경에서 '바라'의 주어는 **오직 하나님(אֱלֹהִים)**뿐이다. 무(Ex Nihilo)에서 유를 창조하시는 하나님의 독점적 신적 행위를 나타낸다.

### [목회적 강해]
창세기 1장 1절은 성경 전체의 기초석이다. 물질은 영원하지 않으며, 신격화될 수 없다. 오직 하나님만이 영원하시며 우주 만물의 절대 주권자이시다.""",
                "theological_tags": "원어강해, 창조론, 히브리어문법",
                "practical_points": "설교 적용: 성도의 인생의 시작도 나의 결단이 아닌 하나님의 절대 주권에 맡겨야 함."
            },
            # 2. WESLEY (존 웨슬리 주석)
            {
                "source": "WESLEY",
                "reference": "데살로니가전서 5:23",
                "title": "온전한 성화(Entire Sanctification)의 성결 신학",
                "content": """**살전 5:23 해설**:
'평강의 하나님이 친히 너희를 온전히 거룩하게 하시고(ὁλοτελεῖς, holoteleis)...'

1. **온전한 거룩함(Entire Sanctification)**:
   하나님께서는 우리의 어떤 한 부분만을 거룩하게 하시는 것이 아니라, 우리의 전 존재를 거룩하게 하신다.
   여기서 '온전히'란 영혼에 잔존하는 불신과 이기심의 뿌리를 성령의 불로 정결하게 하시고, 순전한 사랑으로 하나님과 이웃을 사랑하는 상태를 뜻한다.
2. **영과 혼과 몸의 보존**:
   성화는 단지 추상적 정신 상태가 아니다. 우리의 육체적 행실과 감정, 영적 교제 모두가 주 예수 다시 오실 때까지 흠 없이(blameless) 보존되는 능력이다.
   약속하신 이는 미쁘시니 그가 또한 이루실 것이다(24절).""",
                "theological_tags": "웨슬리안, 완전성화, 성령세례, 성화",
                "practical_points": "I. 평강의 하나님만이 거룩하게 하신다. / II. 영과 혼과 육의 전인적 거룩 / III. 미쁘신 하나님의 신실한 약속"
            },
            # 3. HOKMA (호크마 종합주석)
            {
                "source": "HOKMA",
                "reference": "창세기 1:1",
                "title": "구속사의 서막: 창조의 목적과 신학적 문맥",
                "content": """**[역사·문화적 배경]**
당대 고대 근동(바벨론의 에누마 엘리쉬 등)의 창조 신화는 신들 간의 유혈 낭자한 투쟁과 폭력의 부산물로 인간이 창조되었다고 보았다. 반면 모세는 하나님의 말씀에 의한 평화롭고 질서정연하며 거룩한 주권적 창조를 선언함으로써 세속 신화를 단번에 분쇄한다.

**[구속사적 메시지]**
태초의 창조는 장차 그리스도 안에서 성취될 '새 하늘과 새 땅'의 종말론적 구속을 예표한다. 어둠과 혼돈 속에서 빛을 부르신 하나님은 죄악의 어둠 속에 죽어가는 영혼에게 구원의 빛을 비추시는 분이시다.""",
                "theological_tags": "종합주석, 구속사, 비교종교학",
                "practical_points": "혼돈과 공허 가운데 역사하시는 성령 하나님의 운행하심을 의지할 것."
            },
            # 4. GRAND (그랜드 종합주석)
            {
                "source": "GRAND",
                "reference": "요한복음 3:3-5",
                "title": "설교 대지: 물과 성령으로 거듭난 자의 특권",
                "content": """### [본문 연구 및 설교 아웃라인]

**명제**: 사람은 도덕적 수양이 아닌 오직 성령의 초자연적 재창조로만 하나님 나라를 소유한다.

- **대지 I. 종교적 열심의 한계 (3:1-3)**
  - 니고데모는 율법 학자요 산헤드린 공회원이었으나 영생의 길을 알지 못했다.
  - 도덕과 종교로는 인간의 타락한 옛 본성을 개조할 수 없다.

- **대지 II. 물과 성령의 거듭남 (3:4-5)**
  - 물은 회개와 죄 씻음의 표요, 성령은 속사람의 근본적 신생(新生)이다.
  - 중생은 위로부터(ἄνωθεν, anothen) 임하는 은총의 선물이다.

- **대지 III. 하나님 나라를 보는 새로운 눈 (3:6-8)**
  - 육으로 난 것은 육이요 영으로 난 것은 영이다.
  - 거듭난 성도는 세상의 가치관을 버리고 하늘의 신령한 것을 사모한다.""",
                "theological_tags": "신생, 중생, 설교대지, 강해설교",
                "practical_points": "대지 설교용 예화: 애벌레가 나비로 변태하듯, 인간의 수양이 아닌 생명적 본질의 변화가 일어나야 한다."
            },
            # 5. CHARISMA (카리스마 주석)
            {
                "source": "CHARISMA",
                "reference": "이사야 53:5",
                "title": "채찍에 맞으심으로 허락된 치유와 성령의 권능",
                "content": """**신유와 영적 치유의 실제**:
'그가 채찍에 맞으므로 우리는 나음을 받았도다.'

1. **대속의 온전한 범위**:
   예수님의 십자가 사역은 영혼 구원만을 위한 것이 아니다. 마태복음 8:17은 이사야 53:4-5를 인용하며 예수님의 육체 치유 사역이 바로 이 예언의 직접적 성취임을 선포한다.
2. **믿음의 기름부으심**:
   질병은 아담의 타락 이후 사탄의 세력이 인간에게 가져온 억압이다. 성도는 예수 이름의 권세와 보혈의 공로를 의지하여 담대히 치유를 선포해야 한다.
3. **치유의 기도 지침**:
   믿음의 기도는 병든 자를 일으킨다. 의심을 버리고 이미 십자가에서 성취된 채찍의 공로를 믿음으로 주장하라.""",
                "theological_tags": "치유, 성령론, 치유기도, 영적전쟁",
                "practical_points": "성경적 치유 사역의 원리: 의학을 존중하되, 궁극적 치유의 주권은 하나님께 있음을 신뢰하고 안수와 기도로 간구한다."
            },
            # 6. MATTHEW_HENRY (매튜 헨리 주석)
            {
                "source": "MATTHEW_HENRY",
                "reference": "데살로니가전서 4:16-17",
                "title": "주의 강림과 성도의 영광스러운 소망에 대한 묵상",
                "content": """**[경건한 묵상]**
그날은 두려운 날이 될 것이나, 성도에게는 최고의 위로의 날이 될 것이다.
주께서 스스로 호령과 큰 소리로 하늘로부터 내려오실 것이니, 만물이 그 명령에 복종할 것이다.

그리스도 안에서 잠든 성도들이 먼저 일어날 것이라 하셨으니, 무덤은 영원한 감옥이 아니요 단지 주의 부르심을 기다리는 안식처일 뿐이다.
그리고 살아남은 우리 또한 공중으로 이끌려 주님을 뵈오리니, 더 이상 슬픔이나 이별이 없는 주와의 영원한 동행이 시작된다.
그러므로 성도여, 세속의 헛된 낙에 마음을 빼앗기지 말고 이 소망의 말씀으로 서로 위로하라.""",
                "theological_tags": "종말론, 재림, 경건묵상, 청교도영성",
                "practical_points": "영적 안목: 장례식에서 성도들에게 영원한 부활의 소망을 선포하는 최적의 위로 본문."
            },
            # 7. BAKER (베이커 성경배경주석)
            {
                "source": "BAKER",
                "reference": "데살로니가전서 4:16-17",
                "title": "로마 제국의 황제 방문(파루시아) 풍습과 성경적 재림 배경",
                "content": """**[그리스-로마 세계의 '파루시아(Parousia)' 의전]**
- 16-17절의 '영접하게 하시리니'에 사용된 헬라어 **ἀπάντησις (아판테시스)**는 고대 헬레니즘 세계의 공식 외교 용어이다.
- 로마 황제나 최고 통치자가 어느 도시에 공식 방문(Parousia)할 때, 그 도시의 유력한 시민들과 영접 사절단이 성문 밖 멀리까지 마중 나가 통치자를 환호하며 맞이한 후, 그를 성 안으로 모시고 들어오는 장엄한 의식을 가리켰다.
- 바울은 이 로마 제국의 익숙한 공식 방문 의전을 차용하여, 온 우주의 진정한 주(Kyrios)이신 예수 그리스도의 재림 시 성도들이 공중으로 나아가 만왕의 왕을 영접하는 승리의 환희를 생생하게 묘사하고 있다.""",
                "theological_tags": "성경배경사, 고고학, 제2성전기문헌",
                "practical_points": "설교 시 시각적 설명: 로마의 황제 입성식을 압도하는 하늘 군왕의 재림 영접 장면을 회중에게 묘사."
            },
            # 8. ESV_EXPOSITORY (ESV 성경해설주석)
            {
                "source": "ESV_EXPOSITORY",
                "reference": "요한복음 3:16",
                "title": "구속사의 절정: 하나님의 우주적 사랑과 독생자의 희생",
                "content": """**[본문 강해]**
1. **사랑의 동기 (οὕτως ἠγάπησεν, outos egapesen)**:
   '이처럼'은 사랑의 강도(intensity)뿐 아니라 그 사랑이 실천된 방식(manner)을 함께 가리킨다. 하나님은 세상을 심판하셔야 마땅했으나, 가장 값비싼 독생자를 내어주시는 방식으로 사랑을 확증하셨다.
2. **독생자 (μονογενής, monogenes)**:
   단순한 물리적 출생이 아니라 '유일무이한(one-of-a-kind)', '가장 사랑받는 유일한 아들'의 신학적 위상을 나타낸다.
3. **구속사적 결과**:
   멸망(ἀπόληται)에서 영생(ζωὴν αἰώνιον)으로의 절대적 이동. 이 생명은 단지 끝없는 시간의 지속이 아니라, 하나님과 누리는 질적으로 새로운 영원한 사귐이다.""",
                "theological_tags": "현대복음주의, 구속사, 기독론",
                "practical_points": "현대적 적용: 고립과 무조건적 수용에 굶주린 현대인들에게 독생자를 주신 하나님의 절대적 사랑 제시."
            }
        ]

        with open(os.path.join(output_dir, "sample_commentaries.json"), "w", encoding="utf-8") as f:
            json.dump(sample_commentaries, f, ensure_ascii=False, indent=2)

        # 3. 샘플 스트롱코드 사전 (히브리어 및 헬라어 핵심 어휘)
        sample_strongs = [
            {
                "strong_id": "H7225",
                "lemma": "רֵאשִׁית",
                "transliteration": "rêʼshîyth",
                "pronunciation": "ray-sheeth'",
                "part_of_speech": "명사 여성형",
                "definition_kr": "처음, 시작, 으뜸, 첫 열매, 최고의 부분",
                "definition_en": "first, beginning, best, chief",
                "root_id": "H7218",
                "derivation": "From the same as H7218 (ro'sh)",
                "occurrence_count": 51
            },
            {
                "strong_id": "H430",
                "lemma": "אֱלֹהִים",
                "transliteration": "ʼĕlôhîym",
                "pronunciation": "el-o-heem'",
                "part_of_speech": "명사 남성 복수형",
                "definition_kr": "하나님, 참 신, 전능자 (장엄 복수형)",
                "definition_en": "God, gods, judges, angels",
                "root_id": "H433",
                "derivation": "Plural of H433",
                "occurrence_count": 2606
            },
            {
                "strong_id": "H1254",
                "lemma": "בָּרָא",
                "transliteration": "bârâʼ",
                "pronunciation": "baw-raw'",
                "part_of_speech": "동사",
                "definition_kr": "창조하다 (오직 하나님의 초자연적 무로부터의 창조에만 사용됨)",
                "definition_en": "to create, shape, form",
                "root_id": None,
                "derivation": "A primitive root",
                "occurrence_count": 54
            },
            {
                "strong_id": "G37",
                "lemma": "ἁγιάζω",
                "transliteration": "hagiazō",
                "pronunciation": "hag-ee-ad'-zo",
                "part_of_speech": "동사",
                "definition_kr": "거룩하게 하다, 성결케 하다, 정결케 하다, 성별하여 하나님께 드리다",
                "definition_en": "to make holy, consecrate, sanctify, purify",
                "root_id": "G40",
                "derivation": "From G40 (hagios)",
                "occurrence_count": 28
            },
            {
                "strong_id": "G3651",
                "lemma": "ὁλοτελής",
                "transliteration": "holotelēs",
                "pronunciation": "hol-ot-el-ace'",
                "part_of_speech": "형용사",
                "definition_kr": "온전한, 전인적인, 완벽하게 끝까지 성취된 (살전 5:23)",
                "definition_en": "complete, whole, entirely, through and through",
                "root_id": "G3650",
                "derivation": "From G3650 and G5056",
                "occurrence_count": 1
            },
            {
                "strong_id": "G2424",
                "lemma": "Ἰησοῦς",
                "transliteration": "Iēsous",
                "pronunciation": "ee-ay-sooce'",
                "part_of_speech": "고유명사",
                "definition_kr": "예수 (여호와는 구원이시다)",
                "definition_en": "Jesus, Jehovah is Salvation",
                "root_id": "H3091",
                "derivation": "Of Hebrew origin (H3091)",
                "occurrence_count": 917
            }
        ]

        with open(os.path.join(output_dir, "sample_strongs.json"), "w", encoding="utf-8") as f:
            json.dump(sample_strongs, f, ensure_ascii=False, indent=2)

        # 4. 샘플 TSK 교차 관주 데이터
        sample_cross_refs = [
            {"from_verse_id": 1001001, "to_verse_id": 43001001, "score": 5.0, "relationship_type": "PARALLEL", "note": "요 1:1 '태초에 말씀이 계시니라' 창조의 로고스"},
            {"from_verse_id": 1001001, "to_verse_id": 58011003, "score": 4.5, "relationship_type": "EXPLANATORY", "note": "히 11:3 '믿음으로 모든 세계가 하나님의 말씀으로 지어진 줄을 아나니'"},
            {"from_verse_id": 43003003, "to_verse_id": 47005017, "score": 5.0, "relationship_type": "THEMATIC", "note": "고후 5:17 '새로운 피조물' 중생의 신학"},
            {"from_verse_id": 52005023, "to_verse_id": 3019002, "score": 4.8, "relationship_type": "QUOTATION", "note": "레 19:2 '너희는 거룩하라 나 여호와가 거룩함이니라' 성결의 언약"},
            {"from_verse_id": 52005023, "to_verse_id": 58012014, "score": 4.9, "relationship_type": "PARALLEL", "note": "히 12:14 '거룩함을 따르라 이것이 없이는 아무도 주를 보지 못하리라'"}
        ]

        with open(os.path.join(output_dir, "sample_cross_refs.json"), "w", encoding="utf-8") as f:
            json.dump(sample_cross_refs, f, ensure_ascii=False, indent=2)

        print(f"Sample dataset successfully generated in: {output_dir}")
