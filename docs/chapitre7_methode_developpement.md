# CHAPITRE 7 : MÉTHODE DE DÉVELOPPEMENT DE L'APPLICATION « API-GEO-CARBONE » POUR LA GESTION DES FORÊTS ET DES FOYERS DE STOCK DE CARBONE DU DÉPARTEMENT D'OUMÉ

---

## 7.1 Approche méthodique générale

### 7.1.1 Contexte et justification

Dans le cadre de cette thèse portant sur l'apport de la géomatique dans la lutte contre la réduction des foyers de stocks de carbone forestiers en milieu tropical, le développement d'un outil informatique dédié s'est imposé comme une nécessité méthodologique. L'application **API.GEO.Carbone** a été conçue pour répondre à un triple objectif : (i) centraliser et normaliser les données géospatiales relatives aux réserves forestières du département d'Oumé, (ii) fournir une interface cartographique interactive permettant la visualisation et l'analyse spatio-temporelle de l'occupation du sol, et (iii) intégrer un module d'intelligence artificielle facilitant l'interrogation en langage naturel des données forestières.

Le département d'Oumé, situé dans le centre-ouest de la Côte d'Ivoire, abrite **six (6) forêts classées** couvrant une superficie légale totale de **81 056 hectares** :

| N° | Forêt classée | Code | Superficie légale (ha) |
|----|---------------|------|------------------------|
| 1 | Forêt Classée de TENÉ | TENE | 29 549 |
| 2 | Forêt Classée de SANGOUÉ | SANGOUE | 27 360 |
| 3 | Forêt Classée de DOKA | DOKA | 10 945 |
| 4 | Forêt Classée de ZOUÉKÉ Bloc I | ZOUEKE_1 | 6 825 |
| 5 | Forêt Classée de LAHOUDA | LAHOUDA | 3 300 |
| 6 | Forêt Classée de ZOUÉKÉ Bloc II | ZOUEKE_2 | 3 077 |
| | **TOTAL** | | **81 056** |

**Tableau 7.1** — Répertoire des forêts classées du département d'Oumé intégrées dans l'application API.GEO.Carbone.

### 7.1.2 Méthodologie de développement adoptée

Le développement de l'application API.GEO.Carbone s'inscrit dans une approche **itérative et incrémentale**, inspirée de la méthode agile. Cette approche a été retenue pour les raisons suivantes :

- **Adaptabilité** : les exigences fonctionnelles ont évolué au fur et à mesure de l'avancement des travaux de terrain et de l'acquisition des données satellitaires ;
- **Livraison progressive** : chaque itération a produit un module fonctionnel testable (cartographie, statistiques, analyse IA) ;
- **Validation continue** : les résultats intermédiaires ont pu être confrontés aux données de terrain (placettes de mesure).

Le cycle de développement a suivi les phases suivantes :

1. **Phase d'analyse** : identification des besoins, collecte des données géospatiales (images Landsat 1986, Landsat 2003, Sentinel-2 2023), définition de la nomenclature d'occupation du sol ;
2. **Phase de conception** : modélisation de la base de données géographique, architecture technique client-serveur, spécification des API REST ;
3. **Phase de développement** : implémentation du backend (Django/PostGIS), du frontend cartographique (Leaflet.js), et du module NLP (Chat-to-Map) ;
4. **Phase de test et validation** : confrontation des résultats de classification avec les mesures de terrain, tests de performance, validation des calculs de stock de carbone ;
5. **Phase de déploiement** : mise en production, optimisation des performances, génération du cache géographique statique.

### 7.1.3 Données d'entrée

L'application exploite trois séries temporelles de données d'occupation du sol :

| Année | Source satellite | Résolution spatiale | Méthode de classification |
|-------|----------------|---------------------|---------------------------|
| 1986 | Landsat TM | 30 m | Classification supervisée |
| 2003 | Landsat ETM+ | 30 m | Classification supervisée |
| 2023 | Sentinel-2 | 10 m | Classification supervisée |

**Tableau 7.2** — Sources de données satellitaires utilisées pour la cartographie d'occupation du sol.

### 7.1.4 Nomenclature d'occupation du sol

La nomenclature retenue pour la classification de l'occupation du sol comprend **neuf (9) classes** regroupées en deux catégories : les foyers de stock de carbone (classes forestières) et les classes non forestières.

| Code | Libellé | Catégorie | Biomasse (t/ha) | Carbone total (tC/ha) | Stock CO₂ (tCO₂/ha) | Couleur |
|------|---------|-----------|----------------:|---------------------:|--------------------:|---------|
| FORET_DENSE | Forêt dense | Forestier | 1 739,16 | 869,10 | 3 186,70 | ■ #006400 |
| FORET_CLAIRE | Forêt claire | Forestier | 1 804,16 | 902,08 | 3 307,62 | ■ #32CD32 |
| FORET_DEGRADEE | Forêt dégradée | Forestier | 1 062,09 | 531,04 | 1 947,15 | ■ #9ACD32 |
| JACHERE | Jachère / Reboisement | Forestier | 1 671,98 | 792,66 | 2 906,42 | ■ #FFFF00 |
| CACAO | Cacao | Non forestier | 0 | 0 | 0 | ■ #FFA500 |
| CAFE | Café | Non forestier | 0 | 0 | 0 | ■ #8B4513 |
| HEVEA | Hévéa | Non forestier | 0 | 0 | 0 | ■ #FFB6C1 |
| CULTURE_HERBACEE | Culture annuelle / Herbacée | Non forestier | 0 | 0 | 0 | ■ #DA70D6 |
| SOL_NU | Sol nu | Non forestier | 0 | 0 | 0 | ■ #E0FFFF |

