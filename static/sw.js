// Service Worker básico - ERP Gastronómico (Templo del Smash)
// Estrategia: cache-first para static, network-first para rutas dinámicas

const CACHE_NAME = 'erp-smash-v2.1.0';
const STATIC_ASSETS = [
  '/',
  '/static/manifest.json',
  '/login',
  'https://cdn.tailwindcss.com',
  'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap'
];

// Instalación: precachea assets estáticos básicos
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(STATIC_ASSETS).catch((err) => {
        console.warn('[SW] No se pudo cachear todo (offline-first tolerante):', err);
      });
    })
  );
  self.skipWaiting();
});

// Activación: limpia caches viejos
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k))
      );
    })
  );
  self.clients.claim();
});

// Fetch: estrategia híbrida
self.addEventListener('fetch', (event) => {
  const req = event.request;
  // Solo GET
  if (req.method !== 'GET') return;

  const url = new URL(req.url);

  // Network-first para rutas dinámicas (dashboard, forms, API)
  if (url.pathname.startsWith('/api/') || url.pathname === '/' || url.pathname === '/login') {
    event.respondWith(
      fetch(req).then((res) => {
        const copy = res.clone();
        caches.open(CACHE_NAME).then((cache) => cache.put(req, copy)).catch(() => {});
        return res;
      }).catch(() => caches.match(req))
    );
    return;
  }

  // Cache-first para static (JS, CSS, imágenes, fuentes)
  event.respondWith(
    caches.match(req).then((cached) => {
      return cached || fetch(req).then((res) => {
        const copy = res.clone();
        caches.open(CACHE_NAME).then((cache) => cache.put(req, copy)).catch(() => {});
        return res;
      }).catch(() => cached);
    })
  );
});