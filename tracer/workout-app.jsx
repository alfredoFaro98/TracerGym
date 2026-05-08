/* workout-app.jsx — pages + app shell */
const { useState, useEffect, useCallback, useMemo, useRef } = React;

// ─── Seed data ────────────────────────────────────────────────────────────────
const ALL_EXERCISES = [
  { name: 'Panca Piana',               tags: ['Petto', 'Tricipiti'] },
  { name: 'Panca Inclinata',           tags: ['Petto'] },
  { name: 'Croci ai Cavi',             tags: ['Petto'] },
  { name: 'Trazioni',                  tags: ['Dorso', 'Bicipiti'] },
  { name: 'Lat Machine',               tags: ['Dorso'] },
  { name: 'Rematore con Bilanciere',   tags: ['Dorso'] },
  { name: 'Squat',                     tags: ['Gambe', 'Glutei'] },
  { name: 'Leg Press',                 tags: ['Gambe'] },
  { name: 'Military Press',            tags: ['Spalle'] },
  { name: 'Alzate Laterali',           tags: ['Spalle'] },
  { name: 'Curl con Bilanciere',       tags: ['Bicipiti'] },
  { name: 'Curl ai Cavi',              tags: ['Bicipiti'] },
  { name: 'Tricep Pushdown',           tags: ['Tricipiti'] },
  { name: 'Dip alle Parallele',        tags: ['Tricipiti', 'Petto'] },
  { name: 'Romanian Deadlift',         tags: ['Gambe', 'Dorsali'] },
  { name: 'Face Pull',                 tags: ['Spalle', 'Dorsali'] },
  { name: 'Hyperextension',            tags: ['Dorsali', 'Glutei'] },
  { name: 'Shoulder Press Manubri',    tags: ['Spalle'] },
  { name: 'Stacchi',                   tags: ['Dorsali', 'Gambe'] },
  { name: 'Affondi',                   tags: ['Gambe', 'Glutei'] },
];

function generateSessions() {
  const sessions = [];
  const today = new Date();
  const notePool = ['Focus forza', 'Buone sensazioni', 'Stanchezza accumulata', 'Volume day', 'Deload', 'Giornata PR', ''];
  let uid = 1;
  for (let ago = 365; ago >= 1; ago--) {
    if (Math.random() > 0.71) {
      const date = new Date(today);
      date.setDate(today.getDate() - ago);
      const exs = [...ALL_EXERCISES].sort(() => Math.random() - .5).slice(0, 3 + Math.floor(Math.random() * 3));
      const sets = [];
      exs.forEach(ex => {
        const n = 3 + Math.floor(Math.random() * 2);
        const bw = 40 + Math.floor(Math.random() * 80);
        const br = 6 + Math.floor(Math.random() * 7);
        for (let i = 0; i < n; i++) {
          sets.push({
            id: `s${uid++}`,
            exercise: ex.name,
            reps: Math.max(1, br + Math.floor(Math.random() * 3) - 1),
            weight: Math.max(5, bw + i * 5),
            rest: [60, 90, 120, 180][Math.floor(Math.random() * 4)],
          });
        }
      });
      sessions.push({
        id: `sess-${uid++}`,
        date,
        notes: notePool[Math.floor(Math.random() * notePool.length)],
        sets,
      });
    }
  }
  return sessions.sort((a, b) => b.date - a.date);
}

// ─── Shared input style ───────────────────────────────────────────────────────
const inputBase = {
  width: '100%', padding: '9px 12px',
  background: '#09090f', border: '1px solid #202030',
  borderRadius: '7px', color: '#f0f0f3',
  fontSize: '13px', fontFamily: "'Space Grotesk', sans-serif",
  outline: 'none', transition: 'border-color .15s',
};

