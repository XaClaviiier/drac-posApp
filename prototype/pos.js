"use strict";

(() => {
  function createFeature(api) {
    const $ = (id) => document.getElementById(id), create = api.create, money = window.POSItems.money;
    let selected = null;
    const access = () => ["Owner", "Kasir"].includes(api.role());

    function entries() {
      const store = api.state();
      if (!store || !api.canRead()) return [];
      return (store.serviceOrders || []).flatMap((order) => {
        const invoice = window.POSInvoices.forOrder(store, order.id), registration = store.records.find((r) => r.id === order.registrationId);
        if (!invoice && !window.POSHandoff.queued(order)) return [];
        const summary = invoice ? window.POSInvoices.summary(invoice) : null;
        const final = invoice && window.POSInvoices.finalFor(store, order.id);
        const stage = !invoice ? "ready" : !final ? "draft" : summary.balance ? "unpaid" : "paid";
        return [{ order, invoice, registration, stage, amount: summary ? final ? summary.balance : summary.total : window.POSItems.totals(order.realization.items).total, stale: invoice && !final && !window.POSInvoices.isFresh(store, invoice), at: invoice?.createdAt || order.handoff.history.at(-1).at }];
      }).sort((a, b) => a.at.localeCompare(b.at) || a.order.reference.localeCompare(b.order.reference));
    }

    function preview() {
      $("pos-preview-items").replaceChildren();
      $("pos-create-invoice").hidden = true; $("pos-open-order").hidden = true;
      $("pos-preview-identity").textContent = ""; $("pos-preview-reference").textContent = ""; $("pos-preview-total").textContent = "";
      $("pos-preview-heading").textContent = "Pilih transaksi";
      $("pos-preview-note").textContent = "Pilih kendaraan di antrean untuk memeriksa rincian dan melanjutkan pembayaran.";
      if (!access() || !api.canRead() || !selected) return;
      const store = api.state(), order = store.serviceOrders?.find((o) => o.id === selected);
      if (!order) { $("pos-preview-note").textContent = "SO tidak tersedia pada data terbaru. Pilih transaksi lain setelah memuat ulang."; return; }
      const r = store.records.find((r) => r.id === order.registrationId), invoice = window.POSInvoices.forOrder(store, order.id);
      const ready = window.POSHandoff.queued(order);
      const rows = invoice ? window.POSInvoices.snapshot(invoice).items : order.realization?.items || [];
      $("pos-preview-heading").textContent = invoice ? "Invoice sudah tersedia" : "Periksa realisasi";
      $("pos-preview-identity").textContent = `${r.plate} · ${r.customer}`;
      $("pos-preview-reference").textContent = `${order.reference}${invoice ? ` · ${invoice.reference}` : ""}`;
      $("pos-preview-total").textContent = money.format(window.POSItems.totals(rows).total);
      $("pos-preview-note").textContent = invoice ? "Buka invoice tersimpan untuk menerbitkan, membayar atau mencetak sesuai statusnya." : ready ? "Realisasi sudah diserahkan. Periksa rincian lalu buat invoice draf secara eksplisit." : "SO tidak lagi siap ditagih. Minta Owner memeriksa penyerahan terbaru.";
      for (const item of rows) {
        const row = create("div", "so-item"); row.append(create("strong", "", item.label), create("span", "muted", `${item.quantity.replace(".", ",")} ${item.unit} × ${money.format(item.unitPrice)}`), create("strong", "", money.format(window.POSItems.subtotal(item)))); $("pos-preview-items").append(row);
      }
      $("pos-open-order").hidden = false;
      $("pos-create-invoice").hidden = !invoice && !ready;
      $("pos-create-invoice").disabled = !invoice && !api.canWrite();
      $("pos-create-invoice").textContent = invoice ? "Buka invoice" : "Buat invoice draf";
    }

    function render() {
      const allowed = access();
      $("nav-cashier").hidden = !allowed; $("cashier-list").replaceChildren();
      if (!allowed) { selected = null; $("cashier-count").textContent = ""; $("pos-invoice-note").textContent = ""; $("pos-preview-context").textContent = ""; preview(); return; }
      const all = entries(), query = $("cashier-search").value.toLocaleLowerCase("id-ID").replace(/\s+/g, ""), filter = $("pos-stage").value;
      const shown = all.filter((entry) => (filter === "all" || (filter === "pending" ? entry.stage !== "paid" : entry.stage === filter)) && ($("cashier-filter").value === "all" || entry.order.workflow?.status === $("cashier-filter").value) && (!query || [entry.registration.plate, entry.registration.customer, entry.order.reference, entry.invoice?.reference || ""].some((value) => value.toLocaleLowerCase("id-ID").replace(/\s+/g, "").includes(query))));
      $("cashier-count").textContent = api.canRead() ? `${shown.length} transaksi` : "Data belum tersedia";
      $("cashier-empty").hidden = shown.length > 0;
      $("cashier-empty").querySelector("h3").textContent = !api.canRead() ? "Data belum tersedia" : !all.length ? "Belum ada transaksi menunggu" : "Tidak ada hasil";
      $("cashier-empty-note").textContent = !api.canRead() ? "Periksa pesan penyimpanan dan muat data terbaru." : !all.length ? "SO yang diserahkan dan invoice belum lunas akan muncul di sini." : "Ubah pencarian atau filter tagihan/pekerjaan. Detail terpilih tetap terbuka.";
      for (const entry of shown) {
        const row = create("article", "record pos-record"), button = create("button", `pos-choice${selected === entry.order.id ? " is-selected" : ""}`);
        const status = entry.stale ? "Perlu Owner" : ({ ready: "Siap ditagih", draft: "Invoice draf", unpaid: "Belum Lunas", paid: "Lunas" })[entry.stage];
        button.setAttribute("aria-pressed", String(selected === entry.order.id));
        button.setAttribute("aria-label", `Pilih transaksi ${entry.registration.plate}, ${status}`);
        button.append(create("strong", "plate", entry.registration.plate), create("span", "record-customer", entry.registration.customer), create("span", "pos-doc", `${entry.order.reference}${entry.invoice ? ` · ${entry.invoice.reference}` : ""}`), create("span", "status-label", status), create("strong", "pos-amount", `${entry.stage === "unpaid" ? "Sisa " : entry.stage === "paid" ? "Sisa " : "Total "}${money.format(entry.amount)}${entry.stage === "ready" && entry.amount === 0 ? " · tanpa biaya" : ""}`));
        button.addEventListener("click", () => select(entry.order.id)); row.append(button); $("cashier-list").append(row);
      }
      const chosen = all.find((entry) => entry.order.id === selected);
      $("pos-invoice-note").textContent = chosen?.stage === "paid" ? "Transaksi ini sudah Lunas. Nota tetap terbuka; pilih transaksi berikutnya saat siap." : chosen && !shown.includes(chosen) ? "Transaksi terpilih berada di luar filter. Isian tetap dipertahankan." : "";
      $("pos-preview-context").textContent = $("pos-invoice-note").textContent;
      preview();
    }

    function select(orderId) {
      if (!access() || !api.canRead()) return false;
      const entry = entries().find((entry) => entry.order.id === orderId);
      if (!entry) return false;
      if (entry.invoice) {
        if (!api.openInvoice(orderId)) return false;
      } else if (!api.showPreview()) return false;
      selected = orderId; render();
      if (!entry.invoice) { $("pos-preview-heading").tabIndex = -1; $("pos-preview-heading").focus(); }
      return true;
    }

    $("cashier-search").addEventListener("input", render); $("cashier-filter").addEventListener("change", render); $("pos-stage").addEventListener("change", render);
    $("pos-create-invoice").addEventListener("click", () => { if (access() && selected && api.openInvoice(selected)) render(); });
    $("pos-open-order").addEventListener("click", () => { if (access() && selected) api.openOrder(selected); });
    $("pos-back").addEventListener("click", () => api.showList());
    window.addEventListener("online", render); window.addEventListener("offline", render);
    return { render, reflectInvoice: (orderId) => { if (access()) { selected = orderId; render(); } } };
  }
  window.POSCashier = Object.freeze({ createFeature });
})();
