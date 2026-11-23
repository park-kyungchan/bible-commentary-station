import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { BibleDataService } from '../../web/js/services/bibleService.js';
import { createStore } from '../../web/js/core/state.js';
import { createWorshipPanel } from '../../web/js/features/worshipPanel.js';

const ROOT_DIR = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..');

function createFixtureFetcher() {
  const calls = [];
  const manifest = {
    schemaVersion: 3,
    appVersion: '3.0.0',
    defaultVersion: 'krv',
    versions: [
      {
        id: 'krv',
        nameKr: '개역한글',
        license: 'PUBLIC_DOMAIN',
        pathPrefix: './data/krv/',
        searchIndexPath: './data/search/krv.json',
      },
    ],
    books: [
      { bookId: 9, id: '1SA', name: '사무엘상', abbr: '삼상', testament: 'OT', totalChapters: 31 },
      { bookId: 19, id: 'PSA', name: '시편', abbr: '시', testament: 'OT', totalChapters: 150 },
      { bookId: 40, id: 'MAT', name: '마태복음', abbr: '마', testament: 'NT', totalChapters: 28 },
    ],
  };

  const psaBook = {
    bookId: 19,
    osis: 'PSA',
    nameKr: '시편',
    chapters: Object.fromEntries(
      Array.from({ length: 12 }, (_, idx) => [
        String(idx + 1),
        idx === 0
          ? ['복 있는 사람은 악인의 꾀를 좇지 아니하며', '오직 여호와의 율법을 즐거워하여']
          : [`시편 ${idx + 1}편 1절 여호와는 나의 목자시니`, `시편 ${idx + 1}편 2절 푸른 초장에 누이시며`],
      ])
    ),
  };

  const oneSaBook = {
    bookId: 9,
    osis: '1SA',
    nameKr: '사무엘상',
    chapters: {
      '30': Array.from({ length: 30 }, (_, i) => `삼상 30장 ${i + 1}절`),
    },
  };

  const matBook = {
    bookId: 40,
    osis: 'MAT',
    nameKr: '마태복음',
    chapters: {
      '17': Array.from({ length: 21 }, (_, i) => (i === 20 ? '' : `마태복음 17장 ${i + 1}절`)),
    },
  };

  const searchIndex = {
    version: 'krv',
    books: ['1SA', 'PSA', 'MAT'],
    verses: [
      [1, 23, 1, '여호와는 나의 목자시니 내가 부족함이 없으리로다'],
      [1, 1, 1, '하나님께서 사랑하시는 복 있는 사람'],
    ],
  };

  const fixtures = {
    './data/manifest.json': manifest,
    './data/exegesis.json': { sources: [], commentaries: [], crossReferences: {}, chains: {}, strongs: {} },
    './data/worship.json': { hymns: [], responsiveReadings: [], liturgies: [], templates: [] },
    './data/krv/PSA.json': psaBook,
    './data/krv/1SA.json': oneSaBook,
    './data/krv/MAT.json': matBook,
    './data/search/krv.json': searchIndex,
  };

  const fetcher = async (url) => {
    calls.push(url);
    if (Object.prototype.hasOwnProperty.call(fixtures, url)) {
      return { ok: true, status: 200, json: async () => structuredClone(fixtures[url]) };
    }
    return { ok: false, status: 404, json: async () => ({}) };
  };

  return { calls, fetcher };
}

test('reading 10 chapters of Psalms fetches PSA.json exactly once and makes 0 HelloAO calls', async () => {
  const { calls, fetcher } = createFixtureFetcher();
  const svc = new BibleDataService('./data', fetcher);
  await svc.init();

  for (let ch = 1; ch <= 10; ch += 1) {
    const verses = await svc.getMergedChapterVerses('krv', 'none', 'PSA', ch);
    assert.equal(verses.length, 2);
  }

  const psaFetches = calls.filter((u) => u.endsWith('/PSA.json'));
  assert.equal(psaFetches.length, 1, 'PSA.json must be fetched exactly once across 10 chapter reads');
  assert.equal(calls.filter((u) => u.includes('helloao.org')).length, 0, 'Zero automatic HelloAO requests on chapter load');
});