**Tableau 7.3** — Nomenclature d'occupation du sol et valeurs de référence carbone.

Les valeurs de biomasse et de stock de carbone sont issues des mesures de terrain réalisées sur les placettes d'échantillonnage au sein des forêts classées du département d'Oumé.

---

## 7.2 Architecture Technique

### 7.2.1 Architecture générale

L'application API.GEO.Carbone repose sur une architecture **client-serveur à trois niveaux** (three-tier architecture) :

```
┌─────────────────────────────────────────────────────────────────┐
│                    COUCHE PRÉSENTATION                          │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────┐     │
│  │  Leaflet.js  │  │  Sidebar UI  │  │  Chat-to-Map IA   │     │
│  │  (Carte      │  │  (Couches,   │  │  (Requêtes NLP    │     │
│  │  interactive) │  │  Légende,    │  │  en français)     │     │
│  │              │  │  Stats)      │  │                   │     │
│  └──────┬───────┘  └──────┬───────┘  └────────┬──────────┘     │
│         └─────────────────┼───────────────────┘                │
│                           │ API REST (JSON/GeoJSON)            │
├───────────────────────────┼─────────────────────────────────────┤
│                    COUCHE MÉTIER                                │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────┐     │
│  │  Django REST  │  │  Moteur NLP  │  │  Cache GeoJSON    │     │
│  │  Framework   │  │  (Analyse    │  │  statique         │     │
│  │  (ViewSets)  │  │  sémantique) │  │  (Tier 1/Tier 2)  │     │
│  └──────┬───────┘  └──────┬───────┘  └────────┬──────────┘     │
│         └─────────────────┼───────────────────┘                │
│                           │ ORM Django + SQL brut PostGIS      │
├───────────────────────────┼─────────────────────────────────────┤
│                    COUCHE DONNÉES                               │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────┐     │
│  │  PostgreSQL   │  │  PostGIS     │  │  Fichiers cache   │     │
│  │  (Données    │  │  (Fonctions  │  │  GeoJSON          │     │
│  │  relationnelles│  │  spatiales) │  │  (media/geocache/)│     │
│  └──────────────┘  └──────────────┘  └───────────────────┘     │
└─────────────────────────────────────────────────────────────────┘
```

**Figure 7.1** — Architecture trois-tiers de l'application API.GEO.Carbone.

### 7.2.2 Pile technologique

Le choix des technologies a été guidé par les critères de performance, d'interopérabilité avec les standards géospatiaux (OGC), et de maturité des écosystèmes open source.

**Backend (côté serveur) :**

| Technologie | Version | Rôle |
|-------------|---------|------|
| Python | 3.x | Langage de programmation principal |
| Django | 4.x | Framework web (modèle MTV) |
| Django REST Framework | 3.x | Construction des API RESTful |
| PostGIS | 3.x | Extension spatiale de PostgreSQL |
| PostgreSQL | 15+ | Système de gestion de base de données relationnelle |
| GDAL/OGR | 3.x | Bibliothèque de traitement géospatial |
| GEOS | 3.x | Moteur de géométrie computationnelle |
| PROJ | 9.x | Transformations de coordonnées |

**Tableau 7.4** — Technologies du backend.

**Frontend (côté client) :**

| Technologie | Rôle |
|-------------|------|
| Leaflet.js 1.9+ | Bibliothèque de cartographie web interactive |
| Canvas Renderer | Rendu haute performance (milliers de polygones) |
| Tailwind CSS | Framework CSS utilitaire pour l'interface |
| JavaScript (ES6+) | Logique client (modules : API, Layers, Choropleth, etc.) |

**Tableau 7.5** — Technologies du frontend.

### 7.2.3 Architecture de performance ultra-rapide

L'un des défis majeurs de l'application est le rendu de milliers de polygones d'occupation du sol sur la carte interactive. Une architecture de cache à deux niveaux a été mise en place :

**Tier 1 — Cache GeoJSON statique (< 50 ms) :**
Les fichiers GeoJSON pré-calculés sont stockés dans le répertoire `media/geocache/` et servis directement comme fichiers statiques. Ce cache est généré par la commande `prebuild_geojson` qui applique une simplification géométrique (tolérance de 0,0006°, soit ~66 m de précision) adaptée à l'affichage cartographique thématique.

**Tier 2 — Requête PostGIS dynamique (200-3 000 ms) :**
En l'absence de fichier cache, une requête SQL brute est exécutée avec une simplification adaptative au niveau de zoom :

| Niveau de zoom | Tolérance (degrés) | Précision approx. |
|---------------|--------------------|--------------------|
| 7 | 0,01 | ~1 100 m |
| 10 | 0,002 | ~220 m |
| 12 | 0,0008 | ~88 m |
| 14 | 0,0003 | ~33 m |

**Tableau 7.6** — Simplification adaptative selon le niveau de zoom.

**Côté client**, trois optimisations complémentaires assurent la fluidité :

1. **Rendu Canvas** : utilisation du moteur Canvas de Leaflet (au lieu du SVG) pour dessiner efficacement des milliers de polygones ;
2. **Double buffering** : la nouvelle couche est construite hors écran puis ajoutée à la carte *avant* de supprimer l'ancienne, éliminant tout clignotement visuel ;
3. **Préchargement en arrière-plan** : les données des trois années (1986, 2003, 2023) sont chargées en mémoire au démarrage, rendant le changement d'année quasi instantané (< 5 ms).

