# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "py-jama-rest-client",
#     "requests",
#     "beautifulsoup4",
# ]
# ///
"""Template: import atomic requirements into Jama as folder-per-section.

Copy to .tmp/import_reqs_<timestamp>.py, fill the CONSTANTS and SECTIONS,
then run:
    uv run .tmp/import_reqs_<ts>.py --dry-run   (validate + audit, no Jama)
    uv run .tmp/import_reqs_<ts>.py             (resolve keys + import)
Credentials are read by the jama-editor client from its own config; this
script never reads or prints them.
"""
import argparse
import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

JAMA_EDITOR_SCRIPTS = Path(os.environ.get(
    "JAMA_EDITOR_SCRIPTS",
    str(Path.home() / ".config/chipagents/auto/skills/jama-editor/scripts")))

PROJECT_ID = 0
PARENT_ID = 0
REQ_PREFIX = "XX-REQ"
ALL_DOC_KEYS = []
GENERIC_MAP = {}
SECTIONS = [
    ("Section Title",
     "<p>Brief section description.</p>",
     [
         ("XX-REQ-001: Function Title",
          "<p>The IP shall ...</p>",
          ["PROJ-SPEC-0001"]),
     ]),
]

INCLUSIVE = {"master": "initiator", "slave": "target",
             "whitelist": "allowlist", "blacklist": "blocklist"}
FORBIDDEN_HTML = [r"<code\b", r"<font\b", r"style\s*=", r"color\s*="]
COMPOSITE_PATTERNS = [
    (r"\band\s+shall\b", "'and shall' joins behaviours"),
    (r"\bshall\s+also\b", "'shall also'"),
    (r"\badditionally\b", "'additionally'"),
    (r"\bwithout\s+affecting\b", "behaviour + preservation"),
    (r"\b(auto-?clear|cleared)\b.*\b(assert|set)\b|\b(assert|set)\b.*\b(auto-?clear|cleared)\b",
     "trigger + clear in one item"),
    (r"<(ul|ol)\b", "list in body: check each item is not an independent behaviour"),
]


def strip_html(text):
    return re.sub(r"<[^>]+>", " ", text)


def validate_atomicity(sections):
    warnings = []
    for title, _desc, reqs in sections:
        for name, body, _keys in reqs:
            plain = strip_html(body).lower()
            n = len(re.findall(r"\bshall\b", plain))
            if n != 1:
                warnings.append((name, "found %d 'shall' (need exactly 1)" % n))
            for pat, why in COMPOSITE_PATTERNS:
                if re.search(pat, body, re.I):
                    warnings.append((name, why))
    return warnings


def audit(sections):
    findings = defaultdict(list)
    names = []
    for title, _desc, reqs in sections:
        for name, body, keys in reqs:
            names.append(name)
            m = re.match(r"^(.+?)-(\d{3}):\s*(.+)$", name)
            if not m or m.group(1) != REQ_PREFIX:
                findings["numbering"].append("%s: bad name format" % name)
            title_part = m.group(3) if m else name
            for impl in GENERIC_MAP:
                pat = r"\b%s\b" % re.escape(impl)
                if re.search(pat, title_part):
                    findings["title_identifier"].append("%s: '%s'" % (name, impl))
                if re.search(pat, strip_html(body)):
                    findings["genericization"].append("%s: '%s'" % (name, impl))
            text = (name + " " + strip_html(body)).lower()
            for bad, good in INCLUSIVE.items():
                if re.search(r"\b%s\b" % bad, text):
                    findings["inclusive"].append("%s: '%s' -> '%s'" % (name, bad, good))
            for pat in FORBIDDEN_HTML:
                if re.search(pat, body, re.I):
                    findings["forbidden_html"].append("%s: %s" % (name, pat))
            if not keys:
                findings["connection"].append("%s: no source keys" % name)
            if re.search(r"<strong>\s*Source:", body):
                findings["connection"].append("%s: footer must be 'Connection:'" % name)
    nums = []
    for n in names:
        m = re.match(r"^.+?-(\d{3}):", n)
        if m:
            nums.append(int(m.group(1)))
    if nums != list(range(1, len(nums) + 1)):
        findings["numbering"].append("not sequential 001..%03d: %s" % (len(nums), nums))
    groups = defaultdict(list)
    for n in names:
        groups[re.sub(r"^.+?-\d{3}:\s*", "", n).strip().lower()].append(n)
    for key, grp in groups.items():
        if len(grp) > 1:
            findings["duplicate"].append("%s: %s" % (key, ", ".join(grp)))
    return findings


