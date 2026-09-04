/* Heatmap annuale in stile "contribution graph", condivisa da tutte le pagine
   che ne mostrano una (dashboard, profilo atleta, acqua, integratori).
   Una colonna per settimana e una riga per giorno con lunedi' in alto, nomi
   dei mesi allineati alla settimana in cui il mese inizia, etichette
   Lun/Mer/Ven a sinistra e legenda opzionale.

   Ogni pagina passa solo la propria semantica:
     TracerHeatmap.build({
       container: 'year-heatmap',      // id o elemento
       year: 2026,
       colorFor: function (dateStr) { ... },   // colore della cella
       labelFor: function (dateStr, giorno, meseBreve) { ... },  // tooltip
       legend: [c0, c1, c2, c3, c4]   // opzionale, da "Meno" a "Piu'"
     });
*/
window.TracerHeatmap = (function () {
    var MONTHS_SHORT = ['gen', 'feb', 'mar', 'apr', 'mag', 'giu', 'lug', 'ago', 'set', 'ott', 'nov', 'dic'];
    var DAY_LABELS = ['Lun', '', 'Mer', '', 'Ven', '', ''];
    var GAP = 3;
    var LABEL_COL = 30;
    // Anello sul giorno corrente. E' un box-shadow inset e non un border
    // perche' cosi' non occupa spazio: la cella resta della stessa dimensione
    // e la griglia non si sposta di un pixel. Bianco e non accento, se no
    // sparirebbe sulle celle dei livelli alti, che sono gia' accento pieno.
    var TODAY_RING = 'rgba(255,255,255,.92)';

    // Data locale del browser nello stesso formato con cui sono costruite le
    // celle, cosi' il confronto e' fra stringhe omogenee.
    function todayKey() {
        var now = new Date();
        return now.getFullYear() + '-' + pad(now.getMonth() + 1) + '-' + pad(now.getDate());
    }

    function accentRgb() {
        return (getComputedStyle(document.documentElement).getPropertyValue('--acc-rgb').trim() || '124, 108, 246');
    }

    function pad(n) {
        return String(n).padStart(2, '0');
    }

    // Tooltip unico agganciato al <body> con position:fixed: come figlio della
    // cella verrebbe tagliato dal contenitore, che ha overflow-x:auto per lo
    // scroll orizzontale (e la spec CSS forza "auto" anche sull'asse verticale).
    function attachTooltip(container) {
        if (container.dataset.hmTipReady) return;
        container.dataset.hmTipReady = '1';

        var tip = document.createElement('div');
        tip.style.cssText = 'position:fixed;display:none;background:var(--panel,#1b2d34);color:#fff;font-size:11px;font-weight:600;padding:5px 8px;border-radius:6px;white-space:nowrap;pointer-events:none;z-index:10000;box-shadow:0 6px 16px rgba(0,0,0,.4);border:1px solid rgba(255,255,255,.08);';
        document.body.appendChild(tip);

        container.addEventListener('mouseover', function (e) {
            var cell = e.target.closest('[data-hmcell]');
            if (!cell || !cell.dataset.hmlabel) return;
            tip.textContent = cell.dataset.hmlabel;
            tip.style.display = 'block';
            var r = cell.getBoundingClientRect();
            var t = tip.getBoundingClientRect();
            // Sopra la cella e centrata; se non ci sta (prime righe) scende
            // sotto, restando comunque dentro i bordi della finestra.
            var left = Math.min(Math.max(4, r.left + r.width / 2 - t.width / 2), window.innerWidth - t.width - 4);
            var top = r.top - t.height - 6;
            if (top < 4) top = r.bottom + 6;
            tip.style.left = left + 'px';
            tip.style.top = top + 'px';
        });
        container.addEventListener('mouseout', function (e) {
            if (e.target.closest('[data-hmcell]')) tip.style.display = 'none';
        });
        var scroller = container.closest('.heatmap-scroll-wrap');
        if (scroller) {
            scroller.addEventListener('scroll', function () { tip.style.display = 'none'; });
        }
    }

    function build(opts) {
        var container = typeof opts.container === 'string'
            ? document.getElementById(opts.container)
            : opts.container;
        if (!container) return;

        var year = opts.year;
        container.innerHTML = '';
        container.style.display = 'flex';
        container.style.flexDirection = 'column';
        container.style.gap = '6px';

        // Parte dal lunedi' della settimana che contiene il 1 gennaio, cosi'
        // ogni colonna e' una settimana intera anche a cavallo d'anno.
        var start = new Date(year, 0, 1);
        start.setDate(start.getDate() - ((start.getDay() + 6) % 7));
        var end = new Date(year, 11, 31);
        // Contate iterando (e non dividendo i millisecondi) per non sbagliare
        // di una colonna nelle settimane con cambio d'ora.
        var weeks = 0;
        for (var probe = new Date(start); probe <= end; probe.setDate(probe.getDate() + 7)) weeks++;

        var colsCss = 'grid-template-columns:repeat(' + weeks + ',minmax(0,1fr));gap:' + GAP + 'px;';

        // Riga dei mesi
        var months = document.createElement('div');
        months.style.cssText = 'display:grid;' + colsCss + 'margin-left:' + (LABEL_COL + GAP * 2) + 'px;';
        var seenMonth = {};
        var cursor = new Date(start);
        for (var w = 0; w < weeks; w++) {
            // Il mese "possiede" la colonna se una delle sue prime 7 date cade
            // in questa settimana: evita etichette a meta' mese.
            for (var d = 0; d < 7; d++) {
                var day = new Date(cursor);
                day.setDate(day.getDate() + d);
                if (day.getFullYear() === year && day.getDate() <= 7 && !seenMonth[day.getMonth()]) {
                    seenMonth[day.getMonth()] = true;
                    var ml = document.createElement('div');
                    ml.style.cssText = 'grid-row:1;grid-column:' + (w + 1) + ';font-size:11px;font-weight:600;color:#a7abc0;white-space:nowrap;';
                    ml.textContent = MONTHS_SHORT[day.getMonth()];
                    months.appendChild(ml);
                    break;
                }
            }
            cursor.setDate(cursor.getDate() + 7);
        }
        container.appendChild(months);

        // Etichette giorni + griglia
        var body = document.createElement('div');
        body.style.cssText = 'display:flex;gap:' + (GAP * 2) + 'px;align-items:stretch;';

        var dayLabels = document.createElement('div');
        dayLabels.style.cssText = 'display:grid;grid-template-rows:repeat(7,1fr);gap:' + GAP + 'px;width:' + LABEL_COL + 'px;flex-shrink:0;';
        DAY_LABELS.forEach(function (txt) {
            var el = document.createElement('div');
            el.style.cssText = 'display:flex;align-items:center;font-size:10.5px;font-weight:600;color:#a7abc0;line-height:1;';
            el.textContent = txt;
            dayLabels.appendChild(el);
        });
        body.appendChild(dayLabels);

        var grid = document.createElement('div');
        grid.style.cssText = 'display:grid;' + colsCss + 'grid-template-rows:repeat(7,1fr);grid-auto-flow:column;flex:1;min-width:0;';

        var oggi = todayKey();
        var day2 = new Date(start);
        for (var i = 0; i < weeks * 7; i++) {
            var cell = document.createElement('div');
            cell.style.cssText = 'width:100%;aspect-ratio:1;border-radius:3px;';
            if (day2.getFullYear() === year) {
                var dateStr = year + '-' + pad(day2.getMonth() + 1) + '-' + pad(day2.getDate());
                cell.style.background = opts.colorFor(dateStr);
                cell.setAttribute('data-hmcell', '1');
                cell.dataset.hmlabel = opts.labelFor(dateStr, day2.getDate(), MONTHS_SHORT[day2.getMonth()]);
                if (dateStr === oggi) cell.style.boxShadow = 'inset 0 0 0 1.5px ' + TODAY_RING;
            } else {
                cell.style.background = 'transparent';
            }
            grid.appendChild(cell);
            day2.setDate(day2.getDate() + 1);
        }
        body.appendChild(grid);
        container.appendChild(body);

        if (opts.legend && opts.legend.length) {
            container.appendChild(makeLegend(opts.legend, 'flex-end'));
        }

        attachTooltip(container);
    }

    function makeLegend(colors, align) {
        var legend = document.createElement('div');
        legend.style.cssText = 'display:flex;align-items:center;justify-content:' + align +
            ';gap:4px;font-size:10.5px;font-weight:600;color:#a7abc0;margin-top:2px;';
        var less = document.createElement('span');
        less.textContent = 'Meno';
        legend.appendChild(less);
        colors.forEach(function (color) {
            var sq = document.createElement('span');
            sq.style.cssText = 'width:11px;height:11px;border-radius:3px;background:' + color + ';';
            legend.appendChild(sq);
        });
        var more = document.createElement('span');
        more.textContent = 'Più';
        legend.appendChild(more);
        return legend;
    }

    /* Versione a mese singolo, usata su mobile dove la griglia annuale non ci
       sta. Stessi colorFor/labelFor della annuale, cosi' le due viste dicono
       la stessa cosa. Sostituisce il calendario SVG di CalHeatMap, che
       disegnava celle minuscole di dimensione fissa e ignorava la larghezza
       dello schermo.

         TracerHeatmap.buildMonth({
           container: 'mobile-cal-heatmap',
           year: 2026, month: 8,          // month: 0 = gennaio
           colorFor: ..., labelFor: ..., legend: [...]
         });
    */
    function buildMonth(opts) {
        var container = typeof opts.container === 'string'
            ? document.getElementById(opts.container)
            : opts.container;
        if (!container) return;

        var year = opts.year;
        var month = opts.month;
        container.innerHTML = '';
        container.style.cssText = 'display:flex;flex-direction:column;gap:10px;width:100%;';

        var grid = document.createElement('div');
        grid.style.cssText = 'display:grid;grid-template-columns:repeat(7,minmax(0,1fr));gap:6px;';

        // Celle vuote iniziali per far cadere il 1 del mese nel suo giorno
        // della settimana, con lunedi' in prima colonna.
        var first = new Date(year, month, 1);
        var lead = (first.getDay() + 6) % 7;
        for (var i = 0; i < lead; i++) {
            var vuota = document.createElement('div');
            vuota.style.cssText = 'aspect-ratio:1;';
            grid.appendChild(vuota);
        }

        var oggi = todayKey();
        var giorni = new Date(year, month + 1, 0).getDate();
        for (var d = 1; d <= giorni; d++) {
            var dateStr = year + '-' + pad(month + 1) + '-' + pad(d);
            var cell = document.createElement('div');
            cell.style.cssText = 'aspect-ratio:1;border-radius:7px;background:' + opts.colorFor(dateStr) + ';';
            cell.setAttribute('data-hmcell', '1');
            cell.dataset.hmlabel = opts.labelFor(dateStr, d, MONTHS_SHORT[month]);
            if (dateStr === oggi) cell.style.boxShadow = 'inset 0 0 0 2px ' + TODAY_RING;
            grid.appendChild(cell);
        }
        container.appendChild(grid);

        if (opts.legend && opts.legend.length) {
            container.appendChild(makeLegend(opts.legend, 'center'));
        }

        attachTooltip(container);
    }

    return { build: build, buildMonth: buildMonth, accentRgb: accentRgb, MONTHS_SHORT: MONTHS_SHORT };
})();
