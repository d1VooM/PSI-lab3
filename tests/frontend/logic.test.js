const test = require("node:test");
const assert = require("node:assert");
const L = require("../../app/static/js/logic.js");

test("validateAmount: валидные значения", () => {
  assert.deepStrictEqual(L.validateAmount("100"), { ok: true, value: "100" });
  assert.strictEqual(L.validateAmount("12,5").value, "12.5");
  assert.strictEqual(L.validateAmount(" 1 000 ").value, "1000");
});

test("validateAmount: пустое, буквы, ноль, минус", () => {
  for (const bad of ["", "   ", null, undefined, "abc", "12a", "1e5", "-5", "0", "0.0"])
    assert.strictEqual(L.validateAmount(bad).ok, false, `должно отклонять: ${bad}`);
  assert.match(L.validateAmount("-3").error, /отрицательной/);
  assert.match(L.validateAmount("0").error, /больше нуля/);
  assert.match(L.validateAmount("x").error, /числом/);
});

test("validateDate: формат и календарь", () => {
  assert.strictEqual(L.validateDate("2026-10-27").ok, true);
  assert.strictEqual(L.validateDate("2024-02-29").ok, true);
  for (const bad of ["", "27.10.2026", "2026-1-5", "2026-02-31", "2025-02-29", "2026-13-01", "1800-01-01"])
    assert.strictEqual(L.validateDate(bad).ok, false, `должно отклонять: ${bad}`);
  assert.match(L.validateDate("2026-02-31").error, /не существует/);
});

test("canConvert: кнопка неактивна, пока поля не заполнены", () => {
  assert.strictEqual(L.canConvert({ amount: "", from: "EUR", to: "USD" }), false);
  assert.strictEqual(L.canConvert({ amount: "5", from: "", to: "USD" }), false);
  assert.strictEqual(L.canConvert({ amount: "5", from: "EUR", to: "USD" }), true);
});

test("distancePercent: Луна на шкале, границы", () => {
  assert.ok(L.distancePercent(0.001) >= 2);
  assert.ok(L.distancePercent(1e6) <= 98);
  assert.ok(L.distancePercent(3) > L.distancePercent(1));
  assert.strictEqual(L.distancePercent(null), 0);
  assert.ok(Math.abs(L.MOON_PERCENT - 33.33) < 0.1);
});

test("escapeHtml защищает от XSS в именах астероидов", () => {
  assert.strictEqual(L.escapeHtml('<img src=x onerror="a">'), "&lt;img src=x onerror=&quot;a&quot;&gt;");
});
