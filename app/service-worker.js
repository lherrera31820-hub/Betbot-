// Bump CACHE whenever app shell files change, otherwise returning users keep
// getting the previously cached index.html and never see new UI.
const CACHE = 'betbot-v3';
const SHELL = ['./index.html', './manifest.webmanifest', './icon-192.png', './icon-512.png'];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(cache => cache.addAll(SHELL)));
  self.skipWaiting();
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

async function networkFirst(request, fallbackUrl) {
  try {
    const res = await fetch(request);
    if (res && res.ok) (await caches.open(CACHE)).put(request, res.clone());
    return res;
  } catch (err) {
    const cached = await caches.match(request);
    if (cached) return cached;
    if (fallbackUrl) {
      const fallback = await caches.match(fallbackUrl);
      if (fallback) return fallback;
    }
    throw err;
  }
}

self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET') return;
  const url = e.request.url;
  // Picks data and the HTML shell go network-first so fresh picks and new UI
  // ship without waiting for a cache version bump.
  if (url.includes('picks.json')) {
    e.respondWith(networkFirst(e.request));
    return;
  }
  if (e.request.mode === 'navigate' || url.endsWith('/') || url.endsWith('.html')) {
    e.respondWith(networkFirst(e.request, './index.html'));
    return;
  }
  e.respondWith(caches.match(e.request).then(r => r || fetch(e.request).catch(() => caches.match('./index.html'))));
});
