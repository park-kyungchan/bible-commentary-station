import { normalizeSearchText, tokenizeSearchQuery } from '../core/koreanQuery.js';

export const HELLOAO_API_BASE = 'https://bible.helloao.org/api';

export const LIVE_TRANSLATIONS = Object.freeze([
  { id: 'kor_old', label: '한국어 구역 성경 (인터넷 연결)', shortLabel: '한국어 구역', lang: 'ko', source: 'live' },
  { id: 'BSB', label: '현대 영어 성경 (인터넷 연결)', shortLabel: '현대 영어', lang: 'en', source: 'live' },
  { id: 'eng_kjv', label: '킹제임스 영어 성경 (인터넷 연결)', shortLabel: '킹제임스 영어', lang: 'en', source: 'live' },
  { id: 'eng_web', label: '세계 영어 성경 (인터넷 연결)', shortLabel: '세계 영어', lang: 'en', source: 'live' },
  { id: 'hbo_wlc', label: '구약 히브리어 원문 (인터넷 연결)', shortLabel: '히브리어 원문', lang: 'he', source: 'live', testament: 'OT' },
  { id: 'grc_sbl', label: '신약 헬라어 원문 (인터넷 연결)', shortLabel: '헬라어 원문', lang: 'el', source: 'live', testament: 'NT' },
]);

export const LIVE_COMMENTARY_SOURCES = Object.freeze([
  { id: 'matthew-henry', name: '매튜 헨리 주석', badge: '고전·경건', books: 65, desc: '성경 65권을 아우르는 대표적인 경건·강해 고전 주석 원문' },
  { id: 'john-calvin', name: '존 칼빈 주석', badge: '개혁·신학', books: 48, desc: '종교개혁자 칼빈의 정통 주해 원문 (48권)' },
  { id: 'jamieson-fausset-brown', name: '제이미슨·포셋·브라운 주석', badge: '고전·주해', books: 66, desc: '구·신약 66권 전체를 간결하게 해설한 고전 주석' },
  { id: 'adam-clarke', name: '아담 클라크 주석', badge: '고전·원어', books: 66, desc: '원어와 역사적 배경에 충실한 66권 고전 주석' },
  { id: 'john-gill', name: '존 길 주석', badge: '원어·강해', books: 66, desc: '히브리어·헬라어 분석이 깊은 66권 절별 주석' },
  { id: 'keil-delitzsch', name: '카일·델리취 구약 주석', badge: '구약·원어', books: 39, desc: '구약 39권 히브리어 문법·역사 주석' },
  { id: 'tyndale', name: '틴데일 성경 노트', badge: '현대·참고', books: 65, desc: '복음주의 학자들이 정리한 65권 성경 참고 노트' },
  { id: 'tsk', name: '성경 상호 관주 모음', badge: '관주·연결', books: 66, desc: '66권 모든 절에 연결된 방대한 성경 상호 참조' },
]);

export function calculateVerseId(bookId, chapter, verse) { return bookId * 1_000_000 + chapter * 1_000 + verse; }

export function extractHelloAoText(contentArr) {
  if (!Array.isArray(contentArr)) return String(contentArr || '').trim();
  const parts = [];
  for (const node of contentArr) {
    if (typeof node === 'string') parts.push(node);
    else if (node && typeof node === 'object') {
      if (typeof node.text === 'string') parts.push(node.text);
      else if (node.lineBreak) parts.push('\n');
      else if (Array.isArray(node.content)) parts.push(extractHelloAoText(node.content));
    }
  }
  return parts.join(' ').replace(/[ \t]+\n/g, '\n').replace(/[ \t]{2,}/g, ' ').trim();
}

class LruCache {
  constructor(maxSize) { this.maxSize = maxSize; this.map = new Map(); }
  get(k) { if (!this.map.has(k)) return undefined; const v = this.map.get(k); this.map.delete(k); this.map.set(k, v); return v; }
  set(k, v) { if (this.map.has(k)) this.map.delete(k); else if (this.map.size >= this.maxSize) this.map.delete(this.map.keys().next().value); this.map.set(k, v); }
  get size() { return this.map.size; }
}

