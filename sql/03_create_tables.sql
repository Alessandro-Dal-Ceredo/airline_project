-- ==================================================
-- CREAZIONE TABELLE PRINCIPALI
-- ==================================================

-- Connettiti al database flyght_booking
\c flyght_booking;

-- ==================================================
-- TABELLA UTENTE (tabella principale per autenticazione)
-- ==================================================
CREATE TABLE utente (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(200) NOT NULL, -- Spazio per password hashate
    email VARCHAR(100) UNIQUE NOT NULL,
    tipo tipo_utente NOT NULL,
    createdat TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indici per performance
CREATE INDEX idx_utente_username ON utente(username);
CREATE INDEX idx_utente_email ON utente(email);
CREATE INDEX idx_utente_tipo ON utente(tipo);

-- Commenti
COMMENT ON TABLE utente IS 'Tabella principale degli utenti (compagnie e passeggeri)';
COMMENT ON COLUMN utente.password IS 'Password hashata con werkzeug';
COMMENT ON COLUMN utente.tipo IS 'Tipo utente: compagnia o passeggero';

-- ==================================================
-- TABELLA COMPAGNIA_AEREA (estensione per utenti compagnia)
-- ==================================================
CREATE TABLE compagnia_aerea (
    id INTEGER PRIMARY KEY REFERENCES utente(id) ON DELETE CASCADE,
    nome_compagnia VARCHAR(100) UNIQUE NOT NULL
);

-- Indice
CREATE INDEX idx_compagnia_nome ON compagnia_aerea(nome_compagnia);

-- Commenti
COMMENT ON TABLE compagnia_aerea IS 'Estensione per utenti di tipo compagnia aerea';

-- ==================================================
-- TABELLA PASSEGGERO (estensione per utenti passeggero)
-- ==================================================
CREATE TABLE passeggero (
    id INTEGER PRIMARY KEY REFERENCES utente(id) ON DELETE CASCADE,
    nome VARCHAR(50) NOT NULL,
    cognome VARCHAR(50) NOT NULL
);

-- Indice per ricerche
CREATE INDEX idx_passeggero_nome_cognome ON passeggero(cognome, nome);

-- Commenti
COMMENT ON TABLE passeggero IS 'Estensione per utenti di tipo passeggero';

-- ==================================================
-- TABELLA AEROPORTO
-- ==================================================
CREATE TABLE aeroporto (
    codice CHAR(3) PRIMARY KEY, -- Codice IATA (es: FCO, MXP, LHR)
    citta VARCHAR(100) NOT NULL,
    paese VARCHAR(100) NOT NULL
);

-- Indici per ricerche geografiche
CREATE INDEX idx_aeroporto_citta ON aeroporto(citta);
CREATE INDEX idx_aeroporto_paese ON aeroporto(paese);

-- Commenti
COMMENT ON TABLE aeroporto IS 'Aeroporti con codice IATA standard';
COMMENT ON COLUMN aeroporto.codice IS 'Codice IATA a 3 caratteri (es: FCO, MXP, LHR)';

-- ==================================================
-- TABELLA TRATTA
-- ==================================================
CREATE TABLE tratta (
    id SERIAL PRIMARY KEY,
    aeroporto_partenza CHAR(3) NOT NULL REFERENCES aeroporto(codice) ON UPDATE CASCADE,
    aeroporto_arrivo CHAR(3) NOT NULL REFERENCES aeroporto(codice) ON UPDATE CASCADE,
    compagnia_id INTEGER NOT NULL REFERENCES compagnia_aerea(id) ON DELETE RESTRICT,
    
    -- Constraint per evitare tratte con stesso aeroporto
    CONSTRAINT check_different_airports CHECK (aeroporto_partenza <> aeroporto_arrivo)
);

-- Indici per performance nelle ricerche
CREATE INDEX idx_tratta_partenza ON tratta(aeroporto_partenza);
CREATE INDEX idx_tratta_arrivo ON tratta(aeroporto_arrivo);
CREATE INDEX idx_tratta_compagnia ON tratta(compagnia_id);
CREATE INDEX idx_tratta_route ON tratta(aeroporto_partenza, aeroporto_arrivo);

-- Indice univoco per evitare duplicati
CREATE UNIQUE INDEX idx_tratta_unique ON tratta(aeroporto_partenza, aeroporto_arrivo, compagnia_id);

-- Commenti
COMMENT ON TABLE tratta IS 'Tratte servite dalle compagnie aeree';
COMMENT ON CONSTRAINT check_different_airports ON tratta IS 'Assicura che partenza e arrivo siano diversi';

-- ==================================================
-- TABELLA AEREO
-- ==================================================
CREATE TABLE aereo (
    id SERIAL PRIMARY KEY,
    modello VARCHAR(100) NOT NULL,
    posti_totali INTEGER NOT NULL,
    posti_economy INTEGER NOT NULL DEFAULT 0,
    posti_business INTEGER NOT NULL DEFAULT 0,
    posti_first INTEGER NOT NULL DEFAULT 0,
    compagnia_id INTEGER NOT NULL REFERENCES compagnia_aerea(id) ON DELETE RESTRICT,
    
    -- Constraints per validazione posti
    CONSTRAINT check_posti_positivi CHECK (posti_totali > 0),
    CONSTRAINT check_economy_non_neg CHECK (posti_economy >= 0),
    CONSTRAINT check_business_non_neg CHECK (posti_business >= 0),
    CONSTRAINT check_first_non_neg CHECK (posti_first >= 0),
    CONSTRAINT check_sum_posti CHECK (posti_economy + posti_business + posti_first = posti_totali)
);

-- Indici
CREATE INDEX idx_aereo_compagnia ON aereo(compagnia_id);
CREATE INDEX idx_aereo_modello ON aereo(modello);

-- Commenti
COMMENT ON TABLE aereo IS 'Flotta delle compagnie aeree';
COMMENT ON CONSTRAINT check_sum_posti ON aereo IS 'Assicura che la somma dei posti per classe = posti totali';

-- ==================================================
-- TABELLA EXTRA
-- ==================================================
CREATE TABLE extra (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) UNIQUE NOT NULL,
    prezzo NUMERIC(10,2) NOT NULL,
    
    -- Constraint per prezzo non negativo
    CONSTRAINT check_extra_prezzo_non_negativo CHECK (prezzo >= 0)
);

