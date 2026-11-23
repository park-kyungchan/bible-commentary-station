import 'dart:convert';
import 'dart:io';
import 'package:bible_commentary_workstation/data/services/artifact_sync_service.dart';
import 'package:crypto/crypto.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

List<int> _makeMinimalValidSqliteBytes() {
  final bytes = List<int>.filled(4096, 0);
  const magic = 'SQLite format 3\x00';
  final magicBytes = utf8.encode(magic);
  for (var i = 0; i < magicBytes.length; i++) {
    bytes[i] = magicBytes[i];
  }
  return bytes;
}

void main() {
  late Directory tempDir;

  setUp(() async {
    tempDir = await Directory.systemTemp.createTemp('bcs_sync_test_');
  });

  tearDown(() async {
    if (await tempDir.exists()) {
      await tempDir.delete(recursive: true);
    }
  });

  test('fails closed when manifest omits compressed_sha256', () async {
    final service = ArtifactSyncService(
      directoryProvider: () async => tempDir,
      manifestUrl: 'https://example.test/release_manifest.json',
      bundleUrl: 'https://example.test/bible_pastoral_core.db.gz',
      clientFactory: () => MockClient((request) async {
        if (request.url.path.endsWith('release_manifest.json')) {
          return http.Response(
            jsonEncode({'version': '3.0.0', 'compressed_size_bytes': 128}),
            200,
          );
        }
        fail('Bundle must not be downloaded when manifest lacks compressed_sha256');
      }),
    );

    final events = await service.downloadAndInstallMasterDb().toList();
    expect(events.last.isCompleted, isFalse);
    expect(events.last.error, isNotNull);
    expect(events.last.error, contains('SHA-256'));
    expect(await service.isLocalDatabaseReady(), isFalse);
  });

  test('fails closed when manifest compressed_sha256 is not valid 64-hex', () async {
    final service = ArtifactSyncService(
      directoryProvider: () async => tempDir,
      manifestUrl: 'https://example.test/release_manifest.json',
      bundleUrl: 'https://example.test/bible_pastoral_core.db.gz',
      clientFactory: () => MockClient((request) async {
        return http.Response(
          jsonEncode({'compressed_sha256': 'not-a-valid-sha'}),
          200,
        );
      }),
    );

    final events = await service.downloadAndInstallMasterDb().toList();
    expect(events.last.isCompleted, isFalse);
    expect(events.last.error, isNotNull);
    expect(await service.isLocalDatabaseReady(), isFalse);
  });

  test('rejects tampered bundle with mismatched SHA-256 without overwriting DB', () async {
    final validGz = gzip.encode(_makeMinimalValidSqliteBytes());
    final wrongSha = 'a' * 64;

    final service = ArtifactSyncService(
      directoryProvider: () async => tempDir,
      manifestUrl: 'https://example.test/release_manifest.json',
      bundleUrl: 'https://example.test/bible_pastoral_core.db.gz',
      clientFactory: () => MockClient((request) async {
        if (request.url.path.endsWith('release_manifest.json')) {
          return http.Response(
            jsonEncode({
              'compressed_sha256': wrongSha,
              'compressed_size_bytes': validGz.length,
            }),
            200,
          );
        }
        return http.Response.bytes(validGz, 200);
      }),
    );

    final events = await service.downloadAndInstallMasterDb().toList();
    expect(events.last.isCompleted, isFalse);
    expect(events.last.error, isNotNull);
    expect(events.last.error, contains('SHA-256'));
    expect(await (await service.getLocalDbFile()).exists(), isFalse);
  });

  test('verifies valid SHA-256 and runs beforeSwap/afterSwap around atomic install', () async {
    final rawSqlite = _makeMinimalValidSqliteBytes();
    final gzBytes = gzip.encode(rawSqlite);
    final expectedSha = sha256.convert(gzBytes).toString();
    final lifecycleLog = <String>[];

    final service = ArtifactSyncService(
      directoryProvider: () async => tempDir,
      manifestUrl: 'https://example.test/release_manifest.json',
      bundleUrl: 'https://example.test/bible_pastoral_core.db.gz',
      clientFactory: () => MockClient((request) async {
        if (request.url.path.endsWith('release_manifest.json')) {
          return http.Response(
            jsonEncode({
              'compressed_sha256': expectedSha,
              'compressed_size_bytes': gzBytes.length,
            }),
            200,
          );
        }
        return http.Response.bytes(gzBytes, 200);
      }),
    );

    final events = await service
        .downloadAndInstallMasterDb(
          beforeSwap: () async => lifecycleLog.add('beforeSwap'),
          afterSwap: () async => lifecycleLog.add('afterSwap'),
        )
        .toList();

    expect(events.last.isCompleted, isTrue);
    expect(events.last.error, isNull);
    expect(lifecycleLog, equals(['beforeSwap', 'afterSwap']));
    expect(await service.isLocalDatabaseReady(), isTrue);
  });
}
