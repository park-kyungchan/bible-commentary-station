import 'package:flutter/material.dart';

/// Sanctuary Hanji & Sumi Ink (Light) + Evening Study (Dark) + Zero-Glare Pulpit Theme.
/// Aligned 1:1 with the v3.0 Web PWA WCAG AAA (>= 7.0:1) design token system.
class PastoralTheme {
  // --- Sanctuary Hanji Light Tokens ---
  static const Color lightCanvas = Color(0xFFFAF6EE);
  static const Color lightSurface = Color(0xFFFFFDF9);
  static const Color lightSubtle = Color(0xFFF3ECE0);
  static const Color lightBorderHairline = Color(0xFFE3D9C8);
  static const Color lightBorderControl = Color(0xFF9E8F7B);
  static const Color lightBrandNavy = Color(0xFF1B365D);
  static const Color lightBrandSoft = Color(0xFFEBF0F7);
  static const Color lightInkPrimary = Color(0xFF1F1A15);
  static const Color lightInkSecondary = Color(0xFF4A4036);
  static const Color lightInkMuted = Color(0xFF5C5044);
  static const Color lightWarmAccent = Color(0xFF7A3900);
  static const Color lightAccentSoft = Color(0xFFFDF2DF);
  static const Color lightForest = Color(0xFF165B3E);
  static const Color lightForestSoft = Color(0xFFE6F4EC);
  static const Color lightCrimson = Color(0xFF9F1239);
  static const Color lightCrimsonSoft = Color(0xFFFFE4E6);

  // --- Evening Study Dark Tokens ---
  static const Color darkCanvas = Color(0xFF141210);
  static const Color darkSurface = Color(0xFF1E1B18);
  static const Color darkSubtle = Color(0xFF28241F);
  static const Color darkBorderHairline = Color(0xFF363029);
  static const Color darkBorderControl = Color(0xFF6E6356);
  static const Color darkBrandGold = Color(0xFFF0B44C);
  static const Color darkInkPrimary = Color(0xFFF5EFE4);
  static const Color darkInkSecondary = Color(0xFFD8CEBE);
  static const Color darkInkMuted = Color(0xFFB5A998);
  static const Color darkWarmAccent = Color(0xFFF5C76B);
  static const Color darkForest = Color(0xFF6EE7B7);
  static const Color darkCrimson = Color(0xFFFDA4AF);

  // --- Isolated Zero-Glare Pulpit Tokens (Independent of Light/Dark Mode) ---
  static const Color pulpitBackground = Color(0xFF000000);
  static const Color pulpitBarBg = Color(0xFF141210);
  static const Color pulpitBarBorder = Color(0xFF2E2924);
  static const Color pulpitButtonBg = Color(0xFF24201B);
  static const Color pulpitButtonBorder = Color(0xFF4A4238);
  static const Color pulpitInk = Color(0xFFFFFDF5);
  static const Color pulpitGold = Color(0xFFFFD166);
  static const Color pulpitAlert = Color(0xFFFF8A80);

  // --- Unified 4-Step Senior Font Scale (18-30sp Scripture, 16-23sp Study) ---
  static const List<double> scriptureFontSteps = [18.0, 21.0, 25.0, 30.0];
  static const List<double> studyFontSteps = [16.0, 17.5, 20.0, 23.0];
  static const List<String> fontStepLabels = ['보통', '크게', '아주 크게', '초대형'];
  static const int defaultFontStepIndex = 1;

  static Color statusForest(Brightness brightness) =>
      brightness == Brightness.dark ? darkForest : lightForest;

  static Color statusCrimson(Brightness brightness) =>
      brightness == Brightness.dark ? darkCrimson : lightCrimson;

  static Color warmAccent(Brightness brightness) =>
      brightness == Brightness.dark ? darkWarmAccent : lightWarmAccent;

  static Color hairlineBorder(Brightness brightness) =>
      brightness == Brightness.dark ? darkBorderHairline : lightBorderHairline;

  static Color subtleSurface(Brightness brightness) =>
      brightness == Brightness.dark ? darkSubtle : lightSubtle;

  static Color mutedInk(Brightness brightness) =>
      brightness == Brightness.dark ? darkInkMuted : lightInkMuted;

