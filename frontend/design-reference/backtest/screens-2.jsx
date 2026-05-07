/* PiyasaPilot — Screens (Strateji, Tarayıcı, Sinyaller) */

const { useState: useStateS2, useMemo: useMemoS2 } = React;

// ============== STRATEJİ ==============
function StratejiScreen() {
  const [tab, setTab] = useStateS2('lab');

  return (
    <div className="screen" style={{display: 'flex', flexDirection: 'column'}}>
      <div className="subbar">
        <div className="subbar-group">
          <button className={`subbar-btn ${tab === 'lab' ? 'active' : ''}`} onClick={() => setTab('lab')}>Kural Lab</button>
          <button className={`subbar-btn ${tab === 'cat' ? 'active' : ''}`} onClick={() => setTab('cat')}>Katalog (Hazır)</button>
          <button className={`subbar-btn ${tab === 'old' ? 'active' : ''}`} onClick={() => setTab('old')}>Eski Blueprintler</button>
        </div>
        <div className="subbar-spacer"/>
        <div className="subbar-group">
          <span className="subbar-label">Durum</span>
          <span className="tag up">● Doğrulandı</span>
        </div>
        <div className="subbar-group">
          <button className="subbar-btn">💾 Kaydet</button>
          <button className="subbar-btn">📋 Paper'a AL</button>
          <button className="subbar-btn active" style={{background: 'var(--amber)', color: '#0a0c10', borderColor: 'var(--amber)'}}>
            <Icon.play/> Çalıştır (F9)
          </button>
        </div>
      </div>

      {tab === 'lab' && <KuralLab/>}
      {tab === 'cat' && <Katalog/>}
      {tab === 'old' && <EskiBlueprintler/>}
    </div>
  );
}

