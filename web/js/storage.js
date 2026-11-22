/**
 * IndexedDB Multi-Sermon, Custom BYOT Bible Versions & Custom Hymn Lyrics Storage Engine (v2.5)
 * - 100% local in-browser storage (zero external upload, full copyright compliance for personal GAE/hymn files)
 * - Automatically migrates legacy localStorage sermon drafts
 * - Parses .txt (창1:1 / 창세기 1:1 / GEN 1:1) and .json personal Bible & Hymn files
 */

const DB_NAME = 'BibleStationDB';
const DB_VERSION = 2;
const STORE_SERMONS = 'sermons';
const STORE_CUSTOM_BIBLES = 'custom_bibles';
const STORE_CUSTOM_HYMNS = 'custom_hymns';
const LEGACY_KEY = 'bibleWorkstation.sermonDraft.v1';

// Korean abbreviations + full names -> OSIS 66-book lookup map for BYOT .txt/.json Bible import
const BOOK_ALIAS_TO_OSIS = {
  // Old Testament (39)
  '창': 'GEN', '창세기': 'GEN', 'gen': 'GEN',
  '출': 'EXO', '출애굽기': 'EXO', 'exo': 'EXO',
  '레': 'LEV', '레위기': 'LEV', 'lev': 'LEV',
  '민': 'NUM', '민수기': 'NUM', 'num': 'NUM',
  '신': 'DEU', '신명기': 'DEU', 'deu': 'DEU',
  '수': 'JOS', '여호수아': 'JOS', 'jos': 'JOS',
  '삿': 'JDG', '사사기': 'JDG', 'jdg': 'JDG',
  '룻': 'RUT', '룻기': 'RUT', 'rut': 'RUT',
  '삼상': '1SA', '사무엘상': '1SA', '1sa': '1SA',
  '삼하': '2SA', '사무엘하': '2SA', '2sa': '2SA',
  '왕상': '1KI', '열왕기상': '1KI', '1ki': '1KI',
  '왕하': '2KI', '열왕기하': '2KI', '2ki': '2KI',
  '대상': '1CH', '역대상': '1CH', '1ch': '1CH',
  '대하': '2CH', '역대하': '2CH', '2ch': '2CH',
  '스': 'EZR', '에스라': 'EZR', 'ezr': 'EZR',
  '느': 'NEH', '느헤미야': 'NEH', 'neh': 'NEH',
  '에': 'EST', '에스더': 'EST', 'est': 'EST',
  '욥': 'JOB', '욥기': 'JOB', 'job': 'JOB',
  '시': 'PSA', '시편': 'PSA', 'psa': 'PSA',
  '잠': 'PRO', '잠언': 'PRO', 'pro': 'PRO',
  '전': 'ECC', '전도서': 'ECC', 'ecc': 'ECC',
  '아': 'SNG', '아가': 'SNG', 'sng': 'SNG',
  '사': 'ISA', '이사야': 'ISA', 'isa': 'ISA',
  '렘': 'JER', '예레미야': 'JER', 'jer': 'JER',
  '애': 'LAM', '예레미야애가': 'LAM', '예레미야 애가': 'LAM', 'lam': 'LAM',
  '겔': 'EZK', '에스겔': 'EZK', 'ezk': 'EZK',
  '단': 'DAN', '다니엘': 'DAN', 'dan': 'DAN',
  '호': 'HOS', '호세아': 'HOS', 'hos': 'HOS',
  '욜': 'JOL', '요엘': 'JOL', 'jol': 'JOL',
  '암': 'AMO', '아모스': 'AMO', 'amo': 'AMO',
  '옵': 'OBA', '오바댜': 'OBA', 'oba': 'OBA',
  '욘': 'JON', '요나': 'JON', 'jon': 'JON',
  '미': 'MIC', '미가': 'MIC', 'mic': 'MIC',
  '나': 'NAM', '나훔': 'NAM', 'nam': 'NAM',
  '합': 'HAB', '하박국': 'HAB', 'hab': 'HAB',
  '습': 'ZEP', '스바냐': 'ZEP', 'zep': 'ZEP',
  '학': 'HAG', '학개': 'HAG', 'hag': 'HAG',
  '슥': 'ZEC', '스가랴': 'ZEC', 'zec': 'ZEC',
  '말': 'MAL', '말라기': 'MAL', 'mal': 'MAL',
  // New Testament (27)
  '마': 'MAT', '마태복음': 'MAT', 'mat': 'MAT',
  '막': 'MRK', '마가복음': 'MRK', 'mrk': 'MRK',
  '눅': 'LUK', '누가복음': 'LUK', 'luk': 'LUK',
  '요': 'JHN', '요한복음': 'JHN', 'jhn': 'JHN',
  '행': 'ACT', '사도행전': 'ACT', 'act': 'ACT',
  '롬': 'ROM', '로마서': 'ROM', 'rom': 'ROM',
  '고전': '1CO', '고린도전서': '1CO', '1co': '1CO',
  '고후': '2CO', '고린도후서': '2CO', '2co': '2CO',
  '갈': 'GAL', '갈라디아서': 'GAL', 'gal': 'GAL',
  '엡': 'EPH', '에베소서': 'EPH', 'eph': 'EPH',
  '빌': 'PHP', '빌립보서': 'PHP', 'php': 'PHP',
  '골': 'COL', '골로새서': 'COL', 'col': 'COL',
  '살전': '1TH', '데살로니가전서': '1TH', '1th': '1TH',
  '살후': '2TH', '데살로니가후서': '2TH', '2th': '2TH',
  '딤전': '1TI', '디모데전서': '1TI', '1ti': '1TI',
  '딤후': '2TI', '디모데후서': '2TI', '2ti': '2TI',
  '딛': 'TIT', '디도서': 'TIT', 'tit': 'TIT',
  '몬': 'PHM', '빌레몬서': 'PHM', 'phm': 'PHM',
  '히': 'HEB', '히브리서': 'HEB', 'heb': 'HEB',
  '약': 'JAS', '야고보서': 'JAS', 'jas': 'JAS',
  '벧전': '1PE', '베드로전서': '1PE', '1pe': '1PE',
  '벧후': '2PE', '베드로후서': '2PE', '2pe': '2PE',
  '요일': '1JN', '요한일서': '1JN', '요한1서': '1JN', '1jn': '1JN',
  '요이': '2JN', '요한이서': '2JN', '요한2서': '2JN', '2jn': '2JN',
  '요삼': '3JN', '요한삼서': '3JN', '요한3서': '3JN', '3jn': '3JN',
  '유': 'JUD', '유다서': 'JUD', 'jud': 'JUD',
  '계': 'REV', '요한계시록': 'REV', 'rev': 'REV',
};

