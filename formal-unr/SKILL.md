---
name: formal-unr
description: Jasper Coverage Unreachability (UNR) App flow (JasperGold 2025.09) — prove simulation code-coverage holes (block, expression, toggle, FSM, functional) unreachable with check_unr, under spec-justified constraints only; generate the UNR input TCL (xrun -unr -jg) or the adsim sim.setup UNR_* block with run commands, review UNR/RCH/BND results, merge with the sim coverage DB in IMC, exclude reviewed items with comments and save a .vRefine refinement. Use when the user asks for UNR / unreachability analysis, coverage-hole closure with formal, check_unr setup, adsim -unr, or IMC UNR exclusion / refinement.
---

# Formal UNR Skill — Jasper Coverage Unreachability App

**Resource loading (MANDATORY):**
- `resources/...` paths are relative to this skill's directory (the directory containing this SKILL.md).
- Resources are NOT preloaded. At each step that says "Read `resources/<file>`", open that file with View BEFORE writing any output for the step.
- Never generate a UNR TCL, sim.setup block, IMC exclude script or review CSV from memory when a resource file exists for it.

| Step | Resource file (read when reaching the step) |
|------|---------------------------------------------|
| Any command / option question; doc IDs D1–D9 | `resources/doc_reference.md` |
| Step 0 — lab-kit background, kit-vs-doc corrections K1–K17 | `resources/kit_reference.md` |
| Step 4a — input TCL, pre TCL, black-box list, xrun RUNCMD | `resources/unr_tcl_template.md` |
| Step 4b — adsim `sim.setup` UNR block + RUNCMD | `resources/sim_setup_template.md` |
| Steps 6–8 — result categories, IMC merge, review, exclusion, refinement, reports | `resources/imc_merge_review.md` |

## When to Use
- Activate when the user asks to:
  - Prove simulation coverage holes unreachable and exclude them (coverage closure)
  - Set up `check_unr` / `xrun -unr -jg` / `adsim -unr`
  - Write `UNR_FML_*` sim.setup variables or a UNR input TCL
  - Merge a UNR database with simulation coverage in IMC, exclude UNR items, save a `.vRefine`
  - Debug UNR runs (bounded / unprocessed items, discarded items, wrong instance top, coverage-option mismatch)

## Purpose and Nature of UNR
- UNR reads the UNCOVERED items of an Xcelium simulation coverage DB, turns each into a formal cover target and proves it reachable or unreachable (D1 Ch. 1–2).
- Unreachable items, after review, are converted to Exclude in IMC; UNR alone does not change the coverage score (D1 "Converting Unreachable to Excluded").
- UNR is inherently RTL-structural: the targets are RTL code-coverage items and the analysis target is the RTL. This is not circular as long as:
  - constraints (mode tie-offs, configuration pins, reset choice) come from the SPEC, never from reading the RTL;
  - the exclusion verdict (dead code vs. missing behaviour) is checked against the SPEC.

## Rules (MANDATORY)
- R1 Unreachability results are valid ONLY under the stated constraints, reset/initial state, `-inst_top`, black boxes and coverage options of that run; record all of them in the run summary and in `unr_review.csv`.
- R2 Every constraint (`assume`, `stopat`, tie-off, reset choice) and every black box needs a written reason; constraints need a spec section.
- R3 Do NOT use the RTL to invent constraints. Scan / test / DFT / mode tie-offs only from the spec (or user-approved spec gap entry).
- R4 RTL is the analysis target; it may be read during review only to understand an item, not to justify an exclusion.
- R5 Never exclude without per-item review; never use a blanket `exclude ... -unr`; never exclude at a partially-unreachable (orange) level (D1).
- R6 Sim and UNR must use the same RTL, defines, parameters and coverage configuration (`-covfile`) (D1 Assumptions and Recommendations).
- R7 No `check_cov` / Coverage App in a UNR session (D3: Coverage App runs with all apps except UNR).
- R8 Use the installed Jasper 2025.09 docs (`/cad/adi/apps/cadence/jasper/2025.09-p002/doc`); the lab kit uses jg 2021.12 and legacy IEV commands — do not copy them (`kit_reference.md` K1–K17).
- R9 Anything not confirmable in the docs is written as `UNCONFIRMED — verify in <doc>`; do not invent adsim variables or switches.

