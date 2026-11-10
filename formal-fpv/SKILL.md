---
name: formal-fpv
description: Spec-only JasperGold FPV setup (JasperGold 2025.09) — select the verification path first (Path 1 bind-file SVA, Path 2 FPV wrapper with ABVIP + behavioral/reference models + jasper_scoreboard_3, Path 3 interconnect three-pillar), write spec-derived assumptions, assertions and covers (incl. negative, default/reset-value and bounded-liveness checks), validate assumptions and vacuity, generate a TCL setup (jg -fpv) and/or adsim sim.setup with run commands, coverage sign-off, CEX hand-off, traceability, optional vPlan and final param audit. Use when the user asks for FPV setup, SVA properties, bind files, an FPV wrapper, scoreboard or ABVIP-based FPV, or FPV sign-off of an IP.
---

# Formal FPV Skill — JasperGold FPV Setup (Spec-Only, Path-Based)

**Resource loading (MANDATORY):**
- `resources/...` paths are relative to this skill's directory (the directory containing this SKILL.md).
- Resources are NOT preloaded. At each step that says "Read `resources/<file>`", open that file with View BEFORE writing any output for the step.
- Never generate a props/bind/wrapper file, TCL, sim.setup or model from memory when a resource file exists for it.
- The legacy file is archived under `archive/`; do NOT load it or use it as a source.

| Step | Resource file (read when reaching the step) |
|------|---------------------------------------------|
| Step 2 — Path 1 selected (bind-file SVA) | `resources/path1_bind_sva.md` |
| Step 2 — Path 2 selected (wrapper + ABVIP + models + scoreboard) | `resources/path2_wrapper_scoreboard.md` |
| Step 2 — Path 3 selected (interconnect three-pillar) | `resources/path3_interconnect.md` |
| Step 9a — TCL setup + RUNCMD_tcl | `resources/tcl_template.md` |
| Step 9b — adsim sim.setup + RUNCMD | `resources/sim_setup_template.md` |
| Step 3–5 and Step 10–11 — compile / reset / ABVIP / proof problems | `resources/pitfalls.md` |
| Step 4 — more than one spec clock, gated / divided / muxed clocks, resets per domain | `resources/clocking_multi_clock.md` |
| Path 2 datapath and Step 10–11 — memory / FIFO / arithmetic complexity, proof accelerators | `resources/proof_accelerators.md` |
| Any step — concrete example (memory controller with ECC; EXAMPLE ONLY, not a requirement) | `resources/sram_ecc_worked_example.md` |
| Start of the flow and Gate 4b (before Step 9) — 9-phase / 45-step map, BLOCKING gate G1–G17 | `resources/execution_flow_45.md` |
| Step 5–7 — writing assumptions, assertions, covers or `aux_` helper code (overlap / pairing, equality form, bounded consequents, cover style, clocking) | `resources/sva_coding_rules.md` |
| Checkpoints CP1 (Step 3), CP2 (Gate 4b), CP3 (before Step 12) — PF-01..PF-46 guard checks | `resources/pitfalls.md` |

## When to Use
- Activate when the user asks to:
  - Set up JasperGold FPV for an IP from its specification
  - Write SVA assertions, assumptions or covers, or a bind file
  - Build an FPV wrapper with ABVIP, behavioral memory / reference models and `jasper_scoreboard_3`
  - Verify an interconnect / bus fabric (arbitration, decode, access control, data integrity)
  - Create a JG FPV TCL setup or an adsim `sim.setup` for FPV
  - Sign off FPV results (assumption health, vacuity, coverage)
- Hand off instead:
  - Purely combinational routing → `formal-connectivity`
  - Register-map reset/access/protection → `formal-csr` (FPV of the functional logic still runs here)
  - X/Z checks on outputs → `formal-xprop`

## Upfront Questions (ASK ONCE, BEFORE ANY WORK — MANDATORY)
- Ask ALL of these in ONE question round (AskUserQuestions) before Step 0.
- Do not re-ask later; reuse the answers in every step. Record them in the final summary and in `verification_plan.md`.
- If an answer is "not known yet", continue and mark the dependent output as TODO.

| # | Question | Options / format | Used in |
|---|----------|------------------|---------|
| Q1 | Spec source (+ revision) | PDF / Jama / md path | all steps |
| Q2 | IP name and formal top module (bind target / elaborate `-top`) | `<ip>`, `<top_module>` | Step 2, 9 |
| Q3 | Path selection confirmation (after the Step 0 proposal) | Path 1 / Path 2 / Path 3 / combination; hand-off to `formal-connectivity` / `formal-csr` | Step 0 |
| Q4 | Feature list in scope (spec sections) | feature → spec section | Step 1, 6 |
| Q5 | Clocks per spec (names, edges, ratios, gating) | e.g. `hclk` 1:1, `pclk` = hclk/2 | Step 4 |
| Q6 | Resets per spec (names, polarity, sync/async, sequencing) | e.g. `hresetn` active-low async | Step 4 |
| Q7 | Parameter configurations (name + values per config) | `<cfg_dir>`: `<PARAM>=<VAL>` | Step 9, final audit |
| Q8 | Default / reset-value context | IP-level defaults / SoC-context values / both; are other default values allowed (parameter range)? | Step 6, final audit |
| Q9 | RTL filelist (compile only) | path to `filelist.f` | Step 3 |
| Q10 | Run flow | A. TCL / B. adsim sim.setup / C. both | Step 9 |
| Q11 | adsim block name (if B/C) | e.g. `adip_<ip>` | RUNCMD `-block` |
| Q12 | Run mode | GUI / batch | RUNCMD |
| Q13 | ProofGrid | yes (bsub command + max jobs) / no | Step 10 |
| Q14 | Time limits | global prove limit, per-property limit, coverage limit | Step 10, 12 |
| Q15 | ABVIP needed + protocol per interface | AHB5-Lite / APB4 / APB3 / AXI4 / none; DUT role (master/slave) per interface | Step 5, Path 2/3 |
| Q16 | ABVIP install path | e.g. `/cad/adi/apps/cadence/vip/latest/vips/abvip` | `abvip -set_location` |
| Q17 | Sign-off targets | default: Part W targets of `formal-fpv-complete.md`, or user values | Step 12 |
| Q18 | Coverage reports location | e.g. `${GPMS_NOBACKUP}/../public_html/$USER/jasper_reports` | Step 12 |
| Q19 | vManager / vPlan | vPlan NOW / LATER / NOT NEEDED; vManager on/off | Optional vPlan step |
| Q20 | SoC context for final param audit | SoC RTL glob / SoC CSV / not available | Final Step |
| Q21 | Traceability publish | none / Jama / Confluence | Sign-off traceability |
| Q22 | Output / formal directory | e.g. `$ADIP_BLOCKS_ROOT/<ip>/dv/formal/<formal_dir>` | all outputs |

