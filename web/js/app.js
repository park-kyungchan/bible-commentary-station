import {
  BibleDataService,
  BUILTIN_TRANSLATIONS,
  LIVE_COMMENTARY_SOURCES,
} from './bibleService.js';
import {
  SermonArchiveStore,
  createDefaultSermon,
  parseCustomBibleFile,
  parseCustomHymnFile,
} from './storage.js';

const service = new BibleDataService('./data');
const sermonStore = new SermonArchiveStore();

const HIGHLIGHT_KEY = 'bibleStation.highlights.v2';
const LAST_PLACE_KEY = 'bibleStation.lastPlace.v2';
const FONT_STEPS = [
  { px: 18, label: '보통' },
  { px: 21, label: '크게' },
  { px: 25, label: '아주 크게' },
  { px: 30, label: '초대형' },
];

const REL_LABELS = {
  PROPHECY_FULFILLMENT: '약속과 성취',
  PARALLEL: '같은 말씀',
  EXPLANATORY: '말씀 풀이',
  THEMATIC: '같은 주제',
  QUOTATION: '인용 말씀',
};

const COMM_CATEGORIES = [
  { key: 'ALL', label: '전체 12종' },
  { key: 'CLASSIC', label: '고전·경건 (4)' },
  { key: 'ACADEMIC', label: '원어·학술 (4)' },
  { key: 'EXPOSITORY', label: '강해·설교 (4)' },
];

const state = {
  osis: 'GEN',
  chapter: 22,
  verse: 2,
  verses: [],
  studyTab: 'commentary',
  commCategory: 'ALL',
  selectedSource: 'ALL',
  compareMode: false,
  compareLeft: 'MATTHEW_HENRY',
  compareRight: 'NICOT_NICNT',
  primaryVersion: 'nkrv',
  parallelVersion: 'none', // 'none' | 'BSB' | 'eng_kjv' | 'hbo_wlc' | 'grc_sbl' | 'custom_...'
  primaryMap: null,
  parallelMap: null,
  parallelError: '',
  customBibles: [],
  customHymnLyrics: {},
  liveCommSource: 'matthew-henry',
  liveCommData: null,
  liveCommLoading: false,
  liveCommError: '',
  hymnRange: 'FEATURED', // FEATURED | ALL | 1-100 | 101-200 | ... | 601-645
  expandedHymnNum: null,
  selectedHymn: null,
  worshipMode: 'hymns', // hymns | responsive
  worshipGroup: '전체',
  worshipQuery: '',
  selectedResponsive: null,
  rrViewMode: 'ppt', // ppt | text
  rrRange: 'ALL', // ALL | 1-50 | 51-100 | 101-137
  customPulpitSlides: null,
  theme: 'light',
  fontStepIndex: 1,
  highlights: loadJson(HIGHLIGHT_KEY, {}),
  sermons: [],
  activeSermonId: null,
  pickerTestament: 'OT',
  pickerBook: null,
  pulpit: {
    open: false,
    slideIndex: 0,
    fontSizePt: 40,
    remainingSec: 30 * 60,
    paused: false,
    timerId: null,
    wakeLock: null,
  },
};

function loadJson(key, fallback) {
  try {
    return JSON.parse(localStorage.getItem(key) || 'null') || fallback;
  } catch {
    return fallback;
  }
}

function saveJson(key, value) {
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch {
    // Ignore quota errors
  }
}

function el(tag, attrs = {}, ...children) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v === null || v === undefined) continue;
    if (k === 'className') node.className = v;
    else if (k === 'dataset') Object.assign(node.dataset, v);
    else if (k.startsWith('on') && typeof v === 'function') node.addEventListener(k.slice(2).toLowerCase(), v);
    else node.setAttribute(k, String(v));
  }
  for (const ch of children.flat()) {
    if (ch === null || ch === undefined) continue;
    node.appendChild(typeof ch === 'string' || typeof ch === 'number' ? document.createTextNode(String(ch)) : ch);
  }
  return node;
}

function showToast(msg) {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.classList.add('show');
  clearTimeout(showToast._tid);
  showToast._tid = setTimeout(() => t.classList.remove('show'), 2500);
}

function getActiveSermon() {
  return state.sermons.find((s) => s.id === state.activeSermonId) || state.sermons[0];
}

function getCurrentVerseObj() {
  return state.verses.find((v) => v.verse === state.verse) || state.verses[0] || null;
}

function getAllVersionOptions() {
  const customOpts = state.customBibles.map((cb) => ({
    id: cb.id,
    label: `📂 ${cb.name} (내 파일 · ${cb.verseCount.toLocaleString()}절)`,
    shortLabel: cb.shortName || cb.name,
    lang: 'ko',
    source: 'custom',
  }));
  return [...customOpts, ...BUILTIN_TRANSLATIONS];
}

function getVersionMeta(versionId) {
  return getAllVersionOptions().find((v) => v.id === versionId) || BUILTIN_TRANSLATIONS[0];
}

function populateVersionSelectors() {
  const pSel = document.getElementById('primaryVersionSelect');
  const sSel = document.getElementById('parallelVersionSelect');
  if (!pSel || !sSel) return;
  const opts = getAllVersionOptions();

  pSel.replaceChildren(
    ...opts.map((o) => el('option', { value: o.id, selected: o.id === state.primaryVersion ? '' : null }, `주 역본: ${o.label}`))
  );
  sSel.replaceChildren(
    el('option', { value: 'none', selected: state.parallelVersion === 'none' ? '' : null }, '비교 역본: 사용 안 함'),
    ...opts.map((o) => el('option', { value: o.id, selected: o.id === state.parallelVersion ? '' : null }, `비교: ${o.label}`))
  );
}

/* ---------- 성경 장 로딩 & 다역본 렌더링 ---------- */
async function loadChapter(osis, ch, targetVerse = 1) {
  state.osis = osis;
  state.chapter = ch;
  state.liveCommData = null;
  state.liveCommError = '';
  const meta = service.getBookMeta(osis);
  document.getElementById('currentPlaceText').textContent = `${meta ? meta.name : osis} ${ch}장`;

  const container = document.getElementById('verseList');
  container.replaceChildren(el('p', { style: 'padding:30px;font-size:18px;text-align:center;' }, '성경 말씀을 불러오고 있습니다…'));

  state.verses = await service.getChapterVerses(osis, ch);
  state.verse = state.verses.some((v) => v.verse === targetVerse) ? targetVerse : 1;

  // Load primary & optional parallel version maps
  state.parallelError = '';
  try {
    state.primaryMap = state.primaryVersion === '__none__'
      ? null
      : await service.getVersionChapterMap(state.primaryVersion, osis, ch, state.customBibles);
  } catch (e) {
    state.primaryMap = null;
    showToast(`주 역본 불러오기 실패(${e.message}) — 개역한글로 표시합니다.`);
  }

  if (state.parallelVersion && state.parallelVersion !== 'none') {
    try {
      state.parallelMap = await service.getVersionChapterMap(state.parallelVersion, osis, ch, state.customBibles);
    } catch (e) {
      state.parallelMap = null;
      state.parallelError = `${getVersionMeta(state.parallelVersion).shortLabel} 불러오기 실패 (구·신약 범위 또는 인터넷 연결 확인)`;
    }
  } else {
    state.parallelMap = null;
  }

  saveJson(LAST_PLACE_KEY, { osis, chapter: ch, verse: state.verse, label: `${meta ? meta.name : osis} ${ch}장 ${state.verse}절` });
  renderVerses();
  renderStudyPane();
  loadLiveCommentaryIfActive();
}

