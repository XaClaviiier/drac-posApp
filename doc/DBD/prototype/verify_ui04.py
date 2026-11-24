"""Verify native UI-04: all component states, role journeys, money and preservation."""

import copy
import json
import re
import sys
import zipfile
from pathlib import Path


def contrast_checks():
    from build_ui04 import TOKENS
    def lum(hex_color):
        values = [int(hex_color[j:j+2], 16) / 255 for j in (1, 3, 5)]
        linear = [c / 12.92 if c <= .04045 else ((c + .055) / 1.055) ** 2.4 for c in values]
        return sum(c * w for c, w in zip(linear, (.2126, .7152, .0722)))
    results = {}
    for theme, tk in TOKENS.items():
        for fg, bg in (("text", "surface"), ("text2", "canvas"), ("text2", "sidebar"), ("action", "surface"), ("on_action", "action"), ("on_action", "action_hover"), ("on_action", "action_press"), ("warn", "warn_bg"), ("text", "hover_bg"), ("text", "press_bg")):
            a, b = sorted((lum(tk[fg]), lum(tk[bg])))
            ratio = (b + .05) / (a + .05)
            results[f"{theme}/{fg}/{bg}"] = round(ratio, 3)
    return results


def load(path):
    with zipfile.ZipFile(path) as z:
        return json.loads(z.read("document.json"))


def metadata(node):
    return json.loads(node.get("plugin_data", {}).get("pos.ui04", "{}"))


def descendants(nodes, root, states=False):
    seen, stack = set(), [root]
    while stack:
        i = stack.pop()
        if i in seen or i not in nodes:
            continue
        seen.add(i)
        n = nodes[i]
        yield i
        stack.extend(n.get("children", []))
        if n.get("type") == "instance" and states:
            stack.append(n["component"])
            if states:
                main = nodes.get(n["component"], {})
                component_set = nodes.get(main.get("parent"), {})
                if component_set.get("type") == "componentSet":
                    stack.extend(component_set.get("children", []))
        if states:
            for interaction in n.get("interactions", []):
                stack.extend(a["dest"] for a in interaction.get("actions", []) if a.get("type") == "changeTo")


def text(nodes, root):
    return "\n".join(nodes[i].get("characters", "") for i in descendants(nodes, root))


def rp(v):
    return "Rp " + f"{v:,}".replace(",", ".")


