# Cardio (tapis roulant, cyclette, vogatore…) — registrazione dentro le sessioni

> Stato: progettato con l'utente in due riprese, non ancora iniziato. Nessuna riga di codice scritta.
> Riferimenti di riga verificati sul codice alla migrazione `0044`.

## Contesto

TracerGym registra oggi solo lavoro coi carichi: `WorkoutSession` contiene `WorkoutSet`, e una serie ha `reps`, `weight`, `durata`, più parametri che valgono solo per certi esercizi (`barra_kg`, `zavorra_kg`, `carrucole`, `per_lato`, `avviamento`, `a_cedimento`, `richiamo`).

**Il catalogo è già pronto e non se ne era accorto nessuno.** Su ~1514 esercizi, 14 hanno già `tipologia` che contiene "Cardio":

- inseriti a mano: Tapis Roulant, Cyclette, Ellittica, Vogatore, Corsa, Camminata veloce, Nuoto, HIIT, Salto con la corda
- arrivati dall'import openGym: ergometro braccia, ski erg, cyclette a ritmo di corsa, camminata all'ellittica, camminata allo stepmill

Su questi 14 ci sono **zero serie registrate**. Non perché non vengano usati, ma perché non esiste un posto dove mettere durata, distanza e pendenza. **Manca la registrazione, non il catalogo.**

> **Attenzione al confine con [camminata.md](camminata.md).** Questo documento riguarda il cardio **dentro una seduta**: il tapis prima delle panche, la cyclette a fine allenamento. Camminate e corse **all'aperto** sono uscite a sé stanti e vivono in un modello loro, perché per registrarle qui bisognerebbe creare una `WorkoutSession` vuota apposta.
>
> Gli esercizi "Corsa" e "Camminata veloce" restano quindi in questo elenco, ma vanno intesi come corsa e camminata **sul tapis, in palestra**. La stessa attività fatta fuori si registra nell'altra pagina.



Nota utile: `WorkoutSet.durata` (secondi) **esiste già ed è collegata ovunque**. Un esercizio a tempo (plank) funziona già oggi da capo a fondo. È metà della registrazione a tempo, già fatta.

## La decisione di fondo, e perché

La domanda non era "che campi servono" ma **se il cardio sia parte di una seduta o un'attività a sé**. Tre strade valutate:

- **A** — dentro `WorkoutSet`, con gli esercizi cardio già in catalogo
- **B** — modello autonomo, sullo schema di `SleepEntry` / `WaterEntry` / `MacroEntry`
- **C** — modello autonomo con FK facoltativa a `WorkoutSession`

Era stata proposta la **C**. L'utente ha scelto la **A**, e ha ragione: il contro-argomento alla A (aggiungere colonne quasi sempre NULL) **non regge, perché è già il modello di questo schema**. `carrucole` vale solo per le macchine a cavi, `barra_kg` solo per il bilanciere, `zavorra_kg` solo per il corpo libero. "Parametri che valgono solo per alcuni esercizi, come colonne annullabili sulla serie" è una scelta già presa e ripetuta. I parametri del tapis sono la stessa identica cosa.

In più la A fa cadere da sola il caso del riscaldamento: dieci minuti di tapis prima dei pesi finiscono nella sessione dove sono davvero stati fatti.

## Decisioni prese con l'utente

| Domanda | Scelta |
|---|---|
| Dove vive il cardio | Come esercizio, dentro `WorkoutSet` (opzione A) |
| Come si riconosce un esercizio cardio | Campo `categoria` **nuovo** a scelte fisse; `tipologia` resta com'è |
| Granularità di una seduta | **Una riga per blocco di lavoro**, non una per seduta |
| Intervalli e HIIT | Nessun campo nuovo: si usano i **circuiti** che esistono già |
| Velocità impostata | **Sì**, come regolazione della macchina (vedi sotto) |
| Sforzo percepito (RPE) | **Sì**, è l'unica metrica che copre anche nuoto, HIIT e corda |
| Giornata di solo cardio nella heatmap | Conta come allenamento, ma **distinguibile a vista** |
| Kcal bruciate | Restano un dato del cardio: **non** toccano l'obiettivo di Alimentazione |
| Cardio nel totale "N serie" | **Sì**, è una riga come le altre |

