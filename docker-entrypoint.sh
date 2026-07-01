#!/usr/bin/env bash
# ===== Démarrage du conteneur (la base Neon est joignable à ce moment) =====
set -o errexit

echo ">> Migrations..."
python manage.py migrate --no-input

echo ">> Seed nomenclature (idempotent)..."
python manage.py seed_nomenclature || echo "   (nomenclature déjà présente)"

# Reconstruire le cache GeoJSON UNIQUEMENT si la base contient des occupations.
# Sinon on garde les fichiers media/geocache/*.json commités (sinon carte vide).
echo ">> Vérification des données pour le cache GeoJSON..."
python - <<'PY' || echo "   (prebuild ignoré)"
import os, sys, subprocess, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
django.setup()
from apps.carbone.models import OccupationSol
n = OccupationSol.objects.count()
if n > 0:
    print(f"   {n} occupations en base -> reconstruction du cache")
    subprocess.run([sys.executable, 'manage.py', 'prebuild_geojson'], check=False)
else:
    print("   base vide -> cache commité conservé")
PY

# Superuser optionnel (créé seulement si DJANGO_SUPERUSER_PASSWORD est défini).
python - <<'PY' || true
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
django.setup()
from django.contrib.auth import get_user_model
User = get_user_model()
u = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
e = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@admin.com')
p = os.environ.get('DJANGO_SUPERUSER_PASSWORD')
if p and not User.objects.filter(username=u).exists():
    User.objects.create_superuser(username=u, email=e, password=p)
    print(f">> Superuser '{u}' créé.")
else:
    print(">> Superuser déjà présent ou aucun mot de passe fourni.")
PY

echo ">> Lancement de gunicorn sur le port ${PORT:-8000}..."
exec gunicorn config.wsgi:application \
    --bind "0.0.0.0:${PORT:-8000}" \
    --workers 3 \
    --timeout 120