def make_description(body_html, source_keys, key_to_id, jama_url):
    links = []
    for key in source_keys:
        if key in key_to_id:
            url = "%s/perspective.req#/items/%s?projectId=%s" % (
                jama_url, key_to_id[key], PROJECT_ID)
            links.append('<a href="%s">%s</a>' % (url, key))
        else:
            links.append(key)
    return (body_html + "<br><br>"
            + "<p><strong>Connection:</strong> %s</p>" % ", ".join(links))


def resolve_keys(keys, session, jama_url, token):
    key_to_id, missing = {}, []
    for key in sorted(set(keys)):
        resp = session.get(
            "%s/rest/v1/abstractitems" % jama_url,
            headers={"Authorization": "Bearer %s" % token},
            params={"documentKey": key, "project": PROJECT_ID})
        resp.raise_for_status()
        data = resp.json().get("data", [])
        if data:
            key_to_id[key] = data[0]["id"]
        else:
            missing.append(key)
            print("WARNING: %s not found in project %s" % (key, PROJECT_ID))
    return key_to_id, missing


def report(warnings, findings):
    print("== Atomicity warnings: %d" % len(warnings))
    for name, why in warnings:
        print("  ATOM  %s: %s" % (name, why))
    total = 0
    for cat in ["numbering", "duplicate", "title_identifier", "genericization",
                "inclusive", "forbidden_html", "connection"]:
        items = findings.get(cat, [])
        total += len(items)
        print("== %s: %d" % (cat, len(items)))
        for i in items:
            print("  %s" % i)
    return total


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true",
                    help="validate and audit only; no Jama access")
    ap.add_argument("--accept-warnings", action="store_true",
                    help="import although atomicity warnings remain (reviewed)")
    ap.add_argument("--out", default="spec2req_import_result.json")
    args = ap.parse_args()
    all_keys = set(ALL_DOC_KEYS)
    for _t, _d, reqs in SECTIONS:
        for _n, _b, keys in reqs:
            all_keys.update(keys)
    warnings = validate_atomicity(SECTIONS)
    findings = audit(SECTIONS)
    n_find = report(warnings, findings)
    n_reqs = sum(len(r) for _t, _d, r in SECTIONS)
    print("== Sections: %d, requirements: %d, unique keys: %d"
          % (len(SECTIONS), n_reqs, len(all_keys)))
    if args.dry_run:
        return 0 if n_find == 0 else 1
    if n_find:
        print("ABORT: fix audit findings before import")
        return 1
    if warnings and not args.accept_warnings:
        print("ABORT: review atomicity warnings, then re-run with --accept-warnings")
        return 1
    if not PROJECT_ID or not PARENT_ID:
        print("ABORT: set PROJECT_ID and PARENT_ID")
        return 1
    sys.path.insert(0, str(JAMA_EDITOR_SCRIPTS))
    from client import (set_project_id, create_folder, create_requirement,
                        _get_auth_token)
    from setup_jama import get_jama_url
    from jama_utils import get_session
    set_project_id(PROJECT_ID)
    jama_url = get_jama_url().rstrip("/")
    key_to_id, missing = resolve_keys(all_keys, get_session(), jama_url,
                                      _get_auth_token())
    print("== Keys resolved: %d/%d" % (len(key_to_id), len(all_keys)))
    result = {"project_id": PROJECT_ID, "parent_id": PARENT_ID,
              "missing_keys": missing, "sections": []}
    for title, desc, reqs in SECTIONS:
        fid = create_folder(PARENT_ID, title, desc)
        sec = {"title": title, "folder_id": fid, "requirements": []}
        print("FOLDER %s  %s" % (fid, title))
        for name, body, keys in reqs:
            rid = create_requirement(
                fid, name, make_description(body, keys, key_to_id, jama_url))
            sec["requirements"].append({"name": name, "id": rid, "keys": keys})
            print("  REQ %s  %s" % (rid, name))
        result["sections"].append(sec)
    with open(args.out, "w") as fh:
        json.dump(result, fh, indent=2)
    print("== Summary")
    print("| Section | Folder ID | Reqs |")
    print("|---------|-----------|------|")
    for s in result["sections"]:
        print("| %s | %s | %d |" % (s["title"], s["folder_id"], len(s["requirements"])))
    print("Result written to %s" % args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
