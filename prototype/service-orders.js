"use strict";

(() => {
  const technicians = Object.freeze({ "tech-a": "Teknisi A (contoh)", "tech-b": "Teknisi B (contoh)", "tech-c": "Teknisi C (contoh)" });
  const statuses = Object.freeze({ ready: "Belum dimulai", in_progress: "Dalam Pengerjaan", paused: "Ditunda", completed: "Selesai", cancelled: "Dibatalkan" });
  const actions = Object.freeze({ assigned: "Tetapkan teknisi", started: "Mulai pengerjaan", paused: "Tunda pekerjaan", resumed: "Lanjutkan pengerjaan", completed: "Tandai selesai", cancelled: "Batalkan pekerjaan", reopened: "Buka kembali pekerjaan" });
  const money = new Intl.NumberFormat("id-ID", { style: "currency", currency: "IDR", maximumFractionDigits: 0 });
  const date = new Intl.DateTimeFormat("id-ID", { dateStyle: "medium", timeStyle: "short" });
  const isWriter = (role) => role === "Owner" || role === "Teknisi";
  const initial = () => ({ status: "ready", technicianId: null, startedAt: null, completedAt: null, cancelledAt: null, history: [] });
  const workflow = (order) => order.workflow || initial();
  const allowed = (w, role) => !isWriter(role) ? [] : ({ ready: ["assigned", "started", "cancelled"], in_progress: ["assigned", "paused", "completed", "cancelled"], paused: ["assigned", "resumed", "cancelled"], completed: role === "Owner" ? ["reopened"] : [], cancelled: [] })[w.status] || [];
  const invalid = (message, field) => Object.assign(new Error(message), { field });

  function apply(w, action, technicianId, reason, role, at, memberIds = w.memberIds || []) {
    if (!allowed(w, role).includes(action)) throw invalid("Tindakan tidak diizinkan untuk peran atau status SO terbaru.", "so-action");
    if (typeof reason !== "string" || reason.length > 500) throw invalid("Catatan maksimal 500 karakter.", "so-reason");
    const note = reason.trim();
    const result = structuredClone(w);
    if (!Array.isArray(memberIds) || new Set(memberIds).size !== memberIds.length || memberIds.some((id) => !Object.hasOwn(technicians, id) || id === technicianId)) throw invalid("Anggota harus berbeda dari teknisi utama dan tidak boleh berulang.", "so-technician-select");
    if (["assigned", "started"].includes(action)) {
      if (!Object.hasOwn(technicians, technicianId)) throw invalid("Pilih teknisi penanggung jawab sebelum melanjutkan.", "so-technician-select");
      if (action === "assigned" && technicianId === w.technicianId && JSON.stringify(memberIds) === JSON.stringify(w.memberIds || [])) throw invalid("Pilih teknisi yang berbeda untuk mengubah penanggung jawab atau anggota.", "so-technician-select");
      if (w.technicianId && technicianId !== w.technicianId && !note) throw invalid("Isi alasan pergantian teknisi penanggung jawab.", "so-reason");
      result.technicianId = technicianId;
      if (memberIds.length || Object.hasOwn(w, "memberIds")) result.memberIds = [...memberIds];
    } else if (technicianId !== w.technicianId) {
      throw invalid("Penanggung jawab berubah. Pilih tindakan Tetapkan teknisi untuk menggantinya.", "so-action");
    }
    if (!["assigned", "started"].includes(action) && JSON.stringify(memberIds) !== JSON.stringify(w.memberIds || [])) throw invalid("Ubah anggota melalui tindakan Tetapkan teknisi.", "so-action");
    if (["paused", "cancelled", "reopened"].includes(action) && !note) throw invalid("Isi alasan tindakan sebelum melanjutkan.", "so-reason");
    if (["started", "resumed", "completed", "reopened"].includes(action) && !result.technicianId) throw invalid("Pekerjaan memerlukan teknisi penanggung jawab.", "so-technician-select");
    if (action === "started") { result.status = "in_progress"; result.startedAt = at; }
    if (action === "paused") result.status = "paused";
    if (action === "resumed") result.status = "in_progress";
    if (action === "completed") { result.status = "completed"; result.completedAt = at; }
    if (action === "cancelled") { result.status = "cancelled"; result.cancelledAt = at; }
    if (action === "reopened") { result.status = "in_progress"; result.completedAt = null; }
    return result;
  }

  function validate(store) {
    const fail = () => { throw new Error("invalid-storage"); };
    for (const order of store.serviceOrders || []) {
      if (!Object.hasOwn(order, "workflow")) continue;
      const w = order.workflow;
      if (!w || !Array.isArray(w.history) || !Object.hasOwn(statuses, w.status) || (w.technicianId !== null && !Object.hasOwn(technicians, w.technicianId))) fail();
      let replay = initial();
      let lastTime = Date.parse(order.createdAt);
      const ids = new Set();
      for (const event of w.history) {
        if (!event || typeof event.id !== "string" || !event.id || event.id.length > 100 || ids.has(event.id) || typeof event.at !== "string" || !Number.isFinite(Date.parse(event.at)) || Date.parse(event.at) < lastTime || !isWriter(event.actor) || event.from !== replay.status || event.technicianBefore !== replay.technicianId) fail();
        let next;
        if (event.memberBefore && JSON.stringify(event.memberBefore) !== JSON.stringify(replay.memberIds || [])) fail();
        try { next = apply(replay, event.action, event.technicianAfter, event.reason, event.actor, event.at, event.memberAfter); } catch { fail(); }
        if (event.to !== next.status || event.technicianAfter !== next.technicianId) fail();
        replay = next;
        lastTime = Date.parse(event.at);
        ids.add(event.id);
      }
      for (const field of ["status", "technicianId", "startedAt", "completedAt", "cancelledAt"]) if (w[field] !== replay[field]) fail();
      if (JSON.stringify(w.memberIds || []) !== JSON.stringify(replay.memberIds || [])) fail();
    }
    window.POSRealization.validate(store);
    window.POSHandoff.validate(store);
  }

  function createFeature(api) {
    const $ = (name) => document.getElementById(name);
    const create = api.create;
    let activeId = null;
    let pending = false;
    let applying = false;
    let openingFromEstimate = false;
    const current = () => (api.state()?.serviceOrders || []).find((o) => o.id === activeId);
    const actual = window.POSRealization.createFeature({ ...api, current, workflow, refresh: () => { api.refresh(); handoff.render(); } });
    const handoff = window.POSHandoff.createFeature({ ...api, current, open, renderDetail, hasEdits: () => pending || actual.isDirty() });
    const local = () => ({ action: $("so-action").value, technicianId: $("so-technician-select").value || null, reason: $("so-reason").value, memberIds: [...document.querySelectorAll('[name="so-member"]:checked')].map((el) => el.value) });
    const statusMessage = (message, error = false) => { $("so-action-status").textContent = message; $("so-action-status").dataset.state = error ? "error" : "normal"; };
    function clearValidation() {
      $("so-action-error").textContent = "";
      for (const field of ["so-action", "so-technician-select", "so-reason"]) $(field).removeAttribute("aria-invalid");
    }
    function focusAction() {
      if (!$("so-action").disabled) $("so-action").focus();
      else { $("so-heading").tabIndex = -1; $("so-heading").focus(); }
    }

    function renderList() {
      handoff.renderQueue();
      const query = $("order-search").value.trim().toLocaleLowerCase("id-ID").replace(/\s+/g, "");
      const filter = $("order-filter").value;
      const all = api.state()?.serviceOrders || [];
      const orders = all.filter((o) => {
        const r = api.state().records.find((r) => r.id === o.registrationId);
        const w = workflow(o);
        return (filter === "all" || filter === w.status) && (!query || [r.plate, r.customer, o.reference, technicians[w.technicianId] || "", ...(w.memberIds || []).map((id) => technicians[id])].some((s) => s.toLocaleLowerCase("id-ID").replace(/\s+/g, "").includes(query)));
      });
      $("orders-count").textContent = `${orders.length} dari ${all.length} SO`;
      $("orders-list").replaceChildren();
      $("orders-empty").hidden = orders.length > 0;
      $("orders-empty").querySelector("h3").textContent = all.length ? "Tidak ada hasil" : "Belum ada Service Order";
      $("orders-empty-note").textContent = all.length ? "Ubah pencarian atau pilih Semua status." : "Buat SO dari Diagnosa & Estimasi yang sudah disetujui.";
      orders.forEach((o) => {
        const r = api.state().records.find((r) => r.id === o.registrationId);
        const w = workflow(o);
        const row = create("article", "record so-record");
        const identity = create("div", "record-vehicle");
        identity.append(create("strong", "plate", r.plate), create("span", "record-customer", r.customer));
        const detail = create("div", "record-complaint");
        detail.append(create("strong", "", o.reference), create("p", "muted", technicians[w.technicianId] || "Teknisi belum ditetapkan"));
        const meta = create("div", "record-meta");
        meta.append(create("span", "status-label", statuses[w.status]), create("span", "", `${money.format(o.estimateTotal)} · estimasi`));
        const button = create("button", "record-action", "Buka SO");
        button.setAttribute("aria-label", `Buka SO ${r.plate}`);
        button.addEventListener("click", () => open(o.id));
        row.append(identity, detail, meta, button);
        $("orders-list").append(row);
      });
    }

    function fillActions(preserve = false) {
      const order = current();
      if (!order) return;
      const previous = local();
      const w = workflow(order);
      const options = window.POSHandoff.queued(order) ? [] : allowed(w, api.role());
      $("so-action").replaceChildren(create("option", "", "Pilih tindakan"));
      $("so-action").firstChild.value = "";
      options.forEach((name) => { const option = create("option", "", actions[name]); option.value = name; $("so-action").append(option); });
      const selected = preserve ? previous.action : w.status === "ready" ? "started" : "";
      if (selected && !options.includes(selected)) {
        const stale = create("option", "", `${actions[selected] || "Tindakan sebelumnya"} (tidak tersedia pada status terbaru)`);
        stale.value = selected; stale.disabled = true; $("so-action").append(stale);
      }
      $("so-action").value = selected;
      $("so-technician-select").value = preserve ? previous.technicianId || "" : w.technicianId || "";
      $("so-reason").value = preserve ? previous.reason : "";
      document.querySelectorAll('[name="so-member"]').forEach((el) => { el.checked = (preserve ? previous.memberIds : w.memberIds || []).includes(el.value); });
      $("so-permission-note").textContent = window.POSHandoff.queued(order) ? "SO dalam antrean kasir. Owner harus menariknya sebelum mengubah biaya atau progres." : api.role() === "Kasir" ? "Kasir membaca progres. Perubahan hanya dilakukan Teknisi/Owner pada simulasi ini." : w.status === "completed" ? "SO Selesai terkunci. Hanya Owner dapat membuka kembali dengan alasan." : w.status === "cancelled" ? "SO Dibatalkan ditutup. Kunjungan berikutnya memakai SO baru; biaya sebelumnya tidak dihapus." : "Terapkan tindakan secara eksplisit. Teknisi pada pilihan di bawah adalah data contoh, bukan akun nyata.";
      if (window.POSInvoices.finalFor(api.state(), order.id)) $("so-permission-note").textContent = "Invoice sudah final. SO tidak ditarik atau dibuka kembali; koreksi harga hanya pada invoice oleh Owner.";
      const canEdit = options.length > 0;
      $("so-action").disabled = !canEdit;
      $("so-reason").disabled = !canEdit;
      $("so-apply-action").hidden = !canEdit;
      $("so-clear-action").hidden = !pending;
      updateControls();
    }

    function updateControls() {
      const order = current();
      if (!order) return;
      const action = $("so-action").value;
      $("so-technician-select").disabled = window.POSHandoff.queued(order) || !allowed(workflow(order), api.role()).includes(action) || !["assigned", "started"].includes(action);
      document.querySelectorAll('[name="so-member"]').forEach((el) => { el.disabled = $("so-technician-select").disabled; });
      $("so-apply-action").textContent = actions[action] || "Terapkan perubahan";
    }

    function renderDetail(preserve = false) {
      const order = current();
      if (!order) return;
      const r = api.state().records.find((r) => r.id === order.registrationId);
      const w = workflow(order);
      $("so-reference").textContent = `${order.reference} · dibuat ${date.format(new Date(order.createdAt))}`;
      $("so-identity").textContent = `${r.plate} · ${r.customer}`;
      $("so-status").textContent = statuses[w.status];
      $("so-technician").textContent = technicians[w.technicianId] || "Belum ditetapkan";
      $("so-members").textContent = (w.memberIds || []).map((id) => technicians[id]).join(", ") || "Tanpa anggota tambahan";
      $("so-started").textContent = w.startedAt ? date.format(new Date(w.startedAt)) : "Belum dimulai";
      $("back-from-so").textContent = openingFromEstimate ? "Kembali ke estimasi" : "Kembali ke daftar SO";
      $("so-items").replaceChildren(...order.items.map((item) => {
        const row = create("article", "so-item");
        row.append(create("strong", "", item.label), create("span", "muted", `${String(item.quantity).replace(".", ",")} ${item.unit} × ${money.format(item.unitPrice)}`), create("strong", "", money.format(window.POSItems.subtotal(item))));
        return row;
      }));
      $("so-total").textContent = money.format(order.estimateTotal);
      $("so-history").replaceChildren(...[...w.history].reverse().map((event) => {
        const li = create("li", "progress-event");
        li.append(create("strong", "", actions[event.action]), create("span", "muted", `${date.format(new Date(event.at))} · ${event.actor} (simulasi)`), create("p", "", `${statuses[event.from]} menjadi ${statuses[event.to]} · ${technicians[event.technicianAfter] || "Belum ada teknisi"}`));
        if (event.reason) li.append(create("p", "preserve-text", event.reason));
        if (event.memberAfter?.length) li.append(create("p", "muted", `Anggota: ${event.memberAfter.map((id) => technicians[id]).join(", ")}`));
        return li;
      }));
      $("so-history-empty").hidden = w.history.length > 0;
      $("so-closure-note").textContent = "Penyerahan ke kasir terpisah dari progres. Ini belum invoice atau pembayaran dan tidak mengurangi stok.";
      fillActions(preserve);
      actual.render();
      handoff.render();
    }

    function leave() {
      if (!pending && !actual.isDirty() && !handoff.isDirty()) return true;
      if (!window.confirm("Isian tindakan atau realisasi SO belum disimpan. Tinggalkan formulir dan buang isian lokal? Data tersimpan tidak akan berubah.")) return false;
      pending = false;
      actual.discard();
      handoff.discard();
      if (current()) { fillActions(); statusMessage("Isian lokal dibersihkan. Status tersimpan tidak berubah."); }
      return true;
    }

    function open(orderId, fromEstimate = false) {
      if (activeId !== orderId && !leave()) return;
      if (!api.state()?.serviceOrders?.some((o) => o.id === orderId)) return;
      if (!api.show("so")) return;
      const preserve = activeId === orderId && pending;
      activeId = orderId;
      openingFromEstimate = fromEstimate;
      renderDetail(preserve);
      if (!pending) statusMessage("Belum ada tindakan baru");
    }

    function applyAction(event) {
      event.preventDefault();
      if (applying || !current()) return;
      const order = current();
      const input = local();
      applying = true;
      try {
        clearValidation();
        if (window.POSHandoff.queued(order)) throw invalid("SO dalam antrean kasir. Owner harus menariknya sebelum mengubah progres.", "so-action");
        if (window.POSInvoices.finalFor(api.state(), order.id)) throw invalid("Invoice sudah final. Progres SO terkunci; koreksi harga melalui invoice Owner.", "so-action");
        const before = workflow(order);
        const at = new Date().toISOString();
        const after = apply(before, input.action, input.technicianId, input.reason, api.role(), at, ["assigned", "started"].includes(input.action) ? input.memberIds : before.memberIds || []);
        if (input.action === "completed") {
          if (!order.realization) throw invalid("Isi alasan pencatatan, lalu pilih Simpan realisasi sebelum menandai SO selesai. Estimasi belum menjadi realisasi tersimpan.", "actual-reason");
          if (actual.isDirty()) throw invalid("Simpan perubahan realisasi melalui Simpan realisasi sebelum menandai SO selesai. Isian lokal belum menjadi biaya akhir tersimpan.", "actual-reason");
        }
        if (["completed", "cancelled", "reopened"].includes(input.action) && !window.confirm(`${actions[input.action]} untuk SO ini? ${input.action === "completed" ? "Progres dan realisasi akan terkunci bagi Teknisi. Hanya Owner dapat membuka kembali dengan alasan. " : ""}Estimasi tetap utuh; tindakan ini tidak menerbitkan invoice atau mengubah pembayaran.`)) return;
        after.history.push({ id: crypto.randomUUID(), action: input.action, from: before.status, to: after.status, technicianBefore: before.technicianId, technicianAfter: after.technicianId, reason: input.reason.trim(), actor: api.role(), at });
        if ((before.memberIds || []).length || (after.memberIds || []).length) Object.assign(after.history.at(-1), { memberBefore: before.memberIds || [], memberAfter: after.memberIds || [] });
        const candidate = { ...api.state(), serviceOrders: api.state().serviceOrders.map((o) => o.id === activeId ? { ...o, workflow: after } : o) };
        if (!api.persist(candidate)) { statusMessage("Belum tersimpan. Isian tindakan tetap ada; belum ada status atau riwayat baru.", true); return; }
        pending = false;
        $("so-action-error").textContent = "";
        api.refresh(); renderDetail();
        $("so-action").value = ""; updateControls();
        statusMessage("Perubahan progres tersimpan di perangkat ini");
        api.announce(`${actions[input.action]} tersimpan. Status: ${statuses[after.status]}. Estimasi tidak berubah.`);
        if (!$("so-apply-action").hidden) $("so-action").focus();
        else { $("so-heading").tabIndex = -1; $("so-heading").focus(); }
      } catch (error) {
        $("so-action-error").textContent = error.message;
        if (error.field === "actual-reason") $("actual-error").textContent = error.message;
        const field = $(error.field || "so-action");
        field.setAttribute("aria-invalid", "true");
        if (!field.disabled) field.focus();
        else focusAction();
      } finally { applying = false; }
    }

    $("order-search").addEventListener("input", renderList);
    $("order-filter").addEventListener("change", renderList);
    $("orders-to-diagnoses").addEventListener("click", api.diagnoses);
    $("so-progress-form").addEventListener("submit", applyAction);
    $("so-progress-form").addEventListener("input", () => {
      pending = true; updateControls();
      clearValidation(); $("so-clear-action").hidden = false;
      statusMessage("Isian tindakan belum diterapkan");
    });
    $("so-action").addEventListener("change", () => {
      if (!["assigned", "started"].includes($("so-action").value) && current()) $("so-technician-select").value = workflow(current()).technicianId || "";
      updateControls();
    });
    $("so-clear-action").addEventListener("click", () => {
      pending = false; clearValidation(); fillActions(); focusAction();
      statusMessage("Isian lokal dibersihkan. Status tersimpan tidak berubah.");
    });
    $("so-back-list").addEventListener("click", () => { if (api.show("orders")) renderList(); });
    $("back-from-so").addEventListener("click", () => {
      if (!current()) return;
      if (openingFromEstimate) { if (leave()) api.diagnosis(current().registrationId); }
      else if (api.show("orders")) renderList();
    });
    $("so-open-registration").addEventListener("click", () => { if (current() && leave()) api.registration(current().registrationId); });
    $("so-open-diagnosis").addEventListener("click", () => { if (current() && leave()) api.diagnosis(current().registrationId); });
    return { open, renderList, leave, isDirty: () => pending || actual.isDirty() || handoff.isDirty(), conflict: () => { actual.conflict(); handoff.conflict(); }, roleChanged: () => { if (current()) { fillActions(true); actual.roleChanged(); handoff.render(); } }, onReload: () => {
      renderList();
      if (current()) {
        renderDetail(pending);
        statusMessage(pending ? "Data terbaru dimuat. Isian tindakan dipertahankan; periksa lalu terapkan kembali secara eksplisit." : "Data terbaru dimuat; tidak ada tindakan yang dijalankan otomatis.");
      }
    } };
  }

  window.POSOrders = Object.freeze({ validate, createFeature });
})();