## Upfront Questions (ASK ONCE, BEFORE ANY WORK — MANDATORY)

- Ask ALL of these in ONE question round (AskUserQuestions) before Step 1.
- Do not re-ask later; reuse the answers in every step. Record them in the final summary.
- If an answer is "not known yet", continue and mark the dependent output as TODO.

| # | Question | Options / format | Used in |
|---|----------|------------------|---------|
| Q1 | IP / block name; adsim block name | `<ip>`, `adip_<ip>` | all, RUNCMD `-block` |
| Q2 | Spec source (+ revision) | PDF / Jama / md | constraints, review |
| Q3 | RTL filelist and compile options of the SIM run | `filelist.f`, `+define+...`, `-incdir` | Step 2, RUNCMD |
| Q4 | Simulation coverage DB | existing merged test dir `<covwork>/<covscope>/<covtest>` / run sim first (test list) | Step 2 |
| Q5 | Coverage config files (ccf) used in sim | list of `-covfile` paths, in order | Step 2, 4 |
| Q6 | Coverage types for UNR | `b` `e` `t` `f` (fsm) `u`/functional / all | `-jg_coverage`, `UNR_FML_COVERAGE` |
| Q7 | Parameters / configurations | `<cfg>`: `<PARAM>=<VAL>` (one UNR run per sim config) | Step 3 |
| Q8 | Instance top (sim TB hierarchy → formal top) | `<tb_top>.<inst>` (must be in the covdb, D1 `-inst_top`) | `-inst_top`, `UNR_FML_INSTTOP` |
| Q9 | TB constants on DUT ports | list + spec reason, or "none" (D1: preserved as constants) | Step 3, review C3 |
| Q10 | Clocks (from spec) | names, edges, relation (single / multiple async) | `clock` |
| Q11 | Resets (from spec) | names, polarity | `reset` |
| Q12 | Initial state choice | R1 spec reset / R2 un-initialised (UG default) / R3 `reset -shm` from sim waveform | `reset` |
| Q13 | Black-box list | module names + reason (sim-only model, analog, memory) / none | `-jg_bbmodlist`, `UNR_FML_BBLIST` |
| Q14 | Constraints from spec | scan_en / test_mode / DFT / static config tie-offs, each with spec section / none | `assume`, `stopat` |
| Q15 | Embedded SVA assumes / functional coverage | enable / not | pre TCL |
| Q16 | Effort / ProofGrid | time limit (default 24 h, D1), bsub command, partitioning yes/no | prove settings |
| Q17 | Run flow and mode | A. xrun TCL / B. adsim sim.setup / C. both; GUI / batch | Step 4, 5 |
| Q18 | Results / UNR directory | e.g. `$ADIP_BLOCKS_ROOT/<ip>/dv/formal/<formal_dir>/unr` | all outputs |
| Q19 | Writable covdb location | sim covdb writable? else `-covworkdir` path | RUNCMD |
| Q20 | IMC outputs | exclusion script / `.vRefine` / HTML report / all | Step 8 |
| Q21 | Installed versions | Jasper (default 2025.09-p002), Xcelium, IMC/mdv, adsim modules | Step 1 |
| Q22 | vManager / vPlan | vPlan NOW / LATER / NOT NEEDED | Optional vPlan step |
| Q23 | Traceability / sign-off matrix for exclusions | yes (`formal-traceability`) / no | Sign-off step |

- Only review-time questions are asked later (an item whose spec intent is unclear → ASK-USER in `unr_review.csv`).

