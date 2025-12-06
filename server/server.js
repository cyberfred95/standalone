const express = require('express');
const cors = require('cors');
const multer = require('multer');
const dotenv = require('dotenv');
const { Translator, Credentials } = require('@translated/lara');
const fs = require('fs').promises;
const path = require('path');
const xml2js = require('xml2js');

// Charger les variables d'environnement
dotenv.config();
console.log('PORT:', process.env.PORT);
console.log('NODE_ENV:', process.env.NODE_ENV);

const app = express();
const PORT = process.env.PORT || 3000;

// Configuration de multer pour l'upload de fichiers
const upload = multer({
    dest: 'uploads/',
    limits: { fileSize: 50 * 1024 * 1024 } // 50MB max
});

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Fonction pour convertir les codes de langue courts en codes avec locale
function normalizeLanguageCode(code) {
    if (!code) return code;

    // Si déjà au format xx-XX, retourner tel quel
    if (code.includes('-')) return code;

    // Mapping des codes courts vers codes avec locale
    const langMap = {
        'en': 'en-US',
        'fr': 'fr-FR',
        'es': 'es-ES',
        'de': 'de-DE',
        'it': 'it-IT',
        'pt': 'pt-PT',
        'nl': 'nl-NL',
        'pl': 'pl-PL',
        'ru': 'ru-RU',
        'ja': 'ja-JP',
        'zh': 'zh-CN',
        'ar': 'ar-SA'
    };

    const normalized = langMap[code.toLowerCase()] || code;
    console.log(`Normalisation langue: ${code} -> ${normalized}`);
    return normalized;
}

// Fonction pour nettoyer le HTML avant envoi à Lara
// Remplace les paragraphes vides par <br> pour éviter les bugs de traduction
function cleanHtmlForLara(html) {
    if (!html) return html;
    return html
        // Remplacer <p><br></p> et variantes par <br>
        .replace(/<p>\s*<br\s*\/?>\s*<\/p>/gi, '<br>')
        // Remplacer <p>&nbsp;</p> (paragraphe avec espace insécable) par <br>
        .replace(/<p>(\s|&nbsp;)*<\/p>/gi, '<br>')
        // Supprimer les paragraphes complètement vides
        .replace(/<p>\s*<\/p>/gi, '');
}

// Fonction pour créer un client Lara avec les credentials fournis
function createLaraClient(accessKeyId, accessKeySecret) {
    console.log('Création du client Lara avec:', {
        accessKeyId: accessKeyId ? '***' + accessKeyId.slice(-4) : 'undefined',
        accessKeySecret: accessKeySecret ? '***' : 'undefined'
    });

    if (!accessKeyId || !accessKeySecret) {
        throw new Error('Access Key ID et Secret sont requis');
    }

    try {
        const credentials = new Credentials(accessKeyId, accessKeySecret);
        return new Translator(credentials);
    } catch (error) {
        console.error('Erreur lors de la création du client Lara:', error);
        throw error;
    }
}

// ==================== Routes ====================

// Health check
app.get('/health', (req, res) => {
    res.json({ status: 'ok', service: 'lara-translation-server' });
});

