import 'dart:io';
import 'package:flutter/material.dart';
import 'package:path/path.dart' as p;
import 'package:path_provider/path_provider.dart';
import 'package:sqlite3/sqlite3.dart';
import 'application/workstation_controller.dart';
import 'core/config/app_config.dart';
import 'core/theme/app_theme.dart';
import 'data/repositories/sqlite_bible_repository.dart';
import 'presentation/screens/home_screen.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  final dir = await getApplicationDocumentsDirectory();
  final dbFile = File(p.join(dir.path, AppConfig.localDbFileName));
  final db = sqlite3.open(dbFile.path);
  final repo = SqliteBibleRepository(db);
  final controller = WorkstationController(repo);
  await controller.initialize();
  runApp(BiblicalWorkstationApp(controller: controller));
}

class BiblicalWorkstationApp extends StatelessWidget {
  final WorkstationController controller;

  const BiblicalWorkstationApp({super.key, required this.controller});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: '성경주혜주석 v2.0 (Pastoral Workstation)',
      debugShowCheckedModeBanner: false,
      theme: PastoralTheme.lightTheme,
      darkTheme: PastoralTheme.darkTheme,
      themeMode: ThemeMode.dark,
      home: HomeScreen(controller: controller),
    );
  }
}
