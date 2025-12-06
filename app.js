// Note: config et autres variables globales sont définies dans config.js
// Ce fichier contient les fonctions métier (saveSettings, testLaraApiKeys, etc.)

// ==================== Initialisation ====================

document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
    loadConfigFromStorage();

    // Debug: Afficher l'URL du backend utilisé
    console.log('🚀 Application initialisée');
    console.log('📍 Backend URL:', config.lara.baseUrl);
    console.log('⚙️  Service:', config.translationService);

    if (!hasValidConfig()) {
        openSettingsModal();
    } else {
        initializeForCurrentService();
    }
});

function setupEventListeners() {
    // Boutons principaux
    document.getElementById('translateBtn').addEventListener('click', testTranslation);
    document.getElementById('swapBtn').addEventListener('click', swapLanguages);
    document.getElementById('sourceText').addEventListener('input', updateTranslateButton);

    // Sélecteurs de configuration
    document.getElementById('domain').addEventListener('change', () => {
        loadGlossaries();
        if (config.translationService === 'lara') {
            loadLaraTemplates();
        }
    });
    document.getElementById('sourceLang').addEventListener('change', () => {
        loadGlossaries();
        if (config.translationService === 'lara') {
            loadLaraTemplates();
        }
    });
    document.getElementById('targetLang').addEventListener('change', () => {
        loadGlossaries();
        if (config.translationService === 'lara') {
            loadLaraTemplates();
        }
    });

    // Modes texte/fichier
    document.getElementById('textModeBtn').addEventListener('click', () => switchMode('text'));
    document.getElementById('fileModeBtn').addEventListener('click', () => switchMode('file'));

    // Paramètres
    document.getElementById('settingsBtn').addEventListener('click', openSettingsModal);
    document.getElementById('settingsModalClose').addEventListener('click', closeSettingsModal);
    document.getElementById('cancelSettings').addEventListener('click', closeSettingsModal);
    document.getElementById('saveSettings').addEventListener('click', saveSettings);

    // Service de traduction
    document.getElementById('translationService').addEventListener('change', handleServiceChange);

    // Gestion des fichiers
    setupFileHandlers();

    // Glossaires (Lexa uniquement)
    setupGlossaryHandlers();

    // Templates (Lara uniquement)
    try {
        setupTemplatesHandlers();
    } catch (error) {
        console.error('Erreur lors de la configuration des templates:', error);
    }

    // Fermeture des modals en cliquant à l'extérieur
    setupModalCloseHandlers();
}

function setupFileHandlers() {
    const fileUpload = document.getElementById('fileUpload');
    const fileInput = document.getElementById('fileInput');

    fileUpload.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', handleFileSelect);

    fileUpload.addEventListener('dragover', (e) => {
        e.preventDefault();
        fileUpload.classList.add('dragover');
    });

    fileUpload.addEventListener('dragleave', () => {
        fileUpload.classList.remove('dragover');
    });

    fileUpload.addEventListener('drop', (e) => {
        e.preventDefault();
        fileUpload.classList.remove('dragover');
        handleFileDrop(e);
    });
}

function setupGlossaryHandlers() {
    document.getElementById('addGlossaryBtn').addEventListener('click', openGlossaryModal);
    document.getElementById('modalClose').addEventListener('click', closeGlossaryModal);
    document.getElementById('cancelGlossary').addEventListener('click', closeGlossaryModal);
    document.getElementById('createGlossary').addEventListener('click', createPersonalGlossary);

    document.getElementById('personalGlossariesBtn').addEventListener('click', openPersonalGlossariesModal);
    document.getElementById('personalModalClose').addEventListener('click', closePersonalGlossariesModal);
    document.getElementById('cancelPersonalGlossaries').addEventListener('click', closePersonalGlossariesModal);

    const csvUpload = document.getElementById('csvUpload');
    const csvInput = document.getElementById('csvInput');

    csvUpload.addEventListener('click', () => csvInput.click());
    csvInput.addEventListener('change', handleCsvSelect);

    document.getElementById('glossaryName').addEventListener('input', validateGlossaryForm);
    document.getElementById('glossarySourceLang').addEventListener('change', validateGlossaryForm);
    document.getElementById('glossaryTargetLang').addEventListener('change', validateGlossaryForm);

    csvUpload.addEventListener('dragover', (e) => {
        e.preventDefault();
        csvUpload.classList.add('dragover');
    });

    csvUpload.addEventListener('dragleave', () => {
        csvUpload.classList.remove('dragover');
    });

    csvUpload.addEventListener('drop', (e) => {
        e.preventDefault();
        csvUpload.classList.remove('dragover');
        handleCsvDrop(e);
    });
}

