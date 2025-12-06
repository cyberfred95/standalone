// js/config.js : gestion de la configuration globale, stockage local, initialisation

// Detection automatique de l'environnement
// En local (fichier ou localhost sans proxy) : utilise localhost:3000
// En production (via nginx) : utilise /api
function getApiBaseUrl() {
    const isLocalFile = window.location.protocol === 'file:';
    const isLocalhost = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';

    // Si on est sur un fichier local ou localhost sans nginx (port different de 8080)
    if (isLocalFile || (isLocalhost && window.location.port !== '8080')) {
        return 'http://localhost:8001/lara-django/api/lara';
    }
    // En production ou via docker-compose (nginx sur port 8080)
    // Si on est sous /lara/, l'API Django est disponible via /lara-django/api/lara/
    if (window.location.pathname.startsWith('/lara/')) {
        return '/lara-django/api/lara';
    }
    return '/lara-django/api/lara';
}

let config = {
    translationService: 'lexa', // 'lexa' ou 'lara'
    lexa: {
        apiKey: '',
        baseUrl: 'https://test.portail.lexamt.fr/api/v1'
    },
    lara: {
        accessKeyId: '',
        accessKeySecret: '',
        baseUrl: getApiBaseUrl(),
        style: 'faithful',
        instructions: '',
        translationMemoryIds: '',
        glossaryIds: ''
    },
    // Préférences utilisateur
    preferences: {
        sourceLang: '',
        targetLang: '',
        domainId: '',
        domainName: ''
    }
};

let availableDomains = [];
let selectedFiles = [];
let currentMode = 'text';
let selectedCsvFile = null;
let personalGlossaries = [];
let selectedPersonalGlossary = null;
let availableLanguages = [];

function loadConfigFromStorage() {
    try {
        const stored = localStorage.getItem('translation_config');
        if (stored) {
            const parsed = JSON.parse(stored);
            const oldBaseUrl = parsed.lara?.baseUrl;
            config = { ...config, ...parsed };

            // IMPORTANT: Toujours forcer la mise à jour du baseUrl avec la valeur actuelle
            // pour s'assurer qu'on utilise le bon backend (Django au lieu de Node.js)
            const newBaseUrl = getApiBaseUrl();
            config.lara.baseUrl = newBaseUrl;

            // Log si on a migré l'URL
            if (oldBaseUrl !== newBaseUrl) {
                console.log('🔄 Migration backend détectée:');
                console.log('   Ancienne URL:', oldBaseUrl);
                console.log('   Nouvelle URL:', newBaseUrl);
                // Sauvegarder la config mise à jour
                saveConfigToStorage();
            }

            if (config.translationService) {
                document.getElementById('translationService').value = config.translationService;
            }
            if (config.lexa.apiKey) {
                document.getElementById('lexaApiKey').value = config.lexa.apiKey;
            }
            if (config.lara.accessKeyId) {
                document.getElementById('laraAccessKeyId').value = config.lara.accessKeyId;
            }
            if (config.lara.accessKeySecret) {
                document.getElementById('laraAccessKeySecret').value = config.lara.accessKeySecret;
            }
            if (config.lara.style) {
                document.getElementById('laraStyle').value = config.lara.style;
            }
            if (config.lara.translationMemoryIds) {
                document.getElementById('laraMemoryIds').value = config.lara.translationMemoryIds;
            }
            if (config.lara.glossaryIds) {
                document.getElementById('laraGlossaryIds').value = config.lara.glossaryIds;
            }
        }

        // Toujours vérifier que le baseUrl est correct
        console.log('✅ Backend URL configurée:', config.lara.baseUrl);

        updateServiceModeDisplay();
    } catch (error) {
        console.error('Erreur lors du chargement de la configuration:', error);
    }
}

function saveConfigToStorage() {
    try {
        localStorage.setItem('translation_config', JSON.stringify(config));
        updateServiceModeDisplay();
    } catch (error) {
        console.error('Erreur lors de la sauvegarde de la configuration:', error);
    }
}

function updateServiceModeDisplay() {
    const serviceModeElement = document.getElementById('currentServiceMode');
    if (!serviceModeElement) return;
    if (!config.translationService) {
        serviceModeElement.textContent = 'À choisir';
        serviceModeElement.style.color = '#dc2626';
    } else if (config.translationService === 'lexa') {
        serviceModeElement.textContent = 'Lexa';
        serviceModeElement.style.color = '#059669';
    } else if (config.translationService === 'lara') {
        serviceModeElement.textContent = 'Lara';
        serviceModeElement.style.color = '#059669';
    }
}

function hasValidConfig() {
    if (config.translationService === 'lexa') {
        return !!config.lexa.apiKey;
    } else {
        return !!(config.lara.accessKeyId && config.lara.accessKeySecret);
    }
}

function saveUserPreferences() {
    const sourceLang = document.getElementById('sourceLang');
    const targetLang = document.getElementById('targetLang');
    const domainSelect = document.getElementById('domain');

    config.preferences.sourceLang = sourceLang?.value || '';
    config.preferences.targetLang = targetLang?.value || '';
    config.preferences.domainId = domainSelect?.value || '';
    config.preferences.domainName = domainSelect?.selectedOptions[0]?.dataset.name || '';

    saveConfigToStorage();
}

