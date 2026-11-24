"""Invoice and full-payment acceptance checks on isolated dummy stores."""
import copy
import json
import threading
from datetime import datetime, timezone
from functools import partial
from http.server import ThreadingHTTPServer

from playwright.sync_api import expect, sync_playwright
import phase1_browser as base
import phase2_browser as phase2
import phase3a_browser as phase3a
import phase3b_browser as phase3b
import phase3c_browser as phase3c

checks, errors = [], []


class BrowserServer(ThreadingHTTPServer):
    # Fresh Chromium contexts request the page's scripts concurrently.
    request_queue_size = 128


def passed(name):
    checks.append({"check": name, "passed": True})
    print("PASS", name)


def prepare(page):
    phase3a.create_order(page)
    phase3b.submit(page, "Realisasi untuk invoice contoh")
    phase3a.apply_action(page, "started", tech="tech-a")
    phase3a.apply_action(page, "completed")
    phase3c.send(page)


def invoice(page):
    return base.data(page)["invoices"][0]


def confirm_click(page, selector, accept=True):
    page.once("dialog", lambda d: d.accept() if accept else d.dismiss())
    page.locator(selector).click()


def open_invoice(page):
    page.locator("#nav-invoices").click()
    page.locator("#invoice-list button").first.click()


def correct(page, price, reason="Koreksi harga contoh"):
    page.locator("[name=invoicePrice]").first.fill(str(price))
    page.locator("#invoice-reason").fill(reason)
    confirm_click(page, "#invoice-save-price")


def new_page(browser):
    ctx = browser.new_context(viewport={"width": 1440, "height": 1000}, locale="id-ID")
    page = ctx.new_page()
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.on("console", lambda msg: errors.append(msg.text) if msg.type == "error" else None)
    requests_failed = []
    def failed(request):
        requests_failed.append(f"{request.url}: {request.failure}")
    page.on("requestfailed", failed)
    try:
        base.loaded(page)
    except Exception as exc:
        raise AssertionError(f"Initial load failed; requests: {requests_failed!r}; browser errors: {errors!r}; {exc}") from exc
    finally:
        page.remove_listener("requestfailed", failed)
    return ctx, page


