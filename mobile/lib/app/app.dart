import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../core/api_client.dart';
import 'router.dart';
import 'state.dart';
import 'theme.dart';

class DermaCareApp extends StatefulWidget {
  const DermaCareApp({super.key, this.api});

  /// Injectable for tests.
  final ApiClient? api;

  @override
  State<DermaCareApp> createState() => _DermaCareAppState();
}

class _DermaCareAppState extends State<DermaCareApp> {
  late final AppState _state = AppState(widget.api ?? ApiClient());
  late final GoRouter _router = buildRouter(_state);

  @override
  Widget build(BuildContext context) {
    return AppScope(
      state: _state,
      child: MaterialApp.router(
        title: 'DermaCare',
        theme: buildTheme(Brightness.light),
        darkTheme: buildTheme(Brightness.dark),
        routerConfig: _router,
        debugShowCheckedModeBanner: false,
      ),
    );
  }
}
