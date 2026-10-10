// Ready-made validators — arithmetic isn't the point of the exercise.

/** Luhn checksum for card numbers (digits only). */
export function luhnValid(digits) {
  let sum = 0, dbl = false;
  for (let i = digits.length - 1; i >= 0; i--) {
    let d = digits.charCodeAt(i) - 48;
    if (dbl) { d *= 2; if (d > 9) d -= 9; }
    sum += d; dbl = !dbl;
  }
  return digits.length > 0 && sum % 10 === 0;
}

/** IBAN mod-97 check (no spaces). */
export function ibanValid(iban) {
  const s = iban.slice(4) + iban.slice(0, 4);
  let r = 0;
  for (const ch of s) {
    const v = /[A-Z]/.test(ch) ? String(ch.charCodeAt(0) - 55) : ch;
    for (const d of v) r = (r * 10 + (d.charCodeAt(0) - 48)) % 97;
  }
  return r === 1;
}
