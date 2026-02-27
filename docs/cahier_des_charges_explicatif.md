# CAHIER DES CHARGES EXPLICATIF
# Application API.GEO.Carbone
## Plateforme Web SIG pour la gestion des forêts et des foyers de stock de carbone du département d'Oumé (Côte d'Ivoire)

---

## 1. PRÉSENTATION DU PROJET

### 1.1 Contexte

Le département d'Oumé, situé dans la région du Gôh au centre-ouest de la Côte d'Ivoire, abrite six forêts classées représentant un patrimoine forestier de 81 056 hectares. Ces réserves forestières constituent d'importants foyers de stock de carbone dont le suivi est essentiel dans le contexte de la lutte contre le changement climatique.

Face à la pression anthropique croissante (agriculture extensive, culture du cacao, exploitation forestière), ces forêts subissent une dégradation progressive qui entraîne une réduction des stocks de carbone forestier. La quantification et le suivi de cette dynamique nécessitent des outils géomatiques adaptés.

### 1.2 Objectif général

Développer une application Web SIG nommée **API.GEO.Carbone** permettant de centraliser, visualiser et analyser les données spatio-temporelles relatives à l'occupation du sol et aux stocks de carbone des six forêts classées du département d'Oumé.

### 1.3 Objectifs spécifiques

1. **Cartographier** l'évolution de l'occupation du sol des forêts classées sur trois époques (1986, 2003, 2023) à partir de données de télédétection ;
2. **Quantifier** les superficies et les stocks de carbone par type d'occupation du sol et par forêt classée ;
3. **Analyser** la dynamique de déforestation et la perte de stock de carbone entre les différentes époques ;
4. **Faciliter** l'accès aux données géospatiales grâce à une interface cartographique interactive et un assistant IA en langage naturel ;
5. **Produire** des rapports et des statistiques exploitables pour l'aide à la décision en matière de gestion forestière.

---

## 2. PÉRIMÈTRE FONCTIONNEL

### 2.1 Zone géographique

| Élément | Détail |
|---------|--------|
| Département | Oumé |
| Région | Gôh |
| Pays | Côte d'Ivoire |
| Coordonnées centrales | 6,5° N / 5,5° O |
| Système de coordonnées | WGS 84 (EPSG:4326) |
| Projection de calcul | UTM Zone 30N (EPSG:32630) |

### 2.2 Forêts classées couvertes

Le périmètre du projet englobe les six forêts classées du département d'Oumé :

1. **Forêt Classée de TENÉ** (29 549 ha) — La plus grande du département, située au nord-est ;
2. **Forêt Classée de SANGOUÉ** (27 360 ha) — Deuxième plus grande, située au nord-ouest ;
3. **Forêt Classée de DOKA** (10 945 ha) — Située au sud-est du département ;
4. **Forêt Classée de ZOUÉKÉ Bloc I** (6 825 ha) — Située à l'est ;
5. **Forêt Classée de LAHOUDA** (3 300 ha) — Située au sud-ouest ;
6. **Forêt Classée de ZOUÉKÉ Bloc II** (3 077 ha) — Bloc complémentaire de ZOUÉKÉ.

### 2.3 Périodes temporelles

L'application couvre trois périodes d'observation correspondant à trois jeux de données satellitaires :

- **1986** : état de référence historique (image Landsat TM, résolution 30 m) ;
- **2003** : état intermédiaire (image Landsat ETM+, résolution 30 m) ;
- **2023** : état actuel (image Sentinel-2, résolution 10 m).

---

## 3. DESCRIPTION FONCTIONNELLE

### 3.1 Module de visualisation cartographique

**Objectif** : Permettre la visualisation interactive des données d'occupation du sol sur une carte web.

**Fonctionnalités :**

