import 'dart:convert';
import 'package:extension_google_sign_in_as_googleapis_auth/extension_google_sign_in_as_googleapis_auth.dart';
import 'package:google_sign_in/google_sign_in.dart';
import 'package:googleapis/drive/v3.dart' as drive;
import '../../core/config/app_config.dart';
import '../../domain/models/bible_models.dart';

/// Google Drive Sermon Sync Service with UTF-8 byte-length uploads,
/// stable `gdrive_file_id` in-place updates (prevents duplicates on rename),
/// and bidirectional list/download support.
class GDriveSyncService {
  final GoogleSignIn _googleSignIn;

  GoogleSignInAccount? _currentUser;
  drive.DriveApi? _driveApi;
  String? _appFolderId;
  String? _lastError;

  GDriveSyncService({
    GoogleSignIn? googleSignIn,
    drive.DriveApi? driveApi,
    String? appFolderId,
  })  : _googleSignIn = googleSignIn ?? GoogleSignIn(scopes: AppConfig.gdriveScopes),
        _driveApi = driveApi,
        _appFolderId = appFolderId;

  bool get isSignedIn => _currentUser != null || _driveApi != null;
  String? get userEmail => _currentUser?.email;
  String? get lastError => _lastError;

  Future<bool> signIn() async {
    _lastError = null;
    try {
      _currentUser = await _googleSignIn.signIn();
      if (_currentUser == null) {
        _lastError = '로그인이 취소되었습니다.';
        return false;
      }
      final authClient = await _googleSignIn.authenticatedClient();
      if (authClient == null) {
        _lastError = 'Google Drive 접근 권한을 받지 못했습니다.';
        return false;
      }
      _driveApi = drive.DriveApi(authClient);
      await _ensureAppFolderExists();
      return true;
    } catch (e) {
      _lastError = '로그인 중 오류가 발생했습니다: $e';
      return false;
    }
  }

  Future<String?> _ensureAppFolderExists() async {
    if (_driveApi == null) return null;
    if (_appFolderId != null) return _appFolderId;

    final escapedFolder = AppConfig.gdriveFolderName.replaceAll("'", "\\'");
    final fileList = await _driveApi!.files.list(
      q: "mimeType = 'application/vnd.google-apps.folder' and name = '$escapedFolder' and trashed = false",
      spaces: 'drive',
    );
    if (fileList.files != null && fileList.files!.isNotEmpty) {
      _appFolderId = fileList.files!.first.id;
    } else {
      final folder = await _driveApi!.files.create(
        drive.File()
          ..name = AppConfig.gdriveFolderName
          ..mimeType = 'application/vnd.google-apps.folder',
      );
      _appFolderId = folder.id;
    }
    return _appFolderId;
  }

