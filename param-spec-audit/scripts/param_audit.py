#!/usr/bin/env python3
"""IP parameter / hardcoded-constant audit vs spec, SoC usage and DV coverage.

Produces a single self-contained HTML report.
"""
import argparse
import csv
import glob
import html
import os
import re
import sys
from collections import defaultdict
from datetime import datetime

LIT_RE = re.compile(r"^\s*(\d*\s*'\s*[sS]?[bBhHdDoO]\s*[0-9a-fA-FxXzZ_?]+|'\s*[01xXzZ]|\d+|\{(?:\s*(?:\d*'[sS]?[bBhHdDoO][0-9a-fA-FxXzZ_]+|\d+)\s*,?)+\})\s*$")
PARAM_RE = re.compile(
    r"\b(parameter|localparam)\b\s*(?:(?:int|integer|logic|bit|reg|signed|unsigned)\s*)*"
    r"(\[[^\]]*\])?\s*(\w+)\s*=\s*([^,;]+?)\s*(?=,\s*(?:parameter|localparam)?\s*(?:\[[^\]]*\])?\s*\w+\s*=|[,;]|\)\s*\(|\)\s*$|$)",
    re.S)
DEFAULT_HINT = re.compile(r"DEFAULT|RESET|RST_VAL|INIT|IDLE|TIEOFF|POLARITY", re.I)


def strip_comments(txt):
    txt = re.sub(r"/\*.*?\*/", lambda m: "\n" * m.group(0).count("\n"), txt, flags=re.S)
    return re.sub(r"//[^\n]*", "", txt)


def lineno(txt, pos):
    return txt.count("\n", 0, pos) + 1


def to_int(v):
    if v is None:
        return None
    s = str(v).strip().replace("_", "").replace(" ", "")
    m = re.match(r"^(\d*)'[sS]?([bBhHdDoO])([0-9a-fA-F]+)$", s)
    if m:
        return int(m.group(3), {"b": 2, "h": 16, "d": 10, "o": 8}[m.group(2).lower()])
    if s in ("'0", "0"):
        return 0
    if re.match(r"^-?\d+$", s):
        return int(s)
    return None


def norm(v):
    i = to_int(v)
    if i is None:
        return str(v).strip()
    return str(i) if i < 2 ** 32 else hex(i)


def match_close(txt, start):
    depth = 0
    for i in range(start, len(txt)):
        if txt[i] == "(":
            depth += 1
        elif txt[i] == ")":
            depth -= 1
            if depth == 0:
                return i
    return len(txt) - 1


def split_conns(body):
    out, depth, cur = [], 0, ""
    for ch in body:
        if ch in "({[":
            depth += 1
        elif ch in ")}]":
            depth -= 1
        if ch == "," and depth == 0:
            out.append(cur)
            cur = ""
        else:
            cur += ch
    if cur.strip():
        out.append(cur)
    res = []
    for c in out:
        m = re.match(r"\s*\.(\w+)\s*\((.*)\)\s*$", c, re.S)
        if m:
            res.append((m.group(1), m.group(2).strip()))
    return res


def parse_rtl(files):
    mods = {}
    for f in files:
        raw = open(f, errors="ignore").read()
        txt = strip_comments(raw)
        for mm in re.finditer(r"\bmodule\s+(\w+)", txt):
            name = mm.group(1)
            end = txt.find("endmodule", mm.end())
            body = txt[mm.start(): end if end > 0 else len(txt)]
            base = mm.start()
            params = {}
            for pm in PARAM_RE.finditer(body):
                params[pm.group(3)] = {
                    "kind": pm.group(1), "range": pm.group(2) or "",
                    "default": " ".join(pm.group(4).split()),
                    "file": f, "line": lineno(txt, base + pm.start())}
            mods[name] = {"file": f, "body": body, "base": base, "txt": txt, "params": params}
    for name, m in mods.items():
        body = m["body"]
        for p in m["params"].values():
            p["uses"] = len(re.findall(r"\b%s\b" % re.escape(p_name(p, m)), body)) - 1
    return mods


def p_name(p, m):
    for k, v in m["params"].items():
        if v is p:
            return k
    return ""


