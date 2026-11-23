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
import { shouldReloadOnControllerChange } from '../../web/js/main.js';
import { createCommentaryPanel } from '../../web/js/features/commentaryPanel.js';

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

test('DEF-UX-01: controllerchange never reloads on first-ever visit without prior controller', () => {
  assert.equal(shouldReloadOnControllerChange({ hadController: false, userRequestedUpdate: false }), false);
  assert.equal(shouldReloadOnControllerChange({ hadController: false, userRequestedUpdate: true }), false);
  assert.equal(shouldReloadOnControllerChange({ hadController: true, userRequestedUpdate: false }), false);
  assert.equal(shouldReloadOnControllerChange({ hadController: true, userRequestedUpdate: true }), true);
});

test('DEF-UX-02: commentaryPanel uses single compact select dropdown instead of 17-pill filter wall', () => {
  const prevDoc = globalThis.document;
  const makeNode = (tag) => ({
    tagName: String(tag).toUpperCase(),
    className: '',
    value: '',
    dataset: {},
    attrs: new Map(),
    children: [],
    setAttribute(k, v) { this.attrs.set(k, String(v)); },
    getAttribute(k) { return this.attrs.get(k) ?? null; },
    addEventListener() {},
    appendChild(c) { this.children.push(c); return c; },
    replaceChildren(...cs) { this.children = cs; },
  });
  globalThis.document = {
    createElement: makeNode,
    createElementNS: (_ns, tag) => makeNode(tag),
    createTextNode: (t) => ({ nodeType: 3, textContent: t }),
  };

  const walk = (node, out = []) => {
    out.push(node);
    for (const c of node.children || []) walk(c, out);
    return out;
  };

  try {
    const sources = Array.from({ length: 12 }, (_, i) => ({
      source_code: `SRC_${i}`,
      name_kr: `주석서 ${i + 1}`,
      category: 'CLASSIC',
      category_kr: '고전·경건',
    }));
    const entries = sources.map((s, i) => ({
      source_code: s.source_code,
      title: `제목 ${i + 1}`,
      content_markdown: `내용 ${i + 1}`,
      attributionLabel: '핵심 말씀 참고 요약',
    }));
    const service = {
      exegesis: { sources },
      getCommentariesForVerse: () => entries,
      getCoverageStats: () => ({ coveredVerses: 28 }),
    };
    const panel = createCommentaryPanel({
      store: {
        state: { selectedSource: 'ALL', compareMode: false, liveCommSource: 'matthew-henry', liveCommLoadedKey: '' },
        guards: { liveCommentary: { next: () => ({ signal: undefined, isCurrent: () => true }) } },
      },
      service,
      callbacks: {},
    });

    const body = makeNode('div');
    panel.render(body, { verseId: 1022002, osis: 'GEN', bookName: '창세기', chapter: 22, verse: 2 });
    const all = walk(body);
    const pills = all.filter((n) => String(n.className || '').includes('filter-pill'));
    const selects = all.filter((n) => n.tagName === 'SELECT' && n.getAttribute('aria-label') === '주석 선택');
    assert.equal(pills.length, 0, 'Must not render multi-row filter-pill wall');
    assert.equal(selects.length, 1, 'Must render one compact source select dropdown');
    assert.equal(selects[0].children.length, 13, 'Dropdown must list ALL + 12 matched sources');

    // When <= 1 entry exists, source dropdown must be hidden completely
    const singleService = { ...service, getCommentariesForVerse: () => [entries[0]] };
    const singlePanel = createCommentaryPanel({
      store: {
        state: { selectedSource: 'ALL', compareMode: false, liveCommSource: 'matthew-henry', liveCommLoadedKey: '' },
        guards: { liveCommentary: { next: () => ({ signal: undefined, isCurrent: () => true }) } },
      },
      service: singleService,
      callbacks: {},
    });
    const singleBody = makeNode('div');
    singlePanel.render(singleBody, { verseId: 1001001, osis: 'GEN', bookName: '창세기', chapter: 1, verse: 1 });
    const singleSelects = walk(singleBody).filter((n) => n.tagName === 'SELECT' && n.getAttribute('aria-label') === '주석 선택');
    assert.equal(singleSelects.length, 0, 'Dropdown must be omitted when <= 1 commentary entry');
  } finally {
    globalThis.document = prevDoc;
  }
});

