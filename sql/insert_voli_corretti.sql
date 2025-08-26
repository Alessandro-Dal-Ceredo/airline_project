-- ==================================================
-- INSERIMENTO VOLI CON ASSOCIAZIONI CORRETTE
-- ==================================================
-- Tratte e Aerei corretti:
-- ITA AIRWAYS (id=2): aereo_id=7
--   - Tratta 2: FCO->AMS
--   - Tratta 3: FCO->LHR
--
-- RYANAIR (id=3): aereo_id=9
--   - Tratta 4: FCO->MAD
--
-- EASYJET (id=4): aereo_id=5
--   - Tratta 5: MXP->CDG
--   - Tratta 6: MXP->LGW
--
-- LUFTHANSA (id=5): aereo_id=11
--   - Tratta 7: FRA->MUC
--   - Tratta 8: FCO->FRA
--
-- AIR FRANCE (id=6): aereo_id=8
--   - Tratta 9: LIN->CDG
--   - Tratta 10: FCO->CDG
--   - Tratta 16: BCN->MXP
--
-- BRITISH AIRWAYS (id=7): aereo_id=2
--   - Tratta 11: LHR->FCO
--
-- WIZZ AIR (id=8): aereo_id=4
--   - Tratta 12: FCO->MXP
--
-- KLM (id=9): aereo_id=10
--   - Tratta 13: AMS->FCO
--
-- VUELING (id=10): aereo_id=6
--   - Tratta 14: FCO->BCN
--
-- TURKISH AIRLINES (id=11): aereo_id=3
--   - Tratta 15: FCO->IST

-- ==================================================
-- INSERIMENTO VOLI (prossimi 30 giorni)
-- ==================================================

-- Voli ITA AIRWAYS
INSERT INTO volo (tratta_id, aereo_id, partenza, arrivo, posti_disponibili) VALUES
-- FCO -> AMS (tratta 2, aereo 7)
(2, 7, CURRENT_DATE + INTERVAL '1 day' + TIME '08:30', CURRENT_DATE + INTERVAL '1 day' + TIME '11:00', 180),
(2, 7, CURRENT_DATE + INTERVAL '1 day' + TIME '14:15', CURRENT_DATE + INTERVAL '1 day' + TIME '16:45', 180),
(2, 7, CURRENT_DATE + INTERVAL '1 day' + TIME '19:20', CURRENT_DATE + INTERVAL '1 day' + TIME '21:50', 180),

-- FCO -> LHR (tratta 3, aereo 7)
(3, 7, CURRENT_DATE + INTERVAL '1 day' + TIME '10:45', CURRENT_DATE + INTERVAL '1 day' + TIME '13:15', 180),
(3, 7, CURRENT_DATE + INTERVAL '1 day' + TIME '18:00', CURRENT_DATE + INTERVAL '1 day' + TIME '20:30', 180);

-- Voli RYANAIR
INSERT INTO volo (tratta_id, aereo_id, partenza, arrivo, posti_disponibili) VALUES
-- FCO -> MAD (tratta 4, aereo 9)
(4, 9, CURRENT_DATE + INTERVAL '1 day' + TIME '06:45', CURRENT_DATE + INTERVAL '1 day' + TIME '09:30', 189),
(4, 9, CURRENT_DATE + INTERVAL '1 day' + TIME '15:30', CURRENT_DATE + INTERVAL '1 day' + TIME '18:15', 189);

-- Voli EASYJET
INSERT INTO volo (tratta_id, aereo_id, partenza, arrivo, posti_disponibili) VALUES
-- MXP -> CDG (tratta 5, aereo 5)
(5, 5, CURRENT_DATE + INTERVAL '1 day' + TIME '11:50', CURRENT_DATE + INTERVAL '1 day' + TIME '13:20', 186),
-- MXP -> LGW (tratta 6, aereo 5)
(6, 5, CURRENT_DATE + INTERVAL '1 day' + TIME '17:00', CURRENT_DATE + INTERVAL '1 day' + TIME '18:40', 186);

