import os
import random
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
from config import config
from models import *
from datetime import datetime, timedelta

"""Funzione hepler per la creazione e configurazione dell'applicazione flask"""
def create_app(config_name=None, config_overrides=None):

    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'default')
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    if config_overrides:
        app.config.update(config_overrides)

    db.init_app(app)
    
    """Configuro Flask-Login"""
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    login_manager.login_message = 'Devi effettuare il login per accedere a questa pagina.'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        return Utente.query.get(int(user_id))
    
    return app

"""Creo l'applicazione"""
app = create_app()


"""
Home: pagina che permette di cercare i voli da anonimo o da loggati
mostra le destinazioni piu' popolari:
conto tutti i biglitti che hanno la stessa destinazione d'arrivo, la prenotazione e' confermata e mostro le informazioni
"""

@app.route('/')
def home():
    aeroporti = Aeroporto.query.order_by(Aeroporto.citta).all()
    
    destinazioni_popolari = db.session.query(
        Tratta.aeroporto_arrivo,
        func.count(Biglietto.id).label('num_prenotazioni')
    ).join(
        Volo, Tratta.id == Volo.tratta_id
    ).join(
        Biglietto, Volo.id == Biglietto.volo_id
    ).join(
        Prenotazione, Biglietto.prenotazione_id == Prenotazione.id
    ).filter(
        Prenotazione.stato == 'confermata'  # Solo prenotazioni confermate
    ).group_by(
        Tratta.aeroporto_arrivo
    ).order_by(
        func.count(Biglietto.id).desc()
    ).limit(3).all()

    destinazioni_con_dettagli = []
    for dest_code, num_prenotazioni in destinazioni_popolari:
        aeroporto = Aeroporto.query.filter_by(codice=dest_code).first()
        if aeroporto:
            destinazioni_con_dettagli.append({
                'codice': dest_code,
                'citta': aeroporto.citta,
                'paese': aeroporto.paese,
                'num_prenotazioni': num_prenotazioni
            })
    
    return render_template('home.html', 
                         aeroporti=aeroporti,
                         destinazioni_popolari=destinazioni_con_dettagli)


"""
Search_results: pagina che mostra i risultati della ricerca fatti dalla homepage
la ricerca dei voli chiede areoporto di partenza, arrivo, data, tipo di ricerca (con scali o no)
sort_flights(): le ricerche potranno essere ordinate per prezzo, orario di partenza e durata del volo
sort_combined_trips(): stessa cosa ma controlla i voli che hanno uno scalo
"""

@app.route('/search')
def search_flights():

    origine = request.args.get('origine', '')
    destinazione = request.args.get('destinazione', '')
    data_partenza = request.args.get('data_partenza', '')
    tipo_ricerca = request.args.get('tipo_ricerca', 'con_scali')
    sort_by = request.args.get('sort_by', 'orario')  # orario, prezzo, durata
    sort_order = request.args.get('sort_order', 'asc')  # asc, desc
    
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
        
        # Applica ordinamento ai risultati
        voli_andata = sort_flights(voli_andata, sort_by, sort_order)
        viaggi_combinati = sort_combined_trips(viaggi_combinati, sort_by, sort_order)
    
    return render_template('search_results.html', 
                         voli_andata=voli_andata,
                         viaggi_combinati=viaggi_combinati,
                         aeroporti=aeroporti,
                         origine=origine,
                         destinazione=destinazione,
                         data_partenza=data_partenza,
                         tipo_ricerca=tipo_ricerca,
                         sort_by=sort_by,
                         sort_order=sort_order)


def sort_flights(voli, sort_by, sort_order):
    if not voli:
        return voli
    
    reverse = (sort_order == 'desc')
    
    if sort_by == 'prezzo':
        # Funzione che mi restituisce il prezzo piu' basso tra le classi di un volo
        def get_min_price(volo):
            if not volo.prezzi:
                return float('inf')  # Metti alla fine i voli senza prezzi
            return min(prezzo.prezzo for prezzo in volo.prezzi)
        # restituisco la lista dei voli ordinati per prezzo
        return sorted(voli, key=get_min_price, reverse=reverse)
    
    elif sort_by == 'durata':
        # Ordina per durata del volo
        def get_durata(volo):
            return (volo.arrivo - volo.partenza).total_seconds()
        
        return sorted(voli, key=get_durata, reverse=reverse)
    
    else:
        # Default: ordina per orario di partenza
        return sorted(voli, key=lambda v: v.partenza, reverse=reverse)


