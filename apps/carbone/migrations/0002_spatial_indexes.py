"""
Add explicit spatial GiST indexes and composite indexes for performance.

PostGIS creates GiST indexes automatically for geometry columns created via
Django migrations, but explicit indexes ensure they exist and add composite
indexes for the most common query patterns.
"""
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('carbone', '0001_initial'),
    ]

    operations = [
        # Composite index: the most common query pattern is annee + foret_id
        migrations.RunSQL(
            sql="""
            CREATE INDEX IF NOT EXISTS idx_occupation_annee_foret
            ON carbone_occupationsol (annee, foret_id);
            """,
            reverse_sql="DROP INDEX IF EXISTS idx_occupation_annee_foret;",
        ),

        # Composite index: annee + nomenclature for stats queries
        migrations.RunSQL(
            sql="""
            CREATE INDEX IF NOT EXISTS idx_occupation_annee_nomenclature
            ON carbone_occupationsol (annee, nomenclature_id);
            """,
            reverse_sql="DROP INDEX IF EXISTS idx_occupation_annee_nomenclature;",
        ),

        # Spatial index on occupationsol (may already exist, IF NOT EXISTS handles that)
        migrations.RunSQL(
            sql="""
            CREATE INDEX IF NOT EXISTS idx_occupation_geom_gist
            ON carbone_occupationsol USING GIST (geom);
            """,
            reverse_sql="DROP INDEX IF EXISTS idx_occupation_geom_gist;",
        ),

        # Spatial index on foretclassee
        migrations.RunSQL(
            sql="""
            CREATE INDEX IF NOT EXISTS idx_foretclassee_geom_gist
            ON carbone_foretclassee USING GIST (geom);
            """,
            reverse_sql="DROP INDEX IF EXISTS idx_foretclassee_geom_gist;",
        ),

        # Spatial index on zoneetude
        migrations.RunSQL(
            sql="""
            CREATE INDEX IF NOT EXISTS idx_zoneetude_geom_gist
            ON carbone_zoneetude USING GIST (geom);
            """,
            reverse_sql="DROP INDEX IF EXISTS idx_zoneetude_geom_gist;",
        ),

        # Spatial index on infrastructure
        migrations.RunSQL(
            sql="""
            CREATE INDEX IF NOT EXISTS idx_infrastructure_geom_gist
            ON carbone_infrastructure USING GIST (geom);
            """,
            reverse_sql="DROP INDEX IF EXISTS idx_infrastructure_geom_gist;",
        ),

        # Index on infrastructure type for filtered queries
        migrations.RunSQL(
            sql="""
            CREATE INDEX IF NOT EXISTS idx_infrastructure_type
            ON carbone_infrastructure (type_infra);
            """,
            reverse_sql="DROP INDEX IF EXISTS idx_infrastructure_type;",
        ),
    ]
