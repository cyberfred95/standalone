const { Translator, Credentials } = require('@translated/lara');
const fs = require('fs').promises;
const path = require('path');
const dotenv = require('dotenv');

dotenv.config({ override: true });

// Chemin vers le répertoire des glossaires locaux
const GLOSSARIES_DIR = path.join(__dirname, '..', 'glossaires', 'laratranslation');

// Fonction pour extraire les langues cibles depuis un fichier glossaire local
async function getTargetLanguagesFromLocalFile(glossaryName) {
    try {
        // Extraire domain et sourceLanguage depuis le nom Lara (ex: Legal_Competition_FR)
        const match = glossaryName.match(/^Legal_([^_]+)_([^_]+)$/);
        if (!match) {
            return [];
        }

        const domain = match[1];
        const sourceLanguage = match[2];

        // Construire le chemin du fichier local (ex: Competition_FR.csv)
        const localFileName = `${domain}_${sourceLanguage}.csv`;
        const localFilePath = path.join(GLOSSARIES_DIR, localFileName);

        // Lire la première ligne du fichier
        const content = await fs.readFile(localFilePath, 'utf-8');
        const firstLine = content.split('\n')[0].trim();

        // Parser les langues (première = source, reste = cibles)
        const languages = firstLine.split(',').map(lang => lang.trim());

        if (languages.length > 1) {
            // Retourner toutes les langues sauf la première (qui est la source)
            return languages.slice(1);
        }

        return [];
    } catch (error) {
        // Fichier non trouvé ou erreur de lecture - pas grave, on retourne vide
        return [];
    }
}

// Fonction pour échapper les caractères spéciaux XML
function escapeXml(str) {
    if (!str) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&apos;');
}

// Fonction pour générer le XML des mémoires de traduction
function generateMemoriesXml(memories) {
    const timestamp = new Date().toISOString();
    let xml = `<?xml version="1.0" encoding="UTF-8"?>
<!--
    Mémoires de traduction Lara
    Généré le: ${timestamp}
    Ce fichier sert de base pour la génération des templates de traduction
-->
<memories count="${memories.length}" generated="${timestamp}">
`;

    memories.forEach(memory => {
        xml += `    <memory>
        <id>${escapeXml(memory.id)}</id>
        <name>${escapeXml(memory.name)}</name>
        <sourceLanguage>${escapeXml(memory.sourceLanguage)}</sourceLanguage>
        <targetLanguage>${escapeXml(memory.targetLanguage)}</targetLanguage>
        <domains>${Array.isArray(memory.domains) ? memory.domains.map(escapeXml).join(',') : escapeXml(memory.domain || '')}</domains>
        <languagePairs>
`;
        if (memory.languagePairs) {
            memory.languagePairs.forEach(pair => {
                xml += `            <pair source="${escapeXml(pair.source)}" target="${escapeXml(pair.target)}"/>
`;
            });
        }
        xml += `        </languagePairs>
    </memory>
`;
    });

    xml += `</memories>
`;
    return xml;
}

// Fonction pour générer le XML des glossaires (avec langues cibles)
function generateGlossariesXml(glossaries) {
    const timestamp = new Date().toISOString();
    let xml = `<?xml version="1.0" encoding="UTF-8"?>
<!--
    Glossaires Lara
    Généré le: ${timestamp}
    Ce fichier sert de base pour la génération des templates de traduction
-->
<glossaries count="${glossaries.length}" generated="${timestamp}">
`;

    glossaries.forEach(glossary => {
        xml += `    <glossary>
        <id>${escapeXml(glossary.id)}</id>
        <name>${escapeXml(glossary.name)}</name>
        <sourceLanguage>${escapeXml(glossary.sourceLanguage)}</sourceLanguage>
        <targetLanguages>${escapeXml((glossary.targetLanguages || []).join(','))}</targetLanguages>
        <domain>${escapeXml(glossary.domain)}</domain>
    </glossary>
`;
    });

    xml += `</glossaries>
`;
    return xml;
}

