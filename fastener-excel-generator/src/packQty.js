function calcPackQty(unit, packSize) {
  if (typeof packSize !== 'number') return null;
  if (unit === 'шт') return packSize;
  if (unit === 'тыс.шт') return packSize * 1000;
  return null;
}

module.exports = { calcPackQty };
