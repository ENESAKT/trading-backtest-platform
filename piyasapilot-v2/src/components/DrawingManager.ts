// ─── Drawing Manager — G5 Çizim Altyapısı ────────────────────────────────────
// Lightweight-charts üstüne DOM overlay katmanı ile çizim araçları.
// v1: trend çizgisi, yatay çizgi, dikey çizgi, ölçüm aracı.
// Çizimler sembol + timeframe anahtarıyla localStorage'da saklanır.

import type { IChartApi, UTCTimestamp } from 'lightweight-charts';
import { formatNumber } from '../constants/tr.js';

// ─── Types ────────────────────────────────────────────────────────────────────

export type DrawingTool = 'trendline' | 'hline' | 'vline' | 'measure' | 'none';

export interface DrawingPoint {
  time: number;   // unix seconds
  price: number;
}

export interface DrawingStyle {
  color: string;
  lineWidth: number;
  lineStyle: 'solid' | 'dashed' | 'dotted';
}

export interface DrawingData {
  id: string;
  tool: DrawingTool;
  points: DrawingPoint[];
  style: DrawingStyle;
  label?: string;
}

interface StoredDrawings {
  [symbolTimeframeKey: string]: DrawingData[];
}

// ─── Constants ────────────────────────────────────────────────────────────────

const LS_KEY = 'piyasapilot_drawings';
const DEFAULT_STYLE: DrawingStyle = {
  color: '#58a6ff',
  lineWidth: 2,
  lineStyle: 'solid',
};
const COLORS = ['#58a6ff', '#3fb950', '#f85149', '#bc8cff', '#d29922', '#e3b341', '#8b949e'];
const HANDLE_RADIUS = 5;

// ─── DrawingManager ───────────────────────────────────────────────────────────

export class DrawingManager {
  private chart: IChartApi;
  private container: HTMLElement;
  private canvas!: HTMLCanvasElement;
  private ctx!: CanvasRenderingContext2D;

  private activeTool: DrawingTool = 'none';
  private drawings: DrawingData[] = [];
  private pendingPoints: DrawingPoint[] = [];
  private currentStyle: DrawingStyle = { ...DEFAULT_STYLE };
  private colorIndex = 0;

  private symbol = '';
  private timeframe = '';

  private selectedDrawingId: string | null = null;
  private dragState: { drawingId: string; pointIndex: number; startX: number; startY: number } | null = null;
  private hoverPoint: { x: number; y: number } | null = null;

  private resizeObserver!: ResizeObserver;
  private boundRender: () => void;
  private toolbarEl: HTMLElement | null = null;
  private _onChange: ((count: number) => void) | null = null;

  constructor(chart: IChartApi, container: HTMLElement) {
    this.chart = chart;
    this.container = container;
    this.boundRender = () => this.render();
    this.createCanvas();
    this.bindEvents();
    this.bindChartEvents();
  }

  // ─── Canvas setup ──────────────────────────────────────────────────────

  private createCanvas(): void {
    this.canvas = document.createElement('canvas');
    this.canvas.className = 'drawing-canvas';
    this.canvas.style.cssText =
      'position:absolute;top:0;left:0;width:100%;height:100%;z-index:20;pointer-events:none;';
    this.container.appendChild(this.canvas);
    this.ctx = this.canvas.getContext('2d')!;
    this.resizeCanvas();

    this.resizeObserver = new ResizeObserver(() => {
      this.resizeCanvas();
      this.render();
    });
    this.resizeObserver.observe(this.container);
  }

  private resizeCanvas(): void {
    const rect = this.container.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    this.canvas.width = rect.width * dpr;
    this.canvas.height = rect.height * dpr;
    this.canvas.style.width = `${rect.width}px`;
    this.canvas.style.height = `${rect.height}px`;
    this.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }

  // ─── Events ────────────────────────────────────────────────────────────

