"use strict";

(() => {
  const amounts = window.POSItems;
  const same = (a, b) => JSON.stringify(a) === JSON.stringify(b);
  const canEdit = (status, role) => role === "Owner" || (role === "Teknisi" && !["completed", "cancelled"].includes(status));
  const statusAt = (order, count) => count ? order.workflow.history[count - 1].to : "ready";
  const normalize = (item) => ({ id: item.id, catalogId: item.catalogId, kind: item.kind, label: item.label, unit: item.unit, quantity: amounts.canonical(item.quantity, item.unit), unitPrice: Number(item.unitPrice) });
  const baseline = (order) => order.items.map(normalize);
  const currentItems = (order) => order.realization?.items || baseline(order);
  const addedCost = (before, after) => after.some((item) => {
    const previous = before.find((i) => i.id === item.id);
    return !previous || amounts.subtotal(item) > amounts.subtotal(previous);
  });

  function validateItems(items) {
    if (!Array.isArray(items) || items.length > 100) return false;
    const ids = new Set();
    return items.every((item) => {
      const product = amounts.catalog.find((p) => p.id === item?.catalogId);
      if (!item || typeof item.id !== "string" || !item.id || item.id.length > 100 || ids.has(item.id) || !product || item.label !== product.label || item.unit !== product.unit || item.kind !== product.kind || typeof item.quantity !== "string" || item.quantity !== amounts.canonical(item.quantity, item.unit) || typeof item.unitPrice !== "number" || !amounts.integer(item.unitPrice)) return false;
      ids.add(item.id);
      return true;
    }) && amounts.totals(items) !== null;
  }

  function validate(store) {
    const fail = () => { throw new Error("invalid-storage"); };
    for (const order of store.serviceOrders || []) {
      if (!Object.hasOwn(order, "realization")) continue;
      const real = order.realization;
      if (!real || !validateItems(real.items) || !Array.isArray(real.history) || !real.history.length || real.history.length > 200) fail();
      let previous = baseline(order);
      let at = Date.parse(order.createdAt);
      let workflowCount = 0;
      const ids = new Set();
      for (const event of real.history) {
        const history = order.workflow?.history || [];
        if (!event || typeof event.id !== "string" || !event.id || event.id.length > 100 || ids.has(event.id) || typeof event.at !== "string" || !Number.isFinite(Date.parse(event.at)) || Date.parse(event.at) < at || !Number.isInteger(event.workflowCount) || event.workflowCount < workflowCount || event.workflowCount > history.length || typeof event.reason !== "string" || !event.reason.trim() || event.reason.length > 500 || typeof event.approved !== "boolean" || !["Owner", "Teknisi"].includes(event.actor) || !canEdit(statusAt(order, event.workflowCount), event.actor) || !same(previous, event.before) || !validateItems(event.after) || (same(event.before, event.after) && real.history[0] !== event) || (addedCost(event.before, event.after) && !event.approved)) fail();
        const beforeAt = event.workflowCount ? Date.parse(history[event.workflowCount - 1].at) : Date.parse(order.createdAt);
        const afterAt = history[event.workflowCount] ? Date.parse(history[event.workflowCount].at) : Infinity;
        if (Date.parse(event.at) < beforeAt || Date.parse(event.at) > afterAt) fail();
        previous = event.after;
        at = Date.parse(event.at);
        workflowCount = event.workflowCount;
        ids.add(event.id);
      }
      if (!same(previous, real.items)) fail();
    }
  }

  function createFeature(api) {
    const $ = (id) => document.getElementById(id);
    const create = api.create;
    let orderId = null, buffer = [], dirty = false, stale = false, basis = null, workflowBasis = "", saving = false;
    const signature = () => JSON.stringify(api.current()?.realization || null);
    const writable = () => api.current() && !window.POSHandoff.queued(api.current()) && !window.POSInvoices.finalFor(api.state(), api.current().id) && canEdit(api.workflow(api.current()).status, api.role());
    const message = (text, error = false) => { $("actual-status").textContent = text; $("actual-status").dataset.state = error ? "error" : "normal"; };

    for (const item of amounts.catalog) {
      const option = create("option", "", `${item.label} (${item.unit}, ${amounts.money.format(item.price)})`);
      option.value = item.id;
      $("actual-catalog").append(option);
    }

    function clearError() {
      $("actual-error").textContent = "";
      $("actual-form").querySelectorAll('[aria-invalid="true"]').forEach((field) => field.removeAttribute("aria-invalid"));
    }

    function markDirty(resetApproval = true) {
      dirty = true;
      if (resetApproval) $("actual-approval").checked = false;
      clearError();
      message(stale ? "Isian lokal dipertahankan. Muat realisasi tersimpan sebelum mengedit ulang." : "Perubahan realisasi belum disimpan", stale);
      $("actual-reset").hidden = false;
      totals();
    }

    function totals() {
      const sum = amounts.totals(buffer);
      for (const [name, value] of [["services", "service"], ["parts", "part"], ["total", "total"]]) $("actual-" + name).textContent = sum ? amounts.money.format(sum[value]) : "Periksa qty/harga";
      $("actual-estimate").textContent = amounts.money.format(api.current().estimateTotal);
      for (const item of buffer) {
        const amount = amounts.subtotal(item);
        const el = $("actual-subtotal-" + item.id);
        if (el) el.textContent = amount === null ? "Periksa qty/harga" : amounts.money.format(amount);
      }
      $("actual-empty").hidden = buffer.length > 0;
    }

    function renderItems() {
      $("actual-items").replaceChildren(...buffer.map((item, index) => {
        const row = create("article", "estimate-item");
        const head = create("div", "panel-title");
        const info = create("div");
        const product = amounts.catalog.find((p) => p.id === item.catalogId);
        info.append(create("h3", "", item.label), create("p", "muted", `${item.unit} · harga katalog contoh ${amounts.money.format(product.price)}`));
        const remove = create("button", "secondary", "Hapus item realisasi");
        remove.type = "button";
        remove.dataset.actualRemove = item.id;
        remove.setAttribute("aria-label", `Hapus realisasi ${item.label}, baris ${index + 1}`);
        head.append(info, remove);
        const grid = create("div", "estimate-inputs");
        for (const [key, title] of [["quantity", `Jumlah (${item.unit})`], ["unitPrice", "Harga satuan (Rp)"]]) {
          const group = create("div", "field");
          const label = create("label", "", title);
          const input = create("input");
          input.id = `actual-${key}-${item.id}`;
          label.htmlFor = input.id;
          input.type = "text";
          input.inputMode = key === "quantity" && amounts.fractional(item.unit) ? "decimal" : "numeric";
          input.maxLength = 30;
          input.name = key;
          input.value = String(item[key]);
          input.dataset.actualItem = item.id;
          input.dataset.actualField = key;
          input.setAttribute("aria-describedby", "actual-error");
          group.append(label, input);
          grid.append(group);
        }
        const sum = create("div", "item-subtotal");
        const value = create("strong");
        value.id = "actual-subtotal-" + item.id;
        sum.append(create("span", "muted", "Subtotal"), value);
        grid.append(sum);
        row.append(head, grid);
        return row;
      }));
      totals();
      permissions();
    }

    function permissions() {
      const edit = writable();
      $("actual-form").querySelectorAll("input, textarea, select, [data-actual-remove], #actual-add").forEach((field) => { field.disabled = !edit; });
      $("actual-save").hidden = !edit;
      $("actual-save").disabled = stale;
      $("actual-approval-control").hidden = !edit;
      $("actual-reset").hidden = !dirty;
      const status = api.workflow(api.current()).status;
      $("actual-permission").textContent = window.POSHandoff.queued(api.current()) ? "Realisasi terkunci selama dalam antrean kasir. Owner harus menarik SO sebelum merevisi." : !edit ? "Realisasi hanya dibaca pada peran/status ini. SO Selesai atau Dibatalkan hanya dapat direvisi Owner." : ["completed", "cancelled"].includes(status) ? "Owner dapat menyesuaikan biaya akhir dengan alasan. Status pekerjaan tetap; invoice belum diterbitkan." : "Catat jasa dan part yang benar-benar dikerjakan/dipakai. Tambahan item atau kenaikan biaya per baris memerlukan persetujuan pelanggan.";
      if (window.POSInvoices.finalFor(api.state(), api.current().id)) $("actual-permission").textContent = "Invoice sudah final. Realisasi SO tetap terkunci; koreksi harga hanya oleh Owner pada invoice.";
      $("actual-log").hidden = api.role() !== "Owner";
      $("actual-history").replaceChildren();
      if (api.role() === "Owner") {
        const history = api.current().realization?.history || [];
        for (const event of [...history].reverse()) {
          const li = create("li", "progress-event");
          li.append(create("strong", "", `${new Date(event.at).toLocaleString("id-ID")} · ${event.actor} (simulasi)`), create("p", "preserve-text", event.reason));
          for (const id of new Set([...event.before, ...event.after].map((i) => i.id))) {
            const before = event.before.find((i) => i.id === id), after = event.after.find((i) => i.id === id);
            if (same(before, after)) continue;
            const describe = (i) => i ? `${i.quantity.replace(".", ",")} ${i.unit} × ${amounts.money.format(i.unitPrice)}` : "Tidak ada";
            li.append(create("p", "", `${(after || before).label}: ${describe(before)} menjadi ${describe(after)}`));
          }
          if (same(event.before, event.after)) li.append(create("p", "", "Pencatatan awal sesuai estimasi."));
          li.append(create("span", "muted", event.approved ? "Persetujuan lisan tambahan biaya dicatat untuk revisi ini." : "Revisi ini tidak menambah biaya baris."));
          $("actual-history").append(li);
        }
        if (!history.length) $("actual-history").append(create("li", "", "Belum ada revisi realisasi yang tersimpan."));
      } else $("actual-log").open = false;
    }

    function reset() {
      const order = api.current();
      orderId = order.id;
      buffer = structuredClone(currentItems(order));
      basis = signature();
      workflowBasis = JSON.stringify(order.workflow || null);
      dirty = false; stale = false;
      $("actual-reason").value = "";
      $("actual-approval").checked = false;
      clearError(); renderItems();
      message(order.realization ? "Realisasi tersimpan di perangkat ini" : "Realisasi belum dicatat; rincian awal mengikuti estimasi");
    }

    function render() {
      if (!api.current()) return;
      if (orderId !== api.current().id || !dirty) { reset(); return; }
      if (signature() !== basis) stale = true;
      const workflowNow = JSON.stringify(api.current().workflow || null);
      if (stale || workflowNow !== workflowBasis) $("actual-approval").checked = false;
      workflowBasis = workflowNow;
      permissions(); totals();
      if (stale) message("Realisasi berubah di tab lain. Isian lokal tetap ada; muat realisasi tersimpan sebelum mengedit ulang.", true);
    }

    function error(text, fieldId) {
      $("actual-error").textContent = text;
      const field = $(fieldId);
      field.setAttribute("aria-invalid", "true");
      if (!field.disabled) field.focus();
      else { $("actual-error").tabIndex = -1; $("actual-error").focus(); }
    }

    function save(event) {
      event.preventDefault();
      if (saving || !api.current()) return;
      clearError();
      if (!writable()) { error("Peran atau status SO tidak mengizinkan perubahan realisasi.", "actual-reason"); return; }
      if (stale || signature() !== basis) { stale = true; permissions(); error("Realisasi tersimpan sudah berubah. Muat realisasi tersimpan lalu terapkan ulang perubahan.", "actual-reset"); return; }
      const sum = amounts.totals(buffer);
      for (const item of buffer) {
        if (amounts.quantity(item.quantity, item.unit) === null) { error(amounts.fractional(item.unit) ? "Jumlah harus positif, maksimal 3 desimal dan 999999,999." : "Jumlah pcs/unit/pekerjaan harus bilangan bulat positif, maksimal 999999.", `actual-quantity-${item.id}`); return; }
        if (!amounts.integer(item.unitPrice)) { error("Harga harus rupiah bulat 0–1.000.000.000.", `actual-unitPrice-${item.id}`); return; }
      }
      if (!sum) { error("Total melampaui kapasitas angka demo. Kurangi jumlah atau harga.", "actual-reason"); return; }
      const reason = $("actual-reason").value.trim();
      if (!reason || reason.length > 500) { error("Isi alasan pencatatan/perubahan, maksimal 500 karakter.", "actual-reason"); return; }
      const order = api.current(), before = currentItems(order), after = buffer.map(normalize);
      if (order.realization && same(before, after)) { error("Tidak ada perubahan rincian realisasi untuk disimpan.", "actual-reason"); return; }
      if ((order.realization?.history.length || 0) >= 200) { error("Demo dibatasi 200 revisi per SO. Riwayat lama tetap dipertahankan.", "actual-reason"); return; }
      const approval = addedCost(before, after);
      if (approval && !$("actual-approval").checked) { error("Catat persetujuan lisan pelanggan untuk tambahan item atau kenaikan biaya baris ini.", "actual-approval"); return; }
      const entry = { id: crypto.randomUUID(), at: new Date().toISOString(), actor: api.role(), workflowCount: order.workflow?.history.length || 0, reason, approved: approval, before: structuredClone(before), after: structuredClone(after) };
      const realization = { items: after, history: [...(order.realization?.history || []), entry] };
      saving = true;
      try {
        const state = api.state();
        if (!api.persist({ ...state, serviceOrders: state.serviceOrders.map((o) => o.id === order.id ? { ...o, realization } : o) })) {
          message("Belum tersimpan. Rincian dan alasan tetap ada; belum ada riwayat baru.", true);
          return;
        }
        dirty = false; reset(); api.refresh();
        api.announce("Realisasi tersimpan di perangkat ini. Estimasi awal tetap utuh; belum ada invoice atau pengeluaran stok.");
        $("actual-save").focus();
      } finally { saving = false; }
    }

    $("actual-form").addEventListener("submit", save);
    $("actual-form").addEventListener("input", (event) => {
      if (!writable()) return;
      const el = event.target;
      if (el.dataset.actualField) {
        const item = buffer.find((i) => i.id === el.dataset.actualItem);
        if (!item) return;
        item[el.dataset.actualField] = el.value;
      } else if (!["actual-reason", "actual-approval"].includes(el.id)) return;
      markDirty(el.id !== "actual-approval" && el.id !== "actual-reason");
    });
    $("actual-add").addEventListener("click", () => {
      if (!writable()) return;
      if (buffer.length >= 100) { error("Demo dibatasi 100 baris per SO.", "actual-catalog"); return; }
      const item = amounts.catalog.find((p) => p.id === $("actual-catalog").value);
      if (!item) return;
      buffer.push({ id: crypto.randomUUID(), catalogId: item.id, kind: item.kind, label: item.label, unit: item.unit, quantity: "1", unitPrice: item.price });
      markDirty(); renderItems();
      $(`actual-quantity-${buffer.at(-1).id}`).focus();
    });
    $("actual-items").addEventListener("click", (event) => {
      const button = event.target.closest("[data-actual-remove]");
      if (!button || !writable()) return;
      buffer = buffer.filter((i) => i.id !== button.dataset.actualRemove);
      markDirty(); renderItems(); $("actual-catalog").focus();
    });
    $("actual-reset").addEventListener("click", () => {
      if (dirty && !window.confirm("Buang isian realisasi lokal dan muat rincian tersimpan terbaru? Riwayat tersimpan tetap utuh.")) return;
      reset(); $("actual-catalog").disabled ? $("so-heading").focus() : $("actual-catalog").focus();
    });
    return { render, reset, isDirty: () => dirty, discard: () => { dirty = false; }, roleChanged: () => { $("actual-approval").checked = false; render(); }, conflict: () => { $("actual-approval").checked = false; } };
  }

  window.POSRealization = Object.freeze({ validate, createFeature });
})();
