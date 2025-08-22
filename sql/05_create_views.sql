-- ==================================================
-- CREAZIONE VISTE
-- ==================================================

-- Connettiti al database flyght_booking
\c flyght_booking;

-- ==================================================
-- VISTA VOLI DETTAGLIATI
-- ==================================================
CREATE OR REPLACE VIEW vw_voli_dettagliati AS
SELECT 
    v.id AS volo_id,
    v.partenza,
    v.arrivo,
    (v.arrivo - v.partenza) AS durata,
    v.posti_disponibili,
    
    -- Informazioni tratta
    t.id AS tratta_id,
    t.aeroporto_partenza,
    ap.citta AS citta_partenza,
    ap.paese AS paese_partenza,
    t.aeroporto_arrivo,
    aa.citta AS citta_arrivo,
    aa.paese AS paese_arrivo,
    
    -- Informazioni aereo
    a.id AS aereo_id,
    a.modello AS aereo_modello,
    a.posti_totali,
    a.posti_economy,
    a.posti_business,
    a.posti_first,
    
    -- Informazioni compagnia
    c.id AS compagnia_id,
    c.nome_compagnia,
    u.email AS compagnia_email,
    
    -- Calcolo posti occupati per classe
    (a.posti_economy - COALESCE(economy_occupati.count, 0)) AS posti_disponibili_economy,
    (a.posti_business - COALESCE(business_occupati.count, 0)) AS posti_disponibili_business,
    (a.posti_first - COALESCE(first_occupati.count, 0)) AS posti_disponibili_first

FROM volo v
JOIN tratta t ON v.tratta_id = t.id
JOIN aeroporto ap ON t.aeroporto_partenza = ap.codice
JOIN aeroporto aa ON t.aeroporto_arrivo = aa.codice
JOIN aereo a ON v.aereo_id = a.id
JOIN compagnia_aerea c ON t.compagnia_id = c.id
JOIN utente u ON c.id = u.id

-- Subquery per contare posti occupati in economy
LEFT JOIN (
    SELECT 
        b.volo_id, 
        COUNT(*) as count
    FROM biglietto b
    JOIN prenotazione p ON b.prenotazione_id = p.id
    WHERE b.classe = 'economy' AND p.stato = 'confermata'
    GROUP BY b.volo_id
) economy_occupati ON v.id = economy_occupati.volo_id

-- Subquery per contare posti occupati in business
LEFT JOIN (
    SELECT 
        b.volo_id, 
        COUNT(*) as count
    FROM biglietto b
    JOIN prenotazione p ON b.prenotazione_id = p.id
    WHERE b.classe = 'business' AND p.stato = 'confermata'
    GROUP BY b.volo_id
) business_occupati ON v.id = business_occupati.volo_id

-- Subquery per contare posti occupati in first
LEFT JOIN (
    SELECT 
        b.volo_id, 
        COUNT(*) as count
    FROM biglietto b
    JOIN prenotazione p ON b.prenotazione_id = p.id
    WHERE b.classe = 'first' AND p.stato = 'confermata'
    GROUP BY b.volo_id
) first_occupati ON v.id = first_occupati.volo_id;

-- Commento
COMMENT ON VIEW vw_voli_dettagliati IS 'Vista completa dei voli con tutte le informazioni correlate e disponibilità posti per classe';

-- ==================================================
-- VISTA PRENOTAZIONI DETTAGLIATE
-- ==================================================
CREATE OR REPLACE VIEW vw_prenotazioni_dettagliate AS
SELECT 
    pr.id AS prenotazione_id,
    pr.data_acquisto,
    pr.costo_totale,
    pr.stato AS stato_prenotazione,
    
    -- Informazioni passeggero
    pas.id AS passeggero_id,
    pas.nome,
    pas.cognome,
    (pas.nome || ' ' || pas.cognome) AS nome_completo,
    u.username,
    u.email,
    
    -- Informazioni biglietto
    b.id AS biglietto_id,
    b.classe,
    b.posto,
    
    -- Informazioni volo
    v.id AS volo_id,
    v.partenza,
    v.arrivo,
    (v.arrivo - v.partenza) AS durata_volo,
    
    -- Informazioni tratta  
    t.aeroporto_partenza,
    ap.citta AS citta_partenza,
    t.aeroporto_arrivo,
    aa.citta AS citta_arrivo,
    
    -- Informazioni compagnia
    c.nome_compagnia,
    
    -- Informazioni aereo
    a.modello AS aereo_modello,
    
    -- Calcolo costo base biglietto (senza extra)
    pv.prezzo AS prezzo_biglietto,
    
    -- Count extra per questo biglietto
    COALESCE(extra_count.count, 0) AS numero_extra