  private bindEvents(): void {
    this.container.addEventListener('mousedown', this.onMouseDown);
    this.container.addEventListener('mousemove', this.onMouseMove);
    this.container.addEventListener('mouseup', this.onMouseUp);
    this.container.addEventListener('dblclick', this.onDblClick);
    document.addEventListener('keydown', this.onKeyDown);
  }

  private bindChartEvents(): void {
    this.chart.timeScale().subscribeVisibleLogicalRangeChange(() => {
      requestAnimationFrame(this.boundRender);
    });
    this.chart.subscribeCrosshairMove(() => {
      if (this.drawings.length > 0 || this.pendingPoints.length > 0) {
        requestAnimationFrame(this.boundRender);
      }
    });
  }

  private onMouseDown = (e: MouseEvent): void => {
    if (this.activeTool === 'none') {
      // Check if clicking on a drawing handle for dragging
      const point = this.screenToChart(e.offsetX, e.offsetY);
      if (!point) return;
      const hit = this.hitTestHandle(e.offsetX, e.offsetY);
      if (hit) {
        this.dragState = { drawingId: hit.drawingId, pointIndex: hit.pointIndex, startX: e.offsetX, startY: e.offsetY };
        this.selectedDrawingId = hit.drawingId;
        this.canvas.style.pointerEvents = 'auto';
        this.canvas.style.cursor = 'grabbing';
        e.preventDefault();
        e.stopPropagation();
      }
      return;
    }

    this.canvas.style.pointerEvents = 'auto';
    const point = this.screenToChart(e.offsetX, e.offsetY);
    if (!point) return;

    e.preventDefault();
    e.stopPropagation();

    if (this.activeTool === 'hline') {
      this.addDrawing({
        id: this.genId(),
        tool: 'hline',
        points: [point],
        style: { ...this.currentStyle },
      });
      this.setTool('none');
      return;
    }

    if (this.activeTool === 'vline') {
      this.addDrawing({
        id: this.genId(),
        tool: 'vline',
        points: [point],
        style: { ...this.currentStyle },
      });
      this.setTool('none');
      return;
    }

    // Trendline & measure: two-click
    this.pendingPoints.push(point);
    if (this.pendingPoints.length === 2) {
      this.addDrawing({
        id: this.genId(),
        tool: this.activeTool,
        points: [...this.pendingPoints],
        style: { ...this.currentStyle },
      });
      this.pendingPoints = [];
      this.setTool('none');
    }
  };

  private onMouseMove = (e: MouseEvent): void => {
    if (this.dragState) {
      const point = this.screenToChart(e.offsetX, e.offsetY);
      if (!point) return;
      const drawing = this.drawings.find(d => d.id === this.dragState!.drawingId);
      if (drawing && drawing.points[this.dragState.pointIndex]) {
        drawing.points[this.dragState.pointIndex] = point;
        this.render();
      }
      e.preventDefault();
      return;
    }

    if (this.activeTool !== 'none' && this.pendingPoints.length > 0) {
      this.hoverPoint = { x: e.offsetX, y: e.offsetY };
      this.render();
    }
  };

  private onMouseUp = (_e: MouseEvent): void => {
    if (this.dragState) {
      this.dragState = null;
      this.canvas.style.pointerEvents = 'none';
      this.canvas.style.cursor = '';
      this.saveDrawings();
      this.render();
    }
  };

  private onDblClick = (e: MouseEvent): void => {
    if (this.activeTool !== 'none') return;
    const hit = this.hitTestDrawing(e.offsetX, e.offsetY);
    if (hit) {
      this.selectedDrawingId = hit;
      this.render();
    }
  };

  private onKeyDown = (e: KeyboardEvent): void => {
    if (e.key === 'Escape') {
      if (this.activeTool !== 'none') {
        this.pendingPoints = [];
        this.setTool('none');
        return;
      }
      this.selectedDrawingId = null;
      this.render();
    }
    if ((e.key === 'Delete' || e.key === 'Backspace') && this.selectedDrawingId) {
      this.removeDrawing(this.selectedDrawingId);
      this.selectedDrawingId = null;
    }
  };

