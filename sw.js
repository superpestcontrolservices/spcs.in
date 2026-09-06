const CACHE_NAME = "super-pest-static-v2";
const STATIC_ASSETS = [
    "/css/style.min.css",
    "/js/script.min.js",
    "/images/Fogging%20treatment.webp",
    "/images/Fogging%20treatment-800.webp",
    "/images/Fogging%20treatment-1600.webp",
    "/images/NIPHM%20Event-800.webp",
    "/images/NIPHM%20Event-1600.webp",
    "/images/ajmer-800.webp",
    "/images/ajmer-1400.webp",
    "/images/logo-42.webp",
    "/images/logo-84.webp",
    "/images/logo.webp"
];

self.addEventListener("install", function (event) {
    event.waitUntil(
        caches.open(CACHE_NAME).then(function (cache) {
            return cache.addAll(STATIC_ASSETS);
        })
    );

    self.skipWaiting();
});

self.addEventListener("activate", function (event) {
    event.waitUntil(
        caches.keys().then(function (cacheNames) {
            return Promise.all(
                cacheNames
                    .filter(function (cacheName) {
                        return cacheName !== CACHE_NAME;
                    })
                    .map(function (cacheName) {
                        return caches.delete(cacheName);
                    })
            );
        })
    );

    self.clients.claim();
});

self.addEventListener("fetch", function (event) {
    const requestUrl = new URL(event.request.url);
    const isStaticAsset =
        event.request.method === "GET" &&
        requestUrl.origin === self.location.origin &&
        (STATIC_ASSETS.includes(requestUrl.pathname) ||
            /\.(?:css|js|webp|png|jpg|jpeg|svg|woff2?)$/i.test(requestUrl.pathname));

    if (!isStaticAsset) return;

    event.respondWith(
        caches.match(event.request, { ignoreSearch: true }).then(function (cachedResponse) {
            if (cachedResponse) return cachedResponse;

            return fetch(event.request).then(function (networkResponse) {
                if (!networkResponse.ok) return networkResponse;

                const responseToCache = networkResponse.clone();

                caches.open(CACHE_NAME).then(function (cache) {
                    cache.put(event.request, responseToCache);
                });

                return networkResponse;
            });
        })
    );
});
