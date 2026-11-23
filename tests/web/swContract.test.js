import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..');
const WEB_DIR = path.join(ROOT, 'web');

const FROZEN_SHELL_ASSETS = [
  './',
  './index.html',
  './manifest.json',
  './css/tokens.css',
  './css/base.css',
  './css/layout.css',
  './css/components.css',
  './css/pulpit.css',
  './css/print.css',
  './css/motion.css',
  './icon.svg',
  './icons/icon-192.png',
  './icons/icon-512.png',
  './icons/apple-touch-icon.png',
  './js/main.js',
  './js/core/state.js',
  './js/core/dom.js',
  './js/core/urlSafety.js',
  './js/core/koreanQuery.js',
  './js/services/bibleService.js',
  './js/services/storage.js',
  './js/features/scriptureReader.js',
  './js/features/commentaryPanel.js',
  './js/features/crossRefPanel.js',
  './js/features/worshipPanel.js',
  './js/features/liturgyPanel.js',
  './js/features/sermonStudio.js',
  './js/features/pulpitPrompter.js',
  './js/features/biblePickerModal.js',
  './js/features/versionSettingsModal.js',
  './js/features/bookmarksSearchPanel.js',
];

function extractArrayLiteral(src, constName) {
  const re = new RegExp(`const\\s+${constName}\\s*=\\s*\\[([\\s\\S]*?)\\];`);
  const match = src.match(re);
  assert.ok(match, `Missing ${constName} in web/sw.js`);
  return [...match[1].matchAll(/['"]([^'"]+)['"]/g)].map((m) => m[1]);
}

test('web/sw.js matches SPEC.md v4 cache names, frozen SHELL_ASSETS, corpus routing, and NB-R2-03 data warm', () => {
  const swSrc = fs.readFileSync(path.join(WEB_DIR, 'sw.js'), 'utf8');

  assert.ok(swSrc.includes("const SHELL_CACHE = 'bible-station-shell-v4'"));
  assert.ok(swSrc.includes("const CORPUS_CACHE = 'bible-station-corpus-v4'"));
  const corpusReMatch = swSrc.match(/const\s+CORPUS_PATH_RE\s*=\s*\/(.+?)\/;/);
  assert.ok(corpusReMatch, 'Missing CORPUS_PATH_RE in web/sw.js');
  const corpusRe = new RegExp(corpusReMatch[1]);
  for (const sample of ['/data/krv/GEN.json', '/data/nkrv/GEN.json', '/data/rnksv/GEN.json', '/data/easy/GEN.json', '/data/esv/GEN.json', '/data/search/nkrv.json']) {
    assert.ok(corpusRe.test(sample), `CORPUS_PATH_RE must match ${sample}`);
  }
  assert.equal(corpusRe.test('/data/manifest.json'), false, 'CORPUS_PATH_RE must not match metadata manifest.json');
  assert.ok(swSrc.includes("type === 'SKIP_WAITING'"));
  const installBlock = swSrc.match(/addEventListener\(\s*'install'[\s\S]*?addEventListener\(\s*'activate'/);
  assert.ok(installBlock, 'Missing install listener in web/sw.js');
  assert.equal(installBlock[0].includes('skipWaiting'), false, 'install must not auto-skipWaiting');

  const shellAssets = extractArrayLiteral(swSrc, 'SHELL_ASSETS');
  assert.deepEqual(shellAssets, FROZEN_SHELL_ASSETS);

  const initialData = extractArrayLiteral(swSrc, 'INITIAL_DATA_ASSETS');
  assert.deepEqual(initialData, ['./data/manifest.json', './data/exegesis.json', './data/worship.json']);

  const strictDisk = process.env.SW_STRICT_DISK === '1';
  for (const asset of shellAssets) {
    if (asset === './') continue;
    if (!strictDisk && !asset.startsWith('./js/') && asset !== './manifest.json' && asset !== './index.html') {
      continue;
    }
    const diskPath = path.join(WEB_DIR, asset.slice(2));
    assert.ok(fs.existsSync(diskPath), `Precached asset missing on disk: ${asset}`);
  }
});

test('web/manifest.json matches Sanctuary Hanji colors, Korean name, icons, and zero stale copy', () => {
  const raw = fs.readFileSync(path.join(WEB_DIR, 'manifest.json'), 'utf8');
  assert.equal(raw.includes('8대 주석'), false, 'Stale "8대 주석" must not appear in web/manifest.json');

  const manifest = JSON.parse(raw);
  assert.equal(manifest.short_name, '말씀 서재');
  assert.equal(manifest.background_color, '#FAF6EE');
  assert.equal(manifest.theme_color, '#1B365D');

  const iconSrcs = (manifest.icons || []).map((i) => i.src);
  assert.ok(iconSrcs.includes('./icon.svg'));
  assert.ok(iconSrcs.includes('./icons/icon-192.png'));
  assert.ok(iconSrcs.includes('./icons/icon-512.png'));
});
