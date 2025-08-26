import os
import random
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import IntegrityError
from config import config
from models import db, Utente, CompagniaAerea, Passeggero, Aeroporto, Volo, Tratta, TipoUtente

def create_app(config_name=None, config_overrides=None):
    """Factory function per creare l'app Flask
    config_overrides: dict opzionale per sovrascrivere configurazioni (utile nei test)
    """
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'default')
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Applica eventuali override prima di inizializzare le estensioni
    if config_overrides:
        app.config.update(config_overrides)
    
    # Inizializza le estensioni
    db.init_app(app)
    
    # Configura Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    login_manager.login_message = 'Devi effettuare il login per accedere a questa pagina.'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        return Utente.query.get(int(user_id))
    
    return app

# Crea l'applicazione
app = create_app()

# ==========================================
# ROUTES PRINCIPALI
# ==========================================

@app.route('/')
def home():
    """Homepage con ricerca voli (accessibile a tutti)"""
    aeroporti = Aeroporto.query.order_by(Aeroporto.citta).all()
    return render_template('home.html', aeroporti=aeroporti)

@app.route('/search')
def search_flights():
    """Ricerca voli - accessibile a tutti (solo andata)"""
    origine = request.args.get('origine', '')
    destinazione = request.args.get('destinazione', '')
    data_partenza = request.args.get('data_partenza', '')
    tipo_ricerca = request.args.get('tipo_ricerca', 'con_scali')
    
    voli_andata = []
    viaggi_combinati = []
    aeroporti = Aeroporto.query.all()
    
    if origine and destinazione and data_partenza:
        if tipo_ricerca == 'solo_diretti':
            # Ricerca solo voli diretti
            voli_andata = search_direct_flights(origine, destinazione, data_partenza)
            print(f"DEBUG: Ricerca DIRETTI con origine={origine}, destinazione={destinazione}, data={data_partenza}")
            print(f"DEBUG: Trovati {len(voli_andata)} voli diretti")
        else:
            # Ricerca con scali (include anche diretti)
            voli_andata, viaggi_combinati = search_flights_with_stopovers(origine, destinazione, data_partenza)
            print(f"DEBUG: Ricerca CON SCALI con origine={origine}, destinazione={destinazione}, data={data_partenza}")
            print(f"DEBUG: Trovati {len(voli_andata)} voli diretti + {len(viaggi_combinati)} viaggi con scali")
    
    return render_template('search_results.html', 
                         voli_andata=voli_andata,
                         viaggi_combinati=viaggi_combinati,
                         aeroporti=aeroporti,
                         origine=origine,
                         destinazione=destinazione,
                         data_partenza=data_partenza,
                         tipo_ricerca=tipo_ricerca)


def search_direct_flights(origine, destinazione, data_partenza):
    """Cerca voli diretti per la tratta specificata"""
    voli_query = db.session.query(Volo).join(Tratta).filter(
        Tratta.aeroporto_partenza == origine.upper(),
        Tratta.aeroporto_arrivo == destinazione.upper(),
        db.func.date(Volo.partenza) == db.func.cast(data_partenza, db.Date),
        Volo.posti_disponibili > 0
    ).order_by(Volo.partenza)
    
    return voli_query.all()


def search_flights_with_stopovers(origine, destinazione, data_partenza):
    """Cerca voli con scali e diretti per la tratta specificata"""
    from models import ViaggioCombinato
    from datetime import datetime, timedelta
    
    # 1. Prima trova i voli diretti
    voli_diretti = search_direct_flights(origine, destinazione, data_partenza)
    
    # 2. Poi cerca viaggi con 1 scalo
    viaggi_con_scali = []
    
    # Trova tutti i voli che partono dall'origine nella data specificata
    voli_primo_segmento = db.session.query(Volo).join(Tratta).filter(
        Tratta.aeroporto_partenza == origine.upper(),
        db.func.date(Volo.partenza) == db.func.cast(data_partenza, db.Date),
        Volo.posti_disponibili > 0
    ).all()
    
    for volo_primo in voli_primo_segmento:
        # Aeroporto di scalo è la destinazione del primo volo
        aeroporto_scalo = volo_primo.tratta.aeroporto_arrivo
        
        # Non considerare se il primo volo va già alla destinazione finale
        if aeroporto_scalo == destinazione.upper():
            continue
            
        # Trova voli che partono dall'aeroporto di scalo verso la destinazione finale
        # con almeno 2 ore di connessione
        orario_minimo_connessione = volo_primo.arrivo + timedelta(hours=2)
        orario_massimo_connessione = volo_primo.arrivo + timedelta(hours=12)  # Max 12h di attesa
        
        voli_secondo_segmento = db.session.query(Volo).join(Tratta).filter(
            Tratta.aeroporto_partenza == aeroporto_scalo,
            Tratta.aeroporto_arrivo == destinazione.upper(),
            Volo.partenza >= orario_minimo_connessione,
            Volo.partenza <= orario_massimo_connessione,
            Volo.posti_disponibili > 0
        ).order_by(Volo.partenza).limit(3).all()  # Limita a 3 opzioni per scalo
        
        # Crea viaggi combinati validi
        for volo_secondo in voli_secondo_segmento:
            try:
                viaggio_combinato = ViaggioCombinato(
                    voli_segmenti=[volo_primo, volo_secondo],
                    origine=origine.upper(),
                    destinazione=destinazione.upper(),
                    data_partenza=data_partenza
                )
                viaggi_con_scali.append(viaggio_combinato)
            except ValueError as e:
                # Connessione non valida, salta
                print(f"DEBUG: Connessione non valida: {e}")
                continue
    
    # Ordina i viaggi con scali per orario di partenza
    viaggi_con_scali.sort(key=lambda v: v.partenza_totale)
    
    # Limita il numero di risultati per evitare sovraccarico
    viaggi_con_scali = viaggi_con_scali[:10]
    
    return voli_diretti, viaggi_con_scali