### 7.2.4 Architecture des panneaux cartographiques (Map Panes)

Pour garantir un affichage correct des différentes couches thématiques, chaque type de donnée est rendu dans un panneau cartographique dédié avec un z-index spécifique :

| Panneau | z-index | Contenu | Moteur de rendu |
|---------|---------|---------|-----------------|
| occupationPane | 400 | Polygones d'occupation du sol | Canvas |
| foretsPane | 450 | Limites des forêts classées | SVG |
| limitesPane | 460 | Limites administratives | SVG |
| infraPane | 470 | Routes, hydrographie, localités | Canvas |

**Tableau 7.7** — Isolation des couches par panneaux cartographiques.

---

## 7.3 Modélisation et normalisation des données

### 7.3.1 Modèle Conceptuel de Données (MCD)

Le modèle de données de l'application API.GEO.Carbone est structuré autour de **six entités principales** interconnectées par des relations hiérarchiques et spatiales.

```
┌──────────────────┐         ┌─────────────────────┐
│   ZoneEtude      │         │   ForetClassee       │
├──────────────────┤         ├─────────────────────┤
│ PK id            │         │ PK id                │
│    nom           │         │    code (UNIQUE)      │
│    type_zone     │         │    nom                │
│    niveau        │         │    superficie_legale   │
│    geom (MULTI   │         │    statut_juridique    │
│    POLYGON 4326) │         │    date_classement     │
└──────────────────┘         │    autorite_gestion    │
                             │    geom (MULTIPOLY)    │
                             └──────────┬────────────┘
                                        │ 1
                                        │
                                        │ N
┌──────────────────┐         ┌──────────┴────────────┐
│ Nomenclature     │         │   OccupationSol       │
│ Couvert          │    N    │   (TABLE CENTRALE)     │
├──────────────────┤◄────────┤─────────────────────── │
│ PK id            │    1    │ PK id                  │
│    code (UNIQUE) │         │ FK foret_id            │
│    libelle_fr    │         │ FK nomenclature_id     │
│    stock_carbone │         │    annee (1986/2003/   │
│    _reference    │         │           2023)        │
│    couleur_hex   │         │    superficie_ha       │
│    ordre_affich. │         │    stock_carbone_calc.  │
└──────────────────┘         │    source_donnee       │
                             │    fiabilite_pct       │
                             │    geom (MULTIPOLY)    │
                             └───────────────────────┘

┌──────────────────┐         ┌─────────────────────┐
│   Placette       │         │   Infrastructure     │
├──────────────────┤         ├─────────────────────┤
│ PK id            │         │ PK id                │
│ FK foret_id      │         │    type_infra         │
│    code_placette │         │    nom                │
│    annee_mesure  │         │    categorie          │
│    type_foret    │         │    geom (GEOMETRY)    │
│    biomasse_t_ha │         │    donnees (JSON)     │
│    stock_carbone │         └─────────────────────┘
│    geom (POINT)  │
└──────────────────┘
```

**Figure 7.2** — Modèle Conceptuel de Données de l'application API.GEO.Carbone.

### 7.3.2 Description des entités

**Table OccupationSol (table centrale)** — Cette table constitue le cœur du système d'information géographique. Elle stocke, pour chaque combinaison forêt/type de couvert/année, la géométrie polygonale de l'occupation du sol ainsi que les valeurs calculées de superficie et de stock de carbone. La table est indexée sur les colonnes `annee`, `foret_id`, et `nomenclature_id` pour optimiser les requêtes de filtrage.

**Table ForetClassee** — Stocke les entités géographiques fixes des six forêts classées avec leurs limites officielles, leur statut juridique et leur superficie légale.

**Table NomenclatureCouvert** — Référentiel des neuf types d'occupation du sol avec les valeurs de référence de biomasse, carbone et stock CO₂ par hectare.

**Table Placette** — Points de mesure terrain (biomasse, stock carbone mesuré) permettant la validation des résultats de télédétection.

**Table Infrastructure** — Données contextuelles (réseau routier, hydrographie, chefs-lieux de sous-préfecture) pour l'aide à la décision.

**Table ZoneEtude** — Limites administratives hiérarchiques (département, sous-préfectures, localités).

### 7.3.3 Normalisation

Le modèle de données respecte la **troisième forme normale (3NF)** :

- **1NF** : chaque attribut est atomique ; les géométries sont stockées dans des colonnes PostGIS typées ;
- **2NF** : chaque attribut non-clé dépend de la totalité de la clé primaire ;
- **3NF** : les dépendances transitives sont éliminées par la séparation en tables distinctes (nomenclature séparée de l'occupation du sol, forêt séparée des zones d'étude).

### 7.3.4 Calculs automatiques

Le modèle implémente des calculs automatiques lors de l'enregistrement d'un objet `OccupationSol` :

1. **Superficie automatique** : si la superficie n'est pas renseignée, elle est calculée par transformation de la géométrie dans le système de projection UTM zone 30N (EPSG:32630) puis calcul de l'aire en hectares ;
2. **Stock de carbone** : si le stock de carbone n'est pas renseigné, il est initialisé à partir de la valeur de référence de la nomenclature associée.

---

## 7.4 Exposition des données via l'API géographique

### 7.4.1 Architecture RESTful

L'application expose ses données via une API REST conforme aux bonnes pratiques de conception d'API géographiques. L'URL de base est `/api/v1/`.

