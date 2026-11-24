"""Cashier handoff acceptance checks; isolated dummy contexts only."""

import copy
import json
import threading
from datetime import datetime, timezone
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

from playwright.sync_api import expect, sync_playwright
import phase1_browser as base
import phase2_browser as phase2
import phase3a_browser as phase3a
import phase3b_browser as phase3b

checks, errors = [], []


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass


def passed(name):
    checks.append({"check": name, "passed": True})
    print("PASS", name)


def send(page, accept=True):
    page.once("dialog", lambda d: d.accept() if accept else d.dismiss())
    page.locator("#handoff-send").click()


def withdraw(page, reason="Periksa kembali biaya contoh", accept=True):
    page.locator("#handoff-reason").fill(reason)
    page.once("dialog", lambda d: d.accept() if accept else d.dismiss())
    page.locator("#handoff-withdraw-button").click()


def synthetic_send(page):
    page.locator("#handoff-send").dispatch_event("click")


def handoff_history(page, index=0):
    return phase3a.order(page, index).get("handoff", {}).get("history", [])


def invalid_history_checks(browser, store):
    def real_while_locked(s):
        order = s["serviceOrders"][0]
        event = copy.deepcopy(order["realization"]["history"][-1])
        event.update(id="injected-real", before=copy.deepcopy(order["realization"]["items"]), at=order["handoff"]["history"][-1]["at"])
        event["after"][0]["unitPrice"] -= 1
        order["realization"]["history"].append(event)
        order["realization"]["items"] = event["after"]

    def reopen_while_locked(s):
        order = s["serviceOrders"][0]
        workflow = order["workflow"]
        workflow["history"].append({"id": "injected-progress", "at": order["handoff"]["history"][-1]["at"], "actor": "Owner", "action": "reopened", "from": "completed", "to": "in_progress", "technicianBefore": "tech-a", "technicianAfter": "tech-a", "reason": "Reopen palsu"})
        workflow.update(status="in_progress", completedAt=None)

    def historical_lock(s):
        order = s["serviceOrders"][0]
        # A withdrawal cannot claim that another realization was saved while queued.
        order["handoff"]["history"][1]["realizationRevision"] = 2

    corruptions = (
        lambda s: s["serviceOrders"][0].update(handoff=None),
        lambda s: s["serviceOrders"][0].update(handoff={"history": []}),
        lambda s: s["serviceOrders"][0]["handoff"]["history"][0].update(actor="Kasir"),
        lambda s: s["serviceOrders"][0]["handoff"]["history"][0].update(workflowCount=1),
        lambda s: s["serviceOrders"][0]["handoff"]["history"][0].update(realizationRevision=0),
        lambda s: s["serviceOrders"][0]["handoff"]["history"][0].update(at="invalid"),
        lambda s: s["serviceOrders"][0]["handoff"]["history"][0].update(at="2020-01-01T00:00:00.000Z"),
        lambda s: s["serviceOrders"][0]["handoff"]["history"][1].update(reason=" "),
        lambda s: s["serviceOrders"][0]["handoff"]["history"][1].update(actor="Teknisi"),
        lambda s: s["serviceOrders"][0]["handoff"]["history"][1].update(state="queued"),
        lambda s: s["serviceOrders"][0]["handoff"]["history"][1].update(id=s["serviceOrders"][0]["handoff"]["history"][0]["id"]),
        lambda s: s["serviceOrders"][0]["handoff"]["history"][-1].update(realizationRevision=999),
        historical_lock, real_while_locked, reopen_while_locked,
    )
    for mutate in corruptions:
        bad = copy.deepcopy(store)
        mutate(bad)
        ctx = browser.new_context()
        try:
            page = ctx.new_page()
            base.loaded(page)
            raw = phase3b.inject_store(page, bad)
            expect(page.locator("#storage-alert")).to_be_visible()
            assert page.evaluate("key => localStorage.getItem(key)", base.KEY) == raw
        finally:
            ctx.close()
    passed("History malformed, referensi, aktor, waktu dan mutasi dalam lock ditolak tanpa reseed")


