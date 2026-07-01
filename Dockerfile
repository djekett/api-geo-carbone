# ===== API.GEO.Carbone — Image de production (Railway / tout hôte Docker) =====
# GeoDjango nécessite GDAL / GEOS / PROJ au niveau système : on les installe ici
# (contrairement à Render où build.sh les installait via apt). Railway construit
# cette image sur ses serveurs — aucun Docker requis en local.
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    DJANGO_SETTINGS_MODULE=config.settings.production

# Dépendances système : GDAL/GEOS/PROJ pour GeoDjango + client Postgres.
RUN apt-get update && apt-get install -y --no-install-recommends \
        gdal-bin \
        libgdal-dev \
        libgeos-dev \
        libproj-dev \
        binutils \
        libpq5 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Couche de dépendances (mise en cache tant que requirements.txt ne change pas).
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Code applicatif.
COPY . .

# Fichiers statiques (ne nécessite pas la base de données).
RUN python manage.py collectstatic --no-input

RUN chmod +x docker-entrypoint.sh

# Railway fournit $PORT ; défaut 8000 en local.
EXPOSE 8000
CMD ["./docker-entrypoint.sh"]