def sort_combined_trips(viaggi, sort_by, sort_order):
    if not viaggi:
        return viaggi
    
    reverse = (sort_order == 'desc')
    
    if sort_by == 'prezzo':
        # Ordina per somma dei prezzi minimi di tutti i viaggi
        def get_total_min_price(viaggio):
            total = 0
            for volo in viaggio.voli_segmenti:
                if volo.prezzi:
                    total += min(prezzo.prezzo for prezzo in volo.prezzi)
                else:
                    return float('inf')  # Metti alla fine i voli senza prezzi
            return total
        
        return sorted(viaggi, key=get_total_min_price, reverse=reverse)
    
    elif sort_by == 'durata':
        # Ordina per durata totale del viaggio
        def get_durata_totale(viaggio):
            return viaggio.durata_totale.total_seconds()
        
        return sorted(viaggi, key=get_durata_totale, reverse=reverse)
    
    else:
        # Default: ordina per orario di partenza del primo segmento
        return sorted(viaggi, key=lambda v: v.partenza_totale, reverse=reverse)


def search_direct_flights(origine, destinazione, data_partenza):
    voli_query = db.session.query(Volo).join(Tratta).filter(
        Tratta.aeroporto_partenza == origine.upper(),
        Tratta.aeroporto_arrivo == destinazione.upper(),
        db.func.date(Volo.partenza) == db.func.cast(data_partenza, db.Date),
        Volo.posti_disponibili > 0,
        Volo.partenza > datetime.now()
    ).order_by(Volo.partenza)
    
    return voli_query.all()


def search_flights_with_stopovers(origine, destinazione, data_partenza):
    # Prima trovo i voli diretti
    voli_diretti = search_direct_flights(origine, destinazione, data_partenza)
    
    # Poi cerca viaggi con 1 scalo
    viaggi_con_scali = []
    
    # Trova tutti i voli che partono dall'origine nella data specificata
    voli_primo_segmento = db.session.query(Volo).join(Tratta).filter(
        Tratta.aeroporto_partenza == origine.upper(),
        db.func.date(Volo.partenza) == db.func.cast(data_partenza, db.Date),
        Volo.posti_disponibili > 0,
        Volo.partenza > datetime.now()
    ).all()
    
    for volo_primo in voli_primo_segmento:
        # Aeroporto di scalo è la destinazione del primo volo
        aeroporto_scalo = volo_primo.tratta.aeroporto_arrivo
        
        # Non considerare se il primo volo va già alla destinazione finale perche gia all'interno di voli diretti
        if aeroporto_scalo == destinazione.upper():
            continue
            
        # Trovo voli che partono dall'aeroporto di scalo verso la destinazione finale con almeno 2 ore di connessione
        orario_minimo_connessione = volo_primo.arrivo + timedelta(hours=2)
        orario_massimo_connessione = volo_primo.arrivo + timedelta(hours=12)  # Max 12h di attesa
        
        voli_secondo_segmento = db.session.query(Volo).join(Tratta).filter(
            Tratta.aeroporto_partenza == aeroporto_scalo,
            Tratta.aeroporto_arrivo == destinazione.upper(),
            Volo.partenza >= orario_minimo_connessione,
            Volo.partenza <= orario_massimo_connessione,
            Volo.posti_disponibili > 0
        ).order_by(Volo.partenza).limit(3).all()  # Limita a 3 opzioni per scalo
        
        # Creo viaggi combinati validi
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
                continue
    
    # Ordino i viaggi con scali per orario di partenza (default)
    viaggi_con_scali.sort(key=lambda v: v.partenza_totale)
    
    # Limito il numero di risultati per evitare sovraccarico
    viaggi_con_scali = viaggi_con_scali[:10]
    
    return voli_diretti, viaggi_con_scali

