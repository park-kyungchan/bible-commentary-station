/**
 * Fine-Grained Reactive Signals Kernel (Zero-Dependency)
 * Inspired by TC39 Signals / SolidJS — replaces imperative callback chains
 * with deterministic, glitch-free reactive subscriptions.
 */

let currentObserver = null;
let batchDepth = 0;
const pendingEffects = new Set();

function flushPending() {
  if (batchDepth > 0) return;
  const toRun = Array.from(pendingEffects);
  pendingEffects.clear();
  for (const eff of toRun) {
    if (!eff.disposed) eff.run();
  }
}

export function batch(fn) {
  batchDepth += 1;
  try {
    return fn();
  } finally {
    batchDepth -= 1;
    if (batchDepth === 0) flushPending();
  }
}

export function signal(initialValue, { equals = Object.is } = {}) {
  let value = initialValue;
  const subscribers = new Set();

  function read() {
    if (currentObserver) {
      subscribers.add(currentObserver);
      currentObserver.deps.add(subscribers);
    }
    return value;
  }

  read.peek = () => value;

  read.set = (nextOrUpdater) => {
    const next = typeof nextOrUpdater === 'function' ? nextOrUpdater(value) : nextOrUpdater;
    if (equals(value, next)) return value;
    value = next;
    for (const sub of Array.from(subscribers)) {
      pendingEffects.add(sub);
    }
    flushPending();
    return value;
  };

  read.subscribe = (listener) => {
    const eff = effect(() => listener(read()));
    return eff;
  };

  return read;
}

export function effect(fn) {
  const runner = {
    deps: new Set(),
    disposed: false,
    cleanup: null,
    run() {
      if (runner.disposed) return;
      for (const dep of runner.deps) dep.delete(runner);
      runner.deps.clear();
      if (typeof runner.cleanup === 'function') {
        try { runner.cleanup(); } catch { /* ignore cleanup error */ }
        runner.cleanup = null;
      }
      const prev = currentObserver;
      currentObserver = runner;
      try {
        const ret = fn();
        if (typeof ret === 'function') runner.cleanup = ret;
      } finally {
        currentObserver = prev;
      }
    },
  };

  runner.run();

  return function dispose() {
    runner.disposed = true;
    for (const dep of runner.deps) dep.delete(runner);
    runner.deps.clear();
    if (typeof runner.cleanup === 'function') {
      try { runner.cleanup(); } catch { /* ignore */ }
      runner.cleanup = null;
    }
  };
}

export function computed(fn) {
  const out = signal(undefined);
  const dispose = effect(() => {
    out.set(fn());
  });
  out.dispose = dispose;
  return out;
}

export function createHistory(maxSize = 50) {
  const past = [];
  const future = [];

  return {
    push(entry) {
      past.push(entry);
      if (past.length > maxSize) past.shift();
      future.length = 0;
    },
    undo(current) {
      if (!past.length) return null;
      const prev = past.pop();
      if (current !== undefined) future.push(current);
      return prev;
    },
    redo(current) {
      if (!future.length) return null;
      const next = future.pop();
      if (current !== undefined) past.push(current);
      return next;
    },
    canUndo: () => past.length > 0,
    canRedo: () => future.length > 0,
    clear() {
      past.length = 0;
      future.length = 0;
    },
  };
}
