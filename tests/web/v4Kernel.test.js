import test from 'node:test';
import assert from 'node:assert/strict';

import { batch, computed, createHistory, effect, signal } from '../../web/js/kernel/signals.js';
import { createEventBus } from '../../web/js/kernel/eventBus.js';
import { createCommandRegistry } from '../../web/js/kernel/commandRegistry.js';
import { createPluginHost } from '../../web/js/kernel/pluginHost.js';
import { estimateSpeakingStats } from '../../web/js/features/sermonStudio.js';
import { BibleDataService } from '../../web/js/services/bibleService.js';

test('signals: reactive signal, computed, effect, and batch', () => {
  const count = signal(2);
  const doubled = computed(() => count() * 2);
  let runs = 0;
  const dispose = effect(() => {
    doubled();
    runs += 1;
  });
  assert.equal(doubled(), 4);
  assert.equal(runs, 1);

  batch(() => {
    count.set(3);
    count.set(5);
  });
  assert.equal(doubled(), 10);
  assert.equal(runs, 2);
  dispose();
  count.set(9);
  assert.equal(runs, 2);
});

test('signals: createHistory supports undo and redo', () => {
  const hist = createHistory(10);
  hist.push('GEN:1:1');
  hist.push('PSA:23:1');
  assert.equal(hist.canUndo(), true);
  assert.equal(hist.undo('ROM:8:28'), 'PSA:23:1');
  assert.equal(hist.canRedo(), true);
  assert.equal(hist.redo('PSA:23:1'), 'ROM:8:28');
});

test('eventBus: decoupled pub/sub and rolling trace', () => {
  const bus = createEventBus({ traceLimit: 5 });
  const received = [];
  const unsub = bus.on('passage:jump', (p) => received.push(p));
  bus.emit('passage:jump', { osis: 'JHN', chapter: 3, verse: 16 });
  unsub();
  bus.emit('passage:jump', { osis: 'ROM', chapter: 8, verse: 28 });
  assert.equal(received.length, 1);
  assert.equal(received[0].osis, 'JHN');
  assert.equal(bus.getTrace().length, 2);
});

test('commandRegistry: fuzzy command search and direct scripture warp', () => {
  const reg = createCommandRegistry();
  let executed = false;
  reg.register({
    id: 'lens:matrix',
    title: '다중 역본 매트릭스',
    category: '공간 렌즈',
    keywords: ['matrix', '비교'],
    run: () => { executed = true; },
  });

  const warpRes = reg.search('시 23:1');
  assert.equal(warpRes[0].category, '성경 워프');
  assert.equal(warpRes[0]._ref.osis, 'PSA');
  assert.equal(warpRes[0]._ref.chapter, 23);
  assert.equal(warpRes[0]._ref.verse, 1);

  const cmdRes = reg.search('매트릭스');
  assert.equal(cmdRes[0].id, 'lens:matrix');
  reg.execute('lens:matrix');
  assert.equal(executed, true);
});

test('pluginHost: mounts, unmounts, and emits lens:changed', () => {
  const bus = createEventBus();
  const host = createPluginHost({ bus });
  const log = [];
  host.register({ id: 'bible', mount: () => log.push('m:bible'), unmount: () => log.push('u:bible') });
  host.register({ id: 'graph', mount: () => log.push('m:graph'), unmount: () => log.push('u:graph') });
  host.activate('bible');
  host.activate('graph');
  assert.deepEqual(log, ['m:bible', 'u:bible', 'm:graph']);
  assert.equal(host.getActiveId(), 'graph');
});

test('sermonStudio: estimateSpeakingStats computes Korean speaking duration', () => {
  const stats = estimateSpeakingStats({
    targetDurationMins: 20,
    outline: [
      { id: '1', content: '가'.repeat(560) },
      { id: '2', content: '나'.repeat(280) },
    ],
  });
  assert.equal(stats.totalChars, 840);
  assert.equal(stats.estimatedMins, 3);
  assert.equal(stats.perBlock[0].mins, 2);
  assert.equal(stats.perBlock[1].mins, 1);
});

test('bibleService: getPolyglotChapterVerses aligns multiple translations', async () => {
  const mockData = {
    './data/manifest.json': {
      defaultVersion: 'nkrv',
      versions: [
        { id: 'nkrv', nameKr: '개역개정', lang: 'ko', default: true, pathPrefix: './data/nkrv/' },
        { id: 'esv', nameKr: 'ESV', lang: 'en', pathPrefix: './data/esv/' },
      ],
      books: [{ bookId: 19, id: 'PSA', name: '시편', abbr: '시', totalChapters: 150, chapterVerses: [6] }],
    },
    './data/exegesis.json': { commentaries: [], sources: [], crossReferences: {}, chains: {}, strongs: {} },
    './data/worship.json': { hymns: [], responsiveReadings: [], liturgies: [], templates: [] },
    './data/graph.json': { nodes: [], edges: [], stats: { nodeCount: 0, edgeCount: 0 } },
    './data/nkrv/PSA.json': { chapters: { '23': ['여호와는 나의 목자시니 내게 부족함이 없으리로다'] } },
    './data/esv/PSA.json': { chapters: { '23': ['The LORD is my shepherd; I shall not want.'] } },
  };
  const fetcher = async (url) => ({
    ok: Object.prototype.hasOwnProperty.call(mockData, url),
    json: async () => mockData[url],
  });
  const svc = new BibleDataService('./data', fetcher);
  await svc.init();
  const matrix = await svc.getPolyglotChapterVerses(['nkrv', 'esv'], 'PSA', 23);
  assert.equal(matrix.columns.length, 2);
  assert.equal(matrix.rows.length, 1);
  assert.equal(matrix.rows[0].texts[0], '여호와는 나의 목자시니 내게 부족함이 없으리로다');
  assert.equal(matrix.rows[0].texts[1], 'The LORD is my shepherd; I shall not want.');
});