  // ─── Coordinate conversion ─────────────────────────────────────────────

  private screenToChart(x: number, y: number): DrawingPoint | null {
    const timeScale = this.chart.timeScale();
    const tc = timeScale.coordinateToTime(x);
    if (tc == null) return null;
    try {
      const price = this.estimatePriceFromY(y);
      if (price == null) return null;
      return { time: Number(tc), price };
    } catch {
      return null;
    }
  }

  private estimatePriceFromY(y: number): number | null {
    try {
      const series = this.getMainSeries();
      if (!series) return null;
      const price = (series as any).coordinateToPrice?.(y);
      if (price != null && Number.isFinite(price)) return price;
    } catch {
      // fallback
    }
    return null;
  }

  private chartToScreen(point: DrawingPoint): { x: number; y: number } | null {
    try {
      const timeScale = this.chart.timeScale();
      const x = timeScale.timeToCoordinate(point.time as UTCTimestamp);
      if (x == null) return null;

      const series = this.getMainSeries();
      if (!series) return null;
      const y = (series as any).priceToCoordinate?.(point.price);
      if (y == null || !Number.isFinite(y)) return null;
      return { x, y };
    } catch {
      return null;
    }
  }

  private getMainSeries(): any {
    // Access chart's series via internal API
    try {
      // lightweight-charts stores series — we find the first visible one
      const chartAny = this.chart as any;
      // Try internal method path
      if (chartAny._private__seriesMap) {
        for (const series of chartAny._private__seriesMap.values()) {
          return series;
        }
      }
    } catch { /* fallback */ }
    return this._externalSeries ?? null;
  }

  // External series reference set by ChartPanel
  private _externalSeries: any = null;
  setMainSeries(series: any): void {
    this._externalSeries = series;
  }

  // ─── Hit testing ───────────────────────────────────────────────────────

  private hitTestHandle(screenX: number, screenY: number): { drawingId: string; pointIndex: number } | null {
    for (const drawing of this.drawings) {
      for (let i = 0; i < drawing.points.length; i++) {
        const pt = this.chartToScreen(drawing.points[i]!);
        if (!pt) continue;
        const dx = screenX - pt.x;
        const dy = screenY - pt.y;
        if (Math.sqrt(dx * dx + dy * dy) <= HANDLE_RADIUS + 3) {
          return { drawingId: drawing.id, pointIndex: i };
        }
      }
    }
    return null;
  }

  private hitTestDrawing(screenX: number, screenY: number): string | null {
    for (const drawing of this.drawings) {
      if (drawing.tool === 'hline') {
        const pt = this.chartToScreen(drawing.points[0]!);
        if (pt && Math.abs(screenY - pt.y) <= 5) return drawing.id;
      }
      if (drawing.tool === 'vline') {
        const pt = this.chartToScreen(drawing.points[0]!);
        if (pt && Math.abs(screenX - pt.x) <= 5) return drawing.id;
      }
      if ((drawing.tool === 'trendline' || drawing.tool === 'measure') && drawing.points.length === 2) {
        const p1 = this.chartToScreen(drawing.points[0]!);
        const p2 = this.chartToScreen(drawing.points[1]!);
        if (!p1 || !p2) continue;
        const dist = this.pointToSegmentDist(screenX, screenY, p1.x, p1.y, p2.x, p2.y);
        if (dist <= 6) return drawing.id;
      }
    }
    return null;
  }

  private pointToSegmentDist(px: number, py: number, x1: number, y1: number, x2: number, y2: number): number {
    const dx = x2 - x1;
    const dy = y2 - y1;
    const lenSq = dx * dx + dy * dy;
    if (lenSq === 0) return Math.sqrt((px - x1) ** 2 + (py - y1) ** 2);
    let t = ((px - x1) * dx + (py - y1) * dy) / lenSq;
    t = Math.max(0, Math.min(1, t));
    const cx = x1 + t * dx;
    const cy = y1 + t * dy;
    return Math.sqrt((px - cx) ** 2 + (py - cy) ** 2);
  }

