import 'package:flutter/material.dart';

import '../../app/routes.dart';
import '../../widgets/step_scaffold.dart';

class ProductsScreen extends StatelessWidget {
  const ProductsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return const StepScaffold(
      title: 'Products',
      description: 'TODO: ranked products from the verified catalog with score breakdown and reasons; excluded products with exclusion reasons.',
      nextRoute: Routes.history,
    );
  }
}
