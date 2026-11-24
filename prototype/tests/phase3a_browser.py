"""Browser acceptance checks for SO progress; only isolated dummy browser data."""

import copy
import json
import threading
from datetime import datetime, timezone
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

from playwright.sync_api import expect, sync_playwright
import phase1_browser as base
import phase2_browser as phase2

OUT = base.OUT
checks = []
errors = []


def passed(name):
    checks.append({"check": name, "passed": True})
    print("PASS", name)


def create_order(page, plate="DD 1248 KL"):
    phase2.open_diagnosis(page, plate)
    page.locator("#diagnosis-findings").fill("Filter kabin kotor, aliran udara berkurang.")
    page.locator("#diagnosis-recommendations").fill("Ganti filter kabin dan periksa suhu AC.")
    phase2.add(page, "part-filter")
    page.locator("#save-diagnosis").click()
    page.locator("#verbal-approval").check()
    page.locator("#approve-diagnosis").click()
    page.locator("#create-service-order").click()
    expect(page.locator("#so-view")).to_be_visible()
    return copy.deepcopy(base.data(page)["serviceOrders"][-1])


def order(page, index=0):
    return base.data(page)["serviceOrders"][index]


def apply_action(page, action, reason="", tech=None, accept=True):
    page.locator("#so-action").select_option(action)
    if tech:
        page.locator("#so-technician-select").select_option(tech)
    page.locator("#so-reason").fill(reason)
    if action in ("completed", "cancelled", "reopened"):
        page.once("dialog", lambda dialog: dialog.accept() if accept else dialog.dismiss())
    page.locator("#so-apply-action").click()


