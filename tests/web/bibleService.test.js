import test from 'node:test';
import assert from 'node:assert/strict';
import { BibleDataService } from '../../web/js/services/bibleService.js';

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
