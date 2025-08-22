-- ==================================================
-- POPOLAZIONE DATABASE CON DATI DI ESEMPIO
-- ==================================================

-- Connettiti al database flyght_booking
\c flyght_booking;

-- Disabilita i trigger temporaneamente per inserimento dati
SET session_replication_role = 'replica';

-- ==================================================
-- INSERIMENTO AEROPORTI
-- ==================================================
INSERT INTO aeroporto (codice, citta, paese) VALUES
('FCO', 'Roma', 'Italia'),
('MXP', 'Milano', 'Italia'),
('VCE', 'Venezia', 'Italia'),
('NAP', 'Napoli', 'Italia'),
('PSA', 'Pisa', 'Italia'),
('BGY', 'Bergamo', 'Italia'),
('LHR', 'Londra', 'Regno Unito'),
('CDG', 'Parigi', 'Francia'),
('MAD', 'Madrid', 'Spagna'),
('BCN', 'Barcellona', 'Spagna'),
('AMS', 'Amsterdam', 'Paesi Bassi'),
('FRA', 'Francoforte', 'Germania'),
('MUC', 'Monaco', 'Germania'),
('ZUR', 'Zurigo', 'Svizzera'),
('VIE', 'Vienna', 'Austria'),
('JFK', 'New York', 'Stati Uniti'),
('LAX', 'Los Angeles', 'Stati Uniti'),
('DXB', 'Dubai', 'Emirati Arabi Uniti'),
('NRT', 'Tokyo', 'Giappone'),
('SYD', 'Sydney', 'Australia');

-- ==================================================
-- INSERIMENTO SERVIZI EXTRA
-- ==================================================
INSERT INTO extra (nome, prezzo) VALUES
('Bagaglio extra 20kg', 25.00),
('Pasto premium', 15.00),
('Wi-Fi a bordo', 8.00),
('Selezione posto preferenziale', 12.00),
('Accesso lounge', 35.00),
('Fast track sicurezza', 10.00),
('Assicurazione viaggio', 18.00),
('Trasporto animali', 50.00);

-- ==================================================
-- INSERIMENTO UTENTI COMPAGNIA
-- ==================================================

-- ITA Airways
INSERT INTO utente (username, email, password, tipo) VALUES
('ita_airways', 'admin@itaairways.com', 'scrypt:32768:8:1$MvzQJzGQ6ZkdFNcm$a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6', 'compagnia');

INSERT INTO compagnia_aerea (id, nome_compagnia) VALUES
(1, 'ITA Airways');

-- Ryanair  
INSERT INTO utente (username, email, password, tipo) VALUES
('ryanair', 'fleet@ryanair.com', 'scrypt:32768:8:1$MvzQJzGQ6ZkdFNcm$a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6', 'compagnia');

INSERT INTO compagnia_aerea (id, nome_compagnia) VALUES
(2, 'Ryanair');

-- Lufthansa
INSERT INTO utente (username, email, password, tipo) VALUES
('lufthansa', 'operations@lufthansa.com', 'scrypt:32768:8:1$MvzQJzGQ6ZkdFNcm$a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6', 'compagnia');

INSERT INTO compagnia_aerea (id, nome_compagnia) VALUES
(3, 'Lufthansa');

-- ==================================================
-- INSERIMENTO AEREI
-- ==================================================

-- Flotta ITA Airways
INSERT INTO aereo (modello, posti_totali, posti_economy, posti_business, posti_first, compagnia_id) VALUES
('Airbus A320', 180, 150, 30, 0, 1),
('Airbus A330', 250, 180, 50, 20, 1),
('Boeing 777', 350, 250, 80, 20, 1);

-- Flotta Ryanair
INSERT INTO aereo (modello, posti_totali, posti_economy, posti_business, posti_first, compagnia_id) VALUES
('Boeing 737-800', 189, 189, 0, 0, 2),
('Boeing 737 MAX', 197, 197, 0, 0, 2);

-- Flotta Lufthansa
INSERT INTO aereo (modello, posti_totali, posti_economy, posti_business, posti_first, compagnia_id) VALUES
('Airbus A320', 174, 150, 24, 0, 3),
('Airbus A340', 300, 220, 60, 20, 3),
('Boeing 747', 400, 300, 80, 20, 3);

-- ==================================================
-- INSERIMENTO TRATTE
-- ==================================================

