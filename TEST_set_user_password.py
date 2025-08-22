#!/usr/bin/env python3
"""
Script per impostare una password per l'utente airfrance_admin (ID: 6)
"""

import sys
from werkzeug.security import generate_password_hash
from app import create_app
from models import db, Utente

def set_user_password(user_id, new_password):
    """Imposta una nuova password per un utente specifico"""
    
    app = create_app()
    
    with app.app_context():
        # Trova l'utente
        utente = Utente.query.get(user_id)
        
        if not utente:
            print(f"❌ Utente con ID {user_id} non trovato")
            return False
        
        print(f"👤 Utente trovato: {utente.username} ({utente.email})")
        print(f"📋 Tipo: {utente.tipo}")
        
        if utente.tipo == 'compagnia' and utente.compagnia:
            print(f"✈️  Compagnia: {utente.compagnia.nome_compagnia}")
        
        # Genera hash della password
        password_hash = generate_password_hash(new_password)
        
        # Aggiorna la password
        utente.password = password_hash
        
        try:
            db.session.commit()
            print(f"✅ Password aggiornata con successo per {utente.username}")
            print(f"🔑 Nuova password: {new_password}")
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Errore durante l'aggiornamento: {e}")
            return False

def main():
    """Funzione principale"""
    print("🔐 IMPOSTAZIONE PASSWORD UTENTE AIRFRANCE_ADMIN")
    print("=" * 55)
    
    user_id = 6  # ID dell'utente airfrance_admin
    
    # Chiedi password se non fornita come argomento
    if len(sys.argv) > 1:
        new_password = sys.argv[1]
    else:
        new_password = input("Inserisci la nuova password: ").strip()
        
        if not new_password:
            print("❌ Password non può essere vuota")
            return
    
    # Imposta la password
    success = set_user_password(user_id, new_password)
    
    if success:
        print(f"\n🎉 OPERAZIONE COMPLETATA!")
        print(f"📧 Email: AIRFRANCE_ADMIN@demo.local (o airfrance_admin@demo.local)")
        print(f"👤 Username: AIRFRANCE_ADMIN")
        print(f"🔑 Password: {new_password}")
        print(f"\n🌐 Ora puoi fare login all'applicazione per:")
        print(f"   • Vedere la flotta di Air France")
        print(f"   • Gestire tratte e voli")
        print(f"   • Visualizzare statistiche della compagnia")
        print(f"\n▶️  Avvia l'app con: python app.py")
        print(f"▶️  Vai su: http://localhost:5001")
    
if __name__ == "__main__":
    main()
