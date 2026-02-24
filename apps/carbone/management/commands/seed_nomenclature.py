from django.core.management.base import BaseCommand
from apps.carbone.models import NomenclatureCouvert
from apps.carbone.constants import NOMENCLATURE_DATA


class Command(BaseCommand):
    help = 'Seed the NomenclatureCouvert reference table'

    def handle(self, *args, **options):
        for data in NOMENCLATURE_DATA:
            obj, created = NomenclatureCouvert.objects.update_or_create(
                code=data['code'],
                defaults=data,
            )
            status = 'CREATED' if created else 'UPDATED'
            self.stdout.write(f'  {status}: {obj.libelle_fr} ({obj.code})')
        self.stdout.write(self.style.SUCCESS(f'Nomenclature seeded: {len(NOMENCLATURE_DATA)} types'))
