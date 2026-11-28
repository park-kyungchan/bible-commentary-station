/**
 * Lens 5: Homiletics Studio v4.0 (설교 공방)
 * Features: Real-time Korean/English speaking time estimator (280 chars/min),
 * visual pacing bar vs target duration, reorderable homiletic blocks (↑/↓),
 * auto-save, A4 large-print sheet, Markdown export, and full JSON backup/restore.
 */

import { btn, downloadTextFile, el, generateId, iconEl, setPrintDocument, showConfirm, showToast } from '../core/dom.js';
import { createDefaultSermon, SermonArchiveStore } from '../services/storage.js';

const CHARS_PER_MIN = 280;

const QUICK_PASSAGES = Object.freeze([
  { osis: 'GEN', ch: 22, s: 1, e: 14, label: '창세기 22:1-14' },
  { osis: 'PSA', ch: 23, s: 1, e: 6, label: '시편 23:1-6' },
  { osis: 'ISA', ch: 40, s: 27, e: 31, label: '이사야 40:27-31' },
  { osis: 'MAT', ch: 11, s: 28, e: 30, label: '마태복음 11:28-30' },
  { osis: 'JHN', ch: 3, s: 16, e: 17, label: '요한복음 3:16-17' },
  { osis: 'ROM', ch: 8, s: 28, e: 32, label: '로마서 8:28-32' },
]);

function formatSavedTime(iso) {
  if (!iso) return '';
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? '' : `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`;
}

export function estimateSpeakingStats(sermon) {
  const outline = sermon?.outline || [];
  let totalChars = 0;
  const perBlock = outline.map((pt) => {
    const chars = String(pt.content || '').replace(/\s+/g, '').length;
    totalChars += chars;
    return { id: pt.id, chars, mins: +(chars / CHARS_PER_MIN).toFixed(1) };
  });
  const estimatedMins = +(totalChars / CHARS_PER_MIN).toFixed(1);
  const targetMins = Math.max(5, Number(sermon?.targetDurationMins) || 30);
  const ratio = Math.min(1.35, estimatedMins / targetMins);
  return { totalChars, estimatedMins, targetMins, ratio, perBlock };
}

