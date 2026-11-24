"""Exercise the phase-one prototype using isolated browser contexts only."""

import hashlib
import json
import sys
import threading
from datetime import datetime, timezone
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from playwright.sync_api import expect, sync_playwright


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "prototype" / "evidence"
URL = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8765/prototype/"
KEY = "pos_browser_prototype_v1"
results = []
errors = []


def record(name):
    results.append({"check": name, "passed": True})
    print("PASS", name)


def loaded(page):
    page.goto(URL)
    page.wait_for_load_state("networkidle")
    expect(page.locator("#records-panel")).to_have_attribute("aria-busy", "false")


def fill(page, plate="DD 9999 ZZ", customer="Pelanggan Uji", complaint="AC tidak dingin"):
    page.locator("#plate").fill(plate)
    page.locator("#customer").fill(customer)
    page.locator("#complaint").fill(complaint)
    page.locator("#phone").fill("0812 0000 0099")


def data(page):
    return page.evaluate("key => JSON.parse(localStorage.getItem(key))", KEY)


def no_overflow(page):
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"), "horizontal overflow"


def screenshot(page, filename):
    page.evaluate("window.scrollTo(0, 0)")
    page.screenshot(path=str(OUT / filename), full_page=True, animations="disabled")


def contrast(a, b):
    def lum(color):
        rgb = [int(color[i:i + 2], 16) / 255 for i in (1, 3, 5)]
        rgb = [v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4 for v in rgb]
        return sum(v * w for v, w in zip(rgb, (.2126, .7152, .0722)))
    x, y = sorted((lum(a), lum(b)))
    return (y + .05) / (x + .05)


