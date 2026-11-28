/**
 * Bible Commentary Station v4.0 — Reactive Workspace Store
 * Backed by fine-grained signals + localStorage persistence + migration from v3 prefs.
 */

import { signal } from '../kernel/signals.js';

export const STORAGE_KEYS = Object.freeze({
  PREFS: 'bibleStation.v4.prefs',
  PREFS_V3: 'bibleStation.v3.prefs',
  LAST_PLACE: 'bibleStation.v3.lastPlace',
  HIGHLIGHTS: 'bibleStation.v3.highlights',
});

export const THEMES = Object.freeze([
  { id: 'hanji', label: '한지 주간', desc: '따뜻한 서재 한지 톤 (WCAG AAA)', dark: false },
  { id: 'vellum', label: '양피지 고전', desc: '수도원 양피지·버건디 고전 톤', dark: false },
  { id: 'obsidian', label: '흑요석 서재', desc: '눈이 편안한 심야 연구 다크 톤', dark: true },
  { id: 'sanctuary', label: '강단 암전', desc: 'OLED 순수 흑색·황금 고대비', dark: true },
]);

export const FONT_STEPS = Object.freeze([
  { step: 0, label: '보통' },
  { step: 1, label: '크게' },
  { step: 2, label: '더 크게' },
  { step: 3, label: '아주 크게' },
]);

export function normalizeTheme(val) {
  if (val === 'light') return 'hanji';
  if (val === 'dark') return 'obsidian';
  if (THEMES.some((t) => t.id === val)) return val;
  return 'hanji';
}

export function createRequestGuard(channel = 'default') {
  let generation = 0;
  let activeController = null;

  return {
    channel,
    next() {
      if (activeController) {
        try { activeController.abort(); } catch { /* ignore */ }
      }
      generation += 1;
      const myGen = generation;
      const controller = typeof AbortController !== 'undefined' ? new AbortController() : null;
      activeController = controller;
      return {
        gen: myGen,
        signal: controller ? controller.signal : undefined,
        isCurrent() {
          return myGen === generation && (!controller || !controller.signal.aborted);
        },
      };
    },
    cancel() {
      if (activeController) {
        try { activeController.abort(); } catch { /* ignore */ }
        activeController = null;
      }
      generation += 1;
    },
    current() {
      return generation;
    },
  };
}

function readJson(storage, key, fallback) {
  if (!storage) return fallback;
  try {
    const raw = storage.getItem(key);
    return raw ? JSON.parse(raw) : fallback;
  } catch {
    return fallback;
  }
}

function writeJson(storage, key, value) {
  if (!storage) return false;
  try {
    storage.setItem(key, JSON.stringify(value));
    return true;
  } catch {
    return false;
  }
}

function clampFontStep(val) {
  const n = Number(val);
  if (!Number.isInteger(n)) return 1;
  return Math.max(0, Math.min(FONT_STEPS.length - 1, n));
}

function clampPulpitPt(val) {
  const n = Number(val);
  if (!Number.isFinite(n)) return 34;
  return Math.max(24, Math.min(64, Math.round(n)));
}