| Réf. | Fonctionnalité | Description | Priorité |
|------|---------------|-------------|----------|
| F01 | Affichage de la carte | Carte interactive centrée sur le département d'Oumé | Haute |
| F02 | Fonds de carte | Choix entre OpenStreetMap, Satellite ESRI, Terrain | Haute |
| F03 | Couches d'occupation | Affichage des polygones colorés par type de couvert | Haute |
| F04 | Limites des forêts | Contours des six forêts classées (trait vert pointillé) | Haute |
| F05 | Navigation temporelle | Curseur pour basculer entre 1986, 2003 et 2023 | Haute |
| F06 | Animation temporelle | Lecture automatique de la séquence temporelle | Moyenne |
| F07 | Filtrage par forêt | Sélection d'une forêt spécifique via menu déroulant | Haute |
| F08 | Popups informatifs | Au clic : type de couvert, superficie, carbone, source | Haute |
| F09 | Limites administratives | Contours du département et des sous-préfectures | Moyenne |
| F10 | Placettes de mesure | Points de mesure terrain avec données de biomasse | Moyenne |
| F11 | Réseau routier | Tracé des routes principales et secondaires | Basse |
| F12 | Hydrographie | Tracé des cours d'eau | Basse |
| F13 | Localités | Points des chefs-lieux et localités | Basse |

### 3.2 Module statistique

**Objectif** : Fournir des statistiques agrégées sur l'occupation du sol et le carbone.

| Réf. | Fonctionnalité | Description | Priorité |
|------|---------------|-------------|----------|
| F14 | Statistiques par type | Superficie et carbone par type de couvert | Haute |
| F15 | Comparaison temporelle | Tableau comparatif entre deux années avec deltas | Haute |
| F16 | Analyse de déforestation | Calcul de la perte forestière en hectares et pourcentage | Haute |
| F17 | Classement des forêts | Tri des forêts par superficie forestière ou carbone | Moyenne |
| F18 | Synthèse par forêt | Statistiques détaillées pour une forêt sélectionnée | Moyenne |

### 3.3 Module Chat-to-Map (Intelligence Artificielle)

**Objectif** : Permettre l'interrogation des données en langage naturel français.

| Réf. | Fonctionnalité | Description | Priorité |
|------|---------------|-------------|----------|
| F19 | Saisie en langage naturel | Champ de texte pour requêtes en français | Haute |
| F20 | Extraction d'entités | Reconnaissance des forêts, types de couvert, années | Haute |
| F21 | Détection d'intention | Identification du type de requête (stats, comparaison, etc.) | Haute |
| F22 | Affichage sur carte | Rendu des résultats GeoJSON sur la carte | Haute |
| F23 | Affichage tabulaire | Rendu des statistiques en tableau HTML | Haute |
| F24 | Mémoire de session | Héritage du contexte de la requête précédente | Moyenne |
| F25 | Suggestions | Propositions de requêtes si aucun résultat | Moyenne |
| F26 | Tags d'entités | Affichage visuel des entités reconnues | Basse |

### 3.4 Module de rapports

| Réf. | Fonctionnalité | Description | Priorité |
|------|---------------|-------------|----------|
| F27 | Formulaire de rapport | Saisie du titre, auteur, année, sections | Moyenne |
| F28 | Génération | Production d'un rapport formaté | Moyenne |
| F29 | Export | Téléchargement du rapport | Basse |

### 3.5 Module d'administration

| Réf. | Fonctionnalité | Description | Priorité |
|------|---------------|-------------|----------|
| F30 | Gestion des forêts | CRUD sur les entités ForetClassee | Haute |
| F31 | Gestion de l'occupation | CRUD sur les entités OccupationSol | Haute |
| F32 | Gestion des nomenclatures | Administration du référentiel | Haute |
| F33 | Import de données | Assistant d'import de fichiers géographiques | Haute |
| F34 | Journal des requêtes IA | Consultation des requêtes NLP enregistrées | Basse |

---

## 4. EXIGENCES NON FONCTIONNELLES

### 4.1 Performance

| Exigence | Objectif |
|----------|---------|
| Temps de chargement initial de la carte | < 3 secondes |
| Temps de réponse du cache statique | < 100 ms |
| Temps de changement d'année (après préchargement) | < 50 ms |
| Temps de traitement d'une requête NLP | < 500 ms |
| Nombre maximal de polygones affichés simultanément | > 20 000 |
| Taille maximale d'un fichier GeoJSON cache | < 3 MB |

### 4.2 Ergonomie

- Interface responsive adaptée aux écrans de bureau (1280px minimum) ;
- Navigation intuitive par onglets dans la barre latérale ;
- Curseur temporel avec affichage clair de l'année sélectionnée ;
- Légende visible et compréhensible avec codes couleur ;
- Messages d'erreur explicites en français ;
- Exemples de requêtes cliquables dans le Chat-to-Map.

### 4.3 Fiabilité

