// Domain models for Bible Exegesis, Commentaries, Cross-References & Sermons.

class BibleBook {
  final int bookId;
  final String osisCode;
  final String nameKr;
  final String nameKrAbbr;
  final String nameEn;
  final String testament; // OT or NT
  final int totalChapters;

  const BibleBook({
    required this.bookId,
    required this.osisCode,
    required this.nameKr,
    required this.nameKrAbbr,
    required this.nameEn,
    required this.testament,
    required this.totalChapters,
  });
}

class BibleVerse {
  final int verseId;
  final int bookId;
  final int chapter;
  final int verse;
  final String versionCode;
  final String text;
  final String? textWithStrong;

  const BibleVerse({
    required this.verseId,
    required this.bookId,
    required this.chapter,
    required this.verse,
    required this.versionCode,
    required this.text,
    this.textWithStrong,
  });
}

class CommentaryItem {
  final int commentaryId;
  final String sourceCode;
  final String sourceName;
  final String passageDisplay;
  final String? title;
  final String contentMarkdown;
  final String? theologicalTags;
  final String? practicalPoints;

  const CommentaryItem({
    required this.commentaryId,
    required this.sourceCode,
    required this.sourceName,
    required this.passageDisplay,
    this.title,
    required this.contentMarkdown,
    this.theologicalTags,
    this.practicalPoints,
  });
}

class CrossRefItem {
  final int refId;
  final int fromVerseId;
  final int toVerseId;
  final String toBookName;
  final int toChapter;
  final int toVerse;
  final String fullText;
  final String relationshipType;
  final double score;

  const CrossRefItem({
    required this.refId,
    required this.fromVerseId,
    required this.toVerseId,
    required this.toBookName,
    required this.toChapter,
    required this.toVerse,
    required this.fullText,
    required this.relationshipType,
    this.score = 1.0,
  });

  String get refString => '$toBookName $toChapter:$toVerse';

  /// Plain-Korean label avoiding raw developer enum names in UI.
  String get relationshipLabel {
    switch (relationshipType) {
      case 'QUOTATION':
        return '인용 말씀';
      case 'PARALLEL':
        return '병행 본문';
      case 'PROPHECY_FULFILLMENT':
        return '약속과 성취';
      case 'EXPLANATORY':
        return '풀이 연결';
      case 'THEMATIC':
      default:
        return '주제 연결';
    }
  }
}

class ChainLink {
  final String ref;
  final String book;
  final String text;
  final String type;
  final String point;

  const ChainLink({
    required this.ref,
    required this.book,
    required this.text,
    required this.type,
    required this.point,
  });
}

class ChainReference {
  final String topic;
  final String title;
  final String meaning;
  final String summary;
  final List<ChainLink> chains;

  const ChainReference({
    required this.topic,
    required this.title,
    required this.meaning,
    required this.summary,
    required this.chains,
  });
}

class SermonOutlinePoint {
  final String section; // '서론', '본론 I', '본론 II', '본론 III', '결론'
  final String title;
  final String content;
  final List<String> citations;

  const SermonOutlinePoint({
    required this.section,
    required this.title,
    required this.content,
    this.citations = const [],
  });
}

class Sermon {
  final String sermonId;
  final String title;
  final String preacher;
  final String sermonDate;
  final String serviceType;
  final String scriptureRef;
  final int targetDurationMins;
  final List<SermonOutlinePoint> outline;
  final String? fullTextMarkdown;
  final String? gdriveFileId;
  final String? syncStatus;

  const Sermon({
    required this.sermonId,
    required this.title,
    this.preacher = '목회자',
    required this.sermonDate,
    this.serviceType = '주일대예배',
    required this.scriptureRef,
    this.targetDurationMins = 30,
    required this.outline,
    this.fullTextMarkdown,
    this.gdriveFileId,
    this.syncStatus = 'SYNCED',
  });

  Sermon copyWith({
    String? sermonId,
    String? title,
    String? preacher,
    String? sermonDate,
    String? serviceType,
    String? scriptureRef,
    int? targetDurationMins,
    List<SermonOutlinePoint>? outline,
    String? fullTextMarkdown,
    String? gdriveFileId,
    String? syncStatus,
  }) {
    return Sermon(
      sermonId: sermonId ?? this.sermonId,
      title: title ?? this.title,
      preacher: preacher ?? this.preacher,
      sermonDate: sermonDate ?? this.sermonDate,
      serviceType: serviceType ?? this.serviceType,
      scriptureRef: scriptureRef ?? this.scriptureRef,
      targetDurationMins: targetDurationMins ?? this.targetDurationMins,
      outline: outline ?? this.outline,
      fullTextMarkdown: fullTextMarkdown ?? this.fullTextMarkdown,
      gdriveFileId: gdriveFileId ?? this.gdriveFileId,
      syncStatus: syncStatus ?? this.syncStatus,
    );
  }
}

