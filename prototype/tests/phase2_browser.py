"""Phase-two workflow and failure regressions, on an isolated local origin."""

import copy
import json
import threading
from datetime import datetime, timezone
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

from playwright.sync_api import expect, sync_playwright
import phase1_browser as base

OUT = base.OUT
checks = []
errors = []


def passed(name):
    checks.append({"check": name, "passed": True})
    print("PASS", name)


def open_diagnosis(page, plate="DD 1248 KL"):
    page.locator("#nav-diagnoses").click()
    page.locator("#diagnoses-list .record").filter(has_text=plate).get_by_role("button").click()
    expect(page.locator("#diagnosis-view")).to_be_visible()


def item(page, index=0):
    return page.locator(".estimate-item").nth(index)


def add(page, catalog_id):
    page.locator("#estimate-catalog").select_option(catalog_id)
    page.locator("#add-estimate-item").click()


def saved(page):
    expect(page.locator("#diagnosis-save-status")).to_have_text("Tersimpan di perangkat ini")


def fail_writes(page):
    page.evaluate("""() => {
        window.savedSetItem = Storage.prototype.setItem;
        Storage.prototype.setItem = function(key, value) {
            if (key === 'pos_browser_prototype_v1') throw new DOMException('Test quota', 'QuotaExceededError');
            return window.savedSetItem.call(this, key, value);
        };
    }""")


def restore_writes(page):
    page.evaluate("() => {Storage.prototype.setItem = window.savedSetItem;}")


