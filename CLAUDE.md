# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a web UI for testing professional translation services:
- **Lexa (Lexamt)**: Legal translation API from portail.lexamt.fr - direct API calls from browser
- **Lara (LaraTranslate)**: AI adaptive translation with translation memories - calls via Django backend proxy

The service choice is configured in the setup modal (settings icon).

## Commands

```bash
# Start web interface (Docker)
docker-compose up -d

# View logs
docker-compose logs -f

# Serve locally without Docker (for development)
python -m http.server 8080  # or: npx http-server -p 8080

# Glossary management scripts
npm run glossary:list        # List all glossaries
npm run glossary:validate    # Validate glossaries
npm run glossary:upload-test # Upload test glossary
npm run glossary:upload-all  # Upload all glossaries

# Run quality test
npm run test
```

## Architecture

```
Browser (lexa_standalone.html)
    │
    ├──► Lexa API (direct)
    │    https://api.portail.lexamt.fr/api/v1
    │
    └──► Django Backend (via nginx proxy)
         /lara-django/api/lara → Lara SDK
```

### JavaScript Modules

| File | Purpose |
|------|---------|
| `js/config.js` | Global config, localStorage persistence, API key validation |
| `js/init.js` | App entry point (DOMContentLoaded) |
| `js/lexa.js` | Lexa API: languages, domains, glossaries, translation |
| `js/lara.js` | Lara API: templates, translation, document polling |
| `js/ui.js` | DOM events, modals, mode switching (text/file) |
| `js/files.js` | File upload, drag-and-drop handling |
| `js/utils.js` | Utility functions (showMessage, setLoading, etc.) |

### Data Flow

1. **Config Loading**: `loadConfigFromStorage()` reads from `localStorage` key `translation_config`
2. **Service Selection**: `handleServiceChange()` toggles Lexa/Lara-specific UI sections
3. **Translation**: `testTranslation()` dispatches to `translateWithLexa()` or `translateWithLara()`
4. **Templates (Lara only)**: Selected via domain+languages, provides memory/glossary IDs

## Key Patterns

**API Base URL Detection** (`js/config.js`):
- Local development: `http://localhost:8001/lara-django/api/lara`
- Production (nginx on :8080): `/lara-django/api/lara`

**Translation Services Configuration**:
```javascript
config = {
    translationService: 'lexa' | 'lara',
    lexa: { apiKey, baseUrl },
    lara: { accessKeyId, accessKeySecret, baseUrl, style, instructions, translationMemoryIds, glossaryIds }
}
```

**Template System** (Lara only): Templates link domain+language pairs to specific translation memories and glossaries. Templates are loaded from `/api/lara/templates` and auto-selected based on domain/source/target selection.

## Environment

Configure `.env` with Lara credentials for glossary scripts:
```
LARA_ACCESS_KEY_ID=your_key
LARA_ACCESS_KEY_SECRET=your_secret
```

## File Formats Supported

PDF, DOCX, DOC, TXT, RTF, ODT (max 50MB)

## Language Codes

- Lexa uses uppercase: `FR`, `EN`, `DE`
- Lara uses lowercase: `fr`, `en`, `de`

The UI handles this transparently based on the selected service.