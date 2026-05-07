/* PiyasaPilot — main app */

const { useState: useStateMain, useEffect: useEffectMain } = React;

const TWEAK_DEFAULTS = /*EDITMODE-BEGIN*/{
  "accent": "amber",
  "fontUI": "Inter Tight",
  "fontMono": "JetBrains Mono",
  "uiScale": 100,
  "showTicker": true,
  "useTabularNums": true,
  "candleStyle": "filled",
  "rowZebra": false,
  "showSparklines": true,
  "showHotkeys": true,
  "borderStyle": "sharp",
  "logoStyle": "block"
}/*EDITMODE-END*/;

const ACCENT_PRESETS = {
  amber:  { '--amber': '#ffb020', '--amber-dim': '#b87a10', '--amber-bg': 'rgba(255,176,32,0.10)' },
  cyan:   { '--amber': '#00d4ff', '--amber-dim': '#0095b8', '--amber-bg': 'rgba(0,212,255,0.10)' },
  green:  { '--amber': '#00c875', '--amber-dim': '#008a52', '--amber-bg': 'rgba(0,200,117,0.10)' },
  purple: { '--amber': '#b78bff', '--amber-dim': '#8b66cc', '--amber-bg': 'rgba(183,139,255,0.10)' },
  red:    { '--amber': '#ff4757', '--amber-dim': '#b8313c', '--amber-bg': 'rgba(255,71,87,0.10)' },
};

function App() {
  const [theme, setTheme] = useStateMain('dark');
  const [active, setActive] = useStateMain('grafik');
  const [activeSym, setActiveSym] = useStateMain('VAKBN');
  const [density, setDensity] = useStateMain('normal'); // dense | normal | cozy
  const [compact, setCompact] = useStateMain(false);

  const [tweaks, setTweak] = useTweaks(TWEAK_DEFAULTS);

  // Apply theme + tweaks
  useEffectMain(() => {
    document.documentElement.setAttribute('data-theme', theme);
    document.documentElement.setAttribute('data-density', density);
    document.documentElement.setAttribute('data-compact', String(compact || !tweaks.showTicker));

    const root = document.documentElement.style;
    const accent = ACCENT_PRESETS[tweaks.accent] || ACCENT_PRESETS.amber;
    Object.entries(accent).forEach(([k, v]) => root.setProperty(k, v));
    root.setProperty('--font-ui', `'${tweaks.fontUI}', system-ui, sans-serif`);
    root.setProperty('--font-mono', `'${tweaks.fontMono}', ui-monospace, monospace`);
    root.setProperty('--font-display', `'${tweaks.fontUI}', system-ui, sans-serif`);

    // ui scale
    document.documentElement.style.fontSize = `${tweaks.uiScale * 0.13}px`;
  }, [theme, density, compact, tweaks]);

  // Keyboard shortcuts
  useEffectMain(() => {
    const handle = (e) => {
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
      const tab = NAV_TABS.find(t => t.shortcut === e.key);
      if (tab) { setActive(tab.id); e.preventDefault(); }
    };
    window.addEventListener('keydown', handle);
    return () => window.removeEventListener('keydown', handle);
  }, []);

  const cycleDensity = () => setDensity(d => d === 'dense' ? 'normal' : d === 'normal' ? 'cozy' : 'dense');

  return (
    <div className="app">
      <Ticker/>
      <TopNav
        active={active} onChange={setActive}
        theme={theme} onTheme={() => setTheme(t => t === 'dark' ? 'light' : 'dark')}
        density={density} onDensity={cycleDensity}
        compact={compact} onCompact={() => setCompact(c => !c)}
      />
      <div className="body">
        <Sidebar activeSym={activeSym} onSelect={setActiveSym}/>
        <div className="main">
          {active === 'grafik' && <GrafikScreen activeSym={activeSym}/>}
          {active === 'portfoy' && <PortfoyScreen/>}
          {active === 'strateji' && <StratejiScreen/>}
          {active === 'tarayici' && <TarayiciScreen/>}
          {active === 'sinyaller' && <SinyallerScreen/>}
          {active === 'egitim' && <EgitimScreen/>}
          {active === 'mali' && <MaliScreen/>}
        </div>
      </div>

      <TweaksPanel title="Tweaks">
        <TweakSection title="Tema & Renk">
          <TweakRadio label="Tema" value={theme} options={[{value:'dark',label:'Karanlık'},{value:'light',label:'Aydınlık'}]} onChange={setTheme}/>
          <TweakSelect label="Vurgu Rengi" value={tweaks.accent} options={[
            {value:'amber',label:'Amber (Bloomberg)'},
            {value:'cyan',label:'Cyan (Quant)'},
            {value:'green',label:'Yeşil (Boğa)'},
            {value:'purple',label:'Mor (Modern)'},
            {value:'red',label:'Kırmızı (Sıcak)'},
          ]} onChange={v => setTweak('accent', v)}/>
        </TweakSection>

        <TweakSection title="Tipografi">
          <TweakSelect label="UI Fontu" value={tweaks.fontUI} options={[
            {value:'Inter Tight',label:'Inter Tight'},
            {value:'IBM Plex Sans',label:'IBM Plex Sans'},
            {value:'Geist',label:'Geist'},
            {value:'system-ui',label:'System UI'},
          ]} onChange={v => setTweak('fontUI', v)}/>
          <TweakSelect label="Mono Font" value={tweaks.fontMono} options={[
            {value:'JetBrains Mono',label:'JetBrains Mono'},
            {value:'IBM Plex Mono',label:'IBM Plex Mono'},
            {value:'Geist Mono',label:'Geist Mono'},
            {value:'ui-monospace',label:'System Mono'},
          ]} onChange={v => setTweak('fontMono', v)}/>
          <TweakSlider label="UI Ölçek" min={85} max={120} step={5} value={tweaks.uiScale} onChange={v => setTweak('uiScale', v)} suffix="%"/>
        </TweakSection>

        <TweakSection title="Yoğunluk & Layout">
          <TweakRadio label="Satır Yoğunluğu" value={density} options={[
            {value:'dense',label:'Sıkı'},{value:'normal',label:'Normal'},{value:'cozy',label:'Ferah'}
          ]} onChange={setDensity}/>
          <TweakToggle label="Üst Ticker" checked={tweaks.showTicker} onChange={v => setTweak('showTicker', v)}/>
          <TweakToggle label="Kısayol Etiketleri" checked={tweaks.showHotkeys} onChange={v => setTweak('showHotkeys', v)}/>
          <TweakToggle label="Sparkline'ları Göster" checked={tweaks.showSparklines} onChange={v => setTweak('showSparklines', v)}/>
        </TweakSection>

        <TweakSection title="Görsel Stil">
          <TweakRadio label="Logo" value={tweaks.logoStyle} options={[
            {value:'block',label:'Blok'},{value:'outline',label:'Çizgi'}
          ]} onChange={v => setTweak('logoStyle', v)}/>
          <TweakRadio label="Mum Stili" value={tweaks.candleStyle} options={[
            {value:'filled',label:'Dolu'},{value:'hollow',label:'İçi Boş'}
          ]} onChange={v => setTweak('candleStyle', v)}/>
        </TweakSection>
      </TweaksPanel>
    </div>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(<App/>);
