-- ==================================================
-- CREAZIONE DATABASE FLYGHT_BOOKING
-- ==================================================

-- Crea il database se non esiste
CREATE DATABASE flyght_booking 
    WITH 
    OWNER = postgres 
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.UTF-8'
    LC_CTYPE = 'en_US.UTF-8'
    TABLESPACE = pg_default
    CONNECTION LIMIT = -1;

-- Commenta sul database
COMMENT ON DATABASE flyght_booking 
    IS 'Database per sistema di prenotazione voli BD Airline - voli singoli only';

-- Connettiti al database
\c flyght_booking;

-- Crea extension per UUID se necessario (futuro)
-- CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
