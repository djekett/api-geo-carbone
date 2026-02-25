from django.core.management.base import BaseCommand
from apps.carbone.models import NomenclatureCouvert
from apps.carbone.constants import NOMENCLATURE_DATA


class Command(BaseCommand):
    help = 'Seed the NomenclatureCouvert reference table'

    # Champs valides du modèle NomenclatureCouvert
    VALID_FIELDS = {'code', 'libelle_fr', 'stock_carbone_reference', 'couleur_hex', 'ordre_affichage'}

    def handle(self, *args, **options):
        for data in NOMENCLATURE_DATA:
            # Filtrer uniquement les champs du modèle (exclure biomasse_t_ha, carbone_tc_ha, etc.)
            clean_data = {k: v for k, v in data.items() if k in self.VALID_FIELDS}
            obj, created = NomenclatureCouvert.objects.update_or_create(
                code=clean_data.pop('code'),
                defaults=clean_data,
            )
            status = 'CREATED' if created else 'UPDATED'
            self.stdout.write(f'  {status}: {obj.libelle_fr} ({obj.code})')
        self.stdout.write(self.style.SUCCESS(f'Nomenclature seeded: {len(NOMENCLATURE_DATA)} types'))
