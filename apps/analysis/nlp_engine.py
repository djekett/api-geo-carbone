"""
Moteur NLP pour le module Chat-to-Map.
Extraction d'entites nommees depuis des requetes en francais
et construction securisee de filtres Django ORM.

Version 3.0 : synonymes etendus, intents enrichis (help, deforestation,
ranking, prediction, export, area_calc), normalisation sans accents,
suggestions intelligentes, analyse de deforestation, fuzzy matching,
multi-forest, temporal expressions, quantitative qualifiers,
percentage/fraction extraction, prediction lineaire, calcul de superficie.
"""
import re
import time
import unicodedata
from django.db.models import Sum, Count


def normalize_text(text):
    """Remove accents and convert to lowercase for fuzzy matching."""
    nfkd = unicodedata.normalize('NFKD', text)
    return ''.join(c for c in nfkd if not unicodedata.combining(c)).lower()


def levenshtein_distance(s1, s2):
    """Compute the Levenshtein distance between two strings."""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)
    prev_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        curr_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = prev_row[j + 1] + 1
            deletions = curr_row[j] + 1
            substitutions = prev_row[j] + (c1 != c2)
            curr_row.append(min(insertions, deletions, substitutions))
        prev_row = curr_row
    return prev_row[-1]


class NLPEngine:
    """Pipeline NLP: requete francaise -> entites -> filtre Django ORM."""

    # ------------------------------------------------------------------
    # Forest aliases for fuzzy matching (common misspellings/abbreviations)
    # ------------------------------------------------------------------
    FOREST_ALIASES = {
        'tene': 'TENE', 'tené': 'TENE', 'téné': 'TENE',
        'doka': 'DOKA',
        'sangoué': 'SANGOUE', 'sangue': 'SANGOUE', 'sangoue': 'SANGOUE',
        'lahouda': 'LAHOUDA', 'la houda': 'LAHOUDA',
        'zouéké': 'ZOUEKE_1', 'zoueke': 'ZOUEKE_1', 'zoueké': 'ZOUEKE_1',
        'zouéké 1': 'ZOUEKE_1', 'zouéké bloc 1': 'ZOUEKE_1',
        'zouéké 2': 'ZOUEKE_2', 'zouéké bloc 2': 'ZOUEKE_2',
        'zoueke 1': 'ZOUEKE_1', 'zoueke bloc 1': 'ZOUEKE_1',
        'zoueke 2': 'ZOUEKE_2', 'zoueke bloc 2': 'ZOUEKE_2',
    }

    # Canonical forest names for Levenshtein fallback
    FOREST_CANONICAL = {
        'tene': 'TENE',
        'doka': 'DOKA',
        'sangoue': 'SANGOUE',
        'lahouda': 'LAHOUDA',
        'zoueke': 'ZOUEKE_1',
    }

    # ------------------------------------------------------------------
    # Entity patterns
    # ------------------------------------------------------------------
    FOREST_PATTERNS = {
        r'\btene\b': 'TENE',
        r'\bten[eé]\b': 'TENE',
        r'\bdoka\b': 'DOKA',
        r'\bsangou[eé]\b': 'SANGOUE',
        r'\blahouda\b': 'LAHOUDA',
        r'\bla\s+houda\b': 'LAHOUDA',
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

    PREDICTION_PATTERNS = [
        r'pr[eé]vision',
        r'pr[eé]dire',
        r'futur',
        r'tendance',
        r'projection',
        r'si\s+(?:ca|ça)\s+continue',
        r'extrapolation',
        r'pr[eé]diction',
        r'estimer?\s+(?:en\s+)?\d{4}',
        r'(?:en|pour|vers)\s+20[3-9]\d',
    ]

    EXPORT_PATTERNS = [
        r'export',
        r't[eé]l[eé]charger',
        r'download',
        r'pdf',
        r'rapport',
        r'g[eé]n[eé]rer?\s+(?:un\s+)?(?:fichier|document)',
        r'sauvegarder',
    ]

    AREA_CALCULATION_PATTERNS = [
        r'calculer?\s+(?:la\s+)?superficie',
        r'mesurer?\s+(?:la\s+)?surface',
        r'(?:superficie|surface)\s+totale',
        r'combien\s+(?:d[\'e]\s*)?hectares',
        r'nombre\s+d[\'e]\s*hectares',
        r'total\s+(?:des?\s+)?(?:surfaces?|superficies?)',
    ]

    PERCENTAGE_PATTERNS = [
        r'pourcentage\s+(?:de\s+)?',
        r'part\s+(?:de\s+)?',
        r'proportion\s+(?:de\s+)?',
        r'ratio\s+(?:de\s+)?',
        r'taux\s+(?:de\s+)?',
        r'%\s+(?:de\s+)?',
        r'en\s+pourcentage',
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
    # Temporal expression patterns
    # ------------------------------------------------------------------
    TEMPORAL_BEFORE_PATTERN = r'avant\s+(\d{4})'
    TEMPORAL_AFTER_PATTERN = r'apr[eè]s\s+(\d{4})'
    TEMPORAL_BETWEEN_PATTERN = r'entre\s+(\d{4})\s+et\s+(\d{4})'

    # ------------------------------------------------------------------
    # Quantitative qualifier patterns
    # ------------------------------------------------------------------
    SUPERLATIVE_LARGEST = [
        r'(?:la\s+)?plus\s+grande?\s+(?:for[eê]t)?',
        r'(?:la\s+)?plus\s+vaste',
        r'(?:la\s+)?plus\s+[eé]tendue',
    ]

    SUPERLATIVE_SMALLEST = [
        r'(?:la\s+)?plus\s+petite?\s+(?:for[eê]t)?',
        r'(?:la\s+)?moins\s+grande?',
        r'(?:la\s+)?moins\s+[eé]tendue',
    ]

    THRESHOLD_PATTERNS = [
        r'plus\s+de\s+(\d+(?:[.,]\d+)?)\s*(?:ha|hectares?)',
        r'sup[eé]rieur[e]?\s+[aà]\s+(\d+(?:[.,]\d+)?)\s*(?:ha|hectares?)',
        r'moins\s+de\s+(\d+(?:[.,]\d+)?)\s*(?:ha|hectares?)',
        r'inf[eé]rieur[e]?\s+[aà]\s+(\d+(?:[.,]\d+)?)\s*(?:ha|hectares?)',
    ]

    # ------------------------------------------------------------------
    # Fuzzy matching
    # ------------------------------------------------------------------
    def fuzzy_match_forest(self, word):
        """
        Try to match a word to a known forest using Levenshtein distance.
        Returns the forest code if a close match is found (distance <= 2),
        None otherwise.
        """
        word_norm = normalize_text(word)

        # First try exact alias match
        if word_norm in self.FOREST_ALIASES:
            return self.FOREST_ALIASES[word_norm]

        # Then try Levenshtein distance against canonical names
        best_match = None
        best_distance = float('inf')

        for canonical, code in self.FOREST_CANONICAL.items():
            dist = levenshtein_distance(word_norm, canonical)
            if dist < best_distance:
                best_distance = dist
                best_match = code

        # Accept if distance <= 2 (tolerate small typos)
        max_dist = 2 if len(word_norm) > 4 else 1
        if best_distance <= max_dist:
            return best_match

        return None

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
            'confidence': 0.0,
            'percentage_mode': False,
            'sort_order': None,
            'target_year': None,
        }

        entity_matches = 0

        # Check greetings/help first
        for pattern in self.GREETING_PATTERNS:
            if re.search(pattern, query_lower):
                result['intent'] = 'help'
                result['confidence'] = 1.0
                result['processing_ms'] = int((time.time() - start) * 1000)
                return result

        # Extract forests (try both accented and normalized)
        for pattern, code in self.FOREST_PATTERNS.items():
            if re.search(pattern, query_lower, re.IGNORECASE) or \
               re.search(pattern, query_normalized, re.IGNORECASE):
                if code not in result['forests']:
                    result['forests'].append(code)
                    entity_matches += 1

        # Fuzzy fallback: check aliases and Levenshtein for unrecognized words
        if not result['forests']:
            # Try multi-word alias matches first (e.g. "la houda")
            for alias, code in self.FOREST_ALIASES.items():
                if ' ' in alias and alias in query_normalized:
                    if code not in result['forests']:
                        result['forests'].append(code)
                        entity_matches += 1

            # Then try individual words
            if not result['forests']:
                words = re.findall(r'\b[a-zA-ZÀ-ÿ]{4,}\b', query)
                # Exclude common French words that are NOT forest names
                stop_words = {
                    'dans', 'pour', 'avec', 'entre', 'avant', 'apres',
                    'foret', 'dense', 'claire', 'quelle', 'quelles',
                    'combien', 'superficie', 'surface', 'carbone',
                    'cacao', 'cafe', 'hevea', 'jachere', 'culture',
                    'total', 'annee', 'compare', 'montre', 'affiche',
                    'classement', 'deforestation', 'degradation',
                    'statistiques', 'statistique', 'donnees', 'donnee',
                    'prediction', 'prevision', 'projection', 'tendance',
                    'exporter', 'rapport', 'telecharger', 'calculer',
                    'mesurer', 'pourcentage', 'proportion', 'degradee',
                }
                for word in words:
                    if normalize_text(word) in stop_words:
                        continue
                    matched = self.fuzzy_match_forest(word)
                    if matched and matched not in result['forests']:
                        result['forests'].append(matched)
                        entity_matches += 1

        # Multi-forest: detect "TENE et DOKA", "TENE, DOKA et SANGOUE" patterns
        multi_match = re.findall(
            r'\b([A-ZÀ-Ÿa-zà-ÿ]{3,})\b\s*(?:,\s*|\s+et\s+)\s*\b([A-ZÀ-Ÿa-zà-ÿ]{3,})\b',
            query, re.IGNORECASE,
        )
        for pair in multi_match:
            for word in pair:
                matched = self.fuzzy_match_forest(word)
                if matched and matched not in result['forests']:
                    result['forests'].append(matched)
                    entity_matches += 1

        # Extract cover types
        for pattern, code in self.COVER_PATTERNS.items():
            if re.search(pattern, query_lower, re.IGNORECASE) or \
               re.search(pattern, query_normalized, re.IGNORECASE):
                if code not in result['cover_types']:
                    result['cover_types'].append(code)
                    entity_matches += 1

        # Extract years (standard exact match)
        result['years'] = sorted(set(
            int(y) for y in re.findall(self.YEAR_PATTERN, query_lower)
        ))
        if result['years']:
            entity_matches += 1

        # Temporal expressions: avant/apres/entre
        before_match = re.search(self.TEMPORAL_BEFORE_PATTERN, query_normalized)
        if before_match:
            cutoff = int(before_match.group(1))
            result['temporal'] = {'type': 'before', 'year': cutoff}
            available = [y for y in [1986, 2003, 2023] if y < cutoff]
            if available:
                result['years'] = sorted(set(result['years'] + available))
            entity_matches += 1

        after_match = re.search(self.TEMPORAL_AFTER_PATTERN, query_normalized)
        if after_match:
            cutoff = int(after_match.group(1))
            result['temporal'] = {'type': 'after', 'year': cutoff}
            available = [y for y in [1986, 2003, 2023] if y > cutoff]
            if available:
                result['years'] = sorted(set(result['years'] + available))
            entity_matches += 1

        between_match = re.search(self.TEMPORAL_BETWEEN_PATTERN, query_normalized)
        if between_match:
            y1, y2 = int(between_match.group(1)), int(between_match.group(2))
            result['temporal'] = {'type': 'between', 'start': y1, 'end': y2}
            available = [y for y in [1986, 2003, 2023] if y1 <= y <= y2]
            if available:
                result['years'] = sorted(set(result['years'] + available))
            entity_matches += 1

        # Extract future target year for predictions
        future_match = re.search(r'\b(20[3-9]\d|2100)\b', query_lower)
        if future_match:
            result['target_year'] = int(future_match.group(1))

        # Percentage/fraction extraction
        for pattern in self.PERCENTAGE_PATTERNS:
            if re.search(pattern, query_lower):
                result['percentage_mode'] = True
                entity_matches += 1
                break

        # Quantitative qualifiers: superlatives
        for pattern in self.SUPERLATIVE_LARGEST:
            if re.search(pattern, query_lower):
                result['sort_order'] = 'desc'
                entity_matches += 1
                break

        if not result.get('sort_order'):
            for pattern in self.SUPERLATIVE_SMALLEST:
                if re.search(pattern, query_lower):
                    result['sort_order'] = 'asc'
                    entity_matches += 1
                    break

        # Determine intent (priority: prediction > export > area_calc > compare > deforestation > stats > carbon > ranking > show)

        # PREDICTION intent
        intent_found = False
        for pattern in self.PREDICTION_PATTERNS:
            if re.search(pattern, query_lower) or re.search(pattern, query_normalized):
                result['intent'] = 'prediction'
                if not result['target_year']:
                    result['target_year'] = 2030  # default projection year
                intent_found = True
                entity_matches += 1
                break

        # EXPORT intent
        if not intent_found:
            for pattern in self.EXPORT_PATTERNS:
                if re.search(pattern, query_lower) or re.search(pattern, query_normalized):
                    result['intent'] = 'export'
                    intent_found = True
                    entity_matches += 1
                    break

        # AREA_CALC intent
        if not intent_found:
            for pattern in self.AREA_CALCULATION_PATTERNS:
                if re.search(pattern, query_lower) or re.search(pattern, query_normalized):
                    result['intent'] = 'area_calc'
                    intent_found = True
                    entity_matches += 1
                    break

        # COMPARE intent
        if not intent_found:
            for pattern in self.COMPARISON_PATTERNS:
                if re.search(pattern, query_lower):
                    result['intent'] = 'compare'
                    intent_found = True
                    entity_matches += 1
                    break

        # DEFORESTATION intent
        if not intent_found:
            for pattern in self.DEFORESTATION_PATTERNS:
                if re.search(pattern, query_lower) or re.search(pattern, query_normalized):
                    result['intent'] = 'deforestation'
                    if not result['years']:
                        result['years'] = [1986, 2023]
                    intent_found = True
                    entity_matches += 1
                    break

        # STATS intent
        if not intent_found:
            for pattern in self.STATS_PATTERNS:
                if re.search(pattern, query_lower):
                    result['intent'] = 'stats'
                    intent_found = True
                    entity_matches += 1
                    break

        # CARBON intent
        if not intent_found:
            for pattern in self.CARBON_PATTERNS:
                if re.search(pattern, query_lower):
                    result['intent'] = 'carbon'
                    intent_found = True
                    entity_matches += 1
                    break

        # RANKING intent
        if not intent_found:
            for pattern in self.RANKING_PATTERNS:
                if re.search(pattern, query_lower):
                    result['intent'] = 'ranking'
                    intent_found = True
                    entity_matches += 1
                    break

        # Extract threshold values (enhanced with more patterns)
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
            entity_matches += 1

        # Also try specific hectare threshold patterns
        if 'threshold' not in result:
            for pattern in self.THRESHOLD_PATTERNS:
                m = re.search(pattern, query_lower)
                if m:
                    val = m.group(1).replace(',', '.')
                    result['threshold'] = float(val)
                    if 'moins' in pattern or 'inf' in pattern:
                        result['threshold_op'] = 'lte'
                    else:
                        result['threshold_op'] = 'gte'
                    entity_matches += 1
                    break

        # Calculate confidence score (0.0 to 1.0)
        # Based on how many entities were successfully extracted
        max_possible = 4  # forests, cover_types, years, intent
        result['confidence'] = min(1.0, round(entity_matches / max_possible, 2))
        if result['intent'] != 'show':
            result['confidence'] = max(result['confidence'], 0.3)

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
        stats = qs.values(
            'nomenclature__code',
            'nomenclature__libelle_fr',
            'nomenclature__couleur_hex',
        ).annotate(
            total_superficie_ha=Sum('superficie_ha'),
            total_carbone=Sum('stock_carbone_calcule'),
            nombre_polygones=Count('id'),
        ).order_by('nomenclature__ordre_affichage')

        # If percentage mode, calculate percentages
        if parsed.get('percentage_mode'):
            stats = list(stats)
            total_area = sum(s['total_superficie_ha'] or 0 for s in stats)
            if total_area > 0:
                for s in stats:
                    s['pourcentage'] = round(
                        (s['total_superficie_ha'] or 0) / total_area * 100, 1
                    )
            return stats

        return stats

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

        # Determine sort order based on quantitative qualifiers
        sort_order = '-total_superficie_ha'
        if parsed.get('sort_order') == 'asc':
            sort_order = 'total_superficie_ha'

        return list(OccupationSol.objects.filter(
            annee=annee, **cover_filter,
        ).values(
            'foret__code', 'foret__nom',
        ).annotate(
            total_superficie_ha=Sum('superficie_ha'),
            total_carbone=Sum('stock_carbone_calcule'),
            nombre_polygones=Count('id'),
        ).order_by(sort_order))

    def build_prediction(self, parsed):
        """
        Calculate a linear trend between known years and project to a future year.
        Uses simple linear regression on available data points.
        Returns projected values with a warning about linear extrapolation.
        """
        from apps.carbone.models import OccupationSol

        target_year = parsed.get('target_year', 2030)
        known_years = [1986, 2003, 2023]

        base_filter = {}
        if parsed['forests']:
            base_filter['foret__code__in'] = parsed['forests']
        if parsed['cover_types']:
            base_filter['nomenclature__code__in'] = parsed['cover_types']
        else:
            base_filter['nomenclature__code__in'] = [
                'FORET_DENSE', 'FORET_CLAIRE', 'FORET_DEGRADEE',
            ]

        # Gather data points per nomenclature across known years
        data_points = {}
        for year in known_years:
            records = OccupationSol.objects.filter(
                annee=year, **base_filter,
            ).values(
                'nomenclature__code',
                'nomenclature__libelle_fr',
                'nomenclature__couleur_hex',
            ).annotate(
                superficie_ha=Sum('superficie_ha'),
                carbone=Sum('stock_carbone_calcule'),
            ).order_by('nomenclature__ordre_affichage')

            for rec in records:
                code = rec['nomenclature__code']
                if code not in data_points:
                    data_points[code] = {
                        'code': code,
                        'libelle': rec['nomenclature__libelle_fr'],
                        'couleur': rec['nomenclature__couleur_hex'],
                        'years': [],
                        'superficies': [],
                        'carbones': [],
                    }
                data_points[code]['years'].append(year)
                data_points[code]['superficies'].append(float(rec['superficie_ha'] or 0))
                data_points[code]['carbones'].append(float(rec['carbone'] or 0))

        # Simple linear regression for each cover type
        predictions = []
        for code, dp in data_points.items():
            if len(dp['years']) < 2:
                continue

            # Linear regression: y = slope * x + intercept
            years = dp['years']
            values = dp['superficies']
            n = len(years)
            sum_x = sum(years)
            sum_y = sum(values)
            sum_xy = sum(x * y for x, y in zip(years, values))
            sum_x2 = sum(x * x for x in years)

            denom = n * sum_x2 - sum_x * sum_x
            if denom == 0:
                continue

            slope = (n * sum_xy - sum_x * sum_y) / denom
            intercept = (sum_y - slope * sum_x) / n

            predicted_area = slope * target_year + intercept
            predicted_area = max(0, predicted_area)  # Cannot be negative

            # Calculate annual rate
            annual_change = slope

            # Also project carbon
            c_values = dp['carbones']
            c_sum_y = sum(c_values)
            c_sum_xy = sum(x * y for x, y in zip(years, c_values))
            c_slope = (n * c_sum_xy - sum_x * c_sum_y) / denom
            c_intercept = (c_sum_y - c_slope * sum_x) / n
            predicted_carbone = max(0, c_slope * target_year + c_intercept)

            # Trend direction
            if slope > 0:
                trend = 'hausse'
            elif slope < 0:
                trend = 'baisse'
            else:
                trend = 'stable'

            predictions.append({
                'code': code,
                'libelle': dp['libelle'],
                'couleur': dp['couleur'],
                'historical': [
                    {'annee': y, 'superficie_ha': round(v, 2)}
                    for y, v in zip(years, values)
                ],
                'predicted_superficie_ha': round(predicted_area, 2),
                'predicted_carbone': round(predicted_carbone, 2),
                'annual_change_ha': round(annual_change, 2),
                'trend': trend,
            })

        return {
            'target_year': target_year,
            'known_years': known_years,
            'predictions': predictions,
            'warning': (
                "Ces projections sont basees sur une extrapolation lineaire "
                "des donnees historiques ({years}). Elles ne tiennent pas compte "
                "des facteurs complexes (politiques, climatiques, etc.) et doivent "
                "etre interpretees avec prudence."
            ).format(years=', '.join(str(y) for y in known_years)),
        }

    def build_area_calculation(self, parsed):
        """
        Calculate total area by type for specific filters.
        Returns a detailed breakdown of areas with totals.
        """
        from apps.carbone.models import OccupationSol

        base_filter = {}
        if parsed['forests']:
            base_filter['foret__code__in'] = parsed['forests']
        if parsed['cover_types']:
            base_filter['nomenclature__code__in'] = parsed['cover_types']
        if parsed['years']:
            base_filter['annee__in'] = parsed['years']
        else:
            base_filter['annee'] = 2023  # default to most recent

        records = list(OccupationSol.objects.filter(
            **base_filter,
        ).values(
            'nomenclature__code',
            'nomenclature__libelle_fr',
            'nomenclature__couleur_hex',
        ).annotate(
            total_superficie_ha=Sum('superficie_ha'),
            total_carbone=Sum('stock_carbone_calcule'),
            nombre_polygones=Count('id'),
        ).order_by('nomenclature__ordre_affichage'))

        total_area = sum(r['total_superficie_ha'] or 0 for r in records)
        total_carbone = sum(r['total_carbone'] or 0 for r in records)
        total_polygones = sum(r['nombre_polygones'] or 0 for r in records)

        # Add percentage for each type
        for rec in records:
            area = rec['total_superficie_ha'] or 0
            rec['pourcentage'] = round(area / total_area * 100, 1) if total_area > 0 else 0

        return {
            'detail': records,
            'total_superficie_ha': round(float(total_area), 2),
            'total_carbone': round(float(total_carbone), 2),
            'total_polygones': total_polygones,
            'forests': parsed['forests'],
            'years': parsed['years'],
        }

    # ------------------------------------------------------------------
    # Smart suggestions
    # ------------------------------------------------------------------
    def suggest_queries(self, parsed):
        """Generate context-aware query suggestions based on what entities were found."""
        suggestions = []

        has_forests = bool(parsed['forests'])
        has_cover = bool(parsed['cover_types'])
        has_years = bool(parsed['years'])
        intent = parsed.get('intent', 'show')

        # Completely empty query
        if not has_forests and not has_cover and not has_years and intent == 'show':
            suggestions = [
                "Montre les zones de foret dense a TENE en 2023",
                "Superficie de foret claire a SANGOUE en 2023 ?",
                "Compare TENE entre 1986 et 2023",
                "Deforestation a DOKA",
                "Statistiques de carbone pour 2023",
                "Prevision de deforestation pour 2030",
                "Classement des forets par superficie",
                "Pourcentage de foret dense a LAHOUDA en 2023",
            ]
        else:
            # Context-aware suggestions based on what was found
            if has_forests and has_years:
                forest_name = parsed['forests'][0]
                year = parsed['years'][0]
                suggestions.append(
                    f"Deforestation a {forest_name}"
                )
                suggestions.append(
                    f"Compare {forest_name} entre 1986 et 2023"
                )
                suggestions.append(
                    f"Pourcentage de foret dense a {forest_name} en {year}"
                )
                suggestions.append(
                    f"Prevision pour {forest_name} en 2030"
                )

            elif has_forests and not has_years:
                forest_name = parsed['forests'][0]
                suggestions.append(
                    f"Superficie de {forest_name} en 2023"
                )
                suggestions.append(
                    f"Compare {forest_name} entre 1986 et 2023"
                )
                suggestions.append(
                    f"Deforestation a {forest_name}"
                )
                suggestions.append(
                    "Precisez une annee : 1986, 2003 ou 2023"
                )

            elif has_years and not has_forests:
                year = parsed['years'][0]
                suggestions.append(
                    f"Classement des forets en {year}"
                )
                suggestions.append(
                    f"Foret dense a TENE en {year}"
                )
                suggestions.append(
                    "Precisez une foret : TENE, DOKA, SANGOUE, LAHOUDA, ZOUEKE"
                )

            elif has_cover and not has_forests:
                cover = parsed['cover_types'][0]
                suggestions.append(
                    f"Statistiques de {cover} a TENE en 2023"
                )
                suggestions.append(
                    "Precisez une foret : TENE, DOKA, SANGOUE, LAHOUDA, ZOUEKE"
                )

            else:
                if not has_forests:
                    suggestions.append(
                        "Precisez une foret : TENE, DOKA, SANGOUE, LAHOUDA, ZOUEKE"
                    )
                if not has_cover:
                    suggestions.append(
                        "Precisez un type : foret dense, foret claire, foret degradee, jachere, cacao"
                    )
                if not has_years:
                    suggestions.append(
                        "Precisez une annee : 1986, 2003 ou 2023"
                    )

            # Intent-specific suggestions
            if intent == 'prediction' and not has_forests:
                suggestions.insert(0,
                    "Prevision de deforestation a TENE pour 2030"
                )
            if intent == 'export':
                suggestions.insert(0,
                    "Exporter les statistiques de TENE en 2023"
                )
            if intent == 'compare' and len(parsed['years']) < 2:
                suggestions.insert(0,
                    "Precisez deux annees pour comparer (ex: entre 1986 et 2023)"
                )

        return suggestions
