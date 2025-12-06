// Affichage des résultats de fichiers (commun Lexa/Lara)
function displayFileResults(results, originalFiles) {
    console.log('🔍 [DEBUG] displayFileResults appelé avec:');
    console.log('  - Nombre de résultats:', results.length);
    console.log('  - Résultats complets:', results);
    console.log('  - Fichiers originaux:', originalFiles);

    const fileResults = document.getElementById('fileResults');
    const resultSection = document.getElementById('resultSection');
    const qualityFeedback = document.getElementById('qualityFeedback');
    qualityFeedback.style.display = 'none';
    resultSection.style.display = 'block';
    fileResults.style.display = 'block';
    fileResults.innerHTML = '';
    results.forEach((result, index) => {
        console.log(`🔍 [DEBUG] Traitement du résultat ${index}:`, result);

        const fileResult = document.createElement('div');
        fileResult.className = 'file-result';
        const originalFileName = originalFiles[index]?.name || result.source_file_name || `Fichier ${index + 1}`;
        const status = result.status || 'Unknown';
        const statusClass = getStatusClass(status);
        fileResult.innerHTML = `
            <div class="file-result-row">
                <div class="file-result-name">${originalFileName}</div>
                <span class="status-badge ${statusClass}">${status}</span>
                ${result.id ? `<div class="detail-item"><span class="detail-label">ID:</span> <span class="detail-value">${result.id}</span></div>` : ''}
                <div class="detail-item"><span class="detail-label">Langues:</span> <span class="detail-value">${result.source_language} → ${result.target_language}</span></div>
                ${result.created_at ? `<div class="detail-item"><span class="detail-label">Créé:</span> <span class="detail-value">${formatDate(result.created_at)}</span></div>` : ''}
                ${result.updated_at ? `<div class="detail-item"><span class="detail-label">Màj:</span> <span class="detail-value">${formatDate(result.updated_at)}</span></div>` : ''}
                <div class="download-buttons" id="downloads-${index}">
                    ${generateDownloadButtons(result)}
                </div>
            </div>
            ${result.error ? `<div class="detail-error"><span class="detail-label">Erreur:</span> <span class="detail-value">${result.error}</span></div>` : ''}
        `;
        fileResults.appendChild(fileResult);
    });
}

function getStatusClass(status) {
    switch (status.toLowerCase()) {
        case 'translated': return 'status-translated';
        case 'processing':
        case 'pending':
        case 'initialized': return 'status-processing';
        case 'error':
        case 'failed': return 'status-error';
        default: return 'status-processing';
    }
}

function generateDownloadButtons(result) {
    console.log('🔍 [DEBUG] generateDownloadButtons appelé avec:', result);

    let buttons = '';
    // Support pour le backend Django (downloadUrl) et l'ancien backend Node.js (translated_file)
    const downloadUrl = result.downloadUrl || result.translated_file;

    console.log('🔍 [DEBUG] downloadUrl extrait:', downloadUrl);
    console.log('🔍 [DEBUG] result.downloadUrl:', result.downloadUrl);
    console.log('🔍 [DEBUG] result.translated_file:', result.translated_file);

    if (downloadUrl) {
        console.log('✅ [DEBUG] Bouton de téléchargement créé pour:', downloadUrl);
        buttons += `<a href="${downloadUrl}" class="download-btn" download>📄 Fichier traduit</a>`;
    } else {
        console.warn('⚠️ [DEBUG] Aucun downloadUrl trouvé dans result');
    }

    if (result.source_file) buttons += `<a href="${result.source_file}" class="download-btn secondary" download>📄 Fichier source</a>`;
    if (result.tmx_file) buttons += `<a href="${result.tmx_file}" class="download-btn secondary" download>📄 TMX</a>`;
    if (result.xliff_file) buttons += `<a href="${result.xliff_file}" class="download-btn secondary" download>📄 XLIFF</a>`;
    if (result.reviewed_file) buttons += `<a href="${result.reviewed_file}" class="download-btn" download>📄 Fichier révisé</a>`;

    if (!buttons) {
        console.warn('⚠️ [DEBUG] Aucun bouton généré, affichage du message par défaut');
        buttons = '<span style="color: #6b7280; font-size: 12px;">Fichier en cours de traitement ou erreur</span>';
    }

    console.log('🔍 [DEBUG] Boutons générés:', buttons);
    return buttons;
}

function formatDate(dateString) {
    if (!dateString) return 'N/A';
    try {
        return new Date(dateString).toLocaleString('fr-FR', {
            year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit'
        });
    } catch (e) { return dateString; }
}
// js/utils.js : fonctions utilitaires

function showMessage(msg, type = 'info') {
    const messageDiv = document.getElementById('message');
    if (!messageDiv) return;
    messageDiv.textContent = msg;
    messageDiv.className = type;
    setTimeout(() => {
        messageDiv.textContent = '';
        messageDiv.className = '';
    }, 4000);
}

function setLoading(isLoading) {
    const translateBtn = document.getElementById('translateBtn');
    const loadingDiv = document.getElementById('loading');

    if (translateBtn) {
        translateBtn.disabled = isLoading;
        translateBtn.textContent = isLoading ? 'Traduction en cours...' : 'Traduire';
    }

    if (loadingDiv) {
        loadingDiv.style.display = isLoading ? 'block' : 'none';
    }
}
