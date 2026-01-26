/* ============================================
   DATAFLOW - SCRIPT PRINCIPAL
   Gestion des interactions et animations
   ============================================ */

// ============================================
// VARIABLES GLOBALES
// ============================================
let selectedFile = null;
const fileInput = document.getElementById('fileInput');
const uploadArea = document.getElementById('uploadArea');
const fileName = document.getElementById('fileName');
const fileSize = document.getElementById('fileSize');
const fileInfo = document.getElementById('fileInfo');
const uploadContent = uploadArea?.querySelector('.upload-content');
const submitBtn = document.getElementById('submitBtn');
const uploadForm = document.getElementById('uploadForm');
const progressBar = document.getElementById('progressBar');

// ============================================
// GESTION DU FICHIER
// ============================================

// Événement lors de la sélection d'un fichier
if (fileInput) {
    fileInput.addEventListener('change', function(e) {
        handleFileSelect(e.target.files[0]);
    });
}

// Fonction pour gérer la sélection de fichier
function handleFileSelect(file) {
    if (!file) return;
    
    // ✅ CORRECTION : Ajout de JSON et XML
    const allowedExtensions = ['csv', 'xlsx', 'xls', 'json', 'xml'];
    const fileExtension = file.name.split('.').pop().toLowerCase();
    
    if (!allowedExtensions.includes(fileExtension)) {
        showAlert('Format de fichier non supporté. Utilisez CSV, XLSX, XLS, JSON ou XML.', 'danger');
        return;
    }
    
    // Vérifier la taille (16 MB max)
    const maxSize = 16 * 1024 * 1024; // 16 MB en bytes
    if (file.size > maxSize) {
        showAlert('Le fichier est trop volumineux. Taille maximale : 16 MB.', 'danger');
        return;
    }
    
    selectedFile = file;
    displayFileInfo(file);
    
    // Activer le bouton submit
    if (submitBtn) {
        submitBtn.disabled = false;
    }
}

// Afficher les informations du fichier
function displayFileInfo(file) {
    if (!fileName || !fileSize || !fileInfo || !uploadContent) return;
    
    // Cacher le contenu d'upload et afficher les infos du fichier
    uploadContent.style.display = 'none';
    fileInfo.style.display = 'block';
    
    // Nom du fichier
    fileName.textContent = file.name;
    
    // Taille du fichier
    const sizeMB = (file.size / (1024 * 1024)).toFixed(2);
    const sizeKB = (file.size / 1024).toFixed(2);
    fileSize.textContent = file.size > 1024 * 1024 
        ? `${sizeMB} MB` 
        : `${sizeKB} KB`;
    
    // Animation d'entrée
    fileInfo.classList.add('fade-in');
}

// Fonction pour supprimer le fichier sélectionné
function clearFile() {
    selectedFile = null;
    
    if (fileInput) fileInput.value = '';
    if (uploadContent) uploadContent.style.display = 'block';
    if (fileInfo) fileInfo.style.display = 'none';
    if (submitBtn) submitBtn.disabled = true;
    
    // Retirer la classe drag-over si elle existe
    if (uploadArea) uploadArea.classList.remove('drag-over');
}

// ============================================
// DRAG AND DROP
// ============================================

if (uploadArea) {
    // Prévenir le comportement par défaut
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        uploadArea.addEventListener(eventName, preventDefaults, false);
    });
    
    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    // Highlight lors du drag over
    ['dragenter', 'dragover'].forEach(eventName => {
        uploadArea.addEventListener(eventName, highlight, false);
    });
    
    ['dragleave', 'drop'].forEach(eventName => {
        uploadArea.addEventListener(eventName, unhighlight, false);
    });
    
    function highlight(e) {
        uploadArea.classList.add('drag-over');
    }
    
    function unhighlight(e) {
        uploadArea.classList.remove('drag-over');
    }
    
    // Gérer le drop
    uploadArea.addEventListener('drop', handleDrop, false);
    
    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        
        if (files.length > 0) {
            fileInput.files = files;
            handleFileSelect(files[0]);
        }
    }
}

// ============================================
// SOUMISSION DU FORMULAIRE
// ============================================

if (uploadForm) {
    uploadForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        if (!selectedFile) {
            showAlert('Veuillez sélectionner un fichier.', 'warning');
            return;
        }
        
        // Afficher la barre de progression
        if (progressBar) {
            progressBar.style.display = 'block';
            animateProgressBar();
        }
        
        // Désactiver le bouton pendant le traitement
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Traitement en cours...';
        }
        
        // Soumettre le formulaire
        this.submit();
    });
}

