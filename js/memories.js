// js/memories.js : gestion de l'écran des mémoires

function setupMemoriesScreenHandlers() {
    const backFromMemoriesBtn = document.getElementById('backFromMemories');
    if (backFromMemoriesBtn) {
        backFromMemoriesBtn.addEventListener('click', closeMemoriesScreen);
    }
}

function openMemoriesScreen() {
    const screen = document.getElementById('memoriesScreen');
    if (screen) {
        screen.style.display = 'block';
        loadMemoriesTable();
    }
}

function closeMemoriesScreen() {
    const screen = document.getElementById('memoriesScreen');
    if (screen) screen.style.display = 'none';
}

let allMemories = [];

async function loadMemoriesTable() {
    const container = document.getElementById('memoriesTableContent');
    if (!container) return;

    container.innerHTML = '<div class="memories-loading">Chargement des mémoires...</div>';

    const baseUrl = (typeof config !== 'undefined' && config.lara && config.lara.baseUrl)
        ? config.lara.baseUrl
        : '/api';

    const url = `${baseUrl}/memories-list`; // Will be /lara/api/memories-list -> /api/lara/memories-list

    try {
        const response = await fetch(url);
        if (!response.ok) throw new Error(`Erreur ${response.status}`);

        allMemories = await response.json();

        if (allMemories.length === 0) {
            container.innerHTML = '<div class="memories-empty">Aucune mémoire trouvée</div>';
            return;
        }

        renderMemoriesTable(allMemories);
        setupMemoryFilters();
    } catch (error) {
        console.error('Erreur lors du chargement des mémoires:', error);
        container.innerHTML = '<div class="memories-error">Erreur de chargement des mémoires</div>';
    }
}

function renderMemoriesTable(memories) {
    const container = document.getElementById('memoriesTableContent');
    if (!container) return;

    container.innerHTML = `
        <div class="memories-filters">
            <div class="filters-row">
                <input type="text" id="filterMemoryName" class="filter-input" placeholder="Nom...">
                <input type="text" id="filterMemoryDomain" class="filter-input" placeholder="Domaine...">
                <input type="text" id="filterMemorySource" class="filter-input" placeholder="Source..." style="max-width: 100px;">
                <input type="text" id="filterMemoryTarget" class="filter-input" placeholder="Cible..." style="max-width: 100px;">
                <button id="clearMemoryFiltersBtn" class="clear-filters-btn" title="Supprimer les filtres">✕ Filtres</button>
            </div>
        </div>
        <table class="memories-table">
            <thead>
                <tr>
                    <th>Nom</th>
                    <th style="width: 80px;">Source</th>
                    <th style="width: 80px;">Cible</th>
                    <th>Domaines</th>
                </tr>
            </thead>
            <tbody id="memoriesTableBody">
                ${generateMemoryRows(memories)}
            </tbody>
        </table>
        <div class="memories-count">${memories.length} mémoire(s) affichée(s)</div>
    `;
}

function generateMemoryRows(memories) {
    if (memories.length === 0) {
        return '<tr><td colspan="4" class="memories-empty">Aucune mémoire ne correspond aux filtres</td></tr>';
    }
    return memories.map(m => {
        const domains = m.domains ? m.domains.split(',').map(d => d.trim()).filter(d => d) : [];
        const domainsHtml = domains.map(d => `<span class="memory-domain-tag">${d}</span>`).join('');

        return `
        <tr>
            <td class="memory-name-cell">${m.name}</td>
            <td><span class="memory-lang-tag" style="background-color: #dbeafe; color: #1e40af;">${m.sourceLanguage}</span></td>
            <td><span class="memory-lang-tag" style="background-color: #dbeafe; color: #1e40af;">${m.targetLanguage}</span></td>
            <td>${domainsHtml || '-'}</td>
        </tr>
    `}).join('');
}

function setupMemoryFilters() {
    const inputs = ['filterMemoryName', 'filterMemoryDomain', 'filterMemorySource', 'filterMemoryTarget'];
    inputs.forEach(id => {
        const el = document.getElementById(id);
        if (el) el.addEventListener('input', applyMemoryFilters);
    });

    const clearBtn = document.getElementById('clearMemoryFiltersBtn');
    if (clearBtn) clearBtn.addEventListener('click', clearMemoryFilters);
}

function applyMemoryFilters() {
    const nameFilter = (document.getElementById('filterMemoryName')?.value || '').toLowerCase();
    const domainFilter = (document.getElementById('filterMemoryDomain')?.value || '').toLowerCase();
    const sourceFilter = (document.getElementById('filterMemorySource')?.value || '').toLowerCase();
    const targetFilter = (document.getElementById('filterMemoryTarget')?.value || '').toLowerCase();

    const filtered = allMemories.filter(m => {
        const name = (m.name || '').toLowerCase();
        const domains = (m.domains || '').toLowerCase();
        const source = (m.sourceLanguage || '').toLowerCase();
        const target = (m.targetLanguage || '').toLowerCase();

        return name.includes(nameFilter) &&
            domains.includes(domainFilter) &&
            source.includes(sourceFilter) &&
            target.includes(targetFilter);
    });

    const tbody = document.getElementById('memoriesTableBody');
    const countDiv = document.querySelector('.memories-count');

    if (tbody) {
        tbody.innerHTML = generateMemoryRows(filtered);
    }
    if (countDiv) {
        countDiv.textContent = `${filtered.length} mémoire(s) affichée(s) sur ${allMemories.length}`;
    }
}

function clearMemoryFilters() {
    ['filterMemoryName', 'filterMemoryDomain', 'filterMemorySource', 'filterMemoryTarget'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.value = '';
    });
    applyMemoryFilters();
}
