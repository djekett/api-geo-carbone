# API.GEO.Carbone — Département d'Oumé

Plateforme géospatiale de surveillance du couvert forestier et des stocks de carbone dans les **6 forêts classées** du département d'Oumé, Côte d'Ivoire.

## 📊 Données clés

| Forêt classée | Superficie (ha) |
|---|---:|
| TENÉ | 29 549 |
| SANGOUÉ | 27 360 |
| DOKA | 10 945 |
| ZOUÉKÉ Bloc I | 6 825 |
| LAHOUDA | 3 300 |
| ZOUÉKÉ Bloc II | 3 077 |
| **Total** | **81 056** |

### Valeurs de référence (types forestiers)

| Type | Biomasse (t/ha) | Carbone (tC/ha) | CO₂ éq. (tCO₂/ha) |
|---|---:|---:|---:|
| Forêt dense | 1 739,16 | 869,10 | 3 186,70 |
| Forêt claire | 1 804,16 | 902,08 | 3 307,62 |
| Forêt dégradée | 1 062,09 | 531,04 | 1 947,15 |
| Jachère | 1 671,98 | 792,66 | 2 906,42 |

---

## 🚀 Installation

### Prérequis
- Python 3.10+
- PostgreSQL 14+ avec PostGIS 3.x
- Node.js 18+ (optionnel, pour Tailwind CLI build)

### Mise en place de l'environnement virtuel

**Windows :**
```bat
:: Option 1 : Script automatique
setup.bat

:: Option 2 : Manuel
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
:: Éditez .env avec vos paramètres
```

**Linux/Mac :**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Éditez .env avec vos paramètres
```

### Configuration de la base de données
```sql
CREATE DATABASE api_geo_carbone;
\c api_geo_carbone
CREATE EXTENSION postgis;
```

### Migrations et démarrage
```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

---

## 🏗️ Structure du projet

```
api-geo-carbone/
├── config/                     # Configuration Django
│   ├── settings.py
│   ├── urls.py
│   └── views.py               # HomeView, EnjeuxView
├── apps/
│   ├── carbone/                # App principale (forêts, occupation, carbone)
│   │   ├── models.py
│   │   ├── views.py            # ViewSets REST avec simplification géom.
│   │   ├── serializers.py
│   │   ├── filters.py
│   │   ├── constants.py        # Données de référence (superficies, biomasse)
│   │   └── urls.py
│   ├── analysis/               # Analyse IA / Chat-to-Map
│   ├── geodata/                # Données géographiques additionnelles
│   └── accounts/               # Authentification
├── frontend/
│   ├── templates/
│   │   ├── base.html           # Layout avec Tailwind, fonts
│   │   ├── home.html           # Page d'accueil (hero + stats)
│   │   ├── enjeux.html         # Enjeux (charts + géomatique + timeline)
│   │   ├── map/index.html      # Carte interactive
│   │   └── components/
│   │       ├── navbar.html     # Navbar réutilisable
│   │       └── footer.html     # Footer réutilisable
│   └── static/
│       ├── css/
│       │   ├── main.css        # Styles globaux
│       │   └── map.css         # Styles Leaflet optimisés
│       └── js/
│           ├── map/
│           │   ├── api.js      # Client API (cache, abort controllers)
│           │   ├── app.js      # Initialisation carte (Canvas renderer)
│           │   ├── layers.js   # Gestion des couches (lazy loading)
│           │   ├── choropleth.js
│           │   ├── timeSlider.js
│           │   ├── sidebar.js
│           │   ├── legend.js
│           │   ├── stats.js
│           │   ├── popup.js
│           │   └── report.js   # Génération de rapports HTML
│           └── chat/
│               └── chatPanel.js
├── requirements.txt
├── .env.example
├── setup.bat                   # Script d'installation Windows
├── tailwind.config.js
└── manage.py
```

---

## 🌐 Pages

| URL | Description |
|---|---|
| `/` | Page d'accueil (hero, statistiques, forêts) |
| `/enjeux/` | Enjeux de la déforestation (charts, timeline, géomatique) |
| `/carte/` | Carte interactive Leaflet |
| `/admin/` | Interface d'administration Django |
| `/api/v1/` | API REST (GeoJSON) |

---

## ⚡ Optimisations de performance

### Backend (PostGIS)
- `ST_SimplifyPreserveTopology` avec tolérance dynamique (param `?simplify=0.001`)
- Serializers séparés : complets (detail) vs simplifiés (list) avec `geom_simple`
- `select_related` sur les FK pour éviter les N+1
- `.only()` pour limiter les colonnes chargées
- Pagination désactivée (volumétrie maîtrisée, 6 forêts × 3 années)

### Frontend (Leaflet)
- **Canvas renderer** (`L.canvas({ padding: 0.5 })`) au lieu de SVG
- **Debounce 300ms** sur les changements d'année (évite les appels API en rafale)
- **AbortController** : annule les requêtes en cours quand l'année change rapidement
- **Lazy loading** : couches optionnelles chargées uniquement au clic
- **Pas de hover effects** sur les milliers de polygones d'occupation
- Tiles avec `updateWhenIdle: true` (pas de rechargement pendant le zoom)
- Cache API côté client (5 min TTL)

---

## 📜 Stack technique

- **Backend** : Django 4.2, Django REST Framework, PostGIS, django-filter
- **Frontend** : Leaflet 1.9.4, Chart.js 4.4.1, Tailwind CSS
- **Fonts** : DM Serif Display + DM Sans
- **Base** : PostgreSQL + PostGIS

---

## 📝 Notes

- Le CDN Tailwind (`cdn.tailwindcss.com`) est utilisé en développement. En production, compilez avec :
  ```bash
  npx tailwindcss -i frontend/static/css/tailwind-input.css -o frontend/static/css/tailwind-output.css --minify
  ```
- Les erreurs `content-script-start.js` dans la console sont des **extensions navigateur** (pas liées au projet).
