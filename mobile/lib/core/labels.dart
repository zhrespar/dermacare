// Turkish UI labels for API codes. Unknown codes are shown as-is so nothing is hidden.

const skinTypes = {'dry': 'Kuru', 'oily': 'Yağlı', 'combination': 'Karma', 'normal': 'Normal'};
const sensitivities = {'none': 'Hassas değil', 'mild': 'Biraz hassas', 'high': 'Çok hassas'};
const needs = {
  'acne_care': 'Akne bakımı',
  'wrinkle_care': 'Kırışıklık bakımı',
  'under_eye_care': 'Göz altı bakımı',
  'hydration': 'Nemlendirme',
  'sun_protection': 'Güneş koruması',
};
const categories = {
  'cleanser': 'Temizleyici',
  'treatment': 'Bakım ürünü',
  'serum': 'Serum',
  'eye': 'Göz kremi',
  'moisturizer': 'Nemlendirici',
  'sunscreen': 'Güneş kremi',
};
const severities = {'mild': 'Hafif', 'moderate': 'Orta', 'severe': 'Belirgin', 'very_severe': 'Çok belirgin'};
const regions = {
  'forehead': 'Alın',
  'left_cheek': 'Sol yanak',
  'right_cheek': 'Sağ yanak',
  'nose': 'Burun',
  'chin': 'Çene',
  'left_under_eye': 'Sol göz altı',
  'right_under_eye': 'Sağ göz altı',
};
const qualityReasons = {
  'unsupported_format': 'Desteklenmeyen dosya biçimi (JPEG veya PNG kullanın)',
  'image_too_small': 'Görüntü çok küçük',
  'no_face_detected': 'Yüz bulunamadı',
  'multiple_faces': 'Birden fazla yüz var',
  'blurry': 'Fotoğraf bulanık',
  'too_dark': 'Ortam çok karanlık',
  'overexposed': 'Işık çok fazla',
  'face_too_small': 'Yüz kadrajda çok küçük',
  'regions_not_visible': 'Yüz bölgeleri görünmüyor',
};
const triageTitles = {
  'proceed': 'Analiz tamamlandı',
  'limited': 'Sonuçlar sınırlı',
  'refer_dermatologist': 'Dermatoloğa danışmanızı öneririz',
  'retake': 'Lütfen yeni fotoğraf çekin',
};
const triageTexts = {
  'proceed': 'Bulgular önerilerde kullanılacak.',
  'limited': 'Model bu fotoğrafta yeterince emin değil. Öneriler yalnızca profilinize göre hazırlanacak.',
  'refer_dermatologist':
      'Bu durum kozmetik bakım kapsamının dışında olabilir. Bir dermatoloğa danışmanız önerilir.',
  'retake': 'Fotoğraf analize uygun değil.',
};
const exclusionReasons = {
  'product_not_verified': 'Ürün bilgisi doğrulanmamış',
  'not_available': 'Satışta değil',
  'over_budget': 'Bütçenizin üzerinde',
  'warning_conflicts_with_sensitivity': 'Üretici uyarısı hassasiyetinizle çelişiyor',
  'no_relevant_need': 'İhtiyaçlarınızla eşleşmiyor',
};

String label(Map<String, String> m, String? code) => code == null ? '—' : (m[code] ?? code);

String exclusionLabel(String r) {
  if (r.startsWith('contains_blocked_ingredient:')) {
    return 'Kaçındığınız içerik: ${r.split(':').last}';
  }
  return exclusionReasons[r] ?? r;
}
