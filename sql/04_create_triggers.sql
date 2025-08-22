-- ==================================================
-- CREAZIONE TRIGGER E FUNZIONI
-- ==================================================

-- Connettiti al database flyght_booking
\c flyght_booking;

-- ==================================================
-- TRIGGER PER AGGIORNAMENTO POSTI DISPONIBILI
-- ==================================================

-- Funzione per ricalcolare i posti disponibili di un volo
CREATE OR REPLACE FUNCTION update_posti_disponibili()
RETURNS TRIGGER AS $$
BEGIN
    -- Aggiorna posti disponibili per il volo coinvolto
    UPDATE volo SET posti_disponibili = (
        SELECT a.posti_totali - COALESCE(
            (SELECT COUNT(*) 
             FROM biglietto b 
             JOIN prenotazione p ON b.prenotazione_id = p.id 
             WHERE b.volo_id = volo.id AND p.stato = 'confermata'), 0)
        FROM aereo a 
        WHERE a.id = volo.aereo_id
    )
    WHERE volo.id = COALESCE(NEW.volo_id, OLD.volo_id);
    
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- Trigger per aggiornare posti quando si inserisce un biglietto
CREATE TRIGGER trigger_biglietto_insert
    AFTER INSERT ON biglietto
    FOR EACH ROW
    EXECUTE FUNCTION update_posti_disponibili();

-- Trigger per aggiornare posti quando si cancella un biglietto
CREATE TRIGGER trigger_biglietto_delete
    AFTER DELETE ON biglietto
    FOR EACH ROW
    EXECUTE FUNCTION update_posti_disponibili();

-- Trigger per aggiornare posti quando cambia lo stato prenotazione
CREATE OR REPLACE FUNCTION update_posti_on_prenotazione_change()
RETURNS TRIGGER AS $$
BEGIN
    -- Se lo stato è cambiato, aggiorna posti per tutti i voli della prenotazione
    IF OLD.stato != NEW.stato THEN
        UPDATE volo SET posti_disponibili = (
            SELECT a.posti_totali - COALESCE(
                (SELECT COUNT(*) 
                 FROM biglietto b 
                 JOIN prenotazione p ON b.prenotazione_id = p.id 
                 WHERE b.volo_id = volo.id AND p.stato = 'confermata'), 0)
            FROM aereo a 
            WHERE a.id = volo.aereo_id
        )
        WHERE volo.id IN (
            SELECT b.volo_id FROM biglietto b WHERE b.prenotazione_id = NEW.id
        );
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_prenotazione_stato_change
    AFTER UPDATE ON prenotazione
    FOR EACH ROW
    EXECUTE FUNCTION update_posti_on_prenotazione_change();

-- ==================================================
-- TRIGGER PER INIZIALIZZAZIONE POSTI DISPONIBILI
-- ==================================================

-- Funzione per inizializzare posti disponibili quando si crea un volo
CREATE OR REPLACE FUNCTION init_posti_disponibili()
RETURNS TRIGGER AS $$
BEGIN
    -- Imposta posti_disponibili = posti_totali dell'aereo se non specificato
    IF NEW.posti_disponibili = 0 OR NEW.posti_disponibili IS NULL THEN
        SELECT posti_totali INTO NEW.posti_disponibili
        FROM aereo 
        WHERE id = NEW.aereo_id;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_volo_init_posti
    BEFORE INSERT ON volo
    FOR EACH ROW
    EXECUTE FUNCTION init_posti_disponibili();

-- ==================================================
-- TRIGGER PER VALIDAZIONE BUSINESS LOGIC
-- ==================================================

-- Funzione per validare che un passeggero non prenoti lo stesso volo più volte
CREATE OR REPLACE FUNCTION validate_no_duplicate_booking()
RETURNS TRIGGER AS $$
BEGIN
    -- Controlla se il passeggero ha già un biglietto confermato per questo volo
    IF EXISTS (
        SELECT 1 
        FROM biglietto b 
        JOIN prenotazione p ON b.prenotazione_id = p.id 
        WHERE p.passeggero_id = (
            SELECT passeggero_id FROM prenotazione WHERE id = NEW.prenotazione_id
        )
        AND b.volo_id = NEW.volo_id 
        AND p.stato = 'confermata'
        AND b.id != COALESCE(NEW.id, 0)
    ) THEN
        RAISE EXCEPTION 'Il passeggero ha già prenotato questo volo';
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_validate_duplicate_booking
    BEFORE INSERT OR UPDATE ON biglietto
    FOR EACH ROW
    EXECUTE FUNCTION validate_no_duplicate_booking();

