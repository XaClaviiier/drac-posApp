"""Verify identity, snapshots, registration and history integration in native UI."""
import json
from pathlib import Path
from history_playback import Player,ROOT
m=json.loads((ROOT/'evidence/customer-history-map.json').read_text());mi=json.loads((ROOT/'evidence/maya-invoice-map.json').read_text());so=json.loads((ROOT/'evidence/service-order-map.json').read_text())
spec={
 'phones':['CHPhone == "0812 0000 0147" and not CHNewSaved'],
 'history-empty':['CHScope == "arif" and not CHNewSaved'],
 'customer':['CHPhone == "0812 0000 0148"'],
 'plate-collision':['CHPlateKey == "DD1248KL" and CHDraftKey == "B1234ABC" and not CHPlateChanged'],
 'plate-log':['CHPlateKey == "DD2248KL" and CHPlateChanged and CHSavedPlateReason == "Plat kendaraan berubah; diverifikasi Owner." and CHSavedPlateActor == "Owner · sesi demo" and not CHReasonValid'],
 'visit-old':['CHPhone == "0812 0000 0148" and CHPlateKey == "DD2248KL"'],
 'saved':['CHNewSaved and CHRegCustomerId == "DEMO-C0150" and CHRegName == "Arif Ramadhan" and CHRegPhone == "0812 0000 0147" and CHRegPlate == "DD 1248 KL"','CHNewSaved and CHRegCustomerId == "DEMO-C0147" and CHRegName == "Maya Lestari" and CHRegPhone == "0812 0000 0147" and CHRegPlate == "DD 1248 KL" and CHPhone == "0812 0000 0148" and CHPlateKey == "DD2248KL"'],
 'timeline':['CHScope == "maya" and CHNewSaved and CHRegName == "Arif Ramadhan"'],
 'timeline-arif':['CHScope == "arif" and CHNewSaved and CHRegName == "Arif Ramadhan"'],
 'customer-inactive':['not CHCustomerActive'],
 'vehicle-inactive':['not CHVehicleActive'],
 'offline':['not CHNewSaved and CHOffline and MIPaymentCount == 0'],
 'failed':['not CHNewSaved and CHFail and MIPaymentCount == 0'],
 'current-invoice-readonly':['CHActor == "Teknisi" and MIActor == "Teknisi" and MIStage == "paid" and MITotal == 160000 and MIPaymentCount == 1'],
 'timeline-new':['CHPhone == "0812 0000 0148" and CHPlateKey == "DD2248KL" and CHNewSaved and MITotal == 160000 and MIPaymentCount == 1']}
p=Player([m,mi,so],spec);static_checks=[]
def click(label,target):p.click(label,target)
def reset():
    if not p.p()['name'].endswith('-ch-hub'):click('Demo','ch-hub')
    click('Ulang contoh pelanggan / riwayat','ch-customers')
def phone():
    click('Ubah telepon master','ch-customer-edit');click('Kosongkan telepon contoh','ch-customer-invalid');click('Simpan telepon','ch-customer-invalid');click('Isi contoh telepon baru','ch-customer-edit');click('Simpan telepon','ch-customer');p.assertion(spec['customer'][0])
def register(person,invalid=True):
    click('Registrasi kunjungan baru','ch-choose');click('Pilih '+person,'ch-new-visit')
    if invalid:click('Periksa registrasi','ch-visit-invalid')
    click('Isi keluhan contoh','ch-new-visit');click('Periksa registrasi','ch-review');click('Simpan registrasi baru','ch-saved')
def plate(errors=True):
    click('Demo','ch-hub');click('Demo: sebagai Owner','ch-vehicle-owner');click('Ubah plat (Owner)','ch-plate-edit');click('Contoh "dd 2248 kl"','ch-plate-edit')
    if errors:click('Simpan perubahan plat','ch-plate-invalid')
    click('Isi alasan contoh','ch-plate-edit')
    if errors:
        click('Contoh plat sudah digunakan','ch-plate-edit');click('Simpan perubahan plat','ch-plate-collision');p.assertion(spec['plate-collision'][0]);click('Contoh "dd 2248 kl"','ch-plate-edit')
    click('Simpan perubahan plat','ch-vehicle-owner');click('Ubah plat (Owner)','ch-plate-edit');click('Batal','ch-vehicle-owner');click('Riwayat perubahan plat','ch-plate-log');p.assertion(spec['plate-log'][0])
