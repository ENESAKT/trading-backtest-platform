// ─── Drawing Manager — G5 Çizim Altyapısı ────────────────────────────────────
// Lightweight-charts üstüne DOM overlay katmanı ile çizim araçları.
// v1: trend çizgisi, yatay çizgi, dikey çizgi, ölçüm aracı.
// Çizimler sembol + timeframe anahtarıyla localStorage'da saklanır.

import type { IChartApi, UTCTimestamp } from 'lightweight-charts';
import { formatNumber } from '../constants/tr.js';

// ─── Types ────────────────────────────────────────────────────────────────────

export type DrawingTool = 'trendline' | 'hline' | 'vline' | 'measure' | 'fibonacci' | 'fibonacci_ext' | 'regression' | 'none';

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

// G10: Fibonacci levels
const FIBO_LEVELS = [0, 0.236, 0.382, 0.5, 0.618, 0.786, 1];
const FIBO_EXT_LEVELS = [0, 0.618, 1, 1.272, 1.618, 2, 2.618];
const FIBO_COLORS = ['#f85149', '#e3b341', '#3fb950', '#58a6ff', '#bc8cff', '#d29922', '#8b949e'];

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
      if (!point) {
        if (this.selectedDrawingId) {
          this.selectedDrawingId = null;
          this.render();
        }
        return;
      }
      
      const hitHandle = this.hitTestHandle(e.offsetX, e.offsetY);
      if (hitHandle) {
        this.dragState = { drawingId: hitHandle.drawingId, pointIndex: hitHandle.pointIndex, startX: e.offsetX, startY: e.offsetY };
        this.selectedDrawingId = hitHandle.drawingId;
        this.canvas.style.pointerEvents = 'auto';
        this.canvas.style.cursor = 'grabbing';
        e.preventDefault();
        e.stopPropagation();
        this.render();
        return;
      }

      // Check for single click selection on drawing body
      const hitDrawing = this.hitTestDrawing(e.offsetX, e.offsetY);
      if (hitDrawing) {
        this.selectedDrawingId = hitDrawing;
        this.render();
      } else if (this.selectedDrawingId) {
        // Deselect if clicked empty space
        this.selectedDrawingId = null;
        this.render();
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

    // Trendline, measure & G10 tools: two-click
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
      // Use coordinateToPrice via type assertion since it's an internal method or only available on specific series types
      const price = (series as unknown as { coordinateToPrice?: (val: number) => number }).coordinateToPrice?.(y);
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
      const y = (series as unknown as { priceToCoordinate?: (val: number) => number }).priceToCoordinate?.(point.price);
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
      const chartAny = this.chart as unknown as { _private__seriesMap?: Map<unknown, unknown> };
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

  // Candle reference for regression calculations
  private _candlesRef: Array<{ time: number; close: number }> | null = null;
  setCandles(candles: Array<{ time: number; close: number }>): void {
    this._candlesRef = candles;
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
      if (
        (drawing.tool === 'trendline' || drawing.tool === 'measure' || 
         drawing.tool === 'fibonacci' || drawing.tool === 'fibonacci_ext' || 
         drawing.tool === 'regression') 
        && drawing.points.length === 2
      ) {
        const p1 = this.chartToScreen(drawing.points[0]!);
        const p2 = this.chartToScreen(drawing.points[1]!);
        if (!p1 || !p2) continue;
        const dist = this.pointToSegmentDist(screenX, screenY, p1.x, p1.y, p2.x, p2.y);
        if (dist <= 10) return drawing.id;
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

    // ── G10: Fibonacci Retracement ─────────────────────────────────────────
    if ((drawing.tool === 'fibonacci' || drawing.tool === 'fibonacci_ext') && drawing.points.length === 2) {
      const p1 = this.chartToScreen(drawing.points[0]!);
      const p2 = this.chartToScreen(drawing.points[1]!);
      if (!p1 || !p2) return;

      const priceHigh = Math.max(drawing.points[0]!.price, drawing.points[1]!.price);
      const priceLow  = Math.min(drawing.points[0]!.price, drawing.points[1]!.price);
      const priceRange = priceHigh - priceLow;
      const levels = drawing.tool === 'fibonacci_ext' ? FIBO_EXT_LEVELS : FIBO_LEVELS;

      const canvasW = this.canvas.clientWidth;
      const x1 = Math.min(p1.x, p2.x);
      const x2 = Math.max(p1.x, p2.x);

      this.ctx.save();
      this.ctx.font = '10px "JetBrains Mono", monospace';

      levels.forEach((level, idx) => {
        const levelPrice = drawing.tool === 'fibonacci_ext'
          ? priceLow + priceRange * level          // extension goes above high
          : priceHigh - priceRange * level;        // retracement from high

        // Map price -> screen y via main series
        const series = this.getMainSeries();
        const yCoord = series ? (series as unknown as { priceToCoordinate?: (val: number) => number }).priceToCoordinate?.(levelPrice) : null;
        if (yCoord == null || !Number.isFinite(yCoord)) return;

        const color = FIBO_COLORS[idx % FIBO_COLORS.length]!;
        this.ctx.strokeStyle = color;
        this.ctx.lineWidth = 1;
        this.ctx.setLineDash([4, 3]);
        this.ctx.beginPath();
        this.ctx.moveTo(x1, yCoord);
        this.ctx.lineTo(x2 || canvasW, yCoord);
        this.ctx.stroke();

        // Label
        const levelPct = (level * 100).toFixed(1);
        const labelText = `${levelPct}%  ${formatNumber(levelPrice, 2)}`;
        const metrics = this.ctx.measureText(labelText);
        const lx = x2 + 4;
        const ly = yCoord - 2;
        this.ctx.setLineDash([]);
        this.ctx.fillStyle = 'rgba(13,17,23,0.85)';
        this.ctx.fillRect(lx - 2, ly - 10, metrics.width + 6, 14);
        this.ctx.fillStyle = color;
        this.ctx.fillText(labelText, lx, ly);
      });

      // Draggable handles
      if (isSelected) {
        this.ctx.restore();
        this.ctx.save();
        this.drawHandle(p1.x, p1.y);
        this.drawHandle(p2.x, p2.y);
      }
      this.ctx.restore();
      return;
    }

    // ── G10: Linear Regression Channel ────────────────────────────────────
    if (drawing.tool === 'regression' && drawing.points.length === 2) {
      const p1 = this.chartToScreen(drawing.points[0]!);
      const p2 = this.chartToScreen(drawing.points[1]!);
      if (!p1 || !p2) return;

      // Gather candle prices in range to do regression
      const tMin = Math.min(drawing.points[0]!.time, drawing.points[1]!.time);
      const tMax = Math.max(drawing.points[0]!.time, drawing.points[1]!.time);
      const inRange = this._candlesRef?.filter(c => c.time >= tMin && c.time <= tMax) ?? [];

      if (inRange.length < 2) {
        // Fallback: draw a simple line
        this.ctx.save();
        this.applyStyle(drawing.style);
        this.ctx.beginPath();
        this.ctx.moveTo(p1.x, p1.y);
        this.ctx.lineTo(p2.x, p2.y);
        this.ctx.stroke();
        if (isSelected) { this.drawHandle(p1.x, p1.y); this.drawHandle(p2.x, p2.y); }
        this.ctx.restore();
        return;
      }

      // Linear regression: y = a*x + b  (x = index, y = close)
      const n = inRange.length;
      const xs = inRange.map((_, i) => i);
      const ys = inRange.map(c => c.close);
      const sumX = xs.reduce((s, x) => s + x, 0);
      const sumY = ys.reduce((s, y) => s + y, 0);
      const sumXY = xs.reduce((s, x, i) => s + x * ys[i]!, 0);
      const sumXX = xs.reduce((s, x) => s + x * x, 0);
      const slope = (n * sumXY - sumX * sumY) / (n * sumXX - sumX * sumX);
      const intercept = (sumY - slope * sumX) / n;

      // Standard deviation of residuals
      const residuals = ys.map((y, i) => y - (slope * i + intercept));
      const stdDev = Math.sqrt(residuals.reduce((s, r) => s + r * r, 0) / n);

      // Build regression screen points
      const series = this.getMainSeries();
      const priceToY = (price: number): number | null => {
        const y = series ? (series as unknown as { priceToCoordinate?: (val: number) => number }).priceToCoordinate?.(price) : null;
        return (y != null && Number.isFinite(y)) ? y : null;
      };

      // Endpoints for each channel line
      const startX = Math.min(p1.x, p2.x);
      const endX   = Math.max(p1.x, p2.x);
      const regrAt = (i: number) => slope * i + intercept;

      const midY1 = priceToY(regrAt(0));
      const midY2 = priceToY(regrAt(n - 1));
      const topY1 = priceToY(regrAt(0) + stdDev);
      const topY2 = priceToY(regrAt(n - 1) + stdDev);
      const botY1 = priceToY(regrAt(0) - stdDev);
      const botY2 = priceToY(regrAt(n - 1) - stdDev);

      this.ctx.save();
      const drawLine = (x1: number, y1: number | null, x2: number, y2: number | null, dash: number[], color: string) => {
        if (y1 == null || y2 == null) return;
        this.ctx.strokeStyle = color;
        this.ctx.lineWidth = 1.5;
        this.ctx.setLineDash(dash);
        this.ctx.beginPath();
        this.ctx.moveTo(x1, y1);
        this.ctx.lineTo(x2, y2);
        this.ctx.stroke();
      };

      drawLine(startX, topY1, endX, topY2, [4, 3], drawing.style.color + '99');
      drawLine(startX, midY1, endX, midY2, [], drawing.style.color);
      drawLine(startX, botY1, endX, botY2, [4, 3], drawing.style.color + '99');

      // Fill between channels
      if (topY1 != null && topY2 != null && botY1 != null && botY2 != null) {
        this.ctx.globalAlpha = 0.07;
        this.ctx.fillStyle = drawing.style.color;
        this.ctx.beginPath();
        this.ctx.moveTo(startX, topY1);
        this.ctx.lineTo(endX, topY2);
        this.ctx.lineTo(endX, botY2);
        this.ctx.lineTo(startX, botY1);
        this.ctx.closePath();
        this.ctx.fill();
        this.ctx.globalAlpha = 1;
      }

      if (isSelected) { this.drawHandle(p1.x, p1.y); this.drawHandle(p2.x, p2.y); }
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
        <button class="ctrl-btn drawing-tool-btn" data-drawing-tool="measure" title="Ölçüm Aracı"><svg class="icon-svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path><polyline points="3.27 6.96 12 12.01 20.73 6.96"></polyline><line x1="12" y1="22.08" x2="12" y2="12"></line></svg></button>
        <button class="ctrl-btn drawing-clear-btn" id="drawing-clear-btn" title="Tüm çizimleri sil"><svg class="icon-svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/><path d="M10 11v6M14 11v6"/></svg></button>
      </div>
      <div class="ctrl-group">
        <span class="ctrl-label">İleri</span>
        <button class="ctrl-btn drawing-tool-btn" data-drawing-tool="fibonacci" title="Fibonacci Düzeltme (iki nokta)">Fib</button>
        <button class="ctrl-btn drawing-tool-btn" data-drawing-tool="fibonacci_ext" title="Fibonacci Uzantı (iki nokta)">FibX</button>
        <button class="ctrl-btn drawing-tool-btn" data-drawing-tool="regression" title="Regresyon Kanalı (iki nokta)">Reg</button>
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