def terminal_eligibility_checks(browser):
    ctx = browser.new_context(viewport={"width": 1440, "height": 1000}, locale="id-ID")
    try:
        page = ctx.new_page()
        page.on("pageerror", lambda e: errors.append(str(e)))
        base.loaded(page)
        phase3a.create_order(page)
        phase3a.apply_action(page, "started", tech="tech-a")
        legacy = copy.deepcopy(base.data(page))
        workflow = legacy["serviceOrders"][0]["workflow"]
        at = datetime.now(timezone.utc).isoformat()
        workflow["history"].append({
            "id": "legacy-completed-without-realization", "at": at, "actor": "Teknisi",
            "action": "completed", "from": "in_progress", "to": "completed",
            "technicianBefore": "tech-a", "technicianAfter": "tech-a", "reason": "",
        })
        workflow.update(status="completed", completedAt=at)
        raw = phase3b.inject_store(page, legacy)
        expect(page.locator("#storage-alert")).to_be_hidden()
        phase3a.open_order(page)
        assert page.evaluate("key => localStorage.getItem(key)", base.KEY) == raw
        saved = base.data(page)
        for role in ("Owner", "Teknisi"):
            page.locator("#demo-role").select_option(role)
            synthetic_send(page)
            expect(page.locator("#handoff-error")).to_contain_text("Simpan realisasi")
            assert base.data(page) == saved
        page.locator("#demo-role").select_option("Owner")
        phase3b.submit(page, "Pencatatan akhir sesuai estimasi")
        saved = base.data(page)
        page.locator("#demo-role").select_option("Kasir")
        synthetic_send(page)
        expect(page.locator("#handoff-error")).to_contain_text("hanya Teknisi/Owner")
        assert base.data(page) == saved
        passed("Riwayat terminal legacy tanpa realisasi tetap terbaca tanpa rewrite; handoff Owner/Teknisi ditolak, Kasir tetap read-only")

        page.locator("#demo-role").select_option("Owner")
        phase3a.open_order(page)
        phase3a.apply_action(page, "reopened", "Catat pekerjaan tanpa biaya sebelum selesai")
        phase3b.rows(page).first.get_by_role("button").click()
        phase3b.submit(page, "Pekerjaan ini tanpa biaya contoh")
        assert phase3a.order(page)["realization"]["items"] == []
        phase3a.apply_action(page, "completed")
        send(page)
        expect(page.locator("#handoff-total")).to_contain_text("tanpa biaya, bukan status lunas")
        page.locator("#nav-cashier").click()
        expect(page.locator("#cashier-list")).to_contain_text("tanpa biaya")
        page.locator("#cashier-list button").click()
        page.locator("#pos-open-order").click()
        withdraw(page)
        phase3a.apply_action(page, "reopened", "Periksa ulang kunjungan contoh")
        phase3a.apply_action(page, "cancelled", "Kunjungan dibatalkan tanpa biaya")
        saved = base.data(page)
        synthetic_send(page)
        expect(page.locator("#handoff-error")).to_contain_text("tanpa biaya")
        assert base.data(page) == saved
        phase3b.add(page, "part-filter")
        phase3b.rows(page).first.locator("[name=unitPrice]").fill("70000")
        phase3b.submit(page, "Part sudah terpakai sebelum pembatalan", approval=True)
        saved = base.data(page)
        page.locator("#demo-role").select_option("Teknisi")
        synthetic_send(page)
        expect(page.locator("#handoff-error")).to_contain_text("Dibatalkan hanya Owner")
        assert base.data(page) == saved
        page.locator("#demo-role").select_option("Owner")
        send(page)
        page.locator("#nav-cashier").click()
        page.locator("#cashier-filter").select_option("cancelled")
        expect(page.locator("#cashier-list .record")).to_have_count(1)
        expect(page.locator("#cashier-list")).to_contain_text("70.000")
        assert phase3a.order(page)["estimateTotal"] == 100000
        passed("Selesai Rp0 berlabel tanpa biaya; Dibatalkan Rp0 ditolak, berbiaya hanya Owner dengan total realisasi")
    finally:
        ctx.close()


