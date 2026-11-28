/**
 * Lens 2: Polyglot Synoptic Matrix (다중 역본 매트릭스)
 * Side-by-side comparison of 2 to 4 translations simultaneously out of 23+ versions,
 * with instant theological presets, synchronized row focus, and multi-version clip export.
 */

import { btn, el, iconEl, showToast } from '../core/dom.js';

const MATRIX_PRESETS = Object.freeze([
  { id: 'kr-en-core', label: '표준 한·영 3역본', versions: ['nkrv', 'rnksv', 'esv'] },
  { id: 'kr-compare', label: '한국어 4역본 대조', versions: ['nkrv', 'krv', 'rnksv', 'easy'] },
  { id: 'modern-vivid', label: '현대어·메시지 대조', versions: ['easy', 'klb', 'nlt', 'msg'] },
  { id: 'classic-literal', label: '직역·고전 3역본', versions: ['nkrv', 'nasb', 'nkjv'] },
]);

export function createPolyglotMatrix({ store, service, bus }) {
  const { state, guards } = store;

  function ensureVersions() {
    const locals = service.getLocalVersions().map((v) => v.id);
    if (!Array.isArray(state.polyglotVersions) || state.polyglotVersions.length < 2) {
      state.polyglotVersions = locals.slice(0, 3);
    }
    state.polyglotVersions = state.polyglotVersions.slice(0, 4);
  }

  function applyPreset(versions) {
    const avail = new Set(service.getAvailableVersions(state.customBibles).map((v) => v.id));
    const filtered = versions.filter((v) => avail.has(v));
    if (filtered.length >= 2) {
      state.polyglotVersions = filtered;
      store.savePrefs();
      render();
    }
  }

  async function render() {
    const root = document.getElementById('matrixContainer');
    if (!root) return;
    ensureVersions();

    const req = guards.matrix.next();
    const meta = service.getBookMeta(state.osis);
    const available = service.getAvailableVersions(state.customBibles);

    // Header & Controls
    const presetBar = el(
      'div',
      { className: 'matrix-presets', role: 'group', 'aria-label': '추천 역본 조합' },
      ...MATRIX_PRESETS.map((p) => {
        const active = JSON.stringify(p.versions) === JSON.stringify(state.polyglotVersions);
        return el(
          'button',
          {
            type: 'button',
            className: `chip-btn ${active ? 'is-active' : ''}`,
            onClick: () => applyPreset(p.versions),
          },
          p.label
        );
      })
    );

    const colSelectors = state.polyglotVersions.map((verId, idx) => {
      const sel = el(
        'select',
        {
          className: 'select-field matrix-ver-select',
          'aria-label': `비교 역본 ${idx + 1}`,
          onChange: (e) => {
            const next = [...state.polyglotVersions];
            next[idx] = e.target.value;
            state.polyglotVersions = next;
            store.savePrefs();
            render();
          },
        },
        ...available.map((v) =>
          el('option', { value: v.id, selected: v.id === verId }, `${v.shortLabel}${v.source === 'live' ? ' (온라인)' : ''}`)
        )
      );
      sel.value = verId;

      return el(
        'div',
        { className: 'matrix-col-picker' },
        el('span', { className: 'matrix-col-badge' }, `열 ${idx + 1}`),
        sel,
        state.polyglotVersions.length > 2
          ? el(
              'button',
              {
                type: 'button',
                className: 'btn btn-ghost btn-icon-sm',
                'aria-label': `열 ${idx + 1} 제거`,
                onClick: () => {
                  state.polyglotVersions = state.polyglotVersions.filter((_, i) => i !== idx);
                  store.savePrefs();
                  render();
                },
              },
              iconEl('icon-close')
            )
          : null
      );
    });

    const addColBtn = state.polyglotVersions.length < 4
      ? btn(
          'btn btn-secondary',
          () => {
            const nextVer = available.find((v) => !state.polyglotVersions.includes(v.id))?.id || 'esv';
            state.polyglotVersions = [...state.polyglotVersions, nextVer];
            store.savePrefs();
            render();
          },
          iconEl('icon-plus'),
          '역본 열 추가 (최대 4열)'
        )
      : null;

    const header = el(
      'header',
      { className: 'lens-hero matrix-hero' },
      el(
        'div',
        { className: 'lens-hero-top' },
        el(
          'div',
          {},
          el('span', { className: 'eyebrow-badge' }, 'POLYGLOT SYNOPTIC MATRIX'),
          el('h2', { className: 'lens-title' }, `${meta?.name || state.osis} ${state.chapter}장 · 다중 역본 정밀 대조`)
        ),
        el(
          'div',
          { className: 'action-row' },
          btn('btn btn-secondary', () => bus.emit('picker:open'), iconEl('icon-bible'), '본문 변경'),
          btn('btn btn-secondary', () => bus.emit('chapter:step', { dir: 'prev' }), iconEl('icon-chevron-left'), '이전 장'),
          btn('btn btn-secondary', () => bus.emit('chapter:step', { dir: 'next' }), '다음 장', iconEl('icon-chevron-right'))
        )
      ),
      presetBar,
      el('div', { className: 'matrix-picker-row' }, ...colSelectors, addColBtn)
    );

    const gridWrap = el('div', { className: 'matrix-grid-wrap' }, el('div', { className: 'skeleton-card' }));
    root.replaceChildren(header, gridWrap);

    try {
      const data = await service.getPolyglotChapterVerses(
        state.polyglotVersions,
        state.osis,
        state.chapter,
        state.customBibles,
        req.signal
      );
      if (!req.isCurrent()) return;

      const colCount = data.columns.length;
      const tableHead = el(
        'div',
        { className: 'matrix-row matrix-row-head', dataset: { cols: String(colCount) } },
        el('div', { className: 'matrix-cell matrix-cell-num' }, '절'),
        ...data.columns.map((c) =>
          el(
            'div',
            { className: 'matrix-cell matrix-cell-head' },
            el('strong', {}, c.label),
            el('span', { className: 'matrix-lang-tag' }, String(c.lang || 'ko').toUpperCase())
          )
        ),
        el('div', { className: 'matrix-cell matrix-cell-act' }, '동작')
      );

      const rows = data.rows.map((row) => {
        const isSelected = row.verse === state.selectedVerse;
        return el(
          'article',
          {
            className: `matrix-row ${isSelected ? 'is-selected' : ''}`,
            dataset: { verseNum: String(row.verse), cols: String(colCount) },
            onClick: () => {
              state.selectedVerse = row.verse;
              store.saveLastPlace(state.osis, state.chapter, row.verse);
              gridWrap.querySelectorAll('.matrix-row.is-selected').forEach((n) => n.classList.remove('is-selected'));
              gridWrap.querySelector(`.matrix-row[data-verse-num="${row.verse}"]`)?.classList.add('is-selected');
            },
          },
          el('div', { className: 'matrix-cell matrix-cell-num' }, String(row.verse)),
          ...row.texts.map((txt, cIdx) => {
            const lang = data.columns[cIdx]?.lang || 'ko';
            return el(
              'div',
              { className: `matrix-cell matrix-cell-text ${lang === 'he' ? 'is-rtl' : ''}`, lang },
              txt || el('span', { className: 'verse-empty-note' }, '(없음)')
            );
          }),
          el(
            'div',
            { className: 'matrix-cell matrix-cell-act' },
            btn(
              'btn btn-ghost btn-icon-sm',
              (e) => {
                e.stopPropagation();
                const bundle = data.columns
                  .map((c, i) => `[${c.label}] ${row.texts[i] || '(없음)'}`)
                  .join('\n');
                bus.emit('clip:add', {
                  source: `${row.bookName} ${row.chapter}:${row.verse} (${data.columns.map((c) => c.label).join('·')})`,
                  text: bundle,
                });
              },
              iconEl('icon-sermon')
            ),
            btn(
              'btn btn-ghost btn-icon-sm',
              (e) => {
                e.stopPropagation();
                bus.emit('passage:jump', { osis: row.osis, chapter: row.chapter, verse: row.verse, mode: 'bible' });
              },
              iconEl('icon-study')
            )
          )
        );
      });

      gridWrap.replaceChildren(tableHead, ...rows);
    } catch (err) {
      if (err?.name === 'AbortError' || !req.isCurrent()) return;
      gridWrap.replaceChildren(el('div', { className: 'card empty-state' }, '다중 역본을 불러오는 중 오류가 발생했습니다.'));
      showToast('역본 비교 데이터를 불러오지 못했습니다.');
    }
  }

  return { render };
}
