# Interface de Traduction Lexa / Lara

Application web de traduction professionnelle supportant deux services :
- **Lexa (Lexamt)** : Traduction juridique professionnelle
- **Lara (LaraTranslate)** : Traduction IA adaptative avec mémoires de traduction

## 📋 Architecture

```
├── lexa_standalone.html    # Interface utilisateur
├── styles.css              # Styles CSS
├── app.js                  # Logique JavaScript client
├── nginx.conf              # Configuration Nginx
├── docker-compose.yml      # Orchestration Docker
└── server/
    ├── server.js           # Serveur Node.js + SDK Lara
    ├── package.json        # Dépendances Node.js
    ├── Dockerfile          # Image Docker du serveur
    └── .env.example        # Variables d'environnement
```

### Flux de données

```
┌──────────────┐         ┌─────────┐         ┌──────────────┐
│   Navigateur │ ◄────► │  Nginx  │ ◄────► │  Serveur     │
│   (HTML/JS)  │         │  :8080  │         │  Node.js     │
└──────────────┘         └─────────┘         │  :3000       │
                                              └──────────────┘
                                                      │
                                              ┌───────┴───────┐
                                              │               │
                                         ┌────▼────┐   ┌─────▼─────┐
                                         │  Lexa   │   │   Lara    │
                                         │   API   │   │    SDK    │
                                         └─────────┘   └───────────┘
```

## 🚀 Installation et Démarrage

### Option 1 : Avec Docker (Recommandé)

#### Prérequis
- Docker
- Docker Compose

#### Lancement

```bash
# Cloner le projet
cd test_standalone

# Lancer tous les services
docker-compose up -d

# Vérifier les logs
docker-compose logs -f

# Accéder à l'application
# Interface web : http://localhost:8080
# API serveur : http://localhost:3000
```

#### Arrêt

```bash
# Arrêter les services
docker-compose down

# Arrêter et supprimer les volumes
docker-compose down -v
```

### Option 2 : Sans Docker (Développement)

#### Prérequis
- Node.js 18+
- npm

#### Configuration du serveur

```bash
# Aller dans le répertoire serveur
cd server

# Copier le fichier d'environnement
cp .env.example .env

# Installer les dépendances
npm install

# Démarrer le serveur
npm start

# Ou en mode développement avec rechargement automatique
npm run dev
```

Le serveur sera accessible sur `http://localhost:3000`

#### Servir l'interface web

Option A - Serveur HTTP simple :
```bash
# Avec Python
python -m http.server 8080

# Avec Node.js
npx http-server -p 8080
```

Option B - Ouvrir directement le fichier HTML :
```bash
# Ouvrir lexa_standalone.html dans votre navigateur
```

⚠️ **Note** : Si vous ouvrez directement le fichier HTML (protocole `file://`), les appels vers le serveur Node.js ne fonctionneront pas à cause des restrictions CORS. Utilisez un serveur HTTP local.

## ⚙️ Configuration

### 1. Service Lexa (Lexamt)

1. Cliquer sur l'icône ⚙️ en haut à droite
2. Sélectionner "Lexa (Lexamt)" dans le dropdown
3. Entrer votre **Clé API Lexamt**
4. Sauvegarder

**Fonctionnalités Lexa :**
- Choix du domaine de traduction (médical, juridique, technique, commercial)
- Glossaires par défaut et personnels
- Traduction de texte et documents

### 2. Service Lara (LaraTranslate)

1. Cliquer sur l'icône ⚙️ en haut à droite
2. Sélectionner "Lara (LaraTranslate)" dans le dropdown
3. Configurer les paramètres :

   **Authentification (obligatoire) :**
   - **Access Key ID** : Votre ID de clé d'accès Lara
   - **Access Key Secret** : Votre secret de clé d'accès Lara

   **Style de traduction :**
   - **Faithful** (Fidèle) : Traduction littérale et précise [par défaut]
   - **Fluid** (Fluide) : Traduction naturelle et fluide
   - **Creative** (Créatif) : Traduction créative et adaptée

   **Paramètres optionnels :**
   - **Instructions personnalisées** : Ex: "Soyez formel", "Ton professionnel"
   - **IDs de mémoires de traduction** : Ex: `123, 456, 789`
     - Si vide : utilise toutes les mémoires du compte
     - Si rempli : utilise uniquement les mémoires spécifiées
   - **IDs de glossaires** : Ex: `123, 456`

4. Sauvegarder

**Fonctionnalités Lara :**
- Traduction adaptative sans entraînement
- Utilisation des mémoires de traduction
- Module qualité : Retour automatique sur la qualité de la traduction
- Styles de traduction personnalisables
- Traduction de texte et documents

