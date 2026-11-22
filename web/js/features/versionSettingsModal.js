import { el, iconEl, showConfirm, showToast } from '../core/dom.js';
import {
  parseCustomBibleFile,
  parseCustomHymnFile,
  validateByotFileSize,
} from '../services/storage.js';

export function createVersionSettingsModal({ store, service, archive, modalManager, callbacks }) {
  const { state } = store;

  function renderSelects() {
    const primarySel = document.getElementById('primaryVersionSelect');
    const parallelSel = document.getElementById('parallelVersionSelect');
    const versions = service.getAvailableVersions(state.customBibles);

    if (!versions.some((v) => v.id === state.primaryVersion)) {
      state.primaryVersion = service.getDefaultVersionId();
      store.savePrefs();
    }
    if (state.parallelVersion === state.primaryVersion) {
      state.parallelVersion = 'none';
      store.savePrefs();
    }

    if (primarySel) {
      primarySel.replaceChildren(
        ...versions.map((v) =>
          el('option', { value: v.id, selected: v.id === state.primaryVersion }, v.label)
        )
      );
      primarySel.value = state.primaryVersion;
    }

    if (parallelSel) {
      parallelSel.replaceChildren(
        el('option', { value: 'none', selected: state.parallelVersion === 'none' }, '대조 역본 사용 안 함'),
        ...versions.map((v) =>
          el(
            'option',
            {
              value: v.id,
              selected: v.id === state.parallelVersion,
              disabled: v.id === state.primaryVersion,
            },
            v.id === state.primaryVersion ? `${v.label} (현재 주 역본)` : v.label
          )
        )
      );
      parallelSel.value = state.parallelVersion;
    }
  }

  function renderCustomBibleList() {
    const listEl = document.getElementById('customBibleList');
    if (!listEl) return;

    if (!state.customBibles.length) {
      listEl.replaceChildren(
        el(
          'div',
          { className: 'empty-state' },
          '아직 불러온 개인 성경 파일이 없습니다. 목사님이 소유하신 역본 파일을 선택하면 이 기기에만 안전하게 저장됩니다.'
        )
      );
      return;
    }

    const cards = state.customBibles.map((item) =>
      el(
        'div',
        { className: 'card' },
        el(
          'div',
          { className: 'card-header' },
          el('strong', {}, item.name),
          el('span', { className: 'tag-success' }, `${item.bookCount}권 · ${item.verseCount.toLocaleString()}절`)
        ),
        el(
          'div',
          { className: 'action-row' },
          el(
            'button',
            {
              type: 'button',
              className: 'btn btn-primary',
              onClick: () => {
                state.primaryVersion = item.id;
                if (state.parallelVersion === item.id) state.parallelVersion = 'none';
                store.savePrefs();
                renderSelects();
                callbacks.onVersionChanged?.();
                showToast(`"${item.name}" 역본으로 전환했습니다.`);
              },
            },
            '이 역본으로 읽기'
          ),
          el(
            'button',
            {
              type: 'button',
              className: 'btn btn-danger',
              onClick: async () => {
                const ok = await showConfirm(modalManager, {
                  message: `"${item.name}" 역본을 이 기기에서 지우시겠습니까?`,
                  okLabel: '지우기',
                  cancelLabel: '취소',
                  danger: true,
                });
                if (!ok) return;
                const backup = { ...item };
                const prevPrimary = state.primaryVersion;
                await archive.deleteCustomBible(item.id);
                state.customBibles = state.customBibles.filter((b) => b.id !== item.id);
                if (state.primaryVersion === item.id) {
                  state.primaryVersion = service.getDefaultVersionId();
                }
                if (state.parallelVersion === item.id) state.parallelVersion = 'none';
                store.savePrefs();
                render();
                callbacks.onVersionChanged?.();
                showToast(`"${backup.name}" 역본을 삭제했습니다.`, {
                  undoLabel: '되돌리기',
                  durationMs: 5000,
                  onUndo: async () => {
                    await archive.saveCustomBible(backup);
                    state.customBibles = [...state.customBibles, backup];
                    state.primaryVersion = prevPrimary;
                    store.savePrefs();
                    render();
                    callbacks.onVersionChanged?.();
                    showToast(`"${backup.name}" 역본을 복원했습니다.`);
                  },
                });
              },
            },
            iconEl('icon-trash'),
            '삭제'
          )
        )
      )
    );
    listEl.replaceChildren(...cards);
  }

  function renderCustomHymnList() {
    const listEl = document.getElementById('customHymnList');
    if (!listEl) return;
    const count = Object.keys(state.customHymns || {}).length;
    if (!count) {
      listEl.replaceChildren(
        el('div', { className: 'empty-state' }, '불러온 개인 찬송가 가사가 없습니다. 파일을 선택하면 이 기기에서만 열람됩니다.')
      );
      return;
    }
    listEl.replaceChildren(
      el(
        'div',
        { className: 'card' },
        el(
          'div',
          { className: 'card-header' },
          el('strong', {}, '내 기기 저장 찬송가 가사'),
          el('span', { className: 'tag-success' }, `${count}곡 저장됨`)
        ),
        el(
          'div',
          { className: 'action-row' },
          el(
            'button',
            {
              type: 'button',
              className: 'btn btn-danger',
              onClick: async () => {
                const ok = await showConfirm(modalManager, {
                  message: `저장된 찬송가 가사 ${count}곡을 모두 지우시겠습니까?`,
                  okLabel: '모두 지우기',
                  cancelLabel: '취소',
                  danger: true,
                });
                if (!ok) return;
                const snapshot = { ...state.customHymns };
                await archive.clearCustomHymnLyrics();
                state.customHymns = {};
                renderCustomHymnList();
                callbacks.onCustomHymnsChanged?.();
                showToast('개인 찬송가 가사를 지웠습니다.', {
                  undoLabel: '되돌리기',
                  durationMs: 5000,
                  onUndo: async () => {
                    await archive.saveCustomHymnLyrics(snapshot);
                    state.customHymns = snapshot;
                    renderCustomHymnList();
                    callbacks.onCustomHymnsChanged?.();
                    showToast('찬송가 가사를 복원했습니다.');
                  },
                });
              },
            },
            iconEl('icon-trash'),
            '가사 비우기'
          )
        )
      )
    );
  }

  function render() {
    renderSelects();
    renderCustomBibleList();
    renderCustomHymnList();
  }

  function bindEvents() {
    const primarySel = document.getElementById('primaryVersionSelect');
    const parallelSel = document.getElementById('parallelVersionSelect');
    const bibleInput = document.getElementById('customBibleFileInput');
    const hymnInput = document.getElementById('customHymnFileInput');

    primarySel?.addEventListener('change', (e) => {
      state.primaryVersion = e.target.value;
      if (state.parallelVersion === state.primaryVersion) state.parallelVersion = 'none';
      store.savePrefs();
      renderSelects();
      callbacks.onVersionChanged?.();
    });

    parallelSel?.addEventListener('change', (e) => {
      const next = e.target.value;
      if (next === state.primaryVersion) {
        state.parallelVersion = 'none';
      } else {
        state.parallelVersion = next;
      }
      store.savePrefs();
      renderSelects();
      callbacks.onVersionChanged?.();
    });

    bibleInput?.addEventListener('change', async (e) => {
      const file = e.target.files?.[0];
      e.target.value = '';
      if (!file) return;
      const check = validateByotFileSize(file);
      if (!check.ok) {
        showToast(check.error);
        return;
      }
      try {
        const raw = await file.text();
        const record = parseCustomBibleFile(raw, file.name);
        if (!record.verseCount) {
          showToast('성경 구절을 찾지 못했습니다. "창1:1 말씀" 형식의 파일을 확인해 주세요.');
          return;
        }
        await archive.saveCustomBible(record);
        state.customBibles = [...state.customBibles, record];
        state.primaryVersion = record.id;
        if (state.parallelVersion === record.id) state.parallelVersion = 'none';
        store.savePrefs();
        render();
        callbacks.onVersionChanged?.();
        showToast(`"${record.name}" (${record.verseCount.toLocaleString()}절) 불러오기가 완료되었습니다.`);
      } catch {
        showToast('성경 파일을 읽지 못했습니다. 파일 형식을 확인해 주세요.');
      }
    });

    hymnInput?.addEventListener('change', async (e) => {
      const file = e.target.files?.[0];
      e.target.value = '';
      if (!file) return;
      const check = validateByotFileSize(file);
      if (!check.ok) {
        showToast(check.error);
        return;
      }
      try {
        const raw = await file.text();
        const parsed = parseCustomHymnFile(raw);
        const count = Object.keys(parsed).length;
        if (!count) {
          showToast('찬송가 가사를 찾지 못했습니다. "1장 ..." 형식을 확인해 주세요.');
          return;
        }
        await archive.saveCustomHymnLyrics(parsed);
        state.customHymns = { ...state.customHymns, ...parsed };
        renderCustomHymnList();
        callbacks.onCustomHymnsChanged?.();
        showToast(`찬송가 가사 ${count}곡을 이 기기에 저장했습니다.`);
      } catch {
        showToast('찬송가 파일을 읽지 못했습니다. 파일 형식을 확인해 주세요.');
      }
    });
  }

  function open(triggerEl = null) {
    render();
    modalManager.open('versionModal', triggerEl);
  }

  return { open, render, bindEvents };
}
