/**
 * Script de test pour vérifier le retour du module qualité Lara
 * 
 * Usage:
 * 1. Créer un fichier .env avec ACCESS_KEY_ID et ACCESS_KEY_SECRET
 * 2. npm install
 * 3. node test-quality.js
 */

const { Translator, Credentials } = require('@translated/lara');
require('dotenv').config();

async function testQualityFeedback() {
    console.log('🧪 Test du module qualité Lara\n');

    // Vérifier les credentials
    const accessKeyId = process.env.ACCESS_KEY_ID;
    const accessKeySecret = process.env.ACCESS_KEY_SECRET;

    if (!accessKeyId || !accessKeySecret) {
        console.error('❌ Erreur: ACCESS_KEY_ID et ACCESS_KEY_SECRET requis dans .env');
        console.log('\nCréez un fichier .env avec:');
        console.log('ACCESS_KEY_ID=votre_id');
        console.log('ACCESS_KEY_SECRET=votre_secret');
        process.exit(1);
    }

    console.log('✅ Credentials trouvés');
    console.log(`   Access Key ID: ***${accessKeyId.slice(-4)}\n`);

    try {
        // Créer le client Lara
        console.log('📦 Création du client Lara...');
        const credentials = new Credentials(accessKeyId, accessKeySecret);
        const lara = new Translator(credentials);
        console.log('✅ Client créé\n');

        // Test 1: Traduction simple sans qualité
        console.log('📝 Test 1: Traduction SANS module qualité');
        console.log('━'.repeat(50));
        const result1 = await lara.translate(
            'Ceci est un test de traduction professionnelle.',
            'fr-FR',
            'en-US'
        );
        console.log('Résultat complet:');
        console.log(JSON.stringify(result1, null, 2));
        console.log('');

        // Test 2: Traduction avec qualité activée
        console.log('📝 Test 2: Traduction AVEC module qualité (quality: true)');
        console.log('━'.repeat(50));
        const result2 = await lara.translate(
            'Ceci est un test de traduction professionnelle.',
            'fr-FR',
            'en-US',
            {
                quality: true,
                verbose: true
            }
        );
        console.log('Résultat complet:');
        console.log(JSON.stringify(result2, null, 2));
        console.log('');

        // Analyse des résultats
        console.log('🔍 Analyse des propriétés retournées:');
        console.log('━'.repeat(50));
        console.log('Propriétés disponibles:', Object.keys(result2));
        
        // Chercher le feedback dans tous les endroits possibles
        const possiblePaths = [
            'quality_feedback',
            'feedback',
            'quality',
            'qualityFeedback',
            'metadata.quality',
            'metadata.qualityFeedback',
            'metadata.quality_feedback',
            'metadata.feedback'
        ];

        console.log('\n🔎 Recherche du feedback qualité:');
        possiblePaths.forEach(path => {
            const parts = path.split('.');
            let value = result2;
            
            for (const part of parts) {
                value = value?.[part];
            }
            
            const status = value ? '✅ Trouvé' : '❌ Absent';
            console.log(`   ${status} - ${path}:`, value || 'N/A');
        });

        // Test 3: Tester d'autres options
        console.log('\n📝 Test 3: Traduction avec enableQuality (au cas où)');
        console.log('━'.repeat(50));
        try {
            const result3 = await lara.translate(
                'Ceci est un test de traduction professionnelle.',
                'fr-FR',
                'en-US',
                {
                    enableQuality: true,
                    qualityCheck: true
                }
            );
            console.log('Résultat complet:');
            console.log(JSON.stringify(result3, null, 2));
        } catch (error) {
            console.log('⚠️  Options non supportées:', error.message);
        }

        console.log('\n' + '='.repeat(50));
        console.log('✅ Tests terminés !');
        console.log('='.repeat(50));

    } catch (error) {
        console.error('\n❌ Erreur lors du test:', error);
        console.error('Détails:', error.message);
        process.exit(1);
    }
}

// Exécuter le test
testQualityFeedback().catch(console.error);
