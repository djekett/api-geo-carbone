"""
Moteur NLP pour le module Chat-to-Map.
Extraction d'entites nommees depuis des requetes en francais
et construction securisee de filtres Django ORM.

Version 2.0 : synonymes etendus, intents enrichis (help, deforestation,
ranking), normalisation sans accents, suggestions intelligentes,
analyse de deforestation.
"""
import re
import time
import unicodedata
from django.db.models import Sum, Count


def normalize_text(text):
    """Remove accents and convert to lowercase for fuzzy matching."""
    nfkd = unicodedata.normalize('NFKD', text)
    return ''.join(c for c in nfkd if not unicodedata.combining(c)).lower()


class NLPEngine:
    """Pipeline NLP: requete francaise -> entites -> filtre Django ORM."""

    # ------------------------------------------------------------------
    # Entity patterns
    # ------------------------------------------------------------------
    FOREST_PATTERNS = {
        r'\btene\b': 'TENE',
        r'\bten[eé]\b': 'TENE',
        r'\bdoka\b': 'DOKA',
        r'\bsangou[eé]\b': 'SANGOUE',
        r'\blahouda\b': 'LAHOUDA',
        r'\bzou[eè]k[eé]\s*(?:bloc\s*)?(?:1|i)\b': 'ZOUEKE_1',
        r'\bzou[eè]k[eé]\s*(?:bloc\s*)?(?:2|ii)\b': 'ZOUEKE_2',
        r'\bzou[eè]k[eé]\b': 'ZOUEKE_1',
    }

    COVER_PATTERNS = {
        # Core patterns
        r'\bfor[eê]t\s+dense\b': 'FORET_DENSE',
        r'\bfor[eê]t\s+clair[e]?\b': 'FORET_CLAIRE',
        r'\bfor[eê]t\s+d[eé]grad[eé]e?\b': 'FORET_DEGRADEE',
        r'\bjach[eè]re\b': 'JACHERE',
        r'\bcacao\b': 'CACAO',
        r'\bcaf[eé]\b': 'CAFE',
        r'\bh[eé]v[eé]a\b': 'HEVEA',
        r'\bculture\s*(annuelle|herbac[eé]e)?\b': 'CULTURE_HERBACEE',
        r'\bsol\s+nu\b': 'SOL_NU',
        # Synonymes etendus
        r'\bbois\s+dense\b': 'FORET_DENSE',
        r'\bbois\s+clair\b': 'FORET_CLAIRE',
        r'\bfor[eê]t\s+primaire\b': 'FORET_DENSE',
        r'\bfor[eê]t\s+secondaire\b': 'FORET_CLAIRE',
        r'\bvieille\s+for[eê]t\b': 'FORET_DENSE',
        r'\breboisement\b': 'JACHERE',
        r'\bfriche\b': 'JACHERE',
        r'\bplantation\b': 'CACAO',
        r'\bzone\s+d[eé]bois[eé]e?\b': 'SOL_NU',
        r'\bterrain\s+nu\b': 'SOL_NU',
        r'\bcouvert\s+herbac[eé]\b': 'CULTURE_HERBACEE',
        r'\bchamp\b': 'CULTURE_HERBACEE',
        r'\bcaoutchouc\b': 'HEVEA',
    }

    YEAR_PATTERN = r'\b(1986|2003|2023)\b'

    # ------------------------------------------------------------------
    # Intent patterns
    # ------------------------------------------------------------------
    COMPARISON_PATTERNS = [
        r'compar[eé]',
        r'[eé]volution',
        r'diff[eé]ren',
        r'entre\s+\d{4}\s+et\s+\d{4}',
        r'de\s+\d{4}\s+[aà]\s+\d{4}',
        r'changement',
    ]

    STATS_PATTERNS = [
        r'superficie',
        r'surface',
        r'combien',
        r'quelle?\s+(est|sont)',
        r'total[e]?',
        r'statistiq',
        r'donn[eé]es?\b',
        r'r[eé]partition',
        r'nombre\s+de',
    ]

    CARBON_PATTERNS = [
        r'carbone',
        r'stock',
        r'biomasse',
        r'co2',
        r'tco2',
        r's[eé]questration',
    ]

    DEFORESTATION_PATTERNS = [
        r'd[eé]forestation',
        r'd[eé]boisement',
        r'perte\s+de\s+for[eê]t',
        r'perte\s+foresti[eè]re',
        r'destruction',
        r'recul\s+foresti[eè]r',
        r'd[eé]gradation\s+foresti[eè]re',
    ]

    RANKING_PATTERNS = [
        r'class[eé]ment',
        r'ranking',
        r'\btop\b',
        r'plus\s+grand[e]?',
        r'plus\s+petit[e]?',
        r'meilleur',
        r'pire',
    ]

    GREETING_PATTERNS = [
        r'^bonjour\b',
        r'^salut\b',
        r'^hello\b',
        r'^bonsoir\b',
        r'^aide\b',
        r'^help\b',
        r'^comment\s+([cç]a\s+)?march',
        r'^que\s+peux',
        r'^qu.est.ce\s+que\s+tu',
        r'^quoi\s+faire',
        r'^coucou\b',
    ]

    # ------------------------------------------------------------------
    # Parsing
    # ------------------------------------------------------------------
    def parse(self, query):
        """Analyse une requete en langage naturel et extrait les entites."""
        start = time.time()
        query_lower = query.lower().strip()
        query_normalized = normalize_text(query)

        result = {
            'forests': [],
            'cover_types': [],
            'years': [],
            'intent': 'show',
            'raw_query': query,
            '_inherited': [],
        }

        # Check greetings/help first
        for pattern in self.GREETING_PATTERNS:
            if re.search(pattern, query_lower):
                result['intent'] = 'help'
                result['processing_ms'] = int((time.time() - start) * 1000)
                return result

        # Extract forests (try both accented and normalized)
        for pattern, code in self.FOREST_PATTERNS.items():
            if re.search(pattern, query_lower, re.IGNORECASE) or \
               re.search(pattern, query_normalized, re.IGNORECASE):
                if code not in result['forests']:
                    result['forests'].append(code)

        # Extract cover types
        for pattern, code in self.COVER_PATTERNS.items():
            if re.search(pattern, query_lower, re.IGNORECASE) or \
               re.search(pattern, query_normalized, re.IGNORECASE):
                if code not in result['cover_types']:
                    result['cover_types'].append(code)

        # Extract years
        result['years'] = sorted(set(
            int(y) for y in re.findall(self.YEAR_PATTERN, query_lower)
        ))

        # Determine intent (priority: compare > deforestation > stats > carbon > ranking > show)
        for pattern in self.COMPARISON_PATTERNS:
            if re.search(pattern, query_lower):
                result['intent'] = 'compare'
                break

        if result['intent'] != 'compare':
            for pattern in self.DEFORESTATION_PATTERNS:
                if re.search(pattern, query_lower) or \
                   re.search(pattern, query_normalized):
                    result['intent'] = 'deforestation'
                    if not result['years']:
                        result['years'] = [1986, 2023]
                    break

        if result['intent'] == 'show':
            for pattern in self.STATS_PATTERNS:
                if re.search(pattern, query_lower):
                    result['intent'] = 'stats'
                    break

        if result['intent'] == 'show':
            for pattern in self.CARBON_PATTERNS:
                if re.search(pattern, query_lower):
                    result['intent'] = 'carbon'
                    break

        if result['intent'] == 'show':
            for pattern in self.RANKING_PATTERNS:
                if re.search(pattern, query_lower):
                    result['intent'] = 'ranking'
                    break

        # Extract threshold values
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

    # ------------------------------------------------------------------
    # Query builders
    # ------------------------------------------------------------------
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

    def build_deforestation(self, parsed):
        """Analyse de deforestation entre deux annees."""
        if len(parsed['years']) < 2:
            return None

        annee1, annee2 = parsed['years'][0], parsed['years'][-1]
        base_filter = {}
        if parsed['forests']:
            base_filter['foret__code__in'] = parsed['forests']

        from apps.carbone.models import OccupationSol

        forest_codes = ['FORET_DENSE', 'FORET_CLAIRE', 'FORET_DEGRADEE']

        def forest_area(annee):
            return OccupationSol.objects.filter(
                annee=annee,
                nomenclature__code__in=forest_codes,
                **base_filter,
            ).aggregate(total=Sum('superficie_ha'))['total'] or 0

        def detail_for_year(annee):
            return list(OccupationSol.objects.filter(
                annee=annee,
                nomenclature__code__in=forest_codes,
                **base_filter,
            ).values(
                'nomenclature__code',
                'nomenclature__libelle_fr',
                'nomenclature__couleur_hex',
            ).annotate(
                superficie_ha=Sum('superficie_ha'),
            ).order_by('nomenclature__ordre_affichage'))

        area1 = forest_area(annee1)
        area2 = forest_area(annee2)
        loss = area1 - area2
        pct = (loss / area1 * 100) if area1 > 0 else 0

        return {
            'annee1': annee1,
            'annee2': annee2,
            'superficie_foret_1': round(float(area1), 2),
            'superficie_foret_2': round(float(area2), 2),
            'perte_ha': round(float(loss), 2),
            'perte_pct': round(float(pct), 1),
            'detail_1': detail_for_year(annee1),
            'detail_2': detail_for_year(annee2),
        }

    def build_ranking(self, parsed):
        """Classement des forets par superficie de couvert forestier."""
        from apps.carbone.models import OccupationSol

        annee = parsed['years'][-1] if parsed['years'] else 2023
        cover_filter = {}
        if parsed['cover_types']:
            cover_filter['nomenclature__code__in'] = parsed['cover_types']
        else:
            cover_filter['nomenclature__code__in'] = [
                'FORET_DENSE', 'FORET_CLAIRE', 'FORET_DEGRADEE',
            ]

        return list(OccupationSol.objects.filter(
            annee=annee, **cover_filter,
        ).values(
            'foret__code', 'foret__nom',
        ).annotate(
            total_superficie_ha=Sum('superficie_ha'),
            total_carbone=Sum('stock_carbone_calcule'),
            nombre_polygones=Count('id'),
        ).order_by('-total_superficie_ha'))

    # ------------------------------------------------------------------
    # Smart suggestions
    # ------------------------------------------------------------------
    def suggest_queries(self, parsed):
        """Generate query suggestions when no results or few entities matched."""
        suggestions = []

        if not parsed['forests'] and not parsed['cover_types'] and not parsed['years']:
            suggestions = [
                "Montre les zones de foret dense a TENE en 2023",
                "Superficie de foret claire a SANGOUE en 2023 ?",
                "Compare TENE entre 1986 et 2023",
                "Deforestation a DOKA",
                "Statistiques de carbone pour 2023",
            ]
        else:
            if not parsed['forests']:
                suggestions.append(
                    "Precisez une foret : TENE, DOKA, SANGOUE, LAHOUDA, ZOUEKE"
                )
            if not parsed['cover_types']:
                suggestions.append(
                    "Precisez un type : foret dense, foret claire, foret degradee, jachere, cacao"
                )
            if not parsed['years']:
                suggestions.append(
                    "Precisez une annee : 1986, 2003 ou 2023"
                )

        return suggestions