-- Tratte ITA Airways
INSERT INTO tratta (aeroporto_partenza, aeroporto_arrivo, compagnia_id) VALUES
('FCO', 'MXP', 1), ('MXP', 'FCO', 1),
('FCO', 'LHR', 1), ('LHR', 'FCO', 1),
('FCO', 'CDG', 1), ('CDG', 'FCO', 1),
('MXP', 'FRA', 1), ('FRA', 'MXP', 1),
('FCO', 'JFK', 1), ('JFK', 'FCO', 1);

-- Tratte Ryanair
INSERT INTO tratta (aeroporto_partenza, aeroporto_arrivo, compagnia_id) VALUES
('BGY', 'BCN', 2), ('BCN', 'BGY', 2),
('BGY', 'MAD', 2), ('MAD', 'BGY', 2),
('PSA', 'LHR', 2), ('LHR', 'PSA', 2),
('VCE', 'AMS', 2), ('AMS', 'VCE', 2);

-- Tratte Lufthansa
INSERT INTO tratta (aeroporto_partenza, aeroporto_arrivo, compagnia_id) VALUES
('FRA', 'FCO', 3), ('FCO', 'FRA', 3),
('FRA', 'MXP', 3), ('MXP', 'FRA', 3),
('MUC', 'VCE', 3), ('VCE', 'MUC', 3),
('FRA', 'JFK', 3), ('JFK', 'FRA', 3);

-- ==================================================
-- INSERIMENTO VOLI (prossimi 30 giorni)
-- ==================================================

-- Voli ITA Airways per domani
INSERT INTO volo (tratta_id, aereo_id, partenza, arrivo, posti_disponibili) VALUES
-- FCO -> MXP
(1, 1, CURRENT_DATE + INTERVAL '1 day' + TIME '08:30', CURRENT_DATE + INTERVAL '1 day' + TIME '10:00', 180),
(1, 1, CURRENT_DATE + INTERVAL '1 day' + TIME '14:15', CURRENT_DATE + INTERVAL '1 day' + TIME '15:45', 180),
(1, 1, CURRENT_DATE + INTERVAL '1 day' + TIME '19:20', CURRENT_DATE + INTERVAL '1 day' + TIME '20:50', 180),

-- MXP -> FCO  
(2, 1, CURRENT_DATE + INTERVAL '1 day' + TIME '07:00', CURRENT_DATE + INTERVAL '1 day' + TIME '08:30', 180),
(2, 1, CURRENT_DATE + INTERVAL '1 day' + TIME '16:30', CURRENT_DATE + INTERVAL '1 day' + TIME '18:00', 180),

-- FCO -> LHR
(3, 2, CURRENT_DATE + INTERVAL '1 day' + TIME '10:45', CURRENT_DATE + INTERVAL '1 day' + TIME '13:15', 250),
(3, 2, CURRENT_DATE + INTERVAL '1 day' + TIME '18:00', CURRENT_DATE + INTERVAL '1 day' + TIME '20:30', 250),

-- LHR -> FCO
(4, 2, CURRENT_DATE + INTERVAL '1 day' + TIME '09:30', CURRENT_DATE + INTERVAL '1 day' + TIME '13:00', 250),

-- FCO -> CDG  
(5, 1, CURRENT_DATE + INTERVAL '1 day' + TIME '12:20', CURRENT_DATE + INTERVAL '1 day' + TIME '14:40', 180);

-- Voli Ryanair
INSERT INTO volo (tratta_id, aereo_id, partenza, arrivo, posti_disponibili) VALUES
-- BGY -> BCN
(11, 4, CURRENT_DATE + INTERVAL '1 day' + TIME '06:45', CURRENT_DATE + INTERVAL '1 day' + TIME '08:45', 189),
(11, 4, CURRENT_DATE + INTERVAL '1 day' + TIME '15:30', CURRENT_DATE + INTERVAL '1 day' + TIME '17:30', 189),

-- BCN -> BGY
(12, 4, CURRENT_DATE + INTERVAL '1 day' + TIME '09:15', CURRENT_DATE + INTERVAL '1 day' + TIME '11:15', 189),
(12, 4, CURRENT_DATE + INTERVAL '1 day' + TIME '18:00', CURRENT_DATE + INTERVAL '1 day' + TIME '20:00', 189),

-- BGY -> MAD
(13, 5, CURRENT_DATE + INTERVAL '1 day' + TIME '11:50', CURRENT_DATE + INTERVAL '1 day' + TIME '14:10', 197);

