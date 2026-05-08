/* workout-components.jsx — shared icons, sidebar, heatmap, cards */
const { useState, useEffect, useMemo } = React;

function useMobile() {
  const [m, setM] = useState(() => window.innerWidth <= 640);
  useEffect(() => {
    const h = () => setM(window.innerWidth <= 640);
    window.addEventListener('resize', h);
    return () => window.removeEventListener('resize', h);
  }, []);
  return m;
}

// ─── Icons ────────────────────────────────────────────────────────────────────
const DashIcon = () => (
  <svg width="15" height="15" viewBox="0 0 15 15" fill="none">
    <rect x="1" y="1" width="5.5" height="5.5" rx="1.2" fill="currentColor"/>
    <rect x="8.5" y="1" width="5.5" height="5.5" rx="1.2" fill="currentColor"/>
    <rect x="1" y="8.5" width="5.5" height="5.5" rx="1.2" fill="currentColor"/>
    <rect x="8.5" y="8.5" width="5.5" height="5.5" rx="1.2" fill="currentColor"/>
  </svg>
);

const PlusIcon = ({ size = 15 }) => (
  <svg width={size} height={size} viewBox="0 0 15 15" fill="none">
    <path d="M7.5 2v11M2 7.5h11" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"/>
  </svg>
);

const ShieldIcon = () => (
  <svg width="15" height="15" viewBox="0 0 15 15" fill="none">
    <path d="M7.5 1.5L2 4.5v3.8c0 3.2 2.5 4.8 5.5 5.2 3-.4 5.5-2 5.5-5.2V4.5L7.5 1.5z" stroke="currentColor" strokeWidth="1.4"/>
    <path d="M5 7.5l2 2 3-3" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
);

const LogoutIcon = () => (
  <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
    <path d="M5.5 2H2.5a1 1 0 0 0-1 1v8a1 1 0 0 0 1 1h3" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round"/>
    <path d="M9.5 10l3-3-3-3M12.5 7H5.5" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
);

const TrashIcon = () => (
  <svg width="13" height="13" viewBox="0 0 13 13" fill="none">
    <path d="M1.5 3h10M4.5 3V1.5h4V3M3 3l.5 8.5h6L10 3" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
);

const ChevronRightIcon = () => (
  <svg width="13" height="13" viewBox="0 0 13 13" fill="none">
    <path d="M4.5 3l4 3.5-4 3.5" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
);

const BackIcon = () => (
  <svg width="15" height="15" viewBox="0 0 15 15" fill="none">
    <path d="M10 3L5 7.5 10 12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
);

// ─── Badge ────────────────────────────────────────────────────────────────────
function Badge({ label }) {
  const palette = {
    petto:     { bg: 'rgba(240,136,62,.1)',   text: '#f0883e', border: 'rgba(240,136,62,.22)' },
    dorso:     { bg: 'rgba(59,184,209,.1)',   text: '#3bb8d1', border: 'rgba(59,184,209,.22)' },
    dorsali:   { bg: 'rgba(59,184,209,.1)',   text: '#3bb8d1', border: 'rgba(59,184,209,.22)' },
    gambe:     { bg: 'rgba(63,185,80,.1)',    text: '#3fb950', border: 'rgba(63,185,80,.22)' },
    glutei:    { bg: 'rgba(63,185,80,.1)',    text: '#3fb950', border: 'rgba(63,185,80,.22)' },
    spalle:    { bg: 'rgba(167,139,250,.1)',  text: '#a78bfa', border: 'rgba(167,139,250,.22)' },
    bicipiti:  { bg: 'rgba(248,171,78,.1)',   text: '#f8ab4e', border: 'rgba(248,171,78,.22)' },
    tricipiti: { bg: 'rgba(248,106,78,.1)',   text: '#f86a4e', border: 'rgba(248,106,78,.22)' },
  };
  const c = palette[label.toLowerCase()] || { bg: 'rgba(136,136,160,.1)', text: '#8888a0', border: 'rgba(136,136,160,.2)' };
  return (
    <span style={{
      padding: '2px 7px', borderRadius: '4px',
      background: c.bg, border: `1px solid ${c.border}`,
      color: c.text, fontSize: '10.5px', fontWeight: 600, whiteSpace: 'nowrap',
    }}>{label}</span>
  );
}

