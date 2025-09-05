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