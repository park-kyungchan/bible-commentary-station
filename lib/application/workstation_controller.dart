import 'dart:async';
import 'dart:io';
import 'package:flutter/material.dart';
import '../core/theme/app_theme.dart';
import '../data/services/artifact_sync_service.dart';
import '../data/services/preferences_store.dart';
import '../domain/models/bible_models.dart';
import '../domain/repositories/bible_repository.dart';

enum DatabaseStatus {
  idle,
  syncing,
  ready,
  error,
}

class PulpitSlide {
  final String section;
  final String header;
  final String body;

  const PulpitSlide({
    required this.section,
    required this.header,
    required this.body,
  });
}

/// Central ChangeNotifier connecting SQLite bootstrap/sync, Exegesis,
/// persisted Sanctuary theme/font preferences, Sermon Studio & Pulpit Prompter.
class WorkstationController extends ChangeNotifier {
  BibleRepository? _repository;
  final ArtifactSyncService? _syncService;
  final Future<BibleRepository> Function(File dbFile)? _repositoryOpener;
  final PreferencesStore _preferencesStore;

  List<BibleBook> books = const [];
  List<BibleVerse> chapterVerses = const [];
  List<BibleVerse> searchResults = const [];
  List<CommentaryItem> commentaries = const [];
  List<CrossRefItem> crossRefs = const [];
  List<ChainReference> chains = const [];

  static const Map<String, String> supportedVersions = {
    'NKRV': '개역개정',
    'KRV': '개역한글',
    'RNKSV': '새번역',
    'EASY': '쉬운성경',
    'DOB': '우리말성경',
    'KLB': '현대인의 성경',
    'NKCB': '공동번역개정판',
    'KTV': '바른성경',
    'HKJV': '킹제임스 흠정역',
    'KKJV': '한글킹제임스',
    'TKV': '현대어성경',
    'HCHV': '개역한글 국한문',
    'KCB': '공동번역',
    'CATH': '가톨릭성경',
    'ESV': '영어 표준역 (ESV)',
    'TNIV': '영어 신국제역 (TNIV)',
    'NASB': '영어 신미국표준역 (NASB)',
    'NLT': '영어 새번역 (NLT)',
    'NKJV': '영어 신킹제임스',
    'EN_NRSV': '영어 신개정표준역 (NRSV)',
    'MSG': '영어 메시지 성경 (MSG)',
    'HCSB': '영어 홀만 표준역 (HCSB)',
    'GNT': '영어 굿뉴스 성경 (GNT)',
  };

  int selectedBookId = 1;
  int selectedChapter = 22;
  int selectedVerseNumber = 2;
  String selectedVersionCode = 'KRV';
  bool isUsingFallbackKrv = false;
  bool isLoading = false;
  DatabaseStatus dbStatus = DatabaseStatus.idle;
  SyncProgress? syncProgress;
  String? errorMessage;
  String searchQuery = '';

  ThemeMode themeMode = ThemeMode.light;
  int fontStepIndex = PastoralTheme.defaultFontStepIndex;

  late Sermon activeSermon;
  final List<String> scrapedCitations = [];

