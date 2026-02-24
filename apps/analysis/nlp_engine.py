"""
Moteur NLP pour le module Chat-to-Map.
Extraction d'entites nommees depuis des requetes en francais
et construction securisee de filtres Django ORM.
"""
import re
import time
from django.db.models import Sum, Count


class NLPEngine:
    """Pipeline NLP: requete francaise -> entites -> filtre Django ORM."""

    FOREST_PATTERNS = {
        r'\btene\b': 'TENE',
        r'\bdoka\b': 'DOKA',
        r'\bsangou[eé]\b': 'SANGOUE',
        r'\blahouda\b': 'LAHOUDA',
        r'\bzou[eè]k[eé]\s*(?:bloc\s*)?(?:1|i)\b': 'ZOUEKE_1',
        r'\bzou[eè]k[eé]\s*(?:bloc\s*)?(?:2|ii)\b': 'ZOUEKE_2',
        r'\bzou[eè]k[eé]\b': 'ZOUEKE_1',
    }

    COVER_PATTERNS = {
        r'\bfor[eê]t\s+dense\b': 'FORET_DENSE',
        r'\bfor[eê]t\s+clair[e]?\b': 'FORET_CLAIRE',
        r'\bfor[eê]t\s+d[eé]grad[eé]e?\b': 'FORET_DEGRADEE',
        r'\bjach[eè]re\b': 'JACHERE',
        r'\breboisement\b': 'JACHERE',
        r'\bcacao\b': 'CACAO',
        r'\bcaf[eé]\b': 'CAFE',
        r'\bh[eé]v[eé]a\b': 'HEVEA',
        r'\bculture\s*(annuelle|herbac[eé]e)?\b': 'CULTURE_HERBACEE',
        r'\bsol\s+nu\b': 'SOL_NU',
    }

    YEAR_PATTERN = r'\b(1986|2003|2023)\b'

    COMPARISON_PATTERNS = [
        r'compar[eé]',
        r'[eé]volution',
        r'diff[eé]ren',
        r'entre\s+\d{4}\s+et\s+\d{4}',
        r'de\s+\d{4}\s+[aà]\s+\d{4}',
    ]

    STATS_PATTERNS = [
        r'superficie',
        r'surface',
        r'combien',
        r'quelle?\s+(est|sont)',
        r'total[e]?',
        r'statistiq',
    ]

    CARBON_PATTERNS = [
        r'carbone',
        r'stock',
        r'biomasse',
        r'co2',
        r'tco2',
    ]

    def parse(self, query):
        """Analyse une requete en langage naturel et extrait les entites."""
        start = time.time()
        query_lower = query.lower().strip()

        result = {
            'forests': [],
            'cover_types': [],
            'years': [],
            'intent': 'show',
            'raw_query': query,
        }

        # Extract forests
        for pattern, code in self.FOREST_PATTERNS.items():
            if re.search(pattern, query_lower, re.IGNORECASE):
                if code not in result['forests']:
                    result['forests'].append(code)

        # Extract cover types
        for pattern, code in self.COVER_PATTERNS.items():
            if re.search(pattern, query_lower, re.IGNORECASE):
                if code not in result['cover_types']:
                    result['cover_types'].append(code)

        # Extract years
        result['years'] = sorted(set(int(y) for y in re.findall(self.YEAR_PATTERN, query_lower)))

        # Determine intent
        for pattern in self.COMPARISON_PATTERNS:
            if re.search(pattern, query_lower):
                result['intent'] = 'compare'
                break

        if result['intent'] != 'compare':
            for pattern in self.STATS_PATTERNS:
                if re.search(pattern, query_lower):
                    result['intent'] = 'stats'
                    break

        if result['intent'] == 'show':
            for pattern in self.CARBON_PATTERNS:
                if re.search(pattern, query_lower):
                    result['intent'] = 'carbon'
                    break

        # Extract threshold values (e.g., "superieur a 2000", "plus de 500")
        threshold_match = re.search(
            r'(?:sup[eé]rieur|inf[eé]rieur|plus|moins)\s+(?:[aà]|de)\s+(\d+(?:[.,]\d+)?)',
            query_lower,
        )
        if threshold_match:
            val = threshold_match.group(1).replace(',', '.')
            result['threshold'] = float(val)
            if re.search(r'(?:inf[eé]rieur|moins)', query_lower):
                result['threshold_op'] = 'lte'
            else:
                result['threshold_op'] = 'gte'

        result['processing_ms'] = int((time.time() - start) * 1000)
        return result

    def build_queryset(self, parsed):
        """Construit un queryset Django ORM securise a partir des entites."""
        from apps.carbone.models import OccupationSol

        qs = OccupationSol.objects.select_related('foret', 'nomenclature')

        if parsed['forests']:
            qs = qs.filter(foret__code__in=parsed['forests'])
        if parsed['cover_types']:
            qs = qs.filter(nomenclature__code__in=parsed['cover_types'])
        if parsed['years']:
            qs = qs.filter(annee__in=parsed['years'])

        # Apply threshold filter
        if 'threshold' in parsed:
            field = 'stock_carbone_calcule' if parsed['intent'] == 'carbon' else 'superficie_ha'
            op = parsed.get('threshold_op', 'gte')
            qs = qs.filter(**{f'{field}__{op}': parsed['threshold']})

        return qs

    def build_stats(self, parsed):
        """Construit des statistiques agregees."""
        qs = self.build_queryset(parsed)
        return qs.values(
            'nomenclature__code',
            'nomenclature__libelle_fr',
            'nomenclature__couleur_hex',
        ).annotate(
            total_superficie_ha=Sum('superficie_ha'),
            total_carbone=Sum('stock_carbone_calcule'),
            nombre_polygones=Count('id'),
        ).order_by('nomenclature__ordre_affichage')

    def build_comparison(self, parsed):
        """Construit une comparaison entre deux annees."""
        if len(parsed['years']) < 2:
            return None

        annee1, annee2 = parsed['years'][0], parsed['years'][-1]
        base_filter = {}
        if parsed['forests']:
            base_filter['foret__code__in'] = parsed['forests']
        if parsed['cover_types']:
            base_filter['nomenclature__code__in'] = parsed['cover_types']

        from apps.carbone.models import OccupationSol

        def stats_for_year(annee):
            return OccupationSol.objects.filter(
                annee=annee, **base_filter,
            ).values(
                'nomenclature__code',
                'nomenclature__libelle_fr',
                'nomenclature__couleur_hex',
            ).annotate(
                superficie_ha=Sum('superficie_ha'),
                carbone=Sum('stock_carbone_calcule'),
            ).order_by('nomenclature__ordre_affichage')

        return {
            'annee1': {'annee': annee1, 'data': list(stats_for_year(annee1))},
            'annee2': {'annee': annee2, 'data': list(stats_for_year(annee2))},
        }