test('L3-UX: sermonStudio replaces plain-text scripture input with click-to-select picker button & quick pills, and biblePickerModal selects verse ranges', async () => {
  const { createSermonStudio } = await import('../../web/js/features/sermonStudio.js');
  const { createBiblePickerModal } = await import('../../web/js/features/biblePickerModal.js');
  const prevDoc = globalThis.document;
  const nodes = {};
  const makeNode = (tag) => {
    const n = {
      tagName: String(tag).toUpperCase(),
      id: '',
      className: '',
      value: '',
      textContent: '',
      dataset: {},
      attrs: new Map(),
      listeners: {},
      children: [],
      setAttribute(k, v) { this.attrs.set(k, String(v)); if (k === 'id') { this.id = String(v); nodes[this.id] = this; } },
      getAttribute(k) { return this.attrs.get(k) ?? null; },
      addEventListener(ev, fn) { (this.listeners[ev] ||= []).push(fn); },
      appendChild(c) { this.children.push(c); return c; },
      replaceChildren(...cs) { this.children = cs; },
    };
    return n;
  };
  const walk = (node, out = []) => {
    if (!node) return out;
    out.push(node);
    for (const c of node.children || []) walk(c, out);
    return out;
  };

  nodes.sermonSelect = makeNode('select');
  nodes.sermonSaveStatus = makeNode('span');
  nodes.sermonEditorPane = makeNode('div');
  nodes.sermonClipsPane = makeNode('div');
  nodes.pickerBody = makeNode('div');
  nodes.toast = makeNode('div');

  globalThis.document = {
    createElement: makeNode,
    createElementNS: (_ns, tag) => makeNode(tag),
    createTextNode: (t) => ({ nodeType: 3, textContent: String(t) }),
    getElementById: (id) => nodes[id] || null,
  };

  try {
    const store = {
      state: {
        mode: 'sermon',
        osis: 'GEN',
        chapter: 22,
        selectedVerse: 2,
        primaryVersion: 'nkrv',
        customBibles: [],
        sermons: [{
          id: 's1',
          title: '모리아 산의 순종',
          scriptureRef: '창세기 22:1-14',
          date: '2026-11-23',
          targetDurationMins: 30,
          outline: [{ id: 'o1', section: '서론', title: '부르심', content: '' }],
          clips: [],
        }],
        activeSermonId: 's1',
      },
    };
    const service = {
      getBooks: () => [{ id: 'GEN', name: '창세기', testament: 'OT', totalChapters: 50 }, { id: 'JHN', name: '요한복음', testament: 'NT', totalChapters: 21 }],
      getBookMeta: (osis) => ({ GEN: { id: 'GEN', name: '창세기', testament: 'OT', totalChapters: 50 }, JHN: { id: 'JHN', name: '요한복음', testament: 'NT', totalChapters: 21 } }[osis] || null),
      getChapterVerseCount: (osis, ch) => (osis === 'JHN' && ch === 3 ? 36 : 24),
      getVersionInfo: () => ({ shortLabel: '개역개정' }),
      getVersionChapterMap: async () => ({ 16: '하나님이 세상을 이처럼 사랑하사 독생자를 주셨으니', 17: '하나님이 그 아들을 세상에 보내신 것은' }),
    };
    const archive = { scheduleSermonSave: (_s, _ms, cb) => cb?.({ persisted: 'idb', savedAt: new Date().toISOString() }) };
    const modalManager = { open: () => {}, close: () => {} };

    let pickerModal = null;
    const studio = createSermonStudio({
      store,
      service,
      archive,
      modalManager,
      callbacks: {
        onOpenPassagePicker: (triggerEl, onSelectRange) => pickerModal.open(triggerEl, { onSelectRange }),
      },
    });
    pickerModal = createBiblePickerModal({ store, service, modalManager, callbacks: {} });

    studio.render();
    const editorNodes = walk(nodes.sermonEditorPane);
    const pickBtn = editorNodes.find((n) => n.id === 'btnSermonPickPassage');
    assert.ok(pickBtn, 'Sermon studio must render #btnSermonPickPassage click-to-select button');
    const plainScriptureInputs = editorNodes.filter((n) => n.tagName === 'INPUT' && n.getAttribute('placeholder')?.includes('창세기'));
    assert.equal(plainScriptureInputs.length, 0, 'Plain text input for scriptureRef must be removed');

    // Click #btnSermonPickPassage -> opens picker in range mode -> switch to NT -> pick JHN -> pick ch 3 -> pick verses 16..17 -> confirm
    pickBtn.listeners.click[0]({ currentTarget: pickBtn });
    const ntTab = walk(nodes.pickerBody).find((n) => n.tagName === 'BUTTON' && n.children.some((c) => c.textContent?.includes('신약 성경')));
    assert.ok(ntTab);
    ntTab.listeners.click[0]();

    const jhnBtn = walk(nodes.pickerBody).find((n) => n.dataset?.osis === 'JHN');
    assert.ok(jhnBtn);
    jhnBtn.listeners.click[0]();

    const ch3Btn = walk(nodes.pickerBody).find((n) => n.dataset?.chapter === '3');
    assert.ok(ch3Btn);
    ch3Btn.listeners.click[0]();

    const v16Btn = walk(nodes.pickerBody).find((n) => n.dataset?.verse === '16');
    const v17Btn = walk(nodes.pickerBody).find((n) => n.dataset?.verse === '17');
    assert.ok(v16Btn && v17Btn);
    v16Btn.listeners.click[0]();
    v17Btn.listeners.click[0]();

    const confirmRangeBtn = walk(nodes.pickerBody).find((n) => n.tagName === 'BUTTON' && n.children.some((c) => c.textContent?.includes('요한복음 3:16-17 본문으로 결정')));
    assert.ok(confirmRangeBtn, 'Verse range picker must show "요한복음 3:16-17 본문으로 결정" button');
    await confirmRangeBtn.listeners.click[0]();

    assert.equal(store.state.sermons[0].scriptureRef, '요한복음 3:16-17');
    assert.equal(store.state.sermons[0].clips.length, 1, 'Selecting sermon passage must auto-clip verse text into sermon notes');
    assert.ok(store.state.sermons[0].clips[0].source.includes('요한복음 3:16-17'));
    assert.ok(store.state.sermons[0].clips[0].text.includes('독생자를 주셨으니'));
  } finally {
    globalThis.document = prevDoc;
  }
});
