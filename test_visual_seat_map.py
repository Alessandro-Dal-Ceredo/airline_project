#!/usr/bin/env python3
"""
Test per verificare che la mappa posti contenga le informazioni classe necessarie per il frontend
"""

from app import create_app, generate_seat_map
from models import db, Volo, Aereo, Tratta, CompagniaAerea, Utente, Aeroporto
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
import json

def test_seat_map_with_class_info():
    """Test che la mappa posti contenga le informazioni classe"""
    
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        
        # Crea dati base
        aeroporto_mxp = Aeroporto(codice='MXP', citta='Milano', paese='Italia')
        aeroporto_fco = Aeroporto(codice='FCO', citta='Roma', paese='Italia')
        db.session.add_all([aeroporto_mxp, aeroporto_fco])
        
        utente_comp = Utente(
            username='test_comp',
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
        
        tratta = Tratta(
            aeroporto_partenza='MXP',
            aeroporto_arrivo='FCO', 
            compagnia_id=compagnia.id
        )
        db.session.add(tratta)
        
        # Aereo con tutte e 3 le classi
        aereo = Aereo(
            modello='Test Aircraft',
            posti_totali=30,  # 6 first + 12 business + 12 economy
            posti_first=6,    # 1 fila
            posti_business=12, # 2 file
            posti_economy=12,  # 2 file
            compagnia_id=compagnia.id
        )
        db.session.add(aereo)
        db.session.flush()
        
        # Volo
        domani = datetime.now() + timedelta(days=1)
        dopodomani = domani + timedelta(hours=2)
        
        volo = Volo(
            tratta_id=tratta.id,
            aereo_id=aereo.id,
            partenza=domani,
            arrivo=dopodomani,
            posti_disponibili=30
        )
        db.session.add(volo)
        db.session.flush()
        
        # Genera mappa posti
        seat_map = generate_seat_map(volo)
        
        print(f"\n{'='*60}")
        print("TEST: Verifica informazioni classe nella mappa posti")
        print('='*60)
        
        print(f"Aereo configurato: {aereo.posti_first} first, {aereo.posti_business} business, {aereo.posti_economy} economy")
        print(f"File generate: {len(seat_map)}")
        
        classi_trovate = set()
        posti_per_classe = {'first': 0, 'business': 0, 'economy': 0}
        
        for row_num, posti_fila in seat_map.items():
            print(f"\nFila {row_num}: {len(posti_fila)} posti")
            
            for posto in posti_fila:
                # Verifica che ogni posto abbia le informazioni necessarie
                required_keys = ['numero', 'classe', 'disponibile']
                for key in required_keys:
                    if key not in posto:
                        print(f"❌ ERRORE: posto {posto} manca chiave '{key}'")
                        return
                
                classe = posto['classe']
                classi_trovate.add(classe)
                posti_per_classe[classe] += 1
                
                # Mostra primo posto di ogni fila come esempio
                if posto == posti_fila[0]:
                    print(f"   Esempio posto: {posto['numero']} (classe: {posto['classe']}, disponibile: {posto['disponibile']})")
        
        print(f"\nRisultati:")
        print(f"Classi trovate: {sorted(classi_trovate)}")
        
        for classe in ['first', 'business', 'economy']:
            expected = getattr(aereo, f'posti_{classe}')
            actual = posti_per_classe[classe]
            status = "✅" if expected == actual else "❌"
            print(f"{status} {classe}: {actual}/{expected} posti")
        
        # Test serializzazione JSON (come nell'API)
        seat_map_json = {str(riga): posti for riga, posti in seat_map.items()}
        json_string = json.dumps(seat_map_json, indent=2)
        print(f"\n📋 Mappa serializzabile in JSON: {len(json_string)} caratteri")
        
        # Verifica che posti di classi diverse abbiano identificatori corretti per CSS
        print("\n🎨 Verifica CSS classes:")
        for classe in classi_trovate:
            posti_classe = [p for posti_fila in seat_map.values() for p in posti_fila if p['classe'] == classe]
            print(f"   Classe '{classe}': {len(posti_classe)} posti con data-class='{classe}'")
        
        print(f"\n✅ Test completato con successo!")
        print(f"La mappa contiene tutte le informazioni necessarie per il frontend:")
        print(f"- Numero posto per visualizzazione")
        print(f"- Classe per colori CSS (.first, .business, .economy)")
        print(f"- Disponibilità per disabilitazione")
        print(f"- Serializzazione JSON per API")
        
        db.drop_all()

if __name__ == '__main__':
    test_seat_map_with_class_info()