def find_instances(txt, known, base=0, ftxt=None):
    ftxt = ftxt if ftxt is not None else txt
    res = []
    for k in known:
        for im in re.finditer(r"\b%s\b\s*(#\s*\()?" % re.escape(k), txt):
            pos = im.end()
            povr = {}
            if im.group(1):
                close = match_close(txt, pos - 1)
                povr = dict(split_conns(txt[pos:close]))
                pos = close + 1
            mi = re.match(r"\s*(\w+)\s*(\[[^\]]*\])?\s*\(", txt[pos:])
            if not mi or mi.group(1) in ("module",):
                continue
            ps = pos + mi.end() - 1
            pe = match_close(txt, ps)
            res.append({"module": k, "inst": mi.group(1), "params": povr,
                        "ports": split_conns(txt[ps + 1:pe]),
                        "line": lineno(ftxt, base + im.start())})
    return res


def parse_dv(dv_dirs, pnames):
    hits = defaultdict(lambda: defaultdict(set))
    pats = [r"-param(?:eter)?\s+(\w+)\s+(\S+)", r"-g(\w+)=(\S+)", r"-defparam\s+\S*?\.?(\w+)=(\S+)",
            r"\.(\w+)\s*\(\s*([^()]+?)\s*\)", r"`define\s+(\w+)\s+(\S+)", r"\bset\s+(\w+)\s+(\S+)"]
    for d in dv_dirs:
        files = []
        for root, dirs, fs in os.walk(d):
            dirs[:] = [x for x in dirs if not re.search(r"jgproject|cov_work|vmgr_|Result|html_|merged|\.tmp|INCA|xcelium", x)]
            files += [os.path.join(root, x) for x in fs]
        for f in files:
            if not re.search(r"\.(tcl|setup|sv|svh|v|f|csh|sh|cfg|mk)$|Makefile|RUNCMD", f):
                continue
            if "waiver" in os.path.basename(f) or os.path.getsize(f) > 2_000_000:
                continue
            txt = open(f, errors="ignore").read()
            cfg = os.path.relpath(os.path.dirname(f), d)
            for pat in pats:
                for m in re.finditer(pat, txt):
                    if m.group(1) in pnames:
                        hits[m.group(1)][norm(m.group(2).strip("\"'{}\\"))].add(cfg)
    return hits


def load_spec(path):
    spec = {}
    if path and os.path.isfile(path):
        for r in csv.DictReader(open(path)):
            if r.get("name"):
                spec[r["name"].strip()] = {k: (v or "").strip() for k, v in r.items()}
    return spec


