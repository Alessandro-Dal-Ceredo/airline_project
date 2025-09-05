from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from enum import Enum
import sqlalchemy as sa
from sqlalchemy import Column, Integer, String, DateTime, Numeric, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import relationship

db = SQLAlchemy()

# Definisco gli enum PostgreSQL
class TipoUtente(Enum):
    COMPAGNIA = "compagnia"
    PASSEGGERO = "passeggero"

class ClasseVolo(Enum):
    ECONOMY = "economy"
    BUSINESS = "business"
    FIRST = "first"

class StatoPrenotazione(Enum):
    CONFERMATA = "confermata"
    CANCELLATA = "cancellata"

tipo_utente_enum = ENUM('compagnia', 'passeggero', name='tipo_utente', create_type=False)
classe_volo_enum = ENUM('economy', 'business', 'first', name='classe_volo', create_type=False)
stato_prenotazione_enum = ENUM('confermata', 'cancellata', name='stato_prenotazione', create_type=False)

"""
Tabella degli utenti
"""

class Utente(UserMixin, db.Model):
    __tablename__ = 'utente'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(200), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    tipo = Column(tipo_utente_enum, nullable=False)
    createdat = Column(DateTime, nullable=False, default=datetime.utcnow)

    compagnia = relationship("CompagniaAerea", back_populates="utente", uselist=False)
    passeggero = relationship("Passeggero", back_populates="utente", uselist=False)
    
    def __repr__(self):
        return f'<Utente {self.username}>'

"""
Estensione degli utenti di tipo compagnia
"""

class CompagniaAerea(db.Model):
    __tablename__ = 'compagnia_aerea'
    
    id = Column(Integer, ForeignKey('utente.id', ondelete='CASCADE'), primary_key=True)
    nome_compagnia = Column(String(100), unique=True, nullable=False)

    utente = relationship("Utente", back_populates="compagnia")
    tratte = relationship("Tratta", back_populates="compagnia")
    aerei = relationship("Aereo", back_populates="compagnia")
    
    def __repr__(self):
        return f'<CompagniaAerea {self.nome_compagnia}>'

"""
Estensione degli utenti di tipo passeggero
"""

class Passeggero(db.Model):
    __tablename__ = 'passeggero'
    
    id = Column(Integer, ForeignKey('utente.id', ondelete='CASCADE'), primary_key=True)
    nome = Column(String(50), nullable=False)
    cognome = Column(String(50), nullable=False)

    utente = relationship("Utente", back_populates="passeggero")
    prenotazioni = relationship("Prenotazione", back_populates="passeggero")
    
    @property
    def nome_completo(self):
        return f"{self.nome} {self.cognome}"
    
    def __repr__(self):
        return f'<Passeggero {self.nome} {self.cognome}>'

"""
Tabella degli aereoporti
"""

class Aeroporto(db.Model):
    __tablename__ = 'aeroporto'
    
    codice = Column(String(3), primary_key=True)
    citta = Column(String(100), nullable=False)
    paese = Column(String(100), nullable=False)

    tratte_partenza = relationship("Tratta", foreign_keys="Tratta.aeroporto_partenza", back_populates="aeroporto_partenza_obj")
    tratte_arrivo = relationship("Tratta", foreign_keys="Tratta.aeroporto_arrivo", back_populates="aeroporto_arrivo_obj")
    
    def __repr__(self):
        return f'<Aeroporto {self.codice} - {self.citta}>'

"""
Tabella delle tratte
"""

class Tratta(db.Model):
    __tablename__ = 'tratta'
    
    id = Column(Integer, primary_key=True)
    aeroporto_partenza = Column(String(3), ForeignKey('aeroporto.codice', onupdate='CASCADE'), nullable=False)
    aeroporto_arrivo = Column(String(3), ForeignKey('aeroporto.codice', onupdate='CASCADE'), nullable=False)
    compagnia_id = Column(Integer, ForeignKey('compagnia_aerea.id', ondelete='RESTRICT'), nullable=False)
    
    # Constraint
    __table_args__ = (
        CheckConstraint('aeroporto_partenza <> aeroporto_arrivo', name='check_different_airports'),
    )

    compagnia = relationship("CompagniaAerea", back_populates="tratte")
    aeroporto_partenza_obj = relationship("Aeroporto", foreign_keys=[aeroporto_partenza], back_populates="tratte_partenza")
    aeroporto_arrivo_obj = relationship("Aeroporto", foreign_keys=[aeroporto_arrivo], back_populates="tratte_arrivo")
    voli = relationship("Volo", back_populates="tratta")
    
    def __repr__(self):
        return f'<Tratta {self.aeroporto_partenza}-{self.aeroporto_arrivo}>'

