import Fuse from 'fuse.js';
import { marked } from 'marked';

export type EducationCategory =
  | 'indikatorler'
  | 'formasyonlar'
  | 'sistem-backtest'
  | 'viop-vadeli'
  | 'psikoloji-disiplin';

export type SourceConfidence = 'high' | 'medium' | 'low';
export type SourceMethod = 'frame_ocr' | 'transcript' | 'manual_review' | 'external_verification';

export interface EducationArticle {
  id: string;
  path: string;
  title: string;
  slug: string;
  category: EducationCategory;
  tags: string[];
  difficulty: string;
  indicator_key?: string;
  chart_indicator?: string;
  related_strategies: string[];
  source_courses: string[];
  source_method: SourceMethod;
  source_confidence: SourceConfidence;
  needs_audio_transcript: boolean;
  risk_warnings: string[];
  copy_policy: string;
  excerpt: string;
  content: string;
  searchText: string;
}

interface RawFrontmatter {
  [key: string]: string | string[] | boolean | undefined;
}

type MarkdownToken = {
  type: string;
  text?: string;
  depth?: number;
  lang?: string;
  ordered?: boolean;
  href?: string;
  title?: string | null;
  tokens?: MarkdownToken[];
  items?: MarkdownToken[];
} & Record<string, unknown>;

export const EDUCATION_CATEGORIES: Array<{ id: EducationCategory | 'all'; label: string }> = [
  { id: 'all', label: 'Tümü' },
  { id: 'indikatorler', label: 'İndikatörler' },
  { id: 'formasyonlar', label: 'Formasyonlar' },
  { id: 'sistem-backtest', label: 'Sistem & Backtest' },
  { id: 'viop-vadeli', label: 'VIOP & Vadeli' },
  { id: 'psikoloji-disiplin', label: 'Psikoloji & Disiplin' },
];

const articleModules = import.meta.glob('./**/*.md', {
  query: '?raw',
  import: 'default',
  eager: true,
}) as Record<string, string>;

export const EDUCATION_ARTICLES: EducationArticle[] = Object.entries(articleModules)
  .map(([path, raw]) => parseArticle(path, raw))
  .sort((a, b) => a.title.localeCompare(b.title, 'tr'));

const fuse = new Fuse(EDUCATION_ARTICLES, {
  keys: ['title', 'tags', 'excerpt', 'searchText'],
  threshold: 0.32,
  ignoreLocation: true,
});

export function searchEducationArticles(
  query: string,
  category: EducationCategory | 'all' = 'all',
): EducationArticle[] {
  const normalized = normalizeForSearch(query);
  const titleMatches = normalized
    ? EDUCATION_ARTICLES.filter(article => matchesQuery(
      normalizeForSearch([article.title, article.indicator_key ?? '', ...article.tags].join(' ')),
      normalized,
    ))
    : [];
  const contentMatches = normalized
    ? EDUCATION_ARTICLES.filter(article => matchesQuery(article.searchText, normalized))
      .filter(article => !titleMatches.includes(article))
    : [];
  const exactMatches = [...titleMatches, ...contentMatches];
  const base = normalized
    ? (exactMatches.length ? exactMatches : fuse.search(normalized).map(result => result.item))
    : EDUCATION_ARTICLES;
  return category === 'all'
    ? base
    : base.filter(article => article.category === category);
}

function matchesQuery(text: string, query: string): boolean {
  if (query.length <= 3) {
    return new RegExp(`(^|[^a-z0-9])${escapeRegExp(query)}($|[^a-z0-9])`).test(text);
  }
  return text.includes(query);
}