"""
login: pagina da cui effettuare il login
richiede username e password come input
uso la libreria werkzeug.security con check_password_hash per controllare che l'hash della password inserita sia uguale all'hash nel database
se l'utente e' una compagnia, viene reindirizzato alla dashboard della compagnia
se l'utente e' un passeggero, viene reindirizzato alla dashboard del passeggero
"""

@app.route('/login', methods=['GET', 'POST'])
def login():
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

"""
register: pagina da cui registrarsi al sito
richiede username, email password e il tipo di utente
tenta la registrazione dell'utente, se dovesse fallire fa il rollback del database e da una notifica di errore
se dovesse andare a buon fine la registrazione, l'utente viene reindirizzato alla pagina del login
l'hash della password lo facciamo tramite generate_password_hash della libreria werkzeug.security
"""

@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        tipo = request.form.get('tipo')
        
        # Validazioni
        if not all([username, email, password, tipo]):
            flash('Tutti i campi sono richiesti.', 'error')
            return render_template('register.html')
        
        if tipo not in ['compagnia', 'passeggero']:
            flash('Tipo utente non valido.', 'error')
            return render_template('register.html')
        
        # Controllo se l'utente esiste gia
        if Utente.query.filter_by(username=username).first():
            flash('Username già esistente.', 'error')
            return render_template('register.html')
        
        if Utente.query.filter_by(email=email).first():
            flash('Email già registrata.', 'error')
            return render_template('register.html')
        
        try:
            # Creo nuovo utente
            nuovo_utente = Utente(
                username=username,
                email=email,
                password=generate_password_hash(password),
                tipo=tipo
            )
            db.session.add(nuovo_utente)
            db.session.flush()
            
            # Creo record in base al tipo
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
                
            else:
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

"""
logout: effettua il logout
"""

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logout effettuato con successo.', 'info')
    return redirect(url_for('home'))

"""
dashboard_compagnia: pagina che permette all'utente compagnia di visualizzare:
calcola_ricavi_totali_compagnia(compagnia_id): il proprio ricavo totale facendo la somma del costo totale delle prenotazioni effettuate nei voli apparteneni alla compagnia
le tratte
gli aerei (e le info sull'aereo)
i voli (e le info sul volo)
dalla dashboard si puo' andare alle pagnine di inserimento delle tratte, degli aerei e dei voli
"""

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
    
    # Calcola i ricavi totali della compagnia
    ricavi_totali = calcola_ricavi_totali_compagnia(compagnia.id)
    
    return render_template('dashboard_compagnia.html',
                         compagnia=compagnia,
                         num_voli=num_voli,
                         num_aerei=num_aerei,
                         num_tratte=num_tratte,
                         voli_recenti=voli_recenti,
                         ricavi_totali=ricavi_totali)


def calcola_ricavi_totali_compagnia(compagnia_id):

    # Somma i costi totali delle prenotazioni confermate
    # per i voli che appartengono alle tratte della compagnia
    ricavi = db.session.query(
        func.sum(Prenotazione.costo_totale)
    ).join(
        Biglietto, Prenotazione.id == Biglietto.prenotazione_id
    ).join(
        Volo, Biglietto.volo_id == Volo.id
    ).join(
        Tratta, Volo.tratta_id == Tratta.id
    ).filter(
        Tratta.compagnia_id == compagnia_id,
        Prenotazione.stato == 'confermata'
    ).scalar()

    return float(ricavi) if ricavi else 0.0

"""
dashboard_passeggero: pagina che permette all'utente passeggero di visualizzare le prenotazione effetuate
da questa pagina si possono cancellare le prenotazione (solo se il volo e' a piu' di 24 ore di distanza dalla cancellazione)
e accedere alla pagina dei dettagli della prenotazione
le prenotazioni si possono filtrare per cancellate e confermate
"""

