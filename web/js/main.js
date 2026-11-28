/**
 * Bible Commentary Station v4.0 — Spatial Scriptorium Micro-Kernel Entrypoint
 * Orchestrates 5 spatial lenses via Reactive Signals, Event Bus, Command Registry,
 * Plugin Host, and Dual-Screen BroadcastChannel Sync.
 */

import { bindTablistKeyboard, createModalManager, el, showToast } from './core/dom.js';
import { createStore, FONT_STEPS, THEMES } from './core/state.js';
import { createEventBus } from './kernel/eventBus.js';
import { createCommandRegistry } from './kernel/commandRegistry.js';
import { createPluginHost } from './kernel/pluginHost.js';
import { createBroadcastSync } from './kernel/broadcastSync.js';
import { BibleDataService } from './services/bibleService.js';
import { SermonArchiveStore } from './services/storage.js';
import { createScriptureReader } from './features/scriptureReader.js';
import { createCommentaryPanel } from './features/commentaryPanel.js';
import { createCrossRefPanel } from './features/crossRefPanel.js';
import { createLiturgyPanel } from './features/liturgyPanel.js';
import { createWorshipPanel } from './features/worshipPanel.js';
import { createSermonStudio } from './features/sermonStudio.js';
import { createPulpitPrompter } from './features/pulpitPrompter.js';
import { createBiblePickerModal } from './features/biblePickerModal.js';
import { createVersionSettingsModal } from './features/versionSettingsModal.js';
import { createBookmarksSearchPanel } from './features/bookmarksSearchPanel.js';
import { createPolyglotMatrix } from './features/polyglotMatrix.js';
import { createConstellationGraph } from './features/constellationGraph.js';
import { createCommandPalette } from './features/commandPalette.js';

function applyRootState(state) {
  const root = document.documentElement;
  root.dataset.theme = state.theme;
  root.dataset.fontStep = String(state.fontStepIndex);
  root.dataset.mode = state.mode;
  root.dataset.zen = state.zenMode ? 'true' : 'false';

  const fontLabel = document.getElementById('fontSizeLabel');
  if (fontLabel) fontLabel.textContent = FONT_STEPS[state.fontStepIndex]?.label || '크게';
  const decBtn = document.getElementById('btnFontDec');
  const incBtn = document.getElementById('btnFontInc');
  if (decBtn) decBtn.disabled = state.fontStepIndex <= 0;
  if (incBtn) incBtn.disabled = state.fontStepIndex >= FONT_STEPS.length - 1;

  const themeObj = THEMES.find((t) => t.id === state.theme) || THEMES[0];
  const themeLabel = document.getElementById('themeCycleLabel');
  if (themeLabel) themeLabel.textContent = themeObj.label.split(' ')[0];
  document.getElementById('btnThemeToggle')?.setAttribute('aria-pressed', themeObj.dark ? 'true' : 'false');
  document.getElementById('btnZenToggle')?.setAttribute('aria-pressed', state.zenMode ? 'true' : 'false');

  document.querySelectorAll('[data-action="set-mode"]').forEach((btn) => {
    if (btn.dataset.modeTarget === state.mode) btn.setAttribute('aria-current', 'page');
    else btn.removeAttribute('aria-current');
  });
}

function updateStorageWarningBanner(mode) {
  const banner = document.getElementById('storageWarningBanner');
  const textEl = document.getElementById('storageWarningText');
  if (!banner) return;
  banner.dataset.open = mode === 'memory' ? 'true' : 'false';
  if (mode === 'memory' && textEl) {
    textEl.textContent = '임시 저장 모드입니다. 브라우저를 닫으면 작성한 내용이 사라질 수 있으니 지금 백업 파일로 저장해 두세요.';
  }
}

export function shouldReloadOnControllerChange({ hadController, userRequestedUpdate }) {
  return Boolean(hadController && userRequestedUpdate);
}