### Perché `categoria` nuovo invece di riusare `tipologia`

`tipologia` è testo libero e ha **33 valori distinti e incoerenti**: c'è "Cardio" ma anche "Cardio (cyclette)" e "Cardio (skierg)"; c'è "Corpo Libero" accanto a "Esercizi a corpo libero". Farci dipendere la scheda significherebbe basarsi su `icontains`, fragile. Un campo a scelte fisse lascia `tipologia` al suo ruolo di descrizione libera.

### Perché una riga per blocco

Su una seduta a intervalli, una riga sola costringe a una pendenza media e a una velocità media che non descrivono niente di reale. Una riga per blocco è più fedele, e **non costa niente sulle sedute continue**: una corsa di 40 minuti resta una riga sola.

Conseguenza da sapere: un HIIT da 5 round × 2 blocchi conterà **10 serie** nel totale della sessione. È coerente con come contano già i circuiti coi pesi, ma sul contatore della dashboard si vede.

### Perché le kcal non toccano l'Alimentazione

Le kcal stimate dalle macchine sono notoriamente sovrastimate. Collegarle a `MacroGoal` farebbe entrare quel margine di errore dritto nella dieta. Si registrano e si guardano nelle statistiche cardio; l'obiettivo giornaliero non si muove.

## Le metriche, raggruppate per cosa servono

Non servono tutte alla stessa cosa, e tenerle separate aiuta a decidere cosa mostrare per primo nella scheda:

| Gruppo | Campi | A cosa serve |
|---|---|---|
| **Quanto hai fatto** | `durata`, `distanza_m` | le uniche che rendono confrontabili due sedute a mesi di distanza |
| **Com'era regolata la macchina** | `pendenza_pct`, `livello`, `velocita_kmh` | rendono confrontabile il "quanto": 5 km al 6% non sono 5 km in piano |
| **Come ha risposto il corpo** | `fc_media`, `rpe` | l'unica parte che dice se stavi davvero spingendo |
| **Stima della macchina** | `kcal` | la meno affidabile di tutte |

### Cosa produce davvero ciascun gruppo di esercizi

| Gruppo | Esercizi | Cosa si legge sul display |
|---|---|---|
| Percorso | Tapis, Corsa, Camminata veloce, Stepmill | durata, distanza, pendenza, velocità, kcal |
| Resistenza ciclica | Cyclette (×2), Ellittica (×2), Ergometro braccia | durata, distanza, livello, kcal |
| Remata | Vogatore, Ski erg | durata, distanza, passo /500m, watt |
| Senza macchina | Nuoto, HIIT, Salto con la corda | durata e basta (il nuoto ha le vasche) |

Il gruppo "remata" si copre per calcolo: passo e watt derivano da distanza e durata. Il gruppo "senza macchina" è coperto **solo** da `rpe`: è la ragione per cui quel campo esiste.

## Modello

### `Exercise` — campo nuovo

```python
CATEGORIA_CHOICES = [
    ('pesi', 'Pesi'),
    ('corpo_libero', 'Corpo libero'),
    ('cardio', 'Cardio'),
    ('mobilita', 'Mobilità / stretching'),   # DA CONFERMARE, vedi sotto
]
categoria = models.CharField(max_length=20, choices=CATEGORIA_CHOICES, default='pesi')
```

### `WorkoutSet` — sette campi annullabili

| Campo | Tipo | Note |
|---|---|---|
| `distanza_m` | `PositiveIntegerField(null=True)` | metri, per non avere decimali |
| `pendenza_pct` | `DecimalField(4, 1, null=True)` | tapis; anche dislivello outdoor |
| `livello` | `PositiveIntegerField(null=True)` | resistenza di cyclette/ellittica/vogatore |
| `velocita_kmh` | `DecimalField(4, 1, null=True)` | velocità **impostata**, non media |
| `fc_media` | `PositiveIntegerField(null=True)` | battiti al minuto |
| `rpe` | `PositiveSmallIntegerField(null=True)` | sforzo percepito 1-10 |
| `kcal` | `PositiveIntegerField(null=True)` | quelle che mostra la macchina |

