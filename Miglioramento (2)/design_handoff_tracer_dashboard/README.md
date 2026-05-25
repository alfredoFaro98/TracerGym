# Handoff: Tracer — Dashboard Redesign

## Overview

Redesign completo della dashboard principale di **Tracer**, un'app web di workout tracking. Questo pacchetto contiene il riferimento visivo (HTML interattivo) e tutte le specifiche necessarie per implementare il design nella codebase reale.

> **Importante**: i file `.html` e `.jsx` in questo bundle sono **prototipi di design**, non codice da copiare in produzione. Il tuo compito è **ricreare queste interfacce nel tuo environment esistente** (Django + template, React, o qualsiasi framework tu stia usando), rispettando i pattern e le librerie già in uso nel progetto.

---

## Fidelità

**High-fidelity.** I mockup sono pixel-accurate: colori esatti, tipografia, spaziatura, stati hover/active. Ricrea ogni schermata rispettando fedelmente le specifiche qui sotto.

---

## Varianti

Sono stati progettati **due layout alternativi** — scegli uno oppure usali entrambi come riferimento per diversi aspetti.

| | Variante A — Raffinato | Variante B — Command Center |
|---|---|---|
| **Sidebar** | 224px con label + icona | 64px icon-only |
| **Header** | Titolo inline in cima al main | Top bar fissa persistente |
| **KPI** | Strip orizzontale sotto l'header | Row a tutta larghezza sotto la top bar |
| **Layout contenuto** | Colonna singola verticale | 2 colonne (lista | heatmap+grafico) |

---

## Design Tokens

### Colori — Superficie (dark theme)

```
--color-base:        #0c0c0e   /* sfondo globale */
--color-surface:     #131316   /* sidebar, top bar */
--color-elevated:    #1a1a1e   /* card principali */
--color-card:        #1f1f25   /* card secondarie, input bg */
--color-hover:       #26262e   /* stato hover sulle righe */
--color-border:      #28282f   /* bordi principali */
--color-border-sub:  #1c1c22   /* separatori riga */
```

### Colori — Testo

```
--color-text:        #eeeef2   /* testo primario */
--color-text-sec:    #6868a0   /* testo secondario (label, caption) */
--color-text-muted:  #3e3e56   /* testo terzario (timestamp, sezione label) */
```

### Colori — Accento e Semantici

```
--color-accent:        #F07228                    /* arancione principale */
--color-accent-dim:    rgba(240, 114, 40, 0.10)   /* sfondo badge/icon accento */
--color-accent-mid:    rgba(240, 114, 40, 0.28)   /* bordo attivo sidebar */

--color-success:       #3dd68c
--color-success-dim:   rgba(61, 214, 140, 0.10)

--color-blue:          #5B9EFF
--color-blue-dim:      rgba(91, 158, 255, 0.10)

--color-purple:        #ab6cf7
--color-purple-dim:    rgba(171, 108, 247, 0.10)

--color-red:           #f43f5e
--color-red-dim:       rgba(244, 63, 94, 0.10)
```

### Colori — Gruppi Muscolari (usati nei dot e nei badge)

```
back:       #5B9EFF
chest:      #F07228
legs:       #3dd68c
core:       #ab6cf7
shoulders:  #f59e0b
arms:       #f43f5e
```

### Tipografia

```
Font family: 'Space Grotesk', sans-serif
Google Fonts import: https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700;800&display=swap
```

| Uso | Size | Weight | Extra |
|---|---|---|---|
| Titolo pagina | 25px | 700 | letter-spacing: -0.025em |
| KPI numero (V-A) | 22px | 700 | letter-spacing: -0.04em |
| KPI numero (V-B) | 30px | 700 | letter-spacing: -0.04em |
| Nome workout | 13.5px | 600 | — |
| Sidebar nav item | 13px | 400 / 600 (active) | — |
| Sezione label | 10.5px | 700 | letter-spacing: 0.08em, uppercase |
| Tag esercizio | 10.5px | 500 | — |
| Data (numero) | 21px | 700 | letter-spacing: -0.03em |
| Mese abbreviato | 9.5px | 600 | letter-spacing: 0.06em |
| Caption / muted | 9–10px | 400–500 | — |

### Border Radius

```
Logo mark / KPI icon:  9–10px
Card principale:       12px
Tag esercizio:         4px
Pulsanti azione:       6–8px
Avatar:                50% (cerchio)
Heatmap cell:          2px
```

### Icone

Tutte le icone sono **Lucide Icons** (stroke-only, `strokeWidth: 1.75`). Dimensioni usate: 13px, 14px, 15px, 17px, 18px, 22px. Nessun fill, solo stroke.