def roles_and_zero(browser):
    ctx, page = new_page(browser)
    try:
        raw = page.evaluate("key=>localStorage.getItem(key)", base.KEY)
        page.locator("#nav-invoices").click()
        expect(page.locator("#invoice-empty")).to_be_visible()
        assert page.evaluate("key=>localStorage.getItem(key)", base.KEY) == raw
        prepare(page)
        source = copy.deepcopy(phase3a.order(page))
        page.locator("#demo-role").select_option("Teknisi")
        page.locator("#so-invoice").dispatch_event("click")
        assert not base.data(page).get("invoices")
        page.locator("#demo-role").select_option("Kasir")
        phase3a.open_order(page)
        page.locator("#so-invoice").click()
        initial = copy.deepcopy(base.data(page))
        page.locator("#nav-orders").click()
        page.locator("#orders-list button").click()
        page.locator("#so-invoice").click()
        assert base.data(page) == initial
        for role in ("Teknisi", "Kasir"):
            page.locator("#demo-role").select_option(role)
            expect(page.locator("[name=invoicePrice]").first).to_be_disabled()
            page.evaluate("document.getElementById('invoice-price-form').requestSubmit()")
            expect(page.locator("#invoice-error")).to_contain_text("Peran")
            assert base.data(page) == initial
        page.locator("#demo-role").select_option("Teknisi")
        page.locator("#invoice-issue").dispatch_event("click")
        page.evaluate("document.getElementById('payment-form').requestSubmit()")
        assert base.data(page) == initial
        passed("Legacy/kosong tanpa rewrite, satu invoice per SO; Teknisi baca dan Kasir tidak mengedit harga")

        page.locator("#demo-role").select_option("Owner")
        page.locator("#invoice-reason").fill("Tidak ada perubahan harga")
        page.locator("#invoice-save-price").click()
        expect(page.locator("#invoice-error")).to_contain_text("Belum ada perubahan harga")
        assert base.data(page) == initial
        for value in ("-1", "1e3", "1000000001", ""):
            page.locator("[name=invoicePrice]").first.fill(value)
            page.locator("#invoice-reason").fill("Uji harga invalid")
            page.locator("#invoice-save-price").click()
            expect(page.locator("#invoice-error")).to_contain_text("Harga harus")
            assert base.data(page) == initial
        page.locator("[name=invoicePrice]").first.fill("0")
        page.locator("#invoice-reason").fill("")
        page.locator("#invoice-save-price").click()
        expect(page.locator("#invoice-reason")).to_be_focused()
        page.locator("#invoice-reason").fill('<img src=x onerror="window.invoiceInjected=true"> Gratis contoh')
        page.locator("#invoice-save-price").click()
        assert phase3a.order(page) == source
        page.locator("#demo-role").select_option("Kasir")
        confirm_click(page, "#invoice-issue", accept=False)
        assert invoice(page)["history"][-1]["kind"] == "price"
        confirm_click(page, "#invoice-issue")
        expect(page.locator("#invoice-paid-state")).to_have_text("Lunas")
        assert not [e for e in invoice(page)["history"] if e["kind"] == "payment"]
        page.evaluate("document.getElementById('payment-received').value='0'; document.getElementById('payment-form').requestSubmit()")
        assert not [e for e in invoice(page)["history"] if e["kind"] == "payment"]
        expect(page.locator("#invoice-history li")).to_have_count(0)
        page.locator("#demo-role").select_option("Owner")
        expect(page.locator("#invoice-history")).to_contain_text("Gratis contoh")
        assert page.locator("#invoice-history img").count() == 0
        assert not page.evaluate("Boolean(window.invoiceInjected)")
        page.locator("#demo-role").select_option("Teknisi")
        expect(page.locator("#invoice-history li")).to_have_count(0)
        expect(page.locator("#payment-history li")).to_have_count(0)
        passed("Owner harga lokal beralasan/aman; invoice final Rp0 Lunas tanpa pembayaran; riwayat tidak bocor")
    finally:
        ctx.close()


def stale_draft(browser):
    ctx, page = new_page(browser)
    try:
        prepare(page)
        page.locator("#so-invoice").click()
        page.locator("[name=invoicePrice]").first.fill("90000")
        page.locator("#invoice-reason").fill("Harga draf lama")
        page.locator("#invoice-save-price").click()
        old = copy.deepcopy(invoice(page)["history"])
        phase3a.open_order(page)
        phase3c.withdraw(page)
        phase3b.rows(page).first.locator("[name=unitPrice]").fill("80000")
        phase3b.submit(page)
        phase3c.send(page)
        page.locator("#so-invoice").click()
        page.locator("#invoice-issue").dispatch_event("click")
        expect(page.locator("#invoice-error")).to_contain_text("Penyerahan SO berubah")
        assert invoice(page)["history"] == old
        page.locator("#demo-role").select_option("Kasir")
        page.locator("#invoice-rebase").dispatch_event("click")
        expect(page.locator("#invoice-error")).to_contain_text("Peran")
        page.locator("#demo-role").select_option("Owner")
        page.locator("#invoice-reason").fill("Memuat realisasi setelah penyerahan ulang")
        confirm_click(page, "#invoice-rebase")
        assert invoice(page)["history"][:-1] == old
        expect(page.locator("#invoice-total")).to_contain_text("80.000")
        confirm_click(page, "#invoice-issue")
        page.locator("#nav-cashier").click()
        expect(page.locator("#cashier-list .record")).to_have_count(1)
        expect(page.locator("#cashier-list")).to_contain_text("Belum Lunas")
        page.locator("#pos-stage").select_option("ready")
        expect(page.locator("#cashier-list .record")).to_have_count(0)
        phase3a.open_order(page)
        saved = base.data(page)
        page.evaluate("document.getElementById('handoff-withdraw').requestSubmit()")
        expect(page.locator("#handoff-error")).to_contain_text("sudah final")
        phase3b.synthetic_submit(page)
        assert base.data(page) == saved
        passed("Draf stale perlu rebase Owner eksplisit; final keluar antrean tetapi sumber SO tetap terkunci")
    finally:
        ctx.close()


