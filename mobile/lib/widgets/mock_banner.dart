import 'package:flutter/material.dart';

/// Shown on every screen that displays analysis output while models are mocked.
class MockBanner extends StatelessWidget {
  const MockBanner({super.key});

  @override
  Widget build(BuildContext context) {
    return Card(
      key: const Key('mock-banner'),
      color: const Color(0xFFFFE3C9), // pastel peach
      child: const Padding(
        padding: EdgeInsets.all(12),
        child: Text('DENEME VERİSİ — Yer tutucu modeller kullanılıyor; bu gerçek bir analiz değildir.'),
      ),
    );
  }
}