## Prerequisites (check in Step 2; stop and report if missing)
- P1 Xcelium simulation coverage DB exists (D1: "simulation coverage must already be generated"); merged DBs built with identical coverage options (D1).
- P2 Coverage config (ccf) of the UNR compile = sim ccf (same files, same order); glitch settings per D1 (`set_toggle_strobe 1fs` or `set_toggle_scoring -regeot`, plus `set_glitch_strobe`) — changing them requires a new sim.
- P3 Same RTL revision, defines and parameters as the sim that produced the DB (D1: DB assumed from the same DUT).
- P4 `-inst_top` path exists in the sim TB hierarchy and is coverage-enabled; if the coverage top is not found use `-dutinst` (D1).
- P5 Jasper/Xcelium compatibility (D1 Xcelium Version Dependency); 64-bit Jasper with 64-bit Xcelium (`-64bit`, D2 App. K).
- P6 Write permission for the UNR covtest dir (default `<covwork>/<covscope>/unr`, D1) or `-covworkdir`.

## Step-by-Step Procedure

### Step 0: Background (optional)
- Read `resources/kit_reference.md` if the user refers to the ADI lab kit or an existing `jg_unr.tcl` / `UNR_*` block; apply corrections K1–K17 to existing collateral.

### Step 1: Environment
- Load the installed tools (Q21); do NOT use the kit pins (`jg/adi/2021.12-p001`, K5).
- Record `jg -version` / `xrun -version` / `imc -version` outputs in the run summary.
- tcsh: `module load <jg module> <xlm module> <mdv module> <adsim module>` — module names are site-specific (UNCONFIRMED — verify with `module avail`).

### Step 2: Coverage Database
- Existing DB (Q4): verify the test dir `<covwork>/<covscope>/<covtest>` (D1 `-covdb`; only `<covtest>` may be given, `<covwork>`/`<scope>` optional).
- No DB: run the sim regression with coverage first (kit: `adsim -block <ip_block> -regr <test.list> -cov -cov_merge -clean -batch -no_vmgr -rp S`; merged DB under `.../coverage/cov_work/scope/merged_data`).
- Open the DB in IMC once (`imc -load <test_dir>`, D6 RUNME) and record covered / total per metric for `<tb_top>.<inst>` (baseline).
- Check P2/P3: list the ccf files of the sim compile; compare with Q5.

### Step 3: Constraint and Black-Box Plan (spec-only)
- Build a table `<results>/unr_constraints.md` (bullets): each `assume` / `stopat` / tie-off / reset choice / black box, with spec section, reason, and the configs it applies to.
- Sources: spec mode tables (functional vs scan/test), spec-fixed configuration pins, spec clock/reset section.
- TB constants on `-inst_top` ports are preserved by UNR (D1) → list them (Q9); each one is a constraint (review class C3).
- Black boxes (Q13): sim-only / analog / memory models; their outputs become free (over-approximation) and their items are not analysed.
- Over-constraint risk: prefer fewer constraints; a UNR found only because of a constraint is valid only where the constraint holds in every integration.

### Step 4: Choose Run Flow (ASK THE USER — MANDATORY)
- Use answer Q17 (ask now only if missing). Do NOT pick a default silently.

| Option | Output | Run command |
|--------|--------|-------------|
| **A. xrun TCL** | `jg_unr.tcl`, optional `jg_unr_pre.tcl`, `unr.bblist`, `<cfg_dir>/RUNCMD_xrun` | Step 4a |
| **B. adsim sim.setup** | `UNR_*` block in the block `sim.setup`, `jg_unr.tcl`, `unr.bblist`, `<cfg_dir>/RUNCMD` | Step 4b |
| **C. Both** | both, kept consistent (same TCL / bblist) | — |

