@echo off
echo ============================================
echo    API.GEO.Carbone — Setup environnement
echo ============================================
echo.

REM Créer l'environnement virtuel
echo [1/4] Création de l'environnement virtuel...
python -m venv venv
call venv\Scripts\activate.bat

REM Installer les dépendances
echo [2/4] Installation des dépendances...
pip install --upgrade pip
pip install -r requirements.txt

REM Copier le fichier .env
echo [3/4] Configuration...
if not exist .env (
    copy .env.example .env
    echo    → Fichier .env créé. Éditez-le avec vos paramètres.
) else (
    echo    → Fichier .env existant conservé.
)

REM Compiler Tailwind CSS
echo [4/4] Build Tailwind CSS...
npx tailwindcss -i frontend/static/css/tailwind-input.css -o frontend/static/css/tailwind-output.css --minify 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo    → Tailwind CLI non installé. Installez Node.js puis: npm install -D tailwindcss
    echo    → Le projet fonctionnera avec le CDN Tailwind en mode développement.
)

echo.
echo ============================================
echo    Setup terminé !
echo    Activez le venv: venv\Scripts\activate
echo    Lancez le serveur: python manage.py runserver
echo ============================================
pause
