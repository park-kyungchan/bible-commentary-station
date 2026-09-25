import 'dart:convert';
import 'package:google_sign_in/google_sign_in.dart';
import 'package:googleapis/drive/v3.dart' as drive;
import 'package:extension_google_sign_in_as_googleapis_auth/extension_google_sign_in_as_googleapis_auth.dart';
import '../../core/config/gcp_config.dart';
import '../../domain/models/bible_models.dart';

class GDriveSyncService {
  final GoogleSignIn _googleSignIn = GoogleSignIn(
    scopes: GcpConfig.gdriveScopes,
  );

  GoogleSignInAccount? _currentUser;
  drive.DriveApi? _driveApi;
  String? _appFolderId;

  bool get isSignedIn => _currentUser != null;
  String? get userEmail => _currentUser?.email;

  /// Sign in with Pastor's Google account
  Future<bool> signIn() async {
    try {
      _currentUser = await _googleSignIn.signIn();
      if (_currentUser == null) return false;

      final authClient = await _googleSignIn.authenticatedClient();
      if (authClient == null) return false;

      _driveApi = drive.DriveApi(authClient);
      await _ensureAppFolderExists();
      return true;
    } catch (e) {
      print('Google Drive Sign-In Error: $e');
      return false;
    }
  }

  /// Ensure `내 드라이브/성경주혜주석_설교노트/` exists
  Future<String?> _ensureAppFolderExists() async {
    if (_driveApi == null) return null;
    if (_appFolderId != null) return _appFolderId;

    try {
      final fileList = await _driveApi!.files.list(
        q: "mimeType = 'application/vnd.google-apps.folder' and name = '${GcpConfig.gdriveFolderName}' and trashed = false",
        spaces: 'drive',
      );

      if (fileList.files != null && fileList.files!.isNotEmpty) {
        _appFolderId = fileList.files!.first.id;
      } else {
        // Create folder
        final folderMetadata = drive.File()
          ..name = GcpConfig.gdriveFolderName
          ..mimeType = 'application/vnd.google-apps.folder';

        final folder = await _driveApi!.files.create(folderMetadata);
        _appFolderId = folder.id;
      }
      return _appFolderId;
    } catch (e) {
      print('Failed to ensure Drive folder: $e');
      return null;
    }
  }

  /// Sync Sermon to Google Drive
  Future<String?> uploadSermon(Sermon sermon) async {
    if (_driveApi == null) return null;
    final folderId = await _ensureAppFolderExists();
    if (folderId == null) return null;

    try {
      final fileName = "${sermon.sermonDate}_${sermon.title.replaceAll(' ', '_')}.json";
      final sermonData = jsonEncode({
        "sermonId": sermon.sermonId,
        "title": sermon.title,
        "preacher": sermon.preacher,
        "sermonDate": sermon.sermonDate,
        "serviceType": sermon.serviceType,
        "scriptureRef": sermon.scriptureRef,
        "targetDurationMins": sermon.targetDurationMins,
        "outline": sermon.outline.map((o) => {
          "section": o.section,
          "title": o.title,
          "content": o.content,
          "citations": o.citations,
        }).toList(),
        "fullTextMarkdown": sermon.fullTextMarkdown,
      });

      final mediaStream = Stream.value(utf8.encode(sermonData));
      final uploadMedia = drive.Media(mediaStream, sermonData.length);

      // Check if file already exists
      final existingFiles = await _driveApi!.files.list(
        q: "'$folderId' in parents and name = '$fileName' and trashed = false",
      );

      if (existingFiles.files != null && existingFiles.files!.isNotEmpty) {
        final existingId = existingFiles.files!.first.id!;
        final updated = await _driveApi!.files.update(
          drive.File(),
          existingId,
          uploadMedia: uploadMedia,
        );
        return updated.id;
      } else {
        final newFile = drive.File()
          ..name = fileName
          ..parents = [folderId]
          ..mimeType = 'application/json';

        final created = await _driveApi!.files.create(
          newFile,
          uploadMedia: uploadMedia,
        );
        return created.id;
      }
    } catch (e) {
      print('Sermon upload failed: $e');
      return null;
    }
  }
}
