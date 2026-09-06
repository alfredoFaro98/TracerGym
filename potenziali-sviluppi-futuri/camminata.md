# Camminata e corsa — pagina autonoma

> Stato: progettato con l'utente, non ancora iniziato. Nessuna riga di codice scritta.
> **Non dipende dal lavoro sul cardio**: si può fare prima, dopo o in mezzo.

## Cosa ci va dentro

Quattro cose, decise dall'utente:

- **camminata**
- **corsa**
- **corsa pesata** (con gilet o zaino zavorrato)
- **numero passi giornalieri**

## La decisione di fondo: perché fuori dalle sessioni

Sembra in contraddizione con [cardio.md](cardio.md), dove il cardio finisce dentro `WorkoutSet`. Non lo è, perché **la linea non è "cardio contro pesi", è "dentro una seduta" contro "uscita a sé stante"**.

Dieci minuti di tapis prima delle panche fanno parte di quella seduta: hanno un senso solo lì, e infatti vanno in `WorkoutSet`. Un'ora di corsa al parco non ha nessuna seduta attorno: per registrarla come `WorkoutSet` bisognerebbe creare una `WorkoutSession` vuota apposta per contenerla, che è una finzione.

Sono due situazioni diverse davvero, non la stessa cosa messa in due posti.

### La conseguenza da accettare

Con questa scelta **la corsa può stare in due posti**: sul tapis in palestra è una serie cardio dentro la seduta, all'aperto è un'uscita. È accettabile perché la linea è netta e si sa sempre da che parte si sta (dentro la palestra / fuori), ma vuol dire che un domani "quanto ho corso quest'anno" va chiesto a due tabelle.

Mitigazione possibile, se servirà: la pagina può mostrare **in sola lettura** anche le corse su tapis pescate dalle sessioni. Non è previsto per ora.

## Due modelli, non uno

Le quattro voci **non hanno la stessa forma**, ed è la cosa che decide lo schema:

- Camminata, corsa e corsa pesata sono **eventi**: in un giorno ne puoi fare zero, una o tre.
- I passi sono **un totale giornaliero**: uno solo per data.

E si sovrappongono **di proposito**: una camminata registrata come uscita è già dentro il conteggio passi di quel giorno. Non è un doppione, sono due misure diverse — *quanto ti sei mosso in tutto* e *cosa hai fatto apposta*. Va detto chiaro nella pagina, altrimenti uno guarda i due numeri e si chiede perché non tornano.

### `Uscita`

Le tre attività stanno in **una tabella sola con un campo `tipo`**, non in tre tabelle: condividono quasi tutti i campi, e la corsa pesata è una corsa con in più la zavorra.

```python
class Uscita(models.Model):
    TIPO_CHOICES = [
        ('camminata', 'Camminata'),
        ('corsa', 'Corsa'),
        ('corsa_pesata', 'Corsa pesata'),
    ]
    utente = models.ForeignKey(User, on_delete=models.CASCADE, related_name='uscite')
    data = models.DateField(default=timezone.now)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='camminata')

    durata_min = models.PositiveIntegerField(null=True, blank=True)
    distanza_m = models.PositiveIntegerField(null=True, blank=True)
    dislivello_m = models.PositiveIntegerField(null=True, blank=True)
    zavorra_kg = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    fc_media = models.PositiveIntegerField(null=True, blank=True)
    rpe = models.PositiveSmallIntegerField(null=True, blank=True)   # 1-10
    percorso = models.ForeignKey('Percorso', null=True, blank=True, on_delete=models.SET_NULL)
    nota = models.CharField(max_length=200, blank=True, default='')
    creato_il = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-data', '-creato_il']
```

Due note sui nomi:

- **`zavorra_kg`** è lo stesso nome e lo stesso significato che ha già su `WorkoutSet` per gli esercizi a corpo libero. Coerenza voluta.
- **`durata_min` è in minuti**, mentre `WorkoutSet.durata` è in secondi. Non è una svista: una serie di plank si misura in secondi, un'uscita in minuti. Scrivere 2700 al posto di 45 sarebbe assurdo. La differenza va ricordata quando un domani si vorranno sommare le due cose.

### `Percorso`

La versione piccola e utile dei percorsi: nessun GPX, nessuna mappa. Un nome e una distanza, da riusare.

```python
class Percorso(models.Model):
    utente = models.ForeignKey(User, on_delete=models.CASCADE, related_name='percorsi')
    nome = models.CharField(max_length=80)
    distanza_m = models.PositiveIntegerField()
    dislivello_m = models.PositiveIntegerField(null=True, blank=True)
    nota = models.CharField(max_length=200, blank=True, default='')

    class Meta:
        unique_together = ('utente', 'nome')
        ordering = ['nome']
```

Scegliendo un percorso nel form dell'uscita, distanza e dislivello si compilano da soli. Il vero valore non è risparmiare due campi: è poter **confrontare lo stesso giro nel tempo**.

`on_delete=SET_NULL` di proposito: cancellare un percorso non deve cancellare le uscite fatte su quel percorso, che restano valide con la loro distanza già scritta.

### `PassiGiorno`

Sulla forma di `SleepEntry`: **un valore per giorno**, non voci che si sommano come l'acqua.

