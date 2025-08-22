-- ==================================================
-- SCRIPT MASTER PER CREAZIONE COMPLETA DATABASE
-- ==================================================
-- Verifica finale
\c flyght_booking;

SELECT 'Setup database completato!' as status;

SELECT 
    'TABELLE PRINCIPALI:' as info,
    '' as tabella, 
    '' as records
UNION ALL
SELECT 
    '' as info,
    'Aeroporti' as tabella, 
    COUNT(*)::text as records 
FROM aeroporto
UNION ALL
SELECT '', 'Compagnie', COUNT(*)::text FROM compagnia_aerea
UNION ALL
SELECT '', 'Passeggeri', COUNT(*)::text FROM passeggero
UNION ALL
SELECT '', 'Aerei', COUNT(*)::text FROM aereo
UNION ALL
SELECT '', 'Tratte', COUNT(*)::text FROM tratta
UNION ALL
SELECT '', 'Voli', COUNT(*)::text FROM volo
UNION ALL
SELECT '', 'Prenotazioni', COUNT(*)::text FROM prenotazione
UNION ALL
SELECT '', 'Biglietti', COUNT(*)::text FROM biglietto;

SELECT 
    'VISTE DISPONIBILI:' as info
UNION ALL
SELECT viewname as info
FROM pg_views 
WHERE schemaname = 'public' 
AND viewname LIKE 'vw_%'
ORDER BY info;

SELECT 
    'TRIGGER ATTIVI:' as info
UNION ALL
SELECT 
    t.tgname as info
FROM pg_trigger t
JOIN pg_class c ON t.tgrelid = c.oid
WHERE c.relnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public')
AND NOT t.tgisinternal
ORDER BY info;

-- Password per gli utenti di test:
-- Tutte le password sono: password123
-- Username disponibili:
-- - ita_airways (compagnia)
-- - ryanair (compagnia) 
-- - lufthansa (compagnia)
-- - mario_rossi (passeggero)
-- - giulia_bianchi (passeggero)
-- - luca_verdi (passeggero)
-- - anna_ferrari (passeggero)
-- - marco_colombo (passeggero)