-- Voli LUFTHANSA
INSERT INTO volo (tratta_id, aereo_id, partenza, arrivo, posti_disponibili) VALUES
-- FRA -> MUC (tratta 7, aereo 11)
(7, 11, CURRENT_DATE + INTERVAL '1 day' + TIME '08:20', CURRENT_DATE + INTERVAL '1 day' + TIME '09:20', 220),
(7, 11, CURRENT_DATE + INTERVAL '1 day' + TIME '16:40', CURRENT_DATE + INTERVAL '1 day' + TIME '17:40', 220),
-- FCO -> FRA (tratta 8, aereo 11)
(8, 11, CURRENT_DATE + INTERVAL '1 day' + TIME '07:15', CURRENT_DATE + INTERVAL '1 day' + TIME '09:40', 220);

-- Voli AIR FRANCE
INSERT INTO volo (tratta_id, aereo_id, partenza, arrivo, posti_disponibili) VALUES
-- LIN -> CDG (tratta 9, aereo 8)
(9, 8, CURRENT_DATE + INTERVAL '1 day' + TIME '09:00', CURRENT_DATE + INTERVAL '1 day' + TIME '10:30', 180),
-- FCO -> CDG (tratta 10, aereo 8)
(10, 8, CURRENT_DATE + INTERVAL '1 day' + TIME '12:20', CURRENT_DATE + INTERVAL '1 day' + TIME '14:40', 180),
-- BCN -> MXP (tratta 16, aereo 8)
(16, 8, CURRENT_DATE + INTERVAL '1 day' + TIME '15:45', CURRENT_DATE + INTERVAL '1 day' + TIME '17:15', 180);

-- Voli BRITISH AIRWAYS
INSERT INTO volo (tratta_id, aereo_id, partenza, arrivo, posti_disponibili) VALUES
-- LHR -> FCO (tratta 11, aereo 2)
(11, 2, CURRENT_DATE + INTERVAL '1 day' + TIME '09:30', CURRENT_DATE + INTERVAL '1 day' + TIME '13:00', 180);

-- Voli WIZZ AIR
INSERT INTO volo (tratta_id, aereo_id, partenza, arrivo, posti_disponibili) VALUES
-- FCO -> MXP (tratta 12, aereo 4)
(12, 4, CURRENT_DATE + INTERVAL '1 day' + TIME '07:00', CURRENT_DATE + INTERVAL '1 day' + TIME '08:30', 230),
(12, 4, CURRENT_DATE + INTERVAL '1 day' + TIME '18:30', CURRENT_DATE + INTERVAL '1 day' + TIME '20:00', 230);

-- Voli KLM
INSERT INTO volo (tratta_id, aereo_id, partenza, arrivo, posti_disponibili) VALUES
-- AMS -> FCO (tratta 13, aereo 10)
(13, 10, CURRENT_DATE + INTERVAL '1 day' + TIME '10:15', CURRENT_DATE + INTERVAL '1 day' + TIME '12:45', 148);

-- Voli VUELING
INSERT INTO volo (tratta_id, aereo_id, partenza, arrivo, posti_disponibili) VALUES
-- FCO -> BCN (tratta 14, aereo 6)
(14, 6, CURRENT_DATE + INTERVAL '1 day' + TIME '13:25', CURRENT_DATE + INTERVAL '1 day' + TIME '15:10', 180);

-- Voli TURKISH AIRLINES
INSERT INTO volo (tratta_id, aereo_id, partenza, arrivo, posti_disponibili) VALUES
-- FCO -> IST (tratta 15, aereo 3)
(15, 3, CURRENT_DATE + INTERVAL '1 day' + TIME '14:50', CURRENT_DATE + INTERVAL '1 day' + TIME '19:20', 189);

-- ==================================================
-- INSERIMENTO PREZZI VOLI
-- ==================================================

-- Otteniamo gli ID dei voli appena inseriti
-- Assumiamo che partano dall'ID corrente del sequenziale

