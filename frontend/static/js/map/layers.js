/**
 * Layer Manager — Lazy loading with map panes
 *
 * Layer pane architecture:
 *   z:400 occupationPane  — occupation du sol (heavy, refreshed on year change)
 *   z:450 foretsPane       — forest boundaries (static, loaded once)
 *   z:460 limitesPane      — admin boundaries (static)
 *   z:470 infraPane        — routes, hydro, localités (lazy loaded)
 */
const LayerManager = {
    baseLayers: {},
    overlays: {},
    currentBaseLayer: null,
    loadedOverlays: new Set(),
    _loadingOverlays: new Set(),

    init(map) {
        this.map = map;

        // Base tile layers
        this.baseLayers = {
            osm: L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '&copy; OpenStreetMap', maxZoom: 19,
                updateWhenZooming: false, updateWhenIdle: true,
            }),
            satellite: L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
                attribution: '&copy; Esri', maxZoom: 18,
                updateWhenZooming: false, updateWhenIdle: true,
            }),
            terrain: L.tileLayer('https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png', {
                attribution: '&copy; OpenTopoMap', maxZoom: 17,
                updateWhenZooming: false, updateWhenIdle: true,
            }),
        };
        this.baseLayers.osm.addTo(map);
        this.currentBaseLayer = 'osm';

        // Overlay groups
        this.overlays = {
            forets:     L.layerGroup().addTo(map),
            occupation: L.layerGroup().addTo(map),
            limites:    L.layerGroup(),
            placettes:  L.layerGroup(),
            routes:     L.layerGroup(),
            hydro:      L.layerGroup(),
            localites:  L.layerGroup(),
        };

        this.bindEvents();
    },

    bindEvents() {
        document.querySelectorAll('input[name="baseLayer"]').forEach(radio => {
            radio.addEventListener('change', (e) => this.switchBaseLayer(e.target.value));
        });

        const overlayMap = {
            'layer-forets': 'forets',
            'layer-limites': 'limites',
            'layer-placettes': 'placettes',
            'layer-routes': 'routes',
            'layer-hydro': 'hydro',
            'layer-localites': 'localites',
        };

        Object.entries(overlayMap).forEach(([cbId, key]) => {
            const cb = document.getElementById(cbId);
            if (cb) {
                cb.addEventListener('change', (e) => {
                    if (e.target.checked) {
                        this.map.addLayer(this.overlays[key]);
                        this.loadOverlay(key);
                    } else {
                        this.map.removeLayer(this.overlays[key]);
                    }
                });
            }
        });
    },

    switchBaseLayer(key) {
        if (this.currentBaseLayer && this.baseLayers[this.currentBaseLayer]) {
            this.map.removeLayer(this.baseLayers[this.currentBaseLayer]);
        }
        if (this.baseLayers[key]) {
            this.baseLayers[key].addTo(this.map);
            this.currentBaseLayer = key;
        }
    },

    _setLoading(key, loading) {
        const cb = document.getElementById('layer-' + key);
        if (cb && cb.parentElement) {
            cb.parentElement.classList.toggle('layer-loading', loading);
            if (loading) this._loadingOverlays.add(key);
            else this._loadingOverlays.delete(key);
        }
    },

    async loadOverlay(key) {
        if (this.loadedOverlays.has(key) || this._loadingOverlays.has(key)) return;
        this._setLoading(key, true);

        try {
            switch (key) {
                case 'placettes': await this._loadPlacettes(); break;
                case 'routes':    await this._loadInfra('routes', 'ROUTE', '#8B4513', 2.5); break;
                case 'hydro':     await this._loadInfra('hydro', 'HYDROGRAPHIE', '#3498db', 2); break;
                case 'localites': await this._loadLocalites(); break;
                case 'limites':   await this._loadLimites(); break;
            }
            this.loadedOverlays.add(key);
        } catch (err) {
            console.error(`[Layers] ${key}:`, err);
        }
        this._setLoading(key, false);
    },

    async _loadPlacettes() {
        const data = await API.getPlacettes();
        if (!data?.features?.length) { console.warn('[Layers] Placettes: vide'); return; }

        L.geoJSON(data, {
            pane: 'infraPane',
            pointToLayer: (f, ll) => L.circleMarker(ll, {
                pane: 'infraPane',
                radius: 5, fillColor: '#e74c3c', color: '#c0392b',
                weight: 1.5, fillOpacity: 0.85,
            }),
            onEachFeature: (f, l) => l.bindPopup(PopupBuilder.placette(f.properties)),
        }).addTo(this.overlays.placettes);
        console.log(`[Layers] Placettes: ${data.features.length}`);
    },

    async _loadInfra(key, type, color, weight) {
        const data = await API.getInfrastructures({ type });
        if (!data?.features?.length) { console.warn(`[Layers] ${key}: vide`); return; }

        L.geoJSON(data, {
            pane: 'infraPane',
            style: { color, weight, opacity: 0.75 },
            onEachFeature: (f, l) => {
                if (f.properties.nom) l.bindTooltip(f.properties.nom, { permanent: false });
            },
        }).addTo(this.overlays[key]);
        console.log(`[Layers] ${key}: ${data.features.length}`);
    },

    async _loadLocalites() {
        const [locs, chefs] = await Promise.all([
            API.getInfrastructures({ type: 'LOCALITE' }),
            API.getInfrastructures({ type: 'CHEF_LIEU_SP' }),
        ]);
        const features = [
            ...((locs?.features) || []),
            ...((chefs?.features) || []),
        ];
        if (!features.length) { console.warn('[Layers] Localites: vide'); return; }

        L.geoJSON({ type: 'FeatureCollection', features }, {
            pane: 'infraPane',
            pointToLayer: (f, ll) => {
                const isChef = f.properties.type_infra === 'CHEF_LIEU_SP';
                return L.circleMarker(ll, {
                    pane: 'infraPane',
                    radius: isChef ? 7 : 4,
                    fillColor: isChef ? '#f59e0b' : '#9ca3af',
                    color: isChef ? '#d97706' : '#6b7280',
                    weight: isChef ? 2 : 1,
                    fillOpacity: 0.9,
                });
            },
            onEachFeature: (f, l) => {
                if (f.properties.nom) {
                    l.bindTooltip(f.properties.nom, {
                        permanent: false, direction: 'top', offset: [0, -6]
                    });
                }
            },
        }).addTo(this.overlays.localites);
        console.log(`[Layers] Localites: ${features.length}`);
    },

    async _loadLimites() {
        const zoom = this.map ? this.map.getZoom() : 10;
        const data = await API.getZonesEtude({ zoom });
        if (!data?.features?.length) { console.warn('[Layers] Limites: vide'); return; }

        // SVG renderer for limites: few features, allows CSS pointer-events
        // control so clicks pass through to occupation canvas below
        const svgRenderer = L.svg({ pane: 'limitesPane' });

        L.geoJSON(data, {
            pane: 'limitesPane',
            renderer: svgRenderer,
            style: (f) => {
                const n = f.properties.niveau || 1;
                const styles = {
                    1: { color: '#7c3aed', weight: 3, dashArray: '10, 5' },
                    2: { color: '#a855f7', weight: 2.5, dashArray: '8, 4' },
                    3: { color: '#c084fc', weight: 1.5, dashArray: '5, 5' },
                };
                const s = styles[n] || styles[3];
                return {
                    fillColor: s.color, fillOpacity: 0.03,
                    weight: s.weight, opacity: 0.8,
                    color: s.color, dashArray: s.dashArray,
                };
            },
            onEachFeature: (f, l) => {
                const nom = f.properties.nom || '';
                l.bindTooltip(nom, { permanent: false, direction: 'center' });
                l.bindPopup(`
                    <div class="popup-header" style="background:linear-gradient(135deg,#7c3aed,#6d28d9);">
                        ${nom}
                    </div>
                    <div class="popup-body">
                        <div class="row">
                            <span class="label">Type</span>
                            <span class="value">${f.properties.type_zone || '-'}</span>
                        </div>
                        <div class="row">
                            <span class="label">Niveau</span>
                            <span class="value">${f.properties.niveau || '-'}</span>
                        </div>
                    </div>
                `);
            },
        }).addTo(this.overlays.limites);
        console.log(`[Layers] Limites: ${data.features.length}`);
    },

    clearOverlay(key) {
        if (this.overlays[key]) {
            this.overlays[key].clearLayers();
            this.loadedOverlays.delete(key);
        }
    },
};
