/**
 * Choropleth renderer — Double-buffered layer updates
 *
 * KEY FIX: Uses double-buffering for occupation layer updates:
 * 1. Build new GeoJSON layer OFF-SCREEN
 * 2. Add new layer to the layer group
 * 3. Remove old layer AFTER new one is rendered
 * → No flash/flicker, forests remain stable
 *
 * Each layer type renders into its own map pane:
 * - occupation → pane:'occupationPane' (z:400)
 * - forets    → pane:'foretsPane' (z:450)
 *
 * RESILIENT RENDERING: Features are added individually with try/catch
 * to prevent a single bad geometry from blocking all subsequent features.
 */
const Choropleth = {
    _occupationLayer: null,
    _foretsLayer: null,
    aiLayer: null,

    /**
     * Filter out micro-fragment polygon parts from GeoJSON data.
     * Removes MultiPolygon parts with tiny outer rings (< 6 coords)
     * that are rasterization artifacts from Sentinel-2 data.
     * This ensures the Canvas renderer can handle the data smoothly.
     */
    _filterMicroFragments(geojsonData) {
        if (!geojsonData || !geojsonData.features) return geojsonData;

        const MIN_RING_COORDS = 6;
        let totalBefore = 0;
        let totalAfter = 0;

        for (const feature of geojsonData.features) {
            const geom = feature.geometry;
            if (!geom || geom.type !== 'MultiPolygon') continue;

            const coords = geom.coordinates;
            totalBefore += coords.length;

            // Keep only polygon parts with outer ring >= MIN_RING_COORDS
            const filtered = coords.filter(polygon => {
                if (!polygon || !polygon[0]) return false;
                return polygon[0].length >= MIN_RING_COORDS;
            });

            totalAfter += filtered.length;
            geom.coordinates = filtered;
        }

        // Remove features with empty geometry
        geojsonData.features = geojsonData.features.filter(f =>
            f.geometry && f.geometry.coordinates && f.geometry.coordinates.length > 0
        );

        if (totalBefore !== totalAfter) {
            console.log(`[Choropleth] Filtered micro-fragments: ${totalBefore} → ${totalAfter} polygon parts`);
        }
        return geojsonData;
    },

    /**
     * Render occupation polygons — called on every year change.
     * Uses double-buffering: new layer is built and added BEFORE
     * old layer is removed, preventing visual gaps.
     *
     * RESILIENT: adds features individually with error recovery
     * to prevent a single bad geometry from blocking all layers.
     */
    renderOccupation(geojsonData, layerGroup, map) {
        if (!geojsonData || !geojsonData.features || !geojsonData.features.length) {
            layerGroup.clearLayers();
            this._occupationLayer = null;
            return;
        }

        // Filter micro-fragments for smooth Canvas rendering
        geojsonData = this._filterMicroFragments(geojsonData);

        const layerStyle = (feature) => ({
            fillColor: feature.properties.couleur || '#999',
            weight: 0.3,
            opacity: 0.6,
            color: '#555',
            fillOpacity: 0.6,
        });

        const onEachFn = (feature, layer) => {
            layer.bindPopup(() => PopupBuilder.occupation(feature.properties));
        };

        // Build new layer with resilient feature-by-feature processing
        let newLayer;
        try {
            newLayer = L.geoJSON(geojsonData, {
                pane: 'occupationPane',
                style: layerStyle,
                onEachFeature: onEachFn,
                bubblingMouseEvents: false,
            });
        } catch (err) {
            // Fallback: add features one by one to isolate bad geometries
            console.warn('[Choropleth] Batch rendering failed, using feature-by-feature fallback:', err);
            newLayer = L.featureGroup();
            let ok = 0, fail = 0;
            for (const feature of geojsonData.features) {
                try {
                    const singleGeoJSON = { type: 'FeatureCollection', features: [feature] };
                    const singleLayer = L.geoJSON(singleGeoJSON, {
                        pane: 'occupationPane',
                        style: layerStyle,
                        onEachFeature: onEachFn,
                        bubblingMouseEvents: false,
                    });
                    singleLayer.addTo(newLayer);
                    ok++;
                } catch (e) {
                    fail++;
                    console.error(`[Choropleth] Feature failed:`, feature.properties, e);
                }
            }
            console.log(`[Choropleth] Fallback: ${ok} OK, ${fail} failed`);
        }

        // Double-buffer swap: add new, then remove old
        const oldLayer = this._occupationLayer;
        newLayer.addTo(layerGroup);
        this._occupationLayer = newLayer;

        // Count rendered layers for debugging
        let count = 0;
        if (newLayer.eachLayer) {
            newLayer.eachLayer(() => count++);
        }
        console.log(`[Choropleth] Rendered ${count} occupation layers (${geojsonData.features.length} features)`);

        // Remove old layer after a microtask (ensures new layer is painted first)
        if (oldLayer) {
            requestAnimationFrame(() => {
                layerGroup.removeLayer(oldLayer);
            });
        }

        return newLayer;
    },

    /**
     * Render forest boundaries — called ONCE at startup, never again.
     * Uses a separate pane with higher z-index.
     */
    renderForets(geojsonData, layerGroup, map) {
        layerGroup.clearLayers();
        if (!geojsonData || !geojsonData.features) return;

        // SVG renderer for forests: only 6 features, allows CSS pointer-events
        // control so clicks pass through transparent fill to occupation canvas below
        const svgRenderer = L.svg({ pane: 'foretsPane' });

        this._foretsLayer = L.geoJSON(geojsonData, {
            pane: 'foretsPane',
            renderer: svgRenderer,
            interactive: true,
            style: {
                fillColor: 'transparent',
                weight: 2.5,
                opacity: 1,
                color: '#1a5e1a',
                dashArray: '6, 4',
                fillOpacity: 0,
            },
            onEachFeature: (feature, layer) => {
                const p = feature.properties || {};
                layer.bindPopup(PopupBuilder.foret(p));
                layer.bindTooltip(p.nom || p.code || '', {
                    permanent: false,
                    direction: 'center',
                    className: 'foret-tooltip',
                });
            },
        });

        this._foretsLayer.addTo(layerGroup);
    },

    renderAIResults(geojsonData, map) {
        if (this.aiLayer) map.removeLayer(this.aiLayer);
        if (!geojsonData || !geojsonData.features || !geojsonData.features.length) return;

        this.aiLayer = L.geoJSON(geojsonData, {
            style: (f) => ({
                fillColor: f.properties.couleur || '#ff6600',
                weight: 2, opacity: 1, color: '#ff0000', fillOpacity: 0.7,
            }),
            onEachFeature: (f, l) => l.bindPopup(() => PopupBuilder.occupation(f.properties)),
        }).addTo(map);

        if (this.aiLayer.getBounds().isValid()) {
            map.fitBounds(this.aiLayer.getBounds(), { padding: [50, 50] });
        }
    },

    clearAIResults(map) {
        if (this.aiLayer) { map.removeLayer(this.aiLayer); this.aiLayer = null; }
    },
};