def validate(doc):
    nodes = {int(k): v for k, v in doc["nodes"].items()}
    errors, graph = [], {}
    screens = {i: metadata(n) for i, n in nodes.items() if metadata(n).get("kind") == "screen"}
    index = {(m["theme"], m["device"], m["role"], m["route"]): i for i, m in screens.items()}
    for i, n in nodes.items():
        if "parent" in n and n["parent"] is not None:
            p = nodes.get(n["parent"])
            if not p or i not in p.get("children", []):
                errors.append(f"Broken parent/child {i} name={n.get('name')} parent={n.get('parent')} parent_children={p.get('children') if p else None}")
        for c in n.get("children", []):
            if c not in nodes or nodes[c].get("parent") != i:
                errors.append(f"Broken child {i}/{c}")
        for interaction in n.get("interactions", []):
            for a in interaction.get("actions", []):
                if "dest" in a and a["dest"] not in nodes:
                    errors.append(f"Missing target {i}/{a['dest']}")
        for key in ("name", "characters"):
            if "mekanik" in n.get(key, "").lower() or "supervisor" in n.get(key, "").lower():
                errors.append(f"Old role {i}/{key}")
        if n.get("type") == "componentSet":
            variants = {nodes[c]["name"].split("=", 1)[-1]: c for c in n.get("children", [])}
            for state in ("Default", "Hover", "Pressed", "Focus", "Disabled"):
                if state not in variants:
                    errors.append(f"Missing hover state {i}/{state}")
            if "Default" in variants:
                triggers = {it["trigger"]["type"] for it in nodes[variants["Default"]].get("interactions", [])}
                if not {"mouseEnter", "mouseLeave", "mouseDown", "mouseUp"} <= triggers:
                    errors.append(f"Missing hover triggers {i}")
            if "Disabled" in variants and any(nodes[c].get("interactions") for c in descendants(nodes, variants["Disabled"])):
                errors.append(f"Disabled has actions {i}")
        if n.get("type") == "instance" and "component" in n:
            source = nodes.get(n["component"], {})
            if source.get("children") and not n.get("children"):
                errors.append(f"Unmaterialized instance {i}")
            elif text(nodes, i) != text(nodes, n["component"]):
                errors.append(f"Materialized label differs from source {i}")
    for root, m in screens.items():
        edges = set()
        if m["device"] == "Mobile" and m["role"] != "Login":
            for c in nodes[root].get("children", []):
                n = nodes[c]
                if n.get("type") == "text" and n.get("transform", [0]*6)[5] == 18:
                    if 18 + n.get("height", 0) > 58:
                        errors.append(f"Mobile header overlaps metadata {root}")
        if m["role"] in ("Teknisi", "Kasir"):
            expanded_text = "\n".join(nodes[i].get("characters", "") for i in descendants(nodes, root, states=True))
            if re.search(r"(?:HPP|harga beli|harga pembelian|pengeluaran|profit|laba)\s*(?:contoh)?\s*[:=]?\s*Rp\s*[\d.]", expanded_text, re.I):
                errors.append(f"Restricted financial snippet {root}")
        for i in descendants(nodes, root, states=True):
            n = nodes[i]
            for interaction in n.get("interactions", []):
                for action in interaction.get("actions", []):
                    if action.get("type") == "navigate":
                        edges.add(action["dest"])
            # Data checks are tied to both visible native text and metadata.
            data = metadata(n)
            body = text(nodes, i)
            if data.get("kind") == "line":
                if data["quantity"] * data["unit_price"] != data["subtotal"]:
                    errors.append(f"Line arithmetic {i}")
                if rp(data["unit_price"]) not in body or rp(data["subtotal"]) not in body:
                    errors.append(f"Line visible values {i}")
            if data.get("kind") == "totals" and data["jasa"] + data["barang"] != data["total"]:
                errors.append(f"Total arithmetic {i}")
            if data.get("kind") == "totals":
                for label, field in (("Subtotal jasa", "jasa"), ("Subtotal barang", "barang"), ("Total", "total")):
                    if label + ": " + rp(data[field]) not in body:
                        errors.append(f"Visible total mismatch {i}/{field}")
            if data.get("kind") == "payment" and data["invoice_total"] - data["received"] != data["balance"]:
                errors.append(f"Payment arithmetic {i}")
            if data.get("kind") == "master" and m["role"] != "Owner":
                errors.append(f"HPP content leak {root}")
        graph[root] = edges
    checked = {}
    for theme in ("Light", "Dark"):
        for device in ("Desktop", "Mobile"):
            for role in ("Owner", "Teknisi", "Kasir"):
                start = index.get((theme, device, role, "home"))
                if start is None:
                    errors.append(f"Missing home {theme}/{device}/{role}")
                    continue
                visited, stack = set(), [start]
                while stack:
                    root = stack.pop()
                    if root in visited:
                        continue
                    visited.add(root)
                    m = screens.get(root, {})
                    if m.get("role") == "Login":
                        continue  # Explicit logout/account selection is outside a logged-in journey.
                    if m.get("role") != role:
                        errors.append(f"Role escape {role} to {root}: {m}")
                        continue
                    if m["device"] != device:
                        errors.append(f"Device escape {root}")
                    if role != "Owner" and m["route"] in ("master", "audit", "correction", "revised", "raised"):
                        errors.append(f"Owner-only escape {role}/{root}")
                    if role == "Teknisi" and m["route"] in ("payment", "paid"):
                        errors.append(f"Technician payment escape {root}")
                    stack.extend(graph.get(root, ()))
                expected = {i for i, m in screens.items() if m["role"] == role and m["device"] == device}
                if not expected <= visited:
                    errors.append(f"Unreachable role states {role}/{device}: {sorted(expected - visited)}")
                checked[f"{theme}/{device}/{role}"] = len(visited)
            for state in ("base", "invalid", "loading", "error", "password"):
                if (theme, device, "Login", state) not in index:
                    errors.append(f"Missing login {theme}/{device}/{state}")
    # Verify scenario totals are not detached from the actual line-item set.
    for key, root in index.items():
        theme, device, role, route = key
        rows, totals, payments, adjustments = [], [], [], []
        for i in descendants(nodes, root):
            data = metadata(nodes[i])
            if data.get("kind") == "line":
                rows.append(data)
            elif data.get("kind") == "totals":
                totals.append(data)
            elif data.get("kind") == "payment":
                payments.append(data)
            elif data.get("kind") == "adjustment":
                adjustments.append(data)
        if rows:
            row_sum = sum(row["subtotal"] for row in rows)
            if len(totals) != 1 or totals[0]["total"] != row_sum:
                errors.append(f"Rows do not reconcile {key}")
            jasa = sum(row["subtotal"] for row in rows if row["category"] == "Jasa")
            barang = sum(row["subtotal"] for row in rows if row["category"] == "Part")
            if totals and (totals[0]["jasa"], totals[0]["barang"]) != (jasa, barang):
                errors.append(f"Categories do not reconcile {key}")
            adjusted = row_sum + sum(a["amount"] for a in adjustments)
            if payments and payments[0]["invoice_total"] != adjusted:
                errors.append(f"Receipt total differs from invoice rows {key}")
            for a in adjustments:
                if a["total"] != adjusted:
                    errors.append(f"Adjustment total mismatch {key}")
            expected = {"before": 790000, "wo": 780000, "draft": 780000, "draft-after": 770000, "final": 780000, "revised": 430000, "paid": 780000, "raised": 780000, "revised-paid": 430000, "paid-raised": 780000, "revised-paid-raised": 430000}.get(route)
            if expected is not None and row_sum != expected:
                errors.append(f"Unexpected scenario amount {key}: {row_sum}")
        if payments:
            received = 830000 if route in ("paid-raised", "revised-paid-raised") else 780000 if route in ("paid", "revised-paid") else 500000
            if payments[0]["received"] != received:
                errors.append(f"Receipt rewritten {key}")
            visible = text(nodes, root)
            balance = payments[0]["balance"]
            label = "Kelebihan bayar" if balance < 0 else "Sisa tagihan" if balance > 0 else "Sisa tagihan (lunas)"
            if "Diterima Kasir: " + rp(received) not in visible or label + ": " + rp(abs(balance)) not in visible:
                errors.append(f"Visible payment mismatch {key}")
    return {"passed": not errors, "errors": sorted(set(errors)), "screens": len(screens), "nodes": len(nodes), "component_sets": sum(n.get("type") == "componentSet" for n in nodes.values()), "role_graphs": checked}