// ─── Sidebar ──────────────────────────────────────────────────────────────────
function Sidebar({ currentPage, navigate, user, onLogout }) {
  const [hovered, setHovered] = useState(null);
  const nav = [
    { id: 'dashboard',   label: 'Dashboard',       icon: <DashIcon /> },
    { id: 'new-session', label: 'Nuovo Allenamento', icon: <PlusIcon /> },
    { id: 'admin',       label: 'Pannello Admin',   icon: <ShieldIcon /> },
  ];
  return (
    <aside className="tracer-sidebar" style={{
      width: '220px', minWidth: '220px', height: '100vh',
      background: '#0c0c0f', borderRight: '1px solid #1c1c26',
      display: 'flex', flexDirection: 'column', position: 'sticky', top: 0,
    }}>
      {/* Logo */}
      <div onClick={() => navigate('dashboard')} style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '22px 18px 18px', borderBottom: '1px solid #17171f', cursor: 'pointer' }}>
        <div style={{
          width: '28px', height: '28px', borderRadius: '7px',
          background: 'linear-gradient(135deg, #f0883e, #c85c1a)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: '13px', fontWeight: 800, color: '#fff',
        }}>T</div>
        <div>
          <div style={{ fontSize: '14px', fontWeight: 700, color: '#f0f0f3', letterSpacing: '-0.3px' }}>Tracer</div>
          <div style={{ fontSize: '9.5px', color: '#444456', fontWeight: 600, letterSpacing: '1px' }}>WORKOUT</div>
        </div>
      </div>

      {/* Nav */}
      <nav style={{ flex: 1, padding: '14px 10px', display: 'flex', flexDirection: 'column', gap: '2px' }}>
        {nav.map(item => {
          const active = currentPage === item.id || (currentPage === 'session-detail' && item.id === 'dashboard');
          const hov = hovered === item.id;
          return (
            <button key={item.id}
              onClick={() => navigate(item.id)}
              onMouseEnter={() => setHovered(item.id)}
              onMouseLeave={() => setHovered(null)}
              style={{
                display: 'flex', alignItems: 'center', gap: '9px',
                padding: '9px 10px', borderRadius: '7px', border: 'none',
                background: active ? 'rgba(240,136,62,.11)' : hov ? 'rgba(255,255,255,.035)' : 'transparent',
                color: active ? '#f0883e' : hov ? '#c0c0d0' : '#60607a',
                cursor: 'pointer', fontSize: '13px',
                fontFamily: "'Space Grotesk', sans-serif", fontWeight: active ? 600 : 500,
                width: '100%', textAlign: 'left', transition: 'all .12s ease',
                boxShadow: active ? 'inset 0 0 0 1px rgba(240,136,62,.18)' : 'none',
              }}>
              {item.icon}
              <span style={{ flex: 1 }}>{item.label}</span>
              {active && <span style={{ width: 5, height: 5, borderRadius: '50%', background: '#f0883e', flexShrink: 0 }} />}
            </button>
          );
        })}
      </nav>

      {/* User */}
      <div style={{ padding: '12px 10px', borderTop: '1px solid #17171f', display: 'flex', alignItems: 'center', gap: '9px' }}>
        <div style={{
          width: '32px', height: '32px', borderRadius: '8px', flexShrink: 0,
          background: 'linear-gradient(135deg, #1e1e2e, #141420)',
          border: '1px solid #28283a',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: '13px', fontWeight: 700, color: '#f0883e',
        }}>{(user?.username || 'U')[0].toUpperCase()}</div>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontSize: '12.5px', fontWeight: 600, color: '#d0d0e0', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{user?.username}</div>
          <div style={{ fontSize: '10px', color: '#404052', fontWeight: 500 }}>{user?.isAdmin ? 'Admin' : 'Atleta'}</div>
        </div>
        <button onClick={onLogout} title="Logout" style={{
          width: '28px', height: '28px', borderRadius: '6px',
          border: '1px solid #1e1e2a', background: 'transparent',
          color: '#444456', display: 'flex', alignItems: 'center', justifyContent: 'center',
          cursor: 'pointer', flexShrink: 0, transition: 'all .12s',
        }}
          onMouseEnter={e => { e.currentTarget.style.color = '#f85149'; e.currentTarget.style.borderColor = 'rgba(248,81,73,.3)'; }}
          onMouseLeave={e => { e.currentTarget.style.color = '#444456'; e.currentTarget.style.borderColor = '#1e1e2a'; }}>
          <LogoutIcon />
        </button>
      </div>
    </aside>
  );
}

