const CACHE_NAME = 'skool-v4';

// Only precache essential assets — SVG images are cached on first use
// via the /static/ cache-first strategy (much faster install)
const PRECACHE_URLS = [
  '/static/css/common.css',
  '/static/manifest.json',
  '/static/icons/icon-192.png',
  '/static/icons/icon-512.png',
  '/offline'
];

// --- Install: precache key static assets + offline page ---
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => cache.addAll(PRECACHE_URLS))
      .then(() => self.skipWaiting())
  );
});

// --- Activate: clean up old caches, notify clients of update ---
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys
          .filter((key) => key !== CACHE_NAME)
          .map((key) => caches.delete(key))
      )
    ).then(() => {
      // Notify all clients that a new version is available
      self.clients.matchAll({ type: 'window' }).then((clients) => {
        clients.forEach((client) => {
          client.postMessage({ type: 'SW_UPDATED' });
        });
      });
      return self.clients.claim();
    })
  );
});

// --- Fetch: route by strategy ---
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // Only handle same-origin requests
  if (url.origin !== location.origin) return;

  // Network-first for HTML pages (navigate) — fallback to /offline
  if (event.request.mode === 'navigate') {
    event.respondWith(
      fetch(event.request)
        .then((response) => {
          // Cache successful HTML responses for offline use
          const clone = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
          return response;
        })
        .catch(() => {
          // Try cached version first, then offline page
          return caches.match(event.request).then((cached) => {
            return cached || caches.match('/offline');
          });
        })
    );
    return;
  }

  // Network-first for API calls — cache GET responses for offline
  if (url.pathname.startsWith('/game/') && event.request.method === 'GET') {
    event.respondWith(
      fetch(event.request)
        .then((response) => {
          const clone = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
          return response;
        })
        .catch(() => caches.match(event.request))
    );
    return;
  }

  // For API POST requests, just try network (sync queue handles failures)
  if (event.request.method === 'POST') {
    return; // Let it pass through to network normally
  }

  // Cache-first for static assets (CSS, JS, images, audio)
  if (url.pathname.startsWith('/static/')) {
    event.respondWith(
      caches.match(event.request).then((cached) => {
        if (cached) return cached;
        return fetch(event.request).then((response) => {
          const clone = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
          return response;
        });
      })
    );
    return;
  }
});

// --- Background Sync: replay queued requests ---
self.addEventListener('sync', (event) => {
  if (event.tag === 'sync-answers') {
    event.waitUntil(replayQueue());
  }
});

async function replayQueue() {
  // Open IndexedDB to read the sync queue
  const db = await openSyncDB();
  const tx = db.transaction('sync_queue', 'readonly');
  const store = tx.objectStore('sync_queue');
  const items = await idbGetAll(store);
  tx.oncomplete = null;

  for (const item of items) {
    try {
      const response = await fetch(item.url, {
        method: item.method,
        headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
        credentials: 'same-origin',
        body: item.body,
      });
      if (response.ok) {
        // Remove from queue on success
        const delTx = db.transaction('sync_queue', 'readwrite');
        delTx.objectStore('sync_queue').delete(item.id);
      }
    } catch (e) {
      // Still offline — will retry on next sync
      break;
    }
  }
  db.close();
}

function openSyncDB() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('skool_sync', 1);
    request.onupgradeneeded = () => {
      const db = request.result;
      if (!db.objectStoreNames.contains('sync_queue')) {
        db.createObjectStore('sync_queue', { keyPath: 'id', autoIncrement: true });
      }
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

function idbGetAll(store) {
  return new Promise((resolve, reject) => {
    const request = store.getAll();
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}