| Point d'accès (Endpoint) | Méthode | Description | Format de réponse |
|--------------------------|---------|-------------|-------------------|
| `/api/v1/forets/` | GET | Limites des forêts classées | GeoJSON |
| `/api/v1/occupations/?annee=2023` | GET | Occupation du sol filtrée | GeoJSON |
| `/api/v1/occupations/stats/?annee=2023` | GET | Statistiques agrégées | JSON |
| `/api/v1/occupations/evolution/?foret=TENE&annee1=1986&annee2=2023` | GET | Comparaison temporelle | JSON |
| `/api/v1/placettes/` | GET | Points de mesure terrain | GeoJSON |
| `/api/v1/infrastructures/?type=ROUTE` | GET | Infrastructures filtrées | GeoJSON |
| `/api/v1/zones-etude/` | GET | Limites administratives | GeoJSON |
| `/api/v1/nomenclatures/` | GET | Référentiel des types de couvert | JSON |
| `/api/v1/ai/query/` | POST | Requête IA en langage naturel | JSON |

**Tableau 7.8** — Catalogue des points d'accès de l'API REST.

### 7.4.2 Paramètres de filtrage

L'API supporte un filtrage avancé via les paramètres de requête HTTP :

- **`annee`** : année d'observation (1986, 2003 ou 2023)
- **`foret_code`** : code de la forêt classée (TENE, DOKA, SANGOUE, etc.)
- **`type`** : code du type de couvert (FORET_DENSE, JACHERE, etc.)
- **`zoom`** : niveau de zoom pour la simplification adaptative
- **`bbox`** : emprise géographique (ouest,sud,est,nord) pour le filtrage spatial

### 7.4.3 Sérialisation GeoJSON

Les réponses géographiques sont sérialisées au format GeoJSON (RFC 7946) via les `GeoFeatureModelSerializer` de Django REST Framework. Chaque entité spatiale est retournée sous la forme :

```json
{
  "type": "Feature",
  "id": 5,
  "geometry": {
    "type": "MultiPolygon",
    "coordinates": [...]
  },
  "properties": {
    "foret_code": "DOKA",
    "foret_nom": "Forêt Classée de DOKA",
    "type_couvert": "FORET_DENSE",
    "libelle": "Forêt dense",
    "couleur": "#006400",
    "annee": 2023,
    "superficie_ha": 123.45,
    "stock_carbone_calcule": 107150.50,
    "source_donnee": "Sentinel-2"
  }
}
```

---

## 7.5 Intégration de l'Intelligence Artificielle

### 7.5.1 Module Chat-to-Map : principe

Le module **Chat-to-Map** constitue l'une des innovations majeures de l'application API.GEO.Carbone. Il permet à l'utilisateur d'interroger les données forestières en **langage naturel français**, sans nécessiter de compétences techniques en SIG ou en SQL.

L'architecture du module repose sur un **pipeline de traitement du langage naturel (NLP)** en quatre étapes :

```
Requête utilisateur (français)
        │
        ▼
┌───────────────────────┐
│ 1. NORMALISATION       │
│    Suppression accents │
│    Conversion minusc.  │
└───────────┬───────────┘
            ▼
┌───────────────────────┐
│ 2. EXTRACTION          │
│    D'ENTITÉS           │
│    - Forêts (regex)    │
│    - Types couvert     │
│    - Années            │
│    - Seuils            │
└───────────┬───────────┘
            ▼
┌───────────────────────┐
│ 3. DÉTECTION           │
│    D'INTENTION         │
│    help | compare |    │
│    deforestation |     │
│    stats | carbon |    │
│    ranking | show      │
└───────────┬───────────┘
            ▼
┌───────────────────────┐
│ 4. CONSTRUCTION        │
│    DU FILTRE ORM       │
│    Django QuerySet     │
│    sécurisé            │
└───────────┬───────────┘
            ▼
    Réponse (GeoJSON,
    tableau, graphique)
```

**Figure 7.3** — Pipeline NLP du module Chat-to-Map.

### 7.5.2 Extraction d'entités nommées

Le moteur NLP utilise des **expressions régulières étendues** avec support des variations orthographiques (accents, synonymes) pour extraire trois types d'entités :

**Entités géographiques (forêts) :**
- Patterns regex avec tolérance aux accents : `\btene\b`, `\bsangou[eé]\b`, `\bzou[eè]k[eé]\s*(?:bloc\s*)?(?:1|i)\b`
- Support des noms avec et sans accents grâce à la normalisation Unicode (NFKD)

**Entités thématiques (types de couvert) :**
- Patterns principaux : `\bfor[eê]t\s+dense\b`, `\bjach[eè]re\b`
- Synonymes étendus : « bois dense » → FORET_DENSE, « friche » → JACHERE, « caoutchouc » → HEVEA

**Entités temporelles (années) :**
- Pattern strict : `\b(1986|2003|2023)\b`
- Support d'intervalles : « entre 1986 et 2023 »

### 7.5.3 Détection d'intention

Le système détecte sept types d'intention, classés par ordre de priorité :

| Priorité | Intention | Patterns déclencheurs | Exemple de requête |
|----------|-----------|----------------------|-------------------|
| 1 | help | « bonjour », « aide », « comment ça marche » | « Bonjour, que peux-tu faire ? » |
| 2 | compare | « comparer », « évolution », « entre X et Y » | « Compare TENE entre 1986 et 2023 » |
| 3 | deforestation | « déforestation », « déboisement », « perte forestière » | « Déforestation à DOKA » |
| 4 | stats | « superficie », « combien », « statistiques » | « Quelle est la superficie de forêt dense ? » |
| 5 | carbon | « carbone », « stock », « CO2 », « séquestration » | « Stock de carbone à LAHOUDA en 2023 » |
| 6 | ranking | « classement », « top », « plus grande » | « Classement des forêts par superficie » |
| 7 | show | (défaut) | « Montre les zones de forêt claire à DOKA » |