// ─── Heatmap ──────────────────────────────────────────────────────────────────
function Heatmap({ sessions }) {
  const [animate, setAnimate] = useState(false);
  const [tooltip, setTooltip] = useState(null); // { text, x, y, above }
  useEffect(() => { const t = setTimeout(() => setAnimate(true), 60); return () => clearTimeout(t); }, []);

  const activityMap = useMemo(() => {
    const map = {};
    sessions.forEach(s => {
      const d = s.date instanceof Date ? s.date : new Date(s.date);
      const key = d.toISOString().split('T')[0];
      map[key] = (map[key] || 0) + s.sets.length;
    });
    return map;
  }, [sessions]);

  const maxAct = Math.max(...Object.values(activityMap), 1);
  const today = new Date();

  const start = new Date(today);
  start.setDate(today.getDate() - 363);
  start.setDate(start.getDate() - start.getDay());

  const weeks = [];
  const monthLabels = [];
  for (let w = 0; w < 53; w++) {
    const days = [];
    for (let d = 0; d < 7; d++) {
      const date = new Date(start);
      date.setDate(start.getDate() + w * 7 + d);
      const key = date.toISOString().split('T')[0];
      const count = activityMap[key] || 0;
      const level = count === 0 ? 0 : count < maxAct * .25 ? 1 : count < maxAct * .55 ? 2 : count < maxAct * .8 ? 3 : 4;
      days.push({ date, key, count, level, future: date > today });
    }
    const first = days[0].date;
    if (w === 0 || first.getDate() <= 7) {
      monthLabels.push({ week: w, label: first.toLocaleDateString('it-IT', { month: 'short' }) });
    }
    weeks.push(days);
  }

  const heat = ['#13131c', '#0e4429', '#006d32', '#26a641', '#39d353'];

  const totalSessions = sessions.length;
  const weekSessions = sessions.filter(s => {
    const d = s.date instanceof Date ? s.date : new Date(s.date);
    return (today - d) < 7 * 86400000;
  }).length;
  let streak = 0;
  for (let i = 0; i < 180; i++) {
    const d = new Date(today); d.setDate(today.getDate() - i);
    if (activityMap[d.toISOString().split('T')[0]]) streak++;
    else if (i > 0) break;
  }

  return (
    <div>
      <div style={{ display: 'flex', gap: '28px', marginBottom: '20px' }}>
        {[
          { v: totalSessions, l: 'Sessioni totali' },
          { v: weekSessions,  l: 'Questa settimana' },
          { v: `${streak}gg`, l: 'Streak corrente' },
        ].map(s => (
          <div key={s.l}>
            <div style={{ fontSize: '24px', fontWeight: 700, color: '#f0f0f3', fontFamily: "'JetBrains Mono', monospace", letterSpacing: '-1px' }}>{s.v}</div>
            <div style={{ fontSize: '10.5px', color: '#444456', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '.6px', marginTop: '2px' }}>{s.l}</div>
          </div>
        ))}
      </div>

      <div style={{ position: 'relative', overflowX: 'auto' }}>
        {/* Month labels */}
        <div style={{ position: 'relative', height: '16px', paddingLeft: '22px', marginBottom: '3px' }}>
          {monthLabels.map((m, i) => (
            <span key={i} style={{
              position: 'absolute', left: `${22 + m.week * 15}px`,
              fontSize: '10px', color: '#3a3a52', fontWeight: 500, whiteSpace: 'nowrap',
            }}>{m.label.charAt(0).toUpperCase() + m.label.slice(1)}</span>
          ))}
        </div>

        <div style={{ display: 'flex', alignItems: 'flex-start' }}>
          {/* Day labels */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '3px', marginRight: '5px' }}>
            {['', 'L', '', 'M', '', 'V', ''].map((l, i) => (
              <div key={i} style={{ height: '12px', fontSize: '9px', color: '#2e2e42', lineHeight: '12px', textAlign: 'right' }}>{l}</div>
            ))}
          </div>

          {/* Grid */}
          <div style={{ display: 'flex', gap: '3px' }}>
            {weeks.map((week, wi) => (
              <div key={wi} style={{ display: 'flex', flexDirection: 'column', gap: '3px' }}>
                {week.map((day, di) => (
                  <div key={di}
                    onMouseEnter={e => {
                      const rect = e.currentTarget.getBoundingClientRect();
                      const above = di <= 2;
                      setTooltip({
                        text: day.count > 0 ? `${day.date.toLocaleDateString('it-IT', { day: 'numeric', month: 'short', year: 'numeric' })}: ${day.count} serie` : day.date.toLocaleDateString('it-IT', { day: 'numeric', month: 'short', year: 'numeric' }),
                        x: rect.left + rect.width / 2,
                        y: above ? rect.bottom + 6 : rect.top - 6,
                        above,
                      });
                    }}
                    onMouseLeave={() => setTooltip(null)}
                    style={{
                      width: '12px', height: '12px', borderRadius: '2.5px',
                      background: day.future ? 'transparent' : heat[day.level],
                      opacity: animate ? 1 : 0,
                      transform: animate ? 'scale(1)' : 'scale(0.2)',
                      transition: `opacity .38s ease ${wi * 5}ms, transform .28s ease ${wi * 5}ms`,
                      cursor: day.count > 0 ? 'pointer' : 'default',
                      boxShadow: day.level === 4 ? '0 0 5px rgba(57,211,83,.35)' : 'none',
                      outline: '1px solid rgba(255,255,255,.02)',
                    }} />
                ))}
              </div>
            ))}
          </div>
        </div>

        {/* Legend */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px', marginTop: '10px', justifyContent: 'flex-end' }}>
          <span style={{ fontSize: '9.5px', color: '#2e2e42' }}>Meno</span>
          {heat.map((c, i) => <div key={i} style={{ width: '10px', height: '10px', borderRadius: '2px', background: c }} />)}
          <span style={{ fontSize: '9.5px', color: '#2e2e42' }}>Di più</span>
        </div>
      </div>

      {/* Custom tooltip */}
      {tooltip && (
        <div style={{
          position: 'fixed',
          left: tooltip.x,
          top: tooltip.above ? tooltip.y : 'auto',
          bottom: tooltip.above ? 'auto' : `calc(100vh - ${tooltip.y}px)`,
          transform: 'translateX(-50%)',
          background: '#1c1c2e',
          border: '1px solid #2e2e48',
          borderRadius: '6px',
          padding: '5px 9px',
          fontSize: '11px',
          color: '#c8c8e0',
          whiteSpace: 'nowrap',
          pointerEvents: 'none',
          zIndex: 9999,
          boxShadow: '0 4px 16px rgba(0,0,0,.5)',
        }}>{tooltip.text}</div>
      )}
    </div>
  );
}