function renderVerses() {
  const container = document.getElementById('verseList');
  container.replaceChildren();
  const meta = service.getBookMeta(state.osis);
  const pMeta = getVersionMeta(state.primaryVersion);
  const sMeta = state.parallelVersion !== 'none' ? getVersionMeta(state.parallelVersion) : null;

  container.appendChild(
    el(
      'div',
      { className: 'chapter-heading' },
      el('h1', {}, `${meta ? meta.name : state.osis} ${state.chapter}장`),
      el('span', { className: 'sub' }, `${pMeta.shortLabel}${sMeta ? ` + ${sMeta.shortLabel} 대조` : ''} · 총 ${state.verses.length}절`)
    )
  );

  if (state.parallelError) {
    container.appendChild(el('div', { className: 'callout', style: 'margin-bottom:12px;' }, `⚠️ ${state.parallelError}`));
  }

  for (const v of state.verses) {
    const comms = service.getCommentariesForVerse(v.verseId);
    const refs = service.getCrossReferencesForVerse(v.verseId);
    const isSel = v.verse === state.verse;
    const hl = state.highlights[String(v.verseId)]?.color || '';
    const primaryText = (state.primaryMap && state.primaryMap[v.verse]) ? state.primaryMap[v.verse] : v.text;
    const parallelText = (state.parallelMap && state.parallelMap[v.verse]) ? state.parallelMap[v.verse] : '';

    const topRow = el(
      'div',
      { className: 'verse-top' },
      el('span', { className: 'verse-badge-num' }, v.verse),
      comms.length ? el('span', { className: 'tag tag-accent' }, `한글 주석 ${comms.length}종`) : null,
      refs.length ? el('span', { className: 'tag' }, `연결 말씀 ${refs.length}`) : null
    );

    const cardChildren = [
      topRow,
      el('p', { className: `verse-text ${pMeta.lang === 'he' ? 'rtl-text' : ''}` }, primaryText),
    ];

    if (sMeta && parallelText) {
      cardChildren.push(
        el(
          'div',
          { className: `parallel-verse ${sMeta.lang === 'he' ? 'rtl-text' : ''}` },
          el('div', {}, el('span', { className: 'parallel-badge' }, sMeta.shortLabel)),
          el('div', {}, parallelText)
        )
      );
    }

    if (isSel) {
      const hlOptions = [
        { key: 'yellow', label: '🟡 노랑 밑줄' },
        { key: 'green', label: '🟢 초록 밑줄' },
        { key: 'pink', label: '🩷 분홍 밑줄' },
      ];
      cardChildren.push(
        el(
          'div',
          { className: 'verse-toolbar' },
          ...hlOptions.map((opt) =>
            el(
              'button',
              {
                type: 'button',
                className: 'hl-btn',
                onClick: (e) => {
                  e.stopPropagation();
                  const key = String(v.verseId);
                  if (state.highlights[key]?.color === opt.key) {
                    delete state.highlights[key];
                    showToast('밑줄 표시를 지웠습니다.');
                  } else {
                    state.highlights[key] = {
                      color: opt.key, osis: v.osis, bookName: v.bookName,
                      chapter: v.chapter, verse: v.verse, text: v.text,
                    };
                    showToast(`${v.bookName} ${v.chapter}:${v.verse}에 표시했습니다.`);
                  }
                  saveJson(HIGHLIGHT_KEY, state.highlights);
                  renderVerses();
                },
              },
              opt.label
            )
          ),
          el(
            'button',
            {
              type: 'button',
              className: 'btn btn-sm btn-primary',
              onClick: (e) => {
                e.stopPropagation();
                clipToSermon(`${v.bookName} ${v.chapter}:${v.verse}`, v.text);
              },
            },
            '✍️ 설교 노트에 담기'
          )
        )
      );
    }

    container.appendChild(
      el(
        'article',
        {
          className: `verse-card ${isSel ? 'selected' : ''} ${hl ? `hl-${hl}` : ''}`,
          onClick: () => {
            state.verse = v.verse;
            renderVerses();
            renderStudyPane();
          },
        },
        ...cardChildren
      )
    );
  }
}

/* ---------- 오른쪽 패널: 12대 공식 주석 / 연결 말씀 / 찬송·교독문 / 원어 / 설교 노트 ---------- */
function renderStudyPane() {
  document.querySelectorAll('[data-study-tab]').forEach((btn) => {
    btn.classList.toggle('active', btn.dataset.studyTab === state.studyTab);
  });
  const body = document.getElementById('studyBody');
  body.replaceChildren();

  if (state.studyTab === 'commentary') renderCommentaryTab(body);
  else if (state.studyTab === 'crossref') renderCrossRefTab(body);
  else if (state.studyTab === 'worship') renderWorshipTab(body);
  else if (state.studyTab === 'strongs') renderStrongsTab(body);
  else renderSermonStudioTab(body);
}

function renderCommentaryTab(body) {
  const v = getCurrentVerseObj();
  if (!v) return;
  const allSources = service.exegesis.sources;
  const entries = service.getCommentariesForVerse(v.verseId);

  body.appendChild(
    el(
      'div',
      { style: 'display:flex;align-items:center;justify-content:space-between;gap:10px;margin-bottom:12px;flex-wrap:wrap;' },
      el('strong', { style: 'font-size:18px;color:var(--primary);' }, `${v.bookName} ${v.chapter}장 ${v.verse}절 공식 주석 (${entries.length}종)`),
      el(
        'button',
        {
          type: 'button',
          className: `btn btn-sm ${state.compareMode ? 'btn-primary' : ''}`,
          onClick: () => { state.compareMode = !state.compareMode; renderStudyPane(); },
        },
        state.compareMode ? '하나씩 크게 보기' : '두 주석 나란히 비교'
      )
    )
  );

  if (state.compareMode) {
    const mkSel = (val, onCh) =>
      el(
        'select',
        { className: 'input-lg', onChange: (e) => { onCh(e.target.value); renderStudyPane(); } },
        ...allSources.map((s) => el('option', { value: s.source_code, selected: s.source_code === val ? '' : null }, `[${s.category_kr}] ${s.name_kr}`))
      );
    body.appendChild(
      el('div', { style: 'display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:12px;' },
        mkSel(state.compareLeft, (val) => { state.compareLeft = val; }),
        mkSel(state.compareRight, (val) => { state.compareRight = val; })
      )
    );
    body.appendChild(
      el(
        'div',
        { className: 'compare-grid' },
        buildCommentaryCard(entries.find((e) => e.source_code === state.compareLeft), state.compareLeft, allSources),
        buildCommentaryCard(entries.find((e) => e.source_code === state.compareRight), state.compareRight, allSources)
      )
    );
    renderLiveCommentaryBlock(body, v);
    return;
  }

  // 주석 종류별 큰 분류 탭 (전체 / 고전·경건 / 원어·학술 / 강해·설교)
  body.appendChild(
    el(
      'div',
      { style: 'display:flex;gap:6px;margin-bottom:10px;flex-wrap:wrap;' },
      ...COMM_CATEGORIES.map((cat) =>
        el(
          'button',
          {
            type: 'button',
            className: `btn btn-sm ${state.commCategory === cat.key ? 'btn-primary' : ''}`,
            onClick: () => { state.commCategory = cat.key; state.selectedSource = 'ALL'; renderStudyPane(); },
          },
          cat.label
        )
      )
    )
  );

  const visibleSources = state.commCategory === 'ALL'
    ? allSources
    : allSources.filter((s) => s.category === state.commCategory);

  body.appendChild(
    el(
      'div',
      { className: 'source-grid' },
      el('button', { type: 'button', className: `source-pill ${state.selectedSource === 'ALL' ? 'active' : ''}`, onClick: () => { state.selectedSource = 'ALL'; renderStudyPane(); } }, '분류 전체'),
      ...visibleSources.map((s) =>
        el(
          'button',
          {
            type: 'button',
            className: `source-pill ${state.selectedSource === s.source_code ? 'active' : ''}`,
            onClick: () => { state.selectedSource = s.source_code; renderStudyPane(); },
          },
          s.name_kr.replace(' 성경 주석', '').replace(' 종합주석', '').replace(' 완역 주석', '')
        )
      )
    )
  );

  const allowedCodes = new Set(visibleSources.map((s) => s.source_code));
  const filtered = entries.filter((e) =>
    allowedCodes.has(e.source_code) && (state.selectedSource === 'ALL' || e.source_code === state.selectedSource)
  );

  if (!filtered.length) {
    const meta = service.getBookMeta(state.osis);
    const bhBook = (meta?.nameEn || 'genesis').toLowerCase().replace(/\s+/g, '_');
    body.appendChild(
      el(
        'div',
        { className: 'card' },
        el('h3', {}, `${v.bookName} ${v.chapter}:${v.verse} 대표 주석 안내`),
        el('p', {}, '이 절의 한글 요약 주석은 아래 공식 원문 주석 사이트에서 바로 열람하거나, 대표 강해 말씀에서 12대 공식 주석 비교를 확인하실 수 있습니다.'),
        el(
          'div',
          { style: 'display:flex;gap:8px;margin-top:14px;flex-wrap:wrap;' },
          el('a', { className: 'btn btn-primary btn-sm', href: `https://biblehub.com/commentaries/${bhBook}/${v.chapter}-${v.verse}.htm`, target: '_blank', rel: 'noopener noreferrer', style: 'text-decoration:none;' }, '🌐 공식 주석 원문(BibleHub) 열기'),
          el('button', { type: 'button', className: 'btn btn-sm', onClick: () => loadChapter('GEN', 22, 2) }, '창세기 22:2 (12종)'),
          el('button', { type: 'button', className: 'btn btn-sm', onClick: () => loadChapter('PSA', 23, 1) }, '시편 23:1'),
          el('button', { type: 'button', className: 'btn btn-sm', onClick: () => loadChapter('JHN', 3, 16) }, '요한복음 3:16'),
          el('button', { type: 'button', className: 'btn btn-sm', onClick: () => loadChapter('ISA', 53, 5) }, '이사야 53:5'),
          el('button', { type: 'button', className: 'btn btn-sm', onClick: () => loadChapter('MAT', 11, 28) }, '마태복음 11:28'),
          el('button', { type: 'button', className: 'btn btn-sm', onClick: () => loadChapter('ROM', 8, 28) }, '로마서 8:28'),
          el('button', { type: 'button', className: 'btn btn-sm', onClick: () => loadChapter('PHP', 4, 6) }, '빌립보서 4:6'),
          el('button', { type: 'button', className: 'btn btn-sm', onClick: () => loadChapter('HEB', 11, 1) }, '히브리서 11:1'),
          el('button', { type: 'button', className: 'btn btn-sm', onClick: () => loadChapter('REV', 21, 4) }, '계시록 21:4')
        )
      )
    );
    renderLiveCommentaryBlock(body, v);
    return;
  }

  for (const item of filtered) {
    body.appendChild(buildCommentaryCard(item, item.source_code, allSources));
  }
  renderLiveCommentaryBlock(body, v);
}

