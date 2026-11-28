/**
 * Lens 3: Scripture Constellation Graph (성경 지식 성좌도)
 * Interactive SVG spatial knowledge graph rendering cross-references and
 * biblical character/thematic chains from deterministic `web/data/graph.json`.
 */

import { btn, el, iconEl } from '../core/dom.js';

const SVG_NS = 'http://www.w3.org/2000/svg';

const REL_META = Object.freeze({
  PARALLEL: { label: '병행 말씀', color: '#38BDF8' },
  PROPHECY_FULFILLMENT: { label: '예언과 성취', color: '#F59E0B' },
  EXPLANATORY: { label: '보충 설명', color: '#A78BFA' },
  THEMATIC: { label: '주제 연결', color: '#34D399' },
  CHAIN_MEMBER: { label: '인물·주제 축', color: '#10B981' },
  CHAIN_STEP: { label: '구속사 흐름', color: '#FB7185' },
});

function svgEl(tag, attrs = {}, textContent = null) {
  const node = document.createElementNS(SVG_NS, tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v !== undefined && v !== null) node.setAttribute(k, String(v));
  }
  if (textContent !== null) node.textContent = textContent;
  return node;
}

export function createConstellationGraph({ store, service, bus }) {
  const { state } = store;
  let zoomLevel = 1;

  function getFilteredGraph(graph) {
    const filter = state.graphFilter || 'ALL';
    if (filter === 'ALL') return { nodes: graph.nodes, edges: graph.edges };

    const matchingIds = new Set(
      graph.nodes
        .filter((n) => (filter === 'CHAIN' ? n.kind === 'chain' : n.cluster === filter))
        .map((n) => n.id)
    );
    // Include 1-hop neighbors so constellations stay meaningful
    const expanded = new Set(matchingIds);
    for (const e of graph.edges) {
      if (matchingIds.has(e.source)) expanded.add(e.target);
      if (matchingIds.has(e.target)) expanded.add(e.source);
    }
    return {
      nodes: graph.nodes.filter((n) => expanded.has(n.id)),
      edges: graph.edges.filter((e) => expanded.has(e.source) && expanded.has(e.target)),
    };
  }

  function renderInspector(inspectorEl, graph, node) {
    if (!node) {
      inspectorEl.replaceChildren(
        el(
          'div',
          { className: 'graph-inspector-empty' },
          el('h3', {}, '성좌 노드를 선택해 보세요'),
          el('p', {}, '좌측 성경 지식 성좌도에서 구절 또는 인물·주제 노드를 클릭하면 연결된 관주와 구속사 흐름을 한눈에 볼 수 있습니다.'),
          el('div', { className: 'graph-hub-list' },
            el('strong', {}, '핵심 허브 말씀 TOP 6'),
            ...(graph.topHubs || []).slice(0, 6).map((hub) =>
              el(
                'button',
                {
                  type: 'button',
                  className: 'graph-hub-chip',
                  onClick: () => {
                    state.graphSelectedNodeId = hub.id;
                    render();
                  },
                },
                el('span', {}, hub.label),
                el('span', { className: 'tag-accent' }, `연결 ${hub.degree}`)
              )
            )
          )
        )
      );
      return;
    }

    const nodeById = new Map(graph.nodes.map((n) => [n.id, n]));
    const relatedEdges = graph.edges.filter((e) => e.source === node.id || e.target === node.id);

    const actions = [];
    if (node.kind === 'verse') {
      actions.push(
        btn(
          'btn btn-primary',
          () => bus.emit('passage:jump', { osis: node.osis, chapter: node.chapter, verse: node.verse, mode: 'bible' }),
          iconEl('icon-bible'),
          '성경 서재로 워프'
        ),
        btn(
          'btn btn-secondary',
          () => bus.emit('passage:jump', { osis: node.osis, chapter: node.chapter, verse: node.verse, mode: 'matrix' }),
          '다중 역본 비교'
        )
      );
      if (node.excerpt) {
        actions.push(
          btn(
            'btn btn-ghost',
            () => bus.emit('clip:add', { source: `${node.fullLabel} (성좌도)`, text: node.excerpt }),
            iconEl('icon-sermon'),
            '노트에 담기'
          )
        );
      }
    }

    const neighborCards = relatedEdges.slice(0, 14).map((edge) => {
      const otherId = edge.source === node.id ? edge.target : edge.source;
      const other = nodeById.get(otherId);
      if (!other) return null;
      const relInfo = REL_META[edge.relation] || { label: edge.relation, color: '#94A3B8' };
      return el(
        'button',
        {
          type: 'button',
          className: 'graph-neighbor-btn',
          onClick: () => {
            state.graphSelectedNodeId = other.id;
            render();
          },
        },
        el(
          'div',
          { className: 'graph-neighbor-top' },
          el('strong', {}, other.fullLabel || other.label),
          el('span', { className: 'graph-rel-pill', dataset: { rel: edge.relation } }, relInfo.label)
        ),
        edge.note ? el('p', { className: 'graph-neighbor-note' }, edge.note) : null
      );
    }).filter(Boolean);

    inspectorEl.replaceChildren(
      el(
        'div',
        { className: 'graph-inspector-card' },
        el(
          'div',
          { className: 'graph-inspector-head' },
          el('span', { className: 'eyebrow-badge' }, node.kind === 'chain' ? '인물·주제 축' : `${node.testament === 'OT' ? '구약' : '신약'} · ${node.category || '성경'}`),
          el('h3', {}, node.fullLabel || node.label),
          node.meaning ? el('p', { className: 'tag-accent' }, node.meaning) : null
        ),
        node.excerpt ? el('blockquote', { className: 'graph-excerpt' }, node.excerpt) : null,
        el(
          'div',
          { className: 'graph-stat-row' },
          el('span', { className: 'tag-provenance' }, `연결선 ${node.degree || 0}개`),
          node.kind === 'verse' ? el('span', { className: 'tag-provenance' }, `주석 ${node.commentaryCount || 0}건`) : null,
          node.stage ? el('span', { className: 'tag-accent' }, node.stage) : null
        ),
        actions.length ? el('div', { className: 'action-row' }, ...actions) : null,
        el('h4', { className: 'graph-subhead' }, `연결된 성좌 (${relatedEdges.length}건)`),
        el('div', { className: 'graph-neighbor-list' }, ...neighborCards)
      )
    );
  }

  function render() {
    const root = document.getElementById('graphContainer');
    if (!root) return;
    const graph = service.getGraph();
    if (!graph || !Array.isArray(graph.nodes) || !graph.nodes.length) {
      root.replaceChildren(el('div', { className: 'card empty-state' }, '성경 지식 성좌도 데이터를 불러올 수 없습니다.'));
      return;
    }

    const { nodes, edges } = getFilteredGraph(graph);
    const nodeById = new Map(nodes.map((n) => [n.id, n]));
    const selectedId = state.graphSelectedNodeId && nodeById.has(state.graphSelectedNodeId)
      ? state.graphSelectedNodeId
      : (graph.topHubs?.[0]?.id || nodes[0]?.id);
    const selectedNode = nodeById.get(selectedId) || null;

    const neighborIds = new Set([selectedId]);
    for (const e of edges) {
      if (e.source === selectedId) neighborIds.add(e.target);
      if (e.target === selectedId) neighborIds.add(e.source);
    }

    const filters = [
      { id: 'ALL', label: `전체 성좌 (${graph.stats.nodeCount})` },
      { id: 'CHAIN', label: `인물·주제 축 (${graph.stats.chainNodeCount})` },
      { id: 'OT', label: '구약 중심' },
      { id: 'NT', label: '신약 중심' },
    ];

    const header = el(
      'header',
      { className: 'lens-hero graph-hero' },
      el(
        'div',
        { className: 'lens-hero-top' },
        el(
          'div',
          {},
          el('span', { className: 'eyebrow-badge' }, 'SCRIPTURE CONSTELLATION GRAPH'),
          el('h2', { className: 'lens-title' }, '성경 지식 성좌도 · 관주와 구속사의 공간 지도')
        ),
        el(
          'div',
          { className: 'action-row' },
          ...filters.map((f) =>
            el(
              'button',
              {
                type: 'button',
                className: `chip-btn ${(state.graphFilter || 'ALL') === f.id ? 'is-active' : ''}`,
                onClick: () => {
                  state.graphFilter = f.id;
                  render();
                },
              },
              f.label
            )
          ),
          btn('btn btn-ghost', () => { zoomLevel = Math.min(1.8, +(zoomLevel + 0.2).toFixed(2)); render(); }, '확대 +'),
          btn('btn btn-ghost', () => { zoomLevel = Math.max(0.75, +(zoomLevel - 0.2).toFixed(2)); render(); }, '축소 -'),
          btn('btn btn-ghost', () => { zoomLevel = 1; render(); }, '원래대로')
        )
      )
    );

    const vw = 1000 / zoomLevel;
    const vh = 700 / zoomLevel;
    const vx = (1000 - vw) / 2;
    const vy = (700 - vh) / 2;

    const svg = svgEl('svg', {
      class: 'constellation-svg',
      viewBox: `${vx} ${vy} ${vw} ${vh}`,
      role: 'img',
      'aria-label': '성경 상호 관주 및 구속사 지식 그래프',
    });

    // Subtle orbital guide rings
    svg.appendChild(svgEl('circle', { cx: 500, cy: 350, r: 128, class: 'orbit-ring' }));
    svg.appendChild(svgEl('ellipse', { cx: 500, cy: 350, rx: 380, ry: 270, class: 'orbit-ring orbit-ring-outer' }));

    // Edges layer
    const edgeGroup = svgEl('g', { class: 'graph-edges' });
    for (const e of edges) {
      const s = nodeById.get(e.source);
      const t = nodeById.get(e.target);
      if (!s || !t) continue;
      const isHot = e.source === selectedId || e.target === selectedId;
      const mx = (s.x + t.x) / 2;
      const my = (s.y + t.y) / 2 - (isHot ? 18 : 8);
      const relColor = REL_META[e.relation]?.color || '#64748B';
      edgeGroup.appendChild(
        svgEl('path', {
          d: `M ${s.x} ${s.y} Q ${mx} ${my} ${t.x} ${t.y}`,
          class: `graph-edge ${isHot ? 'is-hot' : 'is-dim'}`,
          stroke: relColor,
        })
      );
    }
    svg.appendChild(edgeGroup);

    // Nodes layer
    const nodeGroup = svgEl('g', { class: 'graph-nodes' });
    for (const n of nodes) {
      const isSelected = n.id === selectedId;
      const isNeighbor = neighborIds.has(n.id);
      const r = n.kind === 'chain' ? 14 : Math.max(6, Math.min(13, 6 + (n.degree || 1) * 0.9));
      const g = svgEl('g', {
        class: `graph-node kind-${n.kind} cluster-${n.cluster} ${isSelected ? 'is-selected' : ''} ${isNeighbor ? 'is-linked' : 'is-dim'}`,
        transform: `translate(${n.x}, ${n.y})`,
        tabindex: '0',
        role: 'button',
        'aria-label': n.fullLabel || n.label,
      });
      if (isSelected) {
        g.appendChild(svgEl('circle', { r: r + 8, class: 'graph-node-halo' }));
      }
      g.appendChild(svgEl('circle', { r, class: 'graph-node-dot' }));
      if (n.kind === 'chain' || isSelected || isNeighbor || (n.degree || 0) >= 4) {
        g.appendChild(
          svgEl('text', { y: r + 14, 'text-anchor': 'middle', class: 'graph-node-label' }, n.label)
        );
      }
      const activate = () => {
        state.graphSelectedNodeId = n.id;
        render();
      };
      g.addEventListener('click', activate);
      g.addEventListener('keydown', (ev) => {
        if (ev.key === 'Enter' || ev.key === ' ') {
          ev.preventDefault();
          activate();
        }
      });
      nodeGroup.appendChild(g);
    }
    svg.appendChild(nodeGroup);

    const canvasCard = el(
      'div',
      { className: 'graph-canvas-card' },
      svg,
      el(
        'div',
        { className: 'graph-legend' },
        el('span', { className: 'legend-dot legend-chain' }, '인물·주제 축'),
        el('span', { className: 'legend-dot legend-ot' }, '구약 성경'),
        el('span', { className: 'legend-dot legend-nt' }, '신약 성경')
      )
    );

    const inspector = el('aside', { className: 'graph-inspector', 'aria-label': '선택한 성좌 상세' });
    renderInspector(inspector, graph, selectedNode);

    root.replaceChildren(header, el('div', { className: 'graph-workspace' }, canvasCard, inspector));
  }

  return { render };
}
