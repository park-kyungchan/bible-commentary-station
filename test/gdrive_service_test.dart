import 'dart:convert';
import 'package:bible_commentary_workstation/data/services/gdrive_service.dart';
import 'package:bible_commentary_workstation/domain/models/bible_models.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:googleapis/drive/v3.dart' as drive;
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

void main() {
  test('uploadSermon updates existing file by gdriveFileId even when title changes', () async {
    final recordedMethods = <String>[];
    final recordedPaths = <String>[];

    final mockClient = MockClient((request) async {
      recordedMethods.add(request.method);
      recordedPaths.add(request.url.path);
      return http.Response(
        jsonEncode({'id': 'existing_drive_id_99'}),
        200,
        headers: {'content-type': 'application/json; charset=utf-8'},
      );
    });

    final service = GDriveSyncService(
      driveApi: drive.DriveApi(mockClient),
      appFolderId: 'app_folder_001',
    );

    const renamedSermon = Sermon(
      sermonId: 'sermon_01',
      title: '새로 바꾼 설교 제목',
      sermonDate: '2026-11-23',
      scriptureRef: '시편 23:1-6',
      outline: [
        SermonOutlinePoint(section: '서론', title: '목자', content: '여호와는 나의 목자'),
      ],
      gdriveFileId: 'existing_drive_id_99',
    );

    final resultId = await service.uploadSermon(renamedSermon);
    expect(resultId, equals('existing_drive_id_99'));
    expect(recordedMethods, equals(['PATCH']));
    expect(recordedPaths.single, contains('existing_drive_id_99'));
  });

  test('uploadSermon creates new file when gdriveFileId is null and no match exists', () async {
    final recordedMethods = <String>[];

    final mockClient = MockClient((request) async {
      recordedMethods.add(request.method);
      if (request.method == 'GET') {
        return http.Response(
          jsonEncode({'files': <dynamic>[]}),
          200,
          headers: {'content-type': 'application/json; charset=utf-8'},
        );
      }
      return http.Response(
        jsonEncode({'id': 'created_drive_id_77'}),
        200,
        headers: {'content-type': 'application/json; charset=utf-8'},
      );
    });

    final service = GDriveSyncService(
      driveApi: drive.DriveApi(mockClient),
      appFolderId: 'app_folder_001',
    );

    const newSermon = Sermon(
      sermonId: 'sermon_02',
      title: '처음 올리는 설교',
      sermonDate: '2026-11-23',
      scriptureRef: '창세기 1:1',
      outline: [],
    );

    final resultId = await service.uploadSermon(newSermon);
    expect(resultId, equals('created_drive_id_77'));
    expect(recordedMethods, equals(['GET', 'POST']));
  });
}
