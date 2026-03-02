"""
Moteur NLP pour le module Chat-to-Map.
Extraction d'entites nommees depuis des requetes en francais
et construction securisee de filtres Django ORM.

Version 4.0 — "Extraordinaire" :
- Tout de v3 conserve (fuzzy, synonymes, intents, etc.)
- FUN_FACTS : 25+ faits ecologiques par theme
- get_fun_fact(intent, cover_types) : selection contextuelle
- get_suggestions(parsed, session_context) : suggestions de suivi intelligentes
- compute_confidence(parsed) : score 0-100
- FOREST_CENTERS : coordonnees geographiques des 6 forets
- chart_data helpers : pre-formatage pour Chart.js
"""
import re
import time
import random
import unicodedata
from difflib import get_close_matches
from django.db.models import Sum, Count, F


def normalize_text(text):
    """Remove accents and convert to lowercase for fuzzy matching."""
    nfkd = unicodedata.normalize('NFKD', text)
    return ''.join(c for c in nfkd if not unicodedata.combining(c)).lower()


# ======================================================================
# Forest geographic centers (lat, lng) for map fly-to
# ======================================================================
FOREST_CENTERS = {
    'TENE':     [6.525, -5.718],
    'DOKA':     [6.398, -5.603],
    'SANGOUE':  [6.350, -5.480],
    'LAHOUDA':  [6.290, -5.390],
    'ZOUEKE_1': [6.440, -5.550],
    'ZOUEKE_2': [6.410, -5.520],
}

# ======================================================================
# Fun facts — 25+ ecology/carbon facts, grouped by theme
# ======================================================================
FUN_FACTS = {
    'foret': [
        "Les forets tropicales ne couvrent que 6% des terres emergees, mais abritent plus de 50% de la biodiversite mondiale.",
        "Un hectare de foret tropicale peut absorber jusqu'a 6 tonnes de CO2 par an.",
        "La Cote d'Ivoire a perdu plus de 80% de son couvert forestier entre 1960 et 2020.",
        "Le departement d'Oume abrite 6 forets classees totalisant 81 056 hectares de superficie legale.",
        "Une foret dense mature peut stocker plus de 3 000 tCO2 par hectare dans sa biomasse.",
        "Les racines des arbres tropicaux peuvent s'enfoncer a plus de 30 metres de profondeur.",
        "Un grand arbre tropical transpire jusqu'a 1 000 litres d'eau par jour.",
    ],
    'carbone': [
        "Le stock de carbone forestier est un indicateur cle du Programme REDD+ de l'ONU.",
        "La foret claire de la zone d'Oume stocke en moyenne 3 308 tCO2/ha — le taux le plus eleve.",
        "La sequestration du carbone dans le sol forestier represente 40 a 60% du stock total.",
        "Bruler 1 hectare de foret tropicale libere l'equivalent des emissions annuelles de 500 voitures.",
        "Les mangroves stockent 3 a 5 fois plus de carbone par hectare que les forets terrestres.",
        "Le marche mondial du credit carbone forestier a depasse 2 milliards USD en 2023.",
    ],
    'deforestation': [
        "L'agriculture (cacao, cafe) est la 1ere cause de deforestation en Cote d'Ivoire.",
        "Chaque minute, l'equivalent de 40 terrains de football de foret tropicale disparait.",
        "La deforestation est responsable de 10 a 15% des emissions mondiales de gaz a effet de serre.",
        "Le cacao represente a lui seul 38% de la deforestation en Cote d'Ivoire.",
        "La Cote d'Ivoire est le 1er producteur mondial de cacao avec 2,2 millions de tonnes/an.",
        "L'agroforesterie peut reduire la deforestation de 30% tout en maintenant les rendements.",
    ],
    'agriculture': [
        "Les systemes agroforestiers cacao-foret peuvent stocker jusqu'a 60 tC/ha.",
        "L'hevea (caoutchouc) couvre de plus en plus les zones anciennement boisees d'Oume.",
        "La culture du cafe sous ombrage conserve 50% du stock carbone originel de la foret.",
        "Les jacheres representent un potentiel de regeneration naturelle important pour la zone.",
        "Un cacaoyer bien gere peut produire pendant 30 a 40 ans sur la meme parcelle.",
    ],
    'general': [
        "L'imagerie satellite Sentinel-2 utilisee ici a une resolution de 10 metres.",
        "Les donnees couvrent 3 epoques : 1986 (Landsat), 2003 (Landsat) et 2023 (Sentinel-2).",
        "La classification supervisee utilisee a un taux de precision global superieur a 85%.",
        "L'API.GEO.Carbone combine PostGIS, Django et Leaflet pour l'analyse spatiale.",
    ],
}