async function loadLiveCommentaryIfActive() {
  if (state.studyTab !== 'commentary' || !state.liveCommSource) return;
  state.liveCommLoading = true;
  state.liveCommError = '';
  try {
    state.liveCommData = await service.fetchLiveCommentaryChapter(state.liveCommSource, state.osis, state.chapter);
  } catch (e) {
    state.liveCommData = null;
    state.liveCommError = e.message;
  } finally {
    state.liveCommLoading = false;
    if (state.studyTab === 'commentary') renderStudyPane();
  }
}

function renderLiveCommentaryBlock(body, v) {
  const sec = el('div', { className: 'live-comm-section' });
  sec.appendChild(
    el(
      'div',
      { style: 'display:flex;align-items:center;justify-content:space-between;gap:8px;flex-wrap:wrap;margin-bottom:10px;' },
      el('strong', { style: 'font-size:17.5px;color:var(--primary);' }, `🌐 전 66권 실시간 공식 원문 주석 (${v.bookName} ${v.chapter}:${v.verse})`),
      el('span', { className: 'tag' }, 'HelloAO 퍼블릭 도메인 원문')
    )
  );

  sec.appendChild(
    el(
      'div',
      { className: 'source-grid', style: 'margin-bottom:12px;' },
      ...LIVE_COMMENTARY_SOURCES.map((srcItem) =>
        el(
          'button',
          {
            type: 'button',
            className: `source-pill ${state.liveCommSource === srcItem.id ? 'active' : ''}`,
            onClick: () => {
              state.liveCommSource = srcItem.id;
              state.liveCommData = null;
              loadLiveCommentaryIfActive();
              renderStudyPane();
            },
          },
          `${srcItem.name.split(' (')[0]}`
        )
      )
    )
  );

  const activeMeta = LIVE_COMMENTARY_SOURCES.find((s) => s.id === state.liveCommSource) || LIVE_COMMENTARY_SOURCES[0];

  if (state.liveCommLoading) {
    sec.appendChild(el('div', { className: 'card' }, el('p', {}, `${activeMeta.name} 원문을 불러오고 있습니다…`)));
    body.appendChild(sec);
    return;
  }
  if (state.liveCommError) {
    sec.appendChild(
      el('div', { className: 'card' },
        el('p', {}, `실시간 주석을 불러오지 못했습니다: ${state.liveCommError}`),
        el('button', { type: 'button', className: 'btn btn-sm btn-primary', style: 'margin-top:8px;', onClick: loadLiveCommentaryIfActive }, '다시 시도')
      )
    );
    body.appendChild(sec);
    return;
  }
  if (!state.liveCommData) {
    sec.appendChild(
      el('div', { className: 'card' },
        el('p', {}, `${activeMeta.name} — ${activeMeta.desc}`),
        el('button', { type: 'button', className: 'btn btn-sm btn-primary', style: 'margin-top:10px;', onClick: loadLiveCommentaryIfActive }, '📖 이 절의 공식 원문 주석 불러오기')
      )
    );
    body.appendChild(sec);
    return;
  }

  if (!state.liveCommData.available) {
    sec.appendChild(
      el('div', { className: 'card' },
        el('h3', {}, activeMeta.name),
        el('p', {}, '선택하신 주석서에는 이 책/장이 수록되어 있지 않습니다(예: 구약 전용 또는 48권 수록 주석). 위에서 매튜 헨리·JFB·아담 클라크·존 길·TSK 등 66권 전체 주석을 선택해 보세요.')
      )
    );
    body.appendChild(sec);
    return;
  }

  const verseText = state.liveCommData.verses[v.verse] || '';
  const introText = state.liveCommData.introduction || '';
  const displayBody = verseText || introText || '이 장의 절별 주석은 인접 절(앞뒤 절) 해설에 통합되어 있습니다. 아래에서 장 전체 서론이나 인접 절을 눌러 확인하실 수 있습니다.';
  const translateUrl = `https://translate.google.com/?sl=en&tl=ko&text=${encodeURIComponent(displayBody.slice(0, 1800))}&op=translate`;

  sec.appendChild(
    el(
      'div',
      { className: 'card' },
      el('div', { style: 'display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-bottom:8px;' },
        el('span', { className: 'tag tag-accent' }, activeMeta.name),
        el('span', { className: 'tag' }, activeMeta.badge),
        el('a', { href: state.liveCommData.url, target: '_blank', rel: 'noopener noreferrer', style: 'margin-left:auto;font-size:13px;color:var(--primary);font-weight:700;' }, '원문 API ↗')
      ),
      el('h3', {}, `${v.bookName} ${v.chapter}:${v.verse} 원문 주해`),
      el('div', { className: 'live-comm-text' }, displayBody),
      el('div', { style: 'display:flex;gap:8px;flex-wrap:wrap;margin-top:14px;' },
        el('button', {
          type: 'button',
          className: 'btn btn-sm btn-soft',
          onClick: () => clipToSermon(`${activeMeta.name} (${v.bookName} ${v.chapter}:${v.verse})`, displayBody),
        }, '✍️ 설교 노트에 담기'),
        el('a', {
          className: 'btn btn-sm btn-primary',
          href: translateUrl,
          target: '_blank',
          rel: 'noopener noreferrer',
          style: 'text-decoration:none;',
        }, '🇰🇷 구글 번역으로 한국어 보기 ↗')
      )
    )
  );
  body.appendChild(sec);
}

function buildCommentaryCard(entry, sourceCode, sources) {
  const srcMeta = sources.find((s) => s.source_code === sourceCode);
  if (!entry) {
    return el('div', { className: 'card' }, el('h3', {}, srcMeta ? srcMeta.name_kr : sourceCode), el('p', {}, '선택하신 절의 주석이 없습니다.'));
  }
  return el(
    'div',
    { className: 'card' },
    el(
      'div',
      { style: 'display:flex;align-items:center;gap:8px;margin-bottom:8px;flex-wrap:wrap;' },
      el('span', { className: 'tag tag-accent' }, srcMeta ? srcMeta.name_kr : entry.source_code),
      srcMeta ? el('span', { className: 'tag' }, srcMeta.category_kr) : null,
      srcMeta?.official_url
        ? el('a', { href: srcMeta.official_url, target: '_blank', rel: 'noopener noreferrer', style: 'margin-left:auto;font-size:13px;color:var(--primary);font-weight:700;' }, '공식 출처 ↗')
        : null
    ),
    el('h3', {}, entry.title),
    el('p', {}, entry.content_markdown),
    entry.practical_points ? el('div', { className: 'callout' }, `💡 설교 · 삶 적용: ${entry.practical_points}`) : null,
    el(
      'div',
      { style: 'margin-top:14px;' },
      el(
        'button',
        {
          type: 'button',
          className: 'btn btn-sm btn-soft',
          onClick: () => clipToSermon(srcMeta ? srcMeta.name_kr : entry.source_code, `${entry.title}\n${entry.content_markdown}`),
        },
        '✍️ 이 주석을 설교 노트에 담기'
      )
    )
  );
}

