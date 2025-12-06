FROM node:18-alpine

# Créer le répertoire de l'application
WORKDIR /app

# Copier les fichiers de dépendances
COPY package*.json ./

# Installer les dépendances
RUN npm ci --only=production

# Copier le code source
COPY server.js ./
COPY templates.xml ./

# Créer le répertoire pour les uploads temporaires
RUN mkdir -p uploads && chmod 777 uploads

# Exposer le port
EXPOSE 3000

# Variables d'environnement par défaut
ENV PORT=3000
ENV NODE_ENV=production

# Commande de démarrage
CMD ["node", "server.js"]