function restoreUserPreferences() {
    const sourceLang = document.getElementById('sourceLang');
    const targetLang = document.getElementById('targetLang');
    const domainSelect = document.getElementById('domain');

    if (config.preferences.sourceLang && sourceLang) {
        const sourceOption = Array.from(sourceLang.options).find(opt => opt.value === config.preferences.sourceLang);
        if (sourceOption) sourceLang.value = config.preferences.sourceLang;
    }

    if (config.preferences.targetLang && targetLang) {
        const targetOption = Array.from(targetLang.options).find(opt => opt.value === config.preferences.targetLang);
        if (targetOption) targetLang.value = config.preferences.targetLang;
    }

    if (config.preferences.domainId && domainSelect) {
        const domainOption = Array.from(domainSelect.options).find(opt => opt.value === config.preferences.domainId);
        if (domainOption) domainSelect.value = config.preferences.domainId;
    }
}

// Sauvegarder les paramètres depuis le modal
async function saveSettings() {
    const service = document.getElementById('translationService').value;
    const saveBtn = document.getElementById('saveSettings');

    // Désactiver le bouton pendant la validation
    saveBtn.disabled = true;
    saveBtn.textContent = 'Validation...';

    try {
        if (service === 'lexa') {
            const apiKey = document.getElementById('lexaApiKey').value.trim();

            if (!apiKey) {
                showSettingsMessage('Veuillez entrer une clé API Lexa.', 'error');
                return;
            }

            // Tester la clé Lexa en récupérant les langues
            showSettingsMessage('Test de la clé API Lexa en cours...', 'success');
            const isValid = await testLexaApiKey(apiKey);

            if (!isValid) {
                showSettingsMessage('Clé API Lexa invalide. Vérifiez votre clé.', 'error');
                return;
            }

            config.lexa.apiKey = apiKey;
            config.translationService = service;

        } else {
            const accessKeyId = document.getElementById('laraAccessKeyId').value.trim();
            const accessKeySecret = document.getElementById('laraAccessKeySecret').value.trim();
            const lexaApiKey = document.getElementById('lexaApiKey').value.trim();

            if (!accessKeyId || !accessKeySecret) {
                showSettingsMessage('Veuillez entrer les clés API Lara (ID et Secret).', 'error');
                return;
            }

            if (!lexaApiKey) {
                showSettingsMessage('La clé API Lexa est nécessaire même en mode Lara (pour récupérer les langues).', 'error');
                return;
            }

            // Tester la clé Lexa d'abord
            showSettingsMessage('Test de la clé API Lexa en cours...', 'success');
            const lexaValid = await testLexaApiKey(lexaApiKey);

            if (!lexaValid) {
                showSettingsMessage('Clé API Lexa invalide. Elle est nécessaire pour récupérer les langues.', 'error');
                return;
            }

            // Tester les clés Lara
            showSettingsMessage('Test des clés API Lara en cours...', 'success');
            const laraValid = await testLaraApiKeys(accessKeyId, accessKeySecret);

            if (!laraValid) {
                showSettingsMessage('Clés API Lara invalides. Vérifiez votre Access Key ID et Secret.', 'error');
                return;
            }

            config.lexa.apiKey = lexaApiKey;
            config.lara.accessKeyId = accessKeyId;
            config.lara.accessKeySecret = accessKeySecret;

            // Lire le Style depuis la modale setup
            const style = document.getElementById('laraStyle')?.value;
            if (style) config.lara.style = style;

            // Lire les Instructions depuis l'écran principal
            const instructionsMain = document.getElementById('laraInstructionsMain')?.value.trim();
            if (instructionsMain !== undefined) config.lara.instructions = instructionsMain;

            config.lara.translationMemoryIds = document.getElementById('laraMemoryIds').value.trim();
            config.lara.glossaryIds = document.getElementById('laraGlossaryIds').value.trim();
            config.translationService = service;
        }

        saveConfigToStorage();

        // Afficher le succès puis fermer après 3 secondes
        showSettingsMessage('Paramètres sauvegardés avec succès !', 'success');

        // Recharger la liste des langues immédiatement si mode lexa
        if (config.translationService === 'lexa') {
            await loadLanguages();
        }

        setTimeout(() => {
            closeSettingsModal();
            initializeForCurrentService();
        }, 3000);

    } catch (error) {
        console.error('Erreur lors de la sauvegarde des paramètres:', error);
        showSettingsMessage(`Erreur: ${error.message}`, 'error');
    } finally {
        saveBtn.disabled = false;
        saveBtn.textContent = 'Sauvegarder';
    }
}

// Afficher un message dans le modal de paramètres
function showSettingsMessage(text, type) {
    const messageDiv = document.getElementById('settingsMessage');
    messageDiv.textContent = text;
    messageDiv.className = type;
    messageDiv.style.padding = '12px';
    messageDiv.style.borderRadius = '4px';
    messageDiv.style.textAlign = 'center';
}

// Test de la clé API Lexa
async function testLexaApiKey(apiKey) {
    try {
        const response = await fetch(`${config.lexa.baseUrl}/languages/`, {
            headers: {
                'Authorization': `Bearer ${apiKey}`,
                'Content-Type': 'application/json'
            }
        });

        return response.ok;
    } catch (error) {
        console.error('Erreur lors du test de la clé Lexa:', error);
        return false;
    }
}

// Test des clés API Lara
async function testLaraApiKeys(accessKeyId, accessKeySecret) {
    try {
        // Faire un test simple avec une traduction courte
        const response = await fetch(`${config.lara.baseUrl}/translate-text`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                accessKeyId: accessKeyId,
                accessKeySecret: accessKeySecret,
                text: 'test',
                source: 'en',
                target: 'fr'
            })
        });

        return response.ok;
    } catch (error) {
        console.error('Erreur lors du test des clés Lara:', error);
        return false;
    }
}