## 📝 Utilisation

### Traduction de texte

1. Rester en "Mode Texte"
2. Sélectionner les langues source et cible
3. (Lexa uniquement) Choisir un domaine et un glossaire optionnel
4. Entrer le texte à traduire
5. Cliquer sur "Traduire"
6. (Lara uniquement) Consulter le feedback qualité si disponible

### Traduction de documents

1. Basculer en "Mode Fichier"
2. Sélectionner les langues source et cible
3. (Lexa uniquement) Choisir un domaine et un glossaire optionnel
4. Glisser-déposer ou cliquer pour sélectionner des fichiers
5. Cliquer sur "Traduire"
6. Télécharger les fichiers traduits

**Formats supportés :** `.pdf`, `.docx`, `.doc`, `.txt`, `.rtf`, `.odt`

## 🔧 API du Serveur Node.js

### Health Check
```bash
GET /health
```

### Traduction de texte (Lara)
```bash
POST /api/lara/translate-text
Content-Type: application/json

{
  "accessKeyId": "votre_access_key_id",
  "accessKeySecret": "votre_access_key_secret",
  "text": "Texte à traduire",
  "source": "fr",
  "target": "en",
  "style": "faithful",
  "instructions": "Soyez formel",
  "adaptTo": "123,456",
  "glossaries": "789"
}
```

**Réponse :**
```json
{
  "translation": "Translated text",
  "sourceLanguage": "fr",
  "targetLanguage": "en",
  "contentType": "text/plain",
  "quality_feedback": "Commentaires sur la qualité..."
}
```

### Traduction de document (Lara)
```bash
POST /api/lara/translate-document
Content-Type: multipart/form-data

file: [fichier]
accessKeyId: votre_access_key_id
accessKeySecret: votre_access_key_secret
source: fr
target: en
style: faithful
adaptTo: 123,456
glossaries: 789
```

**Réponse :**
```json
{
  "id": "doc_12345",
  "status": "translated",
  "filename": "document.pdf",
  "source_language": "fr",
  "target_language": "en",
  "translated_file": "https://...",
  "created_at": "2025-01-20T10:00:00Z",
  "updated_at": "2025-01-20T10:05:00Z"
}
```

## 🔒 Sécurité

### Clés API
- Les clés Lexa et Lara sont stockées dans le **localStorage** du navigateur
- Les clés ne sont **jamais envoyées** au serveur pour Lexa (appel direct à l'API)
- Pour Lara, les clés sont transmises au serveur Node.js uniquement pour l'appel au SDK
- Les clés ne sont **jamais loggées** ni stockées côté serveur

### Fichiers uploadés
- Les fichiers sont stockés temporairement dans `/app/uploads`
- Automatiquement supprimés après traitement
- Taille maximale : **50 MB**

### Headers de sécurité
- CORS activé pour permettre les appels depuis l'interface web
- Timeouts configurés (300s pour les traductions longues)

## 🐛 Dépannage

### Le serveur ne démarre pas
```bash
# Vérifier les logs Docker
docker-compose logs lara-server

# Vérifier que le port 3000 n'est pas déjà utilisé
netstat -an | grep 3000
```

### Erreur CORS
- Assurez-vous d'accéder à l'application via `http://localhost:8080` et non `file://`
- Vérifiez que Nginx est bien démarré : `docker-compose ps`

### Erreur de traduction Lara
- Vérifiez que vos clés API sont correctes
- Consultez les logs du serveur : `docker-compose logs -f lara-server`
- Testez le health check : `curl http://localhost:3000/health`

### SDK Lara non trouvé
```bash
# Reconstruire l'image Docker
docker-compose build --no-cache lara-server
docker-compose up -d
```

## 📦 Structure des données

### Configuration sauvegardée (localStorage)

```javascript
{
  "translationService": "lara",
  "lexa": {
    "apiKey": "xxx",
    "baseUrl": "https://test.portail.lexamt.fr/api/v1"
  },
  "lara": {
    "accessKeyId": "xxx",
    "accessKeySecret": "xxx",
    "baseUrl": "/api/lara",
    "style": "faithful",
    "instructions": "",
    "translationMemoryIds": "123,456",
    "glossaryIds": "789"
  }
}
```

## 📄 Licence

MIT

## 🤝 Support

Pour toute question ou problème :
- Lexa : https://lexamt.com/support
- Lara : https://support.laratranslate.com
- SDK Lara : https://developers.laratranslate.com

## 🔄 Mises à jour

### Mettre à jour les dépendances

```bash
cd server
npm update
```

### Mettre à jour les images Docker

```bash
docker-compose pull
docker-compose up -d --build
```
