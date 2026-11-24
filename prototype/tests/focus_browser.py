"""Pointer and keyboard focus checks across all HTML entry points."""
import threading
from functools import partial
from playwright.sync_api import sync_playwright, expect
import phase1_browser as base
import phase3c_browser as handoff
import phase4_browser as invoice


def outline(page):
    return page.evaluate('getComputedStyle(document.activeElement).outlineStyle')


def main():
    server = invoice.BrowserServer(('127.0.0.1', 0), partial(handoff.QuietHandler, directory=str(base.ROOT)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    origin = f'http://127.0.0.1:{server.server_port}'
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={'width': 1440, 'height': 1000})
            page.goto(origin + '/prototype/')
            page.locator('#demo-role').select_option('Kasir')
            for selector in ('#pos-stage', '#cashier-filter', '#cashier-search'):
                page.locator(selector).click()
                page.keyboard.press('Escape')
                assert outline(page) == 'none'
            page.locator('#cashier-search').fill('contoh')
            assert outline(page) == 'none'
            assert page.locator('.search-control:has(#cashier-search)').evaluate("el => getComputedStyle(el).outlineStyle") == 'none'
            page.keyboard.press('Tab')
            assert outline(page) != 'none'
            page.locator('#theme-toggle').click()
            assert outline(page) == 'none'
            page.locator('#nav-registration').click()
            page.locator('#new-registration').click()
            page.locator('#plate').fill('DD')
            assert outline(page) == 'none'
            page.keyboard.press('Tab')
            expect(page.locator('#complaint')).to_be_focused()
            assert outline(page) != 'none'
            page.goto(origin + '/prototype/preview.html')
            link = page.get_by_role('link', name='Mulai preview')
            link.evaluate("el => el.addEventListener('click', e => e.preventDefault())")
            link.click()
            assert outline(page) == 'none'
            page.keyboard.press('Tab')
            assert outline(page) != 'none'
            page.goto(origin + '/index.html')
            field = page.locator('input:visible').first
            field.click()
            assert outline(page) == 'none'
            assert field.evaluate("el => getComputedStyle(el).boxShadow") == 'none'
            page.keyboard.press('Tab')
            focused = page.locator(':focus')
            assert outline(page) != 'none' or focused.evaluate("el => getComputedStyle(el).boxShadow") != 'none'
            browser.close()
    finally:
        server.shutdown()
        server.server_close()
    print('PASS pointer click/type has no ring; Tab retains focus indicator; selects/search/form/dark/preview/legacy checked')


if __name__ == '__main__':
    main()
