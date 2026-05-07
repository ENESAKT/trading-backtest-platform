/* PiyasaPilot — shared components & icons */

const { useState, useEffect, useRef, useMemo } = React;

// ===== ICONS (minimal line icons) =====
const Icon = {
  star: (p) => <svg viewBox="0 0 16 16" width="11" height="11" fill="currentColor" {...p}><path d="M8 1.5l1.9 4.3 4.6.4-3.5 3.1 1 4.6L8 11.6 3.9 13.9l1-4.6L1.5 6.2l4.6-.4z"/></svg>,
  chev: (p) => <svg viewBox="0 0 12 12" width="10" height="10" fill="none" stroke="currentColor" strokeWidth="1.5" {...p}><path d="M3 4.5L6 7.5L9 4.5"/></svg>,
  search: (p) => <svg viewBox="0 0 16 16" width="12" height="12" fill="none" stroke="currentColor" strokeWidth="1.5" {...p}><circle cx="7" cy="7" r="5"/><path d="M11 11l3 3"/></svg>,
  x: (p) => <svg viewBox="0 0 12 12" width="10" height="10" fill="none" stroke="currentColor" strokeWidth="1.5" {...p}><path d="M2 2l8 8M10 2l-8 8"/></svg>,
  plus: (p) => <svg viewBox="0 0 12 12" width="10" height="10" fill="none" stroke="currentColor" strokeWidth="1.5" {...p}><path d="M6 1v10M1 6h10"/></svg>,
  more: (p) => <svg viewBox="0 0 12 12" width="12" height="12" fill="currentColor" {...p}><circle cx="3" cy="6" r="1"/><circle cx="6" cy="6" r="1"/><circle cx="9" cy="6" r="1"/></svg>,
  expand: (p) => <svg viewBox="0 0 12 12" width="10" height="10" fill="none" stroke="currentColor" strokeWidth="1.5" {...p}><path d="M2 5V2h3M10 7v3H7M2 7v3h3M10 5V2H7"/></svg>,
  download: (p) => <svg viewBox="0 0 12 12" width="10" height="10" fill="none" stroke="currentColor" strokeWidth="1.5" {...p}><path d="M6 1v8M3 6l3 3 3-3M1 11h10"/></svg>,
  play: (p) => <svg viewBox="0 0 12 12" width="10" height="10" fill="currentColor" {...p}><path d="M3 2l7 4-7 4z"/></svg>,
  pause: (p) => <svg viewBox="0 0 12 12" width="10" height="10" fill="currentColor" {...p}><rect x="3" y="2" width="2" height="8"/><rect x="7" y="2" width="2" height="8"/></svg>,
  zap: (p) => <svg viewBox="0 0 12 12" width="11" height="11" fill="currentColor" {...p}><path d="M7 1L2 7h3l-1 4 5-6H6z"/></svg>,
  settings: (p) => <svg viewBox="0 0 12 12" width="11" height="11" fill="none" stroke="currentColor" strokeWidth="1.4" {...p}><circle cx="6" cy="6" r="1.5"/><path d="M6 1v1.5M6 9.5V11M1 6h1.5M9.5 6H11M2.5 2.5l1 1M8.5 8.5l1 1M2.5 9.5l1-1M8.5 3.5l1-1"/></svg>,
  refresh: (p) => <svg viewBox="0 0 12 12" width="11" height="11" fill="none" stroke="currentColor" strokeWidth="1.4" {...p}><path d="M2 6a4 4 0 016.5-3M10 6a4 4 0 01-6.5 3M9 1v3H6M3 11V8h3"/></svg>,
};

// ===== LOGO =====
function Logo({ size = 22 }) {
  return (
    <svg viewBox="0 0 24 24" width={size} height={size} aria-label="PiyasaPilot">
      {/* Cube/pilot mark — angular P */}
      <rect x="1" y="1" width="22" height="22" fill="none" stroke="var(--amber)" strokeWidth="1.4"/>
      <path d="M5 5 H13 a4 4 0 0 1 0 8 H5 V19 H8 V13 H13 a4 4 0 0 0 0 -8 H5 Z" fill="var(--amber)"/>
      <circle cx="17" cy="17" r="2" fill="var(--cyan)"/>
    </svg>
  );
}

