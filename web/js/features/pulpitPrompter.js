/**
 * Next-Gen Pulpit Teleprompter & Dual-Screen Broadcast v4.0
 * Features: Zero-glare OLED stage, Teleprompter smooth auto-scroll,
 * Pacing Gauge (elapsed time vs slide progress), Blackout (B) mode,
 * and BroadcastChannel dual-screen sync (?view=stage).
 */

import { el, showToast } from '../core/dom.js';

function formatTimer(secondsRemaining) {
  const overtime = secondsRemaining < 0;
  const abs = Math.abs(Math.floor(secondsRemaining));
  const mm = String(Math.floor(abs / 60)).padStart(2, '0');
  const ss = String(abs % 60).padStart(2, '0');
  return `${overtime ? '+' : ''}${mm}:${ss}`;
}

export function createPulpitPrompter({ store, broadcast = null }) {
  const { state } = store;
  let isOpen = false;
  let slides = [];
  let currentIndex = 0;
  let totalSeconds = 1800;
  let remainingSeconds = 1800;
  let timerRunning = false;
  let timerInterval = null;
  let autoScrolling = false;
  let scrollRaf = null;
  let lastScrollTs = 0;
  let blackout = false;
  let wakeLock = null;
  let triggerFocusEl = null;

  function broadcastState() {
    if (!broadcast) return;
    const slide = slides[currentIndex] || { heading: '', body: '' };
    broadcast.send('pulpit:sync', {
      open: isOpen,
      blackout,
      index: currentIndex,
      total: slides.length,
      heading: slide.heading || '',
      body: slide.body || '',
      fontPt: state.pulpitFontPt,
      remainingSeconds,
    });
  }

  function applyFontSize() {
    const overlay = document.getElementById('pulpitOverlay');
    if (!overlay) return;
    overlay.style.setProperty('--pulpit-font-pt', `${state.pulpitFontPt}pt`);
  }

  function applyProgress() {
    const overlay = document.getElementById('pulpitOverlay');
    const label = document.getElementById('pulpitProgress');
    const paceEl = document.getElementById('pulpitPaceBadge');
    const slideRatio = slides.length > 0 ? (currentIndex + 1) / slides.length : 0;
    const elapsedRatio = totalSeconds > 0 ? Math.max(0, Math.min(1.5, (totalSeconds - remainingSeconds) / totalSeconds)) : 0;

    if (overlay) overlay.style.setProperty('--pulpit-progress', String(slideRatio));
    if (label) label.textContent = `${slides.length ? currentIndex + 1 : 0} / ${slides.length}`;
    if (paceEl) {
      const diff = slideRatio - elapsedRatio;
      if (remainingSeconds < 0) {
        paceEl.textContent = '마무리 권장';
        paceEl.dataset.pace = 'over';
      } else if (diff < -0.18) {
        paceEl.textContent = '속도 조절';
        paceEl.dataset.pace = 'behind';
      } else if (diff > 0.22) {
        paceEl.textContent = '여유 있음';
        paceEl.dataset.pace = 'ahead';
      } else {
        paceEl.textContent = '순조로움';
        paceEl.dataset.pace = 'steady';
      }
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
    if (toggleBtn) toggleBtn.textContent = timerRunning ? '일시 정지' : '시간 시작';
    applyProgress();
  }

  function stopAutoScroll() {
    autoScrolling = false;
    if (scrollRaf) {
      cancelAnimationFrame(scrollRaf);
      scrollRaf = null;
    }
    const scrollBtn = document.getElementById('btnPulpitAutoScroll');
    if (scrollBtn) scrollBtn.textContent = '자동 스크롤';
  }

  function toggleAutoScroll() {
    if (autoScrolling) {
      stopAutoScroll();
      return;
    }
    const stage = document.getElementById('pulpitStage');
    if (!stage) return;
    autoScrolling = true;
    lastScrollTs = performance.now();
    const scrollBtn = document.getElementById('btnPulpitAutoScroll');
    if (scrollBtn) scrollBtn.textContent = '스크롤 정지';

    const tick = (now) => {
      if (!autoScrolling || !isOpen) return;
      const dt = Math.min(100, now - lastScrollTs) / 1000;
      lastScrollTs = now;
      const pxPerSec = Math.max(18, Math.round((state.pulpitAutoScrollWpm || 240) * 0.16));
      stage.scrollTop += pxPerSec * dt;
      if (stage.scrollTop + stage.clientHeight >= stage.scrollHeight - 2) {
        stopAutoScroll();
        return;
      }
      scrollRaf = requestAnimationFrame(tick);
    };
    scrollRaf = requestAnimationFrame(tick);
  }

  function toggleBlackout() {
    blackout = !blackout;
    const overlay = document.getElementById('pulpitOverlay');
    if (overlay) overlay.dataset.blackout = blackout ? 'true' : 'false';
    const btnB = document.getElementById('btnPulpitBlackout');
    if (btnB) btnB.textContent = blackout ? '화면 복귀 (B)' : '암전 (B)';
    broadcastState();
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
    } catch { wakeLock = null; }
  }

  async function releaseWakeLock() {
    if (!wakeLock) return;
    try { await wakeLock.release(); } catch { /* ignore */ }
    wakeLock = null;
  }

  function renderSlide(direction = 'next') {
    stopAutoScroll();
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
      const paras = String(slide.body || '').split('\n').map((line) => line.trim()).filter(Boolean);
      bodyEl.replaceChildren(...paras.map((p) => el('p', {}, p)));
    }
    if (nextHintEl) {
      nextHintEl.textContent = nextSlide ? `다음 화면: ${nextSlide.heading}` : '마지막 화면입니다';
    }
    if (prevBtn) prevBtn.disabled = currentIndex <= 0;
    if (nextBtn) nextBtn.disabled = currentIndex >= slides.length - 1;
    applyProgress();
    broadcastState();
  }

  function step(delta) {
    const nextIdx = currentIndex + delta;
    if (nextIdx < 0 || nextIdx >= slides.length) return;
    currentIndex = nextIdx;
    renderSlide(delta >= 0 ? 'next' : 'prev');
  }

  function adjustFont(deltaPt) {
    state.pulpitFontPt = Math.max(24, Math.min(64, state.pulpitFontPt + deltaPt));
    store.savePrefs();
    applyFontSize();
    broadcastState();
  }

  function open(deck, triggerEl = null) {
    const overlay = document.getElementById('pulpitOverlay');
    if (!overlay) return;
    slides = Array.isArray(deck?.slides) && deck.slides.length
      ? deck.slides
      : [{ heading: deck?.title || '강단 화면', body: '' }];
    currentIndex = 0;
    blackout = false;
    overlay.dataset.blackout = 'false';
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
    const overlay = document.getElementById('pulpitOverlay');
    isOpen = false;
    blackout = false;
    stopAutoScroll();
    stopTimer();
    releaseWakeLock();
    if (document.fullscreenElement && typeof document.exitFullscreen === 'function') {
      document.exitFullscreen().catch(() => {});
    }
    if (overlay) {
      overlay.dataset.open = 'false';
      overlay.dataset.blackout = 'false';
      overlay.setAttribute('aria-hidden', 'true');
    }
    broadcastState();
    if (triggerFocusEl && typeof triggerFocusEl.focus === 'function') triggerFocusEl.focus();
  }

  function toggleFullscreen() {
    const overlay = document.getElementById('pulpitOverlay');
    if (!overlay) return;
    if (document.fullscreenElement) {
      document.exitFullscreen?.().catch(() => {});
    } else if (overlay.requestFullscreen) {
      overlay.requestFullscreen().catch(() => {});
    }
  }

  function bindEvents() {
    document.getElementById('btnPulpitExit')?.addEventListener('click', close);
    document.getElementById('btnPulpitPrev')?.addEventListener('click', () => step(-1));
    document.getElementById('btnPulpitNext')?.addEventListener('click', () => step(1));
    document.getElementById('btnPulpitSmaller')?.addEventListener('click', () => adjustFont(-4));
    document.getElementById('btnPulpitBigger')?.addEventListener('click', () => adjustFont(4));
    document.getElementById('btnPulpitFullscreen')?.addEventListener('click', toggleFullscreen);
    document.getElementById('btnPulpitAutoScroll')?.addEventListener('click', toggleAutoScroll);
    document.getElementById('btnPulpitBlackout')?.addEventListener('click', toggleBlackout);
    document.getElementById('btnPulpitDualScreen')?.addEventListener('click', () => {
      if (!broadcast?.supported) {
        showToast('이 브라우저에서는 보조 화면 동기화를 지원하지 않습니다.');
        return;
      }
      broadcast.openStageWindow();
      setTimeout(broadcastState, 400);
      showToast('보조 강단 화면 창을 열었습니다.');
    });
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
      if (e.key === 'Escape') { e.preventDefault(); close(); }
      else if (e.key === 'ArrowRight' || e.key === 'PageDown' || e.key === ' ') { e.preventDefault(); step(1); }
      else if (e.key === 'ArrowLeft' || e.key === 'PageUp') { e.preventDefault(); step(-1); }
      else if (e.key === '+' || e.key === '=') { e.preventDefault(); adjustFont(4); }
      else if (e.key === '-') { e.preventDefault(); adjustFont(-4); }
      else if (e.key.toLowerCase() === 'b') { e.preventDefault(); toggleBlackout(); }
      else if (e.key.toLowerCase() === 's') { e.preventDefault(); toggleAutoScroll(); }
    });
  }

  return { open, close, step, bindEvents, isOpen: () => isOpen };
}
