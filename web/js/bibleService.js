export function calculateVerseId(bookId, chapter, verse) {
  return bookId * 1_000_000 + chapter * 1_000 + verse;
}

export const HELLOAO_API_BASE = 'https://bible.helloao.org/api';

// Official free-use / public-domain Bible versions available live via HelloAO (zero API key, CORS *)
export const BUILTIN_TRANSLATIONS = [
  { id: 'nkrv', label: '개역개정 (내장 · 66권 전체)', shortLabel: '개역개정', lang: 'ko', source: 'local' },
  { id: 'nrsv', label: '새번역 (내장 · 66권 전체)', shortLabel: '새번역', lang: 'ko', source: 'local' },
  { id: 'krv', label: '개역한글 (내장 · 66권 전체)', shortLabel: '개역한글', lang: 'ko', source: 'local' },
  { id: 'kor_old', label: '한국어 구역 성경 (실시간)', shortLabel: '한국어 구역', lang: 'ko', source: 'helloao' },
  { id: 'BSB', label: '현대 영어 성경 (BSB)', shortLabel: 'BSB 영어', lang: 'en', source: 'helloao' },
  { id: 'eng_kjv', label: '킹제임스 흠정역 (KJV)', shortLabel: 'KJV 영어', lang: 'en', source: 'helloao' },
  { id: 'eng_web', label: '세계 영어 성경 (WEB)', shortLabel: 'WEB 영어', lang: 'en', source: 'helloao' },
  { id: 'eng_asv', label: '미국 표준역 (ASV 1901)', shortLabel: 'ASV 영어', lang: 'en', source: 'helloao' },
  { id: 'hbo_wlc', label: '구약 히브리어 원문 (WLC)', shortLabel: '히브리어 원문', lang: 'he', source: 'helloao', testament: 'OT' },
  { id: 'grc_sbl', label: '신약 헬라어 원문 (SBL)', shortLabel: '헬라어 원문', lang: 'el', source: 'helloao', testament: 'NT' },
];

// Official public-domain full-Bible commentaries available live for all 31,102 verses via HelloAO
export const LIVE_COMMENTARY_SOURCES = [
  { id: 'matthew-henry', name: '매튜 헨리 주석 (Matthew Henry)', badge: '고전·경건', books: 65, desc: '성경 65권 전체를 아우르는 대표적인 경건·강해 고전 주석 원문' },
  { id: 'john-calvin', name: '존 칼빈 주석 (John Calvin)', badge: '개혁·신학', books: 48, desc: '종교개혁자 칼빈의 정통 주해 원문 (48권)' },
  { id: 'jamieson-fausset-brown', name: 'JFB 주석 (Jamieson-Fausset-Brown)', badge: '고전·주해', books: 66, desc: '구·신약 66권 전체를 간결하고 정확하게 해설한 명저' },
  { id: 'adam-clarke', name: '아담 클라크 주석 (Adam Clarke)', badge: '고전·원어', books: 66, desc: '원어와 역사적 배경에 충실한 66권 방대한 주석' },
  { id: 'john-gill', name: '존 길 주석 (John Gill)', badge: '원어·강해', books: 66, desc: '유대 문헌과 히브리어·헬라어 분석이 탁월한 66권 절별 주석' },
  { id: 'keil-delitzsch', name: '카일 & 델리취 구약 주석 (Keil & Delitzsch)', badge: '구약·원어', books: 39, desc: '구약 39권 히브리어 문법·역사 주석의 최고 권위 고전' },
  { id: 'tyndale', name: '틴데일 스터디 노트 (Tyndale Notes)', badge: '현대·스터디', books: 65, desc: '현대 복음주의 학자들이 정리한 명쾌한 65권 스터디 노트' },
  { id: 'tsk', name: '성경 관주 보고 (Treasury of Scripture Knowledge)', badge: '관주·연결', books: 66, desc: '66권 모든 절에 연결된 50만 개 이상의 성경 상호 참조 관주' },
];