test('active-version search matches whitespace-insensitive Korean queries on krv and custom_* Bibles', async () => {
  const { fetcher } = createFixtureFetcher();
  const svc = new BibleDataService('./data', fetcher);
  await svc.init();

  const hitsNoSpace = await svc.searchActiveVersion('여호와는나의목자', 'krv');
  assert.equal(hitsNoSpace.length, 1);
  assert.equal(hitsNoSpace[0].osis, 'PSA');
  assert.equal(hitsNoSpace[0].chapter, 23);

  const hitsMulti = await svc.searchActiveVersion('하나님 사람', 'krv');
  assert.equal(hitsMulti.length, 1);

  const customBible = {
    id: 'custom_gae',
    name: '개역개정 개인본',
    shortName: '개역개정',
    bookCount: 1,
    books: {
      PSA: { '1': { '1': '복 있는 사람은 악인들의 꾀를 따르지 아니하며' } },
    },
  };
  const customHits = await svc.searchActiveVersion('꾀를 따르지', 'custom_gae', [customBible]);
  assert.equal(customHits.length, 1);
  assert.equal(customHits[0].versionId, 'custom_gae');
  assert.ok(customHits[0].text.includes('꾀를 따르지'));
});

test('empty verse renders empty marker without KRV substitution and 1SA 30:31 is not dropped', async () => {
  const { fetcher } = createFixtureFetcher();
  const svc = new BibleDataService('./data', fetcher);
  await svc.init();

  const mat17 = await svc.getMergedChapterVerses('krv', 'none', 'MAT', 17);
  const v21 = mat17.find((v) => v.verse === 21);
  assert.ok(v21);
  assert.equal(v21.isEmptyPrimary, true);
  assert.equal(v21.primaryText, '');

  const customGae = {
    id: 'custom_gae',
    name: '개역개정',
    shortName: '개역개정',
    books: {
      '1SA': {
        '30': Object.fromEntries(Array.from({ length: 31 }, (_, i) => [String(i + 1), `개역개정 삼상 30:${i + 1}`])),
      },
    },
  };
  const merged = await svc.getMergedChapterVerses('custom_gae', 'krv', '1SA', 30, [customGae]);
  const v31 = merged.find((v) => v.verse === 31);
  assert.ok(v31, '1SA 30:31 must not be dropped when present in active version');
  assert.equal(v31.primaryText, '개역개정 삼상 30:31');
  assert.equal(v31.parallelText, '');
});

test('resolveResponsiveReadingLines supports both single range and segments[]', async () => {
  const { fetcher } = createFixtureFetcher();
  const svc = new BibleDataService('./data', fetcher);
  await svc.init();

  const segLines = await svc.resolveResponsiveReadingLines(
    {
      num: 92,
      title: '세그먼트 교독문',
      segments: [
        { role: 'leader', osis: 'PSA', ch: 1, start_vs: 1, end_vs: 1 },
        { role: 'congregation', osis: 'PSA', ch: 1, start_vs: 2, end_vs: 2 },
      ],
    },
    'krv'
  );
  assert.equal(segLines.length, 2);
  assert.equal(segLines[0].role, 'leader');
  assert.equal(segLines[1].role, 'congregation');
  assert.ok(segLines[0].text.includes('복 있는 사람은'));

  const rangeLines = await svc.resolveResponsiveReadingLines(
    { num: 1, title: '시편 1편', osis: 'PSA', ch: 1, start_vs: 1, end_vs: 2, segments: [] },
    'krv'
  );
  assert.equal(rangeLines.length, 2);
  assert.equal(rangeLines[0].role, 'leader');
  assert.equal(rangeLines[1].role, 'congregation');
});

