const test = require('node:test');
const assert = require('node:assert');
const { parseSizes } = require('../src/sizeParser');

test('parse sizes for "М8 10х100"', () => {
  const res = parseSizes('М8 10х100');
  assert.deepStrictEqual(res, { diameter: 'M8', length: '100', size: '10x100' });
});

test('parse sizes for decimal diameter "4,2x90"', () => {
  const res = parseSizes('4,2x90');
  assert.deepStrictEqual(res, { diameter: null, length: '90', size: '4.2x90' });
});

test('parse sizes for "M12x130"', () => {
  const res = parseSizes('M12x130');
  assert.deepStrictEqual(res, { diameter: 'M12', length: '130', size: '12x130' });
});