- Calcul automatique des superficies via projection UTM 30N (précision < 1%) ;
- Validation des géométries (ST_MakeValid) avant tout traitement ;
- Extraction des polygones uniquement (ST_CollectionExtract) pour éviter les artefacts géométriques ;
- Système de fallback : si le cache statique est absent, la requête SQL dynamique prend le relais.

### 4.4 Sécurité

- Protection contre l'injection SQL via l'ORM Django ;
- Échappement HTML contre les attaques XSS ;
- Authentification requise pour les opérations d'écriture ;
- Token CSRF obligatoire sur les requêtes POST.

### 4.5 Maintenabilité

- Code modulaire organisé en applications Django spécialisées ;
- API REST documentée et auto-descriptive ;
- Commandes de gestion pour l'import et le cache ;
- Nomenclatures et coefficients centralisés dans un fichier unique (`constants.py`).

---

## 5. DONNÉES D'ENTRÉE

### 5.1 Données satellitaires

| Année | Capteur | Résolution | Bandes utilisées | Classification |
|-------|---------|-----------|------------------|----------------|
| 1986 | Landsat 5 TM | 30 m | B1-B7 | Supervisée (maximum de vraisemblance) |
| 2003 | Landsat 7 ETM+ | 30 m | B1-B8 | Supervisée (maximum de vraisemblance) |
| 2023 | Sentinel-2 MSI | 10 m | B2-B12 | Supervisée (Random Forest) |

### 5.2 Données de terrain

- **Placettes de mesure** : points GPS avec mesures de biomasse aérienne et souterraine ;
- **Inventaires forestiers** : type de forêt observé, diamètre des arbres, hauteur ;
- **Données de stock de carbone** : valeurs mesurées en tCO₂/ha par type de couvert.

### 5.3 Données contextuelles

- **Limites administratives** : département d'Oumé, sous-préfectures ;
- **Réseau routier** : routes nationales, départementales et pistes ;
- **Hydrographie** : cours d'eau principaux et secondaires ;
- **Localités** : chefs-lieux de sous-préfecture et localités.

### 5.4 Nomenclature d'occupation du sol

La classification retenue distingue 9 classes d'occupation :

**Classes forestières (foyers de stock de carbone) :**
- Forêt dense (couvert arboré > 70%, canopée fermée)
- Forêt claire (couvert arboré 40-70%, canopée ouverte)
- Forêt dégradée (couvert arboré < 40%, perturbations visibles)
- Jachère / Reboisement jeune (végétation en régénération)

