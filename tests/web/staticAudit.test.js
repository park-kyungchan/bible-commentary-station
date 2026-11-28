import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..');
const WEB_JS_DIR = path.join(ROOT, 'web', 'js');

const EXPECTED_MODULES = [
  'main.js',
  'kernel/signals.js',
  'kernel/eventBus.js',
  'kernel/commandRegistry.js',
  'kernel/pluginHost.js',
  'kernel/broadcastSync.js',
  'core/state.js',
  'core/dom.js',
  'core/urlSafety.js',
  'core/koreanQuery.js',
  'services/bibleService.js',
  'services/storage.js',
  'features/scriptureReader.js',
  'features/commentaryPanel.js',
  'features/crossRefPanel.js',
  'features/polyglotMatrix.js',
  'features/constellationGraph.js',
  'features/commandPalette.js',
  'features/worshipPanel.js',
  'features/liturgyPanel.js',
  'features/sermonStudio.js',
  'features/pulpitPrompter.js',
  'features/biblePickerModal.js',
  'features/versionSettingsModal.js',
  'features/bookmarksSearchPanel.js',
];

const FROZEN_ICONS = new Set([
  'icon-bible', 'icon-matrix', 'icon-graph', 'icon-study', 'icon-worship', 'icon-sermon', 'icon-pulpit',
  'icon-search', 'icon-bookmark', 'icon-sun', 'icon-moon', 'icon-help',
  'icon-settings', 'icon-chevron-left', 'icon-chevron-right', 'icon-print',
  'icon-close', 'icon-plus', 'icon-trash', 'icon-download', 'icon-upload',
  'icon-external', 'icon-back',
]);

function walkJs(dir, acc = []) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) walkJs(full, acc);
    else if (entry.name.endsWith('.js')) acc.push(full);
  }
  return acc;
}

test('legacy root JS files are retired and exact 25 v4 modules exist', () => {
  for (const legacy of ['app.js', 'bibleService.js', 'storage.js']) {
    assert.equal(fs.existsSync(path.join(WEB_JS_DIR, legacy)), false, `Legacy file must be deleted: web/js/${legacy}`);
  }
  const actual = walkJs(WEB_JS_DIR).map((f) => path.relative(WEB_JS_DIR, f).replace(/\\/g, '/')).sort();
  assert.deepEqual(actual, [...EXPECTED_MODULES].sort());
});

test('every web/js module is cleanly bounded (<= 480 LOC)', () => {
  for (const file of walkJs(WEB_JS_DIR)) {
    const lines = fs.readFileSync(file, 'utf8').split('\n').length;
    assert.ok(lines <= 480, `${path.relative(ROOT, file)} has ${lines} lines (max 480)`);
  }
});

test('module import dependency graph has zero circular dependencies', () => {
  const files = walkJs(WEB_JS_DIR);
  const graph = new Map();
  const importRe = /^\s*import\s+(?:[\s\S]*?\s+from\s+)?['"](\.[^'"]+)['"]/gm;

  for (const file of files) {
    const src = fs.readFileSync(file, 'utf8');
    const deps = [];
    for (const m of src.matchAll(importRe)) {
      const resolved = path.resolve(path.dirname(file), m[1]);
      assert.ok(fs.existsSync(resolved), `Missing import target ${m[1]} from ${file}`);
      deps.push(resolved);
    }
    graph.set(file, deps);
  }

  const state = new Map();
  const dfs = (node, stack) => {
    state.set(node, 1);
    for (const dep of graph.get(node) || []) {
      if (state.get(dep) === 1) {
        assert.fail(`Circular import detected: ${[...stack, dep].map((p) => path.relative(WEB_JS_DIR, p)).join(' -> ')}`);
      }
      if (!state.has(dep)) dfs(dep, [...stack, dep]);
    }
    state.set(node, 2);
  };
  for (const file of files) {
    if (!state.has(file)) dfs(file, [file]);
  }
});

test('zero innerHTML, zero visual inline styles, zero test-evasion, zero PII/jargon/emojis', () => {
  const bannedPii = ['복령교회', '박우호', 'cwy0675'];
  const bannedUiStrings = ['원문 API', '8대 주석', 'PPT 슬라이드', 'HTTP 404', 'FTS5', 'HelloAO 퍼블릭'];
  const emojiRe = /[\u{1F300}-\u{1FAFF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}]/u;

  for (const file of walkJs(WEB_JS_DIR)) {
    const rel = path.relative(ROOT, file);
    const src = fs.readFileSync(file, 'utf8');

    assert.equal(/\binnerHTML\b/.test(src), false, `innerHTML forbidden in ${rel}`);
    assert.equal(/return\s+0\s*===\s*1/.test(src), false, `return 0 === 1 artifact in ${rel}`);
    assert.equal(/setAttribute\s*\(\s*['"]style['"]/.test(src), false, `setAttribute('style',...) forbidden in ${rel}`);
    assert.equal(/\bstyle\s*:\s*['"`]/.test(src), false, `inline style: property forbidden in ${rel}`);

    for (const m of src.matchAll(/\.style\.([A-Za-z0-9_]+)\s*(\(|=)/g)) {
      const prop = m[1];
      assert.equal(prop, 'setProperty', `Direct .style.${prop} mutation forbidden in ${rel}`);
    }
    for (const m of src.matchAll(/\.style\.setProperty\(\s*['"]([^'"]+)['"]\s*,\s*([^)]+)\)/g)) {
      const varName = m[1];
      const expr = m[2];
      assert.ok(varName === '--pulpit-font-pt' || varName === '--pulpit-progress', `Disallowed CSS var ${varName} in ${rel}`);
      if (varName === '--pulpit-font-pt') {
        assert.ok(expr.includes('pt'), `--pulpit-font-pt must include pt unit in ${rel}`);
      }
    }

    for (const pii of bannedPii) {
      assert.equal(src.includes(pii), false, `PII/watermark "${pii}" found in ${rel}`);
    }
    for (const bad of bannedUiStrings) {
      assert.equal(src.includes(bad), false, `Forbidden UI jargon "${bad}" found in ${rel}`);
    }
    assert.equal(emojiRe.test(src), false, `Raw OS emoji found in ${rel}`);

    for (const m of src.matchAll(/iconEl\(\s*['"]([^'"]+)['"]/g)) {
      assert.ok(FROZEN_ICONS.has(m[1]), `Unregistered SVG symbol "${m[1]}" in ${rel}`);
    }
  }
});