// Traduction de texte avec Lara
app.post('/api/lara/translate-text', async (req, res) => {
    try {
        const {
            accessKeyId,
            accessKeySecret,
            text,
            source,
            target,
            domain,
            style,
            instructions,
            adaptTo,
            glossaries
        } = req.body;

        // Validation
        if (!accessKeyId || !accessKeySecret) {
            return res.status(400).json({
                error: 'access_key_id et access_key_secret sont requis'
            });
        }

        if (!text || !target) {
            return res.status(400).json({
                error: 'text et target sont requis'
            });
        }

        // Créer le client Lara
        const lara = createLaraClient(accessKeyId, accessKeySecret);

        // Normaliser les codes de langue
        const normalizedTarget = normalizeLanguageCode(target);
        const normalizedSource = source ? normalizeLanguageCode(source) : undefined;

        // Préparer les options
        const options = {};

        if (normalizedSource) options.source = normalizedSource;
        if (domain) options.domain = domain;
        if (style) options.style = style;
        if (instructions) options.instructions = instructions;

        // Note: L'option 'quality' n'existe pas dans le SDK Lara officiel
        // Les options disponibles sont: adaptTo, glossaries, instructions, style, verbose, etc.

        // Convertir les chaînes d'IDs en tableaux
        // Si adaptTo est fourni, l'utiliser ; sinon envoyer un tableau vide pour désactiver les mémoires par défaut
        if (adaptTo) {
            options.adaptTo = typeof adaptTo === 'string'
                ? adaptTo.split(',').map(id => id.trim()).filter(id => id)
                : adaptTo;
        } else {
            // Tableau vide = pas de mémoire (évite que Lara utilise toutes les mémoires du compte)
            options.adaptTo = [];
        }

        if (glossaries) {
            options.glossaries = typeof glossaries === 'string'
                ? glossaries.split(',').map(id => id.trim()).filter(id => id)
                : glossaries;
        } else {
            // Tableau vide = pas de glossaire
            options.glossaries = [];
        }

        // Nettoyer le HTML avant envoi
        const cleanedText = cleanHtmlForLara(text);

        // Effectuer la traduction
        console.log('Traduction de texte avec source:', normalizedSource, 'target:', normalizedTarget, 'et options:', options);
        console.log('📝 Texte source envoyé:', cleanedText);
        const result = await lara.translate(cleanedText, normalizedSource, normalizedTarget, options);

        // Logger la réponse complète pour debug
        console.log('Résultat de la traduction:', JSON.stringify(result, null, 2));

        // Préparer la réponse avec le module qualité si disponible
        const response = {
            translation: result.translation || result.text,
            sourceLanguage: result.sourceLanguage || source,
            targetLanguage: target,
            contentType: result.contentType
        };

        // Ajouter les métadonnées si disponibles (mode verbose)
        if (result.metadata) {
            response.metadata = result.metadata;
            console.log('Métadonnées trouvées:', result.metadata);

            // Le feedback qualité peut être dans les métadonnées
            if (result.metadata.quality || result.metadata.qualityFeedback || result.metadata.quality_feedback) {
                response.quality_feedback = result.metadata.quality || result.metadata.qualityFeedback || result.metadata.quality_feedback;
                console.log('Feedback qualité trouvé dans metadata:', response.quality_feedback);
            }
        }

        // Ajouter le feedback qualité si disponible au niveau racine
        if (result.quality_feedback || result.feedback || result.quality || result.qualityFeedback) {
            response.quality_feedback = result.quality_feedback || result.feedback || result.quality || result.qualityFeedback;
            console.log('Feedback qualité trouvé:', response.quality_feedback);
        }

        if (!response.quality_feedback) {
            console.log('Aucun feedback qualité dans la réponse - Objet complet:', Object.keys(result));
        }

        res.json(response);

    } catch (error) {
        console.error('Erreur lors de la traduction de texte:', error);
        res.status(500).json({
            error: error.message || 'Erreur lors de la traduction',
            details: error.toString()
        });
    }
});

