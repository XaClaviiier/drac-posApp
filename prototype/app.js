"use strict";

(() => {
  const previewMode = new URLSearchParams(location.search).get("demo") === "flow";
  const STORAGE_KEY = previewMode ? "pos_browser_preview_flow_v1" : "pos_browser_prototype_v1";
  const THEME_KEY = "pos_browser_prototype_theme";
  const ROLE_KEY = "pos_browser_prototype_role";
  const fields = ["plate", "complaint", "customer", "phone", "address"];
  const roles = ["Owner", "Teknisi", "Kasir"];
  const $ = (id) => document.getElementById(id);
  const form = $("registration-form");
  let state;
  let expectedRevision = null;
  let blocked = false;
  let conflicted = false;
  let loading = false;
  let submitting = false;
  let draftTimer;
  let view = "list";
  let period = "all";
  let role = "Owner";
  let draftDirty = false;
  let detailRegistrationId = null;
  let diagnosisFeature;
  let ordersFeature;
  let invoicesFeature;
  let cashierFeature;
  let posMode = false;
  let posDetail = false;
  const dateFormat = new Intl.DateTimeFormat("id-ID", { day: "numeric", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" });

  function seed() {
    const now = new Date();
    const at = (days, hours) => new Date(now.getFullYear(), now.getMonth(), now.getDate() - days, hours, 15).toISOString();
    const samples = [
      ["DD 1248 KL", "Budi Contoh", "081200000001", "AC kurang dingin saat mobil berhenti. Kembali dingin ketika berjalan.", "Makassar (alamat contoh)", 0, 8],
      ["DD 8921 AR", "Siti Contoh", "081200000002", "Hembusan AC lemah dan terdengar bunyi dari blower.", "", 0, 9],
      ["DD 5672 TS", "Dewi Contoh", "081200000003", "AC tidak dingin setelah mobil dipakai sekitar 30 menit.", "", 0, 10],
      ["DD 3107 MA", "Ahmad Contoh", "081200000004", "Ada bau lembap ketika AC pertama kali dinyalakan.", "", 1, 14],
    ];
    return { version: 1, revision: null, draft: null, records: samples.map((s, i) => ({
      id: `demo-${i + 1}`, reference: `REG-CONTOH-${String(i + 1).padStart(3, "0")}`,
      plate: s[0], customer: s[1], phone: s[2], complaint: s[3], address: s[4],
      createdAt: at(s[5], s[6]), actor: i % 2 ? "Kasir" : "Teknisi", status: "registered",
    })) };
  }

  function validFields(value) {
    return value && fields.every((key) => typeof value[key] === "string" && value[key].length <= ({ plate: 16, customer: 100, complaint: 1000, phone: 24, address: 300 })[key]);
  }

  function validateStore(value) {
    if (!value || value.version !== 1 || typeof value.revision !== "string" || !Array.isArray(value.records)) throw new Error("invalid-storage");
    const ids = new Set();
    for (const record of value.records) {
      if (!validFields(record) || typeof record.id !== "string" || !record.id || ids.has(record.id) || typeof record.reference !== "string" || !roles.includes(record.actor) || record.status !== "registered" || !Number.isFinite(Date.parse(record.createdAt))) throw new Error("invalid-storage");
      ids.add(record.id);
    }
    if (value.draft !== null && (!validFields(value.draft) || typeof value.draft.id !== "string" || !value.draft.id || ids.has(value.draft.id) || !Number.isFinite(Date.parse(value.draft.updatedAt)))) throw new Error("invalid-storage");
    window.POSDiagnosis.validCollections(value);
    window.POSOrders.validate(value);
    window.POSInvoices.validate(value);
    return value;
  }

  function readStore() {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw === null ? null : validateStore(JSON.parse(raw));
  }

  function storageReadError(error) {
    const corrupt = error instanceof SyntaxError || error.message === "invalid-storage";
    showError(corrupt ? "Data lokal tidak dapat dibaca" : "Akses penyimpanan tidak tersedia",
      corrupt ? "Format data lokal rusak atau tidak sesuai. Data tidak ditimpa. Unduh salinan mentah sebelum meminta bantuan pemulihan; jangan hapus data situs."
        : "Browser menolak akses penyimpanan, atau sumber preview tidak dapat dimuat. Periksa izin data situs dan mode privat, lalu coba lagi. Jangan hapus data situs.");
  }

  function showError(title, message, conflict = false) {
    $("storage-alert-title").textContent = title;
    $("storage-alert-message").textContent = message;
    $("storage-alert").hidden = false;
    $("storage-retry").textContent = conflict ? "Muat data terbaru" : "Coba lagi";
    try { $("storage-backup").hidden = localStorage.getItem(STORAGE_KEY) === null; }
    catch { $("storage-backup").hidden = true; }
    $("announcement").textContent = "";
    draftStatus("Belum tersimpan", true);
  }

  function clearError() { $("storage-alert").hidden = true; }

  function draftStatus(message, error = false) {
    $("draft-status").textContent = message;
    $("draft-status").dataset.state = error ? "error" : "normal";
  }

  function persist(candidate) {
    if (blocked || conflicted) return false;
    try {
      const latest = readStore();
      if ((latest?.revision ?? null) !== expectedRevision) {
        conflicted = true;
        showError("Data berubah di tab lain", "Isian Anda tetap ada. Muat data terbaru sebelum mencoba menyimpan lagi.", true);
        return false;
      }
      // The revision check detects sequential tab conflicts; localStorage is not an atomic server transaction.
      const next = { ...candidate, revision: crypto.randomUUID() };
      window.POSInvoices.assertAppend(state, next);
      validateStore(next);
      localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
      state = next;
      expectedRevision = next.revision;
      clearError();
      return true;
    } catch (error) {
      if (error instanceof SyntaxError || error.message === "invalid-storage") {
        blocked = true;
        storageReadError(error);
      } else {
        showError("Penyimpanan gagal", "Isian tetap ada di halaman ini. Izinkan penyimpanan browser atau kosongkan ruang perangkat, lalu coba lagi. Jangan tutup halaman sebelum berhasil.");
      }
      return false;
    }
  }

  function values() { return Object.fromEntries(fields.map((key) => [key, $(key).value])); }
  function hasInput(value) { return fields.some((key) => value[key].trim()); }
  function fillForm(value) { fields.forEach((key) => { $(key).value = value?.[key] ?? ""; }); }

  function saveDraft() {
    clearTimeout(draftTimer);
    if (!state || blocked || conflicted || loading || submitting) return false;
    const data = values();
    const draft = hasInput(data) ? { ...data, id: state.draft?.id || crypto.randomUUID(), updatedAt: new Date().toISOString() } : null;
    if (persist({ ...state, draft })) {
      draftDirty = false;
      draftStatus(draft ? "Draf tersimpan di perangkat ini" : "Belum ada perubahan");
      renderDraft();
      return true;
    }
    return false;
  }

  function discardDraft() {
    if (!state || blocked || loading) { $("storage-retry").focus(); return; }
    if (!window.confirm("Buang draf registrasi ini dan mulai isian kosong? Registrasi dan dokumen yang sudah tersimpan tidak dihapus.")) return;
    clearTimeout(draftTimer);
    if (!persist({ ...state, draft: null })) {
      draftStatus("Draf belum dibuang. Isian tetap ada; selesaikan masalah penyimpanan terlebih dahulu.", true);
      return;
    }
    draftDirty = false;
    form.reset();
    fields.forEach((key) => { $(`${key}-error`).textContent = ""; $(key).removeAttribute("aria-invalid"); });
    renderDraft();
    draftStatus("Draf dibuang. Siap untuk registrasi baru.");
    $("plate").focus();
  }

  function renderDraft() {
    $("draft-notice").hidden = !state?.draft;
    $("draft-description").textContent = state?.draft?.plate ? `${state.draft.plate.toUpperCase()} · lanjutkan isian yang belum selesai.` : "Lanjutkan isian yang tersimpan di perangkat ini.";
    $("new-registration").textContent = state?.draft ? "Lanjutkan registrasi" : "+ Registrasi kendaraan";
  }

  function create(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  }

  function sameDay(iso) { return new Date(iso).toDateString() === new Date().toDateString(); }

  function renderList() {
    const query = $("search").value.trim().toLocaleLowerCase("id-ID");
    const normalized = query.replace(/\s/g, "");
    const phoneQuery = /^[+\d\s()-]+$/.test(query) ? query.replace(/\D/g, "") : "";
    const list = state ? state.records.filter((r) => (period !== "today" || sameDay(r.createdAt)) && (!query || [r.plate, r.customer, r.phone].some((v) => v.toLocaleLowerCase("id-ID").includes(query)) || r.plate.toLowerCase().replace(/\s/g, "").includes(normalized) || (phoneQuery && r.phone.replace(/\D/g, "").includes(phoneQuery)))) : [];
    $("records-list").replaceChildren();
    list.forEach((r) => {
      const row = create("article", "record");
      const vehicle = create("div", "record-vehicle");
      vehicle.append(create("strong", "plate", r.plate), create("span", "record-customer", r.customer));
      const meta = create("div", "record-meta");
      const diagnosisStatus = diagnosisFeature?.status(r.id);
      meta.append(create("span", "status-label", diagnosisStatus === "approved" ? "Estimasi disetujui" : diagnosisStatus ? "Draf diagnosa" : "Belum diperiksa"), create("span", "", dateFormat.format(new Date(r.createdAt))));
      const button = create("button", "record-action", "Lihat detail");
      button.setAttribute("aria-label", `Lihat detail ${r.plate}`);
      button.addEventListener("click", () => showDetail(r.id));
      row.append(vehicle, create("p", "record-complaint", r.complaint), meta, button);
      $("records-list").append(row);
    });
    $("record-count").textContent = state ? `${list.length} dari ${state.records.length} kunjungan` : "Data belum tersedia";
    $("empty-state").hidden = list.length > 0 || blocked;
    $("empty-message").textContent = query || period === "today" ? "Tidak ada registrasi yang sesuai. Ubah kata pencarian atau pilih Semua kunjungan." : "Tambahkan registrasi pertama untuk memulai penerimaan.";
    $("empty-state").querySelector("h3").textContent = query || period === "today" ? "Tidak ada hasil" : "Belum ada kendaraan";
    $("filter-all").setAttribute("aria-pressed", String(period === "all"));
    $("filter-today").setAttribute("aria-pressed", String(period === "today"));
    renderDraft();
    diagnosisFeature?.renderList();
    ordersFeature?.renderList();
    invoicesFeature?.renderList();
  }

  function closeMenu(returnFocus = false) {
    $("sidebar").classList.remove("is-open");
    $("menu-toggle").setAttribute("aria-expanded", "false");
    if (returnFocus) $("menu-toggle").focus();
  }

  function showView(next) {
    if (next === "cashier" && role === "Teknisi") return false;
    if (view === "diagnosis" && next !== "diagnosis" && diagnosisFeature.isDirty() && !diagnosisFeature.save()) return false;
    if (view === "so" && next !== "so" && !ordersFeature.leave()) return false;
    if (view === "invoice" && next !== "invoice" && !invoicesFeature.leave()) return false;
    if (next === "cashier") { posMode = true; posDetail = false; }
    else if (next === "invoice") { posMode = view === "cashier" || (view === "invoice" && posMode); posDetail = true; }
    else { posMode = false; posDetail = false; }
    view = next;
    const titles = { list: "Registrasi kendaraan", form: "Registrasi baru", detail: "Detail registrasi", diagnoses: "Diagnosa & Estimasi", diagnosis: "Diagnosa & Estimasi", orders: "Service Order", so: "Service Order", cashier: "Kasir / POS", invoices: "Invoice & Pembayaran", invoice: "Invoice & Pembayaran" };
    $("breadcrumb").textContent = `Bengkel / ${titles[next]}`;
    document.title = `${titles[next]} | Prototype POS Bengkel`;
    const posActive = posMode && ["Owner", "Kasir"].includes(role);
    ["list", "form", "detail", "diagnoses", "diagnosis", "orders", "so", "cashier", "invoices", "invoice"].forEach((name) => { $(`${name}-view`).hidden = name !== next; });
    $("cashier-view").hidden = !posActive;
    $("pos-preview").hidden = !posActive || next !== "cashier";
    $("main").classList.toggle("pos-workspace", posActive);
    $("main").dataset.posDetail = String(posDetail);
    $("pos-invoice-note").hidden = !posActive;
    $("invoice-back").textContent = posActive ? "Kembali ke antrean" : "Kembali ke daftar invoice";
    const diagnosisNav = ["diagnoses", "diagnosis"].includes(next);
    const ordersNav = ["orders", "so"].includes(next);
    const invoiceNav = ["invoices", "invoice"].includes(next) && !posActive;
    for (const [navId, current] of [["nav-registration", !diagnosisNav && !ordersNav && !posActive && !invoiceNav], ["nav-diagnoses", diagnosisNav], ["nav-orders", ordersNav], ["nav-cashier", posActive], ["nav-invoices", invoiceNav]]) {
      $(navId).classList.toggle("nav-current", current);
      if (current) $(navId).setAttribute("aria-current", "page");
      else $(navId).removeAttribute("aria-current");
    }
    closeMenu();
    const heading = $(`${next}-heading`);
    heading.tabIndex = -1;
    heading.focus();
    window.scrollTo({ top: 0 });
    return true;
  }

  function openForm() {
    if (blocked || loading) { $("storage-retry").focus(); return; }
    if (view !== "form" && !draftDirty) fillForm(state.draft);
    $("announcement").textContent = "";
    if (!draftDirty) draftStatus(state.draft ? "Draf dipulihkan dari perangkat ini" : "Belum ada perubahan");
    if (showView("form")) $("plate").focus();
  }

  function showDetail(id) {
    const record = state.records.find((r) => r.id === id);
    if (!record) return;
    detailRegistrationId = id;
    $("detail-reference").textContent = record.reference;
    ["plate", "customer", "complaint", "phone", "address"].forEach((key) => { $(`detail-${key}`).textContent = record[key] || "Tidak dicatat"; });
    $("detail-actor").textContent = `${record.actor} (simulasi)`;
    $("detail-time").textContent = dateFormat.format(new Date(record.createdAt));
    updateDiagnosisEntry();
    showView("detail");
  }

  function updateDiagnosisEntry() {
    const status = diagnosisFeature?.status(detailRegistrationId);
    const allowed = diagnosisFeature?.isWriter(role);
    $("detail-status").textContent = status === "approved" ? "Estimasi disetujui" : status ? "Draf diagnosa" : "Belum diperiksa";
    $("open-diagnosis").textContent = status ? "Buka diagnosa" : "Buat diagnosa";
    $("open-diagnosis").disabled = !status && !allowed;
    $("diagnosis-entry-note").textContent = !status && !allowed ? "Diagnosa belum dibuat. Teknisi/Owner dapat membuatnya setelah pemeriksaan; Kasir dapat membaca dokumen yang sudah dibuat." : "Buka pemeriksaan dan estimasi untuk kunjungan ini, tanpa mengisi ulang identitas pelanggan.";
  }

  function validate(data) {
    const errors = {};
    if (!data.plate) errors.plate = "Isi nomor plat kendaraan.";
    else if (!/^[A-Z]{1,3}\s*\d{1,4}(?:\s*[A-Z]{1,3})?$/.test(data.plate)) errors.plate = "Gunakan format plat, misalnya DD 1248 KL.";
    if (!data.complaint) errors.complaint = "Tuliskan keluhan awal mobil.";
    if (!data.customer) errors.customer = "Isi nama pelanggan.";
    if (!data.phone) errors.phone = "Isi nomor telepon pelanggan.";
    else if (!/^(?:0|\+62|62)[\d\s()-]+$/.test(data.phone) || data.phone.replace(/\D/g, "").length < 9 || data.phone.replace(/\D/g, "").length > 15) errors.phone = "Isi nomor telepon 9–15 digit, diawali 0 atau +62.";
    fields.forEach((key) => {
      $(`${key}-error`).textContent = errors[key] || "";
      $(key).setAttribute("aria-invalid", String(Boolean(errors[key])));
    });
    if (Object.keys(errors).length) {
      $(fields.find((key) => errors[key])).focus();
      return false;
    }
    return true;
  }

  function submitRegistration(event) {
    event.preventDefault();
    if (submitting || view !== "form" || !state) return;
    clearTimeout(draftTimer);
    const data = Object.fromEntries(fields.map((key) => [key, $(key).value.trim()]));
    data.plate = data.plate.toUpperCase().replace(/\s+/g, " ");
    if (!validate(data)) {
      if (draftDirty) saveDraft();
      return;
    }
    if (blocked || conflicted) { $("storage-retry").focus(); return; }
    submitting = true;
    $("save-registration").disabled = true;
    const id = state.draft?.id || crypto.randomUUID();
    const now = new Date();
    const record = { ...data, id, reference: `REG-${now.getFullYear()}-${id.slice(0, 8).toUpperCase()}`, createdAt: now.toISOString(), actor: role, status: "registered" };
    const saved = persist({ ...state, draft: null, records: [record, ...state.records] });
    submitting = false;
    $("save-registration").disabled = false;
    if (!saved) return;
    draftDirty = false;
    form.reset();
    fields.forEach((key) => { $(`${key}-error`).textContent = ""; $(key).removeAttribute("aria-invalid"); });
    renderList();
    showDetail(id);
    $("announcement").textContent = `Registrasi ${record.plate} tersimpan di perangkat ini. Belum ada diagnosa atau tagihan.`;
  }

  async function loadData(preserveForm = false) {
    clearTimeout(draftTimer);
    loading = true;
    $("records-panel").setAttribute("aria-busy", "true");
    $("loading-state").hidden = false;
    $("records-list").hidden = true;
    $("storage-retry").disabled = true;
    try {
      const latest = readStore();
      let example = null;
      if (!latest && previewMode) {
        const response = await fetch("preview-store.json", { cache: "no-store" });
        if (!response.ok) throw new Error("preview-unavailable");
        example = validateStore(await response.json());
      }
      state = latest || example || seed();
      expectedRevision = latest?.revision ?? null;
      blocked = false;
      conflicted = false;
      clearError();
      if (!latest) persist(state);
      if (preserveForm && view === "form") {
        const current = values();
        draftDirty = fields.some((key) => current[key] !== (state.draft?.[key] ?? ""));
      } else if (!draftDirty) {
        fillForm(state.draft);
      }
      if (preserveForm && draftDirty) {
        draftStatus("Data terbaru dimuat. Isian Anda belum tersimpan.");
      } else {
        draftStatus(state.draft ? "Draf tersimpan di perangkat ini" : "Belum ada perubahan");
      }
      renderList();
      if (preserveForm) diagnosisFeature.onReload();
      if (preserveForm) ordersFeature.onReload();
      if (preserveForm) invoicesFeature.onReload();
      if (detailRegistrationId) updateDiagnosisEntry();
    } catch (error) {
      blocked = true;
      storageReadError(error);
      if (!state) { $("record-count").textContent = "Data belum tersedia"; $("empty-state").hidden = true; }
    } finally {
      loading = false;
      $("loading-state").hidden = true;
      $("records-list").hidden = false;
      $("records-panel").setAttribute("aria-busy", "false");
      $("storage-retry").disabled = false;
      cashierFeature?.render();
    }
  }

  form.addEventListener("submit", submitRegistration);
  $("discard-draft").addEventListener("click", discardDraft);
  form.addEventListener("input", (event) => {
    if (!fields.includes(event.target.id)) return;
    draftDirty = true;
    $("announcement").textContent = "";
    $(`${event.target.id}-error`).textContent = "";
    event.target.removeAttribute("aria-invalid");
    clearTimeout(draftTimer);
    if (blocked || conflicted) return;
    draftStatus("Menyimpan draf…");
    draftTimer = setTimeout(saveDraft, 400);
  });
  function backToList() {
    if (view === "form" && draftDirty && !saveDraft()) return;
    renderList();
    showView("list");
  }
  $("back-from-form").addEventListener("click", backToList);
  $("back-from-detail").addEventListener("click", backToList);
  $("nav-registration").addEventListener("click", backToList);
  $("nav-diagnoses").addEventListener("click", () => {
    if (view === "form" && draftDirty && !saveDraft()) return;
    diagnosisFeature.renderList();
    showView("diagnoses");
  });
  $("nav-orders").addEventListener("click", () => {
    if (view === "form" && draftDirty && !saveDraft()) return;
    ordersFeature.renderList();
    showView("orders");
  });
  $("open-diagnosis").addEventListener("click", () => {
    if (!detailRegistrationId || (!diagnosisFeature.isWriter(role) && !diagnosisFeature.status(detailRegistrationId))) return;
    diagnosisFeature.open(detailRegistrationId);
  });
  $("nav-cashier").addEventListener("click", () => {
    if (role === "Teknisi") return;
    if (view === "form" && draftDirty && !saveDraft()) return;
    showView("cashier");
  });
  $("cashier-to-orders").addEventListener("click", () => { ordersFeature.renderList(); showView("orders"); });
  $("nav-invoices").addEventListener("click", () => { if (view === "form" && draftDirty && !saveDraft()) return; invoicesFeature.renderList(); showView("invoices"); });
  $("invoice-back").addEventListener("click", () => { if (posMode) showView("cashier"); else { invoicesFeature.renderList(); showView("invoices"); } });
  $("new-registration").addEventListener("click", openForm);
  $("resume-draft").addEventListener("click", openForm);
  $("search").addEventListener("input", renderList);
  $("filter-all").addEventListener("click", () => { period = "all"; renderList(); });
  $("filter-today").addEventListener("click", () => { period = "today"; renderList(); });
  $("demo-role").addEventListener("change", (event) => {
    if (!roles.includes(event.target.value)) { event.target.value = role; return; }
    if (diagnosisFeature.isDirty() && !diagnosisFeature.save()) { event.target.value = role; return; }
    role = event.target.value;
    $("nav-cashier").hidden = role === "Teknisi";
    if (view === "cashier" && role === "Teknisi") showView("orders");
    $("verbal-approval").checked = false;
    diagnosisFeature.applyRole();
    diagnosisFeature.renderList();
    ordersFeature.roleChanged();
    invoicesFeature.roleChanged();
    ordersFeature.renderList();
    updateDiagnosisEntry();
    $("announcement").textContent = `Simulasi peran ${role}. Registrasi tersedia; ini bukan pergantian sesi login.`;
    const dirty = (view === "so" && ordersFeature.isDirty()) || (view === "invoice" && invoicesFeature.isDirty()) || (view === "form" && draftDirty);
    if (role === "Kasir" && view === "invoice") { posMode = true; showView("invoice"); cashierFeature.reflectInvoice(invoicesFeature.activeOrder()); }
    else if (role === "Kasir" && !dirty) showView("cashier");
    else if (role === "Teknisi" && view === "invoice" && posMode) { posMode = false; showView("invoice"); }
    if (role === "Kasir" && dirty) $("announcement").textContent = "Peran Kasir dipilih. Isian lokal tetap dipertahankan; periksa hak peran sebelum melanjutkan.";
    try { localStorage.setItem(ROLE_KEY, role); } catch { $("announcement").textContent += " Pilihan peran tidak tersimpan untuk reload."; }
  });
  $("storage-retry").addEventListener("click", async () => {
    if (conflicted || blocked) { await loadData(true); return; }
    if (view === "diagnosis" && diagnosisFeature.status(diagnosisFeature.active()) !== "approved" && diagnosisFeature.isWriter(role)) diagnosisFeature.save();
    else if (view === "diagnosis") await loadData(true);
    else if (view === "form") saveDraft();
    else await loadData(true);
  });
  $("storage-backup").addEventListener("click", () => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (raw === null) { $("storage-alert-message").textContent = "Tidak ada data lokal pada ruang penyimpanan ini untuk diunduh."; return; }
      const url = URL.createObjectURL(new Blob([raw], { type: "text/plain;charset=utf-8" }));
      const link = document.createElement("a");
      link.href = url;
      link.download = previewMode ? "pos-preview-data-mentah.txt" : "pos-data-mentah.txt";
      document.body.append(link);
      link.click();
      link.remove();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
    } catch {
      $("storage-alert-message").textContent = "Salinan belum dapat diunduh. Izinkan akses penyimpanan browser lalu coba lagi. Data tidak dihapus atau ditimpa.";
    }
  });
  $("menu-toggle").addEventListener("click", () => {
    const open = $("sidebar").classList.toggle("is-open");
    $("menu-toggle").setAttribute("aria-expanded", String(open));
    if (open) $("nav-registration").focus();
  });
  $("menu-close").addEventListener("click", () => closeMenu(true));
  document.addEventListener("keydown", (event) => { if (event.key === "Escape" && $("sidebar").classList.contains("is-open")) closeMenu(true); });
  function setTheme(theme) {
    document.documentElement.dataset.theme = theme;
    $("theme-toggle").textContent = theme === "dark" ? "Tema terang" : "Tema gelap";
    $("theme-toggle").setAttribute("aria-pressed", String(theme === "dark"));
  }
  $("theme-toggle").addEventListener("click", () => {
    const theme = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
    setTheme(theme);
    try { localStorage.setItem(THEME_KEY, theme); } catch { $("announcement").textContent = "Tema berubah untuk halaman ini. Pilihan tema tidak dapat disimpan."; }
  });
  window.addEventListener("storage", (event) => {
    if ((event.key === STORAGE_KEY || event.key === null) && !loading) {
      clearTimeout(draftTimer);
      diagnosisFeature.cancelTimer();
      ordersFeature.conflict();
      invoicesFeature.conflict();
      conflicted = true;
      showError("Data berubah di tab lain", "Isian Anda tetap ada. Muat data terbaru sebelum menyimpan. Tidak ada data yang ditimpa otomatis.", true);
    }
  });
  window.addEventListener("beforeunload", (event) => {
    if (draftDirty && !saveDraft()) { event.preventDefault(); event.returnValue = ""; }
    if (diagnosisFeature.isDirty() && !diagnosisFeature.save()) { event.preventDefault(); event.returnValue = ""; }
    if (ordersFeature.isDirty()) { event.preventDefault(); event.returnValue = ""; }
    if (invoicesFeature.isDirty()) { event.preventDefault(); event.returnValue = ""; }
  });
  diagnosisFeature = window.POSDiagnosis.createFeature({
    state: () => state,
    role: () => role,
    persist,
    create,
    show: showView,
    refresh: () => { renderList(); if (detailRegistrationId) updateDiagnosisEntry(); },
    announce: (message) => { $("announcement").textContent = message; },
    error: (title, message) => showError(title, message, true),
    order: (id) => ordersFeature.open(id, true),
  });
  ordersFeature = window.POSOrders.createFeature({
    state: () => state,
    role: () => role,
    persist,
    create,
    show: showView,
    refresh: renderList,
    announce: (message) => { $("announcement").textContent = message; },
    registration: showDetail,
    diagnosis: (id) => diagnosisFeature.open(id),
    diagnoses: () => { diagnosisFeature.renderList(); showView("diagnoses"); },
    invoice: (id) => invoicesFeature.open(id),
    renderCashier: () => cashierFeature?.render(),
  });
  invoicesFeature = window.POSInvoices.createFeature({ state: () => state, role: () => role, persist, create, show: showView, refresh: renderList, orderDirty: () => ordersFeature.isDirty(), isCurrent: () => { try { return view === "invoice" && !blocked && !conflicted && readStore()?.revision === expectedRevision; } catch { return false; } }, announce: (message) => { $("announcement").textContent = message; } });
  cashierFeature = window.POSCashier.createFeature({ state: () => state, role: () => role, create, canRead: () => Boolean(state) && !blocked, canWrite: () => Boolean(state) && !blocked && !conflicted && !loading && navigator.onLine, openInvoice: (id) => invoicesFeature.open(id), openOrder: (id) => ordersFeature.open(id), showList: () => showView("cashier"), showPreview: () => { if (!showView("cashier")) return false; posDetail = true; $("main").dataset.posDetail = "true"; return true; } });
  try { setTheme(localStorage.getItem(THEME_KEY) === "dark" ? "dark" : "light"); } catch { setTheme("light"); }
  try { const savedRole = localStorage.getItem(ROLE_KEY); if (roles.includes(savedRole)) role = savedRole; } catch { role = "Owner"; }
  $("demo-role").value = role;
  $("nav-cashier").hidden = role === "Teknisi";
  diagnosisFeature.applyRole();
  if (previewMode) document.querySelector(".demo-notice").textContent = "Mode latihan alur. Seluruh data dan harga adalah contoh; latihan disimpan terpisah dari prototype utama. Pembayaran hanya simulasi.";
  loadData().then(() => {
    if (blocked) return;
    const stage = new URLSearchParams(location.search).get("stage");
    const target = previewMode && ["list", "diagnoses", "orders", "cashier", "invoices"].includes(stage) ? stage : role === "Kasir" ? "cashier" : "list";
    showView(target === "cashier" && role === "Teknisi" ? "orders" : target);
  });
})();
