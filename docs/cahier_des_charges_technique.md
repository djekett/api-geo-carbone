# CAHIER DES CHARGES TECHNIQUE
# Application API.GEO.Carbone
## Système d'Information Géographique pour la gestion des forêts et des foyers de stock de carbone du département d'Oumé (Côte d'Ivoire)

---

## 1. INFORMATIONS GÉNÉRALES

| Élément | Détail |
|---------|--------|
| **Nom du projet** | API.GEO.Carbone |
| **Type d'application** | Application Web SIG (Système d'Information Géographique) |
| **Version** | 2.0 |
| **Cadre** | Thèse de doctorat — Apport de la géomatique dans la lutte contre la réduction des foyers de stocks de carbone forestiers |
| **Zone géographique** | Département d'Oumé, Côte d'Ivoire |

---

## 2. SPÉCIFICATIONS TECHNIQUES

### 2.1 Environnement serveur

| Composant | Spécification |
|-----------|--------------|
| **Système d'exploitation** | Linux (Ubuntu 22.04 LTS) / Windows Server |
| **Langage backend** | Python 3.10+ |
| **Framework web** | Django 4.x |
| **Framework API** | Django REST Framework 3.x |
| **Base de données** | PostgreSQL 15+ avec extension PostGIS 3.x |
| **Bibliothèques géospatiales** | GDAL 3.x, GEOS 3.x, PROJ 9.x |
| **Serveur WSGI** | Gunicorn (production) / Django Dev Server (développement) |
| **Serveur HTTP** | Nginx (reverse proxy, fichiers statiques) |

### 2.2 Environnement client

| Composant | Spécification |
|-----------|--------------|
| **Navigateurs supportés** | Chrome 90+, Firefox 88+, Edge 90+, Safari 14+ |
| **Bibliothèque cartographique** | Leaflet.js 1.9+ |
| **Moteur de rendu** | Canvas (par défaut), SVG (couches légères) |
| **Framework CSS** | Tailwind CSS 3.x |
| **JavaScript** | ES6+ (modules natifs) |

### 2.3 Dépendances Python

```
django>=4.2
djangorestframework>=3.14
djangorestframework-gis>=1.0
django-filter>=23.0
django-cors-headers>=4.0
django-leaflet>=0.29
django-jazzmin>=2.6
psycopg2-binary>=2.9
```

---

## 3. ARCHITECTURE DE LA BASE DE DONNÉES

### 3.1 Schéma des tables

#### Table `carbone_foretclassee`

| Colonne | Type | Contrainte | Description |
|---------|------|-----------|-------------|
| id | SERIAL | PK | Identifiant unique |
| code | VARCHAR(20) | UNIQUE, NOT NULL | Code de la forêt (ex: TENE) |
| nom | VARCHAR(200) | NOT NULL | Nom complet |
| superficie_legale_ha | FLOAT | NULLABLE | Superficie légale en hectares |
| statut_juridique | VARCHAR(100) | DEFAULT '' | Statut juridique |
| date_classement | DATE | NULLABLE | Date de classement |
| autorite_gestion | VARCHAR(200) | DEFAULT '' | Autorité de gestion |
| geom | MULTIPOLYGON | SRID 4326 | Géométrie des limites |
| created_at | TIMESTAMP | AUTO | Date de création |
| updated_at | TIMESTAMP | AUTO | Date de mise à jour |

#### Table `carbone_nomenclaturecouvert`

| Colonne | Type | Contrainte | Description |
|---------|------|-----------|-------------|
| id | SERIAL | PK | Identifiant unique |
| code | VARCHAR(30) | UNIQUE, NOT NULL | Code du type (ex: FORET_DENSE) |
| libelle_fr | VARCHAR(100) | NOT NULL | Libellé en français |
| stock_carbone_reference | FLOAT | NULLABLE | Valeur de référence (tCO₂/ha) |
| couleur_hex | VARCHAR(7) | NOT NULL | Couleur d'affichage (#RRGGBB) |
| ordre_affichage | INTEGER | DEFAULT 0 | Ordre dans la légende |

#### Table `carbone_occupationsol` (table principale)

