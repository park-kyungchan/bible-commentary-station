import 'package:flutter/foundation.dart';
import '../domain/models/bible_models.dart';
import '../domain/repositories/bible_repository.dart';

class PulpitSlide {
  final String section;
  final String header;
  final String body;

  const PulpitSlide({required this.section, required this.header, required this.body});
}

/// Central ChangeNotifier connecting SQLite Repository, Exegesis, Sermon Studio & Pulpit Prompter.
class WorkstationController extends ChangeNotifier {
  final BibleRepository _repository;

  List<BibleBook> books = const [];
  List<BibleVerse> chapterVerses = const [];
  List<CommentaryItem> commentaries = const [];
  List<CrossRefItem> crossRefs = const [];
  List<ChainReference> chains = const [];

  int selectedBookId = 1;
  int selectedChapter = 22;
  int selectedVerseNumber = 2;
  bool isLoading = false;
  String? errorMessage;

  late Sermon activeSermon;
  final List<String> scrapedCitations = [];

  WorkstationController(this._repository) {
    activeSermon = Sermon(
      sermonId: 'sermon_default',
      title: '모리아 산의 온전한 순종과 여호와 이레의 축복',
      sermonDate: DateTime.now().toIso8601String().substring(0, 10),
      scriptureRef: '창세기 22:1-14',
      outline: [
        SermonOutlinePoint(
          section: '서론',
          title: '믿음의 시험과 인생의 광야',
          content: '하나님의 부르심 앞에 즉각 응답한 아브라함의 순종을 살펴본다.',
        ),
        SermonOutlinePoint(
          section: '본론 I',
          title: '유일한 독자(야히드)를 내려놓는 결단 (창 22:2)',
          content: '선물보다 선물을 주신 하나님을 더 사랑하는 성숙한 믿음.',
        ),
        SermonOutlinePoint(
          section: '결론',
          title: '여호와 이레의 공급과 결단 (창 22:13-14)',
          content: '순종의 끝에서 예비하시는 하나님을 신뢰하며 나아간다.',
        ),
      ],
    );
  }

  BibleBook? get currentBook {
    for (final b in books) {
      if (b.bookId == selectedBookId) return b;
    }
    return null;
  }

  Future<void> initialize() async {
    isLoading = true;
    errorMessage = null;
    notifyListeners();
    try {
      books = await _repository.listBooks();
      chains = await _repository.listChainReferences();
      final savedSermons = await _repository.listSermons();
      if (savedSermons.isNotEmpty) {
        activeSermon = savedSermons.first;
      }
      await loadChapter(selectedBookId, selectedChapter, verseNumber: selectedVerseNumber);
    } catch (e) {
      errorMessage = e.toString();
    } finally {
      isLoading = false;
      notifyListeners();
    }
  }

  Future<void> loadChapter(int bookId, int chapter, {int verseNumber = 1}) async {
    selectedBookId = bookId;
    selectedChapter = chapter;
    chapterVerses = await _repository.getChapterVerses(
      versionCode: 'KRV',
      bookId: bookId,
      chapter: chapter,
    );
    if (chapterVerses.isNotEmpty) {
      final hasTarget = chapterVerses.any((v) => v.verse == verseNumber);
      selectedVerseNumber = hasTarget ? verseNumber : chapterVerses.first.verse;
      await _loadVerseExegesis();
    } else {
      commentaries = const [];
      crossRefs = const [];
    }
    notifyListeners();
  }

  Future<void> selectVerse(int verseNumber) async {
    selectedVerseNumber = verseNumber;
    await _loadVerseExegesis();
    notifyListeners();
  }

  Future<void> previousChapter() async {
    if (selectedChapter > 1) {
      await loadChapter(selectedBookId, selectedChapter - 1);
    }
  }

  Future<void> nextChapter() async {
    final maxCh = currentBook?.totalChapters ?? 1;
    if (selectedChapter < maxCh) {
      await loadChapter(selectedBookId, selectedChapter + 1);
    }
  }

  Future<void> _loadVerseExegesis() async {
    final verseId = selectedBookId * 1000000 + selectedChapter * 1000 + selectedVerseNumber;
    commentaries = await _repository.getCommentariesForVerse(verseId);
    crossRefs = await _repository.getCrossReferencesForVerse(verseId);
  }

  void scrapCitation(String source, String text) {
    scrapedCitations.insert(0, '[$source] $text');
    notifyListeners();
  }

  Future<void> updateActiveSermon(Sermon updated) async {
    activeSermon = updated;
    await _repository.saveSermon(updated);
    notifyListeners();
  }

  /// Live-builds pulpit slides directly from the currently edited sermon (no hardcoded mock slides).
  List<PulpitSlide> buildPulpitSlides() {
    return [
      PulpitSlide(
        section: '설교 본문 및 제목',
        header: activeSermon.scriptureRef,
        body: '${activeSermon.title}\n\n${activeSermon.sermonDate} · 목표 ${activeSermon.targetDurationMins}분',
      ),
      ...activeSermon.outline.map(
        (pt) => PulpitSlide(
          section: pt.section,
          header: pt.title,
          body: pt.content,
        ),
      ),
    ];
  }
}