Libreria consigliata: `lucide-react` oppure SVG inline da [lucide.dev](https://lucide.dev).

---

## Schermate

### 1. Dashboard — Variante A (Raffinato)

**Dimensioni reference**: 1440 × 900px

#### Layout globale

```
┌──────────────┬─────────────────────────────────────────┐
│  Sidebar     │  Main                                   │
│  224px       │  flex-1                                 │
│  h-full      │                                         │
└──────────────┴─────────────────────────────────────────┘
```

#### Sidebar (`width: 224px`, `background: #131316`, `border-right: 1px solid #28282f`)

**Logo area** (`padding: 20px`, `border-bottom: 1px solid #28282f`):
- Logo mark: 34×34px, `border-radius: 9px`, `background: #F07228`, lettera "T" `font-size: 17px`, `font-weight: 800`, colore bianco
- Nome app: "Tracer" — `font-size: 14.5px`, `font-weight: 700`, `letter-spacing: -0.015em`
- Sottotitolo: "WORKOUT TRACKER" — `font-size: 9px`, `font-weight: 600`, `letter-spacing: 0.1em`, uppercase, `color: #3e3e56`

**Gruppi nav** (`padding: 8px 0`):

| Gruppo | Label sezione | Voci |
|---|---|---|
| — | (nessuna) | Dashboard *(active)*, Nuovo Allenamento |
| GESTIONE | label 9px uppercase #3e3e56 | Atleti, Mappa Muscolare, Catalogo Esercizi |
| ACCOUNT | — | Il mio profilo |
| ADMIN | — | Django Admin, Guida |

Ogni voce nav:
- `padding: 8px 20px`, `display: flex`, `gap: 10px`, `align-items: center`
- Stato default: colore testo `#6868a0`, icona `#3e3e56`, background trasparente
- Stato **active**: background `rgba(240,114,40,0.10)`, `border-left: 2px solid #F07228`, testo `#eeeef2`, icona `#F07228`
- `font-size: 13px`, transition background 120ms

**Footer utente** (`padding: 12px 16px`, `border-top: 1px solid #28282f`):
- Avatar 30×30px cerchio, gradient `#F07228 → #a83010` (135deg), lettera iniziale
- Nome `font-size: 12.5px`, `font-weight: 600`
- Ruolo `font-size: 10px`, `color: #3e3e56`
- Icona logout a destra

#### Main — Header (`padding: 24px 32px 0`)

- H1: "Bentornato, **admin**" — `font-size: 25px`, `font-weight: 700`, `letter-spacing: -0.025em`. "admin" in `color: #F07228`
- Sottotitolo: `font-size: 12.5px`, `color: #3e3e56`
- Pulsante CTA destra: "＋ Nuovo Allenamento" — `background: #F07228`, `padding: 9px 18px`, `border-radius: 8px`, `font-size: 13px`, `font-weight: 600`, bianco

#### KPI Strip (`padding: 14px 32px`, `display: flex`, `gap: 10px`)

4 KPI tiles, `flex: 1` ciascuno:
- Container: `padding: 11px 14px`, `background: #1a1a1e`, `border-radius: 10px`, `border: 1px solid #28282f`
- Icon box: 36×36px, `border-radius: 9px`, background = colore semantico dim (10% alpha)
- Numero: `font-size: 22px`, `font-weight: 700`, `letter-spacing: -0.04em`
- Label: `font-size: 10.5px`, `color: #3e3e56`, `margin-top: 2px`

| KPI | Valore | Label | Icona | Colore |
|---|---|---|---|---|
| Streak | 7 | gg streak | `fire` | `#F07228` |
| Settimana | 5 | questa sett. | `calendar` | `#5B9EFF` |
| Totale | 147 | sessioni totali | `barChart` | `#3dd68c` |
| Ieri | 35 | serie ieri | `zap` | `#ab6cf7` |

#### Card Attività / Heatmap

- Container: `background: #1a1a1e`, `border-radius: 12px`, `border: 1px solid #28282f`, `padding: 14px 20px`
- Header card: label "ATTIVITÀ" a sinistra + nav anno (chevron ← 2026 →) a destra
- Heatmap: griglia 53 colonne × 7 righe, celle `9×9px`, `gap: 2px`, `border-radius: 2px`
- Palette livelli (0→4): `#1a1a22` → `rgba(240,114,40,0.18)` → `rgba(240,114,40,0.42)` → `rgba(240,114,40,0.70)` → `#F07228`
- Labels mese sopra la griglia, `font-size: 9.5px`, `color: #3e3e56`
- Legenda "Meno / Di più" sotto a destra

#### Card Storico Allenamenti

- Container: `background: #1a1a1e`, `border-radius: 12px`, `border: 1px solid #28282f`, `overflow: hidden`
- Header: `padding: 12px 20px`, `border-bottom: 1px solid #28282f`; label sinistra, azioni destra (download, upload, search input, pulsante Filtra)
- Search input: `background: #1f1f25`, `border-radius: 6px`, `padding: 5px 10px`, placeholder "Cerca esercizio o note..."

**WorkoutRow** (singola riga):
- `padding: 10px 20px`, `display: flex`, `gap: 14px`, `align-items: center`
- `border-bottom: 1px solid #1c1c22`
- Hover: `background: #26262e`, transition 120ms
- **Colonna data** (46px, flex-shrink: 0):
  - Dot colorato 7×7px (colore gruppo muscolare), `border-radius: 50%`
  - Numero giorno: `font-size: 21px`, `font-weight: 700`, `letter-spacing: -0.03em`
  - Mese abbreviato: `font-size: 9.5px`, `font-weight: 600`, uppercase, `color: #3e3e56`
- **Colonna info** (flex: 1):
  - Nome giorno: `font-size: 13.5px`, `font-weight: 600`
  - Serie count: `font-size: 11px`, `color: #3e3e56`
  - Tag esercizi: max 3 visibili + badge "+N" in arancione. Tag: `background: #1f1f25`, `border: 1px solid #28282f`, `border-radius: 4px`, `padding: 2px 7px`, `font-size: 10.5px`, `color: #6868a0`
  - Badge overflow: `background: rgba(240,114,40,0.10)`, `color: #F07228`, `font-weight: 600`
- **Azioni hover** (opacity 0→1 on hover, transition 120ms):
  - 👁 Visualizza: `background: #1f1f25`, `border: 1px solid #28282f`
  - 📋 Duplica: uguale
  - 🗑 Elimina: `background: rgba(244,63,94,0.10)`, `border: 1px solid rgba(244,63,94,0.18)`, icona `#f43f5e`
  - Ogni pulsante: 28×28px, `border-radius: 6px`

#### Card Andamento Peso

- Container: `background: #1a1a1e`, `border-radius: 12px`, `padding: 14px 20px`
- Header: label "ANDAMENTO PESO" + `<select>` per scegliere l'esercizio
- Grafico: line chart SVG con area fill (gradient verticale accento→trasparente), punti `r: 3.5`, asse Y con dashed gridlines, asse X con label mese

---

### 2. Dashboard — Variante B (Command Center)

#### Layout globale

```
┌──────┬───────────────────────────────────────────────┐
│ Side │  Top Bar (62px)                               │
│  64  ├───────────────────────────────────────────────┤
│  px  │  KPI Row (4 colonne, border-bottom)           │
│      ├──────────────────────┬────────────────────────┤
│      │  Lista allenamenti   │  Heatmap               │
│      │  58% larghezza       │  +                     │
│      │                      │  Grafico peso          │
└──────┴──────────────────────┴────────────────────────┘
```

#### Sidebar (`width: 64px`, `background: #131316`, `border-right: 1px solid #28282f`)

- Logo mark: 38×38px, `border-radius: 10px`, `background: #F07228`, `margin-bottom: 20px`
- Icone nav: 42px height, `border-radius: 8px`, larghezza 100%
- Active: `background: rgba(240,114,40,0.10)`, `border: 1px solid rgba(240,114,40,0.22)`
- Default: background trasparente, `border: 1px solid transparent`
- Icone: 18px, colore `#F07228` (active) o `#3e3e56` (default)
- Tooltip `title` attribute su ogni icona per accessibilità
- Avatar 34×34px in fondo

#### Top Bar (`height: 62px`, `background: #131316`, `border-bottom: 1px solid #28282f`, `padding: 0 32px`)

- Sinistra: breadcrumb label "DASHBOARD" (10.5px uppercase + `font-weight: 600`) + titolo "Bentornato, admin" (`font-size: 19px`, `font-weight: 700`)
- Destra: search input (`width: 170px`) + pulsante "＋ Nuovo" arancione

#### KPI Row (`display: grid`, `grid-template-columns: repeat(4, 1fr)`, `border-bottom: 1px solid #28282f`)

Ogni KPI tile (`padding: 18px 24px`, `border-right: 1px solid #28282f` tranne l'ultimo):
- Icon box: 48×48px, `border-radius: 12px`
- Numero: `font-size: 30px`, `font-weight: 700`, `letter-spacing: -0.04em`
- Label: `font-size: 10.5px`, `color: #3e3e56`, `margin-top: 3px`
- Trend (opzionale): `font-size: 10px`, `color: #3dd68c`, `font-weight: 500`, es. "↑ +2 rispetto scorsa sett."

#### Sezione Sinistra — Lista allenamenti (`width: 58%`)

Identica alla Variante A, ma con header ridotto (data filter "Maggio 2026" + search più stretta).

#### Sezione Destra — Heatmap + Grafico (`flex: 1`)

**Heatmap** (`padding: 14px 20px`, `border-bottom: 1px solid #28282f`):
- Celle 8×8px (più compatte)
- Stessa struttura della Variante A

**Grafico peso** (`padding: 14px 20px`, `flex: 1`):
- SVG adattivo alla larghezza della colonna (~490px reference)
- Stessa struttura linea + area + punti

---

## Interazioni e Comportamenti

### WorkoutRow hover
```
onMouseEnter → background: #26262e, opacity pulsanti azioni: 1
onMouseLeave → background: transparent, opacity pulsanti azioni: 0
transition: background 120ms ease, opacity 120ms ease
```

### Pulsanti azione (hover sulla riga)
- **👁 Visualizza**: naviga al dettaglio allenamento
- **📋 Duplica**: crea una copia dell'allenamento con data odierna
- **🗑 Elimina**: mostra conferma prima di eliminare (non eliminare direttamente!)

### Heatmap
- Tooltip su hover su ogni cella con data e livello attività
- Navigazione anno: chevron ← / → cambiano l'anno visualizzato
- Le celle future (dopo oggi) hanno `opacity: 0.2`

### Select esercizio (grafico peso)
- Il cambio esercizio ricarica i dati del grafico per quell'esercizio
- Smooth transition dei punti del grafico (opzionale, 200ms)

### Search
- Filtra in tempo reale le righe dello storico per nome esercizio o tag
- Debounce 150ms

---

## Stato e Dati

### Struttura dati WorkoutSession
```typescript
interface WorkoutSession {
  id: number;
  date: number;          // giorno del mese
  month: string;         // es. "MAG"
  dayName: string;       // es. "Venerdì"
  series: number;        // totale serie
  tags: string[];        // nomi esercizi
  muscle: 'back' | 'chest' | 'legs' | 'core' | 'shoulders' | 'arms';
  // extra = tags.length - 3 (calcolato)
}
```

### Struttura dati Heatmap
```typescript
interface HeatmapDay {
  date: string;    // "YYYY-MM-DD"
  level: 0 | 1 | 2 | 3 | 4;  // 0 = nessuna attività
}
```

### Struttura dati WeightProgress
```typescript
interface WeightPoint {
  x: string;   // label asse X (es. "Mar 15")
  y: number;   // peso in kg (es. 34.5)
}
```

### KPI (da API)
- **Streak**: giorni consecutivi con almeno un allenamento
- **Sessioni totali**: count di tutte le sessioni dell'atleta
- **Ultima sessione – serie**: conteggio serie dell'allenamento più recente
- **Questa settimana**: count sessioni da lunedì a oggi

---

## Asset e Dipendenze

| Asset | Dettaglio |
|---|---|
| Font | Space Grotesk (Google Fonts) — pesi 400, 500, 600, 700, 800 |
| Icone | Lucide Icons — `lucide-react` o SVG inline |
| Grafici | SVG custom (no librerie) oppure Recharts/Chart.js se già in uso |
| Immagini | Nessuna — design completamente iconografico |

---

## File in Questo Pacchetto

| File | Contenuto |
|---|---|
| `README.md` | Questo documento |
| `Tracer Redesign.html` | Prototipo interattivo — apri nel browser per esplorare entrambe le varianti (pan/zoom, tweaks colore) |
| `tracer-shared.jsx` | Token, dati mock, componenti condivisi (WorkoutRow, Heatmap, WeightChart) |
| `tracer-v1.jsx` | Markup React della Variante A |
| `tracer-v2.jsx` | Markup React della Variante B |

> Per aprire il prototipo: apri `Tracer Redesign.html` nel browser. Usa la rotellina per zoomare, trascina per spostarti. Il pannello "Tweaks" in basso a destra permette di cambiare il colore accento.

---

## Note per l'Implementazione

1. **Scegli una variante** come base (o ibrido: sidebar icon-only della B + layout colonna singola della A).
2. **Usa i token CSS** come custom properties sul `:root` — questo rende il cambio tema banale.
3. **La sidebar della B** libera 160px di spazio e funziona molto meglio su schermi ≤1280px.
4. **La heatmap** può essere realizzata con una griglia CSS o SVG. La logica di generazione delle settimane è nel file `tracer-shared.jsx`.
5. **I tag degli esercizi** vanno troncati a 3 con badge "+N" — mostrare tutti i tag in una riga rompe il layout.
6. **Accessibilità**: aggiungi `title` o `aria-label` sulle icone e `tooltip` sulle celle heatmap. Le azioni hover-only (visualizza/duplica/elimina) devono essere accessibili anche da tastiera.