export class BibleDataService {
  constructor(baseUrl = './data', fetcher = (...args) => fetch(...args)) {
    this.baseUrl = baseUrl.replace(/\/$/, '');
    this.fetcher = fetcher;
    this.manifest = null;
    this.exegesis = null;
    this.worship = null;
    this.bookCache = new LruCache(24);
    this.liveChapterCache = new LruCache(100);
    this.liveCommentaryCache = new LruCache(60);
    this.searchIndexCache = new LruCache(4);
    this._inflightBooks = new Map();
    this._commentaryByVerse = new Map();
    this._bookMetaByOsis = new Map();
  }

  async init() {
    const [mResp, eResp, wResp] = await Promise.all([
      this.fetcher(`${this.baseUrl}/manifest.json`),
      this.fetcher(`${this.baseUrl}/exegesis.json`),
      this.fetcher(`${this.baseUrl}/worship.json`),
    ]);
    if (!mResp.ok || !eResp.ok) throw new Error('성경 기본 자료를 불러오지 못했습니다.');
    this.manifest = await mResp.json();
    this.exegesis = await eResp.json();
    this.worship = wResp.ok ? await wResp.json() : { hymnGroups: [], responsiveGroups: [], hymns: [], responsiveReadings: [], liturgies: [], templates: [] };
    this._bookMetaByOsis.clear();
    for (const b of this.getBooks()) this._bookMetaByOsis.set(b.id, b);
    this._commentaryByVerse.clear();
    for (const c of this.exegesis?.commentaries || []) {
      const start = Number(c.verse_start_id);
      const span = Math.min(Number(c.verse_end_id || start) - start, 200);
      for (let vid = start; vid <= start + span; vid += 1) {
        if (!this._commentaryByVerse.has(vid)) this._commentaryByVerse.set(vid, []);
        this._commentaryByVerse.get(vid).push(c);
      }
    }
    return { manifest: this.manifest, exegesis: this.exegesis, worship: this.worship };
  }

  getBooks() { return this.manifest?.books || []; }
  getBookMeta(osis) { return this._bookMetaByOsis.get(osis) || this.getBooks().find((b) => b.id === osis) || null; }
  getBookBoundsMap() { const out = Object.create(null); for (const b of this.getBooks()) out[b.id] = { totalChapters: b.totalChapters }; return out; }

  getLocalVersions() {
    const list = Array.isArray(this.manifest?.versions) && this.manifest.versions.length
      ? this.manifest.versions
      : [{ id: 'krv', nameKr: '개역한글', attribution: '대한성서공회 1961 (저작권 보호기간 만료)', license: 'PUBLIC_DOMAIN' }];
    return list.map((v) => ({
      id: v.id, label: `${v.nameKr} (기본 내장 · 66권)`, shortLabel: v.nameKr, isDefault: Boolean(v.default),
      attribution: v.attribution || '', license: v.license || 'PUBLIC_DOMAIN',
      pathPrefix: v.pathPrefix || `${this.baseUrl}/${v.id}/`,
      searchIndexPath: v.searchIndexPath || `${this.baseUrl}/search/${v.id}.json`, lang: v.lang || 'ko', source: 'local',
    }));
  }

  getDefaultVersionId() {
    const locals = this.getLocalVersions();
    return locals.find((v) => v.isDefault)?.id
      || (this.manifest?.defaultVersion && locals.some((v) => v.id === this.manifest.defaultVersion) ? this.manifest.defaultVersion : (locals[0]?.id || 'nkrv'));
  }

  getAvailableVersions(customBibles = []) {
    const customs = (customBibles || []).map((b) => ({ id: b.id, label: `${b.name} (내 기기 저장 · ${b.bookCount || 0}권)`, shortLabel: b.shortName || b.name, lang: 'ko', source: 'custom' }));
    return [...this.getLocalVersions(), ...customs, ...LIVE_TRANSLATIONS];
  }

  getVersionInfo(versionId, customBibles = []) { return this.getAvailableVersions(customBibles).find((v) => v.id === versionId) || null; }

