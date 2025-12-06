// Chargement des glossaires Lexa
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
        if (!response.ok) throw new Error(`Erreur ${response.status}: ${response.statusText}`);
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
            if (glossarySelect.value) clearPersonalGlossary();
        });
        glossarySelect.disabled = false;
    } catch (error) {
        console.error('Erreur lors du chargement des glossaires:', error);
        glossarySelect.innerHTML = '<option value="">Erreur de chargement</option>';
        showMessage('Erreur lors du chargement des glossaires.', 'error');
    }
}

// Traduction Lexa (texte et fichiers)
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
        if (domainName) requestBody.domain_name = domainName;
        const finalGlossaryId = selectedPersonalGlossary ? selectedPersonalGlossary.id : glossaryId;
        if (finalGlossaryId) requestBody.glossary_id = parseInt(finalGlossaryId);
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
        document.getElementById('resultText').value = result.translated_text;
        document.getElementById('qualityFeedback').style.display = 'none';
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
        if (domainName) formData.append('domain_name', domainName);
        const finalGlossaryId = selectedPersonalGlossary ? selectedPersonalGlossary.id : glossaryId;
        if (finalGlossaryId) formData.append('glossary', finalGlossaryId);
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

// Gestion des handlers glossaire
function setupGlossaryHandlers() {
    const personalGlossariesBtn = document.getElementById('personalGlossariesBtn');
    const addGlossaryBtn = document.getElementById('addGlossaryBtn');
    const cancelGlossary = document.getElementById('cancelGlossary');
    const createGlossary = document.getElementById('createGlossary');
    const glossaryName = document.getElementById('glossaryName');
    const cancelPersonalGlossaries = document.getElementById('cancelPersonalGlossaries');

    // CSV handlers
    const csvInput = document.getElementById('csvInput');
    const csvUpload = document.getElementById('csvUpload');

    if (personalGlossariesBtn) {
        personalGlossariesBtn.addEventListener('click', openPersonalGlossariesModal);
    }
    if (addGlossaryBtn) {
        addGlossaryBtn.addEventListener('click', openGlossaryModal);
    }
    if (cancelGlossary) {
        cancelGlossary.addEventListener('click', closeGlossaryModal);
    }
    if (createGlossary) {
        createGlossary.addEventListener('click', createPersonalGlossary);
    }
    if (glossaryName) {
        glossaryName.addEventListener('input', validateGlossaryForm);
    }
    if (cancelPersonalGlossaries) {
        cancelPersonalGlossaries.addEventListener('click', closePersonalGlossariesModal);
    }

    if (csvInput) {
        csvInput.addEventListener('change', handleCsvSelect);
    }

    if (csvUpload) {
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
        csvUpload.addEventListener('click', () => {
            csvInput.click();
        });
    }
}

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
    const modal = document.getElementById('glossaryModal');
    if (modal) modal.style.display = 'none';
}

function openPersonalGlossariesModal() {
    if (!config.lexa.apiKey) {
        showMessage('Veuillez entrer votre clé API Lexa pour accéder aux glossaires personnels.', 'error');
        return;
    }
    const modal = document.getElementById('personalGlossariesModal');
    if (modal) modal.style.display = 'block';
    loadPersonalGlossaries();
}

function closePersonalGlossariesModal() {
    const modal = document.getElementById('personalGlossariesModal');
    if (modal) modal.style.display = 'none';
}

function clearPersonalGlossary() {
    selectedPersonalGlossary = null;
    const selectedDiv = document.getElementById('selectedPersonalGlossary');
    if (selectedDiv) selectedDiv.style.display = 'none';
    if (personalGlossaries.length > 0) {
        displayPersonalGlossaries();
    }
}

function validateGlossaryForm() {
    const name = document.getElementById('glossaryName').value.trim();
    const sourceLang = document.getElementById('glossarySourceLang').value;
    const targetLang = document.getElementById('glossaryTargetLang').value;
    const createBtn = document.getElementById('createGlossary');

    const isValid = name && sourceLang && targetLang && selectedCsvFile && sourceLang !== targetLang;
    if (createBtn) createBtn.disabled = !isValid;
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

async function loadPersonalGlossaries() {
    const listContainer = document.getElementById('personalGlossariesList');
    if (!listContainer) return;

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
    if (!listContainer) return;

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
        if (!response.ok) throw new Error(`Erreur ${response.status}: ${response.statusText}`);
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
        // Définir les valeurs par défaut
        const frLanguage = languages.find(lang => lang.language_code === 'FR');
        const enLanguage = languages.find(lang => lang.language_code === 'EN');
        if (frLanguage) sourceSelect.value = 'FR';
        else if (languages.length > 0) sourceSelect.value = languages[0].language_code;
        if (enLanguage) targetSelect.value = 'EN';
        else if (languages.length > 1) targetSelect.value = languages[1].language_code;
        else if (languages.length > 0) targetSelect.value = languages[0].language_code;

        // Restaurer les préférences utilisateur si disponibles
        if (config.preferences.sourceLang) {
            const savedSource = languages.find(lang => lang.language_code === config.preferences.sourceLang);
            if (savedSource) sourceSelect.value = config.preferences.sourceLang;
        }
        if (config.preferences.targetLang) {
            const savedTarget = languages.find(lang => lang.language_code === config.preferences.targetLang);
            if (savedTarget) targetSelect.value = config.preferences.targetLang;
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
    if (!config.lexa.apiKey) return;
    const domainSelect = document.getElementById('domain');
    domainSelect.innerHTML = '<option value="">Chargement des domaines...</option>';
    domainSelect.disabled = true;
    try {
        const response = await fetch(`${config.lexa.baseUrl}/domains/`, {
            headers: {
                'Authorization': `Bearer ${config.lexa.apiKey}`,
                'Content-Type': 'application/json'
            }
        });
        if (!response.ok) throw new Error(`Erreur ${response.status}: ${response.statusText}`);
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

        // Restaurer le domaine préféré si disponible
        if (config.preferences.domainId) {
            const savedDomain = domains.find(d => d.id.toString() === config.preferences.domainId.toString());
            if (savedDomain) domainSelect.value = config.preferences.domainId;
        }

        domainSelect.disabled = false;
        loadGlossaries();

        // Charger les templates si en mode Lara
        if (config.translationService === 'lara') {
            loadLaraTemplates();
        }
    } catch (error) {
        console.error('Erreur lors du chargement des domaines:', error);
        domainSelect.innerHTML = '<option value="">Erreur de chargement</option>';
        showMessage('Erreur lors du chargement des domaines.', 'error');
    }
}