| Colonne | Type | Contrainte | Description |
|---------|------|-----------|-------------|
| id | SERIAL | PK | Identifiant unique |
| foret_id | INTEGER | FK → foretclassee | Forêt classée associée |
| nomenclature_id | INTEGER | FK → nomenclaturecouvert | Type de couvert |
| annee | SMALLINT | NOT NULL, CHECK(IN 1986,2003,2023) | Année d'observation |
| superficie_ha | FLOAT | NULLABLE | Superficie calculée (ha) |
| stock_carbone_calcule | FLOAT | NULLABLE | Stock CO₂ (tCO₂/ha) |
| source_donnee | VARCHAR(100) | DEFAULT '' | Source satellitaire |
| fiabilite_pct | FLOAT | NULLABLE | Fiabilité (%) |
| notes_admin | TEXT | DEFAULT '' | Notes administratives |
| geom | MULTIPOLYGON | SRID 4326 | Géométrie d'occupation |
| created_at | TIMESTAMP | AUTO | Date de création |
| updated_at | TIMESTAMP | AUTO | Date de mise à jour |

**Index :** `annee`, `(foret_id, annee)`, `(nomenclature_id, annee)`, `(foret_id, nomenclature_id, annee)`

#### Table `carbone_placette`

| Colonne | Type | Contrainte | Description |
|---------|------|-----------|-------------|
| id | SERIAL | PK | Identifiant unique |
| foret_id | INTEGER | FK NULLABLE → foretclassee | Forêt associée |
| code_placette | VARCHAR(50) | DEFAULT '' | Code de la placette |
| annee_mesure | SMALLINT | NULLABLE | Année de mesure |
| type_foret_observe | VARCHAR(100) | DEFAULT '' | Type de forêt observé |
| biomasse_tonne_ha | FLOAT | NULLABLE | Biomasse mesurée (t/ha) |
| stock_carbone_mesure | FLOAT | NULLABLE | Stock carbone mesuré (tCO₂/ha) |
| donnees | JSONB | DEFAULT {} | Données supplémentaires |
| geom | POINT | SRID 4326 | Localisation GPS |
| created_at | TIMESTAMP | AUTO | Date de création |

#### Table `carbone_infrastructure`

| Colonne | Type | Contrainte | Description |
|---------|------|-----------|-------------|
| id | SERIAL | PK | Identifiant unique |
| type_infra | VARCHAR(50) | NOT NULL | Type (ROUTE, HYDROGRAPHIE, etc.) |
| nom | VARCHAR(200) | DEFAULT '' | Nom |
| categorie | VARCHAR(50) | DEFAULT '' | Catégorie |
| geom | GEOMETRY | SRID 4326 | Géométrie (ligne/point) |
| donnees | JSONB | DEFAULT {} | Données supplémentaires |
| created_at | TIMESTAMP | AUTO | Date de création |

#### Table `carbone_zoneetude`

| Colonne | Type | Contrainte | Description |
|---------|------|-----------|-------------|
| id | SERIAL | PK | Identifiant unique |
| nom | VARCHAR(150) | NOT NULL | Nom de la zone |
| type_zone | VARCHAR(50) | NOT NULL | Type (DEPARTEMENT, SOUS_PREFECTURE, etc.) |
| niveau | INTEGER | DEFAULT 1 | Niveau hiérarchique |
| geom | MULTIPOLYGON | SRID 4326 | Géométrie des limites |
| created_at | TIMESTAMP | AUTO | Date de création |
| updated_at | TIMESTAMP | AUTO | Date de mise à jour |

#### Table `analysis_requetenlp` (journalisation)

| Colonne | Type | Contrainte | Description |
|---------|------|-----------|-------------|
| id | SERIAL | PK | Identifiant unique |
| texte_requete | TEXT | NOT NULL | Texte de la requête utilisateur |
| entites_extraites | JSONB | | Entités NLP extraites |
| filtre_orm | TEXT | DEFAULT '' | Description du filtre ORM |
| nombre_resultats | INTEGER | DEFAULT 0 | Nombre de résultats |
| temps_traitement_ms | INTEGER | DEFAULT 0 | Temps de traitement (ms) |
| created_at | TIMESTAMP | AUTO | Date de la requête |

---

## 4. SPÉCIFICATIONS DE L'API REST

### 4.1 Points d'accès (Endpoints)

