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
