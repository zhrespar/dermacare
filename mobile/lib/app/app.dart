import 'package:flutter/material.dart';

import 'router.dart';
import 'theme.dart';

class DermaCareApp extends StatelessWidget {
  const DermaCareApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp.router(
      title: 'DermaCare',
      theme: buildTheme(Brightness.light),
      darkTheme: buildTheme(Brightness.dark),
      routerConfig: appRouter,
      debugShowCheckedModeBanner: false,
    );
  }
}