def allowed(val, rule):
    if not rule or rule.lower() in ("any", "*"):
        return True
    iv = to_int(val)
    for part in rule.split("|"):
        part = part.strip()
        if ".." in part and iv is not None:
            lo, hi = [to_int(x) for x in part.split("..")]
            if lo is not None and hi is not None and lo <= iv <= hi:
                return True
        elif norm(part) == norm(val):
            return True
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ip", required=True)
    ap.add_argument("--top", required=True)
    ap.add_argument("--rtl", nargs="+", required=True, help="IP RTL files/globs")
    ap.add_argument("--soc", nargs="*", default=[], help="SoC RTL files/globs instantiating the IP")
    ap.add_argument("--soc-csv", help="CSV name,value,soc_context if SoC RTL unavailable")
    ap.add_argument("--dv", nargs="*", default=[], help="DV dirs (formal/sim) to scan for param values")
    ap.add_argument("--spec", help="spec params CSV")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    rtl = sorted({f for g in a.rtl for f in glob.glob(g)})
    if not rtl:
        sys.exit("no RTL files matched")
    mods = parse_rtl(rtl)
    if a.top not in mods:
        sys.exit("top %s not found" % a.top)
    spec = load_spec(a.spec)

    tieoffs, propag = [], []
    parents = defaultdict(set)
    for mname, m in mods.items():
        for inst in find_instances(m["body"], [k for k in mods if k != mname], m["base"], m["txt"]):
            parents[inst["module"]].add(mname)

    def scope_hints(mname, child=None):
        seen, stack, out = set(), [mname], []
        while stack:
            x = stack.pop()
            if x in seen:
                continue
            seen.add(x)
            out += ["%s.%s" % (x, p) if x != mname else p for p in mods[x]["params"] if DEFAULT_HINT.search(p)]
            stack += list(parents[x])
        if child:
            out += ["%s.%s" % (child, p) for p in mods[child]["params"] if DEFAULT_HINT.search(p)]
        return sorted(set(out))

    for mname, m in mods.items():
        for inst in find_instances(m["body"], [k for k in mods if k != mname], m["base"], m["txt"]):
            child = mods[inst["module"]]
            for cp, cinfo in child["params"].items():
                if cinfo["kind"] != "parameter":
                    continue
                passed = inst["params"].get(cp)
                propag.append({"parent": mname, "inst": inst["inst"], "child": inst["module"], "param": cp,
                               "value": passed if passed is not None else "(child default %s)" % cinfo["default"],
                               "status": "PASSED" if passed is not None else
                               ("NOT_PROPAGATED" if cp in m["params"] else "CHILD_DEFAULT"),
                               "file": m["file"], "line": inst["line"]})
            for port, expr in inst["ports"]:
                if expr and LIT_RE.match(expr):
                    hint = scope_hints(mname, inst["module"])
                    tieoffs.append({"module": mname, "inst": inst["inst"], "child": inst["module"],
                                    "port": port, "value": expr, "file": m["file"], "line": inst["line"],
                                    "status": "SUSPECT" if hint else "REVIEW",
                                    "note": ("literal used while %s exist(s) in this/ancestor scope and cannot reach here" % ", ".join(hint)) if hint else ""})
        for am in re.finditer(r"\bassign\s+([^=;]+?)\s*=\s*([^;]+);", m["body"]):
            if LIT_RE.match(am.group(2)):
                hint = scope_hints(mname)
                tieoffs.append({"module": mname, "inst": "-", "child": "-", "port": am.group(1).strip(),
                                "value": am.group(2).strip(), "file": m["file"],
                                "line": lineno(m["txt"], m["base"] + am.start()),
                                "status": "SUSPECT" if hint else "REVIEW",
                                "note": ("param(s) %s exist in scope but a literal is used" % ", ".join(hint)) if hint else ""})
        for cm in re.finditer(r"([?:]|\belse\b|\bdefault\s*:)\s*(\d+\s*'\s*[bhdo]\s*[0-9a-fA-F_]+|'[01])\s*[;:)]", m["body"], re.I):
            hint = scope_hints(mname)
            if hint:
                tieoffs.append({"module": mname, "inst": "-", "child": "-", "port": "(expr)",
                                "value": cm.group(2), "file": m["file"],
                                "line": lineno(m["txt"], m["base"] + cm.start()), "status": "SUSPECT",
                                "note": "literal in mux/else/default branch while %s exists" % ", ".join(hint)})

    top_params = mods[a.top]["params"]
    soc = defaultdict(list)
    for f in sorted({f for g in a.soc for f in glob.glob(g)}):
        t = strip_comments(open(f, errors="ignore").read())
        for inst in find_instances(t, [a.top]):
            for k, v in inst["params"].items():
                soc[k].append((v, "%s:%s %s" % (os.path.basename(f), inst["line"], inst["inst"])))
            for k in top_params:
                if k not in inst["params"] and top_params[k]["kind"] == "parameter":
                    soc[k].append((top_params[k]["default"], "%s:%s %s (default)" % (os.path.basename(f), inst["line"], inst["inst"])))
    if a.soc_csv and os.path.isfile(a.soc_csv):
        for r in csv.DictReader(open(a.soc_csv)):
            soc[r["name"].strip()].append((r["value"].strip(), r.get("soc_context", "csv").strip()))

    dv = parse_dv(a.dv, set(top_params))
    rows = []
    for name, p in top_params.items():
        if p["kind"] != "parameter":
            continue
        s = spec.get(name)
        issues = []
        dvvals = set(dv.get(name, {}).keys())
        dv_eff = dvvals or {norm(p["default"])}
        socvals = {norm(v) for v, _ in soc.get(name, [])}
        if not s:
            issues.append("NOT_IN_SPEC")
        else:
            if s.get("spec_default") and norm(s["spec_default"]) != norm(p["default"]):
                issues.append("SPEC_DEFAULT_MISMATCH")
            if not allowed(p["default"], s.get("spec_allowed")):
                issues.append("RTL_DEFAULT_OUT_OF_RANGE")
            bad = [v for v in socvals if not allowed(v, s.get("spec_allowed"))]
            if bad:
                issues.append("SOC_OUT_OF_RANGE(%s)" % ",".join(bad))
        miss = sorted(socvals - dv_eff)
        if miss:
            issues.append("DV_GAP_SOC_VALUE(%s)" % ",".join(miss))
        if len(dv_eff) <= 1:
            issues.append("DV_SINGLE_VALUE")
        if not dvvals:
            issues.append("DV_DEFAULT_ONLY")
        if p.get("uses", 1) <= 0:
            issues.append("UNUSED")
        np_ = [x for x in propag if x["parent"] == a.top and x["status"] == "NOT_PROPAGATED" and x["param"] == name]
        if np_:
            issues.append("NOT_PROPAGATED")
        fail = any(i.split("(")[0] in ("SPEC_DEFAULT_MISMATCH", "RTL_DEFAULT_OUT_OF_RANGE", "SOC_OUT_OF_RANGE",
                                       "DV_GAP_SOC_VALUE", "NOT_PROPAGATED") for i in issues)
        status = "FAIL" if fail else ("WARN" if issues else "PASS")
        rows.append({"name": name, "range": p["range"], "default": p["default"], "spec": s,
                     "soc": soc.get(name, []), "dv": dv.get(name, {}), "issues": issues, "status": status,
                     "file": p["file"], "line": p["line"]})

    for t in tieoffs:
        if t["status"] == "SUSPECT":
            for r in rows:
                if re.search(r"\b%s\b" % re.escape(r["name"]), t["note"]):
                    if "HARDCODED_LITERAL_BYPASS" not in r["issues"]:
                        r["issues"].append("HARDCODED_LITERAL_BYPASS")
                        r["status"] = "FAIL"
    write_html(a, rows, tieoffs, propag, mods)
    print("Report: %s  params=%d FAIL=%d WARN=%d tieoffs=%d suspect=%d" % (
        a.out, len(rows), sum(r["status"] == "FAIL" for r in rows), sum(r["status"] == "WARN" for r in rows),
        len(tieoffs), sum(t["status"] == "SUSPECT" for t in tieoffs)))


