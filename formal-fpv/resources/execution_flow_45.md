# FPV Execution Flow — 9 Phases / 45 Steps, Spec-Only (formal-fpv)

- Used by SKILL.md section "Execution Flow" and by the Gate 4b + CP2 step before Step 9.
- Source: `formal-fpv-complete.md` Part P-v2 (9 phases, 45 steps) and Part P / Part P-v2 "Phase 4b" gate; methodology only.
- Rewritten to spec-only wording: RTL is used only for compile, bind and port / hierarchy names; every expected behaviour, clock, reset, bound and default comes from the spec.
- Jasper syntax: installed docs `/cad/adi/apps/cadence/jasper/2025.09-p002/doc` only.
- "Optional (Qn)" = executed only if the upfront answer Qn selects it; otherwise recorded as skipped in the final summary.
- Pitfall IDs (PF-nn) and checkpoints CP1 / CP2 / CP3: `resources/pitfalls.md`.

## Changes Versus Part P-v2 (Do Not Reuse the Old Wording)

| Old step | Problem | Spec-only replacement |
|----------|---------|-----------------------|
| 2 "Read ALL RTL files — hierarchy, clock/reset domains, CDC, FSMs, parameters" | behaviour learned from the DUT | RTL read for compile dependencies and binding names only; clocks, resets, FSMs, parameters from the spec |
| 4 "flop counts per domain" | RTL structure as input | spec clock / reset list (Q5 / Q6); `get_design_info` statistics are informational only |
| 13 "Signal scope analysis before bind" | — | kept as binding-only (names, hierarchy) |
| 15 "ICG taxonomy / gated-clock patterns / write-protection keys" | patterns taken from RTL | assumptions only from spec AoU; gating per `resources/clocking_multi_clock.md` |
| 16 "X-propagation output properties" | not FPV scope | hand-off to `formal-xprop` |
| 4b item 3 / self-audit 4 "grep posedge in RTL → clocks" | clocks derived from RTL | spec clock list compared with TCL and `clock -analyze` (findings only) |
| 4b self-audit 2a "grep RTL/spec if unsure" | RTL as feature source | feature applicability from the spec feature list (Q4) only |
| 4b item 10 "≥3 configs" | arbitrary count | one `<cfg_dir>` per spec value class (Q7 / Q8) |
| 31 "Relax ASSUMPTION_ISSUE items" | relaxing to match RTL | correct the assumption to the spec AoU text; no spec statement → spec gap |

## Step Mapping

