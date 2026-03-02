"""
Simplify raw GeoJSON from ogr2ogr and add carbon stock properties.
Uses shapely directly (no geopandas overhead).
"""
import json
import os
from shapely.geometry import shape, mapping
from shapely.validation import make_valid

# Carbon stock constants: class_id -> (code, label, stock_tco2/ha, color)
CLASS_MAP = {
    1: ('FORET_DENSE', 'Foret dense', 3186.70, '#004d00'),
    2: ('FORET_CLAIRE', 'Foret claire', 3307.62, '#003300'),
    3: ('FORET_DEGRADEE', 'Foret degradee', 1947.15, '#339933'),
    4: ('JACHERE', 'Jachere / Reboisement jeune', 2906.42, '#006600'),
}

INPUT = 'media/geocache/stock_carbone_raw.json'
OUTPUT = 'media/geocache/stock_carbone.json'
TOLERANCE = 0.002  # degrees (~220m at equator)

print('Loading raw GeoJSON...')
with open(INPUT, 'r', encoding='utf-8') as f:
    data = json.load(f)

print('  %d features loaded' % len(data['features']))

features = []
for i, feat in enumerate(data['features']):
    props = feat.get('properties', {})
    class_id = int(props.get('Class_Id') or props.get('class_id') or 0)

    if class_id not in CLASS_MAP:
        print('  Skip unknown class %d' % class_id)
        continue

    code, libelle, stock, couleur = CLASS_MAP[class_id]
    # Use Area field from shapefile (already in hectares)
    area_ha = round(float(props.get('Area') or 0), 2)

    print('  Simplifying feature %d (%s, %.0f ha)...' % (i + 1, code, area_ha))
    geom = shape(feat['geometry'])
    geom = geom.simplify(TOLERANCE, preserve_topology=True)
    geom = make_valid(geom)

    features.append({
        'type': 'Feature',
        'id': class_id,
        'geometry': mapping(geom),
        'properties': {
            'class_code': code,
            'libelle': libelle,
            'annee': 2023,
            'stock_tco2_ha': stock,
            'couleur': couleur,
            'superficie_ha': area_ha,
        },
    })
    print('    OK: %s (%.0f ha, %s tCO2/ha)' % (libelle, area_ha, stock))

geojson = {'type': 'FeatureCollection', 'features': features}

print('Writing %s...' % OUTPUT)
with open(OUTPUT, 'w', encoding='utf-8') as f:
    json.dump(geojson, f, ensure_ascii=False, separators=(',', ':'))

size_mb = os.path.getsize(OUTPUT) / (1024 * 1024)
print('Done! %.2f MB, %d features' % (size_mb, len(features)))
