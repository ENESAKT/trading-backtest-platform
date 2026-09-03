# HANDOFF — Backtest

## Durum
Proje 6 Ağustos 2026'dan beri uykuda, sunucuda çalışan hiçbir Backtest servisi yok.
Depoda **iki ayrı ve birbirinden ayrışmış sürüm** duruyor: `main` (256 commit, 483 dosya)
ve yerel `codex/financials-ui-api-v1` dalı (210 commit, 1242 dosya). İkisi 19 Mayıs 2026'da
`afc0cec` commit'inde ayrılmış ve o tarihten sonra ikisi de kendi başına büyümüş.

## Sende
1. **Karar: `codex/financials-ui-api-v1` dalı tutulacak mı, silinecek mi?** Hangi sürümün
   gerçek proje olduğunu sadece sen bilebilirsin — kod iki tarafta da tutarlı görünüyor,
   commit mesajları yanıltıcı, ve seçim ürün kararı. Ajan bu yüzden kendi başına seçemez.
   Silme kararı verirsen bunun **geri alınamaz** olduğunu bilerek ver (aşağıya bak).

## Bende
1. Karar "tut" çıkarsa: yapılacak bir şey yok, bu dosya kalsın.
2. Karar "sil" çıkarsa: önce `git bundle create` ile dalın yedeğini al, sonra sil.
   Yedeksiz silme yapma.
3. Proje canlandırılırsa: iki sürüm arasında hangisinin taban alınacağına karar verildikten
   sonra diğerinden alınacak parçalar tek tek taşınır — `git merge` denemek 1242 dosyalık
   bir çakışma üretir.

## Dikkat
- **Dal yalnızca yerelde. `origin`'de kopyası yok** (`git branch -r` boş döner). Silinirse
  geri getirilemez. Rutin temizlik diye silme.
- **Commit mesajları içeriği anlatmıyor.** `84ad71a`'nın başlığı "domain, CORS, cookie ve SSL
  düzeltmeleri" ama commit **1242 dosya / 177.973 satır** ekliyor — bir çalışma dizini
  dökümü, düzeltme değil. `b31c533` başlığı `.env.production.example` diyor ama aynı zamanda
  `backend/api/main.py` dahil **5.390 satır siliyor**.
- Dalda `tests/unit/` altında 52 dosya var, `main`'de 7. Bu depo bu workspace'in
  "test yok" kuralının dışında kalan bir geçmişe sahip; testleri çalıştırma, sadece varlıklarını
  dalın ağırlığının kanıtı olarak say.

## Bağlantılar
- `main` son commit: `1b71a13` (6 Ağustos 2026)
- Ayrışma noktası: `afc0cec` (19 Mayıs 2026, "security: canlıya alma öncesi güvenlik sertleştirmesi")
- Dal ucu: `84ad71a` (19 Mayıs 2026)
- Depoda ayrıca 9 dal daha var (`chore/sprint-0-skeleton`, `codex/backtest-b3-dsl-builder`, …); bu turda incelenmediler
