import test from 'node:test';
import assert from 'node:assert/strict';
import {
  createDefaultSermon,
  parseCustomBibleFile,
  SermonArchiveStore,
  validateByotFileSize,
} from '../../web/js/services/storage.js';
import { MAX_BYOT_FILE_BYTES } from '../../web/js/core/urlSafety.js';

function createMockIdbFactory({ shouldFail = false } = {}) {
  const stores = new Map();
  let openCount = 0;

  const makeStore = (name, keyPath) => {
    const map = new Map();
    stores.set(name, { keyPath, map });
    return { keyPath, map };
  };

  const db = {
    objectStoreNames: { contains: (name) => stores.has(name) },
    createObjectStore: (name, opts) => makeStore(name, opts.keyPath),
    close() {},
    transaction(storeName) {
      const storeRec = stores.get(storeName);
      const tx = { oncomplete: null, onerror: null, onabort: null };
      tx.objectStore = () => ({
        getAll() {
          const req = { result: null, onsuccess: null, onerror: null };
          queueMicrotask(() => {
            req.result = Array.from(storeRec.map.values()).map((v) => structuredClone(v));
            req.onsuccess?.();
          });
          return req;
        },
        put(val) {
          storeRec.map.set(val[storeRec.keyPath], structuredClone(val));
          queueMicrotask(() => tx.oncomplete?.());
        },
        delete(key) {
          storeRec.map.delete(key);
          queueMicrotask(() => tx.oncomplete?.());
        },
        clear() {
          storeRec.map.clear();
          queueMicrotask(() => tx.oncomplete?.());
        },
      });
      return tx;
    },
  };

  return {
    getOpenCount: () => openCount,
    factory: {
      open() {
        openCount += 1;
        const req = { result: db, error: null, onupgradeneeded: null, onsuccess: null, onerror: null };
        queueMicrotask(() => {
          if (shouldFail) {
            req.error = new Error('QuotaExceededError');
            req.onerror?.();
            return;
          }
          if (stores.size === 0) req.onupgradeneeded?.();
          req.onsuccess?.();
        });
        return req;
      },
    },
  };
}

test('SermonArchiveStore caches singleton IDBDatabase handle across 20 consecutive saves', async () => {
  const mock = createMockIdbFactory();
  const store = new SermonArchiveStore({ idbFactory: mock.factory, localStorageRef: null });
  const sermon = createDefaultSermon();

  for (let i = 0; i < 20; i += 1) {
    sermon.title = `설교 수정 ${i + 1}`;
    const res = await store.saveSermon(sermon);
    assert.equal(res.persisted, 'idb');
    assert.ok(res.savedAt);
  }
  assert.equal(mock.getOpenCount(), 1, 'IDB open() must be called only once');
});

test('IDB failure returns persisted: memory and notifies warning callback honestly', async () => {
  const mock = createMockIdbFactory({ shouldFail: true });
  const events = [];
  const store = new SermonArchiveStore({
    idbFactory: mock.factory,
    localStorageRef: null,
    onPersistenceChange: (ev) => events.push(ev),
  });

  const res = await store.saveSermon(createDefaultSermon());
  assert.equal(res.persisted, 'memory');
  assert.ok(res.error);
  assert.ok(events.some((e) => e.mode === 'memory'));
});

test('JSON backup and restore round-trips sermons, worship orders, highlights, and prefs losslessly', async () => {
  const mockA = createMockIdbFactory();
  const storeA = new SermonArchiveStore({ idbFactory: mockA.factory, localStorageRef: null });
  const s1 = { ...createDefaultSermon(), id: 'sermon_test_1', title: '주일 오전 설교' };
  await storeA.saveSermon(s1);
  await storeA.saveWorshipOrder({ id: 'order_1', title: '주일 오전예배', date: '2026-11-22', slots: [{ order: 1, label: '찬송', slotType: 'hymn', value: '1장' }] });

  const backup = await storeA.exportBackupPayload({
    highlights: { '19023001': { color: 'yellow', osis: 'PSA', chapter: 23, verse: 1, text: '여호와는 나의 목자시니' } },
    prefs: { theme: 'dark', fontStepIndex: 3, primaryVersion: 'krv', parallelVersion: 'none', pulpitFontPt: 40 },
  });

  const mockB = createMockIdbFactory();
  const storeB = new SermonArchiveStore({ idbFactory: mockB.factory, localStorageRef: null });
  const restored = await storeB.importBackupPayload(JSON.stringify(backup));

  assert.equal(restored.sermons.length, 1);
  assert.equal(restored.sermons[0].title, '주일 오전 설교');
  assert.equal(restored.worshipOrders.length, 1);
  assert.equal(restored.worshipOrders[0].title, '주일 오전예배');
  assert.equal(restored.highlights['19023001'].color, 'yellow');
  assert.equal(restored.prefs.fontStepIndex, 3);

  const listed = await storeB.listSermons();
  assert.equal(listed[0].id, 'sermon_test_1');
});

test('scheduleSermonSave debounces rapid edits and flushPendingSaves commits immediately', async () => {
  const mock = createMockIdbFactory();
  const store = new SermonArchiveStore({ idbFactory: mock.factory, localStorageRef: null });
  const sermon = { ...createDefaultSermon(), id: 'sermon_debounce' };
  let callbackCount = 0;

  store.scheduleSermonSave({ ...sermon, title: '초안 1' }, 500, () => { callbackCount += 1; });
  store.scheduleSermonSave({ ...sermon, title: '초안 2' }, 500, () => { callbackCount += 1; });
  store.scheduleSermonSave({ ...sermon, title: '최종본' }, 500, () => { callbackCount += 1; });

  const results = await store.flushPendingSaves();
  assert.equal(results.length, 1);
  assert.equal(callbackCount, 1);
  const listed = await store.listSermons();
  assert.equal(listed.find((s) => s.id === 'sermon_debounce')?.title, '최종본');
});

test('BYOT file size guard rejects files > 15 MB and parser ignores prototype keys', () => {
  assert.equal(validateByotFileSize({ size: MAX_BYOT_FILE_BYTES }).ok, true);
  assert.equal(validateByotFileSize({ size: MAX_BYOT_FILE_BYTES + 1 }).ok, false);

  const parsed = parseCustomBibleFile('constructor 1:1 injected\n__proto__ 1:1 bad\n창1:1 태초에 하나님이 천지를 창조하시니라', 'my.txt');
  assert.equal(parsed.verseCount, 1);
  assert.deepEqual(Object.keys(parsed.books), ['GEN']);
  assert.equal(parsed.books.GEN['1']['1'], '태초에 하나님이 천지를 창조하시니라');
});
