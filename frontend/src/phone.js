// Helpline number check, kept in step with phone_problem() in backend/app/schemas/schemas.py.
// Returns null for a plausible number, otherwise a plain reason to show under the field.
//   +91 ...       exactly 10 digits after the country code, not starting with 0
//   +<other> ...  8 to 15 digits in total (international E.164 maximum)
//   no +          10 digits, 11 starting with 0 (trunk prefix), or toll-free 1800/1860
//   any           digits, spaces, ( ) - and a leading + only; not one digit repeated
export function phoneProblem(raw) {
  const v = (raw || "").trim();
  if (!v) return null; // empty clears the helpline
  if (!/^\+?[0-9 ()-]+$/.test(v)) return "Use digits, spaces, ( ) and - only, with + only at the start.";
  const digits = v.replace(/\D/g, "");
  let national = digits;
  if (v.startsWith("+")) {
    if (digits.startsWith("91")) {
      national = digits.slice(2);
      if (national.length !== 10) return `An Indian number has 10 digits after +91; this one has ${national.length}.`;
      if (national[0] === "0") return "Leave out the 0 after +91 (for example +91 481 2000 123).";
    } else if (digits.length < 8 || digits.length > 15) {
      return `An international number has 8 to 15 digits; this one has ${digits.length}.`;
    }
  } else {
    const tollfree = (digits.startsWith("1800") || digits.startsWith("1860")) && (digits.length === 10 || digits.length === 11);
    if (!(tollfree || (digits.length === 10 && digits[0] !== "0") || (digits.length === 11 && digits[0] === "0"))) {
      return `This number has ${digits.length} digits. Use 10 digits (for example 98470 12345 or 481 2000123), 0 + 10 digits, a 1800 toll-free number, or +91 and 10 digits.`;
    }
  }
  if (new Set(national.replace(/^0+/, "") || "0").size === 1) return "That does not look like a real number (the same digit repeated).";
  return null;
}
