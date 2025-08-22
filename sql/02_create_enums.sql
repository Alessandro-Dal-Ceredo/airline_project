-- ==================================================
-- CREAZIONE ENUM TYPES
-- ==================================================

-- Connettiti al database flyght_booking
\c flyght_booking;

-- Enum per tipo utente
CREATE TYPE tipo_utente AS ENUM (
    'compagnia',
    'passeggero'
);

-- Enum per classe volo
CREATE TYPE classe_volo AS ENUM (
    'economy',
    'business',  
    'first'
);

-- Enum per stato prenotazione
CREATE TYPE stato_prenotazione AS ENUM (
    'confermata',
    'cancellata'
);

-- Commenti sugli enum
COMMENT ON TYPE tipo_utente 
    IS 'Tipo di utente: compagnia aerea o passeggero';

COMMENT ON TYPE classe_volo 
    IS 'Classe di servizio del volo: economy, business, first class';

COMMENT ON TYPE stato_prenotazione 
    IS 'Stato della prenotazione: confermata o cancellata';
