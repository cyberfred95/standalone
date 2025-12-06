# Lara Django Backend

Backend Django pour l'application Lara Translation, migré depuis Node.js/Express.

## Architecture

Ce projet utilise:
- **Django 3.2** avec Django REST Framework
- **PostgreSQL** pour la base de données
- **Redis** pour Celery et le cache
- **Docker & Docker Compose** pour l'orchestration
- **Gunicorn** comme serveur WSGI

## Structure du Projet

```
lara-django/
├── config/                 # Configuration Django principale
│   ├── settings.py        # Paramètres Django
│   ├── urls.py            # URLs principales
│   ├── wsgi.py            # Point d'entrée WSGI
│   ├── asgi.py            # Point d'entrée ASGI
│   ├── celery.py          # Configuration Celery
│   └── exceptions.py      # Gestion des exceptions
├── apps/                  # Applications Django
│   ├── domains/           # Gestion des domaines
│   ├── glossaries/        # Gestion des glossaires
│   ├── memories/          # Gestion des mémoires de traduction
│   ├── resources/         # Gestion des ressources
│   ├── templates/         # Gestion des templates
│   └── translation/       # API de traduction
├── manage.py              # Script de gestion Django
├── requirements.txt       # Dépendances Python
├── Dockerfile             # Image Docker
├── docker-compose.yml     # Orchestration Docker
└── .env                   # Variables d'environnement

```

## Applications Django

### 1. **domains**
- Gestion des domaines de traduction (Legal, Medical, etc.)
- Chargement depuis `domaines.xml`
- API: `/api/lara/domaines/`

### 2. **glossaries**
- Gestion des glossaires de traduction
- Chargement depuis `lara-glossaries.xml`
- API: `/api/lara/glossaries-list/`

### 3. **memories**
- Gestion des mémoires de traduction
- Chargement depuis `lara-memories.xml`
- API: `/api/lara/memories-list/`

### 4. **resources**
- Gestion des ressources Lara
- Chargement depuis `lara-resources.json`
- API: `/api/lara/resources-list/`

### 5. **templates**
- Gestion des templates de traduction
- Chargement depuis `templates.xml`
- API: `/api/templates/`

### 6. **translation**
- API de traduction (texte et documents)
- Intégration avec le SDK Lara
- API: `/api/lara/translate-text/`, `/api/lara/translate-document/`

## Installation et Démarrage

### Prérequis
- Docker et Docker Compose
- Fichiers de données XML/JSON du serveur Node.js

### Démarrage avec Docker

1. **Copier les fichiers de données**:
```bash
# Copier les fichiers XML/JSON depuis le serveur Node.js
cp ../domaines.xml ./init_data/
cp ../lara-glossaries.xml ./init_data/
cp ../lara-memories.xml ./init_data/
cp ../lara-resources.json ./init_data/
cp ../templates.xml ./init_data/
```

2. **Configurer les variables d'environnement**:
```bash
cp .env.example .env
# Éditer .env avec vos valeurs
```

3. **Démarrer les services**:
```bash
docker-compose up -d
```

4. **Exécuter les migrations**:
```bash
docker-compose exec django python manage.py migrate
```

5. **Charger les données initiales**:
```bash
docker-compose exec django python manage.py load_domains ../../domaines.xml
docker-compose exec django python manage.py load_glossaries ../../lara-glossaries.xml
docker-compose exec django python manage.py load_memories ../../lara-memories.xml
docker-compose exec django python manage.py load_resources ../../lara-resources.json
docker-compose exec django python manage.py load_templates ../../templates.xml
```

6. **Créer un superutilisateur** (optionnel):
```bash
docker-compose exec django python manage.py createsuperuser
```

### Développement Local (sans Docker)

1. **Créer un environnement virtuel**:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

2. **Installer les dépendances**:
```bash
pip install -r requirements.txt
```

3. **Configurer PostgreSQL et Redis** (doivent être installés localement)

4. **Exécuter les migrations**:
```bash
python manage.py migrate
```

5. **Charger les données**:
```bash
python manage.py load_domains ../domaines.xml
python manage.py load_glossaries ../lara-glossaries.xml
python manage.py load_memories ../lara-memories.xml
python manage.py load_resources ../lara-resources.json
python manage.py load_templates ../templates.xml
```

