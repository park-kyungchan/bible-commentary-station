import 'package:bible_commentary_workstation/data/repositories/sqlite_bible_repository.dart';
import 'package:bible_commentary_workstation/domain/models/bible_models.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sqlite3/sqlite3.dart';

Database _createTestDb() {
  final db = sqlite3.openInMemory();
  db.execute('''
    CREATE TABLE bible_books (
      book_id INTEGER PRIMARY KEY,
      osis_code TEXT NOT NULL UNIQUE,
      name_kr TEXT NOT NULL,
      name_kr_abbr TEXT NOT NULL,
      name_en TEXT NOT NULL,
      testament TEXT NOT NULL,
      category TEXT NOT NULL,
      total_chapters INTEGER NOT NULL,
      total_verses INTEGER NOT NULL
    );
  ''');
  db.execute('''
    CREATE TABLE bible_verses (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      verse_id INTEGER NOT NULL,
      book_id INTEGER NOT NULL,
      chapter INTEGER NOT NULL,
      verse INTEGER NOT NULL,
      version_code TEXT NOT NULL,
      text TEXT NOT NULL,
      text_with_strong TEXT
    );
  ''');
  db.execute('''
    CREATE VIRTUAL TABLE fts_bible_verses_unicode USING fts5(
      text, content='bible_verses', content_rowid='id', tokenize='unicode61 remove_diacritics 2'
    );
  ''');
  db.execute('''
    CREATE VIRTUAL TABLE fts_bible_verses_trigram USING fts5(
      text, content='bible_verses', content_rowid='id', tokenize='trigram'
    );
  ''');
  db.execute('''
    CREATE TRIGGER trg_bible_verses_ai AFTER INSERT ON bible_verses BEGIN
      INSERT INTO fts_bible_verses_unicode(rowid, text) VALUES (new.id, new.text);
      INSERT INTO fts_bible_verses_trigram(rowid, text) VALUES (new.id, new.text);
    END;
  ''');
  db.execute('''
    CREATE TABLE cross_references (
      ref_id INTEGER PRIMARY KEY AUTOINCREMENT,
      from_verse_id INTEGER NOT NULL,
      to_verse_id INTEGER NOT NULL,
      score REAL DEFAULT 1.0,
      relationship_type TEXT DEFAULT 'THEMATIC',
      note TEXT
    );
  ''');
  db.execute('''
    CREATE TABLE chain_topics (
      topic_key TEXT PRIMARY KEY,
      title TEXT NOT NULL,
      meaning TEXT NOT NULL,
      summary TEXT NOT NULL
    );
  ''');
  db.execute('''
    CREATE TABLE chain_links (
      link_id INTEGER PRIMARY KEY AUTOINCREMENT,
      topic_key TEXT NOT NULL,
      verse_id INTEGER NOT NULL,
      passage_display TEXT NOT NULL,
      stage_label TEXT NOT NULL,
      sermon_point TEXT NOT NULL,
      sort_order INTEGER NOT NULL DEFAULT 0
    );
  ''');
  db.execute('''
    CREATE TABLE sermons (
      sermon_id TEXT PRIMARY KEY,
      title TEXT NOT NULL,
      preacher TEXT NOT NULL DEFAULT '목회자',
      sermon_date TEXT NOT NULL,
      service_type TEXT NOT NULL DEFAULT '주일대예배',
      scripture_ref TEXT NOT NULL,
      target_duration_mins INTEGER DEFAULT 30,
      outline_json TEXT NOT NULL DEFAULT '[]',
      full_text_markdown TEXT,
      gdrive_file_id TEXT,
      sync_status TEXT DEFAULT 'LOCAL_ONLY',
      local_updated_at TEXT DEFAULT (datetime('now'))
    );
  ''');

  db.execute(
    "INSERT INTO bible_books VALUES (1, 'GEN', '창세기', '창', 'Genesis', 'OT', '율법서', 50, 1533);",
  );
  db.execute(
    "INSERT INTO bible_books VALUES (19, 'PSA', '시편', '시', 'Psalms', 'OT', '시가서', 150, 2461);",
  );
  db.execute(
    "INSERT INTO bible_verses (verse_id, book_id, chapter, verse, version_code, text) "
    "VALUES (1022002, 1, 22, 2, 'KRV', '여호와께서 가라사대 네 아들 네 사랑하는 독자 이삭을 데리고 모리아 땅으로 가서');",
  );
  db.execute(
    "INSERT INTO bible_verses (verse_id, book_id, chapter, verse, version_code, text) "
    "VALUES (19023001, 19, 23, 1, 'KRV', '여호와는 나의 목자시니 내가 부족함이 없으리로다');",
  );
  db.execute(
    "INSERT INTO cross_references (from_verse_id, to_verse_id, score, relationship_type, note) "
    "VALUES (1022002, 19023001, 0.95, 'PROPHECY_FULFILLMENT', NULL);",
  );
  db.execute(
    "INSERT INTO chain_topics VALUES ('shepherd', '목자 되신 주', '인도하심', '구약에서 신약까지 이어지는 목자 언약');",
  );
  db.execute(
    "INSERT INTO chain_links (topic_key, verse_id, passage_display, stage_label, sermon_point, sort_order) "
    "VALUES ('shepherd', 19023001, '시편 23:1', '시편 고백', '부족함이 없는 공급', 1);",
  );
  return db;
}