- Only spec-gap questions are asked later (missing bound, default, state diagram, error condition, operating condition, clock ratio), since they are found during the flow.

## Inputs Required

| Input | Description | Example |
|-------|-------------|---------|
| **Spec** | IP specification — the ONLY requirement source | `<ip>_spec.pdf` |
| **RTL filelist** | Compile ONLY (DUT under test, never a requirement source) | `filelist.f` |
| **Top module** | Formal top / bind target | `<top_module>` |
| **Output dir** | Where FPV collateral is written | `fpv_env/` |

**SPEC-ONLY PRINCIPLE (MANDATORY):**
- The specification is the ONE AND ONLY source for expected behaviour, assumptions, bounds, latencies, clocks/resets, default and reset values, error conditions, state diagrams and priorities.
- RTL is read ONLY for:
  - the compile filelist and compile dependencies
  - top-level / port / hierarchy names needed to bind or connect (record "binding-only" in the file header)
- NEVER:
  - derive a property, state list, transition, priority term or bound from RTL code or RTL comments
  - generate FSM properties from the RTL state register / encoding
  - add an "RTL priority term" to an antecedent that the spec does not state
  - write or relax a property, or add an assumption, so that it matches RTL behaviour
  - waive a failing assertion by converting it to a cover
- Spec missing or ambiguous → log the item in `spec_gaps.md` and ASK the user. Do not fill it from RTL.
- Deriving expectations from the design under test makes verification circular (RTL bugs become "expected" behaviour).

**TOOL DOCUMENTATION (MANDATORY):**
- For all Jasper command syntax, always refer to the installed Cadence docs at `/cad/adi/apps/cadence/jasper/2025.09-p002/doc`.
- Docs win over memory, over `formal-fpv-complete.md` and over examples in this skill.
- Consult:

| Topic | Document | Look up |
|-------|----------|---------|
| All TCL commands | `jasper_command_reference.pdf` | `analyze`, `elaborate` (`-create_related_covers`, `-bbox_m`, `-disable_auto_bbox`, `-abstract_ram`), `clock` (`-analyze`, `-factor`), `reset` (pin list, `-non_resettable_regs`, `-formal -bound`), `assume`/`assert`/`cover` (`-name`, `task::name`), `check_assumptions` (return values), `get_needed_assumptions`, `prove` (`-bg`, `-wait`, `-dump_trace`, `-orchestration`), `task`, `abstract`, `stopat`, `report`, `abvip`, `jasper_scoreboard_3`, `set_*` limits, `jg` command-line options (`-fpv`, `-batch`, `-proj`) |
| Engines | `jasper_engine_selection.pdf` | Proof Orchestration (default), manual engine mode guidelines |
| Coverage | `jasper_cov_userguide.pdf` | `check_cov -init` (before analyze), coverage types stimuli / COI / proof core / bound, `-measure`, `-report`, ECOV081 with `cov_init`, waivers |
| ProofGrid | `jasper_proofgrid_manager.pdf` | `set_proofgrid_mode`, `set_proofgrid_shell`, max jobs |
| X-propagation | `jasper_xprop_userguide.pdf` | `check_xprop -init`, `$isunknown` support (used by `formal-xprop`) |
| Apps overview | `jasper_apps_userguide.pdf` | FPV app flow, property status indicators |
| Scoreboard PA | `proof_accelerators/jasper_scoreboard_3.pdf` | ports, parameters, `data_integrity` / `no_overflow`, lite checks |
| Memory PAs | `proof_accelerators/jasper_model_ram.pdf`, `jasper_model_mpram.pdf` | abstract memory models |
| All PAs | `proof_accelerators/` (22 datasheets: scoreboards, `jasper_model_*`, `jasper_datapath*`, `jasper_cache`, `jasper_power_sequencer`) | category, ports, parameters, setup steps, sanity checks (summary: `resources/proof_accelerators.md`) |
| Clocking | `AN_clocking_management.pdf` | `-factor` / `-phase`, `-both_edges`, `-pattern`, `-from -to`, `-rate`, gating, muxing, Clock Viewer, `sanity_check`, async → CDC App (summary: `resources/clocking_multi_clock.md`) |
| Official FPV example | `example_jasper_apps/FPV/` (`FPV_verilog_sva_example.tcl`, `README.txt`) | flow order, `jg -fpv` invocation |
| ABVIP | `<abvip_dir>/<protocol>/rtl/*wrapper*.sv`, `<abvip_dir>/<protocol>/examples/`, Help – ABVIP User Guides | parameters, ports, `VERIFY_BLK` roles |
| Browsable HTML docs | `HTML/` | — |

