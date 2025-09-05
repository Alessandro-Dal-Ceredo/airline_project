BEGIN;

-- Vista per VOLI: passeggeri e ricavi (biglietti + extra), solo prenotazioni confermate
CREATE OR REPLACE VIEW v_statistiche_voli AS
WITH extra_per_biglietto AS (
  SELECT be.biglietto_id, COALESCE(SUM(e.prezzo),0) AS extra_tot
  FROM bigliettoextra be
  JOIN extra e ON e.id = be.extra_id
  GROUP BY be.biglietto_id
),
agg AS (
  SELECT
    b.volo_id,
    COUNT(*) FILTER (WHERE p.stato = 'confermata')                                             AS num_biglietti,
    SUM(CASE WHEN p.stato='confermata' THEN pv.prezzo ELSE 0 END)                               AS ricavi_biglietti,
    SUM(CASE WHEN p.stato='confermata' THEN COALESCE(x.extra_tot,0) ELSE 0 END)                 AS ricavi_extra,
    SUM(CASE WHEN p.stato='confermata' THEN pv.prezzo + COALESCE(x.extra_tot,0) ELSE 0 END)     AS ricavi_totale
  FROM biglietto b
  JOIN prenotazione p ON p.id = b.prenotazione_id
  JOIN prezzo_volo pv ON pv.volo_id = b.volo_id AND pv.classe = b.classe
  LEFT JOIN extra_per_biglietto x ON x.biglietto_id = b.id
  GROUP BY b.volo_id
)
SELECT
  v.id                 AS volo_id,
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
FROM volo v
JOIN tratta t           ON t.id = v.tratta_id
JOIN compagnia_aerea ca ON ca.id = t.compagnia_id
LEFT JOIN agg a         ON a.volo_id = v.id;

-- Vista per COMPAGNIE: aggregazione delle metriche per compagnia
CREATE OR REPLACE VIEW v_statistiche_compagnie AS
SELECT
  compagnia_id,
  nome_compagnia,
  SUM(num_passeggeri)     AS num_passeggeri,
  SUM(ricavi_biglietti)   AS ricavi_biglietti,
  SUM(ricavi_extra)       AS ricavi_extra,
  SUM(guadagno_totale)    AS guadagno_totale
FROM v_statistiche_voli
GROUP BY compagnia_id, nome_compagnia;

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