`durata` non va aggiunta: c'è già.

### Distanza e velocità non sono ridondanti

Sembra una violazione della regola "non salvare ciò che si calcola", e invece no.

Quella regola riguarda la **velocità media**, che è `distanza / durata`: tenerla accanto agli altri due garantisce che prima o poi si contraddicano (correggi la durata e la media resta quella vecchia). Quella non si salva, si calcola.

La **velocità impostata** è un'altra cosa: è una regolazione della macchina, come pendenza e livello. E soprattutto, con le righe per blocco, è *l'unica* che conosci davvero: se fai 3 minuti a 12 km/h, il display ti mostra i chilometri **totali** della seduta, non quelli di quel blocco. Nessuno andrà mai a calcolare "0,6 km" per ogni intervallo.

Quindi distanza e velocità sono **i due modi alternativi in cui conosci lo stesso tratto**, e quale dei due hai dipende da come ti sei allenato: intervalli in palestra → sai la velocità; corsa all'aperto → sai la distanza.

Regola d'oro conseguente: **l'app non calcola mai uno dall'altro e non li confronta.** Mostra quello che hai scritto. Se un giorno servirà il passo medio, si calcola al volo da distanza e durata dove ci sono entrambe, come fa già `WorkoutSession.real_sets_count()`, che conta invece di conservare.

## Il lavoro vero

### 1. La scheda che si adatta — e perché non basta il server

Oggi [set_row.html](../tracker/templates/tracker/partials/set_row.html) mostra gli stessi campi per qualunque esercizio: reps, peso, recupero e sette caselle. Su un tapis "reps" e "peso" non significano niente, e manca tutto il resto. Il form deve ramificare su `exercise.categoria`.

**Ma la ramificazione non può stare solo sul server.** L'esercizio si sceglie con un campo di ricerca con autocompletamento ([session_detail.html:392](../tracker/templates/tracker/session_detail.html#L392)): finché non si preme Salva, il server non sa quale esercizio sia. Quindi i campi devono cambiare **nel browser**, appena si sceglie dalla tendina.

