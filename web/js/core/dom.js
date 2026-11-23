import {
  DRIVE_IFRAME_REFERRER,
  DRIVE_IFRAME_SANDBOX,
  sanitizeDrivePreviewUrl,
  sanitizeUrl,
} from './urlSafety.js';

const SVG_NS = 'http://www.w3.org/2000/svg';

export const VALID_ICON_IDS = Object.freeze(new Set([
  'icon-bible', 'icon-study', 'icon-worship', 'icon-sermon', 'icon-pulpit',
  'icon-search', 'icon-bookmark', 'icon-sun', 'icon-moon', 'icon-help',
  'icon-settings', 'icon-chevron-left', 'icon-chevron-right', 'icon-print',
  'icon-close', 'icon-plus', 'icon-trash', 'icon-download', 'icon-upload',
  'icon-external', 'icon-back',
]));

let idCounter = 0;

export function generateId(prefix = 'id') {
  idCounter += 1;
  if (globalThis.crypto && typeof globalThis.crypto.randomUUID === 'function') {
    return `${prefix}_${globalThis.crypto.randomUUID()}`;
  }
  return `${prefix}_${Date.now()}_${idCounter}`;
}

export function iconEl(symbolId, className = 'icon') {
  const safeId = VALID_ICON_IDS.has(symbolId) ? symbolId : 'icon-bible';
  const svg = document.createElementNS(SVG_NS, 'svg');
  svg.setAttribute('class', className);
  svg.setAttribute('aria-hidden', 'true');
  const use = document.createElementNS(SVG_NS, 'use');
  use.setAttribute('href', `#${safeId}`);
  svg.appendChild(use);
  return svg;
}

export function el(tag, attrs = {}, ...children) {
  const node = document.createElement(tag);
  const tagLower = String(tag).toLowerCase();
  let wantsBlank = false;

  if (attrs && typeof attrs === 'object') {
    for (const [key, val] of Object.entries(attrs)) {
      if (val === null || val === undefined || val === false) continue;
      const lower = key.toLowerCase();
      if (lower === 'style' || lower === 'innerhtml' || lower === 'outerhtml') continue;
      if (lower.startsWith('on')) {
        if (typeof val === 'function') node.addEventListener(lower.slice(2), val);
        continue;
      }
      if (key === 'className') { node.className = String(val); continue; }
      if (key === 'dataset' && typeof val === 'object') {
        for (const [dk, dv] of Object.entries(val)) {
          if (dv !== null && dv !== undefined) node.dataset[dk] = String(dv);
        }
        continue;
      }
      if (lower === 'href') {
        const safeHref = sanitizeUrl(String(val));
        if (safeHref) node.setAttribute('href', safeHref);
        continue;
      }
      if (lower === 'src') {
        if (tagLower === 'iframe') {
          const safeDrive = sanitizeDrivePreviewUrl(String(val));
          if (safeDrive) {
            node.setAttribute('src', safeDrive);
            node.setAttribute('sandbox', DRIVE_IFRAME_SANDBOX);
            node.setAttribute('referrerpolicy', DRIVE_IFRAME_REFERRER);
          }
        } else {
          const str = String(val).trim();
          if (str.startsWith('./') || sanitizeUrl(str)) node.setAttribute('src', str);
        }
        continue;
      }
      if (lower === 'target' && String(val) === '_blank') {
        wantsBlank = true;
        node.setAttribute('target', '_blank');
        continue;
      }
      if (val === true) {
        node.setAttribute(key, '');
        if (key in node && typeof node[key] === 'boolean') node[key] = true;
        continue;
      }
      if (key === 'value' && 'value' in node) { node.value = String(val); continue; }
      node.setAttribute(key, String(val));
    }
  }

  if (wantsBlank) node.setAttribute('rel', 'noopener noreferrer');
  if (tagLower === 'iframe') {
    if (!node.getAttribute('sandbox')) node.setAttribute('sandbox', DRIVE_IFRAME_SANDBOX);
    if (!node.getAttribute('referrerpolicy')) node.setAttribute('referrerpolicy', DRIVE_IFRAME_REFERRER);
  }
  appendChildren(node, children);
  return node;
}

export function btn(className, onClick, ...children) {
  return el('button', { type: 'button', className, onClick }, ...children);
}

function appendChildren(parent, children) {
  for (const child of children) {
    if (child === null || child === undefined || child === false) continue;
    if (Array.isArray(child)) appendChildren(parent, child);
    else if (typeof child === 'string' || typeof child === 'number') {
      parent.appendChild(document.createTextNode(String(child)));
    } else {
      parent.appendChild(child);
    }
  }
}

const FOCUSABLE_SEL =
  'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])';

