// Total terms across all subjects: 60
console.log('[particles] particle-terms.js loaded');
const particleTerms = {
  math: ["π", "∑", "√", "∞", "Δ", "θ" , "≈" , "∫" , "≠"],
  python: ["def", "import", "self", "lambda", "yield", "async" , "None" , "try:" , "__init__"],
  javascript: ["=>", "const", "let", "===", "NaN", "async" , "await" , "map()" , "=="],
  html: ["<div>", "<span>", "<img>", "<a>", "<script>", "id=", "<form>", "<input>", "</>"],
  css: ["flex", "grid", "px", "@media", "z-index", "rem", "vh", "em", "!important"],
  chemistry: ["H2O", "NaCl", "CO2", "pH", "mol", "O2", "CH4", "Na+", "Cl-"],
  physics: ["F=ma", "E=mc²", "m/s²", "λ", "Ω", "c", "g", "W=Fd", "Δv"],
  it: ["RAM", "CPU", "SSD", "IP", "0x1F", "LAN", "WAN", "HTTP", "DNS"],
  geography: ["km²", "equator", "delta", "atlas", "biome", "lat", "lon", "hemisphere", "elevation"],
  astronomy: ["orbit", "ly", "AU", "nova", "galaxy", "eclipse", "rad", "spectra", "nebula"],
  engineering: ["CAD", "torque", "psi", "gear", "volt", "amp", "stress", "strain", "Δt"]
};

// Global `particleTerms` available to particle-system.js
