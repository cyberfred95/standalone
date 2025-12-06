// Chargement des templates Lara
async function loadLaraTemplates() {
    console.log('[TRACE] Appel à loadLaraTemplates', new Date().toISOString(), (new Error().stack));
    const templateSelect = document.getElementById('laraTemplateMain');
    const templateHelpText = document.getElementById('templateHelpText');
    if (!templateSelect) return;
    templateSelect.innerHTML = '<option value="">Chargement des templates...</option>';
    const domainSelect = document.getElementById('domain');
    const selectedOption = domainSelect.selectedOptions[0];

    // Debug complet de l'option sélectionnée
    console.log('🔍 [DEBUG] Option sélectionnée complète:', {
        value: selectedOption?.value,
        textContent: selectedOption?.textContent,
        'dataset.name': selectedOption?.dataset.name,
        'dataset (all)': selectedOption?.dataset,
        innerHTML: selectedOption?.innerHTML
    });

    // Utiliser dataset.name pour récupérer le nom du domaine (pas l'ID)
    const domainName = selectedOption?.dataset?.name || '';
    const sourceLang = document.getElementById('sourceLang').value;
    const targetLang = document.getElementById('targetLang').value;

    console.log('🔍 [Frontend] Paramètres de recherche de templates:', {
        domainId: domainSelect.value,
        domainName: domainName,
        sourceLang,
        targetLang
    });

    // Empêcher tout appel si un des paramètres est vide
    if (!domainName || !sourceLang || !targetLang) {
        console.log('[TRACE] Annulation de loadLaraTemplates : paramètres incomplets', {domainName, sourceLang, targetLang});
        return;
    }

    try {
        let url = `${config.lara.baseUrl}/templates`;
        const params = new URLSearchParams();
        params.append('domain', domainName);
        params.append('sourceLanguage', sourceLang);
        params.append('targetLanguage', targetLang);
        url += `/find?${params.toString()}`;
        console.log('🔍 [Frontend] URL de recherche:', url);
        const response = await fetch(url);
        if (!response.ok) throw new Error(`Erreur ${response.status}: ${response.statusText}`);
        const templates = await response.json();
        if (templates.length === 0) {
            templateSelect.innerHTML = '<option value="">Aucun template disponible pour cette combinaison</option>';
        } else if (templates.length === 1) {
            // Un seul template : le sélectionner automatiquement
            templateSelect.innerHTML = '';
            const template = templates[0];
            const option = document.createElement('option');
            option.value = template.id;
            option.textContent = template.name;
            option.dataset.memoryId = template.translationMemoryId || '';
            option.dataset.glossaryId = template.glossaryId || '';
            option.dataset.memoryName = template.translationMemoryName || '';
            option.dataset.glossaryName = template.glossaryName || '';
            option.selected = true;
            templateSelect.appendChild(option);
            // Déclencher l'affichage des infos du template
            handleTemplateChange({ target: templateSelect });
        } else {
            templateSelect.innerHTML = '<option value="">Sélectionnez un template</option>';
            templates.forEach(template => {
                const option = document.createElement('option');
                option.value = template.id;
                option.textContent = template.name;
                option.dataset.memoryId = template.translationMemoryId || '';
                option.dataset.glossaryId = template.glossaryId || '';
                option.dataset.memoryName = template.translationMemoryName || '';
                option.dataset.glossaryName = template.glossaryName || '';
                templateSelect.appendChild(option);
            });
            // Forcer la détection du template sélectionné au chargement
            handleTemplateChange({ target: templateSelect });
        }
        if (templateHelpText) templateHelpText.style.display = 'block';
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
        if (infoDiv) infoDiv.style.display = 'none';
        return;
    }
    const memoryId = selectedOption.dataset.memoryId || '';
    const glossaryId = selectedOption.dataset.glossaryId || '';
    const memoryName = selectedOption.dataset.memoryName || memoryId || 'Non défini';
    const glossaryName = selectedOption.dataset.glossaryName || glossaryId || 'Non défini';
    if (memorySpan) memorySpan.textContent = `🗂️ Mémoire: ${memoryName}`;
    if (glossarySpan) glossarySpan.textContent = `📖 Glossaire: ${glossaryName}`;
    if (infoDiv) infoDiv.style.display = 'block';
}
// Traduction Lara (texte et fichiers)
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
        const instructionsMain = document.getElementById('laraInstructionsMain')?.value.trim();
        const fixTextSwitch = document.getElementById('fixTextSwitch');
        const fixText = fixTextSwitch?.checked || false;
        const domainSelect = document.getElementById('domain');
        const domainName = domainSelect.selectedOptions[0]?.dataset.name;
        const templateSelect = document.getElementById('laraTemplateMain');
        const selectedTemplateOption = templateSelect?.selectedOptions[0];
        const selectedMemory = selectedTemplateOption?.dataset.memoryId || '';
        const selectedGlossary = selectedTemplateOption?.dataset.glossaryId || '';
        const requestBody = {
            accessKeyId: config.lara.accessKeyId,
            accessKeySecret: config.lara.accessKeySecret,
            text: sourceText,
            target: targetLang,
            fixText: fixText
        };
        if (sourceLang) requestBody.source = sourceLang;
        if (domainName) requestBody.domain = domainName;
        if (config.lara.style) requestBody.style = config.lara.style;
        if (instructionsMain) requestBody.instructions = [instructionsMain];
        else if (config.lara.instructions) requestBody.instructions = [config.lara.instructions];
        if (selectedMemory) requestBody.adaptTo = [selectedMemory];
        else if (config.lara.translationMemoryIds) requestBody.adaptTo = config.lara.translationMemoryIds.split(',').map(id => id.trim()).filter(id => id);
        if (selectedGlossary) requestBody.glossaries = [selectedGlossary];
        else if (config.lara.glossaryIds) requestBody.glossaries = config.lara.glossaryIds.split(',').map(id => id.trim()).filter(id => id);
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
        const translatedText = result.translation || result.translated_text || result.text;
        document.getElementById('resultText').value = translatedText;
        let feedback = result.quality_feedback || result.feedback || result.quality || result.qualityFeedback;
        if (!feedback && result.metadata) {
            feedback = result.metadata.quality || result.metadata.qualityFeedback || result.metadata.quality_feedback;
        }
        if (feedback) {
            let feedbackText;
            if (typeof feedback === 'string') feedbackText = feedback;
            else if (typeof feedback === 'object') {
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
        const domainSelect = document.getElementById('domain');
        const domainName = domainSelect.selectedOptions[0]?.dataset.name;
        const templateSelect = document.getElementById('laraTemplateMain');
        const selectedTemplateOption = templateSelect?.selectedOptions[0];
        const selectedMemory = selectedTemplateOption?.dataset.memoryId || '';
        const selectedGlossary = selectedTemplateOption?.dataset.glossaryId || '';
        const results = [];
        for (const file of files) {
            const formData = new FormData();
            formData.append('file', file);
            formData.append('accessKeyId', config.lara.accessKeyId);
            formData.append('accessKeySecret', config.lara.accessKeySecret);
            formData.append('target', targetLang);
            if (sourceLang) formData.append('source', sourceLang);
            if (domainName) formData.append('domain', domainName);
            if (config.lara.style) formData.append('style', config.lara.style);
            if (selectedMemory) formData.append('adaptTo', selectedMemory);
            else if (config.lara.translationMemoryIds) formData.append('adaptTo', config.lara.translationMemoryIds);
            if (selectedGlossary) formData.append('glossaries', selectedGlossary);
            else if (config.lara.glossaryIds) formData.append('glossaries', config.lara.glossaryIds);
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

                // Debug: afficher la réponse du backend
                console.log('📥 [DEBUG] Réponse BRUTE du backend pour traduction document:', result);
                console.log('📥 [DEBUG] Type de result:', typeof result);
                console.log('📥 [DEBUG] result.downloadUrl existe?', 'downloadUrl' in result);
                console.log('📥 [DEBUG] result.downloadUrl valeur:', result.downloadUrl);

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
                } else {
                    console.warn('⚠️ [DEBUG] downloadUrl ne commence pas par / ou est undefined:', result.downloadUrl);
                }

                const finalResult = {
                    ...result,
                    source_file_name: file.name,
                    source_language: sourceLang,
                    target_language: targetLang
                };

                console.log('✅ [DEBUG] Résultat final ajouté:', finalResult);
                console.log('✅ [DEBUG] finalResult.downloadUrl:', finalResult.downloadUrl);
                console.log('✅ [DEBUG] Toutes les clés de finalResult:', Object.keys(finalResult));
                results.push(finalResult);
            }
        }

        console.log('📤 [DEBUG] Appel de displayFileResults avec results:', results);
            displayFileResults(results, files);
            startLaraDocumentStatusPolling(results, files);
        showMessage(`Traduction de ${files.length} fichier(s) avec LaraTranslate lancée !`, 'success');
    } catch (error) {
        console.error('Erreur lors de la traduction Lara:', error);
        showMessage(`Erreur Lara: ${error.message}`, 'error');
    } finally {
        setLoading(false);
    }
}