  static ThemeData get lightTheme {
    const colorScheme = ColorScheme(
      brightness: Brightness.light,
      primary: lightBrandNavy,
      onPrimary: lightSurface,
      primaryContainer: lightBrandSoft,
      onPrimaryContainer: lightBrandNavy,
      secondary: lightWarmAccent,
      onSecondary: lightSurface,
      secondaryContainer: lightAccentSoft,
      onSecondaryContainer: lightWarmAccent,
      surface: lightSurface,
      onSurface: lightInkPrimary,
      surfaceContainerLowest: lightSurface,
      surfaceContainerLow: lightCanvas,
      surfaceContainer: lightSubtle,
      surfaceContainerHigh: lightSubtle,
      surfaceContainerHighest: lightBorderHairline,
      onSurfaceVariant: lightInkSecondary,
      outline: lightBorderControl,
      outlineVariant: lightBorderHairline,
      error: lightCrimson,
      onError: lightSurface,
      errorContainer: lightCrimsonSoft,
      onErrorContainer: lightCrimson,
    );

    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.light,
      scaffoldBackgroundColor: lightCanvas,
      colorScheme: colorScheme,
      dividerColor: lightBorderHairline,
      cardTheme: CardThemeData(
        color: lightSurface,
        elevation: 0,
        margin: const EdgeInsets.symmetric(vertical: 4),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
          side: const BorderSide(color: lightBorderHairline),
        ),
      ),
      dialogTheme: DialogThemeData(
        backgroundColor: lightSurface,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
          side: const BorderSide(color: lightBorderHairline),
        ),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          minimumSize: const Size(48, 48),
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          backgroundColor: lightBrandNavy,
          foregroundColor: lightSurface,
          textStyle: const TextStyle(fontSize: 15, fontWeight: FontWeight.w600),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
        ),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          minimumSize: const Size(48, 48),
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
          foregroundColor: lightInkPrimary,
          side: const BorderSide(color: lightBorderControl),
          textStyle: const TextStyle(fontSize: 15, fontWeight: FontWeight.w600),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
        ),
      ),
      textButtonTheme: TextButtonThemeData(
        style: TextButton.styleFrom(
          minimumSize: const Size(48, 48),
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
          foregroundColor: lightBrandNavy,
          textStyle: const TextStyle(fontSize: 15, fontWeight: FontWeight.w600),
        ),
      ),
      iconButtonTheme: IconButtonThemeData(
        style: IconButton.styleFrom(minimumSize: const Size(48, 48)),
      ),
      segmentedButtonTheme: const SegmentedButtonThemeData(
        style: ButtonStyle(
          minimumSize: WidgetStatePropertyAll<Size>(Size(48, 48)),
        ),
      ),
      listTileTheme: const ListTileThemeData(
        minTileHeight: 52,
        contentPadding: EdgeInsets.symmetric(horizontal: 16, vertical: 4),
      ),
      navigationBarTheme: const NavigationBarThemeData(
        height: 68,
        backgroundColor: lightSurface,
        indicatorColor: lightBrandSoft,
      ),
    );
  }

  static ThemeData get darkTheme {
    const colorScheme = ColorScheme(
      brightness: Brightness.dark,
      primary: darkBrandGold,
      onPrimary: darkCanvas,
      primaryContainer: darkSubtle,
      onPrimaryContainer: darkBrandGold,
      secondary: darkWarmAccent,
      onSecondary: darkCanvas,
      secondaryContainer: darkSubtle,
      onSecondaryContainer: darkWarmAccent,
      surface: darkSurface,
      onSurface: darkInkPrimary,
      surfaceContainerLowest: darkCanvas,
      surfaceContainerLow: darkSurface,
      surfaceContainer: darkSubtle,
      surfaceContainerHigh: darkSubtle,
      surfaceContainerHighest: darkBorderHairline,
      onSurfaceVariant: darkInkSecondary,
      outline: darkBorderControl,
      outlineVariant: darkBorderHairline,
      error: darkCrimson,
      onError: darkCanvas,
      errorContainer: darkSubtle,
      onErrorContainer: darkCrimson,
    );

    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.dark,
      scaffoldBackgroundColor: darkCanvas,
      colorScheme: colorScheme,
      dividerColor: darkBorderHairline,
      cardTheme: CardThemeData(
        color: darkSurface,
        elevation: 0,
        margin: const EdgeInsets.symmetric(vertical: 4),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
          side: const BorderSide(color: darkBorderHairline),
        ),
      ),
      dialogTheme: DialogThemeData(
        backgroundColor: darkSurface,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
          side: const BorderSide(color: darkBorderHairline),
        ),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          minimumSize: const Size(48, 48),
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          backgroundColor: darkBrandGold,
          foregroundColor: darkCanvas,
          textStyle: const TextStyle(fontSize: 15, fontWeight: FontWeight.w600),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
        ),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          minimumSize: const Size(48, 48),
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
          foregroundColor: darkInkPrimary,
          side: const BorderSide(color: darkBorderControl),
          textStyle: const TextStyle(fontSize: 15, fontWeight: FontWeight.w600),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
        ),
      ),
      textButtonTheme: TextButtonThemeData(
        style: TextButton.styleFrom(
          minimumSize: const Size(48, 48),
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
          foregroundColor: darkBrandGold,
          textStyle: const TextStyle(fontSize: 15, fontWeight: FontWeight.w600),
        ),
      ),
      iconButtonTheme: IconButtonThemeData(
        style: IconButton.styleFrom(minimumSize: const Size(48, 48)),
      ),
      segmentedButtonTheme: const SegmentedButtonThemeData(
        style: ButtonStyle(
          minimumSize: WidgetStatePropertyAll<Size>(Size(48, 48)),
        ),
      ),
      listTileTheme: const ListTileThemeData(
        minTileHeight: 52,
        contentPadding: EdgeInsets.symmetric(horizontal: 16, vertical: 4),
      ),
      navigationBarTheme: const NavigationBarThemeData(
        height: 68,
        backgroundColor: darkSurface,
        indicatorColor: darkSubtle,
      ),
    );
  }

  static TextStyle pulpitBodyStyle(double sizePt) => TextStyle(
        fontSize: sizePt,
        height: 1.65,
        fontWeight: FontWeight.w600,
        color: pulpitInk,
        letterSpacing: -0.3,
      );

  static TextStyle pulpitHeaderStyle(double sizePt) => TextStyle(
        fontSize: sizePt + 6.0,
        fontWeight: FontWeight.bold,
        color: pulpitGold,
        height: 1.35,
      );
}
