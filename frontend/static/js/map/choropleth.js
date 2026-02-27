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
 */
const Choropleth = {
    _occupationLayer: null,
    _foretsLayer: null,
    aiLayer: null,

    /**
     * Render occupation polygons — called on every year change.
     * Uses double-buffering: new layer is built and added BEFORE
     * old layer is removed, preventing visual gaps.
     */
    renderOccupation(geojsonData, layerGroup, map) {
        if (!geojsonData || !geojsonData.features || !geojsonData.features.length) {
            layerGroup.clearLayers();
            this._occupationLayer = null;
            return;
        }

        // Build new layer (not yet on map)
        const newLayer = L.geoJSON(geojsonData, {
            pane: 'occupationPane',
            style: (feature) => ({
                fillColor: feature.properties.couleur || '#999',
                weight: 0.3,
                opacity: 0.6,
                color: '#555',
                fillOpacity: 0.6,
            }),
            onEachFeature: (feature, layer) => {
                layer.bindPopup(() => PopupBuilder.occupation(feature.properties));
            },
            bubblingMouseEvents: false,
        });

        // Double-buffer swap: add new, then remove old
        const oldLayer = this._occupationLayer;
        newLayer.addTo(layerGroup);
        this._occupationLayer = newLayer;

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
