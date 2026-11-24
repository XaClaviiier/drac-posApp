"use strict";

(() => {
  const items = window.POSItems, money = items.money, clone = (value) => structuredClone(value);
  const same = (a, b) => JSON.stringify(a) === JSON.stringify(b);
  const final = (invoice) => Boolean(invoice?.history?.some((event) => event.kind === "issued"));
  const forOrder = (store, id) => (store?.invoices || []).find((invoice) => invoice.orderId === id);
  const finalFor = (store, id) => final(forOrder(store, id));
  const cashier = (role) => ["Owner", "Kasir"].includes(role);
  const amount = (value) => Number.isSafeInteger(value) && value >= 0;
  const methods = { cash: "Tunai", transfer: "Transfer manual", "gateway-demo": "Gateway — SIMULASI" };
  const snapshot = (invoice) => invoice.history.findLast((event) => event.kind !== "payment");
  function summary(invoice) {
    const total = items.totals(snapshot(invoice).items).total;
    const paid = invoice.history.filter((event) => event.kind === "payment").reduce((sum, event) => sum + event.amount, 0);
    return { total, paid, balance: Math.max(0, total - paid), overpaid: Math.max(0, paid - total), status: final(invoice) ? (paid >= total ? "Lunas" : "Belum Lunas") : "Belum diterbitkan" };
  }
  const rowsMatch = (a, b) => a.length === b.length && a.every((row, index) => same({ ...row, unitPrice: 0 }, { ...b[index], unitPrice: 0 }));
  function source(order, handoffId) {
    const index = order.handoff?.history.findIndex((event) => event.id === handoffId) ?? -1;
    if (index < 0) return null;
    const event = order.handoff.history[index];
    if (event.state !== "queued") return null;
    return { event, items: order.realization.history[event.realizationRevision - 1].after, end: order.handoff.history[index + 1]?.at };
  }
  const fresh = (store, invoice) => {
    const order = store.serviceOrders.find((order) => order.id === invoice.orderId);
    return window.POSHandoff.queued(order) && order.handoff.history.at(-1).id === snapshot(invoice).handoffId;
  };

  function validate(store) {
    if (!Object.hasOwn(store, "invoices")) return;
    const fail = () => { throw new Error("invalid-storage"); };
    if (!Array.isArray(store.invoices) || store.invoices.length > 10000) fail();
    const ids = new Set(), references = new Set(), orders = new Set();
    for (const invoice of store.invoices) {
      if (!invoice || typeof invoice.id !== "string" || !invoice.id || invoice.id.length > 100 || ids.has(invoice.id) || typeof invoice.reference !== "string" || !invoice.reference || invoice.reference.length > 100 || references.has(invoice.reference) || orders.has(invoice.orderId) || !Array.isArray(invoice.history) || !invoice.history.length || invoice.history.length > 200) fail();
      const order = store.serviceOrders.find((order) => order.id === invoice.orderId);
      if (!order) fail();
      let current = null, issued = false, revision = 0, paid = 0n, previousAt = Date.parse(order.createdAt);
      const events = new Set();
      for (const event of invoice.history) {
        if (!event || typeof event.id !== "string" || !event.id || event.id.length > 100 || events.has(event.id) || typeof event.at !== "string" || !Number.isFinite(Date.parse(event.at)) || Date.parse(event.at) < previousAt || !["Owner", "Kasir", "Teknisi"].includes(event.actor)) fail();
        previousAt = Date.parse(event.at); events.add(event.id);
        if (event.kind === "payment") {
          if (!issued || !cashier(event.actor) || event.invoiceRevision !== revision || !Object.hasOwn(methods, event.method) || !amount(event.amount) || event.amount <= 0 || !amount(event.received) || typeof event.reference !== "string" || event.reference.length > 100 || typeof event.gatewayAcknowledged !== "boolean") fail();
          const due = BigInt(items.totals(current.items).total) - paid;
          if (BigInt(event.amount) !== due || (event.method === "cash" ? event.received < event.amount : event.received !== event.amount) || (event.method === "transfer" && !event.reference.trim()) || (event.method === "gateway-demo" && !event.gatewayAcknowledged)) fail();
          paid += BigInt(event.amount);
          if (paid > BigInt(Number.MAX_SAFE_INTEGER)) fail();
          continue;
        }
        if (!["created", "price", "rebased", "issued", "corrected"].includes(event.kind) || !Array.isArray(event.items) || event.items.length > 100 || !items.totals(event.items) || event.items.some((row) => typeof row.quantity !== "string" || items.canonical(row.quantity, row.unit) !== row.quantity || typeof row.unitPrice !== "number" || !items.integer(row.unitPrice)) || typeof event.reason !== "string" || event.reason.length > 500) fail();
        const origin = source(order, event.handoffId);
        if (!origin || Date.parse(event.at) < Date.parse(origin.event.at) || (origin.end && Date.parse(event.at) > Date.parse(origin.end))) fail();
        if (event.kind === "created") {
          if (current || !cashier(event.actor) || !same(event.items, origin.items) || event.at !== invoice.createdAt || event.actor !== invoice.createdBy) fail();
        } else {
          if (!current) fail();
          if (event.kind === "rebased") {
            if (issued || event.actor !== "Owner" || !event.reason.trim() || event.handoffId === current.handoffId || !same(event.items, origin.items) || order.handoff.history.findIndex((e) => e.id === event.handoffId) <= order.handoff.history.findIndex((e) => e.id === current.handoffId)) fail();
          } else if (event.kind === "issued") {
            if (issued || !cashier(event.actor) || event.handoffId !== current.handoffId || !same(event.items, current.items)) fail();
            issued = true;
          } else if (event.actor !== "Owner" || !event.reason.trim() || (event.kind === "price" ? issued : !issued) || event.handoffId !== current.handoffId || !rowsMatch(event.items, current.items) || same(event.items, current.items)) fail();
        }
        current = event; revision++;
      }
      if (!current || invoice.history[0].kind !== "created" || (issued && (!window.POSHandoff.queued(order) || order.handoff.history.at(-1).id !== current.handoffId))) fail();
      ids.add(invoice.id); references.add(invoice.reference); orders.add(invoice.orderId);
    }
  }

  function assertAppend(previous, candidate) {
    const before = previous?.invoices || [], after = candidate.invoices || [];
    const fail = () => { throw new Error("invalid-storage"); };
    if (!Array.isArray(after) || after.length < before.length || after.length > before.length + 1) fail();
    for (const old of before) {
      const next = after.find((invoice) => invoice.id === old.id);
      if (!next || !["id", "reference", "orderId", "createdAt", "createdBy"].every((key) => next[key] === old[key]) || !Array.isArray(next.history) || next.history.length < old.history.length || next.history.length > old.history.length + 1 || !same(next.history.slice(0, old.history.length), old.history)) fail();
    }
  }

  function createFeature(api) {
    const $ = (id) => document.getElementById(id), create = api.create;
    let activeId = null, edited = [], editDirty = false, payDirty = false, basis = "", stale = false, storageConflict = false, saving = false;
    const current = () => (api.state()?.invoices || []).find((invoice) => invoice.id === activeId);
    const isDirty = () => editDirty || payDirty;
    function guardPrint() {
      const eligible = current() && final(current()) && !stale && !storageConflict && !isDirty() && api.isCurrent();
      document.body.classList.toggle("invoice-print-blocked", !eligible);
      $("invoice-print").disabled = !eligible;
      return Boolean(eligible);
    }
    const error = (message, id = "invoice-error") => { $("invoice-error").textContent = message; const el = $(id); if (id === "invoice-error") el.tabIndex = -1; el.focus(); };
    function clearPaymentError() {
      $("payment-error").textContent = "";
      $("payment-form").querySelectorAll("[aria-invalid]").forEach((field) => field.removeAttribute("aria-invalid"));
    }
    function paymentError(message, id) {
      clearPaymentError();
      const field = $(id), container = field.closest(".field") || field.closest(".approval-check");
      container.after($("payment-error"));
      $("payment-error").textContent = message;
      field.setAttribute("aria-invalid", "true");
      field.focus();
    }
    function renderPaymentPreview() {
      const invoice = current(), balance = invoice ? summary(invoice).balance : null;
      const raw = $("payment-received").value, received = /^\d+$/.test(raw) && amount(Number(raw)) ? Number(raw) : null, method = $("payment-method").value;
      const valid = balance > 0 && received !== null && Object.hasOwn(methods, method) && (method === "cash" ? received >= balance : received === balance);
      $("payment-due").textContent = balance === null ? "—" : money.format(balance);
      $("payment-tendered").textContent = received === null ? "—" : money.format(received);
      $("payment-change").textContent = valid ? money.format(received - balance) : "—";
      $("payment-preview-note").textContent = valid ? (method === "cash" ? "Periksa uang diterima dan kembalian sebelum mencatat pembayaran." : "Non-tunai harus tepat sebesar sisa tagihan; tidak ada kembalian.") : !Object.hasOwn(methods, method) ? "Pilih metode pembayaran yang tersedia." : method === "cash" ? "Isi rupiah bulat minimal sebesar sisa tagihan untuk melihat kembalian." : "Isi rupiah bulat tepat sebesar sisa tagihan. Non-tunai tidak memiliki kembalian.";
    }
    const online = () => { if (navigator.onLine) return true; error("Perubahan invoice dan pembayaran memerlukan koneksi online. Isian tetap ada; prototype ini tidak memverifikasi server."); return false; };
    function clear() {
      editDirty = false; payDirty = false; stale = false;
      $("invoice-reason").value = ""; $("payment-received").value = ""; $("payment-reference").value = ""; $("gateway-ack").checked = false;
      $("invoice-error").textContent = "";
      clearPaymentError();
    }
    function renderList() {
      const query = $("invoice-search").value.toLocaleLowerCase("id-ID").replace(/\s/g, "");
      const all = api.state()?.invoices || [];
      const list = all.filter((invoice) => {
        const order = api.state().serviceOrders.find((o) => o.id === invoice.orderId), r = api.state().records.find((r) => r.id === order.registrationId), s = summary(invoice);
        return ($("invoice-filter").value === "all" || ($("invoice-filter").value === "draft" ? !final(invoice) : final(invoice) && ($("invoice-filter").value === "paid" ? s.balance === 0 : s.balance > 0))) && (!query || [invoice.reference, r.plate, r.customer].some((value) => value.toLocaleLowerCase("id-ID").replace(/\s/g, "").includes(query)));
      });
      $("invoice-list").replaceChildren(); $("invoice-count").textContent = `${list.length} dari ${all.length} invoice`; $("invoice-empty").hidden = list.length > 0;
      $("invoice-empty-note").textContent = all.length ? "Ubah pencarian atau filter." : "Buka SO yang sudah diserahkan pada Antrean kasir untuk membuat invoice draf.";
      for (const invoice of list) {
        const order = api.state().serviceOrders.find((o) => o.id === invoice.orderId), r = api.state().records.find((r) => r.id === order.registrationId), s = summary(invoice);
        const row = create("article", "record"), identity = create("div", "record-vehicle"), detail = create("div", "record-complaint"), meta = create("div", "record-meta");
        identity.append(create("strong", "plate", r.plate), create("span", "record-customer", r.customer)); detail.append(create("strong", "", invoice.reference), create("p", "muted", order.reference));
        meta.append(create("span", "status-label", final(invoice) ? `Final · ${s.status}` : "Draf"), create("span", "", money.format(s.total)));
        const button = create("button", "record-action", "Buka invoice"); button.setAttribute("aria-label", `Buka invoice ${invoice.reference} · ${r.plate}`); button.addEventListener("click", () => open(order.id)); row.append(identity, detail, meta, button); $("invoice-list").append(row);
      }
    }
    function renderReceipt(invoice, r, s) {
      const receipt = $("invoice-receipt"); receipt.replaceChildren(); receipt.hidden = !final(invoice);
      if (!final(invoice)) return;
      receipt.append(create("h2", "", "NOTA SIMULASI — BUKAN BUKTI TRANSAKSI NYATA"), create("p", "", invoice.reference), create("p", "", `${r.plate} · ${r.customer}`), create("p", "", `${new Date(snapshot(invoice).at).toLocaleString("id-ID")} · revisi ${invoice.history.filter((e) => e.kind !== "payment").length}`));
      for (const item of snapshot(invoice).items) { const row = create("div", "receipt-item"); row.append(create("span", "", `${item.label} · ${item.quantity.replace(".", ",")} ${item.unit} × ${money.format(item.unitPrice)}`), create("strong", "", money.format(items.subtotal(item)))); receipt.append(row); }
      receipt.append(create("p", "receipt-total", `Total ${money.format(s.total)} · ${s.status}`));
      if (s.paid) receipt.append(create("p", "", `Pembayaran tercatat (simulasi): ${money.format(s.paid)}`));
      if (s.balance) receipt.append(create("p", "", `Sisa tagihan ${money.format(s.balance)}`));
      if (s.overpaid) receipt.append(create("p", "", `Kelebihan bayar ${money.format(s.overpaid)}. Belum ada refund.`));
      receipt.append(create("p", "muted", "Data contoh. Bukan dokumen fiskal atau konfirmasi gateway nyata."));
    }
    function render() {
      const invoice = current();
      if (!invoice) { $("invoice-receipt").replaceChildren(); $("invoice-items").replaceChildren(); $("invoice-history").replaceChildren(); $("payment-history").replaceChildren(); return; }
      const serialized = JSON.stringify(invoice);
      if (!isDirty()) { basis = serialized; stale = false; edited = clone(snapshot(invoice).items); } else if (basis !== serialized) stale = true;
      const order = api.state().serviceOrders.find((o) => o.id === invoice.orderId), r = api.state().records.find((r) => r.id === order.registrationId), s = summary(invoice), issued = final(invoice), sourceFresh = fresh(api.state(), invoice);
      $("invoice-reference").textContent = `${invoice.reference} · ${order.reference}`; $("invoice-identity").textContent = `${r.plate} · ${r.customer}`;
      $("invoice-state").textContent = issued ? "Final" : "Draf"; $("invoice-paid-state").textContent = s.status;
      $("invoice-total").textContent = money.format(s.total); $("invoice-paid").textContent = money.format(s.paid); $("invoice-balance").textContent = money.format(s.balance);
      $("invoice-overpaid").textContent = s.overpaid ? `Kelebihan bayar ${money.format(s.overpaid)}. Pembayaran tidak diubah dan tidak ada refund otomatis.` : "";
      $("invoice-network").textContent = navigator.onLine ? "Simulasi lokal. Invoice/pembayaran di sini bukan transaksi atau verifikasi server nyata." : "Offline: perubahan invoice dan pembayaran dinonaktifkan. Isian tetap di halaman.";
      $("invoice-source-note").textContent = sourceFresh ? "Rincian berasal dari realisasi SO tersimpan. Harga invoice tidak mengubah SO atau katalog." : "Penyerahan SO sudah berubah/ditarik. Owner perlu menyerahkan SO ulang lalu memuat realisasi terbaru sebelum menerbitkan.";
      const editable = api.role() === "Owner" && sourceFresh && !stale;
      $("invoice-items").replaceChildren();
      edited.forEach((item, index) => {
        const row = create("article", "estimate-item"); row.append(create("h3", "", item.label), create("p", "muted", `${item.quantity.replace(".", ",")} ${item.unit} · qty mengikuti realisasi SO`));
        const label = create("label", "field", "Harga satuan (Rp)"), input = create("input"); input.id = `invoice-price-${index}`; input.name = "invoicePrice"; input.type = "text"; input.inputMode = "numeric"; input.maxLength = 10; input.value = String(item.unitPrice); input.disabled = !editable; input.setAttribute("aria-describedby", "invoice-error");
        input.addEventListener("input", () => { edited[index].unitPrice = input.value; editDirty = true; $("invoice-reset").hidden = false; $("invoice-error").textContent = ""; guardPrint(); });
        label.htmlFor = input.id; label.append(input); row.append(label, create("p", "item-subtotal", items.subtotal(item) === null ? "Periksa harga" : `Subtotal ${money.format(items.subtotal(item))}`)); $("invoice-items").append(row);
      });
      $("invoice-edit-section").hidden = api.role() !== "Owner";
      $("invoice-reason").disabled = api.role() !== "Owner" || stale; $("invoice-save-price").disabled = !editable || !navigator.onLine; $("invoice-save-price").textContent = issued ? "Simpan koreksi harga" : "Simpan harga draf";
      $("invoice-issue").hidden = issued || !cashier(api.role()); $("invoice-issue").disabled = !sourceFresh || stale || !navigator.onLine;
      $("invoice-rebase").hidden = issued || api.role() !== "Owner" || sourceFresh; $("invoice-rebase").disabled = !window.POSHandoff.queued(order) || stale || !navigator.onLine;
      $("invoice-print").disabled = !issued || stale;
      $("invoice-reset").hidden = !isDirty();
      $("payment-section").hidden = !issued || !cashier(api.role()) || s.balance <= 0; $("payment-save").disabled = !issued || s.balance <= 0 || stale || storageConflict || !navigator.onLine;
      $("gateway-note").hidden = $("payment-method").value !== "gateway-demo";
      renderPaymentPreview();
      $("payment-history").replaceChildren();
      if (cashier(api.role())) for (const event of invoice.history.filter((e) => e.kind === "payment")) {
        const row = create("li", "progress-event"); row.append(create("strong", "", `${methods[event.method]} · ${money.format(event.amount)}`), create("p", "", `${event.actor} (simulasi) · ${new Date(event.at).toLocaleString("id-ID")}`), create("p", "", `Uang diterima ${money.format(event.received)} · kembalian ${money.format(event.received - event.amount)}`)); if (event.reference) row.append(create("p", "preserve-text", event.reference)); $("payment-history").append(row);
      }
      $("invoice-log").hidden = api.role() !== "Owner"; $("invoice-history").replaceChildren();
      if (api.role() === "Owner") for (const event of invoice.history.filter((e) => e.kind !== "payment")) {
        const li = create("li", "progress-event"); li.append(create("strong", "", ({ created: "Draf dibuat", price: "Harga draf diubah", rebased: "Realisasi dimuat ulang", issued: "Invoice diterbitkan", corrected: "Harga final dikoreksi" })[event.kind]), create("p", "", `${event.actor} · ${new Date(event.at).toLocaleString("id-ID")} · ${money.format(items.totals(event.items).total)}`));
        if (event.reason) li.append(create("p", "preserve-text", event.reason));
        for (const item of event.items) li.append(create("p", "", `${item.label}: ${item.quantity} ${item.unit} × ${money.format(item.unitPrice)}`)); $("invoice-history").append(li);
      } else $("invoice-log").open = false;
      renderReceipt(invoice, r, s);
      guardPrint();
      if (stale) $("invoice-error").textContent = "Invoice berubah. Isian tetap ada; bersihkan isian lokal dan periksa versi terbaru sebelum menyimpan.";
    }
    function leave() {
      if (!isDirty()) return true;
      if (!window.confirm("Isian harga atau pembayaran belum tersimpan. Tinggalkan dan buang isian lokal? Data tersimpan tetap utuh.")) return false;
      clear(); return true;
    }
    function open(orderId) {
      let invoice = forOrder(api.state(), orderId);
      if ((!invoice || invoice.id !== activeId) && !leave()) return false;
      if (!invoice) {
        if (!cashier(api.role()) || !navigator.onLine || api.orderDirty()) { api.announce("Invoice draf hanya dibuat Kasir/Owner saat online setelah isian SO tersimpan atau dibersihkan."); return false; }
        const order = api.state().serviceOrders.find((o) => o.id === orderId);
        if (!window.POSHandoff.queued(order)) return false;
        const event = order.handoff.history.at(-1), at = new Date().toISOString();
        invoice = { id: crypto.randomUUID(), reference: `INV-CONTOH-${crypto.randomUUID().slice(0, 8).toUpperCase()}`, orderId, createdAt: at, createdBy: api.role(), history: [{ id: crypto.randomUUID(), kind: "created", at, actor: api.role(), handoffId: event.id, items: clone(source(order, event.id).items), reason: "" }] };
        if (!api.persist({ ...api.state(), invoices: [...(api.state().invoices || []), invoice] })) return false;
        api.refresh();
      }
      if (!api.show("invoice")) return false;
      if (activeId !== invoice.id) { activeId = invoice.id; clear(); }
      clearPaymentError();
      render();
      return true;
    }
    function append(event) {
      const invoice = current();
      if (!api.persist({ ...api.state(), invoices: api.state().invoices.map((value) => value.id === invoice.id ? { ...value, history: [...value.history, event] } : value) })) { error("Belum tersimpan. Isian tetap ada; Muat data terbaru tidak menjalankan ulang aksi."); return false; }
      clear(); api.refresh(); render(); $("invoice-state").tabIndex = -1; $("invoice-state").focus(); api.announce("Perubahan invoice tersimpan di perangkat ini — simulasi."); return true;
    }
    function act(kind) {
      if (saving || !current()) return;
      $("invoice-error").textContent = "";
      if (kind === "payment") clearPaymentError();
      const invoice = current(), issued = final(invoice), s = summary(invoice), owner = api.role() === "Owner";
      if ((["price", "corrected", "rebased"].includes(kind) && !owner) || (["issued", "payment"].includes(kind) && !cashier(api.role()))) { error("Peran tidak mengizinkan tindakan invoice ini."); return; }
      if (!online()) return;
      if (stale || storageConflict || basis !== JSON.stringify(invoice)) { error("Basis invoice berubah. Bersihkan isian lalu muat versi terbaru."); return; }
      if (invoice.history.length >= 200) { error("Demo dibatasi 200 peristiwa invoice; riwayat tidak dipangkas."); return; }
      if ((kind === "issued" && issued) || (kind === "price" && issued) || (["payment", "corrected"].includes(kind) && !issued) || (kind === "rebased" && issued)) { error("Status invoice tidak mengizinkan tindakan ini."); return; }
      const order = api.state().serviceOrders.find((o) => o.id === invoice.orderId);
      if (kind !== "rebased" && !fresh(api.state(), invoice)) { error("Penyerahan SO berubah. Owner perlu memuat realisasi terbaru."); return; }
      if ((["issued", "rebased"].includes(kind) && (payDirty || editDirty && kind !== "rebased")) || (kind === "payment" && editDirty) || (["price", "corrected"].includes(kind) && payDirty)) { error("Simpan atau bersihkan isian harga/pembayaran dahulu; aksi tidak menyimpan isian lain otomatis."); return; }
      const reason = $("invoice-reason").value.trim();
      let event = { id: crypto.randomUUID(), kind, at: new Date().toISOString(), actor: api.role(), handoffId: snapshot(invoice).handoffId, items: clone(snapshot(invoice).items), reason: "" };
      if (["price", "corrected", "rebased"].includes(kind)) {
        if (!reason || reason.length > 500) { error("Isi alasan perubahan, maksimal 500 karakter.", "invoice-reason"); return; }
        event.reason = reason;
        if (kind === "rebased") {
          if (!window.POSHandoff.queued(order) || fresh(api.state(), invoice)) { error("Belum ada penyerahan SO baru untuk dimuat."); return; }
          event.handoffId = order.handoff.history.at(-1).id; event.items = clone(source(order, event.handoffId).items);
        } else {
          const invalidIndex = edited.findIndex((row) => !items.integer(row.unitPrice));
          if (invalidIndex >= 0) { error("Harga harus rupiah bulat 0–1.000.000.000.", `invoice-price-${invalidIndex}`); return; }
          event.items = edited.map((row) => ({ ...row, unitPrice: Number(row.unitPrice) }));
          if (!items.totals(event.items)) { error("Total melampaui kapasitas angka demo."); return; }
          if (same(event.items, snapshot(invoice).items)) { error("Belum ada perubahan harga."); return; }
        }
      }
      if (kind === "payment") {
        const raw = $("payment-received").value, method = $("payment-method").value, reference = $("payment-reference").value.trim();
        if (s.balance <= 0 || !/^\d+$/.test(raw) || !amount(Number(raw)) || (method === "cash" ? Number(raw) < s.balance : Number(raw) !== s.balance)) { paymentError("Bayar seluruh sisa tagihan. Tunai boleh lebih untuk kembalian; non-tunai harus tepat.", "payment-received"); return; }
        if (!Object.hasOwn(methods, method)) { paymentError("Pilih metode pembayaran yang tersedia.", "payment-method"); return; }
        if (reference.length > 100 || (method === "transfer" && !reference)) { paymentError("Isi referensi transfer manual, maksimal 100 karakter.", "payment-reference"); return; }
        if (method === "gateway-demo" && !$("gateway-ack").checked) { paymentError("Centang pengakuan simulasi gateway. Ini bukan verifikasi pembayaran nyata.", "gateway-ack"); return; }
        event = { id: event.id, kind, at: event.at, actor: event.actor, invoiceRevision: invoice.history.filter((e) => e.kind !== "payment").length, method, amount: s.balance, received: Number(raw), reference, gatewayAcknowledged: method === "gateway-demo" && $("gateway-ack").checked };
      }
      if (kind === "payment") {
        const registration = api.state().records.find((record) => record.id === order.registrationId);
        if (!window.confirm(`Catat pembayaran penuh untuk ${invoice.reference} · ${registration.plate}?\nMetode: ${methods[event.method]}.\nPembayaran untuk sisa tagihan: ${money.format(event.amount)}.\nUang diterima: ${money.format(event.received)}.\nKembalian: ${money.format(event.received - event.amount)}.\nSIMULASI, bukan transaksi nyata.`)) return;
      } else if (["issued", "corrected", "rebased"].includes(kind) && !window.confirm(`${kind === "issued" ? "Terbitkan invoice final" : kind === "rebased" ? "Ganti rincian draf dengan realisasi baru" : "Koreksi harga final tanpa mengubah pembayaran"} untuk ${invoice.reference}? SIMULASI, bukan transaksi nyata.`)) return;
      saving = true; try { append(event); } finally { saving = false; }
    }
    $("invoice-price-form").addEventListener("submit", (event) => { event.preventDefault(); act(final(current()) ? "corrected" : "price"); });
    $("invoice-reason").addEventListener("input", () => { editDirty = true; $("invoice-reset").hidden = false; guardPrint(); });
    $("invoice-issue").addEventListener("click", () => act("issued")); $("invoice-rebase").addEventListener("click", () => act("rebased"));
    $("payment-form").addEventListener("submit", (event) => { event.preventDefault(); act("payment"); });
    function paymentInput() { payDirty = true; $("invoice-reset").hidden = false; clearPaymentError(); renderPaymentPreview(); guardPrint(); }
    $("payment-form").addEventListener("input", paymentInput);
    $("payment-method").addEventListener("change", () => { $("gateway-ack").checked = false; $("gateway-note").hidden = $("payment-method").value !== "gateway-demo"; paymentInput(); });
    $("invoice-reset").addEventListener("click", () => { if (!leave()) return; clear(); render(); });
    $("invoice-print").addEventListener("click", () => { if (!guardPrint()) { error("Cetak hanya invoice final tersimpan. Simpan atau bersihkan isian dan muat versi terbaru."); return; } render(); window.print(); });
    $("invoice-search").addEventListener("input", renderList); $("invoice-filter").addEventListener("change", renderList);
    window.addEventListener("online", render); window.addEventListener("offline", render);
    window.addEventListener("beforeprint", guardPrint);
    return { open, renderList, leave, isDirty, activeOrder: () => current()?.orderId, roleChanged: render, conflict: () => { storageConflict = true; stale = true; $("gateway-ack").checked = false; guardPrint(); }, onReload: () => { storageConflict = false; renderList(); if (activeId) render(); } };
  }
  window.POSInvoices = Object.freeze({ validate, assertAppend, forOrder, finalFor, summary, snapshot, isFresh: fresh, createFeature });
})();