FROM prenotazione pr
JOIN passeggero pas ON pr.passeggero_id = pas.id  
JOIN utente u ON pas.id = u.id
JOIN biglietto b ON pr.id = b.prenotazione_id
JOIN volo v ON b.volo_id = v.id
JOIN tratta t ON v.tratta_id = t.id
JOIN aeroporto ap ON t.aeroporto_partenza = ap.codice
JOIN aeroporto aa ON t.aeroporto_arrivo = aa.codice
JOIN compagnia_aerea c ON t.compagnia_id = c.id
JOIN aereo a ON v.aereo_id = a.id
LEFT JOIN prezzo_volo pv ON v.id = pv.volo_id AND b.classe = pv.classe

-- Subquery per contare extra
LEFT JOIN (
    SELECT 
        biglietto_id,
        COUNT(*) as count
    FROM bigliettoextra
    GROUP BY biglietto_id
) extra_count ON b.id = extra_count.biglietto_id;

-- Commento
COMMENT ON VIEW vw_prenotazioni_dettagliate IS 'Vista completa delle prenotazioni con tutti i dettagli di volo, passeggero e servizi';

-- ==================================================
-- VISTA STATISTICHE COMPAGNIE
-- ==================================================
CREATE OR REPLACE VIEW vw_statistiche_compagnie AS
SELECT 
    c.id AS compagnia_id,
    c.nome_compagnia,
    u.email AS compagnia_email,
    
    -- Conteggi base
    COUNT(DISTINCT a.id) AS numero_aerei,
    COUNT(DISTINCT t.id) AS numero_tratte,
    COUNT(DISTINCT v.id) AS numero_voli,
    
    -- Statistiche prenotazioni
    COUNT(DISTINCT pr.id) AS numero_prenotazioni_totali,
    COUNT(DISTINCT CASE WHEN pr.stato = 'confermata' THEN pr.id END) AS prenotazioni_confermate,
    COUNT(DISTINCT CASE WHEN pr.stato = 'cancellata' THEN pr.id END) AS prenotazioni_cancellate,
    
    -- Statistiche biglietti per classe
    COUNT(CASE WHEN b.classe = 'economy' AND pr.stato = 'confermata' THEN b.id END) AS biglietti_economy,
    COUNT(CASE WHEN b.classe = 'business' AND pr.stato = 'confermata' THEN b.id END) AS biglietti_business,
    COUNT(CASE WHEN b.classe = 'first' AND pr.stato = 'confermata' THEN b.id END) AS biglietti_first,
    
    -- Statistiche finanziarie
    COALESCE(SUM(CASE WHEN pr.stato = 'confermata' THEN pr.costo_totale END), 0) AS ricavi_totali,
    COALESCE(AVG(CASE WHEN pr.stato = 'confermata' THEN pr.costo_totale END), 0) AS ricavo_medio_prenotazione,
    
    -- Capacità totale flotta
    COALESCE(SUM(a.posti_totali), 0) AS posti_totali_flotta,
    COALESCE(SUM(a.posti_economy), 0) AS posti_economy_flotta,
    COALESCE(SUM(a.posti_business), 0) AS posti_business_flotta,
    COALESCE(SUM(a.posti_first), 0) AS posti_first_flotta

