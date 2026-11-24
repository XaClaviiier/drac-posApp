"use strict";

(() => {
  const last = (order) => order?.handoff?.history.at(-1);
  const queued = (order) => last(order)?.state === "queued";
  const statusAt = (order, count) => count ? order.workflow.history[count - 1].to : "ready";
  const roleAllowed = (status, role) => role === "Owner" || (status === "completed" && role === "Teknisi");
  const money = window.POSItems.money;

  function eligibility(order, role) {
    if (!order) return "Buka Service Order terlebih dahulu.";
    if (queued(order)) return "SO sudah berada dalam antrean kasir. Owner harus menariknya sebelum revisi.";
    const status = order.workflow?.status || "ready";
    if (!["completed", "cancelled"].includes(status)) return "Tutup pekerjaan sebagai Selesai atau Dibatalkan sebelum menyerahkan.";
    if (!roleAllowed(status, role)) return "Penyerahan SO Selesai hanya Teknisi/Owner; SO Dibatalkan hanya Owner.";
    if (!order.realization) return "Simpan realisasi secara eksplisit sebelum menyerahkan. Estimasi bukan biaya akhir.";
    if (status === "cancelled" && window.POSItems.totals(order.realization.items).total === 0) return "SO Dibatalkan tanpa biaya tidak masuk antrean tagihan.";
    return "";
  }

  function validate(store) {
    const fail = () => { throw new Error("invalid-storage"); };
    for (const order of store.serviceOrders || []) {
      if (!Object.hasOwn(order, "handoff")) continue;
      const history = order.handoff?.history;
      if (!Array.isArray(history) || !history.length || history.length > 100 || !order.realization) fail();
      const real = order.realization.history, workflow = order.workflow?.history || [];
      let previous = null, at = Date.parse(order.createdAt);
      const ids = new Set();
      for (const event of history) {
        if (!event || typeof event.id !== "string" || !event.id || event.id.length > 100 || ids.has(event.id) || !["queued", "withdrawn"].includes(event.state) || !["Owner", "Teknisi"].includes(event.actor) || typeof event.at !== "string" || !Number.isFinite(Date.parse(event.at)) || Date.parse(event.at) < at || typeof event.reason !== "string" || event.reason.length > 500 || !Number.isInteger(event.realizationRevision) || event.realizationRevision < 1 || event.realizationRevision > real.length || !Number.isInteger(event.workflowCount) || event.workflowCount < 0 || event.workflowCount > workflow.length) fail();
        if (previous && (event.realizationRevision < previous.realizationRevision || event.workflowCount < previous.workflowCount)) fail();
        const revision = real[event.realizationRevision - 1];
        const beforeAt = Math.max(Date.parse(revision.at), event.workflowCount ? Date.parse(workflow[event.workflowCount - 1].at) : Date.parse(order.createdAt));
        const afterAt = Math.min(real[event.realizationRevision] ? Date.parse(real[event.realizationRevision].at) : Infinity, workflow[event.workflowCount] ? Date.parse(workflow[event.workflowCount].at) : Infinity);
        if (Date.parse(event.at) < beforeAt || Date.parse(event.at) > afterAt) fail();
        if (event.state === "queued") {
          const status = statusAt(order, event.workflowCount);
          if (previous?.state === "queued" || !["completed", "cancelled"].includes(status) || !roleAllowed(status, event.actor) || (status === "cancelled" && window.POSItems.totals(revision.after).total === 0)) fail();
        } else if (previous?.state !== "queued" || event.actor !== "Owner" || !event.reason.trim() || event.realizationRevision !== previous.realizationRevision || event.workflowCount !== previous.workflowCount) fail();
        previous = event; at = Date.parse(event.at); ids.add(event.id);
      }
      if (previous.state === "queued" && (previous.realizationRevision !== real.length || previous.workflowCount !== workflow.length)) fail();
    }
  }

  function createFeature(api) {
    const $ = (id) => document.getElementById(id), create = api.create;
    let orderId = null, basis = "", stale = false, saving = false;
    const signature = () => JSON.stringify([api.current()?.handoff, api.current()?.realization, api.current()?.workflow]);
    const isDirty = () => $("handoff-reason").value !== "";
    const fail = (message, id = "handoff-error") => { $("handoff-error").textContent = message; const field = $(id); if (id === "handoff-error") field.tabIndex = -1; field.focus(); };

    function renderQueue() {
      api.renderCashier?.();
    }

    function render() {
      const order = api.current(); if (!order) return;
      if (orderId !== order.id) { orderId = order.id; $("handoff-reason").value = ""; $("handoff-error").textContent = ""; }
      if (!isDirty()) { basis = signature(); stale = false; } else if (basis !== signature()) stale = true;
      const active = queued(order), event = last(order);
      const invoice = window.POSInvoices.forOrder(api.state(), order.id), issued = window.POSInvoices.finalFor(api.state(), order.id);
      $("handoff-status").textContent = active ? "Dalam antrean kasir" : event ? "Ditarik dari antrean" : "Belum diserahkan ke kasir";
      $("handoff-note").textContent = active ? "Biaya dan progres terkunci. Owner menarik SO dari antrean sebelum revisi; invoice belum diterbitkan." : eligibility(order, api.role()) || "Periksa rincian realisasi tersimpan, lalu serahkan. Tindakan ini mengunci biaya dan progres sampai ditarik Owner.";
      if (issued) { $("handoff-status").textContent = "Invoice final sudah diterbitkan"; $("handoff-note").textContent = "SO tetap terkunci. Koreksi harga dilakukan Owner pada invoice, bukan dengan menarik atau mengubah SO."; }
      $("so-invoice").hidden = !invoice && (!active || api.role() === "Teknisi"); $("so-invoice").textContent = invoice ? "Buka invoice" : "Buat invoice draf";
      const total = order.realization ? window.POSItems.totals(order.realization.items).total : null;
      $("handoff-total").textContent = total === null ? "Realisasi belum dicatat" : `${money.format(total)}${total === 0 ? " · tanpa biaya, bukan status lunas" : " · realisasi tersimpan"}`;
      $("handoff-send").hidden = active || api.role() === "Kasir"; $("handoff-send").disabled = Boolean(eligibility(order, api.role()));
      $("handoff-withdraw").hidden = issued || !active || api.role() !== "Owner"; $("handoff-reason").disabled = issued || !active || api.role() !== "Owner";
      $("handoff-withdraw-button").disabled = stale; $("handoff-reset").hidden = !isDirty();
      $("handoff-log").hidden = api.role() !== "Owner"; $("handoff-history").replaceChildren();
      if (api.role() === "Owner") {
        for (const e of [...(order.handoff?.history || [])].reverse()) {
          const li = create("li", "progress-event");
          li.append(create("strong", "", e.state === "queued" ? "Diserahkan ke kasir" : "Ditarik dari antrean"), create("span", "muted", `${new Date(e.at).toLocaleString("id-ID")} · ${e.actor} (simulasi) · revisi realisasi ${e.realizationRevision}`));
          if (e.reason) li.append(create("p", "preserve-text", e.reason)); $("handoff-history").append(li);
        }
      } else $("handoff-log").open = false;
      if (stale) $("handoff-error").textContent = "Basis SO berubah. Alasan lokal tetap ada; bersihkan isian lalu periksa versi terbaru sebelum menarik.";
    }

    function act(state) {
      if (saving || !api.current()) return;
      $("handoff-error").textContent = "";
      const order = api.current(), active = queued(order), reason = $("handoff-reason").value.trim();
      if (state === "queued") {
        const error = eligibility(order, api.role()); if (error) { fail(error); return; }
        if (api.hasEdits() || isDirty()) { fail("Simpan atau bersihkan isian progres/realisasi/penarikan dahulu. Penyerahan tidak menyimpan isian otomatis."); return; }
      } else {
        if (window.POSInvoices.finalFor(api.state(), order.id)) { fail("Invoice sudah final. SO tidak dapat ditarik; koreksi harga melalui invoice Owner."); return; }
        if (api.role() !== "Owner" || !active) { fail("Hanya Owner dapat menarik SO yang masih dalam antrean."); return; }
        if (stale || basis !== signature()) { fail("Basis SO berubah. Bersihkan isian penarikan lalu periksa versi terbaru."); return; }
        if (!reason || reason.length > 500) { fail("Isi alasan penarikan, maksimal 500 karakter.", "handoff-reason"); return; }
        if (api.hasEdits()) { fail("Bersihkan isian progres/realisasi sebelum menarik SO dari antrean."); return; }
      }
      const history = order.handoff?.history || [];
      if (history.length >= 100) { fail("Demo dibatasi 100 peristiwa penyerahan/penarikan per SO. Riwayat tetap utuh."); return; }
      const total = window.POSItems.totals(order.realization.items).total;
      if (!window.confirm(`${state === "queued" ? "Serahkan ke kasir dan kunci rincian" : "Tarik dari antrean untuk diperiksa ulang"}: ${order.reference}, ${money.format(total)}? Ini tidak menerbitkan invoice atau mengubah stok/pembayaran.`)) return;
      const entry = { id: crypto.randomUUID(), state, actor: api.role(), at: new Date().toISOString(), reason: state === "withdrawn" ? reason : "", realizationRevision: order.realization.history.length, workflowCount: order.workflow?.history.length || 0 };
      saving = true;
      try {
        if (!api.persist({ ...api.state(), serviceOrders: api.state().serviceOrders.map((o) => o.id === order.id ? { ...o, handoff: { history: [...history, entry] } } : o) })) { fail("Belum tersimpan. Isian tetap ada; Coba lagi hanya memuat ulang, tidak menjalankan penyerahan/penarikan."); return; }
        $("handoff-reason").value = ""; api.refresh(); api.renderDetail();
        api.announce(state === "queued" ? "SO masuk antrean kasir. Biaya dan progres terkunci; belum ada invoice." : "SO ditarik dari antrean. Owner dapat merevisi; serahkan ulang setelah diperiksa.");
        $("handoff-status").tabIndex = -1; $("handoff-status").focus();
      } finally { saving = false; }
    }

    $("handoff-send").addEventListener("click", () => act("queued"));
    $("so-invoice").addEventListener("click", () => { if (api.current()) api.invoice(api.current().id); });
    $("handoff-withdraw").addEventListener("submit", (event) => { event.preventDefault(); act("withdrawn"); });
    $("handoff-reason").addEventListener("input", () => { $("handoff-error").textContent = ""; $("handoff-reset").hidden = !isDirty(); });
    $("handoff-reset").addEventListener("click", () => {
      if (isDirty() && !window.confirm("Buang alasan penarikan lokal? Riwayat tersimpan tetap utuh.")) return;
      $("handoff-reason").value = ""; $("handoff-error").textContent = ""; render(); $("handoff-status").tabIndex = -1; $("handoff-status").focus();
    });
    return { render, renderQueue, isDirty, discard: () => { $("handoff-reason").value = ""; $("handoff-error").textContent = ""; }, conflict: () => { stale = true; } };
  }

  window.POSHandoff = Object.freeze({ validate, queued, eligibility, createFeature });
})();
