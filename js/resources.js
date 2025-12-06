// js/resources.js : gestion de l'écran des ressources

function setupResourcesScreenHandlers() {
    const backFromResourcesBtn = document.getElementById('backFromResources');
    if (backFromResourcesBtn) {
        backFromResourcesBtn.addEventListener('click', closeResourcesScreen);
    }

    // Setup tab handlers
    const memoriesTabBtn = document.getElementById('memoriesTabBtn');
    const glossariesTabBtn = document.getElementById('glossariesTabBtn');

    if (memoriesTabBtn) {
        memoriesTabBtn.addEventListener('click', () => showResourceTab('memories'));
    }
    if (glossariesTabBtn) {
        glossariesTabBtn.addEventListener('click', () => showResourceTab('glossaries'));
    }
}

function openResourcesScreen() {
    const screen = document.getElementById('resourcesScreen');
    if (screen) {
        screen.style.display = 'block';
        loadResourcesData();
    }
}

function closeResourcesScreen() {
    const screen = document.getElementById('resourcesScreen');
    if (screen) screen.style.display = 'none';
}

let allResourcesData = null;
let currentResourceTab = 'memories';

async function loadResourcesData() {
    const container = document.getElementById('resourcesTableContent');
    if (!container) return;

    container.innerHTML = '<div class="resources-loading">Chargement des ressources...</div>';

    const baseUrl = (typeof config !== 'undefined' && config.lara && config.lara.baseUrl)
        ? config.lara.baseUrl
        : '/api';

    const url = `${baseUrl}/resources-list`; // Will be /lara/api/resources-list -> /api/lara/resources-list

    try {
        const response = await fetch(url);
        if (!response.ok) throw new Error(`Erreur ${response.status}`);

        allResourcesData = await response.json();

        // Show memories tab by default
        showResourceTab('memories');
    } catch (error) {
        console.error('Erreur lors du chargement des ressources:', error);
        container.innerHTML = '<div class="resources-error">Erreur de chargement des ressources</div>';
    }
}

function showResourceTab(tabName) {
    currentResourceTab = tabName;

    // Update tab buttons
    const memoriesTabBtn = document.getElementById('memoriesTabBtn');
    const glossariesTabBtn = document.getElementById('glossariesTabBtn');

    if (memoriesTabBtn) {
        memoriesTabBtn.classList.toggle('active', tabName === 'memories');
    }
    if (glossariesTabBtn) {
        glossariesTabBtn.classList.toggle('active', tabName === 'glossaries');
    }

    // Render the appropriate table
    if (tabName === 'memories') {
        renderResourceMemoriesTable(allResourcesData.memories || []);
    } else if (tabName === 'glossaries') {
        renderResourceGlossariesTable(allResourcesData.glossaries || []);
    }
}

let allFilteredMemories = [];

function renderResourceMemoriesTable(memories) {
    const container = document.getElementById('resourcesTableContent');
    if (!container) return;

    allFilteredMemories = memories;

    container.innerHTML = `
        <div class="resources-filters">
            <div class="filters-row">
                <input type="text" id="filterResourceMemoryName" class="filter-input" placeholder="Nom...">
                <input type="text" id="filterResourceMemoryDomain" class="filter-input" placeholder="Domaine...">
                <input type="text" id="filterResourceMemorySource" class="filter-input" placeholder="Source..." style="max-width: 100px;">
                <input type="text" id="filterResourceMemoryTarget" class="filter-input" placeholder="Cible..." style="max-width: 100px;">
                <button id="clearResourceMemoryFiltersBtn" class="clear-filters-btn" title="Supprimer les filtres">✕ Filtres</button>
            </div>
        </div>
        <table class="resources-table">
            <thead>
                <tr>
                    <th style="width: 200px;">ID</th>
                    <th>Nom</th>
                    <th style="width: 80px;">Source</th>
                    <th style="width: 80px;">Cible</th>
                    <th>Domaines</th>
                </tr>
            </thead>
            <tbody id="resourceMemoriesTableBody">
                ${generateResourceMemoryRows(memories)}
            </tbody>
        </table>
        <div class="resources-count">${memories.length} mémoire(s) affichée(s)</div>
    `;

    setupResourceMemoryFilters();
}