export function createSermonStudio({ store, service, archive, modalManager, callbacks }) {
  const { state } = store;

  function getActiveSermon() {
    if (!state.sermons.length) {
      const def = createDefaultSermon();
      state.sermons = [def];
      state.activeSermonId = def.id;
    }
    return state.sermons.find((s) => s.id === state.activeSermonId) || state.sermons[0];
  }

  function updateSaveStatus(result = null) {
    const badge = document.getElementById('sermonSaveStatus');
    if (!badge) return;
    const mode = result?.persisted || state.persistenceMode;
    const t = formatSavedTime(result?.savedAt || state.lastSavedAt || getActiveSermon()?.updatedAt);
    badge.textContent = mode === 'memory' ? '임시 저장 모드 (백업 필요)' : (t ? `자동 저장됨 · ${t}` : '자동 저장 준비됨');
  }

  function refreshPacingMeter(sermon) {
    const meter = document.getElementById('sermonPacingMeter');
    if (!meter) return;
    const stats = estimateSpeakingStats(sermon);
    const pct = Math.min(100, Math.round((stats.estimatedMins / stats.targetMins) * 100));
    const over = stats.estimatedMins > stats.targetMins;
    meter.replaceChildren(
      el(
        'div',
        { className: 'pacing-head' },
        el('strong', {}, `실시간 설교 분량 예측 · 약 ${stats.estimatedMins}분 / 목표 ${stats.targetMins}분`),
        el('span', { className: `pacing-badge ${over ? 'is-over' : 'is-ok'}` },
          over ? `${(stats.estimatedMins - stats.targetMins).toFixed(1)}분 초과` : `${stats.totalChars.toLocaleString('ko-KR')}자 · 여유 ${(stats.targetMins - stats.estimatedMins).toFixed(1)}분`)
      ),
      el('progress', { className: `pacing-progress ${over ? 'is-over' : ''}`, max: '100', value: String(pct) })
    );
  }

  function scheduleSave(sermon) {
    refreshPacingMeter(sermon);
    archive.scheduleSermonSave(sermon, 400, (res) => {
      state.persistenceMode = res.persisted;
      state.lastSavedAt = res.savedAt;
      updateSaveStatus(res);
    });
  }

  function buildPulpitDeck(sermon = getActiveSermon()) {
    const slides = [
      { heading: sermon.title || '설교 말씀', body: [sermon.scriptureRef, sermon.date].filter(Boolean).join('\n') },
      ...(sermon.outline || []).map((pt) => ({ heading: `[${pt.section || '대지'}] ${pt.title || ''}`, body: pt.content || '' })),
    ];
    if (sermon.clips?.length) {
      slides.push({ heading: '참고 인용 말씀', body: sermon.clips.map((c) => `${c.source}\n${c.text}`).join('\n\n') });
    }
    return { title: sermon.title || '설교 강단 화면', targetDurationMins: Number(sermon.targetDurationMins) || 30, slides };
  }

  function printSermon() {
    const sermon = getActiveSermon();
    const sections = (sermon.outline || []).map((pt) => ({
      heading: `[${pt.section || '대지'}] ${pt.title || ''}`,
      lines: String(pt.content || '').split('\n'),
    }));
    if (sermon.clips?.length) {
      sections.push({ heading: '참고 말씀·인용 자료', lines: sermon.clips.map((c) => `${c.source}: ${c.text}`) });
    }
    setPrintDocument(sermon.title || '설교 원고', `${sermon.scriptureRef || ''} · ${sermon.date || ''} · 목표 ${sermon.targetDurationMins || 30}분`, sections);
    window.print();
  }

  function addClip(source, text) {
    const sermon = getActiveSermon();
    sermon.clips = [...(sermon.clips || []), { id: generateId('clip'), source, text: String(text || '').trim(), addedAt: new Date().toISOString() }];
    scheduleSave(sermon);
    if (state.mode === 'sermon') renderClips();
    showToast(`"${sermon.title}" 설교 노트에 담았습니다.`);
  }

  async function applyPassageSelection(sel, autoClip = false) {
    const sermon = getActiveSermon();
    sermon.scriptureRef = sel.refLabel;
    scheduleSave(sermon);
    renderEditor();
    if (autoClip && service?.getVersionChapterMap) {
      try {
        const chMap = await service.getVersionChapterMap(state.primaryVersion, sel.osis, sel.chapter, state.customBibles);
        const lines = [];
        for (let v = sel.startVerse; v <= sel.endVerse; v += 1) if (chMap?.[v]) lines.push(`${v}. ${chMap[v]}`);
        if (lines.length) {
          const verLabel = service.getVersionInfo?.(state.primaryVersion, state.customBibles)?.shortLabel || state.primaryVersion;
          addClip(`${sel.refLabel} (${verLabel})`, lines.join('\n'));
          return;
        }
      } catch { /* fallback to toast */ }
    }
    showToast(`설교 본문을 "${sel.refLabel}" 말씀으로 선택했습니다.`);
  }

  function moveOutlineBlock(sermon, idx, delta) {
    const target = idx + delta;
    if (target < 0 || target >= (sermon.outline || []).length) return;
    const next = [...sermon.outline];
    const [moved] = next.splice(idx, 1);
    next.splice(target, 0, moved);
    sermon.outline = next;
    scheduleSave(sermon);
    renderEditor();
  }

  function renderSelect() {
    const sel = document.getElementById('sermonSelect');
    if (!sel) return;
    const active = getActiveSermon();
    sel.replaceChildren(...state.sermons.map((s) => el('option', { value: s.id, selected: s.id === active.id }, `${s.date || ''} · ${s.title || '제목 없음'}`)));
    sel.value = active.id;
  }

  function renderEditor() {
    const pane = document.getElementById('sermonEditorPane');
    if (!pane) return;
    const sermon = getActiveSermon();
    const curBook = service?.getBookMeta?.(state.osis);
    const curPlaceLabel = `${curBook?.name || state.osis} ${state.chapter}:${state.selectedVerse || 1}`;

    const pacingCard = el('section', { id: 'sermonPacingMeter', className: 'card pacing-card', 'aria-live': 'polite' });

    const pickerTrigger = el('button', {
      id: 'btnSermonPickPassage', type: 'button', className: 'current-place-btn sermon-passage-btn', 'aria-haspopup': 'dialog',
      onClick: (e) => callbacks.onOpenPassagePicker?.(e.currentTarget, (sel) => applyPassageSelection(sel, true)),
    }, iconEl('icon-bible'), el('span', { id: 'sermonScriptureRefText' }, sermon.scriptureRef || '눌러서 본문 말씀 선택'), el('span', { className: 'place-caret', 'aria-hidden': 'true' }, '▾'));

    const quickPills = el('div', { className: 'filter-strip', role: 'group', 'aria-label': '자주 쓰는 본문 바로 선택' },
      btn('filter-pill btn-secondary', () => applyPassageSelection({
        osis: state.osis, chapter: state.chapter, startVerse: state.selectedVerse || 1, endVerse: state.selectedVerse || 1, refLabel: curPlaceLabel,
      }, true), `현재 읽던 말씀 (${curPlaceLabel})`),
      ...QUICK_PASSAGES.map((qp) => el('button', {
        type: 'button', className: `filter-pill ${sermon.scriptureRef === qp.label ? 'btn-primary' : 'btn-ghost'}`,
        'aria-pressed': sermon.scriptureRef === qp.label ? 'true' : 'false',
        onClick: () => applyPassageSelection({ osis: qp.osis, chapter: qp.ch, startVerse: qp.s, endVerse: qp.e, refLabel: qp.label }, true),
      }, qp.label))
    );

    const metaCard = el('section', { className: 'card' },
      el('label', {}, '설교 제목', el('input', {
        type: 'text', className: 'input-field', value: sermon.title || '', placeholder: '설교 제목을 입력하세요',
        onInput: (e) => { sermon.title = e.target.value; renderSelect(); scheduleSave(sermon); },
      })),
      el('div', { className: 'sermon-passage-box' },
        el('div', { className: 'card-header' },
          el('strong', {}, '본문 말씀 (눌러서 책·장·절 선택)'),
          el('span', { className: 'tag-provenance' }, '선택 시 본문이 참고 자료에 자동 수록됩니다')
        ),
        el('div', { className: 'action-row' }, pickerTrigger),
        quickPills
      ),
      el('div', { className: 'action-row' },
        el('label', {}, '설교 날짜', el('input', {
          type: 'date', className: 'input-field', value: sermon.date || '',
          onChange: (e) => { sermon.date = e.target.value; renderSelect(); scheduleSave(sermon); },
        })),
        el('label', {}, '목표 시간(분)', el('input', {
          type: 'number', className: 'input-field', min: '5', max: '120', value: String(sermon.targetDurationMins || 30),
          onInput: (e) => { sermon.targetDurationMins = Math.max(5, Math.min(120, Number(e.target.value) || 30)); scheduleSave(sermon); },
        }))
      )
    );

    const outlineLen = (sermon.outline || []).length;
    const outlineCards = (sermon.outline || []).map((pt, idx) => {
      const blockMins = +(String(pt.content || '').replace(/\s+/g, '').length / CHARS_PER_MIN).toFixed(1);
      return el('article', { className: 'card outline-card' },
        el('div', { className: 'card-header' },
          el('input', { type: 'text', className: 'input-field', value: pt.section || '', 'aria-label': `구분 ${idx + 1}`, onInput: (e) => { pt.section = e.target.value; scheduleSave(sermon); } }),
          el('input', { type: 'text', className: 'input-field', value: pt.title || '', placeholder: '소제목을 입력하세요', 'aria-label': `소제목 ${idx + 1}`, onInput: (e) => { pt.title = e.target.value; scheduleSave(sermon); } }),
          el('span', { className: 'tag-provenance' }, `~${blockMins}분`),
          el('button', { type: 'button', className: 'btn btn-ghost btn-icon-sm', disabled: idx === 0, 'aria-label': '위로 이동', onClick: () => moveOutlineBlock(sermon, idx, -1) }, '↑'),
          el('button', { type: 'button', className: 'btn btn-ghost btn-icon-sm', disabled: idx === outlineLen - 1, 'aria-label': '아래로 이동', onClick: () => moveOutlineBlock(sermon, idx, 1) }, '↓'),
          btn('btn btn-danger', async () => {
            const ok = await showConfirm(modalManager, { message: `"${pt.title || pt.section || '이 대지'}" 항목을 삭제하시겠습니까?`, okLabel: '삭제', cancelLabel: '취소', danger: true });
            if (!ok) return;
            const removed = { ...pt };
            sermon.outline = sermon.outline.filter((x) => x.id !== pt.id);
            scheduleSave(sermon); renderEditor();
            showToast('대지 항목을 삭제했습니다.', {
              undoLabel: '되돌리기', durationMs: 5000,
              onUndo: () => {
                const next = [...sermon.outline]; next.splice(idx, 0, removed); sermon.outline = next;
                scheduleSave(sermon); renderEditor(); showToast('삭제한 대지를 복원했습니다.');
              },
            });
          }, iconEl('icon-trash'), '삭제')
        ),
        el('textarea', { className: 'input-field', rows: '4', 'aria-label': `대지 내용 ${idx + 1}`, placeholder: '설교 내용을 자유롭게 적어 주세요.', onInput: (e) => { pt.content = e.target.value; scheduleSave(sermon); } }, pt.content || '')
      );
    });

    const addBtn = btn('btn btn-secondary', () => {
      sermon.outline = [...(sermon.outline || []), { id: generateId('sec'), section: `대지 ${(sermon.outline?.length || 0) + 1}`, title: '', content: '' }];
      scheduleSave(sermon);
      renderEditor();
    }, iconEl('icon-plus'), '새 대지 추가');

    pane.replaceChildren(pacingCard, metaCard, ...outlineCards, addBtn);
    refreshPacingMeter(sermon);
  }

  function renderClips() {
    const pane = document.getElementById('sermonClipsPane');
    if (!pane) return;
    const sermon = getActiveSermon();
    const clips = sermon.clips || [];
    const heading = el('h3', {}, `담아둔 말씀·참고 자료 (${clips.length}건)`);
    if (!clips.length) {
      pane.replaceChildren(heading, el('div', { className: 'card empty-state' }, '성경·주석·다중 역본·성좌도에서 [노트에 담기]를 누르면 이곳에 모아집니다.'));
      return;
    }
    const cards = clips.map((clip, idx) => el('article', { className: 'card clip-card' },
      el('div', { className: 'card-header' }, el('strong', {}, clip.source)),
      el('p', {}, clip.text),
      el('div', { className: 'action-row' },
        btn('btn btn-secondary', () => {
          if (!sermon.outline?.length) sermon.outline = [{ id: generateId('sec'), section: '본론', title: '', content: '' }];
          const target = sermon.outline[sermon.outline.length - 1];
          target.content = target.content ? `${target.content}\n\n[${clip.source}] ${clip.text}` : `[${clip.source}] ${clip.text}`;
          scheduleSave(sermon); renderEditor(); showToast('마지막 대지에 본문을 넣었습니다.');
        }, iconEl('icon-plus'), '대지에 넣기'),
        btn('btn btn-ghost', async () => {
          const ok = await showConfirm(modalManager, { message: '담아둔 참고 자료를 지우시겠습니까?', okLabel: '지우기', cancelLabel: '취소', danger: true });
          if (!ok) return;
          const backup = { ...clip };
          sermon.clips = sermon.clips.filter((c) => c.id !== clip.id);
          scheduleSave(sermon); renderClips();
          showToast('참고 자료를 지웠습니다.', {
            undoLabel: '되돌리기', durationMs: 5000,
            onUndo: () => {
              const next = [...sermon.clips]; next.splice(idx, 0, backup); sermon.clips = next;
              scheduleSave(sermon); renderClips(); showToast('참고 자료를 복원했습니다.');
            },
          });
        }, iconEl('icon-trash'), '지우기')
      )
    ));
    pane.replaceChildren(heading, ...cards);
  }

  async function exportFullBackup() {
    const payload = await archive.exportBackupPayload({ highlights: state.highlights, prefs: store.getPrefsSnapshot() });
    downloadTextFile(JSON.stringify(payload, null, 2), 'application/json;charset=utf-8', `말씀서재-백업-${new Date().toISOString().slice(0, 10)}.json`);
    showToast('전체 백업 파일을 저장했습니다.');
  }

  function render() { renderSelect(); updateSaveStatus(); renderEditor(); renderClips(); }

  function bindEvents() {
    document.getElementById('sermonSelect')?.addEventListener('change', (e) => { state.activeSermonId = e.target.value; render(); });

    document.getElementById('btnNewSermon')?.addEventListener('click', async () => {
      const fresh = { ...createDefaultSermon(), id: generateId('sermon'), title: '새 설교 말씀', outline: [{ id: generateId('sec'), section: '서론', title: '', content: '' }], clips: [] };
      const res = await archive.saveSermon(fresh);
      state.sermons = [res.data, ...state.sermons];
      state.activeSermonId = res.data.id;
      render();
      showToast('새 설교 문서를 만들었습니다.');
    });

    document.getElementById('btnDuplicateSermon')?.addEventListener('click', async () => {
      const cur = getActiveSermon();
      const copy = {
        ...cur, id: generateId('sermon'), title: `${cur.title} (사본)`,
        outline: (cur.outline || []).map((pt) => ({ ...pt, id: generateId('sec') })),
        clips: (cur.clips || []).map((c) => ({ ...c, id: generateId('clip') })),
      };
      const res = await archive.saveSermon(copy);
      state.sermons = [res.data, ...state.sermons];
      state.activeSermonId = res.data.id;
      render();
      showToast('설교 문서를 복제했습니다.');
    });

    document.getElementById('btnDeleteSermon')?.addEventListener('click', async () => {
      const cur = getActiveSermon();
      const ok = await showConfirm(modalManager, { message: `"${cur.title}" 설교를 삭제하시겠습니까?`, okLabel: '삭제', cancelLabel: '취소', danger: true });
      if (!ok) return;
      const backup = { ...cur };
      await archive.deleteSermon(cur.id);
      state.sermons = state.sermons.filter((s) => s.id !== cur.id);
      if (!state.sermons.length) state.sermons = [(await archive.saveSermon(createDefaultSermon())).data];
      state.activeSermonId = state.sermons[0].id;
      render();
      showToast(`"${backup.title}" 설교를 삭제했습니다.`, {
        undoLabel: '되돌리기', durationMs: 5000,
        onUndo: async () => {
          const restored = await archive.saveSermon(backup);
          state.sermons = [restored.data, ...state.sermons];
          state.activeSermonId = restored.data.id;
          render();
          showToast('삭제한 설교를 복원했습니다.');
        },
      });
    });

    document.getElementById('btnSermonPrint')?.addEventListener('click', printSermon);
    document.getElementById('btnSermonExportMd')?.addEventListener('click', () => {
      const sermon = getActiveSermon();
      const safeTitle = (sermon.title || '설교원고').replace(/[^\w가-힣-]+/g, '_');
      downloadTextFile(SermonArchiveStore.toMarkdown(sermon), 'text/markdown;charset=utf-8', `${safeTitle}.md`);
      showToast('설교 원고 파일을 저장했습니다.');
    });

    document.getElementById('btnSermonBackupJson')?.addEventListener('click', exportFullBackup);
    const restoreInput = document.getElementById('sermonRestoreInput');
    document.getElementById('btnSermonRestoreJson')?.addEventListener('click', () => restoreInput?.click());
    restoreInput?.addEventListener('change', async (e) => {
      const file = e.target.files?.[0];
      e.target.value = '';
      if (!file) return;
      try {
        const restored = await archive.importBackupPayload(await file.text());
        if (restored.sermons.length) {
          state.sermons = await archive.listSermons();
          state.activeSermonId = state.sermons[0]?.id || null;
        }
        if (restored.worshipOrders.length) state.worshipOrders = await archive.listWorshipOrders();
        if (restored.highlights) { state.highlights = { ...state.highlights, ...restored.highlights }; store.saveHighlights(); }
        if (restored.prefs) { store.applyPrefsSnapshot(restored.prefs); callbacks.onPrefsRestored?.(); }
        render();
        showToast(`백업에서 설교 ${restored.sermons.length}편을 복원했습니다.`);
      } catch {
        showToast('백업 파일을 읽지 못했습니다. 올바른 백업 파일인지 확인해 주세요.');
      }
    });

    document.getElementById('btnSermonPulpit')?.addEventListener('click', () => callbacks.onLaunchPulpit?.(buildPulpitDeck()));
  }

  return { bindEvents, render, addClip, applyPassageSelection, buildPulpitDeck, exportFullBackup, updateSaveStatus };
}
