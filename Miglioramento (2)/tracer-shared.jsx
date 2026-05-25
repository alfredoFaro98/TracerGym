// ─── Tracer shared tokens, data, and base components ───────────────────────

const TC = {
  base:'#0c0c0e', surface:'#131316', elevated:'#1a1a1e',
  card:'#1f1f25', hover:'#26262e', border:'#28282f', borderSub:'#1c1c22',
  text:'#eeeeF2', textSec:'#6868a0', textMuted:'#3e3e56',
  accent:'#F07228', accentDim:'rgba(240,114,40,0.10)', accentMid:'rgba(240,114,40,0.28)',
  success:'#3dd68c', successDim:'rgba(61,214,140,0.10)',
  blue:'#5B9EFF', blueDim:'rgba(91,158,255,0.10)',
  purple:'#ab6cf7', purpleDim:'rgba(171,108,247,0.10)',
  red:'#f43f5e', redDim:'rgba(244,63,94,0.10)',
};

const MUSCLE_COLORS = {
  back:'#5B9EFF', chest:'#F07228', legs:'#3dd68c',
  core:'#ab6cf7', shoulders:'#f59e0b', arms:'#f43f5e',
};

const WORKOUTS_DATA = [
  {id:1,date:23,month:'MAG',dayName:'Sabato',   series:2,  tags:['PLANK','CRUNCH'],muscle:'core'},
  {id:2,date:22,month:'MAG',dayName:'Venerdì',  series:27, tags:['LAT MACHINE LARGA PRONA','CABLE LAT PUSHDOWN','ILIAC PULL DOWN CAVO'],extra:12,muscle:'back'},
  {id:3,date:21,month:'MAG',dayName:'Giovedì',  series:35, tags:['CHEST PRESS','PECTORAL MACHINE – PEC FLY','PULL DOWN CORDA IN GINOCCHIO'],extra:17,muscle:'chest'},
  {id:4,date:20,month:'MAG',dayName:'Mercoledì',series:28, tags:['PRESSA VERTICALE','ADDUCTOR MACHINE','ADDUCTOR MACHINE'],extra:9,muscle:'legs'},
  {id:5,date:19,month:'MAG',dayName:'Martedì',  series:27, tags:['LAT MACHINE LARGA PRONA','CABLE LAT PUSHDOWN','ILIAC PULL DOWN'],extra:12,muscle:'back'},
  {id:6,date:18,month:'MAG',dayName:'Lunedì',   series:22, tags:['SQUAT','LEG PRESS','CALF RAISE'],extra:5,muscle:'legs'},
];

const WEIGHT_PTS = [
  {x:'Feb',y:33},{x:'Mar 1',y:33.8},{x:'Mar 15',y:34.5},{x:'Apr 1',y:35.2},
  {x:'Apr 20',y:36},{x:'Mag 5',y:37.2},{x:'Mag 12',y:38.4},{x:'Mag 22',y:39.5},
];

// ─── Heatmap data (Mon Dec 29 2025 → 53 weeks) ──────────────────────────────
const HEATMAP_DATA = (()=>{
  const active = {
    '2026-01-07':2,'2026-01-14':2,'2026-01-21':1,'2026-01-28':2,
    '2026-02-03':2,'2026-02-04':3,'2026-02-10':2,'2026-02-11':2,'2026-02-17':3,'2026-02-18':2,'2026-02-24':2,
    '2026-03-02':3,'2026-03-03':2,'2026-03-04':3,'2026-03-09':3,'2026-03-10':2,'2026-03-11':3,
    '2026-03-16':3,'2026-03-17':2,'2026-03-18':4,'2026-03-19':3,'2026-03-23':3,'2026-03-25':3,'2026-03-30':2,'2026-03-31':3,
    '2026-04-01':3,'2026-04-06':3,'2026-04-07':4,'2026-04-08':3,'2026-04-13':3,'2026-04-14':2,'2026-04-15':3,
    '2026-04-20':4,'2026-04-21':3,'2026-04-22':4,'2026-04-27':3,'2026-04-28':4,'2026-04-29':3,'2026-04-30':2,
    '2026-05-04':3,'2026-05-05':4,'2026-05-06':3,'2026-05-11':3,'2026-05-12':4,'2026-05-13':3,'2026-05-14':2,
    '2026-05-18':2,'2026-05-19':3,'2026-05-20':3,'2026-05-21':4,'2026-05-22':3,
  };
  const today = new Date(2026,4,22);
  const d = new Date(2025,11,29);
  const weeks = [];
  while(weeks.length < 53){
    const week=[];
    for(let i=0;i<7;i++){
      const y=d.getFullYear(),mo=d.getMonth()+1,dy=d.getDate();
      const key=`${y}-${String(mo).padStart(2,'0')}-${String(dy).padStart(2,'0')}`;
      week.push({key,level:active[key]||0,inYear:y===2026,future:new Date(d)>today});
      d.setDate(d.getDate()+1);
    }
    weeks.push(week);
  }
  return weeks;
})();

