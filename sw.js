const SHELL_CACHE = 'bible-station-shell-v3';
const CORPUS_CACHE = 'bible-station-corpus-v3';

const SHELL_ASSETS = [
  './',
  './index.html',
  './manifest.json',
  './icon.svg',
  './css/workstation.css',
  './js/storage.js',
  './js/bibleService.js',
  './js/app.js',
  './data/manifest.json',
  './data/exegesis.json',
  './data/worship.json',
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(SHELL_CACHE).then((cache) => cache.addAll(SHELL_ASSETS)).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  const valid = new Set([SHELL_CACHE, CORPUS_CACHE]);
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => !valid.has(k)).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  if (event.request.method !== 'GET') return;
  const url = new URL(event.request.url);
  if (url.origin !== self.location.origin) return;

  if (url.pathname.includes('/data/krv/')) {
    event.respondWith(
      caches.open(CORPUS_CACHE).then(async (cache) => {
        const cached = await cache.match(event.request);
        if (cached) return cached;
        const resp = await fetch(event.request);
        if (resp && resp.ok) cache.put(event.request, resp.clone());
        return resp;
      })
    );
    return;
  }

  event.respondWith(
    caches.open(SHELL_CACHE).then(async (cache) => {
      const cached = await cache.match(event.request);
      const networkPromise = fetch(event.request)
        .then((resp) => {
          if (resp && resp.ok && resp.type === 'basic') cache.put(event.request, resp.clone());
          return resp;
        })
        .catch(() => cached);
      return cached || networkPromise;
    })
  );
});
