const test = require('node:test');
const assert = require('node:assert');
const { normalizeText } = require('../src/normalize');

test('normalize x variants and decimal comma', () => {
  const result = normalizeText('M8 10х100,5 × 2');
  assert.strictEqual(result, 'M8 10x100.5 x 2');
});