def get_fun_fact(intent='general', cover_types=None):
    """Select a contextual fun fact based on intent and cover types."""
    # Choose theme based on context
    if intent in ('deforestation',):
        theme = 'deforestation'
    elif intent in ('carbon', 'stock_carbone'):
        theme = 'carbone'
    elif intent in ('ranking', 'resume', 'stats'):
        theme = random.choice(['foret', 'carbone', 'general'])
    elif cover_types and any(c in ('CACAO', 'CAFE', 'HEVEA', 'CULTURE_HERBACEE') for c in cover_types):
        theme = 'agriculture'
    else:
        theme = random.choice(['foret', 'carbone', 'general'])

    facts = FUN_FACTS.get(theme, FUN_FACTS['general'])
    return random.choice(facts)


def get_suggestions(parsed, session_context=None):
    """Generate smart contextual next-step suggestions."""
    intent = parsed.get('intent', 'show')
    forests = parsed.get('forests', [])
    years = parsed.get('years', [])
    suggestions = []

    if intent == 'stats':
        suggestions.append('Classement des forets par carbone')
        if forests:
            suggestions.append(f'Compare {forests[0]} entre 1986 et 2023')
        suggestions.append('Active le mode CO2 sur la carte')
        suggestions.append('Resume global pour 2023')

    elif intent == 'compare':
        suggestions.append('Analyse de deforestation')
        if forests:
            suggestions.append(f'Resume de {forests[0]}')
        suggestions.append('Classement par superficie')

    elif intent == 'deforestation':
        suggestions.append('Resume global pour 2023')
        suggestions.append('Active le mode CO2')
        if forests:
            suggestions.append(f'Statistiques de {forests[0]} en 2023')

    elif intent == 'ranking':
        by = parsed.get('ranking_by', 'superficie')
        alt = 'carbone' if by == 'superficie' else 'superficie'
        suggestions.append(f'Classement par {alt}')
        suggestions.append('Compare entre 1986 et 2023')
        suggestions.append('Resume global')

    elif intent == 'stock_carbone':
        suggestions.append('Resume global pour 2023')
        suggestions.append('Classement des forets par carbone')
        suggestions.append('Deforestation entre 1986 et 2023')

    elif intent == 'resume':
        suggestions.append('Compare entre 1986 et 2023')
        suggestions.append('Deforestation globale')
        suggestions.append('Active le mode CO2')

    elif intent == 'help':
        suggestions.append('Resume global pour 2023')
        suggestions.append('Montre la foret dense a TENE')
        suggestions.append('Classement des forets')

    elif intent == 'show':
        if forests:
            suggestions.append(f'Statistiques de {forests[0]}')
            suggestions.append(f'Compare {forests[0]} 1986 vs 2023')
        else:
            suggestions.append('Resume global pour 2023')
        suggestions.append('Active le mode carbone')

    else:
        suggestions.append('Resume global')
        suggestions.append('Classement des forets')
        suggestions.append('Active le mode CO2')

    return suggestions[:4]


def compute_confidence(parsed):
    """Compute a confidence score 0-100 based on parsing quality."""
    score = 50  # Base score

    # Boost for exact regex matches (no fuzzy)
    explanation = parsed.get('_explanation', '')
    if 'fuzzy' in explanation:
        score += 20  # Fuzzy still good but not perfect
    elif parsed['forests'] or parsed['cover_types']:
        score += 40  # Exact regex match

    # Boost for years found
    if parsed['years']:
        score += 10

    # Boost for clear intent (not default 'show')
    if parsed['intent'] != 'show':
        score += 10

    # Penalty for no entities at all
    if not parsed['forests'] and not parsed['cover_types'] and not parsed['years']:
        score -= 20

    return max(10, min(100, score))


