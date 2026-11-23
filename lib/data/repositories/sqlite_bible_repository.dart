import 'dart:convert';
import 'package:sqlite3/sqlite3.dart';
import '../../domain/models/bible_models.dart';
import '../../domain/repositories/bible_repository.dart';

/// Concrete SQLite3 implementation of [BibleRepository] using Dual Hybrid FTS5
/// (unicode61 prefix + trigram 3+ char substring) with strict SQLite single-quoted literals.
class SqliteBibleRepository implements BibleRepository {
  final Database _db;
  bool _isClosed = false;

  SqliteBibleRepository(this._db);

  @override
  Future<List<BibleBook>> listBooks() async {
    final rows = _db.select(
      'SELECT book_id, osis_code, name_kr, name_kr_abbr, name_en, testament, total_chapters '
      'FROM bible_books ORDER BY book_id ASC;',
    );
    return rows
        .map((r) => BibleBook(
              bookId: r['book_id'] as int,
              osisCode: r['osis_code'] as String,
              nameKr: r['name_kr'] as String,
              nameKrAbbr: r['name_kr_abbr'] as String,
              nameEn: r['name_en'] as String,
              testament: r['testament'] as String,
              totalChapters: r['total_chapters'] as int,
            ))
        .toList();
  }

  @override
  Future<List<BibleVerse>> getChapterVerses({
    required String versionCode,
    required int bookId,
    required int chapter,
  }) async {
    final rows = _db.select(
      'SELECT verse_id, book_id, chapter, verse, version_code, text, text_with_strong '
      'FROM bible_verses WHERE version_code = ? AND book_id = ? AND chapter = ? ORDER BY verse ASC;',
      [versionCode, bookId, chapter],
    );
    return rows.map(_mapVerse).toList();
  }

  @override
  Future<List<BibleVerse>> searchVerses({
    required String query,
    String versionCode = 'KRV',
    int limit = 25,
  }) async {
    final cleaned = query
        .replaceAll(RegExp(r'["\x27*():^~+.,?!;/\\{}\[\]\-]+'), ' ')
        .trim();
    if (cleaned.isEmpty) return [];
    final tokens = cleaned.split(RegExp(r'\s+'));

    final useTrigram = tokens.every((t) => t.length >= 3);
    if (useTrigram) {
      final trigramExpr = tokens.map((t) => '"$t"').join(' ');
      final trigramRows = _db.select(
        'SELECT v.verse_id, v.book_id, v.chapter, v.verse, v.version_code, v.text, v.text_with_strong '
        'FROM fts_bible_verses_trigram f JOIN bible_verses v ON f.rowid = v.id '
        'WHERE fts_bible_verses_trigram MATCH ? AND v.version_code = ? LIMIT ?;',
        [trigramExpr, versionCode, limit],
      );
      if (trigramRows.isNotEmpty) {
        return trigramRows.map(_mapVerse).toList();
      }
    }

    final unicodeExpr = tokens.map((t) => '"$t"*').join(' ');
    final unicodeRows = _db.select(
      'SELECT v.verse_id, v.book_id, v.chapter, v.verse, v.version_code, v.text, v.text_with_strong '
      'FROM fts_bible_verses_unicode f JOIN bible_verses v ON f.rowid = v.id '
      'WHERE fts_bible_verses_unicode MATCH ? AND v.version_code = ? LIMIT ?;',
      [unicodeExpr, versionCode, limit],
    );
    if (unicodeRows.isNotEmpty) {
      return unicodeRows.map(_mapVerse).toList();
    }

    // Forgiving space-stripped fallback for Korean queries without spaces.
    final compact = tokens.join('');
    final fallbackRows = _db.select(
      "SELECT verse_id, book_id, chapter, verse, version_code, text, text_with_strong "
      "FROM bible_verses "
      "WHERE version_code = ? AND REPLACE(text, ' ', '') LIKE ? "
      "ORDER BY verse_id ASC LIMIT ?;",
      [versionCode, '%$compact%', limit],
    );
    return fallbackRows.map(_mapVerse).toList();
  }

  @override
  Future<List<CommentaryItem>> getCommentariesForVerse(int verseId) async {
    final rows = _db.select(
      'SELECT c.commentary_id, c.source_code, s.name_kr AS source_name, c.passage_display, '
      'c.title, c.content_markdown, c.theological_tags, c.practical_points '
      'FROM commentaries c JOIN commentary_sources s ON c.source_code = s.source_code '
      'WHERE ? BETWEEN c.verse_start_id AND c.verse_end_id ORDER BY s.sort_order ASC;',
      [verseId],
    );
    return rows
        .map((r) => CommentaryItem(
              commentaryId: r['commentary_id'] as int,
              sourceCode: r['source_code'] as String,
              sourceName: r['source_name'] as String,
              passageDisplay: r['passage_display'] as String,
              title: r['title'] as String?,
              contentMarkdown: r['content_markdown'] as String,
              theologicalTags: r['theological_tags'] as String?,
              practicalPoints: r['practical_points'] as String?,
            ))
        .toList();
  }

