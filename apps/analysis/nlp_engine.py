"""
Moteur NLP pour le module Chat-to-Map.
Extraction d'entites nommees depuis des requetes en francais
et construction securisee de filtres Django ORM.

Version 3.0 :
- Fuzzy matching (difflib) pour noms de forets et types de couvert
- Synonymes tres etendus (agricoles, ecologiques, populaires)
- Nouveaux intents : stock_carbone (spatialisation CO2), resume (vue d'ensemble)
- Classement par carbone OU superficie selon le contexte
- Comparaison auto-default (1986 vs 2023 si annees manquantes)
- Meilleure couverture : questions avec "quel/quelle/ou/pourquoi"
- Reponse contextuelle enrichie avec explications
"""
import re
import time
import unicodedata
from difflib import get_close_matches
from django.db.models import Sum, Count, F


def normalize_text(text):
    """Remove accents and convert to lowercase for fuzzy matching."""
    nfkd = unicodedata.normalize('NFKD', text)
    return ''.join(c for c in nfkd if not unicodedata.combining(c)).lower()


# ======================================================================
# Fuzzy matching dictionaries (for difflib)
# ======================================================================
FOREST_NAMES = {
    'tene': 'TENE', 'tené': 'TENE', 'téné': 'TENE',
    'doka': 'DOKA',
    'sangoue': 'SANGOUE', 'sangoué': 'SANGOUE', 'sangue': 'SANGOUE',
    'lahouda': 'LAHOUDA', 'lahouda': 'LAHOUDA',
    'zoueke': 'ZOUEKE_1', 'zouéké': 'ZOUEKE_1', 'zoueke 1': 'ZOUEKE_1',
    'zoueke 2': 'ZOUEKE_2', 'zouéké 2': 'ZOUEKE_2',
    'zoueke bloc 1': 'ZOUEKE_1', 'zoueke bloc 2': 'ZOUEKE_2',
    'zoueke i': 'ZOUEKE_1', 'zoueke ii': 'ZOUEKE_2',
}

COVER_NAMES = {
    'foret dense': 'FORET_DENSE', 'forêt dense': 'FORET_DENSE',
    'bois dense': 'FORET_DENSE', 'foret primaire': 'FORET_DENSE',
    'vieille foret': 'FORET_DENSE', 'grande foret': 'FORET_DENSE',
    'foret claire': 'FORET_CLAIRE', 'forêt claire': 'FORET_CLAIRE',
    'bois clair': 'FORET_CLAIRE', 'foret secondaire': 'FORET_CLAIRE',
    'foret ouverte': 'FORET_CLAIRE',
    'foret degradee': 'FORET_DEGRADEE', 'forêt dégradée': 'FORET_DEGRADEE',
    'foret abimee': 'FORET_DEGRADEE', 'foret endommagee': 'FORET_DEGRADEE',
    'foret perturbee': 'FORET_DEGRADEE',
    'jachere': 'JACHERE', 'jachère': 'JACHERE', 'friche': 'JACHERE',
    'reboisement': 'JACHERE', 'jeune foret': 'JACHERE',
    'repousse': 'JACHERE', 'regeneration': 'JACHERE',
    'cacao': 'CACAO', 'cacaoyer': 'CACAO', 'cacaoculture': 'CACAO',
    'plantation cacao': 'CACAO', 'chocolat': 'CACAO',
    'cafe': 'CAFE', 'café': 'CAFE', 'cafeier': 'CAFE',
    'cafeiculture': 'CAFE', 'plantation cafe': 'CAFE',
    'hevea': 'HEVEA', 'hévéa': 'HEVEA', 'caoutchouc': 'HEVEA',
    'plantation hevea': 'HEVEA', 'latex': 'HEVEA', 'rubber': 'HEVEA',
    'culture herbacee': 'CULTURE_HERBACEE', 'culture annuelle': 'CULTURE_HERBACEE',
    'champ': 'CULTURE_HERBACEE', 'champs': 'CULTURE_HERBACEE',
    'agriculture': 'CULTURE_HERBACEE', 'culture vivriere': 'CULTURE_HERBACEE',
    'parcelle agricole': 'CULTURE_HERBACEE', 'riz': 'CULTURE_HERBACEE',
    'mais': 'CULTURE_HERBACEE', 'manioc': 'CULTURE_HERBACEE',
    'sol nu': 'SOL_NU', 'terrain nu': 'SOL_NU',
    'zone deboisee': 'SOL_NU', 'zone nue': 'SOL_NU',
    'sans vegetation': 'SOL_NU', 'defriche': 'SOL_NU',
}

