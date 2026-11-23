import 'package:flutter/material.dart';

/// Light pastel palette. The app always uses the light theme.
class Pastel {
  static const background = Color(0xFFFBF7F4); // warm cream
  static const surface = Color(0xFFFFFFFF);
  static const surfaceSoft = Color(0xFFF3EEF6); // pale lavender
  static const primary = Color(0xFF8FB9A8); // sage mint
  static const primarySoft = Color(0xFFDCEFE6);
  static const secondary = Color(0xFFF4C7C3); // blush pink
  static const secondarySoft = Color(0xFFFBE6E3);
  static const tertiary = Color(0xFFC9B6E4); // lavender
  static const tertiarySoft = Color(0xFFEDE4F7);
  static const peach = Color(0xFFFFE3C9);
  static const errorSoft = Color(0xFFF9D6D5);
  static const error = Color(0xFFC0605B);
  static const text = Color(0xFF3F3A44); // soft charcoal (keeps contrast readable)
  static const textMuted = Color(0xFF6E6875);
}

ThemeData buildTheme([Brightness _ = Brightness.light]) {
  const scheme = ColorScheme(
    brightness: Brightness.light,
    primary: Color(0xFF4F8A74), // darker sage for button text/icons contrast
    onPrimary: Colors.white,
    primaryContainer: Pastel.primarySoft,
    onPrimaryContainer: Pastel.text,
    secondary: Color(0xFFB9746E),
    onSecondary: Colors.white,
    secondaryContainer: Pastel.secondarySoft,
    onSecondaryContainer: Pastel.text,
    tertiary: Color(0xFF7E66A6),
    onTertiary: Colors.white,
    tertiaryContainer: Pastel.tertiarySoft,
    onTertiaryContainer: Pastel.text,
    error: Pastel.error,
    onError: Colors.white,
    errorContainer: Pastel.errorSoft,
    onErrorContainer: Pastel.text,
    surface: Pastel.surface,
    onSurface: Pastel.text,
    onSurfaceVariant: Pastel.textMuted,
    surfaceContainerHighest: Pastel.surfaceSoft,
    outline: Color(0xFFD9D2DF),
  );
  final shape = RoundedRectangleBorder(borderRadius: BorderRadius.circular(18));
  return ThemeData(
    useMaterial3: true,
    colorScheme: scheme,
    scaffoldBackgroundColor: Pastel.background,
    appBarTheme: const AppBarTheme(
      backgroundColor: Pastel.background,
      foregroundColor: Pastel.text,
      elevation: 0,
      scrolledUnderElevation: 0,
      centerTitle: true,
    ),
    cardTheme: CardThemeData(color: Pastel.surface, elevation: 0, shape: shape),
    filledButtonTheme: FilledButtonThemeData(
      style: FilledButton.styleFrom(
        backgroundColor: Pastel.primary,
        foregroundColor: Pastel.text,
        disabledBackgroundColor: const Color(0xFFE7E2EA),
        minimumSize: const Size.fromHeight(52),
        shape: shape,
        textStyle: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
      ),
    ),
    outlinedButtonTheme: OutlinedButtonThemeData(
      style: OutlinedButton.styleFrom(
        foregroundColor: Pastel.text,
        side: const BorderSide(color: Pastel.tertiary),
        minimumSize: const Size.fromHeight(48),
        shape: shape,
      ),
    ),
    chipTheme: ChipThemeData(
      backgroundColor: Pastel.surface,
      selectedColor: Pastel.secondarySoft,
      side: const BorderSide(color: Color(0xFFE6DDE8)),
      labelStyle: const TextStyle(color: Pastel.text),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
    ),
    segmentedButtonTheme: SegmentedButtonThemeData(
      style: ButtonStyle(
        backgroundColor: WidgetStateProperty.resolveWith(
            (s) => s.contains(WidgetState.selected) ? Pastel.tertiarySoft : Pastel.surface),
        foregroundColor: const WidgetStatePropertyAll(Pastel.text),
      ),
    ),
    inputDecorationTheme: const InputDecorationTheme(
      filled: true,
      fillColor: Pastel.surface,
      border: OutlineInputBorder(borderRadius: BorderRadius.all(Radius.circular(14))),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.all(Radius.circular(14)),
        borderSide: BorderSide(color: Color(0xFFE6DDE8)),
      ),
    ),
    progressIndicatorTheme: const ProgressIndicatorThemeData(
      color: Pastel.primary,
      linearTrackColor: Pastel.primarySoft,
    ),
  );
}