function setupTemplatesHandlers() {
    // Ces éléments n'existent que dans l'écran des templates
    // On les configure de manière défensive
    const viewTemplatesBtn = document.getElementById('viewTemplatesBtn');
    const backFromTemplatesBtn = document.getElementById('backFromTemplates');

    if (viewTemplatesBtn) {
        viewTemplatesBtn.addEventListener('click', openTemplatesScreen);
    }
    if (backFromTemplatesBtn) {
        backFromTemplatesBtn.addEventListener('click', closeTemplatesScreen);
    }
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

// ==================== Gestion de la configuration ====================

function loadConfigFromStorage() {
    try {
        const stored = localStorage.getItem('translation_config');
        if (stored) {
            const parsed = JSON.parse(stored);
            config = { ...config, ...parsed };

            // Remplir les champs du modal de paramètres
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

            if (config.lara.translationMemoryIds) {
                document.getElementById('laraMemoryIds').value = config.lara.translationMemoryIds;
            }

            if (config.lara.glossaryIds) {
                document.getElementById('laraGlossaryIds').value = config.lara.glossaryIds;
            }
        }

        // Mettre à jour l'affichage du mode
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
        serviceModeElement.style.color = '#dc2626'; // Rouge
    } else if (config.translationService === 'lexa') {
        serviceModeElement.textContent = 'Lexa';
        serviceModeElement.style.color = '#059669'; // Vert
    } else if (config.translationService === 'lara') {
        serviceModeElement.textContent = 'Lara';
        serviceModeElement.style.color = '#059669'; // Vert
    }
}

function hasValidConfig() {
    if (config.translationService === 'lexa') {
        return !!config.lexa.apiKey;
    } else {
        return !!(config.lara.accessKeyId && config.lara.accessKeySecret);
    }
}

function handleServiceChange() {
    const service = document.getElementById('translationService').value;
    config.translationService = service;

    // Afficher/masquer la section Lara
    const laraSection = document.getElementById('laraSettings');
    const lexaApiKeyHelp = document.getElementById('lexaApiKeyHelp');

    if (service === 'lexa') {
        laraSection.classList.add('hidden');
        lexaApiKeyHelp.textContent = 'Cette clé est nécessaire pour accéder aux services de traduction Lexamt';
    } else {
        laraSection.classList.remove('hidden');
        lexaApiKeyHelp.textContent = 'Cette clé est nécessaire même en mode Lara pour récupérer la liste des langues';
    }

    // Mettre à jour l'affichage du mode
    updateServiceModeDisplay();

    // Mettre à jour la visibilité des options Lara dans l'écran principal
    updateLaraOptionsVisibility();
}

function initializeForCurrentService() {
    updateServiceModeDisplay();
    updateLaraOptionsVisibility();

    if (config.translationService === 'lexa') {
        loadLanguages();
    } else {
        loadLaraLanguages();
        // Synchroniser les valeurs depuis la config
        syncLaraOptionsFromConfig();
    }
}

function updateLaraOptionsVisibility() {
    const laraStyleGroup = document.getElementById('laraStyleGroup');
    const laraInstructionsSection = document.getElementById('laraInstructionsSection');
    const laraMemoriesSection = document.getElementById('laraMemoriesSection');
    const domainGroup = document.getElementById('domainGroup');
    const glossarySection = document.getElementById('glossarySection');

    const laraTemplateSection = document.getElementById('laraTemplateSection');
    const selectedTemplateInfo = document.getElementById('selectedTemplateInfo');

    if (config.translationService === 'lara') {
        // Mode Lara : afficher le style, les instructions, le sélecteur de template, afficher le domaine
        if (laraStyleGroup) laraStyleGroup.style.display = 'block';
        if (laraInstructionsSection) laraInstructionsSection.style.display = 'block';
        if (laraTemplateSection) {
            laraTemplateSection.style.display = 'block';
            loadLaraTemplates();
        }
        if (domainGroup) domainGroup.style.display = 'block';
        if (glossarySection) glossarySection.style.display = 'none';
        // L'affichage des infos template se fera lors de la sélection d'un template
    } else {
        // Mode Lexa : masquer les options Lara, afficher domaine
        if (laraStyleGroup) laraStyleGroup.style.display = 'none';
        if (laraInstructionsSection) laraInstructionsSection.style.display = 'none';
        if (laraTemplateSection) laraTemplateSection.style.display = 'none';
        if (selectedTemplateInfo) selectedTemplateInfo.style.display = 'none';
        if (domainGroup) domainGroup.style.display = 'block';
        // Les glossaires s'affichent seulement en mode fichier pour Lexa
    }
}

function syncLaraOptionsFromConfig() {
    const styleSelect = document.getElementById('laraStyleMain');
    const instructionsTextarea = document.getElementById('laraInstructionsMain');

    if (styleSelect && config.lara.style) {
        styleSelect.value = config.lara.style;
    }

    if (instructionsTextarea && config.lara.instructions) {
        instructionsTextarea.value = config.lara.instructions;
    }
}

// ==================== Gestion des modes ====================

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

        // Glossaires uniquement pour Lexa
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

// ==================== Gestion des fichiers ====================

function handleFileSelect(event) {
    const files = Array.from(event.target.files);
    addFiles(files);
}

function handleFileDrop(event) {
    const files = Array.from(event.dataTransfer.files);
    addFiles(files);
}

function addFiles(files) {
    files.forEach(file => {
        if (!selectedFiles.find(f => f.name === file.name && f.size === file.size)) {
            selectedFiles.push(file);
        }
    });
    updateFileList();
    updateTranslateButton();
}

function removeFile(index) {
    selectedFiles.splice(index, 1);
    updateFileList();
    updateTranslateButton();
}

function updateFileList() {
    const fileList = document.getElementById('fileList');
    fileList.innerHTML = '';

    selectedFiles.forEach((file, index) => {
        const fileItem = document.createElement('div');
        fileItem.className = 'file-item';

        const fileName = document.createElement('div');
        fileName.className = 'file-item-name';
        fileName.textContent = file.name;

        const fileSize = document.createElement('div');
        fileSize.className = 'file-item-size';
        fileSize.textContent = formatFileSize(file.size);

        const removeBtn = document.createElement('button');
        removeBtn.className = 'file-remove';
        removeBtn.textContent = '×';
        removeBtn.onclick = () => removeFile(index);

        fileItem.appendChild(fileName);
        fileItem.appendChild(fileSize);
        fileItem.appendChild(removeBtn);
        fileList.appendChild(fileItem);
    });
}

function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

// ==================== Chargement des langues - LEXA ====================

async function loadLanguages() {
    if (!config.lexa.apiKey) return;

    const sourceSelect = document.getElementById('sourceLang');
    const targetSelect = document.getElementById('targetLang');

    sourceSelect.innerHTML = '<option value="">Chargement des langues...</option>';
    targetSelect.innerHTML = '<option value="">Chargement des langues...</option>';
    sourceSelect.disabled = true;
    targetSelect.disabled = true;

    try {
        const response = await fetch(`${config.lexa.baseUrl}/languages/`, {
            headers: {
                'Authorization': `Bearer ${config.lexa.apiKey}`,
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            throw new Error(`Erreur ${response.status}: ${response.statusText}`);
        }

        const languages = await response.json();
        availableLanguages = languages;

        sourceSelect.innerHTML = '';
        targetSelect.innerHTML = '';

        languages.forEach(language => {
            const sourceOption = document.createElement('option');
            sourceOption.value = language.language_code;
            sourceOption.textContent = language.name;
            sourceSelect.appendChild(sourceOption);

            const targetOption = document.createElement('option');
            targetOption.value = language.language_code;
            targetOption.textContent = language.name;
            targetSelect.appendChild(targetOption);
        });

        const frLanguage = languages.find(lang => lang.language_code === 'FR');
        const enLanguage = languages.find(lang => lang.language_code === 'EN');

        if (frLanguage) {
            sourceSelect.value = 'FR';
        } else if (languages.length > 0) {
            sourceSelect.value = languages[0].language_code;
        }

        if (enLanguage) {
            targetSelect.value = 'EN';
        } else if (languages.length > 1) {
            targetSelect.value = languages[1].language_code;
        } else if (languages.length > 0) {
            targetSelect.value = languages[0].language_code;
        }

        sourceSelect.disabled = false;
        targetSelect.disabled = false;

        await loadDomains();

    } catch (error) {
        console.error('Erreur lors du chargement des langues:', error);
        sourceSelect.innerHTML = '<option value="">Erreur de chargement</option>';
        targetSelect.innerHTML = '<option value="">Erreur de chargement</option>';
        showMessage('Erreur lors du chargement des langues. Vérifiez votre clé API.', 'error');
    }
}

async function loadDomains() {
    // En mode Lara, on n'a pas besoin de vérifier availableLanguages
    if (!config.lexa.apiKey) return;

    const domainSelect = document.getElementById('domain');
    domainSelect.innerHTML = '<option value="">Chargement...</option>';

    try {
        const response = await fetch(`${config.lexa.baseUrl}/domains/`, {
            headers: {
                'Authorization': `Bearer ${config.lexa.apiKey}`,
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            throw new Error(`Erreur ${response.status}: ${response.statusText}`);
        }

        const domains = await response.json();
        availableDomains = domains;

        domainSelect.innerHTML = '<option value="">Sélectionnez un domaine</option>';
        domains.forEach(domain => {
            const option = document.createElement('option');
            option.value = domain.id;
            option.textContent = domain.name;
            option.dataset.name = domain.name;
            domainSelect.appendChild(option);
        });

        if (config.translationService === 'lexa') {
            showMessage('Domaines et langues chargés avec succès!', 'success');
        }

    } catch (error) {
        console.error('Erreur lors du chargement des domaines:', error);
        domainSelect.innerHTML = '<option value="">Erreur de chargement</option>';
        showMessage('Erreur lors du chargement des domaines. Vérifiez votre clé API.', 'error');
    }
}

async function loadLaraTemplates() {
    const templateSelect = document.getElementById('laraTemplateMain');
    const templateHelpText = document.getElementById('templateHelpText');

    if (!templateSelect) return;

    templateSelect.innerHTML = '<option value="">Chargement des templates...</option>';

    // Récupérer les valeurs actuelles du domaine et des langues
    const domainSelect = document.getElementById('domain');
    const selectedOption = domainSelect.selectedOptions[0];
    const domain = selectedOption?.dataset?.name || '';  // Utiliser le nom, pas l'ID
    const sourceLang = document.getElementById('sourceLang').value;
    const targetLang = document.getElementById('targetLang').value;

    try {
        let url = `${config.lara.baseUrl}/templates`;

        // Filtrer dès qu'on a les langues (le domaine est optionnel)
        if (sourceLang && targetLang) {
            const params = new URLSearchParams();
            if (domain) params.append('domain', domain);
            params.append('sourceLanguage', sourceLang);
            params.append('targetLanguage', targetLang);
            url += `/find?${params.toString()}`;
            console.log('🔍 [app.js] Chargement templates avec:', { domain, sourceLang, targetLang, url });
        }

        const response = await fetch(url);

        if (!response.ok) {
            throw new Error(`Erreur ${response.status}: ${response.statusText}`);
        }

        const templates = await response.json();

        if (templates.length === 0) {
            templateSelect.innerHTML = '<option value="">Aucun template disponible pour cette combinaison</option>';
        } else {
            templateSelect.innerHTML = '<option value="">Sélectionnez un template</option>';
            templates.forEach(template => {
                const option = document.createElement('option');
                option.value = template.id;
                option.textContent = template.name;
                // Stocker les IDs pour les requêtes API et les noms pour l'affichage
                option.dataset.memoryId = template.translationMemoryId || '';
                option.dataset.glossaryId = template.glossaryId || '';
                option.dataset.memoryName = template.translationMemoryName || '';
                option.dataset.glossaryName = template.glossaryName || '';
                templateSelect.appendChild(option);
            });
        }

        if (templateHelpText) templateHelpText.style.display = 'block';

        // Ajouter un event listener pour afficher les infos quand un template est sélectionné
        templateSelect.removeEventListener('change', handleTemplateChange);
        templateSelect.addEventListener('change', handleTemplateChange);

    } catch (error) {
        console.error('Erreur lors du chargement des templates:', error);
        templateSelect.innerHTML = '<option value="">Erreur de chargement</option>';
        showMessage('Erreur lors du chargement des templates de traduction.', 'error');
    }
}

function handleTemplateChange(event) {
    const selectedOption = event.target.selectedOptions[0];
    const infoDiv = document.getElementById('selectedTemplateInfo');
    const memorySpan = document.getElementById('selectedTemplateMemory');
    const glossarySpan = document.getElementById('selectedTemplateGlossary');

    if (!selectedOption || !selectedOption.value) {
        // Aucun template sélectionné, masquer les infos
        if (infoDiv) infoDiv.style.display = 'none';
        return;
    }

    // Récupérer les données du template
    const memoryId = selectedOption.dataset.memoryId || '';
    const glossaryId = selectedOption.dataset.glossaryId || '';
    const memoryName = selectedOption.dataset.memoryName || memoryId || 'Non défini';
    const glossaryName = selectedOption.dataset.glossaryName || glossaryId || 'Non défini';

    // Afficher les informations
    if (memorySpan) memorySpan.textContent = `🗂️ Mémoire: ${memoryName}`;
    if (glossarySpan) glossarySpan.textContent = `📖 Glossaire: ${glossaryName}`;
    if (infoDiv) infoDiv.style.display = 'block';
}

async function loadGlossaries() {
    if (config.translationService !== 'lexa') return;

    const domainId = document.getElementById('domain').value;
    const sourceLang = document.getElementById('sourceLang').value;
    const targetLang = document.getElementById('targetLang').value;
    const glossarySelect = document.getElementById('glossary');

    if (!config.lexa.apiKey || !domainId) {
        glossarySelect.innerHTML = '<option value="">Sélectionnez d\'abord un domaine</option>';
        glossarySelect.disabled = true;
        return;
    }

    glossarySelect.innerHTML = '<option value="">Chargement des glossaires...</option>';
    glossarySelect.disabled = true;

    try {
        const url = `${config.lexa.baseUrl}/domain/${domainId}/glossaries/?source_language=${sourceLang}&target_language=${targetLang}`;

        const response = await fetch(url, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${config.lexa.apiKey}`,
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            throw new Error(`Erreur ${response.status}: ${response.statusText}`);
        }

        const glossaries = await response.json();

        glossarySelect.innerHTML = '<option value="">Aucun glossaire (optionnel)</option>';

        if (glossaries.length === 0) {
            glossarySelect.innerHTML += '<option value="" disabled>Aucun glossaire disponible pour cette paire de langues</option>';
        } else {
            glossaries.forEach(glossary => {
                const option = document.createElement('option');
                option.value = glossary.id;
                option.textContent = `${glossary.name} (${glossary.file_size})`;
                option.dataset.fileUrl = glossary.file_url;
                glossarySelect.appendChild(option);
            });
        }

        glossarySelect.addEventListener('change', () => {
            if (glossarySelect.value) {
                clearPersonalGlossary();
            }
        });

        glossarySelect.disabled = false;

    } catch (error) {
        console.error('Erreur lors du chargement des glossaires:', error);
        glossarySelect.innerHTML = '<option value="">Erreur de chargement</option>';
        showMessage('Erreur lors du chargement des glossaires.', 'error');
    }
}

// ==================== Chargement des langues - LARA ====================

async function loadLaraLanguages() {
    // Pour Lara, on utilise des codes de langue standards ISO 639-1
    // Liste des langues les plus courantes
    const commonLanguages = [
        { code: 'en', name: 'English' },
        { code: 'fr', name: 'Français' },
        { code: 'es', name: 'Español' },
        { code: 'de', name: 'Deutsch' },
        { code: 'it', name: 'Italiano' },
        { code: 'pt', name: 'Português' },
        { code: 'nl', name: 'Nederlands' },
        { code: 'pl', name: 'Polski' },
        { code: 'ru', name: 'Русский' },
        { code: 'ja', name: '日本語' },
        { code: 'zh', name: '中文' },
        { code: 'ar', name: 'العربية' }
    ];

    const sourceSelect = document.getElementById('sourceLang');
    const targetSelect = document.getElementById('targetLang');

    sourceSelect.innerHTML = '';
    targetSelect.innerHTML = '';

    commonLanguages.forEach(lang => {
        const sourceOption = document.createElement('option');
        sourceOption.value = lang.code;
        sourceOption.textContent = lang.name;
        sourceSelect.appendChild(sourceOption);

        const targetOption = document.createElement('option');
        targetOption.value = lang.code;
        targetOption.textContent = lang.name;
        targetSelect.appendChild(targetOption);
    });

    sourceSelect.value = 'fr';
    targetSelect.value = 'en';

    sourceSelect.disabled = false;
    targetSelect.disabled = false;

    // Charger les domaines (utilise l'API Lexa)
    await loadDomains();

    showMessage('Interface LaraTranslate initialisée!', 'success');
}

// ==================== Inversion des langues ====================

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

// ==================== Traduction - Dispatch ====================

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

// ==================== Traduction LEXA ====================

async function translateWithLexa() {
    const domainSelect = document.getElementById('domain');
    const domainId = domainSelect.value;
    const domainName = domainSelect.selectedOptions[0]?.dataset.name;
    const sourceLang = document.getElementById('sourceLang').value;
    const targetLang = document.getElementById('targetLang').value;
    const glossaryId = document.getElementById('glossary').value;

    if (currentMode === 'text') {
        const sourceText = document.getElementById('sourceText').value.trim();
        if (!sourceText) {
            showMessage('Veuillez entrer du texte à traduire.', 'error');
            return;
        }

        await translateTextLexa(sourceText, sourceLang, targetLang, domainName, glossaryId);
    } else {
        if (selectedFiles.length === 0) {
            showMessage('Veuillez sélectionner au moins un fichier.', 'error');
            return;
        }

        await translateFilesLexa(selectedFiles, sourceLang, targetLang, domainName, glossaryId);
    }
}

async function translateTextLexa(sourceText, sourceLang, targetLang, domainName, glossaryId) {
    setLoading(true);

    try {
        const requestBody = {
            action: 'text_translate',
            text: sourceText,
            source_language: sourceLang,
            target_language: targetLang
        };

        if (domainName) {
            requestBody.domain_name = domainName;
        }

        const finalGlossaryId = selectedPersonalGlossary ? selectedPersonalGlossary.id : glossaryId;
        if (finalGlossaryId) {
            requestBody.glossary_id = parseInt(finalGlossaryId);
        }

        const response = await fetch(`${config.lexa.baseUrl}/translate/`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${config.lexa.apiKey}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestBody)
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `Erreur ${response.status}`);
        }

        const result = await response.json();

        const qualityFeedback = document.getElementById('qualityFeedback');

        document.getElementById('resultText').value = result.translated_text;
        qualityFeedback.style.display = 'none'; // Pas de module qualité pour Lexa

        let successMessage = 'Traduction terminée avec succès !';
        if (selectedPersonalGlossary) {
            successMessage += ` (Glossaire personnel utilisé: ${selectedPersonalGlossary.name})`;
        } else if (glossaryId) {
            const glossaryName = document.getElementById('glossary').selectedOptions[0]?.textContent;
            successMessage += ` (Glossaire utilisé: ${glossaryName})`;
        }
        showMessage(successMessage, 'success');

    } catch (error) {
        console.error('Erreur lors de la traduction:', error);
        showMessage(`Erreur: ${error.message}`, 'error');
    } finally {
        setLoading(false);
    }
}

async function translateFilesLexa(files, sourceLang, targetLang, domainName, glossaryId) {
    setLoading(true);

    try {
        const formData = new FormData();
        formData.append('action', 'file_translate');
        formData.append('source_language', sourceLang);
        formData.append('target_language', targetLang);

        if (domainName) {
            formData.append('domain_name', domainName);
        }

        const finalGlossaryId = selectedPersonalGlossary ? selectedPersonalGlossary.id : glossaryId;
        if (finalGlossaryId) {
            formData.append('glossary', finalGlossaryId);
        }

        files.forEach((file, index) => {
            formData.append(`document[]`, file);
        });

        const response = await fetch(`${config.lexa.baseUrl}/translate/`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${config.lexa.apiKey}`
            },
            body: formData
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `Erreur ${response.status}`);
        }

        const results = await response.json();

        displayFileResults(results, files);

        let successMessage = `Traduction de ${files.length} fichier(s) lancée !`;
        if (selectedPersonalGlossary) {
            successMessage += ` (Glossaire personnel utilisé: ${selectedPersonalGlossary.name})`;
        } else if (glossaryId) {
            const glossaryName = document.getElementById('glossary').selectedOptions[0]?.textContent;
            successMessage += ` (Glossaire utilisé: ${glossaryName})`;
        }
        showMessage(successMessage, 'success');

    } catch (error) {
        console.error('Erreur lors de la traduction:', error);
        showMessage(`Erreur: ${error.message}`, 'error');
    } finally {
        setLoading(false);
    }
}

// ==================== Traduction LARA ====================

async function translateWithLara() {
    const sourceLang = document.getElementById('sourceLang').value;
    const targetLang = document.getElementById('targetLang').value;

    if (currentMode === 'text') {
        const sourceText = document.getElementById('sourceText').value.trim();
        if (!sourceText) {
            showMessage('Veuillez entrer du texte à traduire.', 'error');
            return;
        }

        await translateTextLara(sourceText, sourceLang, targetLang);
    } else {
        if (selectedFiles.length === 0) {
            showMessage('Veuillez sélectionner au moins un fichier.', 'error');
            return;
        }

        await translateFilesLara(selectedFiles, sourceLang, targetLang);
    }
}

async function translateTextLara(sourceText, sourceLang, targetLang) {
    setLoading(true);

    try {
        // Récupérer les valeurs depuis l'écran principal
        const styleMain = document.getElementById('laraStyleMain')?.value;
        const instructionsMain = document.getElementById('laraInstructionsMain')?.value.trim();
        const domainSelect = document.getElementById('domain');
        const domainName = domainSelect.selectedOptions[0]?.dataset.name;

        // Récupérer le template sélectionné et ses ressources
        const templateSelect = document.getElementById('laraTemplateMain');
        const selectedTemplateOption = templateSelect?.selectedOptions[0];
        const selectedMemory = selectedTemplateOption?.dataset.memoryId || '';
        const selectedGlossary = selectedTemplateOption?.dataset.glossaryId || '';

        const requestBody = {
            accessKeyId: config.lara.accessKeyId,
            accessKeySecret: config.lara.accessKeySecret,
            text: sourceText,
            target: targetLang
        };

        if (sourceLang) {
            requestBody.source = sourceLang;
        }

        // Ajouter le domaine si sélectionné
        if (domainName) {
            requestBody.domain = domainName;
        }

        // Utiliser les valeurs de l'écran principal en priorité
        if (styleMain) {
            requestBody.style = styleMain;
        } else if (config.lara.style) {
            requestBody.style = config.lara.style;
        }

        if (instructionsMain) {
            requestBody.instructions = instructionsMain;
        } else if (config.lara.instructions) {
            requestBody.instructions = config.lara.instructions;
        }

        // Utiliser la mémoire du template sélectionné en priorité
        if (selectedMemory) {
            requestBody.adaptTo = selectedMemory;
        } else if (config.lara.translationMemoryIds) {
            requestBody.adaptTo = config.lara.translationMemoryIds;
        }

        // Utiliser le glossaire du template sélectionné en priorité
        if (selectedGlossary) {
            requestBody.glossaries = selectedGlossary;
        } else if (config.lara.glossaryIds) {
            requestBody.glossaries = config.lara.glossaryIds;
        }

        const response = await fetch(`${config.lara.baseUrl}/translate-text`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestBody)
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.message || errorData.detail || `Erreur ${response.status}`);
        }

        const result = await response.json();

        const qualityFeedback = document.getElementById('qualityFeedback');
        const qualityFeedbackText = document.getElementById('qualityFeedbackText');

        // Adapter selon le format de réponse de Lara
        const translatedText = result.translation || result.translated_text || result.text;
        document.getElementById('resultText').value = translatedText;

        // Afficher le feedback qualité si disponible
        console.log('Résultat Lara complet:', result); // Debug

        // Chercher le feedback dans plusieurs emplacements possibles
        let feedback = result.quality_feedback || result.feedback || result.quality || result.qualityFeedback;

        // Chercher aussi dans les metadata si disponibles
        if (!feedback && result.metadata) {
            feedback = result.metadata.quality || result.metadata.qualityFeedback || result.metadata.quality_feedback;
        }

        if (feedback) {
            console.log('Feedback qualité trouvé:', feedback); // Debug

            // Formater le feedback pour l'affichage
            let feedbackText;
            if (typeof feedback === 'string') {
                feedbackText = feedback;
            } else if (typeof feedback === 'object') {
                // Si c'est un objet, le formater joliment
                if (feedback.score !== undefined || feedback.comments || feedback.suggestions) {
                    feedbackText = '';
                    if (feedback.score !== undefined) feedbackText += `Score: ${feedback.score}\n`;
                    if (feedback.comments) feedbackText += `Commentaires: ${feedback.comments}\n`;
                    if (feedback.suggestions) feedbackText += `Suggestions: ${feedback.suggestions}\n`;
                } else {
                    feedbackText = JSON.stringify(feedback, null, 2);
                }
            } else {
                feedbackText = String(feedback);
            }

            qualityFeedbackText.textContent = feedbackText;
            qualityFeedback.style.display = 'block';
        } else {
            console.log('Aucun feedback qualité trouvé dans:', Object.keys(result)); // Debug
            qualityFeedback.style.display = 'none';
        }

        showMessage('Traduction LaraTranslate terminée avec succès !', 'success');

    } catch (error) {
        console.error('Erreur lors de la traduction Lara:', error);
        showMessage(`Erreur Lara: ${error.message}`, 'error');
    } finally {
        setLoading(false);
    }
}

async function translateFilesLara(files, sourceLang, targetLang) {
    setLoading(true);

    try {
        // Récupérer les valeurs depuis l'écran principal
        const styleMain = document.getElementById('laraStyleMain')?.value;
        const domainSelect = document.getElementById('domain');
        const domainName = domainSelect.selectedOptions[0]?.dataset.name;

        // Récupérer le template sélectionné et ses ressources
        const templateSelect = document.getElementById('laraTemplateMain');
        const selectedTemplateOption = templateSelect?.selectedOptions[0];
        const selectedMemory = selectedTemplateOption?.dataset.memoryId || '';
        const selectedGlossary = selectedTemplateOption?.dataset.glossaryId || '';

        // Pour les documents, on traite chaque fichier séparément
        const results = [];

        for (const file of files) {
            const formData = new FormData();
            formData.append('file', file);
            formData.append('accessKeyId', config.lara.accessKeyId);
            formData.append('accessKeySecret', config.lara.accessKeySecret);
            formData.append('target', targetLang);

            if (sourceLang) {
                formData.append('source', sourceLang);
            }

            // Ajouter le domaine si sélectionné
            if (domainName) {
                formData.append('domain', domainName);
            }

            // Utiliser les valeurs de l'écran principal en priorité
            if (styleMain) {
                formData.append('style', styleMain);
            } else if (config.lara.style) {
                formData.append('style', config.lara.style);
            }

            // Utiliser la mémoire du template sélectionné en priorité
            if (selectedMemory) {
                formData.append('adaptTo', selectedMemory);
            } else if (config.lara.translationMemoryIds) {
                formData.append('adaptTo', config.lara.translationMemoryIds);
            }

            // Utiliser le glossaire du template sélectionné en priorité
            if (selectedGlossary) {
                formData.append('glossaries', selectedGlossary);
            } else if (config.lara.glossaryIds) {
                formData.append('glossaries', config.lara.glossaryIds);
            }

            const response = await fetch(`${config.lara.baseUrl}/translate-document`, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                results.push({
                    source_file_name: file.name,
                    status: 'Error',
                    error: errorData.message || `Erreur ${response.status}`
                });
            } else {
                const result = await response.json();
                console.log('Résultat Lara reçu:', result);

                // Si downloadUrl est une URL relative, la convertir en URL absolue
                if (result.downloadUrl && result.downloadUrl.startsWith('/')) {
                    // Utiliser le même baseUrl que celui configuré pour les appels API
                    const baseUrl = config.lara.baseUrl;
                    console.log('🔍 [DEBUG] baseUrl actuel:', baseUrl);
                    console.log('🔍 [DEBUG] downloadUrl reçu:', result.downloadUrl);
                    // Extraire le préfixe (http://localhost:8001 ou vide)
                    if (baseUrl.startsWith('http')) {
                        // En local: baseUrl = "http://localhost:8001/lara-django/api/lara"
                        // On extrait "http://localhost:8001"
                        const urlObj = new URL(baseUrl);
                        result.downloadUrl = `${urlObj.origin}${result.downloadUrl}`;
                        console.log('🔧 [DEBUG] URL convertie:', result.downloadUrl);
                    }
                    // En production, si baseUrl est relatif, downloadUrl reste relatif (ce qui est correct)
                }

                results.push({
                    ...result,
                    source_file_name: file.name,
                    source_language: sourceLang,
                    target_language: targetLang
                });
            }
        }

        displayFileResults(results, files);

        showMessage(`Traduction de ${files.length} fichier(s) avec LaraTranslate lancée !`, 'success');

    } catch (error) {
        console.error('Erreur lors de la traduction Lara:', error);
        showMessage(`Erreur Lara: ${error.message}`, 'error');
    } finally {
        setLoading(false);
    }
}

// ==================== Affichage des résultats ====================

function displayFileResults(results, originalFiles) {
    const fileResults = document.getElementById('fileResults');
    const resultSection = document.getElementById('resultSection');
    const qualityFeedback = document.getElementById('qualityFeedback');

    // Masquer le feedback qualité en mode fichier
    qualityFeedback.style.display = 'none';
    resultSection.style.display = 'block';
    fileResults.style.display = 'block';

    fileResults.innerHTML = '';

    results.forEach((result, index) => {
        const fileResult = document.createElement('div');
        fileResult.className = 'file-result';

        const originalFileName = originalFiles[index]?.name || result.source_file_name || `Fichier ${index + 1}`;
        const status = result.status || 'Unknown';
        const statusClass = getStatusClass(status);

        fileResult.innerHTML = `
            <div class="file-result-header">
                ${originalFileName}
                <span class="status-badge ${statusClass}">${status}</span>
            </div>
            <div class="file-result-info">
                ${result.id ? `ID: ${result.id}<br>` : ''}
                Langues: ${result.source_language} → ${result.target_language}<br>
                ${result.created_at ? `Créé: ${formatDate(result.created_at)}<br>` : ''}
                ${result.updated_at ? `Mis à jour: ${formatDate(result.updated_at)}` : ''}
                ${result.error ? `<br><span style="color: #dc2626;">Erreur: ${result.error}</span>` : ''}
            </div>
            <div class="download-buttons" id="downloads-${index}">
                ${generateDownloadButtons(result)}
            </div>
        `;

        fileResults.appendChild(fileResult);
    });
}

function getStatusClass(status) {
    switch (status.toLowerCase()) {
        case 'translated':
            return 'status-translated';
        case 'processing':
        case 'pending':
        case 'initialized':
            return 'status-processing';
        case 'error':
        case 'failed':
            return 'status-error';
        default:
            return 'status-processing';
    }
}

function generateDownloadButtons(result) {
    console.log('generateDownloadButtons appelé avec:', result);
    let buttons = '';

    // Support pour le backend Django (downloadUrl) et l'ancien backend Node.js (translated_file)
    const downloadUrl = result.downloadUrl || result.translated_file;

    if (downloadUrl) {
        console.log('Bouton de téléchargement créé pour:', downloadUrl);
        buttons += `<a href="${downloadUrl}" class="download-btn" download>📄 Fichier traduit</a>`;
    }

    if (result.source_file) {
        buttons += `<a href="${result.source_file}" class="download-btn secondary" download>📄 Fichier source</a>`;
    }

    if (result.tmx_file) {
        buttons += `<a href="${result.tmx_file}" class="download-btn secondary" download>📄 TMX</a>`;
    }

    if (result.xliff_file) {
        buttons += `<a href="${result.xliff_file}" class="download-btn secondary" download>📄 XLIFF</a>`;
    }

    if (result.reviewed_file) {
        buttons += `<a href="${result.reviewed_file}" class="download-btn" download>📄 Fichier révisé</a>`;
    }

    if (!buttons) {
        buttons = '<span style="color: #6b7280; font-size: 12px;">Fichier en cours de traitement ou erreur</span>';
    }

    return buttons;
}

function formatDate(dateString) {
    if (!dateString) return 'N/A';
    try {
        return new Date(dateString).toLocaleString('fr-FR', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        });
    } catch (e) {
        return dateString;
    }
}

