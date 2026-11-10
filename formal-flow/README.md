# formal-flow — Spec-Driven Formal Skill Orchestrator

- Runs the formal skills in a fixed order from one spec, with user input on the terminal between stages.
- Each stage launches one `chipagents batch` agent that loads the stage skill file.
- Python 3.6+, standard library only; no network calls from the script.

## Files

- `formal_flow.py` — orchestrator (CLI, question collection, launch, gates, resume).
- `flow.json` — stage order, skill file, run condition, task text, expected outputs. Add or reorder skills here.

## Stage Order (flow.json)

| # | Stage id | Skill | Runs when |
|---|----------|-------|-----------|
| 0 | `spec_ingest` | installed `doc-convert` | spec is a PDF |
| 1 | `methodology` | `formal-methodology-select/SKILL.md` | always; then the approval gate |
| 2 | `connectivity` | `formal-connectivity/SKILL.md` | report has D-CONN |
| 3 | `csr` | `formal-csr/SKILL.md` | report has D-CSR |
| 4 | `fpv` | `formal-fpv/SKILL.md` | report has D-FPV1/2/3 |
| 5 | `xprop` | `formal-xprop/instructions.md` | report has D-XPROP |
| 6 | `manual_apps` | none (listed only) | report has D-SEC/CDC/FSV/LPV/SPV/UNR/SLINT |
| 7 | `cex_debug` | `formal-cex-debug/SKILL.md` | user answers yes (CEX present) |
| 8 | `traceability` | `formal-traceability/SKILL.md` | always |
| 9 | `vplan` | `formal-vplan/SKILL.md` | user answers NOW |
| 10 | `param_audit` | `param-spec-audit/SKILL.md` | always (last) |

## Usage

```tcsh
python3 /proj/adip_digital/rgulghan/workareas/wrk_rgulghan/Handoff/skills/formal-flow/formal_flow.py --spec <spec.pdf> --ip <ip> --workdir <formal_dir>
python3 .../formal_flow.py --workdir <formal_dir> --resume
python3 .../formal_flow.py --workdir <formal_dir> --from fpv
python3 .../formal_flow.py --workdir <formal_dir> --only csr
python3 .../formal_flow.py --spec <spec.pdf> --ip <ip> --workdir <formal_dir> --dry-run
```

- Options: `--thinking <level>` (default high), `--skip-permissions` (passed to `chipagents batch`; trusted hosts only), `--chipagents <exe>`.

## How a Stage Runs

- Reads the skill's `## Upfront Questions` table (`| Qn | question | options | ... |`) and asks each question on the terminal.
  - Defaults: the previous answer for that stage, else the same question text answered in an earlier stage (asked once, reused).
  - `unknown` → the skill marks the dependent output TODO / spec gap.
- Writes the prompt to `<workdir>/formal_flow/prompts/<stage>_<timestamp>.txt` and runs `chipagents batch --prompt-file ... --working-directory <workdir> --output ... --stats-file ... --allow-edits "**/*"`.
- Reads `STAGE_STATUS: DONE | NEEDS_INPUT | BLOCKED <reason>` from the agent output.
  - NEEDS_INPUT → shows `<workdir>/formal_flow/outputs/<stage>_questions.md`, takes your answer, reruns the stage with it.
  - Then asks: continue / rerun / skip / quit.
- Methodology approval gate: shows the D-* outcomes found in `*_formal_methodology.md`; approve / edit / rerun / quit.
  - approve → `Status: DRAFT` is set to `Status: APPROVED by <user> on <date>`; the outcomes select the later stages.

## State and Logs

- `<workdir>/formal_flow/flow_state.json` — stage status, runs, commands, outputs.
- `<workdir>/formal_flow/flow_answers.json` — all answers (reused on rerun / resume).
- `<workdir>/formal_flow/logs/<stage>_<timestamp>.log` — `chipagents batch` stdout/stderr.

## Limits

- Not run end to end on an IP yet; only `--dry-run` was tested.
- `chipagents batch` exit-code meaning is not documented; the script uses `STAGE_STATUS` first, the exit code second.
- Batch agents cannot ask questions mid-run; they stop with NEEDS_INPUT and the stage is rerun with your answers.
- `cex_debug` runs once after the app stages; CEX found later needs `--only cex_debug`.