// ─── AuthPage ─────────────────────────────────────────────────────────────────
function AuthPage({ onLogin }) {
  const [mode, setMode]       = useState('login');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError]     = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = e => {
    e.preventDefault();
    if (!username.trim() || !password) { setError('Compila tutti i campi'); return; }
    if (password.length < 4)           { setError('Password troppo corta (min 4 caratteri)'); return; }
    setError(''); setLoading(true);
    setTimeout(() => { setLoading(false); onLogin({ username: username.trim(), isAdmin: username.trim() === 'admin' }); }, 700);
  };

  return (
    <div style={{
      flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center',
      background: '#080809', position: 'relative', overflow: 'hidden',
      padding: '16px',
    }}>
      <div style={{
        position: 'absolute', width: '700px', height: '700px',
        background: 'radial-gradient(circle, rgba(240,136,62,.055) 0%, transparent 65%)',
        top: '50%', left: '50%', transform: 'translate(-50%,-50%)', pointerEvents: 'none',
      }} />
      <div className="page-enter" style={{
        width: '100%', maxWidth: '360px', background: '#0d0d14',
        border: '1px solid #1e1e2c', borderRadius: '14px', padding: '32px',
      }}>
        {/* Logo */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '26px' }}>
          <div style={{
            width: '34px', height: '34px', borderRadius: '9px',
            background: 'linear-gradient(135deg, #f0883e, #c85c1a)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: '16px', fontWeight: 800, color: '#fff',
          }}>T</div>
          <div>
            <div style={{ fontSize: '16px', fontWeight: 700, color: '#f0f0f3' }}>Tracer</div>
            <div style={{ fontSize: '9.5px', color: '#404052', fontWeight: 600, letterSpacing: '1px' }}>WORKOUT TRACKER</div>
          </div>
        </div>

        {/* Mode tabs */}
        <div style={{
          display: 'flex', gap: '4px', padding: '4px',
          background: '#09090f', border: '1px solid #17171f',
          borderRadius: '8px', marginBottom: '22px',
        }}>
          {['login', 'register'].map(m => (
            <button key={m} onClick={() => { setMode(m); setError(''); }} style={{
              flex: 1, padding: '7px', borderRadius: '5px', border: 'none',
              background: mode === m ? '#1c1c2c' : 'transparent',
              color: mode === m ? '#f0f0f3' : '#484860',
              fontSize: '13px', fontFamily: "'Space Grotesk', sans-serif",
              fontWeight: mode === m ? 600 : 400, cursor: 'pointer', transition: 'all .13s',
            }}>{m === 'login' ? 'Accedi' : 'Registrati'}</button>
          ))}
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '11px' }}>
          <input type="text" placeholder="Username" value={username}
            onChange={e => setUsername(e.target.value)} style={inputBase}
            onFocus={e => e.target.style.borderColor = 'rgba(240,136,62,.45)'}
            onBlur={e => e.target.style.borderColor = '#202030'} />
          <input type="password" placeholder="Password" value={password}
            onChange={e => setPassword(e.target.value)} style={inputBase}
            onFocus={e => e.target.style.borderColor = 'rgba(240,136,62,.45)'}
            onBlur={e => e.target.style.borderColor = '#202030'} />
          {error && (
            <div style={{
              fontSize: '11.5px', color: '#f85149', padding: '8px 10px',
              background: 'rgba(248,81,73,.07)', borderRadius: '6px',
              border: '1px solid rgba(248,81,73,.14)',
            }}>{error}</div>
          )}
          <button type="submit" disabled={loading} style={{
            padding: '11px', marginTop: '3px',
            background: loading ? '#161622' : 'linear-gradient(135deg, #f0883e, #c85c1a)',
            border: 'none', borderRadius: '8px',
            color: loading ? '#484860' : '#fff',
            fontSize: '14px', fontFamily: "'Space Grotesk', sans-serif",
            fontWeight: 600, cursor: loading ? 'default' : 'pointer', transition: 'all .15s',
          }}>{loading ? 'Accesso…' : (mode === 'login' ? 'Entra' : 'Crea account')}</button>
        </form>

        <div style={{ marginTop: '16px', textAlign: 'center', fontSize: '11px', color: '#2c2c42' }}>
          Demo: <span style={{ color: '#404058' }}>admin</span> / <span style={{ color: '#404058' }}>1234</span>
        </div>
      </div>
    </div>
  );
}

