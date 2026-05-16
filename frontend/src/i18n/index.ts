import { tr } from './tr.js';
import { en } from './en.js';

type Lang = 'tr' | 'en';
type Key = keyof typeof tr;
type Dictionary = Record<Key, string>;

class I18nManager {
  private lang: Lang = 'tr';
  private dict: Dictionary = tr;

  init(): void {
    const stored = localStorage.getItem('pp_lang') as Lang | null;
    const browser = navigator.language.toLowerCase().startsWith('en') ? 'en' : 'tr';
    this.setLang(stored === 'tr' || stored === 'en' ? stored : browser);
  }

  setLang(lang: Lang): void {
    this.lang = lang;
    this.dict = lang === 'en' ? { ...tr, ...en } : tr;
    localStorage.setItem('pp_lang', lang);
    document.documentElement.dataset['lang'] = lang;
    document.documentElement.lang = lang;
  }

  t(key: Key): string {
    return this.dict[key] || tr[key] || key;
  }

  current(): Lang {
    return this.lang;
  }
}

export const i18n = new I18nManager();