function registerServiceWorker() {
  if (!('serviceWorker' in navigator)) return;
  const hadController = Boolean(navigator.serviceWorker.controller);
  let userRequestedUpdate = false;
  let refreshing = false;

  navigator.serviceWorker.addEventListener('controllerchange', () => {
    if (!shouldReloadOnControllerChange({ hadController, userRequestedUpdate })) return;
    if (refreshing) return;
    refreshing = true;
    window.location.reload();
  });

  navigator.serviceWorker.register('./sw.js').then((reg) => {
    const promptUpdate = (worker) => {
      const banner = document.getElementById('swUpdateBanner');
      const reloadBtn = document.getElementById('btnSwReload');
      if (!banner || !reloadBtn) return;
      banner.dataset.open = 'true';
      reloadBtn.onclick = () => {
        userRequestedUpdate = true;
        worker.postMessage({ type: 'SKIP_WAITING' });
      };
    };
    if (reg.waiting) promptUpdate(reg.waiting);
    reg.addEventListener('updatefound', () => {
      const w = reg.installing;
      w?.addEventListener('statechange', () => {
        if (w.state === 'installed' && navigator.serviceWorker.controller) promptUpdate(w);
      });
    });
  }).catch(() => {});
}

function bootStageMirrorMode() {
  document.documentElement.dataset.theme = 'sanctuary';
  document.body.replaceChildren();
  const stage = el(
    'div',
    { className: 'stage-mirror' },
    el('div', { id: 'mirrorTitle', className: 'stage-mirror-title' }, '강단 보조 화면 대기 중'),
    el('div', { id: 'mirrorBody', className: 'stage-mirror-body' }, '기본 창에서 [강단 화면]을 열면 본문과 대지가 실시간 동기화됩니다.')
  );
  document.body.appendChild(stage);

  createBroadcastSync({
    onMessage: (msg) => {
      if (msg.type !== 'pulpit:sync') return;
      const p = msg.payload || {};
      stage.dataset.blackout = p.blackout ? 'true' : 'false';
      stage.style.setProperty('--pulpit-font-pt', `${p.fontPt || 42}pt`);
      const tEl = document.getElementById('mirrorTitle');
      const bEl = document.getElementById('mirrorBody');
      if (tEl) tEl.textContent = p.open ? (p.heading || '') : '강단 화면 대기 중';
      if (bEl) {
        const lines = String(p.open ? (p.body || '') : '기본 창에서 강단 화면을 시작해 주세요.').split('\n').filter(Boolean);
        bEl.replaceChildren(...lines.map((l) => el('p', {}, l)));
      }
    },
  });
}

