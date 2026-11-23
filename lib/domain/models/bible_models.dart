/// Domain models for Bible Exegesis, Commentaries, Cross-References & Sermons.

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
