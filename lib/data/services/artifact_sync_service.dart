import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:archive/archive_io.dart';
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

/// Memory-safe, atomic SQLite bundle updater (Zero-Cost GitHub Releases / Static CDN).
/// - Streams download directly to disk (avoids mobile OOM on multi-MB bundles)
/// - Verifies SHA-256 checksum on disk before decompression
/// - Decompresses to a `.tmp` file and atomically swaps into place
class ArtifactSyncService {
  final http.Client Function() _clientFactory;

  ArtifactSyncService({http.Client Function()? clientFactory})
      : _clientFactory = clientFactory ?? http.Client.new;

  Future<File> getLocalDbFile() async {
    final dir = await getApplicationDocumentsDirectory();
    return File(p.join(dir.path, AppConfig.localDbFileName));
  }

  Future<bool> isLocalDatabaseReady() async {
    final dbFile = await getLocalDbFile();
    return await dbFile.exists() && (await dbFile.length()) > 64 * 1024;
  }

  Stream<SyncProgress> downloadAndInstallMasterDb() async* {
    final client = _clientFactory();
    File? tmpGzFile;
    File? tmpDbFile;

    try {
      yield const SyncProgress(
        isDownloading: true,
        progress: 0.05,
        message: '무과금 릴리스 매니페스트 확인 중...',
      );

      final manifestResp = await client
          .get(Uri.parse(AppConfig.releaseManifestUrl))
          .timeout(const Duration(seconds: 20));
      if (manifestResp.statusCode != 200) {
        throw HttpException('Manifest HTTP ${manifestResp.statusCode}');
      }
      final manifest = jsonDecode(utf8.decode(manifestResp.bodyBytes)) as Map<String, dynamic>;
      final expectedSha256 = manifest['compressed_sha256']?.toString();
      final expectedSize = (manifest['compressed_size_bytes'] as num?)?.toInt() ?? 0;

      final dbFile = await getLocalDbFile();
      tmpGzFile = File('${dbFile.path}.download.gz.tmp');
      tmpDbFile = File('${dbFile.path}.extract.tmp');

      yield const SyncProgress(
        isDownloading: true,
        progress: 0.15,
        message: '성경·주석 마스터 DB 스트리밍 다운로드 시작...',
      );

      final request = http.Request('GET', Uri.parse(AppConfig.masterDbBundleUrl));
      final response = await client.send(request).timeout(const Duration(seconds: 60));
      if (response.statusCode != 200) {
        throw HttpException('Bundle download HTTP ${response.statusCode}');
      }

      final totalBytes = response.contentLength ?? expectedSize;
      int downloaded = 0;

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
              message: '다운로드 중 (${(downloaded / 1048576).toStringAsFixed(1)} MB / ${(totalBytes / 1048576).toStringAsFixed(1)} MB)...',
            );
          }
        }
      } finally {
        await sink.flush();
        await sink.close();
        shaInput.close();
      }

      if (expectedSha256 != null && expectedSha256.isNotEmpty) {
        yield const SyncProgress(
          isDownloading: true,
          progress: 0.85,
          message: 'SHA-256 무결성 검증 중...',
        );
        final actualSha = digestSink.events.single.toString();
        if (actualSha.toLowerCase() != expectedSha256.toLowerCase()) {
          throw const FormatException('SHA-256 checksum mismatch; aborting install.');
        }
      }

      yield const SyncProgress(
        isDownloading: true,
        progress: 0.92,
        message: '압축 해제 및 원자적 DB 교체 중...',
      );

      final inputStream = InputFileStream(tmpGzFile.path);
      final outputStream = OutputFileStream(tmpDbFile.path);
      try {
        GZipDecoder().decodeStream(inputStream, outputStream);
      } finally {
        await inputStream.close();
        await outputStream.close();
      }

      // Atomic swap to prevent corrupting existing DB on crash
      await tmpDbFile.rename(dbFile.path);

      yield const SyncProgress(
        isDownloading: false,
        progress: 1.0,
        message: '로컬 SQLite FTS5 마스터 DB 설치 완료',
        isCompleted: true,
      );
    } catch (e) {
      yield SyncProgress(
        isDownloading: false,
        progress: 0.0,
        message: '동기화 실패',
        error: e.toString(),
      );
    } finally {
      client.close();
      if (tmpGzFile != null && await tmpGzFile.exists()) {
        await tmpGzFile.delete().catchError((_) => tmpGzFile!);
      }
      if (tmpDbFile != null && await tmpDbFile.exists()) {
        await tmpDbFile.delete().catchError((_) => tmpDbFile!);
      }
    }
  }
}

class AccumulatorSink<T> implements Sink<T> {
  final List<T> events = [];
  @override
  void add(T event) => events.add(event);
  @override
  void close() {}
}