**KEY PRINCIPLES:**
- Flow order (FPV example + command reference): `clear -all` → [`check_cov -init`] → [`jasper_scoreboard_3 -init`] → [`abvip -set_location`] → `analyze` → `elaborate` → `clock` → `reset` → constraints → `check_assumptions` → `prove`.
- Every assertion is anchored to a SPEC_ID; every assumption cites a spec section (AoU / integration / protocol / operating mode).
- Proof engines: default Proof Orchestration; manual `set_engine_mode` only with a recorded reason.
- Liveness policy (owner decision): BOUNDED ONLY, bound taken from the spec; no unbounded `s_eventually` / `##[1:$]`.
- Results are reported with their status and bound (proven / CEX / covered / unreachable / bounded with depth / undetermined with depth).

## Execution Flow
- Phase / step map (9 phases, 45 steps, spec-only wording, owner skill per step): `resources/execution_flow_45.md`.
- Checkpoints in this procedure: CP1 before compile (Step 3), Gate 4b + CP2 before Step 9 (BLOCKING), CP3 before Step 12 sign-off (BLOCKING).

---

## Step-by-Step Procedure

### Step 0: Methodology and Path Selection (FIRST — MANDATORY)
- Methodology report present (`<ip>_formal_methodology.md` from `formal-methodology-select`, status APPROVED):
  - take the D-FPV1 / D-FPV2 / D-FPV3 features, paths, hand-offs, config matrix and spec gaps from it; Q3 is pre-filled
  - re-check only that the path table below agrees with the report; a mismatch is raised to the user
- No report → run `formal-methodology-select` (`skills/formal-methodology-select/SKILL.md`) first, then continue here.
- `formal-fpv-complete.md` is a backup only; it is not read at runtime.
- Decide from the spec block diagram, feature list and interface list (NOT from RTL structure).
- Path questions (summary of `formal-methodology-select` `resources/decision_tree.md`); walk in order, the first YES decides the main path:

| # | Question (answer from the spec) | YES → | NO → |
|---|---------------------------------|-------|------|
| P1 | Is the design (or the part in scope) PURELY COMBINATIONAL (no clocks, no state): mux/demux fabric, pinmux, decoder, glue? | Hand off to `formal-connectivity`; stop FPV for that part | P2 |
| P2 | Is it an INTERCONNECT / CROSSBAR (multiple initiators AND multiple targets, decode + arbitration)? | **Path 3** — interconnect three-pillar | P3 |
| P3 | Does the spec require END-TO-END DATA INTEGRITY through storage or transformation (memory controller, bus bridge, DMA, protocol converter, FIFO, ECC)? | **Path 2** — FPV wrapper + ABVIP + behavioral/reference models + `jasper_scoreboard_3` + SVA | P4 |
| P4 | Does it have memory-mapped registers whose reset/access/protection must be signed off? | Hand off the register map to `formal-csr` (separate run) AND continue with **Path 1** for the functional logic | **Path 1** |

- Path summary:

| Path | Typical IPs | Environment | Resource |
|------|-------------|-------------|----------|
| **Path 1** — bind-file custom SVA | control logic, FSMs, timers, interrupt controllers, GPIO, control port, TRU, PLIC | `bind <top> <props_module>`; assumptions + assertions + covers in props files | `resources/path1_bind_sva.md` |
| **Path 2** — FPV wrapper | memory controllers (SRAM controller), bus bridges, DMA, protocol converters | wrapper instantiates DUT + ABVIP (protocol assumptions/checks) + behavioral memory model + reference model + `jasper_scoreboard_3` + SVA | `resources/path2_wrapper_scoreboard.md` |
| **Path 3** — interconnect three-pillar | AHB/APB/AXI fabrics, crossbars | Pillar 1 ABVIP per port; Pillar 2 scoreboard per initiator→target path; Pillar 3 SVA for decode, arbitration, access control, bounded fairness | `resources/path3_interconnect.md` |

- Path 2 datapath with deep storage or arithmetic (memory, FIFO, divider, multiplier): proof accelerator choice and setup in `resources/proof_accelerators.md` (with `resources/path2_wrapper_scoreboard.md`).
- Combinations are normal:
  - Path 2 / Path 3 environments also carry Path 1-style bind props for control features (status, interrupts, error responses).
  - `formal-csr` for the register map runs alongside any path.
  - `formal-xprop` runs alongside any path (X-Prop App session).
- Present the proposed path(s) with the spec evidence (section numbers) and get Q3 confirmation.
- Record the decision, the evidence and any hand-offs in `verification_plan.md` (section "Methodology").

### Step 1: Spec Requirement Extraction
- Read the spec cover-to-cover with View / queryFileWithEmbeddings / pdfMarkdown BEFORE writing rows. Never invent requirements.
- Create `traceability/req_extraction.csv` in the `formal-traceability` format (`SPEC_ID,PDF_Section,Category,Requirement_Text,Formally_Verifiable,Notes`).
- Extract per feature (Q4):
  - interfaces and protocol references (which standard, which revision)
  - functional behaviour, data transforms, latencies (cycles), ordering
  - state diagrams (states, transitions, conditions) — spec names only
  - error conditions and error responses
  - status / interrupt set, clear, mask, priority rules
  - reset values and default / idle / unselected output values (Q8 context)
  - parameters: legal ranges, defaults, parameter-dependent behaviour
  - clocks, clock ratios, resets, reset sequencing
  - assumptions of use (AoU), integration rules, operating modes
  - bounds for every "eventually", "within", "after" statement
