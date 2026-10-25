// Run with: npm test
import assert from "node:assert/strict";
import { test } from "node:test";

import { phoneProblem } from "../src/phone.js";

test("real helpline formats are accepted", () => {
  for (const ok of ["+91 481 2000 123", "+91 98470 12345", "+91-98470-12345", "0481 2000123", "98470 12345", "1800 425 1234",
                    "+44 20 7946 0958", "(0481) 2000123", ""]) {
    assert.equal(phoneProblem(ok), null, ok);
  }
});

test("wrong digit counts, repeated digits and stray characters are refused with a reason", () => {
  assert.match(phoneProblem("+91 00000 1234666660000"), /10 digits after \+91; this one has 18/);
  assert.match(phoneProblem("+91 00000 00000"), /Leave out the 0/);
  assert.match(phoneProblem("1111111111"), /same digit repeated/);
  for (const bad of ["12", "1".repeat(40), "call me!", "+91 98470", "98+470 12345", "+1 23"]) {
    assert.ok(phoneProblem(bad), bad);
  }
});