def open_order(page, plate="DD 1248 KL"):
    page.locator("#nav-orders").click()
    page.locator("#orders-list .so-record").filter(has_text=plate).get_by_role("button").click()


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
                page.on("pageerror", lambda e: errors.append(str(e)))
                base.loaded(page)
                page.locator("#nav-orders").click()
                expect(page.locator("#orders-view")).to_be_visible(timeout=3000)
                expect(page.locator("#orders-empty")).to_be_visible()
                passed("Menu SO membuka empty state dan entry ke diagnosa")
                page.locator("#orders-to-diagnoses").click()
                expect(page.locator("#diagnoses-view")).to_be_visible()
                snapshot = create_order(page)
                assert "workflow" not in snapshot
                before_open = base.data(page)["revision"]
                page.locator("#so-back-list").click()
                page.locator("#order-search").fill("dd1248kl")
                expect(page.locator("#orders-list .so-record")).to_have_count(1)
                page.locator("#order-filter").select_option("completed")
                expect(page.locator("#orders-empty")).to_be_visible()
                page.locator("#order-filter").select_option("all")
                page.locator("#orders-list .so-record").get_by_role("button").click()
                expect(page.locator("#so-status")).to_have_text("Belum dimulai")
                assert base.data(page)["revision"] == before_open
                expect(page.locator("#so-history-empty")).to_be_visible()
                passed("SO lama tanpa workflow terbaca tanpa rewrite; cari/filter/detail/kosong bekerja")

                page.locator("#so-apply-action").click()
                expect(page.locator("#so-action-error")).to_contain_text("Pilih teknisi")
                expect(page.locator("#so-technician-select")).to_be_focused()
                expect(page.locator("#so-technician-select")).to_have_attribute("aria-invalid", "true")
                assert "workflow" not in order(page)
                apply_action(page, "assigned", tech="tech-a")
                assert order(page)["workflow"]["status"] == "ready"
                expect(page.locator("#so-technician")).to_have_text("Teknisi A (contoh)")
                apply_action(page, "started", tech="tech-a")
                expect(page.locator("#so-status")).to_have_text("Dalam Pengerjaan")
                assert len(order(page)["workflow"]["history"]) == 2
                assert order(page)["items"] == snapshot["items"]
                assert order(page)["estimateTotal"] == snapshot["estimateTotal"]
                page.reload()
                open_order(page)
                expect(page.locator("#so-status")).to_have_text("Dalam Pengerjaan")
                passed("Mulai wajib teknisi; assignment/start tersimpan setelah reload tanpa mengubah estimasi")

                revision = base.data(page)["revision"]
                apply_action(page, "paused")
                expect(page.locator("#so-action-error")).to_contain_text("Isi alasan")
                assert base.data(page)["revision"] == revision
                apply_action(page, "paused", "Menunggu komponen contoh")
                expect(page.locator("#so-status")).to_have_text("Ditunda")
                assert page.locator("#so-action option[value=completed]").count() == 0
                page.evaluate("""() => {
                    const action=document.getElementById('so-action');
                    action.add(new Option('Palsu', 'completed')); action.value='completed';
                    document.getElementById('so-progress-form').requestSubmit();
                }""")
                expect(page.locator("#so-action-error")).to_contain_text("tidak diizinkan")
                assert order(page)["workflow"]["status"] == "paused"
                apply_action(page, "assigned", tech="tech-b")
                expect(page.locator("#so-action-error")).to_contain_text("alasan pergantian")
                apply_action(page, "assigned", "Pergantian jadwal contoh", tech="tech-b")
                apply_action(page, "resumed")
                expect(page.locator("#so-status")).to_have_text("Dalam Pengerjaan")
                passed("Tunda beralasan, ganti teknisi, lanjutkan; complete dari paused ditolak di handler")

                saved = copy.deepcopy(base.data(page))
                for role in ("Owner", "Teknisi"):
                    page.locator("#demo-role").select_option(role)
                    page.locator("#so-action").select_option("completed")
                    page.locator("#so-apply-action").click()
                    expect(page.locator("#so-action-error")).to_contain_text("Simpan realisasi")
                    expect(page.locator("#actual-reason")).to_be_focused()
                    assert base.data(page) == saved
                    assert "realization" not in order(page)
                page.locator("#actual-reason").fill("Pencatatan awal sesuai estimasi")
                page.locator("#actual-save").click()
                assert len(order(page)["realization"]["history"]) == 1
                saved = copy.deepcopy(base.data(page))
                page.locator("#actual-items [name=unitPrice]").first.fill("90000")
                page.locator("#so-action").select_option("completed")
                page.locator("#so-apply-action").click()
                expect(page.locator("#so-action-error")).to_contain_text("Simpan perubahan realisasi")
                expect(page.locator("#actual-reason")).to_be_focused()
                expect(page.locator("#actual-items [name=unitPrice]").first).to_have_value("90000")
                assert base.data(page) == saved
                page.locator("#actual-reason").fill("Biaya akhir sesuai pekerjaan contoh")
                page.locator("#actual-save").click()
                assert len(order(page)["realization"]["history"]) == 2
                passed("Owner/Teknisi wajib menyimpan realisasi; editor dirty menahan selesai tanpa autosave atau riwayat baru")

                revision = base.data(page)["revision"]
                apply_action(page, "completed", accept=False)
                assert base.data(page)["revision"] == revision
                apply_action(page, "completed")
                expect(page.locator("#so-status")).to_have_text("Selesai")
                completed = copy.deepcopy(order(page))
                page.reload()
                open_order(page)
                assert order(page) == completed
                page.locator("#demo-role").select_option("Teknisi")
                expect(page.locator("#so-apply-action")).to_be_hidden()
                page.evaluate("""() => {
                    const action=document.getElementById('so-action');
                    action.add(new Option('Reopen palsu', 'reopened')); action.value='reopened';
                    document.getElementById('so-reason').value='Palsu';
                    document.getElementById('so-progress-form').requestSubmit();
                }""")
                assert order(page) == completed
                page.locator("#demo-role").select_option("Owner")
                apply_action(page, "reopened", "Pemeriksaan ulang oleh Owner")
                expect(page.locator("#so-status")).to_have_text("Dalam Pengerjaan")
                assert order(page)["workflow"]["completedAt"] is None
                assert order(page)["workflow"]["startedAt"] == completed["workflow"]["startedAt"]
                passed("Konfirmasi selesai bisa dibatalkan; hanya Owner membuka kembali dengan history tetap")

                page.locator("#demo-role").select_option("Kasir")
                open_order(page)
                revision = base.data(page)["revision"]
                expect(page.locator("#so-action")).to_be_disabled()
                page.evaluate("""() => {
                    const action=document.getElementById('so-action'); action.add(new Option('Palsu','paused')); action.value='paused';
                    document.getElementById('so-reason').value='Kasir tidak boleh';
                    document.getElementById('so-progress-form').requestSubmit();
                }""")
                assert base.data(page)["revision"] == revision
                page.locator("#demo-role").select_option("Teknisi")
                phase2.fail_writes(page)
                apply_action(page, "paused", "Isian dipertahankan saat quota penuh")
                expect(page.locator("#storage-alert")).to_be_visible()
                assert base.data(page)["revision"] == revision
                assert order(page)["workflow"]["status"] == "in_progress"
                phase2.restore_writes(page)
                page.locator("#storage-retry").click()
                expect(page.locator("#so-reason")).to_have_value("Isian dipertahankan saat quota penuh")
                assert base.data(page)["revision"] == revision
                page.locator("#so-apply-action").click()
                expect(page.locator("#so-status")).to_have_text("Ditunda")
                passed("Kasir read-only; gagal write mempertahankan input, retry tidak replay status")

                apply_action(page, "resumed")
                page.locator("#so-action").select_option("paused")
                page.locator("#so-reason").fill("Catatan lokal belum diterapkan")
                page.once("dialog", lambda dialog: dialog.dismiss())
                page.locator("#nav-registration").click()
                expect(page.locator("#so-view")).to_be_visible()
                expect(page.locator("#so-reason")).to_have_value("Catatan lokal belum diterapkan")
                page.locator("#demo-role").select_option("Kasir")
                expect(page.locator("#so-reason")).to_have_value("Catatan lokal belum diterapkan")
                expect(page.locator("#so-reason")).to_be_disabled()
                page.locator("#demo-role").select_option("Teknisi")
                other = ctx.new_page()
                base.loaded(other)
                open_order(other)
                apply_action(other, "paused", "Keputusan dari tab lain")
                expect(page.locator("#storage-alert-title")).to_have_text("Data berubah di tab lain")
                latest_revision = base.data(page)["revision"]
                page.locator("#storage-retry").click()
                expect(page.locator("#so-reason")).to_have_value("Catatan lokal belum diterapkan")
                expect(page.locator("#so-status")).to_have_text("Ditunda")
                page.locator("#so-apply-action").click()
                expect(page.locator("#so-action-error")).to_contain_text("tidak diizinkan")
                assert base.data(page)["revision"] == latest_revision
                page.locator("#so-clear-action").click()
                expect(page.locator("#so-reason")).to_have_value("")
                expect(page.locator("#so-action")).to_be_focused()
                other.close()
                passed("Isian bertahan saat role/conflict; tindakan stale tidak replay, navigasi meminta konfirmasi")

                page.locator("#so-open-registration").click()
                expect(page.locator("#detail-plate")).to_have_text("DD 1248 KL")
                page.locator("#open-diagnosis").click()
                expect(page.locator("#diagnosis-status")).to_have_text("Disetujui")
                page.locator("#create-service-order").click()
                expect(page.locator("#so-status")).to_have_text("Ditunda")
                passed("Tautan registrasi/diagnosa/SO kembali ke dokumen yang sama")

                apply_action(page, "resumed")
                payload = '<img src=x onerror="window.injected=true">'
                apply_action(page, "paused", payload)
                expect(page.locator("#so-history")).to_contain_text(payload)
                assert page.locator("#so-history img").count() == 0
                assert not page.evaluate("Boolean(window.injected)")
                apply_action(page, "cancelled", "Pelanggan menghentikan sisa pekerjaan", accept=False)
                assert order(page)["workflow"]["status"] == "paused"
                apply_action(page, "cancelled", "Pelanggan menghentikan sisa pekerjaan")
                expect(page.locator("#so-status")).to_have_text("Dibatalkan")
                page.locator("#demo-role").select_option("Owner")
                expect(page.locator("#so-apply-action")).to_be_hidden()
                assert order(page)["items"] == snapshot["items"]
                assert order(page)["estimateTotal"] == 100000
                passed("Markup menjadi teks; pembatalan terminal berkonfirmasi dan mempertahankan estimasi/history")

                page.locator("#so-back-list").click()
                page.locator("#order-search").fill("")
                snapshot2 = create_order(page, "DD 8921 AR")
                apply_action(page, "started", tech="tech-c")
                apply_action(page, "paused", "Menunggu pemeriksaan lanjutan contoh")
                valid_store = copy.deepcopy(base.data(page))
                for width, name in ((1440,"desktop"),(768,"tablet"),(390,"mobile")):
                    page.set_viewport_size({"width":width,"height":950})
                    for theme in ("light","dark"):
                        if page.locator("html").get_attribute("data-theme") != theme:
                            page.locator("#theme-toggle").click()
                        base.no_overflow(page)
                        page.screenshot(path=str(OUT/f"phase3a-{name}-{theme}.png"),full_page=True,animations="disabled")
                for width in (320,620,1049,1050):
                    page.set_viewport_size({"width":width,"height":950}); base.no_overflow(page)
                page.set_viewport_size({"width":390,"height":950})
                page.evaluate("document.documentElement.style.fontSize='200%'"); base.no_overflow(page)
                page.evaluate("document.documentElement.style.fontSize=''")
                page.locator("#so-action").select_option("assigned")
                page.locator("#so-action").focus()
                page.keyboard.press("Tab")
                expect(page.locator("#so-technician-select")).to_be_focused()
                page.locator("#so-action").select_option("cancelled")
                page.locator("#so-apply-action").focus(); page.keyboard.press("Enter")
                expect(page.locator("#so-reason")).to_be_focused()
                expect(page.locator("#so-reason")).to_have_attribute("aria-invalid","true")
                page.locator("#so-clear-action").click()
                expect(page.locator("#so-action")).to_be_focused()
                passed("Form/detail/history 320px dan 200%, Tab, keyboard submit, error fokus dan reset diverifikasi")
                page.locator("#so-back-list").click()
                page.screenshot(path=str(OUT/"phase3a-list-mobile.png"),full_page=True,animations="disabled")
                for width in (320,620,1049,1050):
                    page.set_viewport_size({"width":width,"height":950}); base.no_overflow(page)
                page.set_viewport_size({"width":390,"height":950})
                page.evaluate("document.documentElement.style.fontSize='200%'"); base.no_overflow(page)
                page.evaluate("document.documentElement.style.fontSize=''")
                passed("Desktop/tablet/mobile light-dark, 320px dan teks 200% tidak overflow")
                ctx.close()

                corruptions=[]
                for mutate in (
                    lambda s: s["serviceOrders"][0].update(workflow=None),
                    lambda s: s["serviceOrders"][0]["workflow"].update(status="completed"),
                    lambda s: s["serviceOrders"][0]["workflow"]["history"][0].update(actor="Kasir"),
                    lambda s: s["serviceOrders"][0]["workflow"]["history"][-1].update(reason=""),
                    lambda s: s["serviceOrders"][0]["workflow"]["history"][0].update(at="invalid"),
                    lambda s: s["serviceOrders"][0]["workflow"]["history"][1].update(id=s["serviceOrders"][0]["workflow"]["history"][0]["id"]),
                    lambda s: s["serviceOrders"][0]["workflow"]["history"][0].update(technicianAfter="not-a-tech"),
                    lambda s: s["serviceOrders"][0]["workflow"]["history"][1].update(from_state="forged", **{"from":"paused"}),
                    lambda s: s["serviceOrders"][0]["workflow"]["history"][1].update(at="2000-01-01T00:00:00.000Z"),
                ):
                    malformed=copy.deepcopy(valid_store); mutate(malformed); corruptions.append(malformed)
                for malformed in corruptions:
                    badctx=browser.new_context(); badpage=badctx.new_page(); base.loaded(badpage)
                    raw=json.dumps(malformed)
                    badpage.evaluate("([k,v])=>localStorage.setItem(k,v)",[base.KEY,raw]); badpage.reload()
                    expect(badpage.locator("#storage-alert")).to_be_visible()
                    assert badpage.evaluate("key=>localStorage.getItem(key)",base.KEY)==raw
                    badctx.close()
                passed("Workflow/null/status palsu/aktor/alasan/waktu rusak ditolak tanpa menimpa raw data")
                assert not errors, errors
            finally:
                browser.close()
    finally:
        server.shutdown(); server.server_close(); thread.join()
    report = {"passed": True, "checked_at": datetime.now(timezone.utc).isoformat(), "checks": checks, "console_errors": errors}
    (OUT / "verification-phase3a.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{len(checks)} phase-3A checks passed")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        OUT.mkdir(exist_ok=True)
        name = "failure-phase3a-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f") + ".json"
        (OUT / name).write_text(json.dumps({"passed": False, "error": str(exc), "checks_completed": checks}, ensure_ascii=False, indent=2), encoding="utf-8")
        raise