/* ---------- 🎵 찬송가 · 교독문 빠른 찾기 ---------- */
async function renderWorshipTab(body) {
  body.appendChild(
    el(
      'div',
      { style: 'display:flex;gap:8px;margin-bottom:12px;flex-wrap:wrap;' },
      el('button', { type: 'button', className: `btn ${state.worshipMode === 'hymns' ? 'btn-primary' : ''}`, onClick: () => { state.worshipMode = 'hymns'; state.selectedResponsive = null; state.selectedHymn = null; renderStudyPane(); } }, '🎵 새찬송가 찾기'),
      el('button', { type: 'button', className: `btn ${state.worshipMode === 'responsive' ? 'btn-primary' : ''}`, onClick: () => { state.worshipMode = 'responsive'; renderStudyPane(); } }, '📜 교독문 빠른 찾기')
    )
  );

  body.appendChild(
    el('input', {
      type: 'search',
      className: 'input-lg',
      style: 'margin-bottom:14px;',
      value: state.worshipQuery,
      placeholder: state.worshipMode === 'hymns'
        ? '찬송가 번호나 제목·주제 입력 (예: 305, 나 같은 죄인, 감사, 부활)'
        : '교독문 번호나 시편·절기 입력 (예: 11, 시편 23, 부활절, 추수감사)',
      onInput: (e) => {
        state.worshipQuery = e.target.value;
        state.selectedResponsive = null; state.selectedHymn = null;
        renderStudyPane();
      },
    })
  );

  const groups = state.worshipMode === 'hymns'
    ? (service.worship?.hymnGroups || ['전체'])
    : (service.worship?.responsiveGroups || ['전체']);
  if (!groups.includes(state.worshipGroup)) state.worshipGroup = '전체';

  body.appendChild(
    el(
      'div',
      { className: 'source-grid', style: 'margin-bottom:12px;' },
      ...groups.map((g) =>
        el(
          'button',
          {
            type: 'button',
            className: `source-pill ${state.worshipGroup === g ? 'active' : ''}`,
            onClick: () => { state.worshipGroup = g; state.selectedResponsive = null; state.selectedHymn = null; renderStudyPane(); },
          },
          g
        )
      )
    )
  );

  const q = state.worshipQuery.trim();

  if (state.worshipMode === 'hymns') {
    if (state.selectedHymn) {
      const sh = state.selectedHymn;
      body.appendChild(
        el('div', { className: 'no-print', style: 'display:flex;gap:8px;margin-bottom:12px;flex-wrap:wrap;' },
          el('button', { type: 'button', className: 'btn btn-sm', onClick: () => { state.selectedHymn = null; renderStudyPane(); } }, '◀ 찬송가 목록'),
          el('a', { className: 'btn btn-sm btn-primary', href: sh.pptViewUrl, target: '_blank', rel: 'noopener noreferrer', style: 'text-decoration:none;' }, '🔗 새 창에서 큰 화면으로 열기 ↗'),
          el('button', { type: 'button', className: 'btn btn-sm btn-soft', onClick: () => loadChapter(sh.ref.osis, sh.ref.ch, sh.ref.vs) }, `📖 관련 말씀 (${sh.ref.label})`),
          el('button', { type: 'button', className: 'btn btn-sm', onClick: () => clipToSermon(`새찬송가 ${sh.num}장`, `${sh.title} (${sh.section || sh.category})`) }, '✍️ 설교 노트에 담기')
        )
      );
      body.appendChild(
        el('div', { className: 'card', style: 'padding:14px;' },
          el('div', { style: 'display:flex;align-items:center;gap:8px;margin-bottom:10px;flex-wrap:wrap;' },
            el('span', { className: 'tag tag-accent' }, `새찬송가 ${sh.num}장`),
            el('span', { className: 'tag' }, sh.section || sh.category),
            el('strong', { style: 'font-size:19px;' }, sh.title)
          ),
          el('iframe', {
            src: sh.pptPreviewUrl,
            style: 'width:100%;height:500px;border:1.5px solid var(--border);border-radius:12px;background:#111;',
            allow: 'autoplay; fullscreen',
            title: `새찬송가 ${sh.num}장 악보·가사 PPT`,
          })
        )
      );
      return;
    }
    const HYMN_RANGES = [
      { key: 'FEATURED', label: '대표 100곡' },
      { key: '1-100', label: '1~100장' },
      { key: '101-200', label: '101~200장' },
      { key: '201-300', label: '201~300장' },
      { key: '301-400', label: '301~400장' },
      { key: '401-500', label: '401~500장' },
      { key: '501-600', label: '501~600장' },
      { key: '601-645', label: '601~645장' },
      { key: 'ALL', label: '전체 645장' },
    ];
    const hiddenFileInput = el('input', {
      type: 'file',
      accept: '.txt,.json',
      style: 'display:none;',
      onChange: async (e) => {
        const file = e.target.files?.[0];
        if (!file) return;
        try {
          const text = await file.text();
          const parsed = parseCustomHymnFile(text);
          const count = await sermonStore.saveCustomHymnLyrics(parsed);
          state.customHymnLyrics = await sermonStore.getCustomHymnLyricsMap();
          showToast(`내 찬송가 가사 ${count}곡을 PC에 안전하게 저장했습니다.`);
          renderStudyPane();
        } catch (err) {
          showToast(`찬송가 파일 불러오기 오류: ${err.message}`);
        }
      },
    });
    body.appendChild(hiddenFileInput);

    body.appendChild(
      el(
        'div',
        { className: 'range-pills' },
        ...HYMN_RANGES.map((r) =>
          el(
            'button',
            {
              type: 'button',
              className: `btn btn-sm ${state.hymnRange === r.key ? 'btn-primary' : ''}`,
              onClick: () => { state.hymnRange = r.key; renderStudyPane(); },
            },
            r.label
          )
        ),
        el('button', {
          type: 'button',
          className: 'btn btn-sm btn-soft',
          onClick: () => hiddenFileInput.click(),
        }, `📂 내 찬송가 가사 추가 (${Object.keys(state.customHymnLyrics).length}곡)`)
      )
    );

    const allHymns = service.getHymns();
    const hymns = allHymns.filter((h) => {
      const groupOk = state.worshipGroup === '전체' || h.category === state.worshipGroup;
      if (!groupOk) return 0 === 1;
      if (q) {
        return String(h.num) === q || (h.old && String(h.old) === q) || h.title.includes(q) || h.category.includes(q) || (h.section && h.section.includes(q));
      }
      if (state.hymnRange === 'FEATURED') return Boolean(h.featured);
      if (state.hymnRange === 'ALL') return true;
      const [lo, hi] = state.hymnRange.split('-').map(Number);
      return h.num >= lo && h.num <= hi;
    });

    body.appendChild(
      el('p', { style: 'font-size:14.5px;color:var(--text-muted);margin-bottom:10px;font-weight:700;' },
        `21세기 새찬송가 총 ${allHymns.length}장 중 ${hymns.length}곡 표시 (번호나 제목을 입력하면 645장 전체에서 즉시 찾습니다)`
      )
    );

    for (const h of hymns) {
      const lyrics = state.customHymnLyrics[h.num] || '';
      const isExpanded = state.expandedHymnNum === h.num;
      body.appendChild(
        el(
          'div',
          { className: 'card', style: 'padding:14px 18px;' },
          el(
            'div',
            { style: 'display:flex;align-items:center;gap:8px;flex-wrap:wrap;' },
            el('span', { className: 'tag tag-accent', style: 'font-size:15px;' }, `새찬송가 ${h.num}장`),
            h.old ? el('span', { className: 'tag' }, `구 ${h.old}장`) : null,
            el('span', { className: 'tag' }, h.section || h.category),
            lyrics ? el('span', { className: 'tag', style: 'background:#dcfce7;color:#166534;' }, '내 가사 있음') : null,
            el('strong', { style: 'font-size:18px;width:100%;margin-top:4px;' }, h.title),
            isExpanded && lyrics
              ? el('div', { style: 'width:100%;margin-top:10px;padding:12px 14px;background:var(--surface-soft);border-radius:10px;white-space:pre-wrap;font-size:17px;line-height:1.8;' }, lyrics)
              : null,
            el(
              'div',
              { style: 'display:flex;gap:8px;margin-top:8px;flex-wrap:wrap;' },
              h.pptPreviewUrl
                ? el('button', { type: 'button', className: 'btn btn-sm btn-primary', onClick: () => { state.selectedHymn = h; renderStudyPane(); } }, '🎞️ 악보·가사 PPT 바로 보기')
                : null,
              h.pptViewUrl
                ? el('a', { className: 'btn btn-sm', href: h.pptViewUrl, target: '_blank', rel: 'noopener noreferrer', style: 'text-decoration:none;' }, '🔗 새 창 PPT ↗')
                : null,
              el('button', { type: 'button', className: 'btn btn-sm btn-soft', onClick: () => loadChapter(h.ref.osis, h.ref.ch, h.ref.vs) }, `📖 관련 말씀 (${h.ref.label}) 열기`),
              lyrics
                ? el('button', { type: 'button', className: 'btn btn-sm btn-primary', onClick: () => { state.expandedHymnNum = isExpanded ? null : h.num; renderStudyPane(); } }, isExpanded ? '가사 접기' : '🎵 내 가사 보기')
                : null,
              lyrics
                ? el('button', { type: 'button', className: 'btn btn-sm btn-accent', onClick: () => {
                    const stanzas = lyrics.split(/\n\s*\n/).filter(Boolean);
                    state.customPulpitSlides = stanzas.map((st, idx) => ({
                      section: `새찬송가 ${h.num}장 (${idx + 1}/${stanzas.length})`,
                      title: `${h.num}장. ${h.title}`,
                      body: st,
                    }));
                    openPulpitMode();
                  } }, '🎤 강단 큰 화면')
                : null,
              el('button', { type: 'button', className: 'btn btn-sm', onClick: () => clipToSermon(`새찬송가 ${h.num}장`, `${h.title}${h.old ? ` (구 ${h.old}장)` : ''} · ${h.section || h.category}`) }, '✍️ 설교 노트에 담기')
            )
          )
        )
      );
    }
    return;
  }

  // 교독문 상세 보기 (Google Drive 내 PPT 슬라이드 바로 보기 + 개역한글 큰 글씨 텍스트 교독)
  if (state.selectedResponsive) {
    const rr = state.selectedResponsive;
    const hasPpt = Boolean(rr.pptPreviewUrl);
    const hasScripture = Boolean(rr.osis && rr.ch);
    const activeMode = (state.rrViewMode === 'ppt' && hasPpt) ? 'ppt' : (hasScripture ? 'text' : 'ppt');
    const verses = hasScripture
      ? (await service.getChapterVerses(rr.osis, rr.ch)).filter((v) => v.verse >= rr.start_vs && v.verse <= rr.end_vs)
      : [];

    body.appendChild(
      el(
        'div',
        { className: 'no-print', style: 'display:flex;gap:8px;margin-bottom:12px;flex-wrap:wrap;' },
        el('button', { type: 'button', className: 'btn btn-sm', onClick: () => { state.selectedResponsive = null; state.selectedHymn = null; renderStudyPane(); } }, '◀ 교독문 목록'),
        hasPpt
          ? el('button', { type: 'button', className: `btn btn-sm ${activeMode === 'ppt' ? 'btn-primary' : ''}`, onClick: () => { state.rrViewMode = 'ppt'; renderStudyPane(); } }, '🎞️ 내 PPT 슬라이드 보기')
          : null,
        hasScripture
          ? el('button', { type: 'button', className: `btn btn-sm ${activeMode === 'text' ? 'btn-primary' : ''}`, onClick: () => { state.rrViewMode = 'text'; renderStudyPane(); } }, '📖 큰 글씨 텍스트 교독')
          : null,
        hasPpt
          ? el('a', { className: 'btn btn-sm btn-soft', href: rr.pptViewUrl, target: '_blank', rel: 'noopener noreferrer', style: 'text-decoration:none;' }, '🔗 새 창에서 PPT 열기 ↗')
          : null,
        hasScripture
          ? el('button', { type: 'button', className: 'btn btn-sm btn-soft', onClick: () => loadChapter(rr.osis, rr.ch, rr.start_vs) }, '📖 왼쪽에 성경 열기')
          : null,
        hasScripture
          ? el('button', { type: 'button', className: 'btn btn-sm btn-accent', onClick: () => {
              state.customPulpitSlides = [
                { section: `교독문 ${rr.num}번`, title: rr.title, body: `${rr.season} · 사회자와 회중이 번갈아 읽습니다` },
                ...verses.map((v, i) => ({
                  section: i === verses.length - 1 ? '다같이' : (i % 2 === 0 ? '사회자' : '회중'),
                  title: i === verses.length - 1 ? '[다같이]' : (i % 2 === 0 ? '[사회자]' : '[회중]'),
                  body: v.text,
                })),
              ];
              openPulpitMode();
            } }, '🎤 강단 큰 화면 교독')
          : null
      )
    );

    if (activeMode === 'ppt' && hasPpt) {
      body.appendChild(
        el(
          'div',
          { className: 'card', style: 'padding:14px;' },
          el('div', { style: 'display:flex;align-items:center;gap:8px;margin-bottom:10px;flex-wrap:wrap;' },
            el('span', { className: 'tag tag-accent' }, `교독문 ${rr.num}번 · ${rr.season}`),
            el('strong', { style: 'font-size:19px;' }, rr.title)
          ),
          el('iframe', {
            src: rr.pptPreviewUrl,
            style: 'width:100%;height:480px;border:1.5px solid var(--border);border-radius:12px;background:#111;',
            allow: 'autoplay; fullscreen',
            title: `교독문 ${rr.num}번 PPT 슬라이드`,
          }),
          el('p', { style: 'font-size:13.5px;color:var(--text-muted);margin-top:8px;' }, '💡 Google Drive에 저장된 원본 교독문 PPT 슬라이드를 바로 띄웠습니다. 오른쪽 위 전체화면 아이콘이나 [새 창에서 PPT 열기]로 크게 보실 수 있습니다.')
        )
      );
      return;
    }

    const card = el('div', { className: 'card' },
      el('div', { style: 'display:flex;align-items:center;justify-content:space-between;gap:8px;margin-bottom:8px;flex-wrap:wrap;' },
        el('span', { className: 'tag tag-accent' }, `교독문 ${rr.num}번 · ${rr.season}`),
        el('button', { type: 'button', className: 'btn btn-sm no-print', onClick: () => window.print() }, '🖨️ 큰 글씨 인쇄')
      ),
      el('h3', { style: 'font-size:21px;' }, rr.title)
    );
    verses.forEach((v, idx) => {
      const isLast = idx === verses.length - 1;
      const role = isLast ? '다같이' : (idx % 2 === 0 ? '사회자' : '회중');
      const roleColor = isLast ? 'var(--accent)' : (idx % 2 === 0 ? 'var(--primary)' : 'var(--emerald)');
      card.appendChild(
        el(
          'div',
          { style: 'padding:12px 0;border-top:1px solid var(--border);' },
          el('strong', { style: `display:inline-block;min-width:64px;color:${roleColor};font-size:16px;` }, `[${role}]`),
          el('span', { style: 'font-family:"Noto Serif KR",serif;font-size:19px;line-height:1.85;' }, ` ${v.text}`)
        )
      );
    });
    body.appendChild(card);
    return;
  }

  const RR_RANGES = [
    { key: 'ALL', label: '전체 137편' },
    { key: '1-50', label: '1~50번' },
    { key: '51-100', label: '51~100번' },
    { key: '101-137', label: '101~137번 (절기·예식)' },
  ];
  body.appendChild(
    el('div', { className: 'range-pills' },
      ...RR_RANGES.map((r) =>
        el('button', {
          type: 'button',
          className: `btn btn-sm ${state.rrRange === r.key ? 'btn-primary' : ''}`,
          onClick: () => { state.rrRange = r.key; renderStudyPane(); },
        }, r.label)
      )
    )
  );

  const list = service.getResponsiveReadings().filter((r) => {
    const grpOk = state.worshipGroup === '전체' || r.group === state.worshipGroup;
    if (!grpOk) return 0 === 1;
    if (q) return String(r.num) === q || r.title.includes(q) || r.season.includes(q);
    if (state.rrRange === 'ALL') return true;
    const [lo, hi] = state.rrRange.split('-').map(Number);
    return r.num >= lo && r.num <= hi;
  });
  body.appendChild(el('p', { style: 'font-size:14.5px;color:var(--text-muted);margin-bottom:10px;font-weight:700;' }, `21세기 새교독문 총 137편 중 ${list.length}편 표시 (누르면 Google Drive PPT 슬라이드와 큰 글씨 교독문이 바로 열립니다)`));
  for (const rr of list) {
    body.appendChild(
      el(
        'div',
        {
          className: 'card',
          style: 'padding:14px 18px;cursor:pointer;',
          onClick: () => { state.selectedResponsive = rr; state.rrViewMode = rr.pptPreviewUrl ? 'ppt' : 'text'; renderStudyPane(); },
        },
        el(
          'div',
          { style: 'display:flex;align-items:center;gap:8px;flex-wrap:wrap;' },
          el('span', { className: 'tag tag-accent', style: 'font-size:15px;' }, `교독문 ${rr.num}번`),
          el('span', { className: 'tag' }, rr.season),
          rr.pptPreviewUrl ? el('span', { className: 'tag', style: 'background:#dbeafe;color:#1e40af;' }, '🎞️ PPT 슬라이드') : null,
          el('strong', { style: 'font-size:17.5px;width:100%;margin-top:4px;' }, rr.title)
        )
      )
    );
  }
}

