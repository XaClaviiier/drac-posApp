"""SO realization acceptance checks on isolated dummy browser storage."""

import copy
import json
import threading
from pathlib import Path
from datetime import datetime, timezone
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

from playwright.sync_api import expect, sync_playwright
import phase1_browser as base
import phase2_browser as phase2
import phase3a_browser as phase3a

checks = []
errors = []


def passed(name):
    checks.append({"check": name, "passed": True})
    print("PASS", name)


def rows(page):
    return page.locator("#actual-items .estimate-item")


def submit(page, reason="Penyesuaian realisasi contoh", approval=False):
    page.locator("#actual-reason").fill(reason)
    if approval:
        page.locator("#actual-approval").check()
    page.locator("#actual-save").click()


def add(page, catalog_id):
    page.locator("#actual-catalog").select_option(catalog_id)
    page.locator("#actual-add").click()


def reset(page, accept=True):
    page.once("dialog", lambda d: d.accept() if accept else d.dismiss())
    page.locator("#actual-reset").click()


def synthetic_submit(page):
    page.evaluate("document.getElementById('actual-form').requestSubmit()")


def legacy_store():
    return json.loads((Path(__file__).parent / "fixtures" / "phase2-store.json").read_text(encoding="utf-8"))


def inject_store(page, store):
    raw = json.dumps(store)
    page.evaluate("([key,value]) => localStorage.setItem(key,value)", [base.KEY, raw])
    page.reload()
    return raw


def legacy_compatibility(page):
    for with_workflow in (False, True):
        store = legacy_store()
        if with_workflow:
            store["serviceOrders"][0]["workflow"] = {
                "status": "ready", "technicianId": None, "startedAt": None,
                "completedAt": None, "cancelledAt": None, "history": [],
            }
        raw = inject_store(page, store)
        expect(page.locator("#storage-alert")).to_be_hidden(timeout=1500)
        phase3a.open_order(page)
        expect(page.locator("#actual-total")).to_contain_text("90.000")
        assert page.evaluate("key => localStorage.getItem(key)", base.KEY) == raw
    passed("Fixture pra-3B qty numerik/leading zero, dengan/tanpa workflow, terbaca tanpa rewrite")


def diagnosis_privacy(page):
    store = legacy_store()
    store["diagnoses"][0]["items"][0]["quantity"] = "1"
    inject_store(page, store)
    phase2.open_diagnosis(page)
    marker = "LEGACY_OWNER_ONLY_REASON"
    expect(page.locator("#price-log-list")).to_contain_text(marker)
    page.locator("#price-log-panel summary").click()
    for role in ("Teknisi", "Kasir"):
        for leave_first in (False, True):
            page.locator("#demo-role").select_option("Owner")
            phase2.open_diagnosis(page)
            expect(page.locator("#price-log-list")).to_contain_text(marker)
            if leave_first:
                page.locator("#nav-orders").click()
            page.locator("#demo-role").select_option(role)
            expect(page.locator("#price-log-list li")).to_have_count(0)
            assert marker not in page.locator("#price-log-list").text_content()
            assert not page.locator("#price-log-panel").evaluate("el => el.open")
    assert base.data(page) == store
    passed("Log harga Diagnosa hilang dari DOM Teknisi/Kasir pada halaman aktif maupun tersembunyi")


def estimate_overflow(page):
    store = legacy_store()
    store["serviceOrders"] = []
    diagnosis = store["diagnoses"][0]
    diagnosis.update(status="draft", approvedAt=None, approvedBy=None, priceChanges=[])
    template = diagnosis["items"][0]
    diagnosis["items"] = [dict(template, id=f"overflow-{i}", quantity="999999", unitPrice="1000000000") for i in range(10)]
    inject_store(page, store)
    phase2.open_diagnosis(page)
    page.locator("#verbal-approval").check()
    page.locator("#approve-diagnosis").click()
    expect(page.locator("#items-error")).to_contain_text("kapasitas angka")
    expect(page.locator("#estimate-items [name=quantity]").first).to_be_focused()
    assert base.data(page) == store
    passed("Overflow agregat estimasi menolak approval dengan pesan/fokus, tanpa write")


