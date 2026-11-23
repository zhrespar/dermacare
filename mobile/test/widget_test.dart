import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:dermacare/app/app.dart';
import 'package:dermacare/app/routes.dart';

void main() {
  testWidgets('welcome screen shows disclaimer and start button', (tester) async {
    await tester.pumpWidget(const DermaCareApp());
    expect(find.text('DermaCare'), findsOneWidget);
    expect(find.textContaining('does not diagnose'), findsOneWidget);
    expect(find.byKey(const Key('get-started')), findsOneWidget);
  });

  testWidgets('can walk the full journey to History', (tester) async {
    await tester.pumpWidget(const DermaCareApp());
    await tester.tap(find.byKey(const Key('get-started')));
    await tester.pumpAndSettle();
    // auth -> profile -> capture -> quality -> analysis -> results -> routine -> products -> history
    for (var i = 0; i < Routes.flow.length - 2; i++) {
      await tester.tap(find.byKey(const Key('next')));
      await tester.pumpAndSettle();
    }
    expect(find.text('History'), findsOneWidget);
    expect(find.byKey(const Key('next')), findsNothing);
  });
}
