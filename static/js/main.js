// Gestione filtri voli e tab
document.addEventListener('DOMContentLoaded', function() {
    // Inizializzazione filtri
    initializeFilters();
    
    // Inizializzazione tab
    initializeTabs();
    
    // Inizializzazione effetti home page
    initializeHomeEffects();
});

function initializeTabs() {
    const tabs = document.querySelectorAll('.nav-tabs a');
    const tabContents = document.querySelectorAll('.tab-pane');
    
    tabs.forEach(tab => {
        tab.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Rimuovi active da tutti i tab
            tabs.forEach(t => t.parentElement.classList.remove('active'));
            tabContents.forEach(content => content.style.display = 'none');
            
            // Aggiungi active al tab corrente
            this.parentElement.classList.add('active');
            
            // Mostra il contenuto corrispondente
            const targetId = this.getAttribute('href').substring(1);
            const targetContent = document.getElementById(targetId);
            if (targetContent) {
                targetContent.style.display = 'block';
            }
        });
    });
    
    // Mostra il primo tab attivo all'inizio
    const activeTab = document.querySelector('.nav-tabs .active a');
    if (activeTab) {
        const targetId = activeTab.getAttribute('href').substring(1);
        const targetContent = document.getElementById(targetId);
        if (targetContent) {
            targetContent.style.display = 'block';
        }
    }
}

function initializeFilters() {
    const applyFiltersBtn = document.getElementById('applyFiltersBtn');
    const sortSelect = document.getElementById('sortBy');
    const classSelect = document.getElementById('filterClass');
    const priceRange = document.getElementById('priceRange');
    const directOnlyCheckbox = document.getElementById('directOnly');
    
    if (applyFiltersBtn) {
        applyFiltersBtn.addEventListener('click', applyFilters);
    }
    
    // Filtri in tempo reale
    if (sortSelect) {
        sortSelect.addEventListener('change', applyFilters);
    }
    
    if (classSelect) {
        classSelect.addEventListener('change', applyFilters);
    }
    
    if (priceRange) {
        priceRange.addEventListener('input', function() {
            document.getElementById('priceValue').textContent = this.value;
        });
        priceRange.addEventListener('change', applyFilters);
    }
    
    if (directOnlyCheckbox) {
        directOnlyCheckbox.addEventListener('change', applyFilters);
    }
}

function applyFilters() {
    const sortBy = document.getElementById('sortBy')?.value || 'departure';
    const filterClass = document.getElementById('filterClass')?.value || '';
    const maxPrice = parseInt(document.getElementById('priceRange')?.value || '1000');
    const directOnly = document.getElementById('directOnly')?.checked || false;
    
    const flightCards = document.querySelectorAll('.flight-card');
    let visibleFlights = [];
    
    // Applica filtri
    flightCards.forEach(card => {
        let shouldShow = true;
        
        // Filtro prezzo
        const prices = card.querySelectorAll('.text-success');
        let hasValidPrice = false;
        prices.forEach(priceEl => {
            const priceText = priceEl.textContent.replace('€', '').replace(',', '');
            const price = parseInt(priceText);
            if (price <= maxPrice) {
                hasValidPrice = true;
            }
        });
        if (!hasValidPrice && prices.length > 0) {
            shouldShow = false;
        }
        
        // Filtro classe
        if (filterClass) {
            const classBadges = card.querySelectorAll('.badge');
            let hasClass = false;
            classBadges.forEach(badge => {
                if (badge.textContent.toLowerCase().includes(filterClass)) {
                    hasClass = true;
                }
            });
            if (!hasClass) {
                shouldShow = false;
            }
        }
        
        // Filtro voli diretti (attualmente tutti sono diretti)
        // In futuro qui si potrebbe controllare se il volo ha scali
        
        if (shouldShow) {
            card.style.display = 'block';
            visibleFlights.push(card);
        } else {
            card.style.display = 'none';
        }
    });
    
    // Applica ordinamento
    sortFlights(visibleFlights, sortBy);
    
    console.log(`Filtri applicati: ${visibleFlights.length} voli mostrati`);
}

function sortFlights(flights, sortBy) {
    const container = document.querySelector('.flight-results');
    if (!container) return;
    
    const sortedFlights = flights.sort((a, b) => {
        switch(sortBy) {
            case 'price':
                const priceA = getLowestPrice(a);
                const priceB = getLowestPrice(b);
                return priceA - priceB;
                
            case 'departure':
                const timeA = getDepartureTime(a);
                const timeB = getDepartureTime(b);
                return timeA.localeCompare(timeB);
                
            case 'company':
                const companyA = getCompanyName(a);
                const companyB = getCompanyName(b);
                return companyA.localeCompare(companyB);
                
            case 'duration':
                // Per ora non implementato, in futuro si potrebbe calcolare la durata
                return 0;
                
            default:
                return 0;
        }
    });
    
    // Riorganizza i voli nel DOM
    sortedFlights.forEach(flight => {
        container.appendChild(flight);
    });
}

function getLowestPrice(flightCard) {
    const prices = flightCard.querySelectorAll('.text-success');
    let lowest = Infinity;
    prices.forEach(priceEl => {
        const price = parseInt(priceEl.textContent.replace('€', '').replace(',', ''));
        if (price < lowest) {
            lowest = price;
        }
    });
    return lowest === Infinity ? 0 : lowest;
}

function getDepartureTime(flightCard) {
    const timeElement = flightCard.querySelector('.h4.text-primary');
    return timeElement ? timeElement.textContent : '00:00';
}

function getCompanyName(flightCard) {
    const companyElement = flightCard.querySelector('.fas.fa-building').closest('strong');
    return companyElement ? companyElement.textContent.trim() : '';
}

// ===== FUNZIONALITA' CORE SENZA ANIMAZIONI =====
function initializeHomeEffects() {
    // Nessuna animazione - solo log per debug se necessario
    console.log('Home page caricata - animazioni disabilitate per focus su backend');
}

// Funzioni per prenotazione
function updateClasseHidden(voloId) {
    const selectElement = document.getElementById('classe_' + voloId);
    const hiddenElement = document.getElementById('classe_hidden_' + voloId);
    if (selectElement && hiddenElement) {
        hiddenElement.value = selectElement.value;
    }
}

function showFlightDetails(flightId) {
    // TODO: Implementare modal dettagli volo con informazioni scali
    alert('Dettagli volo #' + flightId + ' - funzionalità in sviluppo');
}
