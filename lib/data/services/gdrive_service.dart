import 'dart:convert';
import 'package:extension_google_sign_in_as_googleapis_auth/extension_google_sign_in_as_googleapis_auth.dart';
import 'package:google_sign_in/google_sign_in.dart';
import 'package:googleapis/drive/v3.dart' as drive;
import '../../core/config/app_config.dart';
import '../../domain/models/bible_models.dart';

/// Google Drive Sermon Sync Service (Fixed UTF-8 byte length bug + bidirectional list/upload).
class GDriveSyncService {
  final GoogleSignIn _googleSignIn = GoogleSignIn(scopes: AppConfig.gdriveScopes);

  GoogleSignInAccount? _currentUser;
  drive.DriveApi? _driveApi;
  String? _appFolderId;

  bool get isSignedIn => _currentUser != null;
  String? get userEmail => _currentUser?.email;

  Future<bool> signIn() async {
    try {
      _currentUser = await _googleSignIn.signIn();
      if (_currentUser == null) return false;
      final authClient = await _googleSignIn.authenticatedClient();
      if (authClient == null) return false;
      _driveApi = drive.DriveApi(authClient);
      await _ensureAppFolderExists();
      return true;
    } catch (_) {
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

  Future<String?> uploadSermon(Sermon sermon) async {
    if (_driveApi == null) return null;
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

    // CRITICAL FIX: Use UTF-8 byte length (not UTF-16 string character length!)
    final encodedBytes = utf8.encode(sermonJson);
    final uploadMedia = drive.Media(Stream.value(encodedBytes), encodedBytes.length);

    final escapedName = fileName.replaceAll("'", "\\'");
    final existing = await _driveApi!.files.list(
      q: "'$folderId' in parents and name = '$escapedName' and trashed = false",
    );

    if (existing.files != null && existing.files!.isNotEmpty) {
      final updated = await _driveApi!.files.update(
        drive.File(),
        existing.files!.first.id!,
        uploadMedia: uploadMedia,
      );
      return updated.id;
    }

    final created = await _driveApi!.files.create(
      drive.File()
        ..name = fileName
        ..parents = [folderId]
        ..mimeType = 'application/json',
      uploadMedia: uploadMedia,
    );
    return created.id;
  }
}