@app.route('/api/destinations/<origin_code>')
def get_destinations(origin_code):
    """API per ottenere destinazioni disponibili da un aeroporto di partenza"""
    try:
        # Query per trovare tutti gli aeroporti di destinazione che hanno tratte dall'aeroporto di origine
        destinazioni = db.session.query(Aeroporto).join(
            Tratta, Aeroporto.codice == Tratta.aeroporto_arrivo
        ).filter(
            Tratta.aeroporto_partenza == origin_code.upper()
        ).distinct().order_by(Aeroporto.citta).all()
        
        # Converti in formato JSON
        destinazioni_json = []
        for aeroporto in destinazioni:
            destinazioni_json.append({
                'codice': aeroporto.codice,
                'citta': aeroporto.citta,
                'paese': aeroporto.paese,
                'display': f"{aeroporto.codice} - {aeroporto.citta}, {aeroporto.paese}"
            })
        
        return jsonify({
            'success': True,
            'destinations': destinazioni_json
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/about')
def about():
    """Pagina informazioni"""
    return render_template('about.html')

# ==========================================
# ROUTES AUTENTICAZIONE
# ==========================================

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login per utenti esistenti"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Username e password sono richiesti.', 'error')
            return render_template('login.html')
        
        utente = Utente.query.filter_by(username=username).first()
        
        if utente and check_password_hash(utente.password, password):
            login_user(utente, remember=True)
            flash(f'Benvenuto, {username}!', 'success')
            
            # Redirect in base al tipo utente
            if utente.tipo == 'compagnia':
                return redirect(url_for('dashboard_compagnia'))
            else:
                return redirect(url_for('dashboard_passeggero'))
        else:
            flash('Credenziali non valide.', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Registrazione nuovi utenti"""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        tipo = request.form.get('tipo')
        
        # Validazione base
        if not all([username, email, password, tipo]):
            flash('Tutti i campi sono richiesti.', 'error')
            return render_template('register.html')
        
        if tipo not in ['compagnia', 'passeggero']:
            flash('Tipo utente non valido.', 'error')
            return render_template('register.html')
        
        # Controlla se utente già esistente
        if Utente.query.filter_by(username=username).first():
            flash('Username già esistente.', 'error')
            return render_template('register.html')
        
        if Utente.query.filter_by(email=email).first():
            flash('Email già registrata.', 'error')
            return render_template('register.html')
        
        try:
            # Crea nuovo utente
            nuovo_utente = Utente(
                username=username,
                email=email,
                password=generate_password_hash(password),
                tipo=tipo  # Passiamo direttamente la stringa
            )
            db.session.add(nuovo_utente)
            db.session.flush()  # Per ottenere l'ID
            
            # Crea record specifico in base al tipo
            if tipo == 'compagnia':
                nome_compagnia = request.form.get('nome_compagnia')
                if not nome_compagnia:
                    flash('Nome compagnia richiesto.', 'error')
                    return render_template('register.html')
                
                compagnia = CompagniaAerea(
                    id=nuovo_utente.id,
                    nome_compagnia=nome_compagnia
                )
                db.session.add(compagnia)
                
            else:  # passeggero
                nome = request.form.get('nome')
                cognome = request.form.get('cognome')
                if not all([nome, cognome]):
                    flash('Nome e cognome sono richiesti.', 'error')
                    return render_template('register.html')
                
                passeggero = Passeggero(
                    id=nuovo_utente.id,
                    nome=nome,
                    cognome=cognome
                )
                db.session.add(passeggero)
            
            db.session.commit()
            flash('Registrazione completata! Ora puoi effettuare il login.', 'success')
            return redirect(url_for('login'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Errore durante la registrazione: {str(e)}', 'error')
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    """Logout utente"""
    logout_user()
    flash('Logout effettuato con successo.', 'info')
    return redirect(url_for('home'))

# ==========================================
# DASHBOARD UTENTI
# ==========================================

@app.route('/dashboard/compagnia')
@login_required
def dashboard_compagnia():
    """Dashboard per compagnie aeree"""
    if current_user.tipo != 'compagnia':
        flash('Accesso non autorizzato.', 'error')
        return redirect(url_for('home'))
    
    compagnia = current_user.compagnia
    
    # Statistiche base
    num_voli = db.session.query(Volo).join(Tratta).filter(
        Tratta.compagnia_id == compagnia.id
    ).count()
    
    num_aerei = len(compagnia.aerei)
    num_tratte = len(compagnia.tratte)
    
    # Voli recenti per la dashboard (ultimi 10 voli creati)
    from datetime import datetime
    voli_query = db.session.query(Volo).join(Tratta).filter(
        Tratta.compagnia_id == compagnia.id
    ).order_by(Volo.id.desc()).limit(10)  # Ordina per ID decrescente (ultimi creati)
    
    voli_recenti = voli_query.all()
    
    return render_template('dashboard_compagnia.html',
                         compagnia=compagnia,
                         num_voli=num_voli,
                         num_aerei=num_aerei,
                         num_tratte=num_tratte,
                         voli_recenti=voli_recenti)

@app.route('/dashboard/passeggero')
@login_required
def dashboard_passeggero():
    """Dashboard per passeggeri con filtri per stato prenotazione"""
    if current_user.tipo != 'passeggero':
        flash('Accesso non autorizzato.', 'error')
        return redirect(url_for('home'))
    
    passeggero = current_user.passeggero
    
    # Ottieni il filtro stato dalla query string
    filtro_stato = request.args.get('stato', 'tutte')
    
    # Query base per le prenotazioni del passeggero
    from models import Prenotazione
    prenotazioni_query = Prenotazione.query.filter_by(passeggero_id=passeggero.id)
    
    # Applica il filtro in base allo stato
    if filtro_stato == 'confermate':
        prenotazioni_query = prenotazioni_query.filter_by(stato='confermata')
    elif filtro_stato == 'cancellate':
        prenotazioni_query = prenotazioni_query.filter_by(stato='cancellata')
    # Se 'tutte', non applichiamo filtri aggiuntivi
    
    # Ordina per data di acquisto (più recenti prima)
    prenotazioni = prenotazioni_query.order_by(Prenotazione.data_acquisto.desc()).all()
    
    return render_template('dashboard_passeggero.html',
                         passeggero=passeggero,
                         prenotazioni=prenotazioni,
                         filtro_corrente=filtro_stato)

# ==========================================
# BOOKING/PRENOTAZIONI
# ==========================================

@app.route('/book_multi_flight', methods=['GET', 'POST'])
@login_required
def book_multi_flight():
    """Prenotazione di un viaggio multi-segmento (con scali)"""
    if current_user.tipo != 'passeggero':
        flash('Solo i passeggeri possono prenotare voli.', 'error')
        return redirect(url_for('home'))
    
    # Ottieni gli ID dei voli dal parametro volo_ids (formato: "id1,id2")
    volo_ids_str = request.args.get('volo_ids', '')
    if not volo_ids_str:
        flash('Nessun volo specificato per la prenotazione multi-segmento.', 'error')
        return redirect(url_for('home'))
    
    volo_ids = volo_ids_str.split(',')
    
    try:
        # Verifica che tutti i voli esistano e siano validi per una connessione
        voli_segmenti = []
        for volo_id in volo_ids:
            volo = Volo.query.get(int(volo_id))
            if not volo:
                flash(f'Volo {volo_id} non trovato.', 'error')
                return redirect(url_for('search_flights'))
            voli_segmenti.append(volo)
        
        # Valida la connessione
        from models import ViaggioCombinato
        try:
            viaggio = ViaggioCombinato(
                voli_segmenti=voli_segmenti,
                origine=voli_segmenti[0].tratta.aeroporto_partenza,
                destinazione=voli_segmenti[-1].tratta.aeroporto_arrivo,
                data_partenza=voli_segmenti[0].partenza.date().isoformat()
            )
        except ValueError as e:
            flash(f'Connessione non valida tra i voli: {str(e)}', 'error')
            return redirect(url_for('search_flights'))
        
        if request.method == 'POST':
            return process_multi_booking(viaggio)
        
        return render_template('book_multi_flight.html', viaggio=viaggio)
        
    except Exception as e:
        flash(f'Errore durante il caricamento: {str(e)}', 'error')
        return redirect(url_for('search_flights'))


@app.route('/book_flight/<int:volo_id>', methods=['GET', 'POST'])
@login_required
def book_flight(volo_id):
    """Pagina di selezione classe, posto e extra per la prenotazione"""
    if current_user.tipo != 'passeggero':
        flash('Solo i passeggeri possono prenotare voli.', 'error')
        return redirect(url_for('home'))
    
    try:
        from models import PrezzoVolo, Extra
        
        # Verifica che il volo esista e abbia posti
        volo = Volo.query.get(volo_id)
        if not volo:
            flash('Volo non trovato.', 'error')
            return redirect(url_for('search_flights'))
        
        if volo.posti_disponibili <= 0:
            flash('Volo al completo.', 'error')
            return redirect(url_for('search_flights'))
        
        # Controlla se il passeggero ha già prenotato questo volo
        from models import Biglietto, Prenotazione
        biglietto_esistente = db.session.query(Biglietto).join(Prenotazione).filter(
            Prenotazione.passeggero_id == current_user.id,
            Biglietto.volo_id == int(volo_id)
        ).first()
        
        if biglietto_esistente:
            flash('Hai già prenotato questo volo.', 'warning')
            return redirect(url_for('dashboard_passeggero'))
        
        # Ottieni i prezzi per le diverse classi
        prezzi = PrezzoVolo.query.filter_by(volo_id=volo_id).all()
        prezzi_dict = {prezzo.classe: prezzo.prezzo for prezzo in prezzi}
        
        # Ottieni tutti gli extra disponibili
        extra_disponibili = Extra.query.all()
        
        # Genera mappa posti per questo volo
        posti_aereo = generate_seat_map(volo)
        
        if request.method == 'POST':
            return process_booking(volo_id, volo, prezzi_dict, extra_disponibili)
        
        return render_template('book_flight.html',
                             volo=volo,
                             prezzi=prezzi_dict,
                             extra_disponibili=extra_disponibili,
                             posti_aereo=posti_aereo)
        
    except Exception as e:
        flash(f'Errore durante il caricamento: {str(e)}', 'error')
        return redirect(url_for('search_flights'))


def generate_seat_map(volo):
    """Genera una mappa dei posti per lo specifico volo, includendo disponibilità e classe."""
    from models import Biglietto, Prenotazione

    aereo = volo.aereo
    colonne = ['A', 'B', 'C', 'D', 'E', 'F']  # sedili per fila
    posti_per_fila = len(colonne)

    # (classe, numero di posti)
    classi = [
        ('first', aereo.posti_first),
        ('business', aereo.posti_business),
        ('economy', aereo.posti_economy),
    ]

    # Posti occupati (prenotazioni non cancellate)
    occupati_rows = (
        db.session.query(Biglietto.posto)
        .join(Prenotazione)
        .filter(
            Biglietto.volo_id == volo.id,
            Prenotazione.stato != 'cancellata'
        )
        .all()
    )
    posti_occupati = {row[0] for row in occupati_rows}

    mappa_posti = {}
    fila = 1  # parti da 1, tipico in aereo

    for classe, num_posti in classi:
        if not num_posti or num_posti <= 0:
            continue

        posti_rimasti = num_posti
        while posti_rimasti > 0:
            posti_fila = []
            for lettera in colonne:
                if posti_rimasti == 0:
                    break
                numero_posto = f"{fila}{lettera}"
                posti_fila.append({
                    'numero': numero_posto,
                    'classe': classe,
                    'disponibile': numero_posto not in posti_occupati
                })
                posti_rimasti -= 1

            mappa_posti[fila] = posti_fila
            fila += 1

    return mappa_posti


def process_booking(volo_id, volo, prezzi_dict, extra_disponibili):
    """Processa la prenotazione con classe, posto e extra selezionati, con validazioni e gestione race condition."""
    try:
        from models import Prenotazione, Biglietto, BigliettoExtra, Extra, Prenotazione as Pren
        from datetime import datetime
        
        classe = request.form.get('classe', 'economy')
        posto = request.form.get('posto', '')
        extra_ids = request.form.getlist('extra')  # Lista degli ID extra selezionati
        
        # Verifica che la classe abbia un prezzo
        if classe not in prezzi_dict:
            flash('Classe selezionata non disponibile.', 'error')
            extra_disponibili = Extra.query.all()
            return render_template('book_flight.html',
                                 volo=volo,
                                 prezzi=prezzi_dict,
                                 extra_disponibili=extra_disponibili, 
                                 posti_aereo=generate_seat_map(volo))
        
        # Calcola costo totale
        costo_base = prezzi_dict[classe]
        costo_extra = 0
        
        extra_selezionati = []
        for extra_id in extra_ids:
            try:
                extra = Extra.query.get(int(extra_id))
                if extra:
                    extra_selezionati.append(extra)
                    costo_extra += extra.prezzo
            except ValueError:
                continue
        
        costo_totale = costo_base + costo_extra
        
        # Helper per ottenere la lista dei posti disponibili per classe
        def available_seats_for_class(volo):
            seat_map = generate_seat_map(volo)
            disponibili = []
            for fila in seat_map.values():
                for p in fila:
                    if p['classe'] == classe and p['disponibile']:
                        disponibili.append(p['numero'])
            return disponibili
        
        # Validazione posto/classi/disponibilità
        if posto:
            seat_map = generate_seat_map(volo)
            trovato = None
            for fila in seat_map.values():
                for p in fila:
                    if p['numero'] == posto:
                        trovato = p
                        break
                if trovato:
                    break
            if not trovato:
                flash('Il posto selezionato non esiste per questo volo.', 'error')
                extra_disponibili = Extra.query.all()
                return render_template('book_flight.html', volo=volo, prezzi=prezzi_dict, extra_disponibili=extra_disponibili, posti_aereo=seat_map)
            if trovato['classe'] != classe:
                flash('Il posto selezionato non appartiene alla classe scelta.', 'error')
                extra_disponibili = Extra.query.all()
                return render_template('book_flight.html', volo=volo, prezzi=prezzi_dict, extra_disponibili=extra_disponibili, posti_aereo=seat_map)
            if not trovato['disponibile']:
                flash('Il posto selezionato non è più disponibile.', 'error')
                extra_disponibili = Extra.query.all()
                return render_template('book_flight.html', volo=volo, prezzi=prezzi_dict, extra_disponibili=extra_disponibili, posti_aereo=seat_map)
        else:
            disponibili = available_seats_for_class(volo)
            if not disponibili:
                flash('Nessun posto disponibile per la classe selezionata.', 'error')
                extra_disponibili = Extra.query.all()
                return render_template('book_flight.html',
                                     volo=volo,
                                     prezzi=prezzi_dict,
                                     extra_disponibili=extra_disponibili, 
                                     posti_aereo=generate_seat_map(volo))
            posto = random.choice(disponibili)
        
        # Crea la prenotazione
        nuova_prenotazione = Prenotazione(
            passeggero_id=current_user.id,
            data_acquisto=datetime.now(),
            costo_totale=costo_totale,
            stato='confermata'
        )
        
        db.session.add(nuova_prenotazione)
        db.session.flush()  # Per ottenere l'ID della prenotazione
        
        # Prova a creare il biglietto; in caso di race condition ritenta (solo se posto non era scelto dall'utente)
        max_tentativi = 3 if request.form.get('posto', '') == '' else 1
        tentativo = 0
        nuovo_biglietto = None
        ultimo_errore = None
        while tentativo < max_tentativi:
            try:
                nuovo_biglietto = Biglietto(
                    prenotazione_id=nuova_prenotazione.id,
                    volo_id=int(volo_id),
                    classe=classe,
                    posto=posto
                )
                db.session.add(nuovo_biglietto)
                db.session.flush()
                break  # Inserimento riuscito
            except IntegrityError as ie:
                db.session.rollback()
                # Se il posto è stato preso nel frattempo, scegline un altro solo se non era stato scelto manualmente
                ultimo_errore = ie
                tentativo += 1
                if max_tentativi == 1:
                    flash('Il posto selezionato è appena stato assegnato a qualcun altro. Riprova selezionando un altro posto.', 'warning')
                    # Ricrea la transazione per la prenotazione fallita
                    return render_template('book_flight.html', volo=volo, prezzi=prezzi_dict, extra_disponibili=Extra.query.all(), posti_aereo=generate_seat_map(volo))
                # Ricalcola un nuovo posto disponibile
                disponibili = available_seats_for_class(volo)
                if not disponibili:
                    flash('Nessun posto disponibile per la classe selezionata.', 'error')
                    return render_template('book_flight.html', volo=volo, prezzi=prezzi_dict, extra_disponibili=Extra.query.all(), posti_aereo=generate_seat_map(volo))
                posto = random.choice(disponibili)
                # Ri-aggiungi la prenotazione alla sessione dopo rollback
                db.session.add(nuova_prenotazione)
                db.session.flush()
        
        if nuovo_biglietto is None:
            raise ultimo_errore or Exception('Impossibile creare il biglietto.')
        
        # Aggiungi gli extra al biglietto
        for extra in extra_selezionati:
            biglietto_extra = BigliettoExtra(
                biglietto_id=nuovo_biglietto.id,
                extra_id=extra.id
            )
            db.session.add(biglietto_extra)
        
        # Riduci i posti disponibili
        volo.posti_disponibili = max(0, (volo.posti_disponibili or 0) - 1)
        
        db.session.commit()
        
        # Messaggio di conferma dettagliato
        extra_text = f" + {len(extra_selezionati)} extra" if extra_selezionati else ""
        flash(f'Prenotazione confermata! Volo {volo.tratta.aeroporto_partenza}→{volo.tratta.aeroporto_arrivo} del {volo.partenza.strftime("%d/%m/%Y")} alle {volo.partenza.strftime("%H:%M")}. Classe: {classe.title()}, Posto: {posto}{extra_text}. Totale: €{costo_totale:.0f}', 'success')
        return redirect(url_for('dashboard_passeggero'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Errore durante la prenotazione: {str(e)}', 'error')
        extra_disponibili = Extra.query.all()
        return render_template('book_flight.html',
                             volo=volo,
                             prezzi=prezzi_dict,
                             extra_disponibili=extra_disponibili, 
                             posti_aereo=generate_seat_map(volo))


def process_multi_booking(viaggio):
    """Processa la prenotazione di un viaggio con scali (più voli insieme)"""
    try:
        from models import Prenotazione, Biglietto, BigliettoExtra, Extra, PrezzoVolo
        from datetime import datetime
        
        # Ottieni i dati dal form per ogni segmento
        classi = {}
        posti = {}
        extra_per_segmento = {}
        costo_totale = 0
        
        # Per ogni segmento del viaggio
        for i, volo in enumerate(viaggio.voli_segmenti):
            segmento_id = str(volo.id)
            
            # Classe per questo segmento
            classe = request.form.get(f'classe_{segmento_id}', 'economy')
            classi[segmento_id] = classe
            
            # Posto per questo segmento (opzionale)
            posto = request.form.get(f'posto_{segmento_id}', '')
            posti[segmento_id] = posto
            
            # Extra per questo segmento
            extra_ids = request.form.getlist(f'extra_{segmento_id}')
            extra_per_segmento[segmento_id] = extra_ids
            
            # Calcola il costo per questo segmento
            prezzi = PrezzoVolo.query.filter_by(volo_id=volo.id).all()
            prezzi_dict = {p.classe: p.prezzo for p in prezzi}
            
            if classe not in prezzi_dict:
                flash(f'Classe {classe} non disponibile per il segmento {i+1}.', 'error')
                return render_template('book_multi_flight.html', viaggio=viaggio)
            
            costo_segmento = prezzi_dict[classe]
            
            # Aggiungi costo extra
            for extra_id in extra_ids:
                extra = Extra.query.get(int(extra_id))
                if extra:
                    costo_segmento += extra.prezzo
            
            costo_totale += costo_segmento
            
            # Verifica disponibilità posti
            if volo.posti_disponibili <= 0:
                flash(f'Il segmento {i+1} non ha più posti disponibili.', 'error')
                return render_template('book_multi_flight.html', viaggio=viaggio)
        
        # Inizia la transazione - tutto o niente
        # Crea UNA SOLA prenotazione per tutti i segmenti
        nuova_prenotazione = Prenotazione(
            passeggero_id=current_user.id,
            data_acquisto=datetime.now(),
            costo_totale=costo_totale,
            stato='confermata'
        )
        db.session.add(nuova_prenotazione)
        db.session.flush()
        
        # Crea i biglietti per ogni segmento
        biglietti_creati = []
        for i, volo in enumerate(viaggio.voli_segmenti):
            segmento_id = str(volo.id)
            classe = classi[segmento_id]
            posto_scelto = posti[segmento_id]
            
            # Se non è stato scelto un posto, assegna automaticamente
            if not posto_scelto:
                seat_map = generate_seat_map(volo)
                disponibili = []
                for fila in seat_map.values():
                    for p in fila:
                        if p['classe'] == classe and p['disponibile']:
                            disponibili.append(p['numero'])
                
                if not disponibili:
                    raise Exception(f'Nessun posto disponibile nella classe {classe} per il segmento {i+1}')
                
                posto_scelto = random.choice(disponibili)
            
            # Crea il biglietto
            nuovo_biglietto = Biglietto(
                prenotazione_id=nuova_prenotazione.id,
                volo_id=volo.id,
                classe=classe,
                posto=posto_scelto
            )
            db.session.add(nuovo_biglietto)
            db.session.flush()
            biglietti_creati.append(nuovo_biglietto)
            
            # Aggiungi extra per questo biglietto
            for extra_id in extra_per_segmento[segmento_id]:
                extra = Extra.query.get(int(extra_id))
                if extra:
                    biglietto_extra = BigliettoExtra(
                        biglietto_id=nuovo_biglietto.id,
                        extra_id=extra.id
                    )
                    db.session.add(biglietto_extra)
            
            # Riduci posti disponibili
            volo.posti_disponibili = max(0, volo.posti_disponibili - 1)
        
        # Commit della transazione
        db.session.commit()
        
        # Messaggio di conferma
        dettagli_voli = []
        for i, volo in enumerate(viaggio.voli_segmenti):
            segmento_id = str(volo.id)
            dettagli = f"Segmento {i+1}: {volo.tratta.aeroporto_partenza}→{volo.tratta.aeroporto_arrivo} - Classe: {classi[segmento_id].title()}, Posto: {biglietti_creati[i].posto}"
            dettagli_voli.append(dettagli)
        
        flash(f'Prenotazione viaggio completo confermata! {" | ".join(dettagli_voli)}. Totale: €{costo_totale:.0f}', 'success')
        return redirect(url_for('dashboard_passeggero'))
        
    except IntegrityError as ie:
        db.session.rollback()
        flash('Uno dei posti selezionati è stato appena prenotato da qualcun altro. Riprova.', 'warning')
        return render_template('book_multi_flight.html', viaggio=viaggio)
    except Exception as e:
        db.session.rollback()
        flash(f'Errore durante la prenotazione: {str(e)}', 'error')
        return render_template('book_multi_flight.html', viaggio=viaggio)


@app.route('/passeggero/prenotazione/<int:prenotazione_id>')
@login_required
def dettagli_prenotazione(prenotazione_id):
    """Visualizza dettagli completi di una prenotazione"""
    if current_user.tipo != 'passeggero':
        flash('Accesso non autorizzato.', 'error')
        return redirect(url_for('home'))
    
    try:
        from models import Prenotazione
        
        prenotazione = Prenotazione.query.filter_by(
            id=prenotazione_id,
            passeggero_id=current_user.id
        ).first()
        
        if not prenotazione:
            flash('Prenotazione non trovata.', 'error')
            return redirect(url_for('dashboard_passeggero'))
        
        return render_template('dettagli_prenotazione.html', prenotazione=prenotazione)
        
    except Exception as e:
        flash(f'Errore durante il caricamento: {str(e)}', 'error')
        return redirect(url_for('dashboard_passeggero'))

@app.route('/passeggero/prenotazione/<int:prenotazione_id>/modifica', methods=['GET', 'POST'])
@login_required
def modifica_prenotazione(prenotazione_id):
    """Modifica limitata di una prenotazione (solo alcuni dati)"""
    if current_user.tipo != 'passeggero':
        flash('Accesso non autorizzato.', 'error')
        return redirect(url_for('home'))
    
    try:
        from models import Prenotazione
        
        prenotazione = Prenotazione.query.filter_by(
            id=prenotazione_id,
            passeggero_id=current_user.id
        ).first()
        
        if not prenotazione:
            flash('Prenotazione non trovata.', 'error')
            return redirect(url_for('dashboard_passeggero'))
        
        if prenotazione.stato != 'confermata':
            flash('Puoi modificare solo prenotazioni confermate.', 'error')
            return redirect(url_for('dashboard_passeggero'))
        
        # Verifica se il volo è ancora nel futuro (per ora solo questo controllo)
        from datetime import datetime
        for biglietto in prenotazione.biglietti:
            if biglietto.volo.partenza <= datetime.now():
                flash('Non puoi modificare prenotazioni per voli già partiti.', 'error')
                return redirect(url_for('dashboard_passeggero'))
        
        if request.method == 'POST':
            # Per ora permettiamo solo note o richieste speciali
            note_speciali = request.form.get('note_speciali', '')
            
            # Qui potresti aggiungere un campo note alla tabella Prenotazione
            # Per ora mostriamo solo un messaggio di successo
            flash('Le tue richieste sono state registrate. Ti contatteremo per eventuali modifiche.', 'info')
            return redirect(url_for('dettagli_prenotazione', prenotazione_id=prenotazione_id))
        
        return render_template('modifica_prenotazione.html', prenotazione=prenotazione)
        
    except Exception as e:
        flash(f'Errore durante la modifica: {str(e)}', 'error')
        return redirect(url_for('dashboard_passeggero'))

@app.route('/cancel_booking/<int:prenotazione_id>', methods=['POST'])
@login_required
def cancel_booking(prenotazione_id):
    """Cancella una prenotazione"""
    if current_user.tipo != 'passeggero':
        flash('Accesso non autorizzato.', 'error')
        return redirect(url_for('home'))
    
    try:
        from models import Prenotazione
        
        prenotazione = Prenotazione.query.filter_by(
            id=prenotazione_id,
            passeggero_id=current_user.id
        ).first()
        
        if not prenotazione:
            flash('Prenotazione non trovata.', 'error')
            return redirect(url_for('dashboard_passeggero'))
        
        if prenotazione.stato == 'cancellata':
            flash('Prenotazione già cancellata.', 'warning')
            return redirect(url_for('dashboard_passeggero'))
        
        # Verifica se è possibile cancellare (es: almeno 24h prima del volo)
        from datetime import datetime, timedelta
        for biglietto in prenotazione.biglietti:
            if biglietto.volo.partenza <= datetime.now() + timedelta(hours=24):
                flash('Non puoi cancellare prenotazioni a meno di 24 ore dal volo.', 'error')
                return redirect(url_for('dashboard_passeggero'))
        
        # Aggiorna stato e riaddiziona posti
        prenotazione.stato = 'cancellata'
        for biglietto in prenotazione.biglietti:
            biglietto.volo.posti_disponibili += 1
        
        db.session.commit()
        
        flash('Prenotazione cancellata con successo. I posti sono stati resi disponibili.', 'success')
        return redirect(url_for('dashboard_passeggero'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Errore durante la cancellazione: {str(e)}', 'error')
        return redirect(url_for('dashboard_passeggero'))

@app.route('/passeggero/profilo/cambia-password', methods=['GET', 'POST'])
@login_required
def cambia_password():
    """Cambia password del passeggero"""
    if current_user.tipo != 'passeggero':
        flash('Accesso non autorizzato.', 'error')
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        password_attuale = request.form.get('password_attuale')
        nuova_password = request.form.get('nuova_password')
        conferma_password = request.form.get('conferma_password')
        
        if not all([password_attuale, nuova_password, conferma_password]):
            flash('Tutti i campi sono richiesti.', 'error')
            return render_template('cambia_password.html')
        
        if not check_password_hash(current_user.password, password_attuale):
            flash('Password attuale non corretta.', 'error')
            return render_template('cambia_password.html')
        
        if nuova_password != conferma_password:
            flash('Le nuove password non corrispondono.', 'error')
            return render_template('cambia_password.html')
        
        if len(nuova_password) < 6:
            flash('La password deve avere almeno 6 caratteri.', 'error')
            return render_template('cambia_password.html')
        
        try:
            current_user.password = generate_password_hash(nuova_password)
            db.session.commit()
            flash('Password cambiata con successo!', 'success')
            return redirect(url_for('dashboard_passeggero'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Errore durante il cambio password: {str(e)}', 'error')
    
    return render_template('cambia_password.html')

@app.route('/passeggero/profilo/modifica-dati', methods=['GET', 'POST'])
@login_required
def modifica_dati_profilo():
    """Modifica dati personali del passeggero"""
    if current_user.tipo != 'passeggero':
        flash('Accesso non autorizzato.', 'error')
        return redirect(url_for('home'))
    
    passeggero = current_user.passeggero
    
    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        cognome = request.form.get('cognome', '').strip()
        email = request.form.get('email', '').strip()
        
        if not all([nome, cognome, email]):
            flash('Nome, cognome ed email sono richiesti.', 'error')
            return render_template('modifica_dati_profilo.html', passeggero=passeggero)
        
        # Verifica che l'email non sia già usata da altri
        if email != current_user.email:
            existing_user = Utente.query.filter_by(email=email).first()
            if existing_user:
                flash('Email già utilizzata da un altro utente.', 'error')
                return render_template('modifica_dati_profilo.html', passeggero=passeggero)
        
        try:
            # Aggiorna dati
            passeggero.nome = nome
            passeggero.cognome = cognome
            current_user.email = email
            
            db.session.commit()
            flash('Dati profilo aggiornati con successo!', 'success')
            return redirect(url_for('dashboard_passeggero'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Errore durante l\'aggiornamento: {str(e)}', 'error')
    
    return render_template('modifica_dati_profilo.html', passeggero=passeggero)

# ==========================================
# GESTIONE COMPAGNIA AEREA
# ==========================================

@app.route('/compagnia/aerei')
@login_required
def gestione_aerei():
    """Visualizza lista aerei della compagnia"""
    if current_user.tipo != 'compagnia':
        flash('Accesso non autorizzato.', 'error')
        return redirect(url_for('home'))
    
    compagnia = current_user.compagnia
    return render_template('gestione_aerei.html', compagnia=compagnia)

@app.route('/compagnia/aerei/nuovo', methods=['GET', 'POST'])
@login_required
def nuovo_aereo():
    """Aggiungi nuovo aereo alla flotta"""
    if current_user.tipo != 'compagnia':
        flash('Accesso non autorizzato.', 'error')
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        modello = request.form.get('modello')
        posti_economy = int(request.form.get('posti_economy', 0))
        posti_business = int(request.form.get('posti_business', 0))
        posti_first = int(request.form.get('posti_first', 0))
        
        if not modello:
            flash('Il modello dell\'aereo è richiesto.', 'error')
            return render_template('form_aereo.html')
        
        posti_totali = posti_economy + posti_business + posti_first
        
        if posti_totali <= 0:
            flash('Deve esserci almeno un posto.', 'error')
            return render_template('form_aereo.html')
        
        try:
            from models import Aereo
            nuovo_aereo = Aereo(
                modello=modello,
                posti_totali=posti_totali,
                posti_economy=posti_economy,
                posti_business=posti_business,
                posti_first=posti_first,
                compagnia_id=current_user.id
            )
            
            db.session.add(nuovo_aereo)
            db.session.commit()
            
            flash(f'Aereo {modello} aggiunto con successo alla flotta!', 'success')
            return redirect(url_for('dashboard_compagnia'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Errore durante l\'aggiunta dell\'aereo: {str(e)}', 'error')
    
    return render_template('form_aereo.html')

@app.route('/compagnia/aerei/<int:aereo_id>/modifica', methods=['GET', 'POST'])
@login_required
def modifica_aereo(aereo_id):
    """Modifica aereo esistente"""
    if current_user.tipo != 'compagnia':
        flash('Accesso non autorizzato.', 'error')
        return redirect(url_for('home'))
    
    from models import Aereo
    aereo = Aereo.query.filter_by(id=aereo_id, compagnia_id=current_user.id).first()
    
    if not aereo:
        flash('Aereo non trovato.', 'error')
        return redirect(url_for('dashboard_compagnia'))
    
    if request.method == 'POST':
        aereo.modello = request.form.get('modello')
        aereo.posti_economy = int(request.form.get('posti_economy', 0))
        aereo.posti_business = int(request.form.get('posti_business', 0))
        aereo.posti_first = int(request.form.get('posti_first', 0))
        aereo.posti_totali = aereo.posti_economy + aereo.posti_business + aereo.posti_first
        
        try:
            db.session.commit()
            flash('Aereo modificato con successo!', 'success')
            return redirect(url_for('dashboard_compagnia'))
        except Exception as e:
            db.session.rollback()
            flash(f'Errore durante la modifica: {str(e)}', 'error')
    
    return render_template('form_aereo.html', aereo=aereo)

@app.route('/compagnia/aerei/<int:aereo_id>/elimina', methods=['POST'])
@login_required
def elimina_aereo(aereo_id):
    """Elimina aereo dalla flotta"""
    if current_user.tipo != 'compagnia':
        flash('Accesso non autorizzato.', 'error')
        return redirect(url_for('home'))
    
    try:
        from models import Aereo
        aereo = Aereo.query.filter_by(id=aereo_id, compagnia_id=current_user.id).first()
        
        if not aereo:
            flash('Aereo non trovato.', 'error')
            return redirect(url_for('dashboard_compagnia'))
        
        # Controlla se l'aereo ha voli attivi
        if aereo.voli:
            flash('Impossibile eliminare l\'aereo: ha voli programmati.', 'error')
            return redirect(url_for('dashboard_compagnia'))
        
        db.session.delete(aereo)
        db.session.commit()
        flash('Aereo eliminato con successo dalla flotta.', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Errore durante l\'eliminazione: {str(e)}', 'error')
    
    return redirect(url_for('dashboard_compagnia'))

@app.route('/compagnia/tratte/nuova', methods=['GET', 'POST'])
@login_required
def nuova_tratta():
    """Aggiungi nuova tratta"""
    if current_user.tipo != 'compagnia':
        flash('Accesso non autorizzato.', 'error')
        return redirect(url_for('home'))
    
    aeroporti = Aeroporto.query.order_by(Aeroporto.citta).all()
    
    if request.method == 'POST':
        aeroporto_partenza = request.form.get('aeroporto_partenza')
        aeroporto_arrivo = request.form.get('aeroporto_arrivo')
        
        if not aeroporto_partenza or not aeroporto_arrivo:
            flash('Aeroporto di partenza e arrivo sono richiesti.', 'error')
            return render_template('form_tratta.html', aeroporti=aeroporti)
        
        if aeroporto_partenza == aeroporto_arrivo:
            flash('Aeroporto di partenza e arrivo devono essere diversi.', 'error')
            return render_template('form_tratta.html', aeroporti=aeroporti)
        
        # Controlla se la tratta esiste già
        tratta_esistente = Tratta.query.filter_by(
            aeroporto_partenza=aeroporto_partenza.upper(),
            aeroporto_arrivo=aeroporto_arrivo.upper(),
            compagnia_id=current_user.id
        ).first()
        
        if tratta_esistente:
            flash('Questa tratta esiste già per la tua compagnia.', 'warning')
            return render_template('form_tratta.html', aeroporti=aeroporti)
        
        try:
            nuova_tratta = Tratta(
                aeroporto_partenza=aeroporto_partenza.upper(),
                aeroporto_arrivo=aeroporto_arrivo.upper(),
                compagnia_id=current_user.id
            )
            
            db.session.add(nuova_tratta)
            db.session.commit()
            
            flash(f'Tratta {aeroporto_partenza} → {aeroporto_arrivo} aggiunta con successo!', 'success')
            return redirect(url_for('dashboard_compagnia'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Errore durante l\'aggiunta della tratta: {str(e)}', 'error')
    
    return render_template('form_tratta.html', aeroporti=aeroporti)

@app.route('/compagnia/tratte/<int:tratta_id>/elimina', methods=['POST'])
@login_required
def elimina_tratta(tratta_id):
    """Elimina tratta"""
    if current_user.tipo != 'compagnia':
        flash('Accesso non autorizzato.', 'error')
        return redirect(url_for('home'))
    
    try:
        tratta = Tratta.query.filter_by(id=tratta_id, compagnia_id=current_user.id).first()
        
        if not tratta:
            flash('Tratta non trovata.', 'error')
            return redirect(url_for('dashboard_compagnia'))
        
        # Controlla se ci sono voli programmati
        if tratta.voli:
            flash('Impossibile eliminare la tratta: ha voli programmati.', 'error')
            return redirect(url_for('dashboard_compagnia'))
        
        db.session.delete(tratta)
        db.session.commit()
        flash('Tratta eliminata con successo.', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Errore durante l\'eliminazione: {str(e)}', 'error')
    
    return redirect(url_for('dashboard_compagnia'))

@app.route('/compagnia/voli')
@login_required
def gestione_voli():
    """Visualizza e gestisce tutti i voli della compagnia con filtri"""
    if current_user.tipo != 'compagnia':
        flash('Accesso non autorizzato.', 'error')
        return redirect(url_for('home'))
    
    compagnia = current_user.compagnia
    
    # Query base per i voli della compagnia
    voli_query = db.session.query(Volo).join(Tratta).filter(
        Tratta.compagnia_id == compagnia.id
    )
    
    # Parametri di filtro
    filtro_tratta = request.args.get('tratta', '')
    filtro_aereo = request.args.get('aereo', '')
    data_da = request.args.get('data_da', '')
    data_a = request.args.get('data_a', '')
    stato_volo = request.args.get('stato', '')
    
    # Applicazione filtri
    if filtro_tratta:
        voli_query = voli_query.filter(Volo.tratta_id == int(filtro_tratta))
    
    if filtro_aereo:
        voli_query = voli_query.filter(Volo.aereo_id == int(filtro_aereo))
    
    if data_da:
        try:
            from datetime import datetime
            data_da_dt = datetime.strptime(data_da, '%Y-%m-%d')
            voli_query = voli_query.filter(db.func.date(Volo.partenza) >= data_da_dt.date())
        except ValueError:
            flash('Formato data non valido per "Da"', 'warning')
    
    if data_a:
        try:
            from datetime import datetime
            data_a_dt = datetime.strptime(data_a, '%Y-%m-%d')
            voli_query = voli_query.filter(db.func.date(Volo.partenza) <= data_a_dt.date())
        except ValueError:
            flash('Formato data non valido per "A"', 'warning')
    
    # Filtro per stato (basato sui posti disponibili e data)
    from datetime import datetime
    ora_corrente = datetime.now()
    
    if stato_volo == 'passati':
        voli_query = voli_query.filter(Volo.arrivo < ora_corrente)
    elif stato_volo == 'futuri':
        voli_query = voli_query.filter(Volo.partenza > ora_corrente)
    elif stato_volo == 'pieni':
        voli_query = voli_query.filter(Volo.posti_disponibili == 0)
    elif stato_volo == 'disponibili':
        voli_query = voli_query.filter(
            Volo.posti_disponibili > 0,
            Volo.partenza > ora_corrente
        )
    
    # Ordinamento e paginazione
    ordinamento = request.args.get('ordina', 'partenza_desc')
    
    if ordinamento == 'partenza_asc':
        voli_query = voli_query.order_by(Volo.partenza.asc())
    elif ordinamento == 'partenza_desc':
        voli_query = voli_query.order_by(Volo.partenza.desc())
    elif ordinamento == 'tratta':
        voli_query = voli_query.order_by(Tratta.aeroporto_partenza, Tratta.aeroporto_arrivo)
    elif ordinamento == 'posti':
        voli_query = voli_query.order_by(Volo.posti_disponibili.desc())
    
    voli = voli_query.all()
    
    # Statistiche per i filtri correnti
    totale_voli = len(voli)
    voli_futuri = len([v for v in voli if v.partenza > ora_corrente])
    voli_pieni = len([v for v in voli if v.posti_disponibili == 0])
    
    return render_template('gestione_voli.html',
                         voli=voli,
                         compagnia=compagnia,
                         filtro_tratta=filtro_tratta,
                         filtro_aereo=filtro_aereo,
                         data_da=data_da,
                         data_a=data_a,
                         stato_volo=stato_volo,
                         ordinamento=ordinamento,
                         totale_voli=totale_voli,
                         voli_futuri=voli_futuri,
                         voli_pieni=voli_pieni,
                         ora_corrente=ora_corrente)

@app.route('/compagnia/voli/nuovo', methods=['GET', 'POST'])
@login_required
def nuovo_volo():
    """Aggiungi nuovo volo"""
    if current_user.tipo != 'compagnia':
        flash('Accesso non autorizzato.', 'error')
        return redirect(url_for('home'))
    
    compagnia = current_user.compagnia
    
    if request.method == 'POST':
        tratta_id = request.form.get('tratta_id')
        aereo_id = request.form.get('aereo_id')
        data_partenza = request.form.get('data_partenza')
        ora_partenza = request.form.get('ora_partenza')
        data_arrivo = request.form.get('data_arrivo')
        ora_arrivo = request.form.get('ora_arrivo')
        prezzo_economy = request.form.get('prezzo_economy')
        prezzo_business = request.form.get('prezzo_business')
        prezzo_first = request.form.get('prezzo_first')
        
        try:
            from datetime import datetime
            partenza_dt = datetime.strptime(f'{data_partenza} {ora_partenza}', '%Y-%m-%d %H:%M')
            arrivo_dt = datetime.strptime(f'{data_arrivo} {ora_arrivo}', '%Y-%m-%d %H:%M')
            
            if partenza_dt >= arrivo_dt:
                flash('La data di arrivo deve essere successiva alla partenza.', 'error')
                return render_template('form_volo.html', tratte=compagnia.tratte, aerei=compagnia.aerei)
            
            # Verifica che la tratta appartenga alla compagnia
            tratta = Tratta.query.filter_by(id=tratta_id, compagnia_id=current_user.id).first()
            if not tratta:
                flash('Tratta non valida.', 'error')
                return render_template('form_volo.html', tratte=compagnia.tratte, aerei=compagnia.aerei)
            
            # Verifica che l'aereo appartenga alla compagnia
            from models import Aereo
            aereo = Aereo.query.filter_by(id=aereo_id, compagnia_id=current_user.id).first()
            if not aereo:
                flash('Aereo non valido.', 'error')
                return render_template('form_volo.html', tratte=compagnia.tratte, aerei=compagnia.aerei)
            
            nuovo_volo = Volo(
                tratta_id=tratta_id,
                aereo_id=aereo_id,
                partenza=partenza_dt,
                arrivo=arrivo_dt,
                posti_disponibili=aereo.posti_totali
            )
            
            db.session.add(nuovo_volo)
            db.session.flush()  # Per ottenere l'ID
            
            # Aggiungi prezzi
            from models import PrezzoVolo
            if prezzo_economy:
                prezzo_eco = PrezzoVolo(volo_id=nuovo_volo.id, classe='economy', prezzo=float(prezzo_economy))
                db.session.add(prezzo_eco)
            
            if prezzo_business:
                prezzo_bus = PrezzoVolo(volo_id=nuovo_volo.id, classe='business', prezzo=float(prezzo_business))
                db.session.add(prezzo_bus)
            
            if prezzo_first:
                prezzo_fir = PrezzoVolo(volo_id=nuovo_volo.id, classe='first', prezzo=float(prezzo_first))
                db.session.add(prezzo_fir)
            
            db.session.commit()
            
            flash(f'Volo {tratta.aeroporto_partenza}→{tratta.aeroporto_arrivo} del {partenza_dt.strftime("%d/%m/%Y %H:%M")} aggiunto con successo!', 'success')
            return redirect(url_for('dashboard_compagnia'))
            
        except ValueError:
            flash('Formato data/ora non valido.', 'error')
        except Exception as e:
            db.session.rollback()
            flash(f'Errore durante l\'aggiunta del volo: {str(e)}', 'error')
    
    return render_template('form_volo.html', tratte=compagnia.tratte, aerei=compagnia.aerei)

@app.route('/compagnia/voli/<int:volo_id>/modifica', methods=['GET', 'POST'])
@login_required
def modifica_volo(volo_id):
    """Modifica volo esistente"""
    if current_user.tipo != 'compagnia':
        flash('Accesso non autorizzato.', 'error')
        return redirect(url_for('home'))
    
    compagnia = current_user.compagnia
    
    # Ottieni il volo da modificare
    volo = db.session.query(Volo).join(Tratta).filter(
        Volo.id == volo_id,
        Tratta.compagnia_id == current_user.id
    ).first()
    
    if not volo:
        flash('Volo non trovato.', 'error')
        return redirect(url_for('dashboard_compagnia'))
    
    if request.method == 'POST':
        try:
            data_partenza = request.form.get('data_partenza')
            ora_partenza = request.form.get('ora_partenza') 
            data_arrivo = request.form.get('data_arrivo')
            ora_arrivo = request.form.get('ora_arrivo')
            
            from datetime import datetime
            partenza_dt = datetime.strptime(f'{data_partenza} {ora_partenza}', '%Y-%m-%d %H:%M')
            arrivo_dt = datetime.strptime(f'{data_arrivo} {ora_arrivo}', '%Y-%m-%d %H:%M')
            
            if partenza_dt >= arrivo_dt:
                flash('La data di arrivo deve essere successiva alla partenza.', 'error')
                return render_template('form_volo.html', volo=volo, tratte=compagnia.tratte, aerei=compagnia.aerei, modifica=True)
            
            # Aggiorna il volo
            volo.partenza = partenza_dt
            volo.arrivo = arrivo_dt
            
            db.session.commit()
            flash('Volo modificato con successo!', 'success')
            return redirect(url_for('dashboard_compagnia'))
            
        except ValueError:
            flash('Formato data/ora non valido.', 'error')
        except Exception as e:
            db.session.rollback()
            flash(f'Errore durante la modifica: {str(e)}', 'error')
    
    return render_template('form_volo.html', volo=volo, tratte=compagnia.tratte, aerei=compagnia.aerei, modifica=True)

@app.route('/compagnia/voli/<int:volo_id>/elimina', methods=['POST'])
@login_required
def elimina_volo(volo_id):
    """Elimina volo"""
    if current_user.tipo != 'compagnia':
        flash('Accesso non autorizzato.', 'error')
        return redirect(url_for('home'))
    
    try:
        volo = db.session.query(Volo).join(Tratta).filter(
            Volo.id == volo_id,
            Tratta.compagnia_id == current_user.id
        ).first()
        
        if not volo:
            flash('Volo non trovato.', 'error')
            return redirect(url_for('dashboard_compagnia'))
        
        # Controlla se ci sono prenotazioni attive
        from models import Biglietto, Prenotazione
        prenotazioni_attive = db.session.query(Biglietto).join(Prenotazione).filter(
            Biglietto.volo_id == volo_id,
            Prenotazione.stato == 'confermata'
        ).count()
        
        if prenotazioni_attive > 0:
            flash('Impossibile eliminare il volo: ci sono prenotazioni attive.', 'error')
            return redirect(url_for('dashboard_compagnia'))
        
        db.session.delete(volo)
        db.session.commit()
        flash('Volo eliminato con successo.', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Errore durante l\'eliminazione: {str(e)}', 'error')
    
    return redirect(url_for('dashboard_compagnia'))

# ==========================================
# ERROR HANDLERS
# ==========================================

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.route('/api/voli/<int:volo_id>/seatmap')
def api_seatmap(volo_id):
    """Endpoint API per ottenere la mappa dei posti di un volo in formato JSON."""
    try:
        volo = Volo.query.get(volo_id)
        if not volo:
            return jsonify({'success': False, 'error': 'Volo non trovato.'}), 404
        seat_map = generate_seat_map(volo)
        # Convertiamo le chiavi (righe) in stringhe per JSON coerente
        seat_map_json = {str(riga): posti for riga, posti in seat_map.items()}
        return jsonify({'success': True, 'seat_map': seat_map_json})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

# ==========================================
# CONTEXT PROCESSORS (per variabili globali nei template)
# ==========================================

@app.context_processor
def inject_user():
    return dict(current_user=current_user)

# ==========================================
# MAIN
# ==========================================

if __name__ == '__main__':
    with app.app_context():
        # Crea le tabelle se non esistono (solo in sviluppo)
        # In produzione usa Flask-Migrate
        db.create_all()
    
    app.run(debug=True, port=5001, host='127.0.0.1')
