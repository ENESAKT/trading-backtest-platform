# Hooks

Bu klasor hook scriptleri icindir. Su an aktif hook yoktur.

Guvenli varsayilan:

- Hook'lar onaysiz aktif edilmez.
- `SessionStart` ve `UserPromptSubmit` context inject edecekse 30-50 satirlik
  kisa ozetle sinirlanir.
- `PostToolUse` hook'u otomatik `ruff`, `npm`, test veya format calistirmaz.
- `Stop` hook'u dosya yazmaz, checkbox guncellemez, commit/PR islemi yapmaz.
- `SubagentStop` hook'u agent ciktisini ana context'e otomatik yuklemez.

Riskli hook ornekleri:

- Otomatik full test suite.
- Otomatik lint/fix.
- Otomatik session recap yazimi.
- Otomatik planlama checkbox guncellemesi.
- Otomatik commit, push, PR veya merge.

Hook eklenirse once bu sorular cevaplanmali:

1. Hangi event?
2. Hangi komut?
3. Maksimum calisma suresi?
4. Context'e kac satir donecek?
5. Dosya yazacak mi?
6. Enes onayi olmadan test/git islemi yapacak mi?