  async loadBook(versionId, osis, signal) {
    const localVer = this.getLocalVersions().find((v) => v.id === versionId);
    if (!localVer) throw new Error('지원하지 않는 내장 역본입니다.');
    const key = `${versionId}:${osis}`;
    const cached = this.bookCache.get(key);
    if (cached) return cached;
    if (this._inflightBooks.has(key)) return this._inflightBooks.get(key);
    const promise = (async () => {
      const resp = await this.fetcher(`${localVer.pathPrefix.replace(/\/$/, '')}/${osis}.json`, signal ? { signal } : undefined);
      if (!resp.ok) throw new Error('성경 본문 파일을 불러오지 못했습니다.');
      const data = await resp.json();
      this.bookCache.set(key, data);
      return data;
    })();
    this._inflightBooks.set(key, promise);
    try { return await promise; } finally { this._inflightBooks.delete(key); }
  }

  async getVersionChapterMap(versionId, osis, chapterNum, customBibles = [], signal) {
    if (!versionId || versionId === 'none') return null;
    if (this.getLocalVersions().some((v) => v.id === versionId)) {
      const book = await this.loadBook(versionId, osis, signal);
      const out = {};
      (book.chapters?.[String(chapterNum)] || []).forEach((txt, idx) => { out[idx + 1] = typeof txt === 'string' ? txt : ''; });
      return out;
    }
    if (versionId.startsWith('custom_')) {
      const chData = (customBibles || []).find((b) => b.id === versionId)?.books?.[osis]?.[String(chapterNum)];
      const out = {};
      for (const [vs, txt] of Object.entries(chData || {})) out[Number(vs)] = typeof txt === 'string' ? txt : '';
      return out;
    }
    const key = `${versionId}:${osis}:${chapterNum}`;
    const cached = this.liveChapterCache.get(key);
    if (cached) return cached;
    const resp = await this.fetcher(`${HELLOAO_API_BASE}/${encodeURIComponent(versionId)}/${osis}/${chapterNum}.json`, signal ? { signal } : undefined);
    if (!resp.ok) throw new Error('선택하신 역본을 인터넷에서 불러오지 못했습니다.');
    const out = {};
    for (const item of (await resp.json())?.chapter?.content || []) {
      if (item.type === 'verse' && item.number) out[Number(item.number)] = extractHelloAoText(item.content);
    }
    this.liveChapterCache.set(key, out);
    return out;
  }

  async getMergedChapterVerses(primaryVersionId, parallelVersionId, osis, chapterNum, customBibles = [], signal) {
    const meta = this.getBookMeta(osis);
    const primaryInfo = this.getVersionInfo(primaryVersionId, customBibles);
    const useParallel = parallelVersionId && parallelVersionId !== 'none' && parallelVersionId !== primaryVersionId;
    const parallelInfo = useParallel ? this.getVersionInfo(parallelVersionId, customBibles) : null;
    const [primaryMap, parallelMap] = await Promise.all([
      this.getVersionChapterMap(primaryVersionId, osis, chapterNum, customBibles, signal),
      useParallel ? this.getVersionChapterMap(parallelVersionId, osis, chapterNum, customBibles, signal).catch(() => null) : Promise.resolve(null),
    ]);
    const chFootnotes = this.bookCache.get(`${primaryVersionId}:${osis}`)?.footnotes?.[String(chapterNum)] || null;
    const nums = new Set([...Object.keys(primaryMap || {}), ...Object.keys(parallelMap || {})].map(Number).filter((n) => Number.isInteger(n) && n > 0));
    return Array.from(nums).sort((a, b) => a - b).map((vs) => {
      const rawPrimary = primaryMap && Object.prototype.hasOwnProperty.call(primaryMap, vs) ? String(primaryMap[vs] || '').trim() : '';
      const rawParallel = parallelMap && Object.prototype.hasOwnProperty.call(parallelMap, vs) ? String(parallelMap[vs] || '').trim() : '';
      return {
        verseId: calculateVerseId(meta?.bookId || 1, chapterNum, vs), bookId: meta?.bookId || 1, osis,
        bookName: meta?.name || osis, chapter: chapterNum, verse: vs, primaryText: rawPrimary, isEmptyPrimary: !rawPrimary,
        parallelText: rawParallel, primaryLabel: primaryInfo?.shortLabel || primaryVersionId, parallelLabel: parallelInfo?.shortLabel || '',
        footnotes: Array.isArray(chFootnotes?.[String(vs)]) ? chFootnotes[String(vs)] : [],
      };
    });
  }

