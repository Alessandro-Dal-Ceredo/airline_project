document.addEventListener('DOMContentLoaded', function() {
    initializeTabs();
    
    initializeAlerts();

    initializeCopyLinks();
});

function initializeTabs() {
    const tabs = document.querySelectorAll('.nav-tabs a');
    const tabContents = document.querySelectorAll('.tab-pane');
    
    tabs.forEach(tab => {
        tab.addEventListener('click', function(e) {
            e.preventDefault();
            
            tabs.forEach(t => t.parentElement.classList.remove('active'));
            tabContents.forEach(content => content.style.display = 'none');
            
            this.parentElement.classList.add('active');
            
            const targetId = this.getAttribute('href').substring(1);
            const targetContent = document.getElementById(targetId);
            if (targetContent) {
                targetContent.style.display = 'block';
            }
        });
    });
    
    const activeTab = document.querySelector('.nav-tabs .active a');
    if (activeTab) {
        const targetId = activeTab.getAttribute('href').substring(1);
        const targetContent = document.getElementById(targetId);
        if (targetContent) {
            targetContent.style.display = 'block';
        }
    }
}

function showAlert(alertType, message) {
    var alertDiv = document.querySelector('.alert.' + alertType);
    if (alertDiv) {
        var pElement = alertDiv.querySelector('p[name="p_' + alertType + '"]');
        if (pElement) {
            pElement.textContent = message;
        }
        alertDiv.classList.add('visible');
    }
}

function hideAlert(alertType) {
    var alertDiv = document.querySelector('.alert.' + alertType);
    if (alertDiv && !alertDiv.classList.contains('unclosable')) {
        alertDiv.classList.remove('visible');
        var pElement = alertDiv.querySelector('p[name="p_' + alertType + '"]');
        if (pElement) {
            pElement.textContent = '';
        }
    }
}

function initializeAlerts() {
    // Nasconde in automatico gli alert in 5 sec
    const visibleAlerts = document.querySelectorAll('.alert.visible');
    visibleAlerts.forEach(alert => {
        setTimeout(() => {
            alert.classList.remove('visible');
        }, 5000);
    });
}

// Copia i link nel footer
function initializeCopyLinks() {
    const copyLinks = document.querySelectorAll('.copy-link');
    
    copyLinks.forEach(link => {
        link.addEventListener('click', function(event) {
            event.preventDefault();
            
            const contentToCopy = this.textContent.split(': ')[1];
            if (contentToCopy) {
                const textarea = document.createElement('textarea');
                textarea.value = contentToCopy;
                textarea.style.position = 'absolute';
                textarea.style.left = '-9999px';
                document.body.appendChild(textarea);
                textarea.select();
                
                try {
                    document.execCommand('copy');
                    showAlert('info', 'Copiato negli appunti: ' + contentToCopy);
                } catch(err) {
                    showAlert('warning', 'Impossibile copiare il testo');
                }
                
                document.body.removeChild(textarea);
            }
        });
    });
}