// ==================== Gestion des glossaires personnels (Lexa) ====================

function openGlossaryModal() {
    if (!config.lexa.apiKey) {
        showMessage('Veuillez entrer votre clé API Lexa pour ajouter un glossaire.', 'error');
        return;
    }

    const glossarySourceSelect = document.getElementById('glossarySourceLang');
    const glossaryTargetSelect = document.getElementById('glossaryTargetLang');

    glossarySourceSelect.innerHTML = '';
    glossaryTargetSelect.innerHTML = '';

    availableLanguages.forEach(language => {
        const sourceOption = document.createElement('option');
        sourceOption.value = language.language_code;
        sourceOption.textContent = language.name;
        glossarySourceSelect.appendChild(sourceOption);

        const targetOption = document.createElement('option');
        targetOption.value = language.language_code;
        targetOption.textContent = language.name;
        glossaryTargetSelect.appendChild(targetOption);
    });

    const frLanguage = availableLanguages.find(lang => lang.language_code === 'FR');
    const enLanguage = availableLanguages.find(lang => lang.language_code === 'EN');

    if (frLanguage) {
        glossarySourceSelect.value = 'FR';
    } else if (availableLanguages.length > 0) {
        glossarySourceSelect.value = availableLanguages[0].language_code;
    }

    if (enLanguage) {
        glossaryTargetSelect.value = 'EN';
    } else if (availableLanguages.length > 1) {
        glossaryTargetSelect.value = availableLanguages[1].language_code;
    } else if (availableLanguages.length > 0) {
        glossaryTargetSelect.value = availableLanguages[0].language_code;
    }

    document.getElementById('glossaryName').value = '';
    selectedCsvFile = null;
    updateCsvUploadDisplay();
    validateGlossaryForm();

    document.getElementById('glossaryModal').style.display = 'block';
}

