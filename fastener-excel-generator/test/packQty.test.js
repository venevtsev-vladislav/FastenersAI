const test = require('node:test');
const assert = require('node:assert');
const { calcPackQty } = require('../src/packQty');

test('pack quantity for unit шт', () => {
  assert.strictEqual(calcPackQty('шт', 50), 50);
});

test('pack quantity for unit тыс.шт', () => {
  assert.strictEqual(calcPackQty('тыс.шт', 2), 2000);
});

test('pack quantity for unknown unit', () => {
  assert.strictEqual(calcPackQty('упак', 30), null);
});