def main():
    OUT.mkdir(exist_ok=True)
    original_hash = hashlib.sha256((ROOT / "index.html").read_bytes()).hexdigest()
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            context = browser.new_context(viewport={"width": 1440, "height": 1000}, locale="id-ID")
            page = context.new_page()
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
            loaded(page)
            page.evaluate("localStorage.setItem('dokterac_v2', 'LEGACY_SENTINEL'); localStorage.setItem('dokterac_theme', 'LEGACY_THEME')")
            assert len(data(page)["records"]) == 4
            record("Seed empat kunjungan dummy; legacy berada pada key terpisah")

            page.locator("#search").fill("dd1248kl")
            expect(page.locator("#records-list .record")).to_have_count(1)
            page.get_by_role("button", name="Lihat detail DD 1248 KL", exact=True).click()
            expect(page.locator("#detail-customer")).to_have_text("Budi Contoh")
            page.locator("#back-from-detail").click()
            page.locator("#search").fill("081200000002")
            expect(page.locator("#records-list .record")).to_have_count(1)
            page.locator("#search").fill("tidak-ada")
            expect(page.locator("#empty-state")).to_be_visible()
            page.locator("#search").fill("")
            page.locator("#filter-today").click()
            expect(page.locator("#records-list .record")).to_have_count(3)
            page.locator("#filter-all").click()
            expect(page.locator("#records-list .record")).to_have_count(4)
            record("Pencarian plat/telepon, detail tepat, kosong, dan filter hari ini")

            for role in ("Owner", "Teknisi", "Kasir"):
                page.locator("#demo-role").select_option(role)
                expect(page.locator("#announcement")).to_contain_text(role)
            record("Ketiga peran demo dapat dipilih, tanpa klaim login")

            page.locator("#nav-registration").click()
            page.locator("#new-registration").click()
            page.locator("#save-registration").click()
            expect(page.locator("#plate-error")).to_have_text("Isi nomor plat kendaraan.")
            expect(page.locator("#plate")).to_be_focused()
            page.locator("#plate").fill("DD 1111 ZZ")
            page.evaluate("document.getElementById('registration-form').requestSubmit()")
            expect(page.locator("#draft-status")).to_have_text("Draf tersimpan di perangkat ini")
            assert data(page)["draft"]["plate"] == "DD 1111 ZZ"
            record("Submit invalid sebelum debounce tetap menyimpan draf, tanpa status menggantung")
            page.locator("#plate").fill("bukan-plat")
            page.locator("#customer").fill("   ")
            page.locator("#phone").fill("123")
            page.locator("#complaint").fill("   ")
            page.locator("#save-registration").click()
            expect(page.locator("#phone-error")).to_contain_text("9–15 digit")
            expect(page.locator("#customer-error")).to_be_visible()
            assert len(data(page)["records"]) == 4
            record("Required, whitespace, format plat dan telepon ditolak")

            fill(page)
            expect(page.locator("#draft-status")).to_have_text("Draf tersimpan di perangkat ini")
            page.reload()
            page.locator("#nav-registration").click()
            expect(page.locator("#draft-notice")).to_be_visible()
            page.locator("#resume-draft").click()
            expect(page.locator("#plate")).to_have_value("DD 9999 ZZ")
            page.locator("#demo-role").select_option("Teknisi")
            page.locator("#save-registration").dblclick()
            expect(page.locator("#detail-view")).to_be_visible()
            expect(page.locator("#detail-address")).to_have_text("Tidak dicatat")
            expect(page.locator("#detail-actor")).to_have_text("Teknisi (simulasi)")
            assert len(data(page)["records"]) == 5
            assert data(page)["draft"] is None
            page.reload()
            expect(page.locator("#records-list .record")).to_have_count(5)
            record("Autosave draf, pemulihan, alamat opsional, submit ganda dan reload")
            page.locator("#search").fill("081200000099")
            expect(page.locator("#records-list .record")).to_have_count(1)
            page.locator("#search").fill("")
            record("Nomor telepon berformat spasi ditemukan melalui query digit saja")

            page.locator("#new-registration").click()
            payload = '<img src=x onerror="window.injected=true">'
            fill(page, customer=payload, complaint=payload)
            page.locator("#save-registration").click()
            expect(page.locator("#detail-customer")).to_have_text(payload)
            assert page.locator("#detail-view img").count() == 0
            assert not page.evaluate("Boolean(window.injected)")
            record("Input markup ditampilkan sebagai teks, plat boleh berulang untuk kunjungan baru")

            page.locator("#back-from-detail").click()
            page.locator("#new-registration").click()
            fill(page, plate="DD 8888 ZZ")
            expect(page.locator("#draft-status")).to_have_text("Draf tersimpan di perangkat ini")
            before_count = len(data(page)["records"])
            page.evaluate("""() => {
                window.originalSet = Storage.prototype.setItem;
                Storage.prototype.setItem = function(key, value) {
                    if (key === 'pos_browser_prototype_v1') throw new DOMException('Test quota', 'QuotaExceededError');
                    return window.originalSet.call(this, key, value);
                };
            }""")
            page.locator("#save-registration").click()
            expect(page.locator("#storage-alert")).to_be_visible()
            expect(page.locator("#draft-status")).to_have_text("Belum tersimpan")
            expect(page.locator("#plate")).to_have_value("DD 8888 ZZ")
            assert len(data(page)["records"]) == before_count
            page.evaluate("() => { Storage.prototype.setItem = window.originalSet; }")
            page.locator("#storage-retry").click()
            expect(page.locator("#storage-alert")).to_be_hidden()
            page.locator("#save-registration").click()
            assert len(data(page)["records"]) == before_count + 1
            record("Gagal menulis: tidak ada sukses palsu, input utuh, retry tepat satu record")

            page.locator("#back-from-detail").click()
            page.locator("#new-registration").click()
            fill(page, plate="DD 7777 ZZ")
            expect(page.locator("#draft-status")).to_have_text("Draf tersimpan di perangkat ini")
            other = context.new_page()
            loaded(other)
            other.locator("#resume-draft").click()
            other.locator("#customer").fill("Perubahan tab kedua")
            expect(other.locator("#draft-status")).to_have_text("Draf tersimpan di perangkat ini")
            expect(page.locator("#storage-alert-title")).to_have_text("Data berubah di tab lain")
            latest = data(page)["revision"]
            page.locator("#save-registration").click()
            assert data(page)["revision"] == latest
            expect(page.locator("#customer")).to_have_value("Pelanggan Uji")
            page.locator("#storage-retry").click()
            expect(page.locator("#draft-status")).to_have_text("Data terbaru dimuat. Isian Anda belum tersimpan.")
            page.locator("#back-from-form").click()
            page.locator("#resume-draft").click()
            expect(page.locator("#customer")).to_have_value("Pelanggan Uji")
            page.locator("#save-registration").click()
            expect(page.locator("#detail-customer")).to_have_text("Pelanggan Uji")
            other.close()
            record("Benturan dua tab menolak stale write dan mempertahankan isian lokal")

            assert page.evaluate("localStorage.getItem('dokterac_v2')") == "LEGACY_SENTINEL"
            assert page.evaluate("localStorage.getItem('dokterac_theme')") == "LEGACY_THEME"
            record("Key data dan tema legacy tidak berubah")
            context.close()

            for corrupt in ("{bad-json", '{"version":1,"revision":"x","records":[{}],"draft":null}'):
                ctx = browser.new_context()
                ctx.add_init_script(f"localStorage.setItem({json.dumps(KEY)}, {json.dumps(corrupt)})")
                pg = ctx.new_page()
                loaded(pg)
                expect(pg.locator("#storage-alert")).to_be_visible()
                pg.locator("#storage-retry").click()
                assert pg.evaluate("key => localStorage.getItem(key)", KEY) == corrupt
                ctx.close()
            record("JSON rusak dan struktur salah tidak ditimpa seed")

            ctx = browser.new_context()
            pg = ctx.new_page()
            loaded(pg)
            corrupt = data(pg)
            first = corrupt["records"][0]
            corrupt["draft"] = {key: first[key] for key in ("plate", "customer", "phone", "complaint", "address")}
            corrupt["draft"].update(id=first["id"], updatedAt=first["createdAt"])
            raw = json.dumps(corrupt)
            pg.evaluate("([key, raw]) => localStorage.setItem(key, raw)", [KEY, raw])
            pg.reload()
            expect(pg.locator("#storage-alert")).to_be_visible()
            assert pg.evaluate("key => localStorage.getItem(key)", KEY) == raw
            record("Collision ID draf dengan record ditolak sebelum penulisan, JSON asal utuh")
            ctx.close()

            ctx = browser.new_context()
            ctx.add_init_script("Object.defineProperty(window, 'localStorage', {get() {throw new DOMException('Blocked', 'SecurityError')}})")
            pg = ctx.new_page()
            loaded(pg)
            expect(pg.locator("#storage-alert")).to_be_visible()
            pg.locator("#theme-toggle").click()
            expect(pg.locator("html")).to_have_attribute("data-theme", "dark")
            ctx.close()
            record("Akses storage ditolak menghasilkan error terlihat; tema tetap berfungsi")

            ctx = browser.new_context(viewport={"width": 1440, "height": 1000}, reduced_motion="reduce")
            pg = ctx.new_page()
            pg.on("pageerror", lambda error: errors.append(str(error)))
            loaded(pg)
            for width, label in ((1440, "desktop"), (768, "tablet"), (390, "mobile")):
                pg.set_viewport_size({"width": width, "height": 900})
                for theme in ("light", "dark"):
                    if pg.locator("html").get_attribute("data-theme") != theme:
                        pg.locator("#theme-toggle").click()
                    no_overflow(pg)
                    screenshot(pg, f"{label}-{theme}.png")
                if width < 1050:
                    pg.locator("#menu-toggle").click()
                    expect(pg.locator("#nav-registration")).to_be_focused()
                    pg.keyboard.press("Escape")
                    expect(pg.locator("#menu-toggle")).to_be_focused()
                    pg.locator("#menu-toggle").click()
                    pg.locator("#nav-registration").click()
                    expect(pg.locator("#menu-toggle")).to_have_attribute("aria-expanded", "false")
            record("Desktop/tablet/mobile light-dark, tanpa overflow; menu dan Escape berfungsi")
            pg.set_viewport_size({"width": 1440, "height": 1000})
            pg.locator("#new-registration").click()
            fill(pg)
            expect(pg.locator("#draft-status")).to_have_text("Draf tersimpan di perangkat ini")
            pg.locator("#theme-toggle").click()
            screenshot(pg, "form-desktop-light.png")
            pg.set_viewport_size({"width": 390, "height": 844})
            screenshot(pg, "form-mobile-light.png")
            for width in (320, 620, 1049, 1050, 1280):
                pg.set_viewport_size({"width": width, "height": 900})
                no_overflow(pg)
            pg.set_viewport_size({"width": 390, "height": 844})
            pg.evaluate("document.documentElement.style.fontSize = '200%'")
            no_overflow(pg)
            pg.evaluate("document.documentElement.style.fontSize = ''")
            pg.locator("#plate").focus()
            pg.keyboard.press("Tab")
            expect(pg.locator("#complaint")).to_be_focused()
            assert pg.locator("#complaint").evaluate("el => getComputedStyle(el).outlineStyle") != "none"
            assert pg.locator("#theme-toggle").evaluate("el => getComputedStyle(el).transitionDuration") == "0s"
            record("Form responsive 320–1440, teks 200%, urutan Tab/fokus dan reduced motion")
            pg.reload()
            expect(pg.locator("html")).to_have_attribute("data-theme", "light")
            pg.locator("#resume-draft").click()
            pg.locator("#back-from-form").click()
            expect(pg.locator("#list-view")).to_be_visible()
            record("Tema bertahan setelah reload; kembali dari form menyimpan draf")
            ctx.close()

            pairs = [
                ("light/text", "#172b4d", "#ffffff"), ("light/muted", "#53647b", "#f1f4f8"),
                ("light/primary", "#ffffff", "#006beb"), ("light/warning", "#8b5b10", "#fff5e0"),
                ("light/success", "#147a52", "#eaf7f0"), ("light/error", "#b42332", "#ffffff"),
                ("light/link-sidebar", "#172b4d", "#f1f4f8"), ("light/link-hover", "#172b4d", "#eef5ff"),
                ("dark/text", "#edf2fa", "#181d25"), ("dark/muted", "#aab8cb", "#131820"),
                ("dark/primary", "#10233e", "#66aaff"), ("dark/warning", "#f2ce87", "#3b301c"),
                ("dark/success", "#71d9aa", "#17372c"), ("dark/error", "#ffacb7", "#181d25"),
            ]
            ratios = {name: round(contrast(a, b), 3) for name, a, b in pairs}
            assert min(ratios.values()) >= 4.5, ratios
            record("14 pasangan kontras token light/dark memenuhi 4.5:1")
            assert not errors, errors
            record("Tidak ada error console/page pada alur normal")
        finally:
            browser.close()
    assert hashlib.sha256((ROOT / "index.html").read_bytes()).hexdigest() == original_hash
    record("Hash index.html legacy identik sebelum/sesudah")
    report = {"passed": True, "checked_at": datetime.now(timezone.utc).isoformat(), "url": URL, "checks": results, "console_errors": errors, "contrast": ratios, "legacy_sha256": original_hash, "limitations": ["Chromium headless only", "No real phone keyboard or physical printer", "Prototype, no server authorization or cross-device sync", "Sequential tab conflict detection, not atomic localStorage concurrency"]}
    (OUT / "verification-phase1.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{len(results)} checks passed; evidence: {OUT}")


if __name__ == "__main__":
    server = None
    thread = None
    try:
        if len(sys.argv) == 1:
            server = ThreadingHTTPServer(("127.0.0.1", 0), partial(SimpleHTTPRequestHandler, directory=str(ROOT)))
            URL = f"http://127.0.0.1:{server.server_port}/prototype/"
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
        main()
    except Exception as exc:
        OUT.mkdir(exist_ok=True)
        filename = "failure-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f") + ".json"
        (OUT / filename).write_text(json.dumps({"passed": False, "error": str(exc), "checks_completed": results}, ensure_ascii=False, indent=2), encoding="utf-8")
        raise
    finally:
        if server:
            server.shutdown()
            server.server_close()
            thread.join()