def capacity_limits(page):
    store = legacy_store()
    store["diagnoses"][0]["items"][0]["quantity"] = "1"
    order = store["serviceOrders"][0]
    before = [dict(order["items"][0], quantity="1")]
    actual = [dict(before[0], id=f"limit-{i}", unitPrice=0) for i in range(100)]
    order["realization"] = {"items": actual, "history": [{
        "id": "limit-entry", "at": order["createdAt"], "actor": "Owner", "workflowCount": 0,
        "reason": "Seratus baris contoh", "approved": True, "before": before, "after": copy.deepcopy(actual),
    }]}
    inject_store(page, store)
    phase3a.open_order(page)
    expect(rows(page)).to_have_count(100)
    page.locator("#actual-add").click()
    expect(page.locator("#actual-error")).to_contain_text("100 baris")
    assert base.data(page) == store
    rows(page).last.get_by_role("button").click()
    add(page, "part-filter")
    expect(rows(page)).to_have_count(100)
    submit(page, approval=True)
    expect(page.locator("#actual-status")).to_have_text("Realisasi tersimpan di perangkat ini")
    assert len(phase3a.order(page)["realization"]["items"]) == 100

    store = legacy_store()
    store["diagnoses"][0]["items"][0]["quantity"] = "1"
    order = store["serviceOrders"][0]
    before = [dict(order["items"][0], quantity="1")]
    history = []
    for i in range(199):
        after = [dict(before[0], unitPrice=80000 if i % 2 == 0 else 90000)]
        history.append({"id": f"revision-{i}", "at": order["createdAt"], "actor": "Owner", "workflowCount": 0,
                        "reason": "Revisi contoh", "approved": i % 2 == 1, "before": before, "after": after})
        before = after
    order["realization"] = {"items": before, "history": history}
    inject_store(page, store)
    phase3a.open_order(page)
    rows(page).first.locator("[name=unitPrice]").fill("79000")
    submit(page)
    assert len(phase3a.order(page)["realization"]["history"]) == 200
    saved = base.data(page)
    rows(page).first.locator("[name=unitPrice]").fill("78000")
    submit(page)
    expect(page.locator("#actual-error")).to_contain_text("200 revisi")
    expect(rows(page).first.locator("[name=unitPrice]")).to_have_value("78000")
    assert base.data(page) == saved
    reset(page)
    passed("Batas 100 baris dan 200 revisi sah; penambahan berikutnya ditolak tanpa write atau pemangkasan")


def realization_overflow(page):
    store = legacy_store()
    store["diagnoses"][0]["items"][0]["quantity"] = "1"
    inject_store(page, store)
    phase3a.open_order(page)
    for i in range(10):
        if i:
            add(page, "part-filter")
        rows(page).last.locator("[name=quantity]").fill("999999")
        rows(page).last.locator("[name=unitPrice]").fill("1000000000")
    submit(page, approval=True)
    expect(page.locator("#actual-error")).to_contain_text("kapasitas angka")
    expect(rows(page)).to_have_count(10)
    assert base.data(page) == store
    reset(page)
    passed("Overflow agregat realisasi mempertahankan input dan tidak menulis")


def closure_checks(browser):
    failures = []
    for case in (legacy_compatibility, diagnosis_privacy, estimate_overflow, capacity_limits, realization_overflow):
        ctx = browser.new_context(viewport={"width": 1440, "height": 1000}, locale="id-ID")
        try:
            page = ctx.new_page()
            page.on("pageerror", lambda e: errors.append(str(e)))
            base.loaded(page)
            case(page)
        except Exception as exc:
            failures.append(f"{case.__name__}: {exc}")
        finally:
            ctx.close()
    assert not failures, "\n".join(failures)


