# Session Recap

Oturum sonu özeti oluştur ve planlama.md checkpoint'lerini güncelle.

## Kullanım

Her Codex oturumunun sonunda otomatik veya manuel çağrılır.

## Adımlar

1. Bu oturumda yapılan commit'leri listele:
   ```bash
   git log --oneline --since="6 hours ago"
   ```

2. planlama.md'den tamamlanan görevleri çıkar:
   ```bash
   grep '\- \[x\]' planlama.md | tail -5
   ```

3. Kalan görevlerin ilkini bul:
   ```bash
   grep '\- \[ \]' planlama.md | head -3
   ```

4. Session recap dosyasını oluştur:
   ```bash
   # .Codex/memory/session-recap.md dosyasına yaz
   ```

5. ogrenilenler.md'ye yeni öğrenilen bilgileri ekle (varsa)

## Session Recap Formatı

```markdown
# Session Recap — [tarih]

## Bu Oturumda Yapılanlar
- [commit listesi]
- [önemli kararlar]

## Sprint Durumu
- Sprint X: %Y tamamlandı
- Sıradaki görev: [açıklama]

## Öğrenilenler
- [teknik bilgi 1]
- [teknik bilgi 2]

## Sıradaki Adım
- [görev açıklaması]
```

## Otomatik Tetikleme

Bu skill `.Codex/hooks/auto-recap.sh` hook'u tarafından oturum sonunda
otomatik çağrılır. Manuel çağrı için `/devam` komutuyla eşleşir.