// ─── WorkoutCard ──────────────────────────────────────────────────────────────
function WorkoutCard({ session, onView, onDelete }) {
  const isMobile = useMobile();
  const [hov, setHov] = useState(false);
  const [del, setDel] = useState(false);
  const date = session.date instanceof Date ? session.date : new Date(session.date);
  const exercises = [...new Set(session.sets.map(s => s.exercise))];

  return (
    <div onClick={() => onView(session)}
      onMouseEnter={() => setHov(true)} onMouseLeave={() => setHov(false)}
      style={{
        display: 'flex', alignItems: 'center', gap: '12px',
        padding: '11px 13px', borderRadius: '9px', cursor: 'pointer',
        background: hov ? '#141420' : '#0f0f16',
        border: `1px solid ${hov ? '#252538' : '#18182a'}`,
        transition: 'all .13s ease',
        opacity: del ? 0 : 1, transform: del ? 'translateX(-12px)' : 'none',
      }}>
      {/* Date badge */}
      <div style={{
        minWidth: '42px', textAlign: 'center',
        padding: '6px 7px', borderRadius: '7px',
        background: '#191926', border: '1px solid #222234',
      }}>
        <div style={{ fontSize: '17px', fontWeight: 700, color: '#f0f0f3', fontFamily: "'JetBrains Mono', monospace", lineHeight: 1 }}>{date.getDate()}</div>
        <div style={{ fontSize: '8.5px', color: '#484860', textTransform: 'uppercase', letterSpacing: '.5px', marginTop: '2px' }}>
          {date.toLocaleDateString('it-IT', { month: 'short' })}
        </div>
      </div>

      {/* Info */}
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontSize: '12.5px', color: '#b8b8c8', fontWeight: 500, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
          {exercises.slice(0, 3).join(', ')}{exercises.length > 3 ? ` +${exercises.length - 3}` : ''}
        </div>
        {session.notes && (
          <div style={{ fontSize: '11px', color: '#3c3c52', fontStyle: 'italic', marginTop: '3px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            "{session.notes}"
          </div>
        )}
      </div>

      {/* Sets badge */}
      <div style={{
        padding: '3px 8px', borderRadius: '5px', flexShrink: 0,
        background: 'rgba(240,136,62,.07)', border: '1px solid rgba(240,136,62,.14)',
        fontSize: '11px', fontWeight: 600, color: '#f0883e',
        fontFamily: "'JetBrains Mono', monospace",
      }}>{session.sets.length} serie</div>

      {/* Actions */}
      <div style={{ display: 'flex', gap: '5px', opacity: isMobile || hov ? 1 : 0, transition: 'opacity .13s', flexShrink: 0 }}>
        <button onClick={e => { e.stopPropagation(); onView(session); }} style={{
          width: '26px', height: '26px', borderRadius: '6px',
          border: '1px solid #23233a', background: '#181828', color: '#666680',
          display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer',
        }}><ChevronRightIcon /></button>
        <button onClick={e => { e.stopPropagation(); setDel(true); setTimeout(() => onDelete(session.id), 280); }} style={{
          width: '26px', height: '26px', borderRadius: '6px',
          border: '1px solid rgba(248,81,73,.2)', background: 'rgba(248,81,73,.05)',
          color: '#f85149', display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer',
        }}><TrashIcon /></button>
      </div>
      {!isMobile && <div style={{ color: '#262638', opacity: hov ? 0 : 1, transition: 'opacity .13s', flexShrink: 0 }}><ChevronRightIcon /></div>}
    </div>
  );
}

// ─── BottomNav ────────────────────────────────────────────────────────────────
function BottomNav({ currentPage, navigate, onLogout }) {
  const nav = [
    { id: 'dashboard',   label: 'Home',   icon: <DashIcon /> },
    { id: 'new-session', label: 'Allena', icon: <PlusIcon /> },
    { id: 'admin',       label: 'Admin',  icon: <ShieldIcon /> },
  ];
  return (
    <nav className="tracer-bottom-nav" style={{
      position: 'fixed', bottom: 0, left: 0, right: 0, height: '60px',
      background: '#0c0c0f', borderTop: '1px solid #1c1c26',
      paddingBottom: 'env(safe-area-inset-bottom)', zIndex: 100,
    }}>
      {nav.map(item => {
        const active = currentPage === item.id || (currentPage === 'session-detail' && item.id === 'dashboard');
        return (
          <button key={item.id} onClick={() => navigate(item.id)} style={{
            flex: 1, height: '100%', display: 'flex', flexDirection: 'column',
            alignItems: 'center', justifyContent: 'center', gap: '3px',
            border: 'none', background: 'transparent',
            color: active ? '#f0883e' : '#454560',
            fontSize: '9.5px', fontFamily: "'Space Grotesk', sans-serif",
            fontWeight: active ? 600 : 500, cursor: 'pointer',
          }}>
            {item.icon}
            {item.label}
          </button>
        );
      })}
      <button onClick={onLogout} style={{
        flex: 1, height: '100%', display: 'flex', flexDirection: 'column',
        alignItems: 'center', justifyContent: 'center', gap: '3px',
        border: 'none', background: 'transparent',
        color: '#454560', fontSize: '9.5px', fontFamily: "'Space Grotesk', sans-serif",
        fontWeight: 500, cursor: 'pointer',
      }}>
        <LogoutIcon />
        Esci
      </button>
    </nav>
  );
}

// Export all
Object.assign(window, {
  Sidebar, BottomNav, Heatmap, WorkoutCard, Badge, useMobile,
  DashIcon, PlusIcon, ShieldIcon, LogoutIcon, TrashIcon,
  ChevronRightIcon, BackIcon,
});
