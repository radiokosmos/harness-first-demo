// PII masker — one core for the pi extension and for bin/pii-score.
//
// Masking is pseudonymous and session-stable: the same value always maps to
// the same token (<EMAIL_1>, <CARD_2>, …), so counting and grouping over masked
// output still work — and a token can be turned back into the value just
// before a query runs (detokenize).

import { luhnValid, ibanValid } from "./validators.mjs";

const INTERNAL_DOMAINS = ["corp.example"]; // staff addresses: masking them breaks reviews

// Each detector: a regex, plus a check on the match. Order matters — earlier
// detectors run first, so put the more specific ones first.
const DETECTORS = [
  {
    type: "EMAIL",
    re: /[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}/g,
    keep: (m) => {
      const domain = m.slice(m.lastIndexOf("@") + 1).toLowerCase();
      return !INTERNAL_DOMAINS.some((d) => domain === d || domain.endsWith(`.${d}`));
    },
    norm: (m) => m.toLowerCase(),
  },
  {
    type: "IBAN",
    re: /\b[A-Z]{2}\d{2}[A-Z0-9]{11,30}\b/g,
    keep: (m) => ibanValid(m), // mod-97
  },
  {
    type: "CARD",
    // 15–19 digits: epoch millis are 13 and pass Luhn one time in ten
    re: /\b(?:\d[ -]?){14,18}\d\b/g,
    keep: (m) => luhnValid(m.replace(/[ -]/g, "")), // order numbers fail Luhn
    norm: (m) => m.replace(/[ -]/g, ""),
  },
  {
    type: "PHONE",
    // international format only: a bare local number looks like any other number
    re: /\+\d[\d\s\-().]{7,}\d/g,
    keep: (m) => m.replace(/\D/g, "").length >= 9,
    norm: (m) => m.replace(/\D/g, ""),
  },
];

export class PiiMasker {
  constructor() {
    this.byValue = new Map(); // "TYPE:value" -> token
    this.byToken = new Map(); // token -> original value
    this.counters = {};
  }

  token(type, value, norm) {
    const key = `${type}:${norm}`;
    let t = this.byValue.get(key);
    if (!t) {
      this.counters[type] = (this.counters[type] ?? 0) + 1;
      t = `<${type}_${this.counters[type]}>`;
      this.byValue.set(key, t);
      this.byToken.set(t, value);
    }
    return t;
  }

  /** Mask PII in text. Returns { text, stats } where stats counts hits by type. */
  mask(text) {
    const stats = {};
    let out = text;
    for (const d of DETECTORS) {
      out = out.replace(d.re, (m) => {
        if (d.keep && !d.keep(m)) return m;
        stats[d.type] = (stats[d.type] ?? 0) + 1;
        return this.token(d.type, m, d.norm ? d.norm(m) : m);
      });
    }
    return { text: out, stats };
  }

  /** Replace tokens with the original values (for queries, never for the model). */
  detokenize(text) {
    return text.replace(/<[A-Z]+_\d+>/g, (t) => this.byToken.get(t) ?? t);
  }
}

export { luhnValid, ibanValid };
export const TYPES = ["EMAIL", "PHONE", "IBAN", "CARD", "PERSON"];