// ─── DashboardPage ────────────────────────────────────────────────────────────
function DashboardPage({ sessions, user, navigate, onDelete, onView }) {
  const isMobile = useMobile();
  const hour = new Date().getHours();
  const greeting = hour < 12 ? 'Buongiorno' : hour < 18 ? 'Buon pomeriggio' : 'Buonasera';

  return (
    <div className="page-enter" style={{ flex: 1, overflow: 'auto', padding: isMobile ? '16px 14px 80px' : '28px 32px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '26px' }}>
        <div>
          <h1 style={{ fontSize: '21px', fontWeight: 700, color: '#f0f0f3', letterSpacing: '-0.4px', marginBottom: '3px' }}>
            {greeting}, <span style={{ color: '#f0883e' }}>{user.username}</span>
          </h1>
          <p style={{ fontSize: '12.5px', color: '#484860', fontWeight: 400 }}>
            {new Date().toLocaleDateString('it-IT', { weekday: 'long', day: 'numeric', month: 'long' })}
          </p>
        </div>
        <button onClick={() => navigate('new-session')} style={{
          display: 'flex', alignItems: 'center', gap: '7px',
          padding: '9px 16px',
          background: 'linear-gradient(135deg, #f0883e, #c85c1a)',
          border: 'none', borderRadius: '8px',
          color: '#fff', fontSize: '13px',
          fontFamily: "'Space Grotesk', sans-serif", fontWeight: 600, cursor: 'pointer',
        }}>
          <PlusIcon size={13} />{!isMobile && ' Nuovo allenamento'}
        </button>
      </div>

      {/* Heatmap */}
      <div style={{
        background: '#0d0d14', border: '1px solid #191926',
        borderRadius: '12px', padding: '22px 24px', marginBottom: '20px',
      }}>
        <div style={{ fontSize: '11px', fontWeight: 700, color: '#3a3a52', textTransform: 'uppercase', letterSpacing: '1px', marginBottom: '16px' }}>
          Attività Annuale
        </div>
        <Heatmap sessions={sessions} />
      </div>

      {/* Sessions list */}
      <div style={{ background: '#0d0d14', border: '1px solid #191926', borderRadius: '12px', overflow: 'hidden' }}>
        <div style={{
          padding: '14px 18px', borderBottom: '1px solid #16162a',
          display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        }}>
          <div style={{ fontSize: '11px', fontWeight: 700, color: '#3a3a52', textTransform: 'uppercase', letterSpacing: '1px' }}>
            Storico Allenamenti
          </div>
          <span style={{ fontSize: '11px', color: '#303048', fontFamily: "'JetBrains Mono', monospace" }}>
            {sessions.length} sessioni
          </span>
        </div>
        <div style={{ padding: '10px', display: 'flex', flexDirection: 'column', gap: '5px', maxHeight: isMobile ? 'none' : '440px', overflow: isMobile ? 'visible' : 'auto' }}>
          {sessions.length === 0
            ? <div style={{ padding: '36px', textAlign: 'center', color: '#2c2c42', fontSize: '13px' }}>Nessun allenamento. Inizia subito!</div>
            : sessions.map(s => <WorkoutCard key={s.id} session={s} onView={onView} onDelete={onDelete} />)
          }
        </div>
      </div>
    </div>
  );
}

// ─── NewSessionPage ───────────────────────────────────────────────────────────
function NewSessionPage({ navigate, onCreate }) {
  const isMobile = useMobile();
  const [notes, setNotes] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = e => {
    e.preventDefault();
    setLoading(true);
    setTimeout(() => {
      onCreate({ id: `sess-${Date.now()}`, date: new Date(), notes, sets: [] });
    }, 480);
  };

  const quickNotes = ['Focus forza', 'Volume day', 'Deload', 'Buone sensazioni'];

  return (
    <div className="page-enter" style={{ flex: 1, display: 'flex', padding: isMobile ? '16px 14px 80px' : '28px 32px' }}>
      <div style={{ width: isMobile ? '100%' : '460px' }}>
        <button onClick={() => navigate('dashboard')} style={{
          display: 'flex', alignItems: 'center', gap: '6px',
          padding: '6px 10px', marginBottom: '22px',
          background: 'transparent', border: '1px solid #1c1c2c',
          borderRadius: '7px', color: '#4a4a62', fontSize: '12px',
          fontFamily: "'Space Grotesk', sans-serif", cursor: 'pointer',
        }}>
          <BackIcon /> Dashboard
        </button>

        <h1 style={{ fontSize: '21px', fontWeight: 700, color: '#f0f0f3', letterSpacing: '-0.4px', marginBottom: '4px' }}>
          Nuovo Allenamento
        </h1>
        <p style={{ fontSize: '12.5px', color: '#484860', marginBottom: '24px' }}>
          {new Date().toLocaleDateString('it-IT', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })}
        </p>

        <div style={{ background: '#0d0d14', border: '1px solid #191926', borderRadius: '12px', padding: '22px' }}>
          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '10.5px', fontWeight: 700, color: '#3a3a52', textTransform: 'uppercase', letterSpacing: '.7px', marginBottom: '8px' }}>
                Note (opzionale)
              </label>
              <textarea value={notes} onChange={e => setNotes(e.target.value)}
                placeholder="es. Focus forza, Buone sensazioni, Deload…" rows={3}
                style={{ ...inputBase, resize: 'vertical', padding: '10px 12px' }}
                onFocus={e => e.target.style.borderColor = 'rgba(240,136,62,.4)'}
                onBlur={e => e.target.style.borderColor = '#202030'} />
              {/* Quick tags */}
              <div style={{ display: 'flex', gap: '6px', marginTop: '8px', flexWrap: 'wrap' }}>
                {quickNotes.map(n => (
                  <button key={n} type="button" onClick={() => setNotes(n)} style={{
                    padding: '4px 9px', borderRadius: '5px', border: '1px solid #202030',
                    background: notes === n ? 'rgba(240,136,62,.1)' : 'transparent',
                    color: notes === n ? '#f0883e' : '#48486a',
                    fontSize: '11.5px', fontFamily: "'Space Grotesk', sans-serif",
                    cursor: 'pointer', transition: 'all .12s',
                    borderColor: notes === n ? 'rgba(240,136,62,.3)' : '#202030',
                  }}>{n}</button>
                ))}
              </div>
            </div>

            <button type="submit" disabled={loading} style={{
              padding: '12px',
              background: loading ? '#14142a' : 'linear-gradient(135deg, #f0883e, #c85c1a)',
              border: 'none', borderRadius: '8px',
              color: loading ? '#484860' : '#fff',
              fontSize: '14px', fontFamily: "'Space Grotesk', sans-serif",
              fontWeight: 600, cursor: loading ? 'default' : 'pointer', transition: 'all .15s',
            }}>{loading ? 'Avvio sessione…' : '▶  Inizia Sessione'}</button>
          </form>
        </div>
      </div>
    </div>
  );
}