export function resolveOsisAlias(raw) {
  const key = String(raw || '').trim().toLowerCase().replace(/\s+/g, '');
  if (!key) return null;
  return BOOK_ALIAS_TO_OSIS[key] || BOOK_ALIAS_TO_OSIS[String(raw || '').trim()] || null;
}

/**
 * Parse a user-provided personal Bible text or JSON file into normalized { books: { OSIS: { ch: { vs: text } } }, verseCount }
 */
export function parseCustomBibleFile(rawText, fileName = 'custom.txt', versionName = '') {
  const books = {};
  let verseCount = 0;

  const putVerse = (osis, ch, vs, text) => {
    if (!osis || !ch || !vs || !text) return;
    if (!books[osis]) books[osis] = {};
    const chKey = String(ch);
    if (!books[osis][chKey]) books[osis][chKey] = {};
    books[osis][chKey][String(vs)] = String(text).trim();
    verseCount += 1;
  };

  const trimmed = String(rawText || '').trim();
  if (trimmed.startsWith('{') || trimmed.startsWith('[')) {
    const parsed = JSON.parse(trimmed);
    if (Array.isArray(parsed)) {
      for (const row of parsed) {
        const osis = resolveOsisAlias(row.osis || row.book || row.book_name);
        putVerse(osis, Number(row.chapter || row.ch), Number(row.verse || row.vs), row.text || row.content);
      }
    } else if (parsed && typeof parsed === 'object') {
      const root = parsed.books || parsed;
      for (const [bookKey, chapters] of Object.entries(root)) {
        const osis = resolveOsisAlias(bookKey);
        if (!osis || !chapters || typeof chapters !== 'object') continue;
        for (const [chKey, verses] of Object.entries(chapters)) {
          if (Array.isArray(verses)) {
            verses.forEach((t, idx) => putVerse(osis, Number(chKey), idx + 1, t));
          } else if (verses && typeof verses === 'object') {
            for (const [vsKey, t] of Object.entries(verses)) {
              putVerse(osis, Number(chKey), Number(vsKey), t);
            }
          }
        }
      }
    }
  } else {
    // Line-based text: "창1:1 태초에...", "창세기 1:1 태초에...", "GEN 1:1 In the beginning..."
    const lineRe = /^([가-힣A-Za-z0-9]+)\s*(\d+)\s*:\s*(\d+)\s+(.+)$/;
    for (const rawLine of trimmed.split(/\r?\n/)) {
      const line = rawLine.trim();
      if (!line || line.startsWith('#') || line.startsWith('//')) continue;
      const m = line.match(lineRe);
      if (!m) continue;
      const osis = resolveOsisAlias(m[1]);
      if (osis) putVerse(osis, Number(m[2]), Number(m[3]), m[4]);
    }
  }

  const cleanName = (versionName || fileName.replace(/\.(txt|json)$/i, '') || '내 성경 역본').trim();
  return {
    id: `custom_${Date.now()}`,
    name: cleanName,
    shortName: cleanName.slice(0, 12),
    books,
    bookCount: Object.keys(books).length,
    verseCount,
    importedAt: new Date().toISOString(),
  };
}

