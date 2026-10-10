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
  // TODO: act 3, exercise 3a — IBAN, CARD, PHONE.
  // Decoys in the data: order numbers and epoch millis (13–19 digits),
  // local numbers without a country code, dates, amounts. See corpus/public.jsonl.
  // Validators: luhnValid(digits), ibanValid(iban) from ./validators.mjs.
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
