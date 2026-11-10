# FPV Pitfalls — Generic, Corrected, Spec-Anchored (formal-fpv)

- Used by SKILL.md Steps 3–5 and 10–11 when compile, reset, ABVIP or proof problems appear, and enforced at checkpoints CP1 / CP2 / CP3 (section "Pitfall Guard").
- Derived from `formal-fpv-complete.md` Part O, corrected against the installed Jasper 2025.09 docs and ABVIP sources.
- Each item: symptom → cause → fix → evidence. "Not verified" marks items without doc evidence.
- Every fix must stay spec-only: never resolve a pitfall by copying RTL behaviour into a property or assumption.

## Pitfall Guard (ENFORCED — MANDATORY)
- Each pitfall has an ID `PF-nn` and a "Guard" field: checkpoint, concrete check, pass criterion.
- Checkpoints:
  - CP1 — before every compile (`analyze` / `elaborate`): first at SKILL.md Step 3 for the filelist items, then on the complete collateral before the Gate 4b session; items whose files do not exist yet are "PENDING" at Step 3.
  - CP2 — before `prove`; merged with Gate 4b (`resources/execution_flow_45.md`, G17); BLOCKING.
  - CP3 — after the proof runs, before SKILL.md Step 12 coverage sign-off; BLOCKING for sign-off.
- Record results in `results/<cfg_dir>_pitfall_guard.md`: one table per checkpoint, row `PF-nn | Check | Evidence (file:line / command output) | PASS / FAIL / N/A + spec reason / PENDING`.
- Any FAIL → stop at that checkpoint, apply the fix of the pitfall, re-run the checkpoint; N/A without a reason = FAIL.
- Terms used in the checks:
  - setup = `tcl/jg_fpv_setup.tcl` (Flow A) or `<cfg_dir>/sim.setup` + `<cfg_dir>/pre_analyze.tcl` (Flow B)
  - gate session = setup run in `jg -fpv` up to `check_assumptions`, without `prove` (Gate 4b)
  - run log = console output of the run (`|& tee`) or the session log under `<proj>/sessionLogs/<session>/` (log file name not verified in the command reference)
  - property status = `get_status <prop>` / `get_property_list -include {status <value>} -task <task>`; status values per command reference (`proven`, `cex`, `undetermined`, `covered`, `unreachable`, ...)

| Checkpoint | PF IDs | How checked |
|------------|--------|-------------|
| CP1 (before compile) | PF-01, PF-02, PF-03, PF-04, PF-06, PF-08, PF-09, PF-10, PF-11, PF-12, PF-40, PF-41, PF-45, PF-46 | grep / line order in setup and `filelist.f`; Lint (slang) of props / bind / wrapper; `analyze` / `elaborate` errors in the gate-session log |
| CP2 (before prove, with Gate 4b) | PF-05, PF-07, PF-13, PF-14, PF-15, PF-16, PF-17, PF-18, PF-19, PF-20, PF-21, PF-22, PF-23, PF-24, PF-25, PF-26, PF-27, PF-28, PF-29, PF-30, PF-38, PF-39, PF-42, PF-43, PF-44 | setup / bind / wrapper parameters vs spec citations in `verification_plan.md`; `clock -analyze`; `check_assumptions` return values (G13) |
| CP3 (after prove, before sign-off) | PF-26, PF-30, PF-31, PF-32, PF-33, PF-34, PF-35, PF-36, PF-37, PF-39 | `results/<cfg_dir>_summary.txt` / `_results.csv`; property status per task; coverage report files; `rca/` entries for changed properties |

## Corrections to Part O (do not reuse the old wording)

