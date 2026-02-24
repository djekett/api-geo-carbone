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
};