void main() {
  late Database db;
  late SqliteBibleRepository repo;

  setUp(() {
    db = _createTestDb();
    repo = SqliteBibleRepository(db);
  });

  tearDown(() async {
    await repo.close();
  });

  test('saveSermon persists all columns on insert and ON CONFLICT update', () async {
    final initial = Sermon(
      sermonId: 'sermon_001',
      title: '첫 번째 제목',
      preacher: '목회자',
      sermonDate: '2026-11-22',
      serviceType: '주일대예배',
      scriptureRef: '창세기 22:1-14',
      targetDurationMins: 30,
      outline: const [
        SermonOutlinePoint(section: '서론', title: '도입', content: '본문 배경'),
      ],
      fullTextMarkdown: '# 첫 원고',
      gdriveFileId: 'drive_file_123',
      syncStatus: 'SYNCED',
    );
    await repo.saveSermon(initial);

    final updated = initial.copyWith(
      title: '수정된 설교 제목',
      preacher: '담임 목회자',
      sermonDate: '2026-11-29',
      serviceType: '수요예배',
      scriptureRef: '시편 23:1-6',
      targetDurationMins: 40,
      fullTextMarkdown: '# 수정된 원고',
    );
    await repo.saveSermon(updated);

    final saved = await repo.listSermons();
    expect(saved, hasLength(1));
    final s = saved.first;
    expect(s.title, equals('수정된 설교 제목'));
    expect(s.preacher, equals('담임 목회자'));
    expect(s.sermonDate, equals('2026-11-29'));
    expect(s.serviceType, equals('수요예배'));
    expect(s.scriptureRef, equals('시편 23:1-6'));
    expect(s.targetDurationMins, equals(40));
    expect(s.fullTextMarkdown, equals('# 수정된 원고'));
    expect(s.gdriveFileId, equals('drive_file_123'));
    expect(s.syncStatus, equals('PENDING_UPLOAD'));
  });

  test('cross-references and chain references query cleanly with single-quoted literals', () async {
    final refs = await repo.getCrossReferencesForVerse(1022002);
    expect(refs, hasLength(1));
    expect(refs.first.refString, equals('시편 23:1'));
    expect(refs.first.relationshipLabel, equals('약속과 성취'));

    final chains = await repo.listChainReferences();
    expect(chains, hasLength(1));
    expect(chains.first.chains.first.text, contains('여호와는 나의 목자시니'));
  });

  test('searchVerses handles standard and space-stripped Korean queries', () async {
    final hits1 = await repo.searchVerses(query: '여호와는 나의 목자');
    expect(hits1, isNotEmpty);
    expect(hits1.first.verseId, equals(19023001));

    final hits2 = await repo.searchVerses(query: '여호와는나의목자');
    expect(hits2, isNotEmpty);
    expect(hits2.first.verseId, equals(19023001));
  });

  test('Sermon default preacher contains zero personal PII', () {
    const sermon = Sermon(
      sermonId: 's1',
      title: '테스트',
      sermonDate: '2026-11-23',
      scriptureRef: '시편 23:1',
      outline: [],
    );
    expect(sermon.preacher, equals('목회자'));
    expect(sermon.preacher, isNot(contains('\uBC15\uC6B0\uD638')));
  });
}