// ─── Icons ──────────────────────────────────────────────────────────────────
const TIcon = ({name,size=16,color='currentColor',sw=1.75})=>{
  const p={
    dashboard:<><rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/></>,
    plus:<><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></>,
    plusCircle:<><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="16"/><line x1="8" y1="12" x2="16" y2="12"/></>,
    users:<><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></>,
    body:<><circle cx="12" cy="5" r="2"/><path d="M12 7v5"/><path d="M9 10l3 2 3-2"/><path d="M9 20v-4l3 1.5 3-1.5v4"/></>,
    list:<><line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/></>,
    user:<><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></>,
    settings:<><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></>,
    help:<><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/></>,
    fire:<><path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 0 0 2.5 2.5z"/></>,
    barChart:<><line x1="12" y1="20" x2="12" y2="10"/><line x1="18" y1="20" x2="18" y2="4"/><line x1="6" y1="20" x2="6" y2="16"/></>,
    calendar:<><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></>,
    search:<><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></>,
    copy:<><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></>,
    trash:<><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"/></>,
    eye:<><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></>,
    download:<><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></>,
    upload:<><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></>,
    chevLeft:<polyline points="15 18 9 12 15 6"/>,
    chevRight:<polyline points="9 18 15 12 9 6"/>,
    zap:<polyline points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>,
    trendUp:<><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/></>,
    logout:<><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></>,
    menu:<><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="18" x2="21" y2="18"/></>,
  };
  return(
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth={sw} strokeLinecap="round" strokeLinejoin="round">
      {p[name]||null}
    </svg>
  );
};

// ─── WorkoutRow ──────────────────────────────────────────────────────────────
const WorkoutRow = ({workout, accent})=>{
  const [hov,setHov]=React.useState(false);
  const mc=MUSCLE_COLORS[workout.muscle]||TC.accent;
  const tags=workout.tags.slice(0,3);
  const acc=accent||TC.accent;
  const acDim=`rgba(240,114,40,0.10)`;
  return(
    <div
      onMouseEnter={()=>setHov(true)} onMouseLeave={()=>setHov(false)}
      style={{
        display:'flex',alignItems:'center',gap:14,padding:'10px 20px',
        borderBottom:`1px solid ${TC.borderSub}`,
        background:hov?TC.hover:'transparent',transition:'background 0.12s',cursor:'pointer',
      }}
    >
      <div style={{width:46,flexShrink:0,display:'flex',flexDirection:'column',alignItems:'center',gap:2}}>
        <div style={{width:7,height:7,borderRadius:'50%',background:mc}}/>
        <div style={{fontSize:21,fontWeight:700,color:TC.text,lineHeight:1,letterSpacing:'-0.03em'}}>{workout.date}</div>
        <div style={{fontSize:9.5,color:TC.textMuted,fontWeight:600,letterSpacing:'0.06em'}}>{workout.month}</div>
      </div>
      <div style={{flex:1,minWidth:0}}>
        <div style={{display:'flex',alignItems:'center',gap:8,marginBottom:4}}>
          <span style={{fontSize:13.5,fontWeight:600,color:TC.text}}>{workout.dayName}</span>
          <span style={{fontSize:11,color:TC.textMuted,fontWeight:400}}>{workout.series} serie</span>
        </div>
        <div style={{display:'flex',alignItems:'center',gap:3,flexWrap:'wrap'}}>
          {tags.map((t,ti)=>(
            <span key={ti} style={{
              fontSize:10.5,fontWeight:500,padding:'2px 7px',borderRadius:4,
              background:TC.card,color:TC.textSec,border:`1px solid ${TC.border}`,
              maxWidth:190,overflow:'hidden',textOverflow:'ellipsis',whiteSpace:'nowrap',
            }}>{t}</span>
          ))}
          {workout.extra&&(
            <span style={{
              fontSize:10.5,fontWeight:600,padding:'2px 7px',borderRadius:4,
              background:acDim,color:acc,
            }}>+{workout.extra}</span>
          )}
        </div>
      </div>
      <div style={{display:'flex',gap:4,opacity:hov?1:0,transition:'opacity 0.12s',flexShrink:0}}>
        {[
          {icon:'eye',bg:TC.card,border:`1px solid ${TC.border}`,color:TC.textSec},
          {icon:'copy',bg:TC.card,border:`1px solid ${TC.border}`,color:TC.textSec},
          {icon:'trash',bg:TC.redDim,border:'1px solid rgba(244,63,94,0.18)',color:TC.red},
        ].map(({icon,bg,border,color})=>(
          <button key={icon} style={{
            width:28,height:28,borderRadius:6,display:'flex',alignItems:'center',
            justifyContent:'center',cursor:'pointer',background:bg,border,
          }}>
            <TIcon name={icon} size={13} color={color}/>
          </button>
        ))}
      </div>
    </div>
  );
};