### Step 4a: UNR TCL + xrun (flow A or C)
- Read `resources/unr_tcl_template.md` when doing this step.
- Input TCL order (D1/D2): [`database -init_unicov -app unr -interval <t>`] → `clock` → `reset` → `stopat -env` (BEFORE setup) → `assume` → `check_unr -setup` → prove settings → `check_unr -prove` → `check_unr -list -type unreachable|bounded|unprocessed` → `check_unr -reason -file` → `report -summary -task unr` → `database -export_unicov`.
- Coverage types are selected with xrun `-jg_coverage` (or `check_unr -init -coverage`, before elaborate) — never `check_unr -setup -coverage` (K1).
- Signal paths drop the TB top-module name (D1).
- "Coverage waivers: ADD WAIVERS HERE" placeholder stays in the TCL; already-reviewed refinements are passed with `-load_refinement` (D1).

**xrun run command (MANDATORY — generate per config):**
- Write it to `<cfg_dir>/RUNCMD_xrun` and print it to the user.
```
xrun -64bit -jg -unr -R -covdb <abs_covdb> -inst_top <tb_top>.<inst> \
     -input <abs_unr_dir>/jg_unr.tcl -covfile <abs_ccf> -jg_coverage <b:e:t> \
     -jg_bbmodlist <abs_unr_dir>/unr.bblist -covtest unr_<cfg> -covoverwrite \
     -jg_project <abs_unr_dir>/<cfg>/jgproject [-gui]
```
- Full switch list, recompile notes and the `jg -unr` alternative (UNCONFIRMED): `resources/unr_tcl_template.md` File 4.

### Step 4b: Adsim sim.setup (flow B or C)
- Read `resources/sim_setup_template.md` when doing this step.
- Add the `UNR_*` block to the block's sim.setup (reuse sim compile settings, R6).
- Pass ALL sim ccf files through `UNR_EXTRA_COMPILE_OPTIONS : -covfile ...` (K6).
- `UNR_FML_TCL_FILE` points to the same `jg_unr.tcl` as flow A.
- Mapping `UNR_FML_*` → xrun switches is UNCONFIRMED (not in D8); verify in the first run log and close the TODO table in the template.

**sim.setup run command (MANDATORY — generate per config):**
- Write it to `<cfg_dir>/RUNCMD` and print it to the user.
```
adsim -block <ip_block> -unr -clean [-gui] [-resdir <abs_cfg_dir>/Result_] [-force_setup <abs_cfg_dir>/sim.setup]
```

### Step 5: Run and Sanity-Check the Setup
- Run RUNCMD (GUI or batch per Q17).
- Check in `jg.log` / xrun log before trusting any result:
  - `-inst_top` found; number of extracted UNR targets ≈ number of holes in the baseline (D6: 889 holes → targets).
  - `discarded_items_report.txt` (session dir) reviewed (D2 `-setup`).
  - Resilient Compilation Summary: no unexpected black-boxed module / ignored statement (D1).
  - Coverage-option warnings (D1: UNR warns about missing glitch settings).
  - Clock-loop messages WCK111 / ECK113 / ECK114 (auto-stopat, D1) noted.
  - Constraints listed in the `unr` task (`report -summary -task unr`).

### Step 6: Review Jasper Results
- Read `resources/imc_merge_review.md` §1 when doing this step.
- Categories (D2 `check_unr -list`): `UNR` unreachable, `RCH` reachable, `BND` bounded (undetermined), `UNP` unprocessed, `DSB` disabled.
- Save counts per category and per coverage type in the run summary.
- `check_unr -reason -file <results>/unr_reason` → `unr_reason.txt` (cause per constant/assume-induced UNR) and `unr_reason.cmd` (D1 App. A).

### Step 7: IMC Merge and Per-Item Review
- Read `resources/imc_merge_review.md` §2–§4 when doing this step.
- Merge script: `<jgproject>/sessionLogs/session_<n>/unr_imc_coverage_merge.cmd` (D1/D6); read it before running; keep any blanket `exclude ... -unr` commented.
- GUI: `imc -nostdout -init <merge.cmd>`; batch: `imc -exec <script>` (D7).
- Fill `<results>/unr_review.csv` (one row per UNR item; classes C1–C5; spec reference; constraint dependency).
- Constraint-induced UNRs (C3): exclude only with a spec reason valid in every integration; otherwise report.
- Items the spec says must be reachable (C4): FINDING, not exclusion → `formal-cex-debug` / ask the user.

