/**
 * Lazy-Loading 66-Book Bible & Exegesis Data Service
 * - Loads lightweight manifest.json + exegesis.json upfront (~35KB total)
 * - Fetches individual book chunks (./data/krv/{OSIS}.json, ~68KB avg) on demand with LRU caching
 * - Eliminates the 4.3MB initial blocking JSON load while providing full 31,102-verse offline search
 */

export function calculateVerseId(bookId, chapter, verse) {
  return bookId * 1_000_000 + chapter * 1_000 + verse;
}

export class BibleDataService {
  constructor(baseUrl = './data', fetcher = (...args) => fetch(...args)) {
    this.baseUrl = baseUrl.replace(/\/$/, '');
    this.fetcher = fetcher;
    this.manifest = null;
    this.exegesis = null;
    this.bookCache = new Map();
    this.maxCachedBooks = 16;
  }

  async init() {
    const [manifestResp, exegesisResp] = await Promise.all([
      this.fetcher(`${this.baseUrl}/manifest.json`),
      this.fetcher(`${this.baseUrl}/exegesis.json`),
    ]);
    if (!manifestResp.ok) throw new Error(`Failed to load manifest: HTTP ${manifestResp.status}`);
    if (!exegesisResp.ok) throw new Error(`Failed to load exegesis: HTTP ${exegesisResp.status}`);
    this.manifest = await manifestResp.json();
    this.exegesis = await exegesisResp.json();
    return { manifest: this.manifest, exegesis: this.exegesis };
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
      // Refresh LRU order
      this.bookCache.delete(osis);
      this.bookCache.set(osis, val);
      return val;
    }
    const resp = await this.fetcher(`${this.baseUrl}/krv/${osis}.json`);
    if (!resp.ok) throw new Error(`Failed to load book ${osis}: HTTP ${resp.status}`);
    const data = await resp.json();
    if (this.bookCache.size >= this.maxCachedBooks) {
      const oldestKey = this.bookCache.keys().next().value;
      this.bookCache.delete(oldestKey);
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

  getProvenance(sourceId) {
    return this.exegesis?.provenance?.[sourceId] || null;
  }

  /**
   * Search across currently loaded books or prioritized books in batches without blocking UI.
   */
  async searchKoreanText(query, scopeOsis = null, limit = 30) {
    const q = (query || '').trim();
    if (!q) return [];
    const results = [];
    const targets = scopeOsis
      ? [this.getBookMeta(scopeOsis)].filter(Boolean)
      : this.getBooks();

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
