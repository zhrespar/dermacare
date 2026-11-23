import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:image_picker/image_picker.dart';

import '../../app/routes.dart';
import '../../app/state.dart';
import '../../widgets/common.dart';

class CaptureScreen extends StatefulWidget {
  const CaptureScreen({super.key});

  @override
  State<CaptureScreen> createState() => _CaptureScreenState();
}

class _CaptureScreenState extends State<CaptureScreen> {
  Future<void> _pick(ImageSource src) async {
    final app = AppScope.of(context);
    try {
      final f = await ImagePicker().pickImage(
        source: src,
        preferredCameraDevice: CameraDevice.front,
        maxWidth: 1600,
        imageQuality: 92,
      );
      if (f == null) return;
      app.setPhoto(await f.readAsBytes(), f.name);
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Kameraya veya galeriye erişilemedi. İzinleri kontrol edin.')),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final app = AppScope.of(context);
    return PageScaffold(
      title: 'Yüz fotoğrafı',
      action: app.photo == null ? null : () => context.push(Routes.quality),
      actionLabel: 'Analiz et',
      showDisabledAction: true,
      children: [
        const InfoCard(
          title: 'İyi bir fotoğraf için',
          body: '• Yüzünüz kameraya tam dönük olsun\n'
              '• Gün ışığı gibi eşit bir ışık kullanın\n'
              '• Gözlük, saç veya makyaj yüzü kapatmasın\n'
              '• Kadrajda yalnızca siz olun',
        ),
        const SizedBox(height: 12),
        AspectRatio(
          aspectRatio: 3 / 4,
          child: Container(
            decoration: BoxDecoration(
              color: Theme.of(context).colorScheme.surfaceContainerHighest,
              borderRadius: BorderRadius.circular(16),
            ),
            clipBehavior: Clip.antiAlias,
            child: app.photo == null
                ? const Center(child: Icon(Icons.face_retouching_natural, size: 96))
                : Image.memory(app.photo!, fit: BoxFit.cover),
          ),
        ),
        const SizedBox(height: 12),
        Row(children: [
          Expanded(
            child: OutlinedButton.icon(
              key: const Key('camera'),
              onPressed: () => _pick(ImageSource.camera),
              icon: const Icon(Icons.photo_camera),
              label: const Text('Kamera'),
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: OutlinedButton.icon(
              key: const Key('gallery'),
              onPressed: () => _pick(ImageSource.gallery),
              icon: const Icon(Icons.photo_library),
              label: const Text('Galeri'),
            ),
          ),
        ]),
        const SizedBox(height: 8),
        Text(
          'Fotoğrafınız telefonda saklanmaz; yalnızca analiz için sunucuya gönderilir.',
          style: Theme.of(context).textTheme.bodySmall,
        ),
      ],
    );
  }
}
