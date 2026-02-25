/**
 * Chat-to-Map IA Panel v2.0
 *
 * Requetes en langage naturel francais -> filtres Django ORM
 *
 * Nouveautes v2 :
 * - Rendu HTML riche (tables, couleurs, icones)
 * - Indicateur de frappe (typing dots)
 * - Reponse help avec exemples cliquables
 * - Analyse de deforestation en tableau
 * - Stats en tableau HTML avec pastilles de couleur
 * - Comparaison enrichie avec delta
 * - Classement des forets
 * - Suggestions intelligentes en cas de zero resultat
 * - Heritage de contexte (tags inherited)
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
                this.addMessage('Erreur de communication avec le serveur.', 'ai');
                return;
            }

            // Show parsed entity tags
            if (result.parsed) {
                this.showTags(result.parsed);
            }

            // Route by response type
            this._handleResponse(result);

            // Update results counter
            const countEl = document.getElementById('ai-results-count');
            if (countEl) {
                const n = result.count || result.nb_results || 0;
                countEl.textContent = `${n} resultat(s) — ${result.processing_ms || 0}ms`;
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

            case 'no_results':
                this._renderNoResults(result.suggestions);
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
                html += `<li class="text-xs text-gray-600">• ${c}</li>`;
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
        let html = '<div class="space-y-2">';
        html += '<p class="text-sm font-semibold">&#x1F4CA; Statistiques</p>';
        html += '<table class="w-full text-xs border-collapse">';
        html += '<tr class="border-b bg-gray-50"><th class="py-1.5 px-2 text-left">Type</th><th class="py-1.5 px-2 text-right">Superficie</th><th class="py-1.5 px-2 text-right">Carbone</th></tr>';

        data.forEach(s => {
            const color = s.nomenclature__couleur_hex || '#999';
            const label = s.nomenclature__libelle_fr || s.nomenclature__code || '?';
            const sup = (s.total_superficie_ha || 0).toLocaleString('fr-FR', { maximumFractionDigits: 0 });
            const carb = (s.total_carbone || 0).toLocaleString('fr-FR', { maximumFractionDigits: 0 });
            html += `<tr class="border-b hover:bg-gray-50">
                <td class="py-1 px-2"><span class="inline-block w-2.5 h-2.5 rounded-sm mr-1.5" style="background:${this._escAttr(color)}"></span>${this._esc(label)}</td>
                <td class="py-1 px-2 text-right font-medium">${sup} ha</td>
                <td class="py-1 px-2 text-right">${carb} tCO2</td>
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

    _renderNoResults(suggestions) {
        let html = '<div class="space-y-2">';
        html += '<p class="text-sm">Aucun resultat trouve.</p>';
        if (suggestions && suggestions.length) {
            html += '<p class="text-[10px] text-gray-500 font-bold uppercase tracking-wider">&#x1F4A1; Suggestions</p>';
            html += '<ul class="space-y-1">';
            suggestions.forEach(s => {
                // If suggestion looks like an example query, make it clickable
                if (s.length > 20 && !s.startsWith('Precisez')) {
                    html += `<li class="text-xs text-green-700 cursor-pointer hover:underline chat-example">"${this._esc(s)}"</li>`;
                } else {
                    html += `<li class="text-xs text-amber-700">• ${this._esc(s)}</li>`;
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
