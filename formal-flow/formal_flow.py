#!/usr/bin/env python3
"""Spec-driven formal flow orchestrator.

Runs the formal skills in a fixed order (flow.json), starting with
formal-methodology-select, asks the upfront questions of each skill on the
terminal, launches each skill with `chipagents batch`, and keeps a resumable
state file. Python 3.6 compatible, standard library only.
"""
import argparse
import datetime
import getpass
import glob
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SKILLS_ROOT = os.path.dirname(HERE)
STATUS_RE = re.compile(r"STAGE_STATUS:\s*(DONE|NEEDS_INPUT|BLOCKED)(.*)")
QROW_RE = re.compile(r"^\|\s*(Q\d+[a-z]?)\s*\|(.*)\|\s*$")
OUTCOMES = ["D-CONN", "D-CSR", "D-FPV1", "D-FPV2", "D-FPV3", "D-XPROP",
            "D-SEC", "D-UNR", "D-CDC", "D-FSV", "D-LPV", "D-SPV", "D-SLINT",
            "D-SIM", "D-OOS"]
MANUAL = ["D-SEC", "D-CDC", "D-FSV", "D-LPV", "D-SPV", "D-UNR", "D-SLINT"]


def now():
    return datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")


def ask(prompt, default=None, choices=None):
    hint = ""
    if choices:
        hint = " [" + "/".join(choices) + "]"
    if default:
        hint += " (default: %s)" % default
    while True:
        try:
            ans = input("%s%s: " % (prompt, hint)).strip()
        except EOFError:
            sys.exit("\nInput closed; state saved. Re-run with --resume.")
        if not ans and default is not None:
            ans = default
        if choices and ans.lower() not in [c.lower() for c in choices]:
            print("  choose one of: " + ", ".join(choices))
            continue
        if ans:
            return ans


def norm(text):
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def parse_questions(skill_md):
    """Return [(qid, question, options)] from the Upfront Questions table."""
    rows, in_sec = [], False
    with open(skill_md) as fh:
        for line in fh:
            if line.startswith("## "):
                in_sec = "upfront questions" in line.lower()
                continue
            if not in_sec:
                continue
            m = QROW_RE.match(line.rstrip("\n"))
            if m:
                cells = [c.strip() for c in m.group(2).split("|")]
                question = cells[0] if cells else ""
                options = cells[1] if len(cells) > 1 else ""
                rows.append((m.group(1), question, options))
    return rows


