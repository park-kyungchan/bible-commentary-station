import { btn, el, generateId, iconEl, setPrintDocument, showConfirm, showToast } from '../core/dom.js';
import { matchWorshipItem, normalizeWorshipQuery } from '../core/koreanQuery.js';

const LITURGY_CATEGORIES = [
  { key: '전체', label: '전체' },
  { key: 'creed', label: '신앙고백' },
  { key: 'prayer', label: '주기도문' },
  { key: 'communion', label: '성찬' },
  { key: 'benediction', label: '축도' },
];

const VARIANT_LABELS = Object.freeze({ ecumenical: '새 번역', traditional: '전통', standard: '예식' });
const SLOT_TYPE_LABELS = Object.freeze({
  hymn: '찬송가', liturgy: '예배 예전', responsive: '교독문',
  scripture: '성경 봉독', sermon: '설교 말씀', prayer: '기도', note: '순서 메모',
});

export function createLiturgyPanel({ store, service, archive, modalManager, callbacks }) {
  const { state } = store;
  let liturgyCategory = '전체';
  let activeLiturgy = null;
  let activeOrder = null;

  function buildLiturgyDeck(liturgy) {
    const slides = (liturgy.slides || []).map((sl, idx) => ({
      heading: sl.heading || `${liturgy.title} (${idx + 1})`,
      body: (sl.lines || []).join('\n'),
    }));
    return { title: liturgy.title, targetDurationMins: 5, slides: slides.length ? slides : [{ heading: liturgy.title, body: '' }] };
  }

  function printLiturgy(liturgy) {
    const subtitle = [VARIANT_LABELS[liturgy.variant] || '', liturgy.citation || ''].filter(Boolean).join(' · ');
    setPrintDocument(liturgy.title, subtitle, (liturgy.slides || []).map((sl) => ({ heading: sl.heading || '', lines: sl.lines || [] })));
    window.print();
  }

  function renderLiturgyDetail(detailEl, liturgy) {
    activeLiturgy = liturgy;
    const viewEl = document.getElementById('viewWorship');
    if (viewEl) viewEl.dataset.hasDetail = 'true';

    const variant = VARIANT_LABELS[liturgy.variant] || '';
    const backBtn = el('button', {
      type: 'button', className: 'btn btn-ghost', dataset: { action: 'worship-back' },
      onClick: () => {
        activeLiturgy = null;
        if (viewEl) viewEl.dataset.hasDetail = 'false';
        detailEl.replaceChildren();
        callbacks.onBackToList?.();
      },
    }, iconEl('icon-back'), '예전 목록으로');

    const slides = (liturgy.slides || []).map((sl) =>
      el('section', { className: 'card liturgy-slide' },
        sl.heading ? el('h3', {}, sl.heading) : null,
        ...(sl.lines || []).map((line) => el('p', {}, line))
      )
    );

    detailEl.replaceChildren(
      el('div', { className: 'card-header' }, backBtn, el('h2', {}, liturgy.title), variant ? el('span', { className: 'tag-accent' }, variant) : null),
      liturgy.citation ? el('p', { className: 'tag-provenance' }, liturgy.citation) : null,
      el('div', { className: 'action-row' },
        btn('btn btn-primary', () => callbacks.onLaunchPulpit?.(buildLiturgyDeck(liturgy)), iconEl('icon-pulpit'), '강단 화면으로 열기'),
        btn('btn btn-secondary', () => printLiturgy(liturgy), iconEl('icon-print'), '큰 글씨 인쇄')
      ),
      ...slides
    );
  }

  function renderLiturgies(filterEl, listEl, detailEl, rawQuery) {
    const liturgies = service.worship?.liturgies || [];
    const parsedQ = normalizeWorshipQuery(rawQuery);

    filterEl.replaceChildren(...LITURGY_CATEGORIES.map((cat) => el('button', {
      type: 'button',
      className: `filter-pill ${liturgyCategory === cat.key ? 'btn-primary' : 'btn-ghost'}`,
      'aria-pressed': liturgyCategory === cat.key ? 'true' : 'false',
      onClick: () => { liturgyCategory = cat.key; renderLiturgies(filterEl, listEl, detailEl, state.worshipSearch); },
    }, cat.label)));

    const filtered = liturgies.filter((item) => (liturgyCategory === '전체' || item.category === liturgyCategory) && matchWorshipItem(item, parsedQ, 'liturgy'));
    if (!filtered.length) {
      listEl.replaceChildren(el('div', { className: 'card empty-state' }, '조건에 맞는 예배 예전이 없습니다.'));
      return;
    }

    listEl.replaceChildren(...filtered.map((item) => {
      const variant = VARIANT_LABELS[item.variant] || '';
      return el('article', { className: 'card liturgy-card' },
        el('div', { className: 'card-header' }, el('strong', {}, item.title), variant ? el('span', { className: 'tag-accent' }, variant) : null),
        item.citation ? el('p', { className: 'tag-provenance' }, item.citation) : null,
        el('div', { className: 'action-row' },
          btn('btn btn-secondary', () => renderLiturgyDetail(detailEl, item), '본문 보기'),
          btn('btn btn-primary', () => callbacks.onLaunchPulpit?.(buildLiturgyDeck(item)), iconEl('icon-pulpit'), '강단 화면으로 열기'),
          btn('btn btn-ghost', () => printLiturgy(item), iconEl('icon-print'), '큰 글씨 인쇄')
        )
      );
    }));
  }

  async function buildOrderDeck(order) {
    const slides = [{ heading: order.title, body: `${order.date || ''}\n${order.description || '예배 순서 안내'}` }];
    const liturgies = service.worship?.liturgies || [];
    const hymns = service.worship?.hymns || [];
    const rrs = service.worship?.responsiveReadings || [];

    for (const slot of order.slots || []) {
      const val = String(slot.value || slot.defaultRef || '').trim();
      if (slot.slotType === 'liturgy' && val) {
        const lit = liturgies.find((l) => l.id === val || l.title.includes(val));
        if (lit) {
          for (const sl of lit.slides || []) slides.push({ heading: `${slot.label} · ${lit.title}`, body: (sl.lines || []).join('\n') });
          continue;
        }
      }
      if (slot.slotType === 'responsive' && val) {
        const rr = rrs.find((r) => r.num === Number(val.replace(/[^\d]/g, '')));
        if (rr) {
          const lines = await service.resolveResponsiveReadingLines(rr, state.primaryVersion, state.customBibles);
          const roleText = lines.map((l) => `[${l.role === 'leader' ? '인도자' : l.role === 'congregation' ? '회중' : '다같이'}] ${l.text}`);
          slides.push({ heading: `${slot.label} · 교독문 ${rr.num}번 ${rr.title}`, body: roleText.join('\n\n') || rr.title });
          continue;
        }
      }
      if (slot.slotType === 'hymn' && val) {
        const h = hymns.find((x) => x.num === Number(val.replace(/[^\d]/g, '')));
        const lyrics = h ? state.customHymns?.[h.num] : '';
        slides.push({
          heading: `${slot.label} · ${h ? `새찬송가 ${h.num}장 ${h.title}` : val}`,
          body: lyrics || (h?.ref?.label ? `관련 말씀: ${h.ref.label}` : '찬송가 함께 부르기'),
        });
        continue;
      }
      slides.push({ heading: slot.label, body: val || '순서 진행' });
    }
    return { title: order.title, targetDurationMins: 60, slides };
  }

  function printOrder(order) {
    setPrintDocument(
      order.title,
      order.date || order.description || '',
      (order.slots || []).map((s) => ({ heading: `${s.order}. ${s.label}`, lines: [s.value || s.defaultRef || ''] }))
    );
    window.print();
  }

  function renderOrderEditor(detailEl, orderObj) {
    activeOrder = {
      ...orderObj,
      id: orderObj.id || generateId('order'),
      date: orderObj.date || new Date().toISOString().slice(0, 10),
      slots: (orderObj.slots || []).map((s) => ({ ...s, value: s.value ?? s.defaultRef ?? '' })),
    };
    const viewEl = document.getElementById('viewWorship');
    if (viewEl) viewEl.dataset.hasDetail = 'true';

    const liturgies = service.worship?.liturgies || [];
    const backBtn = el('button', {
      type: 'button', className: 'btn btn-ghost', dataset: { action: 'worship-back' },
      onClick: () => {
        activeOrder = null;
        if (viewEl) viewEl.dataset.hasDetail = 'false';
        detailEl.replaceChildren();
        callbacks.onBackToList?.();
      },
    }, iconEl('icon-back'), '예배 순서 목록으로');

    const slotNodes = activeOrder.slots.map((slot) => {
      let control;
      if (slot.slotType === 'liturgy' && liturgies.length) {
        control = el('select', { className: 'select-field', 'aria-label': slot.label, onChange: (e) => { slot.value = e.target.value; } },
          el('option', { value: '' }, '예전 선택 안 함'),
          ...liturgies.map((l) => el('option', { value: l.id, selected: slot.value === l.id }, l.title))
        );
      } else {
        const placeholder = slot.slotType === 'hymn' ? '찬송가 번호 (예: 1장, 305장)'
          : slot.slotType === 'responsive' ? '교독문 번호 (예: 1번, 92번)' : '말씀 본문이나 순서 내용을 입력하세요';
        control = el('input', { type: 'text', className: 'input-field', value: slot.value || '', placeholder, 'aria-label': slot.label, onInput: (e) => { slot.value = e.target.value; } });
      }
      return el('div', { className: 'card template-slot' },
        el('div', { className: 'card-header' }, el('strong', {}, `${slot.order}. ${slot.label}`), el('span', { className: 'tag-provenance' }, SLOT_TYPE_LABELS[slot.slotType] || '순서')),
        control
      );
    });

    detailEl.replaceChildren(
      el('div', { className: 'card-header' }, backBtn, el('h2', {}, activeOrder.title)),
      el('div', { className: 'action-row' },
        el('input', { type: 'text', className: 'input-field', value: activeOrder.title, 'aria-label': '예배 순서 제목', onInput: (e) => { activeOrder.title = e.target.value; } }),
        el('input', { type: 'date', className: 'input-field', value: activeOrder.date, 'aria-label': '예배 날짜', onChange: (e) => { activeOrder.date = e.target.value; } })
      ),
      el('div', { className: 'action-row' },
        btn('btn btn-primary', async () => callbacks.onLaunchPulpit?.(await buildOrderDeck(activeOrder)), iconEl('icon-pulpit'), '강단 화면으로 순서 진행'),
        btn('btn btn-secondary', async () => {
          const res = await archive.saveWorshipOrder(activeOrder);
          const idx = state.worshipOrders.findIndex((o) => o.id === res.data.id);
          if (idx >= 0) state.worshipOrders[idx] = res.data;
          else state.worshipOrders = [res.data, ...state.worshipOrders];
          showToast('예배 순서를 저장했습니다.');
        }, iconEl('icon-download'), '예배 순서 저장'),
        btn('btn btn-ghost', () => printOrder(activeOrder), iconEl('icon-print'), '큰 글씨 주보 인쇄')
      ),
      ...slotNodes
    );
  }

  function renderTemplates(filterEl, listEl, detailEl, rawQuery) {
    filterEl.replaceChildren();
    const parsedQ = normalizeWorshipQuery(rawQuery);
    const items = [];

    for (const saved of state.worshipOrders || []) {
      if (!matchWorshipItem(saved, parsedQ, 'templates')) continue;
      items.push(el('article', { className: 'card template-card' },
        el('div', { className: 'card-header' }, el('strong', {}, saved.title), el('span', { className: 'tag-success' }, `저장된 순서 · ${saved.date || ''}`)),
        el('div', { className: 'action-row' },
          btn('btn btn-primary', () => renderOrderEditor(detailEl, saved), '열기·편집'),
          btn('btn btn-danger', async () => {
            const ok = await showConfirm(modalManager, { message: `"${saved.title}" 예배 순서를 삭제하시겠습니까?`, okLabel: '삭제', cancelLabel: '취소', danger: true });
            if (!ok) return;
            const backup = { ...saved };
            await archive.deleteWorshipOrder(saved.id);
            state.worshipOrders = state.worshipOrders.filter((o) => o.id !== saved.id);
            renderTemplates(filterEl, listEl, detailEl, state.worshipSearch);
            showToast('예배 순서를 삭제했습니다.', {
              undoLabel: '되돌리기', durationMs: 5000,
              onUndo: async () => {
                await archive.saveWorshipOrder(backup);
                state.worshipOrders = [backup, ...state.worshipOrders];
                renderTemplates(filterEl, listEl, detailEl, state.worshipSearch);
                showToast('예배 순서를 복원했습니다.');
              },
            });
          }, iconEl('icon-trash'), '삭제')
        )
      ));
    }

    for (const tpl of service.worship?.templates || []) {
      if (!matchWorshipItem(tpl, parsedQ, 'templates')) continue;
      items.push(el('article', { className: 'card template-card' },
        el('div', { className: 'card-header' }, el('strong', {}, tpl.title), el('span', { className: 'tag-accent' }, `${(tpl.slots || []).length}개 순서`)),
        tpl.description ? el('p', {}, tpl.description) : null,
        el('div', { className: 'action-row' }, btn('btn btn-primary', () => renderOrderEditor(detailEl, { ...tpl, id: generateId('order') }), '이 양식으로 예배 준비'))
      ));
    }

    listEl.replaceChildren(...(items.length ? items : [el('div', { className: 'card empty-state' }, '조건에 맞는 예배 순서 양식이 없습니다.')]));
  }

  return {
    renderLiturgies,
    renderTemplates,
    getActivePulpitDeck: async () => (activeLiturgy ? buildLiturgyDeck(activeLiturgy) : activeOrder ? buildOrderDeck(activeOrder) : null),
    clearActiveDetail: () => { activeLiturgy = null; activeOrder = null; },
  };
}