function closeGlossaryModal() {
    document.getElementById('glossaryModal').style.display = 'none';
}

function handleCsvSelect(event) {
    const file = event.target.files[0];
    if (file) {
        if (!file.name.toLowerCase().endsWith('.csv')) {
            showMessage('Veuillez sélectionner un fichier CSV.', 'error');
            return;
        }
        selectedCsvFile = file;
        updateCsvUploadDisplay();
        validateGlossaryForm();
    }
}

function handleCsvDrop(event) {
    const files = Array.from(event.dataTransfer.files);
    const csvFile = files.find(file => file.name.toLowerCase().endsWith('.csv'));

    if (csvFile) {
        selectedCsvFile = csvFile;
        updateCsvUploadDisplay();
        validateGlossaryForm();
    } else {
        showMessage('Veuillez déposer un fichier CSV.', 'error');
    }
}

function updateCsvUploadDisplay() {
    const csvUpload = document.getElementById('csvUpload');
    const csvUploadText = document.getElementById('csvUploadText');

    if (selectedCsvFile) {
        csvUpload.classList.add('selected-csv');
        csvUploadText.innerHTML = `✓ ${selectedCsvFile.name}<br><small>${formatFileSize(selectedCsvFile.size)}</small>`;
    } else {
        csvUpload.classList.remove('selected-csv');
        csvUploadText.innerHTML = '📄 Cliquez pour sélectionner un fichier CSV<br>ou glissez-déposez ici';
    }
}