// Animation de la barre de progression
function animateProgressBar() {
    if (!progressBar) return;
    
    const progressBarInner = progressBar.querySelector('.progress-bar');
    let width = 0;
    
    const interval = setInterval(() => {
        if (width >= 90) {
            clearInterval(interval);
        } else {
            width += Math.random() * 15;
            if (width > 90) width = 90;
            progressBarInner.style.width = width + '%';
        }
    }, 200);
}

// ============================================
// SYSTÈME D'ALERTES
// ============================================

function showAlert(message, type = 'info') {
    // Créer l'élément alert
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.setAttribute('role', 'alert');
    
    // Icône selon le type
    let icon = 'info-circle-fill';
    if (type === 'success') icon = 'check-circle-fill';
    if (type === 'danger') icon = 'exclamation-triangle-fill';
    if (type === 'warning') icon = 'exclamation-circle-fill';
    
    alertDiv.innerHTML = `
        <i class="bi bi-${icon} me-2"></i>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    // Insérer l'alert en haut de la page
    const container = document.querySelector('.container');
    if (container) {
        container.insertBefore(alertDiv, container.firstChild);
        
        // Auto-dismiss après 5 secondes
        setTimeout(() => {
            alertDiv.classList.remove('show');
            setTimeout(() => alertDiv.remove(), 300);
        }, 5000);
    }
}

// ============================================
// SMOOTH SCROLL POUR LES ANCRES
// ============================================

document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        const href = this.getAttribute('href');
        
        // Ignorer les liens vides ou #
        if (href === '#' || href === '') return;
        
        e.preventDefault();
        
        const target = document.querySelector(href);
        if (target) {
            const offsetTop = target.offsetTop - 80; // 80px pour la navbar
            
            window.scrollTo({
                top: offsetTop,
                behavior: 'smooth'
            });
        }
    });
});

// ============================================
// EFFET DE SCROLL SUR LA NAVBAR
// ============================================

let lastScroll = 0;
const navbar = document.getElementById('mainNav');

window.addEventListener('scroll', () => {
    const currentScroll = window.pageYOffset;
    
    if (!navbar) return;
    
    // Ajouter la classe "scrolled" après 50px
    if (currentScroll > 50) {
        navbar.classList.add('scrolled');
    } else {
        navbar.classList.remove('scrolled');
    }
    
    // Auto-hide navbar lors du scroll down (optionnel)
    /* 
    if (currentScroll > lastScroll && currentScroll > 500) {
        navbar.style.transform = 'translateY(-100%)';
    } else {
        navbar.style.transform = 'translateY(0)';
    }
    */
    
    lastScroll = currentScroll;
});

// ============================================
// VALIDATION DU FORMULAIRE EN TEMPS RÉEL
// ============================================

if (fileInput) {
    fileInput.addEventListener('change', function() {
        const file = this.files[0];
        
        if (file) {
            // ✅ CORRECTION : Validation avec 5 formats
            const validExtensions = ['csv', 'xlsx', 'xls', 'json', 'xml'];
            const extension = file.name.split('.').pop().toLowerCase();
            
            if (!validExtensions.includes(extension)) {
                this.value = '';
                showAlert('Format non supporté. Utilisez CSV, XLSX, XLS, JSON ou XML.', 'danger');
                return;
            }
            
            // Validation de la taille
            const maxSize = 16 * 1024 * 1024; // 16 MB
            if (file.size > maxSize) {
                this.value = '';
                showAlert('Fichier trop volumineux. Maximum : 16 MB.', 'danger');
                return;
            }
        }
    });
}

// ============================================
// COMPTEUR ANIMÉ POUR LES STATISTIQUES
// ============================================

function animateCounter(element, target, duration = 2000) {
    if (!element) return;
    
    let current = 0;
    const increment = target / (duration / 16); // 60 FPS
    
    const timer = setInterval(() => {
        current += increment;
        if (current >= target) {
            element.textContent = formatNumber(target);
            clearInterval(timer);
        } else {
            element.textContent = formatNumber(Math.floor(current));
        }
    }, 16);
}

function formatNumber(num) {
    if (num >= 1000000) {
        return (num / 1000000).toFixed(1) + 'M';
    } else if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
}

// Démarrer les animations au scroll
const observerOptions = {
    threshold: 0.5,
    rootMargin: '0px 0px -100px 0px'
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            const counters = entry.target.querySelectorAll('[data-count]');
            counters.forEach(counter => {
                const target = parseInt(counter.getAttribute('data-count'));
                animateCounter(counter, target);
                counter.removeAttribute('data-count'); // Pour ne pas réanimer
            });
        }
    });
}, observerOptions);

// Observer les sections avec des compteurs
document.querySelectorAll('.stats-section, .hero-section').forEach(section => {
    observer.observe(section);
});

// ============================================
// GESTION DES TOOLTIPS BOOTSTRAP
// ============================================

// Initialiser tous les tooltips
const tooltipTriggerList = [].slice.call(
    document.querySelectorAll('[data-bs-toggle="tooltip"]')
);
tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
});

// ============================================
// EASTER EGG : CONFETTI AU SUCCÈS
// ============================================

function celebrateSuccess() {
    // Créer des confettis si le nettoyage réussit
    const successAlert = document.querySelector('.alert-success');
    
    if (successAlert && typeof confetti !== 'undefined') {
        confetti({
            particleCount: 100,
            spread: 70,
            origin: { y: 0.6 }
        });
    }
}

// Vérifier si on vient de nettoyer un fichier avec succès
window.addEventListener('load', () => {
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('success') === 'true') {
        celebrateSuccess();
    }
});

// ============================================
// AFFICHAGE DU FORMAT DU FICHIER
// ============================================

// ✅ CORRECTION : Ajout des icônes pour JSON et XML
function getFileIcon(extension) {
    const icons = {
        'csv': 'bi-filetype-csv',
        'xlsx': 'bi-file-earmark-excel',
        'xls': 'bi-file-earmark-excel',
        'json': 'bi-filetype-json',
        'xml': 'bi-filetype-xml'
    };
    return icons[extension] || 'bi-file-earmark';
}

// ============================================
// PRÉVISUALISATION (OPTIONNEL)
// ============================================

function previewFile(file) {
    // Cette fonction peut être étendue pour afficher
    // un aperçu du contenu du fichier CSV
    console.log('Aperçu du fichier:', file.name);
}

// ============================================
// COPIE DANS LE PRESSE-PAPIER (Pour les liens)
// ============================================

function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showAlert('Copié dans le presse-papier !', 'success');
    }).catch(err => {
        console.error('Erreur de copie:', err);
        showAlert('Erreur lors de la copie', 'danger');
    });
}

// ============================================
// THÈME SOMBRE (OPTIONNEL - À IMPLÉMENTER)
// ============================================

function toggleDarkMode() {
    document.body.classList.toggle('dark-mode');
    localStorage.setItem('darkMode', document.body.classList.contains('dark-mode'));
}

// Charger le thème sauvegardé
window.addEventListener('load', () => {
    if (localStorage.getItem('darkMode') === 'true') {
        document.body.classList.add('dark-mode');
    }
});

// ============================================
// DETECTION DE LA CONNEXION INTERNET
// ============================================

window.addEventListener('online', () => {
    showAlert('Connexion Internet rétablie', 'success');
});

window.addEventListener('offline', () => {
    showAlert('Connexion Internet perdue', 'warning');
});

// ============================================
// PERFORMANCE : LAZY LOADING DES IMAGES
// ============================================

if ('IntersectionObserver' in window) {
    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                if (img.dataset.src) {
                    img.src = img.dataset.src;
                    img.classList.add('loaded');
                    observer.unobserve(img);
                }
            }
        });
    });

    document.querySelectorAll('img[data-src]').forEach(img => {
        imageObserver.observe(img);
    });
}

// ============================================
// ANALYTICS (Optionnel - Google Analytics)
// ============================================

function trackEvent(category, action, label) {
    if (typeof gtag !== 'undefined') {
        gtag('event', action, {
            'event_category': category,
            'event_label': label
        });
    }
}

// Tracker les uploads
if (uploadForm) {
    uploadForm.addEventListener('submit', () => {
        trackEvent('File', 'Upload', selectedFile?.name || 'unknown');
    });
}

// ============================================
// CONSOLE MESSAGE
// ============================================

console.log('%c🚀 DataFlow v1.0', 'color: #6366f1; font-size: 20px; font-weight: bold;');
console.log('%cDéveloppé avec ❤️ pour ISI M1 DSIA', 'color: #8b5cf6; font-size: 14px;');
console.log('%c⚠️ N\'exécutez pas de code non vérifié ici !', 'color: #ef4444; font-size: 12px; font-weight: bold;');

// ============================================
// EXPORT DES FONCTIONS GLOBALES
// ============================================

// Rendre certaines fonctions accessibles globalement
window.DataFlow = {
    clearFile,
    showAlert,
    copyToClipboard,
    toggleDarkMode,
    trackEvent
};

console.log('✅ Script DataFlow chargé avec succès !');