/// Google Cloud Platform (GCP) and Cloud Storage configuration
class GcpConfig {
  /// GCP Cloud Storage bucket name for master commentary distribution
  static const String gcsBucketName = "pastoral-bible-commentaries";

  /// Base public URL for downloading release assets
  static const String gcsBaseUrl = "https://storage.googleapis.com/$gcsBucketName/v1";

  /// Version manifest URL for auto-update check
  static const String manifestUrl = "$gcsBaseUrl/release_manifest.json";

  /// Master SQLite database compressed file URL
  static const String masterDbUrl = "$gcsBaseUrl/commentaries_master_v1.0.db.gz";

  /// Local filename for the downloaded database
  static const String localDbFileName = "bible_pastoral_core.db";
  static const String localCompressedFileName = "commentaries_master_v1.0.db.gz";

  /// Google Drive API scopes (only app-created files for privacy)
  static const String gdriveFolderName = "성경주혜주석_설교노트";
  static const List<String> gdriveScopes = [
    "https://www.googleapis.com/auth/drive.file",
  ];
}