// Traduction de document avec Lara
app.post('/api/lara/translate-document', upload.single('file'), async (req, res) => {
    let uploadedFilePath = null;

    try {
        const {
            accessKeyId,
            accessKeySecret,
            source,
            target,
            domain,
            style,
            adaptTo,
            glossaries,
            outputFormat
        } = req.body;

        // Validation
        if (!accessKeyId || !accessKeySecret) {
            return res.status(400).json({
                error: 'access_key_id et access_key_secret sont requis'
            });
        }

        if (!req.file) {
            return res.status(400).json({
                error: 'Aucun fichier fourni'
            });
        }

        if (!target) {
            return res.status(400).json({
                error: 'target est requis'
            });
        }

        uploadedFilePath = req.file.path;
        const filename = req.file.originalname;

        // Créer le client Lara
        const lara = createLaraClient(accessKeyId, accessKeySecret);

        // Normaliser les codes de langue
        const normalizedTarget = normalizeLanguageCode(target);
        const normalizedSource = source ? normalizeLanguageCode(source) : undefined;

        // Préparer les options
        const options = {};

        if (normalizedSource) options.source = normalizedSource;
        if (domain) options.domain = domain;
        if (style) options.style = style;
        if (outputFormat) options.outputFormat = outputFormat;

        // Convertir les chaînes d'IDs en tableaux
        // Si adaptTo est fourni, l'utiliser ; sinon envoyer un tableau vide pour désactiver les mémoires par défaut
        if (adaptTo) {
            options.adaptTo = typeof adaptTo === 'string'
                ? adaptTo.split(',').map(id => id.trim()).filter(id => id)
                : JSON.parse(adaptTo);
        } else {
            // Tableau vide = pas de mémoire (évite que Lara utilise toutes les mémoires du compte)
            options.adaptTo = [];
        }

        if (glossaries) {
            options.glossaries = typeof glossaries === 'string'
                ? glossaries.split(',').map(id => id.trim()).filter(id => id)
                : JSON.parse(glossaries);
        } else {
            // Tableau vide = pas de glossaire
            options.glossaries = [];
        }

        console.log('Traduction de document:', filename, 'target:', normalizedTarget, 'avec options:', options);

        // Utiliser la méthode upload avec les langues source et cible (selon la doc officielle)
        const uploadResult = await lara.documents.upload(uploadedFilePath, filename, normalizedSource, normalizedTarget, options);
        console.log('Document uploadé et traduction lancée:', uploadResult);

        // Étape 2: Attendre que la traduction soit terminée (polling)
        let status = uploadResult;
        let attempts = 0;
        const maxAttempts = 60; // 60 tentatives = 5 minutes max

        while (status.status !== 'translated' && status.status !== 'error' && attempts < maxAttempts) {
            await new Promise(resolve => setTimeout(resolve, 5000)); // Attendre 5 secondes
            status = await lara.documents.status(uploadResult.id);
            console.log(`Statut (tentative ${attempts + 1}):`, status.status);
            attempts++;
        }

        // Préparer la réponse
        const response = {
            id: uploadResult.id,
            status: status.status,
            filename: filename,
            source_language: source,
            target_language: target,
            created_at: status.createdAt || new Date().toISOString(),
            updated_at: status.updatedAt || new Date().toISOString()
        };

        // Si la traduction est terminée, récupérer le fichier traduit
        console.log('Statut final de la traduction:', status.status);
        if (status.status === 'translated') {
            try {
                console.log('Téléchargement du fichier traduit pour le document:', uploadResult.id);
                // Télécharger le fichier traduit
                const translatedBuffer = await lara.documents.download(uploadResult.id);
                console.log('Fichier téléchargé, taille:', translatedBuffer.length, 'octets');

                // Sauvegarder temporairement le fichier traduit
                const translatedFilename = `translated_${filename}`;
                const translatedPath = path.join('uploads', translatedFilename);
                await fs.writeFile(translatedPath, translatedBuffer);
                console.log('Fichier sauvegardé:', translatedPath);

                // Créer une URL de téléchargement (encoder le nom de fichier pour gérer les espaces)
                response.translated_file = `/api/lara/download-file/${encodeURIComponent(translatedFilename)}`;
                response.message = 'Traduction terminée avec succès';
                console.log('URL de téléchargement générée:', response.translated_file);
            } catch (downloadError) {
                console.error('Erreur lors du téléchargement du fichier traduit:', downloadError);
                console.error('Stack:', downloadError.stack);
                response.warning = 'Document traduit mais erreur lors du téléchargement';
                response.error_details = downloadError.message;
            }
        } else if (status.status === 'error') {
            response.error = 'Erreur lors de la traduction du document';
        } else {
            response.warning = 'La traduction prend plus de temps que prévu. Vérifiez le statut plus tard.';
        }

        console.log('Réponse finale envoyée:', JSON.stringify(response, null, 2));

        res.json(response);

    } catch (error) {
        console.error('Erreur lors de la traduction de document:', error);
        res.status(500).json({
            error: error.message || 'Erreur lors de la traduction du document',
            details: error.toString()
        });
    } finally {
        // Nettoyer le fichier uploadé
        if (uploadedFilePath) {
            try {
                await fs.unlink(uploadedFilePath);
            } catch (cleanupError) {
                console.error('Erreur lors du nettoyage du fichier:', cleanupError);
            }
        }
    }
});

// Route pour télécharger un fichier traduit
app.get('/api/lara/download-file/:filename', async (req, res) => {
    try {
        const { filename } = req.params;
        const filePath = path.join('uploads', filename);

        // Vérifier que le fichier existe
        try {
            await fs.access(filePath);
        } catch {
            return res.status(404).json({ error: 'Fichier non trouvé' });
        }

        // Envoyer le fichier
        res.download(filePath, filename, async (err) => {
            if (err) {
                console.error('Erreur lors du téléchargement:', err);
            }
            // Optionnel: Supprimer le fichier après téléchargement
            // try {
            //     await fs.unlink(filePath);
            // } catch (cleanupError) {
            //     console.error('Erreur lors du nettoyage:', cleanupError);
            // }
        });

    } catch (error) {
        console.error('Erreur lors du téléchargement du fichier:', error);
        res.status(500).json({
            error: error.message || 'Erreur lors du téléchargement',
            details: error.toString()
        });
    }
});