def e(x):
    return html.escape(str(x))


def badge(s):
    c = {"PASS": "#2e7d32", "WARN": "#ef6c00", "FAIL": "#c62828", "SUSPECT": "#c62828", "REVIEW": "#ef6c00",
         "NOT_PROPAGATED": "#c62828", "PASSED": "#2e7d32", "CHILD_DEFAULT": "#607d8b"}.get(s, "#607d8b")
    return '<span class="b" style="background:%s">%s</span>' % (c, e(s))


def write_html(a, rows, tieoffs, propag, mods):
    css = ("body{font-family:Arial,sans-serif;margin:24px;color:#222}h1{color:#0067b9}table{border-collapse:collapse;"
           "width:100%;margin:12px 0 28px}th,td{border:1px solid #ccc;padding:5px 8px;font-size:13px;vertical-align:top}"
           "th{background:#0067b9;color:#fff;text-align:left}tr:nth-child(even){background:#f5f8fb}.b{color:#fff;"
           "padding:2px 6px;border-radius:3px;font-size:11px;font-weight:bold}.c{display:inline-block;padding:12px 18px;"
           "margin:4px;border-radius:6px;background:#eef3f8;font-size:15px}code{background:#f0f0f0;padding:1px 3px}")
    h = ["<html><head><meta charset='utf-8'><title>%s parameter audit</title><style>%s</style></head><body>" % (e(a.ip), css)]
    h.append("<h1>%s &mdash; Parameter &amp; Hardcoded-Constant Spec Compliance</h1>" % e(a.ip))
    h.append("<p>Top: <code>%s</code> | Generated %s | Spec: <code>%s</code></p>" % (
        e(a.top), datetime.now().strftime("%Y-%m-%d %H:%M"), e(a.spec or "none")))
    n = lambda k: sum(r["status"] == k for r in rows)
    h.append("".join('<div class="c">%s <b>%s</b></div>' % (k, v) for k, v in [
        ("Top params", len(rows)), ("PASS", n("PASS")), ("WARN", n("WARN")), ("FAIL", n("FAIL")),
        ("Literal tie-offs", len(tieoffs)), ("Suspect literals", sum(t["status"] == "SUSPECT" for t in tieoffs)),
        ("Not propagated", sum(p["status"] == "NOT_PROPAGATED" for p in propag))]))
    h.append("<h2>1. Top-level parameters vs Spec / SoC / DV</h2><table><tr><th>Param</th><th>RTL default</th>"
             "<th>Spec default</th><th>Spec allowed</th><th>Spec ref</th><th>SoC values (context)</th>"
             "<th>DV verified values (configs)</th><th>Issues</th><th>Status</th></tr>")
    for r in rows:
        s = r["spec"] or {}
        socs = "<br>".join("%s <small>(%s)</small>" % (e(v), e(c)) for v, c in r["soc"]) or "<i>no SoC data</i>"
        dvs = "<br>".join("%s <small>(%s)</small>" % (e(v), e(", ".join(sorted(c))[:120])) for v, c in sorted(r["dv"].items())) \
            or "<i>none (RTL default %s only)</i>" % e(r["default"])
        h.append("<tr><td><b>%s</b> %s<br><small>%s:%s</small></td><td><code>%s</code></td><td>%s</td><td>%s</td>"
                 "<td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (
                     e(r["name"]), e(r["range"]), e(os.path.basename(r["file"])), r["line"], e(r["default"]),
                     e(s.get("spec_default", "-")), e(s.get("spec_allowed", "-")), e(s.get("spec_ref", "-")),
                     socs, dvs, "<br>".join(e(i) for i in r["issues"]) or "-", badge(r["status"])))
    h.append("</table><h2>2. Hardcoded literals (tie-offs, constant assigns, literal mux legs)</h2>"
             "<p>SUSPECT = a DEFAULT/RESET/INIT-style parameter exists in scope but a literal is used instead &mdash; "
             "the parameter value will not reach this point.</p><table><tr><th>Module</th><th>Instance &rarr; child</th>"
             "<th>Port / target</th><th>Literal</th><th>Location</th><th>Note</th><th>Status</th></tr>")
    for t in sorted(tieoffs, key=lambda x: x["status"] != "SUSPECT"):
        h.append("<tr><td>%s</td><td>%s &rarr; %s</td><td>%s</td><td><code>%s</code></td><td>%s:%s</td><td>%s</td><td>%s</td></tr>" % (
            e(t["module"]), e(t["inst"]), e(t["child"]), e(t["port"]), e(t["value"]),
            e(os.path.basename(t["file"])), t["line"], e(t["note"]), badge(t["status"])))
    h.append("</table><h2>3. Parameter propagation through hierarchy</h2><table><tr><th>Parent</th><th>Instance</th>"
             "<th>Child</th><th>Child param</th><th>Value passed</th><th>Location</th><th>Status</th></tr>")
    for p in sorted(propag, key=lambda x: x["status"] != "NOT_PROPAGATED"):
        h.append("<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td><code>%s</code></td><td>%s:%s</td><td>%s</td></tr>" % (
            e(p["parent"]), e(p["inst"]), e(p["child"]), e(p["param"]), e(p["value"]),
            e(os.path.basename(p["file"])), p["line"], badge(p["status"])))
    h.append("</table><h2>4. All module parameters</h2><table><tr><th>Module</th><th>Param</th><th>Kind</th>"
             "<th>Default</th><th>Location</th></tr>")
    for mn, m in sorted(mods.items()):
        for pn, p in m["params"].items():
            h.append("<tr><td>%s</td><td>%s %s</td><td>%s</td><td><code>%s</code></td><td>%s:%s</td></tr>" % (
                e(mn), e(pn), e(p["range"]), e(p["kind"]), e(p["default"]), e(os.path.basename(p["file"])), p["line"]))
    h.append("</table><h2>Legend</h2><ul>"
             "<li><b>SPEC_DEFAULT_MISMATCH</b>: RTL default differs from spec default.</li>"
             "<li><b>SOC_OUT_OF_RANGE</b>: SoC override outside spec-allowed values.</li>"
             "<li><b>DV_GAP_SOC_VALUE</b>: SoC uses a value DV never ran.</li>"
             "<li><b>DV_SINGLE_VALUE / DV_DEFAULT_ONLY</b>: DV exercised one value / only the RTL default.</li>"
             "<li><b>NOT_PROPAGATED</b>: parent has a same-named param but does not pass it to the child.</li>"
             "<li><b>HARDCODED_LITERAL_BYPASS</b>: a literal is used where this parameter should drive the value.</li>"
             "<li><b>NOT_IN_SPEC</b>: parameter not described in the spec.</li></ul></body></html>")
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    open(a.out, "w").write("\n".join(h))


if __name__ == "__main__":
    main()
