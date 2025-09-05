BEGIN;

-- Vista per VOLI: passeggeri e ricavi (biglietti + extra), solo prenotazioni confermate
CREATE OR REPLACE VIEW v_statistiche_voli AS
-- Inizia una CTE (common table expression): una sub-query nominata, riutilizzabile nel seguito
WITH extra_per_biglietto AS (
  -- Calcola il totale degli extra per ogni biglietto, COALESCE per gestire i valori NULL
  SELECT be.biglietto_id, COALESCE(SUM(e.prezzo),0) AS extra_tot
  FROM bigliettoextra be
  JOIN extra e ON e.id = be.extra_id
  -- Raggruppa per biglietto con la somma degli extra
  GROUP BY be.biglietto_id
),
-- Inizia una seconda CTE: aggrega i dati per volo
agg AS (
  SELECT
    b.volo_id,
    -- Conta i biglietti confermati
    COUNT(*) FILTER (WHERE p.stato = 'confermata') AS num_biglietti,
    -- Somma i ricavi dei biglietti confermati
    SUM(CASE WHEN p.stato='confermata' THEN pv.prezzo ELSE 0 END) AS ricavi_biglietti, -- Somma i ricavi dei biglietti confermati
    -- Somma i ricavi degli extra confermati
    SUM(CASE WHEN p.stato='confermata' THEN COALESCE(x.extra_tot,0) ELSE 0 END) AS ricavi_extra,
    -- Somma i ricavi totali (biglietti + extra)
    SUM(CASE WHEN p.stato='confermata' THEN pv.prezzo + COALESCE(x.extra_tot,0) ELSE 0 END) AS ricavi_totale
  -- Parto dalla tabella biglietto
  FROM biglietto b
  -- Collego il biglietto alla prenotazione, mi serve per filtrare solo i biglietti confermati
  JOIN prenotazione p ON p.id = b.prenotazione_id
  -- Colleghi al biglietto la somma totale dei suoi extra
  JOIN prezzo_volo pv ON pv.volo_id = b.volo_id AND pv.classe = b.classe
  -- Uso LEFT JOIN per gestire i casi in cui non ci sono extra
  LEFT JOIN extra_per_biglietto x ON x.biglietto_id = b.id
  -- Raggruppo per volo, quindi ho la somma dei ricavi totali per ogni volo
  GROUP BY b.volo_id
  -- Risultato della CTE
  -- volo_id = 10 | num_biglietti = 2 | ricavi_biglietti = 200 | ricavi_extra = 30 | guadagno_totale = 230


)
SELECT
  
  v.id AS volo_id,
  t.aeroporto_partenza,
  t.aeroporto_arrivo,
  v.partenza,
  v.arrivo,
  ca.id                AS compagnia_id,
  ca.nome_compagnia,
  COALESCE(a.num_biglietti,0)     AS num_passeggeri,
  COALESCE(a.ricavi_biglietti,0)  AS ricavi_biglietti,
  COALESCE(a.ricavi_extra,0)      AS ricavi_extra,
  COALESCE(a.ricavi_totale,0)     AS guadagno_totale
  -- Parto dalla tabella volo
  FROM volo v
  -- Collego il volo alla tratta
  JOIN tratta t           ON t.id = v.tratta_id
  -- Collego il volo alla compagnia
  JOIN compagnia_aerea ca ON ca.id = t.compagnia_id
  -- Collego il volo alla CTE, uso LEFT JOIN per gestire i casi in cui non ci sono biglietti
  LEFT JOIN agg a         ON a.volo_id = v.id;
  -- Risultato della vista
  -- volo_id = 10 | aeroporto_partenza = "VCE" | aeroporto_arrivo = "FCO" | partenza = "2025-01-01 10:00:00" | arrivo = "2025-01-01 12:00:00" | nome_compagnia = "Alitalia" | num_passeggeri = 2 | ricavi_biglietti = 200 | ricavi_extra = 30 | guadagno_totale = 230

-- Vista per COMPAGNIE: aggregazione delle metriche per compagnia
CREATE OR REPLACE VIEW v_statistiche_compagnie AS
SELECT
  -- Identificativo e li eredito dalla vista v_statistiche_voli
  compagnia_id,
  nome_compagnia,
  -- Somma i passeggeri per compagnia
  SUM(num_passeggeri)     AS num_passeggeri,
  -- Somma i ricavi dei biglietti per compagnia
  SUM(ricavi_biglietti)   AS ricavi_biglietti,
  -- Somma i ricavi degli extra per compagnia
  SUM(ricavi_extra)       AS ricavi_extra,
  -- Somma i ricavi totali per compagnia
  SUM(guadagno_totale)    AS guadagno_totale
-- Riuso la logica della vista v_statistiche_voli
FROM v_statistiche_voli
-- Raggruppo per compagnia
GROUP BY compagnia_id, nome_compagnia;
-- Risultato della vista
-- compagnia_id = 1 | nome_compaglia = "Alitalia" | num_passeggeri = 2 | ricavi_biglietti = 200 | ricavi_extra = 30 | guadagno_totale = 230
--TODO: Commentare tutto il codice

COMMIT;
CREATE INDEX IF NOT EXISTS idx_volo_tratta_partenza
ON volo (tratta_id, partenza);

CREATE INDEX IF NOT EXISTS idx_volo_aereo
ON volo (aereo_id);

CREATE INDEX IF NOT EXISTS idx_biglietto_volo_classe
ON biglietto (volo_id, classe);

CREATE INDEX IF NOT EXISTS idx_prenotazione_passeggero
ON prenotazione (passeggero_id, data_acquisto DESC);

CREATE INDEX IF NOT EXISTS idx_bigliettoextra_biglietto
ON bigliettoextra (biglietto_id);

CREATE INDEX IF NOT EXISTS ix_tratta_compagnia       ON tratta(compagnia_id);

CREATE INDEX IF NOT EXISTS ix_volo_tratta            ON volo(tratta_id);

CREATE INDEX IF NOT EXISTS ix_volo_aereo             ON volo(aereo_id);

CREATE INDEX IF NOT EXISTS ix_volo_partenza          ON volo(partenza);

CREATE INDEX IF NOT EXISTS ix_prenotazione_passeggero ON prenotazione(passeggero_id);