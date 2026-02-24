import os
import geopandas as gpd
from django.core.management.base import BaseCommand
from django.contrib.gis.geos import GEOSGeometry, MultiPolygon
from django.conf import settings
from apps.carbone.models import OccupationSol, ForetClassee, NomenclatureCouvert


YEAR_DIRS = {
    1986: {
        'dir': '1986',
        'files': {
            'FORET_DENSE': 'Foret_dense86.shp',
            'FORET_CLAIRE': 'Foret_claire86.shp',
            'FORET_DEGRADEE': 'Foret_degradee86.shp',
            'JACHERE': 'Jach\u00e8re86.shp',
        },
    },
    2003: {
        'dir': '2003',
        'files': {
            'FORET_DENSE': 'Foret_dense03.shp',
            'FORET_CLAIRE': 'Foret_claire03.shp',
            'FORET_DEGRADEE': 'Foret_degradee03.shp',
            'JACHERE': 'Jach\u00e8res03.shp',
        },
    },
    2023: {
        'dir': '2023',
        'files': {
            'FORET_DENSE': 'Foret_dense23.shp',
            'FORET_CLAIRE': 'Foret_claire23.shp',
            'FORET_DEGRADEE': 'Foret_degradee23.shp',
            'JACHERE': 'Jach\u00e8res23.shp',
        },
    },
}


class Command(BaseCommand):
    help = 'Import land cover occupation data from shapefiles'

    def add_arguments(self, parser):
        parser.add_argument('--data-dir', default=settings.SHAPEFILE_DATA_DIR)
        parser.add_argument('--year', type=int, help='Import only this year')
        parser.add_argument('--clear', action='store_true', help='Clear existing data before import')

    def handle(self, *args, **options):
        data_dir = options['data_dir']
        target_year = options.get('year')

        if options['clear']:
            if target_year:
                deleted = OccupationSol.objects.filter(annee=target_year).delete()
            else:
                deleted = OccupationSol.objects.all().delete()
            self.stdout.write(f'Cleared: {deleted}')

        forets = {f.code: f for f in ForetClassee.objects.all()}
        if not forets:
            self.stdout.write(self.style.ERROR('No forests found. Run import_forets first.'))
            return

        nomenclatures = {n.code: n for n in NomenclatureCouvert.objects.all()}
        if not nomenclatures:
            self.stdout.write(self.style.ERROR('No nomenclatures found. Run seed_nomenclature first.'))
            return

        years_to_process = [target_year] if target_year else YEAR_DIRS.keys()

        for annee in years_to_process:
            if annee not in YEAR_DIRS:
                self.stdout.write(self.style.WARNING(f'No config for year {annee}'))
                continue

            year_config = YEAR_DIRS[annee]
            year_dir = os.path.join(data_dir, year_config['dir'])

            self.stdout.write(f'\n=== Importing year {annee} from {year_dir} ===')

            for cover_code, shp_name in year_config['files'].items():
                shp_path = os.path.join(year_dir, shp_name)
                if not os.path.exists(shp_path):
                    self.stdout.write(self.style.WARNING(f'  SKIP: {shp_name} not found'))
                    continue

                nomenclature = nomenclatures.get(cover_code)
                if not nomenclature:
                    self.stdout.write(self.style.WARNING(f'  SKIP: nomenclature {cover_code} not found'))
                    continue

                self.stdout.write(f'  Reading: {shp_name} -> {cover_code}')
                try:
                    gdf = gpd.read_file(shp_path)
                    gdf = gdf.to_crs(epsg=4326)

                    imported = 0
                    errors = 0

                    for _, row in gdf.iterrows():
                        try:
                            geom = GEOSGeometry(row.geometry.wkt, srid=4326)
                            if geom.geom_type == 'Polygon':
                                geom = MultiPolygon(geom)
                            elif geom.geom_type != 'MultiPolygon':
                                errors += 1
                                continue

                            # Find which forest this polygon belongs to
                            target_foret = None
                            for code, foret in forets.items():
                                if foret.geom.intersects(geom):
                                    target_foret = foret
                                    break

                            if not target_foret:
                                target_foret = list(forets.values())[0]

                            OccupationSol.objects.create(
                                foret=target_foret,
                                nomenclature=nomenclature,
                                annee=annee,
                                geom=geom,
                                source_donnee=f'Shapefile {shp_name}',
                            )
                            imported += 1

                        except Exception:
                            errors += 1

                    self.stdout.write(self.style.SUCCESS(
                        f'    {cover_code}: {imported} imported, {errors} errors'
                    ))

                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'    ERROR: {e}'))

        self.stdout.write(self.style.SUCCESS('\nOccupation import complete.'))
