"""Cashier POS workspace checks using existing Playwright/browser seams."""
import copy
import json
import threading
from datetime import datetime, timezone
from functools import partial
from playwright.sync_api import expect, sync_playwright
import phase1_browser as base
import phase2_browser as phase2
import phase3a_browser as phase3a
import phase3b_browser as phase3b
import phase3c_browser as phase3c
import phase4_browser as phase4

checks, errors = [], []
ROLE_KEY = "pos_browser_prototype_role"


def passed(name):
    checks.append({"check": name, "passed": True})
    print("PASS", name)


def ready(page, plate):
    phase3a.create_order(page, plate)
    phase3b.submit(page, "Realisasi untuk ruang kerja kasir")
    phase3a.apply_action(page, "started", tech="tech-a")
    phase3a.apply_action(page, "completed")
    phase3c.send(page)


def choose(page, plate):
    page.locator("#cashier-list .record").filter(has_text=plate).get_by_role("button").click()


def home(page):
    if page.locator("#menu-toggle").is_visible() and page.locator("#menu-toggle").get_attribute("aria-expanded") != "true":
        page.locator("#menu-toggle").click()
    page.locator("#nav-cashier").click()


def context(browser, store=None):
    ctx = browser.new_context(viewport={"width": 1440, "height": 1000}, locale="id-ID")
    page = ctx.new_page()
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.on("console", lambda msg: errors.append(msg.text) if msg.type == "error" else None)
    base.loaded(page)
    if store is not None:
        phase3b.inject_store(page, store)
    return ctx, page


def preferences_and_roles(browser, fixture):
    ctx, page = context(browser, fixture)
    try:
        raw = base.data(page)
        page.evaluate("([key,value]) => localStorage.setItem(key,value)", [ROLE_KEY, "invalid-role"])
        page.reload()
        expect(page.locator("#demo-role")).to_have_value("Owner")
        expect(page.locator("#list-view")).to_be_visible()
        assert base.data(page) == raw
        page.evaluate("""() => {
            const el=document.getElementById('demo-role'); el.add(new Option('Tidak sah','unknown'));
            el.value='unknown'; el.dispatchEvent(new Event('change',{bubbles:true}));
        }""")
        expect(page.locator("#demo-role")).to_have_value("Owner")
        assert base.data(page) == raw
        page.evaluate("""key => {
            window.originalPrefSet = Storage.prototype.setItem;
            Storage.prototype.setItem = function(k,v) { if(k === key) throw new DOMException('preference blocked','QuotaExceededError'); return window.originalPrefSet.call(this,k,v); };
        }""", ROLE_KEY)
        page.locator("#demo-role").select_option("Kasir")
        expect(page.locator("#cashier-view")).to_be_visible()
        expect(page.locator("#storage-alert")).to_be_hidden()
        assert base.data(page) == raw
        choose(page, "DD 8921 AR")
        page.locator("#pos-create-invoice").click()
        expect(page.locator("#invoice-identity")).to_contain_text("DD 8921 AR")
        assert len(base.data(page)["invoices"]) == len(raw["invoices"]) + 1
        passed("Preferensi invalid fallback Owner; write preferensi gagal tidak memblokir transaksi atau menulis ulang ledger")
    finally:
        ctx.close()

    ctx, page = context(browser, fixture)
    try:
        raw = base.data(page)
        page.evaluate("key => localStorage.setItem(key,'Kasir')", ROLE_KEY)
        page.add_init_script("""(() => {
            const original = Storage.prototype.getItem;
            Storage.prototype.getItem = function(key) {
                if (key === 'pos_browser_prototype_role') throw new DOMException('Preference read blocked','SecurityError');
                return original.call(this,key);
            };
        })();""")
        page.reload()
        assert page.evaluate("key => {try {localStorage.getItem(key); return false;} catch {return true;}}", ROLE_KEY)
        expect(page.locator("#demo-role")).to_have_value("Owner")
        expect(page.locator("#list-view")).to_be_visible()
        assert base.data(page) == raw
        passed("Read preferensi gagal fallback Owner tanpa merusak data transaksi")
    finally:
        ctx.close()

    ctx, page = context(browser, fixture)
    try:
        page.locator("#demo-role").select_option("Kasir")
        choose(page, "DD 8921 AR")
        saved = base.data(page)
        page.locator("#demo-role").select_option("Teknisi")
        expect(page.locator("#cashier-list .record")).to_have_count(0)
        expect(page.locator("#pos-preview-identity")).to_have_text("")
        expect(page.locator("#pos-preview-items")).to_be_empty()
        page.locator("#nav-cashier").dispatch_event("click")
        page.locator("#pos-create-invoice").dispatch_event("click")
        expect(page.locator("#cashier-view")).to_be_hidden()
        assert base.data(page) == saved
        page.reload()
        expect(page.locator("#demo-role")).to_have_value("Teknisi")
        expect(page.locator("#nav-cashier")).to_be_hidden()
        passed("Teknisi ditolak pada entry/handler POS, daftar/preview dibersihkan dan preferensi bukan login")
    finally:
        ctx.close()