// Vérifier le statut d'un document (si nécessaire pour polling)
app.get('/api/lara/document-status/:documentId', async (req, res) => {
    try {
        const { documentId } = req.params;
        const { accessKeyId, accessKeySecret } = req.query;

        if (!accessKeyId || !accessKeySecret) {
            return res.status(400).json({
                error: 'access_key_id et access_key_secret sont requis'
            });
        }

        const lara = createLaraClient(accessKeyId, accessKeySecret);

        // Vérifier le statut
        const status = await lara.documents.status(documentId);

        res.json(status);

    } catch (error) {
        console.error('Erreur lors de la vérification du statut:', error);
        res.status(500).json({
            error: error.message || 'Erreur lors de la vérification du statut',
            details: error.toString()
        });
    }
});

// Télécharger un document traduit
app.get('/api/lara/download/:documentId', async (req, res) => {
    try {
        const { documentId } = req.params;
        const { accessKeyId, accessKeySecret, outputFormat } = req.query;

        if (!accessKeyId || !accessKeySecret) {
            return res.status(400).json({
                error: 'access_key_id et access_key_secret sont requis'
            });
        }

        const lara = createLaraClient(accessKeyId, accessKeySecret);

        // Télécharger le document
        const options = {};
        if (outputFormat) options.outputFormat = outputFormat;

        const result = await lara.documents.download(documentId, options);

        // Le résultat peut être un buffer ou des métadonnées
        if (Buffer.isBuffer(result)) {
            res.setHeader('Content-Type', 'application/octet-stream');
            res.setHeader('Content-Disposition', `attachment; filename="translated_${documentId}"`);
            res.send(result);
        } else {
            res.json(result);
        }

    } catch (error) {
        console.error('Erreur lors du téléchargement:', error);
        res.status(500).json({
            error: error.message || 'Erreur lors du téléchargement',
            details: error.toString()
        });
    }
});

// Route pour récupérer la liste des mémoires de traduction
app.get('/api/lara/memories', async (req, res) => {
    try {
        const { accessKeyId, accessKeySecret } = req.query;

        if (!accessKeyId || !accessKeySecret) {
            return res.status(400).json({
                error: 'access_key_id et access_key_secret sont requis'
            });
        }

        const lara = createLaraClient(accessKeyId, accessKeySecret);
        const memories = await lara.memories.list();

        res.json(memories);

    } catch (error) {
        console.error('Erreur lors de la récupération des mémoires:', error);
        res.status(500).json({
            error: error.message || 'Erreur lors de la récupération des mémoires',
            details: error.toString()
        });
    }
});

// Route pour récupérer la liste des glossaires disponibles
app.get('/api/lara/glossaries', async (req, res) => {
    try {
        const { accessKeyId, accessKeySecret } = req.query;

        if (!accessKeyId || !accessKeySecret) {
            return res.status(400).json({
                error: 'access_key_id et access_key_secret sont requis'
            });
        }

        const lara = createLaraClient(accessKeyId, accessKeySecret);
        const glossaries = await lara.glossaries.list();

        res.json(glossaries);

    } catch (error) {
        console.error('Erreur lors de la récupération des glossaires:', error);
        res.status(500).json({
            error: error.message || 'Erreur lors de la récupération des glossaires',
            details: error.toString()
        });
    }
});

// Route pour récupérer tous les templates
app.get('/api/templates', async (req, res) => {
    try {
        const templatesPath = path.join(__dirname, 'templates.xml');
        const xmlContent = await fs.readFile(templatesPath, 'utf-8');

        const parser = new xml2js.Parser({ explicitArray: false });
        const result = await parser.parseStringPromise(xmlContent);

        // Convertir les templates en tableau
        let templates = result['translation-templates'].template;
        if (!Array.isArray(templates)) {
            templates = [templates];
        }

        // Transformer les templates pour un format plus utilisable
        const formattedTemplates = templates.map(template => ({
            id: template.$.id,
            name: template.$.name,
            isDefault: template.$['is-default'] === 'true',
            domain: template.domain,
            sourceLanguage: template['source-language'],
            targetLanguage: template['target-language'],
            translationMemoryId: template['translation-memory-id'] || '',
            translationMemoryName: template['translation-memory-name'] || (template['translation-memory'] || ''),
            glossaryId: template['glossary-id'] || '',
            glossaryName: template['glossary-name'] || (template.glossary || ''),
            description: template.description
        }));

        res.json(formattedTemplates);

    } catch (error) {
        console.error('Erreur lors de la lecture des templates:', error);
        res.status(500).json({
            error: error.message || 'Erreur lors de la lecture des templates',
            details: error.toString()
        });
    }
});

