import { btn, el, iconEl } from '../core/dom.js';

export function createBiblePickerModal({ store, service, modalManager, callbacks }) {
  const { state } = store;
  let testament = 'OT';
  let step = 'books';
  let chosenBook = null;
  let chosenChapter = 1;
  let startVerse = 1;
  let endVerse = 1;
  let rangeCallback = null;

  function formatRefLabel(book, ch, vStart, vEnd) {
    const unit = book.id === 'PSA' ? '편' : '장';
    if (!vStart) return `${book.name} ${ch}${unit}`;
    return vStart === vEnd ? `${book.name} ${ch}:${vStart}` : `${book.name} ${ch}:${vStart}-${vEnd}`;
  }

  function finishRange(vStart, vEnd) {
    const book = chosenBook || service.getBookMeta(state.osis);
    if (!book) return;
    const s = Math.min(vStart, vEnd);
    const e = Math.max(vStart, vEnd);
    const refLabel = formatRefLabel(book, chosenChapter, s, e);
    const cb = rangeCallback;
    rangeCallback = null;
    modalManager.close('pickerModal');
    cb?.({ osis: book.id, bookName: book.name, chapter: chosenChapter, startVerse: s, endVerse: e, refLabel });
  }

  function render() {
    const body = document.getElementById('pickerBody');
    if (!body) return;
    body.dataset.panelEnter = 'true';

    if (step === 'books') {
      const books = service.getBooks().filter((b) => b.testament === testament);
      const tabBar = el(
        'div',
        { className: 'testament-tabs', role: 'tablist', 'aria-label': '구약 신약 선택' },
        el(
          'button',
          {
            type: 'button',
            role: 'tab',
            className: `testament-tab ${testament === 'OT' ? 'btn-primary' : 'btn-ghost'}`,
            'aria-selected': testament === 'OT' ? 'true' : 'false',
            onClick: () => { testament = 'OT'; render(); },
          },
          '구약 성경 (39권)'
        ),
        el(
          'button',
          {
            type: 'button',
            role: 'tab',
            className: `testament-tab ${testament === 'NT' ? 'btn-primary' : 'btn-ghost'}`,
            'aria-selected': testament === 'NT' ? 'true' : 'false',
            onClick: () => { testament = 'NT'; render(); },
          },
          '신약 성경 (27권)'
        )
      );

      let activeTile = null;
      const grid = el(
        'div',
        { className: 'book-grid' },
        ...books.map((book) => {
          const isCurrent = book.id === (chosenBook?.id || state.osis);
          const tile = el(
            'button',
            {
              type: 'button',
              className: `book-tile ${isCurrent ? 'btn-primary' : 'btn-secondary'}`,
              dataset: { osis: book.id, active: isCurrent ? 'true' : 'false' },
              onClick: () => {
                chosenBook = book;
                step = 'chapters';
                render();
              },
            },
            book.name
          );
          if (isCurrent) activeTile = tile;
          return tile;
        })
      );

      const hint = rangeCallback
        ? el('p', { className: 'callout' }, '설교 본문 말씀을 고르는 중입니다. 먼저 성경 책 이름을 눌러 주세요.')
        : null;
      body.replaceChildren(...[hint, tabBar, grid].filter(Boolean));
      if (activeTile && typeof activeTile.scrollIntoView === 'function') {
        setTimeout(() => activeTile.scrollIntoView({ block: 'nearest' }), 30);
      }
      return;
    }

    const book = chosenBook || service.getBookMeta(state.osis);
    if (!book) {
      step = 'books';
      render();
      return;
    }

    if (step === 'chapters') {
      const header = el(
        'div',
        { className: 'card-header' },
        el(
          'button',
          {
            type: 'button',
            className: 'btn btn-ghost',
            onClick: () => { step = 'books'; render(); },
          },
          iconEl('icon-back'),
          '책 목록으로'
        ),
        el('strong', {}, `${book.name} — 몇 장을 선택하시겠습니까? (총 ${book.totalChapters}장)`)
      );

      const chapBtns = [];
      for (let ch = 1; ch <= book.totalChapters; ch += 1) {
        const isCur = book.id === state.osis && ch === state.chapter;
        chapBtns.push(
          el(
            'button',
            {
              type: 'button',
              className: `chap-tile ${isCur ? 'btn-primary' : 'btn-secondary'}`,
              dataset: { chapter: String(ch) },
              onClick: () => {
                if (rangeCallback) {
                  chosenChapter = ch;
                  const maxVs = service.getChapterVerseCount?.(book.id, ch) || 30;
                  startVerse = 1;
                  endVerse = Math.min(14, maxVs);
                  step = 'verses';
                  render();
                } else {
                  modalManager.close('pickerModal');
                  callbacks.onSelectChapter?.(book.id, ch, 1);
                }
              },
            },
            `${ch}장`
          )
        );
      }

      body.replaceChildren(header, el('div', { className: 'chap-grid' }, ...chapBtns));
      return;
    }

    const maxVs = service.getChapterVerseCount?.(book.id, chosenChapter) || 30;
    const s = Math.min(startVerse, endVerse);
    const e = Math.max(startVerse, endVerse);
    const previewLabel = formatRefLabel(book, chosenChapter, s, e);

    const header = el(
      'div',
      { className: 'card-header' },
      btn('btn btn-ghost', () => { step = 'chapters'; render(); }, iconEl('icon-back'), '장 선택으로'),
      el('strong', {}, `${book.name} ${chosenChapter}장 — 시작 절과 끝 절을 눌러 주세요 (총 ${maxVs}절)`)
    );

    const summaryBar = el(
      'div',
      { className: 'card picker-range-bar' },
      el('div', { className: 'card-header' },
        el('span', { className: 'tag-accent' }, '선택된 본문'),
        el('strong', { id: 'pickerRangePreview' }, previewLabel)
      ),
      el('div', { className: 'action-row' },
        btn('btn btn-primary', () => finishRange(s, e), iconEl('icon-sermon'), `${previewLabel} 본문으로 결정`),
        btn('btn btn-secondary', () => finishRange(1, maxVs), `${chosenChapter}장 전체 (1-${maxVs}절) 선택`)
      )
    );

    const verseBtns = [];
    for (let vs = 1; vs <= maxVs; vs += 1) {
      const inRange = vs >= s && vs <= e;
      const isEndpoint = vs === s || vs === e;
      verseBtns.push(
        el(
          'button',
          {
            type: 'button',
            className: `chap-tile verse-tile ${isEndpoint ? 'btn-primary' : (inRange ? 'btn-warm' : 'btn-secondary')}`,
            dataset: { verse: String(vs), inRange: inRange ? 'true' : 'false' },
            onClick: () => {
              if (startVerse !== endVerse || vs < startVerse) {
                startVerse = vs;
                endVerse = vs;
              } else {
                endVerse = vs;
              }
              render();
            },
          },
          `${vs}절`
        )
      );
    }

    body.replaceChildren(header, summaryBar, el('div', { className: 'chap-grid' }, ...verseBtns));
  }

  function open(triggerEl = null, options = {}) {
    const meta = service.getBookMeta(options.osis || state.osis);
    testament = meta?.testament === 'NT' ? 'NT' : 'OT';
    step = 'books';
    chosenBook = meta;
    chosenChapter = Number(options.chapter || state.chapter || 1);
    rangeCallback = typeof options.onSelectRange === 'function' ? options.onSelectRange : null;
    render();
    modalManager.open('pickerModal', triggerEl);
  }

  return { open, render };
}