# ======================================================================
# Fuzzy matching dictionaries (for difflib)
# ======================================================================
FOREST_NAMES = {
    'tene': 'TENE', 'tene': 'TENE', 'tene': 'TENE',
    'doka': 'DOKA',
    'sangoue': 'SANGOUE', 'sangoue': 'SANGOUE', 'sangue': 'SANGOUE',
    'lahouda': 'LAHOUDA', 'lahouda': 'LAHOUDA',
    'zoueke': 'ZOUEKE_1', 'zoueke': 'ZOUEKE_1', 'zoueke 1': 'ZOUEKE_1',
    'zoueke 2': 'ZOUEKE_2', 'zoueke 2': 'ZOUEKE_2',
    'zoueke bloc 1': 'ZOUEKE_1', 'zoueke bloc 2': 'ZOUEKE_2',
    'zoueke i': 'ZOUEKE_1', 'zoueke ii': 'ZOUEKE_2',
}

COVER_NAMES = {
    'foret dense': 'FORET_DENSE', 'foret dense': 'FORET_DENSE',
    'bois dense': 'FORET_DENSE', 'foret primaire': 'FORET_DENSE',
    'vieille foret': 'FORET_DENSE', 'grande foret': 'FORET_DENSE',
    'foret claire': 'FORET_CLAIRE', 'foret claire': 'FORET_CLAIRE',
    'bois clair': 'FORET_CLAIRE', 'foret secondaire': 'FORET_CLAIRE',
    'foret ouverte': 'FORET_CLAIRE',
    'foret degradee': 'FORET_DEGRADEE', 'foret degradee': 'FORET_DEGRADEE',
    'foret abimee': 'FORET_DEGRADEE', 'foret endommagee': 'FORET_DEGRADEE',
    'foret perturbee': 'FORET_DEGRADEE',
    'jachere': 'JACHERE', 'jachere': 'JACHERE', 'friche': 'JACHERE',
    'reboisement': 'JACHERE', 'jeune foret': 'JACHERE',
    'repousse': 'JACHERE', 'regeneration': 'JACHERE',
    'cacao': 'CACAO', 'cacaoyer': 'CACAO', 'cacaoculture': 'CACAO',
    'plantation cacao': 'CACAO', 'chocolat': 'CACAO',
    'cafe': 'CAFE', 'cafe': 'CAFE', 'cafeier': 'CAFE',
    'cafeiculture': 'CAFE', 'plantation cafe': 'CAFE',
    'hevea': 'HEVEA', 'hevea': 'HEVEA', 'caoutchouc': 'HEVEA',
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
    """Pipeline NLP v4: requete francaise -> entites -> filtre Django ORM."""

    # ------------------------------------------------------------------
    # Entity patterns (regex -- first pass)
    # ------------------------------------------------------------------
    FOREST_PATTERNS = {
        r'\btene\b': 'TENE', r'\bten[eE]\b': 'TENE', r'\bt[eE]n[eE]\b': 'TENE',
        r'\bdoka\b': 'DOKA',
        r'\bsangou[eE]\b': 'SANGOUE', r'\bsangu[eE]\b': 'SANGOUE',
        r'\blahouda\b': 'LAHOUDA',
        r'\bzou[eE]k[eE]\s*(?:bloc\s*)?(?:1|i)\b': 'ZOUEKE_1',
        r'\bzou[eE]k[eE]\s*(?:bloc\s*)?(?:2|ii)\b': 'ZOUEKE_2',
        r'\bzou[eE]k[eE]\b': 'ZOUEKE_1',
    }

    COVER_PATTERNS = {
        r'\bfor[eE]t\s+dense\b': 'FORET_DENSE',
        r'\bfor[eE]t\s+clair[e]?\b': 'FORET_CLAIRE',
        r'\bfor[eE]t\s+d[eE]grad[eE]e?\b': 'FORET_DEGRADEE',
        r'\bjach[eE]re\b': 'JACHERE',
        r'\bcacao(?:yer|culture)?\b': 'CACAO',
        r'\bcaf[eE](?:ier|iculture)?\b': 'CAFE',
        r'\bh[eE]v[eE]a\b': 'HEVEA',
        r'\bcaoutchouc\b': 'HEVEA',
        r'\bculture\s*(?:annuelle|herbac[eE]e|vivri[eE]re)?\b': 'CULTURE_HERBACEE',
        r'\bsol\s+nu\b': 'SOL_NU',
        r'\bbois\s+dense\b': 'FORET_DENSE',
        r'\bbois\s+clair\b': 'FORET_CLAIRE',
        r'\bfor[eE]t\s+primaire\b': 'FORET_DENSE',
        r'\bfor[eE]t\s+secondaire\b': 'FORET_CLAIRE',
        r'\breboisement\b': 'JACHERE',
        r'\bfriche\b': 'JACHERE',
        r'\bplantation\b': 'CACAO',
        r'\bzone\s+d[eE]bois[eE]e?\b': 'SOL_NU',
        r'\bterrain\s+nu\b': 'SOL_NU',
        r'\bchamps?\b': 'CULTURE_HERBACEE',
        r'\bagriculture\b': 'CULTURE_HERBACEE',
        r'\bmanioc\b': 'CULTURE_HERBACEE',
        r'\briz\b': 'CULTURE_HERBACEE',
        r'\bma[iI]s\b': 'CULTURE_HERBACEE',
        r'\blatex\b': 'HEVEA',
        r'\bchocolat\b': 'CACAO',
    }

    YEAR_PATTERN = r'\b(1986|2003|2023)\b'

    # ------------------------------------------------------------------
    # Intent patterns (enriched v3)
    # ------------------------------------------------------------------
    COMPARISON_PATTERNS = [
        r'compar[eE]', r'[eE]volution', r'diff[eE]ren',
        r'entre\s+\d{4}\s+et\s+\d{4}', r'de\s+\d{4}\s+[aA]\s+\d{4}',
        r'changement', r'avant\s+apr[eE]s', r'progression',
        r'comment\s+a\s+[eE]volu', r'qu.est.ce\s+qui\s+a\s+chang',
    ]

    STATS_PATTERNS = [
        r'superficie', r'surface', r'combien', r'total[e]?',
        r'statistiq', r'donn[eE]es?\b', r'r[eE]partition',
        r'nombre\s+de', r'quelle?\s+(?:est|sont)',
        r'chiffres?', r'bilan', r'r[eE]sum[eE]\s+chiffr',
    ]

    CARBON_PATTERNS = [
        r'carbone', r'\bstock\b', r'biomasse', r'\bco2\b', r'\btco2\b',
        r's[eE]questration', r'[eE]mission', r'puits\s+de\s+carbone',
        r'gaz\s+[aA]\s+effet', r'ges\b',
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
        r'd[eE]forestation', r'd[eE]boisement',
        r'perte\s+(?:de\s+)?for[eE]t', r'perte\s+foresti[eE]re',
        r'destruction', r'recul\s+foresti[eE]r',
        r'd[eE]gradation\s+foresti[eE]re',
        r'disparition\s+(?:de[s]?\s+)?for[eE]t',
        r'for[eE]t[s]?\s+perdue', r'couvert\s+perdu',
    ]

    RANKING_PATTERNS = [
        r'class[eE]ment', r'ranking', r'\btop\b',
        r'plus\s+grand[e]?', r'plus\s+petit[e]?',
        r'meilleur', r'pire', r'quelle?\s+for[eE]t\s+a\s+le\s+plus',
        r'laquelle', r'o[uU]\s+(?:est|se\s+trouve)',
        r'plus\s+(?:de|riche)', r'moins\s+(?:de|riche)',
        r'principal', r'important',
    ]

    RESUME_PATTERNS = [
        r'r[eE]sum[eE]', r'vue\s+d.ensemble', r'synth[eE]se',
        r'global[e]?', r'g[eE]n[eE]ral[e]?',
        r'situation\s+(?:de[s]?\s+)?for[eE]t',
        r'[eE]tat\s+(?:de[s]?\s+)?for[eE]t',
        r'tout(?:e[s]?)?\s+(?:le[s]?\s+)?for[eE]t',
        r'ensemble\s+(?:de[s]?\s+)?for[eE]t',
        r'toutes?\s+les?\s+donn[eE]es?',
        r'aper[cC]u',
    ]

    GREETING_PATTERNS = [
        r'^bonjour\b', r'^salut\b', r'^hello\b', r'^bonsoir\b',
        r'^aide\b', r'^help\b', r'^comment\s+([cC]a\s+)?march',
        r'^que\s+peux', r'^qu.est.ce\s+que\s+tu',
        r'^quoi\s+faire', r'^coucou\b', r'^hey\b', r'^hi\b',
        r'^merci\b', r'^ok\b',
    ]

    # ------------------------------------------------------------------
    # Parsing v4 -- regex + fuzzy fallback
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

        # -- Check greetings/help first --
        for pattern in self.GREETING_PATTERNS:
            if re.search(pattern, query_lower):
                result['intent'] = 'help'
                result['processing_ms'] = int((time.time() - start) * 1000)
                return result

        # -- Extract forests (regex pass) --
        for pattern, code in self.FOREST_PATTERNS.items():
            if re.search(pattern, query_lower, re.IGNORECASE) or \
               re.search(pattern, query_normalized, re.IGNORECASE):
                if code not in result['forests']:
                    result['forests'].append(code)

        # -- Fuzzy forest matching (if regex found nothing) --
        if not result['forests']:
            words = re.findall(r'\b[a-z]{4,}\b', query_normalized)
            forest_keys = list(FOREST_NAMES.keys())
            for word in words:
                matches = get_close_matches(word, forest_keys, n=1, cutoff=0.75)
                if matches:
                    code = FOREST_NAMES[matches[0]]
                    if code not in result['forests']:
                        result['forests'].append(code)
                        result['_explanation'] += f'"{word}" -> {matches[0]} (fuzzy). '

        # -- Check for "toutes les forets" --
        if re.search(r'tout(?:e[s]?)?\s+(?:le[s]?\s+)?for[eE]t', query_lower):
            result['forests'] = []
            result['_explanation'] += 'Toutes les forets selectionnees. '

        # -- Extract cover types (regex pass) --
        for pattern, code in self.COVER_PATTERNS.items():
            if re.search(pattern, query_lower, re.IGNORECASE) or \
               re.search(pattern, query_normalized, re.IGNORECASE):
                if code not in result['cover_types']:
                    result['cover_types'].append(code)

        # -- Fuzzy cover type matching (if regex found nothing) --
        if not result['cover_types']:
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
                        result['_explanation'] += f'"{phrase}" -> {matches[0]} (fuzzy). '

        # -- Extract years --
        result['years'] = sorted(set(
            int(y) for y in re.findall(self.YEAR_PATTERN, query_lower)
        ))

        # -- Determine intent (priority order) --
        intent = self._detect_intent(query_lower, query_normalized)
        result['intent'] = intent

        # -- Auto-defaults for intents that need years --
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

        # -- Extract threshold values --
        threshold_match = re.search(
            r'(?:sup[eE]rieur|inf[eE]rieur|plus|moins)\s+(?:[aA]|de)\s+(\d+(?:[.,]\d+)?)',
            query_lower,
        )
        if threshold_match:
            val = threshold_match.group(1).replace(',', '.')
            result['threshold'] = float(val)
            if re.search(r'(?:inf[eE]rieur|moins)', query_lower):
                result['threshold_op'] = 'lte'
            else:
                result['threshold_op'] = 'gte'

        # -- Detect if ranking should be by carbon --
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

        by_type = list(OccupationSol.objects.filter(**base_filter).values(
            'nomenclature__code',
            'nomenclature__libelle_fr',
            'nomenclature__couleur_hex',
        ).annotate(
            total_superficie_ha=Sum('superficie_ha'),
            total_carbone=Sum('stock_carbone_calcule'),
            nombre_polygones=Count('id'),
        ).order_by('nomenclature__ordre_affichage'))

        totaux = OccupationSol.objects.filter(**base_filter).aggregate(
            superficie=Sum('superficie_ha'),
            carbone=Sum('stock_carbone_calcule'),
            polygones=Count('id'),
        )

        by_forest = list(OccupationSol.objects.filter(**base_filter).values(
            'foret__code', 'foret__nom',
        ).annotate(
            total_superficie_ha=Sum('superficie_ha'),
            total_carbone=Sum('stock_carbone_calcule'),
        ).order_by('-total_superficie_ha'))

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
            if parsed['forests']:
                f = parsed['forests'][0]
                suggestions.append(f"Compare {f} entre 1986 et 2023")
                suggestions.append(f"Deforestation a {f}")

        return suggestions
