import test from 'node:test';
import assert from 'node:assert/strict';
import { createRequestGuard } from '../../web/js/core/state.js';

function delay(ms, value) {
  return new Promise((resolve) => setTimeout(() => resolve(value), ms));
}

test('createRequestGuard aborts superseded request A and commits only newer request B', async () => {
  const guard = createRequestGuard('chapter');
  let committed = null;
  let commitCount = 0;

  const runRequest = async (label, ms) => {
    const req = guard.next();
    const res = await delay(ms, label);
    if (!req.isCurrent()) return { committed: false, aborted: req.signal.aborted };
    committed = res;
    commitCount += 1;
    return { committed: true, aborted: req.signal.aborted };
  };

  const pA = runRequest('GEN:1', 180);
  const pB = runRequest('PSA:23', 15);
  const [resA, resB] = await Promise.all([pA, pB]);

  assert.equal(resB.committed, true);
  assert.equal(resB.aborted, false);
  assert.equal(resA.committed, false);
  assert.equal(resA.aborted, true);
  assert.equal(committed, 'PSA:23');
  assert.equal(commitCount, 1);
});