// Route pour récupérer un template spécifique par combinaison
app.get('/api/templates/find', async (req, res) => {
    try {
        const { domain, sourceLanguage, targetLanguage } = req.query;
        console.log('🔍 Recherche template avec:', { domain, sourceLanguage, targetLanguage });

        // Seule targetLanguage est obligatoire
        if (!targetLanguage) {
            return res.status(400).json({
                error: 'targetLanguage est requis'
            });
        }

        const templatesPath = path.join(__dirname, 'templates.xml');
        const xmlContent = await fs.readFile(templatesPath, 'utf-8');

        const parser = new xml2js.Parser({ explicitArray: false });
        const result = await parser.parseStringPromise(xmlContent);

        let templates = result['translation-templates'].template;
        if (!Array.isArray(templates)) {
            templates = [templates];
        }

        // Chercher tous les templates correspondants (comparaison insensible à la casse pour les langues)
        // Ignorer le template par défaut dans la recherche initiale
        const matchingTemplates = templates.filter(template => {
            // Ignorer le template par défaut
            if (template.$['is-default'] === 'true') return false;

            // Comparaison insensible à la casse pour le domaine
            const domainMatch = !domain ||
                (template.domain && template.domain.toLowerCase() === domain.toLowerCase()) ||
                template.domain === '*';
            const sourceLangMatch = !sourceLanguage ||
                template['source-language'].toUpperCase() === sourceLanguage.toUpperCase() ||
                template['source-language'] === '*';
            const targetLangMatch = template['target-language'].toUpperCase() === targetLanguage.toUpperCase() ||
                template['target-language'] === '*';

            return domainMatch && sourceLangMatch && targetLangMatch;
        });

        // Trier les templates : les matchs exacts en premier, puis les wildcards
        matchingTemplates.sort((a, b) => {
            const aExact = (domain && a.domain === domain ? 1 : 0) +
                (sourceLanguage && a['source-language'].toUpperCase() === sourceLanguage.toUpperCase() ? 1 : 0) +
                (a['target-language'].toUpperCase() === targetLanguage.toUpperCase() ? 1 : 0);
            const bExact = (domain && b.domain === domain ? 1 : 0) +
                (sourceLanguage && b['source-language'].toUpperCase() === sourceLanguage.toUpperCase() ? 1 : 0) +
                (b['target-language'].toUpperCase() === targetLanguage.toUpperCase() ? 1 : 0);
            return bExact - aExact; // Trier par nombre de matchs exacts décroissant
        });

        // N'ajouter le template par défaut que s'il n'y a pas d'autres templates correspondants
        const defaultTemplate = templates.find(t => t.$['is-default'] === 'true');

        let resultTemplates = [...matchingTemplates];

        // Ajouter le template par défaut uniquement si aucun autre template ne correspond
        if (resultTemplates.length === 0 && defaultTemplate) {
            resultTemplates.push(defaultTemplate);
        }

        if (resultTemplates.length === 0 && defaultTemplate) {
            resultTemplates.push(defaultTemplate);
        }

        const formattedTemplates = resultTemplates.map(template => ({
            id: template.$.id,
            name: template.$.name,
            isDefault: template.$['is-default'] === 'true',
            domain: template.domain,
            sourceLanguage: template['source-language'],
            targetLanguage: template['target-language'],
            translationMemoryId: template['translation-memory-id'] || '',
            translationMemoryName: template['translation-memory-name'] || template['translation-memory'] || '',
            glossaryId: template['glossary-id'] || '',
            glossaryName: template['glossary-name'] || template.glossary || '',
            description: template.description
        }));

        console.log('📋 Templates trouvés:', formattedTemplates.map(t => ({
            id: t.id,
            name: t.name,
            translationMemoryId: t.translationMemoryId,
            glossaryId: t.glossaryId
        })));

        res.json(formattedTemplates);

    } catch (error) {
        console.error('Erreur lors de la recherche de template:', error);
        res.status(500).json({
            error: error.message || 'Erreur lors de la recherche de template',
            details: error.toString()
        });
    }
});

