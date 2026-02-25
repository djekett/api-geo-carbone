"""
Import all geographic data from a remote ZIP archive.

Downloads a ZIP file containing shapefiles, extracts it to a temporary
directory, then runs all import commands in the correct order.

Expected ZIP structure (matching your local DATA YEO ALL folder):
  DATA/
    SIG_DATA/
      Limite_Tene.shp (+.dbf, .shx, .prj)
      Limite_Doka.shp
      Limite_Sangoue.shp
      Limite_Lahouda.shp
      Limite_Zuoke.shp
      Limite_Zuoke2.shp
      Limite_Oume.shp (or Limite_Oume.shp)
      Limite_SP.shp
      Placettes.shp
      Routes_Oume.shp
      Reseau_hidrographique_Oume.shp
      Chef_lieu_sous_prefecture.shp
      Localites_departement_Oume.shp
    1986/
      Foret_dense86.shp, Foret_claire86.shp, ...
    2003/
      Foret_dense03.shp, Foret_claire03.shp, ...
    2023/
      Foret_dense23.shp, Foret_claire23.shp, ...

Usage:
  python manage.py import_from_url "https://drive.google.com/uc?id=FILE_ID&export=download"
  python manage.py import_from_url "https://example.com/data.zip"
  python manage.py import_from_url --local /tmp/data.zip
"""
import os
import re
import tempfile
import zipfile

