/* HealthArchive Service Worker
 * 전략: 같은 출처(same-origin) GET 요청은 네트워크 우선(network-first).
 * 성공한 응답은 캐시에 저장해 두고, 오프라인일 때 캐시로 대체한다.
 * 데이터 파일(data/*.js)이 자주 갱신되므로 캐시 우선 전략은 쓰지 않는다.
 */
const CACHE_NAME = 'healtharchive-v1';

const PRECACHE_URLS = [
  '/',
  '/index.html',
  '/manifest.webmanifest',
  '/assets/logo-icon.png',
  '/assets/logo-wordmark.png',
  '/assets/leaf-badge.png',
  '/assets/icon-192.png',
  '/assets/icon-512.png'
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
    caches.keys()
      .then((keys) => Promise.all(
        keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))
      ))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  const request = event.request;
  if (request.method !== 'GET') return;

  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return; // CDN·API 요청은 그대로 통과

  event.respondWith(
    fetch(request)
      .then((response) => {
        if (response && response.ok) {
          const copy = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(request, copy));
        }
        return response;
      })
      .catch(() =>
        caches.match(request).then((cached) => {
          if (cached) return cached;
          // SPA 내비게이션은 오프라인 시 캐시된 index.html로 대체
          if (request.mode === 'navigate') return caches.match('/index.html');
          return Response.error();
        })
      )
  );
});