-- Indice
CREATE INDEX idx_extra_nome ON extra(nome);

-- Commenti
COMMENT ON TABLE extra IS 'Servizi extra acquistabili (bagaglio, pasti, wifi, etc.)';

-- ==================================================
-- TABELLA VOLO
-- ==================================================
CREATE TABLE volo (
    id SERIAL PRIMARY KEY,
    tratta_id INTEGER NOT NULL REFERENCES tratta(id) ON DELETE RESTRICT,
    aereo_id INTEGER NOT NULL REFERENCES aereo(id) ON DELETE RESTRICT,
    partenza TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    arrivo TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    posti_disponibili INTEGER NOT NULL DEFAULT 0,
    
    -- Constraint per orari logici
    CONSTRAINT check_orari_logici CHECK (partenza < arrivo)
);

-- Indici per performance
CREATE INDEX idx_volo_partenza ON volo(partenza);
CREATE INDEX idx_volo_arrivo ON volo(arrivo);
CREATE INDEX idx_volo_tratta ON volo(tratta_id);
CREATE INDEX idx_volo_aereo ON volo(aereo_id);
CREATE INDEX idx_volo_posti_disponibili ON volo(posti_disponibili);

-- Indice composto per ricerche comuni
CREATE INDEX idx_volo_search ON volo(tratta_id, partenza) WHERE posti_disponibili > 0;

-- Commenti
COMMENT ON TABLE volo IS 'Voli schedulati dalle compagnie';
COMMENT ON COLUMN volo.posti_disponibili IS 'Posti totali ancora disponibili (calcolato)';
COMMENT ON CONSTRAINT check_orari_logici ON volo IS 'Assicura che la partenza sia prima dell arrivo';