function validateGlossaryForm() {
    const name = document.getElementById('glossaryName').value.trim();
    const sourceLang = document.getElementById('glossarySourceLang').value;
    const targetLang = document.getElementById('glossaryTargetLang').value;
    const createBtn = document.getElementById('createGlossary');

    const isValid = name && sourceLang && targetLang && selectedCsvFile && sourceLang !== targetLang;
    createBtn.disabled = !isValid;
}

async function createPersonalGlossary() {
    const name = document.getElementById('glossaryName').value.trim();
    const sourceLang = document.getElementById('glossarySourceLang').value;
    const targetLang = document.getElementById('glossaryTargetLang').value;

    if (!selectedCsvFile) {
        showMessage('Veuillez sélectionner un fichier CSV.', 'error');
        return;
    }

    if (sourceLang === targetLang) {
        showMessage('Les langues source et cible doivent être différentes.', 'error');
        return;
    }

    const createBtn = document.getElementById('createGlossary');
    createBtn.disabled = true;
    createBtn.textContent = 'Création...';

    try {
        const formData = new FormData();
        formData.append('name', name);
        formData.append('source_language', sourceLang);
        formData.append('target_language', targetLang);
        formData.append('file', selectedCsvFile);

        const response = await fetch(`${config.lexa.baseUrl}/glossary/`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${config.lexa.apiKey}`
            },
            body: formData
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `Erreur ${response.status}`);
        }

        const result = await response.json();

        showMessage(`Glossaire "${name}" créé avec succès !`, 'success');
        closeGlossaryModal();

    } catch (error) {
        console.error('Erreur lors de la création du glossaire:', error);
        showMessage(`Erreur lors de la création du glossaire: ${error.message}`, 'error');
    } finally {
        createBtn.disabled = false;
        createBtn.textContent = 'Créer le glossaire';
    }
}

async function openPersonalGlossariesModal() {
    if (!config.lexa.apiKey) {
        showMessage('Veuillez entrer votre clé API Lexa pour accéder aux glossaires personnels.', 'error');
        return;
    }

    document.getElementById('personalGlossariesModal').style.display = 'block';
    await loadPersonalGlossaries();
}

function closePersonalGlossariesModal() {
    document.getElementById('personalGlossariesModal').style.display = 'none';
}

async function loadPersonalGlossaries() {
    const listContainer = document.getElementById('personalGlossariesList');

    listContainer.innerHTML = '<div class="empty-glossaires"><div class="spinner"></div>Chargement des glossaires...</div>';

    try {
        const response = await fetch(`${config.lexa.baseUrl}/glossaries/`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${config.lexa.apiKey}`,
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            throw new Error(`Erreur ${response.status}: ${response.statusText}`);
        }

        personalGlossaries = await response.json();
        displayPersonalGlossaries();

    } catch (error) {
        console.error('Erreur lors du chargement des glossaires personnels:', error);
        listContainer.innerHTML = '<div class="empty-glossaires">Erreur lors du chargement des glossaires personnels</div>';
        showMessage('Erreur lors du chargement des glossaires personnels.', 'error');
    }
}

