# Déploiement sur Railway + Neon

Remplace l'hébergement Render. **Aucun Docker requis en local** : Railway
construit l'image à partir du `Dockerfile` sur ses serveurs.

## Architecture
- **Base de données** : Neon (Postgres + PostGIS, gratuit, n'expire pas). Déjà utilisée.
- **Application** : Railway (build via `Dockerfile`, qui installe GDAL/GEOS/PROJ).

## 1. Base Neon (une seule fois)
1. Sur https://neon.tech, créez un projet Postgres.
2. Activez PostGIS : dans le SQL Editor Neon, exécutez `CREATE EXTENSION IF NOT EXISTS postgis;`
3. Récupérez la chaîne de connexion (format
   `postgresql://user:pass@host/db?sslmode=require`) → ce sera `DATABASE_URL`.

## 2. Remplir Neon avec les données (depuis votre PC)
Les shapefiles ne sont pas déployés ; on remplit Neon en lançant les imports en
local mais en pointant la base vers Neon :

```bat
:: Depuis C:\Users\PC 2\Music\api-geo-carbone, venv activé
set DJANGO_SETTINGS_MODULE=config.settings.production
set DATABASE_URL=postgresql://USER:PASS@HOST/DB?sslmode=require

venv\Scripts\python manage.py migrate --no-input
venv\Scripts\python manage.py seed_nomenclature
venv\Scripts\python manage.py import_forets
venv\Scripts\python manage.py import_zones
venv\Scripts\python manage.py import_occupations
venv\Scripts\python manage.py import_placettes
venv\Scripts\python manage.py import_infrastructure
venv\Scripts\python manage.py import_stock_carbone --shapefile "C:\Users\PC 2\Music\DATA YEO ALL\SIG_DATA\data_carb.shp"
venv\Scripts\python manage.py prebuild_geojson
```

> Le calcul des superficies utilise désormais PostGIS (`ST_Area(::geography)`),
> qui fonctionne aussi bien en local que sur Neon.

## 3. Déployer sur Railway
1. Sur https://railway.app → **New Project → Deploy from GitHub repo** (sélectionnez ce dépôt).
2. Railway détecte le `Dockerfile` et `railway.json`.
3. Dans **Variables**, définissez :

| Variable | Valeur |
|---|---|
| `DJANGO_SETTINGS_MODULE` | `config.settings.production` |
| `DATABASE_URL` | *(chaîne Neon, sslmode=require)* |
| `SECRET_KEY` | *(une longue chaîne aléatoire)* |
| `MISTRAL_API_KEY` | *(votre clé Mistral)* |
| `ALLOWED_HOSTS` | *(optionnel — le domaine Railway est déjà géré)* |
| `DJANGO_SUPERUSER_USERNAME` | `admin` *(optionnel)* |
| `DJANGO_SUPERUSER_EMAIL` | `admin@exemple.com` *(optionnel)* |
| `DJANGO_SUPERUSER_PASSWORD` | *(mot de passe admin)* *(optionnel)* |

4. Railway build + déploie. `RAILWAY_PUBLIC_DOMAIN` est fourni automatiquement et
   déjà pris en compte dans `ALLOWED_HOSTS` / CORS / CSRF (voir `config/settings/production.py`).

## Notes
- Le `docker-entrypoint.sh` lance `migrate`, `seed_nomenclature`, reconstruit le
  cache GeoJSON si la base contient des données, crée le superuser si fourni,
  puis démarre gunicorn.
- Si vous gardez Neon rempli (étape 2), le cache sera reconstruit à chaque déploiement.
