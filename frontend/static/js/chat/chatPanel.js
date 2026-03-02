/**
 * Chat-to-Map IA Panel v4.0 — "Extraordinaire"
 *
 * Refonte complete avec :
 * - Mini Chart.js (doughnut/bar) directement dans les messages
 * - Compteurs animes (requestAnimationFrame + easing)
 * - Fly-to forest sur la carte avec pulse highlight
 * - Toast notifications animees
 * - Particules feuilles flottantes (CSS-only)
 * - Typewriter effect pour le welcome
 * - Fun facts ecologiques
 * - Score de confiance
 * - Reactions (thumbs up/down)
 * - Quick actions contextuelles du backend
 * - Glassmorphism UI
 */
const ChatPanel = {
    map: null,
    _chartInstances: [],
    _pulseLayer: null,

    // ==================================================================
    // Init
    // ==================================================================
    init(map) {
        this.map = map;

        var toggle = document.getElementById('chat-toggle');
        var close  = document.getElementById('chat-close');
        var panel  = document.getElementById('chat-panel');
        var send   = document.getElementById('chat-send');
        var input  = document.getElementById('chat-input');

        var self = this;

        if (toggle) toggle.addEventListener('click', function() {
            panel.classList.toggle('hidden');
            if (!panel.classList.contains('hidden') && !self._welcomed) {
                self._showWelcome();
            }
        });
        if (close) close.addEventListener('click', function() {
            panel.classList.add('hidden');
        });
        if (send) send.addEventListener('click', function() { self.sendQuery(); });
        if (input) input.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') self.sendQuery();
        });

        // AI search in sidebar
        var aiSearch = document.getElementById('ai-search');
        if (aiSearch) {
            aiSearch.addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    var q = aiSearch.value.trim();
                    if (q && input) {
                        input.value = q;
                        self.sendQuery();
                        if (panel) panel.classList.remove('hidden');
                    }
                }
            });
        }

        // Create floating particles
        this._createParticles();
    },

    _welcomed: false,

    // ==================================================================
    // Welcome Message with Typewriter
    // ==================================================================
    _showWelcome() {
        this._welcomed = true;
        var container = document.getElementById('chat-messages');
        if (!container) return;

        var div = document.createElement('div');
        div.className = 'chat-msg-ai';
        div.innerHTML =
            '<div class="space-y-3 stagger-children">' +
                '<div class="flex items-center gap-2">' +
                    '<div class="ai-avatar" style="width:24px;height:24px;border-radius:7px;">' +
                        '<i class="fas fa-leaf text-white text-[10px]"></i>' +
                    '</div>' +
                    '<span class="text-sm font-bold text-green-900" id="welcome-text"></span>' +
                    '<span class="typewriter-cursor" id="welcome-cursor"></span>' +
                '</div>' +
                '<div id="welcome-body" style="display:none">' +
                    '<p class="text-xs text-gray-500 mb-2">Je peux analyser <strong>6 forets classees</strong> du departement d\'Oume sur <strong>3 epoques</strong> (1986, 2003, 2023).</p>' +
                    '<div class="grid grid-cols-1 gap-1.5" id="welcome-examples"></div>' +
                '</div>' +
            '</div>';
        container.appendChild(div);

        // Typewriter effect
        var text = 'Bienvenue sur GEO-Carbone IA !';
        var target = document.getElementById('welcome-text');
        var cursor = document.getElementById('welcome-cursor');
        var i = 0;
        var self = this;
        function type() {
            if (i < text.length) {
                target.textContent += text.charAt(i);
                i++;
                setTimeout(type, 35);
            } else {
                if (cursor) cursor.remove();
                // Show body after typewriter
                var body = document.getElementById('welcome-body');
                if (body) body.style.display = 'block';
                // Add example suggestions
                self._addWelcomeExamples();
            }
        }
        setTimeout(type, 400);
    },

    _addWelcomeExamples() {
        var container = document.getElementById('welcome-examples');
        if (!container) return;

        var examples = [
            { icon: 'fa-chart-bar', text: 'Resume global pour 2023', color: 'bg-green-50 text-green-700 border-green-200' },
            { icon: 'fa-exchange-alt', text: 'Compare TENE 1986 vs 2023', color: 'bg-blue-50 text-blue-700 border-blue-200' },
            { icon: 'fa-fire-alt', text: 'Deforestation a DOKA', color: 'bg-red-50 text-red-700 border-red-200' },
            { icon: 'fa-leaf', text: 'Active le mode CO2', color: 'bg-emerald-50 text-emerald-700 border-emerald-200' },
        ];

        var self = this;
        examples.forEach(function(ex, idx) {
            var pill = document.createElement('div');
            pill.className = 'flex items-center gap-2 p-2 rounded-lg border cursor-pointer transition-all hover:shadow-md hover:-translate-y-0.5 chat-example ' + ex.color;
            pill.style.animationDelay = (0.5 + idx * 0.1) + 's';
            pill.innerHTML = '<i class="fas ' + ex.icon + ' text-xs"></i><span class="text-xs font-medium">' + ex.text + '</span>';
            container.appendChild(pill);
        });

        this._bindExamples();
    },

    // ==================================================================
    // Floating Leaf Particles
    // ==================================================================
    _createParticles() {
        var container = document.getElementById('chat-particles');
        if (!container) return;

        var leaves = ['🍃', '🌿', '🍂', '🌱', '☘️', '🍃'];
        for (var i = 0; i < 6; i++) {
            var leaf = document.createElement('span');
            leaf.className = 'leaf-particle';
            leaf.textContent = leaves[i];
            leaf.style.setProperty('--duration', (10 + Math.random() * 8) + 's');
            leaf.style.setProperty('--delay', (i * 2.5) + 's');
            leaf.style.setProperty('--size', (10 + Math.random() * 8) + 'px');
            leaf.style.setProperty('--left', (10 + Math.random() * 80) + '%');
            leaf.style.setProperty('--max-opacity', (0.12 + Math.random() * 0.1).toFixed(2));
            container.appendChild(leaf);
        }
    },

    // ==================================================================
    // Query Sending
    // ==================================================================
    async sendQuery() {
        var input = document.getElementById('chat-input');
        var query = (input ? input.value : '').trim();
        if (!query) return;

        this.addMessage(query, 'user');
        if (input) input.value = '';

        var loading = document.getElementById('ai-loading');
        if (loading) loading.classList.remove('hidden');

        this.showTyping();

        var self = this;
        try {
            var result = await API.queryAI(query);
            self.hideTyping();

            if (!result) {
                self.addMessage('Erreur de communication avec le serveur. Reessayez.', 'ai');
                return;
            }

            // Show parsed entity tags
            if (result.parsed) self.showTags(result.parsed);

            // Update context badge
            self._updateContextBadge(result.parsed);

            // Show explanation if fuzzy match was used
            if (result.explanation) {
                self.addMessage(
                    '<div class="text-[10px] text-amber-600 bg-amber-50/80 rounded-lg px-2.5 py-1.5 mb-1 flex items-center gap-1.5">' +
                    '<i class="fas fa-magic text-amber-500"></i>' + self._esc(result.explanation) +
                    '</div>', 'ai', true
                );
            }

            // Route by response type
            self._handleResponse(result);

            // Update results counter
            var countEl = document.getElementById('ai-results-count');
            if (countEl) {
                var n = result.count || result.nb_results || 0;
                var ms = result.processing_ms || 0;
                countEl.textContent = n > 0 ? n + ' resultat(s) — ' + ms + 'ms' : 'Traite en ' + ms + 'ms';
                countEl.classList.remove('hidden');
            }

        } catch (err) {
            self.hideTyping();
            self.addMessage(
                '<div class="text-red-600 flex items-center gap-2"><i class="fas fa-exclamation-triangle"></i>Erreur lors du traitement. Reformulez votre question.</div>',
                'ai', true
            );
            console.error('AI query error:', err);
        }

        if (loading) loading.classList.add('hidden');
    },

    // ==================================================================
    // Response Router
    // ==================================================================
    _handleResponse(result) {
        switch (result.type) {
            case 'help':           this._renderHelp(result); break;
            case 'stock_carbone':  this._renderStockCarbone(result); break;
            case 'resume':         this._renderResume(result); break;
            case 'geojson':        this._renderGeojson(result); break;
            case 'stats':          this._renderStats(result); break;
            case 'comparison':     this._renderComparison(result); break;
            case 'deforestation':  this._renderDeforestation(result); break;
            case 'ranking':        this._renderRanking(result); break;
            case 'no_results':     this._renderNoResults(result); break;
            default:               this.addMessage('Aucun resultat. Essayez une autre formulation.', 'ai');
        }
    },

    // ==================================================================
    // HELP
    // ==================================================================
    _renderHelp(result) {
        var data = result.data;
        if (!data) return;

        var capIcons = [
            { icon: 'fa-map', bg: 'bg-green-100 text-green-600' },
            { icon: 'fa-calculator', bg: 'bg-blue-100 text-blue-600' },
            { icon: 'fa-exchange-alt', bg: 'bg-purple-100 text-purple-600' },
            { icon: 'fa-chart-line', bg: 'bg-red-100 text-red-600' },
            { icon: 'fa-trophy', bg: 'bg-amber-100 text-amber-600' },
            { icon: 'fa-file-alt', bg: 'bg-teal-100 text-teal-600' },
            { icon: 'fa-leaf', bg: 'bg-emerald-100 text-emerald-600' },
        ];

        var html = '<div class="space-y-3 stagger-children">';
        html += '<div class="flex items-center gap-2"><div class="ai-avatar" style="width:24px;height:24px;border-radius:7px;"><i class="fas fa-leaf text-white text-[10px]"></i></div>';
        html += '<span class="text-sm font-bold text-green-900">' + this._esc(data.message) + '</span></div>';

        if (data.capabilities && data.capabilities.length) {
            html += '<div class="space-y-1.5">';
            var self = this;
            data.capabilities.forEach(function(c, i) {
                var ci = capIcons[i] || capIcons[0];
                html += '<div class="capability-card"><div class="capability-icon ' + ci.bg + '"><i class="fas ' + ci.icon + '"></i></div><span class="text-gray-700">' + self._esc(c) + '</span></div>';
            });
            html += '</div>';
        }

        if (data.examples && data.examples.length) {
            html += '<div class="flex flex-wrap gap-1.5 mt-1">';
            data.examples.forEach(function(ex) {
                html += '<span class="quick-action-pill chat-example">' + ex + '</span>';
            });
            html += '</div>';
        }

        html += '</div>';
        this._addAIMessage(html, result);
    },

    // ==================================================================
    // STOCK CARBONE (activate CO2 mode)
    // ==================================================================
    _renderStockCarbone(result) {
        var data = result.data;
        if (!data) return;

        if (typeof TimeSlider !== 'undefined' && TimeSlider.setMode) {
            TimeSlider.setMode('carbone');
        }

        // Toast notification
        this._showToast('Mode CO2 active !', 'success');

        var html = '<div class="space-y-3 stagger-children">';
        html += '<div class="flex items-center gap-3">';
        html += '<div style="font-size:28px">🌍</div>';
        html += '<div><div class="text-sm font-bold text-green-800">' + this._esc(data.message) + '</div>';
        html += '<div class="text-[10px] text-green-600 mt-0.5">4 classes forestieres • Gradient tCO2/ha</div></div>';
        html += '</div>';
        html += '</div>';
        this._addAIMessage(html, result);
    },

    // ==================================================================
    // RESUME (overview) with Chart.js
    // ==================================================================
    _renderResume(result) {
        var data = result.data;
        if (!data) { this.addMessage('Donnees insuffisantes pour la synthese.', 'ai'); return; }

        var t = data.totaux || {};
        var chartData = result.chart_data;
        var chartId = 'resume-chart-' + Date.now();

        var html = '<div class="space-y-3 stagger-children">';
        html += '<div class="text-sm font-bold text-green-900 flex items-center gap-2">📋 Synthese ' + data.annee + '</div>';

        // Metric cards with animated counters
        html += '<div class="grid grid-cols-3 gap-2">';
        html += '<div class="metric-card"><div class="text-[9px] text-green-600 font-bold uppercase">Superficie</div>';
        html += '<div class="text-sm font-bold text-green-900 anim-counter" data-target="' + Math.round(t.superficie_ha || 0) + '" data-suffix=" ha">0 ha</div></div>';
        html += '<div class="metric-card"><div class="text-[9px] text-blue-600 font-bold uppercase">Carbone</div>';
        html += '<div class="text-sm font-bold text-blue-900 anim-counter" data-target="' + Math.round(t.carbone_tco2 || 0) + '" data-suffix=" tCO2">0 tCO2</div></div>';
        html += '<div class="metric-card"><div class="text-[9px] text-amber-600 font-bold uppercase">Polygones</div>';
        html += '<div class="text-sm font-bold text-amber-900 anim-counter" data-target="' + (t.nb_polygones || 0) + '" data-suffix="">0</div></div>';
        html += '</div>';

        // Mini Chart.js doughnut
        if (chartData) {
            html += '<div class="chat-chart-wrap"><div class="chat-chart-container"><canvas id="' + chartId + '"></canvas></div></div>';
        }

        // Progress bars by type
        if (data.par_type && data.par_type.length) {
            var totalSup = t.superficie_ha || 1;
            html += '<div class="text-[9px] text-gray-500 font-bold uppercase tracking-wider">Repartition</div>';
            html += '<div class="space-y-1.5">';
            var self = this;
            data.par_type.forEach(function(s) {
                var color = s.nomenclature__couleur_hex || '#999';
                var label = s.nomenclature__libelle_fr || '?';
                var sup = (s.total_superficie_ha || 0);
                var pct = (sup / totalSup * 100).toFixed(1);
                html += '<div class="text-xs"><div class="flex justify-between mb-0.5"><span><span class="inline-block w-2 h-2 rounded-sm mr-1" style="background:' + self._escAttr(color) + '"></span>' + self._esc(label) + '</span>';
                html += '<span class="text-gray-500 font-medium">' + sup.toLocaleString('fr-FR', {maximumFractionDigits:0}) + ' ha (' + pct + '%)</span></div>';
                html += '<div class="progress-bar-track"><div class="progress-bar-fill" style="background:' + self._escAttr(color) + '" data-width="' + pct + '%"></div></div></div>';
            });
            html += '</div>';
        }

        html += '</div>';
        this._addAIMessage(html, result);

        // Render chart after DOM insertion
        if (chartData) {
            var self = this;
            setTimeout(function() { self._renderMiniDoughnut(chartId, chartData); }, 100);
        }

        // Animate counters & progress bars
        var self = this;
        setTimeout(function() { self._animateAllCounters(); self._animateProgressBars(); }, 200);
    },

    // ==================================================================
    // STATS with Chart.js
    // ==================================================================
    _renderStats(result) {
        var data = result.data;
        var chartData = result.chart_data;
        if (!data || !Array.isArray(data) || data.length === 0) {
            this.addMessage('Aucune statistique disponible.', 'ai');
            return;
        }

        var totalSup = 0, totalCarb = 0;
        data.forEach(function(s) { totalSup += (s.total_superficie_ha || 0); totalCarb += (s.total_carbone || 0); });

        var chartId = 'stats-chart-' + Date.now();

        var html = '<div class="space-y-3 stagger-children">';
        html += '<div class="text-sm font-bold text-green-900">📊 Statistiques</div>';

        // Mini Chart
        if (chartData) {
            html += '<div class="chat-chart-wrap"><div class="chat-chart-container chart-sm"><canvas id="' + chartId + '"></canvas></div></div>';
        }

        // Progress bars instead of table
        html += '<div class="space-y-1.5">';
        var self = this;
        data.forEach(function(s) {
            var color = s.nomenclature__couleur_hex || '#999';
            var label = s.nomenclature__libelle_fr || s.nomenclature__code || '?';
            var sup = (s.total_superficie_ha || 0);
            var carb = (s.total_carbone || 0);
            var pct = totalSup > 0 ? (sup / totalSup * 100).toFixed(1) : '0';
            html += '<div class="text-xs"><div class="flex justify-between mb-0.5">';
            html += '<span><span class="inline-block w-2 h-2 rounded-sm mr-1" style="background:' + self._escAttr(color) + '"></span>' + self._esc(label) + '</span>';
            html += '<span class="font-medium">' + sup.toLocaleString('fr-FR', {maximumFractionDigits:0}) + ' ha <span class="text-gray-400">(' + pct + '%)</span></span></div>';
            html += '<div class="progress-bar-track"><div class="progress-bar-fill" style="background:' + self._escAttr(color) + '" data-width="' + pct + '%"></div></div></div>';
        });
        html += '</div>';

        // Total
        html += '<div class="flex justify-between text-xs font-bold bg-green-50/80 rounded-lg px-3 py-2 border border-green-200/50">';
        html += '<span>Total</span><span>' + totalSup.toLocaleString('fr-FR', {maximumFractionDigits:0}) + ' ha • ' + totalCarb.toLocaleString('fr-FR', {maximumFractionDigits:0}) + ' tCO2</span></div>';

        html += '</div>';
        this._addAIMessage(html, result);

        if (chartData) {
            var self = this;
            setTimeout(function() { self._renderMiniDoughnut(chartId, chartData); }, 100);
        }
        var self = this;
        setTimeout(function() { self._animateProgressBars(); }, 200);
    },

    // ==================================================================
    // COMPARISON with dual charts
    // ==================================================================
    _renderComparison(result) {
        var data = result.data;
        if (!data) { this.addMessage('Comparaison impossible (donnees insuffisantes).', 'ai'); return; }

        var a1 = data.annee1, a2 = data.annee2;
        var chartData = result.chart_data;
        var chartId = 'comp-chart-' + Date.now();

        var html = '<div class="space-y-3 stagger-children">';
        html += '<div class="text-sm font-bold text-green-900">🔄 Comparaison ' + a1.annee + ' vs ' + a2.annee + '</div>';

        // Comparison bar chart
        if (chartData) {
            html += '<div class="chat-chart-wrap"><div class="chat-chart-container" style="width:240px;height:160px;"><canvas id="' + chartId + '"></canvas></div></div>';
        }

        // Delta table with visual indicators
        var map2 = {};
        (a2.data || []).forEach(function(s) { map2[s.nomenclature__code] = s; });

        html += '<div class="space-y-1">';
        var self = this;
        (a1.data || []).forEach(function(s1) {
            var code = s1.nomenclature__code;
            var s2 = map2[code] || {};
            var color = s1.nomenclature__couleur_hex || '#999';
            var label = s1.nomenclature__libelle_fr || code;
            var v1 = s1.superficie_ha || 0;
            var v2 = s2.superficie_ha || 0;
            var delta = v2 - v1;
            var deltaIcon = delta > 0 ? '<i class="fas fa-arrow-up text-green-500 text-[8px]"></i>' : delta < 0 ? '<i class="fas fa-arrow-down text-red-500 text-[8px]"></i>' : '<i class="fas fa-minus text-gray-400 text-[8px]"></i>';
            var deltaClass = delta > 0 ? 'text-green-600' : delta < 0 ? 'text-red-600' : 'text-gray-400';
            var sign = delta > 0 ? '+' : '';

            html += '<div class="flex items-center justify-between text-xs py-1 border-b border-gray-100">';
            html += '<span><span class="inline-block w-2 h-2 rounded-sm mr-1" style="background:' + self._escAttr(color) + '"></span>' + self._esc(label) + '</span>';
            html += '<span class="flex items-center gap-2">';
            html += '<span class="text-gray-400">' + v1.toLocaleString('fr-FR', {maximumFractionDigits:0}) + '</span>';
            html += '<span>→</span>';
            html += '<span class="font-medium">' + v2.toLocaleString('fr-FR', {maximumFractionDigits:0}) + '</span>';
            html += '<span class="' + deltaClass + ' font-bold flex items-center gap-0.5">' + deltaIcon + ' ' + sign + delta.toLocaleString('fr-FR', {maximumFractionDigits:0}) + '</span>';
            html += '</span></div>';
        });
        html += '</div>';

        html += '</div>';
        this._addAIMessage(html, result);

        // Render grouped bar chart
        if (chartData) {
            var self = this;
            setTimeout(function() { self._renderComparisonChart(chartId, chartData); }, 100);
        }
    },

    // ==================================================================
    // DEFORESTATION with loss bar
    // ==================================================================
    _renderDeforestation(result) {
        var data = result.data;
        if (!data) { this.addMessage('Analyse de deforestation impossible.', 'ai'); return; }

        var arrow = data.perte_ha > 0 ? '📉' : '📈';
        var lossPct = Math.min(Math.abs(data.perte_pct || 0), 100);

        var html = '<div class="space-y-3 stagger-children">';
        html += '<div class="text-sm font-bold text-green-900">' + arrow + ' Deforestation ' + data.annee1 + ' → ' + data.annee2 + '</div>';

        // Big loss indicator
        html += '<div class="text-center py-2">';
        html += '<div class="text-3xl font-bold text-red-600 anim-counter" data-target="' + Math.abs(Math.round(data.perte_ha)) + '" data-suffix=" ha" data-prefix="-">0 ha</div>';
        html += '<div class="text-xs text-red-500 font-medium">de couvert forestier perdu</div>';
        html += '</div>';

        // Visual loss bar
        html += '<div class="loss-bar-track"><div class="loss-bar-fill" data-width="' + lossPct + '%" style="width:0%"><span>' + lossPct.toFixed(1) + '%</span></div></div>';

        // Before/After metrics
        html += '<div class="grid grid-cols-2 gap-2">';
        html += '<div class="metric-card"><div class="text-[9px] text-gray-500 font-bold uppercase">' + data.annee1 + '</div>';
        html += '<div class="text-sm font-bold text-green-800 anim-counter" data-target="' + Math.round(data.superficie_foret_1) + '" data-suffix=" ha">0 ha</div></div>';
        html += '<div class="metric-card"><div class="text-[9px] text-gray-500 font-bold uppercase">' + data.annee2 + '</div>';
        html += '<div class="text-sm font-bold text-red-700 anim-counter" data-target="' + Math.round(data.superficie_foret_2) + '" data-suffix=" ha">0 ha</div></div>';
        html += '</div>';

        // Detail breakdown
        if (data.detail_1 && data.detail_1.length) {
            html += '<div class="text-[9px] text-gray-400 font-bold uppercase mt-1">Detail par type</div>';
            html += '<div class="grid grid-cols-2 gap-2 text-xs">';
            html += '<div>';
            var self = this;
            data.detail_1.forEach(function(d) {
                var c = d.nomenclature__couleur_hex || '#999';
                var l = d.nomenclature__libelle_fr || d.nomenclature__code;
                var v = (d.superficie_ha || 0).toLocaleString('fr-FR', {maximumFractionDigits:0});
                html += '<div class="flex items-center gap-1 py-0.5"><span class="w-2 h-2 rounded-sm flex-shrink-0" style="background:' + self._escAttr(c) + '"></span><span class="truncate">' + self._esc(l) + '</span><span class="ml-auto font-medium">' + v + '</span></div>';
            });
            html += '</div>';

            if (data.detail_2 && data.detail_2.length) {
                html += '<div>';
                data.detail_2.forEach(function(d) {
                    var c = d.nomenclature__couleur_hex || '#999';
                    var l = d.nomenclature__libelle_fr || d.nomenclature__code;
                    var v = (d.superficie_ha || 0).toLocaleString('fr-FR', {maximumFractionDigits:0});
                    html += '<div class="flex items-center gap-1 py-0.5"><span class="w-2 h-2 rounded-sm flex-shrink-0" style="background:' + self._escAttr(c) + '"></span><span class="truncate">' + self._esc(l) + '</span><span class="ml-auto font-medium">' + v + '</span></div>';
                });
                html += '</div>';
            }
            html += '</div>';
        }

        html += '</div>';
        this._addAIMessage(html, result);

        var self = this;
        setTimeout(function() {
            self._animateAllCounters();
            // Animate loss bar
            var fills = document.querySelectorAll('.loss-bar-fill[data-width]');
            fills.forEach(function(f) { f.style.width = f.dataset.width; });
        }, 200);
    },

    // ==================================================================
    // RANKING with cards + fly-to
    // ==================================================================
    _renderRanking(result) {
        var data = result.data;
        var rankingBy = result.ranking_by;
        if (!data || !data.length) { this.addMessage('Aucune donnee pour le classement.', 'ai'); return; }

        var byCarbon = rankingBy === 'carbone';
        var title = byCarbon ? '🏆 Classement par stock carbone' : '🏆 Classement par superficie';
        var maxVal = data[0] ? (byCarbon ? (data[0].total_carbone || 0) : (data[0].total_superficie_ha || 0)) : 1;

        var html = '<div class="space-y-2 stagger-children">';
        html += '<div class="text-sm font-bold text-green-900">' + title + '</div>';

        var self = this;
        var medals = ['🥇', '🥈', '🥉'];
        data.forEach(function(item, idx) {
            var medal = idx < 3 ? medals[idx] : '<span class="text-sm text-gray-400 font-bold">' + (idx+1) + '</span>';
            var nom = item.foret__nom || item.foret__code || '?';
            var code = item.foret__code || '';
            var sup = (item.total_superficie_ha || 0);
            var carb = (item.total_carbone || 0);
            var mainVal = byCarbon ? carb : sup;
            var pct = maxVal > 0 ? (mainVal / maxVal * 100) : 0;

            html += '<div class="ranking-card" data-forest="' + self._escAttr(code) + '" style="animation-delay:' + (idx * 0.08) + 's">';
            html += '<div class="ranking-medal">' + medal + '</div>';
            html += '<div class="flex-1 min-w-0">';
            html += '<div class="text-xs font-bold text-gray-800 truncate">' + self._esc(nom) + '</div>';
            html += '<div class="text-[10px] text-gray-500">' + sup.toLocaleString('fr-FR', {maximumFractionDigits:0}) + ' ha • ' + carb.toLocaleString('fr-FR', {maximumFractionDigits:0}) + ' tCO2</div>';
            html += '<div class="progress-bar-track mt-1"><div class="progress-bar-fill" style="background:' + (byCarbon ? '#16a34a' : '#2563eb') + '" data-width="' + pct.toFixed(0) + '%"></div></div>';
            html += '</div>';
            html += '<i class="fas fa-map-marker-alt text-green-500 text-xs flex-shrink-0"></i>';
            html += '</div>';
        });

        html += '</div>';
        this._addAIMessage(html, result);

        // Bind fly-to on ranking cards
        var self = this;
        setTimeout(function() {
            self._animateProgressBars();
            document.querySelectorAll('.ranking-card[data-forest]').forEach(function(card) {
                card.addEventListener('click', function() {
                    self._flyToForest(card.dataset.forest);
                });
            });
        }, 200);
    },

    // ==================================================================
    // GEOJSON
    // ==================================================================
    _renderGeojson(result) {
        if (result.data) {
            Choropleth.renderAIResults(result.data, this.map);
        }
        var count = result.count || 0;
        var displayed = result.displayed || count;
        var ms = result.processing_ms || 0;
        var truncated = result.truncated;

        var html = '<div class="space-y-2 stagger-children">';
        html += '<div class="flex items-center gap-3">';
        html += '<div style="font-size:24px">🗺️</div>';
        html += '<div><div class="text-sm font-medium"><strong class="anim-counter" data-target="' + displayed + '">' + displayed + '</strong> polygone(s) affiche(s)</div>';
        html += '<div class="text-[10px] text-gray-400">' + ms + 'ms de traitement</div></div>';
        html += '</div>';

        if (truncated) {
            html += '<div class="text-[10px] text-amber-600 bg-amber-50/80 rounded-lg px-2.5 py-1.5 flex items-center gap-1.5">';
            html += '<i class="fas fa-info-circle"></i>' + count + ' resultats au total, ' + displayed + ' affiches. Precisez votre recherche.';
            html += '</div>';
        }

        // Fly to first forest if coordinates available
        if (result.coordinates && result.coordinates.length) {
            this._flyToForest(result.coordinates[0].code);
        }

        html += '</div>';
        this._addAIMessage(html, result);
    },

    // ==================================================================
    // NO RESULTS
    // ==================================================================
    _renderNoResults(result) {
        var suggestions = result.suggestions;
        var html = '<div class="space-y-2 stagger-children">';
        html += '<div class="flex items-center gap-2"><span style="font-size:20px">🔍</span><span class="text-sm text-gray-600">Aucun resultat trouve.</span></div>';
        if (suggestions && suggestions.length) {
            html += '<div class="text-[9px] text-gray-500 font-bold uppercase tracking-wider">Essayez :</div>';
            html += '<div class="flex flex-wrap gap-1.5">';
            suggestions.forEach(function(s) {
                if (s.length > 15) {
                    html += '<span class="quick-action-pill chat-example">' + s + '</span>';
                } else {
                    html += '<span class="text-[10px] text-amber-700 bg-amber-50 px-2.5 py-1 rounded-lg border border-amber-200">' + s + '</span>';
                }
            });
            html += '</div>';
        }
        html += '</div>';
        this._addAIMessage(html, result);
    },

    // ==================================================================
    // Message System
    // ==================================================================
    _addAIMessage(html, result) {
        // Add fun fact
        if (result && result.fun_fact) {
            html += '<div class="fun-fact-card"><span class="mr-1">🌿</span><strong>Le saviez-vous ?</strong> ' + this._esc(result.fun_fact) + '</div>';
        }

        // Add confidence bar
        if (result && result.confidence) {
            var conf = result.confidence;
            var confColor = conf >= 80 ? '#22c55e' : conf >= 50 ? '#f59e0b' : '#ef4444';
            html += '<div class="flex items-center gap-2 mt-1"><span class="text-[9px] text-gray-400">Confiance</span>';
            html += '<div class="confidence-bar flex-1"><div class="confidence-fill" style="width:' + conf + '%;background:' + confColor + '"></div></div>';
            html += '<span class="text-[9px] font-bold" style="color:' + confColor + '">' + conf + '%</span></div>';
        }

        // Add quick actions from backend suggestions
        if (result && result.suggestions && result.suggestions.length) {
            html += '<div class="quick-actions-v4">';
            result.suggestions.forEach(function(s) {
                html += '<span class="quick-action-pill chat-example">' + s + '</span>';
            });
            html += '</div>';
        }

        // Wrap in message with reactions
        var fullHtml = html + '<div class="msg-reactions"><button class="reaction-btn" data-reaction="up" title="Utile"><i class="fas fa-thumbs-up"></i></button><button class="reaction-btn" data-reaction="down" title="Pas utile"><i class="fas fa-thumbs-down"></i></button></div>';

        this.addMessage(fullHtml, 'ai', true);
        this._bindExamples();
        this._bindReactions();
    },

    addMessage(text, type, isHtml) {
        var container = document.getElementById('chat-messages');
        if (!container) return;

        var div = document.createElement('div');
        div.className = type === 'user' ? 'chat-msg-user' : 'chat-msg-ai';

        if (isHtml) {
            div.innerHTML = text;
        } else {
            div.style.whiteSpace = 'pre-wrap';
            div.textContent = text;
        }

        container.appendChild(div);

        // Smooth scroll with delay for animation
        setTimeout(function() {
            container.scrollTo({ top: container.scrollHeight, behavior: 'smooth' });
        }, 50);
    },

    // ==================================================================
    // Typing Indicator v4
    // ==================================================================
    showTyping() {
        var container = document.getElementById('chat-messages');
        if (!container) return;
        var div = document.createElement('div');
        div.id = 'typing-indicator';
        div.className = 'chat-msg-ai typing-v4';
        div.innerHTML =
            '<div class="ai-avatar-sm"><i class="fas fa-leaf text-white text-[8px]"></i></div>' +
            '<div class="typing-dots"><span class="typing-dot"></span><span class="typing-dot"></span><span class="typing-dot"></span></div>' +
            '<span class="text-[10px] text-gray-400 ml-1">Analyse en cours...</span>';
        container.appendChild(div);
        container.scrollTo({ top: container.scrollHeight, behavior: 'smooth' });
    },

    hideTyping() {
        var el = document.getElementById('typing-indicator');
        if (el) el.remove();
    },

    // ==================================================================
    // Chart.js Renderers
    // ==================================================================
    _renderMiniDoughnut(canvasId, chartData) {
        var canvas = document.getElementById(canvasId);
        if (!canvas || typeof Chart === 'undefined') return;

        var ctx = canvas.getContext('2d');
        var chart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: chartData.labels,
                datasets: [{
                    data: chartData.superficie,
                    backgroundColor: chartData.colors,
                    borderWidth: 2,
                    borderColor: 'rgba(255,255,255,0.8)',
                    hoverBorderColor: '#fff',
                    hoverBorderWidth: 3,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                cutout: '62%',
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: 'rgba(20,83,45,0.92)',
                        titleFont: { family: 'DM Sans', size: 11 },
                        bodyFont: { family: 'DM Sans', size: 10 },
                        cornerRadius: 8,
                        padding: 8,
                        callbacks: {
                            label: function(ctx) {
                                var val = ctx.parsed;
                                var total = ctx.dataset.data.reduce(function(a, b) { return a + b; }, 0);
                                var pct = total > 0 ? (val / total * 100).toFixed(1) : 0;
                                return ctx.label + ': ' + val.toLocaleString('fr-FR') + ' ha (' + pct + '%)';
                            }
                        }
                    }
                },
                animation: {
                    animateRotate: true,
                    duration: 1200,
                    easing: 'easeOutQuart',
                },
            }
        });
        this._chartInstances.push(chart);
    },

    _renderComparisonChart(canvasId, chartData) {
        var canvas = document.getElementById(canvasId);
        if (!canvas || typeof Chart === 'undefined') return;

        var ctx = canvas.getContext('2d');
        var chart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: chartData.labels.map(function(l) { return l.length > 10 ? l.substring(0, 10) + '...' : l; }),
                datasets: [
                    {
                        label: String(chartData.annee1),
                        data: chartData.values1,
                        backgroundColor: chartData.colors.map(function(c) { return c + '99'; }),
                        borderColor: chartData.colors,
                        borderWidth: 1,
                        borderRadius: 4,
                    },
                    {
                        label: String(chartData.annee2),
                        data: chartData.values2,
                        backgroundColor: chartData.colors,
                        borderColor: chartData.colors,
                        borderWidth: 1,
                        borderRadius: 4,
                    },
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: 'y',
                plugins: {
                    legend: {
                        display: true,
                        position: 'top',
                        labels: { font: { family: 'DM Sans', size: 9 }, padding: 6, boxWidth: 10 }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(20,83,45,0.92)',
                        titleFont: { family: 'DM Sans', size: 10 },
                        bodyFont: { family: 'DM Sans', size: 9 },
                        cornerRadius: 8,
                    }
                },
                scales: {
                    x: { ticks: { font: { size: 8 } }, grid: { display: false } },
                    y: { ticks: { font: { size: 8, family: 'DM Sans' } }, grid: { display: false } }
                },
                animation: { duration: 1000, easing: 'easeOutQuart' },
            }
        });
        this._chartInstances.push(chart);
    },

    // ==================================================================
    // Animated Counters
    // ==================================================================
    _animateAllCounters() {
        var counters = document.querySelectorAll('.anim-counter[data-target]');
        var self = this;
        counters.forEach(function(el) {
            var target = parseInt(el.dataset.target) || 0;
            if (el._animated) return;
            el._animated = true;
            self._animateCounter(el, target, 1500, el.dataset.suffix || '', el.dataset.prefix || '');
        });
    },

    _animateCounter(el, target, duration, suffix, prefix) {
        var start = performance.now();
        function easeOutQuart(t) { return 1 - Math.pow(1 - t, 4); }
        function update(now) {
            var elapsed = now - start;
            var progress = Math.min(elapsed / duration, 1);
            var eased = easeOutQuart(progress);
            var current = Math.round(eased * target);
            el.textContent = (prefix || '') + current.toLocaleString('fr-FR') + (suffix || '');
            if (progress < 1) requestAnimationFrame(update);
        }
        requestAnimationFrame(update);
    },

    // ==================================================================
    // Animated Progress Bars
    // ==================================================================
    _animateProgressBars() {
        var bars = document.querySelectorAll('.progress-bar-fill[data-width]');
        bars.forEach(function(bar) {
            if (bar._animated) return;
            bar._animated = true;
            setTimeout(function() { bar.style.width = bar.dataset.width; }, 50);
        });
    },

    // ==================================================================
    // Fly-to Forest on Map
    // ==================================================================
    _flyToForest(forestCode) {
        if (!this.map || !forestCode) return;

        // Try to find forest bounds from Choropleth layer
        var self = this;
        var found = false;

        if (typeof Choropleth !== 'undefined' && Choropleth._foretsLayer) {
            Choropleth._foretsLayer.eachLayer(function(layer) {
                if (layer.feature && layer.feature.properties) {
                    var props = layer.feature.properties;
                    if (props.code === forestCode || props.foret_code === forestCode) {
                        self.map.flyToBounds(layer.getBounds(), {
                            duration: 1.5,
                            padding: [30, 30],
                            maxZoom: 12,
                        });
                        found = true;

                        // Pulse highlight
                        var center = layer.getBounds().getCenter();
                        self._addPulseMarker(center);
                    }
                }
            });
        }

        // Fallback to known centers
        if (!found) {
            var CENTERS = {
                'TENE': [6.525, -5.718], 'DOKA': [6.398, -5.603],
                'SANGOUE': [6.350, -5.480], 'LAHOUDA': [6.290, -5.390],
                'ZOUEKE_1': [6.440, -5.550], 'ZOUEKE_2': [6.410, -5.520],
            };
            var coords = CENTERS[forestCode];
            if (coords) {
                this.map.flyTo(coords, 11, { duration: 1.5 });
                this._addPulseMarker(L.latLng(coords[0], coords[1]));
            }
        }
    },

    _addPulseMarker(latlng) {
        if (!this.map || !latlng) return;
        var self = this;

        // Remove previous pulse
        if (this._pulseLayer) {
            this.map.removeLayer(this._pulseLayer);
        }

        var pulseIcon = L.divIcon({
            className: '',
            html: '<div style="width:40px;height:40px;background:rgba(34,197,94,0.3);border:2px solid #22c55e;border-radius:50%;" class="pulse-ring"></div>',
            iconSize: [40, 40],
            iconAnchor: [20, 20],
        });

        this._pulseLayer = L.marker(latlng, { icon: pulseIcon, interactive: false }).addTo(this.map);

        // Remove after 4 seconds
        setTimeout(function() {
            if (self._pulseLayer) {
                self.map.removeLayer(self._pulseLayer);
                self._pulseLayer = null;
            }
        }, 4000);
    },

    // ==================================================================
    // Toast Notifications
    // ==================================================================
    _showToast(message, type) {
        var panel = document.getElementById('chat-panel');
        if (!panel) return;

        // Remove existing toast
        var existing = panel.querySelector('.chat-toast');
        if (existing) existing.remove();

        var toast = document.createElement('div');
        toast.className = 'chat-toast toast-' + (type || 'info');
        toast.innerHTML = '<i class="fas ' + (type === 'success' ? 'fa-check-circle' : 'fa-info-circle') + '"></i><span>' + this._esc(message) + '</span>';
        panel.appendChild(toast);

        // Auto dismiss
        setTimeout(function() {
            toast.classList.add('chat-toast-exit');
            setTimeout(function() { toast.remove(); }, 300);
        }, 3000);
    },

    // ==================================================================
    // Context Badge
    // ==================================================================
    _updateContextBadge(parsed) {
        var badge = document.getElementById('chat-context-badge');
        if (!badge || !parsed) return;

        var parts = [];
        if (parsed.forests && parsed.forests.length) parts.push(parsed.forests[0]);
        if (parsed.years && parsed.years.length) parts.push(parsed.years[parsed.years.length - 1]);

        if (parts.length) {
            badge.textContent = parts.join(' • ');
            badge.classList.remove('hidden');
        } else {
            badge.classList.add('hidden');
        }
    },

    // ==================================================================
    // Tags
    // ==================================================================
    showTags(parsed) {
        var container = document.getElementById('ai-tags');
        if (!container || !parsed) return;

        container.innerHTML = '';
        var tags = [];
        var inherited = parsed._inherited || [];

        (parsed.forests || []).forEach(function(f) {
            var isInherited = inherited.indexOf('forests') !== -1;
            tags.push({ label: f, color: isInherited ? 'bg-green-50 text-green-600 border border-green-200' : 'bg-green-100 text-green-800', icon: 'fa-tree' });
        });
        (parsed.cover_types || []).forEach(function(c) {
            var isInherited = inherited.indexOf('cover_types') !== -1;
            tags.push({ label: c, color: isInherited ? 'bg-blue-50 text-blue-600 border border-blue-200' : 'bg-blue-100 text-blue-800', icon: 'fa-layer-group' });
        });
        (parsed.years || []).forEach(function(y) {
            var isInherited = inherited.indexOf('years') !== -1;
            tags.push({ label: y, color: isInherited ? 'bg-amber-50 text-amber-600 border border-amber-200' : 'bg-amber-100 text-amber-800', icon: 'fa-calendar' });
        });
        if (parsed.intent) {
            tags.push({ label: parsed.intent, color: 'bg-purple-100 text-purple-800', icon: 'fa-bolt' });
        }

        container.innerHTML = tags.map(function(t) {
            return '<span class="text-[10px] px-2 py-0.5 rounded-full ' + t.color + '"><i class="fas ' + t.icon + ' mr-0.5 text-[8px] opacity-60"></i>' + t.label + '</span>';
        }).join(' ');
    },

    // ==================================================================
    // Reactions
    // ==================================================================
    _bindReactions() {
        document.querySelectorAll('.reaction-btn:not([data-bound])').forEach(function(btn) {
            btn.setAttribute('data-bound', '1');
            btn.addEventListener('click', function(e) {
                e.stopPropagation();
                // Toggle reacted state
                var siblings = btn.parentElement.querySelectorAll('.reaction-btn');
                siblings.forEach(function(s) { s.classList.remove('reacted'); });
                btn.classList.add('reacted');
            });
        });
    },

    // ==================================================================
    // Utilities
    // ==================================================================
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

    _esc(str) {
        var div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    },

    _escAttr(str) {
        return String(str).replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/'/g, '&#39;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    },
};
