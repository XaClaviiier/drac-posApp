"use strict";

(() => {
  const catalog = window.POSItems.catalog;
  const money = new Intl.NumberFormat("id-ID", { style: "currency", currency: "IDR", maximumFractionDigits: 0 });
  const date = new Intl.DateTimeFormat("id-ID", { dateStyle: "medium", timeStyle: "short" });
  const text = (v, max) => typeof v === "string" && v.length <= max;
  const id = (v) => typeof v === "string" && v.length > 0 && v.length <= 100;
  const stamp = (v) => typeof v === "string" && Number.isFinite(Date.parse(v));
  const writer = (role) => role === "Owner" || role === "Teknisi";
  const integer = (v, min, max) => String(v).trim() !== "" && /^\d+$/.test(String(v)) && Number.isSafeInteger(Number(v)) && Number(v) >= min && Number(v) <= max;

  function completeItem(item) {
    return window.POSItems.quantity(item.quantity, item.unit) !== null && integer(item.unitPrice, 0, 1000000000) && (Number(item.unitPrice) === item.masterPrice || item.priceReason.trim().length > 0);
  }

  function totals(items) {
    return window.POSItems.totals(items);
  }

  function validCollections(store) {
    const fail = () => { throw new Error("invalid-storage"); };
    if (store.diagnoses !== undefined && !Array.isArray(store.diagnoses)) fail();
    if (store.serviceOrders !== undefined && !Array.isArray(store.serviceOrders)) fail();
    const registrationIds = new Set(store.records.map((r) => r.id));
    const diagnosisIds = new Set();
    const diagnosedRegistrations = new Set();
    for (const d of store.diagnoses || []) {
      if (!d || !id(d.id) || diagnosisIds.has(d.id) || !registrationIds.has(d.registrationId) || diagnosedRegistrations.has(d.registrationId) || !text(d.findings, 2000) || !text(d.recommendations, 2000) || !["draft", "approved"].includes(d.status) || !stamp(d.updatedAt) || !writer(d.updatedBy) || !Array.isArray(d.items) || d.items.length > 100 || !Array.isArray(d.priceChanges)) fail();
      diagnosisIds.add(d.id);
      diagnosedRegistrations.add(d.registrationId);
      const itemIds = new Set();
      for (const i of d.items) {
        if (!i || !id(i.id) || itemIds.has(i.id) || !id(i.catalogId) || !["service", "part"].includes(i.kind) || !text(i.label, 100) || !i.label.trim() || !text(i.unit, 30) || !i.unit.trim() || !text(i.quantity, 30) || !text(i.unitPrice, 30) || !integer(i.masterPrice, 0, 1000000000) || !text(i.priceReason, 300)) fail();
        itemIds.add(i.id);
      }
      for (const change of d.priceChanges) {
        if (!change || !id(change.itemId) || !integer(change.oldPrice, 0, 1000000000) || !integer(change.newPrice, 0, 1000000000) || !text(change.reason, 300) || !writer(change.actor) || !stamp(change.at)) fail();
        if (change.reasonRecordedAt !== undefined && (!stamp(change.reasonRecordedAt) || !writer(change.reasonRecordedBy))) fail();
      }
      if (d.status === "approved") {
        if (!d.findings.trim() || !d.recommendations.trim() || !d.items.length || !d.items.every(completeItem) || !totals(d.items) || !stamp(d.approvedAt) || !writer(d.approvedBy)) fail();
      } else if (d.approvedAt !== null || d.approvedBy !== null) fail();
    }
    const soIds = new Set();
    const linkedDiagnoses = new Set();
    for (const so of store.serviceOrders || []) {
      const d = (store.diagnoses || []).find((item) => item.id === so?.diagnosisId);
      if (!so || !id(so.id) || soIds.has(so.id) || !d || d.status !== "approved" || linkedDiagnoses.has(d.id) || so.registrationId !== d.registrationId || !text(so.reference, 100) || !stamp(so.createdAt) || !writer(so.createdBy) || !Array.isArray(so.items) || so.items.length !== d.items.length || so.estimateTotal !== totals(d.items).total) fail();
      so.items.forEach((i, index) => {
        const original = d.items[index];
        if (!i || i.id !== original.id || i.catalogId !== original.catalogId || i.kind !== original.kind || i.label !== original.label || i.unit !== original.unit || window.POSItems.canonical(i.quantity, i.unit) !== window.POSItems.canonical(original.quantity, original.unit) || i.unitPrice !== Number(original.unitPrice)) fail();
      });
      soIds.add(so.id);
      linkedDiagnoses.add(d.id);
    }
  }

  function createFeature(api) {
    const $ = (name) => document.getElementById(name);
    const form = $("diagnosis-form");
    const create = api.create;
    let activeRegistration = null;
    let buffer = null;
    let dirty = false;
    let timer;
    const diagnosisFor = (registrationId) => (api.state()?.diagnoses || []).find((d) => d.registrationId === registrationId);
    const orderFor = (diagnosisId) => (api.state()?.serviceOrders || []).find((so) => so.diagnosisId === diagnosisId);
    const savedDiagnosis = () => diagnosisFor(activeRegistration);
    const writable = () => writer(api.role()) && buffer && buffer.status === "draft" && savedDiagnosis()?.status !== "approved";
    const setSaveStatus = (message, error = false) => { $("diagnosis-save-status").textContent = message; $("diagnosis-save-status").dataset.state = error ? "error" : "normal"; };

    catalog.forEach((item) => {
      const option = create("option", "", `${item.kind === "service" ? "Jasa" : "Sparepart"}: ${item.label} (${money.format(item.price)})`);
      option.value = item.id;
      $("estimate-catalog").append(option);
    });

    function fresh(registrationId) {
      return { id: crypto.randomUUID(), registrationId, status: "draft", findings: "", recommendations: "", items: [], priceChanges: [], approvedAt: null, approvedBy: null, updatedAt: new Date().toISOString(), updatedBy: writer(api.role()) ? api.role() : "Teknisi" };
    }

    function markDirty() {
      if (!writable()) return;
      dirty = true;
      $("verbal-approval").checked = false;
      $("approval-error").textContent = "";
      setSaveStatus("Menyimpan draf estimasi…");
      clearTimeout(timer);
      timer = setTimeout(save, 400);
      updateTotals();
    }

    function updateTotals() {
      const sum = totals(buffer.items);
      $("estimate-services").textContent = sum ? money.format(sum.service) : "Periksa nilai item";
      $("estimate-parts").textContent = sum ? money.format(sum.part) : "Periksa nilai item";
      $("estimate-total").textContent = sum ? money.format(sum.total) : "Belum dapat dihitung";
      buffer.items.forEach((item) => {
        const subtotal = $(`subtotal-${item.id}`);
        const amount = window.POSItems.subtotal(item);
        if (subtotal) subtotal.textContent = amount === null ? "Periksa qty/harga" : money.format(amount);
      });
    }

    function itemInput(item, key, label, type, parent) {
      const group = create("div", "field");
      const inputId = `item-${key}-${item.id}`;
      const caption = create("label", "", label);
      caption.htmlFor = inputId;
      const input = create("input");
      input.id = inputId;
      input.name = key;
      input.type = type;
      input.value = item[key];
      input.dataset.itemId = item.id;
      input.dataset.itemField = key;
      if (type === "number") {
        input.min = key === "quantity" ? (window.POSItems.fractional(item.unit) ? "0.001" : "1") : "0";
        input.max = key === "quantity" ? "999999.999" : "1000000000";
        input.step = key === "quantity" && window.POSItems.fractional(item.unit) ? "0.001" : "1";
        input.inputMode = key === "quantity" && window.POSItems.fractional(item.unit) ? "decimal" : "numeric";
      } else { input.maxLength = 300; }
      const error = create("span", "field-error");
      error.id = `${inputId}-error`;
      input.setAttribute("aria-describedby", error.id);
      group.append(caption, input, error);
      parent.append(group);
    }

    function renderItems() {
      $("estimate-items").replaceChildren();
      buffer.items.forEach((item, index) => {
        const row = create("article", "estimate-item");
        const heading = create("div", "panel-title");
        const title = create("div");
        title.append(create("h3", "", item.label), create("p", "muted", `${item.kind === "service" ? "Jasa" : "Sparepart"} · satuan ${item.unit} · harga katalog contoh ${money.format(item.masterPrice)}`));
        const remove = create("button", "secondary remove-item", "Hapus item");
        remove.type = "button";
        remove.dataset.itemRemove = item.id;
        remove.setAttribute("aria-label", `Hapus ${item.label}, baris ${index + 1}`);
        heading.append(title, remove);
        const grid = create("div", "estimate-inputs");
        itemInput(item, "quantity", "Jumlah", "number", grid);
        itemInput(item, "unitPrice", "Harga satuan (Rp)", "number", grid);
        const subtotal = create("div", "item-subtotal");
        subtotal.append(create("span", "muted", "Subtotal"), create("strong", "", ""));
        subtotal.lastChild.id = `subtotal-${item.id}`;
        grid.append(subtotal);
        row.append(heading, grid);
        itemInput(item, "priceReason", "Alasan perubahan harga (wajib bila berbeda dari katalog)", "text", row);
        $("estimate-items").append(row);
      });
      $("estimate-empty").hidden = buffer.items.length > 0;
      updateTotals();
      applyRole();
    }

    function applyRole() {
      if (!buffer) return;
      const edit = writable();
      $("diagnosis-findings").disabled = !edit;
      $("diagnosis-recommendations").disabled = !edit;
      $("estimate-catalog").disabled = !edit;
      $("add-estimate-item").disabled = !edit;
      form.querySelectorAll("[data-item-field], [data-item-remove]").forEach((el) => { el.disabled = !edit; });
      $("verbal-approval").disabled = !edit;
      $("verbal-control").hidden = buffer.status === "approved" || !writer(api.role());
      $("save-diagnosis").hidden = !edit;
      $("approve-diagnosis").hidden = !edit;
      const order = orderFor(buffer.id);
      $("create-service-order").hidden = buffer.status !== "approved" || (!writer(api.role()) && !order);
      $("create-service-order").textContent = order ? "Lihat Service Order" : "Buat Service Order";
      $("diagnosis-access").textContent = buffer.status === "approved" ? "Estimasi disetujui dan terkunci. Perubahan realisasi dilakukan pada Service Order di Fase 3." : writer(api.role()) ? "Isi hasil pemeriksaan dan rincian biaya. Persetujuan lisan dicatat setelah pelanggan menyetujuinya." : "Kasir dapat membaca. Pembuatan, perubahan, dan persetujuan estimasi hanya untuk Teknisi/Owner pada simulasi ini.";
      $("price-log-panel").hidden = api.role() !== "Owner";
      $("price-log-list").replaceChildren();
      if (api.role() === "Owner") {
        $("price-log-list").append(...buffer.priceChanges.map((change) => create("li", "", `${date.format(new Date(change.at))} · ${change.actor}: ${money.format(change.oldPrice)} menjadi ${money.format(change.newPrice)}. ${change.reason || "Alasan belum diisi pada draf."}${change.reasonRecordedAt ? ` Alasan dilengkapi oleh ${change.reasonRecordedBy}, ${date.format(new Date(change.reasonRecordedAt))}.` : ""}`)));
        if (!buffer.priceChanges.length) $("price-log-list").append(create("li", "", "Belum ada perubahan harga yang tersimpan."));
      } else $("price-log-panel").open = false;
    }

    function renderEditor() {
      const registration = api.state().records.find((r) => r.id === activeRegistration);
      $("diagnosis-identity").textContent = `${registration.plate} · ${registration.customer} · ${registration.reference}`;
      $("diagnosis-complaint").textContent = registration.complaint;
      $("diagnosis-status").textContent = buffer.status === "approved" ? "Disetujui" : "Draf";
      $("diagnosis-findings").value = buffer.findings;
      $("diagnosis-recommendations").value = buffer.recommendations;
      $("verbal-approval").checked = false;
      $("approval-summary").hidden = buffer.status !== "approved";
      $("approval-summary").textContent = buffer.status === "approved" ? `Persetujuan lisan dicatat oleh ${buffer.approvedBy} (simulasi), ${date.format(new Date(buffer.approvedAt))}.` : "";
      for (const name of ["findings-error", "recommendations-error", "items-error", "approval-error"]) $(name).textContent = "";
      renderItems();
      setSaveStatus(savedDiagnosis() ? "Tersimpan di perangkat ini" : "Belum disimpan");
    }

    function open(registrationId) {
      if (dirty && !save()) return;
      if (!api.state()?.records.some((r) => r.id === registrationId)) return;
      activeRegistration = registrationId;
      buffer = structuredClone(diagnosisFor(registrationId) || fresh(registrationId));
      dirty = false;
      renderEditor();
      api.show("diagnosis");
    }

    function draftCandidate() {
      const previous = savedDiagnosis();
      const next = structuredClone(buffer);
      next.updatedAt = new Date().toISOString();
      next.updatedBy = api.role();
      next.priceChanges = structuredClone(previous?.priceChanges || []);
      next.items.forEach((item) => {
        const before = previous?.items.find((old) => old.id === item.id);
        const lastChange = next.priceChanges.findLast((change) => change.itemId === item.id);
        const oldPrice = before && integer(before.unitPrice, 0, 1000000000) ? Number(before.unitPrice) : lastChange?.newPrice ?? item.masterPrice;
        if (integer(item.unitPrice, 0, 1000000000) && oldPrice !== Number(item.unitPrice)) {
          next.priceChanges.push({ itemId: item.id, oldPrice, newPrice: Number(item.unitPrice), actor: api.role(), at: next.updatedAt, reason: item.priceReason });
        } else if (lastChange && !lastChange.reason.trim() && item.priceReason.trim() && Number(item.unitPrice) === lastChange.newPrice) {
          lastChange.reason = item.priceReason;
          lastChange.reasonRecordedAt = next.updatedAt;
          lastChange.reasonRecordedBy = api.role();
        }
      });
      return next;
    }

    function commit(next) {
      const store = api.state();
      if (!api.persist({ ...store, diagnoses: [...(store.diagnoses || []).filter((d) => d.registrationId !== activeRegistration), next] })) {
        setSaveStatus("Belum tersimpan. Isian tetap ada di halaman ini.", true);
        return false;
      }
      buffer = structuredClone(next);
      dirty = false;
      setSaveStatus("Tersimpan di perangkat ini");
      api.refresh();
      return true;
    }

    function save() {
      clearTimeout(timer);
      if (!writable()) return !dirty;
      const next = draftCandidate();
      if (!commit(next)) return false;
      applyRole();
      return true;
    }

    function approvalValid() {
      let first;
      const error = (field, message) => { $(field).textContent = message; };
      error("findings-error", buffer.findings.trim() ? "" : "Tuliskan masalah yang ditemukan dari pemeriksaan.");
      error("recommendations-error", buffer.recommendations.trim() ? "" : "Tuliskan saran tindakan untuk pelanggan.");
      $("diagnosis-findings").setAttribute("aria-invalid", String(!buffer.findings.trim()));
      $("diagnosis-recommendations").setAttribute("aria-invalid", String(!buffer.recommendations.trim()));
      if (!buffer.findings.trim()) first = $("diagnosis-findings");
      else if (!buffer.recommendations.trim()) first = $("diagnosis-recommendations");
      error("items-error", buffer.items.length ? "" : "Tambahkan minimal satu jasa atau sparepart.");
      if (!buffer.items.length && !first) first = $("estimate-catalog");
      buffer.items.forEach((item) => {
        for (const key of ["quantity", "unitPrice", "priceReason"]) {
          const invalid = key === "quantity" ? window.POSItems.quantity(item.quantity, item.unit) === null : key === "unitPrice" ? !integer(item.unitPrice, 0, 1000000000) : Number(item.unitPrice) !== item.masterPrice && !item.priceReason.trim();
          const input = $(`item-${key}-${item.id}`);
          const message = key === "quantity" ? (window.POSItems.fractional(item.unit) ? "Isi jumlah positif, maksimal 3 desimal dan 999999,999." : "Jumlah harus bilangan bulat 1–999999.") : key === "unitPrice" ? "Harga harus rupiah bulat 0–1.000.000.000." : "Isi alasan perubahan harga lokal.";
          input.setAttribute("aria-invalid", String(invalid));
          $(`${input.id}-error`).textContent = invalid ? message : "";
          if (invalid && !first) first = input;
        }
      });
      error("approval-error", $("verbal-approval").checked ? "" : "Tandai persetujuan hanya setelah pelanggan menyetujui estimasi secara lisan.");
      if (!$("verbal-approval").checked && !first) first = $("verbal-approval");
      if (!first && !totals(buffer.items)) {
        error("items-error", "Total melampaui kapasitas angka demo. Kurangi jumlah atau harga sebelum mencatat persetujuan.");
        first = $(`item-quantity-${buffer.items[0].id}`);
        first.setAttribute("aria-invalid", "true");
        first.setAttribute("aria-describedby", `${first.id}-error items-error`);
      }
      if (first) { first.focus(); return false; }
      return true;
    }

    function approve() {
      clearTimeout(timer);
      if (!writable()) return;
      if (!approvalValid()) { if (dirty) save(); return; }
      const next = draftCandidate();
      next.status = "approved";
      next.approvedAt = next.updatedAt;
      next.approvedBy = api.role();
      if (!commit(next)) return;
      renderEditor();
      api.announce("Persetujuan lisan tercatat di prototype. Estimasi terkunci; belum ada SO atau invoice baru.");
    }

    function showOrder(order) {
      api.order(order.id);
    }

    function createOrder() {
      const d = savedDiagnosis();
      if (!d || d.status !== "approved") return;
      const existing = orderFor(d.id);
      if (existing) { showOrder(existing); return; }
      if (!writer(api.role())) return;
      const orderId = crypto.randomUUID();
      const order = { id: orderId, reference: `SO-${new Date().getFullYear()}-${orderId.slice(0, 8).toUpperCase()}`, diagnosisId: d.id, registrationId: d.registrationId, createdAt: new Date().toISOString(), createdBy: api.role(), items: d.items.map((i) => ({ id: i.id, catalogId: i.catalogId, kind: i.kind, label: i.label, unit: i.unit, quantity: window.POSItems.canonical(i.quantity, i.unit), unitPrice: Number(i.unitPrice) })), estimateTotal: totals(d.items).total };
      if (!api.persist({ ...api.state(), serviceOrders: [...(api.state().serviceOrders || []), order] })) { setSaveStatus("Salinan SO belum tersimpan. Estimasi disetujui tetap utuh.", true); return; }
      api.refresh();
      showOrder(order);
      api.announce("Service Order tersalin dari estimasi disetujui. Pilih penanggung jawab dan mulai pengerjaan ketika siap.");
    }

    function renderList() {
      const records = api.state()?.records || [];
      const visitDate = new Intl.DateTimeFormat("id-ID", { dateStyle: "medium", timeStyle: "short" });
      $("diagnoses-count").textContent = `${records.length} kunjungan`;
      $("diagnoses-empty").hidden = records.length > 0;
      $("diagnoses-list").replaceChildren();
      records.forEach((r) => {
        const d = diagnosisFor(r.id);
        const row = create("article", "record");
        const vehicle = create("div", "record-vehicle");
        vehicle.append(create("strong", "plate", r.plate), create("span", "record-customer", r.customer));
        const meta = create("div", "record-meta");
        meta.append(create("span", "status-label", d ? d.status === "approved" ? "Estimasi disetujui" : "Draf diagnosa" : "Belum ada diagnosa"));
        meta.append(create("span", "", r.reference), create("span", "", visitDate.format(new Date(r.createdAt))));
        const button = create("button", "record-action", d ? "Buka diagnosa" : writer(api.role()) ? "Buat diagnosa" : "Lihat kunjungan");
        button.setAttribute("aria-label", `${button.textContent} ${r.reference} · ${r.plate}`);
        button.addEventListener("click", () => open(r.id));
        row.append(vehicle, create("p", "record-complaint", r.complaint), meta, button);
        $("diagnoses-list").append(row);
      });
    }

    function onReload() {
      if (!activeRegistration || !buffer) return;
      const latest = savedDiagnosis();
      if (!dirty) { buffer = structuredClone(latest || fresh(activeRegistration)); renderEditor(); return; }
      if (latest?.status === "approved") {
        if (window.confirm("Estimasi sudah disetujui di tab lain. Ganti isian lokal yang belum tersimpan dengan estimasi disetujui?")) {
          buffer = structuredClone(latest); dirty = false; renderEditor();
        } else {
          api.error("Estimasi sudah disetujui di tab lain", "Isian lokal tetap terlihat dan tidak menimpa estimasi disetujui. Muat data terbaru untuk memilih kembali versi disetujui.");
          setSaveStatus("Isian lokal dipertahankan, tetapi estimasi sudah disetujui di tab lain. Muat data terbaru lagi untuk membuka versi disetujui.", true);
          applyRole();
        }
      } else {
        setSaveStatus("Data terbaru dimuat. Draf estimasi lokal belum tersimpan.");
      }
    }

    form.addEventListener("submit", (event) => { event.preventDefault(); save(); });
    form.addEventListener("input", (event) => {
      if (!writable()) return;
      const el = event.target;
      if (el.id === "verbal-approval") return;
      if (el.id === "diagnosis-findings") buffer.findings = el.value;
      else if (el.id === "diagnosis-recommendations") buffer.recommendations = el.value;
      else if (el.dataset.itemField) {
        const item = buffer.items.find((i) => i.id === el.dataset.itemId);
        if (!item) return;
        item[el.dataset.itemField] = el.value;
        el.removeAttribute("aria-invalid");
        $(`${el.id}-error`).textContent = "";
      } else return;
      markDirty();
    });
    $("add-estimate-item").addEventListener("click", () => {
      if (!writable()) return;
      if (buffer.items.length >= 100) { $("items-error").textContent = "Demo dibatasi 100 baris per estimasi."; return; }
      const item = catalog.find((i) => i.id === $("estimate-catalog").value);
      if (!item) return;
      const line = { id: crypto.randomUUID(), catalogId: item.id, kind: item.kind, label: item.label, unit: item.unit, masterPrice: item.price, quantity: "1", unitPrice: String(item.price), priceReason: "" };
      buffer.items.push(line);
      renderItems(); markDirty();
      $(`item-quantity-${line.id}`).focus();
    });
    $("estimate-items").addEventListener("click", (event) => {
      const button = event.target.closest("[data-item-remove]");
      if (!button || !writable()) return;
      buffer.items = buffer.items.filter((i) => i.id !== button.dataset.itemRemove);
      renderItems(); markDirty(); $("estimate-catalog").focus();
    });
    $("approve-diagnosis").addEventListener("click", approve);
    $("create-service-order").addEventListener("click", createOrder);
    $("back-from-diagnosis").addEventListener("click", () => { if (!dirty || save()) { renderList(); api.show("diagnoses"); } });
    return { open, renderList, applyRole, onReload, save, isDirty: () => dirty, cancelTimer: () => clearTimeout(timer), isWriter: writer, status: (registrationId) => diagnosisFor(registrationId)?.status, active: () => activeRegistration };
  }

  window.POSDiagnosis = Object.freeze({ validCollections, createFeature });
})();
