/**
 * Panneau de statistiques + graphiques Chart.js
 */
const Stats = {
    superficieChart: null,
    carboneChart: null,

    async load(annee, foretCode) {
        try {
            const data = await API.getOccupationStats({ annee, foret: foretCode || '' });
            if (!data) {
                console.warn('Stats: aucune donnee recue');
                return;
            }
            this.updateSummary(data);
            this.updateCharts(data.resultats || []);
        } catch (err) {
            console.error('Erreur chargement stats:', err);
        }
    },

    updateSummary(data) {
        const totaux = data.totaux || {};
        const resultats = data.resultats || [];

        const supEl = document.getElementById('stat-superficie');
        const carbEl = document.getElementById('stat-carbone');
        const polyEl = document.getElementById('stat-polygones');

        if (supEl) {
            const val = totaux.superficie_ha || 0;
            supEl.textContent = val.toLocaleString('fr-FR', { maximumFractionDigits: 0 }) + ' ha';
        }
        if (carbEl) {
            const val = totaux.carbone_tco2 || 0;
            carbEl.textContent = val.toLocaleString('fr-FR', { maximumFractionDigits: 0 }) + ' tCO2';
        }
        if (polyEl) {
            const total = resultats.reduce((s, r) => s + (r.nombre_polygones || 0), 0);
            polyEl.textContent = total.toLocaleString('fr-FR');
        }
    },

    /**
     * Load carbon stock stats directly from GeoJSON features (no API call needed).
     * Shapes data into same format as updateSummary/updateCharts expect.
     */
    loadCarbone(geojsonData) {
        if (!geojsonData || !geojsonData.features) return;

        const features = geojsonData.features;
        const byClass = {};

        features.forEach(f => {
            const p = f.properties;
            const code = p.class_code || 'UNKNOWN';
            if (!byClass[code]) {
                byClass[code] = {
                    nomenclature__libelle_fr: p.libelle || code,
                    nomenclature__couleur_hex: p.couleur || '#228B22',
                    total_superficie_ha: 0,
                    total_carbone: 0,
                    nombre_polygones: 0,
                };
            }
            byClass[code].total_superficie_ha += (p.superficie_ha || 0);
            byClass[code].total_carbone += (p.superficie_ha || 0) * (p.stock_tco2_ha || 0);
            byClass[code].nombre_polygones += 1;
        });

        const resultats = Object.values(byClass);

        // Update summary (reuses existing method)
        this.updateSummary({
            totaux: {
                superficie_ha: resultats.reduce((s, r) => s + r.total_superficie_ha, 0),
                carbone_tco2: resultats.reduce((s, r) => s + r.total_carbone, 0),
            },
            resultats: resultats,
        });

        // Update charts (reuses existing method)
        this.updateCharts(resultats);
    },

    updateCharts(resultats) {
        if (!resultats || resultats.length === 0) return;

        const labels = resultats.map(r => r.nomenclature__libelle_fr || r.nomenclature__code || '');
        const colors = resultats.map(r => r.nomenclature__couleur_hex || '#999');
        const superficies = resultats.map(r => Math.round(r.total_superficie_ha || 0));
        const carbones = resultats.map(r => Math.round(r.total_carbone || 0));

        // Graphique repartition des superficies (doughnut)
        const supCtx = document.getElementById('chart-superficie');
        if (supCtx) {
            if (this.superficieChart) this.superficieChart.destroy();
            this.superficieChart = new Chart(supCtx, {
                type: 'doughnut',
                data: {
                    labels: labels,
                    datasets: [{
                        data: superficies,
                        backgroundColor: colors,
                        borderWidth: 1,
                        borderColor: '#fff',
                    }],
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: { font: { size: 10 }, padding: 8 },
                        },
                        tooltip: {
                            callbacks: {
                                label: function(ctx) {
                                    const val = ctx.raw || 0;
                                    const total = ctx.dataset.data.reduce((a, b) => a + b, 0);
                                    const pct = total > 0 ? ((val / total) * 100).toFixed(1) : 0;
                                    return `${ctx.label}: ${val.toLocaleString('fr-FR')} ha (${pct}%)`;
                                },
                            },
                        },
                    },
                },
            });
        }

        // Graphique stock carbone (barres horizontales)
        const carbCtx = document.getElementById('chart-carbone');
        if (carbCtx) {
            if (this.carboneChart) this.carboneChart.destroy();
            this.carboneChart = new Chart(carbCtx, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Stock carbone (tCO2)',
                        data: carbones,
                        backgroundColor: colors,
                        borderWidth: 1,
                        borderColor: '#333',
                    }],
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    indexAxis: 'y',
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            callbacks: {
                                label: function(ctx) {
                                    return `${(ctx.raw || 0).toLocaleString('fr-FR')} tCO2`;
                                },
                            },
                        },
                    },
                    scales: {
                        x: { ticks: { font: { size: 10 } } },
                        y: { ticks: { font: { size: 10 } } },
                    },
                },
            });
        }
    },
};
