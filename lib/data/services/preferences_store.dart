import 'dart:convert';
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:path/path.dart' as p;
import 'package:path_provider/path_provider.dart';
import '../../core/config/app_config.dart';
import '../../core/theme/app_theme.dart';

class WorkstationPreferences {
  final ThemeMode themeMode;
  final int fontStepIndex;

  const WorkstationPreferences({
    this.themeMode = ThemeMode.light,
    this.fontStepIndex = PastoralTheme.defaultFontStepIndex,
  });

  WorkstationPreferences copyWith({
    ThemeMode? themeMode,
    int? fontStepIndex,
  }) {
    return WorkstationPreferences(
      themeMode: themeMode ?? this.themeMode,
      fontStepIndex: fontStepIndex ?? this.fontStepIndex,
    );
  }

  Map<String, dynamic> toJson() => {
        'themeMode': themeMode == ThemeMode.dark ? 'dark' : 'light',
        'fontStepIndex': fontStepIndex,
      };

  static WorkstationPreferences fromJson(Map<String, dynamic> json) {
    final rawTheme = json['themeMode']?.toString();
    final themeMode = rawTheme == 'dark' ? ThemeMode.dark : ThemeMode.light;
    final rawStep = (json['fontStepIndex'] as num?)?.toInt() ??
        PastoralTheme.defaultFontStepIndex;
    final clampedStep = rawStep.clamp(
      0,
      PastoralTheme.scriptureFontSteps.length - 1,
    );
    return WorkstationPreferences(
      themeMode: themeMode,
      fontStepIndex: clampedStep,
    );
  }
}

abstract class PreferencesStore {
  Future<WorkstationPreferences> load();
  Future<void> save(WorkstationPreferences prefs);
}

class InMemoryPreferencesStore implements PreferencesStore {
  WorkstationPreferences _prefs;

  InMemoryPreferencesStore([
    this._prefs = const WorkstationPreferences(),
  ]);

  @override
  Future<WorkstationPreferences> load() async => _prefs;

  @override
  Future<void> save(WorkstationPreferences prefs) async {
    _prefs = prefs;
  }
}

/// Persists theme mode and senior font scale as a lightweight JSON file
/// inside the application documents directory (zero extra plugin overhead).
class FilePreferencesStore implements PreferencesStore {
  final Future<Directory> Function() _directoryProvider;

  FilePreferencesStore({Future<Directory> Function()? directoryProvider})
      : _directoryProvider = directoryProvider ?? getApplicationDocumentsDirectory;

  Future<File> _getPrefsFile() async {
    final dir = await _directoryProvider();
    return File(p.join(dir.path, AppConfig.preferencesFileName));
  }

  @override
  Future<WorkstationPreferences> load() async {
    try {
      final file = await _getPrefsFile();
      if (!await file.exists()) {
        return const WorkstationPreferences();
      }
      final raw = await file.readAsString();
      final decoded = jsonDecode(raw);
      if (decoded is Map<String, dynamic>) {
        return WorkstationPreferences.fromJson(decoded);
      }
      return const WorkstationPreferences();
    } catch (_) {
      return const WorkstationPreferences();
    }
  }

  @override
  Future<void> save(WorkstationPreferences prefs) async {
    try {
      final file = await _getPrefsFile();
      final tmpFile = File('${file.path}.tmp');
      await tmpFile.writeAsString(jsonEncode(prefs.toJson()), flush: true);
      await tmpFile.rename(file.path);
    } catch (_) {
      // Non-fatal: keep in-memory preferences active if storage is read-only.
    }
  }
}
