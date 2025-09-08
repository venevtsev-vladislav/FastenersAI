const { normalizeText } = require('./normalize');

function parseSizes(input) {
  const text = normalizeText(input);
  let diameter = null;
  let length = null;
  let size = null;

  const diameterMatch = text.match(/m\s*(\d+(?:\.\d+)?)/i);
  if (diameterMatch) {
    diameter = `M${diameterMatch[1]}`;
  }

  const sizeMatch = text.match(/(\d+(?:\.\d+)?)\s*x\s*(\d+)/);
  if (sizeMatch) {
    size = `${sizeMatch[1]}x${sizeMatch[2]}`;
    length = sizeMatch[2];
  }

  return { diameter, length, size };
}

module.exports = { parseSizes };