  async _loadSearchIndex(versionId, signal) {
    const cached = this.searchIndexCache.get(versionId);
    if (cached) return cached;
    const path = this.getLocalVersions().find((v) => v.id === versionId)?.searchIndexPath;
    if (!path) return null;
    try {
      const resp = await this.fetcher(path, signal ? { signal } : undefined);
      if (!resp.ok) return null;
      const data = await resp.json();
      if (data && Array.isArray(data.verses)) { this.searchIndexCache.set(versionId, data); return data; }
    } catch (err) { if (err?.name === 'AbortError') throw err; }
    return null;
  }

  async searchActiveVersion(query, primaryVersionId, customBibles = [], options = {}) {
    const tokens = tokenizeSearchQuery(query);
    const compact = normalizeSearchText(query);
    if (!compact) return [];
    const { limit = 40, scopeOsis = null, signal } = options;
    const versionLabel = this.getVersionInfo(primaryVersionId, customBibles)?.shortLabel || primaryVersionId;
    const isHit = (t) => { const n = normalizeSearchText(t); return n.includes(compact) || (tokens.length > 1 && tokens.every((tk) => n.includes(tk))); };
    const out = [];
    const pushHit = (meta, ch, vs, text, versionId) => {
      out.push({ osis: meta.id, bookName: meta.name, chapter: ch, verse: vs, verseId: calculateVerseId(meta.bookId, ch, vs), text, versionId, versionLabel });
      return out.length >= limit;
    };

    if (primaryVersionId.startsWith('custom_')) {
      const custom = (customBibles || []).find((b) => b.id === primaryVersionId);
      if (!custom?.books) return [];
      for (const meta of this.getBooks()) {
        if (scopeOsis && meta.id !== scopeOsis) continue;
        for (const [chKey, vsMap] of Object.entries(custom.books[meta.id] || {})) {
          for (const [vsKey, txt] of Object.entries(vsMap)) if (isHit(txt) && pushHit(meta, Number(chKey), Number(vsKey), txt, primaryVersionId)) return out;
        }
      }
      return out;
    }

    const verId = this.getLocalVersions().some((v) => v.id === primaryVersionId) ? primaryVersionId : this.getDefaultVersionId();
    const index = await this._loadSearchIndex(verId, signal);
    if (index) {
      for (const row of index.verses) {
        const osis = index.books?.[row[0]];
        if (!osis || (scopeOsis && osis !== scopeOsis)) continue;
        if (isHit(row[3] || '') && pushHit(this.getBookMeta(osis) || { id: osis, name: osis, bookId: 1 }, row[1], row[2], row[3], verId)) return out;
      }
      return out;
    }

    for (const meta of scopeOsis ? [this.getBookMeta(scopeOsis)].filter(Boolean) : this.getBooks()) {
      if (signal?.aborted) break;
      const book = await this.loadBook(verId, meta.id, signal);
      for (const [chKey, verses] of Object.entries(book.chapters || {})) {
        for (let i = 0; i < verses.length; i += 1) if (isHit(verses[i]) && pushHit(meta, Number(chKey), i + 1, verses[i], verId)) return out;
      }
    }
    return out;
  }

