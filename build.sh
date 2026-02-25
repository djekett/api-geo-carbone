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

# ===== Auto-creation superuser depuis variables d'environnement =====
python -c "
import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
django.setup()
from django.contrib.auth import get_user_model
User = get_user_model()
username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@admin.com')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')
if password and not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username=username, email=email, password=password)
    print(f'Superuser {username} created.')
else:
    print('Superuser already exists or no password set.')
"