- `Formally_Verifiable` = YES (assertion), ASSUME (environment constraint), NO (analog, timing, DFT, power — out of FPV scope, with reason).
- Every missing value (bound, default, transition, condition, ratio) goes to `spec_gaps.md`:
  - `GAP-NNN`, spec section, question, impact (which properties are blocked), status (OPEN / ANSWERED by `<who>` on `<date>`)
- Ask the user the open spec-gap questions in one round; never fill a gap from RTL.

### Step 2: Verification Plan and Environment Layout
- Read the path resource(s) selected in Step 0:
  - `resources/path1_bind_sva.md`, `resources/path2_wrapper_scoreboard.md`, `resources/path3_interconnect.md`
- Write `verification_plan.md`:
  - Methodology (Step 0 result), features → spec sections → property categories
  - environment per path (files, ABVIP roles, models, scoreboards)
  - configurations (Q7) and tasks (main, per-initiator, per-mode, `neg_sanity`)
  - assumptions list with spec citations
  - spec gaps reference, sign-off targets (Q17)
- File naming: `<ip>_<feature>_props.sv`, `<ip>_assumptions.sv`, `<ip>_props_bind.sv`, `<ip>_abvip_bind.sv`, `<ip>_fpv_wrapper.sv`, `<ip>_<model>_model.sv`.

### Step 3: Filelist and Compile Dependencies
- **Checkpoint CP1** (before compile): read `resources/pitfalls.md` "Pitfall Guard"; run the CP1 checks on the filelist now and on the complete collateral before the first `analyze` (Gate 4b session); record in `results/<cfg_dir>_pitfall_guard.md`; any FAIL → fix before compiling.
- RTL is used here for compile only.
- Build `rtl_list/filelist.f` (or reuse Q9) with absolute paths (`${ADIP_BLOCKS_ROOT}` / `${FPV_ROOT}` style variables).
- Compile-dependency audit:
  - list all instantiated modules, packages, includes and interfaces reachable from `<top_module>`
  - every missing module is either compiled, modelled (spec / cell datasheet of the macro), or black-boxed with `elaborate -bbox_m <module>` and its impact recorded
  - use `elaborate -disable_auto_bbox` so an undefined module stops elaboration instead of being black-boxed silently
  - SV interfaces must be compiled (see `resources/pitfalls.md`)
- Black-box impact: outputs of a black box are unconstrained; record per black box which spec features are not verified, and add covers for any assertion that depends on it.
- Run `get_design_info` after elaborate and record the design statistics in `verification_plan.md`.

### Step 4: Clocks and Resets (from the spec, Q5/Q6)
- Clocks:
  - Declare every spec clock: `clock <clk>`; successive `clock` commands are cumulative.
  - Clock ratio from the spec: `clock <clk2> -factor <N>` or `clock <clk1> <clk2> <factor> <phase>` — no spec ratio → spec gap, ask.
  - Audit: run `clock -analyze` and compare the reported clocks with the spec clock list; a clock not in the spec is a finding (record, do not silently add).
- Multi-clock (more than one spec clock) — read `resources/clocking_multi_clock.md`:
  - declare the fastest spec clock first; all Jasper clocks are synchronous to it (`AN_clocking_management.pdf` p4)
  - sync ratio / phase / both edges / pattern / gated / muxed / derived: case table in the resource; ratio, phase and relation from the spec only
  - inputs of a slower domain: `clock -rate <inputs> <clk>`
  - asynchronous clocks: FPV per synchronous domain with a spec ratio; `-from -to` range or `jasper_model_frequency_jitter` only as a later step; metastability → D-CDC hand-off
  - resets of all domains in one `reset` list; `-max_iterations N -clock <clk>` when a slow domain needs it
- Resets:
  - One `reset -expression` with ALL spec resets (list form), e.g. `reset -expression {~<rst1_n> ~<rst2_n>}`; the doc examples use `~` for active-low.
  - `reset -expression` supports pin constraints only.
  - After reset analysis, reset pins are free and may re-assert during the proof. Choose per property:
    - `disable iff` with the reset(s) of the property's spec domain, or
    - a spec-cited assumption (only if the spec states the reset sequencing / that reset stays released).
  - Embedded SVA assumptions are not used during reset analysis unless the design is elaborated with `-global_embedded_assumes` (command reference `reset`, p1223).
  - `-non_resettable_regs` assigns a fixed initial value to non-reset registers; use it only if the spec states the power-up value, otherwise leave it out.
- Record clock/reset decisions with spec citations in `verification_plan.md`.

### Step 5: Assumptions (Spec AoU Only)
- Allowed sources, each cited in the assumption comment (`// SPEC_ID | AoU <section> | <text>`):
  - spec assumptions of use / integration rules
  - bus protocol rules → ABVIP (do not duplicate ABVIP protocol assumptions by hand)
  - spec operating mode in scope (e.g. functional mode only, test mode out of scope) — record as scope limitation
  - spec legal parameter / configuration values and spec "static during operation" statements
  - spec reset sequencing and clock relations
  - abstraction constraints (`stopat`, `abstract`, `elaborate -abstract_ram`) with a written justification
- Forbidden:
  - assumptions derived from RTL behaviour or added only to remove a CEX
  - assumptions that make a spec feature unreachable without a cover proving reachability