-- ==================================================
-- TRIGGER PER VALIDAZIONE CLASSE-AEREO
-- ==================================================

-- Funzione per validare che la classe del biglietto sia disponibile sull'aereo
CREATE OR REPLACE FUNCTION validate_classe_disponibile()
RETURNS TRIGGER AS $$
DECLARE
    posti_classe INTEGER;
BEGIN
    -- Ottieni il numero di posti per la classe specifica dell'aereo
    SELECT 
        CASE NEW.classe
            WHEN 'economy' THEN a.posti_economy
            WHEN 'business' THEN a.posti_business  
            WHEN 'first' THEN a.posti_first
            ELSE 0
        END INTO posti_classe
    FROM volo v
    JOIN aereo a ON v.aereo_id = a.id
    WHERE v.id = NEW.volo_id;
    
    -- Se la classe non ha posti disponibili sull'aereo, solleva errore
    IF posti_classe = 0 THEN
        RAISE EXCEPTION 'La classe % non è disponibile su questo volo', NEW.classe;
    END IF;
    
    -- Verifica che ci siano ancora posti disponibili per questa classe
    DECLARE
        posti_occupati INTEGER;
    BEGIN
        SELECT COUNT(*) INTO posti_occupati
        FROM biglietto b
        JOIN prenotazione p ON b.prenotazione_id = p.id
        WHERE b.volo_id = NEW.volo_id 
        AND b.classe = NEW.classe 
        AND p.stato = 'confermata'
        AND b.id != COALESCE(NEW.id, 0);
        
        IF posti_occupati >= posti_classe THEN
            RAISE EXCEPTION 'Non ci sono più posti disponibili in classe % per questo volo', NEW.classe;
        END IF;
    END;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_validate_classe
    BEFORE INSERT OR UPDATE ON biglietto
    FOR EACH ROW
    EXECUTE FUNCTION validate_classe_disponibile();

-- ==================================================
-- TRIGGER PER AUDIT LOG (OPZIONALE)
-- ==================================================

-- Tabella per audit delle prenotazioni
CREATE TABLE audit_prenotazioni (
    id SERIAL PRIMARY KEY,
    prenotazione_id INTEGER,
    operazione VARCHAR(10) NOT NULL, -- INSERT, UPDATE, DELETE
    stato_vecchio stato_prenotazione,
    stato_nuovo stato_prenotazione,
    timestamp_operazione TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    utente_db VARCHAR(100) DEFAULT CURRENT_USER
);

-- Funzione per audit delle prenotazioni
CREATE OR REPLACE FUNCTION audit_prenotazioni()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO audit_prenotazioni (prenotazione_id, operazione, stato_nuovo)
        VALUES (NEW.id, 'INSERT', NEW.stato);
        RETURN NEW;
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO audit_prenotazioni (prenotazione_id, operazione, stato_vecchio, stato_nuovo)
        VALUES (NEW.id, 'UPDATE', OLD.stato, NEW.stato);
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO audit_prenotazioni (prenotazione_id, operazione, stato_vecchio)
        VALUES (OLD.id, 'DELETE', OLD.stato);
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_audit_prenotazioni
    AFTER INSERT OR UPDATE OR DELETE ON prenotazione
    FOR EACH ROW
    EXECUTE FUNCTION audit_prenotazioni();

-- Commenti sui trigger
COMMENT ON FUNCTION update_posti_disponibili() IS 'Ricalcola automaticamente i posti disponibili quando cambiano i biglietti';
COMMENT ON FUNCTION validate_no_duplicate_booking() IS 'Impedisce a un passeggero di prenotare lo stesso volo più volte';
COMMENT ON FUNCTION validate_classe_disponibile() IS 'Verifica che la classe sia disponibile sull aereo e abbia posti liberi';
COMMENT ON TABLE audit_prenotazioni IS 'Log delle operazioni sulle prenotazioni per audit e debugging';