// ─── SessionDetailPage ────────────────────────────────────────────────────────
function SetRow({ set, index, onDelete }) {
  const [hov, setHov] = useState(false);
  const [del, setDel] = useState(false);
  return (
    <tr onMouseEnter={() => setHov(true)} onMouseLeave={() => setHov(false)}
      style={{ background: hov ? '#10101c' : 'transparent', opacity: del ? 0 : 1, transition: 'all .18s' }}>
      <td style={{ padding: '8px 16px', textAlign: 'center' }}>
        <span style={{
          width: '20px', height: '20px', borderRadius: '5px',
          background: '#181826', border: '1px solid #222238',
          display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
          fontSize: '9.5px', fontWeight: 700, color: '#505068',
          fontFamily: "'JetBrains Mono', monospace",
        }}>{index}</span>
      </td>
      <td style={{ padding: '8px 16px', fontSize: '13px', fontWeight: 700, color: '#f0f0f3', fontFamily: "'JetBrains Mono', monospace" }}>{set.reps}</td>
      <td style={{ padding: '8px 16px', fontSize: '13px', color: '#c0c0d8', fontFamily: "'JetBrains Mono', monospace" }}>
        {set.weight} <span style={{ fontSize: '10px', color: '#38384e' }}>kg</span>
      </td>
      <td style={{ padding: '8px 16px', fontSize: '11.5px', color: '#484862', fontFamily: "'JetBrains Mono', monospace" }}>{set.rest}s</td>
      <td style={{ padding: '8px 16px', textAlign: 'right' }}>
        <button onClick={() => { setDel(true); setTimeout(onDelete, 200); }} style={{
          width: '24px', height: '24px', borderRadius: '5px',
          border: '1px solid rgba(248,81,73,.14)',
          background: hov ? 'rgba(248,81,73,.07)' : 'transparent',
          color: hov ? '#f85149' : '#282838',
          display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
          cursor: 'pointer', transition: 'all .12s',
        }}><TrashIcon /></button>
      </td>
    </tr>
  );
}

