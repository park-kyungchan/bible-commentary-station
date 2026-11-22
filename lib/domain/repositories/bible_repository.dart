import '../models/bible_models.dart';

/// Clean Architecture Repository Contract for Offline-First Scripture & Exegesis Access.
abstract class BibleRepository {
  Future<List<BibleBook>> listBooks();
  Future<List<BibleVerse>> getChapterVerses({
    required String versionCode,
    required int bookId,
    required int chapter,
  });
  Future<List<BibleVerse>> searchVerses({
    required String query,
    String versionCode = 'KRV',
    int limit = 25,
  });
  Future<List<CommentaryItem>> getCommentariesForVerse(int verseId);
  Future<List<CrossRefItem>> getCrossReferencesForVerse(int verseId, {String versionCode = 'KRV'});
  Future<List<ChainReference>> listChainReferences({String versionCode = 'KRV'});
  Future<void> saveSermon(Sermon sermon);
  Future<List<Sermon>> listSermons();
}