| Old pitfall | Correction |
|-------------|------------|
| 1 "JG can use only ONE reset expression" | `reset -expression` accepts a list of pin constraints (e.g. `{~rst1_n ~rst2_n}`); declare all spec resets together |
| 3 `clock -none` / `reset -none` | belongs to `formal-connectivity` (purely combinational); not used in FPV |
| 5 "include RTL priority conditions in the antecedent" | spec-only: priority terms come from the spec; an RTL override not in the spec is a finding |
| 6 reduced counter widths | only via spec-legal parameter values; otherwise use `abstract` (counter abstraction) and record it |
| 9 / 33 "convert to cover" | never convert a spec requirement to a cover; use the spec latency / bound in the assertion |
| 11 / 37 "verify encoding / names against RTL" | allowed for binding (names, port encoding mapping) only; expected behaviour still from the spec |
| 21 "Ht engine abstract port bug" | not verified in 2025.09 docs; do not add constant assumptions on outputs — report as tool issue |
| 18 / 39 error codes ESW212 / ESW046 | not verified; keep the practice (absolute `${FPV_ROOT}` paths, separate `analyze` per language mode) without the codes |
| 27 "include `!ecc_err_2b` in the antecedent" | only if the spec states that an uncorrectable error suppresses the write-back |
| 32 "cover RTL-only paths" | RTL-only behaviour is a spec gap → `spec_gaps.md`, ask the user |
| 34 "add no-collision for all master pairs" | only if the spec states it as AoU; otherwise it hides arbitration bugs |
| 40 "scoreboard only catches ordering" | `jasper_scoreboard_3` asserts `data_integrity` and `no_overflow`; add SVA for address, response, spurious-transfer and memory-semantics checks |

## Setup Order
- **PF-01 Coverage init after analyze** → Coverage App not initialised / missing cover items.
  - Fix: `check_cov -init` before `analyze` (coverage user guide, "Initialization and Configuration").
  - adsim `-jgcov` already issues `cov_init`: do not add `check_cov -init` in `sim.setup` (ECOV081, coverage user guide).
  - Guard CP1: Flow A — line number of `check_cov -init` < first `analyze` in the setup; Flow B — `grep -c "check_cov -init"` in `sim.setup` = 0. Pass: both true for the selected flow.