-- Prezzi voli ITA AIRWAYS (economy + business)
INSERT INTO prezzo_volo (volo_id, classe, prezzo) 
SELECT v.id, 'economy', 
    CASE 
        WHEN v.tratta_id = 2 THEN 145.00  -- FCO->AMS
        WHEN v.tratta_id = 3 THEN 165.00  -- FCO->LHR
    END
FROM volo v
WHERE v.tratta_id IN (2, 3)
  AND v.partenza >= CURRENT_DATE + INTERVAL '1 day'
  AND v.partenza < CURRENT_DATE + INTERVAL '2 days';

INSERT INTO prezzo_volo (volo_id, classe, prezzo) 
SELECT v.id, 'business', 
    CASE 
        WHEN v.tratta_id = 2 THEN 420.00  -- FCO->AMS
        WHEN v.tratta_id = 3 THEN 490.00  -- FCO->LHR
    END
FROM volo v
WHERE v.tratta_id IN (2, 3)
  AND v.partenza >= CURRENT_DATE + INTERVAL '1 day'
  AND v.partenza < CURRENT_DATE + INTERVAL '2 days';

-- Prezzi voli RYANAIR (solo economy)
INSERT INTO prezzo_volo (volo_id, classe, prezzo) 
SELECT v.id, 'economy', 59.99
FROM volo v
WHERE v.tratta_id = 4
  AND v.partenza >= CURRENT_DATE + INTERVAL '1 day'
  AND v.partenza < CURRENT_DATE + INTERVAL '2 days';

-- Prezzi voli EASYJET (solo economy)
INSERT INTO prezzo_volo (volo_id, classe, prezzo) 
SELECT v.id, 'economy', 
    CASE 
        WHEN v.tratta_id = 5 THEN 75.00  -- MXP->CDG
        WHEN v.tratta_id = 6 THEN 85.00  -- MXP->LGW
    END
FROM volo v
WHERE v.tratta_id IN (5, 6)
  AND v.partenza >= CURRENT_DATE + INTERVAL '1 day'
  AND v.partenza < CURRENT_DATE + INTERVAL '2 days';

-- Prezzi voli LUFTHANSA (economy + business + first)
INSERT INTO prezzo_volo (volo_id, classe, prezzo) 
SELECT v.id, 'economy', 
    CASE 
        WHEN v.tratta_id = 7 THEN 89.00   -- FRA->MUC (domestico)
        WHEN v.tratta_id = 8 THEN 155.00  -- FCO->FRA (internazionale)
    END
FROM volo v
WHERE v.tratta_id IN (7, 8)
  AND v.partenza >= CURRENT_DATE + INTERVAL '1 day'
  AND v.partenza < CURRENT_DATE + INTERVAL '2 days';

INSERT INTO prezzo_volo (volo_id, classe, prezzo) 
SELECT v.id, 'business', 
    CASE 
        WHEN v.tratta_id = 7 THEN 240.00  -- FRA->MUC
        WHEN v.tratta_id = 8 THEN 450.00  -- FCO->FRA
    END
FROM volo v
WHERE v.tratta_id IN (7, 8)
  AND v.partenza >= CURRENT_DATE + INTERVAL '1 day'
  AND v.partenza < CURRENT_DATE + INTERVAL '2 days';

INSERT INTO prezzo_volo (volo_id, classe, prezzo) 
SELECT v.id, 'first', 650.00
FROM volo v
WHERE v.tratta_id = 8  -- Solo voli internazionali hanno first class
  AND v.partenza >= CURRENT_DATE + INTERVAL '1 day'
  AND v.partenza < CURRENT_DATE + INTERVAL '2 days';

-- Prezzi voli AIR FRANCE (economy + business)
INSERT INTO prezzo_volo (volo_id, classe, prezzo) 
SELECT v.id, 'economy', 
    CASE 
        WHEN v.tratta_id = 9 THEN 95.00   -- LIN->CDG
        WHEN v.tratta_id = 10 THEN 125.00 -- FCO->CDG
        WHEN v.tratta_id = 16 THEN 110.00 -- BCN->MXP
    END
