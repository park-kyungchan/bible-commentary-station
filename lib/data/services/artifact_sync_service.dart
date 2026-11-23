import 'dart:convert';
import 'dart:io';
import 'package:crypto/crypto.dart';
import 'package:http/http.dart' as http;
import 'package:path/path.dart' as p;
import 'package:path_provider/path_provider.dart';
import '../../core/config/app_config.dart';

class SyncProgress {
  final bool isDownloading;
  final double progress;
  final String message;
  final bool isCompleted;
  final String? error;

  const SyncProgress({
    this.isDownloading = false,
    this.progress = 0.0,
    this.message = '',
    this.isCompleted = false,
    this.error,
  });
}

/// Memory-safe, fail-closed atomic SQLite bundle updater.
/// - Requires a valid 64-hex `compressed_sha256` in the release manifest (fail-closed)
/// - Streams download directly to disk while computing chunked SHA-256
/// - Decompresses via streaming `dart:io` `gzip.decoder` and verifies SQLite header
/// - Invokes `beforeSwap` / `afterSwap` so open SQLite handles close cleanly around rename
class ArtifactSyncService {
  static const List<int> _sqliteMagicHeader = [
    0x53, 0x51, 0x4c, 0x69, 0x74, 0x65, 0x20, 0x66, // "SQLite f"
    0x6f, 0x72, 0x6d, 0x61, 0x74, 0x20, 0x33, 0x00, // "ormat 3\0"
  ];
  static final RegExp _sha256HexPattern = RegExp(r'^[a-fA-F0-9]{64}$');

  final http.Client Function() _clientFactory;
  final Future<Directory> Function() _directoryProvider;
  final String _manifestUrl;
  final String _bundleUrl;

  ArtifactSyncService({
    http.Client Function()? clientFactory,
    Future<Directory> Function()? directoryProvider,
    String? manifestUrl,
    String? bundleUrl,
  })  : _clientFactory = clientFactory ?? http.Client.new,
        _directoryProvider = directoryProvider ?? getApplicationDocumentsDirectory,
        _manifestUrl = manifestUrl ?? AppConfig.releaseManifestUrl,
        _bundleUrl = bundleUrl ?? AppConfig.masterDbBundleUrl;

  Future<File> getLocalDbFile() async {
    final dir = await _directoryProvider();
    return File(p.join(dir.path, AppConfig.localDbFileName));
  }

  /// Returns true only when a non-empty file with a valid SQLite 3 header exists on disk.
  Future<bool> isLocalDatabaseReady() async {
    final dbFile = await getLocalDbFile();
    if (!await dbFile.exists()) return false;
    final length = await dbFile.length();
    if (length < 4096) return false;
    return _hasValidSqliteHeader(dbFile);
  }

  static Future<bool> _hasValidSqliteHeader(File file) async {
    final raf = await file.open();
    try {
      final header = await raf.read(_sqliteMagicHeader.length);
      if (header.length < _sqliteMagicHeader.length) return false;
      for (var i = 0; i < _sqliteMagicHeader.length; i++) {
        if (header[i] != _sqliteMagicHeader[i]) return false;
      }
      return true;
    } finally {
      await raf.close();
    }
  }