  // ─── Rendering ─────────────────────────────────────────────────────────

  render(): void {
    const w = this.canvas.clientWidth;
    const h = this.canvas.clientHeight;
    this.ctx.clearRect(0, 0, w, h);

    for (const drawing of this.drawings) {
      this.renderDrawing(drawing);
    }

    // Render pending (in-progress) drawing
    if (this.pendingPoints.length === 1 && this.hoverPoint) {
      const p1 = this.chartToScreen(this.pendingPoints[0]!);
      if (p1) {
        this.ctx.save();
        this.applyStyle(this.currentStyle);
        this.ctx.globalAlpha = 0.6;
        this.ctx.beginPath();
        this.ctx.moveTo(p1.x, p1.y);
        this.ctx.lineTo(this.hoverPoint.x, this.hoverPoint.y);
        this.ctx.stroke();
        this.ctx.restore();
      }
    }
  }

  private renderDrawing(drawing: DrawingData): void {
    const isSelected = drawing.id === this.selectedDrawingId;

    if (drawing.tool === 'hline' && drawing.points[0]) {
      const pt = this.chartToScreen(drawing.points[0]);
      if (!pt) return;
      this.ctx.save();
      this.applyStyle(drawing.style);
      if (isSelected) this.ctx.lineWidth = drawing.style.lineWidth + 1;
      this.ctx.beginPath();
      this.ctx.moveTo(0, pt.y);
      this.ctx.lineTo(this.canvas.clientWidth, pt.y);
      this.ctx.stroke();
      // Price label
      this.drawLabel(`${formatNumber(drawing.points[0].price, 2)}`, this.canvas.clientWidth - 80, pt.y - 12, drawing.style.color);
      if (isSelected) this.drawHandle(pt.x, pt.y);
      this.ctx.restore();
      return;
    }

    if (drawing.tool === 'vline' && drawing.points[0]) {
      const pt = this.chartToScreen(drawing.points[0]);
      if (!pt) return;
      this.ctx.save();
      this.applyStyle(drawing.style);
      if (isSelected) this.ctx.lineWidth = drawing.style.lineWidth + 1;
      this.ctx.beginPath();
      this.ctx.moveTo(pt.x, 0);
      this.ctx.lineTo(pt.x, this.canvas.clientHeight);
      this.ctx.stroke();
      if (isSelected) this.drawHandle(pt.x, pt.y);
      this.ctx.restore();
      return;
    }

    if (drawing.tool === 'trendline' && drawing.points.length === 2) {
      const p1 = this.chartToScreen(drawing.points[0]!);
      const p2 = this.chartToScreen(drawing.points[1]!);
      if (!p1 || !p2) return;
      this.ctx.save();
      this.applyStyle(drawing.style);
      if (isSelected) this.ctx.lineWidth = drawing.style.lineWidth + 1;
      this.ctx.beginPath();
      this.ctx.moveTo(p1.x, p1.y);
      this.ctx.lineTo(p2.x, p2.y);
      this.ctx.stroke();
      // Percent change label
      const pctChange = ((drawing.points[1]!.price - drawing.points[0]!.price) / drawing.points[0]!.price) * 100;
      const midX = (p1.x + p2.x) / 2;
      const midY = (p1.y + p2.y) / 2;
      this.drawLabel(`${pctChange >= 0 ? '+' : ''}${formatNumber(pctChange, 2)}%`, midX, midY - 14, drawing.style.color);
      if (isSelected) {
        this.drawHandle(p1.x, p1.y);
        this.drawHandle(p2.x, p2.y);
      }
      this.ctx.restore();
      return;
    }

    if (drawing.tool === 'measure' && drawing.points.length === 2) {
      const p1 = this.chartToScreen(drawing.points[0]!);
      const p2 = this.chartToScreen(drawing.points[1]!);
      if (!p1 || !p2) return;
      this.ctx.save();
      this.applyStyle(drawing.style);
      this.ctx.setLineDash([4, 4]);
      this.ctx.beginPath();
      this.ctx.moveTo(p1.x, p1.y);
      this.ctx.lineTo(p2.x, p2.y);
      this.ctx.stroke();
      // Measurement info
      const priceDiff = drawing.points[1]!.price - drawing.points[0]!.price;
      const pctChange = (priceDiff / drawing.points[0]!.price) * 100;
      const timeDiff = drawing.points[1]!.time - drawing.points[0]!.time;
      const bars = Math.round(timeDiff / 86400); // approximate bars (daily)
      const midX = (p1.x + p2.x) / 2;
      const midY = (p1.y + p2.y) / 2;
      const labelLines = [
        `${pctChange >= 0 ? '+' : ''}${formatNumber(pctChange, 2)}%`,
        `Fark: ${formatNumber(priceDiff, 2)}`,
        `${bars} bar`,
      ];
      labelLines.forEach((line, i) => {
        this.drawLabel(line, midX, midY - 14 + i * 16, drawing.style.color);
      });
      if (isSelected) {
        this.drawHandle(p1.x, p1.y);
        this.drawHandle(p2.x, p2.y);
      }
      this.ctx.restore();
    }
  }

