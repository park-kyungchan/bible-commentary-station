import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:sqlite3/sqlite3.dart';
import 'application/workstation_controller.dart';
import 'core/theme/app_theme.dart';
import 'data/repositories/sqlite_bible_repository.dart';
import 'data/services/artifact_sync_service.dart';
import 'data/services/preferences_store.dart';
import 'presentation/screens/home_screen.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  final syncService = ArtifactSyncService();
  final preferencesStore = FilePreferencesStore();
  final controller = WorkstationController(
    syncService: syncService,
    preferencesStore: preferencesStore,
    repositoryOpener: (dbFile) async {
      final db = sqlite3.open(dbFile.path);
      return SqliteBibleRepository(db);
    },
  );
  unawaited(controller.bootstrapAndInitialize());
  runApp(BiblicalWorkstationApp(controller: controller));
}

class BiblicalWorkstationApp extends StatelessWidget {
  final WorkstationController controller;

  const BiblicalWorkstationApp({super.key, required this.controller});

  @override
  Widget build(BuildContext context) {
    return ListenableBuilder(
      listenable: controller,
      builder: (context, _) {
        return MaterialApp(
          title: '말씀 서재',
          debugShowCheckedModeBanner: false,
          localizationsDelegates: const [
            GlobalMaterialLocalizations.delegate,
            GlobalWidgetsLocalizations.delegate,
            GlobalCupertinoLocalizations.delegate,
          ],
          supportedLocales: const [
            Locale('ko', 'KR'),
            Locale('en', 'US'),
          ],
          theme: PastoralTheme.lightTheme,
          darkTheme: PastoralTheme.darkTheme,
          themeMode: controller.themeMode,
          home: HomeScreen(controller: controller),
        );
      },
    );
  }
}
