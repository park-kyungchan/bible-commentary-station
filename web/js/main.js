import { bindTablistKeyboard, createModalManager, showToast } from './core/dom.js';
import { createStore, FONT_STEPS } from './core/state.js';
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

function applyRootState(state) {
  const root = document.documentElement;
  root.dataset.theme = state.theme;
  root.dataset.fontStep = String(state.fontStepIndex);
  root.dataset.mode = state.mode;

  const fontLabel = document.getElementById('fontSizeLabel');
  if (fontLabel) fontLabel.textContent = FONT_STEPS[state.fontStepIndex]?.label || '크게';
  const decBtn = document.getElementById('btnFontDec');
  const incBtn = document.getElementById('btnFontInc');
  if (decBtn) decBtn.disabled = state.fontStepIndex <= 0;
  if (incBtn) incBtn.disabled = state.fontStepIndex >= FONT_STEPS.length - 1;
  document.getElementById('btnThemeToggle')?.setAttribute('aria-pressed', state.theme === 'dark' ? 'true' : 'false');

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

function registerServiceWorker() {
  if (!('serviceWorker' in navigator)) return;
  navigator.serviceWorker.register('./sw.js').then((reg) => {
    const promptUpdate = (worker) => {
      const banner = document.getElementById('swUpdateBanner');
      const reloadBtn = document.getElementById('btnSwReload');
      if (!banner || !reloadBtn) return;
      banner.dataset.open = 'true';
      reloadBtn.onclick = () => worker.postMessage({ type: 'SKIP_WAITING' });
    };
    if (reg.waiting) promptUpdate(reg.waiting);
    reg.addEventListener('updatefound', () => {
      const w = reg.installing;
      w?.addEventListener('statechange', () => {
        if (w.state === 'installed' && navigator.serviceWorker.controller) promptUpdate(w);
      });
    });
    let refreshing = false;
    navigator.serviceWorker.addEventListener('controllerchange', () => {
      if (refreshing) return;
      refreshing = true;
      window.location.reload();
    });
  }).catch(() => {});
}

async function initApp() {
  const store = createStore();
  const { state } = store;
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

  const pulpit = createPulpitPrompter({ store });
  pulpit.bindEvents();

  let scriptureReader;
  let commentaryPanel;
  let crossRefPanel;
  let liturgyPanel;
  let worshipPanel;
  let bookmarksSearch;
  let pickerModal;
  let versionModal;

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
    if (!['bible', 'worship', 'sermon'].includes(nextMode)) return;
    state.mode = nextMode;
    applyRootState(state);
    if (nextMode === 'worship') worshipPanel.render();
    else if (nextMode === 'sermon') sermonStudio.render();
  }

  const jumpToPassage = (osis, ch, vs) => {
    setMode('bible');
    setMobileStudy(false);
    scriptureReader.loadChapter(osis, ch, vs, { scrollToVerse: true });
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

  scriptureReader = createScriptureReader({
    store, service,
    callbacks: {
      onChapterLoaded: renderStudyPane,
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
    store, archive, modalManager,
    callbacks: {
      onLaunchPulpit: (deck) => pulpit.open(deck),
      onPrefsRestored: () => { applyRootState(state); versionModal.render(); scriptureReader.loadChapter(state.osis, state.chapter, state.selectedVerse); },
    },
  });
  sermonStudio.bindEvents();

  pickerModal = createBiblePickerModal({ store, service, modalManager, callbacks: { onSelectChapter: jumpToPassage } });
  versionModal = createVersionSettingsModal({
    store, service, archive, modalManager,
    callbacks: {
      onVersionChanged: () => scriptureReader.loadChapter(state.osis, state.chapter, state.selectedVerse),
      onCustomHymnsChanged: () => { if (state.mode === 'worship') worshipPanel.renderListOnly(); },
    },
  });
  versionModal.bindEvents();

  bookmarksSearch = createBookmarksSearchPanel({
    store, service,
    callbacks: { onOverlayClosed: renderStudyPane, onHighlightRemoved: (vid) => scriptureReader.syncHighlightDom(vid), onJumpToPassage: jumpToPassage },
  });

  applyRootState(state);

  document.querySelectorAll('[data-action="set-mode"]').forEach((b) => b.addEventListener('click', () => setMode(b.dataset.modeTarget)));
  document.querySelectorAll('[data-action="open-pulpit"]').forEach((b) => {
    if (b.id !== 'btnSermonPulpit') b.addEventListener('click', () => launchContextPulpit(b));
  });

  document.getElementById('btnFontDec')?.addEventListener('click', () => { state.fontStepIndex = Math.max(0, state.fontStepIndex - 1); store.savePrefs(); applyRootState(state); });
  document.getElementById('btnFontInc')?.addEventListener('click', () => { state.fontStepIndex = Math.min(FONT_STEPS.length - 1, state.fontStepIndex + 1); store.savePrefs(); applyRootState(state); });
  document.getElementById('btnThemeToggle')?.addEventListener('click', () => { state.theme = state.theme === 'dark' ? 'light' : 'dark'; store.savePrefs(); applyRootState(state); });
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

initApp();
