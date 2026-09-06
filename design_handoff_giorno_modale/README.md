# Handoff: Modale Giorno (Sessioni) + Widget accessori

## Overview
Pacchetto di riferimenti UI per l'app di tracking allenamenti "Tracer": modale per interagire con le sessioni di un giorno (inclusa l'importazione di una sessione da un altro atleta), più alcuni widget correlati (accent color picker, widget acqua, login) prodotti nella stessa sessione di design.

## About the Design Files
I file in questo pacchetto sono **riferimenti di design creati in HTML** — prototipi che mostrano l'aspetto e il comportamento previsti, non codice di produzione da copiare direttamente. Il compito è **ricreare questi design HTML nell'ambiente esistente del codebase target** (React, Vue, ecc.) usando i pattern e le librerie già stabiliti — oppure, se non esiste ancora un ambiente, scegliere il framework più adatto e implementare lì i design.

## Fidelity
**Low/Mid-fidelity**: layout e interazioni sono definiti, palette e tipografia sono indicative (coerenti con lo stile dark dell'app "Tracer": sfondo grigio petrolio, accent arancio/viola, font Space Grotesk + Plus Jakarta Sans) ma da validare contro il design system reale del prodotto.

## Screens / Views

### 1. Modale Giorno (`Modale Giorno - Schizzo.dc.html`)
**Purpose**: aperto cliccando una cella della calendar-heatmap; permette di vedere/gestire le sessioni di una giornata.

**Layout**: card centrata 420px, `flex-direction: column`, gap 16px, padding 22px, bg `#141c24`, border `rgba(255,255,255,0.08)`, radius 18px.

**Componenti**:
- Header: freccia ← / data (Space Grotesk 17px bold) / freccia → per navigare ai giorni adiacenti, + pulsante chiudi (X) in alto a destra.
- Riepilogo: 2 card affiancate (flex:1) "DURATA TOT." e "CALORIE", bg `rgba(244,144,58,0.12)`, border `rgba(244,144,58,0.28)`, valore in Space Grotesk 17px bold.
- Lista sessioni del giorno: righe cliccabili, icona emoji in box 36x36 radius 10, titolo bold 14px bianco, meta 12px grigio (`#8b93a3`), chevron a destra. Hover: bg più chiara.
- Riga azioni: due pulsanti affiancati (flex:1 ciascuno) — **"Nuova sessione"** (bordo dashed) e **"Importa sessione"** (bordo solido) che apre/chiude il pannello di import.
- Pannello import (condizionale):
  - Stato ricerca: input ricerca atleta + lista risultati (avatar, nome, conteggio sessioni), click su un atleta seleziona.
  - Stato atleta selezionato: header con freccia "indietro" + avatar + nome, poi lista delle sue sessioni (titolo, meta: tipo/durata/data) ciascuna con pulsante "Importa" (badge viola `rgba(124,108,246,0.14)` / testo `#a996ff`).

**Nota per implementazione reale**: con molte sessioni (es. centinaia/migliaia) per atleta, la lista sessioni interna al pannello import necessita di **ricerca/filtro proprio** (per data o nome) e/o **paginazione o virtualizzazione** — nel prototipo è solo uno scroll fisso (max-height 160px), non adatto a dataset grandi.

### 2. Accent Color Picker (`Impostazioni - Accent Color Picker.dc.html`)
**Purpose**: pagina impostazioni per scegliere liberamente il colore accent dell'app.

**Componenti**:
- Quadrato saturazione/luminosità (200px alto, gradiente CSS) con cursore draggabile (mousedown + mousemove/mouseup su window).
- Slider tonalità (hue, gradiente arcobaleno 16px alto) con cursore draggabile.
- Swatch colore corrente + input hex editabile, sincronizzati bidirezionalmente con HSV.
- Sezione anteprima: card sessione + pulsante CTA che si aggiornano live col colore scelto.

**Stato**: `{h, s, v, hexInput}`; conversioni HSV↔HEX implementate in JS puro (vedi logica nel file).

### 3. Widget Acqua (`Acqua Widget - Riga Fix.dc.html`)
Card 360px: intestazione con emoji + valore corrente/obiettivo in L, pulsante impostazioni obiettivo (icona gear), 3 quick-add (+250ml/+500ml/+1L), riga orario (fisso 118px) + input ml (56px) + pulsante "Aggiungi" (flex:1), barra di progresso, link "Vedi storico".

### 4. Login (`Tracer Login.dc.html`)
Schermata login split: colonna sinistra con branding, colonna destra col modulo di login. Sfondo grigio petrolio (`#10171a` pagina, `#131c1f` card, `#182226` box "attività recente"), accent viola invariato.

## Interactions & Behavior
- Modale: freccine cambiano giorno mantenendo il modale aperto; click su riga sessione apre dettaglio (non nel prototipo); toggle "Importa sessione" mostra/nasconde pannello; click su atleta passa da ricerca a lista sessioni sue; "indietro" torna alla ricerca.
- Color picker: drag continuo su mousemove/mouseup globali (listener attaccati a `window`, rimossi al rilascio).
- Tutti gli hover-state sono gestiti con leggero aumento di opacità/background, nessuna animazione elaborata.

## State Management
- Modale: `importing` (bool), `query` (string), `selectedAthlete` (object|null).
- Color picker: `h, s, v` (HSV), `hexInput` (string), sincronizzati ad ogni drag/change.
- Dati atleti/sessioni sono mock hardcoded nel file — da collegare a API reale.

## Design Tokens
- Sfondo pagina: `#0c1218` / `#10171a`
- Card: `#141c24` / `#131c1f`
- Card secondaria: `#182226`
- Bordo: `rgba(255,255,255,0.06–0.08)`
- Testo secondario: `#8b93a3` / `#7d8296`
- Accent arancio: `#f4903a` (soft `rgba(244,144,58,0.12–0.18)`)
- Accent viola: `#7c6cf6` / `#a996ff` (soft `rgba(124,108,246,0.14)`)
- Accent blu (corsa): `#6cb4ff`
- Font: `Space Grotesk` (bold, titoli/numeri), `Plus Jakarta Sans` (500/600/700, corpo)
- Radius: 9–18px a seconda del componente
- Font minimo: 10px (etichette maiuscole), corpo 12–14px

## Assets
Solo emoji Unicode (🏋️ 🏃 💧🧑👩) come placeholder icone — da sostituire con icon set reale del prodotto. Icone freccia/chiudi/ricerca/impostazioni sono inline SVG (stroke `currentColor`/hex, disegnate a mano, libere da licenza).

## Files
- `Modale Giorno - Schizzo.dc.html`
- `Impostazioni - Accent Color Picker.dc.html`
- `Acqua Widget - Riga Fix.dc.html`
- `Tracer Login.dc.html`

Ogni file è un documento HTML autonomo (apribile diretto nel browser) che include un runtime leggero (`support.js`, non incluso qui) per il templating — l'importante per l'implementazione è il markup/stile risultante e la logica descritta sopra, non il runtime stesso.