def failure_and_dirty(browser):
    ctx, page = new_page(browser)
    try:
        prepare(page)
        page.locator("#so-invoice").click()
        saved = base.data(page)
        page.locator("[name=invoicePrice]").first.fill("90000")
        page.locator("#invoice-reason").fill("Alasan gagal write")
        phase2.fail_writes(page)
        page.locator("#invoice-save-price").click()
        expect(page.locator("#storage-alert")).to_be_visible()
        assert base.data(page) == saved
        phase2.restore_writes(page)
        page.locator("#storage-retry").click()
        expect(page.locator("[name=invoicePrice]").first).to_have_value("90000")
        expect(page.locator("#invoice-reason")).to_have_value("Alasan gagal write")
        assert base.data(page) == saved
        page.locator("#invoice-save-price").click()
        saved = base.data(page)
        page.locator("[name=invoicePrice]").first.fill("91000")
        page.once("dialog", lambda d: d.dismiss())
        page.locator("#nav-registration").click()
        expect(page.locator("#invoice-view")).to_be_visible()
        page.once("dialog", lambda d: d.dismiss())
        with page.expect_event("dialog", predicate=lambda d: d.type == "beforeunload"):
            page.close(run_before_unload=True)
        assert not page.is_closed()
        assert base.data(page) == saved
        confirm_click(page, "#invoice-reset")
        ctx.set_offline(True)
        page.locator("#invoice-issue").dispatch_event("click")
        expect(page.locator("#invoice-error")).to_contain_text("online")
        assert base.data(page) == saved
        ctx.set_offline(False)
        confirm_click(page, "#invoice-issue")
        saved = base.data(page)
        for raw in ("0", "1", "-1", "1e5", "9007199254740992", ""):
            page.locator("#payment-received").fill(raw)
            page.locator("#payment-save").click()
            expect(page.locator("#payment-error")).to_contain_text("seluruh sisa")
            assert base.data(page) == saved
        page.locator("#payment-received").fill("90000")
        phase2.fail_writes(page)
        confirm_click(page, "#payment-save")
        expect(page.locator("#storage-alert")).to_be_visible()
        assert base.data(page) == saved
        phase2.restore_writes(page)
        page.locator("#storage-retry").click()
        expect(page.locator("#payment-received")).to_have_value("90000")
        assert base.data(page) == saved
        passed("Quota gagal menjaga harga/alasan/pembayaran; retry tidak replay, dirty nav/unload dan offline menolak write")

        other = ctx.new_page()
        base.loaded(other); open_invoice(other)
        correct(other, 80000, "Perubahan basis pembayaran tab lain")
        expect(page.locator("#storage-alert-title")).to_have_text("Data berubah di tab lain")
        page.locator("#storage-retry").click()
        expect(page.locator("#payment-received")).to_have_value("90000")
        page.evaluate("document.getElementById('payment-form').requestSubmit()")
        expect(page.locator("#invoice-error")).to_contain_text("Basis invoice berubah")
        assert not [e for e in invoice(page)["history"] if e["kind"] == "payment"]
        confirm_click(page, "#invoice-reset")
        page.locator("#demo-role").select_option("Kasir")
        page.locator("#payment-received").fill("80000")
        confirm_click(page, "#payment-save")
        saved = base.data(page)
        page.evaluate("document.getElementById('payment-form').requestSubmit()")
        assert base.data(page) == saved
        assert invoice(page)["history"][-1]["actor"] == "Kasir"
        other.close()
        passed("Pembayaran stale tidak menimpa koreksi; setelah reset hanya sisa penuh dibayar, duplikasi ditolak")
    finally:
        ctx.close()


