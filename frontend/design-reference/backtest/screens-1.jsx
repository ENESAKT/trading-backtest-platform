/* PiyasaPilot — Screens (Grafik, Portföy, Strateji) */

const { useState: useStateS } = React;

// ============== GRAFİK ==============
function GrafikScreen({ activeSym }) {
  const [view, setView] = useStateS('single'); // single | quad
  const [tf, setTf] = useStateS('1G');
  const [showBB, setShowBB] = useStateS(true);
  const [showEMA, setShowEMA] = useStateS(true);

  const symData = {
    VAKBN: { data: CANDLES_VAKBN, name: 'Vakıfbank' },
    AKBNK: { data: CANDLES_AKBNK, name: 'Akbank' },
    ARCLK: { data: CANDLES_ARCLK, name: 'Arçelik' },
    ASELS: { data: CANDLES_ASELS, name: 'Aselsan' },
  };
  const cur = symData[activeSym] || symData.VAKBN;

  const tfs = ['1d', '5d', '1S', '15d', '1A', '3A', '6A', '1Y', '5Y'];
  const indicators = ['EMA(20,50,200)', 'BB(20,2)', 'RSI(14)', 'MACD(12,26,9)', 'VOL'];

  const levels = [
    { v: cur.data[cur.data.length-1].high * 1.05, label: 'TAVAN', color: '#b78bff' },
    { v: cur.data[cur.data.length-1].close * 1.04, label: 'SAT 28.77', color: 'var(--down)' },
    { v: cur.data[cur.data.length-1].close, label: cur.data[cur.data.length-1].close.toFixed(2), color: 'var(--amber)' },
    { v: cur.data[cur.data.length-1].close * 0.96, label: 'AL 27.09', color: 'var(--up)' },
    { v: cur.data[cur.data.length-1].low * 0.92, label: 'TABAN', color: 'var(--cyan)' },
  ];

  return (
    <div className="screen" style={{display: 'flex', flexDirection: 'column'}}>
      {/* Sub-toolbar */}
      <div className="subbar">
        <div className="subbar-group">
          <span className="subbar-label">Sembol</span>
          <span className="subbar-value">{activeSym} <span className="chev">▾</span></span>
          <span className="dim" style={{fontFamily: 'var(--font-mono)', fontSize: 11}}>{cur.name}</span>
        </div>
        <div className="subbar-group">
          <span className="subbar-label">Periyot</span>
          {tfs.map(t => (
            <button key={t} className={`subbar-btn ${tf === t ? 'active' : ''}`} onClick={() => setTf(t)}>{t}</button>
          ))}
        </div>
        <div className="subbar-group">
          <span className="subbar-label">İndikatör</span>
          <button className={`subbar-btn ${showEMA ? 'active' : ''}`} onClick={() => setShowEMA(!showEMA)}>EMA</button>
          <button className={`subbar-btn ${showBB ? 'active' : ''}`} onClick={() => setShowBB(!showBB)}>BB</button>
          <button className="subbar-btn">+ Ekle</button>
        </div>
        <div className="subbar-group">
          <span className="subbar-label">Görünüm</span>
          <button className={`subbar-btn ${view === 'single' ? 'active' : ''}`} onClick={() => setView('single')}>▭ Tek</button>
          <button className={`subbar-btn ${view === 'quad' ? 'active' : ''}`} onClick={() => setView('quad')}>⊞ 2×2</button>
        </div>
        <div className="subbar-spacer"/>
        <div className="subbar-group">
          <button className="subbar-btn"><Icon.refresh/> Senkr.</button>
          <button className="subbar-btn">⌘ Çiz</button>
          <button className="subbar-btn">📊 Şablon</button>
          <button className="subbar-btn"><Icon.expand/> Tam</button>
        </div>
      </div>

      {view === 'single' ? (
        <SingleChartView data={cur.data} symbol={activeSym} name={cur.name}
                         showBB={showBB} showEMA={showEMA} levels={levels}/>
      ) : (
        <QuadChartView/>
      )}
    </div>
  );
}