Conseguenza concreta: **[`exercise_suggestions`](../tracker/views.py#L1500) deve restituire anche la categoria**, che oggi manda solo nome e immagine.

Questo lavoro **si ripaga oltre il cardio**: lo stesso meccanismo permette di far sparire "carrucole" da un esercizio col bilanciere, che oggi compare sempre per tutti.

Non conviene spingere la ramificazione più a fondo: HIIT e salto della corda sono cardio senza distanza né pendenza, ma i campi sono facoltativi e lasciarli vuoti costa meno che inventare sotto-categorie per macchina.

### 2. Manca un posto dove impostare `categoria`

Il modale di modifica esercizio gestisce nome, tipologia, tag e immagine — e basta ([views.py:1311](../tracker/views.py#L1311)). Senza aggiungerci `categoria`, il piano "si corregge col tempo dalla pagina Esercizi" **non ha dove avvenire**. Va aggiunta lì, e anche in [`add_exercise_ajax`](../tracker/views.py#L1281) per gli esercizi creati al volo dalla sessione.

### 3. Riempire `categoria` senza sistemare 1514 esercizi a mano

Con `default='pesi'` si parte con 14 esercizi giusti e ~1500 da correggere uno alla volta da un modale: non succederà mai.

**La logica per indovinarla esiste già.** In [exercises.html:713](../tracker/templates/tracker/exercises.html#L713) c'è `equipBucket()`, che mappa `tipologia` → corpo libero / cardio / bilanciere / manubrio / cavi / macchine / elastico / kettlebell, ed è quella che alimenta i filtri per attrezzo. La migrazione dati può riusare la stessa identica logica in Python:

- bucket `cardio` → `categoria='cardio'`
- bucket `corpo` → `categoria='corpo_libero'`
- tutto il resto → `categoria='pesi'`

Così la grande maggioranza parte già a posto, e le correzioni manuali diventano poche.

Suggerimento: il filtro admin "Senza immagine" appena aggiunto alla pagina Esercizi è lo stesso identico meccanismo di un eventuale filtro "categoria da controllare", se servisse un giro di ripulitura.

## Heatmap

Siccome il cardio è una `WorkoutSet`, la heatmap dell'anno **lo conta già da sola**: [views.py:198](../tracker/views.py#L198) colora in base al numero di serie del giorno.

Per distinguere a vista una giornata di **solo** cardio serve che la view esponga anche un "quel giorno c'erano pesi sì/no" per data, e che la cella si disegni col contorno invece che piena. Il meccanismo del bordo esiste già: [year-heatmap.js](../tracker/static/tracker/year-heatmap.js) lo usa per marcare il giorno corrente.

## Punti del codice da toccare

I sette campi nuovi seguono la stessa strada che fa già `durata`. Questi sono i punti, verificati:

| Punto | Cosa fa |
|---|---|
| [views.py:463](../tracker/views.py#L463) | lettura dal POST in `session_detail` |
| [views.py:540](../tracker/views.py#L540), [:560](../tracker/views.py#L560) | creazione delle serie (normale e avviamento) |
| [views.py:762](../tracker/views.py#L762) | `duplicate_set` |
| [views.py:782](../tracker/views.py#L782) | `_CAMPI_PROPAGABILI` — **l'"applica a tutte"**: va deciso se i campi cardio si propagano |
| [views.py:807](../tracker/views.py#L807) | `edit_set` |
| [views.py:877](../tracker/views.py#L877), [:891](../tracker/views.py#L891) | duplicazione di una sessione intera |
| [views.py:391](../tracker/views.py#L391), [:1065](../tracker/views.py#L1065) | export JSON |
| [views.py:1122](../tracker/views.py#L1122) | import JSON |
| [session_detail.html:409](../tracker/templates/tracker/session_detail.html#L409) | form di aggiunta serie |
| [session_detail.html:639](../tracker/templates/tracker/session_detail.html#L639) | form dentro il circuito |
| [session_detail.html:793](../tracker/templates/tracker/session_detail.html#L793) | PDF della sessione |
| [set_row.html:62](../tracker/templates/tracker/partials/set_row.html#L62) | riga di modifica inline |

`_CAMPI_PROPAGABILI` è il punto più facile da dimenticare: è quello che fa funzionare "applica a tutte", ed è ragionevole che pendenza e livello si propaghino agli altri blocchi mentre distanza e kcal no.

## Cosa NON va toccato

Siccome il cardio conta come riga normale:

- `real_sets_count()` resta com'è
- dashboard, PDF sessione e profilo pubblico continuano a funzionare senza modifiche

## Domanda ancora aperta

**La categoria `mobilita` (mobilità / stretching) va inclusa o no?** È l'unica decisione rimasta, e va presa *prima* della migrazione: aggiungerla dopo significa rifare un giro di dati su tutto il catalogo.

## Fasi

1. **Registrazione** — `categoria`, i sette campi, la scheda che si adatta, `exercise_suggestions` che espone la categoria, e il campo `categoria` nel modale di modifica. Alla fine di questa fase il tapis è registrabile.
2. **Heatmap** — giornate di solo cardio distinguibili.
3. **Statistiche** — la card della dashboard si chiama ora "Progressione peso" e dichiara cosa mostra, quindi un eventuale grafico cardio (distanza o passo nel tempo) è una card sua, senza ambiguità da sciogliere.

## Avvertenze

- Porta **due migrazioni di schema più una di dati**: `migrate` obbligatorio in locale e su PythonAnywhere.
- È il cambiamento più invasivo fatto finora sul progetto: tocca modelli, migrazioni, view e i due template più densi del repo.
- I test girano solo su SQLite in locale (manca `mysqlclient`), e la `0039` interroga `information_schema`, che è solo MySQL: la suite si lancia con `MIGRATION_MODULES = {'tracker': None}`.
