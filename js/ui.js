// Changement de service (Lexa/Lara)
function handleServiceChange() {
    const service = document.getElementById('translationService').value;
    config.translationService = service;
    const laraSection = document.getElementById('laraSettings');
    const lexaApiKeyHelp = document.getElementById('lexaApiKeyHelp');
    if (laraSection && lexaApiKeyHelp) {
        if (service === 'lexa') {
            laraSection.classList.add('hidden');
            lexaApiKeyHelp.textContent = 'Cette clé est nécessaire pour accéder aux services de traduction Lexamt';
        } else {
            laraSection.classList.remove('hidden');
            lexaApiKeyHelp.textContent = 'Cette clé est nécessaire même en mode Lara pour récupérer la liste des langues';
        }
    }
    updateServiceModeDisplay();
    updateLaraOptionsVisibility();
}
// Modals paramètres
function openSettingsModal() {
    handleServiceChange();
    const messageDiv = document.getElementById('settingsMessage');
    if (messageDiv) {
        messageDiv.textContent = '';
        messageDiv.className = '';
        messageDiv.style.padding = '0';
    }
    document.getElementById('settingsModal').style.display = 'block';
}

function closeSettingsModal() {
    document.getElementById('settingsModal').style.display = 'none';
}
// Flag pour bloquer les appels à loadLaraTemplates pendant l'init
let isLaraTemplatesInitializing = false;
// Initialisation du service courant (Lexa ou Lara)
function initializeForCurrentService() {
    updateServiceModeDisplay();
    updateLaraOptionsVisibility();
    if (config.translationService === 'lexa') {
        loadLanguages();
    } else {
        isLaraTemplatesInitializing = true;
        loadLaraLanguages();
        syncLaraOptionsFromConfig();
        setTimeout(() => {
            loadLaraTemplates();
            isLaraTemplatesInitializing = false;
        }, 0);
    }
}

function updateLaraOptionsVisibility() {
    console.log('🔍 updateLaraOptionsVisibility appelée, service:', config.translationService);
    const laraInstructionsSection = document.getElementById('laraInstructionsSection');
    const laraTemplateSection = document.getElementById('laraTemplateSection');
    const laraFixTextSection = document.getElementById('laraFixTextSection');
    const domainGroup = document.getElementById('domainGroup');
    const glossarySection = document.getElementById('glossarySection');
    const selectedTemplateInfo = document.getElementById('selectedTemplateInfo');
    if (config.translationService === 'lara') {
        console.log('✅ Mode Lara détecté - affichage des options Lara');
        if (laraInstructionsSection) laraInstructionsSection.style.display = 'block';
        if (laraTemplateSection) {
            laraTemplateSection.style.display = 'block';
            loadLaraTemplates();
        }
        if (laraFixTextSection) laraFixTextSection.style.display = 'block';
        if (domainGroup) domainGroup.style.display = 'block';
        if (glossarySection) glossarySection.style.display = 'none';
    } else {
        console.log('✅ Mode Lexa détecté - masquage des options Lara');
        if (laraInstructionsSection) laraInstructionsSection.style.display = 'none';
        if (laraTemplateSection) laraTemplateSection.style.display = 'none';
        if (laraFixTextSection) laraFixTextSection.style.display = 'none';
        if (selectedTemplateInfo) selectedTemplateInfo.style.display = 'none';
        if (domainGroup) domainGroup.style.display = 'block';
    }
}

function syncLaraOptionsFromConfig() {
    const instructionsTextarea = document.getElementById('laraInstructionsMain');
    if (instructionsTextarea && config.lara.instructions) instructionsTextarea.value = config.lara.instructions;
}
// Gestion des modes (texte/fichier)
function switchMode(mode) {
    currentMode = mode;
    const textModeBtn = document.getElementById('textModeBtn');
    const fileModeBtn = document.getElementById('fileModeBtn');
    const textMode = document.getElementById('textMode');
    const fileMode = document.getElementById('fileMode');
    const glossarySection = document.getElementById('glossarySection');
    if (mode === 'text') {
        textModeBtn.classList.add('active');
        fileModeBtn.classList.remove('active');
        textMode.style.display = 'block';
        fileMode.style.display = 'none';
        glossarySection.style.display = 'none';
        selectedFiles = [];
        updateFileList();
    } else {
        textModeBtn.classList.remove('active');
        fileModeBtn.classList.add('active');
        textMode.style.display = 'none';
        fileMode.style.display = 'block';
        if (config.translationService === 'lexa') {
            glossarySection.style.display = 'block';
        }
        document.getElementById('sourceText').value = '';
    }
    updateTranslateButton();
}

