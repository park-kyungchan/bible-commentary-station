export const DRIVE_IFRAME_SANDBOX = 'allow-scripts allow-same-origin allow-presentation';
export const DRIVE_IFRAME_REFERRER = 'no-referrer';
export const MAX_BYOT_FILE_BYTES = 15 * 1024 * 1024;

const DRIVE_ID_RE = /^[A-Za-z0-9_-]{10,64}$/;
const DRIVE_PREVIEW_RE = /^https:\/\/drive\.google\.com\/file\/d\/[A-Za-z0-9_-]{10,64}\/preview$/;
const DRIVE_VIEW_RE = /^https:\/\/drive\.google\.com\/file\/d\/[A-Za-z0-9_-]{10,64}\/view(?:\?usp=(?:drivesdk|sharing))?$/;

export const BIBLEHUB_SLUGS = Object.freeze({
  GEN: 'genesis', EXO: 'exodus', LEV: 'leviticus', NUM: 'numbers', DEU: 'deuteronomy',
  JOS: 'joshua', JDG: 'judges', RUT: 'ruth', '1SA': '1_samuel', '2SA': '2_samuel',
  '1KI': '1_kings', '2KI': '2_kings', '1CH': '1_chronicles', '2CH': '2_chronicles',
  EZR: 'ezra', NEH: 'nehemiah', EST: 'esther', JOB: 'job', PSA: 'psalms',
  PRO: 'proverbs', ECC: 'ecclesiastes', SNG: 'songs', ISA: 'isaiah', JER: 'jeremiah',
  LAM: 'lamentations', EZK: 'ezekiel', DAN: 'daniel', HOS: 'hosea', JOL: 'joel',
  AMO: 'amos', OBA: 'obadiah', JON: 'jonah', MIC: 'micah', NAM: 'nahum',
  HAB: 'habakkuk', ZEP: 'zephaniah', HAG: 'haggai', ZEC: 'zechariah', MAL: 'malachi',
  MAT: 'matthew', MRK: 'mark', LUK: 'luke', JHN: 'john', ACT: 'acts',
  ROM: 'romans', '1CO': '1_corinthians', '2CO': '2_corinthians', GAL: 'galatians',
  EPH: 'ephesians', PHP: 'philippians', COL: 'colossians', '1TH': '1_thessalonians',
  '2TH': '2_thessalonians', '1TI': '1_timothy', '2TI': '2_timothy', TIT: 'titus',
  PHM: 'philemon', HEB: 'hebrews', JAS: 'james', '1PE': '1_peter', '2PE': '2_peter',
  '1JN': '1_john', '2JN': '2_john', '3JN': '3_john', JUD: 'jude', REV: 'revelation',
});

export function sanitizeUrl(rawUrl) {
  if (typeof rawUrl !== 'string') return null;
  const trimmed = rawUrl.trim();
  if (!trimmed) return null;
  try {
    const parsed = new URL(trimmed);
    if (parsed.protocol !== 'https:') return null;
    return parsed.href;
  } catch {
    return null;
  }
}

export function isValidDriveId(driveId) {
  return typeof driveId === 'string' && DRIVE_ID_RE.test(driveId.trim());
}

export function sanitizeDrivePreviewUrl(rawUrl) {
  const safe = sanitizeUrl(rawUrl);
  if (!safe) return null;
  return DRIVE_PREVIEW_RE.test(safe) ? safe : null;
}

export function sanitizeDriveViewUrl(rawUrl) {
  const safe = sanitizeUrl(rawUrl);
  if (!safe) return null;
  return DRIVE_VIEW_RE.test(safe) ? safe : null;
}

export function buildDrivePreviewUrl(driveId) {
  if (!isValidDriveId(driveId)) return null;
  return `https://drive.google.com/file/d/${driveId.trim()}/preview`;
}

export function buildDriveViewUrl(driveId) {
  if (!isValidDriveId(driveId)) return null;
  return `https://drive.google.com/file/d/${driveId.trim()}/view?usp=sharing`;
}

export function getBibleHubSlug(osis) {
  if (typeof osis !== 'string') return 'genesis';
  const key = osis.trim().toUpperCase();
  return Object.prototype.hasOwnProperty.call(BIBLEHUB_SLUGS, key)
    ? BIBLEHUB_SLUGS[key]
    : 'genesis';
}

export function buildBibleHubCommentaryUrl(osis, chapter, verse) {
  const slug = getBibleHubSlug(osis);
  const ch = Math.max(1, Math.floor(Number(chapter) || 1));
  const vs = Math.max(1, Math.floor(Number(verse) || 1));
  return `https://biblehub.com/commentaries/${slug}/${ch}-${vs}.htm`;
}

export function buildTranslateAssistUrl(text, maxChars = 1200) {
  const clean = String(text || '').trim().slice(0, maxChars);
  if (!clean) return null;
  return `https://translate.google.com/?sl=en&tl=ko&text=${encodeURIComponent(clean)}&op=translate`;
}