def verify_static_old(device):
    node=p.api.ask('node.get',{'id':m['frames'][device+'-ch-visit-old'],'depth':1});texts='\n'.join(n.get('characters','') for n in node['children']);assert '0812 0000 0147' in texts and 'DD 1248 KL' in texts and 'DD 2248 KL' not in texts
    master_ids={m['fieldModes'][k]['variable'] for k in ('CHPhone','CHPlate')}
    assert not any(master_ids.intersection(n.get('boundVariables',{}).values()) for n in node['children']),node['name']
    invoice=p.api.ask('node.get',{'id':m['frames'][device+'-ch-old-invoice'],'depth':1});assert not any(n.get('name') in ('Bayar','Terbitkan invoice','Konfirmasi pembayaran') for n in invoice['children']);static_checks.append({'device':device,'oldSnapshotsNotBoundToMaster':True,'historicInvoiceReadOnly':True})
try:
    for device in ('desktop','mobile'):
        print(json.dumps({'phase':'customers and snapshots','device':device}),flush=True);p.begin(device);reset()
        click('Cari nama / plat','ch-search');click('Cari telepon 0812 0000 0147','ch-phones');p.assertion(spec['phones'][0]);click('Buka Arif','ch-arif');click('Riwayat pelanggan','ch-history-empty');p.assertion(spec['history-empty'][0])
        click('Kembali ke pelanggan','ch-customers');click('Buka Maya','ch-customer');click('Lihat kendaraan','ch-vehicles');click('Buka kendaraan','ch-vehicle');p.disabled('Ubah plat · hanya Owner');register('Arif Ramadhan');p.assertion(spec['saved'][0])
        click('Lihat riwayat kendaraan','ch-timeline-new');click('Pelanggan','ch-customers');click('Buka Maya','ch-customer');click('Riwayat pelanggan','ch-timeline');p.assertion(spec['timeline'][0]);click('Pelanggan','ch-customers');click('Buka Arif','ch-arif');click('Riwayat pelanggan','ch-timeline-arif');p.assertion(spec['timeline-arif'][0])
        click('Pelanggan','ch-customers');click('Buka Maya','ch-customer');phone();plate();p.shot('plate-log',220 if device=='mobile' else 0)
        click('Riwayat kendaraan','ch-timeline-new');click('Buka kunjungan 0150','ch-saved');p.assertion(spec['saved'][0]);click('Lihat riwayat kendaraan','ch-timeline-new');click('Buka kunjungan 0140','ch-visit-old');p.assertion(spec['visit-old'][0]);verify_static_old(device);p.shot('old-snapshot',150 if device=='mobile' else 0)
        for label,target in [('Diagnosa & Estimasi','old-diagnosis'),('Service Order','old-so'),('Invoice','old-invoice'),('Nota','old-receipt')]:
            click(label,'ch-'+target);click('Kembali ke kunjungan 0140','ch-visit-old')
        click('Cari' if device=='desktop' else 'Demo','ch-search' if device=='desktop' else 'ch-hub')
        if device=='mobile':click('Buka kendaraan','ch-vehicles');click('Cari plat dengan huruf kecil / spasi','ch-search')
        click('Cari "dd 1248 kl"','ch-no-results');click('Kembali mencari','ch-search');click('Cari " dd 2248 kl "','ch-vehicle-owner');click('Pelanggan','ch-customers');click('Cari nama / plat','ch-search');click('Cari telepon 0812 0000 0147','ch-arif')
        print(json.dumps({'phase':'inactive and failure guards','device':device}),flush=True);reset();click('Buka Maya','ch-customer');click('Nonaktifkan pelanggan','ch-deactivate-customer');click('Konfirmasi nonaktifkan','ch-customer-inactive');p.assertion(spec['customer-inactive'][0]);click('Riwayat pelanggan','ch-timeline');click('Registrasi kunjungan baru','ch-choose-inactive');p.disabled('Maya Lestari · nonaktif');click('Pilih Arif Ramadhan','ch-new-visit');click('Isi keluhan contoh','ch-new-visit');click('Periksa registrasi','ch-review');click('Simpan registrasi baru','ch-saved')
        click('Kendaraan','ch-vehicles');click('Buka kendaraan','ch-vehicle');click('Nonaktifkan kendaraan','ch-deactivate-vehicle');click('Konfirmasi nonaktifkan','ch-vehicle-inactive');p.assertion(spec['vehicle-inactive'][0]);p.disabled('Registrasi kunjungan baru');click('Riwayat kendaraan','ch-timeline-new');click('Kendaraan','ch-vehicles');click('Buka kendaraan','ch-vehicle-inactive');click('Aktifkan kendaraan','ch-vehicle');click('Pelanggan','ch-customers');click('Buka Maya','ch-customer-inactive');click('Aktifkan pelanggan','ch-customer')
        for label,target,recover in [('Demo: registrasi offline','offline','Demo: koneksi pulih'),('Demo: gagal simpan registrasi','failed','Demo: coba simpan kembali')]:
            reset();click('Demo','ch-hub');click(label,'ch-new-visit');click('Isi keluhan contoh','ch-new-visit');click('Periksa registrasi','ch-review');click('Simpan registrasi baru','ch-'+target);p.assertion(spec[target][0]);click(recover,'ch-review');click('Simpan registrasi baru','ch-saved')
        print(json.dumps({'phase':'new snapshot and live invoice integration','device':device}),flush=True);reset();click('Kendaraan','ch-vehicles');click('Buka kendaraan','ch-vehicle');register('Maya Lestari');click('Pelanggan','ch-customers');click('Buka Maya','ch-customer');phone();plate(False);click('Riwayat kendaraan','ch-timeline-new');click('Buka kunjungan 0150','ch-saved');p.assertion(spec['saved'][1]);p.shot('new-snapshot',200 if device=='mobile' else 0)
        # Build an existing 0147 invoice without resetting customer master data.
        click('Demo','ch-hub');click('Demo: layanan Maya 0147','so-hub')
        click('Realisasi Rp160.000','so-running');click('Tandai selesai','so-complete');click('Konfirmasi','so-completed');click('Serahkan ke kasir','so-handoff');click('Serahkan ke kasir','so-queued');click('Demo: buka POS sebagai Kasir','maya-queue');click('Buka transaksi','maya-preview');click('Buat invoice draf','maya-draft');click('Tinjau penerbitan','maya-issue');click('Terbitkan invoice','maya-final');click('Tunai','maya-cash');click('Isi contoh Rp200.000','maya-cash-filled');click('Tinjau pembayaran','maya-confirm-cash');click('Konfirmasi pembayaran','maya-paid');click('Riwayat kunjungan','ch-timeline-new');p.assertion(spec['timeline-new'][0])
        click('Buka kunjungan 0147','ch-visit-current');click('Invoice','maya-paid');click('Riwayat kunjungan','ch-timeline-new');click('Demo','ch-hub');click('Demo: sebagai Teknisi','ch-customers');click('Buka Maya','ch-customer');click('Riwayat pelanggan','ch-timeline-new');click('Buka kunjungan 0147','ch-visit-current');click('Invoice','ch-current-invoice-readonly');p.assertion(spec['current-invoice-readonly'][0]);p.shot('technician-invoice',180 if device=='mobile' else 0)
    fonts=p.c('text.missingFonts');assert not fonts.get('families',[])
    report={'status':'complete','nativeStepsPassed':len(p.steps),'runtimeChecksPassed':len(p.checks),'disabledControlsPassed':p.disabled_checks,'staticSnapshotChecks':static_checks,'screenshots':p.screens,'fonts':fonts,'limits':['scripted sample inputs','one new registration fixture per demo reset','no real database, authentication or stock/payment writes']};(ROOT/'evidence/customer-history-verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps({'nativeStepsPassed':len(p.steps),'runtimeChecksPassed':len(p.checks),'disabledControls':len(p.disabled_checks)}))
finally:p.close()
