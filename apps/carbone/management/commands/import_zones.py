import os
os.environ['SHAPE_RESTORE_SHX'] = 'YES'
import geopandas as gpd
from django.core.management.base import BaseCommand
from django.contrib.gis.geos import GEOSGeometry, MultiPolygon
from django.db import connection
from django.conf import settings
from apps.carbone.models import ZoneEtude, ForetClassee


class Command(BaseCommand):
    help = 'Import administrative boundaries (zones etude)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--data-dir',
            default=os.path.join(settings.SHAPEFILE_DATA_DIR, 'SIG_DATA'),
        )
        parser.add_argument(
            '--generate-fallback',
            action='store_true',
            help='Generate department boundary from forest polygons if shapefile is missing',
        )

    def handle(self, *args, **options):
        data_dir = options['data_dir']
        oume_imported = False

        # Import department boundary from shapefile
        for name in ['Limite_Oumé.shp', 'Limite_Oume.shp', 'limite_oume.shp', 'LIMITE_OUME.shp']:
            oume_path = os.path.join(data_dir, name)
            if os.path.exists(oume_path):
                try:
                    gdf = gpd.read_file(oume_path)
                    if gdf.crs is None:
                        gdf = gdf.set_crs(epsg=4326)
                    else:
                        gdf = gdf.to_crs(epsg=4326)
                    merged = gdf.geometry.unary_union
                    geom = GEOSGeometry(merged.wkt, srid=4326)
                    if geom.geom_type == 'Polygon':
                        geom = MultiPolygon(geom)
                    elif geom.geom_type == 'GeometryCollection':
                        from django.contrib.gis.geos import Polygon
                        polys = [g for g in geom if isinstance(g, (Polygon, MultiPolygon))]
                        if polys:
                            geom = MultiPolygon(*[p if isinstance(p, Polygon) else list(p) for p in polys])
                        else:
                            raise ValueError('No polygons found in GeometryCollection')

                    # Make geometry valid
                    if not geom.valid:
                        geom = geom.buffer(0)
                        if geom.geom_type == 'Polygon':
                            geom = MultiPolygon(geom)

                    obj, created = ZoneEtude.objects.update_or_create(
                        type_zone='DEPARTEMENT',
                        niveau=1,
                        defaults={'nom': "Département d'Oumé", 'geom': geom},
                    )
                    self.stdout.write(self.style.SUCCESS(
                        f'  Departement: {"CREATED" if created else "UPDATED"}'
                    ))
                    oume_imported = True
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'  ERROR (Oume): {e}'))
                break

        # Fallback: generate department boundary from forest polygons
        if not oume_imported and (options['generate_fallback'] or not ZoneEtude.objects.filter(type_zone='DEPARTEMENT').exists()):
            if ForetClassee.objects.exists():
                self.stdout.write('  Generating fallback boundary from forest polygons...')
                try:
                    with connection.cursor() as cursor:
                        cursor.execute("""
                            INSERT INTO carbone_zoneetude (nom, type_zone, niveau, geom, created_at, updated_at)
                            SELECT
                                'Département d''Oumé' AS nom,
                                'DEPARTEMENT' AS type_zone,
                                1 AS niveau,
                                ST_Multi(
                                    ST_Buffer(
                                        ST_ConvexHull(ST_Collect(geom)),
                                        0.02
                                    )
                                ) AS geom,
                                NOW() AS created_at,
                                NOW() AS updated_at
                            WHERE NOT EXISTS (
                                SELECT 1 FROM carbone_zoneetude
                                WHERE type_zone = 'DEPARTEMENT'
                            );
                        """)
                    self.stdout.write(self.style.SUCCESS(
                        '  Departement: GENERATED (fallback from forest convex hull)'
                    ))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'  ERROR (fallback): {e}'))
            else:
                self.stdout.write(self.style.WARNING(
                    '  SKIP: No shapefile and no forests to generate fallback'
                ))

        # Import sous-prefectures
        sp_path = os.path.join(data_dir, 'Limite_SP.shp')
        if os.path.exists(sp_path):
            try:
                gdf = gpd.read_file(sp_path)
                if gdf.crs is None:
                    gdf = gdf.set_crs(epsg=4326)
                else:
                    gdf = gdf.to_crs(epsg=4326)
                for idx, row in gdf.iterrows():
                    geom = GEOSGeometry(row.geometry.wkt, srid=4326)
                    if geom.geom_type == 'Polygon':
                        geom = MultiPolygon(geom)
                    nom = f'Sous-prefecture {idx + 1}'
                    for col in ['NOM', 'Nom', 'nom', 'NAME', 'Name', 'NOM_SP', 'LABEL']:
                        if col in gdf.columns and row[col]:
                            nom = str(row[col])
                            break
                    obj, created = ZoneEtude.objects.update_or_create(
                        nom=nom,
                        type_zone='SOUS_PREFECTURE',
                        defaults={'niveau': 2, 'geom': geom},
                    )
                    self.stdout.write(f'  SP: {nom} - {"CREATED" if created else "UPDATED"}')
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  ERROR (SP): {e}'))
        else:
            self.stdout.write(self.style.WARNING('  SKIP: Limite_SP.shp not found'))

        self.stdout.write(self.style.SUCCESS('Zone import complete.'))