def main():
    OUT.mkdir(exist_ok=True)
    server = ThreadingHTTPServer(("127.0.0.1", 0), partial(SimpleHTTPRequestHandler, directory=str(base.ROOT)))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base.URL = f"http://127.0.0.1:{server.server_port}/prototype/"
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            try:
                ctx = browser.new_context(viewport={"width": 1440, "height": 1000}, locale="id-ID")
                page = ctx.new_page()
                page.on("pageerror", lambda error: errors.append(str(error)))
                page.on("console", lambda msg: errors.append(msg.text) if msg.type == "error" else None)
                base.loaded(page)
                original = base.data(page)
                assert "diagnoses" not in original
                page.locator("#new-registration").click()
                page.locator("#plate").fill("DD 9000 XX")
                expect(page.locator("#draft-status")).to_have_text("Draf tersimpan di perangkat ini")
                draft_before = base.data(page)["draft"]
                page.locator("#back-from-form").click()
                page.get_by_role("button", name="Lihat detail DD 1248 KL", exact=True).click()
                page.locator("#open-diagnosis").click()
                expect(page.locator("#diagnosis-identity")).to_contain_text("Budi Contoh")
                expect(page.locator("#diagnosis-complaint")).to_contain_text("AC kurang dingin")
                passed("Store Fase 1 terbaca; identitas dan keluhan terhubung tanpa entry ulang")

                page.locator("#approve-diagnosis").click()
                expect(page.locator("#findings-error")).to_contain_text("Tuliskan")
                expect(page.locator("#items-error")).to_contain_text("minimal satu")
                assert not base.data(page).get("serviceOrders")
                page.locator("#diagnosis-findings").fill("Filter kabin kotor, aliran udara lemah.")
                page.locator("#diagnosis-recommendations").fill("Cuci evaporator dan ganti filter kabin.")
                add(page, "service-clean")
                add(page, "part-filter")
                item(page, 1).locator("[name=quantity]").fill("2")
                item(page, 1).locator("[name=unitPrice]").fill("90000")
                item(page, 1).locator("[name=priceReason]").fill("Penyesuaian harga lokal contoh")
                saved(page)
                expect(page.locator("#estimate-total")).to_contain_text("530.000")
                expect(page.locator("#estimate-services")).to_contain_text("350.000")
                expect(page.locator("#estimate-parts")).to_contain_text("180.000")
                assert base.data(page)["records"] == original["records"]
                assert base.data(page)["draft"] == draft_before
                passed("Itemized jasa/part dan total tepat; record serta draf registrasi tetap utuh")

                add(page, "part-dryer")
                item(page, 2).get_by_role("button", name="Hapus Receiver dryer, baris 3", exact=True).click()
                expect(page.locator("#estimate-catalog")).to_be_focused()
                saved(page)
                expect(page.locator("#estimate-total")).to_contain_text("530.000")
                assert len(base.data(page)["diagnoses"][0]["items"]) == 2
                page.locator("#approve-diagnosis").click()
                expect(page.locator("#approval-error")).to_contain_text("secara lisan")
                assert base.data(page)["diagnoses"][0]["status"] == "draft"
                passed("Hapus baris/fokus bekerja; persetujuan tidak otomatis")

                for invalid in ("0", "-1", "1.5", "1000000", ""):
                    item(page).locator("[name=quantity]").fill(invalid)
                    page.locator("#verbal-approval").check()
                    page.locator("#approve-diagnosis").click()
                    expect(item(page).locator("[name=quantity]")).to_have_attribute("aria-invalid", "true")
                    assert base.data(page)["diagnoses"][0]["status"] == "draft"
                item(page).locator("[name=quantity]").fill("1")
                for invalid in ("-1", "1.5", "1000000001", "1e30", ""):
                    item(page).locator("[name=unitPrice]").fill(invalid)
                    page.locator("#verbal-approval").check()
                    page.locator("#approve-diagnosis").click()
                    assert base.data(page)["diagnoses"][0]["status"] == "draft"
                item(page).locator("[name=unitPrice]").fill("350000")
                item(page, 1).locator("[name=priceReason]").fill("")
                page.locator("#verbal-approval").check()
                page.locator("#approve-diagnosis").click()
                expect(item(page, 1).locator("[name=priceReason]")).to_have_attribute("aria-invalid", "true")
                item(page, 1).locator("[name=priceReason]").fill("Harga lokal sesuai kesepakatan contoh")
                saved(page)
                passed("Qty nol/negatif/pecahan/overflow dan harga invalid ditolak; alasan harga wajib")

                page.reload()
                open_diagnosis(page)
                expect(page.locator("#diagnosis-findings")).to_have_value("Filter kabin kotor, aliran udara lemah.")
                expect(page.locator("#verbal-approval")).not_to_be_checked()
                expect(page.locator("#estimate-total")).to_contain_text("530.000")
                page.locator("#price-log-panel summary").click()
                expect(page.locator("#price-log-list")).to_contain_text("100.000")
                passed("Draf estimasi pulih setelah reload; log perubahan harga tersedia untuk Owner")

                fail_writes(page)
                page.locator("#verbal-approval").check()
                page.locator("#approve-diagnosis").click()
                expect(page.locator("#storage-alert")).to_be_visible()
                assert base.data(page)["diagnoses"][0]["status"] == "draft"
                restore_writes(page)
                page.locator("#storage-retry").click()
                page.locator("#verbal-approval").check()
                page.locator("#approve-diagnosis").click()
                expect(page.locator("#diagnosis-status")).to_have_text("Disetujui")
                expect(page.locator("#diagnosis-findings")).to_be_disabled()
                expect(item(page).locator("[name=quantity]")).to_be_disabled()
                assert base.data(page)["diagnoses"][0]["approvedBy"] == "Owner"
                snapshot = copy.deepcopy(base.data(page)["diagnoses"][0])
                page.evaluate("""() => {
                    const field = document.getElementById('diagnosis-findings');
                    field.disabled = false; field.value = 'Tampered';
                    field.dispatchEvent(new Event('input', {bubbles:true}));
                    document.getElementById('save-diagnosis').dispatchEvent(new Event('click'));
                    document.getElementById('add-estimate-item').dispatchEvent(new Event('click'));
                }""")
                assert base.data(page)["diagnoses"][0] == snapshot
                page.reload()
                open_diagnosis(page)
                expect(page.locator("#diagnosis-findings")).to_be_disabled()
                page.screenshot(path=str(OUT / "phase2-approved-desktop.png"), full_page=True, animations="disabled")
                passed("Gagal approval tidak mengubah status; approved terkunci termasuk event buatan/reload")

                fail_writes(page)
                page.locator("#create-service-order").click()
                assert not base.data(page).get("serviceOrders")
                assert base.data(page)["diagnoses"][0] == snapshot
                restore_writes(page)
                page.locator("#create-service-order").dblclick()
                expect(page.locator("#so-view")).to_be_visible()
                assert len(base.data(page)["serviceOrders"]) == 1
                so_snapshot = copy.deepcopy(base.data(page)["serviceOrders"][0])
                page.screenshot(path=str(OUT / "phase2-so-desktop.png"), full_page=True, animations="disabled")
                assert so_snapshot["estimateTotal"] == 530000
                assert so_snapshot["items"][1]["unitPrice"] == 90000
                page.locator("#back-from-so").click()
                page.locator("#create-service-order").click()
                assert base.data(page)["serviceOrders"][0] == so_snapshot
                assert len(base.data(page)["serviceOrders"]) == 1
                passed("SO hanya dari approved; gagal write atomik; klik ulang membuka snapshot sama")

                page.locator("#back-from-so").click()
                page.locator("#demo-role").select_option("Kasir")
                expect(page.locator("#price-log-panel")).to_be_hidden()
                open_diagnosis(page)
                revision = base.data(page)["revision"]
                page.locator("#create-service-order").click()
                expect(page.locator("#so-view")).to_be_visible()
                assert base.data(page)["revision"] == revision
                open_diagnosis(page, "DD 8921 AR")
                expect(page.locator("#diagnosis-findings")).to_be_disabled()
                page.evaluate("""() => {
                    const el = document.getElementById('diagnosis-findings'); el.disabled=false; el.value='Kasir write';
                    el.dispatchEvent(new Event('input', {bubbles:true}));
                    document.getElementById('save-diagnosis').dispatchEvent(new Event('click'));
                    document.getElementById('approve-diagnosis').dispatchEvent(new Event('click'));
                }""")
                assert base.data(page)["revision"] == revision
                passed("Kasir baca SO/diagnosa; handler mutasi dan log lengkap dibatasi pada simulasi")

                page.locator("#demo-role").select_option("Teknisi")
                payload = '<img src=x onerror="window.injected=true">'
                page.locator("#diagnosis-findings").fill(payload)
                page.locator("#diagnosis-recommendations").fill("Pemeriksaan tambahan contoh")
                add(page, "part-filter")
                saved(page)
                assert base.data(page)["diagnoses"][-1]["items"][0]["masterPrice"] == 100000
                assert not page.evaluate("Boolean(window.injected)")
                assert page.locator("#diagnosis-view img").count() == 0
                fail_writes(page)
                page.locator("#diagnosis-findings").fill("Isian lokal tetap ada")
                page.locator("#demo-role").select_option("Kasir")
                expect(page.locator("#demo-role")).to_have_value("Teknisi")
                expect(page.locator("#diagnosis-findings")).to_have_value("Isian lokal tetap ada")
                restore_writes(page)
                page.locator("#storage-retry").click()
                saved(page)
                passed("Snapshot harga katalog tetap; markup aman; role switch ditahan saat draf gagal disimpan")

                other = ctx.new_page()
                base.loaded(other)
                open_diagnosis(other, "DD 8921 AR")
                page.locator("#diagnosis-findings").fill("Draf lokal setelah konflik")
                other.locator("#diagnosis-findings").fill("Pemeriksaan tab kedua")
                other.locator("#save-diagnosis").click()
                expect(page.locator("#storage-alert-title")).to_have_text("Data berubah di tab lain")
                page.locator("#storage-retry").click()
                expect(page.locator("#diagnosis-findings")).to_have_value("Draf lokal setelah konflik")
                page.locator("#back-from-diagnosis").click()
                open_diagnosis(page, "DD 8921 AR")
                expect(page.locator("#diagnosis-findings")).to_have_value("Draf lokal setelah konflik")
                other.close()
                passed("Konflik draf estimasi mempertahankan isian lokal dan menyimpannya saat kembali")

                item(page).locator("[name=unitPrice]").fill("")
                saved(page)
                item(page).locator("[name=unitPrice]").fill("90000")
                item(page).locator("[name=priceReason]").fill("Harga setelah input kosong")
                saved(page)
                log = base.data(page)["diagnoses"][-1]["priceChanges"]
                assert log[-1]["oldPrice"] == 100000 and log[-1]["newPrice"] == 90000
                item(page).locator("[name=priceReason]").fill("")
                item(page).locator("[name=unitPrice]").fill("80000")
                saved(page)
                assert base.data(page)["diagnoses"][-1]["priceChanges"][-1]["reason"] == ""
                fail_writes(page)
                item(page).locator("[name=priceReason]").fill("Alasan A gagal disimpan")
                expect(page.locator("#diagnosis-save-status")).to_contain_text("Belum tersimpan")
                assert base.data(page)["diagnoses"][-1]["priceChanges"][-1]["reason"] == ""
                item(page).locator("[name=priceReason]").fill("Alasan diisi setelah autosave")
                restore_writes(page)
                page.locator("#storage-retry").click()
                saved(page)
                log = base.data(page)["diagnoses"][-1]["priceChanges"]
                assert log[-1]["reason"] == "Alasan diisi setelah autosave"
                assert log[-1]["reasonRecordedBy"] == "Teknisi"
                passed("Log harga melewati input kosong dan alasan terlambat tetap lengkap dengan provenance")
                passed("Reason gagal write tidak mencemari state; retry hanya menyimpan alasan yang berhasil")

                approver = ctx.new_page()
                base.loaded(approver)
                open_diagnosis(approver, "DD 8921 AR")
                approver.locator("#verbal-approval").check()
                page.evaluate("""() => {
                    const original = window.setTimeout;
                    window.setTimeout = (callback, delay, ...args) => original(callback, delay === 400 ? 60000 : delay, ...args);
                }""")
                page.locator("#diagnosis-findings").fill("Isian lokal saat tab lain menyetujui")
                approver.locator("#approve-diagnosis").click()
                expect(page.locator("#storage-alert-title")).to_have_text("Data berubah di tab lain")
                locked_snapshot = copy.deepcopy(base.data(page)["diagnoses"][-1])
                page.once("dialog", lambda dialog: dialog.dismiss())
                page.locator("#storage-retry").click()
                expect(page.locator("#diagnosis-findings")).to_have_value("Isian lokal saat tab lain menyetujui")
                expect(page.locator("#storage-alert")).to_be_visible()
                page.evaluate("document.getElementById('diagnosis-form').requestSubmit()")
                assert base.data(page)["diagnoses"][-1] == locked_snapshot
                page.once("dialog", lambda dialog: dialog.accept())
                page.locator("#storage-retry").click()
                expect(page.locator("#diagnosis-status")).to_have_text("Disetujui")
                expect(page.locator("#diagnosis-findings")).to_have_value(locked_snapshot["findings"])
                expect(page.locator("#storage-alert")).to_be_hidden()
                approver.close()
                passed("Approval tab lain: menolak penggantian mempertahankan isian; menerima membuka snapshot terkunci")

                page.reload()
                page.locator("#demo-role").select_option("Teknisi")
                open_diagnosis(page, "DD 5672 TS")
                page.locator("#diagnosis-findings").fill("Evaporator kotor dan filter kabin tersumbat. Aliran udara melemah setelah AC digunakan.")
                page.locator("#diagnosis-recommendations").fill("Bersihkan evaporator, ganti filter kabin, lalu periksa kembali suhu dan aliran udara.")
                add(page, "service-clean")
                add(page, "part-filter")
                saved(page)
                final_store = base.data(page)
                for width, label in ((1440, "desktop"), (768, "tablet"), (390, "mobile")):
                    page.set_viewport_size({"width": width, "height": 950})
                    for theme in ("light", "dark"):
                        if page.locator("html").get_attribute("data-theme") != theme:
                            page.locator("#theme-toggle").click()
                        base.no_overflow(page)
                        page.evaluate("window.scrollTo(0,0)")
                        page.screenshot(path=str(OUT / f"phase2-{label}-{theme}.png"), full_page=True, animations="disabled")
                for width in (320, 620, 1049, 1050):
                    page.set_viewport_size({"width": width, "height": 950})
                    base.no_overflow(page)
                page.set_viewport_size({"width": 390, "height": 950})
                page.evaluate("document.documentElement.style.fontSize='200%'")
                base.no_overflow(page)
                page.evaluate("document.documentElement.style.fontSize=''")
                page.locator("#diagnosis-findings").focus()
                page.keyboard.press("Tab")
                expect(page.locator("#diagnosis-recommendations")).to_be_focused()
                passed("Desktop/tablet/mobile light-dark, 320px, teks 200%, Tab/fokus diperiksa")
                ctx.close()

                corruptions = []
                bad = copy.deepcopy(final_store); bad["diagnoses"] = {}; corruptions.append(bad)
                bad = copy.deepcopy(final_store); bad["diagnoses"][0]["registrationId"] = "missing"; corruptions.append(bad)
                bad = copy.deepcopy(final_store); bad["serviceOrders"][0]["estimateTotal"] += 1; corruptions.append(bad)
                bad = copy.deepcopy(final_store); bad["serviceOrders"].append(copy.deepcopy(bad["serviceOrders"][0])); corruptions.append(bad)
                for bad in corruptions:
                    bad_ctx = browser.new_context()
                    bad_page = bad_ctx.new_page()
                    base.loaded(bad_page)
                    raw = json.dumps(bad)
                    bad_page.evaluate("([key,raw]) => localStorage.setItem(key,raw)", [base.KEY, raw])
                    bad_page.reload()
                    expect(bad_page.locator("#storage-alert")).to_be_visible()
                    assert bad_page.evaluate("key => localStorage.getItem(key)", base.KEY) == raw
                    bad_ctx.close()
                passed("Collection/relasi rusak, total SO salah dan duplikasi SO ditolak tanpa menimpa data")
                assert not errors, errors
                passed("Tidak ada console/page error pada alur normal")
            finally:
                browser.close()
    finally:
        server.shutdown(); server.server_close(); thread.join()
    report = {"passed": True, "checked_at": datetime.now(timezone.utc).isoformat(), "checks": checks, "console_errors": errors, "limitations": ["Dummy Chromium headless only", "Client role guards are simulation, not server auth", "Sequential localStorage conflict detection, not atomic concurrency", "SO handoff only; progress and payments not implemented"]}
    (OUT / "verification-phase2.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{len(checks)} phase-two checks passed")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        OUT.mkdir(exist_ok=True)
        name = "failure-phase2-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f") + ".json"
        (OUT / name).write_text(json.dumps({"passed": False, "error": str(exc), "checks_completed": checks}, ensure_ascii=False, indent=2), encoding="utf-8")
        raise