  @override
  Future<List<CrossRefItem>> getCrossReferencesForVerse(
    int verseId, {
    String versionCode = 'KRV',
  }) async {
    final rows = _db.select(
      "SELECT cr.ref_id, cr.from_verse_id, cr.to_verse_id, cr.score, cr.relationship_type, "
      "b.name_kr AS to_book_name, (cr.to_verse_id % 1000000) / 1000 AS to_chapter, "
      "cr.to_verse_id % 1000 AS to_verse, COALESCE(v.text, cr.note, '') AS full_text "
      "FROM cross_references cr "
      "JOIN bible_books b ON (cr.to_verse_id / 1000000) = b.book_id "
      "LEFT JOIN bible_verses v ON cr.to_verse_id = v.verse_id AND v.version_code = ? "
      "WHERE cr.from_verse_id = ? ORDER BY cr.score DESC;",
      [versionCode, verseId],
    );
    return rows
        .map((r) => CrossRefItem(
              refId: r['ref_id'] as int,
              fromVerseId: r['from_verse_id'] as int,
              toVerseId: r['to_verse_id'] as int,
              toBookName: r['to_book_name'] as String,
              toChapter: r['to_chapter'] as int,
              toVerse: r['to_verse'] as int,
              fullText: r['full_text'] as String,
              relationshipType: r['relationship_type'] as String,
              score: (r['score'] as num).toDouble(),
            ))
        .toList();
  }

  @override
  Future<List<ChainReference>> listChainReferences({String versionCode = 'KRV'}) async {
    final topics = _db.select('SELECT topic_key, title, meaning, summary FROM chain_topics;');
    return topics.map((t) {
      final links = _db.select(
        "SELECT cl.passage_display, cl.stage_label, cl.sermon_point, b.name_kr, COALESCE(v.text, '') AS verse_text "
        "FROM chain_links cl "
        "JOIN bible_books b ON (cl.verse_id / 1000000) = b.book_id "
        "LEFT JOIN bible_verses v ON cl.verse_id = v.verse_id AND v.version_code = ? "
        "WHERE cl.topic_key = ? ORDER BY cl.sort_order ASC;",
        [versionCode, t['topic_key']],
      );
      return ChainReference(
        topic: t['topic_key'] as String,
        title: t['title'] as String,
        meaning: t['meaning'] as String,
        summary: t['summary'] as String,
        chains: links
            .map((l) => ChainLink(
                  ref: l['passage_display'] as String,
                  book: l['name_kr'] as String,
                  text: l['verse_text'] as String,
                  type: l['stage_label'] as String,
                  point: l['sermon_point'] as String,
                ))
            .toList(),
      );
    }).toList();
  }

  @override
  Future<void> saveSermon(Sermon sermon) async {
    final outlineJson = jsonEncode(
      sermon.outline
          .map((o) => {
                'section': o.section,
                'title': o.title,
                'content': o.content,
                'citations': o.citations,
              })
          .toList(),
    );
    _db.execute(
      "INSERT INTO sermons (sermon_id, title, preacher, sermon_date, service_type, scripture_ref, "
      "target_duration_mins, outline_json, full_text_markdown, gdrive_file_id, sync_status, local_updated_at) "
      "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now')) "
      "ON CONFLICT(sermon_id) DO UPDATE SET "
      "title = excluded.title, "
      "preacher = excluded.preacher, "
      "sermon_date = excluded.sermon_date, "
      "service_type = excluded.service_type, "
      "scripture_ref = excluded.scripture_ref, "
      "target_duration_mins = excluded.target_duration_mins, "
      "outline_json = excluded.outline_json, "
      "full_text_markdown = excluded.full_text_markdown, "
      "gdrive_file_id = COALESCE(excluded.gdrive_file_id, sermons.gdrive_file_id), "
      "sync_status = 'PENDING_UPLOAD', "
      "local_updated_at = datetime('now');",
      [
        sermon.sermonId,
        sermon.title,
        sermon.preacher,
        sermon.sermonDate,
        sermon.serviceType,
        sermon.scriptureRef,
        sermon.targetDurationMins,
        outlineJson,
        sermon.fullTextMarkdown,
        sermon.gdriveFileId,
        sermon.syncStatus ?? 'LOCAL_ONLY',
      ],
    );
  }

  @override
  Future<List<Sermon>> listSermons() async {
    final rows = _db.select('SELECT * FROM sermons ORDER BY sermon_date DESC, local_updated_at DESC;');
    return rows.map((r) {
      final rawOutline = jsonDecode((r['outline_json'] as String?) ?? '[]') as List<dynamic>;
      return Sermon(
        sermonId: r['sermon_id'] as String,
        title: r['title'] as String,
        preacher: r['preacher'] as String,
        sermonDate: r['sermon_date'] as String,
        serviceType: r['service_type'] as String,
        scriptureRef: r['scripture_ref'] as String,
        targetDurationMins: (r['target_duration_mins'] as int?) ?? 30,
        outline: rawOutline
            .map((e) => SermonOutlinePoint(
                  section: e['section'] as String? ?? '',
                  title: e['title'] as String? ?? '',
                  content: e['content'] as String? ?? '',
                  citations: List<String>.from((e['citations'] as List?) ?? const []),
                ))
            .toList(),
        fullTextMarkdown: r['full_text_markdown'] as String?,
        gdriveFileId: r['gdrive_file_id'] as String?,
        syncStatus: r['sync_status'] as String?,
      );
    }).toList();
  }

  @override
  Future<void> close() async {
    if (!_isClosed) {
      _isClosed = true;
      _db.dispose();
    }
  }

  BibleVerse _mapVerse(Row r) => BibleVerse(
        verseId: r['verse_id'] as int,
        bookId: r['book_id'] as int,
        chapter: r['chapter'] as int,
        verse: r['verse'] as int,
        versionCode: r['version_code'] as String,
        text: r['text'] as String,
        textWithStrong: r['text_with_strong'] as String?,
      );
}