@app.route('/dashboard/passeggero')
@login_required
def dashboard_passeggero():
    if current_user.tipo != 'passeggero':
        flash('Accesso non autorizzato.', 'error')
        return redirect(url_for('home'))
    
    passeggero = current_user.passeggero
    
    # Ottiengo il filtro dello stato delle prenotazioni
    filtro_stato = request.args.get('stato', 'tutte')
    
    # Query base per le prenotazioni del passeggero
    prenotazioni_query = Prenotazione.query.filter_by(passeggero_id=passeggero.id)
    
    # Applico il filtro
    if filtro_stato == 'confermate':
        prenotazioni_query = prenotazioni_query.filter_by(stato='confermata')
    elif filtro_stato == 'cancellate':
        prenotazioni_query = prenotazioni_query.filter_by(stato='cancellata')

    # Ordina per data di acquisto
    prenotazioni = prenotazioni_query.order_by(Prenotazione.data_acquisto.desc()).all()
    
    return render_template('dashboard_passeggero.html',
                         passeggero=passeggero,
                         prenotazioni=prenotazioni,
                         filtro_corrente=filtro_stato)

"""
book_flight: pagina da cui prenotare il volo
solo gli utenti passeggero possono accederci
Verifica che il passeggero non abbia gia prenotato questo volo e che il volo esista e abbia posti
generate_seat_map(): funzione che restituisce una mappa dei posti del volo, la crea in base all'aereo e i posti disponibili
process_booking(): funzione principale per la prenotazione del volo
se la prenotazione va a buon fine, porta l'utente alla dashboard passeggero
"""

@app.route('/book_flight/<int:volo_id>', methods=['GET', 'POST'])
@login_required
def book_flight(volo_id):
    if current_user.tipo != 'passeggero':
        flash('Solo i passeggeri possono prenotare voli.', 'error')
        return redirect(url_for('home'))
    # Verifiche
    try:
        volo = Volo.query.get(volo_id)
        if not volo:
            flash('Volo non trovato.', 'error')
            return redirect(url_for('search_flights'))
        
        if volo.posti_disponibili <= 0:
            flash('Volo al completo.', 'error')
            return redirect(url_for('search_flights'))
        
        # Controllo se il passeggero ha già prenotato questo volo
        biglietto_esistente = db.session.query(Biglietto).join(Prenotazione).filter(
            Prenotazione.passeggero_id == current_user.id,
            Biglietto.volo_id == int(volo_id)
        ).first()
        
        if biglietto_esistente:
            flash('Hai già prenotato questo volo.', 'warning')
            return redirect(url_for('dashboard_passeggero'))
        
        # Ottiengo i prezzi
        prezzi = PrezzoVolo.query.filter_by(volo_id=volo_id).all()
        prezzi_dict = {prezzo.classe: prezzo.prezzo for prezzo in prezzi}
        
        # Ottiengo gli extra disponibili
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

    aereo = volo.aereo
    colonne = ['A', 'B', 'C', 'D', 'E', 'F']  # sedili per fila
    posti_per_fila = len(colonne)

    classi = [
        ('first', aereo.posti_first),
        ('business', aereo.posti_business),
        ('economy', aereo.posti_economy),
    ]

    # Posti occupati (senza le prenotazioni cancellate)
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
    fila = 1

    # inserisco dentro mappa_posti i posti dell'aereo
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
    from datetime import datetime, timedelta
    try:

        # richiedo classe, posto e lista degli extra selezionati

        classe = request.form.get('classe', 'economy')
        posto = request.form.get('posto', '')
        extra_ids = request.form.getlist('extra')  # Lista degli extra selezionati
        
        # Verifico che la classe abbia un prezzo
        if classe not in prezzi_dict:
            flash('Classe selezionata non disponibile.', 'error')
            extra_disponibili = Extra.query.all()
            return render_template('book_flight.html',
                                 volo=volo,
                                 prezzi=prezzi_dict,
                                 extra_disponibili=extra_disponibili, 
                                 posti_aereo=generate_seat_map(volo))
        
        # Calcolo costo totale
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
        
        # funzione helper per ottenere la lista dei posti disponibili per classe
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
        
        # Creo la prenotazione
        nuova_prenotazione = Prenotazione(
            passeggero_id=current_user.id,
            data_acquisto=datetime.now(),
            costo_totale=costo_totale,
            stato='confermata'
        )
        
        db.session.add(nuova_prenotazione)
        db.session.flush()
        
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
        
        # Aggiungo gli extra al biglietto
        for extra in extra_selezionati:
            biglietto_extra = BigliettoExtra(
                biglietto_id=nuovo_biglietto.id,
                extra_id=extra.id
            )
            db.session.add(biglietto_extra)
        
        # Riduci i posti disponibili
        volo.posti_disponibili = max(0, (volo.posti_disponibili or 0) - 1)
        
        db.session.commit()
        
        # Messaggio di conferma prenotazione
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

