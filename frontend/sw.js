// Service worker: caches static assets for speed/offline shell only.
// Product data, prices, stock and auth all come from /api/* — those are
// NEVER cached here, since stale stock/pricing/order data would be a real
// correctness bug on a live wholesale storefront.
const CACHE_NAME = 'wolkago-static-v1';
const PRECACHE_URLS = [
  'css/style.css',
  'js/app.js',
  'config.js',
  'offline.html',
  'assets/favicon-32.png',
  'assets/wolkago-logo.png',
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => cache.addAll(PRECACHE_URLS))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  const req = event.request;
  const url = new URL(req.url);

  if (req.method !== 'GET' || url.origin !== self.location.origin) return;

  // Never cache API calls — always hit the network so prices/stock/orders are live.
  if (url.pathname.startsWith('/api/')) return;

  // Page navigations: network-first, falling back to the offline shell.
  if (req.mode === 'navigate') {
    event.respondWith(
      fetch(req).catch(() => caches.match('offline.html'))
    );
    return;
  }

  // Static assets (css/js/images/fonts): stale-while-revalidate.
  event.respondWith(
    caches.open(CACHE_NAME).then((cache) =>
      cache.match(req).then((cached) => {
        const fetchPromise = fetch(req).then((res) => {
          if (res.ok) cache.put(req, res.clone());
          return res;
        }).catch(() => cached);
        return cached || fetchPromise;
      })
    )
  );
});