  /// Uploads a sermon JSON file to Google Drive.
  /// When [Sermon.gdriveFileId] is set, updates that exact Drive file in place
  /// (updating its filename if renamed) instead of creating a duplicate.
  Future<String?> uploadSermon(Sermon sermon) async {
    _lastError = null;
    if (_driveApi == null) {
      _lastError = '먼저 Google 계정에 로그인해 주세요.';
      return null;
    }
    final folderId = await _ensureAppFolderExists();
    if (folderId == null) return null;

    final safeTitle = sermon.title.replaceAll(RegExp(r'[^\w가-힣\-]+'), '_');
    final fileName = '${sermon.sermonDate}_$safeTitle.json';
    final sermonJson = jsonEncode({
      'sermonId': sermon.sermonId,
      'title': sermon.title,
      'preacher': sermon.preacher,
      'sermonDate': sermon.sermonDate,
      'serviceType': sermon.serviceType,
      'scriptureRef': sermon.scriptureRef,
      'targetDurationMins': sermon.targetDurationMins,
      'outline': sermon.outline
          .map((o) => {
                'section': o.section,
                'title': o.title,
                'content': o.content,
                'citations': o.citations,
              })
          .toList(),
      'fullTextMarkdown': sermon.fullTextMarkdown,
    });

    // Use UTF-8 byte length (not UTF-16 string character length).
    final encodedBytes = utf8.encode(sermonJson);

    // 1. Prefer updating existing file by stable gdrive_file_id.
    final existingFileId = sermon.gdriveFileId;
    if (existingFileId != null && existingFileId.isNotEmpty) {
      try {
        final updated = await _driveApi!.files.update(
          drive.File()..name = fileName,
          existingFileId,
          uploadMedia: drive.Media(
            Stream.value(encodedBytes),
            encodedBytes.length,
            contentType: 'application/json',
          ),
        );
        return updated.id ?? existingFileId;
      } catch (_) {
        // Remote file may have been removed; fall through to lookup/create.
      }
    }

    // 2. Fall back to matching existing file by filename inside app folder.
    final escapedName = fileName.replaceAll("'", "\\'");
    final existing = await _driveApi!.files.list(
      q: "'$folderId' in parents and name = '$escapedName' and trashed = false",
    );

    if (existing.files != null && existing.files!.isNotEmpty) {
      final matchedId = existing.files!.first.id;
      if (matchedId != null && matchedId.isNotEmpty) {
        final updated = await _driveApi!.files.update(
          drive.File()..name = fileName,
          matchedId,
          uploadMedia: drive.Media(
            Stream.value(encodedBytes),
            encodedBytes.length,
            contentType: 'application/json',
          ),
        );
        return updated.id ?? matchedId;
      }
    }

    // 3. Create new sermon file inside app folder.
    final created = await _driveApi!.files.create(
      drive.File()
        ..name = fileName
        ..parents = [folderId]
        ..mimeType = 'application/json',
      uploadMedia: drive.Media(
        Stream.value(encodedBytes),
        encodedBytes.length,
        contentType: 'application/json',
      ),
    );
    return created.id;
  }

  /// Lists remote sermon backup files stored in the app-scoped Google Drive folder.
  Future<List<drive.File>> listRemoteSermonFiles() async {
    if (_driveApi == null) return const [];
    final folderId = await _ensureAppFolderExists();
    if (folderId == null) return const [];
    final result = await _driveApi!.files.list(
      q: "'$folderId' in parents and mimeType = 'application/json' and trashed = false",
      spaces: 'drive',
    );
    return result.files ?? const [];
  }

  /// Downloads and parses a sermon JSON backup by its Google Drive file ID.
  Future<Sermon?> downloadSermon(String fileId) async {
    if (_driveApi == null) return null;
    final media = await _driveApi!.files.get(
      fileId,
      downloadOptions: drive.DownloadOptions.fullMedia,
    );
    if (media is! drive.Media) return null;

    final bytes = <int>[];
    await for (final chunk in media.stream) {
      bytes.addAll(chunk);
    }
    final decoded = jsonDecode(utf8.decode(bytes));
    if (decoded is! Map<String, dynamic>) return null;

    final rawOutline = (decoded['outline'] as List<dynamic>?) ?? const [];
    return Sermon(
      sermonId: decoded['sermonId']?.toString() ?? fileId,
      title: decoded['title']?.toString() ?? '제목 없는 설교',
      preacher: decoded['preacher']?.toString() ?? '목회자',
      sermonDate: decoded['sermonDate']?.toString() ?? '',
      serviceType: decoded['serviceType']?.toString() ?? '주일대예배',
      scriptureRef: decoded['scriptureRef']?.toString() ?? '',
      targetDurationMins: (decoded['targetDurationMins'] as num?)?.toInt() ?? 30,
      outline: rawOutline
          .whereType<Map<String, dynamic>>()
          .map((e) => SermonOutlinePoint(
                section: e['section']?.toString() ?? '',
                title: e['title']?.toString() ?? '',
                content: e['content']?.toString() ?? '',
                citations: List<String>.from((e['citations'] as List?) ?? const []),
              ))
          .toList(),
      fullTextMarkdown: decoded['fullTextMarkdown']?.toString(),
      gdriveFileId: fileId,
      syncStatus: 'SYNCED',
    );
  }
}
