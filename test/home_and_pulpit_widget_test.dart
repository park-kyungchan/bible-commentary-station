import 'dart:convert';
import 'dart:io';
import 'package:bible_commentary_workstation/application/workstation_controller.dart';
import 'package:bible_commentary_workstation/core/theme/app_theme.dart';
import 'package:bible_commentary_workstation/data/services/artifact_sync_service.dart';
import 'package:bible_commentary_workstation/data/services/preferences_store.dart';
import 'package:bible_commentary_workstation/domain/models/bible_models.dart';
import 'package:bible_commentary_workstation/domain/repositories/bible_repository.dart';
import 'package:bible_commentary_workstation/main.dart';
import 'package:bible_commentary_workstation/presentation/widgets/pulpit_prompter_view.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

class _FakeBibleRepository implements BibleRepository {
  static const List<BibleBook> _books = [
    BibleBook(
      bookId: 1,
      osisCode: 'GEN',
      nameKr: '창세기',
      nameKrAbbr: '창',
      nameEn: 'Genesis',
      testament: 'OT',
      totalChapters: 50,
    ),
    BibleBook(
      bookId: 19,
      osisCode: 'PSA',
      nameKr: '시편',
      nameKrAbbr: '시',
      nameEn: 'Psalms',
      testament: 'OT',
      totalChapters: 150,
    ),
    BibleBook(
      bookId: 43,
      osisCode: 'JHN',
      nameKr: '요한복음',
      nameKrAbbr: '요',
      nameEn: 'John',
      testament: 'NT',
      totalChapters: 21,
    ),
  ];

  @override
  Future<List<BibleBook>> listBooks() async => _books;

  @override
  Future<List<BibleVerse>> getChapterVerses({
    required String versionCode,
    required int bookId,
    required int chapter,
  }) async {
    if (bookId == 19) {
      return [
        BibleVerse(
          verseId: 19001001,
          bookId: 19,
          chapter: chapter,
          verse: 1,
          versionCode: versionCode,
          text: '복 있는 사람은 악인의 꾀를 좇지 아니하며',
        ),
      ];
    }
    return [
      BibleVerse(
        verseId: 1022001,
        bookId: bookId,
        chapter: chapter,
        verse: 1,
        versionCode: versionCode,
        text: '그 일 후에 하나님이 아브라함을 시험하시려고 그를 부르시되',
      ),
      BibleVerse(
        verseId: 1022002,
        bookId: bookId,
        chapter: chapter,
        verse: 2,
        versionCode: versionCode,
        text: '여호와께서 가라사대 네 아들 네 사랑하는 독자 이삭을 데리고 모리아 땅으로 가서',
      ),
    ];
  }

  @override
  Future<List<BibleVerse>> searchVerses({
    required String query,
    String versionCode = 'KRV',
    int limit = 25,
  }) async =>
      const [];

  @override
  Future<List<CommentaryItem>> getCommentariesForVerse(int verseId) async => const [
        CommentaryItem(
          commentaryId: 1,
          sourceCode: 'MATTHEW_HENRY',
          sourceName: '매튜 헨리',
          passageDisplay: '창세기 22:2',
          title: '순종의 시험',
          contentMarkdown: '아브라함의 믿음은 즉각적인 순종으로 증명됩니다.',
        ),
      ];

  @override
  Future<List<CrossRefItem>> getCrossReferencesForVerse(
    int verseId, {
    String versionCode = 'KRV',
  }) async =>
      const [
        CrossRefItem(
          refId: 1,
          fromVerseId: 1022002,
          toVerseId: 43003016,
          toBookName: '요한복음',
          toChapter: 3,
          toVerse: 16,
          fullText: '하나님이 세상을 이처럼 사랑하사 독생자를 주셨으니',
          relationshipType: 'PROPHECY_FULFILLMENT',
        ),
      ];

  @override
  Future<List<ChainReference>> listChainReferences({String versionCode = 'KRV'}) async =>
      const [];

  @override
  Future<void> saveSermon(Sermon sermon) async {}

  @override
  Future<List<Sermon>> listSermons() async => const [];

  @override
  Future<void> close() async {}
}

