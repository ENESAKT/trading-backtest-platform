import 'package:flutter/material.dart';

ThemeData buildAppTheme() {
  const amber = Color(0xFFF59E0B);
  return ThemeData(
    useMaterial3: true,
    colorScheme: ColorScheme.fromSeed(
      seedColor: amber,
      brightness: Brightness.dark,
      surface: const Color(0xFF111827),
    ),
    scaffoldBackgroundColor: const Color(0xFF0B1120),
    cardTheme: const CardThemeData(
      elevation: 0,
      margin: EdgeInsets.zero,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.all(Radius.circular(8)),
      ),
    ),
  );
}
