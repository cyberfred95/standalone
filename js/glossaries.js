// js/glossaries.js : gestion de l'écran des glossaires

function setupGlossariesScreenHandlers() {
    const backFromGlossariesBtn = document.getElementById('backFromGlossaries');
    if (backFromGlossariesBtn) {
        backFromGlossariesBtn.addEventListener('click', closeGlossariesScreen);
    }
}

function openGlossariesScreen() {
    const screen = document.getElementById('glossariesScreen');
    if (screen) {
        screen.style.display = 'block';
        loadGlossariesTable();
    }
}

function closeGlossariesScreen() {
    const screen = document.getElementById('glossariesScreen');
    if (screen) screen.style.display = 'none';
}

let allGlossaries = [];

async function loadGlossariesTable() {
    const container = document.getElementById('glossariesTableContent');
    if (!container) return;

    container.innerHTML = '<div class="glossaries-loading">Chargement des glossaires...</div>';

    const baseUrl = (typeof config !== 'undefined' && config.lara && config.lara.baseUrl)
        ? config.lara.baseUrl
        : '/api';

    const url = `${baseUrl}/glossaries-list`; // Will be /lara/api/glossaries-list -> /api/lara/glossaries-list

    try {
        const response = await fetch(url);
        if (!response.ok) throw new Error(`Erreur ${response.status}`);

        allGlossaries = await response.json();

        if (allGlossaries.length === 0) {
            container.innerHTML = '<div class="glossaries-empty">Aucun glossaire trouvé</div>';
            return;
        }

        renderGlossariesTable(allGlossaries);
        setupGlossaryFilters();
    } catch (error) {
        console.error('Erreur lors du chargement des glossaires:', error);
        container.innerHTML = '<div class="glossaries-error">Erreur de chargement des glossaires</div>';
    }
}

function renderGlossariesTable(glossaries) {
    const container = document.getElementById('glossariesTableContent');
    if (!container) return;

    container.innerHTML = `
        <div class="glossaries-filters">
            <div class="filters-row">
                <input type="text" id="filterGlossaryName" class="filter-input" placeholder="Nom...">
                <input type="text" id="filterGlossaryDomain" class="filter-input" placeholder="Domaine...">
                <input type="text" id="filterGlossarySource" class="filter-input" placeholder="Source (ex: FR)..." style="max-width: 100px;">
                <input type="text" id="filterGlossaryTarget" class="filter-input" placeholder="Cible (ex: EN)..." style="max-width: 100px;">
                <button id="clearGlossaryFiltersBtn" class="clear-filters-btn" title="Supprimer les filtres">✕ Filtres</button>
            </div>
        </div>
        <table class="glossaries-table">
            <thead>
                <tr>
                    <th>Nom</th>
                    <th style="width: 80px;">Source</th>
                    <th>Cibles</th>
                    <th>Domaine</th>
                </tr>
            </thead>
            <tbody id="glossariesTableBody">
                ${generateGlossaryRows(glossaries)}
            </tbody>
        </table>
        <div class="glossaries-count">${glossaries.length} glossaire(s) affiché(s)</div>
    `;
}

function generateGlossaryRows(glossaries) {
    if (glossaries.length === 0) {
        return '<tr><td colspan="4" class="glossaries-empty">Aucun glossaire ne correspond aux filtres</td></tr>';
    }
    return glossaries.map(g => {
        const targets = g.targetLanguages ? g.targetLanguages.split(',').map(t => t.trim()) : [];
        const targetsHtml = targets.map(t => `<span class="glossary-lang-tag">${t}</span>`).join('');

        return `
        <tr>
            <td class="glossary-name-cell">${g.name}</td>
            <td><span class="glossary-lang-tag" style="background-color: #dbeafe; color: #1e40af;">${g.sourceLanguage}</span></td>
            <td>${targetsHtml}</td>
            <td>${g.domain ? `<span class="glossary-domain-tag">${g.domain}</span>` : '-'}</td>
        </tr>
    `}).join('');
}

function setupGlossaryFilters() {
    const inputs = ['filterGlossaryName', 'filterGlossaryDomain', 'filterGlossarySource', 'filterGlossaryTarget'];
    inputs.forEach(id => {
        const el = document.getElementById(id);
        if (el) el.addEventListener('input', applyGlossaryFilters);
    });

    const clearBtn = document.getElementById('clearGlossaryFiltersBtn');
    if (clearBtn) clearBtn.addEventListener('click', clearGlossaryFilters);
}

function applyGlossaryFilters() {
    const nameFilter = (document.getElementById('filterGlossaryName')?.value || '').toLowerCase();
    const domainFilter = (document.getElementById('filterGlossaryDomain')?.value || '').toLowerCase();
    const sourceFilter = (document.getElementById('filterGlossarySource')?.value || '').toLowerCase();
    const targetFilter = (document.getElementById('filterGlossaryTarget')?.value || '').toLowerCase();

    const filtered = allGlossaries.filter(g => {
        const name = (g.name || '').toLowerCase();
        const domain = (g.domain || '').toLowerCase();
        const source = (g.sourceLanguage || '').toLowerCase();
        const targets = (g.targetLanguages || '').toLowerCase();

        return name.includes(nameFilter) &&
            domain.includes(domainFilter) &&
            source.includes(sourceFilter) &&
            targets.includes(targetFilter);
    });

    const tbody = document.getElementById('glossariesTableBody');
    const countDiv = document.querySelector('.glossaries-count');

    if (tbody) {
        tbody.innerHTML = generateGlossaryRows(filtered);
    }
    if (countDiv) {
        countDiv.textContent = `${filtered.length} glossaire(s) affiché(s) sur ${allGlossaries.length}`;
    }
}

function clearGlossaryFilters() {
    ['filterGlossaryName', 'filterGlossaryDomain', 'filterGlossarySource', 'filterGlossaryTarget'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.value = '';
    });
    applyGlossaryFilters();
}
