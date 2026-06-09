/**
 * NossoDireito — Branding + Analysis Cache Configuration Module
 * Dynamically loaded module for branding customization and analysis persistence
 */

(function() {
    'use strict';

    // ──────────────────────────────────────────────────────────────
    // SECTION 1: Branding Configuration (Dynamic)
    // ──────────────────────────────────────────────────────────────

    window.BRANDING_CONFIG = {
        data: null,
        ready: false,
        error: null
    };

    async function loadBrandingConfig() {
        try {
            const res = await fetch('config.json', { signal: AbortSignal.timeout(5000) });
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const config = await res.json();
            window.BRANDING_CONFIG.data = config;
            window.BRANDING_CONFIG.ready = true;
            applyBrandingToDOM(config);
            return config;
        } catch (err) {
            console.warn('Failed to load config.json (using defaults):', err.message);
            window.BRANDING_CONFIG.error = err;
            window.BRANDING_CONFIG.ready = true;
            return null;
        }
    }

    function applyBrandingToDOM(config) {
        if (!config) return;

        const { branding, design } = config;

        // Update document title
        const pageTitle = document.querySelector('title');
        if (pageTitle && config.seo?.siteTitle) {
            pageTitle.textContent = config.seo.siteTitle;
        }

        // Update OG meta tags
        const updateMetaTag = (property, value) => {
            let tag = document.querySelector(`meta[property="${property}"]`) ||
                      document.querySelector(`meta[name="${property}"]`);
            if (!tag) {
                tag = document.createElement('meta');
                tag.setAttribute('property', property);
                document.head.appendChild(tag);
            }
            tag.setAttribute('content', value);
        };

        if (config.seo?.siteTitle) {
            updateMetaTag('og:title', config.seo.siteTitle);
            updateMetaTag('twitter:title', config.seo.siteTitle);
        }
        if (config.seo?.siteDescription) {
            updateMetaTag('description', config.seo.siteDescription);
            updateMetaTag('og:description', config.seo.siteDescription);
            updateMetaTag('twitter:description', config.seo.siteDescription);
        }
        if (branding?.siteName) {
            updateMetaTag('og:site_name', branding.siteName);
        }
        if (design?.logo?.favicon) {
            const favicon = document.querySelector('link[rel="icon"]');
            if (favicon) favicon.href = design.logo.favicon;
        }

        // Store config in window for JS access
        window.BRANDING = branding;
        window.DESIGN = design;
        window.CONTACT = config.contact;
        window.LEGAL = config.legal;
    }

    // ──────────────────────────────────────────────────────────────
    // SECTION 2: Analysis Result Caching (IndexedDB)
    // ──────────────────────────────────────────────────────────────

    window.ANALYSIS_CACHE = {
        dbPromise: null,
        STORE_NAME: 'analysis_results',
        TTL_MINUTES: 30,

        async getDB() {
            if (this.dbPromise) return this.dbPromise;

            this.dbPromise = new Promise((resolve, reject) => {
                const req = indexedDB.open('NossoDireitoDB', 3);
                req.onerror = () => reject(req.error);
                req.onsuccess = () => resolve(req.result);
                req.onupgradeneeded = (e) => {
                    const db = e.target.result;
                    if (!db.objectStoreNames.contains(this.STORE_NAME)) {
                        db.createObjectStore(this.STORE_NAME, { keyPath: 'id' });
                    }
                };
            });

            return this.dbPromise;
        },

        async save(analysisData) {
            try {
                const db = await this.getDB();
                const tx = db.transaction(this.STORE_NAME, 'readwrite');
                const store = tx.objectStore(this.STORE_NAME);

                const record = {
                    id: 'latest',
                    timestamp: Date.now(),
                    ttl: this.TTL_MINUTES * 60 * 1000,
                    data: analysisData
                };

                store.put(record);
                return new Promise((resolve, reject) => {
                    tx.oncomplete = () => resolve(true);
                    tx.onerror = () => reject(tx.error);
                });
            } catch (err) {
                console.warn('Failed to cache analysis:', err);
                return false;
            }
        },

        async retrieve() {
            try {
                const db = await this.getDB();
                const tx = db.transaction(this.STORE_NAME, 'readonly');
                const store = tx.objectStore(this.STORE_NAME);

                return new Promise((resolve, reject) => {
                    const req = store.get('latest');
                    req.onsuccess = () => {
                        const record = req.result;
                        if (!record) {
                            resolve(null);
                            return;
                        }

                        // Check TTL
                        const age = Date.now() - record.timestamp;
                        if (age > record.ttl) {
                            // Expired, delete it
                            store.delete('latest');
                            resolve(null);
                            return;
                        }

                        resolve(record.data);
                    };
                    req.onerror = () => reject(req.error);
                });
            } catch (err) {
                console.warn('Failed to retrieve cached analysis:', err);
                return null;
            }
        },

        async clear() {
            try {
                const db = await this.getDB();
                const tx = db.transaction(this.STORE_NAME, 'readwrite');
                const store = tx.objectStore(this.STORE_NAME);
                store.delete('latest');
                return new Promise((resolve) => {
                    tx.oncomplete = () => resolve(true);
                });
            } catch (err) {
                console.warn('Failed to clear analysis cache:', err);
                return false;
            }
        }
    };

    // Initialize config loading as early as possible
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', loadBrandingConfig);
    } else {
        loadBrandingConfig();
    }

    // Expose to global scope
    window.loadBrandingConfig = loadBrandingConfig;
    window.applyBrandingToDOM = applyBrandingToDOM;

})();