export function createStore(storageRef = globalThis.localStorage) {
  const savedV4 = readJson(storageRef, STORAGE_KEYS.PREFS, null);
  const savedPrefs = savedV4 || readJson(storageRef, STORAGE_KEYS.PREFS_V3, {});
  const savedHighlights = readJson(storageRef, STORAGE_KEYS.HIGHLIGHTS, {});
  const savedPlace = readJson(storageRef, STORAGE_KEYS.LAST_PLACE, null);

  const defaultPolyglot = Array.isArray(savedPrefs.polyglotVersions) && savedPrefs.polyglotVersions.length >= 2
    ? savedPrefs.polyglotVersions.slice(0, 4)
    : ['nkrv', 'rnksv', 'esv'];

  const state = {
    mode: 'bible', // 'bible' | 'matrix' | 'graph' | 'worship' | 'sermon'
    theme: normalizeTheme(savedPrefs.theme),
    zenMode: Boolean(savedPrefs.zenMode),
    fontStepIndex: clampFontStep(savedPrefs.fontStepIndex ?? 1),
    pulpitFontPt: clampPulpitPt(savedPrefs.pulpitFontPt ?? 34),
    pulpitAutoScrollWpm: Number(savedPrefs.pulpitAutoScrollWpm) || 240,
    primaryVersion: typeof savedPrefs.primaryVersion === 'string'
      ? (savedPrefs.primaryVersion === 'nrsv' ? 'rnksv' : savedPrefs.primaryVersion)
      : '',
    parallelVersion: typeof savedPrefs.parallelVersion === 'string'
      ? (savedPrefs.parallelVersion === 'nrsv' ? 'rnksv' : savedPrefs.parallelVersion)
      : 'none',
    polyglotVersions: defaultPolyglot,

    osis: 'GEN',
    chapter: 22,
    selectedVerse: 2,
    chapterVerses: [],
    chapterDir: 'none',

    studyTab: 'commentary',
    studyOverlay: 'none',
    mobileStudyOpen: false,

    commCategory: 'ALL',
    selectedSource: 'ALL',
    compareMode: false,
    compareLeft: 'MATTHEW_HENRY',
    compareRight: 'CALVIN',
    liveCommSource: 'matthew-henry',
    liveCommData: null,
    liveCommLoading: false,
    liveCommError: '',
    liveCommLoadedKey: '',

    graphFilter: 'ALL', // 'ALL' | 'OT' | 'NT' | 'CHAIN'
    graphSelectedNodeId: null,

    worshipTab: 'liturgy',
    worshipSearch: '',
    worshipGroup: '전체',
    selectedWorshipItem: null,
    selectedWorshipType: null,
    worshipOrders: [],
    activeWorshipOrder: null,

    sermons: [],
    activeSermonId: null,
    customBibles: [],
    customHymns: {},
    highlights: savedHighlights && typeof savedHighlights === 'object' ? savedHighlights : {},
    lastPlaceOnBoot: savedPlace && savedPlace.osis ? savedPlace : null,

    persistenceMode: 'idb',
    lastSavedAt: null,
  };

  // Reactive signals synced for modern v4 components
  const signals = {
    mode: signal(state.mode),
    theme: signal(state.theme),
    zenMode: signal(state.zenMode),
    fontStepIndex: signal(state.fontStepIndex),
    passage: signal({ osis: state.osis, chapter: state.chapter, verse: state.selectedVerse }),
  };

  const guards = {
    chapter: createRequestGuard('chapter'),
    matrix: createRequestGuard('matrix'),
    liveCommentary: createRequestGuard('liveCommentary'),
    search: createRequestGuard('search'),
    worshipDetail: createRequestGuard('worshipDetail'),
  };

  function savePrefs() {
    const payload = {
      theme: state.theme,
      zenMode: state.zenMode,
      fontStepIndex: state.fontStepIndex,
      primaryVersion: state.primaryVersion,
      parallelVersion: state.parallelVersion,
      polyglotVersions: state.polyglotVersions,
      pulpitFontPt: state.pulpitFontPt,
      pulpitAutoScrollWpm: state.pulpitAutoScrollWpm,
    };
    writeJson(storageRef, STORAGE_KEYS.PREFS_V3, payload);
    return writeJson(storageRef, STORAGE_KEYS.PREFS, payload);
  }

  function saveLastPlace(osis, chapter, verse) {
    signals.passage.set({ osis, chapter, verse });
    return writeJson(storageRef, STORAGE_KEYS.LAST_PLACE, {
      osis,
      chapter,
      verse,
      updatedAt: new Date().toISOString(),
    });
  }

  function saveHighlights() {
    return writeJson(storageRef, STORAGE_KEYS.HIGHLIGHTS, state.highlights);
  }

  function getPrefsSnapshot() {
    return {
      theme: state.theme,
      zenMode: state.zenMode,
      fontStepIndex: state.fontStepIndex,
      primaryVersion: state.primaryVersion,
      parallelVersion: state.parallelVersion,
      polyglotVersions: [...state.polyglotVersions],
      pulpitFontPt: state.pulpitFontPt,
      pulpitAutoScrollWpm: state.pulpitAutoScrollWpm,
    };
  }

  function applyPrefsSnapshot(prefs) {
    if (!prefs || typeof prefs !== 'object') return;
    if (typeof prefs.theme === 'string') {
      state.theme = normalizeTheme(prefs.theme);
      signals.theme.set(state.theme);
    }
    if (typeof prefs.zenMode === 'boolean') {
      state.zenMode = prefs.zenMode;
      signals.zenMode.set(state.zenMode);
    }
    if (prefs.fontStepIndex !== undefined) {
      state.fontStepIndex = clampFontStep(prefs.fontStepIndex);
      signals.fontStepIndex.set(state.fontStepIndex);
    }
    if (prefs.pulpitFontPt !== undefined) state.pulpitFontPt = clampPulpitPt(prefs.pulpitFontPt);
    if (typeof prefs.primaryVersion === 'string') state.primaryVersion = prefs.primaryVersion;
    if (typeof prefs.parallelVersion === 'string') state.parallelVersion = prefs.parallelVersion;
    if (Array.isArray(prefs.polyglotVersions) && prefs.polyglotVersions.length >= 2) {
      state.polyglotVersions = prefs.polyglotVersions.slice(0, 4);
    }
    savePrefs();
  }

  return {
    state,
    signals,
    guards,
    savePrefs,
    saveLastPlace,
    saveHighlights,
    getPrefsSnapshot,
    applyPrefsSnapshot,
  };
}