"""
dettagli_prenotazione: pagina dove si possono visualizzare i dettagli delle prenotazioni
filtra le prenotazione con una query usando l'id dell'utente corrente
"""

@app.route('/passeggero/prenotazione/<int:prenotazione_id>')
@login_required
def dettagli_prenotazione(prenotazione_id):

    if current_user.tipo != 'passeggero':
        flash('Accesso non autorizzato.', 'error')
        return redirect(url_for('home'))
    
    try:
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

"""
cancel_booking: cancella la prenotazione che abbia minimo 24 ore di distanza dalla partenza
"""

@app.route('/cancel_booking/<int:prenotazione_id>', methods=['POST'])
@login_required
def cancel_booking(prenotazione_id):
    if current_user.tipo != 'passeggero':
        flash('Accesso non autorizzato.', 'error')
        return redirect(url_for('home'))
    
    try:
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
        
        # Verifico se è possibile cancellare, devono esserci almeno 24h prima del volo)
        for biglietto in prenotazione.biglietti:
            if biglietto.volo.partenza <= datetime.now() + timedelta(hours=24):
                flash('Non puoi cancellare prenotazioni a meno di 24 ore dal volo.', 'error')
                return redirect(url_for('dashboard_passeggero'))
        
        # Aggiorno stato e riaddiziona posti
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

"""
form_aereo: pagina da cui la copagnia puo' modificare o aggiungere un nuovo aereo alla propria flotta
in questo caso aggiunge un nuovo aereo
richiede un nome (modello dell'aereo), e la quantita' di posti nelle classi economy, buisness e first
poi inserisco il nuovo aereo nel database
"""

@app.route('/compagnia/aerei/nuovo', methods=['GET', 'POST'])
@login_required
def nuovo_aereo():
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

"""
form_aereo: pagina da cui la copagnia puo' modificare o aggiungere un nuovo aereo alla propria flotta
in questo caso modifica un aereo gia esistente
filtra l'aereo per l'id richiesto
si possono cambiare nome, e il numero di posti nelle classi
"""

@app.route('/compagnia/aerei/<int:aereo_id>/modifica', methods=['GET', 'POST'])
@login_required
def modifica_aereo(aereo_id):

    if current_user.tipo != 'compagnia':
        flash('Accesso non autorizzato.', 'error')
        return redirect(url_for('home'))

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

"""
elimina: elimina l'aereo selezionato dalla dashboard della compagnia
se un aereo ha voli programmati, non puo' essere eliminato
"""

@app.route('/compagnia/aerei/<int:aereo_id>/elimina', methods=['POST'])
@login_required
def elimina_aereo(aereo_id):
    if current_user.tipo != 'compagnia':
        flash('Accesso non autorizzato.', 'error')
        return redirect(url_for('home'))
    
    try:
        from models import Aereo
        aereo = Aereo.query.filter_by(id=aereo_id, compagnia_id=current_user.id).first()
        
        if not aereo:
            flash('Aereo non trovato.', 'error')
            return redirect(url_for('dashboard_compagnia'))
        
        # Controllo se l'aereo ha voli programmati
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


"""
form_tratta: pagina da cui la compagnia puo' creare una nuova tratta
richiede un areoporto di partenza e uno di arrivo
non puo' essere creata una tratta gia esistente per la compagnia e areoporto arrivo deve essere diverso da quello di destinazione
poi inserisco la tratta nel database la nuova tratta
"""

@app.route('/compagnia/tratte/nuova', methods=['GET', 'POST'])
@login_required
def nuova_tratta():

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
        
        # Controllo se la tratta esiste già
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

"""
elimina: elimina la tratta selezionata
non puo' essere eliminata se ci sono dei voli programmati
"""