"""
Tabella degli aerei
"""

class Aereo(db.Model):
    """Flotta delle compagnie"""
    __tablename__ = 'aereo'
    
    id = Column(Integer, primary_key=True)
    modello = Column(String(100), nullable=False)
    posti_totali = Column(Integer, nullable=False)
    posti_economy = Column(Integer, nullable=False)
    posti_business = Column(Integer, nullable=False)
    posti_first = Column(Integer, nullable=False)
    compagnia_id = Column(Integer, ForeignKey('compagnia_aerea.id', ondelete='RESTRICT'), nullable=False)
    
    # Constraints
    __table_args__ = (
        CheckConstraint('posti_totali > 0', name='check_posti_positivi'),
        CheckConstraint('posti_economy >= 0', name='check_economy_non_neg'),
        CheckConstraint('posti_business >= 0', name='check_business_non_neg'),
        CheckConstraint('posti_first >= 0', name='check_first_non_neg'),
        CheckConstraint('posti_economy + posti_business + posti_first = posti_totali', name='check_sum_posti'),
    )

    compagnia = relationship("CompagniaAerea", back_populates="aerei")
    voli = relationship("Volo", back_populates="aereo")
    
    def __repr__(self):
        return f'<Aereo {self.modello} ({self.posti_totali} posti)>'

"""
Tabella dei voli
"""

class Volo(db.Model):
    __tablename__ = 'volo'
    
    id = Column(Integer, primary_key=True)
    tratta_id = Column(Integer, ForeignKey('tratta.id', ondelete='RESTRICT'), nullable=False)
    aereo_id = Column(Integer, ForeignKey('aereo.id', ondelete='RESTRICT'), nullable=False)
    partenza = Column(DateTime, nullable=False)
    arrivo = Column(DateTime, nullable=False)
    posti_disponibili = Column(Integer, nullable=False, default=0)
    
    # Constraints
    __table_args__ = (
        CheckConstraint('partenza < arrivo', name='check_orari_logici'),
    )

    tratta = relationship("Tratta", back_populates="voli")
    aereo = relationship("Aereo", back_populates="voli")
    prezzi = relationship("PrezzoVolo", back_populates="volo", cascade="all, delete-orphan")
    biglietti = relationship("Biglietto", back_populates="volo")
    
    @property
    def durata(self):
        # calcolo durata del volo
        return self.arrivo - self.partenza
    
    def get_prezzo_per_classe(self, classe):
        # ottengo il prezzo per una classe
        prezzo_obj = next((p for p in self.prezzi if p.classe == classe), None)
        return prezzo_obj.prezzo if prezzo_obj else None
    
    def get_posti_disponibili_per_classe(self, classe):
        # ottengo i posti totali per classe
        if classe == 'economy':
            posti_totali_classe = self.aereo.posti_economy
        elif classe == 'business':
            posti_totali_classe = self.aereo.posti_business
        elif classe == 'first':
            posti_totali_classe = self.aereo.posti_first
        else:
            return 0
        
        # Conto i biglietti già prenotati per classe
        from sqlalchemy import func
        biglietti_occupati = db.session.query(func.count(Biglietto.id)).join(Prenotazione).filter(
            Biglietto.volo_id == self.id,
            Biglietto.classe == classe,
            Prenotazione.stato != 'cancellata'  # Escludi prenotazioni cancellate
        ).scalar() or 0
        
        return max(0, posti_totali_classe - biglietti_occupati)
    
    def has_available_seats_for_class(self, classe):
        # verifico che ci siano posti disponibili per classe
        return self.get_posti_disponibili_per_classe(classe) > 0
    
    def __repr__(self):
        return f'<Volo {self.id} - {self.partenza.strftime("%d/%m %H:%M")}>'


