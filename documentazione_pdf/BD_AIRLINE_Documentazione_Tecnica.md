# BD AIRLINE — SISTEMA DI PRENOTAZIONE VOLI
## DOCUMENTAZIONE TECNICA DEL PROGETTO

**Versione:** 1.0  
**Documento generato il:** 28/08/2025  
**Team:** BD AIRLINE DEVELOPMENT TEAM

---

## 1. INTRODUZIONE

### Descrizione dell'Applicazione

BD AIRLINE è un sistema web per la gestione di prenotazioni di voli aerei, sviluppato con **Flask (Python)** e **PostgreSQL**. L'applicazione supporta due tipologie di utenti — **COMPAGNIE AEREE** e **PASSEGGERI** — con funzionalità dedicate.  
Il sistema copre l’intero ciclo di vita della prenotazione: **ricerca**, **selezione**, **acquisto**, **assegnazione posti**, **servizi extra**, **politiche di cancellazione** e **monitoraggio disponibilità** in tempo reale.

---

## 2. FUNZIONALITÀ PRINCIPALI

### 2.1 Gestione Utenti e Autenticazione

**Sistema di autenticazione**
- **Registrazione differenziata**: COMPAGNIA AEREA o PASSEGGERO.  
- **Login sicuro**: Flask-Login con password **hashate** (Werkzeug).  

### 2.2 Funzionalità per Compagnie Aeree

**GESTIONE FLOTTA**
- Aeromobili.  
- Configurazione posti per classe (**ECONOMY**, **BUSINESS**, **FIRST**).  
- Vincoli per coerenza **posti_totali**.

**GESTIONE TRATTE**
- Creazione tratte tra aeroporti (codici **IATA**).  
- Prevenzione tratte duplicate/circolari.  
- Tratte associate alla **compagnia aerea**.

**GESTIONE VOLI**
- Schedulazione con orari specifici.  
- Definizione prezzi per classe.  
- **Posti disponibili** aggiornati in tempo reale.  
- Filtri avanzati su dashboard.

**DASHBOARD ANALITICA**
- **Ricavi totali**, **Voli Attivi**, **Aerei in Flotta**, **Tratte Servite**.

### 2.3 Funzionalità per Passeggeri

**RICERCA VOLI AVANZATA**
- Filtri per **origine**, **destinazione**, **data**.  
- Supporto **voli diretti** e **con 1 scalo**.  
- Ordinamento dinamico per **prezzo**, **partenza**, **durata** (ASC/DESC).

**SISTEMA DI PRENOTAZIONE**
- Selezione **classe** e **posto** (mappa interattiva).  
- Aggiunta **servizi extra** (bagaglio, pasti, wifi, …).  
- Calcolo **prezzo totale** in tempo reale.  
- Gestione **race conditions** per prenotazioni simultanee.

**GESTIONE PRENOTAZIONI**
- Dettagli prenotazioni, cancellazione con politiche temporali.  
- Filtri per **stato** (CONFERMATA / CANCELLATA).

### 2.4 Funzionalità Condivise

- Ricerca con **scalo** e **connessione ≥ 2 ore**.  
- Mappa posti dinamica (codifica **1A, 2B, 3C**).  
- Prevenzione **doppia assegnazione** dello stesso posto.

---

## 3. PROGETTAZIONE CONCETTUALE E LOGICA DELLA BASE DI DATI

### 3.1 Schema Logico Relazionale
Utente (id: int, username: string, password: string, email: string, tipo: tipo_utente, createdat: timestamp)
PK(id)
AK(username), AK(email)

CompagniaAerea (id*: int, nome_compagnia: string)
PK(id)
AK(nome_compagnia)
id FK(Utente)

Passeggero (id*: int, nome: string, cognome: string)
PK(id)
id FK(Utente)

Aeroporto (codice: string, città: string, paese: string)
PK(codice)

Tratta (id: int, aeroporto_partenza: string, aeroporto_arrivo: string, compagnia_id*: int)
PK(id)
aeroporto_partenza FK(Aeroporto), aeroporto_arrivo FK(Aeroporto), compagnia_id FK(CompagniaAerea)
CHECK (aeroporto_partenza ≠ aeroporto_arrivo)

Aereo (id: int, modello: string, posti_totali: int, posti_economy: int, posti_business: int, posti_first: int, compagnia_id*: int)
PK(id)
compagnia_id FK(CompagniaAerea)
CHECK (posti_totali > 0)
CHECK (posti_economy + posti_business + posti_first = posti_totali)

Extra (id: int, nome: string, prezzo: numeric)
PK(id)
AK(nome)
CHECK (prezzo ≥ 0)

Volo (id: int, tratta_id: int, aereo_id: int, partenza: timestamp, arrivo: timestamp, posti_disponibili: int)
PK(id)
tratta_id FK(Tratta), aereo_id FK(Aereo)
CHECK (partenza < arrivo)

