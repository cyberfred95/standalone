// js/domains.js : gestion de l'écran des domaines

function setupDomainsHandlers() {
    const backFromDomainsBtn = document.getElementById('backFromDomains');
    if (backFromDomainsBtn) {
        backFromDomainsBtn.addEventListener('click', closeDomainsScreen);
    }
}

function openDomainsScreen() {
    const screen = document.getElementById('domainsScreen');
    if (screen) {
        screen.style.display = 'block';
        loadDomainsTable();
    }
}

function closeDomainsScreen() {
    const screen = document.getElementById('domainsScreen');
    if (screen) screen.style.display = 'none';
}

let allDomains = [];

async function loadDomainsTable() {
    const container = document.getElementById('domainsTableContent');
    if (!container) return;

    container.innerHTML = '<div class="domains-loading">Chargement des domaines...</div>';

    // Utiliser l'URL configurée ou une URL relative par défaut si config n'est pas dispo
    const baseUrl = (typeof config !== 'undefined' && config.lara && config.lara.baseUrl)
        ? config.lara.baseUrl
        : '/api';

    const url = `${baseUrl}/domaines`;

    try {
        const response = await fetch(url);
        if (!response.ok) throw new Error(`Erreur ${response.status}`);

        allDomains = await response.json();

        if (allDomains.length === 0) {
            container.innerHTML = '<div class="domains-empty">Aucun domaine trouvé</div>';
            return;
        }

        renderDomainsTable(allDomains);
        setupDomainFilters();
    } catch (error) {
        console.error('Erreur lors du chargement des domaines:', error);
        container.innerHTML = '<div class="domains-error">Erreur de chargement des domaines</div>';
    }
}

function renderDomainsTable(domains) {
    const container = document.getElementById('domainsTableContent');
    if (!container) return;

    container.innerHTML = `
        <div class="domains-filters">
            <div class="filters-row">
                <input type="text" id="filterDomainName" class="filter-input" placeholder="Filtrer par nom...">
                <input type="text" id="filterProche" class="filter-input" placeholder="Filtrer par domaine proche...">
                <button id="clearDomainFiltersBtn" class="clear-filters-btn" title="Supprimer les filtres">✕ Filtres</button>
            </div>
        </div>
        <table class="domains-table">
            <thead>
                <tr>
                    <th>Nom du Domaine</th>
                    <th>Domaines Proches</th>
                </tr>
            </thead>
            <tbody id="domainsTableBody">
                ${generateDomainRows(domains)}
            </tbody>
        </table>
        <div class="domains-count">${domains.length} domaine(s) affiché(s)</div>
    `;
}

function generateDomainRows(domains) {
    if (domains.length === 0) {
        return '<tr><td colspan="2" class="domains-empty">Aucun domaine ne correspond aux filtres</td></tr>';
    }
    return domains.map(domain => {
        const prochesHtml = domain.proches.map(p => `<span class="domain-proche-tag">${p}</span>`).join('');
        return `
        <tr>
            <td class="domain-name-cell">${domain.name}</td>
            <td>${prochesHtml || '-'}</td>
        </tr>
    `}).join('');
}

function setupDomainFilters() {
    const nameInput = document.getElementById('filterDomainName');
    const procheInput = document.getElementById('filterProche');
    const clearBtn = document.getElementById('clearDomainFiltersBtn');

    if (nameInput) nameInput.addEventListener('input', applyDomainFilters);
    if (procheInput) procheInput.addEventListener('input', applyDomainFilters);
    if (clearBtn) clearBtn.addEventListener('click', clearDomainFilters);
}

function applyDomainFilters() {
    const nameFilter = (document.getElementById('filterDomainName')?.value || '').toLowerCase();
    const procheFilter = (document.getElementById('filterProche')?.value || '').toLowerCase();

    const filteredDomains = allDomains.filter(domain => {
        const name = (domain.name || '').toLowerCase();
        const proches = domain.proches.map(p => p.toLowerCase());

        const nameMatch = name.includes(nameFilter);
        const procheMatch = procheFilter === '' || proches.some(p => p.includes(procheFilter));

        return nameMatch && procheMatch;
    });

    const tbody = document.getElementById('domainsTableBody');
    const countDiv = document.querySelector('.domains-count');

    if (tbody) {
        tbody.innerHTML = generateDomainRows(filteredDomains);
    }
    if (countDiv) {
        countDiv.textContent = `${filteredDomains.length} domaine(s) affiché(s) sur ${allDomains.length}`;
    }
}

function clearDomainFilters() {
    const nameInput = document.getElementById('filterDomainName');
    const procheInput = document.getElementById('filterProche');

    if (nameInput) nameInput.value = '';
    if (procheInput) procheInput.value = '';

    applyDomainFilters();
}