function renderCrossRefTab(body) {
  const v = getCurrentVerseObj();
  const refs = v ? service.getCrossReferencesForVerse(v.verseId) : [];

  body.appendChild(el('h3', { style: 'font-size:19px;margin-bottom:12px;color:var(--primary);' }, `함께 읽으면 좋은 연결 말씀 (${v ? `${v.bookName} ${v.chapter}:${v.verse}` : ''})`));
  if (!refs.length) {
    body.appendChild(el('div', { className: 'card' }, el('p', {}, '이 절에 연결된 말씀이 아직 없습니다. 창세기 22:2, 시편 23:1, 요한복음 3:16을 열어보세요.')));
  } else {
    for (const r of refs) {
      const refLabel = `${r.to_book_name} ${r.to_chapter}:${r.to_verse}`;
      body.appendChild(
        el(
          'div',
          { className: 'card' },
          el(
            'div',
            { style: 'display:flex;align-items:center;gap:8px;margin-bottom:10px;flex-wrap:wrap;' },
            el('button', { type: 'button', className: 'btn btn-sm btn-primary', onClick: () => loadChapter(r.to_osis, r.to_chapter, r.to_verse) }, `${refLabel} 바로 가기`),
            el('span', { className: 'tag' }, REL_LABELS[r.relationship_type] || '연결 말씀'),
            el('button', { type: 'button', className: 'btn btn-sm', style: 'margin-left:auto;', onClick: () => clipToSermon(refLabel, r.to_text || '') }, '✍️ 노트에 담기')
          ),
          el('p', { style: 'font-family:"Noto Serif KR",serif;font-size:18px;' }, r.to_text || ''),
          r.note ? el('div', { className: 'callout' }, r.note) : null
        )
      );
    }
  }

  body.appendChild(el('h3', { style: 'font-size:19px;margin:20px 0 12px;color:var(--primary);' }, '성경 인물 흐름 한눈에 보기 (연쇄 관주)'));
  for (const chain of service.getChains()) {
    const card = el(
      'div',
      { className: 'card' },
      el('h3', {}, chain.title),
      el('p', { style: 'font-weight:700;color:var(--accent);margin-bottom:8px;' }, chain.meaning),
      el('p', { style: 'font-size:15.5px;color:var(--text-secondary);margin-bottom:12px;' }, chain.summary)
    );
    for (const link of chain.links) {
      card.appendChild(
        el(
          'div',
          { style: 'padding:12px 0;border-top:1px solid var(--border);' },
          el(
            'div',
            { style: 'display:flex;align-items:center;gap:8px;margin-bottom:6px;flex-wrap:wrap;' },
            el('button', { type: 'button', className: 'btn btn-sm btn-soft', onClick: () => loadChapter(link.osis_code, link.chapter, link.verse) }, link.passage_display),
            el('span', { className: 'tag tag-accent' }, link.stage_label),
            el('button', { type: 'button', className: 'btn btn-sm', style: 'margin-left:auto;', onClick: () => clipToSermon(link.passage_display, `${link.verse_text || ''}\n${link.sermon_point}`) }, '+ 담기')
          ),
          link.verse_text ? el('p', { style: 'font-family:"Noto Serif KR",serif;font-size:16.5px;margin-bottom:4px;' }, link.verse_text) : null,
          el('p', { style: 'font-size:14.5px;color:var(--accent);font-weight:600;' }, `• ${link.sermon_point}`)
        )
      );
    }
    body.appendChild(card);
  }
}

