const ALIAS_ENTRIES = [
  ['창', 'GEN'], ['창세기', 'GEN'], ['gen', 'GEN'], ['genesis', 'GEN'],
  ['출', 'EXO'], ['출애굽기', 'EXO'], ['exo', 'EXO'], ['exodus', 'EXO'],
  ['레', 'LEV'], ['레위기', 'LEV'], ['lev', 'LEV'], ['leviticus', 'LEV'],
  ['민', 'NUM'], ['민수기', 'NUM'], ['num', 'NUM'], ['numbers', 'NUM'],
  ['신', 'DEU'], ['신명기', 'DEU'], ['deu', 'DEU'], ['deuteronomy', 'DEU'],
  ['수', 'JOS'], ['여호수아', 'JOS'], ['jos', 'JOS'], ['joshua', 'JOS'],
  ['삿', 'JDG'], ['사사기', 'JDG'], ['jdg', 'JDG'], ['judges', 'JDG'],
  ['룻', 'RUT'], ['룻기', 'RUT'], ['rut', 'RUT'], ['ruth', 'RUT'],
  ['삼상', '1SA'], ['사무엘상', '1SA'], ['1sa', '1SA'], ['1sam', '1SA'], ['1samuel', '1SA'],
  ['삼하', '2SA'], ['사무엘하', '2SA'], ['2sa', '2SA'], ['2sam', '2SA'], ['2samuel', '2SA'],
  ['왕상', '1KI'], ['열왕기상', '1KI'], ['1ki', '1KI'], ['1kings', '1KI'],
  ['왕하', '2KI'], ['열왕기하', '2KI'], ['2ki', '2KI'], ['2kings', '2KI'],
  ['대상', '1CH'], ['역대상', '1CH'], ['1ch', '1CH'], ['1chronicles', '1CH'],
  ['대하', '2CH'], ['역대하', '2CH'], ['2ch', '2CH'], ['2chronicles', '2CH'],
  ['스', 'EZR'], ['에스라', 'EZR'], ['ezr', 'EZR'], ['ezra', 'EZR'],
  ['느', 'NEH'], ['느헤미야', 'NEH'], ['neh', 'NEH'], ['nehemiah', 'NEH'],
  ['에', 'EST'], ['에스더', 'EST'], ['est', 'EST'], ['esther', 'EST'],
  ['욥', 'JOB'], ['욥기', 'JOB'], ['job', 'JOB'],
  ['시', 'PSA'], ['시편', 'PSA'], ['ps', 'PSA'], ['psa', 'PSA'], ['psalm', 'PSA'], ['psalms', 'PSA'],
  ['잠', 'PRO'], ['잠언', 'PRO'], ['pro', 'PRO'], ['prov', 'PRO'], ['proverbs', 'PRO'],
  ['전', 'ECC'], ['전도서', 'ECC'], ['ecc', 'ECC'], ['ecclesiastes', 'ECC'],
  ['아', 'SNG'], ['아가', 'SNG'], ['아가서', 'SNG'], ['sng', 'SNG'], ['song', 'SNG'], ['songs', 'SNG'],
  ['사', 'ISA'], ['이사야', 'ISA'], ['isa', 'ISA'], ['isaiah', 'ISA'],
  ['렘', 'JER'], ['예레미야', 'JER'], ['jer', 'JER'], ['jeremiah', 'JER'],
  ['애', 'LAM'], ['애가', 'LAM'], ['예레미야애가', 'LAM'], ['lam', 'LAM'], ['lamentations', 'LAM'],
  ['겔', 'EZK'], ['에스겔', 'EZK'], ['ezk', 'EZK'], ['ezek', 'EZK'], ['ezekiel', 'EZK'],
  ['단', 'DAN'], ['다니엘', 'DAN'], ['dan', 'DAN'], ['daniel', 'DAN'],
  ['호', 'HOS'], ['호세아', 'HOS'], ['hos', 'HOS'], ['hosea', 'HOS'],
  ['욜', 'JOL'], ['요엘', 'JOL'], ['jol', 'JOL'], ['joel', 'JOL'],
  ['암', 'AMO'], ['아모스', 'AMO'], ['amo', 'AMO'], ['amos', 'AMO'],
  ['옵', 'OBA'], ['오바댜', 'OBA'], ['oba', 'OBA'], ['obadiah', 'OBA'],
  ['욘', 'JON'], ['요나', 'JON'], ['jon', 'JON'], ['jonah', 'JON'],
  ['미', 'MIC'], ['미가', 'MIC'], ['mic', 'MIC'], ['micah', 'MIC'],
  ['나', 'NAM'], ['나훔', 'NAM'], ['nam', 'NAM'], ['nahum', 'NAM'],
  ['합', 'HAB'], ['하박국', 'HAB'], ['hab', 'HAB'], ['habakkuk', 'HAB'],
  ['습', 'ZEP'], ['스바냐', 'ZEP'], ['zep', 'ZEP'], ['zephaniah', 'ZEP'],
  ['학', 'HAG'], ['학개', 'HAG'], ['hag', 'HAG'], ['haggai', 'HAG'],
  ['슥', 'ZEC'], ['스가랴', 'ZEC'], ['zec', 'ZEC'], ['zechariah', 'ZEC'],
  ['말', 'MAL'], ['말라기', 'MAL'], ['mal', 'MAL'], ['malachi', 'MAL'],
  ['마', 'MAT'], ['마태', 'MAT'], ['마태복음', 'MAT'], ['mat', 'MAT'], ['matt', 'MAT'], ['matthew', 'MAT'],
  ['막', 'MRK'], ['마가', 'MRK'], ['마가복음', 'MRK'], ['mrk', 'MRK'], ['mark', 'MRK'],
  ['눅', 'LUK'], ['누가', 'LUK'], ['누가복음', 'LUK'], ['luk', 'LUK'], ['luke', 'LUK'],
  ['요', 'JHN'], ['요한', 'JHN'], ['요한복음', 'JHN'], ['jhn', 'JHN'], ['john', 'JHN'],
  ['행', 'ACT'], ['사도행전', 'ACT'], ['act', 'ACT'], ['acts', 'ACT'],
  ['롬', 'ROM'], ['로마서', 'ROM'], ['rom', 'ROM'], ['romans', 'ROM'],
  ['고전', '1CO'], ['고린도전서', '1CO'], ['1co', '1CO'], ['1cor', '1CO'], ['1corinthians', '1CO'],
  ['고후', '2CO'], ['고린도후서', '2CO'], ['2co', '2CO'], ['2cor', '2CO'], ['2corinthians', '2CO'],
  ['갈', 'GAL'], ['갈라디아서', 'GAL'], ['gal', 'GAL'], ['galatians', 'GAL'],
  ['엡', 'EPH'], ['에베소서', 'EPH'], ['eph', 'EPH'], ['ephesians', 'EPH'],
  ['빌', 'PHP'], ['빌립보서', 'PHP'], ['php', 'PHP'], ['phil', 'PHP'], ['philippians', 'PHP'],
  ['골', 'COL'], ['골로새서', 'COL'], ['col', 'COL'], ['colossians', 'COL'],
  ['살전', '1TH'], ['데살로니가전서', '1TH'], ['1th', '1TH'], ['1thess', '1TH'],
  ['살후', '2TH'], ['데살로니가후서', '2TH'], ['2th', '2TH'], ['2thess', '2TH'],
  ['딤전', '1TI'], ['디모데전서', '1TI'], ['1ti', '1TI'], ['1tim', '1TI'],
  ['딤후', '2TI'], ['디모데후서', '2TI'], ['2ti', '2TI'], ['2tim', '2TI'],
  ['딛', 'TIT'], ['디도서', 'TIT'], ['tit', 'TIT'], ['titus', 'TIT'],
  ['몬', 'PHM'], ['빌레몬서', 'PHM'], ['phm', 'PHM'], ['philemon', 'PHM'],
  ['히', 'HEB'], ['히브리서', 'HEB'], ['heb', 'HEB'], ['hebrews', 'HEB'],
  ['약', 'JAS'], ['야고보서', 'JAS'], ['jas', 'JAS'], ['james', 'JAS'],
  ['벧전', '1PE'], ['베드로전서', '1PE'], ['1pe', '1PE'], ['1pet', '1PE'],
  ['벧후', '2PE'], ['베드로후서', '2PE'], ['2pe', '2PE'], ['2pet', '2PE'],
  ['요일', '1JN'], ['요한일서', '1JN'], ['요한1서', '1JN'], ['1jn', '1JN'], ['1john', '1JN'],
  ['요이', '2JN'], ['요한이서', '2JN'], ['요한2서', '2JN'], ['2jn', '2JN'], ['2john', '2JN'],
  ['요삼', '3JN'], ['요한삼서', '3JN'], ['요한3서', '3JN'], ['3jn', '3JN'], ['3john', '3JN'],
  ['유', 'JUD'], ['유다서', 'JUD'], ['jud', 'JUD'], ['jude', 'JUD'],
  ['계', 'REV'], ['계시록', 'REV'], ['요한계시록', 'REV'], ['rev', 'REV'], ['revelation', 'REV'],
];