**Tableau 7.9** — Matrice des intentions du moteur NLP.

### 7.5.4 Mémoire conversationnelle

Le module implémente une **mémoire de session** qui hérite les entités manquantes de la requête précédente. Si l'utilisateur demande « Montre la forêt dense à TENE en 2023 » puis « Et la forêt claire ? », le système hérite automatiquement la forêt (TENE) et l'année (2023) de la requête précédente. Les entités héritées sont visuellement distinguées dans l'interface par des tags de couleur plus claire.

### 7.5.5 Sécurité des requêtes

Toutes les requêtes sont construites via l'**ORM Django** (et non par concaténation SQL), ce qui élimine tout risque d'injection SQL. Les filtres sont appliqués de manière programmatique :

```python
qs = OccupationSol.objects.select_related('foret', 'nomenclature')
if parsed['forests']:
    qs = qs.filter(foret__code__in=parsed['forests'])
if parsed['cover_types']:
    qs = qs.filter(nomenclature__code__in=parsed['cover_types'])
if parsed['years']:
    qs = qs.filter(annee__in=parsed['years'])
```

---

## 7.6 Visualisation et analyse décisionnelle

### 7.6.1 Cartographie interactive

L'interface cartographique offre les fonctionnalités suivantes :

- **Fonds de carte** : trois couches de base interchangeables (OpenStreetMap, ESRI Satellite, OpenTopoMap) ;
- **Couches thématiques** : occupation du sol (choroplèthe), limites des forêts classées (contour vert pointillé), limites administratives (violet), placettes de mesure (points rouges), réseau routier, hydrographie, localités ;
- **Navigation temporelle** : curseur temporel avec animation automatique entre les trois dates d'observation (1986, 2003, 2023) ;
- **Sélecteur de forêt** : filtrage par forêt classée individuelle ;
- **Popups informatifs** : au clic sur un polygone, affichage des propriétés (type de couvert, superficie, stock de carbone, source des données).

### 7.6.2 Légende dynamique

La légende est générée dynamiquement à partir du référentiel de nomenclature chargé via l'API. Chaque entrée affiche le code couleur, le libellé et la valeur de référence de stock de carbone (tCO₂/ha).

### 7.6.3 Module statistique

Le panneau statistique affiche en temps réel :

- **Superficie totale** par type de couvert pour l'année et la forêt sélectionnées ;
- **Stock de carbone total** (en tCO₂) ;
- **Nombre de polygones** ;
- **Répartition graphique** des types de couvert.

### 7.6.4 Génération de rapports

L'application intègre un module de génération de rapports permettant à l'utilisateur de :
- Spécifier un titre, un auteur, une année de référence ;
- Sélectionner les sections à inclure (statistiques, cartographie, analyse comparative) ;
- Ajouter des notes personnalisées ;
- Exporter le rapport au format imprimable.

---

## 7.7 Apport méthodique pour la thèse

### 7.7.1 Contribution à la quantification des stocks de carbone

L'application API.GEO.Carbone apporte une contribution méthodologique significative à la thèse par :

1. **Automatisation des calculs** : le calcul des superficies (via transformation UTM zone 30N) et des stocks de carbone (via les valeurs de référence par type de couvert) est automatisé, réduisant les risques d'erreur humaine et assurant la reproductibilité des résultats ;

2. **Analyse spatio-temporelle intégrée** : la possibilité de comparer instantanément les données de trois époques (1986, 2003, 2023) au sein d'une même interface permet de quantifier précisément la dynamique de déforestation et la perte de stocks de carbone ;

3. **Validation croisée** : l'intégration des données de placettes de terrain dans le même système permet la confrontation directe entre les mesures in situ et les résultats de classification satellitaire ;

4. **Accessibilité** : le module Chat-to-Map rend les analyses géospatiales accessibles aux gestionnaires forestiers et aux décideurs non spécialistes en SIG.

### 7.7.2 Reproductibilité scientifique

L'architecture de l'application garantit la reproductibilité des résultats :

