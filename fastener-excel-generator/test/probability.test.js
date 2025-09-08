const test = require('node:test');
const assert = require('node:assert');
const { calculateProbability } = require('../src/probability');

test('standard and size match ensure at least 80%', () => {
  const p = calculateProbability({ type: false, standard: true, size: true, coating: false });
  assert.ok(p >= 80);
});

test('only type match max 40%', () => {
  const p = calculateProbability({ type: true, standard: false, size: false, coating: false });
  assert.ok(p <= 40);
});

test('only coating match max 20%', () => {
  const p = calculateProbability({ type: false, standard: false, size: false, coating: true });
  assert.ok(p <= 20);
});

test('full match clamps to 100%', () => {
  const p = calculateProbability({ type: true, standard: true, size: true, coating: true });
  assert.strictEqual(p, 100);
});