```python
class PassiGiorno(models.Model):
    utente = models.ForeignKey(User, on_delete=models.CASCADE, related_name='passi_giorno')
    data = models.DateField(default=timezone.now)
    passi = models.PositiveIntegerField()
    nota = models.CharField(max_length=200, blank=True, default='')
    creato_il = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('utente', 'data')
        ordering = ['-data']
```

Più `UserProfile.obiettivo_passi = PositiveIntegerField(default=10000)`.

L'obiettivo per singolo giorno (come `WaterGoal` e `MacroGoal`) **non si fa adesso**: è additivo, si aggiunge se servirà.

## Cosa NON salvare

Come per il cardio, si calcola invece di conservare:

- **passo** (min/km) e **velocità media** — sono `durata / distanza`. Salvarli garantisce che prima o poi contraddicano la durata corretta a posteriori.
- **distanza stimata dai passi** — si ricava dai passi e dall'altezza, che è già in `BodyMetric`.

## L'inserimento dei passi è il punto che decide tutto

I passi si leggono sul telefono e si scrivono a mano. Questo vuol dire una cosa sola: **nessuno apre l'app ogni sera per digitare un numero.** Ci si dimentica tre giorni e poi si recupera, oppure si molla.

Quindi l'inserimento su **più giorni in un colpo solo** non è un extra, è la funzione che decide se la pagina viene usata a febbraio o abbandonata. Serve una griglia con i sette giorni della settimana e sette caselle, che si compila e si salva insieme.

Il modello di questa cosa esiste già in [`add_integratore_range`](../tracker/views.py#L2154), che scrive lo stesso valore su un intervallo di date. Qui serve la variante con **valori diversi per ogni giorno**, ma l'impianto (leggere un intervallo, ciclare sulle date, salvare in blocco) è lo stesso.

Siccome `PassiGiorno` ha `unique_together` su utente e data, il salvataggio va fatto con `update_or_create`: reinserire una settimana già compilata deve **correggere** i valori, non fallire.

## La pagina

Una pagina sola, due sezioni, sulla falsariga di quelle che esistono già.

### Passi

- Passi di oggi contro obiettivo, con la barra di avanzamento
- **Heatmap dell'anno** — [year-heatmap.js](../tracker/static/tracker/year-heatmap.js) è già generico, si passano i dati e basta
- Grafico dell'andamento con la scala `--chart-1..5`, che segue l'accent
- Media settimanale e mensile, e striscia di giorni sopra obiettivo (`_week_streak` in [views.py](../tracker/views.py) fa già una cosa del genere per gli allenamenti)
- Inserimento settimanale a sette caselle (vedi sopra)

### Uscite

- Elenco per data, raggruppato come fa la pagina Alimentazione
- Form di aggiunta con i campi che cambiano sul tipo: la **zavorra compare solo sulla corsa pesata**
- Filtro per tipo
- Totali del mese: chilometri, dislivello, passo medio

### Percorsi

Un elenco gestibile (crea, modifica, elimina) dentro la stessa pagina, in una sezione richiudibile. Non merita una pagina sua: si usano solo da qui.

## Cosa NON va toccato

L'utente ha deciso che **un'uscita non fa di quel giorno un giorno di allenamento**:

- la heatmap della home continua a contare solo le serie in palestra
- la striscia settimanale resta quella delle sedute
- dashboard, profilo pubblico e conteggi non cambiano di una riga

**Conseguenza da sapere**: un'ora di corsa lascia la casella di quel giorno spenta nella home. È stato scelto sapendolo. Se un domani si cambia idea, è un cambiamento **additivo** (la heatmap impara a guardare due fonti) e non richiede migrazioni di dati.

Questa decisione è anche ciò che rende la pagina completamente autonoma: **zero modifiche al codice esistente**, a parte la voce nel menu e il campo `obiettivo_passi` sul profilo.

## Fasi

1. **Passi** — modello, obiettivo, inserimento singolo e settimanale, heatmap, grafico. Da sola è già una pagina utile tutti i giorni, ed è la parte più semplice di tutto ciò di cui si è parlato finora.
2. **Uscite** — modello, form che si adatta al tipo, elenco, totali del mese.
3. **Percorsi** — elenco e scorciatoia nel form dell'uscita.

Le tre fasi sono indipendenti fra loro e si possono fermare a qualsiasi punto.

## La voce nel menu

**🏃 Attività**, decisa con l'utente. Scartate "Camminata" (non copre le corse), "Camminata e corsa" (lascia fuori i passi, ed è lunga per la barra) e soprattutto **"Cardio"**, che nel piano [cardio.md](cardio.md) indica il tapis *dentro* la seduta: due voci che sembrano la stessa cosa sarebbero state una trappola.

Posizione: nel gruppo del monitoraggio quotidiano, fra **Misurazioni, Integratori, Alimentazione e Sonno** — non fra gli allenamenti, coerentemente col fatto che un'uscita non conta come seduta.

## Domanda ancora aperta

- **Se un domani le uscite debbano contare nella heatmap della home.** Deciso di no per ora, ed è reversibile senza costi né migrazioni.

## Avvertenze

- Porta **tre modelli nuovi più un campo su `UserProfile`**: una migrazione, `migrate` obbligatorio anche su PythonAnywhere.
- Non tocca `WorkoutSession`, `WorkoutSet` né la dashboard: è il lavoro più isolato fra quelli in programma, e il meno rischioso.
