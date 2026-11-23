import { resolveOsisAlias } from '../core/koreanQuery.js';
import { MAX_BYOT_FILE_BYTES } from '../core/urlSafety.js';

const DB_NAME = 'BibleStationDB';
const DB_VERSION = 3;
const STORES = { SERMONS: 'sermons', BIBLES: 'custom_bibles', HYMNS: 'custom_hymns', ORDERS: 'worship_orders' };
const LEGACY_KEY = 'bibleWorkstation.sermonDraft.v1';

let uidSeq = 0;
function makeUid(prefix) {
  uidSeq += 1;
  return globalThis.crypto?.randomUUID ? `${prefix}_${globalThis.crypto.randomUUID()}` : `${prefix}_${Date.now()}_${uidSeq}`;
}

export function validateByotFileSize(fileOrBytes) {
  const bytes = typeof fileOrBytes === 'number' ? fileOrBytes : Number(fileOrBytes?.size ?? 0);
  return bytes > MAX_BYOT_FILE_BYTES
    ? { ok: false, error: '파일 크기가 15메가바이트를 넘어 불러올 수 없습니다. 더 작은 파일을 선택해 주세요.' }
    : { ok: true };
}

export function parseCustomBibleFile(rawText, fileName = 'custom.txt', versionName = '') {
  const books = Object.create(null);
  let verseCount = 0;
  const putVerse = (osis, ch, vs, text) => {
    const clean = String(text || '').trim();
    if (!osis || !Number.isInteger(ch) || ch < 1 || !Number.isInteger(vs) || vs < 1 || !clean) return;
    if (!books[osis]) books[osis] = Object.create(null);
    if (!books[osis][String(ch)]) books[osis][String(ch)] = Object.create(null);
    books[osis][String(ch)][String(vs)] = clean;
    verseCount += 1;
  };

  const trimmed = String(rawText || '').trim();
  if (trimmed.startsWith('{') || trimmed.startsWith('[')) {
    const parsed = JSON.parse(trimmed);
    if (Array.isArray(parsed)) {
      for (const r of parsed) {
        if (r && typeof r === 'object') putVerse(resolveOsisAlias(r.osis || r.book || r.book_name), Number(r.chapter || r.ch), Number(r.verse || r.vs), r.text || r.content);
      }
    } else if (parsed && typeof parsed === 'object') {
      for (const [bookKey, chapters] of Object.entries(parsed.books || parsed)) {
        const osis = resolveOsisAlias(bookKey);
        if (!osis || !chapters || typeof chapters !== 'object') continue;
        const chMap = chapters.chapters && typeof chapters.chapters === 'object' ? chapters.chapters : chapters;
        for (const [chKey, verses] of Object.entries(chMap)) {
          if (Array.isArray(verses)) verses.forEach((t, idx) => putVerse(osis, Number(chKey), idx + 1, t));
          else if (verses && typeof verses === 'object') for (const [vsKey, t] of Object.entries(verses)) putVerse(osis, Number(chKey), Number(vsKey), t);
        }
      }
    }
  } else {
    const lineRe = /^([가-힣A-Za-z0-9\s]+?)\s*(\d+)\s*(?::|장\s*|편\s*)\s*(\d+)\s*절?\s+(.+)$/;
    for (const rawLine of trimmed.split(/\r?\n/)) {
      const line = rawLine.trim();
      if (!line || line.startsWith('#') || line.startsWith('//')) continue;
      const m = line.match(lineRe);
      if (m) putVerse(resolveOsisAlias(m[1]), Number(m[2]), Number(m[3]), m[4]);
    }
  }

  const plainBooks = JSON.parse(JSON.stringify(books));
  const cleanName = (versionName || String(fileName).replace(/\.(txt|json)$/i, '') || '내 성경 역본').trim();
  return {
    id: makeUid('custom'), name: cleanName, shortName: cleanName.slice(0, 12),
    books: plainBooks, bookCount: Object.keys(plainBooks).length, verseCount, importedAt: new Date().toISOString(),
  };
}

