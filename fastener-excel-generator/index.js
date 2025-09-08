const { normalizeText } = require('./src/normalize');
const { parseSizes } = require('./src/sizeParser');
const { calculateProbability } = require('./src/probability');
const { calcPackQty } = require('./src/packQty');

module.exports = {
  normalizeText,
  parseSizes,
  calculateProbability,
  calcPackQty,
};
