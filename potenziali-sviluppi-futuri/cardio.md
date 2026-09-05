# Cardio (tapis roulant, cyclette, vogatore…) — registrazione dentro le sessioni

> Stato: discusso e progettato con l'utente, non ancora iniziato. Nessuna riga di codice scritta.

## Contesto

TracerGym registra oggi solo lavoro coi carichi: `WorkoutSession` contiene `WorkoutSet`, e una serie ha `reps`, `weight`, `durata`, più una serie di parametri che valgono solo per certi esercizi (`barra_kg`, `zavorra_kg`, `carrucole`, `per_lato`, `avviamento`, `a_cedimento`, `richiamo`). L'utente vuole poter registrare anche il cardio.

**Il catalogo è già pronto e non se ne era accorto nessuno.** Su 1514 esercizi, 14 hanno già `tipologia` che contiene "Cardio":

- inseriti a mano: Tapis Roulant, Cyclette, Ellittica, Vogatore, Corsa, Camminata veloce, Nuoto, HIIT, Salto con la corda
- arrivati dall'import openGym: Hands bike (ergometro braccia), Ski ergometer (skierg), Stationary bike run v. 3 (cyclette), Walk elliptical cross trainer (ellittica), Walking on stepmill (stepmill)

Su questi 14 esercizi ci sono **zero serie registrate**. Non perché non vengano usati, ma perché non esiste un posto dove mettere durata, distanza e pendenza. Manca la registrazione, non il catalogo.