def capacity_checks(browser, store):
    data = copy.deepcopy(store)
    order = data["serviceOrders"][0]
    template = copy.deepcopy(order["handoff"]["history"][-1])
    order["handoff"]["history"] = [dict(template, id=f"handoff-limit-{i}", state="queued" if i % 2 == 0 else "withdrawn", actor="Owner", reason="Penarikan contoh" if i % 2 else "") for i in range(99)]
    ctx = browser.new_context(viewport={"width": 1440, "height": 1000})
    try:
        page = ctx.new_page()
        base.loaded(page)
        phase3b.inject_store(page, data)
        phase3a.open_order(page)
        withdraw(page)
        assert len(handoff_history(page)) == 100
        saved = base.data(page)
        synthetic_send(page)
        expect(page.locator("#handoff-error")).to_contain_text("100 peristiwa")
        assert base.data(page) == saved
        page.reload()
        phase3a.open_order(page)
        assert base.data(page) == saved
        passed("Peristiwa ke-100 tersimpan/pulih; ke-101 ditolak tanpa memangkas riwayat")
    finally:
        ctx.close()


def main():
    server = ThreadingHTTPServer(("127.0.0.1", 0), partial(QuietHandler, directory=str(base.ROOT)))
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
                page.on("console", lambda msg: errors.append(msg.text) if msg.type == "error" else None)
                base.loaded(page)
                page.locator("#nav-cashier").click(timeout=2000)
                expect(page.locator("#cashier-view")).to_be_visible()
                expect(page.locator("#cashier-empty")).to_be_visible()
                passed("Antrean kasir membuka keadaan kosong dengan petunjuk dan tanpa invoice palsu")
                page.locator("#cashier-to-orders").click()
                phase3a.create_order(page)
                legacy = copy.deepcopy(base.data(page))
                raw_before = page.evaluate("key => localStorage.getItem(key)", base.KEY)
                page.reload()
                phase3a.open_order(page)
                assert page.evaluate("key => localStorage.getItem(key)", base.KEY) == raw_before
                synthetic_send(page)
                expect(page.locator("#handoff-error")).to_contain_text("Tutup pekerjaan")
                assert base.data(page) == legacy
                passed("SO legacy tanpa handoff terbaca tanpa write; SO aktif tidak bisa diserahkan")
                phase3b.submit(page, "Rincian akhir sesuai pekerjaan contoh")
                phase3a.apply_action(page, "started", tech="tech-a")
                phase3a.apply_action(page, "completed")
                before = copy.deepcopy(base.data(page))
                send(page, accept=False)
                assert base.data(page) == before
                phase3b.rows(page).first.locator("[name=unitPrice]").fill("95000")
                synthetic_send(page)
                expect(page.locator("#handoff-error")).to_contain_text("bersihkan isian")
                assert base.data(page) == before
                phase3b.reset(page)
                passed("Konfirmasi batal dan editor dirty menolak penyerahan tanpa autosave")
                page.locator("#demo-role").select_option("Teknisi")
                page.once("dialog", lambda d: d.accept())
                page.locator("#handoff-send").click(timeout=2000)
                expect(page.locator("#handoff-status")).to_have_text("Dalam antrean kasir")
                assert phase3a.order(page)["items"] == before["serviceOrders"][0]["items"]
                assert phase3a.order(page)["realization"] == before["serviceOrders"][0]["realization"]
                page.locator("#demo-role").select_option("Kasir")
                page.locator("#nav-cashier").click()
                expect(page.locator("#cashier-list .record")).to_have_count(1)
                expect(page.locator("#cashier-list")).to_contain_text("100.000")
                passed("Teknisi menyerahkan realisasi Selesai, Kasir melihat antrean tepat tanpa mengubah biaya")
                queued_store = copy.deepcopy(base.data(page))
                page.locator("#cashier-search").fill("tidak ditemukan")
                expect(page.locator("#cashier-empty")).to_be_visible()
                page.locator("#cashier-search").fill("DD1248KL")
                expect(page.locator("#cashier-list .record")).to_have_count(1)
                page.locator("#cashier-filter").select_option("cancelled")
                expect(page.locator("#cashier-list .record")).to_have_count(0)
                page.locator("#cashier-filter").select_option("all")
                page.locator("#cashier-list .record button").click()
                page.locator("#pos-open-order").click()
                expect(page.locator("#so-identity")).to_contain_text("DD 1248 KL")
                synthetic_send(page)
                page.evaluate("document.getElementById('handoff-withdraw').requestSubmit()")
                assert base.data(page) == queued_store
                page.locator("#demo-role").select_option("Owner")
                phase3b.synthetic_submit(page)
                expect(page.locator("#actual-error")).to_contain_text("tidak mengizinkan")
                page.evaluate("""() => {
                    const option = new Option('Buka kembali', 'reopened');
                    document.getElementById('so-action').append(option);
                    document.getElementById('so-action').value = 'reopened';
                    document.getElementById('so-reason').value = 'Reopen buatan';
                    document.getElementById('so-progress-form').requestSubmit();
                }""")
                expect(page.locator("#so-action-error")).to_contain_text("antrean kasir")
                assert base.data(page) == queued_store
                passed("Queued mengunci biaya/reopen untuk Owner sekalipun; handler Kasir dan submit ganda tidak menulis")

                page.reload()
                phase3a.open_order(page)
                page.locator("#handoff-withdraw-button").click()
                expect(page.locator("#handoff-reason")).to_be_focused()
                assert base.data(page) == queued_store
                withdraw(page, accept=False)
                assert base.data(page) == queued_store
                reason = '<img src=x onerror="window.handoffInjected=true"> Periksa ulang biaya'
                withdraw(page, reason)
                expect(page.locator("#handoff-status")).to_have_text("Ditarik dari antrean")
                assert phase3a.order(page)["workflow"] == queued_store["serviceOrders"][0]["workflow"]
                assert phase3a.order(page)["realization"] == queued_store["serviceOrders"][0]["realization"]
                page.locator("#handoff-log summary").click()
                expect(page.locator("#handoff-history")).to_contain_text(reason)
                assert page.locator("#handoff-history img").count() == 0
                assert not page.evaluate("Boolean(window.handoffInjected)")
                phase3b.rows(page).first.locator("[name=unitPrice]").fill("90000")
                phase3b.submit(page)
                page.locator("#nav-cashier").click()
                expect(page.locator("#cashier-list .record")).to_have_count(0)
                phase3a.open_order(page)
                send(page)
                assert len(handoff_history(page)) == 3
                page.locator("#nav-cashier").click()
                expect(page.locator("#cashier-list .record")).to_have_count(1)
                expect(page.locator("#cashier-list")).to_contain_text("90.000")
                final_store = copy.deepcopy(base.data(page))
                assert final_store["diagnoses"] == before["diagnoses"]
                assert not final_store.get("invoices") and not final_store.get("payments")
                passed("Owner menarik beralasan lalu merevisi/menyerahkan ulang; riwayat aman dan antrean tidak duplikat")

                page.locator("#demo-role").select_option("Teknisi")
                expect(page.locator("#orders-view")).to_be_visible()
                expect(page.locator("#cashier-list .record")).to_have_count(0)
                expect(page.locator("#handoff-history li")).to_have_count(0)
                page.locator("#nav-cashier").dispatch_event("click")
                expect(page.locator("#cashier-view")).to_be_hidden()
                assert base.data(page) == final_store
                passed("Role switch keluar antrean dan membersihkan daftar/riwayat Owner dari DOM Teknisi")

                page.locator("#demo-role").select_option("Owner")
                phase3a.open_order(page)
                phase2.fail_writes(page)
                withdraw(page, "Alasan gagal write harus bertahan")
                expect(page.locator("#storage-alert")).to_be_visible()
                assert base.data(page) == final_store
                phase2.restore_writes(page)
                page.locator("#storage-retry").click()
                expect(page.locator("#handoff-reason")).to_have_value("Alasan gagal write harus bertahan")
                assert base.data(page) == final_store
                withdraw(page, "Penarikan setelah retry eksplisit")
                assert len(handoff_history(page)) == 4
                phase2.fail_writes(page)
                send(page)
                expect(page.locator("#storage-alert")).to_be_visible()
                assert len(handoff_history(page)) == 4
                phase2.restore_writes(page)
                page.locator("#storage-retry").click()
                assert len(handoff_history(page)) == 4
                send(page)
                assert len(handoff_history(page)) == 5
                passed("Gagal write penyerahan/penarikan mempertahankan state/isian; retry tidak replay")

                other = ctx.new_page()
                base.loaded(other)
                phase3a.open_order(other)
                page.locator("#handoff-reason").fill("Alasan lokal tertinggal")
                withdraw(other, "Penarikan tab kedua")
                latest = copy.deepcopy(base.data(page))
                expect(page.locator("#storage-alert-title")).to_have_text("Data berubah di tab lain")
                page.locator("#storage-retry").click()
                expect(page.locator("#handoff-reason")).to_have_value("Alasan lokal tertinggal")
                page.evaluate("document.getElementById('handoff-withdraw').requestSubmit()")
                assert base.data(page) == latest
                expect(page.locator("#handoff-error")).to_contain_text("masih dalam antrean")
                page.once("dialog", lambda d: d.dismiss())
                page.locator("#nav-cashier").click()
                expect(page.locator("#so-view")).to_be_visible()
                page.once("dialog", lambda d: d.accept())
                page.locator("#handoff-reset").click()
                send(page)
                other.close()
                passed("Konflik penarikan menahan aksi stale, menjaga alasan, dan navigasi dirty tidak membuang isian")

                page.locator("#nav-cashier").click()
                for width, name in ((1440, "desktop"), (768, "tablet"), (390, "mobile")):
                    page.set_viewport_size({"width": width, "height": 1000})
                    for theme in ("light", "dark"):
                        if page.locator("html").get_attribute("data-theme") != theme:
                            page.locator("#theme-toggle").click()
                        base.no_overflow(page)
                        page.screenshot(path=str(base.OUT / f"phase3c-queue-{name}-{theme}.png"), full_page=True, animations="disabled")
                for width in (320, 620, 1049, 1050, 1280):
                    page.set_viewport_size({"width": width, "height": 1000})
                    base.no_overflow(page)
                page.set_viewport_size({"width": 390, "height": 1000})
                page.evaluate("document.documentElement.style.fontSize='200%'")
                base.no_overflow(page)
                page.evaluate("document.documentElement.style.fontSize=''")
                page.locator("#cashier-list .record button").focus()
                page.keyboard.press("Enter")
                expect(page.locator("#pos-preview-heading")).to_be_focused()
                page.locator("#pos-open-order").focus()
                page.keyboard.press("Enter")
                expect(page.locator("#so-heading")).to_be_focused()
                page.locator("#handoff-withdraw-button").focus()
                page.keyboard.press("Enter")
                expect(page.locator("#handoff-reason")).to_be_focused()
                page.locator("#handoff-log").evaluate("el => {el.open=true;}")
                page.set_viewport_size({"width": 320, "height": 1000})
                base.no_overflow(page)
                page.screenshot(path=str(base.OUT / "phase3c-handoff-error-320.png"), full_page=True, animations="disabled")
                passed("Antrean light/dark desktop/tablet/mobile, 320px/200%, keyboard/fokus dan history/error diperiksa")
                ctx.close()
                terminal_eligibility_checks(browser)
                capacity_checks(browser, final_store)
                invalid_history_checks(browser, final_store)
                assert not errors, errors
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join()
    report = {"passed": True, "checked_at": datetime.now(timezone.utc).isoformat(), "checks": checks, "console_errors": errors}
    (base.OUT / "verification-phase3c.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{len(checks)} phase-3C checks passed")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        name = "failure-phase3c-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f") + ".json"
        (base.OUT / name).write_text(json.dumps({"passed": False, "error": str(exc), "checks_completed": checks}, ensure_ascii=False, indent=2), encoding="utf-8")
        raise