function generateResourceMemoryRows(memories) {
    if (memories.length === 0) {
        return '<tr><td colspan="5" class="resources-empty">Aucune mémoire ne correspond aux filtres</td></tr>';
    }
    return memories.map(m => {
        const domains = Array.isArray(m.domains) ? m.domains : [];
        const domainsHtml = domains.map(d => `<span class="resource-domain-tag">${d}</span>`).join('');

        return `
        <tr>
            <td class="resource-id-cell">${m.id || '-'}</td>
            <td class="resource-name-cell">${m.name || '-'}</td>
            <td><span class="resource-lang-tag" style="background-color: #dbeafe; color: #1e40af;">${m.sourceLanguage || '-'}</span></td>
            <td><span class="resource-lang-tag" style="background-color: #dbeafe; color: #1e40af;">${m.targetLanguage || '-'}</span></td>
            <td>${domainsHtml || '-'}</td>
        </tr>
    `}).join('');
}

function setupResourceMemoryFilters() {
    const inputs = ['filterResourceMemoryName', 'filterResourceMemoryDomain', 'filterResourceMemorySource', 'filterResourceMemoryTarget'];
    inputs.forEach(id => {
        const el = document.getElementById(id);
        if (el) el.addEventListener('input', applyResourceMemoryFilters);
    });

    const clearBtn = document.getElementById('clearResourceMemoryFiltersBtn');
    if (clearBtn) clearBtn.addEventListener('click', clearResourceMemoryFilters);
}

function applyResourceMemoryFilters() {
    const nameFilter = (document.getElementById('filterResourceMemoryName')?.value || '').toLowerCase();
    const domainFilter = (document.getElementById('filterResourceMemoryDomain')?.value || '').toLowerCase();
    const sourceFilter = (document.getElementById('filterResourceMemorySource')?.value || '').toLowerCase();
    const targetFilter = (document.getElementById('filterResourceMemoryTarget')?.value || '').toLowerCase();

    const filtered = allFilteredMemories.filter(m => {
        const name = (m.name || '').toLowerCase();
        const domains = Array.isArray(m.domains) ? m.domains.join(' ').toLowerCase() : '';
        const source = (m.sourceLanguage || '').toLowerCase();
        const target = (m.targetLanguage || '').toLowerCase();

        return name.includes(nameFilter) &&
            domains.includes(domainFilter) &&
            source.includes(sourceFilter) &&
            target.includes(targetFilter);
    });

    const tbody = document.getElementById('resourceMemoriesTableBody');
    const countDiv = document.querySelector('.resources-count');

    if (tbody) {
        tbody.innerHTML = generateResourceMemoryRows(filtered);
    }
    if (countDiv) {
        countDiv.textContent = `${filtered.length} mémoire(s) affichée(s) sur ${allFilteredMemories.length}`;
    }
}

function clearResourceMemoryFilters() {
    ['filterResourceMemoryName', 'filterResourceMemoryDomain', 'filterResourceMemorySource', 'filterResourceMemoryTarget'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.value = '';
    });
    applyResourceMemoryFilters();
}

let allFilteredGlossaries = [];

