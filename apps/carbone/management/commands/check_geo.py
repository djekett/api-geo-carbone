"""
Management command: diagnose database health and spatial indexes.
Run: python manage.py check_geo
"""
from django.core.management.base import BaseCommand
from django.db import connection
from apps.carbone.models import (
    OccupationSol, ForetClassee, NomenclatureCouvert,
    ZoneEtude, Infrastructure, Placette,
)


class Command(BaseCommand):
    help = 'Diagnostique la base de données géospatiale (indexes, compteurs, performance)'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(' API.GEO.Carbone — Diagnostic base de données')
        self.stdout.write('=' * 60 + '\n')

        # 1. Data counts
        self.stdout.write(self.style.MIGRATE_HEADING('\n📊 Compteurs de données:'))
        counts = {
            'ForetClassee': ForetClassee.objects.count(),
            'NomenclatureCouvert': NomenclatureCouvert.objects.count(),
            'OccupationSol': OccupationSol.objects.count(),
            'ZoneEtude': ZoneEtude.objects.count(),
            'Infrastructure': Infrastructure.objects.count(),
            'Placette': Placette.objects.count(),
        }
        for model, count in counts.items():
            status = self.style.SUCCESS(f'{count:>6}') if count > 0 else self.style.WARNING(f'{count:>6} ⚠')
            self.stdout.write(f'  {model:<25} {status}')

        # 1b. Occupation per year
        self.stdout.write(self.style.MIGRATE_HEADING('\n📅 Occupation par année:'))
        years = OccupationSol.objects.values('annee').annotate(
            n=__import__('django.db.models', fromlist=['Count']).Count('id')
        ).order_by('annee')
        for y in years:
            self.stdout.write(f"  {y['annee']}: {y['n']} polygones")
        if not years:
            self.stdout.write(self.style.WARNING('  Aucune donnée! Exécutez: python manage.py import_occupations'))

        # 2. Spatial indexes
        self.stdout.write(self.style.MIGRATE_HEADING('\n🗂️  Index spatiaux (GiST):'))
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT indexname, tablename
                FROM pg_indexes
                WHERE schemaname = 'public'
                AND (indexdef LIKE '%gist%' OR indexdef LIKE '%GIST%')
                ORDER BY tablename, indexname;
            """)
            indexes = cursor.fetchall()

        if indexes:
            for name, table in indexes:
                self.stdout.write(f'  ✓ {table:<35} {name}')
        else:
            self.stdout.write(self.style.WARNING('  Aucun index GiST trouvé! Exécutez: python manage.py migrate'))

        # 3. Table sizes
        self.stdout.write(self.style.MIGRATE_HEADING('\n💾 Taille des tables:'))
        tables = ['carbone_occupationsol', 'carbone_foretclassee', 'carbone_zoneetude',
                   'carbone_infrastructure', 'carbone_placette']
        with connection.cursor() as cursor:
            for table in tables:
                try:
                    cursor.execute(f"SELECT pg_size_pretty(pg_total_relation_size('{table}'));")
                    size = cursor.fetchone()[0]
                    self.stdout.write(f'  {table:<35} {size}')
                except Exception:
                    self.stdout.write(f'  {table:<35} (table inexistante)')

        # 4. Performance test
        self.stdout.write(self.style.MIGRATE_HEADING('\n⚡ Test de performance (occupation 1986):'))
        import time
        t0 = time.time()
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*)
                FROM carbone_occupationsol
                WHERE annee = 1986;
            """)
            count = cursor.fetchone()[0]
        dt1 = (time.time() - t0) * 1000

        t0 = time.time()
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT json_build_object(
                    'type', 'FeatureCollection',
                    'features', COALESCE(json_agg(
                        json_build_object(
                            'type', 'Feature',
                            'geometry', ST_AsGeoJSON(ST_SimplifyPreserveTopology(o.geom, 0.0008), 6)::json,
                            'properties', json_build_object('id', o.id)
                        )
                    ), '[]'::json)
                )
                FROM carbone_occupationsol o
                WHERE o.annee = 1986;
            """)
            _ = cursor.fetchone()
        dt2 = (time.time() - t0) * 1000

        self.stdout.write(f'  COUNT: {count} polygones en {dt1:.0f}ms')
        self.stdout.write(f'  GeoJSON simplifié: {dt2:.0f}ms')

        if dt2 > 2000:
            self.stdout.write(self.style.WARNING(f'  ⚠ Lent (>{dt2:.0f}ms). Vérifiez les index spatiaux.'))
        else:
            self.stdout.write(self.style.SUCCESS(f'  ✓ Performance OK'))

        self.stdout.write('\n' + '=' * 60 + '\n')
