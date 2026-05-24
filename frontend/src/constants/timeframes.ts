/**
 * Merkezi timeframe sabitleri — tüm frontend modülleri buradan import eder.
 * Dahili kod değerleri backend ile aynı kalır (1m, 5m, ...).
 * Kullanıcıya gösterilen etiketler Türkçedir (1dk, 5dk, ...).
 *
 * ⚠️  Yeni bir timeframe eklenecekse yalnızca bu dosya güncellenir;
 *     ChartPanel, StrategyPanel, Screener vb. dosyalar bu sabitleri kullanır.
 */

import { TR } from './tr';

// ─── Canonical sıralı liste (küçükten büyüğe) ──────────────────────────────
export const VALID_INTERVALS = [
  '1m', '5m', '15m', '30m',
  '1h', '2h', '4h',
  '1d', '1w', '1mo',
] as const;

export type Interval = (typeof VALID_INTERVALS)[number];

// ─── Türkçe görüntü etiketleri ────────────────────────────────────────────
export const TF_LABEL_TR: Record<string, string> = {
  '1m':  TR.TF_1M,   // '1dk'
  '5m':  TR.TF_5M,   // '5dk'
  '15m': TR.TF_15M,  // '15dk'
  '30m': TR.TF_30M,  // '30dk'
  '1h':  TR.TF_1H,   // '1s'
  '2h':  '2s',
  '4h':  TR.TF_4H,   // '4s'
  '1d':  TR.TF_1D,   // '1g'
  '1w':  TR.TF_1W,   // '1hf'
  '1mo': TR.TF_1MO,  // '1ay'
};

// ─── Timeframe → saniye (cache TTL ve polling hesabı için) ────────────────
export const TF_SECONDS: Record<string, number> = {
  '1m':   60,
  '5m':   300,
  '15m':  900,
  '30m':  1_800,
  '1h':   3_600,
  '2h':   7_200,
  '4h':   14_400,
  '1d':   86_400,
  '1w':   604_800,
  '1mo':  2_592_000,
};

// ─── Backtest / strateji paneli için gösterilen setler ───────────────────
/** Dakika bazlı intraday timeframe'ler */
export const INTRADAY_INTERVALS = ['1m', '5m', '15m', '30m', '1h', '2h', '4h'] as const;

/** Günlük ve üzeri timeframe'ler */
export const DAILY_INTERVALS = ['1d', '1w', '1mo'] as const;

/** StrategyPanel batch taraması için önerilen set */
export const STRATEGY_BATCH_INTERVALS = ['15m', '1h', '4h', '1d', '1w'] as const;

// ─── Yardımcı fonksiyonlar ────────────────────────────────────────────────

/** Timeframe'in Türkçe etiketini döner; bilinmiyorsa aynen döner. */
export function tfLabel(interval: string): string {
  return TF_LABEL_TR[interval] ?? interval;
}

/** Verilen string geçerli bir interval mi? */
export function isValidInterval(value: string): value is Interval {
  return (VALID_INTERVALS as readonly string[]).includes(value);
}

/**
 * <select> elementi için option HTML listesi üretir.
 * @param selected Seçili olan değer (optional)
 * @param subset Gösterilecek subset; belirtilmezse tüm VALID_INTERVALS kullanılır
 */
export function tfOptions(
  selected?: string,
  subset: readonly string[] = VALID_INTERVALS,
): string {
  return subset
    .map(tf => {
      const sel = tf === selected ? ' selected' : '';
      return `<option value="${tf}"${sel}>${tfLabel(tf)}</option>`;
    })
    .join('');
}
