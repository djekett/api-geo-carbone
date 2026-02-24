import os
import geopandas as gpd
from django.core.management.base import BaseCommand
from django.contrib.gis.geos import GEOSGeometry
from django.conf import settings
from apps.carbone.models import Placette, ForetClassee


class Command(BaseCommand):
    help = 'Import field measurement plots (placettes)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--data-dir',
            default=os.path.join(settings.SHAPEFILE_DATA_DIR, 'SIG_DATA'),
        )

    def handle(self, *args, **options):
        data_dir = options['data_dir']
        shp_path = os.path.join(data_dir, 'Placettes.shp')

        if not os.path.exists(shp_path):
            self.stdout.write(self.style.ERROR(f'File not found: {shp_path}'))
            return

        forets = ForetClassee.objects.all()
        gdf = gpd.read_file(shp_path)
        gdf = gdf.to_crs(epsg=4326)

        self.stdout.write(f'Reading {len(gdf)} placettes...')
        self.stdout.write(f'Columns: {list(gdf.columns)}')

        imported = 0
        for idx, row in gdf.iterrows():
            try:
                geom = GEOSGeometry(row.geometry.wkt, srid=4326)

                target_foret = None
                for foret in forets:
                    if foret.geom.contains(geom):
                        target_foret = foret
                        break

                extra = {}
                for col in gdf.columns:
                    if col != 'geometry':
                        val = row[col]
                        if val is not None and str(val) != 'nan':
                            extra[col] = str(val)

                Placette.objects.create(
                    foret=target_foret,
                    code_placette=extra.get('CODE', extra.get('Id', f'P{idx+1:03d}')),
                    geom=geom,
                    donnees=extra,
                )
                imported += 1
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'  Error row {idx}: {e}'))

        self.stdout.write(self.style.SUCCESS(f'Placettes import complete: {imported} imported'))