const LARA_DOCUMENT_STATUS_POLL_INTERVAL = 4000;
const LARA_DOCUMENT_STATUS_FINAL = new Set(['translated', 'error']);

function startLaraDocumentStatusPolling(results, files) {
    console.log('🔄 [POLLING] Démarrage du polling pour', results.length, 'résultat(s)');
    console.log('🔄 [POLLING] Config baseUrl:', config.lara.baseUrl);
    console.log('🔄 [POLLING] Résultats reçus:', JSON.stringify(results, null, 2));

    if (!config.lara.accessKeyId || !config.lara.accessKeySecret) {
        console.warn('Polling Lara des documents désactivé : clés Lara manquantes');
        return;
    }

    results.forEach((result, index) => {
        const status = (result.status || '').toLowerCase();
        console.log(`🔄 [POLLING] Document ${index}: id=${result.id}, status=${status}`);
        if (!result.id || LARA_DOCUMENT_STATUS_FINAL.has(status)) {
            console.log(`🔄 [POLLING] Document ${index} ignoré (pas d'id ou statut final)`);
            return;
        }
        console.log(`🔄 [POLLING] Lancement du polling pour document ${result.id}`);
        pollLaraDocumentStatus(result.id, index, results, files);
    });
}

function pollLaraDocumentStatus(documentId, resultIndex, results, files) {
    const poll = async () => {
        try {
            const statusUrl = buildLaraDocumentStatusUrl(documentId);
            console.log(`🔄 [POLLING] Requête vers: ${statusUrl}`);
            const response = await fetch(statusUrl);
            console.log(`🔄 [POLLING] Réponse HTTP: ${response.status} ${response.statusText}`);
            if (!response.ok) {
                console.warn(`Polling Lara document ${documentId} échoué (${response.status}). nouvelle tentative dans ${LARA_DOCUMENT_STATUS_POLL_INTERVAL}ms.`);
                setTimeout(poll, LARA_DOCUMENT_STATUS_POLL_INTERVAL);
                return;
            }
            const statusData = await response.json();
            console.log(`🔄 [POLLING] Données reçues:`, statusData);
            const updatedResult = results[resultIndex];
            if (!updatedResult) {
                return;
            }

            const newStatus = (statusData.status || updatedResult.status || '').toLowerCase();
            updatedResult.status = newStatus || updatedResult.status;
            if (statusData.createdAt) updatedResult.created_at = statusData.createdAt;
            if (statusData.updatedAt) updatedResult.updated_at = statusData.updatedAt;
            if (statusData.created_at) updatedResult.created_at = statusData.created_at;
            if (statusData.updated_at) updatedResult.updated_at = statusData.updated_at;
            if (newStatus === 'translated') {
                updatedResult.downloadUrl = updatedResult.downloadUrl || buildLaraDocumentDownloadUrl(documentId);
            }

            displayFileResults(results, files);

            if (!LARA_DOCUMENT_STATUS_FINAL.has(newStatus)) {
                setTimeout(poll, LARA_DOCUMENT_STATUS_POLL_INTERVAL);
            }
        } catch (error) {
            console.error('Erreur lors du polling du statut Lara:', error);
            setTimeout(poll, LARA_DOCUMENT_STATUS_POLL_INTERVAL);
        }
    };
    poll();
}

