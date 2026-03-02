/**
 * Chat-to-Map IA Panel v3.0
 *
 * Requetes en langage naturel francais -> filtres Django ORM
 *
 * Nouveautes v3 :
 * - Intent stock_carbone → active le mode CO2 sur la carte
 * - Intent resume → synthese globale avec tableaux par type + foret
 * - Quick actions apres chaque reponse
 * - Explication du fuzzy matching affichee
 * - Meilleure gestion du truncated (limite 200 features)
 * - Message d'accueil enrichi au premier chargement
 * - Heritage de cover_types dans le contexte
 */
const ChatPanel = {
    map: null,

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
        if (input) input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.sendQuery();
        });

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
    },

    // ------------------------------------------------------------------
    // Query sending
    // ------------------------------------------------------------------
    async sendQuery() {
        const input = document.getElementById('chat-input');
        const query = (input ? input.value : '').trim();
        if (!query) return;

        this.addMessage(query, 'user');
        if (input) input.value = '';

        const loading = document.getElementById('ai-loading');
        if (loading) loading.classList.remove('hidden');

        this.showTyping();

        try {
            const result = await API.queryAI(query);
            this.hideTyping();

            if (!result) {
                this.addMessage('Erreur de communication avec le serveur. Reessayez.', 'ai');
                return;
            }

            // Show parsed entity tags
            if (result.parsed) {
                this.showTags(result.parsed);
            }

            // Show explanation if fuzzy match was used
            if (result.explanation) {
                this.addMessage(
                    '<div class="text-[10px] text-amber-600 bg-amber-50 rounded px-2 py-1 mb-1">' +
                    '<i class="fas fa-info-circle mr-1"></i>' + this._esc(result.explanation) +
                    '</div>', 'ai', true
                );
            }

            // Route by response type
            this._handleResponse(result);

            // Update results counter
            const countEl = document.getElementById('ai-results-count');
            if (countEl) {
                const n = result.count || result.nb_results || 0;
                const ms = result.processing_ms || 0;
                countEl.textContent = n > 0
                    ? n + ' resultat(s) — ' + ms + 'ms'
                    : 'Traite en ' + ms + 'ms';
                countEl.classList.remove('hidden');
            }

        } catch (err) {
            this.hideTyping();
            this.addMessage(
                '<div class="text-red-600"><i class="fas fa-exclamation-triangle mr-1"></i>Erreur lors du traitement. Reformulez votre question.</div>',
                'ai', true
            );
            console.error('AI query error:', err);
        }

        if (loading) loading.classList.add('hidden');
    },

    // ------------------------------------------------------------------
    // Response handlers
    // ------------------------------------------------------------------
    _handleResponse(result) {
        switch (result.type) {
            case 'help':
                this._renderHelp(result.data);
                break;
            case 'stock_carbone':
                this._renderStockCarbone(result.data);
                break;
            case 'resume':
                this._renderResume(result.data);
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
                this._renderRanking(result.data, result.ranking_by);
                break;
            case 'no_results':
                this._renderNoResults(result.suggestions);
                break;
            default:
                this.addMessage('Aucun resultat. Essayez une autre formulation.', 'ai');
        }
    },

    // ── HELP ──
    _renderHelp(data) {
        if (!data) return;
        let html = '<div class="space-y-2">';
        html += '<p class="text-sm font-medium">' + data.message + '</p>';

        if (data.capabilities && data.capabilities.length) {
            html += '<p class="text-[10px] text-gray-500 font-bold uppercase tracking-wider mt-2">Ce que je sais faire</p>';
            html += '<ul class="space-y-0.5">';
            data.capabilities.forEach(function(c) {
                html += '<li class="text-xs text-gray-600"><i class="fas fa-check text-green-500 mr-1 text-[9px]"></i>' + c + '</li>';
            });
            html += '</ul>';
        }

        if (data.examples && data.examples.length) {
            html += '<p class="text-[10px] text-gray-500 font-bold uppercase tracking-wider mt-2">Essayez par exemple</p>';
            html += '<div class="flex flex-wrap gap-1 mt-1">';
            data.examples.forEach(function(ex) {
                html += '<span class="text-[10px] bg-green-50 text-green-700 px-2 py-1 rounded-lg cursor-pointer hover:bg-green-100 chat-example border border-green-200">' + ex + '</span>';
            });
            html += '</div>';
        }

        html += '</div>';
        this.addMessage(html, 'ai', true);
        this._bindExamples();
    },

    // ── STOCK CARBONE (activate CO2 mode) ──
    _renderStockCarbone(data) {
        if (!data) return;

        // Activate CO2 mode on the time slider
        if (typeof TimeSlider !== 'undefined' && TimeSlider.setMode) {
            TimeSlider.setMode('carbone');
        }

        let html = '<div class="space-y-2">';
        html += '<div class="flex items-center gap-2">';
        html += '<span class="text-xl">&#x1F33F;</span>';
        html += '<span class="text-sm font-semibold text-green-800">' + data.message + '</span>';
        html += '</div>';
        html += this._quickActions([
            'Resume global pour 2023',
            'Classement des forets par carbone',
            'Deforestation entre 1986 et 2023',
        ]);
        html += '</div>';
        this.addMessage(html, 'ai', true);
        this._bindExamples();
    },

    // ── RESUME (overview) ──
    _renderResume(data) {
        if (!data) {
            this.addMessage('Donnees insuffisantes pour la synthese.', 'ai');
            return;
        }

        let html = '<div class="space-y-3">';
        html += '<p class="text-sm font-semibold">&#x1F4CB; Synthese ' + data.annee + '</p>';

        // Key metrics
        const t = data.totaux || {};
        html += '<div class="grid grid-cols-3 gap-1.5 text-center">';
        html += '<div class="bg-green-50 rounded-lg p-2 border border-green-200">';
        html += '<div class="text-[10px] text-green-600 font-bold uppercase">Superficie</div>';
        html += '<div class="text-sm font-bold text-green-900">' + (t.superficie_ha || 0).toLocaleString('fr-FR', {maximumFractionDigits: 0}) + ' ha</div>';
        html += '</div>';
        html += '<div class="bg-blue-50 rounded-lg p-2 border border-blue-200">';
        html += '<div class="text-[10px] text-blue-600 font-bold uppercase">Carbone</div>';
        html += '<div class="text-sm font-bold text-blue-900">' + (t.carbone_tco2 || 0).toLocaleString('fr-FR', {maximumFractionDigits: 0}) + ' tCO2</div>';
        html += '</div>';
        html += '<div class="bg-amber-50 rounded-lg p-2 border border-amber-200">';
        html += '<div class="text-[10px] text-amber-600 font-bold uppercase">Polygones</div>';
        html += '<div class="text-sm font-bold text-amber-900">' + (t.nb_polygones || 0).toLocaleString('fr-FR') + '</div>';
        html += '</div>';
        html += '</div>';

        // By type
        if (data.par_type && data.par_type.length) {
            html += '<p class="text-[10px] text-gray-500 font-bold uppercase tracking-wider">Par type de couvert</p>';
            html += '<table class="w-full text-xs border-collapse">';
            html += '<tr class="border-b bg-gray-50"><th class="py-1 px-1.5 text-left">Type</th><th class="py-1 px-1.5 text-right">Ha</th><th class="py-1 px-1.5 text-right">tCO2</th></tr>';
            data.par_type.forEach(function(s) {
                var color = s.nomenclature__couleur_hex || '#999';
                var label = s.nomenclature__libelle_fr || '?';
                var sup = (s.total_superficie_ha || 0).toLocaleString('fr-FR', {maximumFractionDigits:0});
                var carb = (s.total_carbone || 0).toLocaleString('fr-FR', {maximumFractionDigits:0});
                html += '<tr class="border-b"><td class="py-0.5 px-1.5"><span class="inline-block w-2 h-2 rounded-sm mr-1" style="background:' + color + '"></span>' + label + '</td>';
                html += '<td class="py-0.5 px-1.5 text-right">' + sup + '</td>';
                html += '<td class="py-0.5 px-1.5 text-right">' + carb + '</td></tr>';
            });
            html += '</table>';
        }

        // By forest
        if (data.par_foret && data.par_foret.length) {
            html += '<p class="text-[10px] text-gray-500 font-bold uppercase tracking-wider mt-1">Par foret</p>';
            html += '<table class="w-full text-xs border-collapse">';
            data.par_foret.forEach(function(f, idx) {
                var medal = idx < 3 ? ['&#x1F947;','&#x1F948;','&#x1F949;'][idx] : (idx+1);
                var nom = f.foret__nom || f.foret__code || '?';
                var sup = (f.total_superficie_ha || 0).toLocaleString('fr-FR', {maximumFractionDigits:0});
                html += '<tr class="border-b"><td class="py-0.5 px-1.5">' + medal + ' ' + nom + '</td>';
                html += '<td class="py-0.5 px-1.5 text-right font-medium">' + sup + ' ha</td></tr>';
            });
            html += '</table>';
        }

        // Quick actions
        html += this._quickActions([
            'Compare entre 1986 et 2023',
            'Deforestation globale',
            'Active le mode CO2',
        ]);
        html += '</div>';
        this.addMessage(html, 'ai', true);
        this._bindExamples();
    },

    // ── GEOJSON ──
    _renderGeojson(result) {
        if (result.data) {
            Choropleth.renderAIResults(result.data, this.map);
        }
        const count = result.count || 0;
        const displayed = result.displayed || count;
        const ms = result.processing_ms || 0;
        const truncated = result.truncated;

        let html = '<div class="space-y-1">';
        html += '<div class="flex items-center gap-2">';
        html += '<span class="text-green-600 text-lg">&#x1F5FA;</span>';
        html += '<span class="text-sm"><strong>' + displayed + '</strong> polygone(s) affiche(s) sur la carte <span class="text-gray-400 text-xs">(' + ms + 'ms)</span></span>';
        html += '</div>';

        if (truncated) {
            html += '<div class="text-[10px] text-amber-600 bg-amber-50 rounded px-2 py-1">';
            html += '<i class="fas fa-info-circle mr-1"></i>' + count + ' resultats au total, ' + displayed + ' affiches (limite). Precisez votre recherche pour voir plus.';
            html += '</div>';
        }

        // Quick actions based on context
        const parsed = result.parsed || {};
        const actions = [];
        if (parsed.forests && parsed.forests.length) {
            actions.push('Statistiques de ' + parsed.forests[0]);
        }
        if (parsed.years && parsed.years.length) {
            actions.push('Compare entre 1986 et 2023');
        }
        actions.push('Resume global');
        html += this._quickActions(actions);
        html += '</div>';

        this.addMessage(html, 'ai', true);
        this._bindExamples();
    },

    // ── STATS ──
    _renderStats(data) {
        if (!data || !Array.isArray(data) || data.length === 0) {
            this.addMessage('Aucune statistique disponible.', 'ai');
            return;
        }

        // Calculate totals
        let totalSup = 0, totalCarb = 0;
        data.forEach(function(s) { totalSup += (s.total_superficie_ha || 0); totalCarb += (s.total_carbone || 0); });

        let html = '<div class="space-y-2">';
        html += '<p class="text-sm font-semibold">&#x1F4CA; Statistiques</p>';
        html += '<table class="w-full text-xs border-collapse">';
        html += '<tr class="border-b bg-gray-50"><th class="py-1.5 px-2 text-left">Type</th><th class="py-1.5 px-2 text-right">Superficie</th><th class="py-1.5 px-2 text-right">Carbone</th></tr>';

        var self = this;
        data.forEach(function(s) {
            var color = s.nomenclature__couleur_hex || '#999';
            var label = s.nomenclature__libelle_fr || s.nomenclature__code || '?';
            var sup = (s.total_superficie_ha || 0).toLocaleString('fr-FR', { maximumFractionDigits: 0 });
            var carb = (s.total_carbone || 0).toLocaleString('fr-FR', { maximumFractionDigits: 0 });
            var pct = totalSup > 0 ? ((s.total_superficie_ha || 0) / totalSup * 100).toFixed(1) : '0';
            html += '<tr class="border-b hover:bg-gray-50">';
            html += '<td class="py-1 px-2"><span class="inline-block w-2.5 h-2.5 rounded-sm mr-1.5" style="background:' + self._escAttr(color) + '"></span>' + self._esc(label) + '</td>';
            html += '<td class="py-1 px-2 text-right font-medium">' + sup + ' ha <span class="text-gray-400">(' + pct + '%)</span></td>';
            html += '<td class="py-1 px-2 text-right">' + carb + ' tCO2</td>';
            html += '</tr>';
        });

        // Total row
        html += '<tr class="bg-green-50 font-bold">';
        html += '<td class="py-1.5 px-2">Total</td>';
        html += '<td class="py-1.5 px-2 text-right">' + totalSup.toLocaleString('fr-FR', {maximumFractionDigits:0}) + ' ha</td>';
        html += '<td class="py-1.5 px-2 text-right">' + totalCarb.toLocaleString('fr-FR', {maximumFractionDigits:0}) + ' tCO2</td>';
        html += '</tr>';

        html += '</table>';
        html += this._quickActions(['Classement des forets', 'Compare entre 1986 et 2023']);
        html += '</div>';
        this.addMessage(html, 'ai', true);
        this._bindExamples();
    },

    // ── COMPARISON ──
    _renderComparison(data) {
        if (!data) {
            this.addMessage('Comparaison impossible (donnees insuffisantes).', 'ai');
            return;
        }
        const a1 = data.annee1, a2 = data.annee2;
        let html = '<div class="space-y-2">';
        html += '<p class="text-sm font-semibold">&#x1F504; Comparaison ' + a1.annee + ' vs ' + a2.annee + '</p>';
        html += '<table class="w-full text-xs border-collapse">';
        html += '<tr class="border-b bg-gray-50"><th class="py-1.5 px-2 text-left">Type</th><th class="py-1.5 px-2 text-right">' + a1.annee + '</th><th class="py-1.5 px-2 text-right">' + a2.annee + '</th><th class="py-1.5 px-2 text-right">Delta</th></tr>';

        const map2 = {};
        (a2.data || []).forEach(function(s) { map2[s.nomenclature__code] = s; });

        var self = this;
        (a1.data || []).forEach(function(s1) {
            var code = s1.nomenclature__code;
            var s2 = map2[code] || {};
            var color = s1.nomenclature__couleur_hex || '#999';
            var label = s1.nomenclature__libelle_fr || code;
            var v1 = s1.superficie_ha || 0;
            var v2 = s2.superficie_ha || 0;
            var delta = v2 - v1;
            var deltaClass = delta > 0 ? 'text-green-600' : delta < 0 ? 'text-red-600' : 'text-gray-400';
            var sign = delta > 0 ? '+' : '';

            html += '<tr class="border-b">';
            html += '<td class="py-1 px-2"><span class="inline-block w-2.5 h-2.5 rounded-sm mr-1" style="background:' + self._escAttr(color) + '"></span>' + self._esc(label) + '</td>';
            html += '<td class="py-1 px-2 text-right">' + v1.toLocaleString('fr-FR', {maximumFractionDigits:0}) + ' ha</td>';
            html += '<td class="py-1 px-2 text-right">' + v2.toLocaleString('fr-FR', {maximumFractionDigits:0}) + ' ha</td>';
            html += '<td class="py-1 px-2 text-right font-semibold ' + deltaClass + '">' + sign + delta.toLocaleString('fr-FR', {maximumFractionDigits:0}) + ' ha</td>';
            html += '</tr>';
        });
        html += '</table>';
        html += this._quickActions(['Deforestation', 'Resume global']);
        html += '</div>';
        this.addMessage(html, 'ai', true);
        this._bindExamples();
    },

    // ── DEFORESTATION ──
    _renderDeforestation(data) {
        if (!data) {
            this.addMessage('Analyse de deforestation impossible (donnees insuffisantes).', 'ai');
            return;
        }
        const arrow = data.perte_ha > 0 ? '&#x1F4C9;' : '&#x1F4C8;';
        const lossClass = data.perte_ha > 0 ? 'text-red-600' : 'text-green-600';
        const sign = data.perte_ha > 0 ? '-' : '+';

        let html = '<div class="space-y-2">';
        html += '<p class="text-sm font-semibold">' + arrow + ' Deforestation (' + data.annee1 + ' &#x2192; ' + data.annee2 + ')</p>';
        html += '<table class="w-full text-xs border-collapse">';
        html += '<tr class="border-b"><td class="py-1.5 text-gray-500">Couvert forestier ' + data.annee1 + '</td><td class="py-1.5 font-semibold text-right">' + data.superficie_foret_1.toLocaleString('fr-FR') + ' ha</td></tr>';
        html += '<tr class="border-b"><td class="py-1.5 text-gray-500">Couvert forestier ' + data.annee2 + '</td><td class="py-1.5 font-semibold text-right">' + data.superficie_foret_2.toLocaleString('fr-FR') + ' ha</td></tr>';
        html += '<tr class="' + lossClass + '"><td class="py-1.5 font-semibold">Variation</td><td class="py-1.5 font-bold text-right">' + sign + Math.abs(data.perte_ha).toLocaleString('fr-FR') + ' ha (' + data.perte_pct + '%)</td></tr>';
        html += '</table>';

        // Detail breakdown
        if (data.detail_1 && data.detail_1.length) {
            html += '<p class="text-[10px] text-gray-400 font-bold uppercase mt-2">Detail par type</p>';
            html += '<div class="flex gap-3 text-xs">';
            html += '<div class="flex-1">';
            html += '<p class="font-semibold text-gray-600 mb-1">' + data.annee1 + '</p>';
            var self = this;
            data.detail_1.forEach(function(d) {
                var c = d.nomenclature__couleur_hex || '#999';
                var l = d.nomenclature__libelle_fr || d.nomenclature__code;
                var v = (d.superficie_ha || 0).toLocaleString('fr-FR', {maximumFractionDigits:0});
                html += '<div><span class="inline-block w-2 h-2 rounded-sm mr-1" style="background:' + self._escAttr(c) + '"></span>' + self._esc(l) + ': ' + v + ' ha</div>';
            });
            html += '</div>';

            if (data.detail_2 && data.detail_2.length) {
                html += '<div class="flex-1">';
                html += '<p class="font-semibold text-gray-600 mb-1">' + data.annee2 + '</p>';
                data.detail_2.forEach(function(d) {
                    var c = d.nomenclature__couleur_hex || '#999';
                    var l = d.nomenclature__libelle_fr || d.nomenclature__code;
                    var v = (d.superficie_ha || 0).toLocaleString('fr-FR', {maximumFractionDigits:0});
                    html += '<div><span class="inline-block w-2 h-2 rounded-sm mr-1" style="background:' + self._escAttr(c) + '"></span>' + self._esc(l) + ': ' + v + ' ha</div>';
                });
                html += '</div>';
            }
            html += '</div>';
        }

        html += this._quickActions(['Resume global', 'Active le mode CO2']);
        html += '</div>';
        this.addMessage(html, 'ai', true);
        this._bindExamples();
    },

    // ── RANKING ──
    _renderRanking(data, rankingBy) {
        if (!data || !data.length) {
            this.addMessage('Aucune donnee pour le classement.', 'ai');
            return;
        }
        const byCarbon = rankingBy === 'carbone';
        const title = byCarbon ? '&#x1F3C6; Classement par stock carbone' : '&#x1F3C6; Classement par superficie';

        let html = '<div class="space-y-2">';
        html += '<p class="text-sm font-semibold">' + title + '</p>';
        html += '<table class="w-full text-xs border-collapse">';
        html += '<tr class="border-b bg-gray-50"><th class="py-1.5 px-2 text-left">#</th><th class="py-1.5 px-2 text-left">Foret</th><th class="py-1.5 px-2 text-right">Superficie</th><th class="py-1.5 px-2 text-right">Carbone</th></tr>';

        var self = this;
        data.forEach(function(item, idx) {
            var medal = idx === 0 ? '&#x1F947;' : idx === 1 ? '&#x1F948;' : idx === 2 ? '&#x1F949;' : (idx + 1);
            var nom = item.foret__nom || item.foret__code || '?';
            var sup = (item.total_superficie_ha || 0).toLocaleString('fr-FR', { maximumFractionDigits: 0 });
            var carb = (item.total_carbone || 0).toLocaleString('fr-FR', { maximumFractionDigits: 0 });
            var supBold = !byCarbon ? ' font-bold' : '';
            var carbBold = byCarbon ? ' font-bold text-green-700' : '';
            html += '<tr class="border-b hover:bg-gray-50">';
            html += '<td class="py-1 px-2">' + medal + '</td>';
            html += '<td class="py-1 px-2 font-medium">' + self._esc(nom) + '</td>';
            html += '<td class="py-1 px-2 text-right' + supBold + '">' + sup + ' ha</td>';
            html += '<td class="py-1 px-2 text-right' + carbBold + '">' + carb + ' tCO2</td>';
            html += '</tr>';
        });
        html += '</table>';

        // Suggest the opposite ranking
        const altAction = byCarbon ? 'Classement des forets par superficie' : 'Classement des forets par carbone';
        html += this._quickActions([altAction, 'Resume global']);
        html += '</div>';
        this.addMessage(html, 'ai', true);
        this._bindExamples();
    },

    // ── NO RESULTS ──
    _renderNoResults(suggestions) {
        let html = '<div class="space-y-2">';
        html += '<p class="text-sm"><i class="fas fa-search text-gray-400 mr-1"></i>Aucun resultat trouve pour cette recherche.</p>';
        if (suggestions && suggestions.length) {
            html += '<p class="text-[10px] text-gray-500 font-bold uppercase tracking-wider">&#x1F4A1; Suggestions</p>';
            html += '<div class="flex flex-wrap gap-1">';
            var self = this;
            suggestions.forEach(function(s) {
                if (s.length > 15 && !s.startsWith('Precisez')) {
                    html += '<span class="text-[10px] bg-green-50 text-green-700 px-2 py-1 rounded-lg cursor-pointer hover:bg-green-100 chat-example border border-green-200">' + self._esc(s) + '</span>';
                } else {
                    html += '<span class="text-[10px] text-amber-700 bg-amber-50 px-2 py-1 rounded-lg border border-amber-200">' + self._esc(s) + '</span>';
                }
            });
            html += '</div>';
        }
        html += '</div>';
        this.addMessage(html, 'ai', true);
        this._bindExamples();
    },

    // ------------------------------------------------------------------
    // Quick Actions (clickable suggestion pills after responses)
    // ------------------------------------------------------------------
    _quickActions(actions) {
        if (!actions || !actions.length) return '';
        let html = '<div class="flex flex-wrap gap-1 mt-2 pt-2 border-t border-gray-100">';
        actions.forEach(function(a) {
            html += '<span class="text-[10px] bg-gray-50 text-gray-600 px-2 py-0.5 rounded-full cursor-pointer hover:bg-green-50 hover:text-green-700 chat-example border border-gray-200 transition-colors">' + a + '</span>';
        });
        html += '</div>';
        return html;
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

        (parsed.forests || []).forEach(function(f) {
            var isInherited = inherited.indexOf('forests') !== -1;
            tags.push({
                label: f,
                color: isInherited ? 'bg-green-50 text-green-600 border border-green-200' : 'bg-green-100 text-green-800',
                icon: 'fa-tree',
            });
        });
        (parsed.cover_types || []).forEach(function(c) {
            var isInherited = inherited.indexOf('cover_types') !== -1;
            tags.push({
                label: c,
                color: isInherited ? 'bg-blue-50 text-blue-600 border border-blue-200' : 'bg-blue-100 text-blue-800',
                icon: 'fa-layer-group',
            });
        });
        (parsed.years || []).forEach(function(y) {
            var isInherited = inherited.indexOf('years') !== -1;
            tags.push({
                label: y,
                color: isInherited ? 'bg-amber-50 text-amber-600 border border-amber-200' : 'bg-amber-100 text-amber-800',
                icon: 'fa-calendar',
            });
        });
        if (parsed.intent) {
            tags.push({
                label: parsed.intent,
                color: 'bg-purple-100 text-purple-800',
                icon: 'fa-bolt',
            });
        }

        container.innerHTML = tags.map(function(t) {
            return '<span class="text-[10px] px-2 py-0.5 rounded-full ' + t.color + '"><i class="fas ' + t.icon + ' mr-0.5 text-[8px] opacity-60"></i>' + t.label + '</span>';
        }).join(' ');
    },

    // ------------------------------------------------------------------
    // Utilities
    // ------------------------------------------------------------------
    _bindExamples() {
        var self = this;
        var input = document.getElementById('chat-input');
        document.querySelectorAll('.chat-example').forEach(function(el) {
            var newEl = el.cloneNode(true);
            el.parentNode.replaceChild(newEl, el);
            newEl.addEventListener('click', function() {
                if (input) {
                    input.value = newEl.textContent.replace(/["\u00AB\u00BB\u201C\u201D]/g, '').trim();
                    self.sendQuery();
                    var panel = document.getElementById('chat-panel');
                    if (panel) panel.classList.remove('hidden');
                }
            });
        });
    },

    /** Escape HTML to prevent XSS */
    _esc(str) {
        var div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    },

    /** Escape for HTML attribute values */
    _escAttr(str) {
        return String(str).replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/'/g, '&#39;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    },
};