export function createModalManager() {
  const stack = [];
  const triggers = new Map();

  function getFocusable(modalEl) {
    const box = modalEl.querySelector('.modal-box') || modalEl;
    return Array.from(box.querySelectorAll(FOCUSABLE_SEL)).filter(
      (n) => !n.hasAttribute('hidden') && n.offsetParent !== null
    );
  }

  function open(modalId, triggerEl = null) {
    const overlay = document.getElementById(modalId);
    if (!overlay) return;
    triggers.set(modalId, triggerEl || document.activeElement);
    overlay.dataset.open = 'true';
    overlay.setAttribute('aria-hidden', 'false');
    if (!stack.includes(modalId)) stack.push(modalId);
    const focusables = getFocusable(overlay);
    const initial = overlay.querySelector('[data-autofocus]') || focusables[0];
    if (initial && typeof initial.focus === 'function') setTimeout(() => initial.focus(), 20);
  }

  function close(modalId) {
    const overlay = document.getElementById(modalId);
    if (!overlay) return;
    overlay.dataset.open = 'false';
    overlay.setAttribute('aria-hidden', 'true');
    const idx = stack.lastIndexOf(modalId);
    if (idx >= 0) stack.splice(idx, 1);
    const trigger = triggers.get(modalId);
    triggers.delete(modalId);
    if (trigger && typeof trigger.focus === 'function') trigger.focus();
  }

  function bindGlobalEvents() {
    document.addEventListener('click', (e) => {
      const closeBtn = e.target.closest?.('.modal-close');
      if (closeBtn) {
        const overlay = closeBtn.closest('.modal-overlay');
        if (overlay?.id) close(overlay.id);
        return;
      }
      if (e.target.classList?.contains('modal-overlay') && e.target.dataset.open === 'true') {
        close(e.target.id);
      }
    });

    document.addEventListener('keydown', (e) => {
      if (!stack.length) return;
      const topId = stack[stack.length - 1];
      const overlay = document.getElementById(topId);
      if (!overlay) return;
      if (e.key === 'Escape') { e.preventDefault(); close(topId); return; }
      if (e.key === 'Tab') {
        const list = getFocusable(overlay);
        if (!list.length) return;
        if (e.shiftKey && document.activeElement === list[0]) {
          e.preventDefault();
          list[list.length - 1].focus();
        } else if (!e.shiftKey && document.activeElement === list[list.length - 1]) {
          e.preventDefault();
          list[0].focus();
        }
      }
    });
  }

  return { open, close, bindGlobalEvents, isOpen: (id) => stack.includes(id) };
}

let toastTimer = null;

export function showToast(message, options = {}) {
  const toastEl = document.getElementById('toast');
  if (!toastEl) return;
  if (toastTimer) clearTimeout(toastTimer);
  toastEl.replaceChildren(el('span', {}, message));
  const duration = options.onUndo ? (options.durationMs || 5000) : (options.durationMs || 3200);
  if (typeof options.onUndo === 'function') {
    toastEl.appendChild(btn('btn btn-warm', () => {
      if (toastTimer) clearTimeout(toastTimer);
      toastEl.dataset.open = 'false';
      options.onUndo();
    }, options.undoLabel || '되돌리기'));
  }
  toastEl.dataset.open = 'true';
  toastTimer = setTimeout(() => { toastEl.dataset.open = 'false'; }, duration);
}

export function showConfirm(modalManager, { message, okLabel = '확인', cancelLabel = '취소', danger = false } = {}) {
  return new Promise((resolve) => {
    const msgEl = document.getElementById('confirmMessage');
    const okBtn = document.getElementById('btnConfirmOk');
    const cancelBtn = document.getElementById('btnConfirmCancel');
    const overlay = document.getElementById('confirmModal');
    if (!overlay || !msgEl || !okBtn || !cancelBtn) { resolve(false); return; }

    msgEl.textContent = message || '이 작업을 진행하시겠습니까?';
    okBtn.textContent = okLabel;
    cancelBtn.textContent = cancelLabel;
    okBtn.className = danger ? 'btn btn-danger' : 'btn btn-primary';

    let settled = false;
    const finish = (answer) => {
      if (settled) return;
      settled = true;
      okBtn.removeEventListener('click', onOk);
      cancelBtn.removeEventListener('click', onCancel);
      document.removeEventListener('keydown', onEsc, true);
      overlay.removeEventListener('click', onOverlayClick);
      modalManager.close('confirmModal');
      resolve(answer);
    };
    const onOk = () => finish(true);
    const onCancel = () => finish(false);
    const onEsc = (e) => { if (e.key === 'Escape') finish(false); };
    const onOverlayClick = (e) => {
      if (e.target === overlay || e.target?.closest?.('.modal-close') || e.target?.classList?.contains?.('modal-close')) {
        finish(false);
      }
    };

    okBtn.addEventListener('click', onOk);
    cancelBtn.addEventListener('click', onCancel);
    document.addEventListener('keydown', onEsc, true);
    overlay.addEventListener('click', onOverlayClick);
    modalManager.open('confirmModal');
  });
}

export function bindTablistKeyboard(tablistEl, selector, onSelect) {
  if (!tablistEl) return;
  tablistEl.addEventListener('keydown', (e) => {
    const tabs = Array.from(tablistEl.querySelectorAll(selector)).filter((t) => !t.hidden);
    const idx = tabs.indexOf(document.activeElement);
    if (idx < 0) return;
    let nextIdx = idx;
    if (e.key === 'ArrowRight') nextIdx = (idx + 1) % tabs.length;
    else if (e.key === 'ArrowLeft') nextIdx = (idx - 1 + tabs.length) % tabs.length;
    else if (e.key === 'Home') nextIdx = 0;
    else if (e.key === 'End') nextIdx = tabs.length - 1;
    else return;
    e.preventDefault();
    tabs[nextIdx].focus();
    onSelect(tabs[nextIdx]);
  });
}

export function setPrintDocument(title, subtitle, sections = []) {
  const sheet = document.getElementById('printSheet');
  if (!sheet) return;
  sheet.replaceChildren(
    el('article', { className: 'print-doc' },
      el('h1', {}, title || '말씀 서재 인쇄 자료'),
      subtitle ? el('p', {}, subtitle) : null,
      ...sections.map((sec) =>
        el('section', { className: 'print-section' },
          sec.heading ? el('h2', {}, sec.heading) : null,
          ...(sec.lines || []).map((line) => el('p', {}, line))
        )
      )
    )
  );
}

export function downloadTextFile(content, mimeType, fileName) {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = fileName;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 10000);
}