// Route pour mettre à jour un template
app.put('/api/templates/:id', async (req, res) => {
    try {
        const { id } = req.params;
        const {
            name,
            domain,
            sourceLanguage,
            targetLanguage,
            translationMemory,
            glossary,
            description
        } = req.body;

        const templatesPath = path.join(__dirname, 'templates.xml');
        const xmlContent = await fs.readFile(templatesPath, 'utf-8');

        const parser = new xml2js.Parser({ explicitArray: false });
        const result = await parser.parseStringPromise(xmlContent);

        let templates = result['translation-templates'].template;
        if (!Array.isArray(templates)) {
            templates = [templates];
        }

        // Trouver et mettre à jour le template
        const templateIndex = templates.findIndex(t => t.$.id === id);
        if (templateIndex === -1) {
            return res.status(404).json({ error: 'Template non trouvé' });
        }

        if (name) templates[templateIndex].$.name = name;
        if (domain) templates[templateIndex].domain = domain;
        if (sourceLanguage) templates[templateIndex]['source-language'] = sourceLanguage;
        if (targetLanguage) templates[templateIndex]['target-language'] = targetLanguage;
        if (translationMemory !== undefined) templates[templateIndex]['translation-memory'] = translationMemory;
        if (glossary !== undefined) templates[templateIndex].glossary = glossary;
        if (description) templates[templateIndex].description = description;

        result['translation-templates'].template = templates;

        // Reconstruire le XML
        const builder = new xml2js.Builder({
            xmldec: { version: '1.0', encoding: 'UTF-8' },
            renderOpts: { pretty: true, indent: '  ' }
        });
        const updatedXml = builder.buildObject(result);

        // Sauvegarder le fichier
        await fs.writeFile(templatesPath, updatedXml, 'utf-8');

        res.json({
            message: 'Template mis à jour avec succès',
            template: templates[templateIndex]
        });

    } catch (error) {
        console.error('Erreur lors de la mise à jour du template:', error);
        res.status(500).json({
            error: error.message || 'Erreur lors de la mise à jour du template',
            details: error.toString()
        });
    }
});

// Route pour créer un nouveau template
app.post('/api/templates', async (req, res) => {
    try {
        const {
            id,
            name,
            domain,
            sourceLanguage,
            targetLanguage,
            translationMemory,
            glossary,
            description
        } = req.body;

        if (!id || !name || !domain || !targetLanguage) {
            return res.status(400).json({
                error: 'id, name, domain et targetLanguage sont requis'
            });
        }

        const templatesPath = path.join(__dirname, 'templates.xml');
        const xmlContent = await fs.readFile(templatesPath, 'utf-8');

        const parser = new xml2js.Parser({ explicitArray: false });
        const result = await parser.parseStringPromise(xmlContent);

        let templates = result['translation-templates'].template;
        if (!Array.isArray(templates)) {
            templates = [templates];
        }

        // Vérifier que l'ID n'existe pas déjà
        if (templates.find(t => t.$.id === id)) {
            return res.status(400).json({ error: 'Un template avec cet ID existe déjà' });
        }

        // Créer le nouveau template
        const newTemplate = {
            $: {
                id: id,
                name: name
            },
            domain: domain,
            'source-language': sourceLanguage || '*',
            'target-language': targetLanguage,
            'translation-memory': translationMemory || '',
            glossary: glossary || '',
            description: description || ''
        };

        templates.push(newTemplate);
        result['translation-templates'].template = templates;

        // Reconstruire le XML
        const builder = new xml2js.Builder({
            xmldec: { version: '1.0', encoding: 'UTF-8' },
            renderOpts: { pretty: true, indent: '  ' }
        });
        const updatedXml = builder.buildObject(result);

        // Sauvegarder le fichier
        await fs.writeFile(templatesPath, updatedXml, 'utf-8');

        res.json({
            message: 'Template créé avec succès',
            template: newTemplate
        });

    } catch (error) {
        console.error('Erreur lors de la création du template:', error);
        res.status(500).json({
            error: error.message || 'Erreur lors de la création du template',
            details: error.toString()
        });
    }
});

