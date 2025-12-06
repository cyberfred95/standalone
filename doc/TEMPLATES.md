# Documentation du Système de Templates Lara

## Vue d'ensemble

Le système de templates permet de définir automatiquement quelles mémoires de traduction et quels glossaires Lara utiliser pour chaque combinaison de domaine juridique, langue source et langue cible.

## Structure du Fichier XML

Le fichier `server/templates.xml` contient la configuration des templates. Chaque template définit :

- **id** : Identifiant unique du template
- **name** : Nom descriptif du template
- **domain** : Domaine juridique (Accounting, Banking, Corporate, etc.)
- **source-language** : Code de la langue source (FR, EN, DE, etc.)
- **target-language** : Code de la langue cible
- **translation-memory** : Nom ou ID de la mémoire de traduction Lara à utiliser
- **glossary** : Nom ou ID du glossaire Lara à utiliser
- **description** : Description du template
- **is-default** : Indique si c'est le template par défaut (optionnel)

## Exemple de Template

```xml
<template id="accounting-fr-en" name="Accounting FR to EN">
    <domain>Accounting</domain>
    <source-language>FR</source-language>
    <target-language>EN</target-language>
    <translation-memory>Droit Financier FR-EN</translation-memory>
    <glossary>Accounting_FR</glossary>
    <description>Template pour la traduction du droit comptable de français vers anglais</description>
</template>
```

## Template Par Défaut

Un template par défaut existe pour gérer toutes les combinaisons non spécifiées :

```xml
<template id="default" name="Default Template" is-default="true">
    <domain>*</domain>
    <source-language>*</source-language>
    <target-language>*</target-language>
    <translation-memory></translation-memory>
    <glossary></glossary>
    <description>Template par défaut utilisé lorsqu'aucune configuration spécifique n'est trouvée</description>
</template>
```

Le caractère `*` signifie "n'importe quelle valeur".

## Domaines Juridiques Disponibles

Le système supporte 24 domaines juridiques :

1. **Accounting** - Comptabilité
2. **Arbitration** - Arbitrage
3. **Banking** - Banque
4. **Climate** - Climat
5. **Competition** - Concurrence
6. **Contracts** - Contrats
7. **Corporate** - Droit des sociétés
8. **Crimes-proceedings** - Procédure pénale
9. **Criminal finance** - Finance criminelle
10. **Customs** - Douanes
11. **GDPR** - Protection des données
12. **HR** - Ressources Humaines
13. **Industrial designs** - Dessins industriels
14. **Insurance** - Assurance
15. **Investment** - Investissement
16. **Labour law** - Droit du travail
17. **Maritime law** - Droit maritime
18. **Patents** - Brevets
19. **Real Estate** - Immobilier
20. **Social benefits** - Prestations sociales
21. **Social security** - Sécurité sociale
22. **Tax** - Fiscalité
23. **Town planning** - Urbanisme
24. **Transport** - Transport

## Langues Disponibles

Le système supporte 29 langues européennes et internationales :

- **AR** - Arabe
- **BG** - Bulgare
- **CS** - Tchèque
- **DA** - Danois
- **DE** - Allemand
- **EL** - Grec
- **EN** - Anglais
- **ES** - Espagnol
- **ET** - Estonien
- **FI** - Finnois
- **FR** - Français
- **HR** - Croate
- **HU** - Hongrois
- **IT** - Italien
- **LT** - Lituanien
- **LV** - Letton
- **MT** - Maltais
- **NL** - Néerlandais
- **PL** - Polonais
- **PT** - Portugais
- **RO** - Roumain
- **RU** - Russe
- **SK** - Slovaque
- **SL** - Slovène
- **SV** - Suédois

## API REST pour les Templates

### GET /api/templates
Récupère tous les templates configurés.

**Réponse :**
```json
[
  {
    "id": "accounting-fr-en",
    "name": "Accounting FR to EN",
    "domain": "Accounting",
    "sourceLanguage": "FR",
    "targetLanguage": "EN",
    "translationMemory": "Droit Financier FR-EN",
    "glossary": "Accounting_FR",
    "description": "Template pour la traduction du droit comptable de français vers anglais",
    "isDefault": false
  }
]
```

### GET /api/templates/find
Trouve le template approprié pour une combinaison spécifique.

**Paramètres :**
- `domain` (requis) : Domaine juridique
- `sourceLanguage` (optionnel) : Langue source
- `targetLanguage` (requis) : Langue cible

**Exemple :**
```
GET /api/templates/find?domain=Accounting&sourceLanguage=FR&targetLanguage=EN
```