function KuralLab() {
  return (
    <div style={{flex: 1, display: 'grid', gridTemplateColumns: '1fr 320px', overflow: 'hidden'}}>
      <div style={{overflow: 'auto', padding: 16, display: 'flex', flexDirection: 'column', gap: 14}}>
        {/* Header form */}
        <div style={{display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12}}>
          <div className="field">
            <label className="field-label">Strateji Adı <span className="req">*</span></label>
            <input defaultValue="EMA 50/200 Crossover"/>
          </div>
          <div className="field">
            <label className="field-label">Not</label>
            <input placeholder="Kısa açıklama..."/>
          </div>
        </div>

        {/* Param grid */}
        <div className="panel">
          <div className="panel-head">
            <span className="panel-title">Backtest Parametreleri</span>
          </div>
          <div style={{display: 'grid', gridTemplateColumns: 'repeat(6, 1fr)', borderTop: '1px solid var(--line-2)'}}>
            {[
              { l: 'Sembol', v: 'VAKBN.IS' },
              { l: 'Periyot', v: '1d' },
              { l: 'Başlangıç', v: '01.01.2024' },
              { l: 'Bitiş', v: '05.05.2026' },
              { l: 'Sermaye', v: '100,000' },
              { l: 'Komisyon %', v: '0.10' },
              { l: 'Slippage Modeli', v: 'Fixed BPS' },
              { l: 'Slippage bps', v: '5' },
              { l: 'Slippage Tick', v: '0.01' },
              { l: 'Likidite %', v: '5' },
              { l: 'Likidite Pencere', v: '5' },
              { l: 'Pozisyon %', v: '20' },
              { l: 'Kaynak', v: 'Cache' },
              { l: 'Yön', v: 'Long + Short', t: 'check' },
            ].map((f, i) => (
              <div key={i} style={{ padding: '8px 12px', borderRight: '1px solid var(--line-2)', borderBottom: '1px solid var(--line-2)' }}>
                <div className="label" style={{marginBottom: 4}}>{f.l}</div>
                <div className="mono" style={{fontSize: 12, color: 'var(--fg-0)', fontWeight: 500}}>{f.v}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Code editors 2x2 */}
        <div style={{display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12}}>
          <div className="code-editor focused">
            <div className="code-head"><span className="up" style={{fontWeight: 700}}>● LONG GİRİŞ</span><span className="dim">DSL kuralı</span><span style={{marginLeft:'auto'}}>3 satır</span></div>
            <div className="code-body">
              <div className="code-gutter">{[1,2,3].map(n => <div key={n}>{n}</div>)}</div>
              <div className="code-content"><span className="tok-comment">{`// EMA 50 yukarı kesim`}</span>{'\n'}
<span className="tok-fn">CROSS_UP</span><span className="tok-op">(</span><span className="tok-fn">EMA</span><span className="tok-op">(</span><span className="tok-arg">C</span><span className="tok-op">,</span><span className="tok-num">50</span><span className="tok-op">),</span> <span className="tok-fn">EMA</span><span className="tok-op">(</span><span className="tok-arg">C</span><span className="tok-op">,</span><span className="tok-num">200</span><span className="tok-op">))</span>{'\n'}
<span className="tok-key">AND</span> <span className="tok-fn">VOLUME</span> <span className="tok-op">&gt;</span> <span className="tok-fn">AVG</span><span className="tok-op">(</span><span className="tok-fn">VOLUME</span><span className="tok-op">,</span> <span className="tok-num">20</span><span className="tok-op">)</span>
              </div>
            </div>
          </div>
          <div className="code-editor">
            <div className="code-head"><span className="down" style={{fontWeight: 700}}>● LONG ÇIKIŞ</span><span className="dim">stop + trailing</span><span style={{marginLeft:'auto'}}>2 satır</span></div>
            <div className="code-body">
              <div className="code-gutter">{[1,2].map(n => <div key={n}>{n}</div>)}</div>
              <div className="code-content"><span className="tok-fn">CROSS_DOWN</span><span className="tok-op">(</span><span className="tok-fn">EMA</span><span className="tok-op">(</span><span className="tok-arg">C</span><span className="tok-op">,</span><span className="tok-num">50</span><span className="tok-op">),</span> <span className="tok-fn">EMA</span><span className="tok-op">(</span><span className="tok-arg">C</span><span className="tok-op">,</span><span className="tok-num">200</span><span className="tok-op">))</span>{'\n'}
<span className="tok-key">OR</span> <span className="tok-fn">STOP</span><span className="tok-op">(</span><span className="tok-num">3%</span><span className="tok-op">)</span>
              </div>
            </div>
          </div>
          <div className="code-editor">
            <div className="code-head"><span className="up" style={{fontWeight: 700}}>● SHORT GİRİŞ</span><span className="dim">aynı kuralın aynası</span></div>
            <div className="code-body">
              <div className="code-gutter">{[1].map(n => <div key={n}>{n}</div>)}</div>
              <div className="code-content"><span className="tok-fn">CROSS_DOWN</span><span className="tok-op">(</span><span className="tok-fn">EMA</span><span className="tok-op">(</span><span className="tok-arg">C</span><span className="tok-op">,</span><span className="tok-num">50</span><span className="tok-op">),</span> <span className="tok-fn">EMA</span><span className="tok-op">(</span><span className="tok-arg">C</span><span className="tok-op">,</span><span className="tok-num">200</span><span className="tok-op">))</span></div>
            </div>
          </div>
          <div className="code-editor">
            <div className="code-head"><span className="down" style={{fontWeight: 700}}>● SHORT ÇIKIŞ</span></div>
            <div className="code-body">
              <div className="code-gutter">{[1].map(n => <div key={n}>{n}</div>)}</div>
              <div className="code-content"><span className="tok-fn">CROSS_UP</span><span className="tok-op">(</span><span className="tok-fn">EMA</span><span className="tok-op">(</span><span className="tok-arg">C</span><span className="tok-op">,</span><span className="tok-num">50</span><span className="tok-op">),</span> <span className="tok-fn">EMA</span><span className="tok-op">(</span><span className="tok-arg">C</span><span className="tok-op">,</span><span className="tok-num">200</span><span className="tok-op">))</span></div>
            </div>
          </div>
        </div>

        {/* Risk panel */}
        <div className="panel">
          <div className="panel-head">
            <span className="panel-title">Risk Yönetimi</span>
          </div>
          <div style={{display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)'}}>
            {[
              { l: 'Stop %', v: '3', accent: 'var(--down)' },
              { l: 'Hedef Al %', v: '8', accent: 'var(--up)' },
              { l: 'Trailing %', v: '5', accent: 'var(--amber)' },
              { l: 'Süre Stop (bar)', v: '0', accent: 'var(--fg-3)' },
            ].map((r, i) => (
              <div key={i} style={{padding: 14, borderRight: '1px solid var(--line-2)', borderBottom: '1px solid var(--line-2)', display: 'flex', flexDirection: 'column', gap: 6}}>
                <div className="label">{r.l}</div>
                <div style={{display: 'flex', alignItems: 'baseline', gap: 4}}>
                  <span className="mono" style={{fontSize: 22, fontWeight: 600, color: r.accent}}>{r.v}</span>
                  <span className="dim">%</span>
                </div>
                <div className="bar"><i style={{width: `${parseInt(r.v) * 10}%`, background: r.accent}}/></div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Right rail — DSL Helper */}
      <div style={{borderLeft: '1px solid var(--line-2)', overflow: 'auto', display: 'flex', flexDirection: 'column'}}>
        <div className="panel-head">
          <span className="panel-title">DSL Yardımcısı</span>
        </div>
        <div style={{padding: 12, display: 'flex', flexDirection: 'column', gap: 10}}>
          <div className="field">
            <label className="field-label">Şablon</label>
            <select><option>EMA 50/200 Crossover</option><option>RSI Aşırı Satım</option><option>Bollinger Squeeze</option></select>
          </div>
          <div className="field">
            <label className="field-label">Hedef</label>
            <select><option>Long Giriş</option><option>Long Çıkış</option><option>Short Giriş</option><option>Short Çıkış</option></select>
          </div>
          <div style={{display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8}}>
            <div className="field">
              <label className="field-label">Sol</label>
              <select><option>EMA(C, p)</option></select>
            </div>
            <div className="field">
              <label className="field-label">Op</label>
              <select><option>yukarı kes</option><option>aşağı kes</option><option>{'>'}</option><option>{'<'}</option></select>
            </div>
            <div className="field">
              <label className="field-label">Sol p</label>
              <input defaultValue="50"/>
            </div>
            <div className="field">
              <label className="field-label">Sağ p</label>
              <input defaultValue="200"/>
            </div>
          </div>
          <div className="field">
            <label className="field-label">Bağlaç</label>
            <select><option>OR</option><option>AND</option></select>
          </div>
          <button className="btn primary" style={{justifyContent: 'center'}}>+ Kural Ekle</button>

          <div className="divider" style={{margin: '4px 0'}}/>

          <div>
            <div className="label" style={{marginBottom: 6}}>Mevcut Fonksiyonlar</div>
            <div style={{display: 'flex', flexWrap: 'wrap', gap: 4}}>
              {['EMA','SMA','RSI','MACD','BB','ATR','ADX','VWAP','VOLUME','CROSS_UP','CROSS_DOWN','HIGHEST','LOWEST'].map(f => (
                <span key={f} className="tag cyan" style={{cursor: 'pointer'}}>{f}</span>
              ))}
            </div>
          </div>

          <div className="divider" style={{margin: '4px 0'}}/>

          <div>
            <div className="label" style={{marginBottom: 6}}>Tahmini Backtest Süresi</div>
            <div style={{display: 'flex', alignItems: 'baseline', gap: 6}}>
              <span className="mono" style={{fontSize: 18, fontWeight: 600, color: 'var(--amber)'}}>~4.2s</span>
              <span className="dim" style={{fontSize: 10}}>584 bar / 1 sembol</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function Katalog() {
  const items = [
    { name: 'EMA Crossover Klasik', desc: 'EMA 50 ve EMA 200 kesişim', sharpe: 0.82, dd: -18.4, win: 52, used: 1240 },
    { name: 'RSI 30/70 Reversion', desc: 'Aşırı alım/satım dönüşümleri', sharpe: 1.14, dd: -12.8, win: 58, used: 980 },
    { name: 'Bollinger Squeeze', desc: 'Volatilite sıkışıp patlama', sharpe: 1.42, dd: -9.2, win: 48, used: 720 },
    { name: 'Donchian Breakout', desc: '20 günlük yüksek/düşük kırılım', sharpe: 0.94, dd: -22.1, win: 44, used: 612 },
    { name: 'MACD Divergence', desc: 'Fiyat-MACD uyumsuzluğu', sharpe: 0.71, dd: -16.8, win: 51, used: 540 },
    { name: 'VWAP Mean Reversion', desc: 'Gün içi VWAP geri dönüş', sharpe: 1.21, dd: -8.4, win: 62, used: 480 },
    { name: 'ATR Trend Follow', desc: 'ATR bandı tabanlı trend takip', sharpe: 1.08, dd: -14.2, win: 49, used: 410 },
    { name: 'Pivot Breakout', desc: 'Klasik pivot seviyeleri', sharpe: 0.68, dd: -19.4, win: 46, used: 380 },
  ];
  return (
    <div style={{flex: 1, overflow: 'auto', padding: 16}}>
      <div style={{display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 12}}>
        {items.map((it, i) => (
          <div key={i} className="panel" style={{cursor: 'pointer'}}>
            <div className="panel-head">
              <span className="panel-title">{it.name}</span>
              <span className="dim mono" style={{marginLeft: 'auto', fontSize: 10}}>{it.used} kez kullanıldı</span>
            </div>
            <div style={{padding: 12, display: 'flex', flexDirection: 'column', gap: 10}}>
              <div className="dim" style={{fontSize: 11}}>{it.desc}</div>
              <div style={{display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 8}}>
                <div>
                  <div className="label">Sharpe</div>
                  <div className="mono" style={{fontSize: 16, color: it.sharpe > 1 ? 'var(--up)' : 'var(--amber)', fontWeight: 600}}>{it.sharpe.toFixed(2)}</div>
                </div>
                <div>
                  <div className="label">Maks DD</div>
                  <div className="mono" style={{fontSize: 16, color: 'var(--down)', fontWeight: 600}}>{it.dd}%</div>
                </div>
                <div>
                  <div className="label">Win %</div>
                  <div className="mono" style={{fontSize: 16, fontWeight: 600}}>{it.win}%</div>
                </div>
              </div>
              <Spark data={Array.from({length: 30}, (_, j) => 100 + Math.sin(j * it.sharpe) * 10 + j * (it.sharpe - 0.8))} w={300} h={32} color={it.sharpe > 1 ? 'var(--up)' : 'var(--amber)'} fill={it.sharpe > 1 ? 'var(--up)' : 'var(--amber)'}/>
              <div style={{display: 'flex', gap: 6}}>
                <button className="btn sm primary" style={{flex: 1, justifyContent: 'center'}}>Yükle</button>
                <button className="btn sm" style={{flex: 1, justifyContent: 'center'}}>Önizle</button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function EskiBlueprintler() {
  return (
    <div style={{flex: 1, padding: 32, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 12}}>
      <div className="dim" style={{fontFamily: 'var(--font-mono)', fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.1em'}}>Geçmiş Sürümler</div>
      <div style={{fontSize: 24, fontWeight: 600, letterSpacing: '-0.01em'}}>v1 blueprint formatı</div>
      <div className="dim" style={{maxWidth: 400, textAlign: 'center', fontSize: 12}}>Eski JSON tabanlı stratejiler burada saklanır. Yeni DSL formatına dönüştürmek için bir tanesini seçin.</div>
      <button className="btn">Eski Dosya İçe Aktar</button>
    </div>
  );
}

// ============== TARAYICI ==============
function TarayiciScreen() {
  const [activePreset, setActivePreset] = useStateS2('rsi_oversold');
  const [hasResults, setHasResults] = useStateS2(false);

  return (
    <div className="screen" style={{display: 'flex', flexDirection: 'column'}}>
      <div className="subbar">
        <div className="subbar-group">
          <span className="panel-title" style={{color: 'var(--amber)'}}>Piyasa Tarayıcı</span>
        </div>
        <div className="subbar-group">
          <span className="subbar-label">Hazır Filtre</span>
          {SCANNER_PRESETS.map(p => (
            <button key={p.id} className={`subbar-btn ${activePreset === p.id ? 'active' : ''}`} onClick={() => setActivePreset(p.id)}>
              {p.label}
            </button>
          ))}
        </div>
        <div className="subbar-spacer"/>
        <div className="subbar-group">
          <button className="subbar-btn">+ Yeni Filtre</button>
          <button className="subbar-btn primary" style={{background: 'var(--cyan)', color: '#0a0c10', borderColor: 'var(--cyan)', fontWeight: 700}} onClick={() => setHasResults(true)}>
            <Icon.zap/> Tara (F9)
          </button>
        </div>
      </div>

      {/* Filter builder */}
      <div style={{borderBottom: '1px solid var(--line-2)', background: 'var(--bg-2)'}}>
        <div className="cmdbar" style={{margin: 12}}>
          <div className="cmdbar-prompt">DSL ›</div>
          <input defaultValue={SCANNER_PRESETS.find(p => p.id === activePreset)?.expr || ''}/>
          <button className="btn ghost" style={{borderLeft: '1px solid var(--amber-dim)', padding: '0 14px'}}>↵ Çalıştır</button>
        </div>
        <div style={{display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', borderTop: '1px solid var(--line-2)'}}>
          {[
            { l: 'Evren', v: 'BIST 100', n: 100 },
            { l: 'Periyot', v: '1d', n: null },
            { l: 'Min Hacim', v: '1M', n: null },
            { l: 'Min Fiyat', v: '₺1.00', n: null },
            { l: 'Sıralama', v: 'Skor ↓', n: null },
          ].map((f, i) => (
            <div key={i} style={{ padding: '10px 14px', borderRight: '1px solid var(--line-2)' }}>
              <div className="label">{f.l}</div>
              <div className="mono" style={{fontSize: 13, color: 'var(--fg-0)', display: 'flex', alignItems: 'center', gap: 6, marginTop: 2}}>
                {f.v} <span className="chev dim">▾</span>
                {f.n && <span className="tag" style={{marginLeft: 'auto'}}>{f.n}</span>}
              </div>
            </div>
          ))}
        </div>
      </div>

      {hasResults ? (
        <ScannerResults preset={activePreset} onReset={() => setHasResults(false)}/>
      ) : (
        <ScannerEmpty onScan={() => setHasResults(true)}/>
      )}
    </div>
  );
}

function ScannerEmpty({ onScan }) {
  return (
    <div className="empty" style={{padding: 40, alignItems: 'center', justifyContent: 'center', textAlign: 'center'}}>
      <div style={{maxWidth: 480, display: 'flex', flexDirection: 'column', gap: 16, alignItems: 'center'}}>
        <svg width="56" height="56" viewBox="0 0 56 56" fill="none">
          <rect x="6" y="6" width="44" height="44" stroke="var(--amber)" strokeWidth="1.5" fill="var(--amber-bg)"/>
          <circle cx="22" cy="22" r="8" stroke="var(--amber)" strokeWidth="1.5"/>
          <path d="M28 28L40 40" stroke="var(--amber)" strokeWidth="1.5"/>
          <text x="28" y="48" textAnchor="middle" fontSize="9" fontFamily="var(--font-mono)" fill="var(--amber)" letterSpacing="0.1em">SCAN</text>
        </svg>
        <div className="label">Tarama Bekleniyor</div>
        <div style={{fontSize: 22, fontWeight: 600, letterSpacing: '-0.01em', textAlign: 'center'}}>Filtrenizi seçin ve <span style={{color: 'var(--amber)'}}>Tara</span>'ya basın</div>
        <div className="dim" style={{fontSize: 12, lineHeight: 1.6, textAlign: 'center'}}>
          Hazır filtrelerden birini seçebilir veya kendi DSL ifadenizi yazabilirsiniz.<br/>
          Tarama; BIST 100 evrenindeki <span className="mono" style={{color: 'var(--fg-1)'}}>100</span> sembol üzerinde çalışır.
        </div>
        <div style={{display: 'flex', gap: 8, marginTop: 8}}>
          <button className="btn primary" onClick={onScan}><Icon.zap/> Şimdi Tara</button>
          <button className="btn">DSL Belgeleri</button>
        </div>

        <div className="divider" style={{width: '100%', margin: '8px 0'}}/>

        <div style={{width: '100%', display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 1, background: 'var(--line-2)'}}>
          {[
            { n: '100', l: 'Sembol' },
            { n: '5+', l: 'Hazır filtre' },
            { n: '~2.4s', l: 'Ort. süre' },
          ].map((s, i) => (
            <div key={i} style={{background: 'var(--bg-1)', padding: 16}}>
              <div className="mono" style={{fontSize: 22, fontWeight: 600, color: 'var(--amber)'}}>{s.n}</div>
              <div className="label">{s.l}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function ScannerResults({ preset, onReset }) {
  const matched = SCANNER_RESULTS;
  return (
    <div style={{flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden'}}>
      <div style={{padding: '10px 14px', borderBottom: '1px solid var(--line-2)', background: 'var(--bg-2)', display: 'flex', alignItems: 'center', gap: 12}}>
        <span className="tag up">● TARAMA TAMAMLANDI</span>
        <span className="dim" style={{fontFamily: 'var(--font-mono)', fontSize: 11}}>
          <span style={{color: 'var(--fg-0)', fontWeight: 600}}>{matched.length}</span> eşleşme / 100 sembol • 2.18s
        </span>
        <div style={{marginLeft: 'auto', display: 'flex', gap: 6}}>
          <button className="btn sm">+ Tümünü Watchlist'e</button>
          <button className="btn sm"><Icon.download/> CSV</button>
          <button className="btn sm" onClick={onReset}>↻ Yeniden Tara</button>
        </div>
      </div>
      <div style={{flex: 1, overflow: 'auto'}}>
        <table className="dt">
          <thead>
            <tr>
              <th style={{textAlign: 'left'}}>#</th>
              <th style={{textAlign: 'left'}}>Sembol</th>
              <th style={{textAlign: 'left'}}>Şirket</th>
              <th>Fiyat</th>
              <th>Değişim %</th>
              <th>Hacim</th>
              <th>RSI(14)</th>
              <th>ATR(14)</th>
              <th>Sinyal</th>
              <th>Skor</th>
              <th style={{width: 100}}>30g Trend</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {matched.map((r, i) => (
              <tr key={r.sym}>
                <td className="dim">{String(i+1).padStart(2,'0')}</td>
                <td><span className="mono" style={{color: 'var(--cyan)', fontWeight: 700}}>{r.sym}</span></td>
                <td className="dim" style={{textAlign: 'left'}}>{r.name}</td>
                <td>₺{r.px.toFixed(2)}</td>
                <td className={r.chg >= 0 ? 'up' : 'down'}>{r.chg >= 0 ? '+' : ''}{r.chg.toFixed(2)}%</td>
                <td>{r.vol}</td>
                <td className={r.rsi < 30 ? 'up' : r.rsi > 70 ? 'down' : ''}>{r.rsi.toFixed(1)}</td>
                <td>{r.atr.toFixed(2)}</td>
                <td><span className={`tag ${r.sig === 'STRONG_BUY' ? 'up' : 'amber'}`}>{r.sig}</span></td>
                <td>
                  <div style={{display: 'flex', alignItems: 'center', gap: 6, justifyContent: 'flex-end'}}>
                    <div className="bar" style={{width: 40}}><i style={{width: `${r.score}%`, background: r.score > 85 ? 'var(--up)' : 'var(--amber)'}}/></div>
                    <span style={{minWidth: 24}}>{r.score}</span>
                  </div>
                </td>
                <td><Spark data={Array.from({length: 30}, (_, j) => Math.sin(j * 0.3 + i) * 10 + j * 0.5 + 50)} w={80} h={20} color={r.chg >= 0 ? 'var(--up)' : 'var(--down)'}/></td>
                <td><button className="btn sm ghost"><Icon.more/></button></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

Object.assign(window, { StratejiScreen, TarayiciScreen });