function SingleChartView({ data, symbol, name, showBB, showEMA, levels }) {
  const last = data[data.length - 1];
  const prev = data[data.length - 2];
  const chg = last.close - prev.close;
  const chgPct = (chg / prev.close) * 100;

  return (
    <div style={{ flex: 1, display: 'grid', gridTemplateColumns: '1fr 280px', overflow: 'hidden' }}>
      <div style={{display: 'flex', flexDirection: 'column', overflow: 'hidden'}}>
        {/* Symbol header strip */}
        <div style={{ padding: '12px 16px', borderBottom: '1px solid var(--line-2)', display: 'flex', alignItems: 'baseline', gap: 16, background: 'var(--bg-1)' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
              <span style={{ fontFamily: 'var(--font-display)', fontSize: 22, fontWeight: 700, letterSpacing: '-0.02em' }}>{symbol}</span>
              <span className="dim" style={{fontSize: 12}}>{name} • IST</span>
              <span className="tag amber">BIST 30</span>
            </div>
          </div>
          <div style={{display: 'flex', gap: 24, alignItems: 'baseline', marginLeft: 'auto'}}>
            <div style={{display: 'flex', flexDirection: 'column', alignItems: 'flex-end'}}>
              <span className="label">Son</span>
              <span className="mono tnum" style={{fontSize: 24, fontWeight: 600}}>₺{last.close.toFixed(2)}</span>
            </div>
            <div style={{display: 'flex', flexDirection: 'column', alignItems: 'flex-end'}}>
              <span className="label">Değişim</span>
              <span className={`mono tnum ${chg >= 0 ? 'tk-chg up' : 'tk-chg down'}`} style={{fontSize: 16, fontWeight: 600}}>
                {chg >= 0 ? '+' : ''}{chg.toFixed(2)}  ({chgPct >= 0 ? '+' : ''}{chgPct.toFixed(2)}%)
              </span>
            </div>
            <div style={{display: 'flex', flexDirection: 'column', alignItems: 'flex-end'}}>
              <span className="label">Hacim</span>
              <span className="mono tnum" style={{fontSize: 13}}>72.8M</span>
            </div>
            <div style={{display: 'flex', flexDirection: 'column', alignItems: 'flex-end'}}>
              <span className="label">Piyasa Değeri</span>
              <span className="mono tnum" style={{fontSize: 13}}>₺218.4B</span>
            </div>
          </div>
        </div>

        <div style={{flex: 1, display: 'flex', flexDirection: 'column', overflow: 'auto'}}>
          <CandleChart data={data} height={400} showBB={showBB} showEMA={showEMA} levels={levels} symbol={symbol}/>
          <RSIChart data={data} height={70}/>
          <HistChart data={data} height={60}/>
        </div>
      </div>

      {/* Right rail */}
      <div style={{ borderLeft: '1px solid var(--line-2)', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        <div className="panel-head">
          <span className="panel-title">Emir Defteri <span className="badge">L2</span></span>
          <span className="dim" style={{fontFamily: 'var(--font-mono)', fontSize: 9, marginLeft: 'auto'}}>Spread: 0.02</span>
        </div>
        <div style={{flex: '0 0 auto', overflow: 'auto', maxHeight: 280}}>
          <table className="dt" style={{fontSize: 10}}>
            <thead>
              <tr><th style={{textAlign:'left'}}>Fiyat</th><th>Miktar</th><th>Toplam</th></tr>
            </thead>
            <tbody>
              {[
                { p: 31.78, q: 12420,  t: 394800,  side: 'sell' },
                { p: 31.74, q: 8420,   t: 267400,  side: 'sell' },
                { p: 31.72, q: 24800,  t: 786400,  side: 'sell' },
                { p: 31.70, q: 18420,  t: 583900,  side: 'sell' },
                { p: 31.68, q: 6240,   t: 197700,  side: 'sell' },
              ].map((r, i) => (
                <tr key={i}>
                  <td className="down" style={{position: 'relative'}}>
                    <span style={{position: 'absolute', right: 0, top: 0, bottom: 0, width: `${(r.q/24800)*100}%`, background: 'var(--down-bg)', zIndex: 0}}/>
                    <span style={{position: 'relative'}}>{r.p.toFixed(2)}</span>
                  </td>
                  <td>{r.q.toLocaleString('tr-TR')}</td>
                  <td className="dim">{(r.t/1000).toFixed(1)}K</td>
                </tr>
              ))}
              <tr style={{background: 'var(--bg-3)'}}>
                <td colSpan="3" style={{textAlign: 'center', padding: '8px'}}>
                  <span className="mono" style={{color: 'var(--amber)', fontSize: 13, fontWeight: 700}}>₺31.66</span>
                  <span className="dim" style={{marginLeft: 8, fontSize: 10}}>↑ 0.32</span>
                </td>
              </tr>
              {[
                { p: 31.66, q: 14820,  t: 469200,  side: 'buy' },
                { p: 31.64, q: 9620,   t: 304400,  side: 'buy' },
                { p: 31.62, q: 18240,  t: 576900,  side: 'buy' },
                { p: 31.60, q: 22480,  t: 710400,  side: 'buy' },
                { p: 31.58, q: 7220,   t: 228000,  side: 'buy' },
              ].map((r, i) => (
                <tr key={i}>
                  <td className="up" style={{position: 'relative'}}>
                    <span style={{position: 'absolute', right: 0, top: 0, bottom: 0, width: `${(r.q/24800)*100}%`, background: 'var(--up-bg)', zIndex: 0}}/>
                    <span style={{position: 'relative'}}>{r.p.toFixed(2)}</span>
                  </td>
                  <td>{r.q.toLocaleString('tr-TR')}</td>
                  <td className="dim">{(r.t/1000).toFixed(1)}K</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="panel-head">
          <span className="panel-title">Son İşlemler</span>
        </div>
        <div style={{overflow: 'auto', flex: 1}}>
          <table className="dt" style={{fontSize: 10}}>
            <thead><tr><th style={{textAlign:'left'}}>Saat</th><th>Fiyat</th><th>Miktar</th></tr></thead>
            <tbody>
              {[
                { t: '17:48:22', p: 31.66, q: 1240, dir: 'up' },
                { t: '17:48:18', p: 31.66, q: 480, dir: 'up' },
                { t: '17:48:14', p: 31.64, q: 2420, dir: 'down' },
                { t: '17:48:09', p: 31.66, q: 820, dir: 'up' },
                { t: '17:48:01', p: 31.64, q: 1640, dir: 'down' },
                { t: '17:47:54', p: 31.66, q: 320, dir: 'up' },
                { t: '17:47:48', p: 31.64, q: 4820, dir: 'down' },
                { t: '17:47:42', p: 31.66, q: 920, dir: 'up' },
                { t: '17:47:38', p: 31.68, q: 240, dir: 'up' },
                { t: '17:47:31', p: 31.66, q: 1820, dir: 'up' },
              ].map((r, i) => (
                <tr key={i}>
                  <td className="dim" style={{fontSize: 10}}>{r.t}</td>
                  <td className={r.dir}>{r.p.toFixed(2)}</td>
                  <td>{r.q.toLocaleString('tr-TR')}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function QuadChartView() {
  const cells = [
    { sym: 'VAKBN', name: 'Vakıfbank', data: CANDLES_VAKBN },
    { sym: 'AKBNK', name: 'Akbank',    data: CANDLES_AKBNK },
    { sym: 'ARCLK', name: 'Arçelik',   data: CANDLES_ARCLK },
    { sym: 'ASELS', name: 'Aselsan',   data: CANDLES_ASELS },
  ];
  return (
    <div style={{flex: 1, display: 'grid', gridTemplateColumns: '1fr 1fr', gridTemplateRows: '1fr 1fr', gap: 1, background: 'var(--line-2)', overflow: 'hidden'}}>
      {cells.map(c => {
        const last = c.data[c.data.length-1].close;
        const prev = c.data[c.data.length-2].close;
        const pct = ((last - prev) / prev) * 100;
        return (
          <div key={c.sym} style={{background: 'var(--bg-1)', display: 'flex', flexDirection: 'column', overflow: 'hidden'}}>
            <div className="panel-head">
              <span className="panel-title">{c.sym} <span className="dim" style={{fontWeight:400, marginLeft: 4}}>{c.name}</span></span>
              <span className={`mono ${pct >= 0 ? 'up' : 'down'}`} style={{marginLeft: 'auto', fontSize: 11, fontWeight: 600}}>
                ₺{last.toFixed(2)} {pct >= 0 ? '+' : ''}{pct.toFixed(2)}%
              </span>
              <button className="icon-btn" style={{marginLeft: 8, color: 'var(--fg-3)'}}><Icon.expand/></button>
            </div>
            <div style={{flex: 1, overflow: 'hidden'}}>
              <CandleChart data={c.data} height={300} showVolume={false} showBB={false}/>
            </div>
          </div>
        );
      })}
    </div>
  );
}

// ============== PORTFÖY ==============
function PortfoyScreen() {
  const totalEquity = WALLETS.reduce((s, w) => s + w.cash, 0);
  const totalPL = WALLETS.reduce((s, w) => s + w.pl, 0);
  const winning = WALLETS.filter(w => w.pl > 0).length;
  const winRate = (winning / WALLETS.length) * 100;
  const maxDD = Math.min(...DRAWDOWN);
  const profitFactor = 0.42;

  return (
    <div className="screen">
      {/* Hero stats */}
      <div className="stat-grid">
        <div className="stat">
          <div className="stat-label">Özkaynak <span className="info">ⓘ</span></div>
          <div className="stat-value">₺{totalEquity.toFixed(0).replace(/\B(?=(\d{3})+(?!\d))/g, ',')}</div>
          <div className="stat-sub"><span className="delta down">▼ -₺{Math.abs(totalPL).toFixed(0)}</span> bugün</div>
          <div style={{position: 'absolute', right: 12, top: 12}}>
            <Spark data={EQUITY} w={70} h={28} color="var(--down)" fill="var(--down)"/>
          </div>
        </div>
        <div className="stat">
          <div className="stat-label">Toplam K/Z</div>
          <div className={`stat-value ${totalPL < 0 ? 'down' : 'up'}`}>{totalPL < 0 ? '-' : '+'}₺{Math.abs(totalPL).toFixed(0).replace(/\B(?=(\d{3})+(?!\d))/g, ',')}</div>
          <div className="stat-sub"><span className="delta down">{((totalPL / 80000) * 100).toFixed(1)}%</span> tüm zaman</div>
        </div>
        <div className="stat">
          <div className="stat-label">Kazanma Oranı</div>
          <div className="stat-value amber">{winRate.toFixed(1)}<span style={{fontSize: 14, color: 'var(--fg-2)'}}>%</span></div>
          <div className="stat-sub">{winning}/{WALLETS.length} cüzdan kârda</div>
          <div style={{marginTop: 4}}>
            <div className="bar"><i style={{width: `${winRate}%`, background: 'var(--amber)'}}/></div>
          </div>
        </div>
        <div className="stat">
          <div className="stat-label">Kâr Faktörü</div>
          <div className="stat-value">{profitFactor.toFixed(2)}</div>
          <div className="stat-sub"><span style={{color: 'var(--down)'}}>● Kötü</span> &lt; 1.0 risk</div>
        </div>
        <div className="stat">
          <div className="stat-label">Maks. Çöküş</div>
          <div className="stat-value down">{maxDD.toFixed(1)}<span style={{fontSize: 14}}>%</span></div>
          <div className="stat-sub">Süre: <span className="mono" style={{color: 'var(--fg-1)'}}>87 gün</span></div>
        </div>
        <div className="stat">
          <div className="stat-label">Sharpe / Sortino</div>
          <div className="stat-value">-1.42 <span className="dim" style={{fontSize: 14}}>/ -1.84</span></div>
          <div className="stat-sub"><span className="delta down">● Kabul edilemez</span></div>
        </div>
      </div>

      {/* Wallets grid */}
      <div className="panel-head" style={{borderTop: 'none'}}>
        <span className="panel-title">Sanal Cüzdanlar <span className="badge">{WALLETS.length} aktif</span></span>
        <div style={{marginLeft: 'auto', display: 'flex', gap: 4}}>
          <button className="btn sm">+ Yeni Cüzdan</button>
          <button className="btn sm">⏸ Tümünü Dondur</button>
          <button className="btn sm">↻ Sıfırla</button>
        </div>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', borderBottom: '1px solid var(--line-2)' }}>
        {WALLETS.map(w => {
          const negative = w.pl < 0;
          return (
            <div key={w.name} style={{ padding: '12px 14px', borderRight: '1px solid var(--line-2)', borderBottom: '1px solid var(--line-2)', display: 'flex', flexDirection: 'column', gap: 8, background: 'var(--bg-1)', position: 'relative' }}>
              <div style={{display: 'flex', alignItems: 'center', justifyContent: 'space-between'}}>
                <div style={{display: 'flex', alignItems: 'center', gap: 6}}>
                  <span className="mono" style={{fontSize: 11, fontWeight: 700, color: 'var(--fg-0)'}}>{w.name}</span>
                  {w.state === 'live' ? <span className="tag up">● CANLI</span> : <span className="tag">PAUSED</span>}
                </div>
                <span className="mono dim" style={{fontSize: 9, fontWeight: 600}}>{w.today >= 0 ? '+' : ''}{w.today}</span>
              </div>
              <div>
                <div className="label">Nakit</div>
                <div className="mono tnum" style={{fontSize: 16, fontWeight: 600}}>₺{w.cash.toFixed(2)}</div>
              </div>
              <div>
                <div className="label">Toplam K/Z</div>
                <div className={`mono tnum ${negative ? 'tk-chg down' : 'tk-chg up'}`} style={{fontSize: 13, fontWeight: 600}}>
                  {negative ? '-' : '+'}₺{Math.abs(w.pl).toFixed(2)} <span style={{fontSize: 10}}>({w.plPct >= 0 ? '+' : ''}{w.plPct.toFixed(2)}%)</span>
                </div>
                <div className="bar" style={{marginTop: 4}}>
                  <i style={{width: `${Math.min(100, Math.abs(w.plPct))}%`, background: negative ? 'var(--down)' : 'var(--up)'}}/>
                </div>
              </div>
              <div style={{display: 'flex', gap: 4, marginTop: 'auto'}}>
                <button className="btn sm">{w.state === 'live' ? '⏸ Dondur' : '▶ Başlat'}</button>
                <button className="btn sm danger">↻ Sıfırla</button>
                <button className="btn sm ghost" style={{marginLeft: 'auto'}}><Icon.more/></button>
              </div>
            </div>
          );
        })}
      </div>

      {/* Charts row */}
      <div style={{display: 'grid', gridTemplateColumns: '1fr 1fr', borderBottom: '1px solid var(--line-2)'}}>
        <div style={{borderRight: '1px solid var(--line-2)'}}>
          <div className="panel-head">
            <span className="panel-title">Özkaynak Eğrisi</span>
            <div style={{marginLeft: 'auto', display: 'flex', gap: 4}}>
              <button className="subbar-btn">1A</button>
              <button className="subbar-btn active">3A</button>
              <button className="subbar-btn">6A</button>
              <button className="subbar-btn">YTD</button>
              <button className="subbar-btn">Tümü</button>
            </div>
          </div>
          <div style={{padding: 12}}>
            <LineChart data={EQUITY} height={220} color="var(--down)" formatY={v => `₺${(v/1000).toFixed(1)}K`}/>
          </div>
        </div>
        <div>
          <div className="panel-head">
            <span className="panel-title">Drawdown <span className="badge" style={{background: 'var(--down-bg)', color: 'var(--down)'}}>-99.0%</span></span>
            <div style={{marginLeft: 'auto', display: 'flex', gap: 4}}>
              <button className="subbar-btn">% Çöküş</button>
              <button className="subbar-btn active">Süre</button>
            </div>
          </div>
          <div style={{padding: 12}}>
            <DrawdownChart data={DRAWDOWN} height={220}/>
          </div>
        </div>
      </div>

      {/* Trade history */}
      <div className="panel-head">
        <span className="panel-title">İşlem Geçmişi <span className="badge">{TRADES.length} kayıt</span></span>
        <div style={{marginLeft: 'auto', display: 'flex', gap: 6, alignItems: 'center'}}>
          <input className="mono" placeholder="Filtrele..." style={{background: 'var(--bg-1)', border: '1px solid var(--line-2)', color: 'var(--fg-0)', padding: '4px 8px', fontSize: 10, width: 160}}/>
          <button className="btn sm"><Icon.download/> CSV</button>
        </div>
      </div>
      <table className="dt">
        <thead>
          <tr>
            <th className="sortable" style={{textAlign:'left'}}>Tarih ↓</th>
            <th className="sortable" style={{textAlign:'left'}}>Strateji</th>
            <th className="sortable" style={{textAlign:'left'}}>Sembol</th>
            <th>Tür</th>
            <th>Fiyat</th>
            <th>Miktar</th>
            <th>Tutar</th>
            <th>K/Z</th>
            <th>K/Z %</th>
          </tr>
        </thead>
        <tbody>
          {TRADES.map((t, i) => (
            <tr key={i}>
              <td className="dim">{t.date}</td>
              <td className="amber">{t.strat}</td>
              <td><span className="mono" style={{color: 'var(--cyan)'}}>{t.sym}</span></td>
              <td><span className={`tag ${t.side === 'AL' ? 'up' : 'down'}`}>{t.side}</span></td>
              <td>{t.px.toFixed(4)}</td>
              <td>{t.qty.toFixed(4)}</td>
              <td>₺{(t.px * t.qty).toFixed(2)}</td>
              <td className={t.pl == null ? 'dim' : t.pl >= 0 ? 'up' : 'down'}>
                {t.pl == null ? '—' : `${t.pl >= 0 ? '+' : ''}₺${t.pl.toFixed(2)}`}
              </td>
              <td className={t.pl == null ? 'dim' : t.pl >= 0 ? 'up' : 'down'}>
                {t.pl == null ? '—' : `${(t.pl / (t.px * t.qty) * 100).toFixed(2)}%`}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

Object.assign(window, { GrafikScreen, PortfoyScreen });
