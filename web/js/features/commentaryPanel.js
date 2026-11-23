import { btn, el, iconEl } from '../core/dom.js';
import { buildBibleHubCommentaryUrl, buildTranslateAssistUrl, sanitizeUrl } from '../core/urlSafety.js';
import { LIVE_COMMENTARY_SOURCES } from '../services/bibleService.js';

const FEATURED_PASSAGES = [
  { osis: 'GEN', ch: 22, vs: 2, label: '창세기 22:2' },
  { osis: 'PSA', ch: 23, vs: 1, label: '시편 23:1' },
  { osis: 'ISA', ch: 53, vs: 5, label: '이사야 53:5' },
  { osis: 'MAT', ch: 11, vs: 28, label: '마태복음 11:28' },
  { osis: 'JHN', ch: 3, vs: 16, label: '요한복음 3:16' },
  { osis: 'ROM', ch: 8, vs: 28, label: '로마서 8:28' },
  { osis: 'PHP', ch: 4, vs: 6, label: '빌립보서 4:6' },
  { osis: 'REV', ch: 21, vs: 4, label: '요한계시록 21:4' },
];

export function createCommentaryPanel({ store, service, callbacks }) {
  const { state, guards } = store;

  function buildCommentaryCard(item, sourceCode, allSources) {
    const src = allSources.find((s) => s.source_code === sourceCode);
    const srcName = src?.name_kr || sourceCode;
    if (!item) {
      return el('div', { className: 'card' },
        el('div', { className: 'card-header' }, el('strong', {}, srcName)),
        el('p', {}, '이 절에는 선택하신 주석의 요약 항목이 아직 없습니다.')
      );
    }

    const attribution = item.attributionLabel || '핵심 말씀 참고 요약';
    const safeOfficialUrl = src?.official_url ? sanitizeUrl(src.official_url) : null;
    const clipText = `${item.title}\n${item.content_markdown}${item.practical_points ? `\n적용: ${item.practical_points}` : ''}`;

    return el('article', { className: 'card' },
      el('div', { className: 'card-header' },
        el('strong', {}, srcName),
        el('span', { className: 'tag-provenance' }, attribution),
        btn('btn btn-secondary', () => callbacks.onClip?.(`${srcName} · ${item.passage_display || ''}`, clipText), iconEl('icon-sermon'), '노트에 담기')
      ),
      el('h3', {}, item.title),
      el('p', {}, item.content_markdown),
      item.practical_points ? el('p', { className: 'tag-accent' }, `목회 적용: ${item.practical_points}`) : null,
      safeOfficialUrl
        ? el('div', { className: 'action-row' },
            el('a', { className: 'btn btn-ghost', href: safeOfficialUrl, target: '_blank' }, iconEl('icon-external'), '출처 안내 열기')
          )
        : null
    );
  }

  async function loadOptInLiveCommentary(verseObj) {
    if (!verseObj) return;
    if (typeof navigator !== 'undefined' && navigator.onLine === false) {
      state.liveCommError = '인터넷 연결이 없어 영문 고전 주석을 불러올 수 없습니다.';
      state.liveCommLoading = false;
      callbacks.onRequestRerender?.();
      return;
    }

    const req = guards.liveCommentary.next();
    const targetKey = `${state.liveCommSource}:${verseObj.osis}:${verseObj.chapter}`;
    state.liveCommLoading = true;
    state.liveCommError = '';
    callbacks.onRequestRerender?.();

    try {
      const data = await service.fetchLiveCommentaryChapter(state.liveCommSource, verseObj.osis, verseObj.chapter, req.signal);
      if (!req.isCurrent()) return;
      state.liveCommData = data;
      state.liveCommLoadedKey = targetKey;
      state.liveCommLoading = false;
      state.liveCommError = '';
      callbacks.onRequestRerender?.();
    } catch (err) {
      if (!req.isCurrent() || err?.name === 'AbortError') return;
      state.liveCommLoading = false;
      state.liveCommError = '영문 고전 주석을 불러오지 못했습니다. 잠시 후 다시 시도해 주세요.';
      callbacks.onRequestRerender?.();
    }
  }

  function renderLiveCommentarySection(body, verseObj) {
    const activeSource = LIVE_COMMENTARY_SOURCES.find((s) => s.id === state.liveCommSource) || LIVE_COMMENTARY_SOURCES[0];
    const isLoaded = state.liveCommLoadedKey === `${state.liveCommSource}:${verseObj.osis}:${verseObj.chapter}` && state.liveCommData;

    const selectEl = el('select', {
      className: 'select-field', 'aria-label': '고전 영문 주석 선택',
      onChange: (e) => {
        state.liveCommSource = e.target.value;
        state.liveCommData = null;
        state.liveCommLoadedKey = '';
        state.liveCommError = '';
        callbacks.onRequestRerender?.();
      },
    }, ...LIVE_COMMENTARY_SOURCES.map((s) => el('option', { value: s.id, selected: s.id === state.liveCommSource }, `${s.name} (${s.badge})`)));

    const card = el('section', { className: 'card live-comm-card' },
      el('div', { className: 'card-header' },
        el('strong', {}, '고전 영문 주석 원문'),
        el('span', { className: 'tag-provenance' }, '필요할 때 눌러서 불러오기')
      ),
      el('p', {}, activeSource.desc),
      el('div', { className: 'action-row' },
        selectEl,
        el('button', { type: 'button', className: 'btn btn-primary', disabled: state.liveCommLoading, onClick: () => loadOptInLiveCommentary(verseObj) },
          state.liveCommLoading ? '불러오는 중...' : '주석 불러오기')
      )
    );

    if (state.liveCommError) {
      card.appendChild(el('p', { className: 'empty-state' }, state.liveCommError));
    } else if (isLoaded) {
      const displayText = state.liveCommData.verses?.[verseObj.verse] || state.liveCommData.introduction || '';
      if (!state.liveCommData.available || !displayText) {
        card.appendChild(el('p', { className: 'empty-state' }, '선택하신 고전 주석에는 이 절의 본문이 수록되어 있지 않습니다.'));
      } else {
        card.appendChild(el('p', {}, displayText));
        const translateUrl = buildTranslateAssistUrl(displayText);
        card.appendChild(el('div', { className: 'action-row' },
          translateUrl ? el('a', { className: 'btn btn-secondary', href: translateUrl, target: '_blank' }, iconEl('icon-external'), '구글 번역으로 읽기') : null,
          btn('btn btn-secondary', () => callbacks.onClip?.(`${activeSource.name} · ${verseObj.bookName} ${verseObj.chapter}:${verseObj.verse}`, displayText), iconEl('icon-sermon'), '노트에 담기')
        ));
      }
    }
    body.appendChild(card);
  }

  function render(body, verseObj) {
    if (!verseObj) {
      body.replaceChildren(el('div', { className: 'empty-state' }, '성경 구절을 선택해 주세요.'));
      return;
    }
    const allSources = service.exegesis?.sources || [];
    const entries = service.getCommentariesForVerse(verseObj.verseId);
    const stats = service.getCoverageStats();
    const hasMultiple = entries.length > 1;

    body.appendChild(el('div', { className: 'card-header' },
      el('strong', {}, `${verseObj.bookName} ${verseObj.chapter}:${verseObj.verse} 참고 요약 (${entries.length}건)`),
      el('span', { className: 'tag-provenance' }, `전체 ${stats.coveredVerses}절 제공`)
    ));

    if (hasMultiple) {
      const entryCodes = new Set(entries.map((e) => e.source_code));
      const matchedSources = allSources.filter((s) => entryCodes.has(s.source_code));
      if (state.selectedSource !== 'ALL' && !entryCodes.has(state.selectedSource)) {
        state.selectedSource = 'ALL';
      }

      if (state.compareMode) {
        if (!entryCodes.has(state.compareLeft) && matchedSources[0]) state.compareLeft = matchedSources[0].source_code;
        if (!entryCodes.has(state.compareRight) && matchedSources[1]) state.compareRight = matchedSources[1].source_code;
        const makeSel = (val, label, onCh) => el('select', { className: 'select-field', 'aria-label': label, onChange: (e) => { onCh(e.target.value); callbacks.onRequestRerender?.(); } },
          ...matchedSources.map((s) => el('option', { value: s.source_code, selected: s.source_code === val }, s.name_kr)));
        body.appendChild(el('div', { className: 'action-row' },
          makeSel(state.compareLeft, '첫 번째 주석 선택', (v) => { state.compareLeft = v; }),
          makeSel(state.compareRight, '두 번째 주석 선택', (v) => { state.compareRight = v; }),
          btn('btn btn-primary', () => { state.compareMode = false; callbacks.onRequestRerender?.(); }, '하나씩 크게 보기')
        ));
        body.appendChild(buildCommentaryCard(entries.find((e) => e.source_code === state.compareLeft), state.compareLeft, allSources));
        body.appendChild(buildCommentaryCard(entries.find((e) => e.source_code === state.compareRight), state.compareRight, allSources));
        renderLiveCommentarySection(body, verseObj);
        return;
      }

      const sourceSelect = el('select', {
        className: 'select-field',
        'aria-label': '주석 선택',
        onChange: (e) => {
          state.selectedSource = e.target.value;
          callbacks.onRequestRerender?.();
        },
      },
        el('option', { value: 'ALL', selected: state.selectedSource === 'ALL' }, `주석 선택: 전체 (${entries.length}건)`),
        ...matchedSources.map((s) => el('option', {
          value: s.source_code,
          selected: state.selectedSource === s.source_code,
        }, s.category_kr ? `[${s.category_kr}] ${s.name_kr}` : s.name_kr))
      );
      sourceSelect.value = state.selectedSource;

      body.appendChild(el('div', { className: 'action-row' },
        sourceSelect,
        btn('btn btn-secondary', () => { state.compareMode = true; callbacks.onRequestRerender?.(); }, '두 주석 비교')
      ));

      const filtered = state.selectedSource === 'ALL'
        ? entries
        : entries.filter((e) => e.source_code === state.selectedSource);
      for (const item of filtered) body.appendChild(buildCommentaryCard(item, item.source_code, allSources));
      renderLiveCommentarySection(body, verseObj);
      return;
    }

    if (entries.length === 1) {
      body.appendChild(buildCommentaryCard(entries[0], entries[0].source_code, allSources));
      renderLiveCommentarySection(body, verseObj);
      return;
    }

    const bhUrl = buildBibleHubCommentaryUrl(verseObj.osis, verseObj.chapter, verseObj.verse);
    const chEntries = service.getCommentariesForChapter?.(verseObj.bookId, verseObj.chapter) || [];
    const chVerses = Array.from(new Set(chEntries.map((c) => c.verse_start))).sort((a, b) => a - b);
    body.appendChild(el('div', { className: 'card' },
      el('h3', {}, `${verseObj.bookName} ${verseObj.chapter}:${verseObj.verse} 참고 안내`),
      el('p', {}, chVerses.length
        ? `이 장(${verseObj.bookName} ${verseObj.chapter}장)에는 ${chVerses.map((v) => `${v}절`).join(', ')}에 핵심 주석 요약이 수록되어 있습니다. 아래 버튼을 누르시면 바로 열립니다.`
        : `성경 전 66권(${stats.coveredVerses}절)에 핵심 말씀 참고 요약이 수록되어 있습니다. 아래 고전 영문 주석을 불러오거나 대표 말씀을 바로 열어 보실 수 있습니다.`),
      chVerses.length
        ? el('div', { className: 'action-row' },
            ...chVerses.map((vs) => btn('btn btn-primary', () => callbacks.onJumpToPassage?.(verseObj.osis, verseObj.chapter, vs), `${verseObj.bookName} ${verseObj.chapter}:${vs} 주석 보기`))
          )
        : null,
      el('div', { className: 'action-row' },
        el('a', { className: 'btn btn-primary', href: bhUrl, target: '_blank' }, iconEl('icon-external'), '바이블허브 영문 주석 열기'),
        ...FEATURED_PASSAGES.map((p) => btn('btn btn-secondary', () => callbacks.onJumpToPassage?.(p.osis, p.ch, p.vs), p.label))
      )
    ));
    renderLiveCommentarySection(body, verseObj);
  }

  return { render };
}
