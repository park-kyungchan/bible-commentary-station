import { bindTablistKeyboard, btn, el, iconEl, setPrintDocument } from '../core/dom.js';
import { matchWorshipItem, normalizeWorshipQuery } from '../core/koreanQuery.js';
import { buildDrivePreviewUrl, buildDriveViewUrl, sanitizeDrivePreviewUrl, sanitizeDriveViewUrl } from '../core/urlSafety.js';

const ROLE_LABELS = Object.freeze({ leader: '인도자', congregation: '회중', unison: '다같이' });

export function createWorshipPanel({ store, service, callbacks }) {
  const { state, guards } = store;
  let debounceTimer = null; let isComposing = false; let activeDetailDeck = null;

  function buildOfflineFallbackCard(onOpenPulpit, onPrint) {
    return el('div', { className: 'card offline-fallback-card' },
      el('p', {}, '인터넷 연결이 필요하거나 공유 설정을 확인해 주세요. 아래 큰 글씨 본문이나 강단 화면은 인터넷 없이 바로 쓰실 수 있습니다.'),
      el('div', { className: 'action-row' },
        onOpenPulpit ? btn('btn btn-primary', onOpenPulpit, iconEl('icon-pulpit'), '강단 화면으로 열기') : null,
        onPrint ? btn('btn btn-secondary', onPrint, iconEl('icon-print'), '큰 글씨 인쇄') : null));
  }

  function buildDrivePreviewSection(item, onOpenPulpit, onPrint) {
    const previewUrl = sanitizeDrivePreviewUrl(item.pptPreviewUrl) || (item.driveId ? buildDrivePreviewUrl(item.driveId) : null);
    const viewUrl = sanitizeDriveViewUrl(item.pptViewUrl) || (item.driveId ? buildDriveViewUrl(item.driveId) : null);
    if (!previewUrl) return null;
    if (typeof navigator !== 'undefined' && navigator.onLine === false) return buildOfflineFallbackCard(onOpenPulpit, onPrint);

    const wrap = el('div', { className: 'embed-frame-wrap' });
    wrap.appendChild(el('iframe', {
      className: 'embed-frame', src: previewUrl, title: `${item.title} 발표 화면`, loading: 'lazy',
      onError: () => wrap.replaceChildren(buildOfflineFallbackCard(onOpenPulpit, onPrint)),
    }));
    return el('div', {},
      wrap,
      el('div', { className: 'action-row' },
        viewUrl ? el('a', { className: 'btn btn-secondary', href: viewUrl, target: '_blank' }, iconEl('icon-external'), '새 창에서 발표 화면 열기') : null,
        btn('btn btn-ghost', () => wrap.replaceChildren(buildOfflineFallbackCard(onOpenPulpit, onPrint)), '화면이 안 보일 때 안내 보기')
      )
    );
  }

  function buildSongCards(item, stanzas, isCustom = false) {
    const guidance = (item.usageTiming || item.pastoralNote)
      ? el('section', { className: 'card' },
          el('div', { className: 'card-header' }, el('h3', {}, '목회 활용 안내'), item.usageTiming ? el('span', { className: 'tag-accent' }, item.usageTiming) : null),
          item.pastoralNote ? el('p', { className: 'callout' }, item.pastoralNote) : null)
      : null;
    const lyrics = stanzas.length
      ? el('section', { className: 'card' },
          el('div', { className: 'card-header' },
            el('h3', {}, isCustom ? '내 기기에 저장된 찬송가 가사' : '찬송가 가사'),
            el('span', { className: 'tag-success' }, `${stanzas.length}절 수록`)),
          ...stanzas.map((st, idx) => el('div', { className: 'card' }, el('strong', {}, `${idx + 1}절`), el('p', {}, st))))
      : null;
    return [guidance, lyrics];
  }

  function renderHymnDetail(detailEl, hymn) {
    const viewEl = document.getElementById('viewWorship');
    if (viewEl) viewEl.dataset.hasDetail = 'true';
    const isCustom = Boolean(state.customHymns?.[hymn.num]);
    const lyrics = state.customHymns?.[hymn.num] || hymn.publicLyrics || '';
    const stanzas = lyrics ? lyrics.split(/\n{2,}/).map((st) => st.trim()).filter(Boolean) : [];
    const noteLines = [hymn.usageTiming ? `예배 활용: ${hymn.usageTiming}` : '', hymn.pastoralNote || ''].filter(Boolean);
    const fallbackBody = [hymn.ref?.label ? `관련 말씀: ${hymn.ref.label}` : '', ...noteLines].filter(Boolean).join('\n\n') || '성도님들과 함께 찬송합니다.';
    const deck = {
      title: `새찬송가 ${hymn.num}장 · ${hymn.title}`, targetDurationMins: 5,
      slides: stanzas.length
        ? stanzas.map((st, idx) => ({ heading: `새찬송가 ${hymn.num}장 ${hymn.title} (${idx + 1}절)`, body: st }))
        : [{ heading: `새찬송가 ${hymn.num}장 · ${hymn.title}`, body: fallbackBody }],
    };
    activeDetailDeck = deck;
    const doPulpit = () => callbacks.onLaunchPulpit?.(deck);
    const doPrint = () => {
      const sections = [];
      if (noteLines.length) sections.push({ heading: '목회 활용 안내', lines: noteLines });
      sections.push({
        heading: stanzas.length ? '찬송가 가사' : '찬송 안내',
        lines: stanzas.length ? stanzas.flatMap((st, idx) => [`[${idx + 1}절]`, ...st.split('\n')]) : [fallbackBody],
      });
      setPrintDocument(`새찬송가 ${hymn.num}장 · ${hymn.title}`, hymn.old ? `통일찬송가 ${hymn.old}장 · ${hymn.category || ''}` : (hymn.category || ''), sections);
      window.print();
    };
    const backBtn = el('button', {
      type: 'button', className: 'btn btn-ghost', dataset: { action: 'worship-back' },
      onClick: () => { activeDetailDeck = null; if (viewEl) viewEl.dataset.hasDetail = 'false'; detailEl.replaceChildren(); },
    }, iconEl('icon-back'), '찬송가 목록으로');

    detailEl.replaceChildren(...[
      el('div', { className: 'card-header' }, backBtn, el('h2', {}, `${hymn.num}장 · ${hymn.title}`), hymn.old ? el('span', { className: 'tag-provenance' }, `통일 ${hymn.old}장`) : null),
      el('div', { className: 'action-row' },
        btn('btn btn-primary', doPulpit, iconEl('icon-pulpit'), '강단 화면으로 열기'),
        btn('btn btn-secondary', doPrint, iconEl('icon-print'), '큰 글씨 인쇄'),
        hymn.ref?.osis ? btn('btn btn-secondary', () => callbacks.onJumpToPassage?.(hymn.ref.osis, hymn.ref.ch || 1, hymn.ref.vs || 1), iconEl('icon-bible'), `관련 말씀 (${hymn.ref.label || hymn.ref.osis})`) : null
      ),
      ...buildSongCards(hymn, stanzas, isCustom),
      buildDrivePreviewSection(hymn, doPulpit, doPrint),
    ].filter(Boolean));
  }

  async function renderResponsiveDetail(detailEl, rr) {
    const req = guards.worshipDetail.next();
    const viewEl = document.getElementById('viewWorship');
    if (viewEl) viewEl.dataset.hasDetail = 'true';
    detailEl.replaceChildren(el('div', { className: 'skeleton-card', 'aria-hidden': 'true' }));

    let lines = [];
    try { lines = await service.resolveResponsiveReadingLines(rr, state.primaryVersion, state.customBibles, req.signal); }
    catch (err) { if (err?.name === 'AbortError') return; }
    if (!req.isCurrent()) return;

    const slides = [];
    for (let i = 0; i < lines.length; i += 2) {
      slides.push({
        heading: `교독문 ${rr.num}번 · ${rr.title}`,
        body: lines.slice(i, i + 2).map((l) => `[${ROLE_LABELS[l.role] || '다같이'}] ${l.text}`).join('\n\n'),
      });
    }
    const deck = { title: `교독문 ${rr.num}번 · ${rr.title}`, targetDurationMins: 5, slides: slides.length ? slides : [{ heading: `교독문 ${rr.num}번`, body: rr.title }] };
    activeDetailDeck = deck;

    const doPulpit = () => callbacks.onLaunchPulpit?.(deck);
    const doPrint = () => {
      setPrintDocument(`교독문 ${rr.num}번 · ${rr.title}`, rr.season || rr.group || '', [
        { heading: '교독 본문', lines: lines.map((l) => `[${ROLE_LABELS[l.role] || '다같이'}] ${l.text}`) },
      ]);
      window.print();
    };

    const backBtn = el('button', {
      type: 'button', className: 'btn btn-ghost', dataset: { action: 'worship-back' },
      onClick: () => { activeDetailDeck = null; if (viewEl) viewEl.dataset.hasDetail = 'false'; detailEl.replaceChildren(); },
    }, iconEl('icon-back'), '교독문 목록으로');

    const linesCard = lines.length
      ? el('section', { className: 'card' }, ...lines.map((line) =>
          el('div', { className: 'rr-line', dataset: { role: line.role || 'unison' } },
            el('strong', {}, `${ROLE_LABELS[line.role] || '다같이'}: `), el('span', {}, line.text)
          )))
      : el('div', { className: 'card empty-state' }, '이 교독문의 성경 본문을 불러오지 못했습니다.');

    detailEl.replaceChildren(...[
      el('div', { className: 'card-header' }, backBtn, el('h2', {}, `${rr.num}번 · ${rr.title}`), rr.season ? el('span', { className: 'tag-accent' }, rr.season) : null),
      el('div', { className: 'action-row' },
        btn('btn btn-primary', doPulpit, iconEl('icon-pulpit'), '강단 화면으로 열기'),
        btn('btn btn-secondary', doPrint, iconEl('icon-print'), '큰 글씨 인쇄'),
        rr.osis ? btn('btn btn-secondary', () => callbacks.onJumpToPassage?.(rr.osis, rr.ch || 1, rr.start_vs || 1), iconEl('icon-bible'), '성경 본문 열기') : null
      ),
      linesCard,
      buildDrivePreviewSection(rr, doPulpit, doPrint),
    ].filter(Boolean));
  }

  function renderFilterPills(filterEl, groups) {
    if (!groups.includes(state.worshipGroup)) state.worshipGroup = '전체';
    filterEl.replaceChildren(...groups.map((grp) => el('button', {
      type: 'button',
      className: `filter-pill ${state.worshipGroup === grp ? 'btn-primary' : 'btn-ghost'}`,
      'aria-pressed': state.worshipGroup === grp ? 'true' : 'false',
      onClick: () => { state.worshipGroup = grp; renderListOnly(); },
    }, grp)));
  }

  function renderHymnsList(filterEl, listEl, detailEl) {
    renderFilterPills(filterEl, service.worship?.hymnGroups || ['전체']);
    const parsedQ = normalizeWorshipQuery(state.worshipSearch);
    const hymns = (service.worship?.hymns || []).filter((h) => (state.worshipGroup === '전체' || h.category === state.worshipGroup) && matchWorshipItem(h, parsedQ, 'hymns'));
    if (parsedQ.num !== null) hymns.sort((a, b) => (a.num === parsedQ.num ? -1 : b.num === parsedQ.num ? 1 : a.num - b.num));
    if (!hymns.length) { listEl.replaceChildren(el('div', { className: 'card empty-state' }, '검색 조건에 맞는 찬송가가 없습니다.')); return; }

    const frag = document.createDocumentFragment();
    for (const h of (parsedQ.raw ? hymns.slice(0, 120) : hymns)) {
      frag.appendChild(btn('card hymn-card', () => renderHymnDetail(detailEl, h),
        el('div', { className: 'card-header' },
          el('span', { className: 'tag-accent' }, `${h.num}장`),
          h.old ? el('span', { className: 'tag-provenance' }, `통일 ${h.old}`) : null,
          h.category ? el('span', { className: 'tag-provenance' }, h.category) : null,
          state.customHymns?.[h.num] ? el('span', { className: 'tag-success' }, '가사 저장됨') : (h.publicLyrics ? el('span', { className: 'tag-success' }, '가사 내장') : null)
        ),
        el('strong', {}, h.title),
        h.usageTiming ? el('p', { className: 'card-note' }, h.usageTiming) : null
      ));
    }
    listEl.replaceChildren(frag);
  }

  function renderResponsiveList(filterEl, listEl, detailEl) {
    renderFilterPills(filterEl, service.worship?.responsiveGroups || ['전체']);
    const parsedQ = normalizeWorshipQuery(state.worshipSearch);
    const readings = (service.worship?.responsiveReadings || []).filter((r) => (state.worshipGroup === '전체' || r.group === state.worshipGroup) && matchWorshipItem(r, parsedQ, 'responsive'));
    if (parsedQ.num !== null) readings.sort((a, b) => (a.num === parsedQ.num ? -1 : b.num === parsedQ.num ? 1 : a.num - b.num));
    if (!readings.length) { listEl.replaceChildren(el('div', { className: 'card empty-state' }, '검색 조건에 맞는 교독문이 없습니다.')); return; }

    const frag = document.createDocumentFragment();
    for (const rr of readings) {
      frag.appendChild(btn('card rr-card', () => renderResponsiveDetail(detailEl, rr),
        el('div', { className: 'card-header' }, el('span', { className: 'tag-accent' }, `${rr.num}번`), rr.season ? el('span', { className: 'tag-provenance' }, rr.season) : null),
        el('strong', {}, rr.title)
      ));
    }
    listEl.replaceChildren(frag);
  }

  function renderCcmDetail(detailEl, song) {
    const viewEl = document.getElementById('viewWorship');
    if (viewEl) viewEl.dataset.hasDetail = 'true';
    const stanzas = (song.publicLyrics || '').split(/\n{2,}/).map((st) => st.trim()).filter(Boolean);
    const noteLines = [song.usageTiming ? `예배 활용: ${song.usageTiming}` : '', song.pastoralNote || ''].filter(Boolean);
    const fallbackBody = noteLines.join('\n\n') || `${song.category || '경배·찬양'} 찬양 시간입니다.`;
    const deck = {
      title: song.title, targetDurationMins: 5,
      slides: stanzas.length
        ? stanzas.map((st, idx) => ({ heading: `${song.title} (${idx + 1}절)`, body: st }))
        : [{ heading: song.title, body: fallbackBody }],
    };
    activeDetailDeck = deck;
    const doPulpit = () => callbacks.onLaunchPulpit?.(deck);
    const doPrint = () => {
      const sections = [];
      if (noteLines.length) sections.push({ heading: '목회 활용 안내', lines: noteLines });
      sections.push({
        heading: stanzas.length ? '찬양 가사' : '찬양 안내',
        lines: stanzas.length ? stanzas.flatMap((st, idx) => [`[${idx + 1}절]`, ...st.split('\n')]) : [song.title],
      });
      setPrintDocument(song.title, song.category || '복음성가 · 찬양', sections);
      window.print();
    };
    const backBtn = el('button', {
      type: 'button', className: 'btn btn-ghost', dataset: { action: 'worship-back' },
      onClick: () => { activeDetailDeck = null; if (viewEl) viewEl.dataset.hasDetail = 'false'; detailEl.replaceChildren(); },
    }, iconEl('icon-back'), '복음성가 목록으로');

    detailEl.replaceChildren(...[
      el('div', { className: 'card-header' }, backBtn, el('h2', {}, song.title), song.category ? el('span', { className: 'tag-accent' }, song.category) : null),
      el('div', { className: 'action-row' },
        btn('btn btn-primary', doPulpit, iconEl('icon-pulpit'), '강단 화면으로 열기'),
        btn('btn btn-secondary', doPrint, iconEl('icon-print'), '큰 글씨 인쇄')
      ),
      ...buildSongCards(song, stanzas, false),
      buildDrivePreviewSection(song, doPulpit, doPrint),
    ].filter(Boolean));
  }

  function renderCcmList(filterEl, listEl, detailEl) {
    renderFilterPills(filterEl, service.worship?.ccmGroups || ['전체']);
    const parsedQ = normalizeWorshipQuery(state.worshipSearch);
    const songs = (service.worship?.ccm || []).filter((s) => (state.worshipGroup === '전체' || s.category === state.worshipGroup) && matchWorshipItem(s, parsedQ, 'ccm'));
    if (!songs.length) { listEl.replaceChildren(el('div', { className: 'card empty-state' }, '검색 조건에 맞는 복음성가가 없습니다.')); return; }

    const frag = document.createDocumentFragment();
    for (const song of songs) {
      frag.appendChild(btn('card hymn-card', () => renderCcmDetail(detailEl, song),
        el('div', { className: 'card-header' },
          song.category ? el('span', { className: 'tag-accent' }, song.category) : null,
          song.publicLyrics ? el('span', { className: 'tag-success' }, '가사 내장') : null
        ),
        el('strong', {}, song.title),
        song.usageTiming ? el('p', { className: 'card-note' }, song.usageTiming) : null
      ));
    }
    listEl.replaceChildren(frag);
  }

  function renderListOnly() {
    const filterEl = document.getElementById('worshipFilterBar');
    const listEl = document.getElementById('worshipListContainer');
    const detailEl = document.getElementById('worshipDetailContainer');
    if (!filterEl || !listEl || !detailEl) return;
    if (state.worshipTab === 'liturgy') callbacks.renderLiturgies?.(filterEl, listEl, detailEl, state.worshipSearch);
    else if (state.worshipTab === 'templates') callbacks.renderTemplates?.(filterEl, listEl, detailEl, state.worshipSearch);
    else if (state.worshipTab === 'hymns') renderHymnsList(filterEl, listEl, detailEl);
    else if (state.worshipTab === 'responsive') renderResponsiveList(filterEl, listEl, detailEl);
    else if (state.worshipTab === 'ccm') renderCcmList(filterEl, listEl, detailEl);
  }

  function syncSubTabs() {
    const hasCcm = Array.isArray(service.worship?.ccm) && service.worship.ccm.length > 0;
    document.querySelectorAll('[data-worship-tab]').forEach((tab) => {
      if (tab.dataset.worshipTab === 'ccm') tab.hidden = !hasCcm;
      tab.setAttribute('aria-selected', tab.dataset.worshipTab === state.worshipTab ? 'true' : 'false');
    });
  }

  function setWorshipTab(nextTab) {
    guards.worshipDetail.cancel();
    activeDetailDeck = null;
    callbacks.clearLiturgyDetail?.();
    state.worshipTab = nextTab;
    state.worshipGroup = '전체';
    const viewEl = document.getElementById('viewWorship');
    if (viewEl) viewEl.dataset.hasDetail = 'false';
    document.getElementById('worshipDetailContainer')?.replaceChildren();
    syncSubTabs();
    renderListOnly();
  }

  function bindEvents() {
    const subTabs = document.getElementById('worshipSubTabs');
    subTabs?.addEventListener('click', (e) => {
      const tab = e.target.closest?.('[data-worship-tab]');
      if (tab && !tab.hidden) setWorshipTab(tab.dataset.worshipTab);
    });
    bindTablistKeyboard(subTabs, '[data-worship-tab]', (tabEl) => setWorshipTab(tabEl.dataset.worshipTab));

    const searchInput = document.getElementById('worshipSearchInput');
    if (searchInput) {
      const scheduleUpdate = () => {
        if (debounceTimer) clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => { state.worshipSearch = searchInput.value; renderListOnly(); }, 150);
      };
      searchInput.addEventListener('compositionstart', () => { isComposing = true; });
      searchInput.addEventListener('compositionend', () => { isComposing = false; state.worshipSearch = searchInput.value; renderListOnly(); });
      searchInput.addEventListener('input', () => { if (!isComposing) scheduleUpdate(); });
    }
  }

  return { bindEvents, render: () => { syncSubTabs(); renderListOnly(); }, setWorshipTab, renderListOnly, getActivePulpitDeck: () => activeDetailDeck };
}
