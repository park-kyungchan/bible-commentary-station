import test from 'node:test';
import assert from 'node:assert/strict';
import {
  matchWorshipItem,
  normalizeSearchText,
  normalizeWorshipQuery,
  parseKoreanRef,
  resolveOsisAlias,
  tokenizeSearchQuery,
} from '../../web/js/core/koreanQuery.js';

test('resolveOsisAlias is prototype-safe and removes ambiguous aliases', () => {
  assert.equal(resolveOsisAlias('constructor'), null);
  assert.equal(resolveOsisAlias('__proto__'), null);
  assert.equal(resolveOsisAlias('toString'), null);
  assert.equal(resolveOsisAlias('valueOf'), null);
  assert.equal(resolveOsisAlias('에스'), null);

  assert.equal(resolveOsisAlias('창세기'), 'GEN');
  assert.equal(resolveOsisAlias('계시록'), 'REV');
  assert.equal(resolveOsisAlias('고린도 전서'), '1CO');
  assert.equal(resolveOsisAlias('요한3서'), '3JN');
  assert.equal(resolveOsisAlias('에스라'), 'EZR');
  assert.equal(resolveOsisAlias('에스더'), 'EST');
});

test('parseKoreanRef handles natural Korean and English scripture queries', () => {
  assert.deepEqual(parseKoreanRef('계시록 21:4'), { osis: 'REV', chapter: 21, verse: 4, endVerse: 4 });
  assert.deepEqual(parseKoreanRef('시편 23편 4절'), { osis: 'PSA', chapter: 23, verse: 4, endVerse: 4 });
  assert.deepEqual(parseKoreanRef('시 23편 1절'), { osis: 'PSA', chapter: 23, verse: 1, endVerse: 1 });
  assert.deepEqual(parseKoreanRef('고린도 전서 13장'), { osis: '1CO', chapter: 13, verse: 1, endVerse: 1 });
  assert.deepEqual(parseKoreanRef('요한3서 1:2'), { osis: '3JN', chapter: 1, verse: 2, endVerse: 2 });
  assert.deepEqual(parseKoreanRef('요한1서 4:9'), { osis: '1JN', chapter: 4, verse: 9, endVerse: 9 });
  assert.deepEqual(parseKoreanRef('창22:2'), { osis: 'GEN', chapter: 22, verse: 2, endVerse: 2 });
  assert.deepEqual(parseKoreanRef('Ps 23:1'), { osis: 'PSA', chapter: 23, verse: 1, endVerse: 1 });
  assert.deepEqual(parseKoreanRef('1 Cor 13:4'), { osis: '1CO', chapter: 13, verse: 4, endVerse: 4 });
  assert.deepEqual(parseKoreanRef('요한복음 3:16-18'), { osis: 'JHN', chapter: 3, verse: 16, endVerse: 18 });
});

test('parseKoreanRef rejects invalid bounds and reversed ranges', () => {
  const bounds = { GEN: { totalChapters: 50, chapterVerses: { 1: 31 } } };
  assert.equal(parseKoreanRef('창세기 0:1', bounds), null);
  assert.equal(parseKoreanRef('창세기 51:1', bounds), null);
  assert.equal(parseKoreanRef('창세기 1:999', bounds), null);
  assert.equal(parseKoreanRef('요한복음 3:16-10'), null);
  assert.equal(parseKoreanRef('여호와는 나의 목자시니'), null);
});

test('worship query normalizer matches placeholder examples and Korean suffixes', () => {
  const qPsalm = normalizeWorshipQuery('시편 23');
  assert.equal(matchWorshipItem({ num: 11, title: '시편23편', season: '위로' }, qPsalm, 'responsive'), true);

  const qHymn = normalizeWorshipQuery('305장');
  assert.equal(qHymn.num, 305);
  assert.equal(matchWorshipItem({ num: 305, old: 405, title: '나 같은 죄인 살리신' }, qHymn, 'hymns'), true);

  const qNewHymn = normalizeWorshipQuery('새찬송가 305');
  assert.equal(qNewHymn.num, 305);
  assert.equal(matchWorshipItem({ num: 305, old: 405, title: '나 같은 죄인 살리신' }, qNewHymn, 'hymns'), true);

  const qRr = normalizeWorshipQuery('11번');
  assert.equal(qRr.num, 11);
  assert.equal(matchWorshipItem({ num: 11, title: '시편23편' }, qRr, 'responsive'), true);
});

test('search text normalization strips punctuation and spaces cleanly', () => {
  assert.equal(normalizeSearchText('여호와는 나의 목자시니!'), '여호와는나의목자시니');
  assert.deepEqual(tokenizeSearchQuery('하나님, 사랑?'), ['하나님', '사랑']);
});