**Réponse :**
Retourne le template correspondant ou le template par défaut si aucun match n'est trouvé.

### POST /api/templates
Crée un nouveau template.

**Corps de la requête :**
```json
{
  "id": "banking-it-en",
  "name": "Banking IT to EN",
  "domain": "Banking",
  "sourceLanguage": "IT",
  "targetLanguage": "EN",
  "translationMemory": "Banking Law IT-EN",
  "glossary": "Banking_IT",
  "description": "Template pour la traduction du droit bancaire d'italien vers anglais"
}
```

### PUT /api/templates/:id
Met à jour un template existant.

**Paramètres :**
- `id` : Identifiant du template à modifier

**Corps de la requête :**
```json
{
  "translationMemory": "Nouvelle mémoire",
  "glossary": "Nouveau glossaire"
}
```

## Interface Utilisateur

### Visualisation des Templates

1. Ouvrir l'écran de paramètres (bouton ⚙️)
2. Cliquer sur le bouton **"Glossaires"** (en vert)
3. Une fenêtre modale s'ouvre avec un tableau affichant tous les templates

Le tableau affiche :
- ID et nom du template
- Domaine juridique
- Langues source et cible
- Mémoire de traduction associée
- Glossaire associé
- Description
- Badge "Défaut" pour le template par défaut

### Utilisation Automatique

Lorsque vous sélectionnez :
- Un domaine juridique
- Une langue source
- Une langue cible

Le système recherche automatiquement le template correspondant et applique :
- La mémoire de traduction appropriée
- Le glossaire approprié

## Nommage des Glossaires et Mémoires

### Glossaires
Les glossaires suivent la convention : `{Domaine}_{LangueSource}`

Exemples :
- `Accounting_FR` - Glossaire de comptabilité en français
- `Banking_EN` - Glossaire bancaire en anglais
- `Corporate_DE` - Glossaire de droit des sociétés en allemand

### Mémoires de Traduction
Les mémoires de traduction suivent généralement : `{Domaine} {Langue1}-{Langue2}`

Exemples :
- `Droit Financier FR-EN` - Mémoire pour traductions financières FR→EN
- `Banking Law DE-EN` - Mémoire pour droit bancaire DE→EN
- `Corporate Law EN-FR` - Mémoire pour droit des sociétés EN→FR

## Ajouter un Nouveau Template

1. **Manuellement** : Éditer le fichier `server/templates.xml`

```xml
<template id="nouveau-template" name="Nouveau Template">
    <domain>Banking</domain>
    <source-language>IT</source-language>
    <target-language>FR</target-language>
    <translation-memory>Banking IT-FR</translation-memory>
    <glossary>Banking_IT</glossary>
    <description>Description du template</description>
</template>
```

2. **Via l'API** : Utiliser l'endpoint POST /api/templates

```javascript
const response = await fetch('/api/templates', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        id: 'nouveau-template',
        name: 'Nouveau Template',
        domain: 'Banking',
        sourceLanguage: 'IT',
        targetLanguage: 'FR',
        translationMemory: 'Banking IT-FR',
        glossary: 'Banking_IT',
        description: 'Description du template'
    })
});
```

## Bonnes Pratiques

1. **IDs uniques** : Utilisez des IDs descriptifs et uniques (ex: `domain-src-tgt`)
2. **Descriptions claires** : Décrivez précisément l'usage de chaque template
3. **Cohérence** : Suivez les conventions de nommage pour les glossaires et mémoires
4. **Template par défaut** : Ne supprimez jamais le template par défaut
5. **Langues principales** : Priorisez les paires FR↔EN car elles ont le plus de ressources

## Dépannage

### Le template n'est pas trouvé
- Vérifiez les codes de langue (FR, EN, etc.)
- Vérifiez l'orthographe du domaine
- Le système utilisera le template par défaut en cas d'échec

### Erreur de chargement des templates
- Vérifiez la syntaxe XML du fichier templates.xml
- Assurez-vous que le serveur Node.js est démarré
- Consultez les logs du serveur pour plus de détails

### Le glossaire ou la mémoire n'est pas appliqué
- Vérifiez que le nom correspond exactement à celui dans Lara
- Vérifiez que les IDs dans les paramètres Lara sont corrects
- Consultez la documentation Lara pour les noms exacts des ressources

## Évolutions Futures

- Interface d'édition des templates dans l'application
- Import/Export de configurations de templates
- Validation automatique des noms de glossaires/mémoires avec l'API Lara
- Historique des modifications de templates
- Templates multi-domaines (pour documents traitant de plusieurs sujets)
