// ─── Variante B: Command Center ───────────────────────────────────────────────
// Icon-only sidebar, full-width top bar, prominent KPI row, 2-column layout.

const TracerV2 = ({tweaks={}}) => {
  const accent = tweaks.accent || TC.accent;
  const acDim  = `rgba(240,114,40,0.10)`;
  const acMid  = `rgba(240,114,40,0.22)`;

  const navItems = [
    {icon:'dashboard',label:'Dashboard',active:true},
    {icon:'plusCircle',label:'Nuovo Allenamento'},
    {icon:'users',label:'Atleti'},
    {icon:'body',label:'Mappa Muscolare'},
    {icon:'list',label:'Catalogo Esercizi'},
    {icon:'user',label:'Il mio profilo'},
  ];
  const bottomNav = [
    {icon:'settings',label:'Django Admin'},
    {icon:'help',label:'Guida'},
  ];

  const kpis = [
    {v:'7',  u:'Giorni di streak',             icon:'fire',    c:accent,     d:acDim,        trend:'+2 rispetto scorsa sett.'},
    {v:'147',u:'Sessioni totali',               icon:'barChart',c:TC.success, d:TC.successDim,trend:'+5 questo mese'},
    {v:'27', u:'Serie nell\'ultima sessione',   icon:'zap',     c:TC.blue,    d:TC.blueDim},
    {v:'5',  u:'Allenamenti questa settimana',  icon:'calendar',c:TC.purple,  d:TC.purpleDim, trend:'Su obiettivo'},
  ];

  const iconBtn = (icon, active) => ({
    display:'flex',alignItems:'center',justifyContent:'center',
    width:'100%',height:42,borderRadius:8,cursor:'pointer',
    background: active ? acDim : 'transparent',
    border: active ? `1px solid ${acMid}` : '1px solid transparent',
    transition:'background 0.12s',
  });

  return (
    <div style={{
      display:'flex',width:1440,height:900,background:TC.base,
      fontFamily:"'Space Grotesk',sans-serif",overflow:'hidden',color:TC.text,
    }}>

      {/* ── Icon Sidebar ───────────────────────────────── */}
      <aside style={{
        width:64,flexShrink:0,background:TC.surface,
        borderRight:`1px solid ${TC.border}`,
        display:'flex',flexDirection:'column',alignItems:'center',
        padding:'16px 8px 16px',height:'100%',gap:0,
      }}>
        {/* Logo mark */}
        <div style={{
          width:38,height:38,borderRadius:10,background:accent,
          display:'flex',alignItems:'center',justifyContent:'center',
          fontSize:19,fontWeight:800,color:'#fff',marginBottom:20,flexShrink:0,
        }}>T</div>

        {/* Top nav */}
        <div style={{display:'flex',flexDirection:'column',gap:2,width:'100%'}}>
          {navItems.map((item,i)=>(
            <div key={i} title={item.label} style={iconBtn(item.icon, item.active)}>
              <TIcon name={item.icon} size={18} color={item.active?accent:TC.textMuted}/>
            </div>
          ))}
        </div>

        <div style={{flex:1}}/>

        {/* Bottom nav */}
        <div style={{display:'flex',flexDirection:'column',gap:2,width:'100%',marginBottom:12}}>
          {bottomNav.map((item,i)=>(
            <div key={i} title={item.label} style={iconBtn(item.icon, false)}>
              <TIcon name={item.icon} size={17} color={TC.textMuted}/>
            </div>
          ))}
        </div>

        {/* Avatar */}
        <div style={{
          width:34,height:34,borderRadius:'50%',flexShrink:0,
          background:`linear-gradient(135deg,${accent},#a83010)`,
          display:'flex',alignItems:'center',justifyContent:'center',
          fontSize:14,fontWeight:700,color:'#fff',cursor:'pointer',
        }} title="admin">A</div>
      </aside>

      {/* ── Main ──────────────────────────────────────────── */}
      <main style={{flex:1,display:'flex',flexDirection:'column',overflow:'hidden'}}>

        {/* Top bar */}
        <div style={{
          display:'flex',alignItems:'center',justifyContent:'space-between',
          padding:'0 32px',height:62,flexShrink:0,
          background:TC.surface,borderBottom:`1px solid ${TC.border}`,
        }}>
          <div>
            <div style={{fontSize:10.5,color:TC.textMuted,marginBottom:1,letterSpacing:'0.05em',textTransform:'uppercase',fontWeight:600}}>Dashboard</div>
            <div style={{fontSize:19,fontWeight:700,letterSpacing:'-0.025em'}}>
              Bentornato,&nbsp;<span style={{color:accent}}>admin</span>
            </div>
          </div>
          <div style={{display:'flex',alignItems:'center',gap:10}}>
            <div style={{
              display:'flex',alignItems:'center',gap:7,padding:'7px 12px',
              background:TC.elevated,borderRadius:8,border:`1px solid ${TC.border}`,
            }}>
              <TIcon name="search" size={13} color={TC.textMuted}/>
              <input style={{background:'none',border:'none',outline:'none',fontSize:12,color:TC.text,width:170}}
                placeholder="Cerca allenamento o esercizio..." readOnly/>
            </div>
            <button style={{
              display:'flex',alignItems:'center',gap:7,padding:'8px 18px',
              background:accent,border:'none',borderRadius:8,
              fontSize:13,fontWeight:600,color:'#fff',cursor:'pointer',
            }}>
              <TIcon name="plus" size={13} color="#fff"/>
              Nuovo
            </button>
          </div>
        </div>

        {/* KPI row */}
        <div style={{
          display:'grid',gridTemplateColumns:'repeat(4,1fr)',flexShrink:0,
          borderBottom:`1px solid ${TC.border}`,
        }}>
          {kpis.map((k,i)=>(
            <div key={i} style={{
              padding:'18px 24px',background:TC.surface,
              borderRight:i<3?`1px solid ${TC.border}`:'none',
              display:'flex',alignItems:'center',gap:14,
            }}>
              <div style={{
                width:48,height:48,borderRadius:12,background:k.d,flexShrink:0,
                display:'flex',alignItems:'center',justifyContent:'center',
              }}>
                <TIcon name={k.icon} size={22} color={k.c}/>
              </div>
              <div style={{minWidth:0}}>
                <div style={{fontSize:30,fontWeight:700,color:TC.text,letterSpacing:'-0.04em',lineHeight:1}}>{k.v}</div>
                <div style={{fontSize:10.5,color:TC.textMuted,marginTop:3,whiteSpace:'nowrap',overflow:'hidden',textOverflow:'ellipsis'}}>{k.u}</div>
                {k.trend&&(
                  <div style={{fontSize:10,color:TC.success,marginTop:2,fontWeight:500}}>↑ {k.trend}</div>
                )}
              </div>
            </div>
          ))}
        </div>

        {/* Two-column content */}
        <div style={{flex:1,display:'flex',overflow:'hidden'}}>

          {/* Left: Workout history */}
          <div style={{
            width:'58%',borderRight:`1px solid ${TC.border}`,
            display:'flex',flexDirection:'column',overflow:'hidden',
          }}>
            {/* List header */}
            <div style={{
              display:'flex',alignItems:'center',justifyContent:'space-between',
              padding:'11px 20px',borderBottom:`1px solid ${TC.border}`,flexShrink:0,
            }}>
              <span style={{fontSize:10.5,fontWeight:700,color:TC.textMuted,letterSpacing:'0.08em',textTransform:'uppercase'}}>
                Storico Allenamenti
              </span>
              <div style={{display:'flex',alignItems:'center',gap:7}}>
                <button style={{
                  display:'flex',alignItems:'center',gap:5,
                  background:'none',border:`1px solid ${TC.border}`,borderRadius:6,
                  padding:'4px 10px',fontSize:11,color:TC.textSec,cursor:'pointer',
                }}>
                  <TIcon name="calendar" size={12} color={TC.textMuted}/>
                  Maggio 2026
                </button>
                <div style={{
                  display:'flex',alignItems:'center',gap:6,padding:'4px 10px',
                  background:TC.card,borderRadius:6,border:`1px solid ${TC.border}`,
                }}>
                  <TIcon name="search" size={12} color={TC.textMuted}/>
                  <input style={{background:'none',border:'none',outline:'none',fontSize:11,color:TC.text,width:120}}
                    placeholder="Cerca..." readOnly/>
                </div>
                <button style={{
                  padding:'4px 12px',background:accent,border:'none',
                  borderRadius:6,fontSize:11.5,fontWeight:600,color:'#fff',cursor:'pointer',
                }}>Filtra</button>
              </div>
            </div>
            <div style={{flex:1,overflow:'hidden'}}>
              {WORKOUTS_DATA.map(w=><WorkoutRow key={w.id} workout={w} accent={accent}/>)}
            </div>
          </div>

          {/* Right: Activity + Chart */}
          <div style={{flex:1,display:'flex',flexDirection:'column',overflow:'hidden'}}>

            {/* Heatmap panel */}
            <div style={{
              padding:'14px 20px',borderBottom:`1px solid ${TC.border}`,flexShrink:0,
            }}>
              <div style={{display:'flex',alignItems:'center',justifyContent:'space-between',marginBottom:9}}>
                <span style={{fontSize:10.5,fontWeight:700,color:TC.textMuted,letterSpacing:'0.08em',textTransform:'uppercase'}}>Attività 2026</span>
                <div style={{display:'flex',alignItems:'center',gap:5}}>
                  <button style={{background:'none',border:'none',cursor:'pointer',padding:2}}><TIcon name="chevLeft" size={12} color={TC.textMuted}/></button>
                  <span style={{fontSize:12,fontWeight:600,color:TC.textSec}}>2026</span>
                  <button style={{background:'none',border:'none',cursor:'pointer',padding:2}}><TIcon name="chevRight" size={12} color={TC.textMuted}/></button>
                </div>
              </div>
              {/* Compact heatmap for narrower column */}
              <TracerHeatmap cellSize={8}/>
            </div>

            {/* Chart panel */}
            <div style={{flex:1,padding:'14px 20px',overflow:'hidden'}}>
              <div style={{display:'flex',alignItems:'center',justifyContent:'space-between',marginBottom:10}}>
                <span style={{fontSize:10.5,fontWeight:700,color:TC.textMuted,letterSpacing:'0.08em',textTransform:'uppercase'}}>Progressione Peso</span>
                <select style={{
                  background:TC.card,border:`1px solid ${TC.border}`,
                  color:TC.textSec,borderRadius:6,padding:'3px 9px',
                  fontSize:11,outline:'none',cursor:'pointer',
                }}>
                  <option>T bar row machine</option>
                  <option>Chest Press</option>
                  <option>Squat</option>
                </select>
              </div>
              <TracerWeightChart cw={490} ch={200} accent={accent}/>
            </div>

          </div>
        </div>
      </main>
    </div>
  );
};

Object.assign(window,{TracerV2});
