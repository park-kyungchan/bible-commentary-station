export const STORAGE_KEYS = Object.freeze({
  PREFS: 'bibleStation.v3.prefs',
  LAST_PLACE: 'bibleStation.v3.lastPlace',
  HIGHLIGHTS: 'bibleStation.v3.highlights',
});

export const FONT_STEPS = Object.freeze([
  { step: 0, label: '보통' },
  { step: 1, label: '크게' },
  { step: 2, label: '더 크게' },
  { step: 3, label: '아주 크게' },
]);

export function createRequestGuard(channel = 'default') {
  let generation = 0;
  let activeController = null;

  return {
    channel,
    next() {
      if (activeController) {
        try {
          activeController.abort();
        } catch {
          // Ignore abort errors on already-aborted controllers
        }
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
        try {
          activeController.abort();
        } catch {
          // Ignore abort errors
        }
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
  return Math.max(24, Math.min(60, Math.round(n)));
}

export function createStore(storageRef = globalThis.localStorage) {
  const savedPrefs = readJson(storageRef, STORAGE_KEYS.PREFS, {});
  const savedHighlights = readJson(storageRef, STORAGE_KEYS.HIGHLIGHTS, {});
  const savedPlace = readJson(storageRef, STORAGE_KEYS.LAST_PLACE, null);

  const state = {
    mode: 'bible',
    theme: savedPrefs.theme === 'dark' ? 'dark' : 'light',
    fontStepIndex: clampFontStep(savedPrefs.fontStepIndex ?? 1),
    pulpitFontPt: clampPulpitPt(savedPrefs.pulpitFontPt ?? 34),
    primaryVersion: typeof savedPrefs.primaryVersion === 'string'
      ? (savedPrefs.primaryVersion === 'nrsv' ? 'rnksv' : savedPrefs.primaryVersion)
      : '',
    parallelVersion: typeof savedPrefs.parallelVersion === 'string'
      ? (savedPrefs.parallelVersion === 'nrsv' ? 'rnksv' : savedPrefs.parallelVersion)
      : 'none',

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

  const guards = {
    chapter: createRequestGuard('chapter'),
    liveCommentary: createRequestGuard('liveCommentary'),
    search: createRequestGuard('search'),
    worshipDetail: createRequestGuard('worshipDetail'),
  };

  function savePrefs() {
    return writeJson(storageRef, STORAGE_KEYS.PREFS, {
      theme: state.theme,
      fontStepIndex: state.fontStepIndex,
      primaryVersion: state.primaryVersion,
      parallelVersion: state.parallelVersion,
      pulpitFontPt: state.pulpitFontPt,
    });
  }

  function saveLastPlace(osis, chapter, verse) {
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
      fontStepIndex: state.fontStepIndex,
      primaryVersion: state.primaryVersion,
      parallelVersion: state.parallelVersion,
      pulpitFontPt: state.pulpitFontPt,
    };
  }

  function applyPrefsSnapshot(prefs) {
    if (!prefs || typeof prefs !== 'object') return;
    if (prefs.theme === 'light' || prefs.theme === 'dark') state.theme = prefs.theme;
    if (prefs.fontStepIndex !== undefined) state.fontStepIndex = clampFontStep(prefs.fontStepIndex);
    if (prefs.pulpitFontPt !== undefined) state.pulpitFontPt = clampPulpitPt(prefs.pulpitFontPt);
    if (typeof prefs.primaryVersion === 'string') state.primaryVersion = prefs.primaryVersion;
    if (typeof prefs.parallelVersion === 'string') state.parallelVersion = prefs.parallelVersion;
    savePrefs();
  }

  return {
    state,
    guards,
    savePrefs,
    saveLastPlace,
    saveHighlights,
    getPrefsSnapshot,
    applyPrefsSnapshot,
  };
}
