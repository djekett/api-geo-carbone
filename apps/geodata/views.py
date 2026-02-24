import os
import zipfile
import tempfile
import geopandas as gpd
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework import status, permissions
from django.contrib.gis.geos import GEOSGeometry, MultiPolygon

from .models import ImportSession
from apps.carbone.models import OccupationSol, ForetClassee, NomenclatureCouvert


class ImportUploadView(APIView):
    """Etape 1-2: Upload et pre-lecture d'un Shapefile ZIP."""
    permission_classes = [permissions.IsAdminUser]
    parser_classes = [MultiPartParser]

    def post(self, request):
        fichier = request.FILES.get('fichier')
        if not fichier:
            return Response({'error': 'Aucun fichier fourni.'}, status=status.HTTP_400_BAD_REQUEST)

        if not fichier.name.endswith('.zip'):
            return Response({'error': 'Le fichier doit etre un .zip'}, status=status.HTTP_400_BAD_REQUEST)

        # Create import session
        session = ImportSession.objects.create(
            utilisateur=request.user,
            fichier_nom=fichier.name,
            fichier=fichier,
        )

        # Extract and read shapefile
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                zip_path = os.path.join(tmpdir, 'upload.zip')
                with open(zip_path, 'wb') as f:
                    for chunk in fichier.chunks():
                        f.write(chunk)

                with zipfile.ZipFile(zip_path, 'r') as z:
                    z.extractall(tmpdir)

                # Find .shp file
                shp_files = [f for f in os.listdir(tmpdir) if f.endswith('.shp')]
                if not shp_files:
                    # Look in subdirectories
                    for root, dirs, files in os.walk(tmpdir):
                        for f in files:
                            if f.endswith('.shp'):
                                shp_files.append(os.path.join(root, f))
                    if not shp_files:
                        return Response({'error': 'Aucun fichier .shp trouve dans le ZIP.'}, status=status.HTTP_400_BAD_REQUEST)
                    shp_path = shp_files[0]
                else:
                    shp_path = os.path.join(tmpdir, shp_files[0])

                gdf = gpd.read_file(shp_path)
                colonnes = list(gdf.columns)
                colonnes.remove('geometry')

                # Preview first 5 features as GeoJSON
                gdf_preview = gdf.head(5).to_crs(epsg=4326)
                preview_geojson = gdf_preview.__geo_interface__

                session.colonnes_detectees = colonnes
                session.nombre_features = len(gdf)
                session.statut = 'PENDING'
                session.save()

                return Response({
                    'session_id': session.id,
                    'fichier': fichier.name,
                    'colonnes': colonnes,
                    'nombre_features': len(gdf),
                    'crs': str(gdf.crs),
                    'preview': preview_geojson,
                })

        except Exception as e:
            session.statut = 'FAILED'
            session.rapport = str(e)
            session.save()
            return Response({'error': f'Erreur de lecture: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)


class ImportExecuteView(APIView):
    """Etape 3-4: Mapping des colonnes et execution de l'import."""
    permission_classes = [permissions.IsAdminUser]

    def post(self, request):
        session_id = request.data.get('session_id')
        mapping = request.data.get('mapping', {})
        foret_code = request.data.get('foret_code')
        annee = request.data.get('annee')
        type_couvert = request.data.get('type_couvert')

        if not session_id:
            return Response({'error': 'session_id requis.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            session = ImportSession.objects.get(id=session_id)
        except ImportSession.DoesNotExist:
            return Response({'error': 'Session non trouvee.'}, status=status.HTTP_404_NOT_FOUND)

        session.mapping_colonnes = mapping
        session.statut = 'PROCESSING'
        session.save()

        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                # Re-extract the file
                zip_path = session.fichier.path
                with zipfile.ZipFile(zip_path, 'r') as z:
                    z.extractall(tmpdir)

                shp_files = []
                for root, dirs, files in os.walk(tmpdir):
                    for f in files:
                        if f.endswith('.shp'):
                            shp_files.append(os.path.join(root, f))

                if not shp_files:
                    return Response({'error': 'Fichier .shp non trouve.'}, status=status.HTTP_400_BAD_REQUEST)

                gdf = gpd.read_file(shp_files[0])
                gdf = gdf.to_crs(epsg=4326)

                foret = ForetClassee.objects.filter(code=foret_code).first() if foret_code else None
                nomenclature = NomenclatureCouvert.objects.filter(code=type_couvert).first() if type_couvert else None

                imported = 0
                errors = 0

                for _, row in gdf.iterrows():
                    try:
                        geom = GEOSGeometry(row.geometry.wkt, srid=4326)
                        if geom.geom_type == 'Polygon':
                            geom = MultiPolygon(geom)

                        # Determine foret from spatial intersection if not specified
                        target_foret = foret
                        if not target_foret:
                            target_foret = ForetClassee.objects.filter(
                                geom__intersects=geom
                            ).first()

                        if not target_foret:
                            errors += 1
                            continue

                        occ = OccupationSol(
                            foret=target_foret,
                            nomenclature=nomenclature,
                            annee=int(annee) if annee else 2023,
                            geom=geom,
                        )

                        # Map columns from shapefile
                        for shp_col, model_field in mapping.items():
                            if hasattr(occ, model_field) and shp_col in row.index:
                                setattr(occ, model_field, row[shp_col])

                        occ.save()
                        imported += 1

                    except Exception as e:
                        errors += 1

                session.nombre_importees = imported
                session.nombre_erreurs = errors
                session.statut = 'COMPLETED'
                session.rapport = f'{imported} features importees, {errors} erreurs.'
                session.save()

                return Response({
                    'session_id': session.id,
                    'imported': imported,
                    'errors': errors,
                    'rapport': session.rapport,
                })

        except Exception as e:
            session.statut = 'FAILED'
            session.rapport = str(e)
            session.save()
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
