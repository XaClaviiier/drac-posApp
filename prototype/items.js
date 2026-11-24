"use strict";

(() => {
  const catalog = Object.freeze([
    { id: "service-check", kind: "service", label: "Pemeriksaan AC", unit: "pekerjaan", price: 50000 },
    { id: "service-clean", kind: "service", label: "Cuci evaporator", unit: "pekerjaan", price: 350000 },
    { id: "service-freon", kind: "service", label: "Vacuum dan isi freon", unit: "pekerjaan", price: 250000 },
    { id: "part-filter", kind: "part", label: "Filter kabin", unit: "pcs", price: 100000 },
    { id: "part-dryer", kind: "part", label: "Receiver dryer", unit: "pcs", price: 180000 },
    { id: "part-compressor", kind: "part", label: "Kompresor contoh", unit: "unit", price: 1850000 },
    { id: "part-refrigerant", kind: "part", label: "Refrigeran timbang (contoh)", unit: "kg", price: 200001 },
    { id: "part-oil", kind: "part", label: "Oli kompresor (contoh)", unit: "liter", price: 100001 },
    { id: "part-hose", kind: "part", label: "Selang AC (contoh)", unit: "meter", price: 80001 },
    { id: "service-hour", kind: "service", label: "Pengerjaan per jam (contoh)", unit: "jam", price: 150001 },
  ].map(Object.freeze));
  const units = ["pcs", "unit", "pekerjaan", "kg", "liter", "meter", "jam"];
  const fractional = ["kg", "liter", "meter", "jam"];
  const money = new Intl.NumberFormat("id-ID", { style: "currency", currency: "IDR", maximumFractionDigits: 0 });
  const integer = (value, min = 0, max = 1000000000) => /^\d+$/.test(String(value)) && Number.isSafeInteger(Number(value)) && Number(value) >= min && Number(value) <= max;

  function quantity(value, unit) {
    const raw = String(value).replace(",", ".");
    if (raw.length > 30) return null;
    const text = raw.replace(/^0+(?=\d)/, "");
    if (!units.includes(unit) || !/^\d{1,6}(?:\.\d{1,3})?$/.test(text)) return null;
    const [whole, fraction = ""] = text.split(".");
    const scaled = BigInt(whole) * 1000n + BigInt(fraction.padEnd(3, "0"));
    if (scaled <= 0n || scaled > 999999999n || (!fractional.includes(unit) && scaled % 1000n !== 0n)) return null;
    return scaled;
  }

  function canonical(value, unit) {
    const scaled = quantity(value, unit);
    if (scaled === null) return null;
    const fraction = String(scaled % 1000n).padStart(3, "0").replace(/0+$/, "");
    return `${scaled / 1000n}${fraction ? `.${fraction}` : ""}`;
  }

  function subtotal(item) {
    const qty = quantity(item.quantity, item.unit);
    if (qty === null || !integer(item.unitPrice)) return null;
    const result = (qty * BigInt(item.unitPrice) + 500n) / 1000n;
    return result <= BigInt(Number.MAX_SAFE_INTEGER) ? Number(result) : null;
  }

  function totals(items) {
    let service = 0n, part = 0n;
    for (const item of items) {
      const amount = subtotal(item);
      if (amount === null || !["service", "part"].includes(item.kind)) return null;
      if (item.kind === "service") service += BigInt(amount);
      else part += BigInt(amount);
    }
    if (service + part > BigInt(Number.MAX_SAFE_INTEGER)) return null;
    return { service: Number(service), part: Number(part), total: Number(service + part) };
  }

  window.POSItems = Object.freeze({ catalog, quantity, canonical, subtotal, totals, integer, money, fractional: (unit) => fractional.includes(unit) });
})();
