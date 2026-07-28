# Tracer

Un workout tracker personale, costruito un pezzo alla volta attorno a come si allena davvero chi lo usa — non attorno a un template generico da app fitness.

Non è pensato per "gamificare" l'allenamento o inondarti di statistiche. È pensato per essere il quaderno digitale che tieni in palestra: veloce da aggiornare tra una serie e l'altra, capace di ricordare tutto quello che scrivi, e onesto sui limiti di quello che non sa ancora fare.

---

## L'idea di fondo

Tutto ruota attorno a un'unità semplice: la **sessione**, cioè un allenamento di una giornata. Dentro una sessione succedono due cose:

- registri **serie** — un esercizio, ripetizioni o durata, peso, recupero, ed eventuali qualificatori (se è di avviamento, se è portata a cedimento, se è un richiamo, se va fatta per lato, se c'è una sbarra da sommare al carico);
- oppure costruisci un **circuito** — un gruppo di esercizi da ripetere per un certo numero di round, con un recupero condiviso tra un round e l'altro, distinto dal recupero delle singole serie.

Ogni esercizio che scrivi viene raggruppato automaticamente: espandendolo vedi tutte le serie fatte per quel movimento in quella giornata, riordinabili trascinandole, modificabili una a una senza perdere il contesto delle altre.

Una sessione, oltre alle serie, può portare con sé il contorno che la rende un ricordo e non solo un log: dove ti sei allenato, a che ora, quanto è durata, il tuo peso corporeo quel giorno, e con chi.

## Cosa c'è dentro

**Allenamenti**
Aggiunta rapida delle serie con autocomplete sugli esercizi già catalogati, modifica inline, duplicazione di una singola serie o dell'intera sessione, riordino via drag & drop sia degli esercizi che delle singole serie al loro interno. I circuiti si possono costruire da zero oppure importare di peso da una sessione passata — utile quando rifai lo stesso allenamento a distanza di settimane senza doverlo riscrivere.

**Catalogo esercizi**
Ogni esercizio ha un nome, una tipologia, dei tag muscolari e, opzionalmente, delle immagini di riferimento. Una mappa del corpo umano interattiva permette di navigare gli esercizi per gruppo muscolare invece che per nome.

**Dashboard**
Una heatmap annuale mostra a colpo d'occhio la costanza degli allenamenti mese per mese. Un grafico di andamento traccia nel tempo il peso sollevato su un esercizio specifico. Una vista di programmazione settimanale riassume la settimana corrente giorno per giorno, esportabile in PDF per chi la stampa o la condivide con un trainer.

**Acqua**
Un log giornaliero dell'acqua bevuta, con obiettivo personalizzabile, aggiunte rapide o a quantità precisa, e una heatmap annuale colorata in base a quanto ci si è avvicinati all'obiettivo ogni giorno.

**Misurazioni**
Peso corporeo, altezza e percentuale di massa grassa, una voce al giorno, con un grafico di andamento selezionabile per metrica. Pensato per restare separato dal peso che eventualmente annoti dentro una singola sessione: sono due gesti diversi, in due momenti diversi.

**Atleti**
Ogni utente ha un profilo che può essere pubblico o privato. Chi rende pubblico il proprio profilo permette ad altri di vedere il proprio storico e, sessione per sessione, di importarne la struttura come punto di partenza per un proprio allenamento.

**Backup**
Le sessioni si esportano e importano in JSON, per chi vuole un backup indipendente dal database o vuole spostare i propri dati altrove.

## Come è fatto

Backend Django, database MySQL in produzione. Il frontend non usa framework JavaScript: sono template Django con JavaScript vanilla dove serve interattività (drag & drop, autocomplete, grafici via Chart.js), pensati per restare leggeri e comprensibili riga per riga piuttosto che dipendere da una build chain.

Il tema è viola scuro, disegnato prima come mockup statici e poi portato dentro l'app pagina per pagina, mantenendo lo stesso linguaggio visivo — stessi colori, stessi badge, stesse card — su dashboard, sessione, profilo e le pagine più recenti come acqua e misurazioni.
