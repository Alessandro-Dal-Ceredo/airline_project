-- Utilizzato per MySQL
CREATE DATABASE IF NOT EXISTS bd_airline;

USE bd_airline;

--TABELLA UTENTE (tabella principale per autenticazione)
CREATE TABLE utente (
    id SERIAL PRIMARY KEY, -- Auto incrementa l'ID
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(200) NOT NULL, 
    email VARCHAR(100) UNIQUE NOT NULL,
    tipo tipo_utente NOT NULL,
    -- Ho inserito without time zone per evitare problemi di conversioni
    createdat TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- TABELLA COMPAGNIA_AEREA (estensione per utenti compagnia)
CREATE TABLE compagnia_aerea (
    -- Cascade per eliminare la compagnia se l'utente viene eliminato
    id INTEGER PRIMARY KEY REFERENCES utente(id) ON DELETE CASCADE,
    nome_compagnia VARCHAR(100) UNIQUE NOT NULL
);

-- TABELLA PASSEGGERO (estensione per utenti passeggero)
CREATE TABLE passeggero (
    id INTEGER PRIMARY KEY REFERENCES utente(id) ON DELETE CASCADE,
    nome VARCHAR(50) NOT NULL,
    cognome VARCHAR(50) NOT NULL
);

-- TABELLA AEROPORTO
CREATE TABLE aeroporto (
    codice CHAR(3) PRIMARY KEY, -- usa i codici IATA (es. VCE)
    citta VARCHAR(100) NOT NULL,
    paese VARCHAR(100) NOT NULL
);

-- TABELLA TRATTA
CREATE TABLE tratta (
    id SERIAL PRIMARY KEY, -- Auto incrementa l'ID
    -- On update cascade per aggiornare la tratta se l'aeroporto viene modificato
    aeroporto_partenza CHAR(3) NOT NULL REFERENCES aeroporto(codice) ON UPDATE CASCADE,
    aeroporto_arrivo CHAR(3) NOT NULL REFERENCES aeroporto(codice) ON UPDATE CASCADE,
    -- Impedisce la cancellazione della compagnia se ci sono tratte associate
    compagnia_id INTEGER NOT NULL REFERENCES compagnia_aerea(id) ON DELETE RESTRICT,
    
    -- Impedisce la partenza e l'arrivo dello stesso aeroporto
    CONSTRAINT tratta_check CHECK (aeroporto_partenza <> aeroporto_arrivo)
);

-- TABELLA AEREO
CREATE TABLE aereo (
    id SERIAL PRIMARY KEY,
    modello VARCHAR(100) NOT NULL,
    posti_totali INTEGER NOT NULL,
    -- Default 0 per evitare valori negativi
    posti_economy INTEGER NOT NULL DEFAULT 0,
    posti_business INTEGER NOT NULL DEFAULT 0,
    posti_first INTEGER NOT NULL DEFAULT 0,
    -- Impedisce la cancellazione della compagnia se ci sono aerei associate
    compagnia_id INTEGER NOT NULL REFERENCES compagnia_aerea(id) ON DELETE RESTRICT,
    
    -- Impedisce valori negativi e che il numero di posti sia uguale al numero di posti totali
    CONSTRAINT aereo_posti_totali_check CHECK (posti_totali > 0),
    CONSTRAINT aereo_check CHECK (posti_economy >= 0 AND posti_business >= 0 AND posti_first >= 0),
    CONSTRAINT aereo_check1 CHECK (posti_economy + posti_business + posti_first = posti_totali)
);

-- TABELLA EXTRA
CREATE TABLE extra (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) UNIQUE NOT NULL, -- Ogni extra è definito una volta.
    prezzo NUMERIC(10,2) NOT NULL, -- formato decimale con 2 decimali

    -- Impedisce valori negativi
    CONSTRAINT extra_prezzo_check CHECK (prezzo >= 0::numeric)
);

-- TABELLA VOLO
CREATE TABLE volo (
    id SERIAL PRIMARY KEY,
    -- Impedisce la cancellazione della tratta se ci sono voli associate
    tratta_id INTEGER NOT NULL REFERENCES tratta(id) ON DELETE RESTRICT,
    -- Impedisce la cancellazione dell'aereo se ci sono voli associate
    aereo_id INTEGER NOT NULL REFERENCES aereo(id) ON DELETE RESTRICT,
    -- Without time zone per evitare problemi di conversioni
    partenza TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    arrivo TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    posti_disponibili INTEGER NOT NULL DEFAULT 0,

    -- Impedisce che la partenza sia successiva all'arrivo
    CONSTRAINT volo_check CHECK (partenza < arrivo)
);

-- TABELLA PREZZO_VOLO
CREATE TABLE prezzo_volo (
    -- Se un voilo viene cancellato, vengono cancellati anche i prezzi
    volo_id INTEGER NOT NULL REFERENCES volo(id) ON DELETE CASCADE,
    classe classe_volo NOT NULL,
    prezzo NUMERIC(10,2) NOT NULL,

    -- Chiave primaria composta
    PRIMARY KEY (volo_id, classe),

    -- Impedisce valori negativi
    CONSTRAINT prezzo_volo_prezzo_check CHECK (prezzo >= 0::numeric)
);

-- TABELLA PRENOTAZIONE
CREATE TABLE prenotazione (
    id SERIAL PRIMARY KEY,
    -- Se un passeggero viene eliminato, vengono cancellate tutte le prenotazioni
    passeggero_id INTEGER NOT NULL REFERENCES passeggero(id) ON DELETE CASCADE,

    data_acquisto TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    costo_totale NUMERIC(10,2) NOT NULL,
    stato stato_prenotazione NOT NULL DEFAULT 'confermata',

    -- Impedisce valori negativi
    CONSTRAINT prenotazione_costo_totale_check CHECK (costo_totale >= 0::numeric)
);

-- TABELLA BIGLIETTO
CREATE TABLE biglietto (
    id SERIAL PRIMARY KEY,
    -- Se una prenotazione viene eliminata, vengono cancellati tutti i biglietti
    prenotazione_id INTEGER NOT NULL REFERENCES prenotazione(id) ON DELETE CASCADE,
    -- Impedisce la cancellazione del volo se ci sono biglietti associate
    volo_id INTEGER NOT NULL REFERENCES volo(id) ON DELETE RESTRICT,
    classe classe_volo NOT NULL,
    posto VARCHAR(10) NOT NULL,

    -- Impedisce che il posto non sia nel formato 01A, 10B, etc.
    CONSTRAINT biglietto_posto_check CHECK (posto ~ '^[0-9]{1,2}[A-Z]$'),

    -- Chiave primaria composta e un posto non può essere associato a più di un biglietto
    CONSTRAINT biglietto_volo_id_posto_key UNIQUE (volo_id, posto)
);

-- TABELLA BIGLIETTOEXTRA (associazione biglietti-extra)
CREATE TABLE bigliettoextra (
    -- Se un biglietto viene eliminato, vengono cancellati tutti gli extra
    biglietto_id INTEGER NOT NULL REFERENCES biglietto(id) ON DELETE CASCADE,
    -- Impedisce la cancellazione dell'extra se ci sono biglietti associati all'extra
    extra_id INTEGER NOT NULL REFERENCES extra(id) ON DELETE RESTRICT,

    -- Chiave primaria composta
    PRIMARY KEY (biglietto_id, extra_id)
);