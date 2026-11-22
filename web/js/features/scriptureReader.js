import { el, iconEl } from '../core/dom.js';

const HL_OPTIONS = [
  { key: 'yellow', label: '노랑 표시' },
  { key: 'green', label: '초록 표시' },
  { key: 'pink', label: '분홍 표시' },
];

export function createScriptureReader({ store, service, callbacks }) {
  const { state, guards } = store;

  function getAdjacentChapter(direction) {
    const books = service.getBooks();
    const idx = books.findIndex((b) => b.id === state.osis);
    if (idx < 0) return null;
    const cur = books[idx];
    if (direction === 'next') {
      if (state.chapter < cur.totalChapters) return { osis: cur.id, chapter: state.chapter + 1 };
      if (idx + 1 < books.length) return { osis: books[idx + 1].id, chapter: 1 };
      return null;
    }
    if (state.chapter > 1) return { osis: cur.id, chapter: state.chapter - 1 };
    if (idx > 0) {
      const prev = books[idx - 1];
      return { osis: prev.id, chapter: prev.totalChapters };
    }
    return null;
  }

  function updateContextBar() {
    const meta = service.getBookMeta(state.osis);
    const placeEl = document.getElementById('currentPlaceText');
    if (placeEl) placeEl.textContent = `${meta?.name || state.osis} ${state.chapter}장`;

    const verEl = document.getElementById('activeVersionLabel');
    if (verEl) {
      const info = service.getVersionInfo(state.primaryVersion, state.customBibles);
      verEl.textContent = info?.shortLabel || state.primaryVersion;
    }

    const prevBtn = document.getElementById('btnPrevChap');
    const nextBtn = document.getElementById('btnNextChap');
    if (prevBtn) prevBtn.disabled = !getAdjacentChapter('prev');
    if (nextBtn) nextBtn.disabled = !getAdjacentChapter('next');
  }

  function renderLoadingSkeleton() {
    const listEl = document.getElementById('verseList');
    if (!listEl) return;
    listEl.dataset.loading = 'true';
    listEl.dataset.chapterDir = state.chapterDir;
    const items = [];
    for (let i = 0; i < 6; i += 1) {
      items.push(el('div', { className: 'skeleton-card', 'aria-hidden': 'true' }));
    }
    listEl.replaceChildren(...items);
  }

  function selectVerseInPlace(verseNum, { scrollIntoView = false } = {}) {
    const listEl = document.getElementById('verseList');
    if (!listEl) return;
    const prevNum = state.selectedVerse;
    state.selectedVerse = verseNum;
    store.saveLastPlace(state.osis, state.chapter, verseNum);

    if (prevNum !== verseNum) {
      const prevCard = listEl.querySelector(`article[data-verse-num="${prevNum}"]`);
      if (prevCard) prevCard.dataset.selected = 'false';
    }
    const nextCard = listEl.querySelector(`article[data-verse-num="${verseNum}"]`);
    if (nextCard) {
      nextCard.dataset.selected = 'true';
      if (scrollIntoView && typeof nextCard.scrollIntoView === 'function') {
        nextCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    }
    callbacks.onVerseSelected?.(getSelectedVerse());
  }

  function toggleHighlightInPlace(verseObj, colorKey) {
    const vid = String(verseObj.verseId);
    const existing = state.highlights[vid];
    const nextColor = existing?.color === colorKey ? 'none' : colorKey;

    if (nextColor === 'none') {
      delete state.highlights[vid];
    } else {
      state.highlights[vid] = {
        color: nextColor,
        verseId: verseObj.verseId,
        osis: verseObj.osis,
        bookName: verseObj.bookName,
        chapter: verseObj.chapter,
        verse: verseObj.verse,
        text: verseObj.primaryText || '(이 역본에는 해당 절이 없음)',
        versionLabel: verseObj.primaryLabel,
        updatedAt: new Date().toISOString(),
      };
    }
    store.saveHighlights();

    const card = document.querySelector(`#verseList article[data-verse-num="${verseObj.verse}"]`);
    if (card) card.dataset.highlight = nextColor;
    callbacks.onHighlightsChanged?.();
  }

  function buildVerseCard(v) {
    const hlColor = state.highlights[String(v.verseId)]?.color || 'none';
    const isSelected = v.verse === state.selectedVerse;

    const textNode = v.isEmptyPrimary
      ? el('p', { className: 'verse-empty-note' }, '(이 역본에는 해당 절이 없음)')
      : el('p', { className: 'verse-text' }, v.primaryText);

    const parallelNode = v.parallelText
      ? el('p', { className: 'parallel-verse' }, `[${v.parallelLabel}] ${v.parallelText}`)
      : null;

    const toolbar = el(
      'div',
      { className: 'verse-toolbar' },
      ...HL_OPTIONS.map((opt) =>
        el(
          'button',
          {
            type: 'button',
            className: `btn btn-ghost hl-btn hl-${opt.key}`,
            dataset: { hlColor: opt.key },
            onClick: (e) => {
              e.stopPropagation();
              toggleHighlightInPlace(v, opt.key);
            },
          },
          opt.label
        )
      ),
      el(
        'button',
        {
          type: 'button',
          className: 'btn btn-secondary',
          dataset: { action: 'clip-verse' },
          onClick: (e) => {
            e.stopPropagation();
            const sourceLabel = `${v.bookName} ${v.chapter}:${v.verse} (${v.primaryLabel})`;
            callbacks.onClipVerse?.(sourceLabel, v.primaryText || '(이 역본에는 해당 절이 없음)');
          },
        },
        iconEl('icon-sermon'),
        '설교 노트에 담기'
      ),
      el(
        'button',
        {
          type: 'button',
          className: 'btn btn-primary',
          dataset: { action: 'open-mobile-study' },
          onClick: (e) => {
            e.stopPropagation();
            selectVerseInPlace(v.verse);
            callbacks.onOpenMobileStudy?.();
          },
        },
        iconEl('icon-study'),
        '이 절 주석 보기'
      )
    );

    return el(
      'article',
      {
        className: 'verse-card',
        tabindex: '0',
        dataset: {
          verseNum: String(v.verse),
          selected: isSelected ? 'true' : 'false',
          highlight: hlColor,
        },
        onClick: () => selectVerseInPlace(v.verse),
        onKeydown: (e) => {
          if (e.target !== e.currentTarget) return;
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            selectVerseInPlace(v.verse);
          }
        },
      },
      el('span', { className: 'verse-num' }, String(v.verse)),
      el('div', { className: 'verse-body' }, textNode, parallelNode, toolbar)
    );
  }

  function renderVerses() {
    const headingEl = document.getElementById('chapterHeading');
    const listEl = document.getElementById('verseList');
    if (!listEl) return;

    const meta = service.getBookMeta(state.osis);
    if (headingEl) {
      headingEl.textContent = `${meta?.name || state.osis} ${state.chapter}장`;
    }

    listEl.dataset.loading = 'false';
    listEl.dataset.chapterDir = state.chapterDir;

    if (!state.chapterVerses.length) {
      listEl.replaceChildren(
        el('div', { className: 'empty-state' }, '이 장의 본문을 불러오지 못했습니다. 역본 설정을 확인해 주세요.')
      );
      return;
    }

    const frag = document.createDocumentFragment();
    for (const v of state.chapterVerses) frag.appendChild(buildVerseCard(v));
    listEl.replaceChildren(frag);
  }

  async function loadChapter(osis, chapter, targetVerse = 1, { direction = 'none', scrollToVerse = false } = {}) {
    const req = guards.chapter.next();
    state.chapterDir = direction;
    renderLoadingSkeleton();

    try {
      const verses = await service.getMergedChapterVerses(
        state.primaryVersion,
        state.parallelVersion,
        osis,
        chapter,
        state.customBibles,
        req.signal
      );
      if (!req.isCurrent()) return;

      state.osis = osis;
      state.chapter = chapter;
      state.chapterVerses = verses;
      const clampedVerse = verses.some((v) => v.verse === targetVerse)
        ? targetVerse
        : (verses[0]?.verse || 1);
      state.selectedVerse = clampedVerse;

      store.saveLastPlace(osis, chapter, clampedVerse);
      updateContextBar();
      renderVerses();

      const pane = document.getElementById('paneScripture');
      if (scrollToVerse) {
        const card = document.querySelector(`#verseList article[data-verse-num="${clampedVerse}"]`);
        card?.scrollIntoView?.({ behavior: 'smooth', block: 'center' });
      } else if (pane) {
        pane.scrollTop = 0;
      }

      callbacks.onChapterLoaded?.(getSelectedVerse());
    } catch (err) {
      if (!req.isCurrent() || err?.name === 'AbortError') return;
      const listEl = document.getElementById('verseList');
      if (listEl) {
        listEl.dataset.loading = 'false';
        listEl.replaceChildren(
          el('div', { className: 'empty-state' }, '성경 본문을 불러오지 못했습니다. 잠시 후 다시 시도해 주세요.')
        );
      }
      callbacks.onError?.('성경 본문을 불러오지 못했습니다.');
    }
  }

  function stepChapter(direction) {
    const next = getAdjacentChapter(direction);
    if (!next) return;
    loadChapter(next.osis, next.chapter, 1, { direction });
  }

  function getSelectedVerse() {
    return state.chapterVerses.find((v) => v.verse === state.selectedVerse) || state.chapterVerses[0] || null;
  }

  function syncHighlightDom(verseId) {
    const v = state.chapterVerses.find((row) => String(row.verseId) === String(verseId));
    if (!v) return;
    const card = document.querySelector(`#verseList article[data-verse-num="${v.verse}"]`);
    if (card) card.dataset.highlight = state.highlights[String(verseId)]?.color || 'none';
  }

  return {
    loadChapter,
    stepChapter,
    selectVerseInPlace,
    getSelectedVerse,
    updateContextBar,
    syncHighlightDom,
  };
}