// ─── Heatmap ─────────────────────────────────────────────────────────────────
const TracerHeatmap = ({cellSize=10})=>{
  const cs=cellSize,gap=2,stride=cs+gap;
  const lc=['#1a1a22','rgba(240,114,40,0.18)','rgba(240,114,40,0.42)','rgba(240,114,40,0.7)','#F07228'];
  const ml=[
    {w:0,l:'Gen'},{w:4,l:'Feb'},{w:9,l:'Mar'},{w:13,l:'Apr'},
    {w:17,l:'Mag'},{w:22,l:'Giu'},{w:26,l:'Lug'},{w:31,l:'Ago'},
    {w:35,l:'Set'},{w:39,l:'Ott'},{w:44,l:'Nov'},{w:48,l:'Dic'},
  ];
  return(
    <div style={{display:'inline-block',userSelect:'none'}}>
      <div style={{position:'relative',height:14,marginBottom:4}}>
        {ml.map(({w,l})=>(
          <span key={l} style={{position:'absolute',left:w*stride,fontSize:9.5,color:TC.textMuted,fontWeight:500}}>{l}</span>
        ))}
      </div>
      <div style={{display:'flex',gap}}>
        {HEATMAP_DATA.map((week,wi)=>(
          <div key={wi} style={{display:'flex',flexDirection:'column',gap}}>
            {week.map((day,di)=>(
              <div key={di} title={day.level>0?day.key:''} style={{
                width:cs,height:cs,borderRadius:2,
                background:!day.inYear||day.future?'transparent':lc[day.level],
                opacity:day.future?0.2:1,
              }}/>
            ))}
          </div>
        ))}
      </div>
      <div style={{display:'flex',alignItems:'center',gap:4,marginTop:8,justifyContent:'flex-end'}}>
        <span style={{fontSize:9.5,color:TC.textMuted}}>Meno</span>
        {lc.map((c,i)=><div key={i} style={{width:9,height:9,borderRadius:2,background:c,border:i===0?`1px solid ${TC.border}`:'none'}}/>)}
        <span style={{fontSize:9.5,color:TC.textMuted}}>Di più</span>
      </div>
    </div>
  );
};

// ─── Weight chart ────────────────────────────────────────────────────────────
const TracerWeightChart = ({cw=1080,ch=110,accent})=>{
  const data=WEIGHT_PTS;
  const acc=accent||'#F07228';
  const pad={t:8,r:12,b:26,l:32};
  const iw=cw-pad.l-pad.r, ih=ch-pad.t-pad.b;
  const mn=31.5,mx=41;
  const xs=i=>(i/(data.length-1))*iw;
  const ys=v=>ih-((v-mn)/(mx-mn))*ih;
  const pts=data.map((d,i)=>`${xs(i).toFixed(1)},${ys(d.y).toFixed(1)}`).join(' ');
  const area=`0,${ih} ${pts} ${xs(data.length-1).toFixed(1)},${ih}`;
  const uid=`wg${Math.round(cw)}`;
  return(
    <svg width={cw} height={ch} style={{display:'block',overflow:'visible'}}>
      <defs>
        <linearGradient id={uid} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={acc} stopOpacity="0.2"/>
          <stop offset="100%" stopColor={acc} stopOpacity="0"/>
        </linearGradient>
      </defs>
      <g transform={`translate(${pad.l},${pad.t})`}>
        {[32,34,36,38,40].map(v=>(
          <g key={v}>
            <line x1={0} y1={ys(v).toFixed(1)} x2={iw} y2={ys(v).toFixed(1)} stroke={TC.border} strokeDasharray="2,6" strokeWidth="1"/>
            <text x={-6} y={ys(v)+4} fontSize={9} fill={TC.textMuted} textAnchor="end">{v}</text>
          </g>
        ))}
        <polygon points={area} fill={`url(#${uid})`}/>
        <polyline points={pts} fill="none" stroke={acc} strokeWidth="2.5" strokeLinejoin="round" strokeLinecap="round"/>
        {data.map((d,i)=>(
          <circle key={i} cx={xs(i).toFixed(1)} cy={ys(d.y).toFixed(1)} r={3.5} fill={acc} stroke={TC.elevated} strokeWidth="1.5"/>
        ))}
        {data.filter((_,i)=>i%2===0).map((d,idx)=>{
          const i=idx*2;
          return <text key={i} x={xs(i).toFixed(1)} y={ih+18} fontSize={9} fill={TC.textMuted} textAnchor="middle">{d.x}</text>;
        })}
      </g>
    </svg>
  );
};

Object.assign(window,{TC,MUSCLE_COLORS,WORKOUTS_DATA,WEIGHT_PTS,HEATMAP_DATA,TIcon,WorkoutRow,TracerHeatmap,TracerWeightChart});
