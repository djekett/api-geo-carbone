/**
 * Chat-to-Map IA Panel
 * Requetes en langage naturel francais -> filtres Django ORM
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

        // Exemples cliquables
        document.querySelectorAll('.chat-example').forEach(el => {
            el.addEventListener('click', () => {
                if (input) {
                    input.value = el.textContent.replace(/"/g, '');
                    this.sendQuery();
                }
            });
        });

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

    async sendQuery() {
        const input = document.getElementById('chat-input');
        const query = (input ? input.value : '').trim();
        if (!query) return;

        this.addMessage(query, 'user');
        if (input) input.value = '';

        const loading = document.getElementById('ai-loading');
        if (loading) loading.classList.remove('hidden');

        try {
            const result = await API.queryAI(query);

            if (!result) {
                this.addMessage('Erreur de communication avec le serveur.', 'ai');
                return;
            }

            // Afficher les entites extraites sous forme de tags
            if (result.parsed) {
                this.showTags(result.parsed);
            }

            if (result.type === 'geojson' && result.data) {
                Choropleth.renderAIResults(result.data, this.map);
                const count = result.count || (result.data.features ? result.data.features.length : 0);
                const ms = result.processing_ms || 0;
                this.addMessage(`${count} polygone(s) trouve(s) (${ms}ms)`, 'ai');

            } else if (result.type === 'stats' && result.data) {
                let msg = 'Statistiques :\n';
                (Array.isArray(result.data) ? result.data : []).forEach(s => {
                    const label = s.nomenclature__libelle_fr || s.nomenclature__code || '?';
                    const sup = (s.total_superficie_ha || 0).toLocaleString('fr-FR', { maximumFractionDigits: 0 });
                    msg += `  - ${label} : ${sup} ha\n`;
                });
                this.addMessage(msg, 'ai');

            } else if (result.type === 'comparison' && result.data) {
                const d = result.data;
                let msg = 'Comparaison temporelle :\n';
                if (d.annee1) msg += `  ${d.annee1.annee} : ${(d.annee1.data || []).length} types de couvert\n`;
                if (d.annee2) msg += `  ${d.annee2.annee} : ${(d.annee2.data || []).length} types de couvert`;
                this.addMessage(msg, 'ai');

            } else {
                this.addMessage('Aucun resultat trouve. Essayez une autre formulation.', 'ai');
            }

            // Compteur de resultats
            const countEl = document.getElementById('ai-results-count');
            if (countEl) {
                countEl.textContent = `${result.count || 0} resultat(s) - ${result.processing_ms || 0}ms`;
                countEl.classList.remove('hidden');
            }

        } catch (err) {
            this.addMessage('Erreur lors du traitement de la requete.', 'ai');
            console.error('AI query error:', err);
        }

        if (loading) loading.classList.add('hidden');
    },

    addMessage(text, type) {
        const container = document.getElementById('chat-messages');
        if (!container) return;

        const div = document.createElement('div');
        div.className = type === 'user' ? 'chat-msg-user' : 'chat-msg-ai';
        div.style.whiteSpace = 'pre-wrap';
        div.textContent = text;
        container.appendChild(div);
        container.scrollTop = container.scrollHeight;
    },

    showTags(parsed) {
        const container = document.getElementById('ai-tags');
        if (!container || !parsed) return;

        container.innerHTML = '';
        const tags = [];

        (parsed.forests || []).forEach(f => tags.push({ label: f, color: 'bg-green-100 text-green-800' }));
        (parsed.cover_types || []).forEach(c => tags.push({ label: c, color: 'bg-blue-100 text-blue-800' }));
        (parsed.years || []).forEach(y => tags.push({ label: y, color: 'bg-amber-100 text-amber-800' }));
        if (parsed.intent) tags.push({ label: parsed.intent, color: 'bg-purple-100 text-purple-800' });

        container.innerHTML = tags.map(t =>
            `<span class="text-xs px-2 py-0.5 rounded-full ${t.color}">${t.label}</span>`
        ).join(' ');
    },
};