function displayPersonalGlossaries() {
    const listContainer = document.getElementById('personalGlossariesList');

    if (personalGlossaries.length === 0) {
        listContainer.innerHTML = '<div class="empty-glossaires">Aucun glossaire personnel trouvé.<br>Créez-en un avec le bouton "+" !</div>';
        return;
    }

    listContainer.innerHTML = '';

    personalGlossaries.forEach(glossary => {
        const glossaryItem = document.createElement('div');
        glossaryItem.className = 'glossary-item';
        if (selectedPersonalGlossary && selectedPersonalGlossary.id === glossary.id) {
            glossaryItem.classList.add('selected');
        }

        glossaryItem.innerHTML = `
            <div class="glossary-info">
                <div class="glossary-name">${glossary.name}</div>
                <div class="glossary-details">
                    ${glossary.source_language} → ${glossary.target_language}<br>
                    Créé le ${formatDate(glossary.created_at)}
                </div>
            </div>
            <div class="glossary-actions">
                <button class="btn-select" onclick="selectPersonalGlossary(${glossary.id})">
                    ${selectedPersonalGlossary && selectedPersonalGlossary.id === glossary.id ? 'Sélectionné' : 'Sélectionner'}
                </button>
                <button class="btn-delete" onclick="deletePersonalGlossary(${glossary.id}, '${glossary.name}')">
                    Supprimer
                </button>
            </div>
        `;

        listContainer.appendChild(glossaryItem);
    });
}