from django.core.management.base import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):
    help = 'Import all geographic data from a remote or local ZIP archive'

    def add_arguments(self, parser):
        parser.add_argument(
            'url',
            nargs='?',
            help='URL of the ZIP archive (Google Drive, Dropbox, GitHub, etc.)',
        )
        parser.add_argument(
            '--local',
            help='Path to a local ZIP file (skip download)',
        )
        parser.add_argument(
            '--skip-nomenclature',
            action='store_true',
            help='Skip nomenclature seeding',
        )
        parser.add_argument(
            '--skip-occupations',
            action='store_true',
            help='Skip land cover occupation import',
        )
        parser.add_argument(
            '--skip-cache',
            action='store_true',
            help='Skip GeoJSON cache generation',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before import',
        )

    def handle(self, *args, **options):
        url = options.get('url')
        local_path = options.get('local')

        if not url and not local_path:
            self.stderr.write(self.style.ERROR(
                'Provide a URL or --local path. Example:\n'
                '  python manage.py import_from_url "https://example.com/data.zip"\n'
                '  python manage.py import_from_url --local /tmp/data.zip'
            ))
            return

        with tempfile.TemporaryDirectory() as tmpdir:
            # Step 1: Get the ZIP file
            if local_path:
                zip_path = local_path
                self.stdout.write(f'Using local file: {zip_path}')
            else:
                zip_path = os.path.join(tmpdir, 'data.zip')
                self._download(url, zip_path)

            if not os.path.exists(zip_path):
                self.stderr.write(self.style.ERROR(f'File not found: {zip_path}'))
                return

            # Step 2: Extract
            extract_dir = os.path.join(tmpdir, 'extracted')
            self.stdout.write(f'\n{"="*60}')
            self.stdout.write('EXTRACTING ZIP...')
            self.stdout.write(f'{"="*60}')
            with zipfile.ZipFile(zip_path, 'r') as z:
                z.extractall(extract_dir)
                self.stdout.write(f'Extracted {len(z.namelist())} files')

            # Step 3: Find the data root (detect folder structure)
            data_root = self._find_data_root(extract_dir)
            sig_data_dir = self._find_sig_data(data_root)

            self.stdout.write(f'\nData root: {data_root}')
            self.stdout.write(f'SIG_DATA dir: {sig_data_dir}')

            # List what we found
            self._list_found_files(data_root, sig_data_dir)

            # Step 4: Run imports in order
            self.stdout.write(f'\n{"="*60}')
            self.stdout.write('RUNNING IMPORTS...')
            self.stdout.write(f'{"="*60}')

            # 4a. Seed nomenclature (no files needed)
            if not options['skip_nomenclature']:
                self.stdout.write(f'\n--- seed_nomenclature ---')
                call_command('seed_nomenclature', stdout=self.stdout)

            # 4b. Import forest boundaries
            self.stdout.write(f'\n--- import_forets ---')
            call_command('import_forets', data_dir=sig_data_dir, stdout=self.stdout)

            # 4c. Import administrative zones
            self.stdout.write(f'\n--- import_zones ---')
            call_command(
                'import_zones',
                data_dir=sig_data_dir,
                generate_fallback=True,
                stdout=self.stdout,
            )

            # 4d. Import land cover occupations
            if not options['skip_occupations']:
                self.stdout.write(f'\n--- import_occupations ---')
                call_command(
                    'import_occupations',
                    data_dir=data_root,
                    clear=options['clear'],
                    stdout=self.stdout,
                )

            # 4e. Import placettes
            self.stdout.write(f'\n--- import_placettes ---')
            call_command('import_placettes', data_dir=sig_data_dir, stdout=self.stdout)

            # 4f. Import infrastructure
            self.stdout.write(f'\n--- import_infrastructure ---')
            call_command('import_infrastructure', data_dir=sig_data_dir, stdout=self.stdout)

            # 4g. Pre-build GeoJSON cache
            if not options['skip_cache']:
                self.stdout.write(f'\n--- prebuild_geojson ---')
                call_command('prebuild_geojson', clear=True, stdout=self.stdout)

        self.stdout.write(f'\n{"="*60}')
        self.stdout.write(self.style.SUCCESS('ALL IMPORTS COMPLETE!'))
        self.stdout.write(f'{"="*60}')

    def _download(self, url, dest_path):
        """Download a file from URL, handling Google Drive and Dropbox links."""
        self.stdout.write(f'\n{"="*60}')
        self.stdout.write(f'DOWNLOADING...')
        self.stdout.write(f'{"="*60}')

        # Google Drive: use gdown (handles confirmation pages & large files)
        gdrive_match = re.search(r'drive\.google\.com/file/d/([^/]+)', url)
        gdrive_uc_match = re.search(r'drive\.google\.com/uc\?id=([^&]+)', url)
        file_id = None
        if gdrive_match:
            file_id = gdrive_match.group(1)
        elif gdrive_uc_match:
            file_id = gdrive_uc_match.group(1)

        if file_id:
            self.stdout.write(f'Google Drive file ID: {file_id}')
            try:
                import gdown
            except ImportError:
                self.stdout.write('Installing gdown...')
                import subprocess
                subprocess.check_call(['pip', 'install', 'gdown'])
                import gdown

            gdrive_url = f'https://drive.google.com/uc?id={file_id}'
            self.stdout.write(f'Downloading with gdown...')
            gdown.download(gdrive_url, dest_path, quiet=False, fuzzy=True)
        else:
            # Dropbox: convert to direct download
            if 'dropbox.com' in url:
                url = url.replace('dl=0', 'dl=1').replace(
                    'www.dropbox.com', 'dl.dropboxusercontent.com'
                )

            # Generic URL download
            self.stdout.write(f'URL: {url}')
            import urllib.request
            import ssl
            ctx = ssl.create_default_context()
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (compatible; API.GEO.Carbone/1.0)',
            })
            with urllib.request.urlopen(req, context=ctx) as response:
                with open(dest_path, 'wb') as f:
                    while True:
                        chunk = response.read(1024 * 1024)
                        if not chunk:
                            break
                        f.write(chunk)

        file_size = os.path.getsize(dest_path)
        self.stdout.write(self.style.SUCCESS(
            f'Downloaded: {file_size / (1024*1024):.1f} MB'
        ))

        if file_size < 1000:
            self.stderr.write(self.style.ERROR(
                f'File too small ({file_size} bytes) - likely an error page, not the ZIP.'
            ))
            raise ValueError('Downloaded file is too small, check URL permissions.')

    def _find_data_root(self, extract_dir):
        """Find the actual data root inside the extracted archive."""
        # Check if there's a single subdirectory (common with ZIP files)
        entries = [e for e in os.listdir(extract_dir) if not e.startswith('.')]
        if len(entries) == 1:
            single_entry = os.path.join(extract_dir, entries[0])
            if os.path.isdir(single_entry):
                # Check if this subdirectory contains the actual data
                sub_entries = os.listdir(single_entry)
                if 'SIG_DATA' in sub_entries or '1986' in sub_entries or '2023' in sub_entries:
                    return single_entry

        # Check if data is directly in extract_dir
        if 'SIG_DATA' in entries or '1986' in entries or '2023' in entries:
            return extract_dir

        # Deep search: look for SIG_DATA folder anywhere
        for root, dirs, files in os.walk(extract_dir):
            if 'SIG_DATA' in dirs:
                return root
            # Check for year folders
            if '1986' in dirs and '2023' in dirs:
                return root

        return extract_dir

    def _find_sig_data(self, data_root):
        """Find the SIG_DATA directory."""
        sig_path = os.path.join(data_root, 'SIG_DATA')
        if os.path.isdir(sig_path):
            return sig_path

        # Try case variations
        for entry in os.listdir(data_root):
            if entry.upper() == 'SIG_DATA' and os.path.isdir(os.path.join(data_root, entry)):
                return os.path.join(data_root, entry)

        # If no SIG_DATA folder, the shapefiles might be directly in the root
        self.stdout.write(self.style.WARNING(
            'SIG_DATA folder not found, using data root as SIG_DATA'
        ))
        return data_root

    def _list_found_files(self, data_root, sig_data_dir):
        """List shapefile files found for diagnostic purposes."""
        self.stdout.write(f'\nShapefiles found:')

        # SIG_DATA shapefiles
        if os.path.isdir(sig_data_dir):
            shp_files = [f for f in os.listdir(sig_data_dir) if f.endswith('.shp')]
            self.stdout.write(f'  SIG_DATA/: {len(shp_files)} .shp files')
            for f in sorted(shp_files):
                self.stdout.write(f'    - {f}')

        # Year directories
        for year in ['1986', '2003', '2023']:
            year_dir = os.path.join(data_root, year)
            if os.path.isdir(year_dir):
                shp_files = [f for f in os.listdir(year_dir) if f.endswith('.shp')]
                self.stdout.write(f'  {year}/: {len(shp_files)} .shp files')
                for f in sorted(shp_files):
                    self.stdout.write(f'    - {f}')
            else:
                self.stdout.write(f'  {year}/: NOT FOUND')
