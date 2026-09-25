/// Domain models for Bible Exegesis, Commentaries, Cross-References & Sermons

class BibleBook {
  final int bookId;
  final String osisCode;
  final String nameKr;
  final String nameKrAbbr;
  final String nameEn;
  final String testament; // OT or NT
  final int totalChapters;

  BibleBook({
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

  BibleVerse({
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
  final String sourceCode; // oxford, wesley, hokma, grand, charisma, henry, baker, esv
  final String sourceName;
  final String passageDisplay;
  final String? title;
  final String contentMarkdown;
  final String? theologicalTags;
  final String? practicalPoints;

  CommentaryItem({
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

  CrossRefItem({
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

  String get refString => "$toBookName $toChapter:$toVerse";
}

class ChainLink {
  final String ref;
  final String book;
  final String text;
  final String type;
  final String point;

  ChainLink({
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

  ChainReference({
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

  SermonOutlinePoint({
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
  final String? syncStatus;

  Sermon({
    required this.sermonId,
    required this.title,
    this.preacher = '박우호 목사',
    required this.sermonDate,
    this.serviceType = '주일대예배',
    required this.scriptureRef,
    this.targetDurationMins = 30,
    required this.outline,
    this.fullTextMarkdown,
    this.syncStatus = 'SYNCED',
  });
}