- Les données sources (shapefiles d'occupation du sol) sont versionnées par année ;
- Les coefficients de biomasse et de carbone sont centralisés dans un référentiel unique ;
- Les requêtes SQL de l'API sont déterministes et documentées ;
- Le cache GeoJSON pré-calculé assure des résultats identiques entre les différents modes d'accès (cache statique vs requête dynamique).

---

## 7.8 Perspectives

### 7.8.1 Perspectives à court terme

- **Intégration de données supplémentaires** : ajout de nouvelles dates d'observation (images Sentinel-2 récentes) pour affiner la dynamique temporelle ;
- **Module de prédiction** : intégration d'un modèle de projection linéaire permettant d'estimer l'évolution des stocks de carbone à l'horizon 2030-2050 ;
- **Export des données** : module d'export au format PDF/Excel des rapports statistiques.

### 7.8.2 Perspectives à moyen terme

- **Intelligence artificielle avancée** : remplacement du moteur NLP basé sur les expressions régulières par un modèle de langage (LLM) pour une meilleure compréhension du langage naturel ;
- **Intégration REDD+** : alignement des calculs de carbone avec les méthodologies du mécanisme REDD+ (Réduction des Émissions liées à la Déforestation et à la Dégradation des forêts) ;
- **Application mobile** : développement d'une version mobile pour la collecte de données terrain.

### 7.8.3 Perspectives à long terme

- **Plateforme nationale** : extension de l'application à l'ensemble des forêts classées de Côte d'Ivoire ;
- **Système d'alerte précoce** : intégration de données satellitaires en temps quasi-réel (Sentinel-2, 5 jours de revisite) pour la détection automatique de la déforestation ;
- **Interopérabilité OGC** : publication des données via des services WMS/WFS conformes aux standards de l'Open Geospatial Consortium.

---

## 7.9 Définition des composants et fonctionnalités de l'application Web SIG

### 7.9.1 Composants frontend

L'architecture frontend est modulaire, organisée en composants JavaScript spécialisés :

| Composant | Fichier | Responsabilité |
|-----------|---------|---------------|
| App | `app.js` | Initialisation, orchestration du chargement |
| API | `api.js` | Client HTTP avec cache mémoire (TTL 5 min), AbortController |
| LayerManager | `layers.js` | Gestion des couches (base + overlay), chargement paresseux |
| Choropleth | `choropleth.js` | Rendu double-bufferé des polygones d'occupation |
| TimeSlider | `timeSlider.js` | Curseur temporel avec mode lecture automatique |
| Sidebar | `sidebar.js` | Navigation par onglets (Couches, Légende, Stats, Rapport) |
| Legend | `legend.js` | Légende dynamique depuis l'API nomenclatures |
| Stats | `stats.js` | Chargement et affichage des statistiques |
| PopupBuilder | `popup.js` | Construction des popups informatifs |
| ReportGenerator | `report.js` | Interface de génération de rapports |
| ChatPanel | `chatPanel.js` | Interface Chat-to-Map IA |

**Tableau 7.10** — Composants frontend de l'application.

### 7.9.2 Composants backend

| Composant | Module | Responsabilité |
|-----------|--------|---------------|
| OccupationSolViewSet | `carbone/views.py` | API occupation du sol (cache + SQL) |
| ForetClasseeViewSet | `carbone/views.py` | API forêts classées |
| ZoneEtudeViewSet | `carbone/views.py` | API zones d'étude |
| InfrastructureViewSet | `carbone/views.py` | API infrastructures |
| PlacetteViewSet | `carbone/views.py` | API placettes de mesure |
| NomenclatureCouvertViewSet | `carbone/views.py` | API référentiel nomenclature |
| AIQueryView | `analysis/views.py` | Endpoint IA (Chat-to-Map) |
| NLPEngine | `analysis/nlp_engine.py` | Moteur de traitement du langage naturel |

**Tableau 7.11** — Composants backend de l'application.

### 7.9.3 Fonctionnalités principales

1. **Visualisation cartographique multi-temporelle** : affichage de l'occupation du sol pour trois époques avec changement instantané ;
2. **Filtrage spatial et thématique** : sélection par forêt, type de couvert, année, emprise géographique ;
3. **Calcul de statistiques en temps réel** : superficie et stock de carbone par type de couvert ;
4. **Analyse comparative** : comparaison côte à côte de deux années avec calcul des deltas ;
5. **Analyse de déforestation** : calcul automatique de la perte de couvert forestier entre deux dates ;
6. **Classement des forêts** : tri des forêts par superficie forestière ou stock de carbone ;
7. **Interrogation en langage naturel** : requêtes en français via le module Chat-to-Map ;
8. **Génération de rapports** : export de synthèses personnalisées ;
9. **Gestion des couches** : activation/désactivation des couches thématiques.

---

## 7.10 Rédaction des algorithmes d'analyse de données

### 7.10.1 Algorithme de calcul de la superficie

```
ALGORITHME CalculerSuperficie
ENTRÉE : geom (géométrie MultiPolygon, SRID 4326)
SORTIE : superficie_ha (réel)

DÉBUT
    // Transformation dans le système de projection UTM Zone 30N
    geom_utm ← ST_Transform(geom, 32630)

    // Calcul de l'aire en mètres carrés
    aire_m2 ← ST_Area(geom_utm)

    // Conversion en hectares
    superficie_ha ← aire_m2 / 10 000

    RETOURNER ARRONDI(superficie_ha, 2)
FIN
```

### 7.10.2 Algorithme de calcul du stock de carbone

```
ALGORITHME CalculerStockCarbone
ENTRÉE : type_couvert (chaîne), superficie_ha (réel)
SORTIE : stock_co2 (réel, en tCO₂/ha)

DÉBUT
    // Référentiel des valeurs de stock par type de couvert
    RÉFÉRENTIEL ← {
        FORET_DENSE   : 3 186,70 tCO₂/ha,
        FORET_CLAIRE  : 3 307,62 tCO₂/ha,
        FORET_DEGRADEE: 1 947,15 tCO₂/ha,
        JACHERE       : 2 906,42 tCO₂/ha,
        AUTRES        : 0 tCO₂/ha
    }

    stock_co2 ← RÉFÉRENTIEL[type_couvert]

    SI stock_co2 = INDÉFINI ALORS
        stock_co2 ← 0
    FIN SI

    RETOURNER stock_co2
FIN
```

### 7.10.3 Algorithme d'analyse de la déforestation

```
ALGORITHME AnalyserDeforestation
ENTRÉE : foret_code (chaîne), annee1 (entier), annee2 (entier)
SORTIE : résultat (dictionnaire)

DÉBUT
    // Types forestiers considérés
    TYPES_FORESTIERS ← [FORET_DENSE, FORET_CLAIRE, FORET_DEGRADEE]

    // Calcul de la superficie forestière pour chaque année
    superficie_1 ← SOMME(superficie_ha)
        OÙ foret.code = foret_code
        ET  nomenclature.code DANS TYPES_FORESTIERS
        ET  annee = annee1

    superficie_2 ← SOMME(superficie_ha)
        OÙ foret.code = foret_code
        ET  nomenclature.code DANS TYPES_FORESTIERS
        ET  annee = annee2

    // Calcul de la perte
    perte_ha ← superficie_1 - superficie_2
    perte_pct ← (perte_ha / superficie_1) × 100

    RETOURNER {
        annee1: annee1,
        annee2: annee2,
        superficie_foret_1: superficie_1,
        superficie_foret_2: superficie_2,
        perte_ha: perte_ha,
        perte_pct: perte_pct
    }
FIN
```

### 7.10.4 Algorithme du moteur NLP (Chat-to-Map)

```
ALGORITHME TraiterRequeteNLP
ENTRÉE : requete (chaîne en français)
SORTIE : résultat (GeoJSON | statistiques | comparaison)

DÉBUT
    // Étape 1 : Normalisation
    texte ← MINUSCULES(requete)
    texte_norm ← SUPPRIMER_ACCENTS(texte)

    // Étape 2 : Extraction d'entités
    forets ← []
    POUR CHAQUE (pattern, code) DANS PATTERNS_FORETS FAIRE
        SI REGEX_MATCH(pattern, texte) OU REGEX_MATCH(pattern, texte_norm) ALORS
            AJOUTER code À forets
        FIN SI
    FIN POUR

    types_couvert ← []
    POUR CHAQUE (pattern, code) DANS PATTERNS_COUVERT FAIRE
        SI REGEX_MATCH(pattern, texte) OU REGEX_MATCH(pattern, texte_norm) ALORS
            AJOUTER code À types_couvert
        FIN SI
    FIN POUR

    annees ← EXTRAIRE_NOMBRES(texte, pattern="\b(1986|2003|2023)\b")

    // Étape 3 : Détection d'intention (par priorité)
    intention ← "show"  // défaut

    SI MATCH(PATTERNS_SALUTATION, texte) ALORS
        intention ← "help"
    SINON SI MATCH(PATTERNS_COMPARAISON, texte) ALORS
        intention ← "compare"
    SINON SI MATCH(PATTERNS_DEFORESTATION, texte) ALORS
        intention ← "deforestation"
        SI annees EST VIDE ALORS
            annees ← [1986, 2023]
        FIN SI
    SINON SI MATCH(PATTERNS_STATISTIQUES, texte) ALORS
        intention ← "stats"
    SINON SI MATCH(PATTERNS_CARBONE, texte) ALORS
        intention ← "carbon"
    SINON SI MATCH(PATTERNS_CLASSEMENT, texte) ALORS
        intention ← "ranking"
    FIN SI

    // Étape 4 : Héritage de contexte de session
    SI forets EST VIDE ET contexte_session.forets EXISTE ALORS
        forets ← contexte_session.forets
    FIN SI
    SI annees EST VIDE ET contexte_session.annees EXISTE ALORS
        annees ← contexte_session.annees
    FIN SI

    // Étape 5 : Construction et exécution du filtre
    SELON intention FAIRE
        "help"          : RETOURNER aide_et_exemples()
        "compare"       : RETOURNER comparer(forets, types, annees)
        "deforestation" : RETOURNER analyser_deforestation(forets, annees)
        "stats"         : RETOURNER calculer_stats(forets, types, annees)
        "carbon"        : RETOURNER calculer_stats(forets, types, annees)
        "ranking"       : RETOURNER classer_forets(types, annees)
        "show"          : RETOURNER charger_geojson(forets, types, annees)
    FIN SELON
FIN
```

### 7.10.5 Algorithme de simplification géométrique adaptative

```
ALGORITHME SimplifierGéométrie
ENTRÉE : geom (géométrie), zoom (entier), type_couche (chaîne)
SORTIE : geom_simplifié (géométrie)

DÉBUT
    // Table de tolérance par niveau de zoom
    TOLÉRANCES ← {
        occupation : {7: 0.01, 8: 0.005, 10: 0.002, 12: 0.0008, 14: 0.0003},
        forets     : {7: 0.005, 10: 0.001, 12: 0.0003},
        zones      : {7: 0.005, 10: 0.001, 12: 0.0005}
    }

    // Sélection de la tolérance adaptée
    tolérance ← INTERPOLER(TOLÉRANCES[type_couche], zoom)

    // Validation puis simplification préservant la topologie
    geom_valide ← ST_MakeValid(geom)
    geom_polygones ← ST_CollectionExtract(geom_valide, 3)  // Polygones uniquement
    geom_simplifié ← ST_SimplifyPreserveTopology(geom_polygones, tolérance)

    RETOURNER geom_simplifié
FIN
```

---

## 7.11 Interface graphique

### 7.11.1 Interface d'administrateurs

L'interface d'administration est accessible via l'URL `/admin/` et est personnalisée avec le thème **Jazzmin** pour offrir une expérience de gestion moderne et intuitive.

**Fonctionnalités de l'interface d'administration :**

- **Gestion des forêts classées** : ajout, modification et suppression des entités géographiques des forêts avec prévisualisation cartographique ;
- **Gestion de l'occupation du sol** : import et édition des polygones d'occupation par année et par forêt ;
- **Gestion des nomenclatures** : administration du référentiel des types de couvert (codes, couleurs, valeurs de carbone) ;
- **Gestion des placettes** : saisie et modification des données de mesure terrain ;
- **Gestion des infrastructures** : import des données contextuelles (routes, hydrographie) ;
- **Import de données** : assistant d'import de fichiers géographiques (Shapefiles, GeoJSON) via l'URL `/backoffice/import/` ;
- **Tableau de bord** : synthèse des données disponibles via l'URL `/backoffice/` ;
- **Journalisation des requêtes IA** : consultation des requêtes Chat-to-Map enregistrées (texte, entités extraites, temps de traitement).

### 7.11.2 Interface d'utilisateurs

L'interface utilisateur principale est l'**interface cartographique interactive** accessible via l'URL `/carte/`. Elle se compose des éléments suivants :

**Zone cartographique (partie centrale) :**
- Carte interactive plein écran basée sur Leaflet.js ;
- Contrôles de zoom en bas à droite ;
- Navigation par glisser-déposer et molette de souris.

**Barre latérale gauche (Sidebar) avec quatre onglets :**

1. **Onglet « Couches »** :
   - Sélecteur de fond de carte (OSM, Satellite, Terrain) ;
   - Cases à cocher pour les couches thématiques (forêts, occupation, limites, placettes, routes, hydrographie, localités) ;
   - Sélecteur de forêt classée (filtre spatial) ;
   - Case à cocher pour l'occupation du sol avec indication de l'année courante.

2. **Onglet « Légende »** :
   - Liste des neuf types d'occupation du sol avec pastille de couleur, libellé et valeur de référence carbone.

3. **Onglet « Statistiques »** :
   - Cartes synthétiques : superficie totale, stock de carbone total, nombre de polygones ;
   - Tableau détaillé par type de couvert.

4. **Onglet « Rapport »** :
   - Formulaire de génération de rapport (titre, auteur, année, sections, notes).

**Curseur temporel (en bas) :**
- Barre de navigation entre les années 1986, 2003 et 2023 ;
- Bouton de lecture automatique (animation) ;
- Affichage de l'année courante.

**Panneau Chat-to-Map (panneau flottant à droite) :**
- Bouton d'ouverture (icône robot IA) ;
- Zone de saisie des requêtes en langage naturel ;
- Historique des échanges avec rendu HTML riche ;
- Tags d'entités reconnues (forêts, types, années, intention) ;
- Indicateur de frappe animé pendant le traitement.

**Barre de recherche IA (en haut de la sidebar) :**
- Champ de recherche rapide permettant de soumettre une requête IA directement depuis la sidebar sans ouvrir le panneau Chat-to-Map.

### 7.11.3 Les utilisateurs

L'application définit trois profils d'utilisateurs :

**1. Administrateur (superutilisateur)**
- Accès complet à l'interface d'administration Django ;
- Gestion des données géographiques (CRUD) ;
- Import de fichiers géographiques ;
- Configuration des nomenclatures et des valeurs de référence ;
- Consultation des journaux de requêtes IA.

**2. Utilisateur authentifié (chercheur / gestionnaire forestier)**
- Accès à l'interface cartographique interactive ;
- Utilisation de toutes les fonctionnalités de visualisation et d'analyse ;
- Utilisation du module Chat-to-Map ;
- Génération de rapports ;
- Consultation des statistiques et comparaisons temporelles.

**3. Utilisateur anonyme (visiteur)**
- Accès en lecture seule à l'interface cartographique ;
- Consultation de la carte et des couches d'occupation du sol ;
- Utilisation limitée du module Chat-to-Map ;
- Navigation entre les années d'observation.

L'authentification est gérée via le système d'authentification Django avec support JWT (JSON Web Token) pour les accès API programmatiques.

---

## 7.12 Conclusion partielle

Le développement de l'application **API.GEO.Carbone** représente une contribution méthodologique et technologique significative dans le cadre de cette thèse. En combinant les technologies géospatiales (PostGIS, Leaflet.js), les paradigmes de développement web moderne (API REST, architecture trois-tiers) et l'intelligence artificielle (traitement du langage naturel), cette application offre un outil opérationnel pour la gestion et le suivi des foyers de stock de carbone forestier du département d'Oumé.

Les principaux apports méthodologiques sont :

1. **Une architecture de performance optimisée** permettant le rendu de milliers de polygones en temps réel grâce au système de cache à deux niveaux (statique < 50 ms, dynamique 200-3 000 ms) et au rendu Canvas double-bufferé ;

2. **Un modèle de données normalisé** (3NF) intégrant les dimensions spatiale, temporelle et thématique, avec des calculs automatiques de superficie (projection UTM 30N) et de stock de carbone ;

3. **Un module d'intelligence artificielle innovant** (Chat-to-Map) permettant l'interrogation des données en langage naturel français, avec mémoire conversationnelle et détection d'intentions multiples ;

4. **Une API REST géographique complète** exposant l'ensemble des données au format GeoJSON (RFC 7946), compatible avec les standards de l'écosystème géospatial ;

5. **Une interface cartographique interactive et accessible** offrant des outils de visualisation multi-temporelle, d'analyse comparative et de génération de rapports, utilisables par des non-spécialistes en SIG.

Cette application constitue un prototype opérationnel démontrant la faisabilité d'un système d'information géographique dédié au suivi du carbone forestier à l'échelle départementale. Les perspectives d'évolution incluent l'intégration de modèles prédictifs, l'extension à d'autres départements et l'alignement avec les méthodologies REDD+ pour contribuer aux efforts nationaux et internationaux de lutte contre le changement climatique.

---

*Application développée dans le cadre de la thèse : « Apport de la géomatique dans la lutte contre la réduction des foyers de stocks de carbone forestiers en milieu tropical : cas des réserves forestières du département d'OUMÉ (Côte d'Ivoire) ».*