def main():
    server = ThreadingHTTPServer(("127.0.0.1", 0), partial(SimpleHTTPRequestHandler, directory=str(base.ROOT)))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base.URL = f"http://127.0.0.1:{server.server_port}/prototype/"
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            try:
                closure_checks(browser)
                ctx = browser.new_context(viewport={"width": 1440, "height": 1000}, locale="id-ID")
                page = ctx.new_page()
                page.on("pageerror", lambda e: errors.append(str(e)))
                base.loaded(page)
                snapshot = phase3a.create_order(page)
                catalog_before = page.evaluate("JSON.stringify(window.POSItems.catalog)")
                diagnosis_before = copy.deepcopy(base.data(page)["diagnoses"])
                expect(page.locator("#actual-form")).to_be_visible(timeout=2000)
                expect(page.locator("#actual-status")).to_contain_text("belum dicatat")
                before = base.data(page)
                page.reload()
                phase3a.open_order(page)
                assert base.data(page) == before
                passed("SO lama terbaca tanpa write dan editor realisasi terpisah tersedia")
                assert snapshot["estimateTotal"] == 100000
                rows(page).first.locator("[name=unitPrice]").fill("90000")
                submit(page)
                expect(page.locator("#actual-status")).to_have_text("Realisasi tersimpan di perangkat ini")
                real = phase3a.order(page)["realization"]
                assert real["items"][0]["unitPrice"] == 90000
                assert real["history"][0]["before"][0]["unitPrice"] == 100000
                assert phase3a.order(page)["items"] == snapshot["items"]
                page.reload()
                phase3a.open_order(page)
                expect(page.locator("#actual-total")).to_contain_text("90.000")
                passed("Harga lokal dan history tersimpan setelah reload; snapshot estimasi tetap")

                revision = base.data(page)["revision"]
                submit(page)
                expect(page.locator("#actual-error")).to_contain_text("Tidak ada perubahan")
                assert base.data(page)["revision"] == revision
                for invalid in ("0", "-1", "0.5", "1000000", "1e3", ""):
                    rows(page).first.locator("[name=quantity]").fill(invalid)
                    submit(page)
                    expect(rows(page).first.locator("[name=quantity]")).to_have_attribute("aria-invalid", "true")
                    assert base.data(page)["revision"] == revision
                rows(page).first.locator("[name=quantity]").fill("1")
                for invalid in ("-1", "0.5", "1e3", "1000000001", ""):
                    rows(page).first.locator("[name=unitPrice]").fill(invalid)
                    submit(page)
                    expect(rows(page).first.locator("[name=unitPrice]")).to_have_attribute("aria-invalid", "true")
                    assert base.data(page)["revision"] == revision
                reset(page)
                add(page, "part-refrigerant")
                rows(page).last.locator("[name=quantity]").fill("0,500")
                rows(page).last.locator("[name=unitPrice]").fill("1")
                expect(page.locator("#actual-total")).to_contain_text("90.001")
                submit(page)
                expect(page.locator("#actual-error")).to_contain_text("persetujuan")
                assert base.data(page)["revision"] == revision
                page.locator("#actual-approval").check()
                rows(page).last.locator("[name=quantity]").fill("0.499")
                expect(page.locator("#actual-approval")).not_to_be_checked()
                expect(page.locator("#actual-total")).to_contain_text("90.000")
                rows(page).last.locator("[name=quantity]").fill("0.5001")
                submit(page, approval=True)
                expect(page.locator("#actual-error")).to_contain_text("3 desimal")
                rows(page).last.locator("[name=quantity]").fill("0.500")
                submit(page, reason=" ", approval=True)
                expect(page.locator("#actual-reason")).to_be_focused()
                submit(page, approval=True)
                real = phase3a.order(page)["realization"]
                assert real["items"][-1]["quantity"] == "0.5"
                assert real["history"][-1]["approved"] is True
                assert len(real["history"]) == 2
                passed("Angka invalid/no-op/alasan kosong ditolak; koma, 3 desimal, setengah naik dan approval per revisi tepat")

                for product, quantity, price in (("part-oil", "0.001", "499"), ("part-hose", "0.001", "500"), ("service-hour", "1.125", "1000")):
                    add(page, product)
                    rows(page).last.locator("[name=quantity]").fill(quantity)
                    rows(page).last.locator("[name=unitPrice]").fill(price)
                expect(page.locator("#actual-parts")).to_contain_text("90.002")
                expect(page.locator("#actual-services")).to_contain_text("1.125")
                expect(page.locator("#actual-total")).to_contain_text("91.127")
                submit(page, approval=True)
                page.reload()
                phase3a.open_order(page)
                expect(page.locator("#actual-total")).to_contain_text("91.127")
                assert phase3a.order(page)["realization"]["items"][-1]["quantity"] == "1.125"
                assert base.data(page)["diagnoses"] == diagnosis_before
                assert page.evaluate("JSON.stringify(window.POSItems.catalog)") == catalog_before
                passed("Kg/liter/meter/jam dihitung desimal tetap; pembulatan per baris sebelum total")

                net_before = base.data(page)
                rows(page).first.locator("[name=unitPrice]").fill("88000")
                add(page, "service-check")
                rows(page).last.locator("[name=unitPrice]").fill("1000")
                expect(page.locator("#actual-total")).to_contain_text("90.127")
                submit(page)
                expect(page.locator("#actual-error")).to_contain_text("persetujuan")
                assert base.data(page) == net_before
                submit(page, approval=True)
                passed("Item tambahan tetap perlu approval saat total bersih turun")

                revision = base.data(page)["revision"]
                rows(page).first.locator("[name=unitPrice]").fill("80000")
                phase2.fail_writes(page)
                submit(page, "Alasan gagal simpan harus bertahan")
                expect(page.locator("#storage-alert")).to_be_visible()
                assert base.data(page)["revision"] == revision
                phase2.restore_writes(page)
                page.locator("#storage-retry").click()
                expect(rows(page).first.locator("[name=unitPrice]")).to_have_value("80000")
                expect(page.locator("#actual-reason")).to_have_value("Alasan gagal simpan harus bertahan")
                assert base.data(page)["revision"] == revision
                page.locator("#actual-save").click()
                expect(page.locator("#actual-status")).to_have_text("Realisasi tersimpan di perangkat ini")
                passed("Quota gagal tidak menulis history; retry menjaga input tanpa replay; simpan eksplisit berhasil")

                rows(page).first.locator("[name=unitPrice]").fill("70000")
                page.locator("#actual-reason").fill("Isian lokal untuk konflik")
                page.once("dialog", lambda d: d.dismiss())
                page.locator("#nav-registration").click()
                expect(page.locator("#so-view")).to_be_visible()
                reset(page, accept=False)
                expect(rows(page).first.locator("[name=unitPrice]")).to_have_value("70000")
                page.locator("#actual-approval").check()
                page.locator("#demo-role").select_option("Kasir")
                expect(page.locator("#actual-approval")).not_to_be_checked()
                expect(rows(page).first.locator("[name=unitPrice]")).to_be_disabled()
                assert page.locator("#actual-history li").count() == 0
                synthetic_submit(page)
                expect(page.locator("#actual-error")).to_contain_text("tidak mengizinkan")
                page.locator("#demo-role").select_option("Teknisi")
                expect(rows(page).first.locator("[name=unitPrice]")).to_have_value("70000")
                other = ctx.new_page()
                base.loaded(other)
                phase3a.open_order(other)
                rows(other).first.locator("[name=unitPrice]").fill("75000")
                submit(other, "Perubahan tersimpan dari tab kedua")
                expect(page.locator("#storage-alert-title")).to_have_text("Data berubah di tab lain")
                latest = copy.deepcopy(base.data(page))
                page.locator("#storage-retry").click()
                expect(rows(page).first.locator("[name=unitPrice]")).to_have_value("70000")
                expect(page.locator("#actual-save")).to_be_disabled()
                synthetic_submit(page)
                expect(page.locator("#actual-error")).to_contain_text("sudah berubah")
                assert base.data(page) == latest
                reset(page)
                expect(rows(page).first.locator("[name=unitPrice]")).to_have_value("75000")
                other.close()
                passed("Dirty guard/role menjaga isian; history Owner dibersihkan; konflik realisasi tidak dapat ditimpa atau direplay")

                rows(page).first.locator("[name=unitPrice]").fill("74000")
                page.locator("#actual-approval").check()
                other = ctx.new_page()
                base.loaded(other)
                phase3a.open_order(other)
                phase3a.apply_action(other, "started", tech="tech-a")
                expect(page.locator("#storage-alert-title")).to_have_text("Data berubah di tab lain")
                page.locator("#storage-retry").click()
                expect(page.locator("#actual-approval")).not_to_be_checked()
                expect(rows(page).first.locator("[name=unitPrice]")).to_have_value("74000")
                expect(page.locator("#so-status")).to_have_text("Dalam Pengerjaan")
                other.close()
                page.locator("#actual-reason").fill("Isian harus bertahan setelah unload dibatalkan")
                before_unload = base.data(page)
                page.once("dialog", lambda dialog: dialog.dismiss())
                with page.expect_event("dialog", predicate=lambda dialog: dialog.type == "beforeunload"):
                    page.close(run_before_unload=True)
                assert not page.is_closed()
                expect(rows(page).first.locator("[name=unitPrice]")).to_have_value("74000")
                expect(page.locator("#actual-reason")).to_have_value("Isian harus bertahan setelah unload dibatalkan")
                assert base.data(page) == before_unload
                passed("Konflik workflow membatalkan approval tanpa membuang isian; unload dibatalkan menjaga input/storage")
                submit(page)
                phase3a.apply_action(page, "completed")
                revision = base.data(page)["revision"]
                synthetic_submit(page)
                assert base.data(page)["revision"] == revision
                page.locator("#demo-role").select_option("Owner")
                rows(page).first.locator("[name=unitPrice]").fill("73000")
                payload = '<img src=x onerror="window.injected=true">'
                submit(page, payload)
                expect(page.locator("#so-status")).to_have_text("Selesai")
                page.locator("#actual-log summary").click()
                expect(page.locator("#actual-history")).to_contain_text(payload)
                assert page.locator("#actual-history img").count() == 0
                assert not page.evaluate("Boolean(window.injected)")
                phase3a.apply_action(page, "reopened", "Peninjauan ulang contoh")
                phase3a.apply_action(page, "cancelled", "Sisa pekerjaan dibatalkan contoh")
                costs_before_cancel_edit = copy.deepcopy(phase3a.order(page)["realization"]["items"])
                assert costs_before_cancel_edit
                page.locator("#demo-role").select_option("Teknisi")
                revision = base.data(page)["revision"]
                synthetic_submit(page)
                assert base.data(page)["revision"] == revision
                page.locator("#demo-role").select_option("Owner")
                rows(page).last.get_by_role("button").click()
                submit(page, "Kurangi pekerjaan yang tidak dilaksanakan")
                expect(page.locator("#so-status")).to_have_text("Dibatalkan")
                assert len(phase3a.order(page)["realization"]["items"]) == len(costs_before_cancel_edit) - 1
                assert phase3a.order(page)["items"] == snapshot["items"]
                assert not base.data(page).get("invoices")
                passed("Progres tidak membuang realisasi; lock Teknisi terminal; Owner revisi tanpa reopen; markup menjadi teks")

                page.locator("#actual-log").evaluate("el => {el.open = true;}")
                rows(page).first.locator("[name=quantity]").fill("0")
                submit(page)
                for width, zoom in ((320, ""), (390, "200%")):
                    page.set_viewport_size({"width": width, "height": 1000})
                    page.evaluate("size => document.documentElement.style.fontSize = size", zoom)
                    base.no_overflow(page)
                    page.screenshot(path=str(base.OUT / f"phase3b-history-error-{width}.png"), full_page=True, animations="disabled")
                page.evaluate("document.documentElement.style.fontSize = ''")
                page.set_viewport_size({"width": 1440, "height": 1000})
                reset(page)
                passed("Editor dirty, error dan riwayat Owner terbuka tidak overflow pada 320px/teks 200%")

                # Exercise estimate fractional quantities through the same user journey.
                page.locator("#so-back-list").click()
                phase2.open_diagnosis(page, "DD 8921 AR")
                page.locator("#diagnosis-findings").fill("Refrigeran berkurang (contoh)")
                page.locator("#diagnosis-recommendations").fill("Isi berdasarkan berat contoh")
                phase2.add(page, "part-refrigerant")
                phase2.item(page).locator("[name=quantity]").fill("0.125")
                phase2.item(page).locator("[name=unitPrice]").fill("4")
                phase2.item(page).locator("[name=priceReason]").fill("Harga uji pembulatan")
                page.locator("#save-diagnosis").click()
                expect(page.locator("#estimate-total")).to_contain_text("1")
                page.locator("#verbal-approval").check()
                page.locator("#approve-diagnosis").click()
                page.locator("#create-service-order").click()
                copied = phase3a.order(page, 1)
                assert copied["estimateTotal"] == 1
                assert copied["items"][0]["quantity"] == "0.125"
                submit(page, "Realisasi awal sesuai estimasi")
                for width, name in ((1440, "desktop"), (768, "tablet"), (390, "mobile")):
                    page.set_viewport_size({"width": width, "height": 1000})
                    for theme in ("light", "dark"):
                        if page.locator("html").get_attribute("data-theme") != theme:
                            page.locator("#theme-toggle").click()
                        base.no_overflow(page)
                        page.evaluate("window.scrollTo(0,0)")
                        page.screenshot(path=str(base.OUT / f"phase3b-{name}-{theme}.png"), full_page=True, animations="disabled")
                for width in (320, 620, 1049, 1050, 1280):
                    page.set_viewport_size({"width": width, "height": 1000})
                    base.no_overflow(page)
                page.set_viewport_size({"width": 390, "height": 1000})
                page.evaluate("document.documentElement.style.fontSize='200%'")
                base.no_overflow(page)
                page.evaluate("document.documentElement.style.fontSize=''")
                rows(page).first.locator("[name=quantity]").fill("0")
                page.locator("#actual-save").focus()
                page.keyboard.press("Enter")
                expect(rows(page).first.locator("[name=quantity]")).to_be_focused()
                expect(rows(page).first.locator("[name=quantity]")).to_have_attribute("aria-invalid", "true")
                page.keyboard.press("Tab")
                expect(rows(page).first.locator("[name=unitPrice]")).to_be_focused()
                reset(page)
                rows(page).first.get_by_role("button").click()
                submit(page, "Tidak ada biaya aktual untuk kunjungan ini")
                assert phase3a.order(page, 1)["realization"]["items"] == []
                expect(page.locator("#actual-empty")).to_be_visible()
                page.reload()
                page.locator("#menu-toggle").click()
                phase3a.open_order(page, "DD 8921 AR")
                expect(page.locator("#actual-empty")).to_be_visible()
                passed("Estimasi pecahan tersalin tepat; realisasi kosong pulih; desktop/tablet/mobile tema, 320px/200% dan keyboard lulus")

                final_store = copy.deepcopy(base.data(page))
                ctx.close()

                corruptions = (
                    lambda s: s["serviceOrders"][0].update(realization=None),
                    lambda s: s["serviceOrders"][0]["realization"]["items"][0].update(quantity="1.5"),
                    lambda s: s["serviceOrders"][0]["realization"]["history"][0].update(actor="Kasir"),
                    lambda s: s["serviceOrders"][0]["realization"]["history"][1].update(approved=False),
                    lambda s: s["serviceOrders"][0]["realization"]["history"][0].update(reason=" "),
                    lambda s: s["serviceOrders"][0]["realization"]["history"][0]["before"][0].update(unitPrice=1),
                    lambda s: s["serviceOrders"][0]["realization"]["history"][0].update(at="invalid"),
                    lambda s: s["serviceOrders"][0]["realization"]["history"][1].update(id=s["serviceOrders"][0]["realization"]["history"][0]["id"]),
                    lambda s: s["serviceOrders"][0]["realization"]["history"][-1].update(actor="Teknisi"),
                    lambda s: s["serviceOrders"][0]["realization"]["history"][-1].update(workflowCount=0),
                )
                for mutate in corruptions:
                    bad = copy.deepcopy(final_store)
                    mutate(bad)
                    badctx = browser.new_context()
                    badpage = badctx.new_page()
                    base.loaded(badpage)
                    raw = json.dumps(bad)
                    badpage.evaluate("([key,value]) => localStorage.setItem(key,value)", [base.KEY, raw])
                    badpage.reload()
                    expect(badpage.locator("#storage-alert")).to_be_visible()
                    assert badpage.evaluate("key => localStorage.getItem(key)", base.KEY) == raw
                    badctx.close()
                passed("Realisasi null, angka/history/approval/role/basis/waktu palsu ditolak tanpa reseed")
                assert not errors, errors
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join()
    report = {"passed": True, "checked_at": datetime.now(timezone.utc).isoformat(), "checks": checks, "console_errors": errors}
    (base.OUT / "verification-phase3b.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{len(checks)} phase-3B checks passed")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        name = "failure-phase3b-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f") + ".json"
        (base.OUT / name).write_text(json.dumps({"passed": False, "error": str(exc), "checks_completed": checks}, ensure_ascii=False, indent=2), encoding="utf-8")
        raise