"""
Tabella dei prezzi per ogni volo
"""

class PrezzoVolo(db.Model):
    __tablename__ = 'prezzo_volo'
    
    volo_id = Column(Integer, ForeignKey('volo.id', ondelete='CASCADE'), primary_key=True)
    classe = Column(classe_volo_enum, primary_key=True)
    prezzo = Column(Numeric(10,2), nullable=False)
    
    # Constraints
    __table_args__ = (
        CheckConstraint('prezzo >= 0', name='check_prezzo_non_negativo'),
    )

    volo = relationship("Volo", back_populates="prezzi")
    
    def __repr__(self):
        return f'<PrezzoVolo {self.classe}: €{self.prezzo}>'

"""
Tabella degli extra
"""

class Extra(db.Model):
    __tablename__ = 'extra'
    
    id = Column(Integer, primary_key=True)
    nome = Column(String(100), unique=True, nullable=False)
    prezzo = Column(Numeric(10,2), nullable=False)
    
    # Constraints
    __table_args__ = (
        CheckConstraint('prezzo >= 0', name='check_extra_prezzo_non_negativo'),
    )

    biglietti = relationship("BigliettoExtra", back_populates="extra")
    
    def __repr__(self):
        return f'<Extra {self.nome} - €{self.prezzo}>'

"""
Tabella delle prenotazioni
"""