PrezzoVolo (volo_id*: int, classe: classe_volo, prezzo: numeric)
PK(volo_id, classe)
volo_id FK(Volo)
CHECK (prezzo ≥ 0)

Prenotazione (id: int, passeggero_id*: int, data_acquisto: timestamp, costo_totale: numeric, stato: stato_prenotazione)
PK(id)
passeggero_id FK(Passeggero)
CHECK (costo_totale ≥ 0)

Biglietto (id: int, prenotazione_id: int, volo_id: int, classe: classe_volo, posto: string)
PK(id)
prenotazione_id FK(Prenotazione), volo_id FK(Volo)
AK(volo_id, posto)
CHECK (posto ~ '[0-9]{1,2}[A-Z]')

BigliettoExtra (biglietto_id: int, extra_id: int)
PK(biglietto_id, extra_id)
biglietto_id FK(Biglietto), extra_id FK(Extra)


AGGIUNGERE IMMAGINE DELLA MODELLO CONCETTUALE E MIGLIORARE QUELLO SOPRA

## 4. QUERY PRINCIPALI TRADOTTE IN SQL DA CODICE PYTHON

### 4.1 Ricerca Voli Diretti

```sql
-- Ricerca voli diretti con filtri e ordinamento
SELECT v.id, v.partenza, v.arrivo, v.posti_disponibili,
       t.aeroporto_partenza, t.aeroporto_arrivo,
       a.modello AS aereo_modello,
       c.nome_compagnia,
       pv.classe, pv.prezzo
FROM volo v
JOIN tratta t ON v.tratta_id = t.id
JOIN aereo a ON v.aereo_id = a.id
JOIN compagnia_aerea c ON t.compagnia_id = c.id
LEFT JOIN prezzo_volo pv ON v.id = pv.volo_id
WHERE t.aeroporto_partenza = %s
  AND t.aeroporto_arrivo = %s
  AND DATE(v.partenza) = %s
  AND v.posti_disponibili > 0
ORDER BY v.partenza;
```

### 4.2 Calcolo Ricavi Compagnia

```sql
-- Ricavi totali per compagnia
SELECT COALESCE(SUM(pr.costo_totale), 0) AS ricavi_totali
FROM prenotazione pr
JOIN biglietto b ON pr.id = b.prenotazione_id
JOIN volo v ON b.volo_id = v.id
JOIN tratta t ON v.tratta_id = t.id
WHERE t.compagnia_id = %s
  AND pr.stato = 'confermata';
```

### 4.3 Destinazioni Più Popolari
```sql
-- Destinazioni più richieste
SELECT t.aeroporto_arrivo,
       a.citta, a.paese,
       COUNT(b.id) AS num_prenotazioni
FROM tratta t
JOIN aeroporto a ON t.aeroporto_arrivo = a.codice
JOIN volo v ON t.id = v.tratta_id
JOIN biglietto b ON v.id = b.volo_id
JOIN prenotazione pr ON b.prenotazione_id = pr.id
WHERE pr.stato = 'confermata'
GROUP BY t.aeroporto_arrivo, a.citta, a.paese
ORDER BY num_prenotazioni DESC
LIMIT 3;
```

### 4.4 Posti Occupati
```sql
-- Posti Occupati
SELECT b.posto
FROM biglietto AS b
JOIN prenotazione AS p
  ON p.id = b.prenotazione_id
WHERE b.volo_id = %s
  AND p.stato <> 'cancellata';
```
---

## 5. PRINCIPALI SCELTE PROGETTUALI

### 5.1 Politiche di Integrità

#### 5.1.1 Integrità Referenziale
- **CASCADE DELETE**: eliminando un **UTENTE** si eliminano i dati specializzati.  
- **RESTRICT DELETE**: prevenuta l’eliminazione di **COMPAGNIA/AEREO** con voli attivi.  
- **UNIQUE**: prevenzione duplicati (username, email, nome_compagnia, posto per volo).

#### 5.1.2 Integrità di Dominio
- **CHECK**: validazione orari, prezzi ≥ 0, coerenza posti.  
- **ENUM**: tipi per stato prenotazione, classi volo, tipo utente.  
- **NOT NULL**: campi obbligatori per dati critici.

#### 5.1.3 Integrità Semantica via Trigger

COPIARE E INCOLLARE TRIGGER DENTRO **CreateTriggerFunctions**


### 5.2 Politiche di Autorizzazione

#### 5.2.1 Autenticazione
- Password **hashate** (Werkzeug).  
- Session management con **Flask-Login** e cookie sicuri.  

#### 5.2.2 Autorizzazione Basata su Ruoli

########################################################################################################################
########################################################################################################################
######################################## GABRIIIIII ####################################################################
########################################################################################################################
########################################################################################################################
########################################################################################################################

