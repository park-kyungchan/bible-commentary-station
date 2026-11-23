const SHELL_CACHE = 'bible-station-shell-v4';
const CORPUS_CACHE = 'bible-station-corpus-v4';

const SHELL_ASSETS = [
  './',
  './index.html',
  './manifest.json',
  './css/tokens.css',
  './css/base.css',
  './css/layout.css',
  './css/components.css',
  './css/pulpit.css',
  './css/print.css',
  './css/motion.css',
  './icon.svg',
  './icons/icon-192.png',
  './icons/icon-512.png',
  './icons/apple-touch-icon.png',
  './js/main.js',
  './js/core/state.js',
  './js/core/dom.js',
  './js/core/urlSafety.js',
  './js/core/koreanQuery.js',
  './js/services/bibleService.js',
  './js/services/storage.js',
  './js/features/scriptureReader.js',
  './js/features/commentaryPanel.js',
  './js/features/crossRefPanel.js',
  './js/features/worshipPanel.js',
  './js/features/liturgyPanel.js',
  './js/features/sermonStudio.js',
  './js/features/pulpitPrompter.js',
  './js/features/biblePickerModal.js',
  './js/features/versionSettingsModal.js',
  './js/features/bookmarksSearchPanel.js',
];

const INITIAL_DATA_ASSETS = [
  './data/manifest.json',
  './data/exegesis.json',
  './data/worship.json',
];

const CORPUS_PATH_RE = /\/data\/(?!manifest\.json|exegesis\.json|worship\.json)[^/]+\//;
const METADATA_PATH_RE = /\/data\/(manifest|exegesis|worship)\.json$/;

function offlineJsonResponse(path) {
  return new Response(
    JSON.stringify({
      offline: true,
      error: 'OFFLINE_CACHE_MISS',
      path,
      message: '인터넷 연결이 없어 해당 자료를 불러오지 못했습니다.',
    }),
    {
      status: 503,
      statusText: 'Service Unavailable',
      headers: { 'Content-Type': 'application/json; charset=utf-8' },
    }
  );
}

self.addEventListener('install', (event) => {
  event.waitUntil(
    Promise.all([
      caches.open(SHELL_CACHE).then((cache) => cache.addAll(SHELL_ASSETS)),
      caches.open(CORPUS_CACHE).then((cache) =>
        Promise.allSettled(INITIAL_DATA_ASSETS.map((asset) => cache.add(asset)))
      ),
    ])
  );
});

self.addEventListener('activate', (event) => {
  const valid = new Set([SHELL_CACHE, CORPUS_CACHE]);
  event.waitUntil(
    caches
      .keys()
      .then((keys) => Promise.all(keys.filter((k) => !valid.has(k)).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});

self.addEventListener('fetch', (event) => {
  if (event.request.method !== 'GET') return;
  const url = new URL(event.request.url);
  if (url.origin !== self.location.origin) return;

  if (
    event.request.mode === 'navigate' ||
    url.pathname.endsWith('/') ||
    url.pathname.endsWith('/index.html')
  ) {
    event.respondWith(
      caches.open(SHELL_CACHE).then(async (cache) => {
        try {
          const resp = await fetch(event.request);
          if (resp && resp.ok && resp.type === 'basic') {
            cache.put('./index.html', resp.clone());
          }
          return resp;
        } catch {
          const cached =
            (await cache.match(event.request)) ||
            (await cache.match('./index.html')) ||
            (await cache.match('./'));
          return cached || new Response('오프라인 상태입니다.', { status: 503 });
        }
      })
    );
    return;
  }

  if (CORPUS_PATH_RE.test(url.pathname)) {
    event.respondWith(
      caches.open(CORPUS_CACHE).then(async (cache) => {
        const cached = await cache.match(event.request);
        if (cached) return cached;
        try {
          const resp = await fetch(event.request);
          if (resp && resp.ok) {
            cache.put(event.request, resp.clone());
          }
          return resp;
        } catch {
          return offlineJsonResponse(url.pathname);
        }
      })
    );
    return;
  }

  if (METADATA_PATH_RE.test(url.pathname)) {
    event.respondWith(
      caches.open(CORPUS_CACHE).then(async (cache) => {
        const cached = await cache.match(event.request);
        try {
          const resp = await fetch(event.request);
          if (resp && resp.ok) {
            cache.put(event.request, resp.clone());
            return resp;
          }
          return cached || resp;
        } catch {
          return cached || offlineJsonResponse(url.pathname);
        }
      })
    );
    return;
  }

  event.respondWith(
    caches.open(SHELL_CACHE).then(async (cache) => {
      const cached = await cache.match(event.request);
      if (cached) return cached;
      try {
        const resp = await fetch(event.request);
        if (resp && resp.ok && resp.type === 'basic') {
          cache.put(event.request, resp.clone());
        }
        return resp;
      } catch {
        return new Response('', { status: 503, statusText: 'Offline' });
      }
    })
  );
});
