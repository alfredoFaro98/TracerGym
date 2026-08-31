# App nativa Android per TracerGym — Fase 1 (fondamenta)

> Stato: pianificato, non ancora iniziato. Ripreso in un secondo momento, dopo aver sistemato la responsività del sito web.

## Contesto

TracerGym oggi è un'unica app Django che renderizza HTML lato server: ogni pagina (dashboard, sessioni, acqua, macro, sonno, ecc.) è un template con logica di business dentro `tracker/views.py`. Non esiste nessuna API JSON generale — solo qualche endpoint AJAX puntuale (`exercise_suggestions`, `week_training_data`, ecc.) usato da JS interno alle pagine stesse.

L'utente vuole un'app nativa Android (scelta React Native + Expo, niente Mac per ora). Un'app nativa non può leggere l'HTML renderizzato: serve un'API JSON con autenticazione a token, e un progetto mobile separato che la consuma. Costruire subito la copertura API completa per tutte le ~15 funzionalità (sessioni/circuiti, acqua, macro, integratori, misurazioni, sonno, catalogo esercizi, atleti...) sarebbe un lavoro di settimane prima di vedere un solo schermo funzionante sul telefono.

Questa Fase 1 costruisce uno **scheletro end-to-end verticale**: login + dashboard + storico sessioni (sola lettura) funzionanti davvero tra Django e un'app Expo sul telefono Android dell'utente, tramite Expo Go (nessuna build/pubblicazione ancora richiesta). Una volta provato che la pipeline intera regge, le fasi successive aggiungono acqua/macro/sonno/nuovo allenamento ecc. ripetendo lo stesso pattern.

**Fuori scope per questa fase** (rimandato a iterazioni successive): scrittura/log di nuovi allenamenti dall'app, acqua/macro/integratori/misurazioni/sonno, catalogo esercizi, profili atleti, notifiche push, funzionamento offline, build/pubblicazione su Play Store.

## Decisioni prese con l'utente

- Stack: **React Native con Expo** (JS/TS, testabile su Android reale via app Expo Go senza build né Mac).
- Piattaforma: **solo Android** per ora.
- Auth: **DRF TokenAuthentication** (token semplice senza scadenza) invece di JWT — più semplice da implementare e sufficiente per un'app a uso personale; si potrà passare a refresh-token/JWT più avanti se servirà scadenza.
- Monorepo: il progetto Expo vive in una cartella `mobile/` dentro lo stesso repository, accanto a `tracker/`.

## Backend — nuovo strato API (Django REST Framework)

1. **Dipendenza**: aggiungere `djangorestframework` a `requirements.txt` e a `INSTALLED_APPS` in `core/settings.py`, insieme a `rest_framework.authtoken` (per il token model — niente da scrivere a mano, arriva con una migrazione automatica di DRF).
2. **Config DRF** in `core/settings.py`: `REST_FRAMEWORK = {'DEFAULT_AUTHENTICATION_CLASSES': [TokenAuthentication, SessionAuthentication], 'DEFAULT_PERMISSION_CLASSES': [IsAuthenticated]}` — `SessionAuthentication` resta per poter navigare la "browsable API" di DRF dal browser durante lo sviluppo.
3. **Nuovo package `tracker/api/`** (separato da `views.py` per non mescolare contratti JSON e template HTML):
   - `serializers.py` — serializer per `WorkoutSession` (riusa la stessa forma di `_export_session_dict`/`_build_session_context`, già in `views.py:944-984` e `views.py:536-564`, come riferimento per i campi da esporre: sets normali + circuiti con i loro round), `WorkoutSet`, `Exercise`/`ExerciseImage` (con URL immagine reso assoluto via `request.build_absolute_uri()`, dato che oggi `ImageField.url` è relativo — vedi `core/settings.py:166-175` per `MEDIA_URL`).
   - `views.py` — `APIView`/`generics` per:
     - `POST /api/auth/login/` — riusa `authenticate()` + restituisce/crea il token (pattern equivalente a `TracerLoginView`, `views.py:59-74`, ma senza sessione/redirect).
     - `GET /api/dashboard/` — stessi numeri della dashboard web: acqua di oggi, macro di oggi, streak settimanale (riusa `_week_streak`, `views.py:1385-1400`), totale sessioni, `real_sets_count` (già su `WorkoutSession`, `models.py`), ultime N sessioni.
     - `GET /api/sessions/` — lista paginata (usa `PageNumberPagination` di DRF, stesso `Paginator` concettuale già usato in `dashboard`, `views.py:104-135`).
     - `GET /api/sessions/<id>/` — dettaglio con sets e circuiti, riusando la logica di `_build_session_context` (`views.py:536-564`) adattata a JSON invece che a contesto per template.
   - `urls.py` — monta i path sopra; incluso da `core/urls.py` con `path('api/', include('tracker.api.urls'))`.
4. **Niente CORS**: un'app nativa non è un browser, non è soggetta a CORS — non serve `django-cors-headers` per questa fase (lo si aggiungerebbe solo se in futuro un frontend web separato dovesse chiamare l'API da un altro dominio).
5. **Migrazione**: solo quella automatica di `rest_framework.authtoken` (tabella token, nessun modello nostro da toccare).

## Mobile — progetto Expo

1. `npx create-expo-app@latest mobile --template` (template TypeScript, default attuale di Expo) dentro la root del repo.
2. Struttura minima:
   - `mobile/src/api/client.ts` — wrapper fetch con base URL configurabile (IP locale per test via Expo Go sulla stessa rete Wi-Fi, dominio PythonAnywhere per test "prod") e header `Authorization: Token <...>`.
   - `mobile/src/screens/LoginScreen.tsx` — form utente/password, chiama `/api/auth/login/`, salva il token con `expo-secure-store`.
   - `mobile/src/screens/DashboardScreen.tsx` — chiama `/api/dashboard/`, mostra le stesse card della dashboard web (serie totali, streak, acqua/macro di oggi).
   - `mobile/src/screens/SessionsListScreen.tsx` + `SessionDetailScreen.tsx` — sola lettura per ora.
   - Navigazione: `@react-navigation/native` (stack semplice: Login → Tab con Dashboard/Storico).
3. **Palette**: riuso dei colori già consolidati nel web (`#7c6cf6` viola accento, sfondo `#0d0d14`/`#0d0d1a`, testo `#f0f0f3`) così l'app sembra "Tracer" fin da subito invece di un template generico.

## Verifica end-to-end

1. `python manage.py check` dopo le modifiche backend.
2. Avvio server dev (`python manage.py runserver`) e verifica via script Python (`requests`, stesso approccio già usato con un utente di prova temporaneo, creato e poi rimosso) del ciclo completo: login → token → `GET /api/dashboard/` → `GET /api/sessions/` → `GET /api/sessions/<id>/`, controllando che le cifre coincidano con quelle della dashboard web per lo stesso utente.
3. Lato mobile non è possibile testare su un telefono reale da qui: va verificato solo che il progetto Expo si avvii (`npx expo start`) senza errori e che passi il type-check (`tsc --noEmit`), ma la verifica visiva finale sull'app (schermata di login, dashboard) va fatta scansionando il QR code con Expo Go su un Android, sulla stessa rete Wi-Fi del PC.
