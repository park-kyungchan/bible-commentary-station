import { el, iconEl, showToast } from '../core/dom.js';
import { parseKoreanRef } from '../core/koreanQuery.js';

const COLOR_LABELS = Object.freeze({
  yellow: '노랑',
  green: '초록',
  pink: '분홍',
});

export function createBookmarksSearchPanel({ store, service, callbacks }) {
  const { state, guards } = store;

  function setOverlayHeader(overlayMode, titleText) {
    const pane = document.getElementById('paneStudy');
    const titleEl = document.getElementById('studyOverlayTitle');
    state.studyOverlay = overlayMode;

    if (pane) {
      pane.dataset.studyOverlay = overlayMode;
      if (overlayMode !== 'none') {
        pane.dataset.mobileOpen = 'true';
        state.mobileStudyOpen = true;
      }
    }
    if (titleEl && titleText) titleEl.textContent = titleText;

    document.querySelectorAll('[data-study-tab]').forEach((tab) => {
      const isSelected = overlayMode === 'none' && tab.dataset.studyTab === state.studyTab;
      tab.setAttribute('aria-selected', isSelected ? 'true' : 'false');
    });
  }

  function closeOverlay() {
    guards.search.cancel();
    setOverlayHeader('none', '');
    callbacks.onOverlayClosed?.();
  }

  function openBookmarks() {
    setOverlayHeader('bookmarks', '표시한 말씀');
    renderBookmarks();
  }

  function renderBookmarks() {
    const body = document.getElementById('studyBody');
    if (!body) return;

    const items = Object.entries(state.highlights)
      .map(([verseId, data]) => ({ verseId, ...data }))
      .sort((a, b) => (b.updatedAt || '').localeCompare(a.updatedAt || ''));

    if (!items.length) {
      body.replaceChildren(
        el(
          'div',
          { className: 'card empty-state' },
          el('p', {}, '아직 표시한 말씀이 없습니다. 성경 구절을 누른 뒤 색상 표시 버튼을 눌러 저장해 보세요.')
        )
      );
      return;
    }

    const cards = items.map((item) => {
      const colorName = COLOR_LABELS[item.color] || '표시';
      const refText = `${item.bookName} ${item.chapter}:${item.verse}`;
      return el(
        'article',
        { className: 'card bookmark-card' },
        el(
          'div',
          { className: 'card-header' },
          el('span', { className: `hl-badge hl-${item.color}` }, colorName),
          el('strong', {}, refText),
          item.versionLabel ? el('span', { className: 'tag-provenance' }, item.versionLabel) : null
        ),
        el('p', {}, item.text || ''),
        el(
          'div',
          { className: 'action-row' },
          el(
            'button',
            {
              type: 'button',
              className: 'btn btn-primary',
              onClick: () => {
                closeOverlay();
                callbacks.onJumpToPassage?.(item.osis, item.chapter, item.verse);
              },
            },
            iconEl('icon-bible'),
            '본문 이동'
          ),
          el(
            'button',
            {
              type: 'button',
              className: 'btn btn-ghost',
              onClick: () => {
                delete state.highlights[item.verseId];
                store.saveHighlights();
                callbacks.onHighlightRemoved?.(item.verseId);
                renderBookmarks();
                showToast(`${refText} 표시를 지웠습니다.`);
              },
            },
            iconEl('icon-trash'),
            '표시 지우기'
          )
        )
      );
    });

    body.replaceChildren(...cards);
  }

  async function runSearch(rawQuery) {
    const query = String(rawQuery || '').trim();
    if (!query) {
      showToast('찾으실 말씀이나 구절(예: 시편 23편 4절, 선한 목자)을 입력해 주세요.');
      return;
    }

    const bounds = service.getBookBoundsMap();
    const parsedRef = parseKoreanRef(query, bounds);
    if (parsedRef) {
      closeOverlay();
      callbacks.onJumpToPassage?.(parsedRef.osis, parsedRef.chapter, parsedRef.verse);
      showToast('입력하신 성경 구절로 바로 이동했습니다.');
      return;
    }

    const req = guards.search.next();
    const verInfo = service.getVersionInfo(state.primaryVersion, state.customBibles);
    const verLabel = verInfo?.shortLabel || state.primaryVersion;
    setOverlayHeader('search', `"${query}" 말씀 찾기 (${verLabel})`);

    const body = document.getElementById('studyBody');
    if (body) {
      body.replaceChildren(
        el('div', { className: 'skeleton-card', 'aria-hidden': 'true' }),
        el('div', { className: 'skeleton-card', 'aria-hidden': 'true' }),
        el('div', { className: 'empty-state' }, `${verLabel} 전체에서 말씀을 찾고 있습니다...`)
      );
    }

    try {
      const hits = await service.searchActiveVersion(
        query,
        state.primaryVersion,
        state.customBibles,
        { limit: 40, signal: req.signal }
      );
      if (!req.isCurrent()) return;

      if (!body) return;
      if (!hits.length) {
        body.replaceChildren(
          el(
            'div',
            { className: 'card empty-state' },
            el('p', {}, `"${query}"와 일치하는 말씀을 ${verLabel}에서 찾지 못했습니다. 띄어쓰기를 줄이거나 다른 낱말로 다시 찾아보세요.`)
          )
        );
        return;
      }

      const nodes = [
        el('p', { className: 'tag-provenance' }, `${verLabel} 검색 결과 ${hits.length}건`),
        ...hits.map((hit) =>
          el(
            'button',
            {
              type: 'button',
              className: 'card search-hit-card',
              onClick: () => {
                closeOverlay();
                callbacks.onJumpToPassage?.(hit.osis, hit.chapter, hit.verse);
              },
            },
            el(
              'div',
              { className: 'card-header' },
              el('strong', {}, `${hit.bookName} ${hit.chapter}:${hit.verse}`),
              el('span', { className: 'tag-provenance' }, hit.versionLabel)
            ),
            el('p', {}, hit.text)
          )
        ),
      ];
      body.replaceChildren(...nodes);
    } catch (err) {
      if (!req.isCurrent() || err?.name === 'AbortError') return;
      if (body) {
        body.replaceChildren(
          el('div', { className: 'card empty-state' }, el('p', {}, '말씀 검색 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.'))
        );
      }
    }
  }

  return { openBookmarks, renderBookmarks, runSearch, closeOverlay };
}