def failures(browser, fixture):
    ctx, page = context(browser, fixture)
    try:
        page.locator("#demo-role").select_option("Kasir")
        choose(page, "DD 8921 AR")
        saved = base.data(page)
        phase2.fail_writes(page)
        page.locator("#pos-create-invoice").click()
        expect(page.locator("#storage-alert")).to_be_visible()
        expect(page.locator("#pos-preview-identity")).to_contain_text("DD 8921 AR")
        expect(page.locator("#invoice-view")).to_be_hidden()
        assert base.data(page) == saved
        phase2.restore_writes(page)
        page.locator("#storage-retry").click()
        expect(page.locator("#pos-create-invoice")).to_be_enabled()
        assert base.data(page) == saved
        ctx.set_offline(True)
        page.locator("#pos-create-invoice").dispatch_event("click")
        expect(page.locator("#invoice-view")).to_be_hidden()
        assert base.data(page) == saved
        ctx.set_offline(False)
        other = ctx.new_page()
        base.loaded(other)
        phase3a.open_order(other, "DD 8921 AR")
        other.locator("#so-invoice").click()
        newer = base.data(page)
        expect(page.locator("#storage-alert-title")).to_have_text("Data berubah di tab lain")
        page.locator("#pos-create-invoice").dispatch_event("click")
        assert base.data(page) == newer
        expect(page.locator("#invoice-view")).to_be_hidden()
        page.locator("#storage-retry").click()
        page.locator("#pos-create-invoice").click()
        expect(page.locator("#invoice-identity")).to_contain_text("DD 8921 AR")
        assert base.data(page) == newer
        assert len([i for i in newer["invoices"] if i["orderId"] == newer["serviceOrders"][1]["id"]]) == 1
        other.close()
        passed("Create gagal/offline/konflik menjaga preview dan pilihan, retry tidak replay atau menggandakan invoice")
    finally:
        ctx.close()


def projection_edges(browser, fixture):
    ctx, page = context(browser, fixture)
    try:
        phase3a.open_order(page)
        phase3c.withdraw(page, "Periksa realisasi sebelum invoice final")
        saved = base.data(page)
        page.locator("#demo-role").select_option("Kasir")
        expect(page.locator("#cashier-list .record").filter(has_text="DD 1248 KL")).to_contain_text("Perlu Owner")
        choose(page, "DD 1248 KL")
        expect(page.locator("#invoice-source-note")).to_contain_text("ditarik")
        page.locator("#invoice-issue").dispatch_event("click")
        expect(page.locator("#invoice-error")).to_contain_text("Penyerahan SO berubah")
        assert base.data(page) == saved
        passed("Draf stale tetap terlihat bertanda Perlu Owner dan tidak dapat diterbitkan Kasir")
    finally:
        ctx.close()
    ctx, page = context(browser, fixture)
    try:
        page.locator("#nav-invoices").click()
        page.locator("#invoice-list .record").filter(has_text="DD 5672 TS").get_by_role("button").click()
        page.locator("#payment-received").fill("100000")
        phase4.confirm_click(page, "#payment-save")
        phase4.correct(page, 110000)
        saved = base.data(page)
        home(page)
        expect(page.locator("#cashier-list .record").filter(has_text="DD 5672 TS")).to_contain_text("Sisa Rp 10.000")
        assert base.data(page) == saved
        passed("Invoice terkoreksi menampilkan sisa Rp10.000, bukan total Rp110.000, tanpa write proyeksi")
    finally:
        ctx.close()