void main() {
  testWidgets('R-FL-01: fresh empty dir renders real bootstrap error UI, never fake ready badge', (
    tester,
  ) async {
    final emptyDir = await Directory.systemTemp.createTemp('bcs_empty_app_');
    addTearDown(() async {
      if (await emptyDir.exists()) {
        await emptyDir.delete(recursive: true);
      }
    });

    final failingSync = ArtifactSyncService(
      directoryProvider: () async => emptyDir,
      manifestUrl: 'https://example.test/release_manifest.json',
      bundleUrl: 'https://example.test/bible_pastoral_core.db.gz',
      clientFactory: () => MockClient((_) async {
        // Manifest missing compressed_sha256 -> fail closed
        return http.Response(jsonEncode({'version': '3.0.0'}), 200);
      }),
    );

    final controller = WorkstationController(
      syncService: failingSync,
      repositoryOpener: (_) async => _FakeBibleRepository(),
    );
    await controller.bootstrapAndInitialize();

    await tester.pumpWidget(BiblicalWorkstationApp(controller: controller));
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('bootstrap_error_view')), findsOneWidget);
    expect(find.text('성경 자료를 불러오지 못했습니다'), findsOneWidget);
    expect(find.byKey(const Key('btn_retry_bootstrap')), findsOneWidget);
    expect(find.text('오프라인 FTS5 준비됨'), findsNothing);
    expect(find.text('자료 확인 필요'), findsOneWidget);

    final retrySize = tester.getSize(find.byKey(const Key('btn_retry_bootstrap')));
    expect(retrySize.height, greaterThanOrEqualTo(48.0));
  });

  testWidgets('R-FL-02: defaults to Sanctuary Hanji Light, toggles Dark, persists 4-step font scale', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(1280, 900);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.reset);

    final prefs = InMemoryPreferencesStore();
    final controller = WorkstationController(
      repository: _FakeBibleRepository(),
      preferencesStore: prefs,
    );
    await controller.initialize();

    await tester.pumpWidget(BiblicalWorkstationApp(controller: controller));
    await tester.pumpAndSettle();

    // Default ThemeMode.light with Sanctuary Hanji #FAF6EE canvas
    expect(controller.themeMode, equals(ThemeMode.light));
    final scaffoldLight = tester.widget<Scaffold>(find.byType(Scaffold).first);
    expect(
      Theme.of(tester.element(find.byWidget(scaffoldLight))).scaffoldBackgroundColor,
      equals(PastoralTheme.lightCanvas),
    );

    // Toggle to Evening Study Dark (#141210 canvas)
    await tester.tap(find.byKey(const Key('btn_theme_toggle')));
    await tester.pumpAndSettle();
    expect(controller.themeMode, equals(ThemeMode.dark));
    expect(
      Theme.of(tester.element(find.byType(Scaffold).first)).scaffoldBackgroundColor,
      equals(PastoralTheme.darkCanvas),
    );
    final savedPrefs = await prefs.load();
    expect(savedPrefs.themeMode, equals(ThemeMode.dark));

    // 4-step font scaler (default 21sp -> 25sp -> 30sp)
    expect(controller.scriptureFontSize, equals(21.0));
    await tester.tap(find.byKey(const Key('btn_font_inc')));
    await tester.pumpAndSettle();
    expect(controller.scriptureFontSize, equals(25.0));

    await tester.tap(find.byKey(const Key('btn_font_inc')));
    await tester.pumpAndSettle();
    expect(controller.scriptureFontSize, equals(30.0));
    expect((await prefs.load()).fontStepIndex, equals(3));

    // Verify >= 48dp hit targets on primary controls
    for (final key in const [
      Key('btn_font_dec'),
      Key('btn_font_inc'),
      Key('btn_theme_toggle'),
      Key('btn_pulpit_mode'),
      Key('btn_prev_chapter'),
      Key('btn_next_chapter'),
    ]) {
      final size = tester.getSize(find.byKey(key));
      expect(size.height, greaterThanOrEqualTo(48.0), reason: 'Height < 48dp for $key');
    }
  });

  testWidgets('R-FL-02: tablet 800x1280 exposes >=48dp Book Picker modal and switches books', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(800, 1280);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.reset);

    final controller = WorkstationController(repository: _FakeBibleRepository());
    await controller.initialize();

    await tester.pumpWidget(BiblicalWorkstationApp(controller: controller));
    await tester.pumpAndSettle();

    expect(find.text('창세기 22장'), findsOneWidget);

    final pickerBtn = find.byKey(const Key('btn_tablet_book_picker'));
    expect(pickerBtn, findsOneWidget);
    expect(tester.getSize(pickerBtn).height, greaterThanOrEqualTo(48.0));

    await tester.tap(pickerBtn);
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('book_picker_modal')), findsOneWidget);
    await tester.tap(find.byKey(const Key('picker_book_19')));
    await tester.pumpAndSettle();

    expect(find.text('시편 1장'), findsOneWidget);
    expect(find.textContaining('복 있는 사람은'), findsOneWidget);
  });

  testWidgets('R-FL-02: PulpitPrompterView enforces zero-glare palette, >=48dp targets & Korean labels', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(1280, 900);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.reset);

    var exited = false;
    await tester.pumpWidget(
      MaterialApp(
        theme: PastoralTheme.lightTheme,
        home: PulpitPrompterView(
          slides: const [
            PulpitSlide(section: '서론', header: '첫째 대지', body: '첫째 본문 내용'),
            PulpitSlide(section: '본론', header: '둘째 대지', body: '둘째 본문 내용'),
            PulpitSlide(section: '결론', header: '셋째 대지', body: '셋째 본문 내용'),
          ],
          targetDurationMins: 30,
          onExit: () => exited = true,
          onWakelockChanged: (_) async {},
        ),
      ),
    );
    await tester.pumpAndSettle();

    final scaffold = tester.widget<Scaffold>(find.byType(Scaffold));
    expect(scaffold.backgroundColor, equals(PastoralTheme.pulpitBackground));

    // Verify all Pulpit controls have >= 48dp height and plain Korean labels
    for (final entry in const {
      'pulpit_btn_smaller': '글자 작게',
      'pulpit_btn_bigger': '글자 크게',
      'pulpit_btn_timer_toggle': '일시정지',
      'pulpit_btn_timer_reset': '초기화',
      'pulpit_btn_exit': '나가기',
      'pulpit_btn_prev': '이전 대지',
      'pulpit_btn_next': '다음 대지',
    }.entries) {
      final finder = find.byKey(Key(entry.key));
      expect(finder, findsOneWidget);
      expect(find.text(entry.value), findsOneWidget);
      expect(
        tester.getSize(finder).height,
        greaterThanOrEqualTo(48.0),
        reason: 'Pulpit button ${entry.key} must be >= 48dp tall',
      );
    }

    // Advance slide via Korean next button
    expect(find.text('대지 1 / 3 · 서론'), findsOneWidget);
    await tester.tap(find.byKey(const Key('pulpit_btn_next')));
    await tester.pumpAndSettle();
    expect(find.text('대지 2 / 3 · 본론'), findsOneWidget);

    // Exit button invokes callback cleanly
    await tester.tap(find.byKey(const Key('pulpit_btn_exit')));
    await tester.pumpAndSettle();
    expect(exited, isTrue);
  });
}
