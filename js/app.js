import { BibleDataService } from './bibleService.js';
import { SermonArchiveStore, createDefaultSermon } from './storage.js';

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
  worshipMode: 'hymns', // hymns | responsive
  worshipQuery: '',
  selectedResponsive: null,
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

/* ---------- 성경 장 로딩 & 렌더링 ---------- */
async function loadChapter(osis, ch, targetVerse = 1) {
  state.osis = osis;
  state.chapter = ch;
  const meta = service.getBookMeta(osis);
  document.getElementById('currentPlaceText').textContent = `${meta ? meta.name : osis} ${ch}장`;

  const container = document.getElementById('verseList');
  container.replaceChildren(el('p', { style: 'padding:30px;font-size:18px;text-align:center;' }, '성경 말씀을 불러오고 있습니다…'));

  state.verses = await service.getChapterVerses(osis, ch);
  state.verse = state.verses.some((v) => v.verse === targetVerse) ? targetVerse : 1;

  saveJson(LAST_PLACE_KEY, { osis, chapter: ch, verse: state.verse, label: `${meta ? meta.name : osis} ${ch}장 ${state.verse}절` });
  renderVerses();
  renderStudyPane();
}

function renderVerses() {
  const container = document.getElementById('verseList');
  container.replaceChildren();
  const meta = service.getBookMeta(state.osis);

  container.appendChild(
    el(
      'div',
      { className: 'chapter-heading' },
      el('h1', {}, `${meta ? meta.name : state.osis} ${state.chapter}장`),
      el('span', { className: 'sub' }, `개역한글 · 총 ${state.verses.length}절`)
    )
  );

  for (const v of state.verses) {
    const comms = service.getCommentariesForVerse(v.verseId);
    const refs = service.getCrossReferencesForVerse(v.verseId);
    const isSel = v.verse === state.verse;
    const hl = state.highlights[String(v.verseId)]?.color || '';

    const topRow = el(
      'div',
      { className: 'verse-top' },
      el('span', { className: 'verse-badge-num' }, v.verse),
      comms.length ? el('span', { className: 'tag tag-accent' }, `주석 ${comms.length}종`) : null,
      refs.length ? el('span', { className: 'tag' }, `연결 말씀 ${refs.length}`) : null
    );

    const cardChildren = [topRow, el('p', { className: 'verse-text' }, v.text)];

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
          el('button', { type: 'button', className: 'btn btn-sm', onClick: () => loadChapter('ROM', 8, 28) }, '로마서 8:28')
        )
      )
    );
    return;
  }

  for (const item of filtered) {
    body.appendChild(buildCommentaryCard(item, item.source_code, allSources));
  }
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
      el('button', { type: 'button', className: `btn ${state.worshipMode === 'hymns' ? 'btn-primary' : ''}`, onClick: () => { state.worshipMode = 'hymns'; state.selectedResponsive = null; renderStudyPane(); } }, '🎵 새찬송가 찾기'),
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
        state.selectedResponsive = null;
        renderStudyPane();
      },
    })
  );

  const q = state.worshipQuery.trim();

  if (state.worshipMode === 'hymns') {
    const hymns = service.getHymns().filter((h) =>
      !q || String(h.num) === q || String(h.old) === q || h.title.includes(q) || h.category.includes(q)
    );
    body.appendChild(el('p', { style: 'font-size:14.5px;color:var(--text-muted);margin-bottom:10px;font-weight:700;' }, `검색된 찬송가 ${hymns.length}곡 (번호·주제를 누르면 관련 성경으로 바로 이동합니다)`));
    for (const h of hymns) {
      body.appendChild(
        el(
          'div',
          { className: 'card', style: 'padding:14px 18px;' },
          el(
            'div',
            { style: 'display:flex;align-items:center;gap:10px;flex-wrap:wrap;' },
            el('span', { className: 'tag tag-accent', style: 'font-size:15px;' }, `새찬송가 ${h.num}장`),
            el('span', { className: 'tag' }, `구 ${h.old}장`),
            el('span', { className: 'tag' }, h.category),
            el('strong', { style: 'font-size:18px;width:100%;margin-top:4px;' }, h.title),
            el(
              'div',
              { style: 'display:flex;gap:8px;margin-top:8px;flex-wrap:wrap;' },
              el('button', { type: 'button', className: 'btn btn-sm btn-soft', onClick: () => loadChapter(h.ref.osis, h.ref.ch, h.ref.vs) }, `📖 관련 말씀 (${h.ref.label}) 열기`),
              el('button', { type: 'button', className: 'btn btn-sm', onClick: () => clipToSermon(`새찬송가 ${h.num}장`, `${h.title} (구 ${h.old}장 · ${h.category})`) }, '✍️ 설교 노트에 담기')
            )
          )
        )
      );
    }
    return;
  }

  // 교독문 상세 보기 (개역한글 본문을 사회자 / 회중 / 다같이 형식으로 즉시 생성)
  if (state.selectedResponsive) {
    const rr = state.selectedResponsive;
    const verses = (await service.getChapterVerses(rr.osis, rr.ch))
      .filter((v) => v.verse >= rr.start_vs && v.verse <= rr.end_vs);

    body.appendChild(
      el(
        'div',
        { className: 'no-print', style: 'display:flex;gap:8px;margin-bottom:12px;flex-wrap:wrap;' },
        el('button', { type: 'button', className: 'btn btn-sm', onClick: () => { state.selectedResponsive = null; renderStudyPane(); } }, '◀ 교독문 목록'),
        el('button', { type: 'button', className: 'btn btn-sm btn-soft', onClick: () => loadChapter(rr.osis, rr.ch, rr.start_vs) }, '📖 왼쪽에 본문 열기'),
        el('button', { type: 'button', className: 'btn btn-sm btn-primary', onClick: () => window.print() }, '🖨️ 교독문 큰 글씨 인쇄')
      )
    );

    const card = el('div', { className: 'card' },
      el('div', { style: 'margin-bottom:8px;' }, el('span', { className: 'tag tag-accent' }, `교독문 ${rr.num}번 · ${rr.season}`)),
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

  const list = service.getResponsiveReadings().filter((r) =>
    !q || String(r.num) === q || r.title.includes(q) || r.season.includes(q)
  );
  body.appendChild(el('p', { style: 'font-size:14.5px;color:var(--text-muted);margin-bottom:10px;font-weight:700;' }, `교독문 ${list.length}편 (누르면 사회자·회중 큰 글씨 교독문이 바로 열립니다)`));
  for (const rr of list) {
    body.appendChild(
      el(
        'div',
        {
          className: 'card',
          style: 'padding:14px 18px;cursor:pointer;',
          onClick: () => { state.selectedResponsive = rr; renderStudyPane(); },
        },
        el(
          'div',
          { style: 'display:flex;align-items:center;gap:10px;flex-wrap:wrap;' },
          el('span', { className: 'tag tag-accent', style: 'font-size:15px;' }, `교독문 ${rr.num}번`),
          el('span', { className: 'tag' }, rr.season),
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

async function initApp() {
  try {
    await service.init();
    state.sermons = await sermonStore.listSermons();
    state.activeSermonId = state.sermons[0]?.id || null;
    applyFontStep();

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
