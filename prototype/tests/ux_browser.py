"""Regression checks for the eight audited UX issues, isolated dummy contexts."""
import json
import tempfile
import threading
from functools import partial
from pathlib import Path
from playwright.sync_api import sync_playwright, expect
import phase1_browser as base
import phase2_browser as diagnosis
import phase3c_browser as handoff
import phase4_browser as invoice


def main():
    server = invoice.BrowserServer(('127.0.0.1', 0), partial(handoff.QuietHandler, directory=str(base.ROOT)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    url = f'http://127.0.0.1:{server.server_port}/prototype/'
    fixture = json.loads((base.ROOT / 'prototype/preview-store.json').read_text(encoding='utf-8'))
    errors, checks = [], []
    try:
        with sync_playwright() as p, tempfile.TemporaryDirectory(prefix='pos-ux-') as scratch:
            browser = p.chromium.launch()

            def fresh(store=None, script=''):
                ctx = browser.new_context(viewport={'width': 1440, 'height': 1000}, accept_downloads=True, timezone_id="UTC")
                if store is not None:
                    ctx.add_init_script(f'if (localStorage.getItem({json.dumps(base.KEY)}) === null) localStorage.setItem({json.dumps(base.KEY)}, {json.dumps(json.dumps(store))});')
                if script:
                    ctx.add_init_script(script)
                page = ctx.new_page()
                page.on('pageerror', lambda e: errors.append(str(e)))
                page.goto(url)
                expect(page.locator('#records-panel')).to_have_attribute('aria-busy', 'false')
                return ctx, page

            ctx, page = fresh()
            page.locator('#new-registration').click()
            page.locator('#plate').fill('DD 9999 UX')
            expect(page.locator('#draft-status')).to_have_text('Draf tersimpan di perangkat ini')
            original = base.data(page)
            invoice.confirm_click(page, '#discard-draft', accept=False)
            expect(page.locator('#plate')).to_have_value('DD 9999 UX')
            assert base.data(page) == original
            diagnosis.fail_writes(page)
            invoice.confirm_click(page, '#discard-draft')
            expect(page.locator('#plate')).to_have_value('DD 9999 UX')
            assert base.data(page) == original
            diagnosis.restore_writes(page)
            page.evaluate('key => {const s=JSON.parse(localStorage.getItem(key));s.revision="other-tab";localStorage.setItem(key,JSON.stringify(s));}', base.KEY)
            invoice.confirm_click(page, '#discard-draft')
            expect(page.locator('#plate')).to_have_value('DD 9999 UX')
            expect(page.locator('#storage-alert-title')).to_have_text('Data berubah di tab lain')
            page.locator('#storage-retry').click()
            invoice.confirm_click(page, '#discard-draft')
            expect(page.locator('#plate')).to_have_value('')
            assert base.data(page)['draft'] is None
            assert base.data(page)['records'] == original['records']
            page.reload()
            expect(page.locator('#draft-notice')).to_be_hidden()
            checks.append('U5: cancel, quota, conflict preserve draft; confirmed discard only clears draft and survives reload')
            ctx.close()

            duplicate = json.loads(json.dumps(fixture))
            extra = dict(duplicate['records'][0], id='duplicate-visit', reference='REG-OTHER-VISIT', createdAt='2026-11-12T09:05:00.000Z')
            duplicate['records'].append(extra)
            ctx, page = fresh(duplicate)
            page.locator('#nav-diagnoses').click()
            rows = page.locator('#diagnoses-list .record').filter(has_text=extra['plate'])
            expect(rows).to_have_count(2)
            assert len(set(rows.get_by_role('button').evaluate_all('els=>els.map(e=>e.getAttribute("aria-label"))'))) == 2
            expect(rows.filter(has_text='REG-OTHER-VISIT')).to_contain_text('09.05')
            rows.filter(has_text='REG-OTHER-VISIT').get_by_role('button').click()
            expect(page.locator('#diagnosis-requirements')).to_contain_text('Draf boleh disimpan')
            page.locator('#diagnosis-findings').fill('Pemeriksaan parsial')
            page.locator('#save-diagnosis').click()
            diagnosis.saved(page)
            assert next(d for d in base.data(page)['diagnoses'] if d['registrationId'] == extra['id'])['status'] == 'draft'
            checks.append('U4/U6: duplicate plate visits identifiable; requirements visible and partial diagnosis draft remains valid')
            ctx.close()

            ctx, page = fresh(fixture)
            page.locator('#nav-invoices').click()
            for record in fixture['invoices']:
                order = next(o for o in fixture['serviceOrders'] if o['id'] == record['orderId'])
                registration = next(r for r in fixture['records'] if r['id'] == order['registrationId'])
                labels = page.locator('#invoice-list button').evaluate_all('els=>els.map(e=>e.getAttribute("aria-label"))')
                assert any(record['reference'] in label and registration['plate'] in label for label in labels), labels
            page.locator('#invoice-list .record').filter(has_text='DD 5672 TS').get_by_role('button').click()
            balance = int(page.locator('#invoice-balance').inner_text().replace('Rp', '').replace('.', '').replace('\xa0', '').strip())
            before = base.data(page)
            page.locator('#payment-received').fill(str(balance + 20000))
            expect(page.locator('#payment-change')).to_contain_text('20.000')
            dialogs = []
            def cancel(dialog):
                dialogs.append(dialog.message)
                dialog.dismiss()
            page.once('dialog', cancel)
            page.locator('#payment-save').click()
            assert '20.000' in dialogs[-1] and 'DD 5672 TS' in dialogs[-1]
            assert base.data(page) == before
            page.locator('#payment-method').select_option('transfer')
            page.locator('#payment-save').click()
            expect(page.locator('#payment-received')).to_have_attribute('aria-invalid', 'true')
            expect(page.locator('#payment-error')).to_be_visible()
            for width in (1440, 390, 320):
                page.set_viewport_size({'width': width, 'height': 900})
                page.locator('#payment-received').focus()
                base.no_overflow(page)
                box = page.locator('#payment-error').bounding_box()
                assert box and 0 <= box['y'] < 900, box
            page.locator('#payment-received').fill(str(balance))
            expect(page.locator('#payment-received')).not_to_have_attribute('aria-invalid', 'true')
            page.locator('#payment-save').click()
            expect(page.locator('#payment-reference')).to_have_attribute('aria-invalid', 'true')
            page.locator('#payment-reference').fill('TRANSFER-UX')
            expect(page.locator('#payment-error')).to_be_empty()
            for theme in ('light', 'dark'):
                if page.locator('html').get_attribute('data-theme') != theme:
                    page.locator('#theme-toggle').click()
                base.no_overflow(page)
                page.screenshot(path=str(Path(scratch) / f'payment-{theme}.png'), full_page=True)
            invoice.confirm_click(page, '#payment-save')
            assert base.data(page)['invoices'][-1]['history'][-1]['kind'] == 'payment'
            checks.append('U2/U3/U7: contextual invoice names, cash preview/confirmation, cancel unchanged, local responsive errors and exact transfer payment')
            ctx.close()

            corrupt = '{broken raw customer data'
            ctx, page = fresh(script=f'localStorage.setItem({json.dumps(base.KEY)}, {json.dumps(corrupt)});')
            expect(page.locator('#storage-alert-message')).to_contain_text('Format data lokal rusak')
            with page.expect_download() as download:
                page.locator('#storage-backup').click()
            assert Path(download.value.path()).read_text(encoding='utf-8') == corrupt
            page.locator('#storage-retry').click()
            assert page.evaluate('key=>localStorage.getItem(key)', base.KEY) == corrupt
            checks.append('U8: corrupt raw download is exact; retry never overwrites data')
            ctx.close()
            ctx, page = fresh(script=f'''const nativeGet=Storage.prototype.getItem; Storage.prototype.getItem=function(key){{if(key==={json.dumps(base.KEY)})throw new DOMException('Blocked','SecurityError');return nativeGet.call(this,key);}};''')
            expect(page.locator('#storage-alert-title')).to_have_text('Akses penyimpanan tidak tersedia')
            expect(page.locator('#storage-backup')).to_be_hidden()
            expect(page.locator('#storage-help')).to_be_visible()
            checks.append('U8: blocked storage has distinct instructions and no unavailable backup action')
            ctx.close()
            assert not errors, errors
            browser.close()
    finally:
        server.shutdown()
        server.server_close()
    (base.OUT / 'verification-ux.json').write_text(json.dumps({'passed': True, 'checks': checks, 'browser_errors': errors}, ensure_ascii=False, indent=2), encoding='utf-8')
    for check in checks:
        print('PASS', check)


if __name__ == '__main__':
    main()