/**
 * Parse a user-provided personal hymn lyrics .json or .txt file into { [num]: lyricsText }
 */
export function parseCustomHymnFile(rawText) {
  const map = {};
  const trimmed = String(rawText || '').trim();
  if (trimmed.startsWith('{')) {
    const parsed = JSON.parse(trimmed);
    for (const [k, v] of Object.entries(parsed)) {
      const n = Number(String(k).replace(/[^\d]/g, ''));
      if (n >= 1 && n <= 645 && typeof v === 'string' && v.trim()) {
        map[n] = v.trim();
      }
    }
    return map;
  }
  // TXT format separated by lines like "1장 ..." or "[1장]" or "=== 1 ==="
  let currentNum = null;
  let buf = [];
  const flush = () => {
    if (currentNum && buf.length) {
      map[currentNum] = buf.join('\n').trim();
    }
    buf = [];
  };
  for (const rawLine of trimmed.split(/\r?\n/)) {
    const line = rawLine.trim();
    const header = line.match(/^(?:\[|===?\s*)?(?:새찬송가\s*|찬송가\s*)?(\d{1,3})장(?:\s*[:.\-\]]|\s|$)/);
    if (header) {
      flush();
      const n = Number(header[1]);
      currentNum = n >= 1 && n <= 645 ? n : null;
      const rest = line.slice(header[0].length).trim();
      if (rest) buf.push(rest);
    } else if (currentNum) {
      buf.push(rawLine);
    }
  }
  flush();
  return map;
}

export function createDefaultSermon() {
  return {
    id: `sermon_${Date.now()}`,
    title: '모리아 산의 온전한 순종과 여호와 이레의 축복',
    scriptureRef: '창세기 22:1-14',
    date: new Date().toISOString().slice(0, 10),
    targetDurationMins: 30,
    updatedAt: new Date().toISOString(),
    outline: [
      {
        id: 'sec_1',
        section: '서론',
        title: '믿음의 시험과 인생의 모리아 산',
        content: '하나님께서 아브라함을 부르실 때 즉각 응답한 믿음("내가 여기 있나이다"). 가장 소중한 약속 앞에서 신앙의 중심을 점검한다.',
      },
      {
        id: 'sec_2',
        section: '본론 I',
        title: '유일한 독자(야히드)를 내려놓는 결단 (창 22:2)',
        content: '히브리어 "야히드"는 생명처럼 소중한 유일한 보물을 뜻한다. 선물보다 선물을 주신 하나님을 더 사랑하는 믿음.',
      },
      {
        id: 'sec_3',
        section: '본론 II',
        title: '묵묵히 사흘 길을 동행하는 순종 (창 22:3-9)',
        content: '아침 일찍 일어나 출발한 아브라함과 나무를 지고 오른 이삭의 순종은 십자가로 향하신 예수 그리스도의 예표.',
      },
      {
        id: 'sec_4',
        section: '결론',
        title: '여호와 이레의 예비하심과 결단 (창 22:13-14)',
        content: '순종의 끝에서 예비하시는 하나님. 오늘 나의 모리아 산에 무엇을 올려드릴 것인가?',
      },
    ],
    clips: [],
  };
}