function renderStrongsTab(body) {
  body.appendChild(el('h3', { style: 'font-size:19px;margin-bottom:12px;color:var(--primary);' }, '원어(히브리어 · 헬라어) 쉽게 풀기'));
  for (const s of service.getStrongs()) {
    body.appendChild(
      el(
        'div',
        { className: 'card' },
        el(
          'div',
          { style: 'display:flex;align-items:center;gap:10px;margin-bottom:8px;flex-wrap:wrap;' },
          el('span', { className: 'tag tag-accent' }, s.strong_id),
          el('strong', { style: 'font-size:24px;' }, s.lemma),
          el('span', { style: 'font-size:17px;font-weight:700;color:var(--primary);' }, `발음: ${s.pronunciation}`),
          el('span', { className: 'tag', style: 'margin-left:auto;' }, s.part_of_speech)
        ),
        el('p', { style: 'font-weight:600;' }, s.definition_kr),
        el('p', { style: 'font-size:14.5px;color:var(--text-muted);margin-top:6px;' }, `성경 전체에 ${s.occurrence_count}번 나오는 단어입니다.`)
      )
    );
  }
}

function renderSermonStudioTab(body) {
  const sermon = getActiveSermon();
  if (!sermon) return;

  const selector = el(
    'select',
    {
      className: 'input-lg',
      style: 'flex:1;',
      onChange: (e) => { state.activeSermonId = e.target.value; renderStudyPane(); },
    },
    ...state.sermons.map((s) => el('option', { value: s.id, selected: s.id === sermon.id ? '' : null }, `${s.date} · ${s.title}`))
  );

  body.appendChild(
    el(
      'div',
      { className: 'no-print', style: 'display:flex;gap:8px;margin-bottom:12px;flex-wrap:wrap;' },
      selector,
      el(
        'button',
        {
          type: 'button',
          className: 'btn btn-primary',
          onClick: async () => {
            const fresh = createDefaultSermon();
            fresh.title = '새 설교 노트';
            fresh.outline = [{ id: `sec_${Date.now()}`, section: '서론', title: '말씀 시작', content: '' }];
            await sermonStore.saveSermon(fresh);
            state.sermons = await sermonStore.listSermons();
            state.activeSermonId = fresh.id;
            renderStudyPane();
            showToast('새 설교 노트를 만들었습니다.');
          },
        },
        '+ 새 설교 쓰기'
      )
    )
  );

  body.appendChild(
    el(
      'div',
      { className: 'no-print', style: 'display:flex;gap:8px;margin-bottom:14px;flex-wrap:wrap;' },
      el('button', { type: 'button', className: 'btn btn-sm', onClick: () => window.print() }, '🖨️ 큰 글씨 인쇄'),
      el('button', { type: 'button', className: 'btn btn-sm', onClick: () => downloadText(`${sermon.date}_${sermon.title}.txt`, SermonArchiveStore.toMarkdown(sermon), 'text/plain') }, '💾 파일로 보관'),
      el('button', { type: 'button', className: 'btn btn-sm btn-accent', style: 'margin-left:auto;', onClick: openPulpitMode }, '🎤 강단 큰 화면으로 보기')
    )
  );

  body.appendChild(
    el(
      'div',
      { className: 'card' },
      el('label', { className: 'field-label' }, '설교 제목'),
      el('input', {
        className: 'input-lg',
        style: 'margin-bottom:12px;font-weight:700;',
        value: sermon.title,
        onInput: (e) => { sermon.title = e.target.value; sermonStore.saveSermon(sermon); },
      }),
      el('label', { className: 'field-label' }, '설교 본문'),
      el('input', {
        className: 'input-lg',
        value: sermon.scriptureRef,
        onInput: (e) => { sermon.scriptureRef = e.target.value; sermonStore.saveSermon(sermon); },
      })
    )
  );

  sermon.outline.forEach((item, idx) => {
    body.appendChild(
      el(
        'div',
        { className: 'card' },
        el(
          'div',
          { style: 'display:flex;gap:8px;margin-bottom:10px;align-items:center;' },
          el('input', {
            className: 'input-lg',
            style: 'max-width:110px;font-weight:800;',
            value: item.section,
            onInput: (e) => { item.section = e.target.value; sermonStore.saveSermon(sermon); },
          }),
          el('input', {
            className: 'input-lg',
            style: 'flex:1;font-weight:700;',
            value: item.title,
            placeholder: '대지 제목을 적으세요',
            onInput: (e) => { item.title = e.target.value; sermonStore.saveSermon(sermon); },
          }),
          el(
            'button',
            {
              type: 'button',
              className: 'btn btn-sm no-print',
              onClick: () => {
                if (sermon.outline.length <= 1) return;
                sermon.outline.splice(idx, 1);
                sermonStore.saveSermon(sermon);
                renderStudyPane();
              },
            },
            '삭제'
          )
        ),
        el('textarea', {
          className: 'input-lg',
          placeholder: '설교 내용을 편하게 적으세요…',
          onInput: (e) => { item.content = e.target.value; sermonStore.saveSermon(sermon); },
        }, item.content)
      )
    );
  });

  body.appendChild(
    el(
      'button',
      {
        type: 'button',
        className: 'btn btn-soft no-print',
        style: 'width:100%;margin-bottom:14px;',
        onClick: () => {
          sermon.outline.push({ id: `sec_${Date.now()}`, section: `본론 ${sermon.outline.length}`, title: '', content: '' });
          sermonStore.saveSermon(sermon);
          renderStudyPane();
        },
      },
      '+ 설교 대지 한 칸 더 추가하기'
    )
  );

  if (sermon.clips && sermon.clips.length) {
    const tray = el('div', { className: 'card' }, el('h3', {}, `담아둔 말씀 · 주석 · 찬송 (${sermon.clips.length}건)`));
    for (const c of sermon.clips) {
      tray.appendChild(
        el(
          'div',
          { style: 'padding:10px 0;border-top:1px solid var(--border);font-size:15.5px;line-height:1.65;' },
          el('strong', { style: 'color:var(--primary);' }, `[${c.source}] `),
          c.text
        )
      );
    }
    body.appendChild(tray);
  }
}

async function clipToSermon(source, text) {
  const sermon = getActiveSermon();
  if (!sermon) return;
  sermon.clips = sermon.clips || [];
  sermon.clips.unshift({ id: `clip_${Date.now()}`, source, text, clippedAt: new Date().toISOString() });
  await sermonStore.saveSermon(sermon);
  showToast(`'${source}' 내용을 설교 노트에 담았습니다.`);
  if (state.studyTab === 'studio') renderStudyPane();
}

