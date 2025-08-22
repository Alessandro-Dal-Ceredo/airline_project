# 🎨 Guida Colori Sistema Prenotazione Posti

## 📋 **Panoramica**
Il sistema di selezione posti utilizza un sistema di colori intuitivo per distinguere le classi e gli stati dei posti, rendendo la selezione chiara e user-friendly.

## 🎨 **Schema Colori per Classe**

### 🥇 **First Class**
- **Colore base**: `#ffd700` (oro) con bordo `#ffb300`
- **Hover**: `#ffed4a` (oro più chiaro) con bordo `#ffc107` 
- **Selezionato**: `#ff8f00` (arancione oro) con bordo `#e65100`
- **Significato**: Lusso, esclusività, premium

### 💼 **Business**
- **Colore base**: `#4a90e2` (blu professionale) con bordo `#357abd`
- **Hover**: `#5ba0f2` (blu più chiaro) con bordo `#4a90e2`
- **Selezionato**: `#1976d2` (blu intenso) con bordo `#0d47a1`
- **Significato**: Professionalità, comfort, efficienza

### 🎫 **Economy**
- **Colore base**: `#e8f4f8` (azzurro tenue) con bordo `#b8dce8`
- **Hover**: `#f0f9fb` (azzurro chiarissimo) con bordo `#a0d1e4`
- **Selezionato**: `#0288d1` (blu cielo intenso) con bordo `#01579b`
- **Significato**: Accessibilità, chiarezza, economia

## 🚫 **Stati Speciali**

### ❌ **Posto Occupato**
- **Colore**: `#f5f5f5` (grigio chiaro)
- **Testo**: `#999` (grigio medio)
- **Bordo**: `#ddd` (grigio)
- **Cursore**: `not-allowed`

### 🔒 **Posto Non Disponibile** (classe diversa)
- **Effetto**: `opacity: 0.4` (semi-trasparente)
- **Cursore**: `not-allowed`
- **Comportamento**: Non cliccabile

## ✨ **Effetti Visivi**

### 🎯 **Cambi di Stato**
I cambi di colore avvengono istantaneamente per una selezione chiara e immediata, senza animazioni o effetti che possano distrarre dall'utilizzo.

## 🔄 **Comportamento Interattivo**

### 📝 **Selezione Classe → Aggiornamento Posti**
1. **Seleziono Economy** → Solo posti economy cliccabili (azzurri), altri disabilitati
2. **Seleziono Business** → Solo posti business cliccabili (blu), altri disabilitati
3. **Seleziono First** → Solo posti first cliccabili (oro), altri disabilitati

### 🔄 **Cambio Classe con Posto Già Selezionato**
- Se ho selezionato un posto Economy (azzurro selezionato)
- E cambio in Business → il posto Economy si deseleziona automaticamente
- Solo i posti Business diventano cliccabili

## 📖 **Legenda Visual**

```
🥇 First Class     💼 Business        🎫 Economy         ❌ Occupato        ✨ Selezionato     🔒 Non disponibile
   #ffd700           #4a90e2           #e8f4f8           #f5f5f5           #ff8f00          opacity: 0.4
```

## 🎯 **Vantaggi UX**

### ✅ **Chiarezza Visiva**
- Ogni classe ha la sua identità cromatica
- I colori selezionati sono varianti intensificate della classe
- Lo stato di selezione è immediatamente riconoscibile

### ✅ **Feedback Immediato**
- Hover states per feedback al passaggio del mouse
- Cambio colore immediato per evidenziare la selezione
- Disabilitazione visiva per posti non selezionabili

### ✅ **Consistenza**
- Schema colori coerente in tutta l'applicazione
- Cambi di stato immediati e chiari
- Comportamento prevedibile e intuitivo

## 🔧 **Implementazione Tecnica**

### CSS Classes
```css
/* Colori base */
.seat-item.first { background:#ffd700; border-color:#ffb300; }
.seat-item.business { background:#4a90e2; border-color:#357abd; }
.seat-item.economy { background:#e8f4f8; border-color:#b8dce8; }

/* Stati selezionati */
.seat-item.first.selected { background:#ff8f00; border-color:#e65100; color:#fff; }
.seat-item.business.selected { background:#1976d2; border-color:#0d47a1; color:#fff; }
.seat-item.economy.selected { background:#0288d1; border-color:#01579b; color:#fff; }
```

### JavaScript Logic
- `updateSeatAvailability()`: Gestisce abilitazione/disabilitazione posti
- Event listeners per cambio classe e selezione posto
- Gestione automatica deselezione per classi incompatibili

---

*Sistema implementato per BD Airline - Esperienza utente premium per la selezione posti* ✈️