def no_motion(doc):
    result = copy.deepcopy(doc)
    for n in result["nodes"].values():
        for interaction in n.get("interactions", []):
            interaction["duration_ms"] = 0
            interaction["transition"] = {"type": "instant"}
    return result


def preserve_print(source, candidate):
    def subtree(doc):
        nodes = {int(k): v for k, v in doc["nodes"].items()}
        root = next(i for i, n in nodes.items() if n.get("name") == "Invoice A4 / Template siap isi")
        return {i: nodes[i] for i in descendants(nodes, root)}
    return subtree(source) == subtree(candidate)


def negative_checks(doc):
    nodes = doc["nodes"]
    ids = {tuple(metadata(n).get(k) for k in ("theme", "device", "role", "route")): int(i) for i, n in nodes.items() if metadata(n).get("kind") == "screen"}
    bad = copy.deepcopy(doc)
    root = ids[("Light", "Desktop", "Kasir", "home")]
    bad["nodes"][str(root)]["interactions"] = [{"trigger": {"type": "onClick"}, "actions": [{"type": "navigate", "dest": ids[("Light", "Desktop", "Owner", "audit")]}]}]
    assert not validate(bad)["passed"], "Verifier accepted role escape"
    bad = copy.deepcopy(doc)
    line = next(i for i, n in nodes.items() if metadata(n).get("kind") == "line")
    data = metadata(bad["nodes"][line]); data["subtotal"] += 1
    bad["nodes"][line]["plugin_data"]["pos.ui04"] = json.dumps(data)
    assert not validate(bad)["passed"], "Verifier accepted bad money"
    bad = copy.deepcopy(doc)
    default = next(i for i, n in nodes.items() if n.get("type") == "component" and n.get("name") == "State=Default")
    bad["nodes"][default]["interactions"] = []
    assert not validate(bad)["passed"], "Verifier accepted missing hover"
    bad = copy.deepcopy(doc)
    tech = ids[("Light", "Desktop", "Teknisi", "home")]
    instance = next(i for i in descendants({int(k): v for k, v in bad["nodes"].items()}, tech) if bad["nodes"][str(i)].get("type") == "instance")
    component = bad["nodes"][str(bad["nodes"][str(instance)]["component"])]
    siblings = bad["nodes"][str(component["parent"])]["children"]
    focus = next(i for i in siblings if bad["nodes"][str(i)]["name"] == "State=Focus")
    bad["nodes"][str(focus)]["interactions"].append({"trigger": {"type": "onClick"}, "actions": [{"type": "navigate", "dest": ids[("Light", "Desktop", "Owner", "audit")]}]})
    assert not validate(bad)["passed"], "Verifier accepted focus-variant role escape"
    bad = copy.deepcopy(doc)
    payment = next(i for i, n in nodes.items() if metadata(n).get("kind") == "payment")
    data = metadata(bad["nodes"][payment]); data["invoice_total"] = 1; data["balance"] = 1 - data["received"]
    bad["nodes"][payment]["plugin_data"]["pos.ui04"] = json.dumps(data)
    tech_nodes = {int(k): v for k, v in bad["nodes"].items()}
    label = next(i for i in tech_nodes[tech].get("children", []) if tech_nodes[i].get("type") == "text")
    bad["nodes"][str(label)]["characters"] += " HPP Rp 50.000"
    total_text = next(i for i, n in nodes.items() if n.get("characters", "").startswith("Total: Rp "))
    bad["nodes"][total_text]["characters"] = "Total: Rp 1"
    bad["nodes"][str(instance)]["children"] = []
    failures = validate(bad)["errors"]
    assert any("Receipt total differs" in e for e in failures), "Verifier accepted detached invoice amount"
    assert any("Restricted financial snippet" in e for e in failures), "Verifier accepted HPP snippet"
    assert any("Visible total mismatch" in e for e in failures), "Verifier accepted wrong displayed total"
    assert any("Unmaterialized instance" in e for e in failures), "Verifier accepted invisible control"
    return ["role_escape_rejected", "incorrect_subtotal_rejected", "missing_hover_rejected", "focus_variant_role_escape_rejected", "detached_invoice_amount_rejected", "hpp_snippet_rejected", "wrong_visible_total_rejected", "invisible_control_rejected"]


