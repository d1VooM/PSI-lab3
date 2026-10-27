// Чистая логика без DOM: подключается в браузере и тестируется в Node.
(function (root, factory) {
  if (typeof module === "object" && module.exports) module.exports = factory();
  else root.OrbitLogic = factory();
})(this, function () {
  function validateAmount(raw) {
    const s = String(raw == null ? "" : raw).trim().replace(/\s/g, "").replace(",", ".");
    if (!s) return { ok: false, error: "Введите сумму" };
    if (!/^[+-]?\d+(\.\d+)?$/.test(s)) return { ok: false, error: "Сумма должна быть числом" };
    const n = Number(s);
    if (n < 0) return { ok: false, error: "Сумма не может быть отрицательной" };
    if (n === 0) return { ok: false, error: "Сумма должна быть больше нуля" };
    if (n > 1e12) return { ok: false, error: "Сумма слишком большая" };
    return { ok: true, value: s };
  }

  function validateDate(raw) {
    const s = String(raw == null ? "" : raw).trim();
    if (!s) return { ok: false, error: "Введите дату в формате ГГГГ-ММ-ДД" };
    if (!/^\d{4}-\d{2}-\d{2}$/.test(s))
      return { ok: false, error: "Неверный формат даты. Нужно ГГГГ-ММ-ДД, например 2026-10-27" };
    const [y, m, d] = s.split("-").map(Number);
    const dt = new Date(Date.UTC(y, m - 1, d));
    if (dt.getUTCFullYear() !== y || dt.getUTCMonth() !== m - 1 || dt.getUTCDate() !== d)
      return { ok: false, error: "Такой даты не существует в календаре" };
    if (y < 1900 || y > 2100) return { ok: false, error: "Год должен быть между 1900 и 2100" };
    return { ok: true, value: s };
  }

  function canConvert(s) {
    return String(s.amount == null ? "" : s.amount).trim() !== "" && !!s.from && !!s.to;
  }

  // Позиция астероида на шкале 0..100% (логарифмическая, 1 LD = Луна).
  function distancePercent(lunar) {
    if (!(lunar > 0)) return 0;
    const p = ((Math.log10(lunar) + 1) / 3) * 100;
    return Math.min(98, Math.max(2, p));
  }
  const MOON_PERCENT = distancePercent(1);

  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  }

  return { validateAmount, validateDate, canConvert, distancePercent, MOON_PERCENT, escapeHtml };
});
