const CACHE_NAME = 'bible-workstation-v7';
const CACHE_PREFIX = 'bible-workstation-';

function isKrvCorpusRequest(requestUrl) {
  if (requestUrl.origin !== self.location.origin) return false;

  try {
    let pathname = requestUrl.pathname;
    for (let attempt = 0; attempt < 16; attempt++) {
      const decodedPath = decodeURIComponent(pathname);
      if (decodedPath === pathname) break;
      pathname = decodedPath;
    }
    // Ambiguous nested encodings should bypass the cache as well.
    if (/%[0-9a-f]{2}/i.test(pathname)) return true;
    const normalizedPath = pathname.replace(/\\/g, '/').replace(/\/{2,}/g, '/').toLowerCase();
    return normalizedPath.includes('/bible_krv.json');
  } catch (error) {
    // Malformed paths should fail closed for caching.
    return true;
  }
}

function isKrvCorpusResponse(response) {
  return Boolean(response.url && isKrvCorpusRequest(new URL(response.url)));
}
const ASSETS_TO_CACHE = [
  './',
  './index.html',
  './bible_data.js',
  './bible_krv_verse_counts.json',
  './manifest.json',
  './icon.svg'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(ASSETS_TO_CACHE);
    }).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.filter((key) => key.startsWith(CACHE_PREFIX) && key !== CACHE_NAME).map((key) => caches.delete(key))
      );
    }).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  if (event.request.method !== 'GET') return;

  const requestUrl = new URL(event.request.url);
  if (isKrvCorpusRequest(requestUrl)) {
    event.respondWith(fetch(event.request, { cache: 'no-store' }));
    return;
  }

  event.respondWith(
    caches.open(CACHE_NAME).then((cache) => cache.match(event.request).then((cachedResponse) => {
      if (cachedResponse) {
        // Fetch in background to update this app's cache.
        fetch(event.request).then((networkResponse) => {
          if (networkResponse && networkResponse.status === 200 && !isKrvCorpusResponse(networkResponse)) {
            cache.put(event.request, networkResponse.clone());
          }
        }).catch(() => {});
        return cachedResponse;
      }
      return fetch(event.request).then((networkResponse) => {
        if (!networkResponse || networkResponse.status !== 200 || networkResponse.type !== 'basic') {
          return networkResponse;
        }
        if (isKrvCorpusResponse(networkResponse)) return networkResponse;
        cache.put(event.request, networkResponse.clone());
        return networkResponse;
      });
    }))
  );
});
