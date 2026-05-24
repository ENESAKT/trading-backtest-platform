/**
 * SymbolUniverse — sembol evrenini backend'den çeken ve önbelleğe alan modül.
 *
 * Kullanım:
 *   import { symbolUniverse } from '../core/SymbolUniverse.js';
 *   const symbols = await symbolUniverse.all();
 *   const cryptos = await symbolUniverse.byGroup('Kripto');
 *
 * Fallback davranışı:
 *   Backend erişilemezse symbols.ts içindeki statik liste kullanılır.
 *   Her başarılı yüklemeden sonra in-memory cache güncellenir (TTL: 5 dk).
 */

import type { SymbolInfo } from '../types.js';
import { ALL_SYMBOLS } from '../constants/symbols.js';

interface BackendSymbol {
  symbol: string;
  name: string;
  asset_type: string;
  group: string;
  currency: string;
  active: boolean;
  market: string;
  provider: string;
}

interface SymbolUniverseResponse {
  symbols: BackendSymbol[];
  total: number;
  fetched_at: string;
}

/** Backend yanıtını SymbolInfo tipine dönüştürür */
function toSymbolInfo(s: BackendSymbol): SymbolInfo {
  return {
    symbol:    s.symbol,
    name:      s.name,
    assetType: (s.asset_type as SymbolInfo['assetType']) ?? 'equity',
    group:     s.group,
    currency:  s.currency,
  };
}

const CACHE_TTL_MS = 5 * 60 * 1000; // 5 dakika

class SymbolUniverseManager {
  private _cache: SymbolInfo[] | null = null;
  private _fetchedAt = 0;
  private _loading: Promise<SymbolInfo[]> | null = null;

  /** Tüm aktif sembolleri döner (cache önce, sonra backend, fallback statik). */
  async all(forceRefresh = false): Promise<SymbolInfo[]> {
    const now = Date.now();
    if (!forceRefresh && this._cache && (now - this._fetchedAt) < CACHE_TTL_MS) {
      return this._cache;
    }
    if (this._loading) return this._loading;
    this._loading = this._fetch().finally(() => { this._loading = null; });
    return this._loading;
  }

  /** Belirtilen gruba ait sembolleri döner. */
  async byGroup(group: string): Promise<SymbolInfo[]> {
    return (await this.all()).filter(s => s.group === group);
  }

  /** Belirtilen asset_type'a ait sembolleri döner. */
  async byAssetType(type: SymbolInfo['assetType']): Promise<SymbolInfo[]> {
    return (await this.all()).filter(s => s.assetType === type);
  }

  /** Sembol stringine göre SymbolInfo döner; bulunamazsa undefined. */
  async find(symbol: string): Promise<SymbolInfo | undefined> {
    return (await this.all()).find(s => s.symbol === symbol);
  }

  /** Cache'i sıfırlar — ayarlar değiştiğinde çağrılabilir. */
  invalidate(): void {
    this._cache = null;
    this._fetchedAt = 0;
  }

  /** Mevcut cache'i (stale olsa bile) döner. Async değil, UI için hızlı erişim. */
  snapshot(): SymbolInfo[] {
    return this._cache ?? ALL_SYMBOLS;
  }

  private async _fetch(): Promise<SymbolInfo[]> {
    try {
      const resp = await fetch('/api/symbols?active_only=true', {
        credentials: 'same-origin',
        headers: { Accept: 'application/json' },
      });
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const data: SymbolUniverseResponse = await resp.json();
      const symbols = data.symbols.map(toSymbolInfo);
      this._cache = symbols;
      this._fetchedAt = Date.now();
      return symbols;
    } catch (err) {
      console.warn('[SymbolUniverse] Backend erişilemedi, statik liste kullanılıyor.', err);
      // Fallback: statik liste
      if (!this._cache) {
        this._cache = ALL_SYMBOLS;
        this._fetchedAt = Date.now();
      }
      return this._cache;
    }
  }
}

/** Uygulama genelinde tek örnek. */
export const symbolUniverse = new SymbolUniverseManager();

/**
 * Bir kez yükler ve döner. app.ts gibi başlatma noktalarında kullanılır.
 * Tekrar çağrılsa da TTL dolmadıkça backend'e ikinci istek atmaz.
 */
export async function preloadSymbolUniverse(): Promise<SymbolInfo[]> {
  return symbolUniverse.all();
}