| Phase | Step # | Step (generic, spec-only) | SKILL.md step | Output artefact | Owner skill |
|-------|--------|---------------------------|---------------|-----------------|-------------|
| 1 Preparation | 1 | Read the spec cover-to-cover; extract all requirements with SPEC_IDs and categories | Step 1 | `traceability/req_extraction.csv`, `spec_gaps.md` | formal-fpv (format: formal-traceability) |
| 1 Preparation | 1b | Write the verification strategy (scope, features, assumptions, black boxes, coverage, configs, sign-off criteria) | Step 2 | `verification_plan.md` | formal-fpv |
| 1 Preparation | 2 | Read RTL for compile dependencies and binding names only | Step 3 | `rtl_list/filelist.f`, binding notes in file headers | formal-fpv |
| 1 Preparation | 3 | Select the verification path from the spec block diagram / feature list | Step 0 | `verification_plan.md` "Methodology" | formal-fpv (input: `formal-methodology-select` report) |
| 1 Preparation | 4 | List spec clocks, ratios, resets, reset sequencing | Step 4 | `verification_plan.md` clock / reset table | formal-fpv |
| 1 Preparation | 5 | Map requirements to Jama items — Optional (Q21 = Jama) | Sign-Off Traceability | `req_extraction.csv` with Jama ID column | formal-traceability |
| 1 Preparation | 6 | Create the output directory layout | Output Files (Q22) | `<formal_dir>/` tree | formal-fpv |
| 2 Plan | 7 | Map SPEC_ID → property name → config(s); list assumptions with AoU citations | Step 2, Step 5 | `verification_plan.md`, `aou_traceability.csv` | formal-fpv / formal-traceability |
| 2 Plan | 7b | Generate vPlan — Optional (Q19 = NOW) | Optional Step vPlan | `<IP>_VPLAN.vplanx` | formal-vplan |
| 3 Infrastructure | 8 | Build the compile filelist with absolute paths; dependency audit | Step 3 | `rtl_list/filelist.f` | formal-fpv |
| 3 Infrastructure | 9 | Behavioural models for black-boxed macros / cells from the spec or cell datasheet | Step 3, Path 2 resource | `models/*.sv` | formal-fpv |
| 3 Infrastructure | 10 | Purely combinational part → hand-off | Step 0 (P1) | hand-off note in `verification_plan.md` | manual (hand-off `formal-connectivity`) |
| 3 Infrastructure | 11 | Register map → hand-off | Step 0 (P4) | hand-off note in `verification_plan.md` | manual (hand-off `formal-csr`) |
| 3 Infrastructure | 12 | Generate run scripts per configuration | Step 9 | `<cfg_dir>/RUNCMD_tcl` / `RUNCMD` | formal-fpv |
| 4 Collateral | 13 | Write assertions per spec feature (SPEC_ID comment, bounded liveness, defaults, negatives) | Step 6, Step 7 | `props/<ip>_<feature>_props.sv`, `props/<ip>_props_bind.sv` | formal-fpv |
| 4 Collateral | 14 | ABVIP per spec interface with the spec DUT role | Step 5, Path 2 / 3 resource | `props/<ip>_abvip_bind.sv` or wrapper | formal-fpv |
| 4 Collateral | 15 | Write spec-AoU assumptions + reachability covers | Step 5 | `props/<ip>_assumptions.sv` | formal-fpv |
| 4 Collateral | 16 | X/Z on outputs → hand-off | Integrations | hand-off note | manual (hand-off `formal-xprop`) |
| 4 Collateral | 17 | CSR setup → hand-off | Integrations | hand-off note | manual (hand-off `formal-csr`) |
| 4 Collateral | 18 | TCL / sim.setup with coverage init before `analyze`; one `<cfg_dir>` per config | Step 9a / 9b, Step 12 | `tcl/jg_fpv_setup.tcl`, `<cfg_dir>/sim.setup` | formal-fpv |
| 4b Gate | — | BLOCKING GATE (G1–G17) + CP2 | Gate 4b + CP2 (before Step 9) | `results/<cfg_dir>_gate4b.md`, `results/<cfg_dir>_pitfall_guard.md` | formal-fpv |
| 5 Primary config | 19 | Lint all generated SVA | CP1 (before Step 3 compile) | `results/<cfg_dir>_pitfall_guard.md` (CP1) | formal-fpv |
| 5 Primary config | 20 | `check_assumptions -conflict` and `-dead_end` | Step 8 (re-checked in G13) | `verification_plan.md` "Environment health" | formal-fpv |
| 5 Primary config | 21 | Run the proof (Proof Orchestration) | Step 9, Step 10 | `results/<cfg_dir>_summary.txt`, `_results.csv` | formal-fpv |
| 5 Primary config | 22 | Triage CEX against the spec | Step 11 | `rca/` | formal-cex-debug |
| 5 Primary config | 23 | Vacuity: precondition / witness covers, `neg_sanity` | Step 8 | `verification_plan.md` "Environment health" | formal-fpv |
| 6 Additional configs | 24 | Run every remaining `<cfg_dir>` | Step 9, Step 10 | `results/<cfg_dir>_*` | formal-fpv |
| 6 Additional configs | 25 | Triage config-specific CEX | Step 11 | `rca/` | formal-cex-debug |
| 6 Additional configs | 26 | Compare results across configs; each difference explained by spec parameter behaviour | Step 10 | `verification_plan.md` config comparison | formal-fpv |
| 6 Additional configs | 27 | CSR run | Integrations | CSR results | manual (hand-off `formal-csr`) |
| 7 RCA | 28 | Spec-anchored RCA on all failures | Step 11 | `rca/formal_rca_report.md` | formal-cex-debug |
| 7 RCA | 29 | Classify failures (labels per `formal-cex-debug`) | Step 11 | `rca/rca_summary.csv` | formal-cex-debug |
| 7 RCA | 30 | Fix property issues to the spec text | Step 11 | `props/*.sv` | formal-fpv |
| 7 RCA | 31 | Correct assumption issues to the spec AoU (never relax to match RTL) | Step 11, Step 5 | `props/<ip>_assumptions.sv`, `spec_gaps.md` | formal-fpv |
| 7 RCA | 32 | Report RTL bugs (Jira) — Optional (user tracking choice) | Step 11 | bug list in `rca/` | manual |
| 7 RCA | 33 | Re-run all configs (Gate 4b + CP2 again if collateral changed) | Step 9, Step 10 | `results/<cfg_dir>_*` | formal-fpv |
| 8 Coverage | 34 | Measure coverage (stimuli, COI, proof core, bound) and assumption health against Q17 targets | Step 12 | `results/<cfg_dir>_cov_*.html` | formal-fpv |
| 8 Coverage | 35 | Justify each unreachable cover with a spec citation | Step 12 | `traceability/unreachable_covers.csv` | formal-fpv / formal-traceability |
| 8 Coverage | 36 | Waivers at `# ADD WAIVERS HERE`, spec-cited | Step 12 | TCL waiver block | formal-fpv |
| 8 Coverage | 37 | Re-run with waivers; confirm targets | Step 12 | `results/<cfg_dir>_cov_*.html` | formal-fpv |
| 8 Coverage | 38 | Final coverage reports per config | Step 12 | `results/<cfg_dir>_cov_*.html` | formal-fpv |
| 9 Sign-off | 39 | Master traceability CSV | Sign-Off Traceability | `traceability/formal_traceability.csv` | formal-traceability |
| 9 Sign-off | 40 | Sign-off matrix | Sign-Off Traceability | `traceability/signoff_matrix.csv` | formal-traceability |
| 9 Sign-off | 41 | Sign-off checklist + CP3 | CP3 (before Step 12 sign-off), Quality Checklist | `results/<cfg_dir>_pitfall_guard.md` (CP3) | formal-fpv |
| 9 Sign-off | 42 | Publish results on Confluence — Optional (Q21 = Confluence) | Sign-Off Traceability | Confluence page | formal-traceability / manual |
| 9 Sign-off | 43 | vManager integration / vPlan mapping — Optional (Q19 vManager on) | Optional Step vPlan | vManager session | formal-vplan |
| 9 Sign-off | 44 | Update Jama / Jira status — Optional (Q21 = Jama, user tracking choice) | Sign-Off Traceability | Jama / Jira items | formal-traceability / manual |
| 9 Sign-off | 45 | Archive `jgproject` directories and session databases | — | archive location in final summary | manual |
| Final | (added) | Parameter spec audit (mandatory, not in Part P-v2) | Final Step | `reports/<ip>_param_audit.html` | param-spec-audit |