async function listLaraResources() {
    try {
        // Récupérer les credentials depuis les variables d'environnement
        const accessKeyId = process.env.LARA_ACCESS_KEY_ID;
        const accessKeySecret = process.env.LARA_ACCESS_KEY_SECRET;

        if (!accessKeyId || !accessKeySecret) {
            console.error('Erreur: LARA_ACCESS_KEY_ID et LARA_ACCESS_KEY_SECRET doivent etre definis dans .env');
            console.log('\nVeuillez creer un fichier .env avec:');
            console.log('LARA_ACCESS_KEY_ID=votre_key_id');
            console.log('LARA_ACCESS_KEY_SECRET=votre_secret');
            process.exit(1);
        }

        console.log('Connexion a Lara...');
        console.log(`   Access Key ID: ${accessKeyId.substring(0, 8)}...`);
        const credentials = new Credentials(accessKeyId, accessKeySecret);
        const lara = new Translator(credentials);

        // Lister les mémoires de traduction
        console.log('\nRecuperation des memoires de traduction...');
        let memories = [];
        try {
            memories = await lara.memories.list();
            console.log(`${memories.length} memoires trouvees:\n`);

            if (memories.length === 0) {
                console.log('Aucune memoire trouvee. Verifications:');
                console.log('   - Les cles API sont-elles correctes?');
                console.log('   - Y a-t-il des memoires configurees dans votre compte Lara?');
            }

            memories.forEach((memory, index) => {
                console.log(`${index + 1}. ID: ${memory.id}`);
                console.log(`   Nom: ${memory.name || 'Sans nom'}`);
                console.log(`   Langue source: ${memory.sourceLanguage || 'N/A'}`);
                console.log(`   Langue cible: ${memory.targetLanguage || 'N/A'}`);
                console.log(`   Domaine: ${memory.domain || 'N/A'}`);
                console.log('');
            });
        } catch (memoryError) {
            console.error('Erreur lors de la recuperation des memoires:', memoryError.message);
            console.error('   Details:', memoryError);
        }

        // Lister les glossaires
        console.log('\nRecuperation des glossaires depuis Lara...');
        let glossaries = [];

        try {
            const laraGlossaries = await lara.glossaries.list();
            console.log(`${laraGlossaries.length} glossaires trouves sur Lara:\n`);

            laraGlossaries.forEach((glossary, index) => {
                if (index < 5) {
                    console.log(`${index + 1}. ID: ${glossary.id}`);
                    console.log(`   Nom: ${glossary.name || 'Sans nom'}`);
                    console.log('');
                }

                // Extraire domaine et langue depuis le nom
                // Ex: Legal_Accounting_BG -> domain: Accounting, lang: BG
                const name = glossary.name || '';
                const match = name.match(/^Legal_([^_]+)_([^_]+)$/);

                if (match) {
                    glossaries.push({
                        id: glossary.id,
                        name: glossary.name,
                        domain: match[1],
                        sourceLanguage: match[2]
                    });
                } else {
                    // Glossaire qui ne suit pas la convention, le garder quand même
                    glossaries.push({
                        id: glossary.id,
                        name: glossary.name,
                        domain: '',
                        sourceLanguage: ''
                    });
                }
            });

            if (laraGlossaries.length > 5) {
                console.log(`   ... et ${laraGlossaries.length - 5} autres glossaires\n`);
            }
        } catch (glossaryError) {
            console.error('Erreur lors de la recuperation des glossaires:', glossaryError.message);
            console.error('   Details:', glossaryError);
        }


        // --- ENRICHISSEMENT DES MEMOIRES ---
        // Exemple de mapping (à adapter selon la logique métier réelle)
        // Pour chaque mémoire, on peut associer plusieurs domaines proches
        // et déduire les langues à partir du nom si besoin
        const domainMappings = {
            '1.1 DROIT FINANCIER FR<>EN': ['Accounting', 'Banking', 'Investment', 'Insurance'],
            '1.2 LITIGES FR<>EN': ['Arbitration'],
            '1.3 DROIT IMMOBILIER FR<>EN': ['Real Estate'],
            '1.4 DROIT COMMERCIAL FR<>EN': ['Contracts', 'Competition'],
            '1.5 DROIT FISCAL FR<>EN': ['Tax', 'Customs'],
            '1.6 DROIT DES SOCIETES FR<>EN': ['Corporate'],
            '1.7. PI/IT FR<>EN': ['Patents', 'Industrial designs', 'GDPR'],
            '1.8 DROIT SOCIAL FR<>EN': ['Labour law', 'HR', 'Social benefits', 'Social security'],
            '1.9 DROIT PENAL FR<>EN': ['Crimes-proceedings', 'Criminal finance'],
            '1.9 DROIT PUBLIC FR<>EN': ['Climate', 'Town planning'],
            '1.9 DROIT MARITIME FR<>EN': ['Maritime law'],
            '1.9 TECHNIQUE FR<>EN': ['Transport'],
            // ... autres mappings si besoin
        };

        // Fonction utilitaire pour extraire les langues à partir du nom
        function extractLangsFromName(name) {
            const match = name.match(/([A-Z]{2})<>?([A-Z]{2})/);
            if (match) {
                return [match[1], match[2]];
            }
            return ['', ''];
        }

        // Fonction pour lire et parser domaines.xml
        async function loadDomainesProximity() {
            try {
                const xmlContent = await fs.readFile('server/domaines.xml', 'utf-8');
                const proximity = {};
                // Parser simple du XML
                const domaineMatches = xmlContent.matchAll(/<domaine name="([^"]+)">(.*?)<\/domaine>/gs);
                for (const match of domaineMatches) {
                    const domainName = match[1];
                    const prochesContent = match[2];
                    const proches = [];
                    const procheMatches = prochesContent.matchAll(/<proche>([^<]+)<\/proche>/g);
                    for (const pMatch of procheMatches) {
                        proches.push(pMatch[1]);
                    }
                    proximity[domainName] = proches;
                }
                return proximity;
            } catch (error) {
                console.warn('Impossible de lire server/domaines.xml, utilisation du mapping statique');
                return {
                    'Accounting': ['Banking', 'Investment', 'Insurance'],
                    'Banking': ['Accounting', 'Investment', 'Insurance'],
                    'Investment': ['Accounting', 'Banking', 'Insurance'],
                    'Insurance': ['Accounting', 'Banking', 'Investment'],
                    'Arbitration': ['Crimes-proceedings', 'Corporate'],
                    'Real Estate': ['Town planning', 'Contracts'],
                    'Contracts': ['Competition', 'Corporate'],
                    'Competition': ['Contracts', 'Corporate'],
                    'Corporate': ['Contracts', 'Competition'],
                    'Tax': ['Customs'],
                    'Customs': ['Tax'],
                    'Patents': ['Industrial designs', 'GDPR'],
                    'Industrial designs': ['Patents', 'GDPR'],
                    'GDPR': ['Patents', 'Industrial designs'],
                    'Labour law': ['HR', 'Social benefits', 'Social security'],
                    'HR': ['Labour law', 'Social benefits', 'Social security'],
                    'Social benefits': ['Labour law', 'HR', 'Social security'],
                    'Social security': ['Labour law', 'HR', 'Social benefits'],
                    'Crimes-proceedings': ['Criminal finance'],
                    'Criminal finance': ['Crimes-proceedings'],
                    'Climate': ['Town planning'],
                    'Town planning': ['Climate'],
                    'Maritime law': [],
                    'Transport': [],
                };
            }
        }

        const domainProximity = await loadDomainesProximity();

        const memoriesData = memories.map(m => {
            let primaryDomains = domainMappings[m.name] || [];

            // Cas spécial pour la mémoire générique FR<>EN : elle s'applique à tous les domaines
            if (m.name && m.name.includes('GENERIQUE') && m.name.includes('FR') && m.name.includes('EN')) {
                primaryDomains = Object.keys(domainProximity);
            }

            let [sourceLanguage, targetLanguage] = extractLangsFromName(m.name);
            // Si l'API fournit déjà les langues, on les garde
            if (m.sourceLanguage) sourceLanguage = m.sourceLanguage;
            if (m.targetLanguage) targetLanguage = m.targetLanguage;

            // Collecter tous les domaines liés (primaires + proches)
            const allDomains = new Set(primaryDomains);
            primaryDomains.forEach(domain => {
                if (domainProximity[domain]) {
                    domainProximity[domain].forEach(proche => allDomains.add(proche));
                }
            });

            return {
                id: m.id || '',
                name: m.name || '',
                sourceLanguage: sourceLanguage || '',
                targetLanguage: targetLanguage || '',
                domains: Array.from(allDomains),
                languagePairs: [
                    { source: sourceLanguage, target: targetLanguage },
                    { source: targetLanguage, target: sourceLanguage }
                ].filter(pair => pair.source && pair.target)
            };
        });
        // --- GENERATION DU FICHIER DOMAINES.XML ---

        // Générer le XML des domaines et proximités
        function generateDomainesXml(domainProximity) {
            const timestamp = new Date().toISOString();
            let xml = `<?xml version="1.0" encoding="UTF-8"?>\n<!--\n    Domaines et proximités\n    Généré le: ${timestamp}\n    Ce fichier liste pour chaque domaine les domaines proches\n-->\n<domaines generated="${timestamp}">\n`;
            for (const [domain, proches] of Object.entries(domainProximity)) {
                xml += `  <domaine name="${escapeXml(domain)}">\n`;
                proches.forEach(p => {
                    xml += `    <proche>${escapeXml(p)}</proche>\n`;
                });
                xml += `  </domaine>\n`;
            }
            xml += `</domaines>\n`;
            return xml;
        }

        // Enrichir les glossaires avec les langues cibles depuis les fichiers locaux
        console.log('\nRecuperation des langues cibles depuis les fichiers locaux...');
        const glossariesData = [];
        for (const g of glossaries) {
            const targetLanguages = await getTargetLanguagesFromLocalFile(g.name);
            glossariesData.push({
                id: g.id || '',
                name: g.name || '',
                sourceLanguage: g.sourceLanguage || '',
                targetLanguages: targetLanguages,
                domain: g.domain || ''
            });
        }
        console.log(`   ${glossariesData.filter(g => g.targetLanguages.length > 0).length} glossaires avec langues cibles trouvees`);

        // Sauvegarder dans un fichier JSON (compatibilité)
        const data = {
            memories: memoriesData,
            glossaries: glossariesData
        };

        await fs.writeFile(
            'server/lara-resources.json',
            JSON.stringify(data, null, 2),
            'utf-8'
        );
        console.log('\nDonnees sauvegardees dans server/lara-resources.json');

        // Générer et sauvegarder le fichier XML des mémoires
        const memoriesXml = generateMemoriesXml(memoriesData);
        await fs.writeFile(
            'server/lara-memories.xml',
            memoriesXml,
            'utf-8'
        );
        console.log('Memoires sauvegardees dans server/lara-memories.xml');

        // Générer et sauvegarder le fichier domaines.xml
        const domainesXml = generateDomainesXml(domainProximity);
        await fs.writeFile(
            'server/domaines.xml',
            domainesXml,
            'utf-8'
        );
        console.log('Domaines sauvegardés dans server/domaines.xml');

        // Générer et sauvegarder le fichier XML des glossaires
        const glossariesXml = generateGlossariesXml(glossariesData);
        await fs.writeFile(
            'server/lara-glossaries.xml',
            glossariesXml,
            'utf-8'
        );
        console.log('Glossaires sauvegardes dans server/lara-glossaries.xml');

        console.log(`\nResume:`);
        console.log(`   - ${memories.length} memoires de traduction`);
        console.log(`   - ${glossaries.length} glossaires`);
        console.log(`\nFichiers generes:`);
        console.log(`   - server/lara-resources.json (JSON combine)`);
        console.log(`   - server/lara-memories.xml (memoires pour templates)`);
        console.log(`   - server/lara-glossaries.xml (glossaires pour templates)`);

    } catch (error) {
        console.error('Erreur:', error.message);
        console.error(error);
        process.exit(1);
    }
}

listLaraResources();
