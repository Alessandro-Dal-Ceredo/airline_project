# Airline Project

Airline Project è un'applicazione web per la gestione e la prenotazione di voli, sviluppata come progetto universitario per il corso di Basi di Dati CT0006. Il sistema modella utenti, compagnie aeree, passeggeri, aeroporti, tratte, aerei, voli, prezzi, prenotazioni, biglietti ed extra.

L'applicazione è realizzata con Flask e PostgreSQL. La parte applicativa espone pagine web per passeggeri e compagnie, mentre la parte database include script SQL per enum, tabelle, viste, trigger e indici.

## Membri

- Alessandro Dal Ceredo - 892355
- Gabriele D'Amato - 890654

## Funzionalità principali

- Registrazione e login di utenti con ruolo `passeggero` o `compagnia`.
- Ricerca voli per origine, destinazione e data.
- Ricerca di voli diretti e viaggi con uno scalo.
- Ordinamento dei risultati per orario, prezzo o durata.
- Dashboard passeggero con storico prenotazioni e filtro per stato.
- Prenotazione di voli con scelta di classe, posto ed eventuali extra.
- Cancellazione delle prenotazioni consentita solo se mancano più di 24 ore alla partenza.
- Dashboard compagnia con statistiche operative e ricavi.
- Gestione di flotta, tratte e voli da parte delle compagnie.
- Vincoli e trigger database per mantenere coerenza tra utenti, compagnie, aerei, voli e biglietti.

## Stack tecnico

- Backend: Python, Flask
- Autenticazione: Flask-Login
- ORM: Flask-SQLAlchemy / SQLAlchemy
- Migrazioni: Flask-Migrate / Alembic
- Database: PostgreSQL
- Template: Jinja2
- Frontend: HTML, CSS, JavaScript
- Driver database: psycopg2

## Struttura del progetto

```text
.
├── app.py                         # Applicazione Flask, rotte e logica principale
├── models.py                      # Modelli SQLAlchemy e classe ViaggioCombinato
├── config.py                      # Configurazione Flask e PostgreSQL
├── requirements.txt               # Dipendenze Python
├── info.txt                       # Informazioni del progetto
├── templates/                     # Template Jinja2 delle pagine web
├── static/
│   ├── css/                       # Stili dell'interfaccia
│   └── js/                        # Script client-side
├── sql/
│   ├── CreateEnum.sql             # Enum PostgreSQL
│   ├── CreateTables.sql           # Schema relazionale
│   ├── CreateTriggerFunctions.sql # Funzioni trigger e trigger
│   └── CreateViews.sql            # Viste statistiche e indici
└── DocumentazioneVideo/           # PDF e video di documentazione
```

Nel repository è presente anche la cartella `892355_890654/`, che contiene una copia consegnabile del progetto con documentazione e archivio ZIP.

## Modello dati

Le entità principali sono:

- `Utente`: account applicativo, specializzato in compagnia o passeggero.
- `CompagniaAerea`: compagnia proprietaria di aerei, tratte e voli.
- `Passeggero`: utente che può cercare e prenotare voli.
- `Aeroporto`: aeroporto identificato da codice IATA.
- `Tratta`: collegamento tra aeroporto di partenza e arrivo.
- `Aereo`: mezzo della compagnia con posti divisi per classe.
- `Volo`: istanza programmata di una tratta con aereo, partenza, arrivo e posti disponibili.
- `PrezzoVolo`: prezzo per classe su un volo.
- `Prenotazione`: acquisto effettuato da un passeggero.
- `Biglietto`: posto assegnato a un passeggero per un volo.
- `Extra`: servizi aggiuntivi acquistabili.
- `BigliettoExtra`: associazione tra biglietti ed extra.

## Logica database

Gli script SQL includono:

- enum per tipo utente, classe di volo e stato prenotazione;
- vincoli di integrità su orari, posti, prezzi, aeroporti e unicità dei posti;
- trigger per normalizzare i codici IATA in maiuscolo;
- trigger per inizializzare e aggiornare i posti disponibili;
- trigger per controllare la coerenza tra tratta, aereo e compagnia;
- trigger per validare i sottotipi di utente;
- viste statistiche per passeggeri, ricavi dei voli e ricavi aggregati per compagnia;
- indici sulle colonne più usate nelle query applicative.

## Requisiti

- Python 3.10 o superiore
- PostgreSQL
- Ambiente virtuale Python consigliato
- Dipendenze elencate in `requirements.txt`

## Configurazione locale

1. Clonare il repository:

   ```bash
   git clone https://github.com/Alessandro-Dal-Ceredo/airline_project.git
   cd airline_project
   ```

2. Creare e attivare un ambiente virtuale:

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Installare le dipendenze:

   ```bash
   pip install -r requirements.txt
   ```

4. Creare un database PostgreSQL, per esempio:

   ```sql
   CREATE DATABASE flight_booking;
   ```

5. Configurare le variabili d'ambiente usate da `config.py`:

   ```bash
   export POSTGRES_USER=dalce
   export POSTGRES_PASSWORD=
   export POSTGRES_HOST=localhost
   export POSTGRES_PORT=5432
   export POSTGRES_DB=flight_booking
   export SECRET_KEY=dev-secret-key
   ```

6. Inizializzare lo schema database eseguendo gli script nella cartella `sql/` nell'ordine:

   ```text
   CreateEnum.sql
   CreateTables.sql
   CreateTriggerFunctions.sql
   CreateViews.sql
   ```

7. Avviare l'applicazione:

   ```bash
   python app.py
   ```

8. Aprire il browser su:

   ```text
   http://127.0.0.1:5001
   ```

## Flussi utente

### Passeggero

1. Si registra come passeggero.
2. Cerca voli per aeroporto di partenza, aeroporto di arrivo e data.
3. Confronta voli diretti o con scalo.
4. Sceglie classe, posto ed extra.
5. Consulta le prenotazioni dalla dashboard.
6. Può cancellare una prenotazione se il volo non parte entro 24 ore.

### Compagnia

1. Si registra come compagnia.
2. Inserisce aerei con capienza divisa per classe.
3. Crea tratte tra aeroporti.
4. Programma voli indicando tratta, aereo, orari e prezzi.
5. Consulta statistiche, voli recenti e ricavi.
6. Gestisce la cancellazione di aerei, tratte e voli quando non ci sono vincoli attivi.

## Note operative

All'avvio diretto con `python app.py`, l'app esegue `db.create_all()` dentro il contesto Flask. Gli script SQL restano comunque importanti perché definiscono enum, trigger, viste e indici che non sono completamente rappresentati dalla sola creazione ORM.

Il file `.gitignore` esclude ambienti virtuali, cache Python, file IDE, `.env` e `config.py`. Se si lavora in un nuovo checkout, assicurarsi di ricreare o configurare correttamente `config.py` e le variabili d'ambiente necessarie.

## Documentazione

La cartella `DocumentazioneVideo/` contiene materiale di supporto al progetto, tra cui PDF e video dimostrativo.