function openDb() {
  return new Promise((resolve, reject) => {
    if (typeof indexedDB === 'undefined') {
      reject(new Error('IndexedDB unavailable'));
      return;
    }
    const req = indexedDB.open(DB_NAME, DB_VERSION);
    req.onupgradeneeded = () => {
      const db = req.result;
      if (!db.objectStoreNames.contains(STORE_SERMONS)) {
        db.createObjectStore(STORE_SERMONS, { keyPath: 'id' });
      }
      if (!db.objectStoreNames.contains(STORE_CUSTOM_BIBLES)) {
        db.createObjectStore(STORE_CUSTOM_BIBLES, { keyPath: 'id' });
      }
      if (!db.objectStoreNames.contains(STORE_CUSTOM_HYMNS)) {
        db.createObjectStore(STORE_CUSTOM_HYMNS, { keyPath: 'num' });
      }
    };
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}

export class SermonArchiveStore {
  constructor() {
    this._memoryFallback = new Map();
    this._customBiblesMem = new Map();
    this._customHymnsMem = new Map();
  }

  async listSermons() {
    try {
      const db = await openDb();
      const sermons = await new Promise((resolve, reject) => {
        const tx = db.transaction(STORE_SERMONS, 'readonly');
        const req = tx.objectStore(STORE_SERMONS).getAll();
        req.onsuccess = () => resolve(req.result || []);
        req.onerror = () => reject(req.error);
      });
      if (sermons.length === 0) {
        const migrated = this._tryMigrateLegacy() || createDefaultSermon();
        await this.saveSermon(migrated);
        return [migrated];
      }
      return sermons.sort((a, b) => (b.updatedAt || '').localeCompare(a.updatedAt || ''));
    } catch {
      if (this._memoryFallback.size === 0) {
        const def = createDefaultSermon();
        this._memoryFallback.set(def.id, def);
      }
      return Array.from(this._memoryFallback.values());
    }
  }

  async saveSermon(sermon) {
    const payload = { ...sermon, updatedAt: new Date().toISOString() };
    this._memoryFallback.set(payload.id, payload);
    try {
      const db = await openDb();
      await new Promise((resolve, reject) => {
        const tx = db.transaction(STORE_SERMONS, 'readwrite');
        tx.objectStore(STORE_SERMONS).put(payload);
        tx.oncomplete = () => resolve();
        tx.onerror = () => reject(tx.error);
      });
    } catch {
      // Fallback already updated
    }
    return payload;
  }

  async deleteSermon(id) {
    this._memoryFallback.delete(id);
    try {
      const db = await openDb();
      await new Promise((resolve, reject) => {
        const tx = db.transaction(STORE_SERMONS, 'readwrite');
        tx.objectStore(STORE_SERMONS).delete(id);
        tx.oncomplete = () => resolve();
        tx.onerror = () => reject(tx.error);
      });
    } catch {
      // Fallback already updated
    }
  }

  // --- Custom BYOT Bible Versions (IndexedDB, 100% local) ---
  async listCustomBibles() {
    try {
      const db = await openDb();
      const rows = await new Promise((resolve, reject) => {
        const tx = db.transaction(STORE_CUSTOM_BIBLES, 'readonly');
        const req = tx.objectStore(STORE_CUSTOM_BIBLES).getAll();
        req.onsuccess = () => resolve(req.result || []);
        req.onerror = () => reject(req.error);
      });
      return rows;
    } catch {
      return Array.from(this._customBiblesMem.values());
    }
  }

  async saveCustomBible(bibleRecord) {
    this._customBiblesMem.set(bibleRecord.id, bibleRecord);
    try {
      const db = await openDb();
      await new Promise((resolve, reject) => {
        const tx = db.transaction(STORE_CUSTOM_BIBLES, 'readwrite');
        tx.objectStore(STORE_CUSTOM_BIBLES).put(bibleRecord);
        tx.oncomplete = () => resolve();
        tx.onerror = () => reject(tx.error);
      });
    } catch {
      // Fallback already updated
    }
    return bibleRecord;
  }

  async deleteCustomBible(id) {
    this._customBiblesMem.delete(id);
    try {
      const db = await openDb();
      await new Promise((resolve, reject) => {
        const tx = db.transaction(STORE_CUSTOM_BIBLES, 'readwrite');
        tx.objectStore(STORE_CUSTOM_BIBLES).delete(id);
        tx.oncomplete = () => resolve();
        tx.onerror = () => reject(tx.error);
      });
    } catch {
      // Fallback already updated
    }
  }

  // --- Custom BYOT Hymn Lyrics (IndexedDB, 100% local) ---
  async getCustomHymnLyricsMap() {
    try {
      const db = await openDb();
      const rows = await new Promise((resolve, reject) => {
        const tx = db.transaction(STORE_CUSTOM_HYMNS, 'readonly');
        const req = tx.objectStore(STORE_CUSTOM_HYMNS).getAll();
        req.onsuccess = () => resolve(req.result || []);
        req.onerror = () => reject(req.error);
      });
      const out = {};
      for (const r of rows) out[r.num] = r.lyrics;
      return out;
    } catch {
      return Object.fromEntries(this._customHymnsMem.entries());
    }
  }

  async saveCustomHymnLyrics(lyricsMap) {
    const entries = Object.entries(lyricsMap || {});
    for (const [numStr, lyrics] of entries) {
      this._customHymnsMem.set(Number(numStr), lyrics);
    }
    try {
      const db = await openDb();
      await new Promise((resolve, reject) => {
        const tx = db.transaction(STORE_CUSTOM_HYMNS, 'readwrite');
        const store = tx.objectStore(STORE_CUSTOM_HYMNS);
        for (const [numStr, lyrics] of entries) {
          store.put({ num: Number(numStr), lyrics });
        }
        tx.oncomplete = () => resolve();
        tx.onerror = () => reject(tx.error);
      });
    } catch {
      // Fallback already updated
    }
    return entries.length;
  }

  _tryMigrateLegacy() {
    try {
      const raw = localStorage.getItem(LEGACY_KEY);
      if (!raw) return null;
      const legacy = JSON.parse(raw);
      return {
        id: `migrated_${Date.now()}`,
        title: legacy.title || '이전 설교 초안',
        scriptureRef: legacy.passage || '창세기 22:1-14',
        date: new Date().toISOString().slice(0, 10),
        targetDurationMins: 30,
        updatedAt: new Date().toISOString(),
        outline: Array.isArray(legacy.cards) && legacy.cards.length
          ? legacy.cards.map((c, idx) => ({
              id: `mig_${idx}`,
              section: c.tag || `대지 ${idx + 1}`,
              title: c.title || '',
              content: c.content || '',
            }))
          : createDefaultSermon().outline,
        clips: [],
      };
    } catch {
      return null;
    }
  }

  static toMarkdown(sermon) {
    const lines = [
      `# ${sermon.title}`,
      `- **본문**: ${sermon.scriptureRef}`,
      `- **날짜**: ${sermon.date}`,
      `- **목표 시간**: ${sermon.targetDurationMins}분`,
      '',
    ];
    for (const item of sermon.outline || []) {
      lines.push(`## [${item.section}] ${item.title}`, '', item.content || '', '');
    }
    if (sermon.clips && sermon.clips.length) {
      lines.push('---', '## 인용·스크랩 자료', '');
      for (const clip of sermon.clips) {
        lines.push(`- **${clip.source}**: ${clip.text}`);
      }
    }
    return lines.join('\n');
  }
}
