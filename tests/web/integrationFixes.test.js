import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import {
  createLiturgyPanel,
  formatSlotPrintLines,
  normalizeSlotValue,
} from '../../web/js/features/liturgyPanel.js';
import { showConfirm } from '../../web/js/core/dom.js';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..');

const SAMPLE_WORSHIP = {
  liturgies: [
    { id: 'apostles-creed-ecumenical', title: '사도신경 (새 번역)', slides: [{ heading: '사도신경', lines: ['나는 전능하신 아버지 하나님을 믿습니다.'] }] },
    { id: 'lords-prayer-ecumenical', title: '주기도문 (새 번역)', slides: [{ heading: '주기도문', lines: ['하늘에 계신 우리 아버지', '나라와 권능과 영광이 영원히 아버지의 것입니다. 아멘.'] }] },
    { id: 'communion-institution', title: '성찬 예식', slides: [{ heading: '성찬 제정', lines: ['이것은 너희를 위하는 내 몸이니'] }] },
    { id: 'benediction-pauline', title: '축도 (고후 13:13)', slides: [{ heading: '축도', lines: ['주 예수 그리스도의 은혜와 하나님의 사랑과'] }] },
    { id: 'benediction-aaronic', title: '축도 (민 6:24-26)', slides: [{ heading: '축도', lines: ['여호와는 네게 복을 주시고 너를 지키시기를 원하며'] }] },
    { id: 'benediction-hebrews', title: '축도 (히 13:20-21)', slides: [{ heading: '축도', lines: ['평강의 하나님이 모든 선한 일에 너희를 온전케 하사'] }] },
  ],
  hymns: [
    { num: 23, title: '만 입이 내게 있으면', ref: { osis: 'PSA', ch: 51, vs: 15, label: '시편 51:15' } },
    { num: 28, title: '복의 근원 강림하사', ref: { osis: '1SA', ch: 7, vs: 12, label: '사무엘상 7:12' } },
  ],
  responsiveReadings: [
    { num: 1, title: '시편 1편', osis: 'PSA', ch: 1, start_vs: 1, end_vs: 2, segments: [] },
    { num: 92, title: '성찬 교독문', segments: [{ role: 'leader', osis: '1CO', ch: 11, start_vs: 23, end_vs: 23 }] },
  ],
  templates: [
    {
      id: 'sunday-morning',
      title: '주일 오전예배',
      slots: [
        { order: 1, label: '기원 찬양', slotType: 'hymn', defaultRef: 'hymn:23' },
        { order: 2, label: '신앙고백 (사도신경)', slotType: 'liturgy', defaultRef: 'liturgy:apostles-creed-ecumenical' },
        { order: 3, label: '교독문', slotType: 'responsive', defaultRef: 'responsive:1' },
        { order: 4, label: '주기도문', slotType: 'liturgy', defaultRef: 'liturgy:lords-prayer-ecumenical' },
        { order: 5, label: '성경봉독', slotType: 'scripture', defaultRef: 'PSA 23:1-6' },
        { order: 6, label: '축도', slotType: 'liturgy', defaultRef: 'liturgy:benediction-pauline' },
      ],
    },
  ],
};

