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

    /**
     * Render carbon stock spatialization (2023) — 4 polygon classes with green gradient.
     * Uses the same double-buffering pattern as renderOccupation.
     *
     * Visual differences from occupation mode:
     * - Higher fill opacity (0.75) for emphasis on carbon stock density
     * - Darker border color (#0a2e0a) for contrast
     * - Slightly thicker borders (0.6px) for class boundaries
     */
    renderStockCarbone(geojsonData, layerGroup, map) {
        if (!geojsonData || !geojsonData.features || !geojsonData.features.length) {
            layerGroup.clearLayers();
            this._occupationLayer = null;
            return;
        }

        const newLayer = L.geoJSON(geojsonData, {
            pane: 'occupationPane',
            style: (feature) => ({
                fillColor: feature.properties.couleur || '#228B22',
                weight: 0.6,
                opacity: 0.85,
                color: '#0a2e0a',
                fillOpacity: 0.75,
            }),
            onEachFeature: (feature, layer) => {
                const props = feature.properties;
                layer.bindPopup(() => PopupBuilder.stockCarbone(props));
                // Tooltip with class name for quick identification
                layer.bindTooltip(
                    (props.libelle || props.class_code || '') + ' — ' + (props.stock_tco2_ha || 0).toLocaleString('fr') + ' tCO2/ha',
                    { sticky: true, direction: 'top', className: 'carbone-tooltip' }
                );
            },
            bubblingMouseEvents: false,
        });

        // Double-buffer swap (same as renderOccupation)
        const oldLayer = this._occupationLayer;
        newLayer.addTo(layerGroup);
        this._occupationLayer = newLayer;

        if (oldLayer) {
            requestAnimationFrame(() => {
                layerGroup.removeLayer(oldLayer);
            });
        }

        return newLayer;
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