function updateTranslateButton() {
    const translateBtn = document.getElementById('translateBtn');
    if (currentMode === 'text') {
        const sourceText = document.getElementById('sourceText').value.trim();
        translateBtn.disabled = !sourceText;
    } else {
        translateBtn.disabled = selectedFiles.length === 0;
    }
}

// Inversion des langues
function swapLanguages() {
    const sourceLang = document.getElementById('sourceLang');
    const targetLang = document.getElementById('targetLang');
    const temp = sourceLang.value;
    sourceLang.value = targetLang.value;
    targetLang.value = temp;
    if (config.translationService === 'lexa') {
        loadGlossaries();
    }
}
// Initialisation principale
// Gérée par app.js pour éviter l'exécution en double des listeners (ce qui causait le dysfonctionnement du menu burger)

// Aiguillage traduction selon service
async function testTranslation() {
    const sourceLang = document.getElementById('sourceLang').value;
    const targetLang = document.getElementById('targetLang').value;
    if (!hasValidConfig()) {
        showMessage('Veuillez configurer vos clés API dans les paramètres.', 'error');
        openSettingsModal();
        return;
    }
    if (config.translationService === 'lexa') {
        await translateWithLexa();
    } else {
        await translateWithLara();
    }
}
// js/ui.js : gestion des événements DOM, affichage, modals, boutons, etc.

function setupEventListeners() {
    document.getElementById('translateBtn').addEventListener('click', testTranslation);
    document.getElementById('swapBtn').addEventListener('click', swapLanguages);
    document.getElementById('sourceText').addEventListener('input', updateTranslateButton);
    document.getElementById('domain').addEventListener('change', (e) => {
        console.log('[TRACE] Event: change sur #domain', new Date().toISOString(), e);
        loadGlossaries();
        if (config.translationService === 'lara' && !isLaraTemplatesInitializing) {
            loadLaraTemplates();
        }
        saveUserPreferences();
    });
    document.getElementById('sourceLang').addEventListener('change', (e) => {
        console.log('[TRACE] Event: change sur #sourceLang', new Date().toISOString(), e);
        loadGlossaries();
        if (config.translationService === 'lara' && !isLaraTemplatesInitializing) {
            loadLaraTemplates();
        }
        saveUserPreferences();
    });
    document.getElementById('targetLang').addEventListener('change', (e) => {
        console.log('[TRACE] Event: change sur #targetLang', new Date().toISOString(), e);
        loadGlossaries();
        if (config.translationService === 'lara' && !isLaraTemplatesInitializing) {
            loadLaraTemplates();
        }
        saveUserPreferences();
    });
    document.getElementById('textModeBtn').addEventListener('click', () => switchMode('text'));
    document.getElementById('fileModeBtn').addEventListener('click', () => switchMode('file'));
    document.getElementById('settingsModalClose').addEventListener('click', closeSettingsModal);
    document.getElementById('cancelSettings').addEventListener('click', closeSettingsModal);
    document.getElementById('saveSettings').addEventListener('click', saveSettings);
    document.getElementById('translationService').addEventListener('change', handleServiceChange);
    setupFileHandlers();
    setupGlossaryHandlers();
    try { setupTemplatesHandlers(); } catch (error) { console.error('Erreur lors de la configuration des templates:', error); }
    try { setupDomainsHandlers(); } catch (error) { console.error('Erreur lors de la configuration des domaines:', error); }
    try { setupGlossariesScreenHandlers(); } catch (error) { console.error('Erreur lors de la configuration des glossaires:', error); }
    try { setupMemoriesScreenHandlers(); } catch (error) { console.error('Erreur lors de la configuration des mémoires:', error); }
    try { setupResourcesScreenHandlers(); } catch (error) { console.error('Erreur lors de la configuration des ressources:', error); }
    setupModalCloseHandlers();
    setupPasswordToggleHandlers();
    setupBurgerMenuHandlers();
}