@app.route('/compagnia/tratte/<int:tratta_id>/elimina', methods=['POST'])
@login_required
def elimina_tratta(tratta_id):

    if current_user.tipo != 'compagnia':
        flash('Accesso non autorizzato.', 'error')
        return redirect(url_for('home'))
    
    try:
        tratta = Tratta.query.filter_by(id=tratta_id, compagnia_id=current_user.id).first()
        
        if not tratta:
            flash('Tratta non trovata.', 'error')
            return redirect(url_for('dashboard_compagnia'))
        
        # Controllo se ci sono voli programmati
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

"""
gestione_voli: pagina da cui la compagnia puo' vedere tutti i suoi voli
i voli si possono filtrare per tratta, modell di aereo, data di partenza e lo stato (tutti, passati, disponibili, pieni)
si possono ordinare per data di partenza (crescente o decrescente), tratta, numero di posti disponibili
da qua si possono anche eliminare voli che non hanno prenotazioni attive
"""

@app.route('/compagnia/voli')
@login_required
def gestione_voli():
    from datetime import datetime, timedelta
    if current_user.tipo != 'compagnia':
        flash('Accesso non autorizzato.', 'error')
        return redirect(url_for('home'))
    
    compagnia = current_user.compagnia

    voli_query = db.session.query(Volo).join(Tratta).filter(
        Tratta.compagnia_id == compagnia.id
    )
    
    # Parametri di filtraggio
    filtro_tratta = request.args.get('tratta', '')
    filtro_aereo = request.args.get('aereo', '')
    data_da = request.args.get('data_da', '')
    data_a = request.args.get('data_a', '')
    stato_volo = request.args.get('stato', '')
    
    # Applico i filtri
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
    
    # Filtro per data e posti disponibili (lo stato del volo)
    ora_corrente = datetime.now();
    
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
    
    # Ordinamento
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

"""
form_volo: pagina da cui aggiugere un nuovo volo
richiede la tratta, un aereo, data e oraro di partenza, data e orario di arrivo, e il prezzo per i posti di ogni classe (economy, business e first)
poi aggiungo il volo nel database insieme al prezzo
"""

@app.route('/compagnia/voli/nuovo', methods=['GET', 'POST'])
@login_required
def nuovo_volo():

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
            partenza_dt = datetime.strptime(f'{data_partenza} {ora_partenza}', '%Y-%m-%d %H:%M')
            arrivo_dt = datetime.strptime(f'{data_arrivo} {ora_arrivo}', '%Y-%m-%d %H:%M')
            
            if partenza_dt >= arrivo_dt:
                flash('La data di arrivo deve essere successiva alla partenza.', 'error')
                return render_template('form_volo.html', tratte=compagnia.tratte, aerei=compagnia.aerei)
            
            # Verifico che la tratta appartenga alla compagnia
            tratta = Tratta.query.filter_by(id=tratta_id, compagnia_id=current_user.id).first()
            if not tratta:
                flash('Tratta non valida.', 'error')
                return render_template('form_volo.html', tratte=compagnia.tratte, aerei=compagnia.aerei)
            
            # Verifico che l'aereo appartenga alla compagnia
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
            db.session.flush()
            
            # Aggiungo i prezzi
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
            # messaggio di conferma aggiunta
            flash(f'Volo {tratta.aeroporto_partenza}→{tratta.aeroporto_arrivo} del {partenza_dt.strftime("%d/%m/%Y %H:%M")} aggiunto con successo!', 'success')
            return redirect(url_for('dashboard_compagnia'))
            
        except ValueError:
            flash('Formato data/ora non valido.', 'error')
        except Exception as e:
            db.session.rollback()
            flash(f'Errore durante l\'aggiunta del volo: {str(e)}', 'error')
    
    return render_template('form_volo.html', tratte=compagnia.tratte, aerei=compagnia.aerei)

"""
elimina: elimina il volo selezionato
il volo non puo' essere eliminato se ci sono prenotazioni attive
"""

@app.route('/compagnia/voli/<int:volo_id>/elimina', methods=['POST'])
@login_required
def elimina_volo(volo_id):
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

"""
404 e 500: pagine di errore
"""
@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500


@app.context_processor
def inject_user():
    return dict(current_user=current_user)

"""
main: main
"""

if __name__ == '__main__':
    with app.app_context():

        db.create_all()
    
    app.run(debug=True, port=5001, host='127.0.0.1')
