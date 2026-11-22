import 'package:flutter/material.dart';

class PastoralTheme {
  static const Color primaryNavy = Color(0xFF1E293B);
  static const Color accentGold = Color(0xFFD97706);
  static const Color statusEmerald = Color(0xFF10B981); // Semantic emerald status color
  static const Color backgroundLight = Color(0xFFF8FAFC);

  static const Color darkBg = Color(0xFF0F172A);
  static const Color darkCard = Color(0xFF1E293B);
  static const Color darkBorder = Color(0xFF334155);

  // WCAG AAA 21:1 Contrast Pulpit Palette
  static const Color pulpitBackground = Color(0xFF000000);
  static const Color pulpitText = Color(0xFFFFFFFF);
  static const Color pulpitAccent = Color(0xFFFBBF24);

  static ThemeData get lightTheme => ThemeData(
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

  static ThemeData get darkTheme => ThemeData(
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

  static TextStyle pulpitBodyStyle(double sizePt) => TextStyle(
        fontSize: sizePt,
        height: 1.6,
        fontWeight: FontWeight.w600,
        color: pulpitText,
        letterSpacing: -0.4,
      );

  static TextStyle pulpitHeaderStyle(double sizePt) => TextStyle(
        fontSize: sizePt + 6.0,
        fontWeight: FontWeight.bold,
        color: pulpitAccent,
        height: 1.35,
      );
}