| Endpoint | Méthode | Auth. requise | Description |
|----------|---------|--------------|-------------|
| `GET /api/v1/forets/` | GET | Non | Liste des forêts classées (GeoJSON) |
| `GET /api/v1/forets/liste/` | GET | Non | Liste sans géométrie |
| `GET /api/v1/occupations/` | GET | Non | Occupation du sol filtrée |
| `POST /api/v1/occupations/` | POST | Admin | Créer une occupation |
| `GET /api/v1/occupations/stats/` | GET | Non | Statistiques agrégées |
| `GET /api/v1/occupations/evolution/` | GET | Non | Comparaison temporelle |
| `GET /api/v1/placettes/` | GET | Non | Points de mesure terrain |
| `GET /api/v1/infrastructures/` | GET | Non | Données contextuelles |
| `GET /api/v1/zones-etude/` | GET | Non | Limites administratives |
| `GET /api/v1/nomenclatures/` | GET | Non | Référentiel de couvert |
| `POST /api/v1/ai/query/` | POST | Non | Requête IA en langage naturel |

### 4.2 Paramètres de requête

**Endpoint `/api/v1/occupations/` :**

| Paramètre | Type | Obligatoire | Description |
|-----------|------|------------|-------------|
| annee | integer | Recommandé | Année (1986, 2003, 2023) |
| foret_code | string | Non | Code de la forêt |
| foret | integer | Non | ID de la forêt |
| type | string | Non | Code du type de couvert |
| zoom | integer | Non | Niveau de zoom (simplification) |
| bbox | string | Non | Emprise (ouest,sud,est,nord) |

### 4.3 Format de réponse

**En-têtes de cache :**
- `Cache-Control: public, max-age=3600` (fichiers statiques)
- `X-GeoCache: HIT` (cache statique) ou `X-GeoCache: SQL` (requête dynamique)

