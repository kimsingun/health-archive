/* PWA: 서비스 워커 등록 + 앱 설치 안내 버튼 */
(function () {
  'use strict';

  if ('serviceWorker' in navigator) {
    window.addEventListener('load', function () {
      navigator.serviceWorker.register('/sw.js').catch(function (err) {
        console.warn('Service worker 등록 실패:', err);
      });
    });
  }

  // 이미 설치된(standalone) 상태면 설치 버튼을 띄우지 않는다
  var isStandalone = window.matchMedia('(display-mode: standalone)').matches ||
    window.navigator.standalone === true;
  if (isStandalone) return;

  var deferredPrompt = null;
  var installBtn = null;

  function createInstallButton() {
    if (installBtn) return installBtn;
    var btn = document.createElement('button');
    btn.type = 'button';
    btn.textContent = '📱 앱으로 설치';
    btn.setAttribute('aria-label', 'HealthArchive 앱으로 설치');
    btn.style.cssText = [
      'position:fixed', 'right:16px', 'bottom:16px', 'z-index:9999',
      'padding:10px 16px', 'border:none', 'border-radius:24px',
      'background:#2f6d57', 'color:#fff', 'font-size:14px', 'font-weight:600',
      'font-family:inherit', 'cursor:pointer',
      'box-shadow:0 4px 14px rgba(39,50,46,.28)'
    ].join(';');
    document.body.appendChild(btn);
    installBtn = btn;
    return btn;
  }

  window.addEventListener('beforeinstallprompt', function (e) {
    e.preventDefault();
    deferredPrompt = e;
    var btn = createInstallButton();
    btn.onclick = function () {
      btn.remove();
      installBtn = null;
      if (!deferredPrompt) return;
      deferredPrompt.prompt();
      deferredPrompt.userChoice.finally(function () {
        deferredPrompt = null;
      });
    };
  });

  window.addEventListener('appinstalled', function () {
    if (installBtn) {
      installBtn.remove();
      installBtn = null;
    }
    deferredPrompt = null;
  });
})();