-- Voli Lufthansa
INSERT INTO volo (tratta_id, aereo_id, partenza, arrivo, posti_disponibili) VALUES
-- FRA -> FCO
(19, 6, CURRENT_DATE + INTERVAL '1 day' + TIME '08:20', CURRENT_DATE + INTERVAL '1 day' + TIME '10:45', 174),
(19, 6, CURRENT_DATE + INTERVAL '1 day' + TIME '16:40', CURRENT_DATE + INTERVAL '1 day' + TIME '19:05', 174),

-- FCO -> FRA
(20, 6, CURRENT_DATE + INTERVAL '1 day' + TIME '07:15', CURRENT_DATE + INTERVAL '1 day' + TIME '09:40', 174),

-- FRA -> JFK (volo intercontinentale)
(26, 8, CURRENT_DATE + INTERVAL '1 day' + TIME '13:45', CURRENT_DATE + INTERVAL '1 day' + TIME '17:30', 400);

-- ==================================================
-- INSERIMENTO PREZZI VOLI
-- ==================================================

-- Prezzi voli domestici ITA (voli 1-5)
INSERT INTO prezzo_volo (volo_id, classe, prezzo) VALUES
-- Volo 1: FCO->MXP 08:30
(1, 'economy', 89.00), (1, 'business', 245.00),
-- Volo 2: FCO->MXP 14:15
(2, 'economy', 95.00), (2, 'business', 260.00),
-- Volo 3: FCO->MXP 19:20
(3, 'economy', 85.00), (3, 'business', 240.00),
-- Volo 4: MXP->FCO 07:00
(4, 'economy', 92.00), (4, 'business', 250.00),
-- Volo 5: MXP->FCO 16:30
(5, 'economy', 88.00), (5, 'business', 245.00);

-- Prezzi voli internazionali ITA (voli 6-9)
INSERT INTO prezzo_volo (volo_id, classe, prezzo) VALUES
-- Volo 6: FCO->LHR 10:45
(6, 'economy', 145.00), (6, 'business', 420.00), (6, 'first', 1200.00),
-- Volo 7: FCO->LHR 18:00
(7, 'economy', 155.00), (7, 'business', 440.00), (7, 'first', 1300.00),
-- Volo 8: LHR->FCO 09:30
(8, 'economy', 150.00), (8, 'business', 430.00), (8, 'first', 1250.00),
-- Volo 9: FCO->CDG 12:20
(9, 'economy', 120.00), (9, 'business', 350.00);

-- Prezzi voli Ryanair (solo economy)
INSERT INTO prezzo_volo (volo_id, classe, prezzo) VALUES
-- Voli 10-14
(10, 'economy', 35.99),
(11, 'economy', 42.99),
(12, 'economy', 39.99),
(13, 'economy', 45.99),
(14, 'economy', 52.99);

-- Prezzi voli Lufthansa
INSERT INTO prezzo_volo (volo_id, classe, prezzo) VALUES
-- Voli 15-18
(15, 'economy', 125.00), (15, 'business', 380.00),
(16, 'economy', 130.00), (16, 'business', 390.00),
(17, 'economy', 135.00), (17, 'business', 395.00),
-- Volo intercontinentale FRA->JFK
(18, 'economy', 485.00), (18, 'business', 1450.00), (18, 'first', 3200.00);

-- ==================================================
-- INSERIMENTO UTENTI PASSEGGERO
-- ==================================================
INSERT INTO utente (username, email, password, tipo) VALUES
('mario_rossi', 'mario.rossi@email.com', 'scrypt:32768:8:1$MvzQJzGQ6ZkdFNcm$a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6', 'passeggero'),
('giulia_bianchi', 'giulia.bianchi@email.com', 'scrypt:32768:8:1$MvzQJzGQ6ZkdFNcm$a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6', 'passeggero'),
('luca_verdi', 'luca.verdi@email.com', 'scrypt:32768:8:1$MvzQJzGQ6ZkdFNcm$a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6', 'passeggero'),
('anna_ferrari', 'anna.ferrari@email.com', 'scrypt:32768:8:1$MvzQJzGQ6ZkdFNcm$a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6', 'passeggero'),
('marco_colombo', 'marco.colombo@email.com', 'scrypt:32768:8:1$MvzQJzGQ6ZkdFNcm$a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6', 'passeggero');

INSERT INTO passeggero (id, nome, cognome) VALUES
(4, 'Mario', 'Rossi'),
(5, 'Giulia', 'Bianchi'), 
(6, 'Luca', 'Verdi'),
(7, 'Anna', 'Ferrari'),
(8, 'Marco', 'Colombo');

-- ==================================================
-- INSERIMENTO PRENOTAZIONI DI ESEMPIO
-- ==================================================