  Stream<SyncProgress> downloadAndInstallMasterDb({
    Future<void> Function()? beforeSwap,
    Future<void> Function()? afterSwap,
  }) async* {
    final client = _clientFactory();
    File? tmpGzFile;
    File? tmpDbFile;

    try {
      yield const SyncProgress(
        isDownloading: true,
        progress: 0.05,
        message: '성경 자료 정보를 확인하는 중...',
      );

      final manifestResp = await client
          .get(Uri.parse(_manifestUrl))
          .timeout(const Duration(seconds: 20));
      if (manifestResp.statusCode != 200) {
        throw HttpException('자료 안내 파일을 불러오지 못했습니다 (${manifestResp.statusCode}).');
      }

      final decoded = jsonDecode(utf8.decode(manifestResp.bodyBytes));
      if (decoded is! Map<String, dynamic>) {
        throw const FormatException('자료 안내 파일 형식이 올바르지 않습니다.');
      }

      // Mandatory fail-closed SHA-256 verification before downloading or installing.
      final expectedSha256 = decoded['compressed_sha256']?.toString().trim();
      if (expectedSha256 == null || !_sha256HexPattern.hasMatch(expectedSha256)) {
        throw const FormatException(
          '자료 무결성 검증 값(SHA-256)이 누락되었거나 올바르지 않아 설치를 중단했습니다.',
        );
      }
      final expectedSize = (decoded['compressed_size_bytes'] as num?)?.toInt() ?? 0;

      final dbFile = await getLocalDbFile();
      await dbFile.parent.create(recursive: true);
      tmpGzFile = File('${dbFile.path}.download.gz.tmp');
      tmpDbFile = File('${dbFile.path}.extract.tmp');

      yield const SyncProgress(
        isDownloading: true,
        progress: 0.15,
        message: '성경과 주석 자료를 내려받는 중...',
      );

      final request = http.Request('GET', Uri.parse(_bundleUrl));
      final response = await client.send(request).timeout(const Duration(seconds: 60));
      if (response.statusCode != 200) {
        throw HttpException('성경 자료를 내려받지 못했습니다 (${response.statusCode}).');
      }

      final totalBytes = response.contentLength ?? expectedSize;
      var downloaded = 0;

      final sink = tmpGzFile.openWrite();
      final digestSink = AccumulatorSink<Digest>();
      final shaInput = sha256.startChunkedConversion(digestSink);

      try {
        await for (final chunk in response.stream) {
          sink.add(chunk);
          shaInput.add(chunk);
          downloaded += chunk.length;
          if (totalBytes > 0) {
            final pct = 0.15 + (0.65 * (downloaded / totalBytes)).clamp(0.0, 0.65);
            yield SyncProgress(
              isDownloading: true,
              progress: pct,
              message:
                  '내려받는 중 (${(downloaded / 1048576).toStringAsFixed(1)} MB / ${(totalBytes / 1048576).toStringAsFixed(1)} MB)...',
            );
          }
        }
      } finally {
        await sink.flush();
        await sink.close();
        shaInput.close();
      }

      yield const SyncProgress(
        isDownloading: true,
        progress: 0.85,
        message: '자료 안전성을 확인하는 중...',
      );
      if (digestSink.events.isEmpty) {
        throw const FormatException('자료 무결성 검증을 완료하지 못했습니다.');
      }
      final actualSha = digestSink.events.single.toString();
      if (actualSha.toLowerCase() != expectedSha256.toLowerCase()) {
        throw const FormatException(
          '내려받은 자료의 안전성 검증(SHA-256)이 일치하지 않아 설치를 중단했습니다.',
        );
      }

      yield const SyncProgress(
        isDownloading: true,
        progress: 0.92,
        message: '성경 자료를 설치하는 중...',
      );

      final extractSink = tmpDbFile.openWrite();
      try {
        await extractSink.addStream(tmpGzFile.openRead().transform(gzip.decoder));
        await extractSink.flush();
      } finally {
        await extractSink.close();
      }

      if (!await _hasValidSqliteHeader(tmpDbFile)) {
        throw const FormatException('압축 해제된 파일이 올바른 성경 데이터베이스 형식이 아닙니다.');
      }

      // Close open SQLite handle cleanly before atomic swap, then reopen afterward.
      if (beforeSwap != null) {
        await beforeSwap();
      }
      await _atomicSwap(tmpDbFile, dbFile);
      if (afterSwap != null) {
        await afterSwap();
      }

      yield const SyncProgress(
        isDownloading: false,
        progress: 1.0,
        message: '오프라인 성경 자료 준비가 완료되었습니다.',
        isCompleted: true,
      );
    } catch (e) {
      yield SyncProgress(
        isDownloading: false,
        progress: 0.0,
        message: '성경 자료를 준비하지 못했습니다.',
        error: e.toString(),
      );
    } finally {
      client.close();
      if (tmpGzFile != null && await tmpGzFile.exists()) {
        try {
          await tmpGzFile.delete();
        } catch (_) {}
      }
      if (tmpDbFile != null && await tmpDbFile.exists()) {
        try {
          await tmpDbFile.delete();
        } catch (_) {}
      }
    }
  }

  Future<void> _atomicSwap(File source, File target) async {
    if (Platform.isWindows && await target.exists()) {
      final backup = File('${target.path}.bak');
      if (await backup.exists()) {
        await backup.delete();
      }
      await target.rename(backup.path);
      try {
        await source.rename(target.path);
      } catch (e) {
        await backup.rename(target.path);
        rethrow;
      }
      try {
        await backup.delete();
      } catch (_) {}
      return;
    }
    await source.rename(target.path);
  }
}

class AccumulatorSink<T> implements Sink<T> {
  final List<T> events = [];

  @override
  void add(T event) => events.add(event);

  @override
  void close() {}
}
