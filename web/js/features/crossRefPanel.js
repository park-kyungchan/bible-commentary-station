import { el, iconEl } from '../core/dom.js';

const REL_LABELS = Object.freeze({
  PARALLEL: '병행 말씀',
  EXPLANATORY: '보충 설명',
  PROPHECY_FULFILLMENT: '예언과 성취',
  THEMATIC: '주제 연결',
});

export function createCrossRefPanel({ service, callbacks }) {
  function renderCrossRef(body, verseObj) {
    const heading = verseObj
      ? `함께 읽으면 좋은 연결 말씀 (${verseObj.bookName} ${verseObj.chapter}:${verseObj.verse})`
      : '함께 읽으면 좋은 연결 말씀';
    body.appendChild(el('h3', {}, heading));

    const refs = verseObj ? service.getCrossReferencesForVerse(verseObj.verseId) : [];
    if (!refs.length) {
      body.appendChild(
        el(
          'div',
          { className: 'card empty-state' },
          el('p', {}, '이 절에 직접 연결된 말씀이 아직 없습니다. 창세기 22:2, 시편 23:1, 요한복음 3:16에서 확인해 보세요.')
        )
      );
    } else {
      for (const r of refs) {
        const refLabel = `${r.to_book_name} ${r.to_chapter}:${r.to_verse}`;
        const relLabel = REL_LABELS[r.relationship_type] || '연결 말씀';
        body.appendChild(
          el(
            'article',
            { className: 'card' },
            el(
              'div',
              { className: 'card-header' },
              el(
                'button',
                {
                  type: 'button',
                  className: 'btn btn-primary',
                  onClick: () => callbacks.onJumpToPassage?.(r.to_osis, r.to_chapter, r.to_verse),
                },
                `${refLabel} 바로 가기`
              ),
              el('span', { className: 'tag-accent' }, relLabel),
              el(
                'button',
                {
                  type: 'button',
                  className: 'btn btn-secondary',
                  onClick: () => callbacks.onClip?.(refLabel, r.to_text || ''),
                },
                iconEl('icon-sermon'),
                '노트에 담기'
              )
            ),
            r.to_text ? el('p', {}, r.to_text) : null,
            r.note ? el('p', { className: 'tag-provenance' }, r.note) : null
          )
        );
      }
    }

    body.appendChild(el('h3', {}, '성경 인물·주제 흐름 한눈에 보기'));
    for (const chain of service.getChains()) {
      const card = el(
        'article',
        { className: 'card chain-card' },
        el('h3', {}, chain.title),
        chain.meaning ? el('p', { className: 'tag-accent' }, chain.meaning) : null,
        chain.summary ? el('p', {}, chain.summary) : null
      );
      for (const link of chain.links || []) {
        card.appendChild(
          el(
            'div',
            { className: 'card' },
            el(
              'div',
              { className: 'card-header' },
              el(
                'button',
                {
                  type: 'button',
                  className: 'btn btn-secondary',
                  onClick: () => callbacks.onJumpToPassage?.(link.osis_code, link.chapter, link.verse),
                },
                link.passage_display
              ),
              el('span', { className: 'tag-accent' }, link.stage_label),
              el(
                'button',
                {
                  type: 'button',
                  className: 'btn btn-ghost',
                  onClick: () => callbacks.onClip?.(link.passage_display, `${link.verse_text || ''}\n${link.sermon_point || ''}`),
                },
                iconEl('icon-plus'),
                '담기'
              )
            ),
            link.verse_text ? el('p', {}, link.verse_text) : null,
            link.sermon_point ? el('p', {}, `핵심: ${link.sermon_point}`) : null
          )
        );
      }
      body.appendChild(card);
    }
  }

  function buildStrongCard(s) {
    const langLabel = s.language === 'GREEK' ? '신약 헬라어' : '구약 히브리어';
    return el(
      'article',
      { className: 'card strong-card' },
      el(
        'div',
        { className: 'card-header' },
        el('span', { className: 'tag-accent' }, s.strong_id),
        el('strong', {}, s.lemma),
        el('span', {}, `발음: ${s.pronunciation}`),
        el('span', { className: 'tag-provenance' }, `${langLabel} · ${s.part_of_speech || ''}`)
      ),
      el('p', {}, s.definition_kr),
      el('p', {}, `성경 전체에 ${s.occurrence_count}번 나오는 핵심 단어입니다.`),
      el(
        'div',
        { className: 'action-row' },
        el(
          'button',
          {
            type: 'button',
            className: 'btn btn-secondary',
            onClick: () => callbacks.onClip?.(`원어 ${s.strong_id} (${s.pronunciation})`, `${s.lemma} — ${s.definition_kr}`),
          },
          iconEl('icon-sermon'),
          '노트에 담기'
        )
      )
    );
  }

  function renderStrongs(body, verseObj) {
    const heading = verseObj
      ? `이 절의 원어 풀이 (${verseObj.bookName} ${verseObj.chapter}:${verseObj.verse})`
      : '원어(히브리어 · 헬라어) 쉽게 풀기';
    body.appendChild(el('h3', {}, heading));

    const entries = verseObj ? service.getCommentariesForVerse(verseObj.verseId) : [];
    const linked = verseObj ? service.getStrongsForVerse(verseObj, entries) : [];

    if (!linked.length) {
      body.appendChild(
        el(
          'div',
          { className: 'card empty-state' },
          el('p', {}, '이 절에 연결된 원어 항목이 없습니다. 아래에서 전체 핵심 원어를 펼쳐 보실 수 있습니다.')
        )
      );
    } else {
      for (const s of linked) {
        body.appendChild(buildStrongCard(s));
      }
    }

    const allStrongs = service.getStrongs();
    if (allStrongs.length) {
      const details = el(
        'details',
        { className: 'card' },
        el('summary', { className: 'btn btn-ghost' }, `전체 핵심 원어 모아보기 (${allStrongs.length}개)`),
        ...allStrongs.map((s) => buildStrongCard(s))
      );
      body.appendChild(details);
    }
  }

  return { renderCrossRef, renderStrongs };
}