export function parseCustomHymnFile(rawText) {
  const map = {};
  const trimmed = String(rawText || '').trim();
  if (trimmed.startsWith('{')) {
    for (const [k, v] of Object.entries(JSON.parse(trimmed))) {
      const n = Number(String(k).replace(/[^\d]/g, ''));
      if (n >= 1 && n <= 645 && typeof v === 'string' && v.trim()) map[n] = v.trim();
    }
    return map;
  }
  let currentNum = null;
  let buf = [];
  const flush = () => { if (currentNum && buf.length) map[currentNum] = buf.join('\n').trim(); buf = []; };
  for (const rawLine of trimmed.split(/\r?\n/)) {
    const line = rawLine.trim();
    const header = line.match(/^(?:\[|===?\s*)?(?:새찬송가\s*|찬송가\s*)?(\d{1,3})장(?:\s*[:.\-\]]|\s|$)/);
    if (header) {
      flush();
      const n = Number(header[1]);
      currentNum = n >= 1 && n <= 645 ? n : null;
      const rest = line.slice(header[0].length).trim();
      if (rest) buf.push(rest);
    } else if (currentNum) buf.push(rawLine);
  }
  flush();
  return map;
}

export function createDefaultSermon() {
  return {
    id: makeUid('sermon'), title: '모리아 산의 온전한 순종과 여호와 이레의 축복',
    scriptureRef: '창세기 22:1-14', date: new Date().toISOString().slice(0, 10),
    targetDurationMins: 30, updatedAt: new Date().toISOString(),
    outline: [
      { id: makeUid('sec'), section: '서론', title: '믿음의 시험과 인생의 모리아 산', content: '하나님께서 아브라함을 부르실 때 즉각 응답한 믿음("내가 여기 있나이다"). 가장 소중한 약속 앞에서 신앙의 중심을 점검한다.' },
      { id: makeUid('sec'), section: '본론 I', title: '유일한 독자를 내려놓는 결단 (창 22:2)', content: '히브리어 "야히드"는 생명처럼 소중한 유일한 보물을 뜻한다. 선물보다 선물을 주신 하나님을 더 사랑하는 믿음.' },
      { id: makeUid('sec'), section: '본론 II', title: '묵묵히 사흘 길을 동행하는 순종 (창 22:3-9)', content: '아침 일찍 일어나 출발한 아브라함과 나무를 지고 오른 이삭의 순종은 십자가로 향하신 예수 그리스도의 예표.' },
      { id: makeUid('sec'), section: '결론', title: '여호와 이레의 예비하심과 결단 (창 22:13-14)', content: '순종의 끝에서 예비하시는 하나님. 오늘 나의 모리아 산에 무엇을 올려드릴 것인가?' },
    ],
    clips: [],
  };
}

export class SermonArchiveStore {
  constructor(options = {}) {
    this._idbFactory = options.idbFactory !== undefined ? options.idbFactory : globalThis.indexedDB;
    this._localStorage = options.localStorageRef !== undefined ? options.localStorageRef : globalThis.localStorage;
    this._onPersistenceChange = typeof options.onPersistenceChange === 'function' ? options.onPersistenceChange : null;
    this._dbPromise = null;
    this._mem = { [STORES.SERMONS]: new Map(), [STORES.BIBLES]: new Map(), [STORES.HYMNS]: new Map(), [STORES.ORDERS]: new Map() };
    this._pendingSermons = new Map();
    this._debounceTimers = new Map();
    this.persistenceMode = 'idb';
  }

  _notify(mode, error = null) { this.persistenceMode = mode; this._onPersistenceChange?.({ mode, error }); }

  _getDb() {
    if (this._dbPromise) return this._dbPromise;
    if (!this._idbFactory || typeof this._idbFactory.open !== 'function') {
      return Promise.reject(new Error('브라우저 내부 저장소를 사용할 수 없습니다.'));
    }
    this._dbPromise = new Promise((resolve, reject) => {
      try {
        const req = this._idbFactory.open(DB_NAME, DB_VERSION);
        req.onupgradeneeded = () => {
          const db = req.result;
          for (const [name, keyPath] of [[STORES.SERMONS, 'id'], [STORES.BIBLES, 'id'], [STORES.HYMNS, 'num'], [STORES.ORDERS, 'id']]) {
            if (!db.objectStoreNames.contains(name)) db.createObjectStore(name, { keyPath });
          }
        };
        req.onsuccess = () => {
          const db = req.result;
          if (db) { db.onclose = () => { this._dbPromise = null; }; db.onversionchange = () => { this._dbPromise = null; try { db.close(); } catch { /* noop */ } }; }
          resolve(db);
        };
        req.onerror = () => { this._dbPromise = null; reject(req.error || new Error('저장소 열기 실패')); };
      } catch (err) { this._dbPromise = null; reject(err); }
    });
    return this._dbPromise;
  }

