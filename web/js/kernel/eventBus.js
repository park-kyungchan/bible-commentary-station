/**
 * Decoupled Pub/Sub Event Bus with Rolling Diagnostic Trace
 * Eliminates cross-feature callback spaghetti across workspace lenses.
 */

export function createEventBus({ traceLimit = 40 } = {}) {
  const listeners = new Map();
  const trace = [];

  function on(eventName, handler) {
    if (!listeners.has(eventName)) listeners.set(eventName, new Set());
    listeners.get(eventName).add(handler);
    return () => off(eventName, handler);
  }

  function once(eventName, handler) {
    const unsub = on(eventName, (payload) => {
      unsub();
      handler(payload);
    });
    return unsub;
  }

  function off(eventName, handler) {
    const set = listeners.get(eventName);
    if (set) {
      set.delete(handler);
      if (set.size === 0) listeners.delete(eventName);
    }
  }

  function emit(eventName, payload = {}) {
    trace.push({ eventName, ts: Date.now() });
    if (trace.length > traceLimit) trace.shift();
    const set = listeners.get(eventName);
    if (!set || set.size === 0) return 0;
    let invoked = 0;
    for (const handler of Array.from(set)) {
      handler(payload);
      invoked += 1;
    }
    return invoked;
  }

  function clear() {
    listeners.clear();
    trace.length = 0;
  }

  function getTrace() {
    return trace.slice();
  }

  return { on, once, off, emit, clear, getTrace };
}
