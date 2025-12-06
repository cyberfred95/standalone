# Documentation API - Lara Translation Server

## Vue d'ensemble

Ce serveur Node.js/Express agit comme un proxy/middleware entre votre application frontend et l'API LaraTranslate (Translated.com), en ajoutant des fonctionnalités supplémentaires comme la gestion des templates de traduction.

## Fichiers de documentation

| Fichier | Description |
|---------|-------------|
| `swagger.yaml` | Spécification OpenAPI 3.0 complète |
| `api-docs.html` | Interface Swagger UI interactive |

## Consulter la documentation

### Option 1 : Swagger UI (recommandé)

1. Démarrez un serveur HTTP dans le dossier `doc` :
   ```bash
   cd doc
   npx serve .
   ```
   Ou avec Python :
   ```bash
   cd doc
   python -m http.server 8080
   ```

2. Ouvrez `http://localhost:8080/api-docs.html` dans votre navigateur

### Option 2 : Importer dans Postman/Insomnia

Importez directement le fichier `swagger.yaml` dans votre client API favori.

### Option 3 : Swagger Editor en ligne

1. Allez sur [editor.swagger.io](https://editor.swagger.io)
2. File > Import file > Sélectionnez `swagger.yaml`

---

## Résumé des Endpoints

### Health Check

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/health` | Vérifier l'état du serveur |

### Traduction

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| POST | `/api/lara/translate-text` | Traduire un texte |
| POST | `/api/lara/translate-document` | Traduire un document |

### Documents

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/api/lara/download-file/:filename` | Télécharger un fichier traduit |
| GET | `/api/lara/document-status/:documentId` | Vérifier le statut d'un document |
| GET | `/api/lara/download/:documentId` | Télécharger par ID |

### Ressources Lara

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/api/lara/memories` | Lister les mémoires de traduction |
| GET | `/api/lara/glossaries` | Lister les glossaires |

### Templates

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/api/templates` | Lister tous les templates |
| POST | `/api/templates` | Créer un template |
| GET | `/api/templates/find` | Rechercher des templates |
| PUT | `/api/templates/:id` | Modifier un template |

---

## Authentification

Toutes les routes `/api/lara/*` nécessitent les credentials LaraTranslate :

- **accessKeyId** : Votre Access Key ID
- **accessKeySecret** : Votre Access Key Secret

### Pour les requêtes POST
```json
{
  "accessKeyId": "votre_access_key_id",
  "accessKeySecret": "votre_access_key_secret",
  "text": "Texte à traduire",
  "target": "en"
}
```

### Pour les requêtes GET
```
GET /api/lara/memories?accessKeyId=xxx&accessKeySecret=xxx
```

---

## Exemples d'utilisation

### Traduction de texte simple

```bash
curl -X POST http://localhost:3000/api/lara/translate-text \
  -H "Content-Type: application/json" \
  -d '{
    "accessKeyId": "votre_access_key_id",
    "accessKeySecret": "votre_access_key_secret",
    "text": "Bonjour, comment allez-vous ?",
    "source": "fr",
    "target": "en"
  }'
```

**Réponse :**
```json
{
  "translation": "Hello, how are you?",
  "sourceLanguage": "fr-FR",
  "targetLanguage": "en",
  "contentType": "text/plain"
}
```

### Traduction avec options avancées

```bash
curl -X POST http://localhost:3000/api/lara/translate-text \
  -H "Content-Type: application/json" \
  -d '{
    "accessKeyId": "votre_access_key_id",
    "accessKeySecret": "votre_access_key_secret",
    "text": "Le contrat de bail est signé par les deux parties.",
    "source": "fr",
    "target": "en",
    "domain": "Legal",
    "style": "faithful",
    "instructions": "Utilisez un ton formel et juridique",
    "adaptTo": "123,456",
    "glossaries": "789"
  }'
```

### Traduction de document

```bash
curl -X POST http://localhost:3000/api/lara/translate-document \
  -F "accessKeyId=votre_access_key_id" \
  -F "accessKeySecret=votre_access_key_secret" \
  -F "file=@/chemin/vers/document.docx" \
  -F "source=fr" \
  -F "target=en" \
  -F "domain=Legal"
```

**Réponse :**
```json
{
  "id": "doc_123456",
  "status": "translated",
  "filename": "document.docx",
  "source_language": "fr",
  "target_language": "en",
  "translated_file": "/api/lara/download-file/translated_document.docx",
  "message": "Traduction terminée avec succès"
}
```

### Recherche de templates

```bash
curl "http://localhost:3000/api/templates/find?domain=Legal&sourceLanguage=fr&targetLanguage=en"
```

**Réponse :**
```json
[
  {
    "id": "legal-fr-en",
    "name": "Juridique FR vers EN",
    "isDefault": false,
    "domain": "Legal",
    "sourceLanguage": "fr",
    "targetLanguage": "en",
    "translationMemoryId": "mem_123",
    "translationMemoryName": "Mémoire Juridique",
    "glossaryId": "glos_456",
    "glossaryName": "Glossaire Juridique"
  }
]
```

### Création d'un template

```bash
curl -X POST http://localhost:3000/api/templates \
  -H "Content-Type: application/json" \
  -d '{
    "id": "accounting-fr-de",
    "name": "Comptabilité FR vers DE",
    "domain": "Accounting",
    "sourceLanguage": "fr",
    "targetLanguage": "de",
    "translationMemory": "mem_789",
    "glossary": "glos_101",
    "description": "Template pour les documents comptables"
  }'
```

---

## Codes de langue supportés

Les codes courts sont automatiquement convertis :

| Code court | Code complet |
|------------|--------------|
| `fr` | `fr-FR` |
| `en` | `en-US` |
| `es` | `es-ES` |
| `de` | `de-DE` |
| `it` | `it-IT` |
| `pt` | `pt-PT` |
| `nl` | `nl-NL` |
| `pl` | `pl-PL` |
| `ru` | `ru-RU` |
| `ja` | `ja-JP` |
| `zh` | `zh-CN` |
| `ar` | `ar-SA` |

---

## Styles de traduction

| Style | Description |
|-------|-------------|
| `faithful` | Traduction fidèle au texte original |
| `fluid` | Traduction fluide et naturelle |
| `creative` | Traduction créative avec adaptation culturelle |

---

## Codes d'erreur HTTP

| Code | Description |
|------|-------------|
| 200 | Succès |
| 400 | Paramètres manquants ou invalides |
| 404 | Ressource non trouvée |
| 500 | Erreur serveur interne |

---

## Format des erreurs

```json
{
  "error": "Message d'erreur lisible",
  "details": "Détails techniques (stack trace en développement)"
}
```

---

## Notes techniques

### Formats de fichiers supportés

- PDF (.pdf)
- Microsoft Word (.docx, .doc)
- OpenDocument (.odt)
- Texte brut (.txt)
- Rich Text Format (.rtf)

### Limites

- Taille maximale de fichier : 50 MB
- Timeout traduction document : 5 minutes (60 tentatives x 5 secondes)

### Module Qualité

Le module qualité Lara est automatiquement activé pour les traductions de texte.
Le feedback est retourné dans le champ `quality_feedback` de la réponse.