  async _getAll(storeName) {
    const db = await this._getDb();
    return new Promise((resolve, reject) => {
      const req = db.transaction(storeName, 'readonly').objectStore(storeName).getAll();
      req.onsuccess = () => resolve(req.result || []);
      req.onerror = () => reject(req.error || new Error('읽기 오류'));
    });
  }

  async _write(storeName, fn, extra = {}) {
    const savedAt = new Date().toISOString();
    try {
      const db = await this._getDb();
      await new Promise((resolve, reject) => {
        const tx = db.transaction(storeName, 'readwrite');
        fn(tx.objectStore(storeName));
        tx.oncomplete = () => resolve();
        tx.onerror = () => reject(tx.error || new Error('쓰기 오류'));
        tx.onabort = () => reject(tx.error || new Error('쓰기 중단'));
      });
      this._notify('idb');
      return { persisted: 'idb', savedAt, ...extra };
    } catch (err) {
      this._notify('memory', err);
      return { persisted: 'memory', savedAt, error: err, ...extra };
    }
  }

  async listSermons() {
    try {
      const rows = await this._getAll(STORES.SERMONS);
      this._notify('idb');
      if (!rows.length) { const init = this._tryMigrateLegacy() || createDefaultSermon(); await this.saveSermon(init); return [init]; }
      rows.forEach((s) => this._mem[STORES.SERMONS].set(s.id, s));
      return rows.sort((a, b) => (b.updatedAt || '').localeCompare(a.updatedAt || ''));
    } catch (err) {
      this._notify('memory', err);
      if (!this._mem[STORES.SERMONS].size) { const def = createDefaultSermon(); this._mem[STORES.SERMONS].set(def.id, def); }
      return Array.from(this._mem[STORES.SERMONS].values());
    }
  }

  saveSermon(sermon) {
    const payload = { ...sermon, updatedAt: new Date().toISOString() };
    this._mem[STORES.SERMONS].set(payload.id, payload);
    return this._write(STORES.SERMONS, (s) => s.put(payload), { data: payload });
  }

  scheduleSermonSave(sermon, delayMs = 400, onSaved = null) {
    const id = sermon.id;
    this._pendingSermons.set(id, { sermon: { ...sermon }, onSaved });
    if (this._debounceTimers.has(id)) clearTimeout(this._debounceTimers.get(id));
    this._debounceTimers.set(id, setTimeout(() => {
      this._debounceTimers.delete(id);
      const p = this._pendingSermons.get(id);
      this._pendingSermons.delete(id);
      if (p) this.saveSermon(p.sermon).then((res) => p.onSaved?.(res));
    }, delayMs));
  }

  async flushPendingSaves() {
    for (const t of this._debounceTimers.values()) clearTimeout(t);
    this._debounceTimers.clear();
    const items = Array.from(this._pendingSermons.values());
    this._pendingSermons.clear();
    const out = [];
    for (const item of items) { const res = await this.saveSermon(item.sermon); item.onSaved?.(res); out.push(res); }
    return out;
  }

  deleteSermon(id) {
    if (this._debounceTimers.has(id)) { clearTimeout(this._debounceTimers.get(id)); this._debounceTimers.delete(id); this._pendingSermons.delete(id); }
    this._mem[STORES.SERMONS].delete(id);
    return this._write(STORES.SERMONS, (s) => s.delete(id));
  }

  async _listStore(storeName, keyField = 'id', sort = false) {
    try {
      const rows = await this._getAll(storeName);
      rows.forEach((r) => this._mem[storeName].set(r[keyField], r));
      return sort ? rows.sort((a, b) => (b.updatedAt || '').localeCompare(a.updatedAt || '')) : rows;
    } catch (err) { this._notify('memory', err); return Array.from(this._mem[storeName].values()); }
  }