// ===== TICKER STRIP =====
function Ticker() {
  const items = [...TICKER, ...TICKER]; // double for seamless loop
  const [time, setTime] = useState(new Date());
  useEffect(() => {
    const id = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(id);
  }, []);
  const t = time.toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  return (
    <div className="ticker">
      <div className="ticker-label">⚡ Canlı Piyasa</div>
      <div className="ticker-track">
        {items.map((it, i) => (
          <div className="tk-item" key={i}>
            <span className="tk-sym">{it.sym}</span>
            <span className="tk-px">{it.px}</span>
            <span className={`tk-chg ${it.dir}`}>{it.chg}</span>
          </div>
        ))}
      </div>
      <div className="ticker-clock">
        <span className="live"><i className="live-dot"/> CANLI</span>
        <span>İST {t}</span>
        <span style={{color: 'var(--fg-3)'}}>•</span>
        <span>BIST AÇIK</span>
      </div>
    </div>
  );
}

// ===== TOPNAV =====
function TopNav({ active, onChange, theme, onTheme, density, onDensity, compact, onCompact, onTweaksOpen, tweaksOn }) {
  return (
    <div className="topnav">
      <div className="brand">
        <Logo size={22}/>
        <div>
          <div className="brand-name">Piyasa<span>Pilot</span></div>
        </div>
        <div className="brand-meta">v2.4</div>
      </div>
      <div className="nav-tabs">
        {NAV_TABS.map(t => (
          <button key={t.id} className={`nav-tab ${active === t.id ? 'active' : ''}`} onClick={() => onChange(t.id)}>
            <span className="tab-num">{t.code}</span>
            <span>{t.label}</span>
          </button>
        ))}
      </div>
      <div className="nav-right">
        <button className="nav-tool" onClick={onTheme}>
          {theme === 'dark' ? '◐' : '◑'} {theme === 'dark' ? 'Karanlık' : 'Aydınlık'}
        </button>
        <button className="nav-tool" onClick={onDensity}>
          ☰ {density.toUpperCase()}
        </button>
        <button className="nav-tool" onClick={onCompact}>
          {compact ? '◰' : '◳'} {compact ? 'Kompakt' : 'Geniş'}
        </button>
      </div>
    </div>
  );
}