### Step 8: Exclusion, Refinement and Reports
- Read `resources/imc_merge_review.md` §5–§7 when doing this step.
- Per-item `exclude ... -unr -comment "<UNR_ID>: <reason> (spec §x.y)"` only for rows with Decision EXCLUDE; `save -refinement <results>/<ip>_<cfg>_unr.vRefine` (D7).
- Reports per Q20: `report_metrics -out <dir> -overwrite -detail ...` (D7); record coverage before/after.
- Hook the refinement into later merges: `COVERAGE_REFINE_FILE` (D8) / `load -refinement` (D7).

### Step 9: Undetermined (BND / UNP) Handling
- BND / UNP items stay coverage holes; they are never excluded.
- Escalation order (all D1/D2/D4 options):
  1. Longer `-time_limit` / `set_prove_time_limit` (default 24 h, D1).
  2. Chunking: `set_unr_prove_max_chunks` (default 6), `set_unr_prove_max_properties_per_chunk` (default 100000) or the `-prove` switches (App. B).
  3. ProofGrid: `set_proofgrid_mode shell`, `set_proofgrid_shell {<bsub>}`, `-persistent_grid_jobs`; ProofMaster is compatible with `check_unr -prove` (D4).
  4. Engines: `-engine_mode {<engines>}` (D4 for engine choice).
  5. Re-run only the open items: `check_unr -prove -property <list>` (D2); reuse `-save_ppd` / `-with_ppd`.
  6. Partitioning: `check_unr -generate_partition / -load_partition / -run_partition` or xrun `-jg_unr_partition` (D1; Xcelium ≥ 23.09).
  7. Smaller scope: a lower `-inst_top` per sub-block (inputs become free → sound for UNR, may lose UNRs).
  8. Initial state R3 (`reset -shm`) if the spec reset sequence is long (D1; D6: initialised run found 40 vs 39 UNR).
  9. Abstractions (counters, memories) are general Jasper features — use with UNR is UNCONFIRMED — verify in D2 / D1 before use; any abstraction is recorded like a constraint.
- Black-boxing to gain convergence removes the box's own items from analysis — record it (R2).

### Step 10: Re-run / Iteration
- Re-run after: RTL change, new sim DB, ccf change, constraint change, refinement update.
- Pass the reviewed refinement with `-load_refinement` so refined holes are skipped (D1); `-covoverwrite` or a new `-covtest` name per run (D1).
- Re-validate existing `.vRefine` rules after any RTL/ccf change (D7 "Handling Invalid Refinement Rules").
- Keep one `unr_review.csv` per config; carry decisions forward only for unchanged items (same file/line/checksum).

### Step 11: Debug Hand-off — `formal-cex-debug` (when relevant)
- Load skill `formal-cex-debug` (file: `/proj/adip_digital/rgulghan/workareas/wrk_rgulghan/Handoff/skills/formal-cex-debug/SKILL.md`).
- Triggers: a C4 item (spec says reachable, Jasper says UNR) → over-constraint or RTL bug; a reachable item the user expected to be dead → inspect the witness (`check_unr -prove -keep_trace`, D2).
- Output: `<results>/rca/unr_<UNR_ID>.md`.

## UNR Pitfalls Reference