- Naming: `asm_<CAT><NN>_<desc>`; one file `props/<ip>_assumptions.sv` (+ ABVIP bind / wrapper parameters).
- For every value forced by an assumption, abstraction or `stopat`-and-constrain step, add a cover showing each spec-legal value is reachable.
- Every assumption gets a row in `aou_traceability.csv` (`formal-traceability` Step 7b).

### Step 6: Assertions (Spec Features)
- Read `resources/sva_coding_rules.md` before writing any property or `aux_` helper code.
- Generate, per spec feature (Q4), the applicable categories:

| Category | Spec content checked | Example form |
|----------|----------------------|--------------|
| Data integrity | data in → data out / storage, transform, latency | scoreboard (Path 2/3) or `<in_valid> \|-> ##<SPEC_LAT> <out> == <f(in)>` |
| Response / error | each spec error condition → spec error response; no error on legal access | `<illegal_cond> \|-> <err_resp>` |
| State machine | spec states / transitions / conditions | assert on spec-observable outputs per state; state mapping to RTL only if the user supplies it (binding-only) |
| Status / interrupt | set, clear, sticky, mask, priority; `irq == f(status, enable)` per spec | `$rose(<status>) \|-> <spec_set_cond>` plus the reverse direction or the equality form (`resources/sva_coding_rules.md` R2) |
| Reset / default values | outputs, status, idle / unselected outputs per Q8 context | see "Default and reset values" |
| Parameter behaviour | per-parameter spec behaviour, optional features | `generate if (<PARAM>)` around feature props |
| Counters / timers | increment, reload, wrap / saturate, expiry per spec | `<expire> \|-> <count> == <SPEC_VALUE>` |
| Priority / arbitration | spec priority order, grant rules | `<req_hi> && <req_lo> \|-> !<gnt_lo>` |
| Bounded liveness | every spec "within N" / "eventually (bounded)" | `<req> \|-> ##[1:<SPEC_BOUND>] <ack>` only if the spec excludes overlapping requests and one-to-one pairing; otherwise `aux_` helper template (`resources/sva_coding_rules.md` R1) |

- SVA conventions:
  - Naming `ast_<CAT><NN>_<desc>`, `cov_<CAT><NN>_<desc>`; comment above each: `// SPEC_ID | <section> | <requirement text>`.
  - `default clocking` per spec clock domain; `default disable iff (<spec reset of the domain>)`.
  - Expected values come from the spec or from a spec-defined parameter — never a literal copied from RTL.
  - Arrayed / per-channel features: generate the property for every index; checking a subset is a coverage limitation recorded in `verification_plan.md`.
  - Signals not visible at the bind scope: retarget the bind to the module of the spec interface, or ask; never copy or re-derive RTL logic.
  - Spec-derived helper code (flags, counters, shift registers) is allowed with the `aux_` prefix and a SPEC_ID comment (`resources/sva_coding_rules.md` R10).
- Liveness policy (BOUNDED ONLY):
  - Use `##[1:<SPEC_BOUND>]` with `localparam int <SPEC_ID>_BOUND = <spec expression>`; no `s_eventually`, no `##[1:$]`.
  - Spec gives no bound → spec gap; ask the user; do not invent or widen a bound to make a proof pass.
- Default and reset values (Q8):
  - IP context: expected value = spec default / parameter default; SoC context: expected value = SoC parameter value (from Q20 source).
  - If other default values are allowed, write the property against the parameter (expected value = `<PARAM>`) and run one config per spec value class (Q7).
  - Reset check form, chosen per spec reset type, with the default disable overridden:
    - async reset: `ast_R<NN>: assert property (disable iff (1'b0) !<rst_n> |-> <sig> == <SPEC_DEFAULT>);`
    - sync reset: `ast_R<NN>: assert property (disable iff (1'b0) !<rst_n> |=> <sig> == <SPEC_DEFAULT>);`
  - Idle / unselected outputs: `<not_selected_cond> |-> <out> == <SPEC_DEFAULT or PARAM>` for every mode the spec lists.
- X/Z on outputs is NOT checked here → `formal-xprop`.

### Step 7: Covers and Negative Checks
- Covers follow `resources/sva_coding_rules.md` R7: no `|->` / `|=>` inside a `cover`; cover sequences.
- Related covers: elaborate with `-create_related_covers {witness precondition}` (one witness / precondition cover per assertion).
- Scenario covers per feature: each spec mode, each state and spec transition, each error condition, each interrupt source, each parameter-enabled feature, back-to-back and boundary cases stated in the spec.
- Assumption-reachability covers (Step 5): every assumption-forced / abstracted value class is reachable.
- Negative checks (spec "must not" behaviour), as assertions:
  - disabled path: `!<en> |-> <out> == <SPEC_DEFAULT>` or `!<en> |=> $stable(<out>)` per spec
  - masked source: `!<int_en>[i] && <no other enabled source> |-> !<irq>`
  - lower priority / non-selected source never wins: `<req_hi> && <req_lo> |-> !<gnt_lo>`
  - restricted initiator / protected access never reaches the target (Path 3)
  - no spurious response / write without a spec-valid request (Path 2)
- Expected-CEX sanity (environment not over-constrained):
  - one deliberately wrong property per feature in a separate task `neg_sanity`, created after all constraints:
  - `task -create neg_sanity -copy_assumes -source_task <embedded>` then `assert -name neg_sanity::neg_<CAT><NN> {<wrong expectation>}`
  - each must give a CEX; a PROVEN `neg_*` means the environment is over-constrained → review assumptions
  - exclude `neg_sanity` from sign-off results

