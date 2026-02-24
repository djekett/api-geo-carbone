import time
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .nlp_engine import NLPEngine
from .models import RequeteNLP
from apps.carbone.serializers import OccupationSolSerializer


class AIQueryView(APIView):
    """Endpoint de requete en langage naturel (Chat-to-Map)."""

    def post(self, request):
        query = request.data.get('query', '').strip()
        if not query:
            return Response(
                {'error': 'Le champ "query" est requis.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        start = time.time()
        engine = NLPEngine()
        parsed = engine.parse(query)

        nb_results = 0
        orm_desc = ''

        # Build response based on intent
        if parsed['intent'] == 'compare' and len(parsed['years']) >= 2:
            comparison = engine.build_comparison(parsed)
            response_data = {
                'type': 'comparison',
                'parsed': parsed,
                'data': comparison,
            }
            orm_desc = f"compare {parsed['years']}"
        elif parsed['intent'] == 'stats':
            stats = list(engine.build_stats(parsed))
            response_data = {
                'type': 'stats',
                'parsed': parsed,
                'data': stats,
            }
            nb_results = len(stats)
            orm_desc = 'stats'
        else:
            # Default: return GeoJSON features
            qs = engine.build_queryset(parsed)
            count = qs.count()
            features = qs[:200]  # Limit for performance
            serializer = OccupationSolSerializer(features, many=True)
            response_data = {
                'type': 'geojson',
                'parsed': parsed,
                'count': count,
                'data': serializer.data,
            }
            nb_results = count
            orm_desc = f"geojson {count} features"

        processing_ms = int((time.time() - start) * 1000)
        response_data['processing_ms'] = processing_ms

        # Log the query (non-blocking)
        try:
            RequeteNLP.objects.create(
                texte_requete=query,
                entites_extraites=parsed,
                filtre_orm=orm_desc,
                nombre_resultats=nb_results,
                temps_traitement_ms=processing_ms,
            )
        except Exception:
            pass  # Ne pas bloquer la reponse si le log echoue

        return Response(response_data)