export function extractHelloAoText(contentArr) {
  if (!Array.isArray(contentArr)) return String(contentArr || '').trim();
  const parts = [];
  for (const node of contentArr) {
    if (typeof node === 'string') {
      parts.push(node);
    } else if (node && typeof node === 'object') {
      if (typeof node.text === 'string') parts.push(node.text);
      else if (node.lineBreak) parts.push('\n');
      else if (Array.isArray(node.content)) parts.push(extractHelloAoText(node.content));
    }
  }
  return parts.join(' ').replace(/[ \t]+\n/g, '\n').replace(/[ \t]{2,}/g, ' ').trim();
}

export class BibleDataService {
  constructor(baseUrl = './data', fetcher = (...args) => fetch(...args)) {
    this.baseUrl = baseUrl.replace(/\/$/, '');
    this.fetcher = fetcher;
    this.manifest = null;
    this.exegesis = null;
    this.worship = null;
    this.bookCache = new Map();
    this.liveChapterCache = new Map();
    this.liveCommentaryCache = new Map();
    this.maxCachedBooks = 16;
  }

  async init() {
    const [manifestResp, exegesisResp, worshipResp] = await Promise.all([
      this.fetcher(`${this.baseUrl}/manifest.json`),
      this.fetcher(`${this.baseUrl}/exegesis.json`),
      this.fetcher(`${this.baseUrl}/worship.json`),
    ]);
    if (!manifestResp.ok) throw new Error(`manifest HTTP ${manifestResp.status}`);
    if (!exegesisResp.ok) throw new Error(`exegesis HTTP ${exegesisResp.status}`);
    this.manifest = await manifestResp.json();
    this.exegesis = await exegesisResp.json();
    this.worship = worshipResp.ok ? await worshipResp.json() : { hymns: [], responsiveReadings: [] };
    return { manifest: this.manifest, exegesis: this.exegesis, worship: this.worship };
  }

  getBooks() {
    return this.manifest ? this.manifest.books : [];
  }

  getBookMeta(osis) {
    return this.getBooks().find((b) => b.id === osis) || null;
  }

  async loadBook(osis) {
    if (this.bookCache.has(osis)) {
      const val = this.bookCache.get(osis);
      this.bookCache.delete(osis);
      this.bookCache.set(osis, val);
      return val;
    }
    const resp = await this.fetcher(`${this.baseUrl}/krv/${osis}.json`);
    if (!resp.ok) throw new Error(`book ${osis} HTTP ${resp.status}`);
    const data = await resp.json();
    if (this.bookCache.size >= this.maxCachedBooks) {
      this.bookCache.delete(this.bookCache.keys().next().value);
    }
    this.bookCache.set(osis, data);
    return data;
  }

  async getChapterVerses(osis, chapterNum) {
    const book = await this.loadBook(osis);
    const list = book.chapters[String(chapterNum)] || [];
    return list.map((text, idx) => ({
      verseId: calculateVerseId(book.bookId, chapterNum, idx + 1),
      bookId: book.bookId,
      osis,
      bookName: book.nameKr,
      chapter: chapterNum,
      verse: idx + 1,
      text,
    }));
  }

  /**
   * Fetch a map of { [verseNum]: verseText } for any supported version:
   * - 'krv': built-in offline KRV
   * - 'custom_...': user-imported BYOT Bible stored locally in IndexedDB (e.g. 개역개정 GAE)
   * - HelloAO translation id ('BSB', 'eng_kjv', 'hbo_wlc', 'grc_sbl', 'kor_old', ...)
   */
  async getVersionChapterMap(versionId, osis, chapterNum, customBibles = []) {
    if (!versionId || versionId === 'none') return null;
    if (versionId === 'krv' || versionId === 'nkrv' || versionId === 'nrsv') {
      const cacheKey = `${versionId}:${osis}:${chapterNum}`;
      if (this.liveChapterCache.has(cacheKey)) return this.liveChapterCache.get(cacheKey);
      const resp = await this.fetcher(`${this.baseUrl}/${versionId}/${osis}.json`);
      if (!resp.ok) throw new Error(`${versionId}/${osis} HTTP ${resp.status}`);
      const book = await resp.json();
      const list = book.chapters[String(chapterNum)] || [];
      const out = {};
      list.forEach((txt, idx) => { out[idx + 1] = txt; });
      this.liveChapterCache.set(cacheKey, out);
      return out;
    }
    if (versionId.startsWith('custom_')) {
      const custom = customBibles.find((b) => b.id === versionId);
      if (!custom || !custom.books || !custom.books[osis]) return {};
      const chData = custom.books[osis][String(chapterNum)];
      if (!chData) return {};
      const out = {};
      for (const [vs, txt] of Object.entries(chData)) out[Number(vs)] = txt;
      return out;
    }

    const cacheKey = `${versionId}:${osis}:${chapterNum}`;
    if (this.liveChapterCache.has(cacheKey)) {
      return this.liveChapterCache.get(cacheKey);
    }
    const url = `${HELLOAO_API_BASE}/${encodeURIComponent(versionId)}/${osis}/${chapterNum}.json`;
    const resp = await this.fetcher(url);
    if (!resp.ok) {
      throw new Error(`역본(${versionId}) 불러오기 실패 (HTTP ${resp.status})`);
    }
    const payload = await resp.json();
    const out = {};
    for (const item of payload?.chapter?.content || []) {
      if (item.type === 'verse' && item.number) {
        out[Number(item.number)] = extractHelloAoText(item.content);
      }
    }
    this.liveChapterCache.set(cacheKey, out);
    return out;
  }

