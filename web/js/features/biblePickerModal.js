import { el, iconEl } from '../core/dom.js';

export function createBiblePickerModal({ store, service, modalManager, callbacks }) {
  const { state } = store;
  let testament = 'OT';
  let step = 'books';
  let chosenBook = null;

  function render() {
    const body = document.getElementById('pickerBody');
    if (!body) return;

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
          const isCurrent = book.id === state.osis;
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

      body.replaceChildren(tabBar, grid);
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
      el('strong', {}, `${book.name} — 몇 장을 여시겠습니까? (총 ${book.totalChapters}장)`)
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
            onClick: () => {
              modalManager.close('pickerModal');
              callbacks.onSelectChapter?.(book.id, ch, 1);
            },
          },
          `${ch}장`
        )
      );
    }

    body.replaceChildren(header, el('div', { className: 'chap-grid' }, ...chapBtns));
  }

  function open(triggerEl = null) {
    const meta = service.getBookMeta(state.osis);
    testament = meta?.testament === 'NT' ? 'NT' : 'OT';
    step = 'books';
    chosenBook = meta;
    render();
    modalManager.open('pickerModal', triggerEl);
  }

  return { open, render };
}