```python
def requires_user_type(user_type):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if current_user.tipo != user_type:
                flash('Accesso non autorizzato.', 'error')
                return redirect(url_for('home'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Esempio d'uso
@app.route('/dashboard/compagnia')
@login_required
@requires_user_type('compagnia')
def dashboard_compagnia():
    ...
```

#### 5.2.3 Separazione Dati per Compagnia

```python
# Filtro automatico per compagnia nei risultati
voli_query = db.session.query(Volo).join(Tratta).filter(
    Tratta.compagnia_id == current_user.compagnia.id
)
```

### 5.3 Uso di Indici

########################################################################################################################
########################################################################################################################
######################################## DA VERIFICARE #################################################################
########################################################################################################################
########################################################################################################################
########################################################################################################################


- **Ricerche**: indice composto `(tratta_id, partenza)` con condizione su `posti_disponibili`.  
- **Rotte**: indice `(aeroporto_partenza, aeroporto_arrivo)`.  
- **Dashboard**: indici temporali e FK per join efficienti.

### 5.4 Gestione Concorrenza

#### 5.4.1 Race Condition Management

```python
# Gestione prenotazioni simultanee sullo stesso posto
max_tentativi = 3
tentativo = 0
while tentativo < max_tentativi:
    try:
        nuovo_biglietto = Biglietto(posto=posto, volo_id=volo_id)
        db.session.add(nuovo_biglietto)
        db.session.flush()
        break  # Successo
    except IntegrityError:
        db.session.rollback()
        tentativo += 1  # riprova con posto diverso
```

#### 5.4.2 Transazioni ACID

########################################################################################################################
########################################################################################################################
######################################## GABRIIIIII ####################################################################
########################################################################################################################
########################################################################################################################
########################################################################################################################

- **Atomic**: prenotazione (prenotazione + biglietto + extra) in **unica transazione**.  
- **Consistent**: trigger mantengono coerenza **posti**.  
- **Isolated**: livelli di isolamento appropriati.  
- **Durable**: commit espliciti.

---

## 6. ULTERIORI INFORMAZIONI

### 6.1 Architettura Tecnologica

**Stack:**
- **Backend**: Python 3.8+ / Flask 2.3+  
- **Database**: PostgreSQL 
- **ORM**: SQLAlchemy 1.4+ / Flask‑SQLAlchemy  
- **Auth**: Flask‑Login  
- **Frontend**: HTML5, CSS3, JavaScript (vanilla)  
- **Templating**: Jinja2

**Librerie principali (`requirements.txt`):**
```txt
Flask==2.3.3
Flask-SQLAlchemy==3.0.5
Flask-Login==0.6.2
psycopg2-binary==2.9.7
Werkzeug==2.3.7
SQLAlchemy==1.4.41
```

**Configurazione:**
```python
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = f"postgresql://{{user}}:{{pwd}}@{{host}}/{{db}}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_ECHO = True

class ProductionConfig(Config):
    DEBUG = False
    # Opzioni sicurezza aggiuntive...
```

### 6.4 Sicurezza e Validazione
**Gestione errori**
```python
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500
```
---

## 7. CONTRIBUTO AL PROGETTO

> **Nota:** Progetto completato principalmente insieme dato che vivendo nella stessa città c'è stato possibile trovarci e lavorare sul progetto in contemporanea. ( C'è stata una maggior cura per il Front-End e User-Experience da parte di Alessandro Dal Ceredo, mentre per il Back-End da parte di Gabriele D'Amato )

### 7.1 [Alessandro Dal Ceredo - Gabriele D'Amato] — DATABASE DESIGN & BACKEND CORE (35%)
- Progettazione schema (concettuale/logico), modelli SQLAlchemy, trigger e stored procedure, autenticazione, logica core.

### 7.2 [Alessandro Dal Ceredo - Gabriele D'Amato] — FRONTEND & USER EXPERIENCE (30%)
- UI responsive, template Jinja2, JS per mappa posti e ordinamenti, ricerca avanzata, test di usabilità.

### 7.3 [Alessandro Dal Ceredo - Gabriele D'Amato] — BUSINESS LOGIC & ADVANCED FEATURES (25%)
- Ricerca con scali, ordinamento multi‑criterio, gestione posti real‑time, dashboard analytics, prezzi dinamici.

### 7.4 [Alessandro Dal Ceredo - Gabriele D'Amato] — TESTING & DEPLOYMENT (10%)
- Setup ambiente, unit/integration testing, documentazione, deployment, debugging.

**Metodologia di Sviluppo**
- **Agile** (sprint bisettimanali, review/retro).  
- **Git/GitHub** (branching + code review).  
- **Trello/Jira**, **Slack/Discord**, **Docs** condivisi, **Zoom/Meet**.

---
