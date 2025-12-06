const fs = require('fs').promises;
const xml2js = require('xml2js');

async function generateTemplates() {
    // Statistiques pour le rapport final
    let totalTemplates = 0;
    let templatesWithMemory = 0;
    let templatesWithoutMemory = 0;
    try {
        // Charger les ressources Lara
        const path = require('path');
        const resourcesContent = await fs.readFile(path.join(__dirname, 'lara-resources.json'), 'utf-8');
        const resources = JSON.parse(resourcesContent);

        // Charger les mémoires depuis le XML
        const memoriesXmlContent = await fs.readFile(path.join(__dirname, 'lara-memories.xml'), 'utf-8');
        const memoriesParser = new xml2js.Parser();
        const memoriesXml = await memoriesParser.parseStringPromise(memoriesXmlContent);
        const memories = memoriesXml.memories.memory.map(m => ({
            id: m.id[0],
            name: m.name[0],
            sourceLanguage: m.sourceLanguage[0],
            targetLanguage: m.targetLanguage[0],
            domains: m.domains[0] ? m.domains[0].split(',') : [],
            languagePairs: m.languagePairs[0].pair ? m.languagePairs[0].pair.map(p => ({
                source: p.$.source,
                target: p.$.target
            })) : []
        }));

        console.log('📊 Génération des templates...');
        console.log(`   - ${memories.length} mémoires de traduction`);
        console.log(`   - ${resources.glossaries.length} glossaires\n`);

        // Mapping entre les domaines du système et les mémoires Lara
        const memoryMapping = {
            'Accounting': '1.1 DROIT FINANCIER FR<>EN',
            'Banking': '1.1 DROIT FINANCIER FR<>EN',
            'Investment': '1.1 DROIT FINANCIER FR<>EN',
            'Insurance': '1.1 DROIT FINANCIER FR<>EN',
            'Arbitration': '1.2 LITIGES FR<>EN',
            'Crimes-proceedings': '1.9 DROIT PENAL FR<>EN',
            'Criminal finance': '1.9 DROIT PENAL FR<>EN',
            'Real Estate': '1.3 DROIT IMMOBILIER FR<>EN',
            'Contracts': '1.4 DROIT COMMERCIAL FR<>EN',
            'Competition': '1.4 DROIT COMMERCIAL FR<>EN',
            'Corporate': '1.6 DROIT DES SOCIETES FR<>EN',
            'Tax': '1.5 DROIT FISCAL FR<>EN',
            'Customs': '1.5 DROIT FISCAL FR<>EN',
            'Patents': '1.7. PI/IT FR<>EN',
            'Industrial designs': '1.7. PI/IT FR<>EN',
            'Labour law': '1.8 DROIT SOCIAL FR<>EN',
            'HR': '1.8 DROIT SOCIAL FR<>EN',
            'Social benefits': '1.8 DROIT SOCIAL FR<>EN',
            'Social security': '1.8 DROIT SOCIAL FR<>EN',
            'GDPR': '1.7. PI/IT FR<>EN',
            'Climate': '1.9 DROIT PUBLIC FR<>EN',
            'Town planning': '1.9 DROIT PUBLIC FR<>EN',
            'Maritime law': '1.9 DROIT MARITIME FR<>EN',
            'Transport': '1.9 TECHNIQUE FR<>EN'
        };

        // Trouver la mémoire par défaut
        const defaultMemory = memories.find(m => m.name === '2.1 GENERIQUE FR<>ENus');

        // Créer la structure XML
        const templates = {
            'translation-templates': {
                template: []
            }
        };

        // Template par défaut
        templates['translation-templates'].template.push({
            $: {
                id: 'default',
                name: 'Default Template',
                'is-default': 'true'
            },
            domain: '*',
            'source-language': '*',
            'target-language': '*',
            'translation-memory-id': '',
            'translation-memory-name': '',
            'glossary-id': '',
            'glossary-name': '',
            description: 'Template par défaut utilisé lorsqu\'aucune configuration spécifique n\'est trouvée'
        });


        // Grouper les glossaires par domaine
        const glossariesByDomain = {};
        resources.glossaries.forEach(g => {
            if (!glossariesByDomain[g.domain]) {
                glossariesByDomain[g.domain] = [];
            }
            glossariesByDomain[g.domain].push(g);
        });

        // Pour tous les glossaires (triés par domaine pour la clarté)
        const allDomains = Object.keys(glossariesByDomain);

        for (const domain of allDomains) {
            const domainGlossaries = glossariesByDomain[domain];
            // Mémoire spécifique définie dans le mapping ?
            const specificMemoryName = memoryMapping[domain];

            for (const glossary of domainGlossaries) {
                const sourceLang = glossary.sourceLanguage;
                if (Array.isArray(glossary.targetLanguages) && glossary.targetLanguages.length > 0) {
                    for (const targetLang of glossary.targetLanguages) {
                        if (sourceLang === targetLang) continue;
                        const templateId = `${domain.toLowerCase().replace(/[^a-z0-9]/g, '-')}-${sourceLang.toLowerCase()}-${targetLang.toLowerCase()}`;

                        let memory = null;

                        // 1. Essayer la mémoire spécifique
                        if (specificMemoryName) {
                            const specificMemory = memories.find(m => m.name === specificMemoryName);
                            if (specificMemory) {
                                const sLang = sourceLang.toUpperCase();
                                const tLang = targetLang.toUpperCase();
                                const pairMatches = specificMemory.languagePairs.some(pair =>
                                    (pair.source.toUpperCase() === sLang && pair.target.toUpperCase() === tLang) ||
                                    (pair.source.toUpperCase() === tLang && pair.target.toUpperCase() === sLang)
                                );
                                if (pairMatches) {
                                    memory = specificMemory;
                                }
                            }
                        }

                        // 2. Si pas de mémoire spécifique, essayer la mémoire générique
                        if (!memory && defaultMemory) {
                            const sLang = sourceLang.toUpperCase();
                            const tLang = targetLang.toUpperCase();
                            // Vérifier si la générique supporte cette paire
                            const pairMatches = defaultMemory.languagePairs.some(pair =>
                                (pair.source.toUpperCase() === sLang && pair.target.toUpperCase() === tLang) ||
                                (pair.source.toUpperCase() === tLang && pair.target.toUpperCase() === sLang)
                            );
                            if (pairMatches) {
                                memory = defaultMemory;
                            }
                        }

                        if (memory) {
                            // console.log(`Mémoire trouvée pour ${domain} ${sourceLang}->${targetLang}: ${memory.name}`);
                        }

                        templates['translation-templates'].template.push({
                            $: {
                                id: templateId,
                                name: `${domain} ${sourceLang} to ${targetLang}`
                            },
                            domain: domain,
                            'source-language': sourceLang,
                            'target-language': targetLang,
                            'translation-memory-id': memory ? memory.id : '',
                            'translation-memory-name': memory ? memory.name : '',
                            'glossary-id': glossary.id,
                            'glossary-name': glossary.name,
                            description: `Template pour la traduction du domaine ${domain} de ${sourceLang} vers ${targetLang}`
                        });
                        totalTemplates++;
                        if (memory) {
                            templatesWithMemory++;
                        } else {
                            templatesWithoutMemory++;
                        }
                    }
                } else {
                    // Cas sans targetLanguages (legacy)
                    // ... (similaire, simplifié pour brevity si pas utilisé souvent)
                }
            }
        }

        console.log(`✅ ${templates['translation-templates'].template.length} templates générés\n`);

        // ...


        // Construire le XML
        const builder = new xml2js.Builder({
            xmldec: { version: '1.0', encoding: 'UTF-8' },
            renderOpts: { pretty: true, indent: '  ' }
        });
        const xml = builder.buildObject(templates);

        // Sauvegarder
        await fs.writeFile(path.join(__dirname, 'templates.xml'), xml, 'utf-8');
        console.log('💾 Fichier templates.xml généré avec succès!');

        // Afficher quelques exemples
        // Afficher quelques exemples (mixte avec/sans mémoire)
        console.log('\n📋 Exemples de templates générés:');
        const examples = templates['translation-templates'].template.filter(t => t['translation-memory-id']).slice(0, 3)
            .concat(templates['translation-templates'].template.filter(t => !t['translation-memory-id']).slice(0, 3));

        examples.forEach(t => {
            console.log(`\n   ${t.$.name}`);
            console.log(`   - Domaine: ${t.domain}`);
            console.log(`   - ${t['source-language']} → ${t['target-language']}`);
            console.log(`   - Mémoire: ${t['translation-memory-name'] || '(non défini)'} (${t['translation-memory-id'] || 'pas d\'ID'})`);
            console.log(`   - Glossaire: ${t['glossary-name'] || '(non défini)'} (${t['glossary-id'] || 'pas d\'ID'})`);
        });

        // Rapport final bien visible
        console.log('\n' + '-'.repeat(60));
        console.log('📑 Rapport de génération :');
        console.log(`   - Total de templates générés : ${totalTemplates}`);
        console.log(`   - Templates AVEC mémoire de traduction : ${templatesWithMemory}`);
        console.log(`   - Templates SANS mémoire de traduction : ${templatesWithoutMemory}`);
        if (totalTemplates > 0) {
            const percentWith = ((templatesWithMemory / totalTemplates) * 100).toFixed(1);
            const percentWithout = ((templatesWithoutMemory / totalTemplates) * 100).toFixed(1);
            console.log(`   - % avec mémoire : ${percentWith}%`);
            console.log(`   - % sans mémoire : ${percentWithout}%`);
        }
        console.log('-'.repeat(60) + '\n');

    } catch (error) {
        console.error('❌ Erreur:', error.message);
        console.error(error);
        process.exit(1);
    }
}

generateTemplates();