class Prenotazione(db.Model):
    __tablename__ = 'prenotazione'
    
    id = Column(Integer, primary_key=True)
    passeggero_id = Column(Integer, ForeignKey('passeggero.id', ondelete='CASCADE'), nullable=False)
    data_acquisto = Column(DateTime, nullable=False, default=datetime.utcnow)
    costo_totale = Column(Numeric(10,2), nullable=False)
    stato = Column(stato_prenotazione_enum, nullable=False, default='confermata')
    
    # Constraints
    __table_args__ = (
        CheckConstraint('costo_totale >= 0', name='check_costo_non_negativo'),
    )

    passeggero = relationship("Passeggero", back_populates="prenotazioni")
    biglietti = relationship("Biglietto", back_populates="prenotazione", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<Prenotazione {self.id} - €{self.costo_totale}>'

"""
Tabella dei biglietti
"""

class Biglietto(db.Model):
    __tablename__ = 'biglietto'
    
    id = Column(Integer, primary_key=True)
    prenotazione_id = Column(Integer, ForeignKey('prenotazione.id', ondelete='CASCADE'), nullable=False)
    volo_id = Column(Integer, ForeignKey('volo.id', ondelete='RESTRICT'), nullable=False)
    classe = Column(classe_volo_enum, nullable=False)
    posto = Column(String(10), nullable=False)
    
    # Constraints
    __table_args__ = (
        sa.UniqueConstraint('volo_id', 'posto', name='unique_posto_per_volo'),
    )

    prenotazione = relationship("Prenotazione", back_populates="biglietti")
    volo = relationship("Volo", back_populates="biglietti")
    extra = relationship("BigliettoExtra", back_populates="biglietto", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<Biglietto {self.posto} - {self.classe}>'


"""
Tabella di associazione degli extra ai biglietti
"""

class BigliettoExtra(db.Model):
    __tablename__ = 'bigliettoextra'
    
    biglietto_id = Column(Integer, ForeignKey('biglietto.id', ondelete='CASCADE'), primary_key=True)
    extra_id = Column(Integer, ForeignKey('extra.id', ondelete='RESTRICT'), primary_key=True)

    biglietto = relationship("Biglietto", back_populates="extra")
    extra = relationship("Extra", back_populates="biglietti")
    
    def __repr__(self):
        return f'<BigliettoExtra {self.biglietto_id}-{self.extra_id}>'

"""
Classe helper per gestire i vaggi con scali
"""

class ViaggioCombinato:
    
    def __init__(self, voli_segmenti, origine, destinazione, data_partenza):
        self.voli_segmenti = voli_segmenti  # Lista di voli che formano il viaggio
        self.origine = origine
        self.destinazione = destinazione
        self.data_partenza = data_partenza
        self._validate_connection_times()

    """
    funzione che controlla che la destinazione e la partenza di un volo coincidano
    e che ci siano almeno 2 ore di connessione tra un volo e il successivo
    """
    
    def _validate_connection_times(self):

        from datetime import timedelta
        
        for i in range(len(self.voli_segmenti) - 1):
            volo_corrente = self.voli_segmenti[i]
            volo_successivo = self.voli_segmenti[i + 1]

            if volo_corrente.tratta.aeroporto_arrivo != volo_successivo.tratta.aeroporto_partenza:
                raise ValueError(f"Connessione non valida: {volo_corrente.tratta.aeroporto_arrivo} != {volo_successivo.tratta.aeroporto_partenza}")

            tempo_connessione = volo_successivo.partenza - volo_corrente.arrivo
            if tempo_connessione < timedelta(hours=2):
                raise ValueError(f"Tempo di connessione insufficiente: {tempo_connessione} < 2 ore")
    
    @property
    def partenza_totale(self):
        # orario di partenza del primo volo
        return self.voli_segmenti[0].partenza
    
    @property
    def arrivo_totale(self):
        # orario di arrivo dell'ultimo volo
        return self.voli_segmenti[-1].arrivo
    
    @property
    def durata_totale(self):
        # durata totale del viaggio
        return self.arrivo_totale - self.partenza_totale
    
    @property
    def aeroporti_scalo(self):
        # lista degli aereoporti di scalo
        scali = []
        for i in range(len(self.voli_segmenti) - 1):
            scali.append(self.voli_segmenti[i].tratta.aeroporto_arrivo)
        return scali
    
    @property
    def numero_scali(self):
        # numero di scali di un viaggio
        return len(self.voli_segmenti) - 1
    
    @property
    def is_diretto(self):
        # ritorna true se il viaggio non ha scali
        return len(self.voli_segmenti) == 1
    
    def get_prezzo_minimo_per_classe(self, classe):
        # calcolo il prezzo totale per un viaggio con una classe
        prezzo_totale = 0
        for volo in self.voli_segmenti:
            prezzo_segmento = volo.get_prezzo_per_classe(classe)
            if prezzo_segmento is None:
                return None  # Classe non disponibile su almeno un segmento
            prezzo_totale += prezzo_segmento
        return prezzo_totale
    
    def get_posti_disponibili_per_classe(self, classe):
        # calcolo i posti minimi per una classe (prendo il minimo tra i voli)
        posti_minimi = float('inf')
        for volo in self.voli_segmenti:
            posti_segmento = volo.get_posti_disponibili_per_classe(classe)
            posti_minimi = min(posti_minimi, posti_segmento)
        return int(posti_minimi) if posti_minimi != float('inf') else 0
    
    def has_available_seats_for_class(self, classe):
        # controllo che ci siano posri disponibili per una classe su tutti i segmenti
        return self.get_posti_disponibili_per_classe(classe) > 0
    
    def get_compagnie(self):
        # lista delle compagnie che hanno i voli nel viaggio
        compagnie = set()
        for volo in self.voli_segmenti:
            compagnie.add(volo.tratta.compagnia.nome_compagnia)
        return list(compagnie)
    
    def get_tempi_connessione(self):
        # lista dei tempi di connessione tra i voli
        tempi = []
        for i in range(len(self.voli_segmenti) - 1):
            volo_corrente = self.voli_segmenti[i]
            volo_successivo = self.voli_segmenti[i + 1]
            tempo_connessione = volo_successivo.partenza - volo_corrente.arrivo
            tempi.append(tempo_connessione)
        return tempi
    
    def __repr__(self):
        scali_str = " → ".join([self.origine] + self.aeroporti_scalo + [self.destinazione])
        return f'<ViaggioCombinato {scali_str} ({self.numero_scali} scali)>'
    
    def to_dict(self):
        # converte il viaggio in un dizionario
        return {
            'voli_segmenti': self.voli_segmenti,
            'origine': self.origine,
            'destinazione': self.destinazione,
            'partenza_totale': self.partenza_totale,
            'arrivo_totale': self.arrivo_totale,
            'durata_totale': self.durata_totale,
            'aeroporti_scalo': self.aeroporti_scalo,
            'numero_scali': self.numero_scali,
            'is_diretto': self.is_diretto,
            'compagnie': self.get_compagnie(),
            'tempi_connessione': self.get_tempi_connessione()
        }
