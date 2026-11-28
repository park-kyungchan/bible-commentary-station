/**
 * Universal Command Palette / Omnibar (⌘K / Ctrl+K / /)
 * Instant keyboard-first navigation across 66 books, 23 versions, 645 hymns,
 * 137 responsive readings, 95 CCMs, 12 liturgies, themes, and spatial lenses.
 */

import { el, iconEl } from '../core/dom.js';

export function createCommandPalette({ registry, service, store, bus }) {
  let isOpen = false;
  let activeIdx = 0;
  let currentItems = [];
  let triggerEl = null;

  function renderResults(query = '') {
    const listEl = document.getElementById('cmdPaletteList');
    if (!listEl) return;
    currentItems = registry.search(query, {
      limit: 14,
      bookBounds: service.getBookBoundsMap(),
    });
    activeIdx = Math.min(activeIdx, Math.max(0, currentItems.length - 1));

    if (!currentItems.length) {
      listEl.replaceChildren(
        el('div', { className: 'cmd-empty' }, `"${query}"에 해당하는 성경·찬송·명령을 찾지 못했습니다.`)
      );
      return;
    }

    listEl.replaceChildren(
      ...currentItems.map((item, idx) =>
        el(
          'button',
          {
            type: 'button',
            className: `cmd-item ${idx === activeIdx ? 'is-active' : ''}`,
            role: 'option',
            'aria-selected': idx === activeIdx ? 'true' : 'false',
            onMouseEnter: () => {
              activeIdx = idx;
              syncActiveClass(listEl);
            },
            onClick: () => runItem(item),
          },
          el('span', { className: 'cmd-item-icon' }, iconEl(item.icon || 'icon-search')),
          el(
            'span',
            { className: 'cmd-item-text' },
            el('strong', { className: 'cmd-item-title' }, item.title),
            item.subtitle ? el('span', { className: 'cmd-item-sub' }, item.subtitle) : null
          ),
          el('span', { className: 'cmd-item-cat' }, item.category || ''),
          item.shortcut ? el('kbd', { className: 'cmd-kbd' }, item.shortcut) : null
        )
      )
    );
  }

  function syncActiveClass(listEl) {
    const buttons = listEl.querySelectorAll('.cmd-item');
    buttons.forEach((b, i) => {
      b.classList.toggle('is-active', i === activeIdx);
      b.setAttribute('aria-selected', i === activeIdx ? 'true' : 'false');
    });
  }

  function runItem(item) {
    if (!item || typeof item.run !== 'function') return;
    close();
    item.run({
      store,
      service,
      bus,
      jumpToPassage: (osis, chapter, verse, mode = 'bible') =>
        bus.emit('passage:jump', { osis, chapter, verse, mode }),
    });
  }

  function open(trigger = null) {
    const overlay = document.getElementById('cmdPaletteOverlay');
    const input = document.getElementById('cmdPaletteInput');
    if (!overlay || !input) return;
    triggerEl = trigger || document.activeElement;
    isOpen = true;
    activeIdx = 0;
    overlay.dataset.open = 'true';
    overlay.setAttribute('aria-hidden', 'false');
    input.value = '';
    renderResults('');
    setTimeout(() => input.focus(), 10);
  }

  function close() {
    if (!isOpen) return;
    const overlay = document.getElementById('cmdPaletteOverlay');
    if (overlay) {
      overlay.dataset.open = 'false';
      overlay.setAttribute('aria-hidden', 'true');
    }
    isOpen = false;
    if (triggerEl && typeof triggerEl.focus === 'function') triggerEl.focus();
  }

  function bindEvents() {
    const overlay = document.getElementById('cmdPaletteOverlay');
    const input = document.getElementById('cmdPaletteInput');

    overlay?.addEventListener('click', (e) => {
      if (e.target === overlay) close();
    });

    input?.addEventListener('input', (e) => {
      activeIdx = 0;
      renderResults(e.target.value);
    });

    input?.addEventListener('keydown', (e) => {
      const listEl = document.getElementById('cmdPaletteList');
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        if (currentItems.length) {
          activeIdx = (activeIdx + 1) % currentItems.length;
          if (listEl) syncActiveClass(listEl);
        }
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        if (currentItems.length) {
          activeIdx = (activeIdx - 1 + currentItems.length) % currentItems.length;
          if (listEl) syncActiveClass(listEl);
        }
      } else if (e.key === 'Enter') {
        e.preventDefault();
        if (currentItems[activeIdx]) runItem(currentItems[activeIdx]);
      } else if (e.key === 'Escape') {
        e.preventDefault();
        close();
      }
    });

    document.addEventListener('keydown', (e) => {
      const target = e.target;
      const inEditable = target && (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.tagName === 'SELECT' || target.isContentEditable);
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        if (isOpen) close();
        else open();
      } else if (!inEditable && e.key === '/' && !isOpen) {
        e.preventDefault();
        open();
      }
    });
  }

  return { open, close, bindEvents, isOpen: () => isOpen };
}
