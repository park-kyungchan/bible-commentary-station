/**
 * Declarative Workspace Lens / Plugin Host
 * Manages lifecycle of spatial lenses (Scriptorium, Polyglot Matrix,
 * Constellation Graph, Worship Sanctuary, Homiletics Studio).
 */

export function createPluginHost({ bus }) {
  const plugins = new Map();
  let activeId = null;

  function register(plugin) {
    if (!plugin || !plugin.id) throw new Error('Plugin requires an id');
    plugins.set(plugin.id, {
      id: plugin.id,
      title: plugin.title || plugin.id,
      shortTitle: plugin.shortTitle || plugin.title || plugin.id,
      icon: plugin.icon || 'icon-bible',
      shortcut: plugin.shortcut || '',
      mount: plugin.mount || (() => {}),
      unmount: plugin.unmount || (() => {}),
      render: plugin.render || (() => {}),
    });
  }

  function activate(id, container, payload = {}) {
    if (!plugins.has(id)) return false;
    if (activeId && activeId !== id) {
      const prev = plugins.get(activeId);
      try { prev.unmount(); } catch { /* ignore */ }
    }
    activeId = id;
    const next = plugins.get(id);
    next.mount(container, payload);
    next.render(payload);
    bus?.emit('lens:changed', { lensId: id, plugin: next });
    return true;
  }

  function rerenderActive(payload = {}) {
    if (!activeId || !plugins.has(activeId)) return;
    plugins.get(activeId).render(payload);
  }

  function list() {
    return Array.from(plugins.values());
  }

  function getActiveId() {
    return activeId;
  }

  return { register, activate, rerenderActive, list, getActiveId };
}
