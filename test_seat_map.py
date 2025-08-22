#!/usr/bin/env python3
"""
Script di test per verificare la generazione dinamica della mappa posti
"""

from app import create_app, generate_seat_map
from models import db, Volo, Aereo, Tratta, CompagniaAerea, Utente
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta

def test_seat_map_generation():
    """Test della generazione mappa posti con configurazioni diverse"""
    
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        
        # Crea dati di test
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
        
        # Test con diversi tipi di aereo
        test_configs = [
            {
                'nome': 'Solo Economy (Boeing 737)',
                'modello': 'Boeing 737', 
                'first': 0,
                'business': 0,
                'economy': 150
            },
            {
                'nome': 'Mixed Small (Embraer 190)',
                'modello': 'Embraer 190',
                'first': 4,
                'business': 12, 
                'economy': 84
            },
            {
                'nome': 'Full Service (Airbus A350)',
                'modello': 'Airbus A350',
                'first': 12,
                'business': 48,
                'economy': 240
            },
            {
                'nome': 'Solo Business (Regional Jet)',
                'modello': 'Regional Jet', 
                'first': 0,
                'business': 30,
                'economy': 0
            }
        ]
        
        for config in test_configs:
            print(f"\n{'='*60}")
            print(f"TEST: {config['nome']}")
            print(f"Configurazione: First={config['first']}, Business={config['business']}, Economy={config['economy']}")
            print('='*60)
            
            # Crea aereo
            aereo = Aereo(
                modello=config['modello'],
                posti_totali=config['first'] + config['business'] + config['economy'],
                posti_first=config['first'],
                posti_business=config['business'], 
                posti_economy=config['economy'],
                compagnia_id=compagnia.id
            )
            db.session.add(aereo)
            db.session.flush()
            
            # Crea volo
            domani = datetime.now() + timedelta(days=1)
            dopodomani = domani + timedelta(hours=2)
            
            volo = Volo(
                tratta_id=tratta.id,
                aereo_id=aereo.id,
                partenza=domani,
                arrivo=dopodomani,
                posti_disponibili=aereo.posti_totali
            )
            db.session.add(volo)
            db.session.flush()
            
            # Genera mappa posti
            seat_map = generate_seat_map(volo)
            
            # Analizza la mappa
            stats = {
                'first': {'count': 0, 'rows': set()},
                'business': {'count': 0, 'rows': set()},
                'economy': {'count': 0, 'rows': set()}
            }
            
            rows_sorted = sorted(seat_map.keys())
            
            for row in rows_sorted:
                for seat in seat_map[row]:
                    classe = seat['classe']
                    stats[classe]['count'] += 1
                    stats[classe]['rows'].add(row)
                    
            print(f"\nRisultati generazione mappa:")
            print(f"File generate: {len(rows_sorted)} ({min(rows_sorted) if rows_sorted else 'N/A'}-{max(rows_sorted) if rows_sorted else 'N/A'})")
            
            for classe in ['first', 'business', 'economy']:
                expected = config[classe] 
                actual = stats[classe]['count']
                rows = sorted(stats[classe]['rows']) if stats[classe]['rows'] else []
                
                status = "✅" if expected == actual else "❌"
                print(f"{status} {classe.title()}: {actual}/{expected} posti, file {rows}")
                
            # Verifica che non ci siano gap nelle file
            if rows_sorted:
                expected_rows = list(range(1, len(rows_sorted) + 1))
                actual_rows = rows_sorted
                if expected_rows == actual_rows:
                    print("✅ File consecutive senza gap")
                else:
                    print(f"❌ Gap nelle file! Expected: {expected_rows}, Actual: {actual_rows}")
            
            # Pulisci per test successivo
            db.session.delete(volo)
            db.session.delete(aereo)
            db.session.flush()
            
        db.drop_all()
        print(f"\n{'='*60}")
        print("TUTTI I TEST COMPLETATI")
        print('='*60)

if __name__ == '__main__':
    test_seat_map_generation()