class Flow(object):
    def __init__(self, args):
        self.args = args
        self.workdir = os.path.abspath(args.workdir)
        self.fdir = os.path.join(self.workdir, "formal_flow")
        for sub in ("prompts", "logs", "outputs"):
            os.makedirs(os.path.join(self.fdir, sub), exist_ok=True)
        self.state_file = os.path.join(self.fdir, "flow_state.json")
        self.answers_file = os.path.join(self.fdir, "flow_answers.json")
        with open(os.path.join(HERE, "flow.json")) as fh:
            self.cfg = json.load(fh)
        self.state = self._load(self.state_file, {"stages": {}, "meta": {}})
        self.answers = self._load(self.answers_file, {"by_text": {}, "by_stage": {}})
        meta = self.state["meta"]
        if args.spec:
            meta["spec"] = os.path.abspath(args.spec)
        if args.ip:
            meta["ip"] = args.ip
        if not meta.get("spec") or not meta.get("ip"):
            sys.exit("--spec and --ip are required for a new flow.")
        if not os.path.isfile(meta["spec"]):
            sys.exit("Spec not found: " + meta["spec"])
        self.save()

    @staticmethod
    def _load(path, default):
        if os.path.isfile(path):
            with open(path) as fh:
                return json.load(fh)
        return default

    def save(self):
        with open(self.state_file, "w") as fh:
            json.dump(self.state, fh, indent=2)
        with open(self.answers_file, "w") as fh:
            json.dump(self.answers, fh, indent=2)

    def stage_state(self, sid):
        return self.state["stages"].setdefault(sid, {"status": "pending", "runs": []})

    def outcomes(self):
        return set(self.state["meta"].get("outcomes", []))

    def spec_md(self):
        found = sorted(glob.glob(os.path.join(self.workdir, "spec", "*.md")))
        return found[0] if found else None

    def should_run(self, stage):
        cond, outs = stage["when"], self.outcomes()
        if cond == "always":
            return True
        if cond == "spec_is_pdf":
            return self.state["meta"]["spec"].lower().endswith(".pdf")
        if cond == "D-FPV":
            return bool(outs & {"D-FPV1", "D-FPV2", "D-FPV3"})
        if cond == "MANUAL":
            return bool(outs & set(MANUAL))
        if cond == "ask_cex":
            return ask("Did any run produce a failing property (CEX) to debug?",
                       "no", ["yes", "no"]).lower() == "yes"
        if cond == "ask_vplan":
            prev = self.state["meta"].get("vplan_timing")
            ans = ask("Create the vPlan now?", prev or "LATER",
                      ["NOW", "LATER", "NOT_NEEDED"]).upper()
            self.state["meta"]["vplan_timing"] = ans
            self.save()
            return ans == "NOW"
        return cond in outs

    def collect_answers(self, stage):
        skill = stage.get("skill")
        if not skill:
            return []
        qs = parse_questions(os.path.join(SKILLS_ROOT, skill))
        if not qs:
            return []
        stored = self.answers["by_stage"].setdefault(stage["id"], {})
        print("\n--- %s: upfront questions (%d) ---" % (stage["title"], len(qs)))
        print("    Enter = default; 'unknown' = mark TODO in the skill outputs.")
        result = []
        for qid, question, options in qs:
            key = norm(question)
            default = stored.get(qid) or self.answers["by_text"].get(key)
            if not default and "spec" in key and "source" in key:
                default = self.state["meta"]["spec"]
            label = "%s %s" % (qid, question)
            if options:
                label += "\n      options: " + options
            ans = ask("  " + label, default or "unknown")
            stored[qid] = ans
            self.answers["by_text"][key] = ans
            result.append((qid, question, ans))
            self.save()
        return result

    def build_prompt(self, stage, qa, extra):
        meta = self.state["meta"]
        lines = [self.cfg["rules_line"], ""]
        if stage.get("skill"):
            path = os.path.join(SKILLS_ROOT, stage["skill"])
            lines.append("- Load and follow the skill file %s and every file it references under its resources/ directory." % path)
        else:
            lines.append("- Load the installed skill '%s' with the Skill tool and follow it." % stage["installed_skill"])
        lines += [
            "- IP name: %s" % meta["ip"],
            "- Spec (only requirements source): %s" % meta["spec"],
        ]
        md = self.spec_md()
        if md:
            lines.append("- Spec markdown: %s" % md)
        rep = meta.get("methodology_report")
        if rep:
            lines.append("- Approved methodology report: %s" % rep)
        lines += [
            "- Working directory for all outputs: %s" % self.workdir,
            "- Task: %s" % stage["task"].replace("<spec_stem>", os.path.splitext(os.path.basename(meta["spec"]))[0]),
            "- This is a non-interactive run. The upfront questions are already answered below; do not ask them again.",
            "- An answer 'unknown' means: continue and mark the dependent output TODO or a spec gap.",
            "- If you need any other user input, write the questions to %s and stop." % self.qfile(stage),
            "- End the final response with exactly one line: STAGE_STATUS: DONE, STAGE_STATUS: NEEDS_INPUT, or STAGE_STATUS: BLOCKED <reason>.",
        ]
        if qa:
            lines += ["", "Upfront answers:"]
            lines += ["- %s %s -> %s" % (q, t, a) for q, t, a in qa]
        if extra:
            lines += ["", "Answers to your follow-up questions (continue from the existing outputs):", extra]
        return "\n".join(lines) + "\n"

    def qfile(self, stage):
        return os.path.join(self.fdir, "outputs", stage["id"] + "_questions.md")

    def launch(self, stage, prompt):
        ts = now()
        pfile = os.path.join(self.fdir, "prompts", "%s_%s.txt" % (stage["id"], ts))
        ofile = os.path.join(self.fdir, "outputs", "%s_%s.txt" % (stage["id"], ts))
        sfile = os.path.join(self.fdir, "outputs", "%s_%s_stats.json" % (stage["id"], ts))
        lfile = os.path.join(self.fdir, "logs", "%s_%s.log" % (stage["id"], ts))
        with open(pfile, "w") as fh:
            fh.write(prompt)
        cmd = [self.args.chipagents, "batch", "--prompt-file", pfile,
               "--working-directory", self.workdir, "--output", ofile,
               "--stats-file", sfile, "--name", "%s_%s_%s" % (self.state["meta"]["ip"], stage["id"], ts),
               "--allow-edits", "**/*"]
        if self.args.thinking:
            cmd += ["--thinking", self.args.thinking]
        if self.args.skip_permissions:
            cmd.append("--skip-permissions")
        run = {"ts": ts, "prompt": pfile, "output": ofile, "log": lfile, "cmd": cmd}
        print("\n>>> %s\n    prompt: %s" % (stage["title"], pfile))
        if self.args.dry_run:
            print("    (dry run) " + " ".join(cmd))
            run["status"] = "DRY_RUN"
            return run
        with open(lfile, "w") as log:
            rc = subprocess.call(cmd, stdout=log, stderr=subprocess.STDOUT)
        run["rc"] = rc
        text = open(ofile).read() if os.path.isfile(ofile) else ""
        found = STATUS_RE.findall(text)
        run["status"] = found[-1][0] if found else ("BLOCKED" if rc else "UNKNOWN")
        run["reason"] = found[-1][1].strip() if found else ("exit code %d" % rc if rc else "")
        print("    rc=%d status=%s %s\n    output: %s" % (rc, run["status"], run["reason"], ofile))
        return run

    def check_outputs(self, stage):
        missing = []
        for pat in stage.get("outputs", []):
            if not glob.glob(os.path.join(self.workdir, pat), recursive=True):
                missing.append(pat)
        return missing

    def approval_gate(self, stage):
        reps = sorted(glob.glob(os.path.join(self.workdir, "**", "*_formal_methodology.md"), recursive=True))
        if not reps:
            print("  No *_formal_methodology.md found.")
            return "rerun"
        rep = reps[-1]
        text = open(rep).read()
        outs = sorted(o for o in OUTCOMES if re.search(re.escape(o) + r"\b", text))
        print("\n=== Methodology approval ===\n  report: %s\n  outcomes found: %s" % (rep, ", ".join(outs) or "none"))
        while True:
            ans = ask("  approve / edit (edit the report yourself, then reload) / rerun / quit",
                      None, ["approve", "edit", "rerun", "quit"]).lower()
            if ans == "edit":
                input("  Edit %s, then press Enter to reload..." % rep)
                text = open(rep).read()
                outs = sorted(o for o in OUTCOMES if re.search(re.escape(o) + r"\b", text))
                print("  outcomes found: %s" % (", ".join(outs) or "none"))
                continue
            if ans == "approve":
                stamp = "Status: APPROVED by %s on %s" % (getpass.getuser(), datetime.date.today())
                new = re.sub(r"Status:\s*DRAFT[^\n]*", stamp, text, count=1)
                if new != text:
                    with open(rep, "w") as fh:
                        fh.write(new)
                self.state["meta"]["methodology_report"] = rep
                self.state["meta"]["outcomes"] = outs
                self.save()
            return ans

    def run_stage(self, stage):
        st = self.stage_state(stage["id"])
        if stage["id"] == "manual_apps":
            manual = sorted(self.outcomes() & set(MANUAL))
            print("\n=== Manual apps selected (no skill yet): %s ===" % ", ".join(manual))
            print("  Plan these by hand from the methodology report.")
            st["status"] = "done"
            self.save()
            return True
        qa = self.collect_answers(stage)
        extra = ""
        while True:
            run = self.launch(stage, self.build_prompt(stage, qa, extra))
            st["runs"].append(run)
            self.save()
            if run["status"] == "DRY_RUN":
                st["status"] = "pending"
                self.save()
                return True
            if run["status"] == "NEEDS_INPUT":
                qf = self.qfile(stage)
                if os.path.isfile(qf):
                    print("\n--- questions from the skill (%s) ---\n%s" % (qf, open(qf).read()))
                extra = ask("  Your answers (one line; or 'quit')")
                if extra.lower() == "quit":
                    st["status"] = "needs_input"
                    self.save()
                    return False
                continue
            missing = self.check_outputs(stage)
            if missing:
                print("  missing expected outputs: " + ", ".join(missing))
            if stage.get("gate") == "approval" and run["status"] == "DONE" and not missing:
                g = self.approval_gate(stage)
                if g == "rerun":
                    extra = ask("  Changes requested (one line)")
                    continue
                if g == "quit":
                    st["status"] = "awaiting_approval"
                    self.save()
                    return False
                st["status"] = "done"
                self.save()
                return True
            ok = run["status"] == "DONE" and not missing
            ans = ask("  %s: continue / rerun / skip / quit" % stage["title"],
                      "continue" if ok else "rerun", ["continue", "rerun", "skip", "quit"]).lower()
            if ans == "rerun":
                extra = ask("  Notes for the rerun (one line, or '-')", "-")
                extra = "" if extra == "-" else extra
                continue
            st["status"] = {"continue": "done", "skip": "skipped", "quit": "failed"}[ans]
            if ans == "continue" and not ok:
                st["status"] = "done_with_issues"
            self.save()
            return ans != "quit"

    def main(self):
        stages = self.cfg["stages"]
        ids = [s["id"] for s in stages]
        for opt in (self.args.from_stage, self.args.only):
            if opt and opt not in ids:
                sys.exit("Unknown stage %s; stages: %s" % (opt, ", ".join(ids)))
        start = ids.index(self.args.from_stage) if self.args.from_stage else 0
        for i, stage in enumerate(stages):
            if self.args.only and stage["id"] != self.args.only:
                continue
            st = self.stage_state(stage["id"])
            if i < start or (self.args.resume and st["status"] in ("done", "done_with_issues", "skipped")):
                continue
            if stage["id"] != "methodology" and stage["id"] != "spec_ingest" and not self.state["meta"].get("methodology_report"):
                if not self.args.dry_run:
                    sys.exit("Methodology report not approved yet; run the methodology stage first.")
            if not self.should_run(stage):
                st["status"] = "not_selected"
                self.save()
                print("\n--- %s: not selected" % stage["title"])
                continue
            if not self.run_stage(stage):
                print("\nStopped at %s. Re-run with --resume to continue." % stage["id"])
                return 1
        print("\nFlow complete. State: %s" % self.state_file)
        for s in stages:
            print("  %-14s %s" % (s["id"], self.stage_state(s["id"])["status"]))
        return 0


def parse_args():
    p = argparse.ArgumentParser(description="Spec-driven formal skill orchestrator")
    p.add_argument("--spec", help="IP spec (PDF or md)")
    p.add_argument("--ip", help="IP name")
    p.add_argument("--workdir", required=True, help="Formal output directory (all skill outputs)")
    p.add_argument("--resume", action="store_true", help="Skip stages already done")
    p.add_argument("--from", dest="from_stage", help="Start at this stage id")
    p.add_argument("--only", help="Run only this stage id")
    p.add_argument("--thinking", default="high", help="chipagents batch --thinking level")
    p.add_argument("--skip-permissions", action="store_true", help="Pass --skip-permissions to chipagents batch")
    p.add_argument("--dry-run", action="store_true", help="Write prompts and print commands; do not launch")
    p.add_argument("--chipagents", default="chipagents", help="chipagents executable")
    return p.parse_args()


if __name__ == "__main__":
    sys.exit(Flow(parse_args()).main())
