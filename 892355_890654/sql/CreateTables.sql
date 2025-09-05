CREATE DATABASE IF NOT EXISTS bd_airline;

USE bd_airline;

--TABELLA UTENTE (tabella principale per autenticazione)
CREATE TABLE utente (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(200) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    tipo tipo_utente NOT NULL,
    createdat TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- TABELLA COMPAGNIA_AEREA (estensione per utenti compagnia)
CREATE TABLE compagnia_aerea (
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
    codice CHAR(3) PRIMARY KEY,
    citta VARCHAR(100) NOT NULL,
    paese VARCHAR(100) NOT NULL
);

-- TABELLA TRATTA
CREATE TABLE tratta (
    id SERIAL PRIMARY KEY,
    aeroporto_partenza CHAR(3) NOT NULL REFERENCES aeroporto(codice) ON UPDATE CASCADE,
    aeroporto_arrivo CHAR(3) NOT NULL REFERENCES aeroporto(codice) ON UPDATE CASCADE,
    compagnia_id INTEGER NOT NULL REFERENCES compagnia_aerea(id) ON DELETE RESTRICT,
    
    CONSTRAINT tratta_check CHECK (aeroporto_partenza <> aeroporto_arrivo)
);

-- TABELLA AEREO
CREATE TABLE aereo (
    id SERIAL PRIMARY KEY,
    modello VARCHAR(100) NOT NULL,
    posti_totali INTEGER NOT NULL,
    posti_economy INTEGER NOT NULL DEFAULT 0,
    posti_business INTEGER NOT NULL DEFAULT 0,
    posti_first INTEGER NOT NULL DEFAULT 0,
    compagnia_id INTEGER NOT NULL REFERENCES compagnia_aerea(id) ON DELETE RESTRICT,
    
    CONSTRAINT aereo_posti_totali_check CHECK (posti_totali > 0),
    CONSTRAINT aereo_check CHECK (posti_economy >= 0 AND posti_business >= 0 AND posti_first >= 0),
    CONSTRAINT aereo_check1 CHECK (posti_economy + posti_business + posti_first = posti_totali)
);

-- TABELLA EXTRA
CREATE TABLE extra (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) UNIQUE NOT NULL,
    prezzo NUMERIC(10,2) NOT NULL,
    
    CONSTRAINT extra_prezzo_check CHECK (prezzo >= 0::numeric)
);

-- TABELLA VOLO
CREATE TABLE volo (
    id SERIAL PRIMARY KEY,
    tratta_id INTEGER NOT NULL REFERENCES tratta(id) ON DELETE RESTRICT,
    aereo_id INTEGER NOT NULL REFERENCES aereo(id) ON DELETE RESTRICT,
    partenza TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    arrivo TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    posti_disponibili INTEGER NOT NULL DEFAULT 0,
    
    CONSTRAINT volo_check CHECK (partenza < arrivo)
);

-- TABELLA PREZZO_VOLO
CREATE TABLE prezzo_volo (
    volo_id INTEGER NOT NULL REFERENCES volo(id) ON DELETE CASCADE,
    classe classe_volo NOT NULL,
    prezzo NUMERIC(10,2) NOT NULL,
    
    PRIMARY KEY (volo_id, classe),
    
    CONSTRAINT prezzo_volo_prezzo_check CHECK (prezzo >= 0::numeric)
);

-- TABELLA PRENOTAZIONE
CREATE TABLE prenotazione (
    id SERIAL PRIMARY KEY,
    passeggero_id INTEGER NOT NULL REFERENCES passeggero(id) ON DELETE CASCADE,
    data_acquisto TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    costo_totale NUMERIC(10,2) NOT NULL,
    stato stato_prenotazione NOT NULL DEFAULT 'confermata',
    
    CONSTRAINT prenotazione_costo_totale_check CHECK (costo_totale >= 0::numeric)
);

-- TABELLA BIGLIETTO
CREATE TABLE biglietto (
    id SERIAL PRIMARY KEY,
    prenotazione_id INTEGER NOT NULL REFERENCES prenotazione(id) ON DELETE CASCADE,
    volo_id INTEGER NOT NULL REFERENCES volo(id) ON DELETE RESTRICT,
    classe classe_volo NOT NULL,
    posto VARCHAR(10) NOT NULL,
    
    CONSTRAINT biglietto_posto_check CHECK (posto ~ '^[0-9]{1,2}[A-Z]$'),
    
    CONSTRAINT biglietto_volo_id_posto_key UNIQUE (volo_id, posto)
);

-- TABELLA BIGLIETTOEXTRA (associazione biglietti-extra)
CREATE TABLE bigliettoextra (
    biglietto_id INTEGER NOT NULL REFERENCES biglietto(id) ON DELETE CASCADE,
    extra_id INTEGER NOT NULL REFERENCES extra(id) ON DELETE RESTRICT,
    
    PRIMARY KEY (biglietto_id, extra_id)
);