// js/init.js : Initialisation de l'application au chargement de la page

document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 Initialisation de l\'application...');

    // Configurer les event listeners
    setupEventListeners();

    // Charger la configuration depuis le localStorage
    loadConfigFromStorage();

    // Mettre à jour la visibilité des options Lara/Lexa dès le départ
    updateLaraOptionsVisibility();

    // Debug: Afficher l'URL du backend utilisé
    console.log('📍 Backend URL:', config.lara.baseUrl);
    console.log('⚙️  Service:', config.translationService);

    // Si pas de configuration valide, ouvrir le modal de paramètres
    if (!hasValidConfig()) {
        console.log('⚠️  Aucune configuration valide, ouverture du modal de paramètres');
        openSettingsModal();
    } else {
        console.log('✅ Configuration valide, initialisation du service');
        initializeForCurrentService();
    }
});