function selectPersonalGlossary(glossaryId) {
    const glossary = personalGlossaries.find(g => g.id === glossaryId);
    if (glossary) {
        selectedPersonalGlossary = glossary;

        document.getElementById('glossary').value = '';

        document.getElementById('selectedPersonalGlossaryName').textContent = glossary.name;
        document.getElementById('selectedPersonalGlossary').style.display = 'block';

        displayPersonalGlossaries();

        showMessage(`Glossaire personnel "${glossary.name}" sélectionné.`, 'success');
    }
}

function clearPersonalGlossary() {
    selectedPersonalGlossary = null;
    document.getElementById('selectedPersonalGlossary').style.display = 'none';
    if (personalGlossaries.length > 0) {
        displayPersonalGlossaries();
    }
}

async function deletePersonalGlossary(glossaryId, glossaryName) {
    if (!confirm(`Êtes-vous sûr de vouloir supprimer le glossaire "${glossaryName}" ? Cette action est irréversible.`)) {
        return;
    }

    try {
        const response = await fetch(`${config.lexa.baseUrl}/glossary/${glossaryId}/`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${config.lexa.apiKey}`
            }
        });

        if (!response.ok) {
            throw new Error(`Erreur ${response.status}: ${response.statusText}`);
        }

        personalGlossaries = personalGlossaries.filter(g => g.id !== glossaryId);

        if (selectedPersonalGlossary && selectedPersonalGlossary.id === glossaryId) {
            clearPersonalGlossary();
        }

        displayPersonalGlossaries();

        showMessage(`Glossaire "${glossaryName}" supprimé avec succès.`, 'success');

    } catch (error) {
        console.error('Erreur lors de la suppression:', error);
        showMessage(`Erreur lors de la suppression: ${error.message}`, 'error');
    }
}

// ==================== Modal des paramètres ====================

function openSettingsModal() {
    // Charger les valeurs actuelles
    handleServiceChange();

    // Effacer le message précédent
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

            // Lire Style et Instructions depuis l'écran principal (pas depuis le setup)
            const styleMain = document.getElementById('laraStyleMain')?.value;
            const instructionsMain = document.getElementById('laraInstructionsMain')?.value.trim();
            if (styleMain) config.lara.style = styleMain;
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

// ==================== Utilitaires ====================

function setLoading(isLoading) {
    const loading = document.getElementById('loading');
    const translateBtn = document.getElementById('translateBtn');

    if (isLoading) {
        loading.style.display = 'block';
        translateBtn.disabled = true;
        translateBtn.textContent = 'Traduction...';
    } else {
        loading.style.display = 'none';
        updateTranslateButton();
        translateBtn.textContent = 'Traduire';
    }
}

function showMessage(text, type) {
    const messageDiv = document.getElementById('message');
    messageDiv.textContent = text;
    messageDiv.className = type;

    setTimeout(() => {
        messageDiv.textContent = '';
        messageDiv.className = '';
    }, 5000);
}

// ==================== Gestion des Templates ====================

async function openTemplatesScreen() {
    const screen = document.getElementById('templatesScreen');
    const container = document.querySelector('.container');
    const settingsModal = document.getElementById('settingsModal');

    if (!screen) return;

    // Masquer le container principal et le modal des paramètres
    if (container) {
        container.style.display = 'none';
    }
    if (settingsModal) {
        settingsModal.style.display = 'none';
    }

    // Afficher l'écran des templates
    screen.style.display = 'block';
    await loadTemplatesTable();
}

function closeTemplatesScreen() {
    const screen = document.getElementById('templatesScreen');
    const container = document.querySelector('.container');

    if (screen) {
        screen.style.display = 'none';
    }

    // Réafficher le container principal
    if (container) {
        container.style.display = 'block';
    }
}

async function loadTemplates() {
    const tableBody = document.getElementById('templatesTableBody');
    const messageDiv = document.getElementById('templatesMessage');

    if (!tableBody) return;

    // Afficher un message de chargement
    tableBody.innerHTML = '<tr><td colspan="9" style="text-align: center; padding: 20px;">Chargement des templates...</td></tr>';

    try {
        // Utiliser l'URL complète du serveur
        const serverUrl = config.lara.baseUrl;
        const response = await fetch(`${serverUrl}/templates`);

        if (!response.ok) {
            throw new Error('Erreur lors du chargement des templates');
        }

        const templates = await response.json();

        if (!templates || templates.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="9" style="text-align: center; padding: 20px;">Aucun template trouvé</td></tr>';
            return;
        }

        // Trier les templates: template par défaut en premier, puis par domaine
        templates.sort((a, b) => {
            if (a.isDefault) return -1;
            if (b.isDefault) return 1;
            return a.domain.localeCompare(b.domain);
        });

        // Construire le tableau
        tableBody.innerHTML = templates.map(template => {
            const rowClass = template.isDefault ? 'template-default' : '';
            return `
                <tr class="${rowClass}">
                    <td>${escapeHtml(template.id)}</td>
                    <td>${escapeHtml(template.name)}</td>
                    <td>${escapeHtml(template.domain)}</td>
                    <td>${escapeHtml(template.sourceLanguage)}</td>
                    <td>${escapeHtml(template.targetLanguage)}</td>
                    <td>${template.translationMemoryName ? escapeHtml(template.translationMemoryName) : '<span class="template-empty">Non défini</span>'}</td>
                    <td>${template.glossaryName ? escapeHtml(template.glossaryName) : '<span class="template-empty">Non défini</span>'}</td>
                    <td>${template.description ? escapeHtml(template.description) : '<span class="template-empty">-</span>'}</td>
                    <td>${template.isDefault ? '<span class="badge-default">Défaut</span>' : ''}</td>
                </tr>
            `;
        }).join('');

        if (messageDiv) {
            messageDiv.innerHTML = `<p style="color: #059669; font-size: 14px;">✓ ${templates.length} templates chargés avec succès</p>`;
        }

    } catch (error) {
        console.error('Erreur lors du chargement des templates:', error);
        tableBody.innerHTML = '<tr><td colspan="9" style="text-align: center; padding: 20px; color: #dc2626;">Erreur lors du chargement des templates</td></tr>';

        if (messageDiv) {
            messageDiv.innerHTML = '<p style="color: #dc2626; font-size: 14px;">✗ Erreur: ' + escapeHtml(error.message) + '</p>';
        }
    }
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
