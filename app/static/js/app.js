(() => {
  "use strict";
  const L = window.OrbitLogic;
  const $ = (s) => document.querySelector(s);
  const nf = new Intl.NumberFormat("ru-RU", { maximumFractionDigits: 4 });
  const nf1 = new Intl.NumberFormat("ru-RU", { maximumFractionDigits: 1 });
  const ruDate = (iso) => (iso ? iso.split("-").reverse().join(".") : "—");

  async function api(url, options) {
    let res;
    try { res = await fetch(url, options); }
    catch { throw new Error("Нет связи с сервером приложения. Проверьте, что оно запущено."); }
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.error || "Что-то пошло не так, попробуйте ещё раз");
    return data;
  }
  function alertBox(el, kind, text) {
    el.className = `alert alert-${kind} mb-0`;
    el.textContent = text;
    el.hidden = false;
  }
  const hide = (el) => { el.hidden = true; };
  function setBusy(btn, busy, label) {
    btn.dataset.label = btn.dataset.label || btn.textContent;
    btn.textContent = busy ? label : btn.dataset.label;
    btn.dataset.busy = busy ? "1" : "";
  }

  /* ---------- Конвертер ---------- */
  const c = {
    form: $("#convertForm"), amount: $("#amount"), from: $("#from"), to: $("#to"),
    btn: $("#convertBtn"), err: $("#amountError"), alert: $("#curAlert"),
    swap: $("#swapBtn"), retry: $("#retryRates"), out: $("#result"),
  };
  let ratesReady = false;

  function refreshButton() {
    c.btn.disabled = !(ratesReady && L.canConvert({ amount: c.amount.value, from: c.from.value, to: c.to.value }));
  }
  function setAmountError(msg) {
    c.err.textContent = msg || "";
    c.amount.classList.toggle("is-invalid", !!msg);
  }
  function renderCurMeta(d) {
    $("#curSource").textContent = d.source;
    $("#curDate").textContent = ruDate(d.rate_date);
    const badge = $("#curBadge");
    badge.textContent = d.from_cache ? "из кэша" : "актуально";
    badge.className = `badge rounded-pill ${d.from_cache ? "text-bg-warning" : "text-bg-success"}`;
    $("#curMeta").hidden = false;
    d.warning ? alertBox(c.alert, "warning", d.warning) : hide(c.alert);
  }

  async function loadRates() {
    hide(c.retry);
    try {
      const d = await api("/api/rates");
      const opts = d.currencies.map((x) =>
        `<option value="${L.escapeHtml(x.code)}">${L.escapeHtml(x.code)} · ${L.escapeHtml(x.name)}</option>`).join("");
      const keepFrom = c.from.value, keepTo = c.to.value;
      c.from.innerHTML = c.to.innerHTML = opts;
      c.from.value = keepFrom || "EUR";
      c.to.value = keepTo || "MDL";
      ratesReady = true;
      renderCurMeta(d);
    } catch (e) {
      ratesReady = false;
      alertBox(c.alert, "danger", e.message);
      c.retry.hidden = false;
    }
    refreshButton();
  }

  c.amount.addEventListener("input", () => {
    const raw = c.amount.value;
    setAmountError(raw.trim() ? (L.validateAmount(raw).error || "") : "");
    refreshButton();
  });
  [c.from, c.to].forEach((el) => el.addEventListener("change", refreshButton));
  c.swap.addEventListener("click", () => {
    [c.from.value, c.to.value] = [c.to.value, c.from.value];
    if (c.amount.value.trim() && L.validateAmount(c.amount.value).ok && ratesReady) c.form.requestSubmit();
  });
  c.retry.addEventListener("click", loadRates);

  c.form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const v = L.validateAmount(c.amount.value);
    if (!v.ok) { setAmountError(v.error); c.out.hidden = true; return; }
    setAmountError("");
    setBusy(c.btn, true, "Считаем…");
    c.btn.disabled = true;
    try {
      const d = await api("/api/convert", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ amount: v.value, from: c.from.value, to: c.to.value }),
      });
      $("#resultValue").textContent = `${nf.format(Number(d.result))} ${d.to}`;
      $("#resultFrom").textContent = `${nf.format(Number(d.amount))} ${d.from} =`;
      $("#resultRate").textContent = d.same_currency
        ? "Валюты совпадают, курс 1 : 1"
        : `1 ${d.from} = ${nf.format(Number(d.rate))} ${d.to}`;
      c.out.hidden = false;
      $("#resultHint").hidden = true;
      renderCurMeta(d);
    } catch (err) {
      c.out.hidden = true;
      alertBox(c.alert, "danger", err.message);
    } finally {
      setBusy(c.btn, false);
      refreshButton();
    }
  });

  /* ---------- Астероиды ---------- */
  const n = {
    form: $("#neoForm"), date: $("#neoDate"), btn: $("#neoBtn"), err: $("#dateError"),
    alert: $("#neoAlert"), list: $("#neoList"), sum: $("#neoSummary"), only: $("#onlyHazard"),
    today: $("#todayBtn"), meta: $("#neoMeta"),
  };
  let lastNeo = null;
  const localToday = () => {
    const d = new Date();
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
  };
  n.date.value = localToday();

  function asteroidCard(a) {
    const pct = L.distancePercent(a.miss_lunar);
    const dia = a.diameter_min_m != null
      ? `${nf1.format(a.diameter_min_m)}–${nf1.format(a.diameter_max_m)} м` : "—";
    const vel = a.velocity_kms != null ? `${nf1.format(a.velocity_kms)} км/с` : "—";
    const miss = a.miss_km != null
      ? `${new Intl.NumberFormat("ru-RU", { maximumFractionDigits: 0 }).format(a.miss_km)} км` : "—";
    const ld = a.miss_lunar != null ? `${nf1.format(a.miss_lunar)} расстояний до Луны` : "";
    const name = a.url
      ? `<a href="${L.escapeHtml(a.url)}" target="_blank" rel="noopener">${L.escapeHtml(a.name)}</a>`
      : L.escapeHtml(a.name);
    return `<article class="neo ${a.hazardous ? "is-hazard" : ""}">
      <div class="d-flex justify-content-between align-items-start gap-2 mb-3">
        <h3 class="neo-name">${name}</h3>
        <span class="badge rounded-pill ${a.hazardous ? "text-bg-danger" : "text-bg-success"}">
          ${a.hazardous ? "Потенциально опасен" : "Не опасен"}</span>
      </div>
      <dl class="row neo-stats g-2 mb-3">
        <div class="col-4"><dt>Диаметр</dt><dd>${dia}</dd></div>
        <div class="col-4"><dt>Скорость</dt><dd>${vel}</dd></div>
        <div class="col-4"><dt>Расстояние</dt><dd>${miss}</dd></div>
      </dl>
      <div class="track" role="img" aria-label="${L.escapeHtml(ld)}">
        <span class="track-earth"></span>
        <span class="track-moon" style="left:${L.MOON_PERCENT}%"></span>
        <span class="track-rock" style="left:${pct}%"></span>
      </div>
      <div class="track-legend"><span>Земля</span><span style="margin-left:${Math.max(0, L.MOON_PERCENT - 8)}%">Луна</span><span class="ms-auto">${L.escapeHtml(ld)}</span></div>
    </article>`;
  }

  function renderNeo() {
    const d = lastNeo;
    if (!d) return;
    $("#neoSource").textContent = d.source;
    $("#neoStamp").textContent = new Date(d.fetched_at).toLocaleString("ru-RU");
    $("#neoShownDate").textContent = ruDate(d.date);
    const badge = $("#neoBadge");
    badge.textContent = d.from_cache ? "из кэша" : "актуально";
    badge.className = `badge rounded-pill ${d.from_cache ? "text-bg-warning" : "text-bg-success"}`;
    n.meta.hidden = false;
    d.warning ? alertBox(n.alert, "warning", d.warning) : hide(n.alert);

    const closest = d.asteroids.length ? Math.min(...d.asteroids.map((a) => a.miss_lunar ?? Infinity)) : null;
    $("#sumCount").textContent = d.count;
    $("#sumHazard").textContent = d.hazardous_count;
    $("#sumClosest").textContent = closest != null && isFinite(closest) ? `${nf1.format(closest)} LD` : "—";
    n.sum.hidden = false;

    const rows = d.asteroids.filter((a) => !n.only.checked || a.hazardous);
    n.list.innerHTML = rows.length
      ? rows.map(asteroidCard).join("")
      : `<p class="empty">${d.asteroids.length ? "Среди этих астероидов опасных нет." : "Для этой даты астероидов нет."}</p>`;
  }

  n.only.addEventListener("change", renderNeo);
  n.today.addEventListener("click", () => { n.date.value = localToday(); n.err.textContent = ""; n.date.classList.remove("is-invalid"); });
  n.form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const v = L.validateDate(n.date.value);
    n.err.textContent = v.ok ? "" : v.error;
    n.date.classList.toggle("is-invalid", !v.ok);
    if (!v.ok) return;
    setBusy(n.btn, true, "Запрашиваем NASA…");
    n.btn.disabled = true;
    try {
      lastNeo = await api(`/api/neo?date=${encodeURIComponent(v.value)}`);
      renderNeo();
    } catch (err) {
      alertBox(n.alert, "danger", err.message);
    } finally {
      setBusy(n.btn, false);
      n.btn.disabled = false;
    }
  });

  /* ---------- Вкладки ---------- */
  const hash = location.hash.replace("#", "");
  if (hash === "neo") bootstrap.Tab.getOrCreateInstance($("#tab-neo")).show();
  document.querySelectorAll('[data-bs-toggle="pill"]').forEach((t) =>
    t.addEventListener("shown.bs.tab", () => history.replaceState(null, "", t.dataset.hash)));

  loadRates();
})();