  listCustomBibles() { return this._listStore(STORES.BIBLES, 'id'); }
  saveCustomBible(record) { this._mem[STORES.BIBLES].set(record.id, record); return this._write(STORES.BIBLES, (s) => s.put(record), { data: record }); }
  deleteCustomBible(id) { this._mem[STORES.BIBLES].delete(id); return this._write(STORES.BIBLES, (s) => s.delete(id)); }
  async getCustomHymnLyricsMap() { const out = {}; for (const r of await this._listStore(STORES.HYMNS, 'num')) out[r.num] = r.lyrics ?? r; return out; }
  saveCustomHymnLyrics(lyricsMap) {
    const entries = Object.entries(lyricsMap || {});
    for (const [k, v] of entries) this._mem[STORES.HYMNS].set(Number(k), { num: Number(k), lyrics: v });
    return this._write(STORES.HYMNS, (s) => { for (const [k, v] of entries) s.put({ num: Number(k), lyrics: v }); }, { count: entries.length });
  }
  clearCustomHymnLyrics() { this._mem[STORES.HYMNS].clear(); return this._write(STORES.HYMNS, (s) => s.clear()); }
  listWorshipOrders() { return this._listStore(STORES.ORDERS, 'id', true); }
  saveWorshipOrder(order) {
    const payload = { ...order, id: order.id || makeUid('order'), updatedAt: new Date().toISOString() };
    this._mem[STORES.ORDERS].set(payload.id, payload);
    return this._write(STORES.ORDERS, (s) => s.put(payload), { data: payload });
  }
  deleteWorshipOrder(id) { this._mem[STORES.ORDERS].delete(id); return this._write(STORES.ORDERS, (s) => s.delete(id)); }

  async exportBackupPayload({ highlights = {}, prefs = {} } = {}) {
    await this.flushPendingSaves();
    const [sermons, worshipOrders] = await Promise.all([this.listSermons(), this.listWorshipOrders()]);
    return { format: 'bible-station-backup', schemaVersion: 3, exportedAt: new Date().toISOString(), sermons, worshipOrders, highlights, prefs };
  }

  async importBackupPayload(rawText) {
    const parsed = typeof rawText === 'string' ? JSON.parse(rawText) : rawText;
    if (!parsed || typeof parsed !== 'object' || !Array.isArray(parsed.sermons)) throw new Error('올바른 백업 파일 형식이 아닙니다.');
    const sermons = [];
    for (const s of parsed.sermons) if (s?.id && typeof s.title === 'string') sermons.push((await this.saveSermon(s)).data);
    const worshipOrders = [];
    for (const o of Array.isArray(parsed.worshipOrders) ? parsed.worshipOrders : []) {
      if (o?.id && typeof o.title === 'string') worshipOrders.push((await this.saveWorshipOrder(o)).data);
    }
    return {
      sermons, worshipOrders,
      highlights: parsed.highlights && typeof parsed.highlights === 'object' ? parsed.highlights : null,
      prefs: parsed.prefs && typeof parsed.prefs === 'object' ? parsed.prefs : null,
    };
  }

  _tryMigrateLegacy() {
    try {
      const raw = this._localStorage?.getItem(LEGACY_KEY);
      if (!raw) return null;
      const legacy = JSON.parse(raw);
      return {
        id: makeUid('migrated'), title: legacy.title || '이전 설교 초안', scriptureRef: legacy.passage || '창세기 22:1-14',
        date: new Date().toISOString().slice(0, 10), targetDurationMins: 30, updatedAt: new Date().toISOString(),
        outline: Array.isArray(legacy.cards) && legacy.cards.length
          ? legacy.cards.map((c, i) => ({ id: makeUid('mig'), section: c.tag || `대지 ${i + 1}`, title: c.title || '', content: c.content || '' }))
          : createDefaultSermon().outline,
        clips: [],
      };
    } catch { return null; }
  }

  static toMarkdown(sermon) {
    const lines = [`# ${sermon.title}`, `- 본문: ${sermon.scriptureRef}`, `- 날짜: ${sermon.date}`, `- 목표 시간: ${sermon.targetDurationMins}분`, ''];
    for (const item of sermon.outline || []) lines.push(`## [${item.section}] ${item.title}`, '', item.content || '', '');
    if (sermon.clips?.length) {
      lines.push('---', '## 인용·스크랩 자료', '');
      for (const clip of sermon.clips) lines.push(`- ${clip.source}: ${clip.text}`);
    }
    return lines.join('\n');
  }
}