### Step 8: Assumption Validation and Vacuity
- After constraints, before (or with) the proof:
  - `check_assumptions -conflict` (expected: no conflict) and `check_assumptions -dead_end` (expected: no dead end).
  - `get_needed_assumptions -property <ast>` for key assertions: assumptions that are not needed are reviewed; assertions that need an unexpected assumption are reviewed against the spec.
- Vacuity:
  - every precondition cover covered; an unreachable precondition = vacuous assertion → finding (assumption or spec issue)
  - every witness cover covered
  - `neg_sanity` results as in Step 7
- Record results in `verification_plan.md` ("Environment health").

### Gate 4b + CP2 (BLOCKING — Before Step 9)
- Read `resources/execution_flow_45.md` "Phase 4b" and `resources/pitfalls.md` "Pitfall Guard".
- Per `<cfg_dir>`: evaluate G1–G17 (gate session: setup up to `check_assumptions`, no `prove`) and the CP2 PF items.
- Record `results/<cfg_dir>_gate4b.md` and the CP2 table in `results/<cfg_dir>_pitfall_guard.md` (PASS / FAIL per item).
- Any FAIL → STOP; do not run `prove` or the RUNCMD; fix or ask (spec gap), then re-run the gate.

### Step 9: Run Flows (Q10) — Each Flow Has Its Own RUNCMD
- One `<cfg_dir>` per parameter configuration (Q7); `<cfg_dir>` = `default` when only one config exists.

| Flow | Generated per `<cfg_dir>` | Launch | Resource |
|------|---------------------------|--------|----------|
| **A. TCL** | `tcl/jg_fpv_setup.tcl` (shared) + `<cfg_dir>/RUNCMD_tcl` | `jg -fpv` | `resources/tcl_template.md` |
| **B. adsim** | `<cfg_dir>/sim.setup` + `<cfg_dir>/RUNCMD` + `<cfg_dir>/pre_analyze.tcl` (+ `pre_exit.tcl`) | `adsim ... -jasper -formal` | `resources/sim_setup_template.md` |
| **C. both** | all files of A and B | either | both resources |

#### Step 9a: Flow A — TCL (`jg -fpv`)
- Read `resources/tcl_template.md` and generate `tcl/jg_fpv_setup.tcl` from it.
- Configuration is passed with `jg -define CFG <cfg_dir>`; parameters are applied with `elaborate -parameter <PARAM> <VAL>`.
- `<cfg_dir>/RUNCMD_tcl` (`chmod +x`):

```tcsh
#!/bin/tcsh -f
# RUNCMD_tcl — Flow A, config <cfg_dir>
set FPV_ROOT = <formal_dir_abs>
cd ${FPV_ROOT}/<cfg_dir>
jg -fpv -tcl ${FPV_ROOT}/tcl/jg_fpv_setup.tcl -define CFG <cfg_dir> -proj ${FPV_ROOT}/<cfg_dir>/jgproject
# batch (Q12): add -batch; the script ends with: exit -force
```

#### Step 9b: Flow B — adsim `sim.setup`
- Read `resources/sim_setup_template.md` and generate the files from it.
- adsim runs `FML_TCL_COMMANDS` and then issues its own `prove -all`; do not add `prove` to `sim.setup`.
- `abvip -set_location` and `jasper_scoreboard_3 -init` must run before `analyze` → `pre_analyze.tcl` hook.
- Coverage in adsim: `-jgcov` (adsim issues `cov_init`; do not add `check_cov -init`).
- `<cfg_dir>/RUNCMD` (`chmod +x`):

```tcsh
#!/bin/tcsh -f
# RUNCMD — Flow B, config <cfg_dir>
adsim -clean -block <block_name> -gui -jgcov -jasper -formal \
      -resdir <formal_dir_abs>/<cfg_dir>/Result_ \
      -force_setup <formal_dir_abs>/<cfg_dir>/sim.setup
```

- Same form as the `formal-connectivity` / `formal-csr` RUNCMD; `-resdir` and `-force_setup` point to the same `<cfg_dir>`.
- `-jgcov` requires one-step mode; `-gui` provides it (as stated in `formal-connectivity` / `formal-csr`). For batch (Q12) see `resources/pitfalls.md`.

### Step 10: Engines, Bounds, ProofGrid and Results
- Engines: default Proof Orchestration (`prove -all`; `prove -orchestration on|off` to toggle). Manual `set_engine_mode {<engines>}` only with a recorded reason (`jasper_engine_selection.pdf`).
- Limits (Q14): `set_prove_time_limit <t>`, `set_prove_per_property_time_limit <t>`.
- Bounds:
  - `set_max_trace_length <N>` stops engines at depth N — it caps every proof; use it only for a bounded sign-off run and report it.
  - `set_prove_target_bound <N>` only changes reporting to "Bounded Proven (User)"; combine with `set_max_trace_length` to stop engines.
  - N must cover the deepest spec latency / bound in scope (largest `<SPEC_ID>_BOUND` + reset and pipeline depth from the spec); record the derivation.
- Complexity (undetermined / slow with deep memory, FIFO, divider / multiplier, counter in the COI): read `resources/proof_accelerators.md` — `jasper_model_ram` / `jasper_model_mpram` / `elaborate -abstract_ram`, `abstract -counter`, `-suggest` / `-justify` before triaging a CEX; record every abstraction as a limitation.
- ProofGrid (Q13):

```tcl
set_proofgrid_mode shell
set_proofgrid_shell {bsub -J %jasper_session_id -n %jasper_engine_job_threads -K -q <queue> -R "rusage[mem=%jasper_engine_job_memory_request_mib] span[hosts=1]"}
set_proofgrid_max_jobs <N>
set_proofgrid_per_engine_max_jobs <M>
```