function buildLaraDocumentStatusUrl(documentId) {
    let baseUrl = config.lara.baseUrl.replace(/\/$/, '');
    if (!baseUrl.startsWith('http')) {
        baseUrl = `${window.location.origin}${baseUrl}`;
    }
    const url = new URL(`${baseUrl}/document-status/${documentId}`);
    url.searchParams.set('accessKeyId', config.lara.accessKeyId);
    url.searchParams.set('accessKeySecret', config.lara.accessKeySecret);
    console.log('🔍 [POLLING] URL de statut construite:', url.toString());
    return url.toString();
}

function buildLaraDocumentDownloadUrl(documentId) {
    let baseUrl = config.lara.baseUrl.replace(/\/$/, '');
    if (!baseUrl.startsWith('http')) {
        baseUrl = `${window.location.origin}${baseUrl}`;
    }
    const url = new URL(`${baseUrl}/download/${documentId}`);
    url.searchParams.set('accessKeyId', config.lara.accessKeyId);
    url.searchParams.set('accessKeySecret', config.lara.accessKeySecret);
    return url.toString();
}
// js/lara.js : toutes les fonctions liées à Lara (langues, templates, traduction)

async function loadLaraLanguages() {
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
    // Définir les valeurs par défaut
    sourceSelect.value = 'fr';
    targetSelect.value = 'en';

    // Restaurer les préférences utilisateur si disponibles
    if (config.preferences.sourceLang) {
        const savedSource = commonLanguages.find(lang => lang.code === config.preferences.sourceLang);
        if (savedSource) sourceSelect.value = config.preferences.sourceLang;
    }
    if (config.preferences.targetLang) {
        const savedTarget = commonLanguages.find(lang => lang.code === config.preferences.targetLang);
        if (savedTarget) targetSelect.value = config.preferences.targetLang;
    }

    sourceSelect.disabled = false;
    targetSelect.disabled = false;
    await loadDomains();
    showMessage('Interface LaraTranslate initialisée!', 'success');
}

