/**
 * API Client for API.GEO.Carbone — Ultra-fast cache-first architecture
 *
 * Loading strategy:
 * 1. Backend checks for pre-built static GeoJSON files (< 50ms)
 * 2. Falls back to dynamic PostGIS query if no cache
 * 3. Frontend caches all API responses in memory (5min TTL)
 * 4. Background preloads all 3 years on startup → instant year switching
 *
 * Features:
 * - Memory cache with 5min TTL
 * - AbortController per endpoint key
 * - Performance logging
 */
const API = {
    BASE_URL: '/api/v1',
    _cache: new Map(),
    _controllers: new Map(),
    CACHE_TTL: 5 * 60 * 1000,

    _abort(key) {
        const c = this._controllers.get(key);
        if (c) { c.abort(); this._controllers.delete(key); }
    },

    async get(endpoint, params, options) {
        if (!options) options = {};
        if (typeof options === 'boolean') options = { useCache: options };
        const { useCache = true, abortKey = null } = options;

        const url = new URL(this.BASE_URL + endpoint, window.location.origin);
        if (params) {
            Object.entries(params).forEach(([k, v]) => {
                if (v !== null && v !== undefined && v !== '') {
                    url.searchParams.append(k, v);
                }
            });
        }

        const cacheKey = url.toString();
        if (useCache && this._cache.has(cacheKey)) {
            const cached = this._cache.get(cacheKey);
            if (Date.now() - cached.ts < this.CACHE_TTL) {
                console.log(`[API] cache hit: ${endpoint}`);
                return cached.data;
            }
            this._cache.delete(cacheKey);
        }

        if (abortKey) this._abort(abortKey);
        const controller = new AbortController();
        if (abortKey) this._controllers.set(abortKey, controller);

        const t0 = performance.now();

        try {
            const response = await fetch(url.toString(), { signal: controller.signal });
            if (abortKey) this._controllers.delete(abortKey);

            const dt = Math.round(performance.now() - t0);

            if (!response.ok) {
                console.error(`[API] ${response.status}: ${endpoint} (${dt}ms)`);
                return null;
            }

            const data = await response.json();
            const features = data?.features?.length;
            const cacheStatus = response.headers.get('X-GeoCache') || 'SQL';
            console.log(`[API] ${endpoint}${url.search} → ${features != null ? features + ' features' : 'ok'} (${dt}ms, ${cacheStatus})`);

            if (useCache) this._cache.set(cacheKey, { data, ts: Date.now() });
            return data;

        } catch (err) {
            if (err.name === 'AbortError') return null;
            console.error(`[API] ${endpoint}:`, err);
            return null;
        }
    },

    async post(endpoint, body) {
        try {
            const r = await fetch(this.BASE_URL + endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken(),
                },
                body: JSON.stringify(body),
            });
            return r.ok ? r.json() : null;
        } catch (err) {
            console.error(`[API] POST ${endpoint}:`, err);
            return null;
        }
    },

    getCSRFToken() {
        const c = document.cookie.split(';').find(c => c.trim().startsWith('csrftoken='));
        return c ? c.split('=')[1] : '';
    },

    clearCache() { this._cache.clear(); },

    clearCachePrefix(prefix) {
        const fullPrefix = new URL(this.BASE_URL + prefix, window.location.origin).toString();
        for (const key of this._cache.keys()) {
            if (key.startsWith(fullPrefix)) this._cache.delete(key);
        }
    },

    // ===== ENDPOINTS =====
    // Occupation: cache enabled (backend serves static files when available)
    // Simple params only (annee, foret_code) → cache hits on backend
    // Complex params (bbox, zoom, type) → SQL fallback

    getForets()                { return this.get('/forets/'); },
    getOccupations(params)     { return this.get('/occupations/', params, { useCache: true, abortKey: 'occ' }); },
    getOccupationStats(params) { return this.get('/occupations/stats/', params, { useCache: false }); },
    getEvolution(foret, a1, a2){ return this.get('/occupations/evolution/', { foret, annee1: a1, annee2: a2 }); },
    getPlacettes(params)       { return this.get('/placettes/', params); },
    getInfrastructures(params) { return this.get('/infrastructures/', params); },
    getZonesEtude(params)      { return this.get('/zones-etude/', params); },
    getNomenclatures()         { return this.get('/nomenclatures/'); },
    queryAI(query)             { return this.post('/ai/query/', { query }); },

    /**
     * Preload occupation data for all years into browser memory.
     * Since backend serves static cache files, this is very fast.
     * After preload, year switching is instant (memory cache hit).
     */
    async preloadAllYears(foretCode) {
        const years = [1986, 2003, 2023];
        const promises = years.map(annee => {
            const params = { annee };
            if (foretCode) params.foret_code = foretCode;
            return this.get('/occupations/', params, { useCache: true });
        });
        await Promise.all(promises);
        console.log('[API] ✓ Preloaded all years (instant switching ready)');
    },
};