test('DEF-V1-01: normalizeSlotValue, buildOrderDeck, and print lines resolve typed defaultRefs without raw English prefixes', async () => {
  const realWorshipPath = path.join(ROOT, 'web', 'data', 'worship.json');
  const realWorship = fs.existsSync(realWorshipPath) ? JSON.parse(fs.readFileSync(realWorshipPath, 'utf8')) : null;
  const worship = realWorship && Array.isArray(realWorship.templates) && realWorship.templates.length > 0
    ? realWorship
    : SAMPLE_WORSHIP;

  const mockService = {
    worship,
    getBookMeta: (osis) => ({ PSA: { name: '시편' }, ROM: { name: '로마서' }, '1CO': { name: '고린도전서' }, LUK: { name: '누가복음' }, MAT: { name: '마태복음' } }[osis] || null),
    resolveResponsiveReadingLines: async (rr) => [{ role: 'leader', text: `${rr.title} 본문` }],
  };

  const panel = createLiturgyPanel({
    store: { state: { primaryVersion: 'krv', customBibles: [], customHymns: {}, worshipOrders: [] } },
    service: mockService,
    archive: {},
    modalManager: {},
    callbacks: {},
  });

  const liturgyIds = new Set((worship.liturgies || []).map((l) => l.id));
  const rawPrefixRe = /\b(?:liturgy|hymn|responsive):/i;

  for (const tpl of worship.templates) {
    for (const slot of tpl.slots) {
      const normalized = normalizeSlotValue(slot.slotType, slot.defaultRef || '', mockService);
      assert.equal(rawPrefixRe.test(normalized), false, `Raw prefix leaked in ${tpl.id}/${slot.label}: ${normalized}`);
      if (slot.slotType === 'liturgy' && slot.defaultRef) {
        assert.ok(liturgyIds.has(normalized), `Liturgy slot must resolve to real liturgy id: ${normalized}`);
      }
      if (slot.slotType === 'hymn' && slot.defaultRef) {
        assert.match(normalized, /^\d+장$/);
      }
      if (slot.slotType === 'responsive' && slot.defaultRef) {
        assert.match(normalized, /^\d+번$/);
      }
      const printLines = formatSlotPrintLines(slot, worship, mockService);
      for (const line of printLines) {
        assert.equal(rawPrefixRe.test(line), false, `Raw prefix leaked into printOrder: ${line}`);
      }
    }

    const deck = await panel.buildOrderDeck(tpl);
    assert.ok(deck.slides.length >= tpl.slots.length);
    for (const slide of deck.slides) {
      assert.equal(rawPrefixRe.test(slide.heading), false, `Raw prefix in Pulpit heading: ${slide.heading}`);
      assert.equal(rawPrefixRe.test(slide.body), false, `Raw prefix in Pulpit body: ${slide.body}`);
    }
  }
});

test('DEF-V1-02: clicking #confirmModal .modal-close settles showConfirm(false) and cleans up listeners', async () => {
  const prevDoc = globalThis.document;
  const makeTarget = (id, classes = []) => {
    const listeners = new Map();
    return {
      id,
      textContent: '',
      className: classes.join(' '),
      dataset: { open: 'false' },
      classList: { contains: (c) => classes.includes(c) },
      closest(sel) { return sel === '.modal-close' && classes.includes('modal-close') ? this : null; },
      addEventListener(type, fn) {
        if (!listeners.has(type)) listeners.set(type, new Set());
        listeners.get(type).add(fn);
      },
      removeEventListener(type, fn) { listeners.get(type)?.delete(fn); },
      dispatch(type, target = this) {
        for (const fn of Array.from(listeners.get(type) || [])) fn({ type, target });
      },
      listenerCount(type) { return listeners.get(type)?.size || 0; },
    };
  };

  const overlay = makeTarget('confirmModal', ['modal-overlay']);
  const closeBtn = makeTarget('btnCloseX', ['modal-close']);
  const msgEl = makeTarget('confirmMessage');
  const okBtn = makeTarget('btnConfirmOk');
  const cancelBtn = makeTarget('btnConfirmCancel');
  const docListeners = new Map();
  const nodes = { confirmModal: overlay, confirmMessage: msgEl, btnConfirmOk: okBtn, btnConfirmCancel: cancelBtn };

  globalThis.document = {
    getElementById: (id) => nodes[id] || null,
    addEventListener(type, fn) {
      if (!docListeners.has(type)) docListeners.set(type, new Set());
      docListeners.get(type).add(fn);
    },
    removeEventListener(type, fn) { docListeners.get(type)?.delete(fn); },
  };

  const modalManager = {
    open(id) { nodes[id].dataset.open = 'true'; },
    close(id) { nodes[id].dataset.open = 'false'; },
  };

  try {
    // First dialog cancelled via top-right .modal-close button
    const firstPromise = showConfirm(modalManager, { message: '첫 번째 항목 삭제?', danger: true });
    overlay.dispatch('click', closeBtn);
    const firstAnswer = await firstPromise;
    assert.equal(firstAnswer, false, 'Clicking .modal-close must resolve showConfirm to false');
    assert.equal(okBtn.listenerCount('click'), 0, 'Old onOk listener must be removed after .modal-close');
    assert.equal(overlay.listenerCount('click'), 0, 'Old overlay listener must be removed after .modal-close');

    // Second dialog confirmed via #btnConfirmOk — must resolve cleanly with zero leaked callbacks
    const secondPromise = showConfirm(modalManager, { message: '두 번째 항목 삭제?', danger: true });
    assert.equal(okBtn.listenerCount('click'), 1, 'Exactly one active onOk listener');
    okBtn.dispatch('click', okBtn);
    const secondAnswer = await secondPromise;
    assert.equal(secondAnswer, true);
    assert.equal(okBtn.listenerCount('click'), 0);
  } finally {
    globalThis.document = prevDoc;
  }
});
