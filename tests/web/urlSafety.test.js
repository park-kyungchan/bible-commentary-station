import test from 'node:test';
import assert from 'node:assert/strict';
import {
  buildBibleHubCommentaryUrl,
  buildDrivePreviewUrl,
  DRIVE_IFRAME_REFERRER,
  DRIVE_IFRAME_SANDBOX,
  sanitizeDrivePreviewUrl,
  sanitizeUrl,
} from '../../web/js/core/urlSafety.js';
import { el } from '../../web/js/core/dom.js';

function withMockDocument(fn) {
  const prevDoc = globalThis.document;
  globalThis.document = {
    createElement(tag) {
      const attrs = new Map();
      const listeners = [];
      return {
        tagName: tag.toUpperCase(),
        className: '',
        dataset: {},
        children: [],
        setAttribute(k, v) { attrs.set(k, String(v)); },
        getAttribute(k) { return attrs.has(k) ? attrs.get(k) : null; },
        addEventListener(type, cb) { listeners.push({ type, cb }); },
        appendChild(child) { this.children.push(child); return child; },
        _attrs: attrs,
        _listeners: listeners,
      };
    },
    createTextNode(text) { return { nodeType: 3, textContent: text }; },
  };
  try {
    return fn();
  } finally {
    globalThis.document = prevDoc;
  }
}

test('sanitizeUrl allows only https URLs and rejects javascript/data/http schemes', () => {
  assert.equal(sanitizeUrl('javascript:alert(1)'), null);
  assert.equal(sanitizeUrl('JAVASCRIPT:void(0)'), null);
  assert.equal(sanitizeUrl('data:text/html,<script>alert(1)</script>'), null);
  assert.equal(sanitizeUrl('http://example.com/insecure'), null);
  assert.equal(sanitizeUrl('not a url'), null);
  assert.equal(sanitizeUrl('https://www.ccel.org/ccel/henry/mhc'), 'https://www.ccel.org/ccel/henry/mhc');
});

test('Drive preview sanitizer enforces exact Drive preview URL allowlist', () => {
  const valid = 'https://drive.google.com/file/d/1BmEbgdVdzGkdgwfdyhspikmWVc9kvTvg/preview';
  assert.equal(sanitizeDrivePreviewUrl(valid), valid);
  assert.equal(sanitizeDrivePreviewUrl('https://evil.example/file/d/1BmEbgdVdzGkdgwfdyhspikmWVc9kvTvg/preview'), null);
  assert.equal(sanitizeDrivePreviewUrl('https://drive.google.com/file/d/short/preview'), null);
  assert.equal(sanitizeDrivePreviewUrl('https://drive.google.com/file/d/1BmEbgdVdzGkdgwfdyhspikmWVc9kvTvg/edit'), null);
  assert.equal(buildDrivePreviewUrl('../etc/passwd'), null);
  assert.equal(buildDrivePreviewUrl('1BmEbgdVdzGkdgwfdyhspikmWVc9kvTvg'), valid);
});

test('BibleHub slug map correctly maps SNG to songs and other multi-word books', () => {
  assert.equal(buildBibleHubCommentaryUrl('SNG', 2, 1), 'https://biblehub.com/commentaries/songs/2-1.htm');
  assert.equal(buildBibleHubCommentaryUrl('1SA', 16, 7), 'https://biblehub.com/commentaries/1_samuel/16-7.htm');
  assert.equal(buildBibleHubCommentaryUrl('PSA', 23, 1), 'https://biblehub.com/commentaries/psalms/23-1.htm');
});

test('el() strips javascript: href, string onclick, inline style, and enforces rel/sandbox', () => {
  withMockDocument(() => {
    const badLink = el('a', {
      href: 'javascript:alert(1)',
      onclick: 'alert(1)',
      style: 'color:red',
      target: '_blank',
    }, 'click');
    assert.equal(badLink.getAttribute('href'), null);
    assert.equal(badLink.getAttribute('onclick'), null);
    assert.equal(badLink.getAttribute('style'), null);
    assert.equal(badLink._listeners.length, 0);
    assert.equal(badLink.getAttribute('rel'), 'noopener noreferrer');

    const badFrame = el('iframe', { src: 'https://evil.example/embed' });
    assert.equal(badFrame.getAttribute('src'), null);
    assert.equal(badFrame.getAttribute('sandbox'), DRIVE_IFRAME_SANDBOX);
    assert.equal(badFrame.getAttribute('referrerpolicy'), DRIVE_IFRAME_REFERRER);

    const goodFrame = el('iframe', {
      src: 'https://drive.google.com/file/d/1BmEbgdVdzGkdgwfdyhspikmWVc9kvTvg/preview',
    });
    assert.equal(
      goodFrame.getAttribute('src'),
      'https://drive.google.com/file/d/1BmEbgdVdzGkdgwfdyhspikmWVc9kvTvg/preview'
    );
    assert.equal(goodFrame.getAttribute('sandbox'), DRIVE_IFRAME_SANDBOX);
    assert.equal(goodFrame.getAttribute('referrerpolicy'), DRIVE_IFRAME_REFERRER);
  });
});
