function normalizeText(input) {
  if (typeof input !== 'string') return '';
  let text = input.toLowerCase();
  // Replace different x variants with 'x'
  text = text.replace(/[×х]/g, 'x');
  // Replace comma with dot
  text = text.replace(/,/g, '.');
  // Replace Cyrillic M with Latin M
  text = text.replace(/[м]/g, 'm');
  // din\s*(number) -> din$1
  text = text.replace(/din\s*(\d+)/g, 'din$1');
  // Replace 'оцинк' variants with 'цинк'
  text = text.replace(/оцинк\w*/g, 'цинк');
  // Collapse spaces
  text = text.replace(/\s+/g, ' ');
  // Trim
  text = text.trim();
  // Uppercase M prefixes for diameter tokens
  text = text.replace(/m(?=\d)/g, 'M');
  return text;
}

module.exports = { normalizeText };