**Classes non forestières :**
- Cacao (plantations cacaoyères)
- Café (plantations caféières)
- Hévéa (plantations d'hévéa)
- Culture annuelle / Herbacée (cultures vivrières, pâturages)
- Sol nu (surfaces sans végétation)

---

## 6. LIVRABLES ATTENDUS

| N° | Livrable | Format | Description |
|----|----------|--------|-------------|
| L1 | Application web | Déployée | Application API.GEO.Carbone fonctionnelle |
| L2 | Base de données | PostgreSQL/PostGIS | Base peuplée avec les données des 3 époques |
| L3 | Cache GeoJSON | Fichiers JSON | Fichiers pré-calculés pour chargement rapide |
| L4 | API REST | HTTP/JSON | Endpoints documentés et fonctionnels |
| L5 | Module Chat-to-Map | Intégré | Assistant IA en langage naturel |
| L6 | Documentation technique | Markdown | Cahier des charges technique |
| L7 | Documentation explicative | Markdown | Cahier des charges explicatif |
| L8 | Chapitre de thèse | Markdown | Chapitre 7 — Méthode de développement |

---

## 7. ACTEURS DU SYSTÈME

### 7.1 Diagramme des acteurs

```
                    ┌───────────────────┐
                    │   API.GEO.Carbone │
                    │    (Application)   │
                    └─────┬──────┬──────┘
                          │      │
              ┌───────────┘      └───────────┐
              │                              │
    ┌─────────┴─────────┐        ┌──────────┴──────────┐
    │   Administrateur   │        │     Utilisateur      │
    │   (Chercheur       │        │     (Gestionnaire    │
    │    principal)      │        │      forestier /     │
    │                    │        │      Décideur)       │
    │  • Importer données│        │                      │
    │  • Gérer nomencl.  │        │  • Visualiser carte  │
    │  • Configurer      │        │  • Interroger IA     │
    │  • Tout utilisateur│        │  • Consulter stats   │
    └────────────────────┘        │  • Générer rapports  │
                                  └──────────────────────┘
                                          │
                              ┌───────────┘
                              │
                    ┌─────────┴─────────┐
                    │     Visiteur       │
                    │    (Anonyme)       │
                    │                    │
                    │  • Visualiser carte│
                    │  • Naviguer temps  │
                    │  • Consulter stats │
                    └────────────────────┘
```

**Figure 1** — Diagramme des acteurs du système.

### 7.2 Cas d'utilisation principaux

| Acteur | Cas d'utilisation | Description |
|--------|------------------|-------------|
| Visiteur | Consulter la carte | Visualiser l'occupation du sol pour une année donnée |
| Visiteur | Naviguer dans le temps | Changer d'année via le curseur temporel |
| Utilisateur | Interroger l'IA | Poser une question en français via Chat-to-Map |
| Utilisateur | Comparer deux époques | Analyser l'évolution entre deux dates |
| Utilisateur | Analyser la déforestation | Quantifier la perte forestière |
| Utilisateur | Générer un rapport | Produire une synthèse personnalisée |
| Administrateur | Importer des données | Charger de nouvelles couches géographiques |
| Administrateur | Gérer les nomenclatures | Modifier les types de couvert et leurs valeurs |
| Administrateur | Régénérer le cache | Mettre à jour les fichiers GeoJSON pré-calculés |

---

## 8. CONTRAINTES

### 8.1 Contraintes techniques

- La base de données doit supporter l'extension PostGIS pour le traitement spatial ;
- Les géométries doivent être stockées en WGS 84 (EPSG:4326) pour la compatibilité avec les standards web ;
- Le rendu cartographique doit supporter au moins 20 000 polygones simultanément ;
- Le module NLP fonctionne exclusivement en français.

### 8.2 Contraintes de données

- Les données satellitaires sont limitées aux trois dates disponibles (1986, 2003, 2023) ;
- La précision des données de 1986 et 2003 (30 m) est inférieure à celle de 2023 (10 m) ;
- Les valeurs de biomasse et de carbone sont des valeurs de référence moyennes par type de couvert, et non des mesures individuelles par polygone.

### 8.3 Contraintes organisationnelles

- Le projet est développé dans le cadre d'une thèse de doctorat ;
- L'application doit être utilisable par des non-spécialistes en SIG (gestionnaires forestiers, décideurs) ;
- La documentation doit être rédigée en français.

---

## 9. GLOSSAIRE

| Terme | Définition |
|-------|-----------|
| **API REST** | Interface de programmation basée sur le protocole HTTP pour l'échange de données |
| **Biomasse** | Masse totale de matière organique vivante dans un écosystème (en tonnes/hectare) |
| **Canvas** | Moteur de rendu graphique HTML5 pour le dessin haute performance |
| **Cache GeoJSON** | Fichiers JSON pré-calculés contenant les géométries simplifiées |
| **Chat-to-Map** | Module d'intelligence artificielle permettant l'interrogation en langage naturel |
| **Classification supervisée** | Méthode de télédétection où l'algorithme apprend à partir d'échantillons d'entraînement |
| **Django** | Framework web Python suivant le patron Model-Template-View (MTV) |
| **GeoJSON** | Format de données géographiques basé sur JSON (RFC 7946) |
| **Leaflet** | Bibliothèque JavaScript open source pour les cartes interactives |
| **NLP** | Natural Language Processing — Traitement du langage naturel |
| **ORM** | Object-Relational Mapping — Correspondance objet-relationnel |
| **PostGIS** | Extension spatiale de PostgreSQL pour le traitement de données géographiques |
| **REDD+** | Mécanisme de réduction des émissions liées à la déforestation et à la dégradation |
| **Sentinel-2** | Constellation de satellites d'observation de la Terre de l'ESA (résolution 10 m) |
| **SIG** | Système d'Information Géographique |
| **Stock de carbone** | Quantité de carbone séquestrée dans un écosystème (en tCO₂/ha) |
| **tCO₂/ha** | Tonnes de dioxyde de carbone équivalent par hectare |
| **UTM** | Universal Transverse Mercator — Système de projection cartographique |
| **WGS 84** | World Geodetic System 1984 — Système géodésique de référence mondial |