- Results:
  - `report -summary -results -file results/<cfg_dir>_summary.txt -force` and `report -csv -file results/<cfg_dir>_results.csv -force`
  - CEX traces: `prove -all -dump_trace -dump_trace_type vcd -dump_trace_dir results/<cfg_dir>_cex` (VCD is readable by `formal-cex-debug` / queryWaveform)
  - report each property with status and depth: proven / bounded (depth) / undetermined (depth reached) / CEX (length) / covered / unreachable

### Step 11: CEX, Unreachable and Undetermined Triage
- Full procedure: `formal-cex-debug` (`/proj/adip_digital/rgulghan/workareas/wrk_rgulghan/Handoff/skills/formal-cex-debug/SKILL.md`); output in `rca/`.
- Spec-anchored triage summary (apply in this order):
  - Does the trace violate a spec AoU / protocol rule that is not yet assumed? → add the spec-cited assumption (+ reachability cover); no spec statement → spec gap, ask.
  - Does the property state exactly what the spec says? → fix the property to the spec text (never to the RTL).
  - Property and environment match the spec, RTL deviates → RTL_BUG; keep the assertion failing and report.
  - Spec unclear → SPEC_AMBIGUITY; log in `spec_gaps.md`, ask.
  - Unreachable cover → check assumptions and black boxes against the spec; EXPECTED only if the spec states it is unreachable.
  - Undetermined → engine / abstraction work (`resources/pitfalls.md`); report the bound reached; never treat as proven.
- Classification labels and `rca_summary.csv` format: as defined in `formal-cex-debug`.

### Step 12: Coverage Sign-Off
- **Checkpoint CP3** (BLOCKING for sign-off): run the CP3 checks of `resources/pitfalls.md` on the results of every `<cfg_dir>`; record in `results/<cfg_dir>_pitfall_guard.md`; any FAIL → back to Step 11.
- Flow A: `check_cov -init -type {stimuli coi proof bound} -model all -covdut <top_module>` BEFORE `analyze` (coverage user guide, "Initialization and Configuration"); default `-type` is `{stimuli coi bound proof}`.
- After the proof: `check_cov -measure -type {stimuli coi proof bound} -task <embedded> -time_limit <t>`.
- Report: `check_cov -report -type checker -report_file results/<cfg_dir>_cov_checker.html -force -html` and the same with `-type stimuli`, `-type formal`, `-type bounded`.
- Review:
  - stimuli unreachable / deadcode items: over-constraint or spec-unreachable (cite the spec) — each must be explained
  - checker (COI / proof core) uncovered items: missing assertions for spec features → add properties or record as gap
  - bounded items: depth reached vs spec bound
- Targets (Q17): default per `formal-fpv-complete.md` Part W; user values override.
- Waivers:

```tcl
# ADD WAIVERS HERE
```

### Sign-Off Traceability (Automatic After the Proof — MANDATORY)
- Run `formal-traceability` (`/proj/adip_digital/rgulghan/workareas/wrk_rgulghan/Handoff/skills/formal-traceability/SKILL.md`) automatically when the proof runs finish; do not ask.
- Inputs: `req_extraction.csv` (Step 1), all props / assumption / bind files, `results/*` per `<cfg_dir>`.
- Outputs in `traceability/`: `formal_traceability.csv`, `signoff_matrix.csv`, `aou_traceability.csv`, completeness audit (unmapped requirements, orphan properties).
- Publish only if Q21 says so.

### Optional Step: Verification Plan (vPlan, Q19)
- NOW → run `formal-vplan` (`/proj/adip_digital/rgulghan/workareas/wrk_rgulghan/Handoff/skills/formal-vplan/SKILL.md`) with `req_extraction.csv` as the requirement source.
- LATER → list it as a pending item in the final summary.
- NOT NEEDED → skip.

### Final Step: Parameter Spec Audit (MANDATORY)
- Run `param-spec-audit` (`/proj/adip_digital/rgulghan/workareas/wrk_rgulghan/Handoff/skills/param-spec-audit/SKILL.md`) as the last step.
- Inputs: IP name, top, RTL glob, spec param CSV (from Step 1), SoC context (Q20), DV dirs (`<formal_dir>` + sim dirs).
- Purpose: confirms every parameter / hardcoded default the spec defines was exercised by the configurations of Step 9 (IP and SoC context, Q8).
- Output: `reports/<ip>_param_audit.html`; untested spec values become new `<cfg_dir>` entries or recorded gaps.

---

## Integrations with Sibling Skills

| Skill | Path | When | Interface |
|-------|------|------|-----------|
| `formal-connectivity` | `skills/formal-connectivity/SKILL.md` | Step 0 P1 YES (purely combinational part) | hand off that part; FPV keeps sequential parts |
| `formal-csr` | `skills/formal-csr/SKILL.md` | Step 0 P4 YES (register map) | separate CSR run; FPV keeps functional logic |
| `formal-xprop` | `skills/formal-xprop/instructions.md` | any path; X/Z on outputs | separate X-Prop App session (`check_xprop -init` before analyze); same filelist / clocks / resets |
| `formal-cex-debug` | `skills/formal-cex-debug/SKILL.md` | Step 11 | CEX VCD from `-dump_trace`, property file, spec; returns `rca/` |
| `formal-traceability` | `skills/formal-traceability/SKILL.md` | automatically after the proof | `req_extraction.csv`, props, results |
| `formal-vplan` | `skills/formal-vplan/SKILL.md` | Q19 = NOW | `req_extraction.csv` |
| `param-spec-audit` | `skills/param-spec-audit/SKILL.md` | final step (mandatory) | spec param CSV, configs, DV dirs |