  async fetchLiveCommentaryChapter(commentaryId, osis, chapterNum, signal) {
    const key = `${commentaryId}:${osis}:${chapterNum}`;
    const cached = this.liveCommentaryCache.get(key);
    if (cached) return cached;
    const resp = await this.fetcher(`${HELLOAO_API_BASE}/c/${encodeURIComponent(commentaryId)}/${osis}/${chapterNum}.json`, signal ? { signal } : undefined);
    if (!resp.ok) {
      if (resp.status === 404) { const empty = { available: false, introduction: '', verses: {} }; this.liveCommentaryCache.set(key, empty); return empty; }
      throw new Error('영문 고전 주석을 불러오지 못했습니다.');
    }
    const payload = await resp.json();
    const verses = {};
    for (const item of payload?.chapter?.content || []) {
      if (item.type === 'verse' && item.number) {
        const txt = extractHelloAoText(item.content);
        verses[Number(item.number)] = verses[Number(item.number)] ? `${verses[Number(item.number)]}\n\n${txt}` : txt;
      }
    }
    const result = { available: true, introduction: (payload?.chapter?.introduction || '').trim(), verses };
    this.liveCommentaryCache.set(key, result);
    return result;
  }

  async resolveResponsiveReadingLines(rr, versionId, customBibles = [], signal) {
    const activeVer = (this.getLocalVersions().some((v) => v.id === versionId) || versionId.startsWith('custom_')) ? versionId : this.getDefaultVersionId();
    const lines = [];
    if (Array.isArray(rr.segments) && rr.segments.length > 0) {
      for (const seg of rr.segments) {
        if (seg.customText) { lines.push({ role: seg.role || 'unison', text: seg.customText, refLabel: '' }); continue; }
        if (!seg.osis || !seg.ch) continue;
        const chMap = await this.getVersionChapterMap(activeVer, seg.osis, seg.ch, customBibles, signal);
        const start = Number(seg.start_vs || 1);
        const end = Number(seg.end_vs || start);
        const texts = [];
        for (let v = start; v <= end; v += 1) if (chMap?.[v]) texts.push(chMap[v]);
        if (texts.length) lines.push({ role: seg.role || 'leader', text: texts.join(' '), refLabel: `${this.getBookMeta(seg.osis)?.abbr || seg.osis} ${seg.ch}:${start === end ? start : `${start}-${end}`}` });
      }
      return lines;
    }
    if (rr.osis && rr.ch) {
      const chMap = await this.getVersionChapterMap(activeVer, rr.osis, rr.ch, customBibles, signal);
      const start = Number(rr.start_vs || 1);
      const end = Number(rr.end_vs || start);
      const total = end - start + 1;
      for (let v = start; v <= end; v += 1) {
        if (!chMap?.[v]) continue;
        const i = v - start;
        lines.push({ role: i === total - 1 && total >= 3 ? 'unison' : (i % 2 === 0 ? 'leader' : 'congregation'), text: chMap[v], refLabel: `${rr.ch}:${v}` });
      }
    }
    return lines;
  }

  getCommentariesForVerse(vid) { return this._commentaryByVerse.get(vid) || []; }
  getCoverageStats() {
    if (this.exegesis?.coverageStats) return this.exegesis.coverageStats;
    const e = this.exegesis?.commentaries || [];
    return { commentaryEntries: e.length, coveredVerses: new Set(e.map((c) => c.verse_start_id)).size, coveredBooks: new Set(e.map((c) => c.book_id)).size, totalVerses: 31102 };
  }
  getCrossReferencesForVerse(vid) { return this.exegesis?.crossReferences?.[String(vid)] || []; }
  getChains() { return this.exegesis?.chains ? Object.values(this.exegesis.chains) : []; }
  getStrongs() { return this.exegesis?.strongs ? Object.values(this.exegesis.strongs) : []; }
  getStrongsForVerse(verseObj, commentaries = []) {
    if (!verseObj) return [];
    const wantLang = this.getBookMeta(verseObj.osis)?.testament === 'NT' ? 'GREEK' : 'HEBREW';
    const commBlob = commentaries.map((c) => `${c.title || ''} ${c.content_markdown || ''} ${c.theological_tags || ''}`).join(' ');
    const verseBlob = `${verseObj.primaryText || ''} ${commBlob}`;
    return this.getStrongs().filter((s) => (!s.language || s.language === wantLang) && (
      (commBlob && (commBlob.includes(s.pronunciation) || commBlob.includes(s.lemma) || commBlob.includes(s.strong_id)))
      || (String(s.definition_kr || '').split(',')[0].trim().length >= 2 && verseBlob.includes(String(s.definition_kr || '').split(',')[0].trim()))
    ));
  }
}