- **PF-02 Scoreboard macros undefined** (e.g. `` `JS3_IN_ORDER ``) → `jasper_scoreboard_3 -init` missing or issued before `clear -all`.
  - Fix: `clear -all` → `jasper_scoreboard_3 -init` → `analyze` (command reference `jasper_scoreboard_3`; scoreboard PDF flow).
  - Guard CP1: line order in the setup (Flow B: `pre_analyze.tcl`) is `clear -all` < `jasper_scoreboard_3 -init` < `analyze`. Pass: order holds, or N/A (no scoreboard).
- **PF-03 ABVIP modules not found** → `abvip -set_location <dir>` missing or after `analyze`.
  - Fix: before `analyze`; in adsim via `pre_analyze.tcl` (adsim `formal.md` ABVIP section).
  - Guard CP1: `abvip -set_location` present before the first `analyze` (Flow B: in `pre_analyze.tcl`). Pass: present and ordered, or N/A (no ABVIP, Q15).
- **PF-04 Relative paths fail** depending on launch directory.
  - Fix: `set FPV_ROOT <abs>` and prefix every file; `-proj` defaults to `./jgproject` (command-line options).
  - Guard CP1: every file entry in `filelist.f`, setup and RUNCMD starts with `/` or `${`. Pass: 0 relative entries.
- **PF-05 Tasks miss constraints** → tasks created before all assumptions were added.
  - Fix: create tasks (`task -create <t> -copy_all -source_task <embedded>`) after all constraints.
  - Guard CP2: in the setup every `task -create` line is after the last `assume` / constraint command. Pass: true for all tasks (incl. `neg_sanity`).

## Compile and Elaboration
- **PF-06 Unknown module silently black-boxed** → missing dependency (common library, SV interface, tech cell).
  - Fix: `elaborate -disable_auto_bbox`; add the missing file before its first user in the filelist.
  - SV interfaces (`*_if`, interface connectors) must be compiled; they cannot be black-boxed.
  - Guard CP1: `-disable_auto_bbox` on the `elaborate` line of the setup; gate-session log has 0 `elaborate` errors. Pass: both true.
- **PF-07 Tech cell / macro without a usable model**:
  - black box (`-bbox_m`) → outputs unconstrained (clock-gate output free → registers behind it may not update as in silicon)
  - fix: behavioral model from the cell / macro datasheet, or black box with the impact recorded and covers on affected assertions
  - Guard CP2 (= G11): every `-bbox_m <module>` in the setup has a `verification_plan.md` entry (unverified spec features) and covers on dependent assertions. Pass: 0 unlisted black boxes.
- **PF-08 Optional feature removed by a parameter** → props referencing it fail to elaborate.
  - Fix: wrap the props in `generate if (<PARAM>)`, condition taken from the spec.
  - Guard CP1: `elaborate` clean for every `<cfg_dir>`; each `generate if` condition cites the spec parameter. Pass: 0 errors in all configs.
- **PF-09 Parameter dependencies**: pass parameters per `<cfg_dir>` with `elaborate -parameter <name> <value>`; derived parameters stay derived (not verified: order dependence of `-parameter`).
  - Guard CP1: per `<cfg_dir>` the `-parameter` list equals the Q7 entry; no derived parameter overridden. Pass: exact match.
- **PF-10 Related covers error** → `-create_related_covers precondition` combined with `-no_preconditions` is an error (command reference `elaborate`).
  - Guard CP1: `grep -c "no_preconditions"` in the setup = 0. Pass: 0.
- **PF-11 ABVIP example flags not in 2025.09 reference** → e.g. `elaborate -enable_sva_isunknown` appears in an ABVIP example TCL but not in the 2025.09 command reference; do not copy example flags without checking the reference.
  - Guard CP1: every command switch used in the setup is found in `jasper_command_reference.pdf` (text search). Pass: 0 switches without a reference hit.
- **PF-12 SVA / bind syntax errors found only in Jasper** → long analyze iterations.
  - Fix: lint all generated props, bind, wrapper and model files (Lint tool, slang) before `analyze`.
  - Guard CP1: Lint result for `props/*.sv`, `wrapper/*.sv`, `models/*.sv`. Pass: 0 errors; warnings reviewed.

## Clocks and Resets
- **PF-13 Multi-clock design proves with wrong relation** → only one clock declared or ratio invented.
  - Fix: declare every spec clock (cumulative `clock` commands; `-factor` / ratio form); no spec ratio → spec gap.
  - Audit with `clock -analyze`.
  - Guard CP2 (= G9): `clock` lines in the setup vs the Q5 spec clock list; `clock -analyze` output in the gate session. Pass: every spec clock declared with its spec ratio; extra inferred clocks recorded as findings.
- **PF-14 Secondary reset domain starts uninitialised / resets re-assert mid-proof**:
  - all spec resets in one `reset -expression` list
  - after reset analysis reset pins are free; use `disable iff` with the property's domain reset(s), or a spec-cited reset-sequencing assumption
  - Guard CP2: exactly one `reset -expression` containing every Q6 reset; each assertion module has `default disable iff` or a spec-cited reset assumption. Pass: both true.
- **PF-15 Embedded assumptions ignored during reset** → embedded SVA assumptions are not used in reset analysis unless `-global_embedded_assumes` (command reference `reset`).
  - Guard CP2: if a spec-cited assumption must hold during reset, `elaborate` has `-global_embedded_assumes`. Pass: present, or N/A with reason.
- **PF-16 `reset -expression` with internal signals** → supports pin constraints only.
  - Guard CP2: every signal in `reset -expression` is a top-level input of `<top_module>` (binding names). Pass: 0 internal signals.
- **PF-17 Non-reset registers forced to one value** → `-non_resettable_regs` narrows initial states; use only with a spec power-up value.
  - Guard CP2: `grep -c "non_resettable_regs"` in the setup = 0, or each use cites the spec power-up value. Pass: true.
- **PF-18 APB4 ABVIP reset checks** → `RST_CHECKS_ON = 1` needs `reset -formal -bound 1 <reset_expression>` (APB4 bind example comment).
  - Guard CP2: `RST_CHECKS_ON = 1` in an APB4 bind ⇒ `reset -formal -bound 1` in the setup. Pass: implication holds, or N/A.

## ABVIP
- **PF-19 Wrong role** → ABVIP asserts on the stimulus side and assumes on the DUT side; DUT outputs unchecked.
  - AHB5-Lite wrapper `VERIFY_BLK`: 0 = master (DUT is manager), 2 = slave (DUT is subordinate), 3 = monitor; value 1 is not listed in `cdn_abvip_ahb5_lite_wrapper.sv`.
  - APB slave DUT: `cdn_abvip_apb4_master` with `PSEL_N` left at 1.
  - Guard CP2: per interface, ABVIP module / `VERIFY_BLK` in the bind or wrapper vs the Q15 DUT role. Pass: all match, or N/A (no ABVIP).
- **PF-20 Decoder never selects the DUT** → AHB5-Lite wrapper defaults `ACTIVE_SLAVES = 32'hf` with `SLAVE0..3` ranges `0x0000–0x6fff`.
  - Fix: `ACTIVE_SLAVES = 32'h1` and `SLAVE0_ADDRESS_START/END` from the spec memory map.
  - Guard CP2: `ACTIVE_SLAVES` and `SLAVE*_ADDRESS_START/END` set explicitly with a spec memory-map citation. Pass: no wrapper default left, or N/A.
- **PF-21 Bus width mismatch** → wrapper defaults `ABUS_WIDTH = 64`, `DBUS_WIDTH = 32` (power of 2 required); set from the spec.
  - Guard CP2: `ABUS_WIDTH` / `DBUS_WIDTH` set explicitly with a spec citation. Pass: true, or N/A.
- **PF-22 Wait-state bound** → `MAX_WAIT_CYCLES_READY` default 16; take from the spec, otherwise spec gap.
  - Guard CP2: `MAX_WAIT_CYCLES_READY` cites the spec or a `GAP-NNN`. Pass: true, or N/A.
- **PF-23 Duplicate protocol assumptions** → hand-written protocol assumptions on top of ABVIP may conflict; rely on ABVIP and `check_assumptions -conflict`.
  - Guard CP2 (with G13): no `asm_*` restating a protocol rule already covered by the ABVIP; `check_assumptions -conflict` does not return `conflict`. Pass: both true.
- **PF-24 Disabled ABVIP checks** → only for spec-unsupported features; record each.
  - Guard CP2: every disabled ABVIP check / parameter-off check has a `verification_plan.md` entry with the spec reason. Pass: 0 unrecorded.
- **PF-25 Vendor example `assume {hresetn == 1}`** (ABVIP slave example TCL) keeps reset released; use it only if the spec states reset is not re-asserted during operation.
  - Guard CP2: every assumption on a reset signal in the setup / props cites the spec reset-sequencing statement. Pass: 0 uncited reset assumptions.

## Scoreboard and Datapath
- **PF-26 `no_overflow` fails** → scoreboard misconfiguration: `MAX_PENDING` must equal the maximum number of chunks the DUV holds (scoreboard PDF).
  - Guard CP2: `MAX_PENDING` value with its spec derivation in `verification_plan.md`. CP3: scoreboard `no_overflow` status is not `cex`. Pass: both, or N/A (no scoreboard).
- **PF-27 `data_integrity` false CEX with partial writes** → the output carries merged data (read-modify-write) per spec.
  - Fix: scoreboard valid only for transfers the spec defines as pass-through (e.g. full-word writes); verify partial writes with memory-semantics SVA; do not restrict stimulus to full words globally.
  - Guard CP2: scoreboard valid condition cites the spec pass-through definition; partial-write SVA present if the spec defines partial writes; no global full-word stimulus assumption. Pass: all true, or N/A.
- **PF-28 Wrong results with `FREE_DATA = 1`** → only valid if incoming data is never used as control and is not constrained (scoreboard PDF, Parameter FREE_DATA).
  - Guard CP2: `FREE_DATA = 1` only with a recorded justification (data not used as control, unconstrained). Pass: true, or N/A.
- **PF-29 Error injection breaks write paths** → inject only where the spec error model applies (e.g. storage read path); constraints come from the spec error classes.
  - Guard CP2: every error-injection point and constraint cites the spec error model / error class. Pass: 0 uncited injection points, or N/A.
- **PF-30 Vacuous datapath proof** → no assertion besides the scoreboard covers; add SVA and check precondition covers.
  - Guard CP2 (= G10): explicit datapath SVA besides the scoreboard. CP3: all precondition covers of datapath assertions `covered`. Pass: both, or N/A.

## Proof and Results
- **PF-31 Proof stops early everywhere** → `set_max_trace_length` stops all engines at that depth; results are bounded.
  - Use it only for a bounded sign-off run; `set_prove_target_bound` changes reporting only (command reference).
  - Guard CP3: if `set_max_trace_length` is in the setup, `results/<cfg_dir>_summary.txt` and the sign-off report state the bound and report affected results as bounded. Pass: true, or N/A.
- **PF-32 Undetermined assertions** → engine / complexity.
  - Keep Proof Orchestration; try spec-justified abstractions (`abstract`, `stopat` + spec-legal value assumptions + covers, `elaborate -abstract_ram`); report the bound reached; never count as proven.
  - Guard CP3: `get_property_list -include {type assert status undetermined} -task <embedded>` list equals the undetermined rows reported with depth; none counted as proven. Pass: counts match.
- **PF-33 Free variables (cut points) not exercised** → add covers for each spec-legal value; force values only for spec operating modes, each covered.
  - Guard CP3: every cover attached to a `stopat` / free variable has status `covered` (or `unreachable` with a spec citation). Pass: 0 unexplained.
- **PF-34 Expected-CEX `neg_*` proven** → environment over-constrained; review assumptions and black boxes.
  - Guard CP3: `get_status` of every `neg_sanity::neg_*` is `cex`. Pass: 0 `proven` / `undetermined`.
- **PF-35 `prove -all` includes `neg_sanity`** → `prove -all` proves all tasks; report `<embedded>` and `neg_sanity` separately; in adsim gate `neg_sanity` behind a custom switch.
  - Guard CP3: sign-off counts in `results/<cfg_dir>_summary.txt` / `signoff_matrix.csv` exclude `neg_sanity`. Pass: 0 `neg_*` in sign-off counts.
- **PF-36 Batch run without GUI and `-jgcov`** → `formal-connectivity` / `formal-csr` state `-jgcov` requires one-step mode provided by `-gui`; for batch runs without `-gui`, set `FORMAL_ALWAYS_ONE_STEP_FLOW : 1` (adsim `formal.md`) and confirm coverage results appear (not verified).
  - Guard CP3: batch Flow B run ⇒ `FORMAL_ALWAYS_ONE_STEP_FLOW : 1` in `sim.setup` and coverage report files exist in `results/`. Pass: true, or N/A (GUI / Flow A).

## Spec Anchoring
- **PF-37 Property passes only after relaxing it** → relaxing to match RTL is forbidden; return to the spec text, log a spec gap if unclear.
  - Guard CP3: every property changed after Gate 4b (diff of `props/`) has an `rca/` entry citing the spec text or a `GAP-NNN`; no RTL-only justification. Pass: 0 uncited changes.
- **PF-38 Bound unknown** → no invented bound; spec gap, ask.
  - Guard CP2 (= G2 / G8): every bound `localparam` cites the spec or a `GAP-NNN` answered by the user. Pass: 0 uncited bounds.
- **PF-39 Default value differs between IP and SoC context** → run both contexts (Q8) and let `param-spec-audit` confirm coverage of every spec value.
  - Guard CP2 (= G14): a `<cfg_dir>` per Q8 context. CP3: `param-spec-audit` scheduled as the final step with the Q20 SoC source. Pass: both, or N/A (single context per Q8).
- **PF-40 Signal not visible at the bind scope** → retarget the bind or ask; never copy or re-derive RTL logic into the props.
  - Spec-derived helper code (flags, counters, shift registers modelling a spec rule) is allowed: prefix `aux_`, `// SPEC-<NNN>` comment, listed in the file header (`resources/sva_coding_rules.md` R10).
  - Guard CP1: every hierarchical reference in `props/*.sv` is recorded as binding-only in the file header; every helper signal is named `aux_*` with a SPEC_ID comment; no helper code reproducing RTL code. Pass: 0 unrecorded references, 0 helper signals without `aux_` prefix or SPEC_ID.

## SVA Coding (`resources/sva_coding_rules.md`)
- **PF-41 Cover with implication** → `cover property (<a> |=> <b>)` also matches traces without `<a>` under LRM semantics (Cadence SVA 6.0 lecture, slide 101–104).
  - Fix: cover the sequence (`<a> ##1 <b>`), R7.
  - Guard CP1: `grep -nE "cover (property|sequence)[^;]*\|[-=]>" props/*.sv` = 0 hits; every `cover` statement on one line. Pass: 0 hits, 0 multi-line covers.
- **PF-42 Weak open-ended consequent** → `[*]`, `[+]`, `##[*]`, `##[+]`, `$]`, `[->`, `[=`, `until` in a consequent never fail if the end never comes (assert / assume weak by default from the 2009 LRM; slide 76–77, 110–111, 189).
  - Fix: spec bound (`##[1:<SPEC_BOUND>]`), R3; no bound in the spec → spec gap.
  - Guard CP2 (= G8): G8 grep hits in `props/` are only in antecedents (each listed with reason) or recorded bounded `intersect` exceptions. Pass: 0 open-ended consequents.
- **PF-43 Overlapping trigger / missing pairing** → `<req> |-> ##[<lo>:<hi>] <gnt>` lets one grant satisfy several requests and never flags a grant without a request (slide 50, 134–136).
  - Fix: spec allows overlap or requires one response per request → `aux_` counter / shift-register template + "no grant without outstanding request" assertion (R1).
  - Guard CP2: every bounded-response assertion has either a spec citation for "no overlap, no pairing" or an R1 helper with an `ast_*_no_gnt_wo_req` / `_no_spurious` assertion. Pass: 0 unpaired response checks.
- **PF-44 Stuck-output check** → a one-direction implication on an output passes with the output tied to its active value (slide 57, 234).
  - Fix: equality form `<out> == $past(<f(in)>)` or the reverse property; covers for both output values (R2).
  - Guard CP2: every spec output function has an equality or reverse-direction assertion and `cov_*` for each output value (class). Pass: 0 one-direction-only outputs.
- **PF-45 Clock misuse in SVA** → clock signal inside a property expression, negedge property clock without a spec negedge domain, or more than one clock in one property (slide 39–43, 146, 177).
  - Fix: R9 (posedge default, one clock per property, per-domain props modules).
  - Guard CP1: per props module one `default clocking`; no property with two `@(` clock events; the clock port does not appear in any property expression; `negedge` only with a spec citation. Pass: 0 violations.
- **PF-46 LRM mode not recorded** → default strength and cover meaning differ between 2005 and 2009+ modes (slide 110–111, 115).
  - Fix: record the `analyze` switch (`-sv` = 2005 per command reference; `-sv09` / `-sv12` / `-sv17`) in `verification_plan.md` (R11, `resources/tcl_template.md` Notes).
  - Guard CP1: the language switch of every `analyze` line in the setup matches the mode recorded in `verification_plan.md`. Pass: recorded and consistent.
