/**
 * Zero-Cost Dual-Screen Pulpit Broadcast Sync
 * Uses browser BroadcastChannel API to synchronize a detached congregation/pulpit
 * display window (?view=stage) with the main workstation in real time.
 */

const CHANNEL_NAME = 'bible-station-pulpit-v4';

export function createBroadcastSync({ onMessage } = {}) {
  let channel = null;

  if (typeof BroadcastChannel !== 'undefined') {
    try {
      channel = new BroadcastChannel(CHANNEL_NAME);
      if (typeof onMessage === 'function') {
        channel.onmessage = (evt) => {
          if (evt?.data && typeof evt.data === 'object') {
            onMessage(evt.data);
          }
        };
      }
    } catch {
      channel = null;
    }
  }

  function send(type, payload = {}) {
    if (!channel) return false;
    try {
      channel.postMessage({ type, payload, ts: Date.now() });
      return true;
    } catch {
      return false;
    }
  }

  function openStageWindow() {
    if (typeof window === 'undefined' || typeof window.open !== 'function') return null;
    const url = new URL(window.location.href);
    url.searchParams.set('view', 'stage');
    return window.open(url.toString(), 'bibleStationStage', 'width=1280,height=720,menubar=no,toolbar=no');
  }

  function close() {
    if (channel) {
      try { channel.close(); } catch { /* ignore */ }
      channel = null;
    }
  }

  return {
    supported: Boolean(channel),
    send,
    openStageWindow,
    close,
  };
}