  private applyStyle(style: DrawingStyle): void {
    this.ctx.strokeStyle = style.color;
    this.ctx.lineWidth = style.lineWidth;
    if (style.lineStyle === 'dashed') {
      this.ctx.setLineDash([6, 4]);
    } else if (style.lineStyle === 'dotted') {
      this.ctx.setLineDash([2, 3]);
    } else {
      this.ctx.setLineDash([]);
    }
  }

  private drawHandle(x: number, y: number): void {
    this.ctx.save();
    this.ctx.fillStyle = '#58a6ff';
    this.ctx.strokeStyle = '#0d1117';
    this.ctx.lineWidth = 2;
    this.ctx.setLineDash([]);
    this.ctx.beginPath();
    this.ctx.arc(x, y, HANDLE_RADIUS, 0, Math.PI * 2);
    this.ctx.fill();
    this.ctx.stroke();
    this.ctx.restore();
  }

  private drawLabel(text: string, x: number, y: number, color: string): void {
    this.ctx.save();
    this.ctx.font = '10px "JetBrains Mono", monospace';
    const metrics = this.ctx.measureText(text);
    const pad = 4;
    this.ctx.fillStyle = 'rgba(13,17,23,0.85)';
    this.ctx.fillRect(x - pad, y - 10, metrics.width + pad * 2, 14);
    this.ctx.fillStyle = color;
    this.ctx.fillText(text, x, y);
    this.ctx.restore();
  }

  // ─── Public API ────────────────────────────────────────────────────────

  setTool(tool: DrawingTool): void {
    this.activeTool = tool;
    this.pendingPoints = [];
    this.hoverPoint = null;

    if (tool === 'none') {
      this.canvas.style.pointerEvents = 'none';
      this.canvas.style.cursor = '';
    } else {
      this.canvas.style.pointerEvents = 'auto';
      this.canvas.style.cursor = 'crosshair';
      // Advance color for next drawing
      this.currentStyle.color = COLORS[this.colorIndex % COLORS.length]!;
      this.colorIndex++;
    }

    this.updateToolbarState();
    this.container.dataset['drawingTool'] = tool;
    this.render();
  }

  getTool(): DrawingTool { return this.activeTool; }

  onDrawingChange(callback: (count: number) => void): void {
    this._onChange = callback;
  }

  private notifyChange(): void {
    this.container.dataset['drawingCount'] = String(this.drawings.length);
    this._onChange?.(this.drawings.length);
  }

  setContext(symbol: string, timeframe: string): void {
    // Save current drawings before switching
    if (this.symbol && this.timeframe) {
      this.saveDrawings();
    }
    this.symbol = symbol;
    this.timeframe = timeframe;
    this.selectedDrawingId = null;
    this.pendingPoints = [];
    this.loadDrawings();
    this.notifyChange();
    this.render();
  }