| ID | Pitfall | Prevention |
|----|---------|------------|
| UNR-P01 | `check_unr -setup -coverage all` (kit) | coverage types via `-jg_coverage` / `-init -coverage` (K1) |
| UNR-P02 | `database -init_unicov` without `-app unr` | omit, or `-app unr -interval <t>` (K2) |
| UNR-P03 | different / missing ccf in UNR compile | same `-covfile` list as sim (K6, R6) |
| UNR-P04 | glitch strobe mismatch → sim glitch hits | D1 glitch settings in sim and UNR (K7) |
| UNR-P05 | `-inst_top` not the coverage top / wrong hierarchy separator | verify in IMC; `-dutinst` if needed (D1) |
| UNR-P06 | signal paths with TB top-module name in `assume`/`stopat` | drop the top-module name (D1) |
| UNR-P07 | `stopat` after `check_unr -setup` | `stopat -env` before setup (D1) |
| UNR-P08 | RTL-derived tie-offs | spec-only constraints (R3) |
| UNR-P09 | TB port constants silently preserved | list and justify (Q9, D1) |
| UNR-P10 | blanket `exclude ... -unr` / partial-UNR exclusion | per-item review (R5) |
| UNR-P11 | UNR of one config reused for another | refinement per config (class C2) |
| UNR-P12 | BND treated as unreachable | BND stays a hole (Step 9) |
| UNR-P13 | resilient compilation removed code unnoticed | read the summary (Step 5) |
| UNR-P14 | `check_cov` / `-jgcov` in the UNR session | not supported together (D3, R7) |
| UNR-P15 | second run fails: covtest exists | `-covoverwrite` or new `-covtest` (D1) |
| UNR-P16 | sim covdb not writable | `-covworkdir` (Xcelium ≥ 23.01-a071 / 23.03-s001) |
| UNR-P17 | old Jasper with new Xcelium | D1 version dependency (K5) |
| UNR-P18 | legacy IEV commands (`define effort`, `assertion -summary`) | Jasper commands only (K4) |
| UNR-P19 | expression scoring other than SOP/control; block items of unconditional statements | not targeted by UNR (D1 Supported Coverage Items) |
| UNR-P20 | enum assigned X never reported UNR | D1 formal/sim difference; stays a hole |
| UNR-P21 | branch scoring with multiple expressions per case tag | D1 Limitations; one UNR property for several sim items |
| UNR-P22 | stale `.vRefine` after RTL change | re-validate (Step 10) |
| UNR-P23 | `!UNR_SIM_COMPLETE_FLAG` read as a UNR setting | `!` = negated prefix (kit_reference.md) |

## Output Files

```
<formal_dir>/unr/
├── jg_unr.tcl                      UNR input TCL (xrun -input / UNR_FML_TCL_FILE)
├── jg_unr_pre.tcl                  Optional pre-elaboration TCL (-jg_pre_tcl)
├── unr.bblist                      Black-box module list (each with reason)
├── unr_constraints.md              Constraint / black-box / reset plan with spec refs (Step 3)
├── <cfg_dir>/RUNCMD_xrun           xrun run command (flow A/C)
├── <cfg_dir>/sim.setup             UNR_* block (flow B/C) — or edit of the block sim.setup
├── <cfg_dir>/RUNCMD                adsim run command (flow B/C)
└── <cfg_dir>/jgproject/            Jasper project (sessionLogs/session_<n>/unr_imc_coverage_merge.cmd)

<formal_dir>/unr/results/<cfg>/
├── unr_summary.txt                 report -summary -task unr
├── unr_reason.txt / unr_reason.cmd check_unr -reason (App. A)
├── discarded_items_report.txt      copied from the session dir
├── unr_review.csv                  Per-item review and decision
├── imc_unr_exclude.cmd             Reviewed per-item excludes
├── <ip>_<cfg>_unr.vRefine          IMC refinement (save -refinement)
├── unr_cov_report/                 report_metrics output
└── rca/unr_<UNR_ID>.md             formal-cex-debug reports (if any)
```

## Optional Step: vPlan Creation (USER DECIDES — now or later)
- Use answer Q22 (ask now only if missing; do NOT decide silently):
  - **NOW** → after Step 8: load skill `formal-vplan` (file: `/proj/adip_digital/rgulghan/workareas/wrk_rgulghan/Handoff/skills/formal-vplan/SKILL.md`); UNR section = per config: targets, UNR / RCH / BND counts, refinement file, open findings.
  - **LATER** → list as pending in the final summary.
  - **NOT NEEDED** → skip.