test('multi-version manifest (nkrv default:true + krv + rnksv) loads chapters, footnotes, parallel, and search cleanly', async () => {
  const store = createStore(null);
  assert.equal(store.state.primaryVersion, '', 'Fresh store leaves primaryVersion unset so manifest default:true wins');

  const multiFixtures = {
    './data/manifest.json': {
      schemaVersion: 3,
      appVersion: '3.0.0',
      defaultVersion: 'nkrv',
      versions: [
        { id: 'nkrv', nameKr: '개역개정', default: true, pathPrefix: './data/nkrv/', searchIndexPath: './data/search/nkrv.json' },
        { id: 'krv', nameKr: '개역한글', pathPrefix: './data/krv/', searchIndexPath: './data/search/krv.json' },
        { id: 'rnksv', nameKr: '새번역', pathPrefix: './data/rnksv/', searchIndexPath: './data/search/rnksv.json' },
      ],
      books: [{ bookId: 19, id: 'PSA', name: '시편', abbr: '시', testament: 'OT', totalChapters: 150 }],
    },
    './data/exegesis.json': { sources: [], commentaries: [], crossReferences: {}, chains: {}, strongs: {} },
    './data/worship.json': { hymns: [], responsiveReadings: [], liturgies: [], templates: [] },
    './data/nkrv/PSA.json': { bookId: 19, osis: 'PSA', chapters: { '1': ['복 있는 사람은 악인들의 꾀를 따르지 아니하며'] } },
    './data/krv/PSA.json': { bookId: 19, osis: 'PSA', chapters: { '1': ['복 있는 사람은 악인의 꾀를 좇지 아니하며'] } },
    './data/rnksv/PSA.json': {
      bookId: 19,
      osis: 'PSA',
      chapters: { '1': ['복 있는 사람은 악인의 꾀를 따르지 아니하며'] },
      footnotes: { '1': { '1': ['㉠ 또는 "복되도다"'] } },
    },
    './data/search/nkrv.json': { version: 'nkrv', books: ['PSA'], verses: [[0, 1, 1, '복 있는 사람은 악인들의 꾀를 따르지 아니하며']] },
    './data/search/krv.json': { version: 'krv', books: ['PSA'], verses: [[0, 1, 1, '복 있는 사람은 악인의 꾀를 좇지 아니하며']] },
    './data/search/rnksv.json': { version: 'rnksv', books: ['PSA'], verses: [[0, 1, 1, '복 있는 사람은 악인의 꾀를 따르지 아니하며']] },
  };

  const fetcher = async (url) => ({
    ok: Object.prototype.hasOwnProperty.call(multiFixtures, url),
    status: Object.prototype.hasOwnProperty.call(multiFixtures, url) ? 200 : 404,
    json: async () => structuredClone(multiFixtures[url] || {}),
  });

  const svc = new BibleDataService('./data', fetcher);
  await svc.init();
  assert.equal(svc.getDefaultVersionId(), 'nkrv');

  const nkrvWithRnksv = await svc.getMergedChapterVerses('nkrv', 'rnksv', 'PSA', 1);
  assert.equal(nkrvWithRnksv[0].primaryLabel, '개역개정');
  assert.equal(nkrvWithRnksv[0].parallelLabel, '새번역');
  assert.ok(nkrvWithRnksv[0].primaryText.includes('악인들의 꾀를 따르지'));

  const rnksvVerses = await svc.getMergedChapterVerses('rnksv', 'krv', 'PSA', 1);
  assert.deepEqual(rnksvVerses[0].footnotes, ['㉠ 또는 "복되도다"']);
  assert.equal(rnksvVerses[0].parallelLabel, '개역한글');

  const nkrvHits = await svc.searchActiveVersion('악인들의 꾀를 따르지', 'nkrv');
  assert.equal(nkrvHits.length, 1);
  assert.equal(nkrvHits[0].versionId, 'nkrv');

  const rnksvHits = await svc.searchActiveVersion('악인의 꾀를 따르지', 'rnksv');
  assert.equal(rnksvHits.length, 1);
  assert.equal(rnksvHits[0].versionId, 'rnksv');
});

