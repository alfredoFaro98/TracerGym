/*
 * Sincronizza il token CSRF con il cookie prima di ogni invio.
 *
 * Perche' serve: Django rigenera il segreto CSRF ad ogni login e ad ogni
 * logout (auth.login/auth.logout chiamano rotate_token). Il cookie e' unico
 * per tutto il browser, quindi e' condiviso fra tutte le schede aperte, ma il
 * token stampato da {% csrf_token %} resta "congelato" nell'HTML gia'
 * renderizzato. Risultato: se fai login o logout in una scheda, tutte le altre
 * schede gia' aperte hanno in pagina il token vecchio e al primo POST si
 * beccano un 403 "CSRF verification failed".
 *
 * Qui, un attimo prima che la richiesta parta, andiamo a rileggere il cookie
 * (che e' sempre quello aggiornato) e riscriviamo il token nel form / negli
 * header. Cosi' la richiesta passa il controllo CSRF: se nel frattempo la
 * sessione e' finita l'utente viene mandato al login, invece di sbattere su un
 * 403 senza spiegazioni.
 */
(function () {
    'use strict';

    var COOKIE_NAME = 'csrftoken';
    var HEADER_NAME = 'X-CSRFToken';
    var FIELD_NAME = 'csrfmiddlewaretoken';

    function currentToken() {
        var cookies = document.cookie ? document.cookie.split('; ') : [];
        for (var i = 0; i < cookies.length; i++) {
            var eq = cookies[i].indexOf('=');
            if (eq > -1 && cookies[i].slice(0, eq) === COOKIE_NAME) {
                return decodeURIComponent(cookies[i].slice(eq + 1));
            }
        }
        return null;
    }

    // Riallinea gli <input name="csrfmiddlewaretoken"> di un form al cookie.
    // Se il cookie non c'e' lasciamo stare: meglio il token stampato nell'HTML
    // che nessun token.
    function refreshForm(form) {
        var token = currentToken();
        if (!token || !form || !form.querySelectorAll) return;
        var inputs = form.querySelectorAll('input[name="' + FIELD_NAME + '"]');
        for (var i = 0; i < inputs.length; i++) {
            inputs[i].value = token;
        }
    }

    // Submit normale (click sul bottone, invio da tastiera). Fase di cattura:
    // cosi' giriamo prima dei listener della pagina, che spesso fanno
    // preventDefault() e mandano il form via fetch con new FormData(form) --
    // e a quel punto la FormData legge gia' il token aggiornato.
    document.addEventListener('submit', function (e) {
        refreshForm(e.target);
    }, true);

    // Submit programmatico: form.submit() non fa scattare l'evento 'submit',
    // quindi il listener qui sopra non lo vedrebbe.
    var nativeSubmit = HTMLFormElement.prototype.submit;
    HTMLFormElement.prototype.submit = function () {
        refreshForm(this);
        return nativeSubmit.apply(this, arguments);
    };

    // fetch(): copre sia i POST con FormData sia quelli JSON che si portano
    // dietro l'header X-CSRFToken interpolato da {{ csrf_token }}.
    var nativeFetch = window.fetch;
    if (typeof nativeFetch === 'function') {
        window.fetch = function (input, init) {
            var token = currentToken();
            var method = (init && init.method) || (input && input.method) || 'GET';
            var url = (typeof input === 'string') ? input : (input && input.url) || '';
            var sameOrigin = !/^https?:\/\//i.test(url) || url.indexOf(window.location.origin + '/') === 0;

            if (token && sameOrigin && !/^(GET|HEAD|OPTIONS|TRACE)$/i.test(method)) {
                init = init || {};

                // Django legge prima il campo POST e solo se manca guarda
                // l'header, quindi la FormData va corretta comunque.
                if (init.body instanceof FormData && init.body.has(FIELD_NAME)) {
                    init.body.set(FIELD_NAME, token);
                }

                var headers = new Headers(init.headers || (input && input.headers) || {});
                headers.set(HEADER_NAME, token);
                init.headers = headers;
            }
            return nativeFetch.call(this, input, init);
        };
    }
})();
