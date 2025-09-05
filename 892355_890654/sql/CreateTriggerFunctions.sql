BEGIN;

-- Uppercase automatico per codice IATA
CREATE OR REPLACE FUNCTION fn_uppercase_iata() RETURNS trigger AS $$
BEGIN
  IF NEW.codice IS NOT NULL THEN
    NEW.codice := UPPER(NEW.codice);
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_uppercase_iata_ins ON aeroporto;
CREATE TRIGGER trg_uppercase_iata_ins
BEFORE INSERT ON aeroporto
FOR EACH ROW EXECUTE FUNCTION fn_uppercase_iata();

DROP TRIGGER IF EXISTS trg_uppercase_iata_upd ON aeroporto;
CREATE TRIGGER trg_uppercase_iata_upd
BEFORE UPDATE ON aeroporto
FOR EACH ROW EXECUTE FUNCTION fn_uppercase_iata();


-- Inizializza posti_disponibili con la capienza dell'aereo
CREATE OR REPLACE FUNCTION fn_init_posti_disponibili() RETURNS trigger AS $$
DECLARE tot INT;
BEGIN
  SELECT posti_totali INTO tot FROM aereo WHERE id = NEW.aereo_id;
  IF tot IS NULL THEN
    RAISE EXCEPTION 'AEREO % non trovato', NEW.aereo_id;
  END IF;
  NEW.posti_disponibili := tot;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_init_posti_disponibili ON volo;
CREATE TRIGGER trg_init_posti_disponibili
BEFORE INSERT ON volo
FOR EACH ROW EXECUTE FUNCTION fn_init_posti_disponibili();


-- Coerenza compagnia tra TRATTA e AEREO
CREATE OR REPLACE FUNCTION fn_check_compagnia_match() RETURNS trigger AS $$
DECLARE comp_tratta INT; comp_aereo INT;
BEGIN
  SELECT compagnia_id INTO comp_tratta FROM tratta WHERE id = NEW.tratta_id;
  SELECT compagnia_id INTO comp_aereo  FROM aereo  WHERE id = NEW.aereo_id;
  IF comp_tratta IS NULL OR comp_aereo IS NULL OR comp_tratta <> comp_aereo THEN
    RAISE EXCEPTION 'COMPAGNIA mismatch tra TRATTA % e AEREO %', NEW.tratta_id, NEW.aereo_id;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_check_compagnia_match_ins ON volo;
CREATE TRIGGER trg_check_compagnia_match_ins
BEFORE INSERT ON volo
FOR EACH ROW EXECUTE FUNCTION fn_check_compagnia_match();

DROP TRIGGER IF EXISTS trg_check_compagnia_match_upd ON volo;
CREATE TRIGGER trg_check_compagnia_match_upd
BEFORE UPDATE OF tratta_id, aereo_id ON volo
FOR EACH ROW EXECUTE FUNCTION fn_check_compagnia_match();


-- Sottotipi di UTENTE: controlla tipo all'inserimento in compagnia_aerea/passeggero
CREATE OR REPLACE FUNCTION fn_check_tipo_utente_compagnia() RETURNS trigger AS $$
DECLARE tip tipo_utente;
BEGIN
  SELECT tipo INTO tip FROM utente WHERE id = NEW.id;
  IF tip IS DISTINCT FROM 'compagnia' THEN
    RAISE EXCEPTION 'UTENTE % non è di tipo compagnia', NEW.id;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_check_tipo_compagnia ON compagnia_aerea;
CREATE TRIGGER trg_check_tipo_compagnia
BEFORE INSERT ON compagnia_aerea
FOR EACH ROW EXECUTE FUNCTION fn_check_tipo_utente_compagnia();

CREATE OR REPLACE FUNCTION fn_check_tipo_utente_passeggero() RETURNS trigger AS $$
DECLARE tip tipo_utente;
BEGIN
  SELECT tipo INTO tip FROM utente WHERE id = NEW.id;
  IF tip IS DISTINCT FROM 'passeggero' THEN
    RAISE EXCEPTION 'UTENTE % non è di tipo passeggero', NEW.id;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_check_tipo_passeggero ON passeggero;
CREATE TRIGGER trg_check_tipo_passeggero
BEFORE INSERT ON passeggero
FOR EACH ROW EXECUTE FUNCTION fn_check_tipo_utente_passeggero();


-- Validazione capacità per classe e posti disponibili prima di emettere un biglietto
CREATE OR REPLACE FUNCTION fn_validate_ticket_capacity() RETURNS trigger AS $$
DECLARE
  tot_disp INT;
  seats_e INT; seats_b INT; seats_f INT;
  used INT;
BEGIN
  SELECT posti_disponibili INTO tot_disp FROM volo WHERE id = NEW.volo_id;
  IF tot_disp IS NULL OR tot_disp <= 0 THEN
    RAISE EXCEPTION 'Nessun posto disponibile per VOLO %', NEW.volo_id;
  END IF;

  SELECT a.posti_economy, a.posti_business, a.posti_first
    INTO seats_e, seats_b, seats_f
  FROM aereo a
  JOIN volo v ON v.aereo_id = a.id
  WHERE v.id = NEW.volo_id;

  IF NEW.classe = 'economy' THEN
    SELECT COUNT(*) INTO used FROM biglietto WHERE volo_id = NEW.volo_id AND classe = 'economy';
    IF used >= seats_e THEN RAISE EXCEPTION 'Classe ECONOMY esaurita per VOLO %', NEW.volo_id; END IF;
  ELSIF NEW.classe = 'business' THEN
    SELECT COUNT(*) INTO used FROM biglietto WHERE volo_id = NEW.volo_id AND classe = 'business';
    IF used >= seats_b THEN RAISE EXCEPTION 'Classe BUSINESS esaurita per VOLO %', NEW.volo_id; END IF;
  ELSE
    SELECT COUNT(*) INTO used FROM biglietto WHERE volo_id = NEW.volo_id AND classe = 'first';
    IF used >= seats_f THEN RAISE EXCEPTION 'Classe FIRST esaurita per VOLO %', NEW.volo_id; END IF;
  END IF;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_validate_ticket_capacity ON biglietto;
CREATE TRIGGER trg_validate_ticket_capacity
BEFORE INSERT ON biglietto
FOR EACH ROW EXECUTE FUNCTION fn_validate_ticket_capacity();


-- Decremento/incremento posti_disponibili su insert/delete biglietto
CREATE OR REPLACE FUNCTION fn_dec_posti_disponibili() RETURNS trigger AS $$
BEGIN
  UPDATE volo SET posti_disponibili = posti_disponibili - 1
  WHERE id = NEW.volo_id;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_dec_posti_after_insert ON biglietto;
CREATE TRIGGER trg_dec_posti_after_insert
AFTER INSERT ON biglietto
FOR EACH ROW EXECUTE FUNCTION fn_dec_posti_disponibili();

CREATE OR REPLACE FUNCTION fn_inc_posti_disponibili() RETURNS trigger AS $$
BEGIN
  UPDATE volo SET posti_disponibili = posti_disponibili + 1
  WHERE id = OLD.volo_id;
  RETURN OLD;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_inc_posti_after_delete ON biglietto;
CREATE TRIGGER trg_inc_posti_after_delete
AFTER DELETE ON biglietto
FOR EACH ROW EXECUTE FUNCTION fn_inc_posti_disponibili();

COMMIT;
