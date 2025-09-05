-- Enum per tipo utente
-- Definito per distinguere in modo chiaro se l'utente è una compagnia o un passeggero
CREATE TYPE tipo_utente AS ENUM (
    'compagnia',
    'passeggero'
);

-- Enum per classe volo
-- Definito per distinguere in modo chiaro se il volo è in classe economy, business o first
CREATE TYPE classe_volo AS ENUM (
    'economy',
    'business',  
    'first'
);

-- Enum per stato prenotazione
-- Definito per distinguere in modo chiaro se la prenotazione è confermata o cancellata
CREATE TYPE stato_prenotazione AS ENUM (
    'confermata',
    'cancellata'
);