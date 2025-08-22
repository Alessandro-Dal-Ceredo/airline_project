#!/usr/bin/env python3
"""
Test per le nuove funzionalità di prenotazione:
- Validazione lato server posto/classe/disponibilità
- Assegnazione casuale posto se non selezionato
- Gestione race condition con IntegrityError
- Endpoint API per mappa posti JSON
"""

import unittest
import json
import threading
import time
import os
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
from sqlalchemy.exc import IntegrityError

# Import dell'app e modelli
from app import create_app
from models import db, Utente, CompagniaAerea, Passeggero, Aeroporto, Volo, Tratta, Aereo, PrezzoVolo, Prenotazione, Biglietto, Extra


class BookingFeaturesTestCase(unittest.TestCase):
    """Test case per le funzionalità di prenotazione"""

    def setUp(self):
        """Imposta l'ambiente di test"""
        # Configura database SQLite file-based per condividere la connessione tra app e client
        db_path = os.path.join(os.path.dirname(__file__), 'test_booking.db')
        if os.path.exists(db_path):
            os.remove(db_path)
        overrides = {
            'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
            'SQLALCHEMY_ENGINE_OPTIONS': {'connect_args': {'check_same_thread': False}},
            'TESTING': True,
            'WTF_CSRF_ENABLED': False,
        }
        self.app = create_app('testing', config_overrides=overrides)
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        db.create_all()
        self.client = self.app.test_client()
        
        # Crea dati di test
        self._create_test_data()

    def tearDown(self):
        """Pulisce l'ambiente di test"""
        db.session.remove()
        db.drop_all()
        # Rimuovi file DB
        db_path = os.path.join(os.path.dirname(__file__), 'test_booking.db')
        try:
            if os.path.exists(db_path):
                os.remove(db_path)
        except Exception:
            pass
        self.app_context.pop()

    def _create_test_data(self):
        """Crea dati di test nel database"""
        
        # Aeroporti
        aeroporto_mxp = Aeroporto(codice='MXP', citta='Milano', paese='Italia')
        aeroporto_fco = Aeroporto(codice='FCO', citta='Roma', paese='Italia') 
        db.session.add_all([aeroporto_mxp, aeroporto_fco])

        # Compagnia aerea
        utente_comp = Utente(
            username='testcomp',
            email='test@comp.com',
            password=generate_password_hash('password'),
            tipo='compagnia'
        )
        db.session.add(utente_comp)
        db.session.flush()

        compagnia = CompagniaAerea(
            id=utente_comp.id,
            nome_compagnia='Test Airlines'
        )
        db.session.add(compagnia)

        # Passeggero
        utente_pass = Utente(
            username='testpass',
            email='test@pass.com', 
            password=generate_password_hash('password'),
            tipo='passeggero'
        )
        db.session.add(utente_pass)
        db.session.flush()

        passeggero = Passeggero(
            id=utente_pass.id,
            nome='Mario',
            cognome='Rossi'
        )
        db.session.add(passeggero)

        # Aereo
        aereo = Aereo(
            modello='Boeing 737',
            posti_totali=180,
            posti_economy=150,
            posti_business=24,
            posti_first=6,
            compagnia_id=compagnia.id
        )
        db.session.add(aereo)

        # Tratta
        tratta = Tratta(
            aeroporto_partenza='MXP',
            aeroporto_arrivo='FCO',
            compagnia_id=compagnia.id
        )
        db.session.add(tratta)

        # Volo
        domani = datetime.now() + timedelta(days=1)
        dopodomani = domani + timedelta(hours=2)
        
        volo = Volo(
            tratta_id=1,  # Sarà assegnato dopo il commit
            aereo_id=1,   # Sarà assegnato dopo il commit  
            partenza=domani,
            arrivo=dopodomani,
            posti_disponibili=180
        )
        db.session.add(volo)
        
        db.session.flush()
        
        # Aggiorna con gli ID corretti
        volo.tratta_id = tratta.id
        volo.aereo_id = aereo.id

        # Prezzi per il volo
        prezzo_eco = PrezzoVolo(volo_id=volo.id, classe='economy', prezzo=100.0)
        prezzo_bus = PrezzoVolo(volo_id=volo.id, classe='business', prezzo=300.0) 
        prezzo_first = PrezzoVolo(volo_id=volo.id, classe='first', prezzo=800.0)
        db.session.add_all([prezzo_eco, prezzo_bus, prezzo_first])

        # Extra
        extra = Extra(nome='Bagaglio extra', prezzo=25.0)
        db.session.add(extra)

        db.session.commit()

        # Salva riferimenti per i test
        self.compagnia_id = compagnia.id
        self.passeggero_id = passeggero.id
        self.volo_id = volo.id
        self.aereo_id = aereo.id

    def login_passenger(self):
        """Effettua login come passeggero"""
        return self.client.post('/login', data={
            'username': 'testpass',
            'password': 'password'
        })

    def test_api_seatmap_endpoint(self):
        """Test endpoint API per mappa posti"""
        # Debug: stampa route disponibili
        print("\nRoute registrate:")
        for rule in self.app.url_map.iter_rules():
            print(f"  {rule.endpoint}: {rule.rule} ({rule.methods})")
        
        response = self.client.get(f'/api/voli/{self.volo_id}/seatmap')
        print(f"\nResponse status: {response.status_code}")
        print(f"Response data: {response.get_data(as_text=True)[:200]}")
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('seat_map', data)
        
        seat_map = data['seat_map']
        # Verifica che ci siano file per first class (righe 1-3)
        self.assertIn('1', seat_map)
        first_class_seats = seat_map['1']
        self.assertTrue(len(first_class_seats) > 0)
        self.assertEqual(first_class_seats[0]['classe'], 'first')
        self.assertTrue(first_class_seats[0]['disponibile'])

    def test_api_seatmap_volo_inesistente(self):
        """Test endpoint API con volo inesistente"""
        response = self.client.get('/api/voli/99999/seatmap')
        self.assertEqual(response.status_code, 404)
        
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertIn('error', data)

    def test_validazione_posto_classe_sbagliata(self):
        """Test validazione: posto first class selezionato per economy"""
        self.login_passenger()
        
        response = self.client.post(f'/book_flight/{self.volo_id}', data={
            'classe': 'economy',
            'posto': '1A'  # Posto first class
        })
        
        self.assertEqual(response.status_code, 200)
        # Verifica che mostri un errore
        body = response.get_data(as_text=True)
        self.assertIn('Il posto selezionato non appartiene alla classe scelta', body)

    def test_validazione_posto_inesistente(self):
        """Test validazione: posto inesistente"""
        self.login_passenger()
        
        response = self.client.post(f'/book_flight/{self.volo_id}', data={
            'classe': 'economy',
            'posto': '99Z'  # Posto inesistente
        })
        
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn('Il posto selezionato non esiste per questo volo', body)

    def test_assegnazione_casuale_posto_economy(self):
        """Test assegnazione casuale posto economy quando non specificato"""
        self.login_passenger()
        
        # Prenota senza specificare posto
        response = self.client.post(f'/book_flight/{self.volo_id}', data={
            'classe': 'economy'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn('Prenotazione confermata', body)
        
        # Verifica che sia stato assegnato un posto
        prenotazione = Prenotazione.query.first()
        biglietto = prenotazione.biglietti[0]
        self.assertIsNotNone(biglietto.posto)
        self.assertEqual(biglietto.classe, 'economy')
        
        # Verifica che il posto sia nell'range economy (fila 9+)
        fila = int(biglietto.posto[:-1])
        self.assertGreaterEqual(fila, 9)

    def test_assegnazione_casuale_posto_business(self):
        """Test assegnazione casuale posto business"""
        self.login_passenger()
        
        response = self.client.post(f'/book_flight/{self.volo_id}', data={
            'classe': 'business'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn('Prenotazione confermata', body)
        
        prenotazione = Prenotazione.query.first()
        biglietto = prenotazione.biglietti[0]
        self.assertEqual(biglietto.classe, 'business')
        
        # Verifica che il posto sia nell'range business (fila 4-8)
        fila = int(biglietto.posto[:-1])
        self.assertGreaterEqual(fila, 4)
        self.assertLess(fila, 9)

    def test_posto_manuale_corretto(self):
        """Test selezione manuale posto corretto"""
        self.login_passenger()
        
        response = self.client.post(f'/book_flight/{self.volo_id}', data={
            'classe': 'first',
            'posto': '2C'  # Posto first class valido
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn('Prenotazione confermata', body)
        
        prenotazione = Prenotazione.query.first()
        biglietto = prenotazione.biglietti[0]
        self.assertEqual(biglietto.posto, '2C')
        self.assertEqual(biglietto.classe, 'first')

    def test_posto_occupato_validazione(self):
        """Test validazione posto già occupato"""
        self.login_passenger()
        
        # Prima prenotazione
        self.client.post(f'/book_flight/{self.volo_id}', data={
            'classe': 'economy',
            'posto': '10A'
        }, follow_redirects=True)
        
        # Logout e nuovo login (simula altro utente)
        self.client.get('/logout')
        
        # Crea secondo passeggero
        utente_pass2 = Utente(
            username='testpass2',
            email='test2@pass.com',
            password=generate_password_hash('password'),
            tipo='passeggero'
        )
        db.session.add(utente_pass2)
        db.session.flush()
        
        passeggero2 = Passeggero(
            id=utente_pass2.id,
            nome='Luigi',
            cognome='Bianchi'
        )
        db.session.add(passeggero2)
        db.session.commit()
        
        # Login secondo utente
        self.client.post('/login', data={
            'username': 'testpass2',
            'password': 'password'
        })
        
        # Tenta di prenotare stesso posto
        response = self.client.post(f'/book_flight/{self.volo_id}', data={
            'classe': 'economy',
            'posto': '10A'  # Già occupato
        })
        
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn('Il posto selezionato non è più disponibile', body)

    def test_seatmap_con_posti_occupati(self):
        """Test che la seatmap mostri correttamente i posti occupati"""
        # Crea una prenotazione
        self.login_passenger()
        self.client.post(f'/book_flight/{self.volo_id}', data={
            'classe': 'economy',
            'posto': '15C'
        }, follow_redirects=True)
        
        # Verifica seatmap
        response = self.client.get(f'/api/voli/{self.volo_id}/seatmap')
        data = json.loads(response.data)
        
        seat_map = data['seat_map']
        
        # Trova il posto 15C e verifica che sia marcato come non disponibile
        fila_15 = seat_map.get('15', [])
        posto_15c = None
        for posto in fila_15:
            if posto['numero'] == '15C':
                posto_15c = posto
                break
        
        self.assertIsNotNone(posto_15c)
        self.assertFalse(posto_15c['disponibile'])

    def test_nessun_posto_disponibile_classe(self):
        """Test comportamento quando non ci sono posti disponibili per una classe"""
        # Riempi tutti i posti first class (6 posti)
        volo = Volo.query.get(self.volo_id)
        aereo = volo.aereo
        
        # Crea prenotazioni per tutti i posti first
        posti_first = ['1A', '1B', '1C', '1D', '1E', '1F']
        
        for i, posto in enumerate(posti_first):
            # Crea utente e passeggero
            utente = Utente(
                username=f'user{i}',
                email=f'user{i}@test.com',
                password=generate_password_hash('password'),
                tipo='passeggero'
            )
            db.session.add(utente)
            db.session.flush()
            
            passeggero = Passeggero(
                id=utente.id,
                nome=f'User{i}',
                cognome='Test'
            )
            db.session.add(passeggero)
            db.session.flush()
            
            # Crea prenotazione
            prenotazione = Prenotazione(
                passeggero_id=passeggero.id,
                data_acquisto=datetime.now(),
                costo_totale=800.0,
                stato='confermata'
            )
            db.session.add(prenotazione)
            db.session.flush()
            
            biglietto = Biglietto(
                prenotazione_id=prenotazione.id,
                volo_id=self.volo_id,
                classe='first',
                posto=posto
            )
            db.session.add(biglietto)
        
        db.session.commit()
        
        # Ora prova a prenotare first class
        self.login_passenger()
        response = self.client.post(f'/book_flight/{self.volo_id}', data={
            'classe': 'first'  # Senza specificare posto
        })
        
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn('Nessun posto disponibile per la classe selezionata', body)

    def simulate_concurrent_booking(self, posto_target, results, index):
        """Simula prenotazione concorrente (per test race condition)"""
        try:
            with self.app.app_context():
                from models import Prenotazione, Biglietto
                
                # Simula una piccola attesa per sincronizzazione
                time.sleep(0.01)
                
                prenotazione = Prenotazione(
                    passeggero_id=self.passeggero_id,
                    data_acquisto=datetime.now(),
                    costo_totale=100.0,
                    stato='confermata'
                )
                db.session.add(prenotazione)
                db.session.flush()
                
                biglietto = Biglietto(
                    prenotazione_id=prenotazione.id,
                    volo_id=self.volo_id,
                    classe='economy',
                    posto=posto_target
                )
                db.session.add(biglietto)
                db.session.commit()
                
                results[index] = 'SUCCESS'
                
        except IntegrityError:
            with self.app.app_context():
                db.session.rollback()
            results[index] = 'INTEGRITY_ERROR'
        except Exception as e:
            with self.app.app_context():
                db.session.rollback()
            results[index] = f'ERROR: {str(e)}'

    def test_race_condition_handling(self):
        """Test gestione race condition con vincolo unico"""
        posto_target = '20A'
        num_threads = 3
        results = [''] * num_threads
        threads = []
        
        # Avvia thread concorrenti che provano a prenotare stesso posto
        for i in range(num_threads):
            thread = threading.Thread(
                target=self.simulate_concurrent_booking,
                args=(posto_target, results, i)
            )
            threads.append(thread)
            thread.start()
        
        # Aspetta che tutti i thread finiscano
        for thread in threads:
            thread.join()
        
        # Verifica risultati
        successes = results.count('SUCCESS')
        integrity_errors = results.count('INTEGRITY_ERROR')
        
        # Dovrebbe esserci solo 1 successo e gli altri IntegrityError
        self.assertEqual(successes, 1)
        self.assertGreater(integrity_errors, 0)
        
        # Verifica che ci sia effettivamente solo 1 biglietto per quel posto
        biglietti = Biglietto.query.filter_by(posto=posto_target, volo_id=self.volo_id).all()
        self.assertEqual(len(biglietti), 1)

    def test_extra_selection(self):
        """Test selezione servizi extra durante prenotazione"""
        self.login_passenger()
        
        extra = Extra.query.first()
        
        response = self.client.post(f'/book_flight/{self.volo_id}', data={
            'classe': 'economy',
            'posto': '12A',
            'extra': [str(extra.id)]  # Seleziona l'extra
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn('Prenotazione confermata', body)
        
        # Verifica che l'extra sia stato aggiunto
        prenotazione = Prenotazione.query.first()
        biglietto = prenotazione.biglietti[0]
        
        self.assertEqual(len(biglietto.extra), 1)
        self.assertEqual(biglietto.extra[0].extra_id, extra.id)
        
        # Verifica costo totale (100 + 25)
        self.assertEqual(float(prenotazione.costo_totale), 125.0)


def run_tests():
    """Esegue tutti i test"""
    print("🧪 AVVIO TEST FUNZIONALITÀ PRENOTAZIONE")
    print("=" * 50)
    
    # Configura unittest per output dettagliato
    unittest.main(verbosity=2, exit=False)


if __name__ == '__main__':
    run_tests()
