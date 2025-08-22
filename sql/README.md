# Database SQL Scripts - BD Airline (flyght_booking)

Questa cartella contiene tutti gli script SQL necessari per creare e configurare il database PostgreSQL per il sistema di prenotazione voli BD Airline.

## 📂 Struttura File

```
sql/
├── 00_run_all.sql              # Script master che esegue tutto in ordine
├── 01_create_database.sql      # Creazione database flyght_booking  
├── 02_create_enums.sql         # Creazione enum types
├── 03_create_tables.sql        # Creazione tabelle principali
├── 04_create_triggers.sql      # Trigger e funzioni PL/pgSQL
├── 05_create_views.sql         # Viste per query ottimizzate
├── 06_populate_sample_data.sql # Dati di esempio per test
└── README.md                   # Questo file
```

## 🚀 Esecuzione Rapida

### Opzione 1: Script Master (Consigliato)
```bash
# Esegui tutto in una volta
psql -U postgres -f /Users/dalce/Developer/bdProject/sql/00_run_all.sql
```

### Opzione 2: Esecuzione Manuale
```bash
# Esegui gli script in ordine
psql -U postgres -f /Users/dalce/Developer/bdProject/sql/01_create_database.sql
psql -U postgres -f /Users/dalce/Developer/bdProject/sql/02_create_enums.sql
psql -U postgres -f /Users/dalce/Developer/bdProject/sql/03_create_tables.sql
psql -U postgres -f /Users/dalce/Developer/bdProject/sql/04_create_triggers.sql
psql -U postgres -f /Users/dalce/Developer/bdProject/sql/05_create_views.sql
psql -U postgres -f /Users/dalce/Developer/bdProject/sql/06_populate_sample_data.sql
```

## 🗄️ Schema Database

### Tabelle Principali
- **utente** - Autenticazione e dati base
- **compagnia_aerea** - Estensione per compagnie
- **passeggero** - Estensione per passeggeri  
- **aeroporto** - Aeroporti con codici IATA
- **tratta** - Rotte servite dalle compagnie
- **aereo** - Flotta delle compagnie
- **volo** - Voli schedulati
- **prezzo_volo** - Prezzi per classe
- **prenotazione** - Prenotazioni passeggeri
- **biglietto** - Biglietti individuali
- **extra** - Servizi aggiuntivi
- **bigliettoextra** - Associazione biglietti-extra

### Viste Principali
- **vw_voli_dettagliati** - Voli con tutte le info correlate
- **vw_prenotazioni_dettagliate** - Prenotazioni complete
- **vw_statistiche_compagnie** - Statistiche aggregate per compagnia
- **vw_voli_ricerca** - Vista ottimizzata per ricerca voli
- **vw_dashboard_passeggero** - Statistiche per dashboard passeggeri

### Trigger Implementati
- **Gestione posti disponibili** - Aggiornamento automatico
- **Validazione prenotazioni** - Impedisce duplicati
- **Validazione classi** - Verifica disponibilità classe sull'aereo
- **Audit log** - Tracciamento modifiche prenotazioni

## 👥 Utenti di Test

Dopo l'esecuzione degli script, saranno disponibili questi utenti per test:

### Compagnie Aeree
- **Username:** `ita_airways` | **Password:** `password123`
- **Username:** `ryanair` | **Password:** `password123`  
- **Username:** `lufthansa` | **Password:** `password123`

### Passeggeri
- **Username:** `mario_rossi` | **Password:** `password123`
- **Username:** `giulia_bianchi` | **Password:** `password123`
- **Username:** `luca_verdi` | **Password:** `password123`
- **Username:** `anna_ferrari` | **Password:** `password123`
- **Username:** `marco_colombo` | **Password:** `password123`

## 🛠️ Requisiti

- **PostgreSQL 12+**
- **Utente con privilegi di creazione database** (es: postgres)
- **Connessione locale o remota configurata**

## 🔧 Configurazione Flask

Dopo aver eseguito gli script, assicurati che il file `config.py` nel progetto Flask punti al database:

```python
SQLALCHEMY_DATABASE_URI = 'postgresql://username:password@localhost/flyght_booking'
```

## 📊 Dati di Esempio

Gli script popolano il database con:

- **20 aeroporti** internazionali
- **3 compagnie aeree** (ITA Airways, Ryanair, Lufthansa)
- **8 aerei** con configurazioni realistiche
- **24 tratte** bidirezionali
- **18 voli** per domani con orari variati
- **4 prenotazioni** di esempio (3 confermate, 1 cancellata)
- **8 servizi extra** acquistabili

## 🚨 Note Importanti

1. **Backup**: Crea sempre un backup prima di eseguire script su database di produzione
2. **Permessi**: Assicurati di avere i permessi necessari per creare database
3. **Connessione**: Verifica che PostgreSQL sia in esecuzione e accessibile
4. **Encoding**: Gli script utilizzano UTF-8 per caratteri internazionali
5. **Trigger**: I trigger gestiscono automaticamente la logica di business

## 🐛 Troubleshooting

### Errore di connessione
```bash
# Verifica stato PostgreSQL
sudo systemctl status postgresql

# Avvia PostgreSQL se non attivo
sudo systemctl start postgresql
```

### Database già esistente
```sql
-- Elimina database esistente (ATTENZIONE: perdita dati!)
DROP DATABASE IF EXISTS flyght_booking;
```

### Permessi insufficienti
```bash
# Esegui come superuser
sudo -u postgres psql -f /path/to/script.sql
```

## 📝 Personalizzazione

Per adattare gli script alle tue esigenze:

1. **Modifica dati aeroporti** in `06_populate_sample_data.sql`
2. **Aggiungi compagnie** seguendo il pattern esistente
3. **Configura prezzi voli** secondo le tue logiche di business
4. **Personalizza trigger** per regole specifiche

## 🔄 Reset Database

Per resettare completamente il database:

```sql
-- Connettiti come superuser
DROP DATABASE IF EXISTS flyght_booking;
-- Poi riesegui gli script
```

---

**Progetto:** BD Airline - Sistema Prenotazione Voli Singoli  
**Database:** PostgreSQL flyght_booking  
**Versione:** 1.0  
**Data:** Dicembre 2024