function renderResourceGlossariesTable(glossaries) {
    const container = document.getElementById('resourcesTableContent');
    if (!container) return;

    allFilteredGlossaries = glossaries;

    container.innerHTML = `
        <div class="resources-filters">
            <div class="filters-row">
                <input type="text" id="filterResourceGlossaryName" class="filter-input" placeholder="Nom...">
                <input type="text" id="filterResourceGlossaryDomain" class="filter-input" placeholder="Domaine...">
                <input type="text" id="filterResourceGlossarySource" class="filter-input" placeholder="Source (ex: FR)..." style="max-width: 100px;">
                <input type="text" id="filterResourceGlossaryTarget" class="filter-input" placeholder="Cible (ex: EN)..." style="max-width: 100px;">
                <button id="clearResourceGlossaryFiltersBtn" class="clear-filters-btn" title="Supprimer les filtres">✕ Filtres</button>
            </div>
        </div>
        <table class="resources-table">
            <thead>
                <tr>
                    <th style="width: 200px;">ID</th>
                    <th>Nom</th>
                    <th style="width: 80px;">Source</th>
                    <th>Cibles</th>
                    <th>Domaine</th>
                </tr>
            </thead>
            <tbody id="resourceGlossariesTableBody">
                ${generateResourceGlossaryRows(glossaries)}
            </tbody>
        </table>
        <div class="resources-count">${glossaries.length} glossaire(s) affiché(s)</div>
    `;

    setupResourceGlossaryFilters();
}

function generateResourceGlossaryRows(glossaries) {
    if (glossaries.length === 0) {
        return '<tr><td colspan="5" class="resources-empty">Aucun glossaire ne correspond aux filtres</td></tr>';
    }
    return glossaries.map(g => {
        const targets = Array.isArray(g.targetLanguages) ? g.targetLanguages : [];
        const targetsHtml = targets.map(t => `<span class="resource-lang-tag">${t}</span>`).join('');

        return `
        <tr>
            <td class="resource-id-cell">${g.id || '-'}</td>
            <td class="resource-name-cell">${g.name || '-'}</td>
            <td><span class="resource-lang-tag" style="background-color: #dbeafe; color: #1e40af;">${g.sourceLanguage || '-'}</span></td>
            <td>${targetsHtml || '-'}</td>
            <td>${g.domain ? `<span class="resource-domain-tag">${g.domain}</span>` : '-'}</td>
        </tr>
    `}).join('');
}

function setupResourceGlossaryFilters() {
    const inputs = ['filterResourceGlossaryName', 'filterResourceGlossaryDomain', 'filterResourceGlossarySource', 'filterResourceGlossaryTarget'];
    inputs.forEach(id => {
        const el = document.getElementById(id);
        if (el) el.addEventListener('input', applyResourceGlossaryFilters);
    });

    const clearBtn = document.getElementById('clearResourceGlossaryFiltersBtn');
    if (clearBtn) clearBtn.addEventListener('click', clearResourceGlossaryFilters);
}

function applyResourceGlossaryFilters() {
    const nameFilter = (document.getElementById('filterResourceGlossaryName')?.value || '').toLowerCase();
    const domainFilter = (document.getElementById('filterResourceGlossaryDomain')?.value || '').toLowerCase();
    const sourceFilter = (document.getElementById('filterResourceGlossarySource')?.value || '').toLowerCase();
    const targetFilter = (document.getElementById('filterResourceGlossaryTarget')?.value || '').toLowerCase();

    const filtered = allFilteredGlossaries.filter(g => {
        const name = (g.name || '').toLowerCase();
        const domain = (g.domain || '').toLowerCase();
        const source = (g.sourceLanguage || '').toLowerCase();
        const targets = Array.isArray(g.targetLanguages) ? g.targetLanguages.join(' ').toLowerCase() : '';

        return name.includes(nameFilter) &&
            domain.includes(domainFilter) &&
            source.includes(sourceFilter) &&
            targets.includes(targetFilter);
    });

    const tbody = document.getElementById('resourceGlossariesTableBody');
    const countDiv = document.querySelector('.resources-count');

    if (tbody) {
        tbody.innerHTML = generateResourceGlossaryRows(filtered);
    }
    if (countDiv) {
        countDiv.textContent = `${filtered.length} glossaire(s) affiché(s) sur ${allFilteredGlossaries.length}`;
    }
}

function clearResourceGlossaryFilters() {
    ['filterResourceGlossaryName', 'filterResourceGlossaryDomain', 'filterResourceGlossarySource', 'filterResourceGlossaryTarget'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.value = '';
    });
    applyResourceGlossaryFilters();
}
