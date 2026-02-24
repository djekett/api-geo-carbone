/**
 * Report Generator — HTML report with embedded CSS
 */
const ReportGenerator = {
    init() {
        const btn = document.getElementById('btn-generate-report');
        if (btn) btn.addEventListener('click', () => this.generate());

        const dl = document.getElementById('report-download');
        if (dl) dl.addEventListener('click', () => this.download());

        const close = document.getElementById('report-modal-close');
        if (close) close.addEventListener('click', () => this.closeModal());

        // Close modal on backdrop click
        const modal = document.getElementById('report-modal');
        if (modal) modal.addEventListener('click', (e) => {
            if (e.target === modal) this.closeModal();
        });
    },

    _html: '',

    async generate() {
        const status = document.getElementById('report-status');
        const btn = document.getElementById('btn-generate-report');
        if (status) { status.classList.remove('hidden'); status.textContent = 'Chargement des données...'; status.className = 'text-xs text-center py-2 text-blue-600'; }
        if (btn) btn.disabled = true;

        try {
            const year = document.getElementById('report-year')?.value || '2023';
            const title = document.getElementById('report-title')?.value || 'Rapport d\'analyse';
            const author = document.getElementById('report-author')?.value || '';
            const notes = document.getElementById('report-notes')?.value || '';

            // Get enabled sections
            const sections = {};
            document.querySelectorAll('.report-section').forEach(cb => {
                sections[cb.value] = cb.checked;
            });

            // Fetch stats
            const stats = await API.getOccupationStats({ annee: year });

            // Build HTML
            this._html = this.buildHTML({ year, title, author, notes, sections, stats });

            // Show in modal
            const content = document.getElementById('report-content');
            if (content) {
                content.innerHTML = `<div class="report-preview">${this._html}</div>`;
            }
            document.getElementById('report-modal')?.classList.remove('hidden');

            if (status) { status.textContent = 'Rapport généré avec succès !'; status.className = 'text-xs text-center py-2 text-green-600'; }
        } catch (err) {
            console.error('Report error:', err);
            if (status) { status.textContent = 'Erreur lors de la génération.'; status.className = 'text-xs text-center py-2 text-red-600'; }
        }

        if (btn) btn.disabled = false;
    },

    buildHTML({ year, title, author, notes, sections, stats }) {
        const now = new Date().toLocaleDateString('fr-FR', { year: 'numeric', month: 'long', day: 'numeric' });
        let html = `<h1>${title}</h1>`;
        html += `<p style="color:#6b7280;font-size:13px;">Date : ${now} | Année d'analyse : ${year}${author ? ' | Auteur : ' + author : ''}</p><hr style="border-color:#e5e7eb;margin:16px 0;">`;

        if (sections.context) {
            html += `<h2>1. Contexte et méthodologie</h2>`;
            html += `<p>Ce rapport analyse l'état de l'occupation du sol et les stocks de carbone dans les 6 forêts classées du département d'Oumé (81 056 ha) pour l'année <strong>${year}</strong>.</p>`;
            html += `<p>Les données sont issues de l'analyse d'images satellitaires (Landsat, Sentinel-2) avec une classification supervisée en 9 types de couvert.</p>`;
            html += `<div class="success-box"><strong>Forêts étudiées :</strong> TENÉ (29 549 ha), DOKA (10 945 ha), SANGOUÉ (27 360 ha), LAHOUDA (3 300 ha), ZOUÉKÉ I (6 825 ha), ZOUÉKÉ II (3 077 ha)</div>`;
        }

        if (sections.stats && stats?.resultats) {
            html += `<h2>2. Statistiques de superficie (${year})</h2>`;
            html += `<table><thead><tr><th>Type de couvert</th><th>Superficie (ha)</th><th>% du total</th></tr></thead><tbody>`;
            const total = stats.totaux?.superficie_ha || 1;
            stats.resultats.forEach(r => {
                const label = r.nomenclature__libelle_fr || r.nomenclature__code || '-';
                const sup = Math.round(r.total_superficie_ha || 0);
                const pct = ((r.total_superficie_ha || 0) / total * 100).toFixed(1);
                html += `<tr><td>${label}</td><td>${sup.toLocaleString('fr-FR')}</td><td>${pct}%</td></tr>`;
            });
            html += `</tbody></table>`;
            html += `<p><strong>Superficie totale :</strong> ${Math.round(total).toLocaleString('fr-FR')} ha</p>`;
        }

        if (sections.carbon && stats?.resultats) {
            html += `<h2>3. Analyse des stocks de carbone</h2>`;
            const carbone = stats.totaux?.carbone_tco2;
            if (carbone) {
                html += `<p>Stock total estimé : <strong>${Math.round(carbone).toLocaleString('fr-FR')} tCO₂</strong></p>`;
            }
            html += `<table><thead><tr><th>Type</th><th>Biomasse (t/ha)</th><th>Carbone (tC/ha)</th><th>CO₂ éq. (tCO₂/ha)</th></tr></thead><tbody>`;
            const ref = {
                'FORET_DENSE': { b: 1739.16, c: 869.10, co2: 3186.70 },
                'FORET_CLAIRE': { b: 1804.16, c: 902.08, co2: 3307.62 },
                'FORET_DEGRADEE': { b: 1062.09, c: 531.04, co2: 1947.15 },
                'JACHERE': { b: 1671.98, c: 792.66, co2: 2906.42 },
            };
            Object.entries(ref).forEach(([code, vals]) => {
                html += `<tr><td>${code.replace(/_/g, ' ')}</td><td>${vals.b.toLocaleString('fr-FR')}</td><td>${vals.c.toLocaleString('fr-FR')}</td><td>${vals.co2.toLocaleString('fr-FR')}</td></tr>`;
            });
            html += `</tbody></table>`;
            html += `<div class="alert-box">Les types non forestiers (cacao, café, hévéa, cultures, sol nu) ont un stock de carbone nul dans cette analyse.</div>`;
        }

        if (sections.evolution) {
            html += `<h2>4. Évolution temporelle</h2>`;
            html += `<p>La comparaison sur 3 périodes (1986, 2003, 2023) montre une dégradation continue du couvert forestier au profit des cultures.</p>`;
            html += `<div class="alert-box">La conversion forêt dense → sol nu représente une perte de <strong>plus de 98%</strong> du stock de carbone (3 187 → 0 tCO₂/ha).</div>`;
        }

        if (sections.recommendations) {
            html += `<h2>5. Recommandations</h2>`;
            html += `<div class="success-box"><strong>Priorités :</strong><br>• Reboisement stratégique des zones les plus dégradées<br>• Développement de l'agroforesterie durable<br>• Mise en œuvre de mécanismes REDD+ pour la valorisation du carbone<br>• Renforcement de la surveillance géospatiale</div>`;
        }

        if (notes) {
            html += `<h2>Notes complémentaires</h2><p>${notes}</p>`;
        }

        html += `<hr style="border-color:#e5e7eb;margin:20px 0;"><p style="color:#9ca3af;font-size:10px;text-align:center;">Rapport généré par API.GEO.Carbone — Département d'Oumé, Côte d'Ivoire</p>`;

        return html;
    },

    download() {
        if (!this._html) return;

        const fullHTML = `<!DOCTYPE html><html lang="fr"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Rapport API.GEO.Carbone</title>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&family=DM+Serif+Display&display=swap" rel="stylesheet">
<style>
body{font-family:'DM Sans',sans-serif;max-width:800px;margin:40px auto;padding:0 24px;color:#1f2937;line-height:1.6;font-size:14px;}
h1{font-family:'DM Serif Display',serif;color:#14532d;font-size:28px;margin-bottom:4px;}
h2{font-family:'DM Serif Display',serif;color:#166534;font-size:20px;margin-top:28px;border-bottom:2px solid #dcfce7;padding-bottom:6px;}
h3{font-size:15px;font-weight:700;color:#374151;margin-top:16px;}
table{width:100%;border-collapse:collapse;margin:14px 0;font-size:13px;}
th{background:#f0fdf4;padding:10px;text-align:left;font-weight:600;border:1px solid #e5e7eb;}
td{padding:8px 10px;border:1px solid #e5e7eb;}
tr:hover{background:#fafafa;}
.alert-box{background:#fef2f2;border-left:4px solid #ef4444;padding:12px 16px;margin:14px 0;border-radius:6px;}
.success-box{background:#f0fdf4;border-left:4px solid #22c55e;padding:12px 16px;margin:14px 0;border-radius:6px;}
hr{border:none;border-top:1px solid #e5e7eb;}
</style></head><body>${this._html}</body></html>`;

        const blob = new Blob([fullHTML], { type: 'text/html' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `rapport-geocarbone-${new Date().toISOString().slice(0, 10)}.html`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    },

    closeModal() {
        document.getElementById('report-modal')?.classList.add('hidden');
    },
};
