/**
 * Universal Command Registry & Fuzzy Omnibar Engine (⌘K / Ctrl+K / /)
 * Indexes workspace actions, 66 Bible books, 23 translations, 645 hymns,
 * 137 responsive readings, 95 CCMs, and 12 liturgies in one unified search space.
 */

import { normalizeSearchText, parseKoreanRef } from '../core/koreanQuery.js';

export function createCommandRegistry() {
  const staticCommands = new Map();
  const dynamicProviders = [];

  function register(cmd) {
    if (!cmd || !cmd.id) throw new Error('Command requires an id');
    staticCommands.set(cmd.id, {
      id: cmd.id,
      title: cmd.title || cmd.id,
      subtitle: cmd.subtitle || '',
      category: cmd.category || '명령',
      keywords: Array.isArray(cmd.keywords) ? cmd.keywords : [],
      shortcut: cmd.shortcut || '',
      icon: cmd.icon || 'icon-search',
      priority: Number(cmd.priority || 0),
      run: cmd.run,
    });
    return () => staticCommands.delete(cmd.id);
  }

  function registerProvider(providerFn) {
    if (typeof providerFn === 'function') dynamicProviders.push(providerFn);
  }

  function scoreCommand(cmd, normQuery, rawQuery) {
    if (!normQuery) return 10 + (cmd.priority || 0);
    const titleNorm = normalizeSearchText(cmd.title);
    const subNorm = normalizeSearchText(cmd.subtitle);
    const kwNorm = (cmd.keywords || []).map((k) => normalizeSearchText(k)).join(' ');
    const hay = `${titleNorm} ${subNorm} ${kwNorm}`;

    if (titleNorm === normQuery) return 120 + (cmd.priority || 0);
    if (titleNorm.startsWith(normQuery)) return 95 + (cmd.priority || 0);
    if (titleNorm.includes(normQuery)) return 75 + (cmd.priority || 0);
    if (hay.includes(normQuery)) return 55 + (cmd.priority || 0);

    const tokens = String(rawQuery || '').trim().split(/\s+/).map(normalizeSearchText).filter(Boolean);
    if (tokens.length > 1 && tokens.every((tk) => hay.includes(tk))) {
      return 45 + (cmd.priority || 0);
    }
    return 0;
  }

  function search(rawQuery = '', { limit = 16, bookBounds = null } = {}) {
    const trimmed = String(rawQuery || '').trim();
    const normQuery = normalizeSearchText(trimmed);
    const results = [];

    if (trimmed) {
      const parsedRef = parseKoreanRef(trimmed, bookBounds);
      if (parsedRef) {
        results.push({
          id: `warp:${parsedRef.osis}:${parsedRef.chapter}:${parsedRef.verse}`,
          title: `${parsedRef.osis} ${parsedRef.chapter}:${parsedRef.verse} 바로 이동`,
          subtitle: '성경 구절 즉시 워프 · Enter로 열기',
          category: '성경 워프',
          shortcut: 'Enter',
          icon: 'icon-bible',
          score: 200,
          _ref: parsedRef,
          run: (ctx) => ctx?.jumpToPassage?.(parsedRef.osis, parsedRef.chapter, parsedRef.verse),
        });
      }
    }

    for (const cmd of staticCommands.values()) {
      const score = scoreCommand(cmd, normQuery, trimmed);
      if (score > 0) results.push({ ...cmd, score });
    }

    for (const provider of dynamicProviders) {
      const items = provider(trimmed, normQuery) || [];
      for (const item of items) {
        results.push({
          priority: 0,
          icon: 'icon-search',
          ...item,
          score: item.score ?? scoreCommand(item, normQuery, trimmed),
        });
      }
    }

    results.sort((a, b) => (b.score - a.score) || a.title.localeCompare(b.title, 'ko'));
    return results.slice(0, limit);
  }

  function execute(id, ctx = {}) {
    const cmd = staticCommands.get(id);
    if (!cmd || typeof cmd.run !== 'function') return false;
    cmd.run(ctx);
    return true;
  }

  return { register, registerProvider, search, execute };
}
