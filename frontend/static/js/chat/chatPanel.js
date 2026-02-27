/**
 * Chat-to-Map IA Panel v3.0
 *
 * Requetes en langage naturel francais -> filtres Django ORM
 *
 * Nouveautes v3 :
 * - Rendu HTML riche (tables, couleurs, icones)
 * - Indicateur de frappe (typing dots)
 * - Reponse help avec exemples cliquables
 * - Analyse de deforestation en tableau
 * - Stats en tableau HTML avec pastilles de couleur
 * - Comparaison enrichie avec delta
 * - Classement des forets
 * - Suggestions intelligentes en cas de zero resultat
 * - Heritage de contexte (tags inherited)
 * - Rendu de predictions avec fleches de tendance
 * - Export de rapport telechargeable
 * - Raccourcis clavier (Escape, Ctrl+Enter)
 * - Historique de requetes (localStorage, fleches haut/bas)
 * - Auto-suggestions en temps reel
 * - Indicateur de confiance
 * - Calcul de superficie
 */
const ChatPanel = {
    map: null,
    _queryHistory: [],
    _historyIndex: -1,
    _maxHistory: 10,
    _suggestionsVisible: false,

    // Example queries for auto-suggestions
    _exampleQueries: [
        "Montre les zones de foret dense a TENE en 2023",
        "Superficie de foret claire a SANGOUE en 2023",
        "Compare TENE entre 1986 et 2023",
        "Deforestation a DOKA",
        "Deforestation a LAHOUDA",
        "Statistiques de carbone pour 2023",
        "Classement des forets par superficie",
        "Prevision de deforestation pour 2030",
        "Exporter les donnees de TENE en 2023",
        "Calculer la superficie de foret dense a DOKA",
        "Pourcentage de cacao a SANGOUE en 2023",
        "Compare TENE et DOKA en 2023",
        "Foret dense a ZOUEKE en 2003",
        "Quelle est la plus grande foret en 2023",
        "Superficie de LAHOUDA avant 2003",
        "Tendance de deforestation a TENE pour 2040",
        "Surface totale de foret degradee en 1986",
        "Carbone stocke a DOKA en 2023",
        "Evolution de SANGOUE entre 1986 et 2023",
        "Rapport de deforestation a TENE",
    ],

    init(map) {
        this.map = map;

        const toggle = document.getElementById('chat-toggle');
        const close = document.getElementById('chat-close');
        const panel = document.getElementById('chat-panel');
        const send = document.getElementById('chat-send');
        const input = document.getElementById('chat-input');

        if (toggle) toggle.addEventListener('click', () => panel.classList.toggle('hidden'));
        if (close) close.addEventListener('click', () => panel.classList.add('hidden'));

        if (send) send.addEventListener('click', () => this.sendQuery());
        if (input) {
            input.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && !e.ctrlKey) this.sendQuery();
            });

            // Keyboard shortcuts: Ctrl+Enter to send
            input.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && e.ctrlKey) {
                    e.preventDefault();
                    this.sendQuery();
                }

                // Arrow up/down for query history
                if (e.key === 'ArrowUp') {
                    e.preventDefault();
                    this._navigateHistory('up', input);
                }
                if (e.key === 'ArrowDown') {
                    e.preventDefault();
                    this._navigateHistory('down', input);
                }

                // Escape to close panel
                if (e.key === 'Escape') {
                    this._hideSuggestions();
                    if (panel) panel.classList.add('hidden');
                }
            });

            // Auto-suggestions on input
            input.addEventListener('input', (e) => {
                this._showAutoSuggestions(input.value);
            });

            // Hide suggestions when clicking outside
            document.addEventListener('click', (e) => {
                if (!e.target.closest('#chat-input') && !e.target.closest('#chat-suggestions')) {
                    this._hideSuggestions();
                }
            });
        }

        // Global Escape handler for closing panel
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && panel && !panel.classList.contains('hidden')) {
                panel.classList.add('hidden');
            }
        });

        // Load query history from localStorage
        this._loadHistory();

        // Exemples cliquables (initiaux)
        this._bindExamples();

        // Barre de recherche IA dans la sidebar
        const aiSearch = document.getElementById('ai-search');
        if (aiSearch) {
            aiSearch.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    const q = aiSearch.value.trim();
                    if (q && input) {
                        input.value = q;
                        this.sendQuery();
                        if (panel) panel.classList.remove('hidden');
                    }
                }
            });
        }

        // Create suggestions container if it doesn't exist
        this._createSuggestionsContainer();
    },

    // ------------------------------------------------------------------
    // Query history management
    // ------------------------------------------------------------------
    _loadHistory() {
        try {
            const stored = localStorage.getItem('chat_query_history');
            if (stored) {
                this._queryHistory = JSON.parse(stored);
            }
        } catch (e) {
            this._queryHistory = [];
        }
    },

    _saveHistory(query) {
        // Remove duplicate if exists
        this._queryHistory = this._queryHistory.filter(q => q !== query);
        // Add to front
        this._queryHistory.unshift(query);
        // Keep only last N
        if (this._queryHistory.length > this._maxHistory) {
            this._queryHistory = this._queryHistory.slice(0, this._maxHistory);
        }
        // Reset index
        this._historyIndex = -1;
        // Save to localStorage
        try {
            localStorage.setItem('chat_query_history', JSON.stringify(this._queryHistory));
        } catch (e) {
            // localStorage might be full or unavailable
        }
    },

    _navigateHistory(direction, input) {
        if (!this._queryHistory.length) return;

        if (direction === 'up') {
            if (this._historyIndex < this._queryHistory.length - 1) {
                this._historyIndex++;
            }
        } else {
            if (this._historyIndex > -1) {
                this._historyIndex--;
            }
        }

        if (this._historyIndex === -1) {
            input.value = '';
        } else {
            input.value = this._queryHistory[this._historyIndex];
        }
    },

    // ------------------------------------------------------------------
    // Auto-suggestions
    // ------------------------------------------------------------------
    _createSuggestionsContainer() {
        const input = document.getElementById('chat-input');
        if (!input) return;

        // Check if container already exists
        if (document.getElementById('chat-suggestions')) return;

        const container = document.createElement('div');
        container.id = 'chat-suggestions';
        container.className = 'absolute bottom-full left-0 right-0 bg-white border border-gray-200 rounded-t-lg shadow-lg max-h-48 overflow-y-auto z-50 hidden';
        container.style.cssText = 'position: absolute; bottom: 100%; left: 0; right: 0;';

        // Insert before input's parent
        const inputParent = input.parentElement;
        if (inputParent) {
            inputParent.style.position = 'relative';
            inputParent.insertBefore(container, input);
        }
    },

    _showAutoSuggestions(value) {
        const container = document.getElementById('chat-suggestions');
        if (!container) return;

        const trimmed = value.trim().toLowerCase();
        if (trimmed.length < 2) {
            this._hideSuggestions();
            return;
        }

        // Filter matching examples
        const matches = this._exampleQueries.filter(q =>
            q.toLowerCase().includes(trimmed)
        ).slice(0, 5);

        // Also add matching history items
        const historyMatches = this._queryHistory.filter(q =>
            q.toLowerCase().includes(trimmed) && !matches.includes(q)
        ).slice(0, 3);

        const allMatches = [...historyMatches.map(q => ({ text: q, isHistory: true })),
                           ...matches.map(q => ({ text: q, isHistory: false }))];

        if (allMatches.length === 0) {
            this._hideSuggestions();
            return;
        }

        container.innerHTML = allMatches.map(item => {
            const icon = item.isHistory ? '&#x1F550;' : '&#x1F4AC;';
            return `<div class="px-3 py-2 text-xs cursor-pointer hover:bg-green-50 border-b border-gray-100 chat-suggestion"
                         data-query="${this._escAttr(item.text)}">
                        <span class="mr-1">${icon}</span>
                        ${this._esc(item.text)}
                    </div>`;
        }).join('');

        container.classList.remove('hidden');
        this._suggestionsVisible = true;

        // Bind click events
        container.querySelectorAll('.chat-suggestion').forEach(el => {
            el.addEventListener('click', () => {
                const input = document.getElementById('chat-input');
                if (input) {
                    input.value = el.dataset.query;
                    this._hideSuggestions();
                    this.sendQuery();
                }
            });
        });
    },

    _hideSuggestions() {
        const container = document.getElementById('chat-suggestions');
        if (container) {
            container.classList.add('hidden');
            container.innerHTML = '';
        }
        this._suggestionsVisible = false;
    },

    // ------------------------------------------------------------------
    // Query sending
    // ------------------------------------------------------------------
    async sendQuery() {
        const input = document.getElementById('chat-input');
        const query = (input ? input.value : '').trim();
        if (!query) return;

        this._hideSuggestions();
        this.addMessage(query, 'user');
        this._saveHistory(query);
        if (input) input.value = '';

        const loading = document.getElementById('ai-loading');
        if (loading) loading.classList.remove('hidden');

        this.showTyping();

        try {
            const result = await API.queryAI(query);
            this.hideTyping();

            if (!result) {
                this.addMessage('Erreur de communication avec le serveur.', 'ai');
                return;
            }

            // Show parsed entity tags
            if (result.parsed) {
                this.showTags(result.parsed);
            }

            // Show confidence indicator
            if (result.metadata && typeof result.metadata.confidence === 'number') {
                this._showConfidence(result.metadata.confidence);
            } else if (result.parsed && typeof result.parsed.confidence === 'number') {
                this._showConfidence(result.parsed.confidence);
            }

            // Route by response type
            this._handleResponse(result);

            // Update results counter
            const countEl = document.getElementById('ai-results-count');
            if (countEl) {
                const n = result.count || result.nb_results || 0;
                countEl.textContent = `${n} resultat(s) -- ${result.processing_ms || 0}ms`;
                countEl.classList.remove('hidden');
            }

        } catch (err) {
            this.hideTyping();
            this.addMessage('Erreur lors du traitement de la requete.', 'ai');
            console.error('AI query error:', err);
        }

        if (loading) loading.classList.add('hidden');
    },

    // ------------------------------------------------------------------
    // Confidence indicator
    // ------------------------------------------------------------------
    _showConfidence(score) {
        let container = document.getElementById('ai-confidence');
        if (!container) {
            // Try to find a place to put it near the tags
            const tagsContainer = document.getElementById('ai-tags');
            if (tagsContainer) {
                container = document.createElement('div');
                container.id = 'ai-confidence';
                container.className = 'mt-1';
                tagsContainer.parentElement.insertBefore(container, tagsContainer.nextSibling);
            } else {
                return;
            }
        }

        const pct = Math.round(score * 100);
        let colorClass = 'bg-red-400';
        let label = 'Faible';
        if (pct >= 75) {
            colorClass = 'bg-green-500';
            label = 'Eleve';
        } else if (pct >= 50) {
            colorClass = 'bg-yellow-400';
            label = 'Moyen';
        } else if (pct >= 25) {
            colorClass = 'bg-orange-400';
            label = 'Partiel';
        }

        container.innerHTML = `
            <div class="flex items-center gap-2 text-[10px] text-gray-500">
                <span>Confiance:</span>
                <div class="flex-1 bg-gray-200 rounded-full h-1.5 max-w-[80px]">
                    <div class="${colorClass} h-1.5 rounded-full transition-all" style="width: ${pct}%"></div>
                </div>
                <span class="font-medium">${label} (${pct}%)</span>
            </div>
        `;
    },

    // ------------------------------------------------------------------
    // Response handlers
    // ------------------------------------------------------------------
    _handleResponse(result) {
        switch (result.type) {

            case 'help':
                this._renderHelp(result.data);
                break;

            case 'geojson':
                this._renderGeojson(result);
                break;

            case 'stats':
                this._renderStats(result.data);
                break;

            case 'comparison':
                this._renderComparison(result.data);
                break;

            case 'deforestation':
                this._renderDeforestation(result.data);
                break;

            case 'ranking':
                this._renderRanking(result.data);
                break;

            case 'prediction':
                this._renderPrediction(result.data);
                break;

            case 'export':
                this._renderExport(result.data);
                break;

            case 'area_calc':
                this._renderAreaCalc(result.data);
                break;

            case 'no_results':
                this._renderNoResults(result.suggestions, result.detail);
                break;

            default:
                this.addMessage('Aucun resultat trouve. Essayez une autre formulation.', 'ai');
        }
    },

    _renderHelp(data) {
        if (!data) return;
        let html = '<div class="space-y-2">';
        html += `<p class="text-sm font-medium">${data.message}</p>`;

        if (data.capabilities && data.capabilities.length) {
            html += '<p class="text-[10px] text-gray-500 font-bold uppercase tracking-wider mt-2">Capacites</p>';
            html += '<ul class="space-y-0.5">';
            data.capabilities.forEach(c => {
                html += `<li class="text-xs text-gray-600">&#x2022; ${c}</li>`;
            });
            html += '</ul>';
        }

        if (data.examples && data.examples.length) {
            html += '<p class="text-[10px] text-gray-500 font-bold uppercase tracking-wider mt-2">Exemples</p>';
            html += '<ul class="space-y-1">';
            data.examples.forEach(ex => {
                html += `<li class="text-xs text-green-700 cursor-pointer hover:underline chat-example">"${ex}"</li>`;
            });
            html += '</ul>';
        }
        html += '</div>';
        this.addMessage(html, 'ai', true);
        this._bindExamples();
    },

    _renderGeojson(result) {
        if (result.data) {
            Choropleth.renderAIResults(result.data, this.map);
        }
        const count = result.count || 0;
        const ms = result.processing_ms || 0;
        const html = `<div class="flex items-center gap-2">
            <span class="text-green-600 text-lg">&#x1F5FA;</span>
            <span class="text-sm"><strong>${count}</strong> polygone(s) affiche(s) sur la carte <span class="text-gray-400 text-xs">(${ms}ms)</span></span>
        </div>`;
        this.addMessage(html, 'ai', true);
    },

    _renderStats(data) {
        if (!data || !Array.isArray(data) || data.length === 0) {
            this.addMessage('Aucune statistique disponible.', 'ai');
            return;
        }

        const hasPercentage = data.some(s => s.pourcentage !== undefined);

        let html = '<div class="space-y-2">';
        html += '<p class="text-sm font-semibold">&#x1F4CA; Statistiques</p>';
        html += '<table class="w-full text-xs border-collapse">';
        html += '<tr class="border-b bg-gray-50"><th class="py-1.5 px-2 text-left">Type</th><th class="py-1.5 px-2 text-right">Superficie</th>';
        if (hasPercentage) {
            html += '<th class="py-1.5 px-2 text-right">%</th>';
        }
        html += '<th class="py-1.5 px-2 text-right">Carbone</th></tr>';

        data.forEach(s => {
            const color = s.nomenclature__couleur_hex || '#999';
            const label = s.nomenclature__libelle_fr || s.nomenclature__code || '?';
            const sup = (s.total_superficie_ha || 0).toLocaleString('fr-FR', { maximumFractionDigits: 0 });
            const carb = (s.total_carbone || 0).toLocaleString('fr-FR', { maximumFractionDigits: 0 });
            html += `<tr class="border-b hover:bg-gray-50">
                <td class="py-1 px-2"><span class="inline-block w-2.5 h-2.5 rounded-sm mr-1.5" style="background:${this._escAttr(color)}"></span>${this._esc(label)}</td>
                <td class="py-1 px-2 text-right font-medium">${sup} ha</td>`;
            if (hasPercentage) {
                html += `<td class="py-1 px-2 text-right text-gray-500">${s.pourcentage || 0}%</td>`;
            }
            html += `<td class="py-1 px-2 text-right">${carb} tCO2</td>
            </tr>`;
        });
        html += '</table></div>';
        this.addMessage(html, 'ai', true);
    },

    _renderComparison(data) {
        if (!data) {
            this.addMessage('Comparaison impossible (donnees insuffisantes).', 'ai');
            return;
        }
        const a1 = data.annee1, a2 = data.annee2;
        let html = '<div class="space-y-2">';
        html += `<p class="text-sm font-semibold">&#x1F504; Comparaison ${a1.annee} vs ${a2.annee}</p>`;
        html += '<table class="w-full text-xs border-collapse">';
        html += `<tr class="border-b bg-gray-50"><th class="py-1.5 px-2 text-left">Type</th><th class="py-1.5 px-2 text-right">${a1.annee}</th><th class="py-1.5 px-2 text-right">${a2.annee}</th><th class="py-1.5 px-2 text-right">Delta</th></tr>`;

        const map2 = {};
        (a2.data || []).forEach(s => { map2[s.nomenclature__code] = s; });

        (a1.data || []).forEach(s1 => {
            const code = s1.nomenclature__code;
            const s2 = map2[code] || {};
            const color = s1.nomenclature__couleur_hex || '#999';
            const label = s1.nomenclature__libelle_fr || code;
            const v1 = s1.superficie_ha || 0;
            const v2 = s2.superficie_ha || 0;
            const delta = v2 - v1;
            const deltaClass = delta > 0 ? 'text-green-600' : delta < 0 ? 'text-red-600' : 'text-gray-400';
            const sign = delta > 0 ? '+' : '';

            html += `<tr class="border-b">
                <td class="py-1 px-2"><span class="inline-block w-2.5 h-2.5 rounded-sm mr-1" style="background:${this._escAttr(color)}"></span>${this._esc(label)}</td>
                <td class="py-1 px-2 text-right">${v1.toLocaleString('fr-FR', {maximumFractionDigits:0})} ha</td>
                <td class="py-1 px-2 text-right">${v2.toLocaleString('fr-FR', {maximumFractionDigits:0})} ha</td>
                <td class="py-1 px-2 text-right font-semibold ${deltaClass}">${sign}${delta.toLocaleString('fr-FR', {maximumFractionDigits:0})} ha</td>
            </tr>`;
        });
        html += '</table></div>';
        this.addMessage(html, 'ai', true);
    },

    _renderDeforestation(data) {
        if (!data) {
            this.addMessage('Analyse de deforestation impossible (donnees insuffisantes).', 'ai');
            return;
        }
        const arrow = data.perte_ha > 0 ? '&#x1F4C9;' : '&#x1F4C8;';
        const lossClass = data.perte_ha > 0 ? 'text-red-600' : 'text-green-600';
        const sign = data.perte_ha > 0 ? '-' : '+';

        let html = '<div class="space-y-2">';
        html += `<p class="text-sm font-semibold">${arrow} Deforestation (${data.annee1} &#x2192; ${data.annee2})</p>`;
        html += '<table class="w-full text-xs border-collapse">';
        html += `<tr class="border-b"><td class="py-1.5 text-gray-500">Couvert forestier ${data.annee1}</td><td class="py-1.5 font-semibold text-right">${data.superficie_foret_1.toLocaleString('fr-FR')} ha</td></tr>`;
        html += `<tr class="border-b"><td class="py-1.5 text-gray-500">Couvert forestier ${data.annee2}</td><td class="py-1.5 font-semibold text-right">${data.superficie_foret_2.toLocaleString('fr-FR')} ha</td></tr>`;
        html += `<tr class="${lossClass}"><td class="py-1.5 font-semibold">Variation</td><td class="py-1.5 font-bold text-right">${sign}${Math.abs(data.perte_ha).toLocaleString('fr-FR')} ha (${data.perte_pct}%)</td></tr>`;
        html += '</table>';

        // Detail breakdown if available
        if (data.detail_1 && data.detail_1.length) {
            html += `<p class="text-[10px] text-gray-400 font-bold uppercase mt-2">Detail par type</p>`;
            html += '<div class="flex gap-3 text-xs">';
            html += '<div class="flex-1">';
            html += `<p class="font-semibold text-gray-600 mb-1">${data.annee1}</p>`;
            data.detail_1.forEach(d => {
                const c = d.nomenclature__couleur_hex || '#999';
                const l = d.nomenclature__libelle_fr || d.nomenclature__code;
                const v = (d.superficie_ha || 0).toLocaleString('fr-FR', {maximumFractionDigits:0});
                html += `<div><span class="inline-block w-2 h-2 rounded-sm mr-1" style="background:${this._escAttr(c)}"></span>${this._esc(l)}: ${v} ha</div>`;
            });
            html += '</div>';

            if (data.detail_2 && data.detail_2.length) {
                html += '<div class="flex-1">';
                html += `<p class="font-semibold text-gray-600 mb-1">${data.annee2}</p>`;
                data.detail_2.forEach(d => {
                    const c = d.nomenclature__couleur_hex || '#999';
                    const l = d.nomenclature__libelle_fr || d.nomenclature__code;
                    const v = (d.superficie_ha || 0).toLocaleString('fr-FR', {maximumFractionDigits:0});
                    html += `<div><span class="inline-block w-2 h-2 rounded-sm mr-1" style="background:${this._escAttr(c)}"></span>${this._esc(l)}: ${v} ha</div>`;
                });
                html += '</div>';
            }
            html += '</div>';
        }

        html += '</div>';
        this.addMessage(html, 'ai', true);
    },

    _renderRanking(data) {
        if (!data || !data.length) {
            this.addMessage('Aucune donnee pour le classement.', 'ai');
            return;
        }
        let html = '<div class="space-y-2">';
        html += '<p class="text-sm font-semibold">&#x1F3C6; Classement des forets</p>';
        html += '<table class="w-full text-xs border-collapse">';
        html += '<tr class="border-b bg-gray-50"><th class="py-1.5 px-2 text-left">#</th><th class="py-1.5 px-2 text-left">Foret</th><th class="py-1.5 px-2 text-right">Superficie</th><th class="py-1.5 px-2 text-right">Carbone</th></tr>';

        data.forEach((item, idx) => {
            const medal = idx === 0 ? '&#x1F947;' : idx === 1 ? '&#x1F948;' : idx === 2 ? '&#x1F949;' : (idx + 1);
            const nom = item.foret__nom || item.foret__code || '?';
            const sup = (item.total_superficie_ha || 0).toLocaleString('fr-FR', { maximumFractionDigits: 0 });
            const carb = (item.total_carbone || 0).toLocaleString('fr-FR', { maximumFractionDigits: 0 });
            html += `<tr class="border-b hover:bg-gray-50">
                <td class="py-1 px-2">${medal}</td>
                <td class="py-1 px-2 font-medium">${this._esc(nom)}</td>
                <td class="py-1 px-2 text-right">${sup} ha</td>
                <td class="py-1 px-2 text-right">${carb} tCO2</td>
            </tr>`;
        });
        html += '</table></div>';
        this.addMessage(html, 'ai', true);
    },

    // ------------------------------------------------------------------
    // NEW: Prediction renderer
    // ------------------------------------------------------------------
    _renderPrediction(data) {
        if (!data || !data.predictions || data.predictions.length === 0) {
            this.addMessage('Aucune prediction disponible (donnees historiques insuffisantes).', 'ai');
            return;
        }

        let html = '<div class="space-y-2">';
        html += `<p class="text-sm font-semibold">&#x1F52E; Projection pour ${data.target_year}</p>`;

        // Predictions table
        html += '<table class="w-full text-xs border-collapse">';
        html += '<tr class="border-b bg-gray-50">';
        html += '<th class="py-1.5 px-2 text-left">Type</th>';
        html += '<th class="py-1.5 px-2 text-right">Tendance</th>';
        html += '<th class="py-1.5 px-2 text-right">Projection</th>';
        html += '<th class="py-1.5 px-2 text-right">Carbone</th>';
        html += '<th class="py-1.5 px-2 text-right">/an</th>';
        html += '</tr>';

        data.predictions.forEach(p => {
            const color = p.couleur || '#999';
            const label = p.libelle || p.code || '?';

            // Trend arrow and color
            let trendIcon, trendClass;
            if (p.trend === 'hausse') {
                trendIcon = '&#x2191;';  // up arrow
                trendClass = 'text-green-600';
            } else if (p.trend === 'baisse') {
                trendIcon = '&#x2193;';  // down arrow
                trendClass = 'text-red-600';
            } else {
                trendIcon = '&#x2194;';  // left-right arrow
                trendClass = 'text-gray-500';
            }

            const projected = (p.predicted_superficie_ha || 0).toLocaleString('fr-FR', {maximumFractionDigits: 0});
            const carbone = (p.predicted_carbone || 0).toLocaleString('fr-FR', {maximumFractionDigits: 0});
            const annual = p.annual_change_ha || 0;
            const annualSign = annual > 0 ? '+' : '';
            const annualClass = annual > 0 ? 'text-green-600' : annual < 0 ? 'text-red-600' : 'text-gray-400';

            html += `<tr class="border-b hover:bg-gray-50">
                <td class="py-1 px-2"><span class="inline-block w-2.5 h-2.5 rounded-sm mr-1.5" style="background:${this._escAttr(color)}"></span>${this._esc(label)}</td>
                <td class="py-1 px-2 text-right ${trendClass} font-semibold">${trendIcon}</td>
                <td class="py-1 px-2 text-right font-medium">${projected} ha</td>
                <td class="py-1 px-2 text-right">${carbone} tCO2</td>
                <td class="py-1 px-2 text-right ${annualClass}">${annualSign}${annual.toLocaleString('fr-FR', {maximumFractionDigits: 1})} ha</td>
            </tr>`;

            // Mini historical sparkline as text
            if (p.historical && p.historical.length) {
                html += '<tr class="border-b"><td colspan="5" class="py-0.5 px-2 text-[10px] text-gray-400">';
                html += 'Historique: ';
                html += p.historical.map(h =>
                    `${h.annee}: ${(h.superficie_ha || 0).toLocaleString('fr-FR', {maximumFractionDigits: 0})} ha`
                ).join(' &#x2192; ');
                html += '</td></tr>';
            }
        });

        html += '</table>';

        // Warning message
        if (data.warning) {
            html += `<div class="mt-2 p-2 bg-amber-50 border border-amber-200 rounded text-[10px] text-amber-700">
                <strong>&#x26A0; Avertissement :</strong> ${this._esc(data.warning)}
            </div>`;
        }

        html += '</div>';
        this.addMessage(html, 'ai', true);
    },

    // ------------------------------------------------------------------
    // NEW: Export renderer
    // ------------------------------------------------------------------
    _renderExport(data) {
        if (!data) {
            this.addMessage('Aucune donnee a exporter.', 'ai');
            return;
        }

        // Build a text summary for download
        let reportText = '=== RAPPORT API.GEO.CARBONE ===\n';
        reportText += `Date: ${new Date().toLocaleDateString('fr-FR')}\n`;
        reportText += `Forets: ${(data.forests || []).join(', ') || 'Toutes'}\n`;
        reportText += `Annees: ${(data.years || []).join(', ') || 'Non specifiee'}\n`;
        reportText += `Types: ${(data.cover_types || []).join(', ') || 'Tous'}\n`;
        reportText += '\n--- STATISTIQUES ---\n';

        if (data.stats && data.stats.length) {
            data.stats.forEach(s => {
                const label = s.nomenclature__libelle_fr || s.nomenclature__code || '?';
                const sup = (s.total_superficie_ha || 0).toFixed(2);
                const carb = (s.total_carbone || 0).toFixed(2);
                reportText += `${label}: ${sup} ha | ${carb} tCO2\n`;
            });
        }

        if (data.area) {
            reportText += `\nTotal superficie: ${data.area.total_superficie_ha} ha\n`;
            reportText += `Total carbone: ${data.area.total_carbone} tCO2\n`;
            reportText += `Nombre polygones: ${data.area.total_polygones}\n`;
        }

        reportText += '\n=== FIN DU RAPPORT ===\n';

        // Create downloadable blob
        const blob = new Blob([reportText], { type: 'text/plain;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        const filename = `rapport_geo_carbone_${new Date().toISOString().slice(0, 10)}.txt`;

        let html = '<div class="space-y-2">';
        html += '<p class="text-sm font-semibold">&#x1F4E4; Rapport pret</p>';

        // Show summary
        if (data.stats && data.stats.length) {
            html += '<table class="w-full text-xs border-collapse">';
            html += '<tr class="border-b bg-gray-50"><th class="py-1.5 px-2 text-left">Type</th><th class="py-1.5 px-2 text-right">Superficie</th><th class="py-1.5 px-2 text-right">Carbone</th></tr>';
            data.stats.forEach(s => {
                const color = s.nomenclature__couleur_hex || '#999';
                const label = s.nomenclature__libelle_fr || s.nomenclature__code || '?';
                const sup = (s.total_superficie_ha || 0).toLocaleString('fr-FR', { maximumFractionDigits: 0 });
                const carb = (s.total_carbone || 0).toLocaleString('fr-FR', { maximumFractionDigits: 0 });
                html += `<tr class="border-b">
                    <td class="py-1 px-2"><span class="inline-block w-2.5 h-2.5 rounded-sm mr-1.5" style="background:${this._escAttr(color)}"></span>${this._esc(label)}</td>
                    <td class="py-1 px-2 text-right">${sup} ha</td>
                    <td class="py-1 px-2 text-right">${carb} tCO2</td>
                </tr>`;
            });
            html += '</table>';
        }

        // Download button
        html += `<a href="${url}" download="${filename}"
                    class="inline-flex items-center gap-1.5 mt-2 px-3 py-1.5 bg-green-600 text-white text-xs rounded hover:bg-green-700 transition-colors cursor-pointer"
                    onclick="setTimeout(function(){URL.revokeObjectURL('${url}')},1000)">
                    &#x1F4BE; Telecharger le rapport (.txt)
                 </a>`;

        html += '</div>';
        this.addMessage(html, 'ai', true);
    },

    // ------------------------------------------------------------------
    // NEW: Area calculation renderer
    // ------------------------------------------------------------------
    _renderAreaCalc(data) {
        if (!data || !data.detail || data.detail.length === 0) {
            this.addMessage('Aucune donnee de superficie disponible.', 'ai');
            return;
        }

        let html = '<div class="space-y-2">';
        html += '<p class="text-sm font-semibold">&#x1F4D0; Calcul de superficies</p>';

        // Metadata
        if (data.forests && data.forests.length) {
            html += `<p class="text-[10px] text-gray-500">Forets: ${data.forests.join(', ')}</p>`;
        }
        if (data.years && data.years.length) {
            html += `<p class="text-[10px] text-gray-500">Annees: ${data.years.join(', ')}</p>`;
        }

        // Detail table
        html += '<table class="w-full text-xs border-collapse">';
        html += '<tr class="border-b bg-gray-50"><th class="py-1.5 px-2 text-left">Type</th><th class="py-1.5 px-2 text-right">Superficie</th><th class="py-1.5 px-2 text-right">%</th><th class="py-1.5 px-2 text-right">Carbone</th></tr>';

        data.detail.forEach(d => {
            const color = d.nomenclature__couleur_hex || '#999';
            const label = d.nomenclature__libelle_fr || d.nomenclature__code || '?';
            const sup = (d.total_superficie_ha || 0).toLocaleString('fr-FR', { maximumFractionDigits: 0 });
            const pct = d.pourcentage || 0;
            const carb = (d.total_carbone || 0).toLocaleString('fr-FR', { maximumFractionDigits: 0 });

            html += `<tr class="border-b hover:bg-gray-50">
                <td class="py-1 px-2"><span class="inline-block w-2.5 h-2.5 rounded-sm mr-1.5" style="background:${this._escAttr(color)}"></span>${this._esc(label)}</td>
                <td class="py-1 px-2 text-right font-medium">${sup} ha</td>
                <td class="py-1 px-2 text-right text-gray-500">${pct}%</td>
                <td class="py-1 px-2 text-right">${carb} tCO2</td>
            </tr>`;
        });

        // Totals row
        const totalSup = (data.total_superficie_ha || 0).toLocaleString('fr-FR', { maximumFractionDigits: 0 });
        const totalCarb = (data.total_carbone || 0).toLocaleString('fr-FR', { maximumFractionDigits: 0 });
        html += `<tr class="bg-gray-100 font-semibold">
            <td class="py-1.5 px-2">TOTAL</td>
            <td class="py-1.5 px-2 text-right">${totalSup} ha</td>
            <td class="py-1.5 px-2 text-right">100%</td>
            <td class="py-1.5 px-2 text-right">${totalCarb} tCO2</td>
        </tr>`;

        html += '</table>';
        html += `<p class="text-[10px] text-gray-400 mt-1">${data.total_polygones || 0} polygone(s)</p>`;
        html += '</div>';
        this.addMessage(html, 'ai', true);
    },

    _renderNoResults(suggestions, detail) {
        let html = '<div class="space-y-2">';
        html += '<p class="text-sm">Aucun resultat trouve.</p>';
        if (detail) {
            html += `<p class="text-xs text-gray-500">${this._esc(detail)}</p>`;
        }
        if (suggestions && suggestions.length) {
            html += '<p class="text-[10px] text-gray-500 font-bold uppercase tracking-wider">&#x1F4A1; Suggestions</p>';
            html += '<ul class="space-y-1">';
            suggestions.forEach(s => {
                // If suggestion looks like an example query, make it clickable
                if (s.length > 20 && !s.startsWith('Precisez')) {
                    html += `<li class="text-xs text-green-700 cursor-pointer hover:underline chat-example">"${this._esc(s)}"</li>`;
                } else {
                    html += `<li class="text-xs text-amber-700">&#x2022; ${this._esc(s)}</li>`;
                }
            });
            html += '</ul>';
        }
        html += '</div>';
        this.addMessage(html, 'ai', true);
        this._bindExamples();
    },

    // ------------------------------------------------------------------
    // Message display
    // ------------------------------------------------------------------
    addMessage(text, type, isHtml) {
        const container = document.getElementById('chat-messages');
        if (!container) return;

        const div = document.createElement('div');
        div.className = type === 'user' ? 'chat-msg-user' : 'chat-msg-ai';

        if (isHtml) {
            div.innerHTML = text;
        } else {
            div.style.whiteSpace = 'pre-wrap';
            div.textContent = text;
        }

        container.appendChild(div);
        container.scrollTop = container.scrollHeight;
    },

    showTyping() {
        const container = document.getElementById('chat-messages');
        if (!container) return;
        const div = document.createElement('div');
        div.id = 'typing-indicator';
        div.className = 'chat-msg-ai';
        div.innerHTML = '<span class="flex gap-1.5 items-center py-1"><span class="typing-dot"></span><span class="typing-dot"></span><span class="typing-dot"></span></span>';
        container.appendChild(div);
        container.scrollTop = container.scrollHeight;
    },

    hideTyping() {
        const el = document.getElementById('typing-indicator');
        if (el) el.remove();
    },

    showTags(parsed) {
        const container = document.getElementById('ai-tags');
        if (!container || !parsed) return;

        container.innerHTML = '';
        const tags = [];
        const inherited = parsed._inherited || [];

        (parsed.forests || []).forEach(f => {
            const isInherited = inherited.includes('forests');
            tags.push({
                label: f,
                color: isInherited ? 'bg-green-50 text-green-600 border border-green-200' : 'bg-green-100 text-green-800',
            });
        });
        (parsed.cover_types || []).forEach(c => tags.push({ label: c, color: 'bg-blue-100 text-blue-800' }));
        (parsed.years || []).forEach(y => {
            const isInherited = inherited.includes('years');
            tags.push({
                label: y,
                color: isInherited ? 'bg-amber-50 text-amber-600 border border-amber-200' : 'bg-amber-100 text-amber-800',
            });
        });
        if (parsed.intent) tags.push({ label: parsed.intent, color: 'bg-purple-100 text-purple-800' });
        if (parsed.percentage_mode) tags.push({ label: '%', color: 'bg-indigo-100 text-indigo-800' });
        if (parsed.target_year) tags.push({ label: `-> ${parsed.target_year}`, color: 'bg-cyan-100 text-cyan-800' });
        if (parsed.sort_order) {
            const sortLabel = parsed.sort_order === 'asc' ? 'ASC' : 'DESC';
            tags.push({ label: sortLabel, color: 'bg-pink-100 text-pink-800' });
        }

        container.innerHTML = tags.map(t =>
            `<span class="text-xs px-2 py-0.5 rounded-full ${t.color}">${t.label}</span>`
        ).join(' ');
    },

    // ------------------------------------------------------------------
    // Utilities
    // ------------------------------------------------------------------
    _bindExamples() {
        const input = document.getElementById('chat-input');
        document.querySelectorAll('.chat-example').forEach(el => {
            // Remove old listener by cloning
            const newEl = el.cloneNode(true);
            el.parentNode.replaceChild(newEl, el);
            newEl.addEventListener('click', () => {
                if (input) {
                    input.value = newEl.textContent.replace(/["\u00AB\u00BB\u201C\u201D]/g, '').trim();
                    this.sendQuery();
                    const panel = document.getElementById('chat-panel');
                    if (panel) panel.classList.remove('hidden');
                }
            });
        });
    },

    /** Escape HTML to prevent XSS */
    _esc(str) {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    },

    /** Escape for HTML attribute values */
    _escAttr(str) {
        return String(str).replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/'/g, '&#39;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    },
};
