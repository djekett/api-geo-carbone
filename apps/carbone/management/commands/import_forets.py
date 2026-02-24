import os
import geopandas as gpd
from django.core.management.base import BaseCommand
from django.contrib.gis.geos import GEOSGeometry, MultiPolygon
from django.conf import settings
from apps.carbone.models import ForetClassee
from apps.carbone.constants import FORETS_DATA


SHAPEFILE_MAP = {
    'TENE': 'Limite_Tene.shp',
    'DOKA': 'Limite_Doka.shp',
    'SANGOUE': 'Limite_Sangoue.shp',
    'LAHOUDA': 'Limite_Lahouda.shp',
    'ZOUEKE_1': 'Limite_Zuoke.shp',
    'ZOUEKE_2': 'Limite_Zuoke2.shp',
}


class Command(BaseCommand):
    help = 'Import forest boundaries from shapefiles'

    def add_arguments(self, parser):
        parser.add_argument(
            '--data-dir',
            default=os.path.join(settings.SHAPEFILE_DATA_DIR, 'SIG_DATA'),
            help='Directory containing forest limit shapefiles',
        )

    def handle(self, *args, **options):
        data_dir = options['data_dir']
        self.stdout.write(f'Importing forests from: {data_dir}')

        for code, shp_name in SHAPEFILE_MAP.items():
            shp_path = os.path.join(data_dir, shp_name)
            if not os.path.exists(shp_path):
                self.stdout.write(self.style.WARNING(f'  SKIP: {shp_name} not found'))
                continue

            try:
                gdf = gpd.read_file(shp_path)
                gdf = gdf.to_crs(epsg=4326)

                merged = gdf.geometry.unary_union
                geom = GEOSGeometry(merged.wkt, srid=4326)
                if geom.geom_type == 'Polygon':
                    geom = MultiPolygon(geom)

                foret_data = FORETS_DATA.get(code, {})
                obj, created = ForetClassee.objects.update_or_create(
                    code=code,
                    defaults={
                        'nom': foret_data.get('nom', f'Foret Classee de {code}'),
                        'superficie_legale_ha': foret_data.get('superficie_legale_ha'),
                        'geom': geom,
                    },
                )
                status = 'CREATED' if created else 'UPDATED'
                self.stdout.write(self.style.SUCCESS(f'  {status}: {obj.nom}'))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  ERROR ({shp_name}): {e}'))

        self.stdout.write(self.style.SUCCESS('Forest import complete.'))
