# PiyasaPilot Mobile

Flutter + Dart başlangıç iskeleti. Web terminalin mobilde sıkışan deneyimini kopyalamak yerine, backend API'lerine bağlanan native bir MVVM / Clean Architecture kabuğu sağlar.

## Çalıştırma

```bash
flutter pub get
flutter analyze
flutter test
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000
```

Production:

```bash
flutter build apk --dart-define=API_BASE_URL=https://piyasapilotu.com
```

## Kapsam

- Auth: login/register ekran iskeleti ve `/api/auth/mobile/*` token akışına hazır API client
- Terminal: sembol/timeframe shell, loading ve error state
- Portfolio: paper mode uyarısı ve empty state
- Settings: API URL, plan ve güvenli çıkış yeri
- Onboarding: dil/tema/ilk sembol akışı için başlangıç ekranı

Canlı push bildirim, App Store/Play Store signing, Firebase ve gerçek ikon/splash üretimi kullanıcı hesabı/panel aksiyonu gerektirir.