FROM compagnia_aerea c
JOIN utente u ON c.id = u.id
LEFT JOIN aereo a ON c.id = a.compagnia_id
LEFT JOIN tratta t ON c.id = t.compagnia_id  
LEFT JOIN volo v ON t.id = v.tratta_id
LEFT JOIN biglietto b ON v.id = b.volo_id
LEFT JOIN prenotazione pr ON b.prenotazione_id = pr.id

GROUP BY c.id, c.nome_compagnia, u.email;

-- Commento
COMMENT ON VIEW vw_statistiche_compagnie IS 'Statistiche aggregate per compagnia: flotta, voli, prenotazioni e ricavi';

-- ==================================================
-- VISTA VOLI RICERCA (ottimizzata per search)
-- ==================================================
CREATE OR REPLACE VIEW vw_voli_ricerca AS
SELECT 
    v.id AS volo_id,
    v.partenza,
    v.arrivo,
    EXTRACT(EPOCH FROM (v.arrivo - v.partenza))/3600 AS durata_ore,
    v.posti_disponibili,
    
    -- Tratta
    t.aeroporto_partenza,
    t.aeroporto_arrivo,
    ap.citta AS citta_partenza,
    aa.citta AS citta_arrivo,
    
    -- Compagnia e aereo
    c.nome_compagnia,
    a.modello AS aereo_modello,
    a.posti_economy,
    a.posti_business,
    a.posti_first,
    
    -- Prezzi (come JSON per facile parsing)
    json_object_agg(pv.classe, pv.prezzo) FILTER (WHERE pv.classe IS NOT NULL) AS prezzi_json,
    
    -- Prezzo minimo per ordinamento
    MIN(pv.prezzo) AS prezzo_minimo,
    
    -- Disponibilità per classe (calcolata)
    (a.posti_economy - COALESCE(economy_occ.count, 0)) AS posti_disponibili_economy,
    (a.posti_business - COALESCE(business_occ.count, 0)) AS posti_disponibili_business,
    (a.posti_first - COALESCE(first_occ.count, 0)) AS posti_disponibili_first,
    
    -- Flag per disponibilità
    (v.posti_disponibili > 0) AS ha_posti_disponibili,
    (DATE(v.partenza) >= CURRENT_DATE) AS volo_futuro

FROM volo v
JOIN tratta t ON v.tratta_id = t.id
JOIN aeroporto ap ON t.aeroporto_partenza = ap.codice
JOIN aeroporto aa ON t.aeroporto_arrivo = aa.codice
JOIN compagnia_aerea c ON t.compagnia_id = c.id
JOIN aereo a ON v.aereo_id = a.id
LEFT JOIN prezzo_volo pv ON v.id = pv.volo_id

-- Posti occupati economy
LEFT JOIN (
    SELECT b.volo_id, COUNT(*) as count
    FROM biglietto b
    JOIN prenotazione p ON b.prenotazione_id = p.id
    WHERE b.classe = 'economy' AND p.stato = 'confermata'
    GROUP BY b.volo_id
) economy_occ ON v.id = economy_occ.volo_id

-- Posti occupati business  
LEFT JOIN (
    SELECT b.volo_id, COUNT(*) as count
    FROM biglietto b
    JOIN prenotazione p ON b.prenotazione_id = p.id
    WHERE b.classe = 'business' AND p.stato = 'confermata'
    GROUP BY b.volo_id
) business_occ ON v.id = business_occ.volo_id

-- Posti occupati first
LEFT JOIN (
    SELECT b.volo_id, COUNT(*) as count
    FROM biglietto b
    JOIN prenotazione p ON b.prenotazione_id = p.id
    WHERE b.classe = 'first' AND p.stato = 'confermata'
    GROUP BY b.volo_id
) first_occ ON v.id = first_occ.volo_id

GROUP BY 
    v.id, v.partenza, v.arrivo, v.posti_disponibili,
    t.aeroporto_partenza, t.aeroporto_arrivo, 
    ap.citta, aa.citta,
    c.nome_compagnia, a.modello,
    a.posti_economy, a.posti_business, a.posti_first,
    economy_occ.count, business_occ.count, first_occ.count;

