/// Route paths for the full user journey, in flow order.
class Routes {
  static const welcome = '/';
  static const auth = '/auth';
  static const profile = '/profile';
  static const capture = '/capture';
  static const quality = '/quality';
  static const analysis = '/analysis';
  static const results = '/results';
  static const routine = '/routine';
  static const products = '/products';
  static const history = '/history';

  static const flow = [
    welcome, auth, profile, capture, quality, analysis, results, routine, products, history,
  ];
}