function setupTemplatesHandlers() {
    console.log('setupTemplatesHandlers called');
    const templateSelect = document.getElementById('laraTemplateMain');
    if (templateSelect) {
        templateSelect.addEventListener('change', handleTemplateChange);
    }

    const viewTemplatesBtn = document.getElementById('viewTemplatesBtn');
    if (viewTemplatesBtn) {
        viewTemplatesBtn.addEventListener('click', function (e) {
            openTemplatesScreen();
        });
    }

    const backFromTemplatesBtn = document.getElementById('backFromTemplates');
    if (backFromTemplatesBtn) {
        backFromTemplatesBtn.addEventListener('click', closeTemplatesScreen);
    }
}

function openTemplatesScreen() {
    console.log('openTemplatesScreen called');
    const screen = document.getElementById('templatesScreen');
    console.log('templatesScreen element:', screen);
    if (screen) {
        screen.style.display = 'block';
        console.log('Calling loadTemplatesTable...');
        loadTemplatesTable();
    }
}

function closeTemplatesScreen() {
    const screen = document.getElementById('templatesScreen');
    if (screen) screen.style.display = 'none';
}

let allTemplates = [];

async function loadTemplatesTable() {
    console.log('loadTemplatesTable called');
    console.log('config.lara.baseUrl:', config.lara.baseUrl);
    const container = document.getElementById('templatesTableContent');
    console.log('templatesTableContent element:', container);
    if (!container) {
        console.log('ERROR: container not found, returning early');
        return;
    }

    container.innerHTML = '<div class="templates-loading">Chargement des templates...</div>';

    const url = `${config.lara.baseUrl}/templates`;
    console.log('Fetching templates from:', url);
    try {
        const response = await fetch(url);
        console.log('Fetch response:', response.status, response.statusText);
        if (!response.ok) throw new Error(`Erreur ${response.status}`);
        allTemplates = await response.json();

        console.log('Loaded templates:', allTemplates.length);
        const templatesWithMemory = allTemplates.filter(t => !!(t.translationMemoryId || t.translationMemoryName));
        console.log('Templates with memory:', templatesWithMemory.length);

        if (allTemplates.length === 0) {
            container.innerHTML = '<div class="templates-empty">Aucun template configuré</div>';
            return;
        }

        renderTemplatesTable(allTemplates);
        setupTemplateFilters();
    } catch (error) {
        console.error('Erreur lors du chargement des templates:', error);
        container.innerHTML = '<div class="templates-error">Erreur de chargement des templates</div>';
    }
}

function renderTemplatesTable(templates) {
    const container = document.getElementById('templatesTableContent');
    if (!container) return;

    container.innerHTML = `
        <div class="templates-filters">
            <div class="filters-row">
                <input type="text" id="filterName" class="filter-input" placeholder="Filtrer par nom...">
                <input type="text" id="filterDomain" class="filter-input" placeholder="Domaine...">
                <input type="text" id="filterSource" class="filter-input" placeholder="Source...">
                <input type="text" id="filterTarget" class="filter-input" placeholder="Cible...">
                <input type="text" id="filterMemory" class="filter-input" placeholder="Mémoire...">
                <input type="text" id="filterGlossary" class="filter-input" placeholder="Glossaire...">
                <label class="filter-checkbox">
                    <input type="checkbox" id="filterHasMemory"> Avec mémoire
                </label>
                <button id="clearFiltersBtn" class="clear-filters-btn" title="Supprimer les filtres">✕ Filtres</button>
            </div>
        </div>
        <table class="templates-table">
            <thead>
                <tr>
                    <th>Nom</th>
                    <th>Domaine</th>
                    <th>Source</th>
                    <th>Cible</th>
                    <th>Mémoire de traduction</th>
                    <th>Glossaire</th>
                </tr>
            </thead>
            <tbody id="templatesTableBody">
                ${generateTemplateRows(templates)}
            </tbody>
        </table>
        <div class="templates-count">${templates.length} template(s) affiché(s)</div>
    `;
}