// Route pour récupérer tous les domaines (visualisation domaines.xml)
app.get('/api/lara/domaines', async (req, res) => {
    try {
        const domainesPath = path.join(__dirname, 'domaines.xml');
        // Vérifier si le fichier existe
        try {
            await fs.access(domainesPath);
        } catch {
            return res.status(404).json({ error: 'Fichier domaines.xml non trouvé' });
        }

        const xmlContent = await fs.readFile(domainesPath, 'utf-8');

        const parser = new xml2js.Parser({ explicitArray: false });
        const result = await parser.parseStringPromise(xmlContent);

        let domaines = result.domaines.domaine;
        if (!domaines) {
            domaines = [];
        } else if (!Array.isArray(domaines)) {
            domaines = [domaines];
        }

        // Formater pour le client
        const formattedDomaines = domaines.map(d => ({
            name: d.$.name,
            proches: d.proche ? (Array.isArray(d.proche) ? d.proche : [d.proche]) : []
        }));

        res.json(formattedDomaines);
    } catch (error) {
        console.error('Erreur lors de la lecture des domaines:', error);
        res.status(500).json({
            error: error.message || 'Erreur lors de la lecture des domaines',
            details: error.toString()
        });
    }
});

// Route pour récupérer tous les glossaires (visualisation lara-glossaries.xml)
app.get('/api/lara/glossaries-list', async (req, res) => {
    try {
        const glossariesPath = path.join(__dirname, 'lara-glossaries.xml');
        try {
            await fs.access(glossariesPath);
        } catch {
            return res.status(404).json({ error: 'Fichier lara-glossaries.xml non trouvé' });
        }

        const xmlContent = await fs.readFile(glossariesPath, 'utf-8');
        const parser = new xml2js.Parser({ explicitArray: false });
        const result = await parser.parseStringPromise(xmlContent);

        let glossaries = result.glossaries.glossary;
        if (!glossaries) {
            glossaries = [];
        } else if (!Array.isArray(glossaries)) {
            glossaries = [glossaries];
        }

        res.json(glossaries);
    } catch (error) {
        console.error('Erreur lors de la lecture des glossaires:', error);
        res.status(500).json({
            error: error.message || 'Erreur lors de la lecture des glossaires',
            details: error.toString()
        });
    }
});

// Route pour récupérer toutes les mémoires (visualisation lara-memories.xml)
app.get('/api/lara/memories-list', async (req, res) => {
    try {
        const memoriesPath = path.join(__dirname, 'lara-memories.xml');
        try {
            await fs.access(memoriesPath);
        } catch {
            return res.status(404).json({ error: 'Fichier lara-memories.xml non trouvé' });
        }

        const xmlContent = await fs.readFile(memoriesPath, 'utf-8');
        const parser = new xml2js.Parser({ explicitArray: false });
        const result = await parser.parseStringPromise(xmlContent);

        let memories = result.memories.memory;
        if (!memories) {
            memories = [];
        } else if (!Array.isArray(memories)) {
            memories = [memories];
        }

        res.json(memories);
    } catch (error) {
        console.error('Erreur lors de la lecture des mémoires:', error);
        res.status(500).json({
            error: error.message || 'Erreur lors de la lecture des mémoires',
            details: error.toString()
        });
    }
});

// Route pour récupérer toutes les ressources (visualisation lara-resources.json)
app.get('/api/lara/resources-list', async (req, res) => {
    try {
        const resourcesPath = path.join(__dirname, 'lara-resources.json');
        try {
            await fs.access(resourcesPath);
        } catch {
            return res.status(404).json({ error: 'Fichier lara-resources.json non trouvé' });
        }

        const jsonContent = await fs.readFile(resourcesPath, 'utf-8');
        const resources = JSON.parse(jsonContent);

        res.json(resources);
    } catch (error) {
        console.error('Erreur lors de la lecture des ressources:', error);
        res.status(500).json({
            error: error.message || 'Erreur lors de la lecture des ressources',
            details: error.toString()
        });
    }
});

// Alias /api/lara/templates - Liste tous les templates
app.get('/api/lara/templates', async (req, res) => {
    try {
        const templatesPath = path.join(__dirname, 'templates.xml');
        const xmlContent = await fs.readFile(templatesPath, 'utf-8');
        const parser = new xml2js.Parser({ explicitArray: false });
        const result = await parser.parseStringPromise(xmlContent);
        let templates = result['translation-templates'].template;
        if (!Array.isArray(templates)) templates = [templates];
        const formattedTemplates = templates.map(template => ({
            id: template.$.id,
            name: template.$.name,
            isDefault: template.$['is-default'] === 'true',
            domain: template.domain,
            sourceLanguage: template['source-language'],
            targetLanguage: template['target-language'],
            translationMemoryId: template['translation-memory-id'] || '',
            translationMemoryName: template['translation-memory-name'] || template['translation-memory'] || '',
            glossaryId: template['glossary-id'] || '',
            glossaryName: template['glossary-name'] || template.glossary || '',
            description: template.description
        }));
        res.json(formattedTemplates);
    } catch (error) {
        console.error('Erreur /api/lara/templates:', error);
        res.status(500).json({ error: error.message });
    }
});