  /**
   * Fetch full-66-book official public-domain commentary chapter from HelloAO API
   */
  async fetchLiveCommentaryChapter(commentaryId, osis, chapterNum) {
    const cacheKey = `${commentaryId}:${osis}:${chapterNum}`;
    if (this.liveCommentaryCache.has(cacheKey)) {
      return this.liveCommentaryCache.get(cacheKey);
    }
    const url = `${HELLOAO_API_BASE}/c/${encodeURIComponent(commentaryId)}/${osis}/${chapterNum}.json`;
    const resp = await this.fetcher(url);
    if (!resp.ok) {
      if (resp.status === 404) {
        const empty = { available: false, introduction: '', verses: {}, url };
        this.liveCommentaryCache.set(cacheKey, empty);
        return empty;
      }
      throw new Error(`실시간 주석 불러오기 실패 (HTTP ${resp.status})`);
    }
    const payload = await resp.json();
    const verses = {};
    for (const item of payload?.chapter?.content || []) {
      if (item.type === 'verse' && item.number) {
        const txt = extractHelloAoText(item.content);
        verses[Number(item.number)] = verses[Number(item.number)]
          ? `${verses[Number(item.number)]}\n\n${txt}`
          : txt;
      }
    }
    const result = {
      available: true,
      introduction: (payload?.chapter?.introduction || '').trim(),
      verses,
      url,
    };
    this.liveCommentaryCache.set(cacheKey, result);
    return result;
  }

  getCommentariesForVerse(verseId) {
    if (!this.exegesis) return [];
    return this.exegesis.commentaries.filter(
      (c) => verseId >= c.verse_start_id && verseId <= c.verse_end_id
    );
  }

  getCrossReferencesForVerse(verseId) {
    if (!this.exegesis) return [];
    return this.exegesis.crossReferences[String(verseId)] || [];
  }

  getChains() {
    return this.exegesis ? Object.values(this.exegesis.chains) : [];
  }

  getStrongs() {
    return this.exegesis ? Object.values(this.exegesis.strongs) : [];
  }

  getHymns() {
    return this.worship?.hymns || [];
  }

  getResponsiveReadings() {
    return this.worship?.responsiveReadings || [];
  }

  async searchKoreanText(query, scopeOsis = null, limit = 30) {
    const q = (query || '').trim();
    if (!q) return [];
    const results = [];
    const targets = scopeOsis ? [this.getBookMeta(scopeOsis)].filter(Boolean) : this.getBooks();

    for (const meta of targets) {
      const book = await this.loadBook(meta.id);
      for (const [chKey, verses] of Object.entries(book.chapters)) {
        for (let i = 0; i < verses.length; i++) {
          if (verses[i].includes(q)) {
            results.push({
              osis: meta.id,
              bookName: meta.name,
              chapter: Number(chKey),
              verse: i + 1,
              verseId: calculateVerseId(meta.bookId, Number(chKey), i + 1),
              text: verses[i],
            });
            if (results.length >= limit) return results;
          }
        }
      }
    }
    return results;
  }
}
