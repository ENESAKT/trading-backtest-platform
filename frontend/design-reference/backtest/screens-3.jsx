/* PiyasaPilot — Screens (Sinyaller, Eğitimler, Mali Analiz) */

const { useState: useStateS3 } = React;

// ============== SİNYALLER ==============
function SinyallerScreen() {
  const [filterSide, setFilterSide] = useStateS3('all');
  const [grp, setGrp] = useStateS3('BIST 30');

  const filtered = filterSide === 'all' ? SIGNALS : SIGNALS.filter(s => filterSide === 'buy' ? s.side === 'AL' : s.side === 'SAT');

  return (
    <div className="screen" style={{display: 'flex', flexDirection: 'column'}}>
      <div className="subbar">
        <div className="subbar-group">
          <span className="panel-title" style={{color: 'var(--amber)'}}>Sinyaller</span>
          <span className="tag up">● CANLI</span>
        </div>
        <div className="subbar-group">
          <span className="subbar-label">Telegram</span>
          <span className="tag" style={{background: 'var(--down-bg)', color: 'var(--down)'}}>● Yapılandırılmamış</span>
          <button className="subbar-btn">Bağla</button>
        </div>
        <div className="subbar-spacer"/>
        <div className="subbar-group">
          <button className={`subbar-btn ${filterSide === 'all' ? 'active' : ''}`} onClick={() => setFilterSide('all')}>Tümü</button>
          <button className={`subbar-btn ${filterSide === 'buy' ? 'active' : ''}`} onClick={() => setFilterSide('buy')}>AL</button>
          <button className={`subbar-btn ${filterSide === 'sell' ? 'active' : ''}`} onClick={() => setFilterSide('sell')}>SAT</button>
        </div>
      </div>

      {/* Filter strip */}
      <div style={{borderBottom: '1px solid var(--line-2)', background: 'var(--bg-2)', display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)'}}>
        {[
          { l: 'Aktif', v: '✓ Açık', c: 'var(--up)' },
          { l: 'Sinyal', v: '✓ Açık', c: 'var(--up)' },
          { l: 'İşlem', v: '✗ Kapalı', c: 'var(--fg-3)' },
          { l: 'Sistem', v: '✗ Kapalı', c: 'var(--fg-3)' },
          { l: 'Günlük Özet', v: '✓ Açık', c: 'var(--up)' },
          { l: 'Grup', v: 'BIST 30', c: 'var(--amber)' },
          { l: 'Min Güç', v: '0', c: 'var(--fg-1)' },
        ].map((f, i) => (
          <div key={i} style={{padding: '10px 14px', borderRight: '1px solid var(--line-2)'}}>
            <div className="label">{f.l}</div>
            <div className="mono" style={{fontSize: 12, color: f.c, fontWeight: 600, marginTop: 2}}>{f.v}</div>
          </div>
        ))}
      </div>

      {/* Aggregate stats */}
      <div className="stat-grid" style={{gridTemplateColumns: 'repeat(5, 1fr)'}}>
        <div className="stat">
          <div className="stat-label">Bugün</div>
          <div className="stat-value">{SIGNALS.length}</div>
          <div className="stat-sub"><span className="delta up">+8</span> son saat</div>
        </div>
        <div className="stat">
          <div className="stat-label">AL Sinyali</div>
          <div className="stat-value up">{SIGNALS.filter(s => s.side === 'AL').length}</div>
          <div className="stat-sub">{Math.round(SIGNALS.filter(s => s.side === 'AL').length / SIGNALS.length * 100)}% pay</div>
        </div>
        <div className="stat">
          <div className="stat-label">SAT Sinyali</div>
          <div className="stat-value down">{SIGNALS.filter(s => s.side === 'SAT').length}</div>
          <div className="stat-sub">{Math.round(SIGNALS.filter(s => s.side === 'SAT').length / SIGNALS.length * 100)}% pay</div>
        </div>
        <div className="stat">
          <div className="stat-label">Ort. Güç</div>
          <div className="stat-value amber">4.2<span style={{fontSize: 14, color: 'var(--fg-2)'}}>/5</span></div>
          <div className="stat-sub">★★★★☆</div>
        </div>
        <div className="stat">
          <div className="stat-label">Konsensüs %</div>
          <div className="stat-value">68<span style={{fontSize: 14, color: 'var(--fg-2)'}}>%</span></div>
          <div className="stat-sub">Min: 60%</div>
        </div>
      </div>

      <div style={{flex: 1, display: 'grid', gridTemplateColumns: '1fr 280px', overflow: 'hidden'}}>
        {/* Signal feed */}
        <div style={{overflow: 'auto', borderRight: '1px solid var(--line-2)'}}>
          <div className="panel-head" style={{position: 'sticky', top: 0, zIndex: 1}}>
            <span className="panel-title">Canlı Akış <span className="badge">{filtered.length} sinyal</span></span>
            <span className="dim" style={{marginLeft: 'auto', fontFamily: 'var(--font-mono)', fontSize: 9}}>Her bar kapanışında güncellenir</span>
          </div>
          {filtered.map((s, i) => {
            const isBuy = s.side === 'AL';
            return (
              <div key={i} style={{
                display: 'grid',
                gridTemplateColumns: '60px 1fr 1fr 1fr 80px',
                alignItems: 'center',
                padding: '12px 14px',
                borderBottom: '1px solid var(--line-1)',
                gap: 14,
                cursor: 'pointer',
                position: 'relative',
              }}>
                <span style={{position: 'absolute', left: 0, top: 0, bottom: 0, width: 3, background: isBuy ? 'var(--up)' : 'var(--down)'}}/>
                <span className={`tag ${isBuy ? 'up' : 'down'}`} style={{fontSize: 11, padding: '2px 8px'}}>{s.side}</span>
                <div>
                  <div className="mono" style={{fontSize: 13, fontWeight: 700, color: 'var(--cyan)'}}>{s.sym}</div>
                  <div className="dim" style={{fontSize: 10, fontFamily: 'var(--font-mono)'}}>{s.note}</div>
                </div>
                <div>
                  <div className="label">Strateji</div>
                  <div className="mono" style={{fontSize: 11, color: 'var(--amber)', fontWeight: 600, marginTop: 2}}>{s.strat}</div>
                </div>
                <div>
                  <div className="label">Güç</div>
                  <div style={{marginTop: 2, display: 'flex', alignItems: 'center', gap: 4}}>
                    {[1,2,3,4,5].map(n => (
                      <span key={n} style={{
                        width: 8, height: 8,
                        background: n <= s.strength ? 'var(--amber)' : 'var(--bg-4)',
                      }}/>
                    ))}
                    <span className="mono dim" style={{fontSize: 10, marginLeft: 4}}>{s.strength}/5</span>
                  </div>
                </div>
                <div style={{textAlign: 'right'}}>
                  <div className="mono" style={{fontSize: 14, fontWeight: 600}}>{s.px < 1 ? s.px.toFixed(4) : s.px.toFixed(2)}</div>
                  <div className="dim" style={{fontSize: 10, fontFamily: 'var(--font-mono)'}}>{s.tf} • {s.t}</div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Right side — distribution */}
        <div style={{display: 'flex', flexDirection: 'column', overflow: 'auto'}}>
          <div className="panel-head">
            <span className="panel-title">Strateji Dağılımı</span>
          </div>
          <div style={{padding: 12, display: 'flex', flexDirection: 'column', gap: 10}}>
            {[
              { n: 'donchian_breakout', c: SIGNALS.filter(s => s.strat === 'donchian_breakout').length, color: 'var(--amber)' },
              { n: 'sma_crossover',     c: SIGNALS.filter(s => s.strat === 'sma_crossover').length, color: 'var(--cyan)' },
              { n: 'rsi_reversion',     c: SIGNALS.filter(s => s.strat === 'rsi_reversion').length, color: '#b78bff' },
              { n: 'macd_divergence',   c: SIGNALS.filter(s => s.strat === 'macd_divergence').length, color: 'var(--up)' },
              { n: 'atr_trend',         c: SIGNALS.filter(s => s.strat === 'atr_trend').length, color: '#ff6b9d' },
              { n: 'pivot_breakout',    c: SIGNALS.filter(s => s.strat === 'pivot_breakout').length, color: 'var(--down)' },
              { n: 'bollinger_reversion', c: SIGNALS.filter(s => s.strat === 'bollinger_reversion').length, color: 'var(--fg-2)' },
            ].map((it, i) => {
              const pct = (it.c / SIGNALS.length) * 100;
              return (
                <div key={i}>
                  <div style={{display: 'flex', justifyContent: 'space-between', fontSize: 10, fontFamily: 'var(--font-mono)', marginBottom: 3}}>
                    <span style={{color: it.color}}>● {it.n}</span>
                    <span><span style={{color: 'var(--fg-0)', fontWeight: 600}}>{it.c}</span> <span className="dim">({pct.toFixed(0)}%)</span></span>
                  </div>
                  <div className="bar"><i style={{width: `${pct}%`, background: it.color}}/></div>
                </div>
              );
            })}
          </div>

          <div className="panel-head">
            <span className="panel-title">Sembol Dağılımı</span>
          </div>
          <div style={{padding: 12, display: 'flex', flexWrap: 'wrap', gap: 4}}>
            {SIGNALS.map((s, i) => (
              <span key={i} className="tag" style={{
                background: s.side === 'AL' ? 'var(--up-bg)' : 'var(--down-bg)',
                color: s.side === 'AL' ? 'var(--up)' : 'var(--down)',
                cursor: 'pointer',
              }}>{s.sym}</span>
            ))}
          </div>

          <div className="panel-head">
            <span className="panel-title">Sessiz Saat</span>
          </div>
          <div style={{padding: 12}}>
            <div className="mono" style={{fontSize: 18, fontWeight: 600}}>23:00 — 09:00</div>
            <div className="dim" style={{fontSize: 11, marginTop: 2}}>Bu aralıkta bildirim gönderilmez</div>
            <div style={{height: 24, background: 'var(--bg-3)', marginTop: 8, position: 'relative', borderRadius: 0}}>
              <div style={{position: 'absolute', left: '0%', width: '37.5%', top: 0, bottom: 0, background: 'var(--bg-4)'}}/>
              <div style={{position: 'absolute', left: '95.8%', width: '4.2%', top: 0, bottom: 0, background: 'var(--bg-4)'}}/>
              <div style={{position: 'absolute', left: '37.5%', top: 0, bottom: 0, width: 1, background: 'var(--amber)'}}/>
              {[0,4,8,12,16,20,24].map(h => (
                <span key={h} style={{position: 'absolute', left: `${(h/24)*100}%`, top: '100%', fontSize: 8, fontFamily: 'var(--font-mono)', color: 'var(--fg-3)', transform: 'translateX(-50%)', marginTop: 2}}>{String(h).padStart(2,'0')}</span>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// ============== EĞİTİMLER ==============
function EgitimScreen() {
  const [activeId, setActiveId] = useStateS3(1);
  const [cat, setCat] = useStateS3('all');
  const [q, setQ] = useStateS3('');

  const cats = [
    { id: 'all', label: 'Tümü', count: ARTICLES.length },
    { id: 'İndikatörler', label: 'İndikatörler', count: 20 },
    { id: 'Formasyonlar', label: 'Formasyonlar', count: 12 },
    { id: 'Sistem & Backtest', label: 'Sistem & Backtest', count: 10 },
    { id: 'VİOP & Vadeli', label: 'VİOP & Vadeli', count: 8 },
    { id: 'Psikoloji & Disiplin', label: 'Psikoloji & Disiplin', count: 7 },
  ];

  const filtered = ARTICLES.filter(a =>
    (cat === 'all' || a.cat === cat) &&
    (!q || a.title.toLowerCase().includes(q.toLowerCase()))
  );

  const active = ARTICLES.find(a => a.id === activeId) || ARTICLES[0];

  return (
    <div className="screen" style={{display: 'grid', gridTemplateColumns: '200px 320px 1fr', overflow: 'hidden'}}>
      {/* Categories */}
      <div style={{borderRight: '1px solid var(--line-2)', overflow: 'auto', background: 'var(--bg-2)'}}>
        <div className="panel-head"><span className="panel-title">Kategoriler</span></div>
        {cats.map(c => (
          <div key={c.id} onClick={() => setCat(c.id)} style={{
            padding: '10px 14px',
            borderBottom: '1px solid var(--line-1)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            cursor: 'pointer',
            background: cat === c.id ? 'var(--bg-3)' : 'transparent',
            borderLeft: cat === c.id ? '2px solid var(--amber)' : '2px solid transparent',
          }}>
            <span style={{fontSize: 12, color: cat === c.id ? 'var(--fg-0)' : 'var(--fg-1)', fontWeight: cat === c.id ? 600 : 500}}>{c.label}</span>
            <span className="tag mono" style={{fontSize: 9}}>{c.count}</span>
          </div>
        ))}

        <div style={{padding: 14, borderTop: '1px solid var(--line-2)', marginTop: 12}}>
          <div className="label" style={{marginBottom: 8}}>İlerleme</div>
          <div className="mono" style={{fontSize: 22, fontWeight: 600, color: 'var(--amber)'}}>12<span style={{color: 'var(--fg-3)'}}>/57</span></div>
          <div className="dim" style={{fontSize: 10, marginTop: 2}}>okundu</div>
          <div className="bar" style={{marginTop: 8}}><i style={{width: '21%', background: 'var(--amber)'}}/></div>
        </div>
      </div>

      {/* Article list */}
      <div style={{borderRight: '1px solid var(--line-2)', overflow: 'auto', display: 'flex', flexDirection: 'column'}}>
        <div className="panel-head" style={{position: 'sticky', top: 0, zIndex: 1}}>
          <input value={q} onChange={e => setQ(e.target.value)} placeholder="Makale ara..." style={{flex: 1, background: 'var(--bg-1)', border: '1px solid var(--line-2)', padding: '4px 8px', fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--fg-0)'}}/>
        </div>
        {filtered.map(a => (
          <div key={a.id} onClick={() => setActiveId(a.id)} style={{
            padding: '10px 14px',
            borderBottom: '1px solid var(--line-1)',
            cursor: 'pointer',
            background: activeId === a.id ? 'var(--bg-3)' : 'transparent',
            borderLeft: activeId === a.id ? '2px solid var(--amber)' : '2px solid transparent',
          }}>
            <div style={{fontSize: 12, fontWeight: activeId === a.id ? 600 : 500, color: 'var(--fg-0)', lineHeight: 1.35}}>{a.title}</div>
            <div style={{display: 'flex', gap: 6, marginTop: 5, alignItems: 'center'}}>
              <span className="dim" style={{fontFamily: 'var(--font-mono)', fontSize: 9, textTransform: 'uppercase', letterSpacing: '0.06em'}}>{a.cat}</span>
              <span className="dim">•</span>
              <span className={`tag ${a.level === 'başlangıç' ? 'up' : a.level === 'orta' ? 'amber' : 'down'}`} style={{fontSize: 8}}>{a.level}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Article reader */}
      <div style={{overflow: 'auto', display: 'flex', flexDirection: 'column'}}>
        <div className="panel-head">
          <span className="dim mono" style={{fontSize: 9, textTransform: 'uppercase', letterSpacing: '0.08em'}}>İndikatörler › ADX/ADXR</span>
          <div style={{marginLeft: 'auto', display: 'flex', gap: 4}}>
            <span className="tag amber">{active.level}</span>
            <span className="tag">kaynak güveni: yüksek</span>
            <button className="btn sm">★ Kaydet</button>
            <button className="btn sm"><Icon.download/></button>
          </div>
        </div>

        <div style={{padding: '24px 32px', maxWidth: 720, fontSize: 13, lineHeight: 1.7, color: 'var(--fg-1)'}}>
          <div style={{display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8}}>
            <span className="dim mono" style={{fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.1em'}}>İndikatörler</span>
          </div>
          <h1 style={{fontFamily: 'var(--font-display)', fontSize: 32, fontWeight: 700, letterSpacing: '-0.02em', margin: '4px 0 16px', color: 'var(--fg-0)'}}>
            {active.title}
          </h1>
          <div style={{display: 'flex', gap: 6, marginBottom: 24}}>
            {(active.tags || ['trend','yön','güç']).map(t => <span key={t} className="tag outline" style={{fontSize: 10}}>{t}</span>)}
          </div>

          <div style={{padding: 14, background: 'var(--bg-2)', borderLeft: '3px solid var(--amber)', marginBottom: 24}}>
            <div className="label" style={{marginBottom: 6}}>Kaynak Notu</div>
            <div className="mono dim" style={{fontSize: 11}}>Fuat Aksoy • İndikatörler • kare OCR • Ses transkripti eksik olabilir. • original_piyasapilot_content</div>
          </div>

          <p style={{marginTop: 0}}>ADX, trendin yönünden çok gücünü okumak için kullanılır. Fiyat yukarı ya da aşağı gidiyor olabilir; ADX'in görevi bu hareketin belirginleşip belirginleşmediğini ayrı bir pencereden göstermektir.</p>

          <h2 style={{fontFamily: 'var(--font-display)', fontSize: 20, fontWeight: 700, marginTop: 32, marginBottom: 12, color: 'var(--fg-0)'}}>Nedir?</h2>
          <p>Yön hareketi ailesinde artı ve eksi yön çizgileri yön tarafını, ADX ise trend gücünü anlatır. ADXR, ADX'in daha yumuşak bir akrabası gibi düşünülebilir; hızlı oynamaları azaltır ama daha geç tepki verir.</p>

          <h2 style={{fontFamily: 'var(--font-display)', fontSize: 20, fontWeight: 700, marginTop: 32, marginBottom: 12, color: 'var(--fg-0)'}}>Nasıl Hesaplanır?</h2>
          <p>PiyasaPilot DSL'de ana seriler:</p>

          <div className="code-editor" style={{marginTop: 12, marginBottom: 16}}>
            <div className="code-head"><span style={{color: 'var(--cyan)'}}>● DSL</span><span style={{marginLeft: 'auto'}} className="dim">PiyasaPilot v2.4</span></div>
            <div className="code-body">
              <div className="code-gutter">{[1,2,3,4].map(n => <div key={n}>{n}</div>)}</div>
              <div className="code-content"><span className="tok-fn">PLUS_DI</span><span className="tok-op">(</span><span className="tok-num">14</span><span className="tok-op">)</span>{'\n'}<span className="tok-fn">MINUS_DI</span><span className="tok-op">(</span><span className="tok-num">14</span><span className="tok-op">)</span>{'\n'}<span className="tok-fn">ADX</span><span className="tok-op">(</span><span className="tok-num">14</span><span className="tok-op">)</span>{'\n'}<span className="tok-fn">ADXR</span><span className="tok-op">(</span><span className="tok-num">14</span><span className="tok-op">,</span><span className="tok-num">14</span><span className="tok-op">)</span>
              </div>
            </div>
          </div>

          <p>Trend filtresi örneği:</p>

          <div className="code-editor" style={{marginTop: 12}}>
            <div className="code-body">
              <div className="code-gutter"><div>1</div></div>
              <div className="code-content"><span className="tok-arg">C</span> <span className="tok-op">{'>'}</span> <span className="tok-fn">EMA</span><span className="tok-op">(</span><span className="tok-arg">C</span><span className="tok-op">,</span><span className="tok-num">50</span><span className="tok-op">)</span> <span className="tok-key">AND</span> <span className="tok-fn">PLUS_DI</span><span className="tok-op">(</span><span className="tok-num">14</span><span className="tok-op">)</span> <span className="tok-op">{'>'}</span> <span className="tok-fn">MINUS_DI</span><span className="tok-op">(</span><span className="tok-num">14</span><span className="tok-op">)</span> <span className="tok-key">AND</span> <span className="tok-fn">ADX</span><span className="tok-op">(</span><span className="tok-num">14</span><span className="tok-op">)</span> <span className="tok-op">{'>'}</span> <span className="tok-num">20</span></div>
            </div>
          </div>

          <p style={{marginTop: 16}}>Bu kural fiyat yönünü EMA ile, yön hareketini DI çizgileriyle, trend gücünü ADX ile kontrol eder.</p>

          <h2 style={{fontFamily: 'var(--font-display)', fontSize: 20, fontWeight: 700, marginTop: 32, marginBottom: 12, color: 'var(--fg-0)'}}>Nasıl Okunur?</h2>
          <p>ADX yükseliyorsa piyasa daha trendli davranıyor olabilir. Düşen ADX, yönlü hareketin zayıfladığını veya piyasanın yataya döndüğünü gösterebilir.</p>

          <div style={{display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginTop: 24, padding: '16px 0', borderTop: '1px solid var(--line-2)', borderBottom: '1px solid var(--line-2)'}}>
            <button className="btn">← Önceki: Aktif vs Pasif</button>
            <button className="btn primary" style={{justifyContent: 'flex-end'}}>Sonraki: Algoritmik Trade →</button>
          </div>
        </div>
      </div>
    </div>
  );
}

// ============== MALİ ANALİZ ==============
function MaliScreen() {
  const [activeSym, setActiveSym] = useStateS3('THYAO');
  const [tab, setTab] = useStateS3('overview');
  const [q, setQ] = useStateS3('');

  const filtered = COMPANIES.filter(c => !q || c.sym.toLowerCase().includes(q.toLowerCase()) || c.name.toLowerCase().includes(q.toLowerCase()));
  const active = COMPANIES.find(c => c.sym === activeSym) || COMPANIES[0];

  return (
    <div className="screen" style={{display: 'flex', flexDirection: 'column'}}>
      <div className="subbar">
        <div className="subbar-group">
          <span className="panel-title" style={{color: 'var(--amber)'}}>Mali Analiz</span>
          <span className="dim">{active.name} <span className="mono" style={{color: 'var(--cyan)'}}>{active.sym}</span></span>
        </div>
        <div className="subbar-spacer"/>
        <div className="subbar-group">
          <input placeholder="THYAO" defaultValue="THYAO" style={{background: 'var(--bg-1)', border: '1px solid var(--line-2)', padding: '4px 10px', color: 'var(--fg-0)', fontFamily: 'var(--font-mono)', fontSize: 11, width: 100}}/>
          <button className="subbar-btn">Ara</button>
          <button className="subbar-btn">Grafiği Aç</button>
          <button className="subbar-btn primary" style={{background: 'var(--amber)', color: '#0a0c10', borderColor: 'var(--amber)'}}>Backtest'e Ekle</button>
        </div>
      </div>

      <div style={{flex: 1, display: 'grid', gridTemplateColumns: '240px 1fr', overflow: 'hidden'}}>
        {/* Company list */}
        <div style={{borderRight: '1px solid var(--line-2)', overflow: 'auto', background: 'var(--bg-2)'}}>
          <div className="panel-head" style={{position: 'sticky', top: 0, zIndex: 1}}>
            <input value={q} onChange={e => setQ(e.target.value)} placeholder="Şirket ara..." style={{flex: 1, background: 'var(--bg-1)', border: '1px solid var(--line-2)', padding: '4px 8px', fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--fg-0)'}}/>
          </div>
          {filtered.map(c => (
            <div key={c.sym} onClick={() => setActiveSym(c.sym)} style={{
              padding: '9px 14px',
              borderBottom: '1px solid var(--line-1)',
              cursor: 'pointer',
              background: activeSym === c.sym ? 'var(--bg-3)' : 'transparent',
              borderLeft: activeSym === c.sym ? '2px solid var(--amber)' : '2px solid transparent',
            }}>
              <div className="mono" style={{fontSize: 12, fontWeight: 700, color: activeSym === c.sym ? 'var(--amber)' : 'var(--cyan)'}}>{c.sym}</div>
              <div className="dim" style={{fontSize: 10, marginTop: 1}}>{c.name}</div>
            </div>
          ))}
        </div>

        {/* Detail */}
        <div style={{overflow: 'auto'}}>
          {/* Header */}
          <div style={{padding: '20px 24px', borderBottom: '1px solid var(--line-2)', background: 'var(--bg-1)'}}>
            <div style={{display: 'flex', alignItems: 'baseline', gap: 12}}>
              <span style={{fontFamily: 'var(--font-display)', fontSize: 26, fontWeight: 700, letterSpacing: '-0.02em'}}>{active.name}</span>
              <span className="tag amber">{active.sym}</span>
              <span className="tag up">● Metadata hazır</span>
              <span className="tag" style={{background: 'var(--down-bg)', color: 'var(--down)'}}>● Finansal yok</span>
            </div>
            <div style={{display: 'flex', gap: 20, marginTop: 14, alignItems: 'baseline'}}>
              <div>
                <div className="label">Kapanış</div>
                <div className="mono" style={{fontSize: 22, fontWeight: 600}}>₺312.40</div>
              </div>
              <div>
                <div className="label">Değişim</div>
                <div className="mono up" style={{fontSize: 16, fontWeight: 600}}>+6.54 (+2.14%)</div>
              </div>
              <div>
                <div className="label">Piyasa Değeri</div>
                <div className="mono" style={{fontSize: 16, fontWeight: 600}}>₺{THYAO_FIN.marketCap}</div>
              </div>
              <div>
                <div className="label">F/K</div>
                <div className="mono" style={{fontSize: 16, fontWeight: 600, color: 'var(--up)'}}>{THYAO_FIN.peRatio}</div>
              </div>
              <div>
                <div className="label">PD/DD</div>
                <div className="mono" style={{fontSize: 16, fontWeight: 600}}>{THYAO_FIN.pbRatio}</div>
              </div>
              <div>
                <div className="label">EV/EBITDA</div>
                <div className="mono" style={{fontSize: 16, fontWeight: 600}}>{THYAO_FIN.evEbitda}</div>
              </div>
              <div>
                <div className="label">Beta</div>
                <div className="mono" style={{fontSize: 16, fontWeight: 600, color: 'var(--amber)'}}>{THYAO_FIN.beta}</div>
              </div>
              <div>
                <div className="label">Halka Açıklık</div>
                <div className="mono" style={{fontSize: 16, fontWeight: 600}}>{THYAO_FIN.freeFloat}</div>
              </div>
            </div>
          </div>

          {/* Tabs */}
          <div className="tabs">
            {[
              { id: 'overview', l: 'Şirket Özeti' },
              { id: 'financials', l: 'Finansal Tablolar' },
              { id: 'ratios', l: 'Oranlar' },
              { id: 'history', l: 'Metrik Geçmişi' },
              { id: 'source', l: 'Kaynak Durumu' },
            ].map(t => (
              <div key={t.id} className={`tab ${tab === t.id ? 'active' : ''}`} onClick={() => setTab(t.id)}>{t.l}</div>
            ))}
            <div style={{flex: 1}}/>
          </div>

          {tab === 'overview' && (
            <div style={{padding: 24, display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16}}>
              <div className="panel">
                <div className="panel-head"><span className="panel-title">Gelir & Kâr (M USD)</span></div>
                <div style={{padding: 16}}>
                  <FinBarChart data={THYAO_FIN.rev} secondary={THYAO_FIN.netIncome} labels={['Gelir', 'Net Kâr']}/>
                </div>
              </div>
              <div className="panel">
                <div className="panel-head"><span className="panel-title">EBITDA Marjı (%)</span></div>
                <div style={{padding: 16}}>
                  <FinLineChart data={THYAO_FIN.margin}/>
                </div>
              </div>
              <div className="panel" style={{gridColumn: '1 / span 2'}}>
                <div className="panel-head"><span className="panel-title">Yıllık Özet</span></div>
                <table className="dt">
                  <thead>
                    <tr>
                      <th style={{textAlign:'left'}}>Metrik</th>
                      <th>2021</th><th>2022</th><th>2023</th><th>2024</th><th>2025</th>
                      <th>YoY %</th>
                      <th style={{width: 100}}>Trend</th>
                    </tr>
                  </thead>
                  <tbody>
                    {[
                      { k: 'Gelir (M USD)', d: THYAO_FIN.rev },
                      { k: 'EBITDA', d: THYAO_FIN.ebitda },
                      { k: 'Net Kâr', d: THYAO_FIN.netIncome },
                      { k: 'EBITDA Marjı %', d: THYAO_FIN.margin, suffix: '%' },
                    ].map((row, i) => {
                      const vals = Object.values(row.d);
                      const last = vals[vals.length - 1], prev = vals[vals.length - 2];
                      const yoy = ((last - prev) / prev) * 100;
                      return (
                        <tr key={i}>
                          <td>{row.k}</td>
                          {vals.map((v, j) => <td key={j}>{typeof v === 'number' ? v.toLocaleString('tr-TR') : v}{row.suffix || ''}</td>)}
                          <td className={yoy >= 0 ? 'up' : 'down'}>{yoy >= 0 ? '+' : ''}{yoy.toFixed(1)}%</td>
                          <td><Spark data={vals} w={80} h={20} color={yoy >= 0 ? 'var(--up)' : 'var(--down)'}/></td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {tab === 'financials' && (
            <div style={{padding: 32, textAlign: 'center'}}>
              <div className="empty" style={{padding: 40, alignItems: 'center', justifyContent: 'center'}}>
                <div style={{maxWidth: 480, display: 'flex', flexDirection: 'column', gap: 14, alignItems: 'center'}}>
                  <div className="label">Veri Bağlı Değil</div>
                  <div style={{fontSize: 22, fontWeight: 600, letterSpacing: '-0.01em'}}>Finansal tablo verisi henüz bağlı değil</div>
                  <div className="dim" style={{fontSize: 12, lineHeight: 1.6}}>
                    Bu şirket için KAP/finansal tablo kaynağı bağlandığında oranlar, dönemler ve tablolar burada görünecek.
                  </div>
                  <div style={{display: 'flex', gap: 8}}>
                    <button className="btn primary">KAP'a Bağlan</button>
                    <button className="btn">Manuel Ekle</button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {(tab === 'ratios' || tab === 'history' || tab === 'source') && (
            <div style={{padding: 32, color: 'var(--fg-2)', textAlign: 'center'}}>
              <div className="empty" style={{padding: 40, alignItems: 'center', justifyContent: 'center'}}>
                <div style={{fontSize: 18, color: 'var(--fg-0)'}}>Bu sekme yakında</div>
                <div className="dim" style={{fontSize: 12, marginTop: 6}}>{tab} verileri kaynak bağlandıktan sonra eklenecek.</div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function FinBarChart({ data, secondary, labels }) {
  const years = Object.keys(data);
  const maxV = Math.max(...years.flatMap(y => [data[y], secondary[y]]));
  return (
    <div>
      <div style={{display: 'flex', gap: 12, marginBottom: 12, fontSize: 10, fontFamily: 'var(--font-mono)', textTransform: 'uppercase', letterSpacing: '0.06em'}}>
        <span><span style={{display: 'inline-block', width: 10, height: 10, background: 'var(--amber)', marginRight: 4, verticalAlign: 'middle'}}/>{labels[0]}</span>
        <span><span style={{display: 'inline-block', width: 10, height: 10, background: 'var(--cyan)', marginRight: 4, verticalAlign: 'middle'}}/>{labels[1]}</span>
      </div>
      <div style={{display: 'flex', alignItems: 'flex-end', gap: 14, height: 180}}>
        {years.map(y => (
          <div key={y} style={{flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4}}>
            <div style={{fontSize: 10, fontFamily: 'var(--font-mono)', color: 'var(--fg-1)'}}>{(data[y]/1000).toFixed(1)}k</div>
            <div style={{flex: 1, width: '100%', display: 'flex', alignItems: 'flex-end', gap: 4}}>
              <div style={{flex: 1, background: 'var(--amber)', height: `${(data[y]/maxV)*100}%`, minHeight: 1}}/>
              <div style={{flex: 1, background: 'var(--cyan)', height: `${(secondary[y]/maxV)*100}%`, minHeight: 1}}/>
            </div>
            <div style={{fontSize: 10, fontFamily: 'var(--font-mono)', color: 'var(--fg-3)'}}>{y}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

function FinLineChart({ data }) {
  const years = Object.keys(data);
  const vals = Object.values(data);
  const min = Math.min(...vals), max = Math.max(...vals);
  const range = max - min || 1;
  const W = 380, H = 180;
  const xPx = i => 30 + (i / (vals.length - 1)) * (W - 40);
  const yPx = v => 12 + (1 - (v - min) / range) * (H - 36);
  const pts = vals.map((v, i) => `${xPx(i)},${yPx(v)}`).join(' ');
  return (
    <svg width="100%" height={H} viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none">
      <polygon points={`${xPx(0)},${H-24} ${pts} ${xPx(vals.length-1)},${H-24}`} fill="var(--up)" opacity="0.18"/>
      <polyline points={pts} fill="none" stroke="var(--up)" strokeWidth="1.8"/>
      {vals.map((v, i) => (
        <g key={i}>
          <circle cx={xPx(i)} cy={yPx(v)} r="3" fill="var(--up)"/>
          <text x={xPx(i)} y={yPx(v) - 8} textAnchor="middle" fontSize="10" fontFamily="var(--font-mono)" fill="var(--fg-0)" fontWeight="600">{v.toFixed(1)}%</text>
          <text x={xPx(i)} y={H-8} textAnchor="middle" fontSize="10" fontFamily="var(--font-mono)" fill="var(--fg-3)">{years[i]}</text>
        </g>
      ))}
    </svg>
  );
}

Object.assign(window, { SinyallerScreen, EgitimScreen, MaliScreen });