def malformed(browser, store):
    def payment(s):
        return next(e for e in s["invoices"][0]["history"] if e["kind"] == "payment")
    mutations = (
        lambda s: s.update(invoices=None),
        lambda s: s["invoices"].append(copy.deepcopy(s["invoices"][0])),
        lambda s: s["invoices"][0].update(orderId="missing"),
        lambda s: s["invoices"][0]["history"][0].update(actor="Teknisi"),
        lambda s: s["invoices"][0]["history"][0].update(handoffId="missing"),
        lambda s: s["invoices"][0]["history"][1].update(actor="Teknisi"),
        lambda s: s["invoices"][0]["history"][1]["items"][0].update(unitPrice=1),
        lambda s: payment(s).update(amount=1),
        lambda s: payment(s).update(amount=0),
        lambda s: payment(s).update(received=1),
        lambda s: payment(s).update(invoiceRevision=1),
        lambda s: payment(s).update(method="transfer", reference="ok"),
        lambda s: payment(s).update(method="gateway-demo", received=100000, gatewayAcknowledged=False),
        lambda s: payment(s).update(actor="Teknisi"),
        lambda s: payment(s).update(at="2020-01-01T00:00:00Z"),
        lambda s: s["invoices"][0]["history"][-1].update(actor="Kasir"),
        lambda s: s["invoices"][0]["history"][-1]["items"][0].update(quantity="2"),
        lambda s: s["invoices"][0]["history"][-1].update(reason=" "),
        lambda s: s["serviceOrders"][0]["handoff"]["history"].append(dict(s["serviceOrders"][0]["handoff"]["history"][-1], id="withdraw-after-final", state="withdrawn", actor="Owner", reason="Tidak sah")),
    )
    for mutate in mutations:
        bad = copy.deepcopy(store); mutate(bad)
        ctx, page = new_page(browser)
        try:
            raw = phase3b.inject_store(page, bad)
            expect(page.locator("#storage-alert")).to_be_visible()
            assert page.evaluate("key=>localStorage.getItem(key)", base.KEY) == raw
        finally:
            ctx.close()
    ctx, page = new_page(browser)
    try:
        assert page.evaluate("""store => {
            const changed = structuredClone(store);
            changed.invoices[0].history[0].reason = 'rewrite';
            try { POSInvoices.assertAppend(store,changed); return false; } catch { return true; }
        }""", store)
    finally:
        ctx.close()
    passed("19 history/sumber/aktor/nominal/lock palsu ditolak tanpa reseed; rewrite prefix ditolak")


def capacity(browser, store):
    data = copy.deepcopy(store)
    original = data["invoices"][0]["history"][0]
    history = [copy.deepcopy(original)]
    for index in range(1, 198):
        event = dict(copy.deepcopy(original), id=f"price-limit-{index}", kind="price", actor="Owner", reason="Perubahan harga contoh")
        event["items"][0]["unitPrice"] = 99999 if index % 2 else 100000
        history.append(event)
    data["invoices"][0]["history"] = history
    ctx, page = new_page(browser)
    try:
        phase3b.inject_store(page, data)
        open_invoice(page)
        confirm_click(page, "#invoice-issue")
        page.locator("#payment-received").fill("99999")
        confirm_click(page, "#payment-save")
        assert len(invoice(page)["history"]) == 200
        saved = base.data(page)
        page.locator("[name=invoicePrice]").first.fill("1")
        page.locator("#invoice-reason").fill("Tidak boleh memangkas riwayat")
        page.locator("#invoice-save-price").click()
        expect(page.locator("#invoice-error")).to_contain_text("200 peristiwa")
        assert base.data(page) == saved
        passed("Peristiwa invoice ke-200 tersimpan; ke-201 ditolak tanpa pemangkasan atau perubahan uang")
    finally:
        ctx.close()