  getDrawingCount(): number { return this.drawings.length; }

  addDrawing(drawing: DrawingData): void {
    this.drawings.push(drawing);
    this.saveDrawings();
    this.notifyChange();
    this.render();
  }

  removeDrawing(id: string): void {
    this.drawings = this.drawings.filter(d => d.id !== id);
    this.saveDrawings();
    this.notifyChange();
    this.render();
  }

  clearAll(): void {
    this.drawings = [];
    this.selectedDrawingId = null;
    this.saveDrawings();
    this.notifyChange();
    this.render();
  }

  // ─── Persistence ───────────────────────────────────────────────────────

  private storageKey(): string {
    return `${this.symbol}__${this.timeframe}`;
  }

  private loadDrawings(): void {
    try {
      const stored = JSON.parse(localStorage.getItem(LS_KEY) || '{}') as StoredDrawings;
      this.drawings = stored[this.storageKey()] ?? [];
    } catch {
      this.drawings = [];
    }
  }

  private saveDrawings(): void {
    if (!this.symbol || !this.timeframe) return;
    try {
      const stored = JSON.parse(localStorage.getItem(LS_KEY) || '{}') as StoredDrawings;
      if (this.drawings.length > 0) {
        stored[this.storageKey()] = this.drawings;
      } else {
        delete stored[this.storageKey()];
      }
      localStorage.setItem(LS_KEY, JSON.stringify(stored));
    } catch {
      // localStorage full or unavailable
    }
  }

  // ─── Toolbar ───────────────────────────────────────────────────────────

  buildToolbar(): string {
    return `
      <div class="ctrl-group">
        <span class="ctrl-label">Çizim</span>
        <button class="ctrl-btn drawing-tool-btn" data-drawing-tool="trendline" title="Trend Çizgisi">⟋</button>
        <button class="ctrl-btn drawing-tool-btn" data-drawing-tool="hline" title="Yatay Çizgi">―</button>
        <button class="ctrl-btn drawing-tool-btn" data-drawing-tool="vline" title="Dikey Çizgi">│</button>
        <button class="ctrl-btn drawing-tool-btn" data-drawing-tool="measure" title="Ölçüm Aracı">📏</button>
        <button class="ctrl-btn drawing-clear-btn" id="drawing-clear-btn" title="Tüm çizimleri sil">🗑</button>
      </div>
    `;
  }

  bindToolbar(controlsEl: HTMLElement): void {
    this.toolbarEl = controlsEl;
    controlsEl.addEventListener('click', (e) => {
      const btn = (e.target as HTMLElement).closest('button');
      if (!btn) return;

      if (btn.classList.contains('drawing-tool-btn')) {
        const tool = btn.dataset['drawingTool'] as DrawingTool;
        if (this.activeTool === tool) {
          this.setTool('none');
        } else {
          this.setTool(tool);
        }
        return;
      }

      if (btn.id === 'drawing-clear-btn') {
        this.clearAll();
      }
    });
  }

  private updateToolbarState(): void {
    if (!this.toolbarEl) return;
    this.toolbarEl.querySelectorAll<HTMLElement>('.drawing-tool-btn').forEach(btn => {
      btn.classList.toggle('active', btn.dataset['drawingTool'] === this.activeTool);
    });
  }

  // ─── Helpers ───────────────────────────────────────────────────────────

  private genId(): string {
    return `d_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
  }

  // ─── Cleanup ───────────────────────────────────────────────────────────

  destroy(): void {
    this.container.removeEventListener('mousedown', this.onMouseDown);
    this.container.removeEventListener('mousemove', this.onMouseMove);
    this.container.removeEventListener('mouseup', this.onMouseUp);
    this.container.removeEventListener('dblclick', this.onDblClick);
    document.removeEventListener('keydown', this.onKeyDown);
    this.resizeObserver.disconnect();
    this.canvas.remove();
  }
}
