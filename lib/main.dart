import 'package:flutter/material.dart';
import 'core/theme/app_theme.dart';
import 'presentation/screens/home_screen.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const BiblicalWorkstationApp());
}

class BiblicalWorkstationApp extends StatelessWidget {
  const BiblicalWorkstationApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: '성경주혜주석 (Pastoral Workstation)',
      debugShowCheckedModeBanner: false,
      theme: PastoralTheme.lightTheme,
      darkTheme: PastoralTheme.darkTheme,
      themeMode: ThemeMode.dark, // Default to pastoral dark workstation mode
      home: const HomeScreen(),
    );
  }
}