export const BOOK_ALIAS_TO_OSIS = Object.create(null);
for (const [alias, osis] of ALIAS_ENTRIES) {
  BOOK_ALIAS_TO_OSIS[alias] = osis;
}

const PUNCT_RE = /[.,?!;:/\\{}[\]()"'*^~·\-–—]/g;

export function resolveOsisAlias(raw) {
  if (typeof raw !== 'string') return null;
  const key = raw.trim().toLowerCase().replace(/\s+/g, '').replace(/\./g, '');
  if (!key) return null;
  return Object.prototype.hasOwnProperty.call(BOOK_ALIAS_TO_OSIS, key)
    ? BOOK_ALIAS_TO_OSIS[key]
    : null;
}

export function parseKoreanRef(query, bookBoundsMap = null) {
  const raw = String(query || '').trim();
  if (!raw) return null;

  const refRe = /^([가-힣0-9A-Za-z\s]+?)\s*(\d+)\s*(?:(?:장|편)\s*(?:(\d+)\s*절?(?:\s*[-~]\s*(\d+)\s*절?)?)?|[:.]\s*(\d+)(?:\s*[-~]\s*(\d+))?|\s+(\d+)(?:\s*[-~]\s*(\d+))?)?$/;
  const match = raw.match(refRe);
  if (!match) return null;

  const osis = resolveOsisAlias(match[1]);
  if (!osis) return null;

  const chapter = Number(match[2]);
  const verseRaw = match[3] ?? match[5] ?? match[7];
  const endVerseRaw = match[4] ?? match[6] ?? match[8];
  const verse = verseRaw !== undefined ? Number(verseRaw) : 1;
  const endVerse = endVerseRaw !== undefined ? Number(endVerseRaw) : verse;

  if (!Number.isInteger(chapter) || chapter < 1) return null;
  if (!Number.isInteger(verse) || verse < 1) return null;
  if (!Number.isInteger(endVerse) || endVerse < verse) return null;

  if (bookBoundsMap && bookBoundsMap[osis]) {
    const meta = bookBoundsMap[osis];
    if (meta.totalChapters && chapter > meta.totalChapters) return null;
    if (meta.chapterVerses && meta.chapterVerses[chapter]) {
      const maxVs = meta.chapterVerses[chapter];
      if (verse > maxVs || endVerse > maxVs) return null;
    }
  }

  return { osis, chapter, verse, endVerse };
}

export function normalizeSearchText(text) {
  return String(text || '')
    .toLowerCase()
    .replace(PUNCT_RE, '')
    .replace(/\s+/g, '');
}

export function tokenizeSearchQuery(query) {
  return String(query || '')
    .trim()
    .split(/\s+/)
    .map((tok) => normalizeSearchText(tok))
    .filter(Boolean);
}

export function normalizeWorshipQuery(raw) {
  const trimmed = String(raw || '').trim();
  if (!trimmed) {
    return { raw: '', compact: '', num: null, textCompact: '' };
  }
  const strippedPrefix = trimmed.replace(/^(?:새\s*찬송가|통일\s*찬송가|찬송가|교독문|새\s*교독문)\s*/u, '');
  const numMatch = strippedPrefix.match(/^(\d{1,3})\s*(?:장|번|편)?$/u);
  const num = numMatch ? Number(numMatch[1]) : null;
  const compact = normalizeSearchText(trimmed);
  const textCompact = normalizeSearchText(strippedPrefix.replace(/(?:장|번)$/u, ''));
  return { raw: trimmed, compact, num, textCompact };
}

export function matchWorshipItem(item, parsedQuery, kind) {
  if (!parsedQuery || !parsedQuery.raw) return true;
  if (parsedQuery.num !== null) {
    if (kind === 'hymns') {
      if (item.num === parsedQuery.num || (item.old && item.old === parsedQuery.num)) return true;
    } else if (kind === 'responsive') {
      if (item.num === parsedQuery.num) return true;
    }
  }
  const haystack = normalizeSearchText(
    [
      item.num != null ? String(item.num) : '',
      item.old ? String(item.old) : '',
      item.title || '',
      item.altTitle || '',
      item.category || '',
      item.section || '',
      item.season || '',
      item.group || '',
      item.citation || '',
      item.description || '',
      item.ref?.label || '',
    ].join(' ')
  );
  const needle = parsedQuery.textCompact || parsedQuery.compact;
  return needle ? haystack.includes(needle) : true;
}