-- Prenotazione 1: Mario Rossi - volo FCO->MXP
INSERT INTO prenotazione (passeggero_id, costo_totale, stato, data_acquisto) VALUES
(4, 104.00, 'confermata', CURRENT_TIMESTAMP - INTERVAL '2 days');

INSERT INTO biglietto (prenotazione_id, volo_id, classe, posto) VALUES
(1, 1, 'economy', '12A');

INSERT INTO bigliettoextra (biglietto_id, extra_id) VALUES
(1, 4); -- Selezione posto preferenziale

-- Prenotazione 2: Giulia Bianchi - volo BGY->BCN
INSERT INTO prenotazione (passeggero_id, costo_totale, stato, data_acquisto) VALUES
(5, 58.99, 'confermata', CURRENT_TIMESTAMP - INTERVAL '1 day');

INSERT INTO biglietto (prenotazione_id, volo_id, classe, posto) VALUES
(2, 10, 'economy', '8C');

INSERT INTO bigliettoextra (biglietto_id, extra_id) VALUES
(2, 1), -- Bagaglio extra
(2, 3); -- Wi-Fi

-- Prenotazione 3: Luca Verdi - volo FCO->LHR Business
INSERT INTO prenotazione (passeggero_id, costo_totale, stato, data_acquisto) VALUES
(6, 470.00, 'confermata', CURRENT_TIMESTAMP - INTERVAL '3 hours');

INSERT INTO biglietto (prenotazione_id, volo_id, classe, posto) VALUES
(3, 6, 'business', '3B');

INSERT INTO bigliettoextra (biglietto_id, extra_id) VALUES
(3, 2), -- Pasto premium
(3, 5); -- Accesso lounge

-- Prenotazione 4: Anna Ferrari - volo cancellato
INSERT INTO prenotazione (passeggero_id, costo_totale, stato, data_acquisto) VALUES
(7, 89.00, 'cancellata', CURRENT_TIMESTAMP - INTERVAL '5 days');

INSERT INTO biglietto (prenotazione_id, volo_id, classe, posto) VALUES
(4, 2, 'economy', '15F');

-- Riabilita i trigger
SET session_replication_role = 'origin';

-- ==================================================
-- AGGIORNAMENTO POSTI DISPONIBILI
-- ==================================================

-- Aggiorna manualmente i posti disponibili considerando le prenotazioni
UPDATE volo SET posti_disponibili = (
    SELECT a.posti_totali - COALESCE(
        (SELECT COUNT(*) 
         FROM biglietto b 
         JOIN prenotazione p ON b.prenotazione_id = p.id 
         WHERE b.volo_id = volo.id AND p.stato = 'confermata'), 0)
    FROM aereo a 
    WHERE a.id = volo.aereo_id
);

-- ==================================================
-- VERIFICA DATI INSERITI
-- ==================================================

-- Mostra riepilogo dei dati inseriti
SELECT 'Aeroporti' as tabella, COUNT(*) as records FROM aeroporto
UNION ALL
SELECT 'Compagnie', COUNT(*) FROM compagnia_aerea  
UNION ALL
SELECT 'Passeggeri', COUNT(*) FROM passeggero
UNION ALL
SELECT 'Aerei', COUNT(*) FROM aereo
UNION ALL  
SELECT 'Tratte', COUNT(*) FROM tratta
UNION ALL
SELECT 'Voli', COUNT(*) FROM volo
UNION ALL
SELECT 'Prezzi voli', COUNT(*) FROM prezzo_volo
UNION ALL
SELECT 'Prenotazioni', COUNT(*) FROM prenotazione
UNION ALL
SELECT 'Biglietti', COUNT(*) FROM biglietto
UNION ALL
SELECT 'Extra', COUNT(*) FROM extra
ORDER BY tabella;

-- Test delle viste principali
SELECT 'Test vista voli dettagliati - primi 5 records:' as info;
SELECT volo_id, aeroporto_partenza, aeroporto_arrivo, nome_compagnia, partenza 
FROM vw_voli_dettagliati 
WHERE volo_futuro = true 
ORDER BY partenza 
LIMIT 5;

SELECT 'Test vista prenotazioni dettagliate:' as info;
SELECT prenotazione_id, nome_completo, aeroporto_partenza, aeroporto_arrivo, stato_prenotazione
FROM vw_prenotazioni_dettagliate
WHERE stato_prenotazione = 'confermata';

COMMENT ON SCHEMA public IS 'Database flyght_booking popolato con dati di esempio - BD Airline sistema voli singoli';