ALL_FORESTS_LIST = ['TENE', 'DOKA', 'SANGOUE', 'LAHOUDA', 'ZOUEKE_1', 'ZOUEKE_2']


class NLPEngine:
    """Pipeline NLP v3: requete francaise -> entites -> filtre Django ORM."""

    # ------------------------------------------------------------------
    # Entity patterns (regex — first pass)
    # ------------------------------------------------------------------
    FOREST_PATTERNS = {
        r'\btene\b': 'TENE', r'\bten[eé]\b': 'TENE', r'\bt[eé]n[eé]\b': 'TENE',
        r'\bdoka\b': 'DOKA',
        r'\bsangou[eé]\b': 'SANGOUE', r'\bsangu[eé]\b': 'SANGOUE',
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
        r'\bcacao(?:yer|culture)?\b': 'CACAO',
        r'\bcaf[eé](?:ier|iculture)?\b': 'CAFE',
        r'\bh[eé]v[eé]a\b': 'HEVEA',
        r'\bcaoutchouc\b': 'HEVEA',
        r'\bculture\s*(?:annuelle|herbac[eé]e|vivri[eè]re)?\b': 'CULTURE_HERBACEE',
        r'\bsol\s+nu\b': 'SOL_NU',
        r'\bbois\s+dense\b': 'FORET_DENSE',
        r'\bbois\s+clair\b': 'FORET_CLAIRE',
        r'\bfor[eê]t\s+primaire\b': 'FORET_DENSE',
        r'\bfor[eê]t\s+secondaire\b': 'FORET_CLAIRE',
        r'\breboisement\b': 'JACHERE',
        r'\bfriche\b': 'JACHERE',
        r'\bplantation\b': 'CACAO',
        r'\bzone\s+d[eé]bois[eé]e?\b': 'SOL_NU',
        r'\bterrain\s+nu\b': 'SOL_NU',
        r'\bchamps?\b': 'CULTURE_HERBACEE',
        r'\bagriculture\b': 'CULTURE_HERBACEE',
        r'\bmanioc\b': 'CULTURE_HERBACEE',
        r'\briz\b': 'CULTURE_HERBACEE',
        r'\bma[ïi]s\b': 'CULTURE_HERBACEE',
        r'\blatex\b': 'HEVEA',
        r'\bchocolat\b': 'CACAO',
    }

    YEAR_PATTERN = r'\b(1986|2003|2023)\b'

    # ------------------------------------------------------------------
    # Intent patterns (enriched v3)
    # ------------------------------------------------------------------
    COMPARISON_PATTERNS = [
        r'compar[eé]', r'[eé]volution', r'diff[eé]ren',
        r'entre\s+\d{4}\s+et\s+\d{4}', r'de\s+\d{4}\s+[aà]\s+\d{4}',
        r'changement', r'avant\s+apr[eè]s', r'progression',
        r'comment\s+a\s+[eé]volu', r'qu.est.ce\s+qui\s+a\s+chang',
    ]

    STATS_PATTERNS = [
        r'superficie', r'surface', r'combien', r'total[e]?',
        r'statistiq', r'donn[eé]es?\b', r'r[eé]partition',
        r'nombre\s+de', r'quelle?\s+(?:est|sont)',
        r'chiffres?', r'bilan', r'r[eé]sum[eé]\s+chiffr',
    ]

    CARBON_PATTERNS = [
        r'carbone', r'\bstock\b', r'biomasse', r'\bco2\b', r'\btco2\b',
        r's[eé]questration', r'[eé]mission', r'puits\s+de\s+carbone',
        r'gaz\s+[aà]\s+effet', r'ges\b',
    ]

    STOCK_CARBONE_PATTERNS = [
        r'spatiali[sz]ation', r'spatiali[sz]er',
        r'carte\s+(?:du\s+)?(?:stock\s+)?carbone',
        r'affiche[r]?\s+(?:le\s+)?(?:stock\s+)?carbone',
        r'montre[r]?\s+(?:le\s+)?(?:stock\s+)?carbone\s+sur\s+(?:la\s+)?carte',
        r'visuali[sz]er?\s+(?:le\s+)?carbone',
        r'mode\s+co2', r'mode\s+carbone',
        r'active[r]?\s+(?:le\s+)?(?:mode\s+)?co2',
        r'active[r]?\s+(?:le\s+)?(?:mode\s+)?carbone',
        r'bouton\s+co2',
        r'stock\s+carbone\s+(?:sur\s+)?(?:la\s+)?carte',
    ]

    DEFORESTATION_PATTERNS = [
        r'd[eé]forestation', r'd[eé]boisement',
        r'perte\s+(?:de\s+)?for[eê]t', r'perte\s+foresti[eè]re',
        r'destruction', r'recul\s+foresti[eè]r',
        r'd[eé]gradation\s+foresti[eè]re',
        r'disparition\s+(?:de[s]?\s+)?for[eê]t',
        r'for[eê]t[s]?\s+perdue', r'couvert\s+perdu',
    ]

    RANKING_PATTERNS = [
        r'class[eé]ment', r'ranking', r'\btop\b',
        r'plus\s+grand[e]?', r'plus\s+petit[e]?',
        r'meilleur', r'pire', r'quelle?\s+for[eê]t\s+a\s+le\s+plus',
        r'laquelle', r'o[uù]\s+(?:est|se\s+trouve)',
        r'plus\s+(?:de|riche)', r'moins\s+(?:de|riche)',
        r'principal', r'important',
    ]

    RESUME_PATTERNS = [
        r'r[eé]sum[eé]', r'vue\s+d.ensemble', r'synth[eè]se',
        r'global[e]?', r'g[eé]n[eé]ral[e]?',
        r'situation\s+(?:de[s]?\s+)?for[eê]t',
        r'[eé]tat\s+(?:de[s]?\s+)?for[eê]t',
        r'tout(?:e[s]?)?\s+(?:le[s]?\s+)?for[eê]t',
        r'ensemble\s+(?:de[s]?\s+)?for[eê]t',
        r'toutes?\s+les?\s+donn[eé]es?',
        r'aper[çc]u',
    ]

    GREETING_PATTERNS = [
        r'^bonjour\b', r'^salut\b', r'^hello\b', r'^bonsoir\b',
        r'^aide\b', r'^help\b', r'^comment\s+([cç]a\s+)?march',
        r'^que\s+peux', r'^qu.est.ce\s+que\s+tu',
        r'^quoi\s+faire', r'^coucou\b', r'^hey\b', r'^hi\b',
        r'^merci\b', r'^ok\b',
    ]

    # ------------------------------------------------------------------
    # Parsing v3 — regex + fuzzy fallback
    # ------------------------------------------------------------------
    def parse(self, query):
        """Analyse une requete en langage naturel et extrait les entites."""
        start = time.time()
        query_stripped = query.strip()
        if len(query_stripped) > 500:
            query_stripped = query_stripped[:500]

        query_lower = query_stripped.lower()
        query_normalized = normalize_text(query_stripped)

        result = {
            'forests': [],
            'cover_types': [],
            'years': [],
            'intent': 'show',
            'raw_query': query_stripped,
            '_inherited': [],
            '_explanation': '',
        }

        # ── Check greetings/help first ──
        for pattern in self.GREETING_PATTERNS:
            if re.search(pattern, query_lower):
                result['intent'] = 'help'
                result['processing_ms'] = int((time.time() - start) * 1000)
                return result

        # ── Extract forests (regex pass) ──
        for pattern, code in self.FOREST_PATTERNS.items():
            if re.search(pattern, query_lower, re.IGNORECASE) or \
               re.search(pattern, query_normalized, re.IGNORECASE):
                if code not in result['forests']:
                    result['forests'].append(code)

        # ── Fuzzy forest matching (if regex found nothing) ──
        if not result['forests']:
            words = re.findall(r'\b[a-zéèêàùôî]{4,}\b', query_normalized)
            forest_keys = list(FOREST_NAMES.keys())
            for word in words:
                matches = get_close_matches(word, forest_keys, n=1, cutoff=0.75)
                if matches:
                    code = FOREST_NAMES[matches[0]]
                    if code not in result['forests']:
                        result['forests'].append(code)
                        result['_explanation'] += f'"{word}" → {matches[0]} (fuzzy). '

        # ── Check for "toutes les forets" ──
        if re.search(r'tout(?:e[s]?)?\s+(?:le[s]?\s+)?for[eê]t', query_lower):
            result['forests'] = []  # empty = all forests
            result['_explanation'] += 'Toutes les forets selectionnees. '

        # ── Extract cover types (regex pass) ──
        for pattern, code in self.COVER_PATTERNS.items():
            if re.search(pattern, query_lower, re.IGNORECASE) or \
               re.search(pattern, query_normalized, re.IGNORECASE):
                if code not in result['cover_types']:
                    result['cover_types'].append(code)

        # ── Fuzzy cover type matching (if regex found nothing) ──
        if not result['cover_types']:
            # Try 2-3 word combinations
            bigrams = []
            words_list = query_normalized.split()
            for i in range(len(words_list)):
                if i + 1 < len(words_list):
                    bigrams.append(words_list[i] + ' ' + words_list[i+1])
                if i + 2 < len(words_list):
                    bigrams.append(words_list[i] + ' ' + words_list[i+1] + ' ' + words_list[i+2])

            cover_keys = list(COVER_NAMES.keys())
            for phrase in bigrams:
                matches = get_close_matches(phrase, cover_keys, n=1, cutoff=0.7)
                if matches:
                    code = COVER_NAMES[matches[0]]
                    if code not in result['cover_types']:
                        result['cover_types'].append(code)
                        result['_explanation'] += f'"{phrase}" → {matches[0]} (fuzzy). '

        # ── Extract years ──
        result['years'] = sorted(set(
            int(y) for y in re.findall(self.YEAR_PATTERN, query_lower)
        ))

        # ── Determine intent (priority order) ──
        intent = self._detect_intent(query_lower, query_normalized)
        result['intent'] = intent

        # ── Auto-defaults for intents that need years ──
        if intent in ('compare', 'deforestation') and len(result['years']) < 2:
            if len(result['years']) == 1:
                y = result['years'][0]
                if y == 2023:
                    result['years'] = [1986, 2023]
                elif y == 1986:
                    result['years'] = [1986, 2023]
                else:
                    result['years'] = [y, 2023]
            else:
                result['years'] = [1986, 2023]
            result['_explanation'] += f'Comparaison auto: {result["years"][0]} vs {result["years"][-1]}. '

        # ── Extract threshold values ──
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

        # ── Detect if ranking should be by carbon ──
        if intent == 'ranking':
            if any(re.search(p, query_lower) for p in self.CARBON_PATTERNS):
                result['ranking_by'] = 'carbone'
            else:
                result['ranking_by'] = 'superficie'

        result['processing_ms'] = int((time.time() - start) * 1000)
        return result

    def _detect_intent(self, query_lower, query_normalized):
        """Detect user intent from query text. Returns intent string."""
        # Priority 1: stock carbone spatialisation
        for p in self.STOCK_CARBONE_PATTERNS:
            if re.search(p, query_lower) or re.search(p, query_normalized):
                return 'stock_carbone'

        # Priority 2: comparison
        for p in self.COMPARISON_PATTERNS:
            if re.search(p, query_lower):
                return 'compare'

        # Priority 3: deforestation
        for p in self.DEFORESTATION_PATTERNS:
            if re.search(p, query_lower) or re.search(p, query_normalized):
                return 'deforestation'

        # Priority 4: resume / overview
        for p in self.RESUME_PATTERNS:
            if re.search(p, query_lower) or re.search(p, query_normalized):
                return 'resume'

        # Priority 5: stats
        for p in self.STATS_PATTERNS:
            if re.search(p, query_lower):
                return 'stats'

        # Priority 6: carbon
        for p in self.CARBON_PATTERNS:
            if re.search(p, query_lower):
                return 'carbon'

        # Priority 7: ranking
        for p in self.RANKING_PATTERNS:
            if re.search(p, query_lower) or re.search(p, query_normalized):
                return 'ranking'

        return 'show'

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
        """Classement des forets par superficie OU carbone selon le contexte."""
        from apps.carbone.models import OccupationSol

        annee = parsed['years'][-1] if parsed['years'] else 2023
        cover_filter = {}
        if parsed['cover_types']:
            cover_filter['nomenclature__code__in'] = parsed['cover_types']
        else:
            cover_filter['nomenclature__code__in'] = [
                'FORET_DENSE', 'FORET_CLAIRE', 'FORET_DEGRADEE',
            ]

        # Sort by carbon if the user asked about carbon, otherwise by area
        sort_field = '-total_carbone' if parsed.get('ranking_by') == 'carbone' else '-total_superficie_ha'

        return list(OccupationSol.objects.filter(
            annee=annee, **cover_filter,
        ).values(
            'foret__code', 'foret__nom',
        ).annotate(
            total_superficie_ha=Sum('superficie_ha'),
            total_carbone=Sum('stock_carbone_calcule'),
            nombre_polygones=Count('id'),
        ).order_by(sort_field))

    def build_resume(self, parsed):
        """Vue d'ensemble / synthese globale pour une annee."""
        from apps.carbone.models import OccupationSol, ForetClassee

        annee = parsed['years'][-1] if parsed['years'] else 2023
        base_filter = {'annee': annee}
        if parsed['forests']:
            base_filter['foret__code__in'] = parsed['forests']

        # Stats par type
        by_type = list(OccupationSol.objects.filter(**base_filter).values(
            'nomenclature__code',
            'nomenclature__libelle_fr',
            'nomenclature__couleur_hex',
        ).annotate(
            total_superficie_ha=Sum('superficie_ha'),
            total_carbone=Sum('stock_carbone_calcule'),
            nombre_polygones=Count('id'),
        ).order_by('nomenclature__ordre_affichage'))

        # Totaux
        totaux = OccupationSol.objects.filter(**base_filter).aggregate(
            superficie=Sum('superficie_ha'),
            carbone=Sum('stock_carbone_calcule'),
            polygones=Count('id'),
        )

        # Stats par foret
        by_forest = list(OccupationSol.objects.filter(**base_filter).values(
            'foret__code', 'foret__nom',
        ).annotate(
            total_superficie_ha=Sum('superficie_ha'),
            total_carbone=Sum('stock_carbone_calcule'),
        ).order_by('-total_superficie_ha'))

        # Nombre de forets dans la DB
        nb_forets = ForetClassee.objects.count()

        return {
            'annee': annee,
            'nb_forets': nb_forets,
            'totaux': {
                'superficie_ha': round(float(totaux['superficie'] or 0), 1),
                'carbone_tco2': round(float(totaux['carbone'] or 0), 1),
                'nb_polygones': totaux['polygones'] or 0,
            },
            'par_type': by_type,
            'par_foret': by_forest,
        }

    # ------------------------------------------------------------------
    # Smart suggestions v3
    # ------------------------------------------------------------------
    def suggest_queries(self, parsed):
        """Generate contextual query suggestions."""
        suggestions = []

        if not parsed['forests'] and not parsed['cover_types'] and not parsed['years']:
            suggestions = [
                "Montre les zones de foret dense a TENE en 2023",
                "Quelle est la superficie de foret a DOKA en 2003 ?",
                "Compare TENE entre 1986 et 2023",
                "Deforestation a LAHOUDA",
                "Stock carbone pour 2023",
                "Classement des forets par carbone",
                "Resume global pour 2023",
                "Active le mode CO2 sur la carte",
            ]
        else:
            if not parsed['forests']:
                suggestions.append(
                    "Precisez une foret : TENE, DOKA, SANGOUE, LAHOUDA, ZOUEKE"
                )
            if not parsed['cover_types']:
                suggestions.append(
                    "Precisez un type : foret dense, foret claire, jachere, cacao, hevea"
                )
            if not parsed['years']:
                suggestions.append(
                    "Precisez une annee : 1986, 2003 ou 2023"
                )
            # Suggest related queries
            if parsed['forests']:
                f = parsed['forests'][0]
                suggestions.append(f"Compare {f} entre 1986 et 2023")
                suggestions.append(f"Deforestation a {f}")

        return suggestions