function escapeRegExp(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

export function categoryLabel(category: EducationCategory): string {
  return EDUCATION_CATEGORIES.find(item => item.id === category)?.label ?? category;
}

export function renderMarkdown(content: string): string {
  const tokens = marked.lexer(content, { gfm: true }) as MarkdownToken[];
  return tokens.map(renderBlockToken).join('');
}

function parseArticle(path: string, raw: string): EducationArticle {
  const match = raw.match(/^---\n([\s\S]*?)\n---\n([\s\S]*)$/);
  if (!match) throw new Error(`Eğitim makalesinde frontmatter yok: ${path}`);

  const meta = parseFrontmatter(match[1] ?? '');
  const content = (match[2] ?? '').trim();
  const slug = stringValue(meta.slug) || path.split('/').pop()?.replace(/\.md$/, '') || path;
  const title = requireString(meta, 'title', path);
  const tags = stringArray(meta.tags);
  const excerpt = firstParagraph(content);
  const category = (stringValue(meta.category) || 'indikatorler') as EducationCategory;

  return {
    id: slug,
    path,
    title,
    slug,
    category,
    tags,
    difficulty: stringValue(meta.difficulty) || 'başlangıç',
    indicator_key: stringValue(meta.indicator_key),
    chart_indicator: stringValue(meta.chart_indicator),
    related_strategies: stringArray(meta.related_strategies),
    source_courses: stringArray(meta.source_courses),
    source_method: (stringValue(meta.source_method) || 'frame_ocr') as SourceMethod,
    source_confidence: (stringValue(meta.source_confidence) || 'medium') as SourceConfidence,
    needs_audio_transcript: booleanValue(meta.needs_audio_transcript),
    risk_warnings: stringArray(meta.risk_warnings),
    copy_policy: stringValue(meta.copy_policy) || 'original_piyasapilot_content',
    excerpt,
    content,
    searchText: normalizeForSearch([title, excerpt, ...tags, content].join(' ')),
  };
}

function parseFrontmatter(raw: string): RawFrontmatter {
  const out: RawFrontmatter = {};
  const lines = raw.split(/\r?\n/);
  let i = 0;
  while (i < lines.length) {
    const line = lines[i] ?? '';
    i += 1;
    if (!line.trim() || line.trimStart().startsWith('#')) continue;
    const match = line.match(/^([A-Za-z0-9_-]+):\s*(.*)$/);
    if (!match) continue;

    const key = match[1]!;
    const value = match[2] ?? '';
    if (value.trim()) {
      out[key] = parseScalar(value.trim());
      continue;
    }

    const items: string[] = [];
    while (i < lines.length) {
      const itemMatch = (lines[i] ?? '').match(/^\s*-\s*(.+?)\s*$/);
      if (!itemMatch) break;
      items.push(stripQuotes(itemMatch[1] ?? ''));
      i += 1;
    }
    out[key] = items;
  }
  return out;
}

function parseScalar(value: string): string | string[] | boolean {
  if (value === 'true') return true;
  if (value === 'false') return false;
  if (value.startsWith('[') && value.endsWith(']')) {
    const inner = value.slice(1, -1).trim();
    return inner ? inner.split(',').map(item => stripQuotes(item.trim())) : [];
  }
  return stripQuotes(value);
}

function requireString(meta: RawFrontmatter, key: string, path: string): string {
  const value = stringValue(meta[key]);
  if (!value) throw new Error(`Eğitim makalesinde ${key} eksik: ${path}`);
  return value;
}

function stringValue(value: RawFrontmatter[string]): string {
  return typeof value === 'string' ? value : '';
}

function stringArray(value: RawFrontmatter[string]): string[] {
  if (Array.isArray(value)) return value;
  if (typeof value === 'string' && value.trim()) return [value.trim()];
  return [];
}

function booleanValue(value: RawFrontmatter[string]): boolean {
  return value === true || value === 'true';
}

function stripQuotes(value: string): string {
  return value.replace(/^['"]|['"]$/g, '').trim();
}

function firstParagraph(content: string): string {
  const paragraph = content
    .split(/\n{2,}/)
    .find(block => block.trim() && !block.trim().startsWith('#'));
  return paragraph?.replace(/\s+/g, ' ').trim() ?? '';
}

function normalizeForSearch(value: string): string {
  return value
    .toLocaleLowerCase('tr-TR')
    .replaceAll('ı', 'i')
    .replaceAll('ğ', 'g')
    .replaceAll('ü', 'u')
    .replaceAll('ş', 's')
    .replaceAll('ö', 'o')
    .replaceAll('ç', 'c')
    .normalize('NFD')
    .replace(/\p{Diacritic}/gu, '');
}

function renderBlockToken(token: MarkdownToken): string {
  switch (token.type) {
    case 'heading': {
      const depth = Math.min(Math.max(Number(token.depth ?? 2), 2), 4);
      return `<h${depth}>${renderInlineTokens(token.tokens, token.text)}</h${depth}>`;
    }
    case 'paragraph':
      return `<p>${renderInlineTokens(token.tokens, token.text)}</p>`;
    case 'list': {
      const tag = token.ordered ? 'ol' : 'ul';
      const items = (token.items ?? []).map(item => `<li>${renderListItem(item)}</li>`).join('');
      return `<${tag}>${items}</${tag}>`;
    }
    case 'code':
      return `<pre><code>${escapeHtml(token.text ?? '')}</code></pre>`;
    case 'blockquote':
      return `<blockquote>${(token.tokens ?? []).map(renderBlockToken).join('')}</blockquote>`;
    case 'hr':
      return '<hr>';
    case 'space':
      return '';
    default:
      return token.text ? `<p>${escapeHtml(token.text)}</p>` : '';
  }
}

function renderListItem(token: MarkdownToken): string {
  if (token.tokens?.length) return token.tokens.map(renderBlockToken).join('');
  return escapeHtml(token.text ?? '');
}

function renderInlineTokens(tokens: MarkdownToken[] | undefined, fallback = ''): string {
  if (!tokens?.length) return escapeHtml(fallback);
  return tokens.map(renderInlineToken).join('');
}

function renderInlineToken(token: MarkdownToken): string {
  switch (token.type) {
    case 'text':
    case 'escape':
      return renderInlineTokens(token.tokens, token.text);
    case 'strong':
      return `<strong>${renderInlineTokens(token.tokens, token.text)}</strong>`;
    case 'em':
      return `<em>${renderInlineTokens(token.tokens, token.text)}</em>`;
    case 'codespan':
      return `<code>${escapeHtml(token.text ?? '')}</code>`;
    case 'br':
      return '<br>';
    case 'link': {
      const href = safeHref(token.href);
      if (!href) return renderInlineTokens(token.tokens, token.text);
      const title = token.title ? ` title="${escapeAttr(String(token.title))}"` : '';
      return `<a href="${escapeAttr(href)}"${title} target="_blank" rel="noreferrer">${renderInlineTokens(token.tokens, token.text)}</a>`;
    }
    default:
      return escapeHtml(token.text ?? '');
  }
}

function safeHref(value: unknown): string {
  const href = String(value ?? '').trim();
  return /^(https?:|mailto:)/i.test(href) ? href : '';
}

function escapeHtml(value: string): string {
  return value.replace(/[&<>"']/g, ch => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;',
  })[ch] ?? ch);
}

function escapeAttr(value: string): string {
  return escapeHtml(value).replace(/`/g, '&#96;');
}