async function initApp() {
  if (typeof window !== 'undefined' && new URLSearchParams(window.location.search).get('view') === 'stage') {
    bootStageMirrorMode();
    return;
  }

  const store = createStore();
  const { state } = store;
  const bus = createEventBus();
  const registry = createCommandRegistry();
  const pluginHost = createPluginHost({ bus });
  const broadcast = createBroadcastSync();
  const service = new BibleDataService('./data');
  const modalManager = createModalManager();
  modalManager.bindGlobalEvents();

  let sermonStudio = null;
  const archive = new SermonArchiveStore({
    onPersistenceChange: ({ mode }) => {
      state.persistenceMode = mode;
      updateStorageWarningBanner(mode);
      sermonStudio?.updateSaveStatus();
    },
  });

  const pulpit = createPulpitPrompter({ store, broadcast });
  pulpit.bindEvents();

  let scriptureReader;
  let commentaryPanel;
  let crossRefPanel;
  let liturgyPanel;
  let worshipPanel;
  let bookmarksSearch;
  let pickerModal;
  let versionModal;
  let polyglotMatrix;
  let constellationGraph;
  let commandPalette;

  const setMobileStudy = (open) => {
    const pane = document.getElementById('paneStudy');
    if (pane) pane.dataset.mobileOpen = open ? 'true' : 'false';
    state.mobileStudyOpen = open;
  };

  function renderStudyPane() {
    if (state.studyOverlay === 'bookmarks') { bookmarksSearch.renderBookmarks(); return; }
    if (state.studyOverlay === 'search') return;
    document.querySelectorAll('[data-study-tab]').forEach((tab) => {
      tab.setAttribute('aria-selected', tab.dataset.studyTab === state.studyTab ? 'true' : 'false');
    });
    const body = document.getElementById('studyBody');
    if (!body) return;
    body.replaceChildren();
    body.dataset.panelEnter = 'true';
    const verseObj = scriptureReader.getSelectedVerse();
    if (state.studyTab === 'commentary') commentaryPanel.render(body, verseObj);
    else if (state.studyTab === 'crossref') crossRefPanel.renderCrossRef(body, verseObj);
    else crossRefPanel.renderStrongs(body, verseObj);
  }

  function setMode(nextMode) {
    if (!['bible', 'matrix', 'graph', 'worship', 'sermon'].includes(nextMode)) return;
    state.mode = nextMode;
    store.signals.mode.set(nextMode);
    applyRootState(state);
    pluginHost.activate(nextMode);
  }

  function cycleTheme(explicitTheme = null) {
    if (explicitTheme && THEMES.some((t) => t.id === explicitTheme)) {
      state.theme = explicitTheme;
    } else {
      const idx = THEMES.findIndex((t) => t.id === state.theme);
      state.theme = THEMES[(idx + 1) % THEMES.length].id;
    }
    store.signals.theme.set(state.theme);
    store.savePrefs();
    applyRootState(state);
    const tObj = THEMES.find((t) => t.id === state.theme);
    if (tObj) showToast(`테마 전환: ${tObj.label}`);
  }

  function toggleZenMode() {
    state.zenMode = !state.zenMode;
    store.signals.zenMode.set(state.zenMode);
    store.savePrefs();
    applyRootState(state);
    showToast(state.zenMode ? '몰입 읽기(Zen) 모드를 켰습니다.' : '몰입 읽기 모드를 해제했습니다.');
  }

  const jumpToPassage = (osis, ch, vs, targetMode = 'bible') => {
    setMode(targetMode);
    setMobileStudy(false);
    scriptureReader.loadChapter(osis, ch, vs, { scrollToVerse: true }).then(() => {
      if (state.mode === 'matrix') polyglotMatrix.render();
    });
  };

  async function launchContextPulpit(triggerEl = null) {
    if (state.mode === 'worship') {
      const litDeck = await liturgyPanel.getActivePulpitDeck();
      const worDeck = worshipPanel.getActivePulpitDeck();
      if (litDeck) { pulpit.open(litDeck, triggerEl); return; }
      if (worDeck) { pulpit.open(worDeck, triggerEl); return; }
    }
    pulpit.open(sermonStudio.buildPulpitDeck(), triggerEl);
  }

  // Instantiate Features
  scriptureReader = createScriptureReader({
    store, service,
    callbacks: {
      onChapterLoaded: () => { renderStudyPane(); if (state.mode === 'matrix') polyglotMatrix.render(); },
      onVerseSelected: renderStudyPane,
      onClipVerse: (src, txt) => sermonStudio.addClip(src, txt),
      onOpenMobileStudy: () => { if (state.studyOverlay !== 'none') bookmarksSearch.closeOverlay(); setMobileStudy(true); renderStudyPane(); },
      onHighlightsChanged: () => { if (state.studyOverlay === 'bookmarks') bookmarksSearch.renderBookmarks(); },
      onError: (msg) => showToast(msg),
    },
  });

  commentaryPanel = createCommentaryPanel({
    store, service,
    callbacks: { onClip: (src, txt) => sermonStudio.addClip(src, txt), onJumpToPassage: jumpToPassage, onRequestRerender: renderStudyPane },
  });

  crossRefPanel = createCrossRefPanel({
    service,
    callbacks: { onClip: (src, txt) => sermonStudio.addClip(src, txt), onJumpToPassage: jumpToPassage },
  });

  polyglotMatrix = createPolyglotMatrix({ store, service, bus });
  constellationGraph = createConstellationGraph({ store, service, bus });

  liturgyPanel = createLiturgyPanel({
    store, service, archive, modalManager,
    callbacks: { onLaunchPulpit: (deck) => pulpit.open(deck), onBackToList: () => worshipPanel.renderListOnly() },
  });

  worshipPanel = createWorshipPanel({
    store, service,
    callbacks: {
      onLaunchPulpit: (deck) => pulpit.open(deck),
      onJumpToPassage: jumpToPassage,
      renderLiturgies: (...a) => liturgyPanel.renderLiturgies(...a),
      renderTemplates: (...a) => liturgyPanel.renderTemplates(...a),
      clearLiturgyDetail: () => liturgyPanel.clearActiveDetail(),
    },
  });
  worshipPanel.bindEvents();

  sermonStudio = createSermonStudio({
    store, service, archive, modalManager,
    callbacks: {
      onLaunchPulpit: (deck) => pulpit.open(deck),
      onOpenPassagePicker: (triggerEl, onSelectRange) => pickerModal.open(triggerEl, { onSelectRange }),
      onPrefsRestored: () => { applyRootState(state); versionModal.render(); scriptureReader.loadChapter(state.osis, state.chapter, state.selectedVerse); },
    },
  });
  sermonStudio.bindEvents();

  pickerModal = createBiblePickerModal({ store, service, modalManager, callbacks: { onSelectChapter: (osis, ch, vs) => jumpToPassage(osis, ch, vs, state.mode === 'matrix' ? 'matrix' : 'bible') } });
  versionModal = createVersionSettingsModal({
    store, service, archive, modalManager,
    callbacks: {
      onVersionChanged: () => {
        scriptureReader.loadChapter(state.osis, state.chapter, state.selectedVerse);
        if (state.mode === 'matrix') polyglotMatrix.render();
      },
      onCustomHymnsChanged: () => { if (state.mode === 'worship') worshipPanel.renderListOnly(); },
    },
  });
  versionModal.bindEvents();

  bookmarksSearch = createBookmarksSearchPanel({
    store, service,
    callbacks: { onOverlayClosed: renderStudyPane, onHighlightRemoved: (vid) => scriptureReader.syncHighlightDom(vid), onJumpToPassage: jumpToPassage },
  });

  // Register 5 Spatial Lenses in Plugin Host
  pluginHost.register({ id: 'bible', title: '몰입 서재', render: () => renderStudyPane() });
  pluginHost.register({ id: 'matrix', title: '다중 역본 매트릭스', render: () => polyglotMatrix.render() });
  pluginHost.register({ id: 'graph', title: '성경 지식 성좌도', render: () => constellationGraph.render() });
  pluginHost.register({ id: 'worship', title: '예배 · 찬송', render: () => worshipPanel.render() });
  pluginHost.register({ id: 'sermon', title: '설교 공방', render: () => sermonStudio.render() });

  // Event Bus Wiring (Decoupled Cross-Lens Communication)
  bus.on('passage:jump', ({ osis, chapter, verse, mode = 'bible' }) => jumpToPassage(osis, chapter, verse, mode));
  bus.on('clip:add', ({ source, text }) => sermonStudio.addClip(source, text));
  bus.on('picker:open', () => pickerModal.open());
  bus.on('chapter:step', ({ dir }) => scriptureReader.stepChapter(dir));

  // Register Universal Command Palette Actions
  registry.register({ id: 'lens:bible', title: '몰입 서재 (성경 · 주석)', subtitle: '성경 본문과 12대 주석·원어 풀이', category: '공간 렌즈', shortcut: '1', icon: 'icon-bible', priority: 30, run: () => setMode('bible') });
  registry.register({ id: 'lens:matrix', title: '다중 역본 매트릭스 (2~4열 대조)', subtitle: '23개 역본 중 최대 4종 동시 비교', category: '공간 렌즈', shortcut: '2', icon: 'icon-matrix', priority: 29, run: () => setMode('matrix') });
  registry.register({ id: 'lens:graph', title: '성경 지식 성좌도 (Knowledge Graph)', subtitle: '상호 관주와 구속사 인물 축 시각화', category: '공간 렌즈', shortcut: '3', icon: 'icon-graph', priority: 28, run: () => setMode('graph') });
  registry.register({ id: 'lens:worship', title: '예배 · 찬송 성소', subtitle: '예전 · 645찬송가 · 137교독문 · 95복음성가', category: '공간 렌즈', shortcut: '4', icon: 'icon-worship', priority: 27, run: () => setMode('worship') });
  registry.register({ id: 'lens:sermon', title: '설교 공방 (Homiletics Studio)', subtitle: '실시간 시간 예측 · 대지 편집 · 인쇄/백업', category: '공간 렌즈', shortcut: '5', icon: 'icon-sermon', priority: 26, run: () => setMode('sermon') });
  registry.register({ id: 'action:pulpit', title: '강단 텔레프롬프터 열기', subtitle: '무눈부심 OLED · 자동 스크롤 · 보조 화면 동기화', category: '강단', shortcut: 'P', icon: 'icon-pulpit', priority: 25, run: () => launchContextPulpit() });
  registry.register({ id: 'action:zen', title: '몰입 읽기(Zen) 모드 전환', subtitle: '상단/보조 도구를 숨기고 성경 본문에만 집중', category: '보기', shortcut: 'Z', icon: 'icon-study', priority: 20, run: toggleZenMode });

  for (const t of THEMES) {
    registry.register({
      id: `theme:${t.id}`,
      title: `테마: ${t.label}`,
      subtitle: t.desc,
      category: '테마',
      keywords: [t.id, '테마', '다크', '라이트', '색상'],
      icon: t.dark ? 'icon-moon' : 'icon-sun',
      priority: 12,
      run: () => cycleTheme(t.id),
    });
  }

  // Dynamic Command Providers (645 Hymns, 137 Responsive Readings, 66 Books)
  registry.registerProvider((raw, norm) => {
    if (!norm) return [];
    const out = [];
    const hymns = service.worship?.hymns || [];
    for (const h of hymns) {
      if (String(h.num) === raw.replace(/[^0-9]/g, '') || String(h.title || '').includes(raw)) {
        out.push({
          id: `hymn:${h.num}`,
          title: `새찬송가 ${h.num}장 · ${h.title}`,
          subtitle: `${h.category || '찬송가'} · 예배 화면에서 바로 열기`,
          category: '찬송가',
          icon: 'icon-worship',
          score: String(h.num) === raw.replace(/[^0-9]/g, '') ? 130 : 80,
          run: () => {
            state.worshipTab = 'hymns';
            state.worshipSearch = String(h.num);
            setMode('worship');
          },
        });
        if (out.length >= 5) break;
      }
    }
    const books = service.getBooks();
    for (const b of books) {
      if (b.name.includes(raw) || b.abbr === raw || b.id.toLowerCase() === raw.toLowerCase()) {
        out.push({
          id: `book:${b.id}`,
          title: `${b.name} 1장 열기`,
          subtitle: `${b.testament === 'OT' ? '구약' : '신약'} · 총 ${b.totalChapters}장`,
          category: '성경 66권',
          icon: 'icon-bible',
          score: 88,
          run: () => jumpToPassage(b.id, 1, 1, 'bible'),
        });
      }
    }
    return out;
  });

  commandPalette = createCommandPalette({ registry, service, store, bus });
  commandPalette.bindEvents();

  applyRootState(state);

  // Bind UI Controls
  document.querySelectorAll('[data-action="set-mode"]').forEach((b) => b.addEventListener('click', () => setMode(b.dataset.modeTarget)));
  document.querySelectorAll('[data-action="open-pulpit"]').forEach((b) => {
    if (b.id !== 'btnSermonPulpit') b.addEventListener('click', () => launchContextPulpit(b));
  });
  document.getElementById('btnOpenCommand')?.addEventListener('click', (e) => commandPalette.open(e.currentTarget));
  document.getElementById('btnZenToggle')?.addEventListener('click', toggleZenMode);
  document.getElementById('btnExitZen')?.addEventListener('click', toggleZenMode);
  document.getElementById('btnFontDec')?.addEventListener('click', () => { state.fontStepIndex = Math.max(0, state.fontStepIndex - 1); store.savePrefs(); applyRootState(state); });
  document.getElementById('btnFontInc')?.addEventListener('click', () => { state.fontStepIndex = Math.min(FONT_STEPS.length - 1, state.fontStepIndex + 1); store.savePrefs(); applyRootState(state); });
  document.getElementById('btnThemeToggle')?.addEventListener('click', () => cycleTheme());
  document.getElementById('btnHelp')?.addEventListener('click', (e) => modalManager.open('helpModal', e.currentTarget));
  document.getElementById('btnOpenPicker')?.addEventListener('click', (e) => pickerModal.open(e.currentTarget));
  document.getElementById('btnPrevChap')?.addEventListener('click', () => scriptureReader.stepChapter('prev'));
  document.getElementById('btnNextChap')?.addEventListener('click', () => scriptureReader.stepChapter('next'));
  document.getElementById('btnVersionSettings')?.addEventListener('click', (e) => versionModal.open(e.currentTarget));
  document.getElementById('btnBookmarks')?.addEventListener('click', () => bookmarksSearch.openBookmarks());
  document.getElementById('btnCloseStudyOverlay')?.addEventListener('click', () => bookmarksSearch.closeOverlay());
  document.getElementById('btnCloseMobileStudy')?.addEventListener('click', () => setMobileStudy(false));
  document.getElementById('btnStorageBackupNow')?.addEventListener('click', () => sermonStudio.exportFullBackup());

  document.getElementById('searchForm')?.addEventListener('submit', (e) => {
    e.preventDefault();
    bookmarksSearch.runSearch(document.getElementById('searchInput')?.value || '');
  });

  const studyTabList = document.getElementById('studyTabList');
  const selectStudyTab = (tab) => {
    state.studyTab = tab.dataset.studyTab;
    if (state.studyOverlay !== 'none') bookmarksSearch.closeOverlay();
    else renderStudyPane();
  };
  studyTabList?.addEventListener('click', (e) => {
    const tab = e.target.closest?.('[data-study-tab]');
    if (tab) selectStudyTab(tab);
  });
  bindTablistKeyboard(studyTabList, '[data-study-tab]', selectStudyTab);

  document.addEventListener('visibilitychange', () => { if (document.visibilityState === 'hidden') archive.flushPendingSaves(); });
  window.addEventListener('pagehide', () => { archive.flushPendingSaves(); });
  registerServiceWorker();

  try {
    const [, sermons, customBibles, customHymns, worshipOrders] = await Promise.all([
      service.init(),
      archive.listSermons(),
      archive.listCustomBibles(),
      archive.getCustomHymnLyricsMap(),
      archive.listWorshipOrders(),
    ]);
    state.sermons = sermons;
    state.activeSermonId = sermons[0]?.id || null;
    state.customBibles = customBibles;
    state.customHymns = customHymns;
    state.worshipOrders = worshipOrders;
    if (!state.primaryVersion) state.primaryVersion = service.getDefaultVersionId();
    versionModal.render();

    const boot = state.lastPlaceOnBoot;
    if (boot && service.getBookMeta(boot.osis)) {
      await scriptureReader.loadChapter(boot.osis, boot.chapter || 1, boot.verse || 1, { scrollToVerse: true });
      showToast('지난번 읽던 곳으로 열었습니다.');
    } else {
      await scriptureReader.loadChapter('GEN', 22, 2, { scrollToVerse: false });
    }
  } catch {
    showToast('성경 자료를 불러오는 중 문제가 발생했습니다. 잠시 후 새로고침해 주세요.');
  }
}

if (typeof document !== 'undefined') {
  initApp();
}
