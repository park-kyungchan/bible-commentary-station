/// Zero-Cost ($0.00) Configurable Distribution & Sync Settings.
/// Override URLs at build time via `--dart-define=RELEASE_MANIFEST_URL=...`.
class AppConfig {
  static const String releaseManifestUrl = String.fromEnvironment(
    'RELEASE_MANIFEST_URL',
    defaultValue:
        'https://github.com/park-kyungchan/bible-commentary-station/releases/latest/download/release_manifest.json',
  );

  static const String masterDbBundleUrl = String.fromEnvironment(
    'MASTER_DB_BUNDLE_URL',
    defaultValue:
        'https://github.com/park-kyungchan/bible-commentary-station/releases/latest/download/bible_pastoral_core.db.gz',
  );

  static const String localDbFileName = 'bible_pastoral_core.db';

  /// Google Drive app-scoped folder (uses `drive.file` least-privilege scope).
  static const String gdriveFolderName = '성경주혜주석_설교노트';
  static const List<String> gdriveScopes = [
    'https://www.googleapis.com/auth/drive.file',
  ];
}