- Paths are relative to `/proj/adip_digital/rgulghan/workareas/wrk_rgulghan/Handoff/`.

## Output Files

```
<formal_dir>/
├── verification_plan.md            — methodology (Step 0), features, environment, configs, health
├── spec_gaps.md                    — GAP-NNN open questions and answers
├── rtl_list/filelist.f             — compile only
├── props/
│   ├── <ip>_assumptions.sv         — spec AoU assumptions (asm_*)
│   ├── <ip>_<feature>_props.sv     — assertions + covers per feature (ast_*, cov_*)
│   ├── <ip>_props_bind.sv          — bind statements (Path 1, control props of Path 2/3)
│   └── <ip>_abvip_bind.sv          — ABVIP bind (if bind-style ABVIP)
├── wrapper/<ip>_fpv_wrapper.sv     — Path 2 / Path 3 only
├── models/                         — Path 2 / Path 3 only (memory / reference models)
├── tcl/jg_fpv_setup.tcl            — Flow A / C
├── <cfg_dir>/
│   ├── RUNCMD_tcl                  — Flow A / C
│   ├── sim.setup                   — Flow B / C
│   ├── RUNCMD                      — Flow B / C
│   ├── pre_analyze.tcl             — Flow B / C (abvip, scoreboard init)
│   └── pre_exit.tcl                — Flow B / C (reports)
├── results/                        — summaries, CSV, CEX VCD, coverage HTML per <cfg_dir>
│   ├── <cfg_dir>_gate4b.md         — Gate 4b G1–G17 PASS / FAIL table
│   └── <cfg_dir>_pitfall_guard.md  — CP1 / CP2 / CP3 PF-nn PASS / FAIL tables
├── rca/                            — formal-cex-debug outputs
├── traceability/                   — req_extraction.csv, formal_traceability.csv, signoff_matrix.csv, aou_traceability.csv
└── reports/<ip>_param_audit.html   — param-spec-audit
```

## Reference
- Source methodology: `/proj/adip_digital/rgulghan/workareas/wrk_rgulghan/Handoff/formal-fpv-complete.md` (Part B decision tree; Part W sign-off). Methodology only — Jasper syntax always from the installed docs.
- Jasper docs: `/cad/adi/apps/cadence/jasper/2025.09-p002/doc`.
- ABVIP: `/cad/adi/apps/cadence/vip/latest/vips/abvip/<protocol>/{rtl,examples}`.
- adsim formal reference: `adsim` skill, `resources/formal.md`.

## Quality Checklist

### Path and Spec
- [ ] Upfront questions asked once; answers recorded in `verification_plan.md`
- [ ] Step 0 path decision recorded with spec evidence and confirmed (Q3); hand-offs listed
- [ ] `req_extraction.csv` built from the spec only; every gap in `spec_gaps.md`
- [ ] No property, state, transition, priority term or bound derived from RTL

### Environment
- [ ] Filelist dependency audit done; every black box listed with impact
- [ ] All spec clocks / resets declared; `clock -analyze` audit compared with spec
- [ ] Multi-clock: fastest clock first, spec ratio / phase per clock, slower-domain inputs `clock -rate`d, `sanity_check -analyze all` / `reset -analyze` clean, async crossings handed to D-CDC (`resources/clocking_multi_clock.md`)
- [ ] Proof accelerators / abstractions only after the complexity gate; PA commands after `elaborate` and before `clock` / `reset`; PA sanity checks pass; abstracted instances listed as limitations (`resources/proof_accelerators.md`)
- [ ] Every assumption cites a spec section and has a reachability cover where it forces values
- [ ] ABVIP role (`VERIFY_BLK` / master vs slave wrapper) matches the DUT role per interface
- [ ] `check_assumptions -conflict` / `-dead_end` clean (`-dead_end` returns `no_dead_end`); `neg_sanity` all CEX
- [ ] CP1 recorded PASS in `results/<cfg_dir>_pitfall_guard.md` before the first compile
- [ ] Gate 4b (G1–G17) and CP2 PASS in `results/<cfg_dir>_gate4b.md` / `_pitfall_guard.md` before any `prove`

### Properties
- [ ] Every assertion has a SPEC_ID comment; naming `asm_` / `ast_` / `cov_`
- [ ] Liveness bounded only, bound from the spec
- [ ] Default / reset values per Q8 context; parameter-based expected values
- [ ] Negative checks for disabled / masked / lower-priority / restricted paths
- [ ] Related covers (witness + precondition) all covered
- [ ] `resources/sva_coding_rules.md` applied: overlap / pairing via `aux_` helper (R1), equality form and both output values covered (R2), no open-ended consequent (R3), no implication in covers (R7), one clock per property (R9)
- [ ] `analyze` language mode recorded in `verification_plan.md` (R11)

### Runs and Sign-Off
- [ ] Each flow has its RUNCMD; one `<cfg_dir>` per configuration
- [ ] Results reported with status and depth; no undetermined counted as proven
- [ ] CP3 PASS in `results/<cfg_dir>_pitfall_guard.md` before coverage sign-off
- [ ] Every CEX triaged via `formal-cex-debug` (spec-anchored)
- [ ] Coverage measured (stimuli, COI, proof core, bound) and reviewed; waivers only at `# ADD WAIVERS HERE`
- [ ] `formal-traceability` run automatically; vPlan per Q19
- [ ] `param-spec-audit` run as the final step