  WorkstationController({
    BibleRepository? repository,
    ArtifactSyncService? syncService,
    Future<BibleRepository> Function(File dbFile)? repositoryOpener,
    PreferencesStore? preferencesStore,
  })  : _repository = repository,
        _syncService = syncService,
        _repositoryOpener = repositoryOpener,
        _preferencesStore = preferencesStore ?? InMemoryPreferencesStore() {
    activeSermon = Sermon(
      sermonId: 'sermon_default',
      title: '모리아 산의 온전한 순종과 여호와 이레의 축복',
      preacher: '목회자',
      sermonDate: DateTime.now().toIso8601String().substring(0, 10),
      scriptureRef: '창세기 22:1-14',
      outline: const [
        SermonOutlinePoint(
          section: '서론',
          title: '믿음의 시험과 인생의 광야',
          content: '하나님의 부르심 앞에 즉각 응답한 아브라함의 순종을 살펴본다.',
        ),
        SermonOutlinePoint(
          section: '본론 I',
          title: '유일한 독자를 내려놓는 결단 (창 22:2)',
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

  bool get isDatabaseReady => dbStatus == DatabaseStatus.ready && books.isNotEmpty;

  double get scriptureFontSize => PastoralTheme.scriptureFontSteps[fontStepIndex];

  double get studyFontSize => PastoralTheme.studyFontSteps[fontStepIndex];

  String get fontStepLabel => PastoralTheme.fontStepLabels[fontStepIndex];

  bool get canDecreaseFont => fontStepIndex > 0;

  bool get canIncreaseFont => fontStepIndex < PastoralTheme.scriptureFontSteps.length - 1;

  String get selectedVersionName =>
      supportedVersions[selectedVersionCode] ?? selectedVersionCode;

  BibleBook? get currentBook {
    for (final b in books) {
      if (b.bookId == selectedBookId) return b;
    }
    return null;
  }

  /// First-run safe bootstrap: loads preferences, downloads & verifies SQLite bundle
  /// before opening SQLite (closing any prior handle cleanly around atomic swap),
  /// and surfaces real errors instead of rendering a blank screen.
  Future<void> bootstrapAndInitialize({bool forceSync = false}) async {
    isLoading = true;
    errorMessage = null;
    notifyListeners();

    final prefs = await _preferencesStore.load();
    themeMode = prefs.themeMode;
    fontStepIndex = prefs.fontStepIndex;
    notifyListeners();

    try {
      if (_syncService != null && (_repository == null || forceSync)) {
        final hasLocalDb = !forceSync && await _syncService.isLocalDatabaseReady();
        if (!hasLocalDb) {
          dbStatus = DatabaseStatus.syncing;
          notifyListeners();

          String? syncError;
          await for (final progress in _syncService.downloadAndInstallMasterDb(
            beforeSwap: closeDatabase,
          )) {
            syncProgress = progress;
            if (progress.error != null) {
              syncError = progress.error;
            }
            notifyListeners();
          }

          if (syncError != null) {
            dbStatus = DatabaseStatus.error;
            errorMessage = syncError;
            isLoading = false;
            notifyListeners();
            return;
          }
        }

        if (_repositoryOpener == null) {
          throw StateError('데이터베이스 연결 설정이 누락되었습니다.');
        }
        await closeDatabase();
        final dbFile = await _syncService.getLocalDbFile();
        _repository = await _repositoryOpener(dbFile);
      }

      if (_repository == null) {
        dbStatus = DatabaseStatus.error;
        errorMessage = '오프라인 성경 자료가 아직 설치되지 않았습니다. 인터넷 연결 후 다시 시도해 주세요.';
        isLoading = false;
        notifyListeners();
        return;
      }

      await initialize();
    } catch (e) {
      dbStatus = DatabaseStatus.error;
      errorMessage = e.toString();
      isLoading = false;
      notifyListeners();
    }
  }

  Future<void> retryBootstrap() => bootstrapAndInitialize(forceSync: true);

  Future<void> initialize() async {
    final repo = _repository;
    if (repo == null) {
      dbStatus = DatabaseStatus.error;
      errorMessage = '성경 데이터베이스에 연결할 수 없습니다.';
      isLoading = false;
      notifyListeners();
      return;
    }

    isLoading = true;
    errorMessage = null;
    notifyListeners();
    try {
      final prefs = await _preferencesStore.load();
      themeMode = prefs.themeMode;
      fontStepIndex = prefs.fontStepIndex;

      books = await repo.listBooks();
      if (books.isEmpty) {
        throw StateError('성경 66권 목록을 찾을 수 없습니다. 성경 자료를 다시 받아 주세요.');
      }
      if (!books.any((b) => b.bookId == selectedBookId)) {
        selectedBookId = books.first.bookId;
        selectedChapter = 1;
        selectedVerseNumber = 1;
      }

      chains = await repo.listChainReferences();
      final savedSermons = await repo.listSermons();
      if (savedSermons.isNotEmpty) {
        activeSermon = savedSermons.first;
      }
      await loadChapter(
        selectedBookId,
        selectedChapter,
        verseNumber: selectedVerseNumber,
      );
      dbStatus = DatabaseStatus.ready;
    } catch (e) {
      dbStatus = DatabaseStatus.error;
      errorMessage = e.toString();
    } finally {
      isLoading = false;
      notifyListeners();
    }
  }

  Future<void> setVersionCode(String code) async {
    if (!supportedVersions.containsKey(code)) return;
    selectedVersionCode = code;
    if (_repository == null) {
      notifyListeners();
      return;
    }
    await loadChapter(
      selectedBookId,
      selectedChapter,
      verseNumber: selectedVerseNumber,
    );
  }

  Future<void> loadChapter(int bookId, int chapter, {int verseNumber = 1}) async {
    final repo = _repository;
    if (repo == null) return;

    selectedBookId = bookId;
    selectedChapter = chapter;
    var verses = await repo.getChapterVerses(
      versionCode: selectedVersionCode,
      bookId: bookId,
      chapter: chapter,
    );
    if (verses.isEmpty && selectedVersionCode != 'KRV') {
      verses = await repo.getChapterVerses(
        versionCode: 'KRV',
        bookId: bookId,
        chapter: chapter,
      );
      isUsingFallbackKrv = verses.isNotEmpty;
    } else {
      isUsingFallbackKrv = false;
    }
    chapterVerses = verses;
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

  Future<void> searchScripture(String query) async {
    final repo = _repository;
    searchQuery = query.trim();
    if (repo == null || searchQuery.isEmpty) {
      searchResults = const [];
      notifyListeners();
      return;
    }
    var results = await repo.searchVerses(
      query: searchQuery,
      versionCode: selectedVersionCode,
    );
    if (results.isEmpty && selectedVersionCode != 'KRV') {
      results = await repo.searchVerses(
        query: searchQuery,
        versionCode: 'KRV',
      );
    }
    searchResults = results;
    notifyListeners();
  }

  Future<void> toggleThemeMode() async {
    themeMode = themeMode == ThemeMode.dark ? ThemeMode.light : ThemeMode.dark;
    notifyListeners();
    await _persistPreferences();
  }

  Future<void> increaseFontSize() => setFontStep(fontStepIndex + 1);

  Future<void> decreaseFontSize() => setFontStep(fontStepIndex - 1);

  Future<void> setFontStep(int stepIndex) async {
    final clamped = stepIndex.clamp(0, PastoralTheme.scriptureFontSteps.length - 1);
    if (clamped == fontStepIndex) return;
    fontStepIndex = clamped;
    notifyListeners();
    await _persistPreferences();
  }

  Future<void> _persistPreferences() async {
    await _preferencesStore.save(
      WorkstationPreferences(
        themeMode: themeMode,
        fontStepIndex: fontStepIndex,
      ),
    );
  }

  Future<void> _loadVerseExegesis() async {
    final repo = _repository;
    if (repo == null) return;
    final verseId = selectedBookId * 1000000 + selectedChapter * 1000 + selectedVerseNumber;
    final effectiveVersion = isUsingFallbackKrv ? 'KRV' : selectedVersionCode;
    commentaries = await repo.getCommentariesForVerse(verseId);
    crossRefs = await repo.getCrossReferencesForVerse(
      verseId,
      versionCode: effectiveVersion,
    );
  }

  void scrapCitation(String source, String text) {
    scrapedCitations.insert(0, '[$source] $text');
    notifyListeners();
  }

  Future<void> updateActiveSermon(Sermon updated) async {
    activeSermon = updated;
    await _repository?.saveSermon(updated);
    notifyListeners();
  }

  /// Live-builds pulpit slides directly from the currently edited sermon.
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

  /// Builds pulpit slides for an offline Korean worship liturgy.
  List<PulpitSlide> buildLiturgySlides(WorshipLiturgy liturgy) {
    return liturgy.slides
        .map(
          (slide) => PulpitSlide(
            section: liturgy.title,
            header: slide.heading,
            body: slide.body,
          ),
        )
        .toList();
  }

  Future<void> closeDatabase() async {
    final repo = _repository;
    _repository = null;
    if (repo != null) {
      await repo.close();
    }
  }

  @override
  void dispose() {
    unawaited(closeDatabase());
    super.dispose();
  }
}
