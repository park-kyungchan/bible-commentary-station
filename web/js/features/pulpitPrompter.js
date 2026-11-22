import { el } from '../core/dom.js';

function formatTimer(secondsRemaining) {
  const overtime = secondsRemaining < 0;
  const abs = Math.abs(Math.floor(secondsRemaining));
  const mm = String(Math.floor(abs / 60)).padStart(2, '0');
  const ss = String(abs % 60).padStart(2, '0');
  return `${overtime ? '+' : ''}${mm}:${ss}`;
}

export function createPulpitPrompter({ store }) {
  const { state } = store;
  let isOpen = false;
  let slides = [];
  let currentIndex = 0;
  let totalSeconds = 1800;
  let remainingSeconds = 1800;
  let timerRunning = false;
  let timerInterval = null;
  let wakeLock = null;
  let triggerFocusEl = null;

  function applyFontSize() {
    const overlay = document.getElementById('pulpitOverlay');
    if (!overlay) return;
    overlay.style.setProperty('--pulpit-font-pt', `${state.pulpitFontPt}pt`);
  }

  function applyProgress() {
    const overlay = document.getElementById('pulpitOverlay');
    const label = document.getElementById('pulpitProgress');
    const ratio = slides.length > 0 ? (currentIndex + 1) / slides.length : 0;
    if (overlay) {
      overlay.style.setProperty('--pulpit-progress', String(ratio));
    }
    if (label) {
      label.textContent = `${slides.length ? currentIndex + 1 : 0} / ${slides.length}`;
    }
  }

  function renderTimer() {
    const timerEl = document.getElementById('pulpitTimer');
    const toggleBtn = document.getElementById('btnPulpitTimerToggle');
    if (timerEl) {
      timerEl.textContent = formatTimer(remainingSeconds);
      timerEl.dataset.warning = remainingSeconds <= 300 && remainingSeconds >= 0 ? 'true' : 'false';
      timerEl.dataset.overtime = remainingSeconds < 0 ? 'true' : 'false';
    }
    if (toggleBtn) {
      toggleBtn.textContent = timerRunning ? '일시 정지' : '시간 시작';
    }
  }

  function stopTimer() {
    if (timerInterval) {
      clearInterval(timerInterval);
      timerInterval = null;
    }
    timerRunning = false;
    renderTimer();
  }

  function startTimer() {
    if (timerInterval) clearInterval(timerInterval);
    timerRunning = true;
    renderTimer();
    timerInterval = setInterval(() => {
      remainingSeconds -= 1;
      renderTimer();
    }, 1000);
  }

  async function requestWakeLock() {
    try {
      if (navigator.wakeLock && typeof navigator.wakeLock.request === 'function') {
        wakeLock = await navigator.wakeLock.request('screen');
      }
    } catch {
      wakeLock = null;
    }
  }

  async function releaseWakeLock() {
    if (!wakeLock) return;
    try {
      await wakeLock.release();
    } catch {
      // Ignore already released lock
    }
    wakeLock = null;
  }

  function renderSlide(direction = 'next') {
    const stage = document.getElementById('pulpitStage');
    const titleEl = document.getElementById('pulpitTitle');
    const bodyEl = document.getElementById('pulpitBody');
    const nextHintEl = document.getElementById('pulpitNextHint');
    const prevBtn = document.getElementById('btnPulpitPrev');
    const nextBtn = document.getElementById('btnPulpitNext');

    const slide = slides[currentIndex] || { heading: '', body: '' };
    const nextSlide = slides[currentIndex + 1];

    if (stage) {
      stage.dataset.slideDir = direction;
      stage.scrollTop = 0;
    }
    if (titleEl) titleEl.textContent = slide.heading || '';
    if (bodyEl) {
      const paras = String(slide.body || '')
        .split('\n')
        .map((line) => line.trim())
        .filter(Boolean);
      bodyEl.replaceChildren(...paras.map((p) => el('p', {}, p)));
    }
    if (nextHintEl) {
      nextHintEl.textContent = nextSlide ? `다음 화면: ${nextSlide.heading}` : '마지막 화면입니다';
    }
    if (prevBtn) prevBtn.disabled = currentIndex <= 0;
    if (nextBtn) nextBtn.disabled = currentIndex >= slides.length - 1;
    applyProgress();
  }

  function step(delta) {
    const nextIdx = currentIndex + delta;
    if (nextIdx < 0 || nextIdx >= slides.length) return;
    currentIndex = nextIdx;
    renderSlide(delta >= 0 ? 'next' : 'prev');
  }

  function adjustFont(deltaPt) {
    state.pulpitFontPt = Math.max(24, Math.min(60, state.pulpitFontPt + deltaPt));
    store.savePrefs();
    applyFontSize();
  }

  function open(deck, triggerEl = null) {
    const overlay = document.getElementById('pulpitOverlay');
    if (!overlay) return;
    slides = Array.isArray(deck?.slides) && deck.slides.length
      ? deck.slides
      : [{ heading: deck?.title || '강단 화면', body: '' }];
    currentIndex = 0;
    totalSeconds = Math.max(60, Math.round((Number(deck?.targetDurationMins) || 30) * 60));
    remainingSeconds = totalSeconds;
    isOpen = true;
    triggerFocusEl = triggerEl || document.activeElement;

    applyFontSize();
    renderSlide('next');
    startTimer();
    requestWakeLock();

    overlay.dataset.open = 'true';
    overlay.setAttribute('aria-hidden', 'false');
    document.getElementById('btnPulpitNext')?.focus();
  }

  function close() {
    if (!isOpen) return;
    isOpen = false;
    stopTimer();
    releaseWakeLock();
    if (document.fullscreenElement && typeof document.exitFullscreen === 'function') {
      document.exitFullscreen().catch(() => {});
    }
    const overlay = document.getElementById('pulpitOverlay');
    if (overlay) {
      overlay.dataset.open = 'false';
      overlay.setAttribute('aria-hidden', 'true');
    }
    if (triggerFocusEl && typeof triggerFocusEl.focus === 'function') {
      triggerFocusEl.focus();
    }
    triggerFocusEl = null;
  }

  function toggleFullscreen() {
    const overlay = document.getElementById('pulpitOverlay');
    if (!overlay) return;
    if (document.fullscreenElement) {
      document.exitFullscreen?.().catch(() => {});
    } else if (typeof overlay.requestFullscreen === 'function') {
      overlay.requestFullscreen().catch(() => {});
    }
  }

  function bindEvents() {
    document.getElementById('btnPulpitPrev')?.addEventListener('click', () => step(-1));
    document.getElementById('btnPulpitNext')?.addEventListener('click', () => step(1));
    document.getElementById('btnPulpitExit')?.addEventListener('click', close);
    document.getElementById('btnPulpitSmaller')?.addEventListener('click', () => adjustFont(-3));
    document.getElementById('btnPulpitBigger')?.addEventListener('click', () => adjustFont(3));
    document.getElementById('btnPulpitFullscreen')?.addEventListener('click', toggleFullscreen);
    document.getElementById('btnPulpitTimerToggle')?.addEventListener('click', () => {
      if (timerRunning) stopTimer();
      else startTimer();
    });
    document.getElementById('btnPulpitTimerReset')?.addEventListener('click', () => {
      remainingSeconds = totalSeconds;
      renderTimer();
    });

    document.addEventListener('keydown', (e) => {
      if (!isOpen) return;
      if (e.key === 'Escape') {
        e.preventDefault();
        close();
      } else if (e.key === 'ArrowRight' || e.key === 'PageDown') {
        e.preventDefault();
        step(1);
      } else if (e.key === ' ' && e.target?.tagName !== 'BUTTON') {
        e.preventDefault();
        step(1);
      } else if (e.key === 'ArrowLeft' || e.key === 'PageUp') {
        e.preventDefault();
        step(-1);
      } else if (e.key === '+' || e.key === '=') {
        e.preventDefault();
        adjustFont(3);
      } else if (e.key === '-' || e.key === '_') {
        e.preventDefault();
        adjustFont(-3);
      }
    });

    document.addEventListener('visibilitychange', () => {
      if (isOpen && document.visibilityState === 'visible') {
        requestWakeLock();
      }
    });
  }

  return { bindEvents, open, close, step, isOpen: () => isOpen };
}