-- ==================================================
-- TABELLA PREZZO_VOLO
-- ==================================================
CREATE TABLE prezzo_volo (
    volo_id INTEGER NOT NULL REFERENCES volo(id) ON DELETE CASCADE,
    classe classe_volo NOT NULL,
    prezzo NUMERIC(10,2) NOT NULL,
    
    PRIMARY KEY (volo_id, classe),
    
    -- Constraint per prezzo non negativo
    CONSTRAINT check_prezzo_non_negativo CHECK (prezzo >= 0)
);

-- Indici
CREATE INDEX idx_prezzo_volo_classe ON prezzo_volo(classe);
CREATE INDEX idx_prezzo_volo_prezzo ON prezzo_volo(prezzo);

-- Commenti
COMMENT ON TABLE prezzo_volo IS 'Prezzi per classe di ogni volo';

-- ==================================================
-- TABELLA PRENOTAZIONE
-- ==================================================
CREATE TABLE prenotazione (
    id SERIAL PRIMARY KEY,
    passeggero_id INTEGER NOT NULL REFERENCES passeggero(id) ON DELETE CASCADE,
    data_acquisto TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    costo_totale NUMERIC(10,2) NOT NULL,
    stato stato_prenotazione NOT NULL DEFAULT 'confermata',
    
    -- Constraint per costo non negativo
    CONSTRAINT check_costo_non_negativo CHECK (costo_totale >= 0)
);

-- Indici per performance
CREATE INDEX idx_prenotazione_passeggero ON prenotazione(passeggero_id);
CREATE INDEX idx_prenotazione_data ON prenotazione(data_acquisto);
CREATE INDEX idx_prenotazione_stato ON prenotazione(stato);

-- Commenti
COMMENT ON TABLE prenotazione IS 'Prenotazioni effettuate dai passeggeri';
COMMENT ON COLUMN prenotazione.costo_totale IS 'Costo totale inclusi voli ed extra';

-- ==================================================
-- TABELLA BIGLIETTO
-- ==================================================
CREATE TABLE biglietto (
    id SERIAL PRIMARY KEY,
    prenotazione_id INTEGER NOT NULL REFERENCES prenotazione(id) ON DELETE CASCADE,
    volo_id INTEGER NOT NULL REFERENCES volo(id) ON DELETE RESTRICT,
    classe classe_volo NOT NULL,
    posto VARCHAR(10) NOT NULL,
    
    -- Constraint per formato posto (es: 12A, 5F)
    CONSTRAINT check_formato_posto CHECK (posto ~ '^[0-9]{1,2}[A-Z]$'),
    
    -- Constraint per unicità posto per volo
    CONSTRAINT unique_posto_per_volo UNIQUE (volo_id, posto)
);

-- Indici
CREATE INDEX idx_biglietto_prenotazione ON biglietto(prenotazione_id);
CREATE INDEX idx_biglietto_volo ON biglietto(volo_id);
CREATE INDEX idx_biglietto_classe ON biglietto(classe);

-- Commenti
COMMENT ON TABLE biglietto IS 'Biglietti individuali per ogni volo prenotato';
COMMENT ON COLUMN biglietto.posto IS 'Numero posto formato: cifra + lettera (es: 12A)';
COMMENT ON CONSTRAINT unique_posto_per_volo ON biglietto IS 'Ogni posto può essere assegnato una sola volta per volo';

-- ==================================================
-- TABELLA BIGLIETTOEXTRA (associazione biglietti-extra)
-- ==================================================
CREATE TABLE bigliettoextra (
    biglietto_id INTEGER NOT NULL REFERENCES biglietto(id) ON DELETE CASCADE,
    extra_id INTEGER NOT NULL REFERENCES extra(id) ON DELETE RESTRICT,
    
    PRIMARY KEY (biglietto_id, extra_id)
);

-- Indici
CREATE INDEX idx_bigliettoextra_biglietto ON bigliettoextra(biglietto_id);
CREATE INDEX idx_bigliettoextra_extra ON bigliettoextra(extra_id);

-- Commenti
COMMENT ON TABLE bigliettoextra IS 'Associazione tra biglietti e servizi extra acquistati';