def main():
    server = phase4.BrowserServer(("127.0.0.1", 0), partial(phase3c.QuietHandler, directory=str(base.ROOT)))
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
                saved = base.data(page)
                page.locator("#demo-role").select_option("Kasir")
                expect(page.locator("#cashier-view")).to_be_visible(timeout=2000)
                expect(page.locator("#nav-cashier")).to_have_attribute("aria-current", "page")
                assert base.data(page) == saved
                page.reload()
                expect(page.locator("#demo-role")).to_have_value("Kasir")
                expect(page.locator("#cashier-view")).to_be_visible()
                assert base.data(page) == saved
                passed("Kasir langsung POS dan reload mempertahankan preferensi tanpa write ledger")
                page.locator("#demo-role").select_option("Owner")
                phase4.prepare(page)
                saved = copy.deepcopy(base.data(page))
                page.locator("#demo-role").select_option("Kasir")
                page.locator("#cashier-list .record button").click()
                expect(page.locator("#pos-preview")).to_be_visible(timeout=2000)
                expect(page.locator("#pos-preview-identity")).to_contain_text("DD 1248 KL")
                assert base.data(page) == saved
                page.locator("#cashier-search").fill("tidak sesuai pilihan")
                expect(page.locator("#pos-preview-context")).to_be_visible()
                expect(page.locator("#pos-preview-context")).to_contain_text("di luar filter")
                expect(page.locator("#pos-preview-identity")).to_contain_text("DD 1248 KL")
                assert base.data(page) == saved
                page.locator("#cashier-search").fill("")
                page.locator("#pos-create-invoice").click()
                expect(page.locator("#invoice-view")).to_be_visible()
                expect(page.locator("#cashier-view")).to_be_visible()
                assert page.locator("#cashier-view").bounding_box()["x"] < page.locator("#invoice-view").bounding_box()["x"]
                passed("Preview SO tanpa write; create eksplisit memakai satu editor invoice di kanan antrean")
                page.locator("#demo-role").select_option("Owner")
                page.locator("[name=invoicePrice]").first.fill("90000")
                page.locator("#invoice-reason").fill("Harga invoice lokal untuk contoh POS")
                page.locator("#invoice-save-price").click()
                ready(page, "DD 8921 AR")
                ready(page, "DD 5672 TS")
                page.locator("#so-invoice").click()
                phase4.confirm_click(page, "#invoice-issue")
                fixture = copy.deepcopy(base.data(page))
                page.locator("#demo-role").select_option("Kasir")
                expect(page.locator("#cashier-list .record")).to_have_count(3)
                expect(page.locator("#cashier-list")).to_contain_text("Total Rp 90.000")
                expect(page.locator("#cashier-list")).to_contain_text("Belum Lunas")
                for query, plate in (("DD1248KL", "DD 1248 KL"), ("Budi Contoh", "DD 1248 KL"), (fixture["serviceOrders"][1]["reference"], "DD 8921 AR"), (fixture["invoices"][1]["reference"], "DD 5672 TS")):
                    page.locator("#cashier-search").fill(query)
                    expect(page.locator("#cashier-list .record")).to_have_count(1)
                    expect(page.locator("#cashier-list")).to_contain_text(plate)
                page.locator("#cashier-search").fill("tidak ada")
                expect(page.locator("#cashier-empty")).to_be_visible()
                page.locator("#cashier-search").fill("")
                for stage in ("ready", "draft", "unpaid"):
                    page.locator("#pos-stage").select_option(stage)
                    expect(page.locator("#cashier-list .record")).to_have_count(1)
                page.locator("#pos-stage").select_option("pending")
                page.locator("#cashier-filter").select_option("cancelled")
                expect(page.locator("#cashier-list .record")).to_have_count(0)
                page.locator("#cashier-filter").select_option("all")
                assert base.data(page) == fixture
                passed("Proyeksi siap/draf/belum lunas tepat dan unik; empat identitas, filter/kosong tanpa write")

                page.locator("#payment-received").fill("100000")
                for plate in ("DD 8921 AR", "DD 1248 KL"):
                    page.once("dialog", lambda d: d.dismiss())
                    choose(page, plate)
                    expect(page.locator("#invoice-identity")).to_contain_text("DD 5672 TS")
                    expect(page.locator("#payment-received")).to_have_value("100000")
                    expect(page.locator("#cashier-list .record").filter(has_text="DD 5672 TS").get_by_role("button")).to_have_attribute("aria-pressed", "true")
                    assert base.data(page) == fixture
                page.locator("#demo-role").select_option("Owner")
                page.locator("#demo-role").select_option("Kasir")
                expect(page.locator("#payment-received")).to_have_value("100000")
                phase4.confirm_click(page, "#invoice-reset")
                passed("Batal pindah preview/invoice mempertahankan isian, transaksi dan pilihan; role-switch tidak membuang input")

                page.locator("#payment-received").fill("120000")
                phase4.confirm_click(page, "#payment-save")
                expect(page.locator("#invoice-paid-state")).to_have_text("Lunas")
                expect(page.locator("#cashier-list .record")).to_have_count(2)
                expect(page.locator("#invoice-identity")).to_contain_text("DD 5672 TS")
                expect(page.locator("#pos-invoice-note")).to_contain_text("sudah Lunas")
                expect(page.locator("#payment-history")).to_contain_text("20.000")
                paid = copy.deepcopy(base.data(page))
                page.evaluate("() => {window.prints=0;window.print=()=>{window.prints++};}")
                page.locator("#invoice-print").click()
                assert page.evaluate("window.prints") == 1
                page.emulate_media(media="print")
                expect(page.locator("#cashier-view")).to_be_hidden()
                expect(page.locator("#invoice-receipt")).to_be_visible()
                expect(page.locator("#invoice-receipt")).to_contain_text("DD 5672 TS")
                page.screenshot(path=str(base.OUT / "pos-print.png"), full_page=True, animations="disabled")
                page.emulate_media(media="screen")
                assert base.data(page) == paid
                passed("Bayar lunas menjaga nota terpilih tanpa auto-pindah; print POS hanya receipt dan tanpa write")

                for width, name in ((1440, "desktop"), (768, "tablet"), (390, "mobile")):
                    page.set_viewport_size({"width": width, "height": 1000})
                    for theme in ("light", "dark"):
                        if page.locator("html").get_attribute("data-theme") != theme: page.locator("#theme-toggle").click()
                        base.no_overflow(page)
                        page.screenshot(path=str(base.OUT / f"pos-detail-{name}-{theme}.png"), full_page=True, animations="disabled")
                page.locator("#invoice-back").click()
                expect(page.locator("#cashier-view")).to_be_visible()
                expect(page.locator("#invoice-view")).to_be_hidden()
                page.screenshot(path=str(base.OUT / "pos-mobile-list.png"), full_page=True, animations="disabled")
                page.locator("#pos-stage").select_option("ready")
                page.locator("#cashier-list .record button").focus()
                page.keyboard.press("Enter")
                expect(page.locator("#pos-preview-heading")).to_be_focused()
                expect(page.locator("#cashier-view")).to_be_hidden()
                expect(page.locator("#pos-preview")).to_be_visible()
                page.locator("#pos-back").click()
                expect(page.locator("#cashier-heading")).to_be_focused()
                page.evaluate("window.dispatchEvent(new Event('beforeprint'))")
                page.emulate_media(media="print")
                expect(page.locator("#invoice-receipt")).to_be_hidden()
                page.emulate_media(media="screen")
                for width in (320, 620, 1049, 1050, 1280):
                    page.set_viewport_size({"width": width, "height": 1000}); base.no_overflow(page)
                page.set_viewport_size({"width": 390, "height": 1000})
                page.evaluate("document.documentElement.style.fontSize='200%'")
                base.no_overflow(page)
                page.evaluate("document.documentElement.style.fontSize=''")
                passed("Desktop dua area, mobile list/detail, light/dark, 320px/200%, Enter/fokus dan native-print gate pada view aktif")
                ctx.close()
                preferences_and_roles(browser, fixture)
                failures(browser, fixture)
                projection_edges(browser, fixture)
                assert not errors, errors
            finally:
                browser.close()
    finally:
        server.shutdown(); server.server_close(); thread.join()
    report = {"passed": True, "checked_at": datetime.now(timezone.utc).isoformat(), "checks": checks, "console_errors": errors}
    (base.OUT / "verification-pos.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{len(checks)} POS checks passed")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        name = "failure-pos-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f") + ".json"
        (base.OUT / name).write_text(json.dumps({"passed": False, "error": str(exc), "checks_completed": checks, "console_errors": errors}, ensure_ascii=False, indent=2), encoding="utf-8")
        raise