**Format GeoJSON (occupation) :**
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "id": 1,
      "geometry": { "type": "MultiPolygon", "coordinates": [...] },
      "properties": {
        "id": 1,
        "foret_code": "TENE",
        "foret_nom": "Forêt Classée de TENÉ",
        "type_couvert": "FORET_DENSE",
        "libelle": "Forêt dense",
        "couleur": "#006400",
        "annee": 2023,
        "superficie_ha": 1234.56,
        "stock_carbone_calcule": 3186.70,
        "source_donnee": "Sentinel-2"
      }
    }
  ]
}
```

---

## 5. SPÉCIFICATIONS DU MODULE NLP (CHAT-TO-MAP)

### 5.1 Endpoint

| Élément | Valeur |
|---------|--------|
| URL | `POST /api/v1/ai/query/` |
| Content-Type | application/json |
| Corps | `{"query": "texte en français"}` |

### 5.2 Entités reconnues

| Type d'entité | Exemples | Code extrait |
|---------------|----------|-------------|
| Forêt | tene, téné, tené | TENE |
| Forêt | doka | DOKA |
| Forêt | sangoué, sangue | SANGOUE |
| Forêt | lahouda | LAHOUDA |
| Forêt | zouéké bloc 1 | ZOUEKE_1 |
| Forêt | zouéké bloc 2 | ZOUEKE_2 |
| Couvert | forêt dense, bois dense | FORET_DENSE |
| Couvert | forêt claire, bois clair | FORET_CLAIRE |
| Couvert | forêt dégradée | FORET_DEGRADEE |
| Couvert | jachère, friche, reboisement | JACHERE |
| Couvert | cacao, plantation | CACAO |
| Couvert | café | CAFE |
| Couvert | hévéa, caoutchouc | HEVEA |
| Couvert | culture, champ | CULTURE_HERBACEE |
| Couvert | sol nu, zone déboisée | SOL_NU |
| Année | 1986, 2003, 2023 | Entier |

### 5.3 Intentions détectées

| Intention | Mots-clés déclencheurs | Type de réponse |
|-----------|----------------------|-----------------|
| help | bonjour, aide, comment ça marche | Aide + exemples |
| compare | comparer, évolution, entre X et Y | Tableau comparatif |
| deforestation | déforestation, déboisement, perte | Analyse de perte |
| stats | superficie, combien, statistiques | Tableau statistique |
| carbon | carbone, stock, CO₂ | Tableau carbone |
| ranking | classement, top, plus grande | Classement |
| show | (défaut) | GeoJSON sur carte |

### 5.4 Format de réponse IA

```json
{
  "type": "stats|geojson|comparison|deforestation|ranking|help|no_results",
  "parsed": {
    "forests": ["TENE"],
    "cover_types": ["FORET_DENSE"],
    "years": [2023],
    "intent": "stats",
    "_inherited": []
  },
  "data": [...],
  "count": 4,
  "processing_ms": 45
}
```

---

## 6. SPÉCIFICATIONS DE PERFORMANCE

| Métrique | Objectif | Mesure réelle |
|----------|---------|--------------|
| Temps de chargement initial | < 3 s | ~2 s |
| Réponse cache statique (Tier 1) | < 100 ms | < 50 ms |
| Réponse SQL dynamique (Tier 2) | < 5 s | 200-3 000 ms |
| Changement d'année (après préchargement) | < 50 ms | < 5 ms |
| Requête NLP (Chat-to-Map) | < 500 ms | < 200 ms |
| Taille du cache GeoJSON total | < 20 MB | ~10 MB |

---

## 7. SÉCURITÉ

| Aspect | Mesure |
|--------|--------|
| Injection SQL | Prévenue par ORM Django + requêtes paramétrées |
| XSS | Échappement HTML (textContent + _esc()) |
| CSRF | Token Django CSRF obligatoire sur POST |
| Authentification | JWT pour accès API, session Django pour web |
| Autorisations | Lecture publique, écriture admin uniquement |
| CORS | Configuré via django-cors-headers |

---

## 8. COMMANDES DE GESTION

| Commande | Description |
|----------|-------------|
| `python manage.py prebuild_geojson` | Générer le cache GeoJSON statique |
| `python manage.py prebuild_geojson --year 2023` | Régénérer une année |
| `python manage.py prebuild_geojson --clear` | Nettoyer et régénérer |
| `python manage.py simplify_geometries` | Prévisualisation de simplification |
| `python manage.py simplify_geometries --apply` | Simplifier les géométries lourdes |
| `python manage.py seed_nomenclature` | Initialiser les nomenclatures |
| `python manage.py import_forets` | Importer les forêts classées |
| `python manage.py import_occupations` | Importer l'occupation du sol |
| `python manage.py import_placettes` | Importer les placettes terrain |
| `python manage.py import_infrastructure` | Importer les infrastructures |
| `python manage.py import_zones` | Importer les limites administratives |
| `python manage.py check_geo` | Vérifier l'intégrité des géométries |

---

## 9. STRUCTURE DES FICHIERS

```
api-geo-carbone/
├── config/
│   ├── settings/
│   │   └── base.py                  # Configuration Django + PostGIS
│   ├── urls.py                      # Routage URL principal
│   └── views.py                     # Vues de pages HTML
├── apps/
│   ├── accounts/                    # Authentification utilisateurs
│   ├── carbone/                     # Application principale
│   │   ├── models.py               # 6 modèles géospatiaux
│   │   ├── views.py                # ViewSets REST + cache 2-tier
│   │   ├── serializers.py          # Sérialiseurs GeoJSON
│   │   ├── filters.py              # Filtres Django
│   │   ├── constants.py            # Nomenclatures et coefficients
│   │   ├── urls.py                 # Routes API
│   │   └── management/commands/    # Commandes d'import et cache
│   ├── analysis/                   # Module IA Chat-to-Map
│   │   ├── nlp_engine.py           # Moteur NLP
│   │   ├── views.py                # Endpoint IA
│   │   ├── models.py               # Journalisation requêtes
│   │   └── urls.py                 # Route IA
│   └── geodata/                    # Import de données géographiques
├── frontend/
│   ├── static/
│   │   ├── js/map/                 # Modules cartographiques JS
│   │   │   ├── app.js              # Initialisation
│   │   │   ├── api.js              # Client API avec cache
│   │   │   ├── layers.js           # Gestionnaire de couches
│   │   │   ├── choropleth.js       # Rendu double-bufferé
│   │   │   ├── timeSlider.js       # Curseur temporel
│   │   │   ├── sidebar.js          # Barre latérale
│   │   │   ├── legend.js           # Légende dynamique
│   │   │   ├── stats.js            # Statistiques
│   │   │   ├── popup.js            # Popups informatifs
│   │   │   └── report.js           # Rapports
│   │   ├── js/chat/
│   │   │   └── chatPanel.js        # Interface Chat-to-Map
│   │   └── css/
│   │       ├── main.css            # Styles globaux
│   │       └── map.css             # Styles cartographiques
│   └── templates/
│       ├── base.html               # Template de base
│       ├── map/index.html          # Carte interactive
│       └── components/             # Composants HTML réutilisables
├── media/
│   └── geocache/                   # Cache GeoJSON pré-calculé
│       ├── forets.json
│       ├── occupations_1986.json
│       ├── occupations_2003.json
│       ├── occupations_2023.json
│       ├── occupations_*_TENE.json
│       ├── occupations_*_DOKA.json
│       └── zones.json
└── docs/                           # Documentation
```