// ===== SIDEBAR =====
function Sidebar({ activeSym, onSelect }) {
  const [q, setQ] = useState('');
  const [favOpen, setFavOpen] = useState(true);
  const cats = [
    { id: 'bist30', label: 'BIST 30',     dot: 'var(--amber)' },
    { id: 'bist100', label: 'BIST 100',   dot: 'var(--down)' },
    { id: 'us', label: 'ABD Piyasaları',  dot: 'var(--cyan)' },
    { id: 'crypto', label: 'Kripto',      dot: 'var(--up)' },
    { id: 'fx', label: 'Döviz / Emtia',   dot: '#b78bff' },
    { id: 'viop', label: 'Vİ VİOP',       dot: '#ff6b9d' },
  ];
  return (
    <div className="sidebar">
      <div className="sidebar-search">
        <div className="sidebar-search-wrap">
          <input value={q} onChange={e => setQ(e.target.value)} placeholder="Sembol ara..." />
        </div>
      </div>
      <div className="sb-section">
        <div className="sb-header" onClick={() => setFavOpen(!favOpen)}>
          <span style={{display: 'flex', alignItems: 'center', gap: 6}}>
            <Icon.star style={{color: 'var(--amber)'}}/> Favoriler
          </span>
          <span className="count">{WATCHLIST.length}</span>
        </div>
        {favOpen && (
          <div className="watchlist">
            {WATCHLIST.map(w => (
              <div key={w.sym}
                   className={`watch-row ${activeSym === w.sym ? 'active' : ''}`}
                   onClick={() => onSelect && onSelect(w.sym)}>
                <span className="watch-star"><Icon.star style={{color: 'var(--amber)'}}/></span>
                <div className="watch-info">
                  <span className="watch-sym">{w.sym}</span>
                  <span className="watch-name">{w.name}</span>
                </div>
                <div className="watch-px">
                  <span className="watch-val">{w.px.toFixed(2)}</span>
                  <span className={`watch-chg ${w.chg > 0 ? 'up' : w.chg < 0 ? 'down' : 'flat'}`}>
                    {w.chg === 0 ? '—' : `${w.chg > 0 ? '+' : ''}${w.chg.toFixed(2)}%`}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
      <div className="sb-section">
        {cats.map(c => (
          <div key={c.id} className="sb-cat">
            <div className="sb-cat-label">
              <span className="sb-cat-mark" style={{ background: c.dot }}/>
              {c.label}
            </div>
            <span className="sb-cat-chev">▸</span>
          </div>
        ))}
      </div>
      <div style={{flex: 1}}/>
      <div style={{padding: '10px 12px', borderTop: '1px solid var(--line-2)', fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--fg-3)', textTransform: 'uppercase', letterSpacing: '0.08em', display: 'flex', justifyContent: 'space-between'}}>
        <span>WS bağlı</span>
        <span style={{color: 'var(--up)'}}>● 18ms</span>
      </div>
    </div>
  );
}

// ===== MICRO CHART HELPERS =====

// Sparkline
function Spark({ data, w = 80, h = 24, color = 'var(--amber)', fill }) {
  if (!data || data.length === 0) return null;
  const min = Math.min(...data), max = Math.max(...data);
  const r = max - min || 1;
  const pts = data.map((v, i) => `${(i / (data.length - 1)) * w},${h - ((v - min) / r) * h}`).join(' ');
  return (
    <svg width={w} height={h} className="spark">
      {fill && <polygon points={`0,${h} ${pts} ${w},${h}`} fill={fill} opacity="0.2"/>}
      <polyline points={pts} fill="none" stroke={color} strokeWidth="1.2"/>
    </svg>
  );
}

// CANDLESTICK CHART (with EMA overlays + bollinger optional)
function CandleChart({ data, height = 360, showVolume = true, showBB = true, showEMA = true, levels = [], symbol = '', currency = '₺' }) {
  const wrapRef = useRef(null);
  const [w, setW] = useState(800);
  useEffect(() => {
    const ro = new ResizeObserver(([e]) => setW(e.contentRect.width));
    if (wrapRef.current) ro.observe(wrapRef.current);
    return () => ro.disconnect();
  }, []);

  const padL = 8, padR = 64, padT = 8, padB = showVolume ? 80 : 28;
  const priceH = height - padB - padT;
  const volH = showVolume ? 56 : 0;

  const min = Math.min(...data.map(c => c.low));
  const max = Math.max(...data.map(c => c.high));
  const range = max - min || 1;
  const candleW = Math.max(2, (w - padL - padR) / data.length * 0.7);
  const stride = (w - padL - padR) / data.length;

  // EMA
  const ema = (arr, period) => {
    const k = 2 / (period + 1);
    const out = [];
    let prev = arr[0].close;
    arr.forEach((c, i) => {
      const v = i === 0 ? c.close : c.close * k + prev * (1 - k);
      out.push(v); prev = v;
    });
    return out;
  };
  const ema20 = useMemo(() => ema(data, 20), [data]);
  const ema50 = useMemo(() => ema(data, 50), [data]);
  const ema200 = useMemo(() => ema(data, 200), [data]);

  // Bollinger 20,2
  const bb = useMemo(() => {
    const period = 20, mult = 2;
    return data.map((_, i) => {
      const s = Math.max(0, i - period + 1);
      const slice = data.slice(s, i + 1).map(c => c.close);
      const mean = slice.reduce((a, b) => a + b, 0) / slice.length;
      const variance = slice.reduce((a, b) => a + (b - mean) ** 2, 0) / slice.length;
      const std = Math.sqrt(variance);
      return { up: mean + std * mult, mid: mean, lo: mean - std * mult };
    });
  }, [data]);

  const yPx = (v) => padT + ((max - v) / range) * priceH;
  const xPx = (i) => padL + i * stride + stride / 2;

  const last = data[data.length - 1];
  const prev = data[data.length - 2];
  const lastChg = last.close - prev.close;
  const lastChgPct = (lastChg / prev.close) * 100;

  // Volume
  const maxVol = Math.max(...data.map(c => c.volume));
  const volTop = priceH + padT + 12;

  // Y-axis ticks
  const tickCount = 6;
  const ticks = Array.from({ length: tickCount + 1 }, (_, i) => min + (range / tickCount) * i);

  // Time labels (months)
  const months = ['Tem','Ağu','Eyl','Eki','Kas','Ara','2026','Şub','Mar'];

  return (
    <div ref={wrapRef} className="chart-wrap" style={{ height }}>
      <svg width={w} height={height} style={{ display: 'block' }}>
        <defs>
          <pattern id="grid" width="80" height="40" patternUnits="userSpaceOnUse">
            <path d="M 80 0 L 0 0 0 40" fill="none" stroke="var(--line-1)" strokeWidth="1"/>
          </pattern>
        </defs>
        <rect x={padL} y={padT} width={w - padL - padR} height={priceH} fill="url(#grid)"/>

        {/* Y axis grid lines + labels */}
        {ticks.map((t, i) => (
          <g key={i}>
            <line x1={padL} y1={yPx(t)} x2={w - padR} y2={yPx(t)} stroke="var(--line-1)" strokeDasharray="2 4" opacity="0.5"/>
            <text x={w - padR + 6} y={yPx(t) + 3} fill="var(--fg-3)" fontSize="10" fontFamily="var(--font-mono)">{t.toFixed(2)}</text>
          </g>
        ))}

        {/* Bollinger fill */}
        {showBB && (
          <>
            <path d={`M ${bb.map((b, i) => `${xPx(i)},${yPx(b.up)}`).join(' L ')} L ${bb.map((b, i) => `${xPx(data.length - 1 - i)},${yPx(bb[data.length - 1 - i].lo)}`).join(' L ')} Z`}
                  fill="var(--cyan-bg)" opacity="0.5"/>
            <polyline points={bb.map((b, i) => `${xPx(i)},${yPx(b.up)}`).join(' ')} fill="none" stroke="var(--cyan-dim)" strokeWidth="1" strokeDasharray="2 3" opacity="0.7"/>
            <polyline points={bb.map((b, i) => `${xPx(i)},${yPx(b.lo)}`).join(' ')} fill="none" stroke="var(--cyan-dim)" strokeWidth="1" strokeDasharray="2 3" opacity="0.7"/>
          </>
        )}

        {/* Candles */}
        {data.map((c, i) => {
          const up = c.close >= c.open;
          const x = xPx(i);
          const yO = yPx(c.open), yC = yPx(c.close), yH = yPx(c.high), yL = yPx(c.low);
          const top = Math.min(yO, yC), h = Math.max(1, Math.abs(yC - yO));
          const color = up ? 'var(--up)' : 'var(--down)';
          return (
            <g key={i}>
              <line x1={x} x2={x} y1={yH} y2={yL} stroke={color} strokeWidth="1"/>
              <rect x={x - candleW/2} y={top} width={candleW} height={h} fill={color}/>
            </g>
          );
        })}

        {/* EMA lines */}
        {showEMA && (
          <>
            <polyline points={ema20.map((v, i) => `${xPx(i)},${yPx(v)}`).join(' ')} fill="none" stroke="#b78bff" strokeWidth="1.2" opacity="0.85"/>
            <polyline points={ema50.map((v, i) => `${xPx(i)},${yPx(v)}`).join(' ')} fill="none" stroke="var(--amber)" strokeWidth="1.2" opacity="0.85"/>
            <polyline points={ema200.map((v, i) => `${xPx(i)},${yPx(v)}`).join(' ')} fill="none" stroke="var(--cyan)" strokeWidth="1.2" opacity="0.7"/>
          </>
        )}

        {/* Levels */}
        {levels.map((lv, i) => (
          <g key={i}>
            <line x1={padL} y1={yPx(lv.v)} x2={w - padR} y2={yPx(lv.v)} stroke={lv.color || 'var(--fg-3)'} strokeWidth="0.8" strokeDasharray="3 3" opacity="0.85"/>
            <rect x={w - padR + 1} y={yPx(lv.v) - 7} width={56} height={14} fill={lv.color || 'var(--fg-3)'}/>
            <text x={w - padR + 5} y={yPx(lv.v) + 3} fontSize="9" fontFamily="var(--font-mono)" fill="#0a0c10" fontWeight="700">{lv.label}</text>
          </g>
        ))}

        {/* Last price marker */}
        <g>
          <line x1={padL} y1={yPx(last.close)} x2={w - padR} y2={yPx(last.close)} stroke="var(--amber)" strokeWidth="1" strokeDasharray="2 3" opacity="0.6"/>
          <rect x={w - padR + 1} y={yPx(last.close) - 8} width={62} height={16} fill="var(--amber)"/>
          <text x={w - padR + 5} y={yPx(last.close) + 4} fontSize="10" fontFamily="var(--font-mono)" fill="#0a0c10" fontWeight="700">{last.close.toFixed(2)}</text>
        </g>

        {/* Volume */}
        {showVolume && (
          <g>
            <line x1={padL} y1={volTop} x2={w - padR} y2={volTop} stroke="var(--line-2)"/>
            {data.map((c, i) => {
              const up = c.close >= c.open;
              const h = Math.max(1, (c.volume / maxVol) * volH);
              const x = xPx(i);
              return (
                <rect key={i} x={x - candleW/2} y={volTop + (volH - h)} width={candleW} height={h}
                      fill={up ? 'var(--up)' : 'var(--down)'} opacity="0.55"/>
              );
            })}
            <text x={padL + 4} y={volTop + 10} fontSize="9" fontFamily="var(--font-mono)" fill="var(--fg-3)">VOL</text>
          </g>
        )}

        {/* X-axis months */}
        {months.map((m, i) => {
          const x = padL + (i / (months.length - 1)) * (w - padL - padR);
          return <text key={m} x={x} y={height - 6} fontSize="10" fontFamily="var(--font-mono)" fill="var(--fg-3)" textAnchor="middle">{m}</text>;
        })}
      </svg>

      {/* Floating OHLC readout */}
      <div style={{ position: 'absolute', top: 8, left: 12, fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--fg-1)', display: 'flex', gap: 12, pointerEvents: 'none' }}>
        <span><span style={{color: 'var(--fg-3)'}}>O</span> {data[data.length-1].open.toFixed(2)}</span>
        <span><span style={{color: 'var(--fg-3)'}}>H</span> {data[data.length-1].high.toFixed(2)}</span>
        <span><span style={{color: 'var(--fg-3)'}}>L</span> {data[data.length-1].low.toFixed(2)}</span>
        <span><span style={{color: 'var(--fg-3)'}}>C</span> {data[data.length-1].close.toFixed(2)}</span>
        <span className={lastChg >= 0 ? 'tk-chg up' : 'tk-chg down'}>
          {lastChg >= 0 ? '+' : ''}{lastChg.toFixed(2)} ({lastChgPct >= 0 ? '+' : ''}{lastChgPct.toFixed(2)}%)
        </span>
      </div>
      {/* Indicator legend */}
      {showEMA && (
        <div style={{ position: 'absolute', top: 28, left: 12, fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--fg-2)', display: 'flex', gap: 10, textTransform: 'uppercase', letterSpacing: '0.06em', pointerEvents: 'none' }}>
          <span><span style={{color: '#b78bff'}}>━</span> EMA 20</span>
          <span><span style={{color: 'var(--amber)'}}>━</span> EMA 50</span>
          <span><span style={{color: 'var(--cyan)'}}>━</span> EMA 200</span>
          {showBB && <span><span style={{color: 'var(--cyan-dim)'}}>┄</span> BB(20,2)</span>}
        </div>
      )}
    </div>
  );
}

// RSI sub-chart
function RSIChart({ data, height = 70 }) {
  const wrapRef = useRef(null);
  const [w, setW] = useState(800);
  useEffect(() => {
    const ro = new ResizeObserver(([e]) => setW(e.contentRect.width));
    if (wrapRef.current) ro.observe(wrapRef.current);
    return () => ro.disconnect();
  }, []);

  // RSI(14)
  const rsi = useMemo(() => {
    const period = 14, out = [50];
    let avgG = 0, avgL = 0;
    for (let i = 1; i < data.length; i++) {
      const ch = data[i].close - data[i-1].close;
      const g = ch > 0 ? ch : 0, l = ch < 0 ? -ch : 0;
      if (i <= period) {
        avgG = (avgG * (i-1) + g) / i;
        avgL = (avgL * (i-1) + l) / i;
      } else {
        avgG = (avgG * (period - 1) + g) / period;
        avgL = (avgL * (period - 1) + l) / period;
      }
      const rs = avgL === 0 ? 100 : avgG / avgL;
      out.push(100 - 100 / (1 + rs));
    }
    return out;
  }, [data]);

  const padL = 8, padR = 64;
  const yPx = v => 4 + (1 - v / 100) * (height - 8);
  const xPx = i => padL + (i / (data.length - 1)) * (w - padL - padR);
  const pts = rsi.map((v, i) => `${xPx(i)},${yPx(v)}`).join(' ');
  const last = rsi[rsi.length - 1];

  return (
    <div ref={wrapRef} style={{ width: '100%', height, background: 'var(--bg-1)', borderTop: '1px solid var(--line-2)', position: 'relative' }}>
      <svg width={w} height={height}>
        <line x1={padL} y1={yPx(70)} x2={w - padR} y2={yPx(70)} stroke="var(--down-dim)" strokeDasharray="2 3" opacity="0.5"/>
        <line x1={padL} y1={yPx(30)} x2={w - padR} y2={yPx(30)} stroke="var(--up-dim)" strokeDasharray="2 3" opacity="0.5"/>
        <line x1={padL} y1={yPx(50)} x2={w - padR} y2={yPx(50)} stroke="var(--line-2)" opacity="0.5"/>
        <polyline points={pts} fill="none" stroke="#b78bff" strokeWidth="1.2"/>
        <text x={w - padR + 6} y={yPx(70) + 3} fontSize="9" fontFamily="var(--font-mono)" fill="var(--down)">70.00</text>
        <text x={w - padR + 6} y={yPx(30) + 3} fontSize="9" fontFamily="var(--font-mono)" fill="var(--up)">30.00</text>
        <rect x={w - padR + 1} y={yPx(last) - 7} width={42} height={14} fill="#b78bff"/>
        <text x={w - padR + 4} y={yPx(last) + 3} fontSize="10" fontFamily="var(--font-mono)" fill="#0a0c10" fontWeight="700">{last.toFixed(2)}</text>
      </svg>
      <div style={{ position: 'absolute', top: 6, left: 12, fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--fg-2)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
        RSI(14) <span style={{color: '#b78bff', marginLeft: 6}}>{last.toFixed(2)}</span>
      </div>
    </div>
  );
}

// Equity curve / line chart
function LineChart({ data, height = 220, color = 'var(--up)', fill = true, label, formatY = v => v.toFixed(0), inverted = false, gridY = 5 }) {
  const wrapRef = useRef(null);
  const [w, setW] = useState(600);
  useEffect(() => {
    const ro = new ResizeObserver(([e]) => setW(e.contentRect.width));
    if (wrapRef.current) ro.observe(wrapRef.current);
    return () => ro.disconnect();
  }, []);

  const padL = 50, padR = 16, padT = 12, padB = 22;
  const min = Math.min(...data), max = Math.max(...data);
  const range = max - min || 1;
  const yPx = v => padT + (1 - (v - min) / range) * (height - padT - padB);
  const xPx = i => padL + (i / (data.length - 1)) * (w - padL - padR);
  const pts = data.map((v, i) => `${xPx(i)},${yPx(v)}`).join(' ');

  const ticks = Array.from({ length: gridY + 1 }, (_, i) => min + (range / gridY) * i);

  return (
    <div ref={wrapRef} style={{ width: '100%', height, position: 'relative' }}>
      <svg width={w} height={height} style={{ display: 'block' }}>
        {ticks.map((t, i) => (
          <g key={i}>
            <line x1={padL} y1={yPx(t)} x2={w - padR} y2={yPx(t)} stroke="var(--line-1)" strokeDasharray="2 3" opacity="0.6"/>
            <text x={padL - 4} y={yPx(t) + 3} fontSize="9" fontFamily="var(--font-mono)" fill="var(--fg-3)" textAnchor="end">{formatY(t)}</text>
          </g>
        ))}
        {fill && (
          <polygon
            points={`${padL},${height - padB} ${pts} ${w - padR},${height - padB}`}
            fill={color} opacity="0.15"
          />
        )}
        <polyline points={pts} fill="none" stroke={color} strokeWidth="1.5"/>
      </svg>
      {label && (
        <div style={{ position: 'absolute', top: 6, left: padL + 4, fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--fg-2)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
          {label}
        </div>
      )}
    </div>
  );
}

// MACD-like histogram
function HistChart({ data, height = 60 }) {
  const wrapRef = useRef(null);
  const [w, setW] = useState(600);
  useEffect(() => {
    const ro = new ResizeObserver(([e]) => setW(e.contentRect.width));
    if (wrapRef.current) ro.observe(wrapRef.current);
    return () => ro.disconnect();
  }, []);

  // build a fake MACD histogram from candle deltas
  const series = data.map((c, i) => i === 0 ? 0 : (c.close - data[i-1].close) * 0.6);
  const maxAbs = Math.max(...series.map(v => Math.abs(v))) || 1;
  const padL = 8, padR = 64;
  const yMid = height / 2;
  const yPx = v => yMid - (v / maxAbs) * (height / 2 - 4);
  const stride = (w - padL - padR) / data.length;
  const last = series[series.length - 1];

  return (
    <div ref={wrapRef} style={{ width: '100%', height, background: 'var(--bg-1)', borderTop: '1px solid var(--line-2)', position: 'relative' }}>
      <svg width={w} height={height}>
        <line x1={padL} y1={yMid} x2={w - padR} y2={yMid} stroke="var(--line-2)"/>
        {series.map((v, i) => {
          const x = padL + i * stride + stride / 2;
          const h = Math.abs(v / maxAbs) * (height / 2 - 4);
          const up = v >= 0;
          return <rect key={i} x={x - stride * 0.35} y={up ? yMid - h : yMid} width={Math.max(1, stride * 0.7)} height={h}
                       fill={up ? 'var(--up)' : 'var(--down)'} opacity="0.85"/>;
        })}
        <rect x={w - padR + 1} y={yPx(last) - 7} width={42} height={14} fill={last >= 0 ? 'var(--up)' : 'var(--down)'}/>
        <text x={w - padR + 4} y={yPx(last) + 3} fontSize="10" fontFamily="var(--font-mono)" fill="#0a0c10" fontWeight="700">{last.toFixed(2)}</text>
      </svg>
      <div style={{ position: 'absolute', top: 6, left: 12, fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--fg-2)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
        MACD(12,26,9) <span style={{color: last >= 0 ? 'var(--up)' : 'var(--down)', marginLeft: 6}}>{last.toFixed(3)}</span>
      </div>
    </div>
  );
}

// Drawdown bar/line
function DrawdownChart({ data, height = 160 }) {
  const wrapRef = useRef(null);
  const [w, setW] = useState(600);
  useEffect(() => {
    const ro = new ResizeObserver(([e]) => setW(e.contentRect.width));
    if (wrapRef.current) ro.observe(wrapRef.current);
    return () => ro.disconnect();
  }, []);

  const padL = 50, padR = 16, padT = 12, padB = 22;
  const min = Math.min(...data); // most negative
  const max = 0;
  const range = max - min || 1;
  const yPx = v => padT + (1 - (v - min) / range) * (height - padT - padB);
  const xPx = i => padL + (i / (data.length - 1)) * (w - padL - padR);
  const pts = data.map((v, i) => `${xPx(i)},${yPx(v)}`).join(' ');
  const ticks = [0, -25, -50, -75, -100];

  return (
    <div ref={wrapRef} style={{ width: '100%', height, position: 'relative' }}>
      <svg width={w} height={height} style={{ display: 'block' }}>
        {ticks.map((t, i) => (
          <g key={i}>
            <line x1={padL} y1={yPx(t)} x2={w - padR} y2={yPx(t)} stroke="var(--line-1)" strokeDasharray="2 3" opacity="0.6"/>
            <text x={padL - 4} y={yPx(t) + 3} fontSize="9" fontFamily="var(--font-mono)" fill="var(--fg-3)" textAnchor="end">{t}%</text>
          </g>
        ))}
        <polygon points={`${padL},${yPx(0)} ${pts} ${w - padR},${yPx(0)}`} fill="var(--down)" opacity="0.18"/>
        <polyline points={pts} fill="none" stroke="var(--down)" strokeWidth="1.5"/>
      </svg>
    </div>
  );
}

Object.assign(window, { Icon, Logo, Ticker, TopNav, Sidebar, Spark, CandleChart, RSIChart, LineChart, HistChart, DrawdownChart });