def main():
    path = sys.argv[1]
    doc = load(path)
    result = validate(doc)
    result["contrast"] = contrast_checks()
    result["passed"] &= min(result["contrast"].values()) >= 4.5
    if "--negative" in sys.argv:
        result["negative_checks"] = negative_checks(doc)
    if "--source" in sys.argv:
        source_path = sys.argv[sys.argv.index("--source") + 1]
        source = load(source_path)
        result["invoice_print_preserved"] = preserve_print(source, doc)
        result["passed"] &= result["invoice_print_preserved"]
        if "--snapshot-source" in sys.argv:
            from complete_ui04 import save_archive
            snapshot = sys.argv[sys.argv.index("--snapshot-source") + 1]
            if Path(snapshot).exists():
                raise FileExistsError("Preserved source snapshot already exists: " + snapshot)
            save_archive(source_path, snapshot, source)
            result["source_snapshot"] = snapshot
    if "--manifest-out" in sys.argv:
        output = sys.argv[sys.argv.index("--manifest-out") + 1]
        manifest = json.loads(Path(path + ".manifest.json").read_text(encoding="utf-8"))
        manifest["source_snapshot"] = "pos-ui-before-ui04.figcraft"
        manifest["published"] = "pos-ui.figcraft"
        Path(output).write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    if "--no-motion-out" in sys.argv:
        from complete_ui04 import save_archive
        output = sys.argv[sys.argv.index("--no-motion-out") + 1]
        reduced = no_motion(doc)
        save_archive(path, output, reduced)
        reread = load(output)
        result["no_motion_equal_content"] = no_motion(doc) == reread
        result["no_motion_zero_durations"] = all(not it.get("duration_ms", 0) for n in reread["nodes"].values() for it in n.get("interactions", []))
        result["passed"] &= result["no_motion_equal_content"] and result["no_motion_zero_durations"]
    if "--report" in sys.argv:
        output = sys.argv[sys.argv.index("--report") + 1]
        Path(output).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