// Alias /api/lara/templates/find - Recherche de templates
app.get('/api/lara/templates/find', async (req, res) => {
    try {
        const { domain, sourceLanguage, targetLanguage } = req.query;
        console.log('🔍 [LARA] Recherche template avec:', { domain, sourceLanguage, targetLanguage });
        if (!targetLanguage) {
            return res.status(400).json({ error: 'targetLanguage est requis' });
        }
        const templatesPath = path.join(__dirname, 'templates.xml');
        const xmlContent = await fs.readFile(templatesPath, 'utf-8');
        const parser = new xml2js.Parser({ explicitArray: false });
        const result = await parser.parseStringPromise(xmlContent);
        let templates = result['translation-templates'].template;
        if (!Array.isArray(templates)) templates = [templates];

        const matchingTemplates = templates.filter(template => {
            if (template.$['is-default'] === 'true') return false;
            const domainMatch = !domain || (template.domain && template.domain.toLowerCase() === domain.toLowerCase()) || template.domain === '*';
            const sourceLangMatch = !sourceLanguage || template['source-language'].toUpperCase() === sourceLanguage.toUpperCase() || template['source-language'] === '*';
            const targetLangMatch = template['target-language'].toUpperCase() === targetLanguage.toUpperCase() || template['target-language'] === '*';
            return domainMatch && sourceLangMatch && targetLangMatch;
        });

        matchingTemplates.sort((a, b) => {
            const aExact = (domain && a.domain === domain ? 1 : 0) + (sourceLanguage && a['source-language'].toUpperCase() === sourceLanguage.toUpperCase() ? 1 : 0) + (a['target-language'].toUpperCase() === targetLanguage.toUpperCase() ? 1 : 0);
            const bExact = (domain && b.domain === domain ? 1 : 0) + (sourceLanguage && b['source-language'].toUpperCase() === sourceLanguage.toUpperCase() ? 1 : 0) + (b['target-language'].toUpperCase() === targetLanguage.toUpperCase() ? 1 : 0);
            return bExact - aExact;
        });

        const defaultTemplate = templates.find(t => t.$['is-default'] === 'true');
        let resultTemplates = [...matchingTemplates];
        if (resultTemplates.length === 0 && defaultTemplate) {
            resultTemplates.push(defaultTemplate);
        }

        const formattedTemplates = resultTemplates.map(template => ({
            id: template.$.id,
            name: template.$.name,
            isDefault: template.$['is-default'] === 'true',
            domain: template.domain,
            sourceLanguage: template['source-language'],
            targetLanguage: template['target-language'],
            translationMemoryId: template['translation-memory-id'] || '',
            translationMemoryName: template['translation-memory-name'] || template['translation-memory'] || '',
            glossaryId: template['glossary-id'] || '',
            glossaryName: template['glossary-name'] || template.glossary || '',
            description: template.description
        }));

        console.log('📋 [LARA] Templates trouvés:', formattedTemplates.map(t => ({
            id: t.id,
            name: t.name,
            translationMemoryId: t.translationMemoryId,
            glossaryId: t.glossaryId
        })));

        res.json(formattedTemplates);
    } catch (error) {
        console.error('Erreur /api/lara/templates/find:', error);
        res.status(500).json({ error: error.message });
    }
});

// Gestion des erreurs globales
app.use((error, req, res, next) => {
    console.error('Erreur non gérée:', error);
    res.status(500).json({
        error: 'Erreur serveur interne',
        details: error.message
    });
});

// Démarrage du serveur
app.listen(PORT, () => {
    console.log(`✅ Serveur Lara Translation démarré sur le port ${PORT}`);
    console.log(`🔗 Health check: http://localhost:${PORT}/health`);
});

// Gestion de l'arrêt gracieux
process.on('SIGTERM', () => {
    console.log('SIGTERM reçu, arrêt du serveur...');
    process.exit(0);
});

process.on('SIGINT', () => {
    console.log('SIGINT reçu, arrêt du serveur...');
    process.exit(0);
});