Nota utile: `WorkoutSet.durata` (secondi) **esiste già ed è collegata ovunque** — form di aggiunta ([session_detail.html:408](../tracker/templates/tracker/session_detail.html#L408) e [:638](../tracker/templates/tracker/session_detail.html#L638)), form di modifica ([set_row.html:61](../tracker/templates/tracker/partials/set_row.html#L61)), visualizzazione, PDF, duplicazione, export JSON. Un esercizio a tempo (plank) funziona già oggi end-to-end. È metà della registrazione a tempo, già fatta.

## La decisione di fondo, e perché

La domanda non era "che campi servono" ma **se il cardio sia parte di una seduta o un'attività a sé**. Sono state valutate tre strade:

- **A — dentro `WorkoutSet`**, con gli esercizi cardio già in catalogo
- **B — modello autonomo**, sullo schema di `SleepEntry`/`WaterEntry`/`MacroEntry`
- **C — modello autonomo con FK facoltativa a `WorkoutSession`**, come fa già `WorkoutSet.circuit`

Inizialmente era stata proposta la **C**. L'utente ha scelto la **A**, e ha ragione: il contro-argomento alla A (aggiungere colonne quasi sempre NULL) **non regge, perché è già il modello di questo schema**. `carrucole` vale solo per le macchine a cavi, `barra_kg` solo per il bilanciere, `zavorra_kg` solo per il corpo libero. "Parametri che valgono solo per alcuni esercizi, come colonne annullabili sulla serie" è una scelta già presa e ripetuta. I parametri del tapis sono la stessa identica cosa.

In più la A fa cadere da sola il caso del riscaldamento: dieci minuti di tapis prima dei pesi finiscono nella sessione dove sono davvero stati fatti, senza doppio posto dove guardare.

## Decisioni prese con l'utente

| Domanda | Scelta |
|---|---|
| Dove vive il cardio | Come esercizio, dentro `WorkoutSet` (opzione A) |
| Come si riconosce un esercizio cardio | Campo `categoria` **nuovo** a scelte fisse; `tipologia` resta com'è |
| Giornata di solo cardio nella heatmap | Conta come allenamento, ma **distinguibile a vista** |
| Kcal bruciate | Restano un dato del cardio: **non** toccano l'obiettivo di Alimentazione |
| Cardio nel totale "N serie" della sessione | **Sì**, è una riga come le altre |

### Perché un campo `categoria` nuovo invece di riusare `tipologia`

`tipologia` è testo libero e oggi ha **33 valori distinti e incoerenti**: c'è "Cardio" ma anche "Cardio (cyclette)" e "Cardio (skierg)"; c'è "Corpo Libero" accanto a "Esercizi a corpo libero". Farci dipendere la scheda significherebbe basarsi su `icontains`, fragile.

Aggiungere `categoria` a scelte fisse lascia `tipologia` al suo ruolo di descrizione libera e non obbliga a rimappare 1514 esercizi, molti arrivati dall'import.

### Perché le kcal non toccano l'Alimentazione

Le kcal stimate dalle macchine cardio sono notoriamente sovrastimate. Collegarle a `MacroGoal` significherebbe far entrare quel margine di errore dritto nella dieta. Si registrano e si guardano nelle statistiche cardio, l'obiettivo giornaliero non si muove.

## Modello

### `Exercise` — campo nuovo

```python
CATEGORIA_CHOICES = [
    ('pesi', 'Pesi'),
    ('corpo_libero', 'Corpo libero'),
    ('cardio', 'Cardio'),
    ('mobilita', 'Mobilità / stretching'),   # da confermare con l'utente
]
categoria = models.CharField(max_length=20, choices=CATEGORIA_CHOICES, default='pesi')
```

Migrazione dati contestuale: `categoria='cardio'` sui 14 esercizi con `tipologia__icontains='cardio'`. Tutto il resto parte da `pesi` e si corregge col tempo dalla pagina Esercizi.

### `WorkoutSet` — cinque campi annullabili

| Campo | Tipo | Note |
|---|---|---|
| `distanza_m` | `PositiveIntegerField(null=True)` | metri, per non avere decimali |
| `pendenza_pct` | `DecimalField(4,1, null=True)` | tapis; anche dislivello outdoor |
| `livello` | `PositiveIntegerField(null=True)` | resistenza di cyclette/ellittica/vogatore/stepper |
| `fc_media` | `PositiveIntegerField(null=True)` | battiti al minuto |
| `kcal` | `PositiveIntegerField(null=True)` | quelle che mostra la macchina |

`durata` non va aggiunta: c'è già.

### Cosa NON salvare

**Velocità media e passo non vanno memorizzati**: sono `distanza / durata`. Tenerli accanto agli altri due garantisce che prima o poi si contraddicano — si corregge la durata e la velocità resta quella vecchia. Vanno calcolati, come fa già `WorkoutSession.real_sets_count()`, che conta invece di conservare.

Diverso il caso della **velocità impostata** sul tapis, che con gli intervalli non coincide con la media: se servirà, è un campo suo con un altro significato, da decidere a parte.

## Il lavoro vero: la scheda che si adatta

È il pezzo più grosso, ed è bene saperlo prima di iniziare. Oggi [set_row.html](../tracker/templates/tracker/partials/set_row.html) mostra gli stessi campi per qualunque esercizio: reps, peso, recupero e sette caselle. Su un tapis roulant "reps" e "peso" non significano niente, e manca tutto il resto.

Quindi il form di aggiunta e la riga di modifica devono **ramificare su `exercise.categoria`**: sul cardio spariscono reps e peso, compaiono distanza/pendenza/livello/FC/kcal.

Questo lavoro **si ripaga oltre il cardio**: lo stesso meccanismo permette di far sparire "carrucole" da un esercizio col bilanciere, che oggi compare sempre per tutti.

Non conviene spingere la ramificazione più a fondo: HIIT e salto della corda sono cardio senza distanza né pendenza, ma i campi sono facoltativi e lasciarli vuoti costa meno che inventare sotto-categorie per macchina.

## Heatmap

Siccome il cardio è una `WorkoutSet`, la heatmap dell'anno **lo conta già da sola**: [views.py:155](../tracker/views.py#L155) colora in base al numero di serie del giorno, quindi non serve aggiungere niente per farlo comparire.

Per distinguere a vista una giornata di **solo** cardio serve che la view esponga anche un "quel giorno c'erano pesi sì/no" per data, e che la cella si disegni col contorno invece che piena. Il meccanismo del bordo esiste già: [year-heatmap.js](../tracker/static/tracker/year-heatmap.js) lo usa per marcare il giorno corrente.

## Cosa NON va toccato

Siccome l'utente ha scelto che il cardio conti come riga normale:

- `real_sets_count()` resta com'è
- dashboard, PDF sessione e profilo pubblico continuano a funzionare senza modifiche

## Fasi

1. **Registrazione** — `categoria`, i cinque campi, form e riga che si adattano. Alla fine di questa fase il tapis è registrabile. Tocca: `models.py`, due migrazioni, le view di creazione/modifica/duplicazione/export in `views.py` (vedi i punti dove passa già `durata`: righe ~433, 510, 530, 640, 732, 761, 793), `set_row.html`, il form in `session_detail.html`, il PDF.
2. **Heatmap** — giornate di solo cardio distinguibili.
3. **Statistiche** — il grafico della dashboard traccia oggi il *peso* nel tempo per esercizio; per il cardio la curva che dice qualcosa è la distanza o il passo, quindi va trattato separatamente.

## Avvertenze

- Porta **due migrazioni nuove** (campo su `Exercise` + campi su `WorkoutSet`, più la migrazione dati): `migrate` obbligatorio in locale e su PythonAnywhere.
- È il cambiamento più invasivo fatto finora sul progetto: tocca modelli, migrazioni, view e i due template più densi del repo.
- Al momento della discussione il DB locale era indietro con la `0041` (`zavorra_kg`), da applicare prima di iniziare.
