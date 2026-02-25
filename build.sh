#!/usr/bin/env bash
# ===== Script de build pour Render =====
set -o errexit

# Installer les dependances systeme pour GeoDjango (GDAL, GEOS, PROJ)
apt-get update && apt-get install -y --no-install-recommends \
    gdal-bin \
    libgdal-dev \
    libgeos-dev \
    libproj-dev \
    && rm -rf /var/lib/apt/lists/*

# Installer les dependances Python
pip install --upgrade pip
pip install -r requirements.txt

# Activer extension PostGIS sur la base de donnees
python -c "
import dj_database_url, psycopg2, os
db = dj_database_url.config(default=os.environ.get('DATABASE_URL'))
conn = psycopg2.connect(
    dbname=db['NAME'], user=db['USER'],
    password=db['PASSWORD'], host=db['HOST'], port=db['PORT']
)
conn.autocommit = True
cur = conn.cursor()
cur.execute('CREATE EXTENSION IF NOT EXISTS postgis;')
print('PostGIS extension activated.')
conn.close()
"

# Appliquer les migrations
python manage.py migrate --no-input

# Collecter les fichiers statiques
python manage.py collectstatic --no-input

# ===== IMPORT OCCUPATIONS DU SOL UNIQUEMENT (temporaire) =====
echo "============================================================"
echo "IMPORTING LAND COVER DATA (occupations only)..."
echo "============================================================"
python manage.py import_from_url "https://drive.google.com/file/d/1h11UM_rd35tsTtZWYsiV_J7LxL2JFJfG/view?usp=sharing" \
    --only occupations || echo "WARNING: Occupations import failed (non-blocking)"

# Rebuild GeoJSON cache separement
echo "Rebuilding GeoJSON cache..."
python manage.py prebuild_geojson --clear || echo "WARNING: Cache rebuild failed (non-blocking)"