function generateTemplateRows(templates) {
    if (templates.length === 0) {
        return '<tr><td colspan="6" class="templates-empty">Aucun template ne correspond aux filtres</td></tr>';
    }
    return templates.map(template => `
        <tr class="${template.isDefault ? 'template-row-default' : ''}"
            data-name="${(template.name || '').toLowerCase()}"
            data-domain="${(template.domain || '*').toLowerCase()}"
            data-source="${(template.sourceLanguage || '*').toLowerCase()}"
            data-target="${(template.targetLanguage || '*').toLowerCase()}"
            data-memory="${(template.translationMemoryName || template.translationMemoryId || '-').toLowerCase()}"
            data-glossary="${(template.glossaryName || template.glossaryId || '-').toLowerCase()}">
            <td class="template-name-cell">
                ${template.name}
                ${template.isDefault ? '<span class="badge-default">Défaut</span>' : ''}
            </td>
            <td>${template.domain || '*'}</td>
            <td>${template.sourceLanguage || '*'}</td>
            <td>${template.targetLanguage || '*'}</td>
            <td>${template.translationMemoryName || template.translationMemoryId || '-'}</td>
            <td>${template.glossaryName || template.glossaryId || '-'}</td>
        </tr>
    `).join('');
}

function setupTemplateFilters() {
    const filterInputs = ['filterName', 'filterDomain', 'filterSource', 'filterTarget', 'filterMemory', 'filterGlossary'];

    filterInputs.forEach(id => {
        const input = document.getElementById(id);
        if (input) {
            input.addEventListener('input', applyTemplateFilters);
        }
    });

    const hasMemoryCheckbox = document.getElementById('filterHasMemory');
    if (hasMemoryCheckbox) {
        hasMemoryCheckbox.addEventListener('change', applyTemplateFilters);
    }

    const clearBtn = document.getElementById('clearFiltersBtn');
    if (clearBtn) {
        clearBtn.addEventListener('click', clearTemplateFilters);
    }
}

function applyTemplateFilters() {
    const filters = {
        name: (document.getElementById('filterName')?.value || '').toLowerCase(),
        domain: (document.getElementById('filterDomain')?.value || '').toLowerCase(),
        source: (document.getElementById('filterSource')?.value || '').toLowerCase(),
        target: (document.getElementById('filterTarget')?.value || '').toLowerCase(),
        memory: (document.getElementById('filterMemory')?.value || '').toLowerCase(),
        glossary: (document.getElementById('filterGlossary')?.value || '').toLowerCase(),
        hasMemoryOnly: document.getElementById('filterHasMemory')?.checked || false
    };

    const filteredTemplates = allTemplates.filter(template => {
        const name = (template.name || '').toLowerCase();
        const domain = (template.domain || '*').toLowerCase();
        const source = (template.sourceLanguage || '*').toLowerCase();
        const target = (template.targetLanguage || '*').toLowerCase();
        const memory = (template.translationMemoryName || template.translationMemoryId || '-').toLowerCase();
        const glossary = (template.glossaryName || template.glossaryId || '-').toLowerCase();
        const hasMemory = !!(template.translationMemoryId || template.translationMemoryName);

        // Appliquer le filtre "avec mémoire uniquement"
        if (filters.hasMemoryOnly && !hasMemory) {
            return false;
        }

        return name.includes(filters.name) &&
            domain.includes(filters.domain) &&
            source.includes(filters.source) &&
            target.includes(filters.target) &&
            memory.includes(filters.memory) &&
            glossary.includes(filters.glossary);
    });

    const tbody = document.getElementById('templatesTableBody');
    const countDiv = document.querySelector('.templates-count');

    if (tbody) {
        tbody.innerHTML = generateTemplateRows(filteredTemplates);
    }
    if (countDiv) {
        countDiv.textContent = `${filteredTemplates.length} template(s) affiché(s) sur ${allTemplates.length}`;
    }
}

function clearTemplateFilters() {
    const filterInputs = ['filterName', 'filterDomain', 'filterSource', 'filterTarget', 'filterMemory', 'filterGlossary'];
    filterInputs.forEach(id => {
        const input = document.getElementById(id);
        if (input) input.value = '';
    });

    const hasMemoryCheckbox = document.getElementById('filterHasMemory');
    if (hasMemoryCheckbox) hasMemoryCheckbox.checked = false;

    applyTemplateFilters();
}