function SessionDetailPage({ session, exercises, navigate, onAddSet, onDeleteSet }) {
  const isMobile = useMobile();
  const [exInput, setExInput]     = useState('');
  const [reps, setReps]           = useState('');
  const [weight, setWeight]       = useState('');
  const [rest, setRest]           = useState('90');
  const [suggestions, setSugg]    = useState([]);
  const [showSugg, setShowSugg]   = useState(false);
  const [formErr, setFormErr]     = useState('');
  const [lastAdded, setLastAdded] = useState(null);
  const exRef = useRef(null);

  useEffect(() => {
    if (lastAdded) { const t = setTimeout(() => setLastAdded(null), 2800); return () => clearTimeout(t); }
  }, [lastAdded]);

  const onExChange = val => {
    setExInput(val);
    if (val.length >= 2) {
      setSugg(exercises.filter(e => e.name.toLowerCase().includes(val.toLowerCase())).slice(0, 7));
      setShowSugg(true);
    } else setShowSugg(false);
  };

  const pickSugg = name => { setExInput(name); setShowSugg(false); };

  const handleAdd = e => {
    e.preventDefault();
    if (!exInput.trim())                       { setFormErr('Inserisci un esercizio'); return; }
    if (!reps || isNaN(reps) || +reps < 1)     { setFormErr('Ripetizioni non valide'); return; }
    if (weight === '' || isNaN(weight) || +weight < 0) { setFormErr('Peso non valido'); return; }
    setFormErr('');
    const s = { id: `s${Date.now()}`, exercise: exInput.trim(), reps: +reps, weight: +weight, rest: +rest || 90 };
    onAddSet(session.id, s);
    setLastAdded(s);
    setReps(''); setWeight('');
  };

  const date = session.date instanceof Date ? session.date : new Date(session.date);

  // Group by exercise (preserving order)
  const groups = [];
  const seen = [];
  session.sets.forEach(s => {
    if (!seen.includes(s.exercise)) { seen.push(s.exercise); groups.push({ exercise: s.exercise, sets: [] }); }
    groups.find(g => g.exercise === s.exercise).sets.push(s);
  });

  return (
    <div className="page-enter" style={{ flex: 1, overflow: 'auto', padding: isMobile ? '14px 14px 80px' : '28px 32px' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '14px', marginBottom: '24px', flexWrap: 'wrap' }}>
        <button onClick={() => navigate('dashboard')} style={{
          display: 'flex', alignItems: 'center', gap: '5px', padding: '7px 11px',
          background: 'transparent', border: '1px solid #1c1c2c',
          borderRadius: '7px', color: '#484862', fontSize: '12px',
          fontFamily: "'Space Grotesk', sans-serif", cursor: 'pointer',
        }}><BackIcon /> Dashboard</button>
        <div>
          <h1 style={{ fontSize: '17px', fontWeight: 700, color: '#f0f0f3', letterSpacing: '-0.3px' }}>
            {date.toLocaleDateString('it-IT', { weekday: 'long', day: 'numeric', month: 'long' })}
          </h1>
          {session.notes && <p style={{ fontSize: '11.5px', color: '#484862', fontStyle: 'italic', marginTop: '2px' }}>"{session.notes}"</p>}
        </div>
        <div style={{
          marginLeft: 'auto', padding: '6px 12px',
          background: 'rgba(240,136,62,.07)', border: '1px solid rgba(240,136,62,.14)',
          borderRadius: '7px', fontSize: '13px', color: '#f0883e',
          fontWeight: 600, fontFamily: "'JetBrains Mono', monospace",
        }}>{session.sets.length} serie</div>
      </div>

      {/* Two columns */}
      <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '340px 1fr', gap: '18px', alignItems: 'start' }}>

        {/* Form */}
        <div style={{
          background: '#0d0d14', border: '1px solid #191926',
          borderRadius: '12px', position: isMobile ? 'static' : 'sticky', top: '0', overflow: 'visible',
        }}>
          <div style={{ padding: '13px 16px', borderBottom: '1px solid #16162a' }}>
            <div style={{ fontSize: '10.5px', fontWeight: 700, color: '#3a3a52', textTransform: 'uppercase', letterSpacing: '1px' }}>Aggiungi Serie</div>
          </div>
          <form onSubmit={handleAdd} style={{ padding: '15px 16px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {/* Exercise */}
            <div style={{ position: 'relative' }}>
              <label style={{ display: 'block', fontSize: '10px', fontWeight: 700, color: '#34344e', textTransform: 'uppercase', letterSpacing: '.7px', marginBottom: '6px' }}>Esercizio</label>
              <input ref={exRef} type="text" value={exInput} placeholder="Cerca o inserisci nuovo…"
                onChange={e => onExChange(e.target.value)}
                onFocus={e => { e.target.style.borderColor = 'rgba(240,136,62,.4)'; if (exInput.length >= 2) setShowSugg(true); }}
                onBlur={e => { e.target.style.borderColor = '#202030'; setTimeout(() => setShowSugg(false), 150); }}
                style={inputBase} />
              {showSugg && suggestions.length > 0 && (
                <div style={{
                  position: 'absolute', top: '100%', left: 0, right: 0, zIndex: 200,
                  background: '#12121e', border: '1px solid #242438',
                  borderRadius: '8px', marginTop: '4px', overflow: 'hidden',
                  boxShadow: '0 12px 32px rgba(0,0,0,.55)',
                }}>
                  {suggestions.map((ex, i) => (
                    <button key={i} type="button" onMouseDown={() => pickSugg(ex.name)}
                      style={{
                        width: '100%', padding: '9px 12px', background: 'transparent',
                        border: 'none', borderBottom: i < suggestions.length - 1 ? '1px solid #1c1c2c' : 'none',
                        color: '#b8b8d0', fontSize: '13px',
                        fontFamily: "'Space Grotesk', sans-serif", textAlign: 'left',
                        cursor: 'pointer', display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                      }}
                      onMouseEnter={e => e.currentTarget.style.background = '#1c1c2c'}
                      onMouseLeave={e => e.currentTarget.style.background = 'transparent'}>
                      <span>{ex.name}</span>
                      <div style={{ display: 'flex', gap: '4px' }}>{ex.tags.map(t => <Badge key={t} label={t} />)}</div>
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Reps + Weight */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '9px' }}>
              {[
                { label: 'Ripetizioni', val: reps, set: setReps, type: 'number', min: '1', max: '999', ph: '10' },
                { label: 'Peso (kg)',   val: weight, set: setWeight, type: 'number', min: '0', step: '.5', ph: '80' },
              ].map(f => (
                <div key={f.label}>
                  <label style={{ display: 'block', fontSize: '10px', fontWeight: 700, color: '#34344e', textTransform: 'uppercase', letterSpacing: '.7px', marginBottom: '6px' }}>{f.label}</label>
                  <input type={f.type} min={f.min} max={f.max} step={f.step} placeholder={f.ph}
                    value={f.val} onChange={e => f.set(e.target.value)} style={inputBase}
                    onFocus={e => e.target.style.borderColor = 'rgba(240,136,62,.4)'}
                    onBlur={e => e.target.style.borderColor = '#202030'} />
                </div>
              ))}
            </div>

            {/* Rest */}
            <div>
              <label style={{ display: 'block', fontSize: '10px', fontWeight: 700, color: '#34344e', textTransform: 'uppercase', letterSpacing: '.7px', marginBottom: '6px' }}>Recupero</label>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: '5px' }}>
                {['60', '90', '120', '180'].map(r => (
                  <button key={r} type="button" onClick={() => setRest(r)} style={{
                    padding: '8px 4px', borderRadius: '6px',
                    border: `1px solid ${rest === r ? 'rgba(240,136,62,.35)' : '#1e1e30'}`,
                    background: rest === r ? 'rgba(240,136,62,.09)' : '#09090f',
                    color: rest === r ? '#f0883e' : '#484862',
                    fontSize: '11px', fontFamily: "'JetBrains Mono', monospace",
                    fontWeight: rest === r ? 700 : 400, cursor: 'pointer', transition: 'all .12s',
                  }}>{r}s</button>
                ))}
              </div>
            </div>

            {formErr && (
              <div style={{ fontSize: '11.5px', color: '#f85149', padding: '7px 10px', background: 'rgba(248,81,73,.07)', borderRadius: '6px', border: '1px solid rgba(248,81,73,.14)' }}>{formErr}</div>
            )}

            <button type="submit" style={{
              padding: '11px', background: 'linear-gradient(135deg, #f0883e, #c85c1a)',
              border: 'none', borderRadius: '8px', color: '#fff',
              fontSize: '13.5px', fontFamily: "'Space Grotesk', sans-serif",
              fontWeight: 600, cursor: 'pointer', marginTop: '1px',
            }}>+ Aggiungi Serie</button>
          </form>

          {lastAdded && (
            <div style={{
              margin: '0 16px 14px', padding: '9px 12px',
              background: 'rgba(63,185,80,.06)', border: '1px solid rgba(63,185,80,.15)',
              borderRadius: '7px', fontSize: '12px', color: '#3fb950',
            }}>✓ {lastAdded.exercise} — {lastAdded.reps} × {lastAdded.weight} kg</div>
          )}
        </div>

        {/* Table */}
        <div>
          {session.sets.length === 0 ? (
            <div style={{
              background: '#0d0d14', border: '1px dashed #1c1c2e',
              borderRadius: '12px', padding: '52px 24px', textAlign: 'center',
            }}>
              <div style={{ fontSize: '26px', marginBottom: '10px', opacity: .4 }}>〇</div>
              <div style={{ fontSize: '13.5px', color: '#2c2c44', fontWeight: 500 }}>Aggiungi la prima serie dal pannello</div>
            </div>
          ) : (
            <div style={{ background: '#0d0d14', border: '1px solid #191926', borderRadius: '12px', overflow: 'hidden' }}>
              <div style={{ padding: '13px 16px', borderBottom: '1px solid #16162a' }}>
                <div style={{ fontSize: '10.5px', fontWeight: 700, color: '#3a3a52', textTransform: 'uppercase', letterSpacing: '1px' }}>Serie Registrate</div>
              </div>
              {groups.map(g => (
                <div key={g.exercise} style={{ borderBottom: '1px solid #131322' }}>
                  <div style={{ padding: '10px 16px 5px', display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                    <span style={{ fontSize: '13px', fontWeight: 600, color: '#c0c0d8' }}>{g.exercise}</span>
                    {(ALL_EXERCISES.find(e => e.name === g.exercise)?.tags || []).map(t => <Badge key={t} label={t} />)}
                  </div>
                  <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                    <thead>
                      <tr style={{ background: '#0a0a14' }}>
                        {['Set', 'Reps', 'Peso', 'Recupero', ''].map(h => (
                          <th key={h} style={{
                            padding: '5px 16px', fontSize: '9.5px', fontWeight: 700,
                            color: '#282840', textTransform: 'uppercase', letterSpacing: '.6px',
                            textAlign: h === '' || h === 'Set' ? 'center' : 'left',
                          }}>{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {g.sets.map((s, i) => (
                        <SetRow key={s.id} set={s} index={i + 1} onDelete={() => onDeleteSet(session.id, s.id)} />
                      ))}
                    </tbody>
                  </table>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ─── AdminPage ────────────────────────────────────────────────────────────────
function AdminPage({ sessions, exercises }) {
  const isMobile = useMobile();
  const [tab, setTab] = useState('overview');
  const totalSets = sessions.reduce((n, s) => n + s.sets.length, 0);
  const usage = useMemo(() => {
    const m = {};
    sessions.forEach(s => s.sets.forEach(set => { m[set.exercise] = (m[set.exercise] || 0) + 1; }));
    return Object.entries(m).sort(([,a],[,b]) => b - a).slice(0, 10);
  }, [sessions]);
  const fakeUsers = [
    { username: 'admin',  role: 'Superuser', sessions: 12,                      last: '2 ore fa' },
    { username: 'marco',  role: 'Atleta',    sessions: Math.max(0, sessions.length - 20), last: 'ieri' },
    { username: 'lucia',  role: 'Atleta',    sessions: 23,                      last: '3 giorni fa' },
    { username: 'andrea', role: 'Atleta',    sessions: 8,                       last: '1 settimana fa' },
  ];

  return (
    <div className="page-enter" style={{ flex: 1, overflow: 'auto', padding: isMobile ? '16px 14px 80px' : '28px 32px' }}>
      <div style={{ marginBottom: '22px' }}>
        <h1 style={{ fontSize: '21px', fontWeight: 700, color: '#f0f0f3', letterSpacing: '-0.4px', marginBottom: '3px' }}>Pannello Admin</h1>
        <p style={{ fontSize: '12.5px', color: '#484860' }}>Gestione utenti, esercizi e statistiche globali</p>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: '4px', padding: '4px', background: '#0d0d14', border: '1px solid #191926', borderRadius: '9px', width: 'fit-content', marginBottom: '22px' }}>
        {['overview', 'utenti', 'esercizi'].map(t => (
          <button key={t} onClick={() => setTab(t)} style={{
            padding: '7px 14px', borderRadius: '6px', border: 'none',
            background: tab === t ? '#1a1a2c' : 'transparent',
            color: tab === t ? '#f0f0f3' : '#484862',
            fontSize: '12.5px', fontFamily: "'Space Grotesk', sans-serif",
            fontWeight: tab === t ? 600 : 500, cursor: 'pointer',
            textTransform: 'capitalize', transition: 'all .12s',
          }}>{t}</button>
        ))}
      </div>

      {tab === 'overview' && (
        <div>
          <div style={{ display: 'grid', gridTemplateColumns: `repeat(${isMobile ? 2 : 4},1fr)`, gap: '13px', marginBottom: '20px' }}>
            {[
              { v: fakeUsers.length,              l: 'Utenti Totali',      s: '+2 questo mese' },
              { v: sessions.length,               l: 'Sessioni Totali',    s: 'tutti gli utenti' },
              { v: totalSets.toLocaleString('it'), l: 'Serie Registrate',  s: 'nel database' },
              { v: exercises.length,              l: 'Esercizi Catalogati', s: 'database globale' },
            ].map(c => (
              <div key={c.l} style={{ background: '#0d0d14', border: '1px solid #191926', borderRadius: '10px', padding: '16px 18px' }}>
                <div style={{ fontSize: '26px', fontWeight: 700, color: '#f0f0f3', fontFamily: "'JetBrains Mono', monospace", letterSpacing: '-1px' }}>{c.v}</div>
                <div style={{ fontSize: '11px', fontWeight: 600, color: '#525268', marginTop: '5px' }}>{c.l}</div>
                <div style={{ fontSize: '10px', color: '#2c2c42', marginTop: '2px' }}>{c.s}</div>
              </div>
            ))}
          </div>

          <div style={{ background: '#0d0d14', border: '1px solid #191926', borderRadius: '10px', overflow: 'hidden' }}>
            <div style={{ padding: '13px 18px', borderBottom: '1px solid #16162a', fontSize: '10.5px', fontWeight: 700, color: '#3a3a52', textTransform: 'uppercase', letterSpacing: '1px' }}>
              Esercizi Più Usati
            </div>
            <div style={{ padding: '10px 14px' }}>
              {usage.map(([name, count], i) => {
                const pct = (count / usage[0][1]) * 100;
                return (
                  <div key={name} style={{ padding: '7px 4px', display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <span style={{ fontSize: '9.5px', color: '#2e2e44', fontFamily: "'JetBrains Mono', monospace", width: '14px', textAlign: 'right' }}>{i + 1}</span>
                    <span style={{ fontSize: '13px', color: '#b0b0c8', flex: 1 }}>{name}</span>
                    <div style={{ width: '100px', height: '3px', background: '#18182a', borderRadius: '2px', overflow: 'hidden' }}>
                      <div style={{ width: `${pct}%`, height: '100%', background: 'linear-gradient(90deg,#f0883e,#c85c1a)', borderRadius: '2px' }} />
                    </div>
                    <span style={{ fontSize: '10.5px', color: '#484862', fontFamily: "'JetBrains Mono', monospace", width: '28px', textAlign: 'right' }}>{count}</span>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {tab === 'utenti' && (
        <div style={{ background: '#0d0d14', border: '1px solid #191926', borderRadius: '10px', overflow: 'hidden' }}>
          <div style={{ padding: '13px 18px', borderBottom: '1px solid #16162a', fontSize: '10.5px', fontWeight: 700, color: '#3a3a52', textTransform: 'uppercase', letterSpacing: '1px' }}>Utenti Registrati</div>
          <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', minWidth: '480px', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ background: '#09090f' }}>
                {['Username', 'Ruolo', 'Sessioni', 'Ultima attività'].map(h => (
                  <th key={h} style={{ padding: '9px 18px', fontSize: '9.5px', fontWeight: 700, color: '#282840', textTransform: 'uppercase', letterSpacing: '.6px', textAlign: 'left' }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {fakeUsers.map(u => (
                <tr key={u.username} style={{ borderBottom: '1px solid #121222' }}>
                  <td style={{ padding: '12px 18px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <div style={{
                        width: '28px', height: '28px', borderRadius: '7px', flexShrink: 0,
                        background: `hsl(${u.username.charCodeAt(0) * 33 % 360}, 30%, 20%)`,
                        border: '1px solid rgba(255,255,255,.05)',
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        fontSize: '11px', fontWeight: 700, color: '#c0c0d8',
                      }}>{u.username[0].toUpperCase()}</div>
                      <span style={{ fontSize: '13px', color: '#c8c8e0', fontWeight: 500 }}>{u.username}</span>
                    </div>
                  </td>
                  <td style={{ padding: '12px 18px' }}>
                    <span style={{
                      padding: '2px 8px', borderRadius: '4px', fontSize: '10.5px', fontWeight: 600,
                      background: u.role === 'Superuser' ? 'rgba(240,136,62,.1)' : 'rgba(136,136,176,.08)',
                      color: u.role === 'Superuser' ? '#f0883e' : '#7878a0',
                      border: `1px solid ${u.role === 'Superuser' ? 'rgba(240,136,62,.22)' : 'rgba(136,136,176,.16)'}`,
                    }}>{u.role}</span>
                  </td>
                  <td style={{ padding: '12px 18px', fontSize: '13px', color: '#686890', fontFamily: "'JetBrains Mono', monospace" }}>{u.sessions}</td>
                  <td style={{ padding: '12px 18px', fontSize: '12px', color: '#383852' }}>{u.last}</td>
                </tr>
              ))}
            </tbody>
          </table>
          </div>
        </div>
      )}

      {tab === 'esercizi' && (
        <div style={{ background: '#0d0d14', border: '1px solid #191926', borderRadius: '10px', overflow: 'hidden' }}>
          <div style={{ padding: '13px 18px', borderBottom: '1px solid #16162a', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ fontSize: '10.5px', fontWeight: 700, color: '#3a3a52', textTransform: 'uppercase', letterSpacing: '1px' }}>Catalogo Esercizi</div>
            <span style={{ fontSize: '10.5px', color: '#2c2c44', fontFamily: "'JetBrains Mono', monospace" }}>{exercises.length} totali</span>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : 'repeat(2,1fr)' }}>
            {exercises.map((ex, i) => (
              <div key={ex.name} style={{
                padding: '11px 18px', display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                borderBottom: '1px solid #111120',
                borderRight: i % 2 === 0 ? '1px solid #111120' : 'none',
              }}>
                <span style={{ fontSize: '12.5px', color: '#b0b0c8' }}>{ex.name}</span>
                <div style={{ display: 'flex', gap: '4px' }}>{ex.tags.map(t => <Badge key={t} label={t} />)}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ─── App ──────────────────────────────────────────────────────────────────────
function App() {
  const [user, setUser]               = useState(null);
  const [page, setPage]               = useState('dashboard');
  const [sessions, setSessions]       = useState(() => generateSessions());
  const [exercises, setExercises]     = useState(ALL_EXERCISES);
  const [activeSession, setActive]    = useState(null);
  const [pageKey, setPageKey]         = useState(0);

  const navigate = useCallback(p => { setPage(p); setPageKey(k => k + 1); }, []);

  const currentSession = useMemo(() =>
    activeSession ? (sessions.find(s => s.id === activeSession.id) || activeSession) : null,
    [activeSession, sessions]
  );

  if (!user) return <AuthPage onLogin={u => { setUser(u); navigate('dashboard'); }} />;

  return (
    <div style={{ display: 'flex', height: '100vh', overflow: 'hidden' }}>
      <Sidebar currentPage={page} navigate={navigate} user={user} onLogout={() => { setUser(null); setPage('dashboard'); }} />
      <main style={{ flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
        <div key={pageKey} style={{ flex: 1, overflow: 'auto', display: 'flex', flexDirection: 'column' }}>
          {page === 'dashboard' && (
            <DashboardPage sessions={sessions} user={user} navigate={navigate}
              onDelete={id => setSessions(p => p.filter(s => s.id !== id))}
              onView={s => { setActive(s); navigate('session-detail'); }} />
          )}
          {page === 'new-session' && (
            <NewSessionPage navigate={navigate}
              onCreate={ns => {
                setSessions(p => [ns, ...p]);
                setActive(ns);
                navigate('session-detail');
              }} />
          )}
          {page === 'session-detail' && currentSession && (
            <SessionDetailPage session={currentSession} exercises={exercises} navigate={navigate}
              onAddSet={(sid, set) => {
                setSessions(p => p.map(s => s.id === sid ? { ...s, sets: [...s.sets, set] } : s));
                if (!exercises.find(e => e.name === set.exercise))
                  setExercises(p => [...p, { name: set.exercise, tags: [] }]);
              }}
              onDeleteSet={(sid, setId) =>
                setSessions(p => p.map(s => s.id === sid ? { ...s, sets: s.sets.filter(x => x.id !== setId) } : s))
              } />
          )}
          {page === 'admin' && <AdminPage sessions={sessions} exercises={exercises} />}
        </div>
      </main>
      <BottomNav currentPage={page} navigate={navigate} onLogout={() => { setUser(null); setPage('dashboard'); }} />
    </div>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(<App />);