-- Commento
COMMENT ON VIEW vw_voli_ricerca IS 'Vista ottimizzata per la ricerca voli con prezzi e disponibilità aggregate';

-- ==================================================
-- VISTA DASHBOARD PASSEGGERI
-- ==================================================
CREATE OR REPLACE VIEW vw_dashboard_passeggero AS
SELECT 
    pas.id AS passeggero_id,
    (pas.nome || ' ' || pas.cognome) AS nome_completo,
    
    -- Statistiche prenotazioni
    COUNT(DISTINCT pr.id) AS numero_prenotazioni_totale,
    COUNT(DISTINCT CASE WHEN pr.stato = 'confermata' THEN pr.id END) AS prenotazioni_attive,
    COUNT(DISTINCT CASE WHEN pr.stato = 'cancellata' THEN pr.id END) AS prenotazioni_cancellate,
    
    -- Statistiche voli
    COUNT(DISTINCT CASE WHEN pr.stato = 'confermata' AND v.partenza >= CURRENT_TIMESTAMP THEN b.id END) AS voli_futuri,
    COUNT(DISTINCT CASE WHEN pr.stato = 'confermata' AND v.partenza < CURRENT_TIMESTAMP THEN b.id END) AS voli_passati,
    
    -- Statistiche finanziarie
    COALESCE(SUM(CASE WHEN pr.stato = 'confermata' THEN pr.costo_totale END), 0) AS spesa_totale,
    COALESCE(AVG(CASE WHEN pr.stato = 'confermata' THEN pr.costo_totale END), 0) AS spesa_media,
    
    -- Classe preferita
    (SELECT b2.classe 
     FROM biglietto b2 
     JOIN prenotazione pr2 ON b2.prenotazione_id = pr2.id 
     WHERE pr2.passeggero_id = pas.id AND pr2.stato = 'confermata'
     GROUP BY b2.classe 
     ORDER BY COUNT(*) DESC 
     LIMIT 1
    ) AS classe_preferita,
    
    -- Compagnia più utilizzata
    (SELECT c2.nome_compagnia
     FROM biglietto b2
     JOIN prenotazione pr2 ON b2.prenotazione_id = pr2.id
     JOIN volo v2 ON b2.volo_id = v2.id
     JOIN tratta t2 ON v2.tratta_id = t2.id
     JOIN compagnia_aerea c2 ON t2.compagnia_id = c2.id
     WHERE pr2.passeggero_id = pas.id AND pr2.stato = 'confermata'
     GROUP BY c2.nome_compagnia
     ORDER BY COUNT(*) DESC
     LIMIT 1
    ) AS compagnia_preferita

FROM passeggero pas
LEFT JOIN prenotazione pr ON pas.id = pr.passeggero_id
LEFT JOIN biglietto b ON pr.id = b.prenotazione_id  
LEFT JOIN volo v ON b.volo_id = v.id

GROUP BY pas.id, pas.nome, pas.cognome;

-- Commento
COMMENT ON VIEW vw_dashboard_passeggero IS 'Statistiche aggregate per dashboard passeggeri con preferenze e storico';

-- ==================================================
-- INDICI SULLE VISTE (per performance)
-- ==================================================

-- Le viste materializzate non sono necessarie per questo progetto,
-- ma ecco alcuni indici utili sulle tabelle base per migliorare le performance delle viste

-- Indice per ricerche per data
CREATE INDEX IF NOT EXISTS idx_volo_data_partenza ON volo(DATE(partenza));

-- Indice per prenotazioni per stato
CREATE INDEX IF NOT EXISTS idx_prenotazione_stato_passeggero ON prenotazione(stato, passeggero_id);

-- Indice composito per biglietti
CREATE INDEX IF NOT EXISTS idx_biglietto_volo_classe ON biglietto(volo_id, classe);

-- ==================================================
-- PERMESSI SULLE VISTE (esempio)
-- ==================================================

-- Esempio di come concedere permessi specifici
-- GRANT SELECT ON vw_voli_ricerca TO compagnia_role;  
-- GRANT SELECT ON vw_dashboard_passeggero TO passeggero_role;
