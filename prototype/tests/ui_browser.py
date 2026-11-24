"""Shared UI presentation checks; isolated dummy data only."""
import json
import threading
from functools import partial
from playwright.sync_api import sync_playwright, expect
import phase1_browser as base
import phase3c_browser as handoff
import phase4_browser as invoice


def main():
    server = invoice.BrowserServer(('127.0.0.1', 0), partial(handoff.QuietHandler, directory=str(base.ROOT)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    url = f'http://127.0.0.1:{server.server_port}/prototype/'
    errors, checks = [], []
    fixture = json.loads((base.ROOT / 'prototype' / 'preview-store.json').read_text(encoding='utf-8'))
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            ctx = browser.new_context(viewport={'width': 1440, 'height': 1000}, reduced_motion='reduce')
            ctx.add_init_script(f"if (!localStorage.getItem({json.dumps(base.KEY)})) localStorage.setItem({json.dumps(base.KEY)}, {json.dumps(json.dumps(fixture))});")
            page = ctx.new_page()
            page.on('pageerror', lambda e: errors.append(str(e)))
            page.on('console', lambda m: errors.append(m.text) if m.type == 'error' else None)
            page.goto(url)
            expect(page.locator('#records-panel')).to_have_attribute('aria-busy', 'false')

            def capture(name):
                for width in (1440, 390, 320):
                    page.set_viewport_size({'width': width, 'height': 900})
                    base.no_overflow(page)
                    # Every visible editable control must retain a programmatic label.
                    assert page.locator('input:visible,textarea:visible,select:visible').evaluate_all('''els => els.every(el => el.labels?.length || el.getAttribute('aria-label') || el.getAttribute('aria-labelledby'))''')
                    if width != 320:
                        page.evaluate('window.scrollTo(0, 0)')
                        page.screenshot(path=str(base.OUT / f'ui-{name}-{width}.png'), full_page=True, animations='disabled')
                page.set_viewport_size({'width': 1440, 'height': 1000})

            capture('registration')
            page.locator('#new-registration').click()
            page.locator('#save-registration').click()
            expect(page.locator('#plate')).to_be_focused()
            expect(page.locator('#plate')).to_have_attribute('aria-invalid', 'true')
            expect(page.locator('#plate-error')).not_to_be_empty()
            capture('form-error')
            checks.append('Registration validation retains labels, message and focus')
            page.locator('#back-from-form').click()
            page.locator('#nav-diagnoses').click()
            page.locator('#diagnoses-list .record').filter(has_text='DD 3107 MA').get_by_role('button').click()
            capture('diagnosis')
            page.locator('#nav-orders').click()
            page.locator('#orders-list .record').filter(has_text='DD 1248 KL').get_by_role('button').click()
            capture('service-order')
            expect(page.get_by_role('navigation', name='Bagian Service Order')).to_be_visible()
            page.locator('#demo-role').select_option('Kasir')
            capture('pos')
            page.set_viewport_size({'width': 390, 'height': 844})
            page.locator('#menu-toggle').click()
            page.locator('#menu-close').click()
            expect(page.locator('#menu-toggle')).to_be_focused()
            page.locator('#menu-toggle').click()
            page.keyboard.press('Escape')
            expect(page.locator('#menu-toggle')).to_be_focused()
            checks.append('Mobile menu close/Escape returns keyboard focus')
            page.locator('#cashier-list .record').filter(has_text='DD 5672 TS').get_by_role('button').click()
            capture('invoice-payment')
            for theme in ('light', 'dark'):
                if page.locator('html').get_attribute('data-theme') != theme:
                    page.locator('#theme-toggle').click()
                colors = page.evaluate('''() => {
                    const style = getComputedStyle(document.documentElement);
                    return Object.fromEntries(['text','muted','surface','secondary','canvas','input','error','action','on-action'].map(n => [n, style.getPropertyValue('--'+n).trim()]));
                }''')
                def full(v):
                    return '#' + ''.join(c * 2 for c in v[1:]) if len(v) == 4 else v
                for fg, bg, minimum in [('text','surface',4.5),('muted','surface',4.5),('muted','secondary',4.5),('error','surface',4.5),('input','surface',3),('on-action','action',4.5)]:
                    assert base.contrast(full(colors[fg]), full(colors[bg])) >= minimum, (theme, fg, bg)
                page.screenshot(path=str(base.OUT / f'ui-invoice-{theme}.png'), full_page=True, animations='disabled')
            checks.append('Current CSS text/action/error/input contrast checked in both themes')
            # Presentation/navigation must not change document data.
            stored = base.data(page)
            assert stored['records'] == fixture['records']
            assert stored['serviceOrders'] == fixture['serviceOrders']
            assert stored['invoices'] == fixture['invoices']
            checks.append('Six workspaces at 1440/390/320px; labels and overflow checked; ledger unchanged')
            assert not errors, errors
            browser.close()
    finally:
        server.shutdown()
        server.server_close()
    (base.OUT / 'verification-ui.json').write_text(json.dumps({'passed': True, 'checks': checks, 'browser_errors': errors}, ensure_ascii=False, indent=2), encoding='utf-8')
    print('PASS shared UI: labels, validation, keyboard menu, actual CSS contrast, responsive pages, ledger unchanged, browser errors empty')


if __name__ == '__main__':
    main()