6. **Démarrer le serveur**:
```bash
python manage.py runserver 8001
```

## Configuration Nginx

Ajouter cette configuration dans `/etc/nginx/sites-available/api.conf`:

```nginx
# API Lara Django (proxy vers le container Django)
location /lara-django/ {
    proxy_pass http://127.0.0.1:8001/;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_cache_bypass $http_upgrade;

    # Timeout pour les traductions longues
    proxy_connect_timeout 300s;
    proxy_send_timeout 300s;
    proxy_read_timeout 300s;

    # Taille maximale des uploads
    client_max_body_size 50M;

    # CORS
    add_header 'Access-Control-Allow-Origin' '*' always;
    add_header 'Access-Control-Allow-Methods' 'GET,POST,DELETE,PUT,OPTIONS' always;
    add_header 'Access-Control-Allow-Headers' 'Content-Type, Authorization' always;

    if ($request_method = 'OPTIONS') {
        add_header 'Access-Control-Allow-Origin' '*';
        add_header 'Access-Control-Allow-Methods' 'GET,POST,DELETE,PUT,OPTIONS';
        add_header 'Access-Control-Allow-Headers' 'Content-Type, Authorization';
        add_header 'Access-Control-Max-Age' 1728000;
        add_header 'Content-Type' 'text/plain; charset=utf-8';
        add_header 'Content-Length' 0;
        return 204;
    }
}
```

Puis recharger Nginx:
```bash
sudo nginx -t
sudo systemctl reload nginx
```

## API Endpoints

Tous les endpoints maintiennent la compatibilité avec le backend Node.js:

### Traduction
- `POST /api/lara/translate-text/` - Traduction de texte
- `POST /api/lara/translate-document/` - Traduction de document
- `GET /api/lara/document-status/:id/` - Statut d'un document
- `GET /api/lara/download/:id/` - Télécharger un document traduit

### Ressources
- `GET /api/lara/domaines/` - Liste des domaines
- `GET /api/lara/glossaries-list/` - Liste des glossaires
- `GET /api/lara/memories-list/` - Liste des mémoires
- `GET /api/lara/resources-list/` - Liste des ressources
- `GET /api/templates/` - Liste des templates
- `GET /api/templates/find/` - Recherche de templates

### Admin
- `GET /health/` - Health check
- `/admin/` - Interface d'administration Django

## Commandes de Gestion

```bash
# Charger les domaines
python manage.py load_domains [path_to_xml]

# Charger les glossaires
python manage.py load_glossaries [path_to_xml]

# Charger les mémoires
python manage.py load_memories [path_to_xml]

# Charger les ressources
python manage.py load_resources [path_to_json]

# Charger les templates
python manage.py load_templates [path_to_xml]

# Charger toutes les données
python manage.py load_all_data
```

## Tests

```bash
# Exécuter tous les tests
python manage.py test

# Exécuter les tests d'une app spécifique
python manage.py test apps.domains

# Avec coverage
coverage run --source='.' manage.py test
coverage report
```

## Logs

Les logs sont disponibles:
- **Console**: `docker-compose logs -f django`
- **Celery**: `docker-compose logs -f celery`
- **PostgreSQL**: `docker-compose logs -f postgres`

## Migration depuis Node.js

Ce backend Django remplace le serveur Node.js (`server/server.js`) avec:
1. Même structure d'API pour compatibilité frontend
2. Base de données PostgreSQL au lieu de fichiers XML/JSON
3. Meilleure scalabilité et performance
4. Interface d'administration Django
5. Support natif pour les tâches asynchrones avec Celery

## Maintenance

### Backup de la base de données
```bash
docker-compose exec postgres pg_dump -U lara_user lara_db > backup.sql
```

### Restauration
```bash
docker-compose exec -T postgres psql -U lara_user lara_db < backup.sql
```

### Mise à jour des données
```bash
# Re-charger les domaines depuis XML
docker-compose exec django python manage.py load_domains --clear ../../domaines.xml
```

## Support

Pour toute question ou problème, consulter la documentation Django:
- https://docs.djangoproject.com/
- https://www.django-rest-framework.org/
