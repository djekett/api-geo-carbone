/**
 * Legende dynamique - charge les nomenclatures depuis l'API
 */
const Legend = {
    nomenclatures: [],

    async init() {
        try {
            const data = await API.getNomenclatures();
            // NomenclatureCouvertSerializer retourne un array simple (pas GeoJSON)
            if (Array.isArray(data)) {
                this.nomenclatures = data;
            } else if (data && data.results) {
                this.nomenclatures = data.results;
            } else {
                this.nomenclatures = [];
            }
            this.render();
        } catch (err) {
            console.error('Erreur chargement nomenclatures:', err);
        }
    },

    render() {
        const container = document.getElementById('legend-list');
        if (!container || this.nomenclatures.length === 0) return;

        container.innerHTML = this.nomenclatures.map(n => `
            <div class="flex items-center gap-3 p-1.5 rounded hover:bg-gray-50 cursor-default">
                <div class="w-5 h-5 rounded border border-gray-300 flex-shrink-0"
                     style="background-color: ${n.couleur_hex || '#999'}"></div>
                <div class="flex-1 min-w-0">
                    <div class="text-sm font-medium text-gray-700 truncate">${n.libelle_fr || n.code || ''}</div>
                    <div class="text-xs text-gray-400">${n.stock_carbone_reference ? n.stock_carbone_reference.toLocaleString('fr') + ' tCO2/ha' : '-'}</div>
                </div>
            </div>
        `).join('');
    },

    /**
     * Carbon stock legend — shows 4 forest classes with green gradient,
     * sorted by stock value descending (highest carbon first).
     * Includes total superficie for each class.
     */
    renderCarbone(geojsonData) {
        const container = document.getElementById('legend-list');
        if (!container || !geojsonData || !geojsonData.features || !geojsonData.features.length) return;

        // Deduplicate by class_code, accumulate superficie
        const classes = {};
        geojsonData.features.forEach(f => {
            const p = f.properties;
            if (p.class_code) {
                if (!classes[p.class_code]) {
                    classes[p.class_code] = {
                        libelle: p.libelle,
                        couleur: p.couleur,
                        stock_tco2_ha: p.stock_tco2_ha || 0,
                        superficie_ha: 0,
                    };
                }
                classes[p.class_code].superficie_ha += (p.superficie_ha || 0);
            }
        });

        // Sort by stock value descending (highest carbon first)
        const sorted = Object.values(classes).sort((a, b) => b.stock_tco2_ha - a.stock_tco2_ha);

        // Calculate total superficie for percentage
        const totalSup = sorted.reduce((s, c) => s + c.superficie_ha, 0);

        container.innerHTML =
            '<div class="flex items-center gap-2 mb-3">' +
                '<div class="w-6 h-6 rounded-lg bg-green-900/10 flex items-center justify-center">' +
                    '<i class="fas fa-leaf text-green-700 text-xs"></i>' +
                '</div>' +
                '<div>' +
                    '<div class="text-xs font-bold text-green-800 uppercase tracking-wide">Stock Carbone 2023</div>' +
                    '<div class="text-[10px] text-gray-400">Spatialisation tCO\u2082/ha</div>' +
                '</div>' +
            '</div>' +
            sorted.map(c => {
                const pct = totalSup > 0 ? ((c.superficie_ha / totalSup) * 100).toFixed(1) : 0;
                return `
                <div class="flex items-center gap-3 p-2 rounded-lg hover:bg-green-50/50 cursor-default transition-colors">
                    <div class="w-5 h-5 rounded border border-gray-300/50 flex-shrink-0 shadow-sm"
                         style="background-color: ${c.couleur || '#228B22'}"></div>
                    <div class="flex-1 min-w-0">
                        <div class="text-sm font-medium text-gray-700 truncate">${c.libelle}</div>
                        <div class="flex items-center gap-2">
                            <span class="text-xs font-bold" style="color:#166534;">
                                ${c.stock_tco2_ha.toLocaleString('fr')} tCO\u2082/ha
                            </span>
                            <span class="text-[10px] text-gray-400">
                                ${c.superficie_ha.toLocaleString('fr', {maximumFractionDigits: 0})} ha (${pct}%)
                            </span>
                        </div>
                    </div>
                </div>`;
            }).join('');
    },
};
