const CACHE_NAME = 'skool-v3';

// Static assets to precache on install
const PRECACHE_URLS = [
  '/static/css/common.css',
  '/static/manifest.json',
  '/static/icons/icon-192.png',
  '/static/icons/icon-512.png',
  '/offline',
  '/static/images/chars/shoe.svg',
  '/static/images/chars/soccer.svg',
  '/static/images/chars/drink.svg',
  '/static/images/chars/hand.svg',
  '/static/images/chars/dumplings.svg',
  '/static/images/chars/meat.svg',
  '/static/images/chars/driver.svg',
  '/static/images/chars/grandma.svg',
  '/static/images/chars/bee.svg',
  '/static/images/chars/friend.svg',
  '/static/images/chars/yes.svg',
  '/static/images/chars/singer.svg',
  '/static/images/chars/house.svg',
  '/static/images/chars/bed.svg',
  '/static/images/chars/big.svg',
  '/static/images/chars/dinosaur.svg',
  '/static/images/chars/wind.svg',
  '/static/images/chars/slow.svg',
  '/static/images/chars/grape.svg',
  '/static/images/chars/four.svg',
  '/static/images/chars/tomato.svg',
  '/static/images/chars/short.svg',
  '/static/images/chars/few.svg',
  '/static/images/chars/ant.svg',
  '/static/images/chars/black.svg',
  '/static/images/chars/can.svg',
  '/static/images/chars/sorry.svg',
  '/static/images/chars/butterfly.svg',
  '/static/images/chars/umbrella.svg',
  '/static/images/chars/snow_nature.svg',
  '/static/images/chars/athlete.svg',
  '/static/images/chars/restaurant.svg',
  '/static/images/chars/brother.svg',
  '/static/images/chars/six.svg',
  '/static/images/chars/stand.svg',
  '/static/images/chars/person.svg',
  '/static/images/chars/milk.svg',
  '/static/images/chars/two.svg',
  '/static/images/chars/doctor.svg',
  '/static/images/chars/cow.svg',
  '/static/images/chars/backpack.svg',
  '/static/images/chars/bird.svg',
  '/static/images/chars/many.svg',
  '/static/images/chars/shirt.svg',
  '/static/images/chars/sheep.svg',
  '/static/images/chars/down.svg',
  '/static/images/chars/pink.svg',
  '/static/images/chars/blue.svg',
  '/static/images/chars/shrimp.svg',
  '/static/images/chars/tiger.svg',
  '/static/images/chars/chicken.svg',
  '/static/images/chars/tofu.svg',
  '/static/images/chars/toy.svg',
  '/static/images/chars/bike.svg',
  '/static/images/chars/sister.svg',
  '/static/images/chars/toothbrush.svg',
  '/static/images/chars/chef.svg',
  '/static/images/chars/yellow.svg',
  '/static/images/chars/towel.svg',
  '/static/images/chars/mom.svg',
  '/static/images/chars/laugh.svg',
  '/static/images/chars/up.svg',
  '/static/images/chars/fire.svg',
  '/static/images/chars/sleep.svg',
  '/static/images/chars/dolphin.svg',
  '/static/images/chars/elephant.svg',
  '/static/images/chars/key.svg',
  '/static/images/chars/sad.svg',
  '/static/images/chars/cry.svg',
  '/static/images/chars/park.svg',
  '/static/images/chars/look.svg',
  '/static/images/chars/bread.svg',
  '/static/images/chars/three.svg',
  '/static/images/chars/candy.svg',
  '/static/images/chars/school.svg',
  '/static/images/chars/river.svg',
  '/static/images/chars/ball.svg',
  '/static/images/chars/tv.svg',
  '/static/images/chars/no.svg',
  '/static/images/chars/hat.svg',
  '/static/images/chars/mouth.svg',
  '/static/images/chars/book.svg',
  '/static/images/chars/jump.svg',
  '/static/images/chars/train.svg',
  '/static/images/chars/cake.svg',
  '/static/images/chars/teacher.svg',
  '/static/images/chars/baozi.svg',
  '/static/images/chars/bowl.svg',
  '/static/images/chars/turtle.svg',
  '/static/images/chars/paper.svg',
  '/static/images/chars/goodbye.svg',
  '/static/images/chars/ten.svg',
  '/static/images/chars/boat.svg',
  '/static/images/chars/pillow.svg',
  '/static/images/chars/good.svg',
  '/static/images/chars/rabbit.svg',
  '/static/images/chars/sing.svg',
  '/static/images/chars/whale.svg',
  '/static/images/chars/hospital.svg',
  '/static/images/chars/horse.svg',
  '/static/images/chars/dance.svg',
  '/static/images/chars/happy.svg',
  '/static/images/chars/blocks.svg',
  '/static/images/chars/parrot.svg',
  '/static/images/chars/dog.svg',
  '/static/images/chars/spoon.svg',
  '/static/images/chars/close.svg',
  '/static/images/chars/pants.svg',
  '/static/images/chars/soup.svg',
  '/static/images/chars/rainbow.svg',
  '/static/images/chars/fish.svg',
  '/static/images/chars/rain.svg',
  '/static/images/chars/red.svg',
  '/static/images/chars/grandpa.svg',
  '/static/images/chars/juice.svg',
  '/static/images/chars/bear.svg',
  '/static/images/chars/snake.svg',
  '/static/images/chars/small.svg',
  '/static/images/chars/chopsticks.svg',
  '/static/images/chars/lamp.svg',
  '/static/images/chars/right.svg',
  '/static/images/chars/police.svg',
  '/static/images/chars/nine.svg',
  '/static/images/chars/chocolate.svg',
  '/static/images/chars/tea.svg',
  '/static/images/chars/white.svg',
  '/static/images/chars/noodles.svg',
  '/static/images/chars/pig.svg',
  '/static/images/chars/table.svg',
  '/static/images/chars/traffic_light.svg',
  '/static/images/chars/fast.svg',
  '/static/images/chars/long.svg',
  '/static/images/chars/baby.svg',
  '/static/images/chars/vegetables.svg',
  '/static/images/chars/love.svg',
  '/static/images/chars/ocean.svg',
  '/static/images/chars/blackboard.svg',
  '/static/images/chars/egg.svg',
  '/static/images/chars/kick.svg',
  '/static/images/chars/bus.svg',
  '/static/images/chars/swim.svg',
  '/static/images/chars/write.svg',
  '/static/images/chars/strawberry.svg',
  '/static/images/chars/star.svg',
  '/static/images/chars/sun.svg',
  '/static/images/chars/seven.svg',
  '/static/images/chars/pizza.svg',
  '/static/images/chars/dad.svg',
  '/static/images/chars/banana.svg',
  '/static/images/chars/open.svg',
  '/static/images/chars/bug.svg',
  '/static/images/chars/fruit.svg',
  '/static/images/chars/farmer.svg',
  '/static/images/chars/monkey.svg',
  '/static/images/chars/computer.svg',
  '/static/images/chars/hot.svg',
  '/static/images/chars/pencil.svg',
  '/static/images/chars/foot.svg',
  '/static/images/chars/basketball.svg',
  '/static/images/chars/clock.svg',
  '/static/images/chars/phone.svg',
  '/static/images/chars/icecream.svg',
  '/static/images/chars/orange_color.svg',
  '/static/images/chars/think.svg',
  '/static/images/chars/eye.svg',
  '/static/images/chars/thankyou.svg',
  '/static/images/chars/flower.svg',
  '/static/images/chars/eat.svg',
  '/static/images/chars/car.svg',
  '/static/images/chars/firefighter.svg',
  '/static/images/chars/listen.svg',
  '/static/images/chars/one.svg',
  '/static/images/chars/subway.svg',
  '/static/images/chars/painter.svg',
  '/static/images/chars/read_action.svg',
  '/static/images/chars/tree.svg',
  '/static/images/chars/water.svg',
  '/static/images/chars/door.svg',
  '/static/images/chars/hello.svg',
  '/static/images/chars/supermarket.svg',
  '/static/images/chars/come.svg',
  '/static/images/chars/cola.svg',
  '/static/images/chars/frog.svg',
  '/static/images/chars/head.svg',
  '/static/images/chars/five.svg',
  '/static/images/chars/rice.svg',
  '/static/images/chars/mountain.svg',
  '/static/images/chars/sky.svg',
  '/static/images/chars/cloud.svg',
  '/static/images/chars/window.svg',
  '/static/images/chars/cup.svg',
  '/static/images/chars/chair.svg',
  '/static/images/chars/cooked_rice.svg',
  '/static/images/chars/want.svg',
  '/static/images/chars/walk.svg',
  '/static/images/chars/green.svg',
  '/static/images/chars/doll.svg',
  '/static/images/chars/beef_noodle.svg',
  '/static/images/chars/hotpot.svg',
  '/static/images/chars/cold.svg',
  '/static/images/chars/ear.svg',
  '/static/images/chars/cat.svg',
  '/static/images/chars/sit.svg',
  '/static/images/chars/eight.svg',
  '/static/images/chars/go.svg',
  '/static/images/chars/fridge.svg',
  '/static/images/chars/airplane.svg',
  '/static/images/chars/apple.svg',
  '/static/images/chars/mouse.svg',
  '/static/images/chars/scientist.svg',
  '/static/images/chars/grass.svg',
  '/static/images/chars/penguin.svg',
  '/static/images/chars/left.svg',
  '/static/images/chars/run.svg',
  '/static/images/chars/moon.svg',
  '/static/images/chars/fries.svg',
  '/static/images/chars/watermelon.svg',
  '/static/images/chars/heart.svg',
  '/static/images/chars/itsokay.svg'
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
