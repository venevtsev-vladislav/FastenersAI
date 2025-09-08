function calculateProbability(match) {
  const weights = { type: 25, standard: 40, size: 30, coating: 15 };
  const bonuses = { standard_plus_size: 15, type_plus_size: 10, full_match: 20 };

  let score = 0;
  for (const key of Object.keys(weights)) {
    if (match[key]) score += weights[key];
  }

  if (match.standard && match.size) score += bonuses.standard_plus_size;
  if (match.type && match.size) score += bonuses.type_plus_size;
  if (match.type && match.standard && match.size && match.coating) score += bonuses.full_match;

  // Guards
  if (match.standard && match.size && score < 80) score = 80;
  const matchedFields = Object.keys(match).filter(k => match[k]);
  if (matchedFields.length === 1 && match.type) score = Math.min(score, 40);
  if (matchedFields.length === 1 && match.coating) score = Math.min(score, 20);

  if (score > 100) score = 100;
  if (score < 0) score = 0;

  return Math.round(score);
}

module.exports = { calculateProbability };
