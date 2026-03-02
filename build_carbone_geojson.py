"""
Build stock_carbone.json from shapefile using fiona + shapely.
Reads feature by feature (low memory), simplifies aggressively.
"""
import os
import json
import fiona
from fiona.transform import transform_geom
from shapely.geometry import shape, mapping
from shapely.validation import make_valid

SHP = r"C:\Users\LENOVO\Documents\DATA YEO ALL\SIG_DATA\extracted_carbone\data carbone\data_carb.shp"
OUT = os.path.join(os.path.dirname(__file__), 'media', 'geocache', 'stock_carbone.json')
TOL = 200  # meters (UTM simplification)

CLASS_MAP = {
    1: ('FORET_DENSE', 'Foret dense', 3186.70, '#004d00'),
    2: ('FORET_CLAIRE', 'Foret claire', 3307.62, '#003300'),
    3: ('FORET_DEGRADEE', 'Foret degradee', 1947.15, '#339933'),
    4: ('JACHERE', 'Jachere / Reboisement jeune', 2906.42, '#006600'),
}

features = []

with fiona.open(SHP) as src:
    print('CRS:', src.crs)
    print('Features:', len(src))

    for i, feat in enumerate(src):
        props = feat['properties']
        class_id = int(props.get('Class_Id') or props.get('class_id') or 0)
        area_ha = float(props.get('Area') or 0)

        if class_id not in CLASS_MAP:
            print('  Skip class %d' % class_id)
            continue

        code, libelle, stock, couleur = CLASS_MAP[class_id]
        print('  [%d] %s (%.0f ha)...' % (i + 1, code, area_ha), end=' ', flush=True)

        # Get geometry in source CRS (UTM)
        geom = shape(feat['geometry'])

        # Simplify in UTM space (meters)
        geom = geom.simplify(TOL, preserve_topology=True)
        geom = make_valid(geom)

        # Transform to WGS84
        geom_wgs84 = transform_geom(
            src.crs, 'EPSG:4326', mapping(geom)
        )

        features.append({
            'type': 'Feature',
            'id': class_id,
            'geometry': geom_wgs84,
            'properties': {
                'class_code': code,
                'libelle': libelle,
                'annee': 2023,
                'stock_tco2_ha': stock,
                'couleur': couleur,
                'superficie_ha': round(area_ha, 2),
            },
        })
        print('OK')

geojson = {'type': 'FeatureCollection', 'features': features}
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(geojson, f, ensure_ascii=False, separators=(',', ':'))

size_mb = os.path.getsize(OUT) / (1024 * 1024)
print('\nDone! %s (%.2f MB, %d features)' % (OUT, size_mb, len(features)))