test('worship.json carries usageTiming and pastoralNote on all 645 hymns and >= 25 offline publicLyrics', async () => {
  const worshipPath = path.join(ROOT_DIR, 'web', 'data', 'worship.json');
  const worship = JSON.parse(fs.readFileSync(worshipPath, 'utf8'));
  const hymns = worship.hymns || [];
  assert.equal(hymns.length, 645);

  let publicLyricsCount = 0;
  for (const h of hymns) {
    assert.equal(typeof h.usageTiming, 'string', `Hymn #${h.num} missing usageTiming`);
    assert.ok(h.usageTiming.trim().length > 0, `Hymn #${h.num} has empty usageTiming`);
    assert.equal(typeof h.pastoralNote, 'string', `Hymn #${h.num} missing pastoralNote`);
    assert.ok(h.pastoralNote.trim().length > 0, `Hymn #${h.num} has empty pastoralNote`);
    if (typeof h.publicLyrics === 'string' && h.publicLyrics.trim().length > 0) {
      publicLyricsCount += 1;
    }
  }
  assert.equal(publicLyricsCount, 645, `Expected all 645 hymns with publicLyrics, got ${publicLyricsCount}`);

  const amazingGrace = hymns.find((h) => h.num === 305);
  assert.ok(amazingGrace?.publicLyrics?.includes('\n\n'), 'Hymn #305 must have multi-stanza publicLyrics');

  const prevDoc = globalThis.document;
  const makeNode = (tag) => {
    const node = {
      tagName: String(tag).toUpperCase(),
      attrs: {},
      dataset: {},
      children: [],
      listeners: {},
      className: '',
      textContent: '',
      setAttribute(k, v) { this.attrs[k] = String(v); },
      getAttribute(k) { return this.attrs[k] ?? null; },
      addEventListener(ev, fn) { (this.listeners[ev] ||= []).push(fn); },
      appendChild(child) { this.children.push(child); return child; },
      replaceChildren(...kids) {
        this.children = kids.flatMap((k) => (k?.tagName === 'FRAGMENT' ? k.children : [k]));
      },
    };
    return node;
  };
  const collectText = (node) => {
    if (!node) return '';
    if (typeof node === 'string') return node;
    if (node.nodeType === 3) return node.textContent;
    return [node.textContent || '', ...(node.children || []).map(collectText)].join(' ');
  };
  const viewWorship = makeNode('section');
  const detailEl = makeNode('div');
  const filterEl = makeNode('div');
  const listEl = makeNode('div');
  globalThis.document = {
    createElement: (t) => makeNode(t),
    createElementNS: (_ns, t) => makeNode(t),
    createDocumentFragment: () => makeNode('fragment'),
    createTextNode: (txt) => ({ nodeType: 3, textContent: String(txt) }),
    getElementById: (id) => ({
      viewWorship,
      worshipFilterBar: filterEl,
      worshipListContainer: listEl,
      worshipDetailContainer: detailEl,
    }[id] || null),
    querySelectorAll: () => [],
  };
  try {
    const store = createStore(null);
    store.state.worshipTab = 'hymns';
    store.state.worshipSearch = '';
    const panel = createWorshipPanel({ store, service: { worship }, callbacks: {} });
    panel.render();
    assert.equal(listEl.children.length, 645);

    store.state.worshipSearch = '305';
    panel.render();
    assert.ok(listEl.children.length >= 1);
    const firstCard = listEl.children[0];
    assert.ok(collectText(firstCard).includes('가사 내장'));
    assert.ok(collectText(firstCard).includes(amazingGrace.usageTiming));
    firstCard.listeners.click[0]();
    assert.ok(detailEl.children.every((c) => c !== null && c !== undefined));
    const detailText = collectText(detailEl);
    assert.ok(detailText.includes(amazingGrace.pastoralNote));
    assert.ok(detailText.includes('4절 수록'));
    const deck = panel.getActivePulpitDeck();
    assert.equal(deck.slides.length, 4);
    assert.ok(deck.slides[0].heading.includes('(1절)'));
    assert.ok(deck.slides[3].heading.includes('(4절)'));

    const noDriveHymn = hymns.find((h) => !h.driveId);
    assert.ok(noDriveHymn);
    store.state.worshipSearch = String(noDriveHymn.num);
    panel.render();
    listEl.children[0].listeners.click[0]();
    assert.ok(detailEl.children.every((c) => c !== null && c !== undefined));
    assert.equal(collectText(detailEl).includes('인터넷 연결이 필요하거나'), false);
  } finally {
    globalThis.document = prevDoc;
  }
});