class WorshipLiturgySlide {
  final String heading;
  final List<String> lines;

  const WorshipLiturgySlide({
    required this.heading,
    required this.lines,
  });

  String get body => lines.join('\n');
}

class WorshipLiturgy {
  final String id;
  final String title;
  final String category;
  final String citation;
  final List<WorshipLiturgySlide> slides;

  const WorshipLiturgy({
    required this.id,
    required this.title,
    required this.category,
    required this.citation,
    required this.slides,
  });
}

/// Built-in offline Korean worship liturgy catalog available without network access.
const List<WorshipLiturgy> kOfflineWorshipLiturgies = [
  WorshipLiturgy(
    id: 'apostles_creed_ecumenical',
    title: '사도신경 (새번역)',
    category: '신앙고백',
    citation: '한국기독교교회협의회 · 대한예수교장로회 공동 새 번역',
    slides: [
      WorshipLiturgySlide(
        heading: '사도신경 (1/5)',
        lines: [
          '나는 전능하신 아버지 하나님,',
          '천지의 창조주를 믿습니다.',
          '나는 그의 유일하신 아들,',
          '우리 주 예수 그리스도를 믿습니다.',
        ],
      ),
      WorshipLiturgySlide(
        heading: '사도신경 (2/5)',
        lines: [
          '그는 성령으로 잉태되어',
          '동정녀 마리아에게서 나시고,',
          '본디오 빌라도에게 고난을 받아',
          '십자가에 못박혀 죽으시고,',
        ],
      ),
      WorshipLiturgySlide(
        heading: '사도신경 (3/5)',
        lines: [
          '장사된 지 사흘 만에 죽은 자',
          '가운데서 다시 살아나셨으며,',
          '하늘에 오르시어 전능하신 아버지',
          '하나님 우편에 앉아 계시다가,',
        ],
      ),
      WorshipLiturgySlide(
        heading: '사도신경 (4/5)',
        lines: [
          '거기로부터 살아 있는 자와 죽은 자를',
          '심판하러 오십니다.',
          '나는 성령을 믿으며 거룩한 공교회와',
          '성도의 교제와 죄를 용서받는 것과',
        ],
      ),
      WorshipLiturgySlide(
        heading: '사도신경 (5/5)',
        lines: [
          '몸의 부활과 영생을 믿습니다.',
          '아멘.',
        ],
      ),
    ],
  ),
  WorshipLiturgy(
    id: 'apostles_creed_traditional',
    title: '사도신경 (전통)',
    category: '신앙고백',
    citation: '한국 개신교 전통 번역 (공공도메인)',
    slides: [
      WorshipLiturgySlide(
        heading: '사도신경 · 전통 (1/4)',
        lines: [
          '전능하사 천지를 만드신 하나님 아버지를',
          '내가 믿사오며,',
          '그 외아들 우리 주 예수 그리스도를 믿사오니,',
        ],
      ),
      WorshipLiturgySlide(
        heading: '사도신경 · 전통 (2/4)',
        lines: [
          '이는 성령으로 잉태하사 동정녀 마리아에게 나시고,',
          '본디오 빌라도에게 고난을 받으사',
          '십자가에 못박혀 죽으시고,',
        ],
      ),
      WorshipLiturgySlide(
        heading: '사도신경 · 전통 (3/4)',
        lines: [
          '장사한 지 사흘 만에 죽은 자 가운데서 다시 살아나시며,',
          '하늘에 오르사 전능하신 하나님 우편에 앉아 계시다가,',
          '저리로서 산 자와 죽은 자를 심판하러 오시리라.',
        ],
      ),
      WorshipLiturgySlide(
        heading: '사도신경 · 전통 (4/4)',
        lines: [
          '성령을 믿사오며, 거룩한 공회와',
          '성도가 서로 교통하는 것과 죄를 사하여 주시는 것과',
          '몸이 다시 사는 것과 영원히 사는 것을 믿사옵나이다. 아멘.',
        ],
      ),
    ],
  ),
  WorshipLiturgy(
    id: 'lords_prayer_ecumenical',
    title: '주기도문 (새번역)',
    category: '주기도문',
    citation: '마태복음 6:9-13 (새 번역)',
    slides: [
      WorshipLiturgySlide(
        heading: '주기도문 (1/3)',
        lines: [
          '하늘에 계신 우리 아버지,',
          '아버지의 이름을 거룩하게 하시며,',
          '아버지의 나라가 오게 하시며,',
          '아버지의 뜻이 하늘에서와 같이',
          '땅에서도 이루어지게 하소서.',
        ],
      ),
      WorshipLiturgySlide(
        heading: '주기도문 (2/3)',
        lines: [
          '오늘 우리에게 일용할 양식을 주시고,',
          '우리가 우리에게 잘못한 사람을',
          '용서하여 준 것같이',
          '우리 죄를 용서하여 주시고,',
        ],
      ),
      WorshipLiturgySlide(
        heading: '주기도문 (3/3)',
        lines: [
          '우리를 시험에 빠지지 않게 하시고',
          '악에서 구하소서.',
          '나라와 권능과 영광이',
          '영원히 아버지의 것입니다. 아멘.',
        ],
      ),
    ],
  ),
  WorshipLiturgy(
    id: 'lords_prayer_traditional',
    title: '주기도문 (전통)',
    category: '주기도문',
    citation: '마태복음 6:9-13 (전통 번역 · 공공도메인)',
    slides: [
      WorshipLiturgySlide(
        heading: '주기도문 · 전통 (1/3)',
        lines: [
          '하늘에 계신 우리 아버지여,',
          '이름이 거룩히 여김을 받으시오며,',
          '나라이 임하옵시며,',
          '뜻이 하늘에서 이룬 것같이 땅에서도 이루어지이다.',
        ],
      ),
      WorshipLiturgySlide(
        heading: '주기도문 · 전통 (2/3)',
        lines: [
          '오늘날 우리에게 일용할 양식을 주옵시고,',
          '우리가 우리에게 죄 지은 자를 사하여 준 것같이',
          '우리 죄를 사하여 주옵시고,',
        ],
      ),
      WorshipLiturgySlide(
        heading: '주기도문 · 전통 (3/3)',
        lines: [
          '우리를 시험에 들게 하지 마옵시고',
          '다만 악에서 구하옵소서.',
          '대개 나라와 권세와 영광이',
          '아버지께 영원히 있사옵나이다. 아멘.',
        ],
      ),
    ],
  ),
  WorshipLiturgy(
    id: 'communion_institution',
    title: '성찬 예식 (고전 11:23-25)',
    category: '성례전',
    citation: '고린도전서 11:23-25 (개역한글)',
    slides: [
      WorshipLiturgySlide(
        heading: '성찬 예식 · 떡을 나누며',
        lines: [
          '주 예수께서 잡히시던 밤에 떡을 가지사',
          '축사하시고 떼어 가라사대',
          '이것은 너희를 위하는 내 몸이니',
          '이것을 행하여 나를 기념하라 하시고',
        ],
      ),
      WorshipLiturgySlide(
        heading: '성찬 예식 · 잔을 나누며',
        lines: [
          '식후에 또한 이와 같이 잔을 가지시고 가라사대',
          '이 잔은 내 피로 세운 새 언약이니',
          '이것을 행하여 마실 때마다 나를 기념하라 하셨으니',
          '(고린도전서 11:23-25)',
        ],
      ),
    ],
  ),
  WorshipLiturgy(
    id: 'benediction_pauline',
    title: '축도 (고후 13:13)',
    category: '축도',
    citation: '고린도후서 13:13 (개역한글)',
    slides: [
      WorshipLiturgySlide(
        heading: '축도 (고린도후서 13:13)',
        lines: [
          '주 예수 그리스도의 은혜와',
          '하나님의 사랑과',
          '성령의 교통하심이',
          '너희 무리와 함께 있을지어다. 아멘.',
        ],
      ),
    ],
  ),
  WorshipLiturgy(
    id: 'benediction_aaronic',
    title: '축도 · 아론의 제사장 축복',
    category: '축도',
    citation: '민수기 6:24-26 (개역한글)',
    slides: [
      WorshipLiturgySlide(
        heading: '축도 (민수기 6:24-26)',
        lines: [
          '여호와는 네게 복을 주시고 너를 지키시기를 원하며',
          '여호와는 그 얼굴로 네게 비취사 은혜 베푸시기를 원하며',
          '여호와는 그 얼굴을 네게로 향하여 드사',
          '평강 주시기를 원하노라. 아멘.',
        ],
      ),
    ],
  ),
  WorshipLiturgy(
    id: 'benediction_hebrews',
    title: '축도 · 평강의 하나님의 축복',
    category: '축도',
    citation: '히브리서 13:20-21 (개역한글)',
    slides: [
      WorshipLiturgySlide(
        heading: '축도 (히브리서 13:20-21)',
        lines: [
          '양의 큰 목자이신 우리 주 예수를',
          '영원한 언약의 피로 죽은 자 가운데서 이끌어 내신 평강의 하나님이',
          '모든 선한 일에 너희를 온전케 하사 자기 뜻을 행하게 하시고',
          '예수 그리스도로 말미암아 우리 속에 이루시기를 원하노라.',
          '영광이 그에게 세세무궁토록 있을지어다. 아멘.',
        ],
      ),
    ],
  ),
  WorshipLiturgy(
    id: 'ten_commandments_standard',
    title: '십계명 (출애굽기 20:1-17)',
    category: '신앙고백',
    citation: '출애굽기 20:1-17 (개역한글 · 열 가지 언약의 말씀)',
    slides: [
      WorshipLiturgySlide(
        heading: '십계명 · 제1~4계명 (하나님 사랑)',
        lines: [
          '제1계명: 너는 나 외에는 다른 신들을 네게 있게 말지니라.',
          '제2계명: 너를 위하여 새긴 우상을 만들지 말고 절하지 말라.',
          '제3계명: 너는 네 하나님 여호와의 이름을 망령되이 일컫지 말라.',
          '제4계명: 안식일을 기억하여 거룩히 지키라.',
        ],
      ),
      WorshipLiturgySlide(
        heading: '십계명 · 제5~10계명 (이웃 사랑)',
        lines: [
          '제5계명: 네 부모를 공경하라.',
          '제6계명: 살인하지 말지니라.',
          '제7계명: 간음하지 말지니라.',
          '제8계명: 도적질하지 말지니라.',
          '제9계명: 네 이웃에 대하여 거짓 증거하지 말지니라.',
          '제10계명: 네 이웃의 집을 탐내지 말지니라. 아멘.',
        ],
      ),
    ],
  ),
  WorshipLiturgy(
    id: 'call_to_worship_psalm100',
    title: '예배로의 부름 · 초청과 기원',
    category: '예배기원',
    citation: '시편 100:1-5 · 요한복음 4:24',
    slides: [
      WorshipLiturgySlide(
        heading: '예배로의 부름 (시편 100:1-5)',
        lines: [
          '온 땅이여 여호와께 즐거이 부를지어다.',
          '기쁨으로 여호와를 섬기며 노래하면서 그 앞에 나아갈지어다.',
          '감사함으로 그 문에 들어가며 찬송함으로 그 궁정에 들어가서',
          '그에게 감사하며 그 이름을 송축할지어다. 아멘.',
        ],
      ),
    ],
  ),
  WorshipLiturgy(
    id: 'baptism_vows_standard',
    title: '세례 · 입교 문답과 서약 예식',
    category: '성례전',
    citation: '마태복음 28:19 · 로마서 10:9-10',
    slides: [
      WorshipLiturgySlide(
        heading: '세례 · 입교 서약',
        lines: [
          '1. 천지의 창조주 하나님과 구주 예수 그리스도와 성령을 믿습니까?',
          '2. 오직 예수 그리스도의 보혈과 은혜로만 구원받는 줄 믿습니까?',
          '3. 하나님의 말씀대로 거룩하게 살며 교회에 충성하기로 서약합니까? (아멘)',
        ],
      ),
    ],
  ),
  WorshipLiturgy(
    id: 'benediction_jude_doxology',
    title: '축도 · 유다서 영광의 송영',
    category: '축도',
    citation: '유다서 1:24-25 (개역한글)',
    slides: [
      WorshipLiturgySlide(
        heading: '축도 (유다서 1:24-25)',
        lines: [
          '능히 너희를 보호하사 거침이 없게 하시고',
          '너희로 그 영광 앞에 흠이 없이 기쁨으로 서게 하실 자',
          '곧 우리 구주 홀로 하나이신 하나님께',
          '영광과 위엄과 권세와 권능이 영원토록 있을지어다. 아멘.',
        ],
      ),
    ],
  ),
];