function setupModalCloseHandlers() {
    document.getElementById('glossaryModal').addEventListener('click', (e) => {
        if (e.target.id === 'glossaryModal') closeGlossaryModal();
    });
    document.getElementById('personalGlossariesModal').addEventListener('click', (e) => {
        if (e.target.id === 'personalGlossariesModal') closePersonalGlossariesModal();
    });
    document.getElementById('settingsModal').addEventListener('click', (e) => {
        if (e.target.id === 'settingsModal') closeSettingsModal();
    });
}

// Toggle password visibility
function setupPasswordToggleHandlers() {
    document.querySelectorAll('.toggle-password-btn').forEach(btn => {
        btn.addEventListener('click', function () {
            const targetId = this.getAttribute('data-target');
            const input = document.getElementById(targetId);
            if (input) {
                if (input.type === 'password') {
                    input.type = 'text';
                    this.textContent = '🙈';
                    this.title = 'Masquer';
                } else {
                    input.type = 'password';
                    this.textContent = '👁';
                    this.title = 'Afficher';
                }
            }
        });
    });
}

// Ouvrir la documentation API dans un nouvel onglet
function openApiDocumentation() {
    window.open('doc/api-docs.html', '_blank');
}

// Gestion du menu burger
function setupBurgerMenuHandlers() {
    const burgerBtn = document.getElementById('burgerBtn');
    const burgerDropdown = document.getElementById('burgerDropdown');
    const setupMenuItem = document.getElementById('setupMenuItem');
    const templatesMenuItem = document.getElementById('templatesMenuItem');
    const domainsMenuItem = document.getElementById('domainsMenuItem');
    const glossariesMenuItem = document.getElementById('glossariesMenuItem');
    const memoriesMenuItem = document.getElementById('memoriesMenuItem');
    const resourcesMenuItem = document.getElementById('resourcesMenuItem');
    const docApiMenuItem = document.getElementById('docApiMenuItem');
    const backFromTemplates = document.getElementById('backFromTemplates');

    if (!burgerBtn || !burgerDropdown) {
        console.error('Burger menu elements not found');
        return;
    }

    // Toggle du menu burger
    burgerBtn.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();

        // Toggle la classe pour montrer/cacher
        if (burgerDropdown.classList.contains('show')) {
            burgerDropdown.classList.remove('show');
        } else {
            burgerDropdown.classList.add('show');
        }
    });

    // Fermer le menu si on clique ailleurs
    document.addEventListener('click', (e) => {
        if (!burgerBtn.contains(e.target) && !burgerDropdown.contains(e.target)) {
            burgerDropdown.classList.remove('show');
        }
    });

    // Menu item : Setup
    if (setupMenuItem) {
        setupMenuItem.addEventListener('click', () => {
            burgerDropdown.classList.remove('show');
            openSettingsModal();
        });
    }

    // Menu item : Templates
    if (templatesMenuItem) {
        templatesMenuItem.addEventListener('click', () => {
            burgerDropdown.classList.remove('show');
            openTemplatesScreen();
        });
    }

    // Menu item : Domaines
    if (domainsMenuItem) {
        domainsMenuItem.addEventListener('click', () => {
            burgerDropdown.classList.remove('show');
            openDomainsScreen();
        });
    }

    // Menu item : Glossaires
    if (glossariesMenuItem) {
        glossariesMenuItem.addEventListener('click', () => {
            burgerDropdown.classList.remove('show');
            openGlossariesScreen();
        });
    }

    // Menu item : Mémoires
    if (memoriesMenuItem) {
        memoriesMenuItem.addEventListener('click', () => {
            burgerDropdown.classList.remove('show');
            openMemoriesScreen();
        });
    }

    // Menu item : Ressources
    if (resourcesMenuItem) {
        resourcesMenuItem.addEventListener('click', () => {
            burgerDropdown.classList.remove('show');
            openResourcesScreen();
        });
    }

    // Menu item : Doc API
    if (docApiMenuItem) {
        docApiMenuItem.addEventListener('click', () => {
            burgerDropdown.classList.remove('show');
            openApiDocumentation();
        });
    }

    // Bouton retour depuis la page templates
    if (backFromTemplates) {
        backFromTemplates.addEventListener('click', closeTemplatesScreen);
    }
}

// ... autres fonctions d'affichage, showMessage, etc. à compléter dans ce fichier
