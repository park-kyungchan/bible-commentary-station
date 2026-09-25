import 'package:flutter/material.dart';

class PastoralTheme {
  // Brand & Theological Colors
  static const Color primaryNavy = Color(0xFF1E293B);
  static const Color accentGold = Color(0xFFD97706);
  static const Color accentBurgundy = Color(0xFF881337);
  static const Color backgroundLight = Color(0xFFF8FAFC);
  static const Color surfaceCardLight = Colors.white;

  // Dark Theme Colors (Pastoral Study & Night Reading)
  static const Color darkBg = Color(0xFF0F172A);
  static const Color darkCard = Color(0xFF1E293B);
  static const Color darkBorder = Color(0xFF334155);
  static const Color darkTextPrimary = Color(0xFFF1F5F9);
  static const Color darkTextSecondary = Color(0xFF94A3B8);

  // Pulpit Prompter High-Contrast Color
  static const Color pulpitBackground = Color(0xFF000000);
  static const Color pulpitText = Color(0xFFFFFFFF);
  static const Color pulpitAccent = Color(0xFFFBBF24); // Warm Gold

  static ThemeData get lightTheme {
    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.light,
      scaffoldBackgroundColor: backgroundLight,
      colorScheme: ColorScheme.fromSeed(
        seedColor: primaryNavy,
        brightness: Brightness.light,
        primary: primaryNavy,
        secondary: accentGold,
      ),
      fontFamily: 'NotoSansKR',
    );
  }

  static ThemeData get darkTheme {
    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.dark,
      scaffoldBackgroundColor: darkBg,
      cardColor: darkCard,
      colorScheme: const ColorScheme.dark(
        primary: accentGold,
        secondary: Color(0xFF38BDF8),
        surface: darkCard,
      ),
      fontFamily: 'NotoSansKR',
    );
  }

  // Pulpit Mode TextStyle: 38pt minimum for 70cm ~ 1m pulpit visibility
  static const TextStyle pulpitLargeTextStyle = TextStyle(
    fontSize: 38.0,
    height: 1.6,
    fontWeight: FontWeight.w600,
    color: pulpitText,
    letterSpacing: -0.5,
  );

  static const TextStyle pulpitHeaderTextStyle = TextStyle(
    fontSize: 44.0,
    fontWeight: FontWeight.bold,
    color: pulpitAccent,
    height: 1.4,
  );
}
