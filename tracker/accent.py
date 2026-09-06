"""Deriva l'intera scala dell'accent da un colore solo.

Un accent non e' un colore ma dodici: --acc piu' quattro toni piu' chiari,
--acc-soft per il testo sopra uno sfondo gia' tinto, e i cinque gradini dei
grafici. I cinque preset in style.css sono tarati a mano; qui si ricostruisce
la stessa scala per un colore scelto dall'utente.

La regola e' stata ricavata misurando i preset in HSL, e non e' uniforme:

- `--acc-2/3/4` sono spostamenti relativi, identici in tutti e cinque i preset
  (--acc-4 e' esattamente L+10 ovunque). Seguono il colore scelto.
- `--acc-soft` e i `--chart-*` no: atterrano su luminosita' assolute (soft fra
  76 e 83 in tutti i preset, a prescindere dal colore di partenza). E' la cosa
  giusta, perche' quelli sono testo e tratti su fondo scuro: se seguissero un
  colore gia' scuro diventerebbero illeggibili.

Da qui la scelta di fondo: **i riempimenti seguono il colore scelto, il testo
resta leggibile**. Chi sceglie un marrone spento ottiene bottoni marroni, ma
le scritte sopra restano visibili invece di sparire nel fondo.
"""
import colorsys

# Luminosita' minime per i toni che finiscono su testo e icone. Sono i valori
# piu' bassi che si trovano nei preset tarati a mano: sotto questi, su fondo
# scuro, si comincia a non leggere.
L_MIN = {'acc_3': 58.0, 'acc_4': 60.0, 'acc_5': 72.0}

# --acc-soft e' sempre testo chiaro sopra un fondo tinto: luminosita' fissa e
# saturazione tenuta bassa, altrimenti "vibra" sopra lo sfondo colorato.
SOFT_L = 78.0
SOFT_S_MAX = 66.0

# I cinque gradini dei grafici, dal piu' chiaro al piu' scuro. Distanziati
# abbastanza da restare separabili quando piu' serie stanno sullo stesso
# grafico, e il piu' scuro stacca ancora dal fondo della card.
CHART_L = [72.0, 60.0, 48.0, 38.0, 29.0]
# I gradini scuri con poca saturazione diventano fango: si alza un po', ma
# senza tradire una scelta volutamente spenta (da qui il tetto).
CHART_S_BOOST = [0.0, 0.0, 8.0, 14.0, 18.0]


def _da_hex(colore):
    c = colore.lstrip('#')
    r, g, b = (int(c[i:i + 2], 16) / 255 for i in (0, 2, 4))
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    return h * 360, s * 100, l * 100


def _a_hex(h, s, l):
    # Fuori range i valori non hanno senso e colorsys li accetterebbe lo
    # stesso, restituendo colori a caso: meglio tagliarli qui.
    s = max(0.0, min(100.0, s))
    l = max(0.0, min(100.0, l))
    r, g, b = colorsys.hls_to_rgb((h % 360) / 360, l / 100, s / 100)
    return '#%02x%02x%02x' % (round(r * 255), round(g * 255), round(b * 255))


def normalizza_hex(valore):
    """Riporta un colore scritto a mano in forma '#rrggbb', o None se non lo e'.

    Accetta anche la forma corta (#abc) e senza cancelletto, perche' e' quello
    che si finisce per incollare da un altro programma.
    """
    if not valore:
        return None
    c = valore.strip().lstrip('#').lower()
    if len(c) == 3 and all(ch in '0123456789abcdef' for ch in c):
        c = ''.join(ch * 2 for ch in c)
    if len(c) != 6 or not all(ch in '0123456789abcdef' for ch in c):
        return None
    return '#' + c


def scala_accent(colore):
    """Le dodici variabili CSS dell'accent, derivate da `colore` (#rrggbb).

    Restituisce un dizionario nome-variabile -> valore, gia' pronto da
    stampare dentro un blocco CSS.

    Il colore viene rinormalizzato qui anche se chi chiama l'ha gia' fatto: il
    risultato finisce in un <style> stampato con |safe, quindi questa funzione
    non deve poter restituire nient'altro che colori esadecimali, qualunque
    cosa le arrivi.
    """
    colore = normalizza_hex(colore) or '#7c6cf6'
    h, s, l = _da_hex(colore)

    acc_3 = (h, s + 4.5, max(l + 8.0, L_MIN['acc_3']))
    acc_4 = (h, s + 11.5, max(l + 10.0, L_MIN['acc_4']))
    acc_5 = (h, s + 12.5, max(l + 19.0, L_MIN['acc_5']))

    r, g, b = (int(colore.lstrip('#')[i:i + 2], 16) for i in (0, 2, 4))

    scala = {
        'acc': colore,
        'acc-2': _a_hex(h, s, l + 3.0),
        'acc-3': _a_hex(*acc_3),
        'acc-4': _a_hex(*acc_4),
        'acc-5': _a_hex(*acc_5),
        'acc-soft': _a_hex(h, min(s, SOFT_S_MAX), SOFT_L),
        'acc-rgb': f'{r}, {g}, {b}',
    }
    for i, (chart_l, boost) in enumerate(zip(CHART_L, CHART_S_BOOST), start=1):
        scala[f'chart-{i}'] = _a_hex(h, s + boost, chart_l)
    return scala


def css_accent(colore):
    """Il blocco CSS da infilare in pagina per un accent personalizzato."""
    righe = '\n'.join(f'  --{nome}: {valore};' for nome, valore in scala_accent(colore).items())
    return ':root[data-accent="custom"] {\n' + righe + '\n}'
