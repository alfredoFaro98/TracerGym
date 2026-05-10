import re
import os

with open('Corpo umano.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Extract styles
style_match = re.search(r'<style>(.*?)</style>', content, re.DOTALL)
styles = style_match.group(1) if style_match else ''

# Extract body map SVG and wrapper
body_map_wrap_match = re.search(r'<div class="body-map-wrap">(.*?)</div><!-- /body-map-wrap -->', content, re.DOTALL)
body_map_wrap = body_map_wrap_match.group(0) if body_map_wrap_match else ''

# Create the django template
template = f"""{{% extends 'tracker/base.html' %}}

{{% block title %}}Mappa Muscolare{{% endblock %}}

{{% block extra_head %}}
<style>
{styles}

/* Adjustments for Django layout */
.main {{
    display: flex;
    align-items: center;
    justify-content: center;
    flex: 1;
    gap: 0;
    overflow: hidden;
    height: calc(100vh - 60px); /* Adjust if you have a header */
}}
.body-map-wrap svg {{
    height: min(78vh, 700px);
    width: auto;
    display: block;
    overflow: visible;
}}

/* Ensure the layout fits the main area */
.app-layout .main-content {{
    padding: 0;
    overflow: hidden;
    display: flex;
    flex-direction: column;
}}
</style>
{{% endblock %}}

{{% block content %}}
<!-- Header -->
<header class="header" style="padding: 16px 24px; flex-shrink: 0; border-bottom: 1px solid var(--border);">
<div class="header-title" style="display:flex; align-items:center; gap:10px;">
    <div class="header-dot"></div>
    <h1 id="viewLabel">Corpo Umano — Vista Anteriore</h1>
</div>
</header>

<!-- Main -->
<div class="main" style="display:flex; flex:1; overflow:hidden;">

    <!-- SVG body map -->
    {body_map_wrap}

    <!-- Divider -->
    <div class="panel-divider"></div>

    <!-- Info Panel -->
    <div class="info-panel" style="overflow-y:auto;">
        <!-- Hint state -->
        <div class="hint-state" id="hintState">
        <div class="hint-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" d="M15 15l-6-6m0 0l6-6m-6 6h12" opacity="0.5"/>
            <circle cx="8" cy="12" r="7" opacity="0.3"/>
            </svg>
        </div>
        <p class="hint-label">Passa il cursore su un muscolo per esplorarne la funzione e gli esercizi.</p>
        <p class="hint-sub">10 gruppi muscolari interattivi</p>
        </div>

        <!-- Active state -->
        <div class="active-state" id="activeState">
        <div class="muscle-eyebrow" id="eyebrow">Gruppo Muscolare</div>
        <h2 class="muscle-name-it" id="muscleIt"></h2>
        <p class="muscle-name-en" id="muscleEn"></p>
        <div class="panel-rule"></div>
        <p class="muscle-desc" id="muscleDesc"></p>
        <div class="section-title">Esercizi Suggeriti</div>
        <div class="exercise-list" id="exerciseList"></div>
        </div>
    </div>
</div>

<!-- Floating tooltip -->
<div class="muscle-tooltip" id="tooltip"></div>

<script>
    const allExercises = {{{{ exercises_json|safe }}}};

    // Helper to filter exercises
    function filterExercises(macroTag, keywords = [], excludeKeywords = []) {{
        return allExercises.filter(ex => {{
            if (!ex.tags.includes(macroTag.toLowerCase())) return false;
            let match = true;
            if (keywords.length > 0) {{
                match = keywords.some(k => ex.nome.toLowerCase().includes(k.toLowerCase()));
            }}
            if (match && excludeKeywords.length > 0) {{
                match = !excludeKeywords.some(k => ex.nome.toLowerCase().includes(k.toLowerCase()));
            }}
            return match;
        }}).map(ex => ex.nome);
    }}

    const data = {{
        calves: {{
            name: 'Polpacci',
            en: 'Gastrocnemio & Soleo',
            desc: 'Controllano la flessione plantare e ammortizzano limpatto durante corsa e salto. Composti dal gastrocnemio superficiale e dal soleo più profondo.',
            exercises: filterExercises('gambe', ['calf', 'polpacci'])
        }},
        quads: {{
            name: 'Quadricipiti',
            en: 'Quadriceps Femoris',
            desc: 'Il gruppo muscolare più potente del corpo: quattro capi che estendono il ginocchio e stabilizzano la rotula in ogni movimento di spinta.',
            exercises: filterExercises('gambe', ['squat', 'pressa', 'extension', 'affondi', 'leg extension'], ['bulgaro', 'jefferson', 'sissy', 'curl', 'stacchi'])
        }},
        abdominals: {{
            name: 'Addominali',
            en: 'Rectus Abdominis',
            desc: 'Il retto delladdome e il trasverso formano il pilastro del core anteriore, stabilizzando la colonna e trasmettendo forza tra tronco e arti.',
            exercises: filterExercises('addome', [], ['obliquo', 'russian', 'side', 'twist'])
        }},
        obliques: {{
            name: 'Obliqui',
            en: 'Obliquus Externus & Internus',
            desc: 'Muscoli laterali che consentono rotazione e flessione del tronco. Fondamentali per i movimenti atletici rotatori e per la stabilità del core.',
            exercises: filterExercises('addome', ['obliqu', 'russian', 'twist', 'side'])
        }},
        hands: {{
            name: 'Mani e Avambracci ant.',
            en: 'Muscoli Intrinseci & Flessori',
            desc: 'Piccoli muscoli intrinseci e flessori che permettono prensione precisa, manipolazione fine degli oggetti e forza di presa elevata.',
            exercises: []
        }},
        forearms: {{
            name: 'Avambracci',
            en: 'Flexor & Extensor Group',
            desc: 'Flessori ed estensori controllano polso e dita con precisione. Essenziali per la forza di presa.',
            exercises: []
        }},
        biceps: {{
            name: 'Bicipiti',
            en: 'Biceps Brachii',
            desc: 'Muscolo a due capi — lungo e breve — che flette il gomito e supina lavambraccio.',
            exercises: filterExercises('bicipiti')
        }},
        'front-shoulders': {{
            name: 'Deltoide Ant. & Lat.',
            en: 'Anterior & Lateral Deltoid',
            desc: 'Gestisce flessione, abduzione e rotazione interna della spalla. Si attiva nei movimenti di spinta frontale e alzate.',
            exercises: filterExercises('spalle', ['frontali', 'lento', 'press', 'laterali', 'military'], ['dietro', '90', 'inverso'])
        }},
        chest: {{
            name: 'Petto',
            en: 'Pectoralis Major & Minor',
            desc: 'Grande e piccolo pettorale eseguono adduzione, flessione e rotazione interna dellomero.',
            exercises: filterExercises('pettorali')
        }},
        traps: {{
            name: 'Trapezi (Medio/Inf)',
            en: 'Trapezius',
            desc: 'Controlla elevazione, retrazione e depressione della scapola per stabilità posturale.',
            exercises: filterExercises('spalle', ['shrug', 'rematore verticale'])
        }}
    }};

    const backData = {{
        'b-upper-traps': {{
            name: 'Trapezio sup.',
            en: 'Upper Trapezius',
            desc: 'La porzione superiore del trapezio solleva le spalle e stabilizza il collo.',
            exercises: filterExercises('spalle', ['shrug', 'tirate', 'alzate laterali'])
        }},
        'b-rear-delts': {{
            name: 'Deltoide Post.',
            en: 'Posterior Deltoid',
            desc: 'Gestisce estensione e rotazione esterna della spalla.',
            exercises: filterExercises('spalle', ['90 gradi', 'inverso', 'posteriori', 'a 90'])
        }},
        'b-rhomboids': {{
            name: 'Romboidi',
            en: 'Rhomboids & Mid Traps',
            desc: 'I romboidi e i trapezi medi retraggono la scapola verso la colonna.',
            exercises: filterExercises('dorsali', ['rematore', 'pulley'])
        }},
        'b-lats': {{
            name: 'Dorsali',
            en: 'Latissimus Dorsi',
            desc: 'Il muscolo più largo del corpo. Responsabile delladduzione e dellestensione dellomero.',
            exercises: filterExercises('dorsali', ['trazioni', 'lat machine', 'pullover', 'chin up', 'dorsy', 'nautilus'])
        }},
        'b-lower-back': {{
            name: 'Lombari',
            en: 'Erector Spinae',
            desc: 'Gli erettori della colonna vertebrale mantengono eretta la schiena.',
            exercises: filterExercises('dorsali', ['iperestensioni', 'goodmorning', 'stacchi'])
        }},
        'b-triceps': {{
            name: 'Tricipiti',
            en: 'Triceps Brachii',
            desc: 'Muscolo a tre capi che costituisce circa i 2/3 del volume del braccio.',
            exercises: filterExercises('tricipiti')
        }},
        'b-forearms': {{
            name: 'Avambracci post.',
            en: 'Extensor Group',
            desc: 'Gli estensori dellavambraccio controllano lestensione del polso e delle dita.',
            exercises: []
        }},
        'b-hands': {{
            name: 'Mani',
            en: 'Dorsal Hand Muscles',
            desc: 'I tendini estensori e i muscoli dorsali permettono apertura delle dita.',
            exercises: []
        }},
        'b-glutes': {{
            name: 'Glutei',
            en: 'Gluteus Maximus & Medius',
            desc: 'Il grande gluteo è il muscolo più potente del corpo umano: estende lanca e ruota esternamente la coscia.',
            exercises: filterExercises('gambe', ['glute', 'ponte', 'abductor', 'adductor', 'bulgaro', 'squat'], ['front'])
        }},
        'b-hamstrings': {{
            name: 'Ischio-Crurali',
            en: 'Hamstrings',
            desc: 'Flettono il ginocchio ed estendono lanca.',
            exercises: filterExercises('gambe', ['curl', 'stacchi gambe tese'])
        }},
        'b-calves': {{
            name: 'Polpacci post.',
            en: 'Gastrocnemius',
            desc: 'La testa posteriore del gastrocnemio è il principale motore della flessione plantare.',
            exercises: filterExercises('gambe', ['calf', 'polpacci'])
        }}
    }};

    Object.assign(data, backData);

    let currentView    = 'front';
    let currentTimeout = null;
    const hintState    = document.getElementById('hintState');
    const activeState  = document.getElementById('activeState');
    const tooltip      = document.getElementById('tooltip');

    function getContainer() {{
      return currentView === 'front'
        ? document.getElementById('svgContainer')
        : document.getElementById('backSvgContainer');
    }}

    document.querySelectorAll('.vt-btn').forEach(btn => {{
      btn.addEventListener('click', () => {{
        const view = btn.dataset.view;
        if (view === currentView) return;
        currentView = view;
        deactivate();
        document.querySelectorAll('.vt-btn').forEach(b => b.classList.toggle('active', b === btn));
        document.getElementById('frontView').classList.toggle('hidden-view', view === 'back');
        document.getElementById('backView').classList.toggle('hidden-view', view === 'front');
        document.getElementById('viewLabel').textContent =
          'Corpo Umano \u2014 Vista ' + (view === 'front' ? 'Anteriore' : 'Posteriore');
        document.getElementById('muscleCount').textContent =
          (view === 'front' ? '10' : '11') + ' gruppi muscolari';
      }});
    }});

    function activate(id, x, y) {{
      document.querySelectorAll('.bodymap').forEach(g => g.classList.remove('is-lit'));
      const target = document.getElementById(id);
      if (target) target.classList.add('is-lit');
      const container = getContainer();
      if(container) container.classList.add('map-hovering');

      const d = data[id];
      if (!d) return;
      tooltip.textContent  = d.name;
      tooltip.style.left   = x + 'px';
      tooltip.style.top    = y + 'px';
      tooltip.classList.add('show');

      document.getElementById('muscleIt').textContent   = d.name;
      document.getElementById('muscleEn').textContent   = d.en;
      document.getElementById('muscleDesc').textContent = d.desc;

      const list = document.getElementById('exerciseList');
      if (d.exercises && d.exercises.length > 0) {{
        list.innerHTML = d.exercises.map((ex, i) =>
          `<div class="exercise-item" style="transition-delay:${{i * 30}}ms"><div class="exercise-pip"></div><span>${{ex}}</span></div>`
        ).join('');
      }} else {{
          list.innerHTML = `<div class="exercise-item" style="transition-delay:0ms; color: var(--text-muted); font-style: italic;">Nessun esercizio specifico nel database</div>`;
      }}

      hintState.classList.add('hidden');
      activeState.classList.add('show');

      requestAnimationFrame(() => {{
        list.querySelectorAll('.exercise-item').forEach((el, i) => {{
          setTimeout(() => el.classList.add('appear'), i * 30);
        }});
      }});
    }}

    function deactivate() {{
      document.querySelectorAll('.bodymap').forEach(g => g.classList.remove('is-lit'));
      ['svgContainer','backSvgContainer'].forEach(id => {{
        const c = document.getElementById(id);
        if (c) c.classList.remove('map-hovering');
      }});
      tooltip.classList.remove('show');
      activeState.classList.remove('show');
      hintState.classList.remove('hidden');
      document.querySelectorAll('.exercise-item').forEach(el => el.classList.remove('appear'));
    }}

    document.querySelectorAll('.bodymap').forEach(group => {{
      group.addEventListener('mouseenter', e => {{
        if (currentTimeout) clearTimeout(currentTimeout);
        const rect = group.getBoundingClientRect();
        activate(group.id, rect.left + rect.width / 2, rect.top);
      }});
      group.addEventListener('mousemove', e => {{
        tooltip.style.left = e.clientX + 'px';
        tooltip.style.top  = e.clientY + 'px';
      }});
      group.addEventListener('mouseleave', () => {{
        currentTimeout = setTimeout(deactivate, 80);
      }});
    }});
</script>
{{% endblock %}}
"""

os.makedirs('tracker/templates/tracker', exist_ok=True)
with open('tracker/templates/tracker/body_map.html', 'w', encoding='utf-8') as f:
    f.write(template)

print('body_map.html created successfully!')