FROM volo v
WHERE v.tratta_id IN (9, 10, 16)
  AND v.partenza >= CURRENT_DATE + INTERVAL '1 day'
  AND v.partenza < CURRENT_DATE + INTERVAL '2 days';

INSERT INTO prezzo_volo (volo_id, classe, prezzo) 
SELECT v.id, 'business', 
    CASE 
        WHEN v.tratta_id = 9 THEN 280.00  -- LIN->CDG
        WHEN v.tratta_id = 10 THEN 380.00 -- FCO->CDG
        WHEN v.tratta_id = 16 THEN 320.00 -- BCN->MXP
    END
FROM volo v
WHERE v.tratta_id IN (9, 10, 16)
  AND v.partenza >= CURRENT_DATE + INTERVAL '1 day'
  AND v.partenza < CURRENT_DATE + INTERVAL '2 days';

-- Prezzi voli BRITISH AIRWAYS (economy + business + first)
INSERT INTO prezzo_volo (volo_id, classe, prezzo) 
SELECT v.id, 'economy', 175.00
FROM volo v
WHERE v.tratta_id = 11
  AND v.partenza >= CURRENT_DATE + INTERVAL '1 day'
  AND v.partenza < CURRENT_DATE + INTERVAL '2 days';

INSERT INTO prezzo_volo (volo_id, classe, prezzo) 
SELECT v.id, 'business', 520.00
FROM volo v
WHERE v.tratta_id = 11
  AND v.partenza >= CURRENT_DATE + INTERVAL '1 day'
  AND v.partenza < CURRENT_DATE + INTERVAL '2 days';

INSERT INTO prezzo_volo (volo_id, classe, prezzo) 
SELECT v.id, 'first', 1200.00
FROM volo v
WHERE v.tratta_id = 11
  AND v.partenza >= CURRENT_DATE + INTERVAL '1 day'
  AND v.partenza < CURRENT_DATE + INTERVAL '2 days';

-- Prezzi voli WIZZ AIR (solo economy)
INSERT INTO prezzo_volo (volo_id, classe, prezzo) 
SELECT v.id, 'economy', 45.99
FROM volo v
WHERE v.tratta_id = 12
  AND v.partenza >= CURRENT_DATE + INTERVAL '1 day'
  AND v.partenza < CURRENT_DATE + INTERVAL '2 days';

-- Prezzi voli KLM (economy + business)
INSERT INTO prezzo_volo (volo_id, classe, prezzo) 
SELECT v.id, 'economy', 135.00
FROM volo v
WHERE v.tratta_id = 13
  AND v.partenza >= CURRENT_DATE + INTERVAL '1 day'
  AND v.partenza < CURRENT_DATE + INTERVAL '2 days';

INSERT INTO prezzo_volo (volo_id, classe, prezzo) 
SELECT v.id, 'business', 395.00
FROM volo v
WHERE v.tratta_id = 13
  AND v.partenza >= CURRENT_DATE + INTERVAL '1 day'
  AND v.partenza < CURRENT_DATE + INTERVAL '2 days';

-- Prezzi voli VUELING (solo economy)
INSERT INTO prezzo_volo (volo_id, classe, prezzo) 
SELECT v.id, 'economy', 68.00
FROM volo v
WHERE v.tratta_id = 14
  AND v.partenza >= CURRENT_DATE + INTERVAL '1 day'
  AND v.partenza < CURRENT_DATE + INTERVAL '2 days';

-- Prezzi voli TURKISH AIRLINES (economy + business)
INSERT INTO prezzo_volo (volo_id, classe, prezzo) 
SELECT v.id, 'economy', 225.00
FROM volo v
WHERE v.tratta_id = 15
  AND v.partenza >= CURRENT_DATE + INTERVAL '1 day'
  AND v.partenza < CURRENT_DATE + INTERVAL '2 days';

INSERT INTO prezzo_volo (volo_id, classe, prezzo) 
SELECT v.id, 'business', 680.00
FROM volo v
WHERE v.tratta_id = 15
  AND v.partenza >= CURRENT_DATE + INTERVAL '1 day'
  AND v.partenza < CURRENT_DATE + INTERVAL '2 days';
