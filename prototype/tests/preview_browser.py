"""Preview journeys and team changes on isolated browser data."""
import copy
import json
import threading
from functools import partial
from playwright.sync_api import sync_playwright, expect
import phase1_browser as base
import phase3a_browser as progress
import phase3b_browser as actual
import phase3c_browser as handoff
import phase4_browser as invoice


def main():
    server = invoice.BrowserServer(("127.0.0.1", 0), partial(handoff.QuietHandler, directory=str(base.ROOT)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base.URL = f"http://127.0.0.1:{server.server_port}/prototype/"
    errors = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            ctx = browser.new_context(viewport={"width": 1440, "height": 1000})
            page = ctx.new_page()
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
            base.loaded(page)
            progress.create_order(page)
            page.locator('[name="so-member"][value="tech-b"]').check()
            progress.apply_action(page, "started", tech="tech-a")
            expect(page.locator('#so-members')).to_contain_text('Teknisi B')
            assert progress.order(page)['workflow']['memberIds'] == ['tech-b']
            page.reload()
            progress.open_order(page)
            expect(page.locator('#so-members')).to_contain_text('Teknisi B')
            page.locator('#so-action').select_option('assigned')
            page.locator('[name="so-member"][value="tech-a"]').check()
            before = base.data(page)
            page.locator('#so-apply-action').click()
            expect(page.locator('#so-action-error')).to_contain_text('berbeda')
            assert base.data(page) == before
            page.locator('[name="so-member"][value="tech-a"]').uncheck()
            page.locator('[name="so-member"][value="tech-c"]').check()
            page.locator('#so-apply-action').click()
            expect(page.locator('#so-members')).to_contain_text('Teknisi C')
            page.locator('#demo-role').select_option('Kasir')
            progress.open_order(page)
            expect(page.locator('[name="so-member"]').first).to_be_disabled()
            page.locator('#demo-role').select_option('Owner')
            # Generate a reproducible public fixture using real application actions.
            progress.create_order(page, 'DD 8921 AR')
            actual.submit(page, 'Realisasi contoh untuk antrean kasir')
            progress.apply_action(page, 'started', tech='tech-b')
            progress.apply_action(page, 'completed')
            handoff.send(page)
            expect(page.locator('[name="so-member"]').first).to_be_disabled()
            locked = base.data(page)
            page.evaluate("document.getElementById('so-progress-form').requestSubmit()")
            assert base.data(page) == locked
            progress.create_order(page, 'DD 5672 TS')
            actual.submit(page, 'Realisasi contoh untuk invoice')
            progress.apply_action(page, 'started', tech='tech-c')
            progress.apply_action(page, 'completed')
            handoff.send(page)
            page.locator('#so-invoice').click()
            invoice.confirm_click(page, '#invoice-issue')
            fixture_path = base.ROOT / 'prototype' / 'preview-store.json'
            if not fixture_path.exists():
                fixture_path.write_text(json.dumps(base.data(page), ensure_ascii=False, indent=2), encoding='utf-8')
            original = copy.deepcopy(base.data(page))
            for member_ids in (['tech-b', 'tech-b'], ['tech-a'], ['unknown']):
                bad = copy.deepcopy(original)
                bad['serviceOrders'][0]['workflow']['memberIds'] = member_ids
                probe = browser.new_context()
                probe.add_init_script(f"localStorage.setItem({json.dumps(base.KEY)}, {json.dumps(json.dumps(bad))})")
                probe_page = probe.new_page()
                probe_page.goto(base.URL)
                expect(probe_page.locator('#storage-alert')).to_be_visible()
                assert base.data(probe_page) == bad
                probe.close()
            page.goto(base.URL + 'preview.html')
            page.get_by_role('link', name='Mulai preview').click()
            expect(page.locator('.demo-notice')).to_contain_text('Mode latihan')
            assert base.data(page) == original
            page.locator('#nav-orders').click()
            expect(page.locator('#orders-list .record')).to_have_count(3)
            page.locator('#demo-role').select_option('Kasir')
            expect(page.locator('#cashier-list .record')).to_have_count(2)
            raw = page.evaluate("localStorage.getItem('pos_browser_preview_flow_v1')")
            page.reload()
            expect(page.locator('#cashier-list .record')).to_have_count(2)
            assert page.evaluate("localStorage.getItem('pos_browser_preview_flow_v1')") == raw
            assert base.data(page) == original
            page.locator('#nav-cashier').click()
            page.screenshot(path=str(base.OUT / 'preview-desktop.png'), full_page=True, animations="disabled")
            page.locator('#theme-toggle').click()
            page.screenshot(path=str(base.OUT / 'preview-dark.png'), full_page=True, animations="disabled")
            page.set_viewport_size({'width': 390, 'height': 844})
            base.no_overflow(page)
            page.screenshot(path=str(base.OUT / 'preview-mobile.png'), full_page=True, animations="disabled")
            page.goto(base.URL + 'preview.html')
            base.no_overflow(page)
            page.screenshot(path=str(base.OUT / 'preview-guide-mobile.png'), full_page=True, animations="disabled")
            # Corrupt preview data must block without replacing either dataset.
            page.evaluate("localStorage.setItem('pos_browser_preview_flow_v1', '{broken')")
            page.goto(base.URL + '?demo=flow')
            expect(page.locator('#storage-alert')).to_be_visible()
            assert page.evaluate("localStorage.getItem('pos_browser_preview_flow_v1')") == '{broken'
            assert base.data(page) == original
            assert not errors, errors
            browser.close()
    finally:
        server.shutdown()
        server.server_close()
    print('PASS Preview isolated/reload/corruption, team persistence/validation/roles, desktop/mobile/dark; browser errors empty')
    (base.OUT / 'verification-preview.json').write_text(json.dumps({
        'passed': True, 'checks': ['isolated datasets', 'reload preservation', 'corrupt store preserved',
        'team persistence', 'duplicate/main/unknown member rejected', 'cashier and handoff lock',
        'desktop/mobile/dark rendered'], 'browser_errors': errors,
    }, ensure_ascii=False, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