## Phase 4b — BLOCKING GATE (Before Step 9 Run Flows)

- Runs once per `<cfg_dir>` after Steps 0–8 and CP1, merged with CP2 of `resources/pitfalls.md`.
- Result file: `results/<cfg_dir>_gate4b.md` (table below, one row per G item: `ID | Check | Evidence | PASS / FAIL / N/A + reason`).
- Any FAIL → STOP: do not run `prove` (Flow A) or the adsim RUNCMD (Flow B); fix the collateral or ask the user (spec gap), then re-run the whole gate.
- N/A is allowed only with a spec reason (feature not in the spec / not in scope per Q4); N/A without reason = FAIL.
- Gate session for G12 / G13: run the setup TCL up to and including `check_assumptions` in `jg -fpv` without `prove` (Flow B: same filelist, clocks, resets and constraints as `sim.setup`).
- Re-run the gate after any change of props, assumptions, wrapper, models, filelist or configs (Step 33).

| ID | Gate item | Check | Pass criterion |
|----|-----------|-------|----------------|
| G1 | Requirement mapping | every `req_extraction.csv` row with `Formally_Verifiable` = YES / ASSUME: grep its SPEC_ID in `props/*.sv` | each row maps to ≥1 `ast_` / `cov_` / `asm_` property, or has a `GAP-NNN` (`spec_gaps.md`) or an out-of-scope reason; 0 unmapped rows |
| G2 | Spec gaps | `spec_gaps.md` OPEN items | every OPEN gap lists the blocked properties; no blocked property is written with an invented value; user informed |
| G3 | Assumption traceability | each `asm_*` in `props/` and ABVIP / wrapper parameter: spec comment + `aou_traceability.csv` row | count of `asm_*` = count of `aou_traceability.csv` rows; each cites a spec AoU / integration / protocol / operating-mode section |
| G4 | Assumption reachability | each value-forcing assumption, `stopat` + constraint, `abstract` | ≥1 `cov_*` per forced value class; abstractions recorded as limitations |
| G5 | Witness / precondition covers | `elaborate -create_related_covers {witness precondition}` in the setup; no `-no_preconditions` | every assertion has a related witness and precondition cover (`get_property_list -include {is_related_cover 1}` count vs assertion count) |
| G6 | Negative checks per feature | per Q4 feature: spec "must not" / disabled / masked / lower-priority / restricted assertions; `neg_sanity` task | ≥1 negative assertion per feature with such spec content; ≥1 `neg_*` per feature in task `neg_sanity` |
| G7 | Default / reset-value checks per feature | per Q4 feature: `ast_R*` for every spec reset value and idle / unselected default (Q8 context) | every spec reset / default value has an assertion; expected value from the spec or a spec parameter |
| G8 | Bounded liveness | grep `s_eventually`, `$]`, `[*]`, `[+]`, `##[*]`, `##[+]`, `[->`, `[=`, `until`, `s_until` in `props/` (`resources/sva_coding_rules.md` R3, PF-42) | 0 `s_eventually` / `s_until` hits; 0 hits in a consequent (antecedent hits listed with reason; `intersect 1'b1[*1:<SPEC_BOUND>]` exceptions recorded); every liveness bound is a `localparam` with a spec citation |
| G9 | Clocks / resets from spec | TCL `clock` / `reset -expression` vs spec list (Q5 / Q6); `clock -analyze` output | every spec clock declared with the spec ratio; all spec resets in one `reset -expression` list; `clock -analyze` extras recorded as findings |
| G10 | Path collateral complete | per spec feature (Q4) and path (Step 0): data integrity → scoreboard + explicit SVA for address, response, spurious transfer, memory semantics; spec storage macro → behavioural model; spec error model → error injection only on the spec error path; spec read-only region → write-block and read checks; spec partial writes → per-lane checks; each spec bus interface → ABVIP with the spec DUT role | every applicable item exists; applicability from the spec only |
| G11 | Black boxes | `-bbox_m` list in setup vs `verification_plan.md` | each black box listed with unverified spec features and covers on dependent assertions; `-disable_auto_bbox` used |
| G12 | Compile clean | CP1 result; gate-session log: `analyze` / `elaborate` | CP1 PASS; 0 errors in `analyze` / `elaborate`; no automatic black box |
| G13 | Assumption health | gate session: `check_assumptions -conflict`, then `check_assumptions -dead_end` (return values: command reference `check_assumptions`) | `-conflict` returns `no_conflict` (or `no_dead_end`); `-dead_end` returns `no_dead_end`; `conflict` / `dead_end` = FAIL; `-dead_end` returning only `no_conflict` (dead end unknown) = FAIL until resolved |
| G14 | Config matrix complete | `<cfg_dir>` list vs Q7 / Q8 and the spec parameter CSV (Step 1) | one `<cfg_dir>` per spec value class (IP and SoC context per Q8), each with its RUNCMD; every spec parameter value assigned to a config or a recorded gap |
| G15 | Hand-offs recorded | `verification_plan.md` "Methodology" | every Step 0 hand-off (`formal-connectivity`, `formal-csr`, `formal-xprop`) listed with scope |
| G16 | Run limits / bounds | Q14 limits; `set_max_trace_length` derivation if used | limits set; any bound ≥ deepest spec bound in scope, derivation recorded |
| G17 | CP2 pitfall guard | `results/<cfg_dir>_pitfall_guard.md` CP2 rows | every CP2 PF item PASS or N/A with reason |

- `results/<cfg_dir>_gate4b.md` template:

```markdown
# Gate 4b — <ip> / <cfg_dir> — <date>
- Result: PASS / FAIL
| ID | Check | Evidence (file:line / command output) | Result |
|----|-------|---------------------------------------|--------|
| G1 | Requirement mapping | <n> rows, <m> unmapped | PASS |
```
