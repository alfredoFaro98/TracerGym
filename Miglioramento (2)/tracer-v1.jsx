// ─── Variante A: Raffinato ────────────────────────────────────────────────────
// Same layout structure as original, significantly elevated in every detail.

const TracerV1 = ({tweaks={}}) => {
  const accent = tweaks.accent || TC.accent;
  const acDim  = `rgba(240,114,40,0.10)`;

  const navGroups = [
    { items:[
      {icon:'dashboard',label:'Dashboard',active:true},
      {icon:'plusCircle',label:'Nuovo Allenamento'},
    ]},
    { label:'GESTIONE', items:[
      {icon:'users',label:'Atleti'},
      {icon:'body',label:'Mappa Muscolare'},
      {icon:'list',label:'Catalogo Esercizi'},
    ]},
    { label:'ACCOUNT', items:[
      {icon:'user',label:'Il mio profilo'},
    ]},
    { label:'ADMIN', items:[
      {icon:'settings',label:'Django Admin'},
      {icon:'help',label:'Guida'},
    ]},
  ];

  const kpis = [
    {v:'7',  u:'gg streak',       icon:'fire',     c:accent,      d:acDim},
    {v:'5',  u:'questa sett.',    icon:'calendar', c:TC.blue,     d:TC.blueDim},
    {v:'147',u:'sessioni totali', icon:'barChart', c:TC.success,  d:TC.successDim},
    {v:'35', u:'serie ieri',      icon:'zap',      c:TC.purple,   d:TC.purpleDim},
  ];

  return (
    <div style={{
      display:'flex',width:1440,height:900,background:TC.base,
      fontFamily:"'Space Grotesk',sans-serif",overflow:'hidden',color:TC.text,
    }}>

      {/* ── Sidebar ───────────────────────────────────────── */}
      <aside style={{
        width:224,flexShrink:0,background:TC.surface,
        borderRight:`1px solid ${TC.border}`,
        display:'flex',flexDirection:'column',height:'100%',
      }}>
        {/* Logo */}
        <div style={{padding:'20px 20px 18px',borderBottom:`1px solid ${TC.border}`}}>
          <div style={{display:'flex',alignItems:'center',gap:10}}>
            <div style={{
              width:34,height:34,borderRadius:9,background:accent,flexShrink:0,
              display:'flex',alignItems:'center',justifyContent:'center',
              fontSize:17,fontWeight:800,color:'#fff',letterSpacing:'-0.02em',
            }}>T</div>
            <div>
              <div style={{fontSize:14.5,fontWeight:700,color:TC.text,letterSpacing:'-0.015em',lineHeight:1.2}}>Tracer</div>
              <div style={{fontSize:9,color:TC.textMuted,fontWeight:600,letterSpacing:'0.1em',textTransform:'uppercase',marginTop:2}}>Workout Tracker</div>
            </div>
          </div>
        </div>

        {/* Nav groups */}
        <nav style={{flex:1,padding:'8px 0'}}>
          {navGroups.map((g,gi)=>(
            <div key={gi} style={{marginBottom:4}}>
              {g.label&&(
                <div style={{padding:'12px 20px 4px',fontSize:9,fontWeight:700,
                  color:TC.textMuted,letterSpacing:'0.12em',textTransform:'uppercase'}}>
                  {g.label}
                </div>
              )}
              {g.items.map((item,ii)=>(
                <div key={ii} style={{
                  display:'flex',alignItems:'center',gap:10,padding:'8px 20px',
                  cursor:'pointer',
                  background:item.active?acDim:'transparent',
                  borderLeft:item.active?`2px solid ${accent}`:'2px solid transparent',
                  color:item.active?TC.text:TC.textSec,
                  fontSize:13,fontWeight:item.active?600:400,
                  transition:'background 0.1s',
                }}>
                  <TIcon name={item.icon} size={15} color={item.active?accent:TC.textMuted}/>
                  {item.label}
                </div>
              ))}
            </div>
          ))}
        </nav>

        {/* User footer */}
        <div style={{
          padding:'12px 16px',borderTop:`1px solid ${TC.border}`,
          display:'flex',alignItems:'center',gap:10,
        }}>
          <div style={{
            width:30,height:30,borderRadius:'50%',flexShrink:0,
            background:`linear-gradient(135deg,${accent},#a83010)`,
            display:'flex',alignItems:'center',justifyContent:'center',
            fontSize:13,fontWeight:700,color:'#fff',
          }}>A</div>
          <div style={{flex:1,minWidth:0}}>
            <div style={{fontSize:12.5,fontWeight:600,color:TC.text}}>admin</div>
            <div style={{fontSize:10,color:TC.textMuted}}>Atleta</div>
          </div>
          <TIcon name="logout" size={15} color={TC.textMuted}/>
        </div>
      </aside>

      {/* ── Main ──────────────────────────────────────────── */}
      <main style={{flex:1,display:'flex',flexDirection:'column',overflow:'hidden'}}>

        {/* Header */}
        <div style={{
          padding:'24px 32px 0',flexShrink:0,
          display:'flex',alignItems:'flex-start',justifyContent:'space-between',
        }}>
          <div>
            <h1 style={{margin:0,fontSize:25,fontWeight:700,letterSpacing:'-0.025em',color:TC.text}}>
              Bentornato,&nbsp;<span style={{color:accent}}>admin</span>
            </h1>
            <p style={{margin:'4px 0 0',fontSize:12.5,color:TC.textMuted}}>
              Ecco il riepilogo dei tuoi allenamenti.
            </p>
          </div>
          <button style={{
            display:'flex',alignItems:'center',gap:7,padding:'9px 18px',
            background:accent,border:'none',borderRadius:8,
            fontSize:13,fontWeight:600,color:'#fff',cursor:'pointer',
          }}>
            <TIcon name="plus" size={14} color="#fff"/>
            Nuovo Allenamento
          </button>
        </div>

        {/* KPI strip */}
        <div style={{display:'flex',gap:10,padding:'14px 32px',flexShrink:0}}>
          {kpis.map((k,i)=>(
            <div key={i} style={{
              flex:1,display:'flex',alignItems:'center',gap:11,
              padding:'11px 14px',background:TC.elevated,
              borderRadius:10,border:`1px solid ${TC.border}`,
            }}>
              <div style={{
                width:36,height:36,borderRadius:9,background:k.d,flexShrink:0,
                display:'flex',alignItems:'center',justifyContent:'center',
              }}>
                <TIcon name={k.icon} size={17} color={k.c}/>
              </div>
              <div>
                <div style={{fontSize:22,fontWeight:700,color:TC.text,letterSpacing:'-0.04em',lineHeight:1}}>{k.v}</div>
                <div style={{fontSize:10.5,color:TC.textMuted,marginTop:2}}>{k.u}</div>
              </div>
            </div>
          ))}
        </div>

        {/* Content */}
        <div style={{flex:1,overflow:'hidden',padding:'0 32px 24px',display:'flex',flexDirection:'column',gap:12}}>

          {/* Heatmap */}
          <div style={{background:TC.elevated,borderRadius:12,border:`1px solid ${TC.border}`,padding:'14px 20px',flexShrink:0}}>
            <div style={{display:'flex',alignItems:'center',justifyContent:'space-between',marginBottom:10}}>
              <span style={{fontSize:10.5,fontWeight:700,color:TC.textMuted,letterSpacing:'0.08em',textTransform:'uppercase'}}>Attività</span>
              <div style={{display:'flex',alignItems:'center',gap:6}}>
                <button style={{background:'none',border:'none',cursor:'pointer',padding:3,color:TC.textMuted}}>
                  <TIcon name="chevLeft" size={13} color={TC.textMuted}/>
                </button>
                <span style={{fontSize:12.5,fontWeight:600,color:TC.text}}>2026</span>
                <button style={{background:'none',border:'none',cursor:'pointer',padding:3,color:TC.textMuted}}>
                  <TIcon name="chevRight" size={13} color={TC.textMuted}/>
                </button>
              </div>
            </div>
            <TracerHeatmap cellSize={9}/>
          </div>

          {/* History */}
          <div style={{background:TC.elevated,borderRadius:12,border:`1px solid ${TC.border}`,overflow:'hidden',flexShrink:0}}>
            <div style={{
              display:'flex',alignItems:'center',justifyContent:'space-between',
              padding:'12px 20px',borderBottom:`1px solid ${TC.border}`,
            }}>
              <span style={{fontSize:10.5,fontWeight:700,color:TC.textMuted,letterSpacing:'0.08em',textTransform:'uppercase'}}>
                Storico Allenamenti
              </span>
              <div style={{display:'flex',alignItems:'center',gap:8}}>
                <button style={{background:'none',border:'none',cursor:'pointer'}}><TIcon name="download" size={14} color={TC.textMuted}/></button>
                <button style={{background:'none',border:'none',cursor:'pointer'}}><TIcon name="upload" size={14} color={TC.textMuted}/></button>
                <div style={{
                  display:'flex',alignItems:'center',gap:6,padding:'5px 10px',
                  background:TC.card,borderRadius:6,border:`1px solid ${TC.border}`,
                }}>
                  <TIcon name="search" size={12} color={TC.textMuted}/>
                  <input style={{background:'none',border:'none',outline:'none',fontSize:11.5,color:TC.text,width:155}}
                    placeholder="Cerca esercizio o note..." readOnly/>
                </div>
                <button style={{
                  padding:'5px 12px',background:accent,border:'none',
                  borderRadius:6,fontSize:12,fontWeight:600,color:'#fff',cursor:'pointer',
                }}>Filtra</button>
              </div>
            </div>
            {WORKOUTS_DATA.map(w=><WorkoutRow key={w.id} workout={w} accent={accent}/>)}
          </div>

          {/* Weight chart */}
          <div style={{background:TC.elevated,borderRadius:12,border:`1px solid ${TC.border}`,padding:'14px 20px',flexShrink:0}}>
            <div style={{display:'flex',alignItems:'center',justifyContent:'space-between',marginBottom:10}}>
              <span style={{fontSize:10.5,fontWeight:700,color:TC.textMuted,letterSpacing:'0.08em',textTransform:'uppercase'}}>Andamento Peso</span>
              <select style={{
                background:TC.card,border:`1px solid ${TC.border}`,
                color:TC.textSec,borderRadius:6,padding:'4px 10px',
                fontSize:11.5,outline:'none',cursor:'pointer',
              }}>
                <option>T bar row machine</option>
                <option>Chest Press</option>
                <option>Squat</option>
              </select>
            </div>
            <TracerWeightChart cw={1110} ch={108} accent={accent}/>
          </div>

        </div>
      </main>
    </div>
  );
};

Object.assign(window,{TracerV1});