## Sign-Off Traceability — `formal-traceability` (only if Q23 = yes)
- Load skill `formal-traceability` (file: `/proj/adip_digital/rgulghan/workareas/wrk_rgulghan/Handoff/skills/formal-traceability/SKILL.md`).
- Inputs: `unr_review.csv` (each EXCLUDE row → spec reference) and `unr_constraints.md` (each constraint as `ASSUME`).
- Not mandatory by default: UNR closes coverage holes, it does not verify spec requirements.

## Final Step: Parameter & Default-Value Audit — NOT APPLICABLE by default
- `param-spec-audit` is not part of the UNR flow; run it only if the user asks (e.g. many C2 items caused by parameter-dependent dead code).
- If requested: load `/proj/adip_digital/rgulghan/workareas/wrk_rgulghan/Handoff/skills/param-spec-audit/SKILL.md`; reuse Q1/Q3/Q7.

## Reference
- Authoritative docs: `/cad/adi/apps/cadence/jasper/2025.09-p002/doc` — `jasper_unr_userguide.pdf` (D1), `jasper_command_reference.pdf` (D2, `check_unr`, `database`, App. K), `example_jasper_apps/UNR/` (D6); IMC `/cad/adi/apps/cadence/mdv/linux/current/doc/imcuser/imcuser.pdf` (D7); adsim `/cad/adi/apps/adi/adsim/man_db/current/adsim_man.db` (D8). Details: `resources/doc_reference.md`.
- Lab kit summary and corrections: `resources/kit_reference.md`.
- Sibling skills: `formal-cex-debug`, `formal-vplan`, `formal-traceability`, `param-spec-audit`, `adsim` (absolute paths above).

## Quality Checklist

### Setup
- [ ] Upfront Questions Q1–Q23 asked once; answers in the final summary
- [ ] Installed Jasper / Xcelium / IMC versions recorded; no kit version pins
- [ ] Sim covdb path verified; baseline coverage numbers recorded
- [ ] UNR compile uses the same RTL, defines, parameters and every sim `-covfile` (same order)
- [ ] `-inst_top` = coverage top in the sim hierarchy; signal paths without TB top-module name

### Constraints
- [ ] Every `assume` / `stopat` / tie-off / reset choice / black box has a reason; constraints cite a spec section
- [ ] No constraint derived from RTL; TB port constants listed
- [ ] `stopat -env` placed before `check_unr -setup`
- [ ] Reset / initial-state choice (R1/R2/R3) recorded

### TCL / sim.setup
- [ ] `check_unr -setup` without `-coverage`; types via `-jg_coverage` / `UNR_FML_COVERAGE`
- [ ] No `database -init_unicov` without `-app unr`; `database -export_unicov` present
- [ ] No `check_cov` / `-jgcov`; no legacy IEV commands
- [ ] "Coverage waivers: ADD WAIVERS HERE" placeholder present
- [ ] `RUNCMD_xrun` and/or `RUNCMD` generated per config and printed
- [ ] adsim `UNR_FML_*` → xrun mapping verified in the first run log (TODO closed)

### Results / Review
- [ ] Target count, discarded items, resilient-compilation summary checked
- [ ] UNR / RCH / BND / UNP / DSB counts per coverage type recorded
- [ ] `check_unr -reason` files generated and used in `unr_review.csv`
- [ ] Every UNR item has a `unr_review.csv` row with class, justification, spec ref, constraint dependency
- [ ] No blanket or partial-level exclusion; every exclude has `-comment`
- [ ] C3 items excluded only with spec reason valid in all integrations; C4 items reported as findings
- [ ] BND / UNP items kept as holes; Step 9 actions recorded

### Outputs / Hand-off
- [ ] `.vRefine` saved; hooked via `COVERAGE_REFINE_FILE` / `load -refinement`; coverage before/after recorded
- [ ] Reports per Q20 generated
- [ ] `formal-cex-debug` run for C4 items (if any)
- [ ] vPlan choice (NOW / LATER / NOT NEEDED) recorded; traceability only if Q23 = yes
- [ ] Every UNCONFIRMED item listed in the final summary