def main():
    server = BrowserServer(("127.0.0.1", 0), partial(phase3c.QuietHandler, directory=str(base.ROOT)))
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
                prepare(page)
                source = copy.deepcopy(phase3a.order(page))
                page.locator("#so-invoice").click(timeout=2000)
                expect(page.locator("#invoice-view")).to_be_visible()
                expect(page.locator("#invoice-state")).to_have_text("Draf")
                expect(page.locator("#invoice-total")).to_contain_text("100.000")
                assert len(base.data(page)["invoices"]) == 1
                assert phase3a.order(page) == source
                confirm_click(page, "#invoice-issue")
                expect(page.locator("#invoice-state")).to_have_text("Final")
                expect(page.locator("#invoice-paid-state")).to_have_text("Belum Lunas")
                page.locator("#payment-received").fill("120000")
                confirm_click(page, "#payment-save")
                expect(page.locator("#invoice-paid-state")).to_have_text("Lunas")
                expect(page.locator("#payment-history")).to_contain_text("20.000")
                assert invoice(page)["history"][-1]["amount"] == 100000
                assert invoice(page)["history"][-1]["received"] == 120000
                passed("Antrean ke invoice final dan pembayaran penuh tunai dengan kembalian; SO tidak ditimpa")
                page.evaluate("() => { window.printCount=0; window.print=()=>{window.printCount++}; }")
                assert page.evaluate("window.printCount") == 0
                other = ctx.new_page()
                base.loaded(other)
                other.locator("#nav-invoices").click()
                other.locator("#invoice-list button").click()
                other.locator("[name=invoicePrice]").first.fill("110000")
                other.locator("#invoice-reason").fill("Koreksi biaya oleh tab kedua")
                confirm_click(other, "#invoice-save-price")
                expect(page.locator("#storage-alert-title")).to_have_text("Data berubah di tab lain")
                page.locator("#demo-role").select_option("Kasir")
                page.locator("#demo-role").select_option("Owner")
                page.evaluate("window.dispatchEvent(new Event('offline')); window.dispatchEvent(new Event('online'))")
                page.locator("#nav-invoices").click()
                page.locator("#invoice-list button").click()
                page.locator("#invoice-reason").fill("Isian lokal selama konflik")
                confirm_click(page, "#invoice-reset")
                page.locator("#invoice-print").dispatch_event("click")
                assert page.evaluate("window.printCount") == 0, "Konflik tidak boleh dibuka kembali oleh role/render"
                page.evaluate("window.dispatchEvent(new Event('beforeprint'))")
                page.emulate_media(media="print")
                expect(page.locator("#invoice-receipt")).to_be_hidden()
                page.emulate_media(media="screen")
                page.locator("#storage-retry").click()
                expect(page.locator("#invoice-total")).to_contain_text("110.000")
                expect(page.locator("#invoice-balance")).to_contain_text("10.000")
                page.locator("#invoice-print").click()
                assert page.evaluate("window.printCount") == 1
                other.close()
                passed("Konflik menjaga guard tombol/beforeprint sampai reload eksplisit; nominal/status terbaru sesuai")
                malformed_store = copy.deepcopy(base.data(page))
                paid_before = [e for e in invoice(page)["history"] if e["kind"] == "payment"]
                correct(page, 90000, "Penurunan setelah pembayaran")
                expect(page.locator("#invoice-overpaid")).to_contain_text("10.000")
                expect(page.locator("#invoice-paid-state")).to_have_text("Lunas")
                assert [e for e in invoice(page)["history"] if e["kind"] == "payment"] == paid_before
                correct(page, 130000, "Kenaikan setelah pembayaran")
                expect(page.locator("#invoice-balance")).to_contain_text("30.000")
                page.locator("#payment-method").select_option("transfer")
                page.locator("#payment-received").fill("29999")
                page.locator("#payment-save").click()
                expect(page.locator("#payment-error")).to_contain_text("seluruh sisa")
                page.locator("#payment-received").fill("30000")
                page.locator("#payment-save").click()
                expect(page.locator("#payment-error")).to_contain_text("referensi")
                page.locator("#payment-reference").fill("TRANSFER-CONTOH-001")
                confirm_click(page, "#payment-save")
                expect(page.locator("#invoice-paid-state")).to_have_text("Lunas")
                correct(page, 140000)
                page.locator("#payment-method").select_option("gateway-demo")
                page.locator("#payment-received").fill("10000")
                page.locator("#payment-save").click()
                expect(page.locator("#payment-error")).to_contain_text("simulasi gateway")
                page.locator("#gateway-ack").check()
                confirm_click(page, "#payment-save")
                expect(page.locator("#payment-history")).to_contain_text("Gateway — SIMULASI")
                expect(page.locator("#invoice-paid")).to_contain_text("140.000")
                passed("Koreksi menjaga uang lama dan kelebihan terpisah; transfer tepat/ref wajib, gateway wajib pengakuan simulasi")

                keyboard_before = base.data(page)
                page.locator("[name=invoicePrice]").first.focus()
                page.keyboard.press("Tab")
                expect(page.locator("#invoice-reason")).to_be_focused()
                page.keyboard.press("Tab")
                expect(page.locator("#invoice-save-price")).to_be_focused()
                page.keyboard.press("Enter")
                expect(page.locator("#invoice-reason")).to_be_focused()
                assert base.data(page) == keyboard_before
                passed("Tab harga/alasan/aksi dan Enter memicu validasi berfokus tanpa write")

                for width, name in ((1440, "desktop"), (768, "tablet"), (390, "mobile")):
                    page.set_viewport_size({"width": width, "height": 1000})
                    for theme in ("light", "dark"):
                        if page.locator("html").get_attribute("data-theme") != theme: page.locator("#theme-toggle").click()
                        base.no_overflow(page)
                        page.screenshot(path=str(base.OUT / f"phase4-invoice-{name}-{theme}.png"), full_page=True, animations="disabled")
                for width in (320, 620, 1049, 1050, 1280):
                    page.set_viewport_size({"width": width, "height": 1000}); base.no_overflow(page)
                page.set_viewport_size({"width": 390, "height": 1000})
                page.evaluate("document.documentElement.style.fontSize='200%'")
                base.no_overflow(page)
                page.evaluate("document.documentElement.style.fontSize=''")
                saved = base.data(page)
                page.evaluate("window.dispatchEvent(new Event('beforeprint'))")
                page.emulate_media(media="print")
                expect(page.locator("#invoice-receipt")).to_be_visible()
                expect(page.locator("#invoice-price-form")).to_be_hidden()
                expect(page.locator("#invoice-log")).to_be_hidden()
                expect(page.locator("#invoice-receipt")).to_contain_text("Lunas")
                assert page.evaluate("getComputedStyle(document.documentElement).backgroundColor") == "rgb(255, 255, 255)", "Kanvas cetak harus putih, termasuk dari tema gelap"
                page.screenshot(path=str(base.OUT / "phase4-print.png"), full_page=True, animations="disabled")
                page.emulate_media(media="screen")
                assert base.data(page) == saved
                passed("Light/dark desktop/tablet/mobile, 320px/200% dan cetak final tanpa kontrol/history atau write")
                ctx.close()
                roles_and_zero(browser)
                stale_draft(browser)
                failure_and_dirty(browser)
                malformed(browser, malformed_store)
                capacity(browser, malformed_store)
                assert not errors, errors
            finally:
                browser.close()
    finally:
        server.shutdown(); server.server_close(); thread.join()
    report = {"passed": True, "checked_at": datetime.now(timezone.utc).isoformat(), "checks": checks, "console_errors": errors}
    (base.OUT / "verification-phase4.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{len(checks)} phase-4 checks passed")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        name = "failure-phase4-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f") + ".json"
        (base.OUT / name).write_text(json.dumps({"passed": False, "error": str(exc), "checks_completed": checks, "console_errors": errors}, ensure_ascii=False, indent=2), encoding="utf-8")
        raise