function downloadText(filename, content, mimeType) {
  const blob = new Blob([content], { type: `${mimeType};charset=utf-8` });
  const url = URL.createObjectURL(blob);
  const a = el('a', { href: url, download: filename });
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

/* ---------- 쉬운 성경 66권 · 장 고르기 모달 ---------- */
function openPickerModal() {
  state.pickerBook = null;
  document.getElementById('pickerModal').classList.add('open');
  renderPickerStep();
}

function closePickerModal() {
  document.getElementById('pickerModal').classList.remove('open');
}

function renderPickerStep() {
  const grid = document.getElementById('pickerGrid');
  const title = document.getElementById('pickerTitle');
  const backBtn = document.getElementById('btnBackToBooks');
  grid.replaceChildren();

  document.querySelectorAll('[data-picker-test]').forEach((b) => {
    b.className = `btn ${b.dataset.pickerTest === state.pickerTestament ? 'btn-primary' : ''}`;
  });

  if (!state.pickerBook) {
    title.textContent = '1단계: 읽으실 성경을 눌러주세요';
    backBtn.style.display = 'none';
    const wrap = el('div', { className: 'book-grid' });
    const books = service.getBooks().filter((b) => b.testament === state.pickerTestament);
    for (const b of books) {
      wrap.appendChild(
        el(
          'button',
          {
            type: 'button',
            className: `book-tile ${b.id === state.osis ? 'active' : ''}`,
            onClick: () => { state.pickerBook = b; renderPickerStep(); },
          },
          b.name
        )
      );
    }
    grid.appendChild(wrap);
  } else {
    const b = state.pickerBook;
    title.textContent = `2단계: ${b.name} 몇 장을 읽으실까요?`;
    backBtn.style.display = 'inline-flex';
    const wrap = el('div', { className: 'chap-grid' });
    for (let ch = 1; ch <= b.totalChapters; ch++) {
      wrap.appendChild(
        el(
          'button',
          {
            type: 'button',
            className: `chap-tile ${b.id === state.osis && ch === state.chapter ? 'active' : ''}`,
            onClick: () => { closePickerModal(); loadChapter(b.id, ch, 1); },
          },
          `${ch}장`
        )
      );
    }
    grid.appendChild(wrap);
  }
}

function renderBookmarksView() {
  const body = document.getElementById('studyBody');
  body.replaceChildren();
  const items = Object.values(state.highlights);
  body.appendChild(el('h3', { style: 'font-size:19px;margin-bottom:12px;color:var(--primary);' }, `📌 내가 표시한 말씀 (${items.length}구절)`));
  if (!items.length) {
    body.appendChild(el('div', { className: 'card' }, el('p', {}, '아직 형광펜으로 표시한 말씀이 없습니다. 성경 구절을 누르고 노랑·초록·분홍 밑줄 버튼을 눌러보세요.')));
    return;
  }
  for (const item of items) {
    body.appendChild(
      el(
        'div',
        { className: 'card' },
        el(
          'div',
          { style: 'display:flex;align-items:center;justify-content:space-between;margin-bottom:8px;' },
          el('strong', { style: 'font-size:17px;color:var(--primary);' }, `${item.bookName} ${item.chapter}:${item.verse}`),
          el('button', { type: 'button', className: 'btn btn-sm btn-primary', onClick: () => loadChapter(item.osis, item.chapter, item.verse) }, '이 말씀 열기')
        ),
        el('p', { style: 'font-family:"Noto Serif KR",serif;' }, item.text)
      )
    );
  }
}

async function runSearch() {
  const q = document.getElementById('searchInput').value.trim();
  if (!q) {
    showToast('찾으실 말씀이나 성경 이름을 입력해 주세요.');
    return;
  }

  const m = q.match(/^([가-힣a-zA-Z0-9]+)\s*(\d+)(?:[:장\s]+(\d+))?/);
  if (m) {
    const [, rawBook, chStr, vsStr] = m;
    const book = service.getBooks().find((b) => b.name === rawBook || b.abbr === rawBook);
    if (book) {
      const ch = Math.max(1, Math.min(book.totalChapters, Number(chStr)));
      const vs = vsStr ? Math.max(1, Number(vsStr)) : 1;
      await loadChapter(book.id, ch, vs);
      showToast(`${book.name} ${ch}장 ${vs}절로 이동했습니다.`);
      return;
    }
  }

  const body = document.getElementById('studyBody');
  body.replaceChildren(el('p', { style: 'padding:20px;font-size:17px;' }, `'${q}' 말씀을 성경 전체에서 찾고 있습니다…`));
  const hits = await service.searchKoreanText(q, null, 25);
  body.replaceChildren(el('h3', { style: 'font-size:19px;margin-bottom:12px;color:var(--primary);' }, `'${q}' 찾은 말씀 (${hits.length}곳)`));
  if (!hits.length) {
    body.appendChild(el('div', { className: 'card' }, el('p', {}, '일치하는 말씀을 찾지 못했습니다. 다른 단어로 다시 찾아보세요.')));
    return;
  }
  for (const h of hits) {
    body.appendChild(
      el(
        'div',
        { className: 'card', style: 'cursor:pointer;', onClick: () => loadChapter(h.osis, h.chapter, h.verse) },
        el('h3', {}, `${h.bookName} ${h.chapter}장 ${h.verse}절`),
        el('p', { style: 'font-family:"Noto Serif KR",serif;' }, h.text)
      )
    );
  }
}

/* ---------- 강단 큰 화면 모드 ---------- */
function buildPulpitSlides() {
  if (state.customPulpitSlides) return state.customPulpitSlides;
  const sermon = getActiveSermon();
  if (!sermon) return [];
  return [
    { section: '설교 제목', title: sermon.title, body: `${sermon.scriptureRef}\n\n${sermon.date}` },
    ...sermon.outline.map((o) => ({ section: o.section, title: o.title || o.section, body: o.content || '' })),
  ];
}

async function openPulpitMode() {
  state.pulpit.open = true;
  state.pulpit.paused = false;
  state.pulpit.slideIndex = 0;
  state.pulpit.remainingSec = (getActiveSermon()?.targetDurationMins || 30) * 60;
  document.getElementById('btnTimerToggle').textContent = '일시정지';
  document.getElementById('pulpitOverlay').classList.add('open');
  renderPulpitSlide();
  startPulpitTimer();
  try {
    if ('wakeLock' in navigator) state.pulpit.wakeLock = await navigator.wakeLock.request('screen');
  } catch {
    // Optional capability
  }
}

function closePulpitMode() {
  state.pulpit.open = false;
  state.customPulpitSlides = null;
  document.getElementById('pulpitOverlay').classList.remove('open');
  clearInterval(state.pulpit.timerId);
  if (state.pulpit.wakeLock) {
    state.pulpit.wakeLock.release().catch(() => {});
    state.pulpit.wakeLock = null;
  }
}

function renderPulpitSlide() {
  const slides = buildPulpitSlides();
  if (!slides.length) return;
  const idx = Math.max(0, Math.min(state.pulpit.slideIndex, slides.length - 1));
  state.pulpit.slideIndex = idx;
  const s = slides[idx];
  document.getElementById('pulpitProgress').textContent = `${idx + 1} / ${slides.length} · ${s.section}`;
  const titleEl = document.getElementById('pulpitTitle');
  const bodyEl = document.getElementById('pulpitBody');
  titleEl.textContent = s.title;
  titleEl.style.fontSize = `${state.pulpit.fontSizePt + 6}pt`;
  bodyEl.textContent = s.body;
  bodyEl.style.fontSize = `${state.pulpit.fontSizePt}pt`;
}

function startPulpitTimer() {
  clearInterval(state.pulpit.timerId);
  const update = () => {
    const mins = String(Math.floor(state.pulpit.remainingSec / 60)).padStart(2, '0');
    const secs = String(state.pulpit.remainingSec % 60).padStart(2, '0');
    const elTimer = document.getElementById('pulpitTimer');
    elTimer.textContent = `${mins}:${secs}`;
    elTimer.style.color = state.pulpit.remainingSec < 300 ? '#f87171' : '#fbbf24';
  };
  update();
  state.pulpit.timerId = setInterval(() => {
    if (!state.pulpit.paused && state.pulpit.remainingSec > 0) state.pulpit.remainingSec--;
    update();
  }, 1000);
}

function applyFontStep() {
  const step = FONT_STEPS[state.fontStepIndex];
  document.documentElement.style.setProperty('--scripture-size', `${step.px}px`);
  document.getElementById('fontSizeLabel').textContent = step.label;
}

function renderCustomBibleList() {
  const listEl = document.getElementById('customBibleList');
  if (!listEl) return;
  listEl.replaceChildren();
  if (!state.customBibles.length) {
    listEl.appendChild(el('p', { style: 'color:var(--text-muted);' }, '아직 불러온 개인 성경 파일이 없습니다. 위에서 개역개정(.txt 또는 .json) 파일을 선택해 추가해 보세요.'));
    return;
  }
  for (const cb of state.customBibles) {
    listEl.appendChild(
      el('div', { style: 'display:flex;align-items:center;justify-content:space-between;gap:10px;padding:10px 0;border-bottom:1px solid var(--border);flex-wrap:wrap;' },
        el('div', {},
          el('strong', { style: 'font-size:17px;' }, cb.name),
          el('div', { style: 'font-size:13.5px;color:var(--text-muted);' }, `${cb.bookCount}권 · ${cb.verseCount.toLocaleString()}절 저장됨`)
        ),
        el('div', { style: 'display:flex;gap:6px;' },
          el('button', {
            type: 'button',
            className: 'btn btn-sm btn-primary',
            onClick: () => {
              state.primaryVersion = cb.id;
              populateVersionSelectors();
              document.getElementById('bibleImportModal').classList.remove('open');
              loadChapter(state.osis, state.chapter, state.verse);
            },
          }, '주 역본으로 읽기'),
          el('button', {
            type: 'button',
            className: 'btn btn-sm',
            onClick: async () => {
              await sermonStore.deleteCustomBible(cb.id);
              state.customBibles = await sermonStore.listCustomBibles();
              if (state.primaryVersion === cb.id) state.primaryVersion = 'krv';
              if (state.parallelVersion === cb.id) state.parallelVersion = 'none';
              populateVersionSelectors();
              renderCustomBibleList();
              loadChapter(state.osis, state.chapter, state.verse);
              showToast('저장된 개인 역본을 삭제했습니다.');
            },
          }, '삭제')
        )
      )
    );
  }
}

async function initApp() {
  try {
    await service.init();
    state.sermons = await sermonStore.listSermons();
    state.activeSermonId = state.sermons[0]?.id || null;
    state.customBibles = await sermonStore.listCustomBibles();
    state.customHymnLyrics = await sermonStore.getCustomHymnLyricsMap();
    populateVersionSelectors();
    applyFontStep();

    document.getElementById('primaryVersionSelect')?.addEventListener('change', (e) => {
      state.primaryVersion = e.target.value;
      loadChapter(state.osis, state.chapter, state.verse);
    });
    document.getElementById('parallelVersionSelect')?.addEventListener('change', (e) => {
      state.parallelVersion = e.target.value;
      loadChapter(state.osis, state.chapter, state.verse);
    });
    document.getElementById('btnBibleImport')?.addEventListener('click', () => {
      renderCustomBibleList();
      document.getElementById('bibleImportStatus').textContent = '';
      document.getElementById('bibleImportModal').classList.add('open');
    });
    document.getElementById('btnCloseBibleImport')?.addEventListener('click', () => {
      document.getElementById('bibleImportModal').classList.remove('open');
    });
    document.getElementById('btnDoBibleImport')?.addEventListener('click', async () => {
      const fileInput = document.getElementById('customBibleFileInput');
      const nameInput = document.getElementById('customBibleNameInput');
      const statusEl = document.getElementById('bibleImportStatus');
      const file = fileInput?.files?.[0];
      if (!file) {
        statusEl.textContent = '먼저 성경 파일(.txt 또는 .json)을 선택해 주세요.';
        return;
      }
      statusEl.textContent = '파일을 읽고 분석하는 중입니다…';
      try {
        const raw = await file.text();
        const parsed = parseCustomBibleFile(raw, file.name, nameInput?.value);
        if (!parsed.verseCount) {
          statusEl.textContent = '인식된 성경 절이 없습니다. "창1:1 본문..." 또는 JSON 형식을 확인해 주세요.';
          return;
        }
        await sermonStore.saveCustomBible(parsed);
        state.customBibles = await sermonStore.listCustomBibles();
        state.primaryVersion = parsed.id;
        populateVersionSelectors();
        renderCustomBibleList();
        statusEl.textContent = `✅ "${parsed.name}" (${parsed.bookCount}권 · ${parsed.verseCount.toLocaleString()}절) 저장 완료!`;
        showToast(`${parsed.name} 불러오기 완료!`);
        loadChapter(state.osis, state.chapter, state.verse);
      } catch (err) {
        statusEl.textContent = `오류: ${err.message}`;
      }
    });

    const last = loadJson(LAST_PLACE_KEY, null);
    if (last && last.osis && last.label) {
      const resumeBtn = document.getElementById('btnResume');
      resumeBtn.textContent = `📌 이어 읽기: ${last.label}`;
      resumeBtn.style.display = 'inline-flex';
      resumeBtn.addEventListener('click', () => loadChapter(last.osis, last.chapter, last.verse));
    }

    document.getElementById('btnFontDec').addEventListener('click', () => {
      if (state.fontStepIndex > 0) { state.fontStepIndex--; applyFontStep(); }
    });
    document.getElementById('btnFontInc').addEventListener('click', () => {
      if (state.fontStepIndex < FONT_STEPS.length - 1) { state.fontStepIndex++; applyFontStep(); }
    });

    document.getElementById('btnThemeToggle').addEventListener('click', (e) => {
      state.theme = state.theme === 'light' ? 'dark' : 'light';
      document.documentElement.setAttribute('data-theme', state.theme);
      e.currentTarget.textContent = state.theme === 'light' ? '🌙 어둡게' : '☀️ 밝게(종이)';
    });

    document.getElementById('btnSearch').addEventListener('click', runSearch);
    document.getElementById('searchInput').addEventListener('keydown', (e) => { if (e.key === 'Enter') runSearch(); });

    document.getElementById('btnOpenPicker').addEventListener('click', openPickerModal);
    document.getElementById('btnClosePicker').addEventListener('click', closePickerModal);
    document.getElementById('btnBackToBooks').addEventListener('click', () => { state.pickerBook = null; renderPickerStep(); });
    document.querySelectorAll('[data-picker-test]').forEach((b) => {
      b.addEventListener('click', () => { state.pickerTestament = b.dataset.pickerTest; state.pickerBook = null; renderPickerStep(); });
    });

    document.getElementById('btnHelp').addEventListener('click', () => document.getElementById('helpModal').classList.add('open'));
    document.getElementById('btnCloseHelp').addEventListener('click', () => document.getElementById('helpModal').classList.remove('open'));

    document.getElementById('btnPrevChap').addEventListener('click', () => {
      if (state.chapter > 1) loadChapter(state.osis, state.chapter - 1, 1);
      else showToast('이 성경의 첫 번째 장입니다.');
    });
    document.getElementById('btnNextChap').addEventListener('click', () => {
      const meta = service.getBookMeta(state.osis);
      if (meta && state.chapter < meta.totalChapters) loadChapter(state.osis, state.chapter + 1, 1);
      else showToast('이 성경의 마지막 장입니다.');
    });

    document.getElementById('btnWorshipQuick').addEventListener('click', () => {
      state.studyTab = 'worship';
      renderStudyPane();
    });
    document.getElementById('btnBookmarks').addEventListener('click', renderBookmarksView);

    document.querySelectorAll('[data-study-tab]').forEach((btn) => {
      btn.addEventListener('click', () => { state.studyTab = btn.dataset.studyTab; renderStudyPane(); });
    });

    document.querySelectorAll('[data-mobile-pane]').forEach((btn) => {
      btn.addEventListener('click', () => {
        const target = btn.dataset.mobilePane;
        document.querySelectorAll('.pane').forEach((p) => p.classList.remove('mobile-active'));
        document.getElementById(target)?.classList.add('mobile-active');
        document.querySelectorAll('[data-mobile-pane]').forEach((b) => {
          b.className = `btn ${b === btn ? 'btn-primary' : ''}`;
        });
      });
    });

    const goPrev = () => { if (state.pulpit.slideIndex > 0) { state.pulpit.slideIndex--; renderPulpitSlide(); } };
    const goNext = () => {
      const slides = buildPulpitSlides();
      if (state.pulpit.slideIndex < slides.length - 1) { state.pulpit.slideIndex++; renderPulpitSlide(); }
    };
    document.getElementById('btnPulpitTop').addEventListener('click', openPulpitMode);
    document.getElementById('btnPulpitClose').addEventListener('click', closePulpitMode);
    document.getElementById('pulpitPrevZone').addEventListener('click', goPrev);
    document.getElementById('pulpitNextZone').addEventListener('click', goNext);
    document.getElementById('btnPulpitPrev').addEventListener('click', goPrev);
    document.getElementById('btnPulpitNext').addEventListener('click', goNext);
    document.getElementById('btnPulpitSmaller').addEventListener('click', () => {
      state.pulpit.fontSizePt = Math.max(34, state.pulpit.fontSizePt - 3);
      renderPulpitSlide();
    });
    document.getElementById('btnPulpitBigger').addEventListener('click', () => {
      state.pulpit.fontSizePt = Math.min(58, state.pulpit.fontSizePt + 3);
      renderPulpitSlide();
    });
    document.getElementById('btnTimerToggle').addEventListener('click', (e) => {
      state.pulpit.paused = !state.pulpit.paused;
      e.currentTarget.textContent = state.pulpit.paused ? '다시 시작' : '일시정지';
    });

    if ('serviceWorker' in navigator) navigator.serviceWorker.register('./sw.js').catch(() => {});

    await loadChapter('GEN', 22, 2);
  } catch (err) {
    console.error(err);
    document.getElementById('verseList').textContent = `불러오는 중 문제가 생겼습니다: ${err.message}`;
  }
}

initApp();
