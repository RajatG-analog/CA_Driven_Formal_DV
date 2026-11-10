# Per-Feature Formal Methodology Decision Tree (Self-Contained)

- Used by `formal-methodology-select` Step 2 (classification) and Step 3 (decision).
- Self-contained port and extension of the Part B app-selection framework; no other file is needed at runtime.
- Every answer is taken from the SPEC inventory (`spec_inventory.md`) and cited as `§<x.y>` / page; never from RTL.
- Visual diagram (text tree + Mermaid): `decision_tree_diagram.md`.
- Jasper command and CSV syntax: installed docs only (`/cad/adi/apps/cadence/jasper/2025.09-p002/doc`).

## 1. Feature Classes (Step 2)

- Assign one PRIMARY class per feature and any number of OVERLAY tags.

| Class | Name | Spec evidence that selects it |
|-------|------|-------------------------------|
| C1 | Combinational connectivity | mux/demux/pinmux tables, "output X = input Y when select = S", glue, tie-offs, no clock in the feature description |
| C2 | CSR / register map | register summary table: offset, width, field, access type, reset value, protection / lock / key |
| C3 | Control / FSM | state diagram or state table, mode sequencing, timers / counters, interrupts, status set/clear, handshakes |
| C4 | Datapath / data integrity | data stored or transformed and returned: memory controller, FIFO, bridge, DMA, protocol converter, ECC / CRC / parity, arithmetic |
| C5 | Interconnect / arbitration | multiple initiators AND multiple targets, address decode, arbitration policy, access control, fairness |
| C6 | X-sensitive (overlay) | non-reset storage, outputs required defined after reset, black-boxed / analog-driven inputs, power-down / isolation outputs |
| C7 | Config-equivalence (overlay) | spec says two configurations / modes / versions must behave identically, clock-gating or ECO change, retiming, "parameter X does not change function" |
| C8 | CDC (overlay) | more than one asynchronous clock, synchronizers, handshake / gray-code crossings, async FIFOs |
| C9 | Reachability / dead code (overlay) | parameter-disabled features, reserved / unused modes, coverage closure of an existing simulation database |
| C10 | Not formal-friendly | analog / mixed-signal behaviour, software / firmware-driven sequences, real-time / physical timing, DFT-only scan behaviour, huge unabstractable state |

- Extended overlay tags (apps exist in the installed docs; no skill yet — manual):
  - S — Functional safety: safety mechanisms (ECC, parity, lockstep, watchdog) with fault-detection / diagnostic-coverage requirements
  - P — Low power: power domains, isolation, retention, UPF / power-sequencing requirements
  - Y — Security path: secret / key / debug-lock data must not reach (or must only reach) specific outputs

## 2. Decision Outcomes

| Outcome | App / method | Skill | Status |
|---------|--------------|-------|--------|
| D-CONN | Jasper Connectivity App (`check_conn`, CSV) | `formal-connectivity` (`skills/formal-connectivity/SKILL.md`) | skill |
| D-CSR | Jasper CSR App (`check_csr`, CSV) | `formal-csr` (`skills/formal-csr/SKILL.md`) | skill |
| D-FPV1 | FPV Path 1 — bind-file custom SVA | `formal-fpv` (`skills/formal-fpv/SKILL.md`) | skill |
| D-FPV2 | FPV Path 2 — FPV wrapper + ABVIP + models + `jasper_scoreboard_3` + SVA | `formal-fpv` | skill |
| D-FPV3 | FPV Path 3 — interconnect three-pillar | `formal-fpv` | skill |
| D-XPROP | X-Prop (`$isunknown` checks / X-Prop App) | `formal-xprop` (`skills/formal-xprop/instructions.md`) | skill |
| D-SEC | Jasper SEC App — config / ECO / clock-gating equivalence | none | no skill yet — manual |
| D-UNR | Jasper UNR App — coverage unreachability (needs a simulation coverage database) | none | no skill yet — manual |
| D-CDC | Jasper CDC App or the project CDC sign-off tool — separate tool / flow | none | no skill yet — manual |
| D-FSV | Jasper FSV App (safety, tag S) | none | no skill yet — manual |
| D-LPV | Jasper LPV App (low power, tag P) | none | no skill yet — manual |
| D-SPV | Jasper SPV App (security path, tag Y) | none | no skill yet — manual |
| D-SLINT | Jasper Superlint (structural pre-flight, all IPs, optional) | none | no skill yet — manual |
| D-SIM | Simulation / hybrid recommended (reason mandatory) | existing sim flow (`adsim` / `unit-test` skills if present) | outside formal skills |
| D-OOS | Out of digital verification scope (analog, physical timing, test-program items) | none | record only |

## 3. Primary Decision Tree (walk in order — first YES decides the PRIMARY outcome)

- Q0 — Is the feature digital and checkable at RTL from the spec?
  - Analog / mixed-signal transfer function, physical timing (setup/hold, slew), ATE / DFT-only scan behaviour → D-OOS (or D-SIM with an AMS model) — record reason.
  - Behaviour defined only by a software / firmware sequence of many register accesses with no bounded hardware property → D-SIM (C10) — record reason.
  - Otherwise → Q1.
- Q1 — Is the feature PURELY COMBINATIONAL (no clock, no state) routing / selection / glue? (C1)
  - YES → D-CONN.
    - Spec content to hand off: every source → destination path, the select / mode condition per path, default / idle / unselected output values, mode priority.
    - Negative categories that the hand-off must request (expected CEX or ILLEGAL rows): mode isolation, select-decode exclusivity, cross-index isolation (adjacent, first/last, mid pair), default output values, no leakage through a deselected path.
    - Large index counts (many IOs / channels) → note "generated CSV" in the hand-off; scaling is handled inside `formal-connectivity`.
    - Clocked features of the same IP continue down the tree separately.
  - NO → Q2.
- Q2 — Is the feature a MEMORY-MAPPED REGISTER MAP whose offsets, reset values, access types or protection must be signed off? (C2)
  - YES → D-CSR (separate CSR run).
    - Hand-off: register-table sections, bus protocol per spec, protection conditions, HW-update fields, bus-error behaviour.
    - Functional effect of register fields (what the field controls) is NOT covered by the CSR app → continue that part at Q3–Q5.
  - NO → Q3.
- Q3 — Is the feature an INTERCONNECT / CROSSBAR (multiple initiators AND multiple targets with decode + arbitration)? (C5)
  - YES → D-FPV3.
    - Pillar 1: ABVIP per initiator / target port for protocol compliance (assumptions on inputs, checks on outputs).
    - Pillar 2: scoreboard per initiator → target path; one Jasper task per initiator with all other initiators constrained idle (the scoreboard does not model multi-initiator contention).
    - Pillar 3: SVA for decode / aliasing / remap (separate task per remap state), single-requester grant, contention grant validity, restricted access never granted + error response, error-response propagation, unmapped address → default-slave error, bounded fairness (pairwise per arbiter, bound from spec).
    - Spec items required: address map, access-control matrix, arbitration policy + bound, remap modes.
  - NO → Q4.
- Q4 — Does the spec require END-TO-END DATA INTEGRITY through storage or transformation? (C4)
  - YES → D-FPV2, then apply the complexity gate (Section 5).
    - Environment: wrapper with ABVIP initiator per bus, behavioural memory model(s), reference model(s) (ECC / CRC / transform) written from the spec, `jasper_scoreboard_3`, SVA, constraint module.
    - Scoreboard gating: only transactions whose output is a pure function of the input (e.g. full-word writes; partial / read-modify-write transfers change data and need the reference model path).
    - Configuration registers that steer the datapath: cut and drive as free variables with stability assumptions during transactions (spec "static during operation") plus reachability covers for every spec-legal value.
    - Error injection (ECC / parity): free error mask XOR-ed on stored data, constrained by the spec correctable / detectable error counts, zero during writes.
    - Memory depth / data width beyond the rubric thresholds → abstraction (`elaborate -abstract_ram`, memory / FIFO proof-accelerator models) or D-SIM / hybrid.
  - NO → Q5.
- Q5 — Is the feature CONTROL logic: FSM, mode sequencing, timers / counters, interrupts, status, handshakes, error responses? (C3)
  - YES → D-FPV1.
    - Bind-file SVA: spec state diagram → assertions on spec-observable outputs, status / interrupt set / clear / mask / priority, counter reload / wrap / expiry, bounded liveness with the spec bound, reset / default values, negative checks.
    - Wide timers / terminal counts beyond the rubric threshold → counter abstraction note or bounded sign-off.
  - NO → Q6.
- Q6 — None of Q1–Q5 matched.
  - Feature is only an overlay concern (C6–C9, S/P/Y) → no primary outcome; overlays decide.
  - Otherwise → spec gap (feature not described well enough to classify) → `spec_gaps.md`, ask the user.

## 4. Overlay Decisions (apply to EVERY feature after the primary decision; not exclusive)

| Overlay trigger (from spec) | Outcome | Notes for the report |
|-----------------------------|---------|----------------------|
| C6 — outputs must be defined after reset; non-reset storage; black-boxed / analog-driven inputs; isolation outputs | D-XPROP | one X-Prop session per IP; reuses the FPV clocks / resets / filelist; separate from the CSR session |
| C7 — two configurations / modes / versions must be equivalent; clock-gating or ECO change; retiming | D-SEC | name spec (golden) and implementation designs and the mapping; no skill yet — manual |
| C9 — coverage closure of an existing simulation database; parameter-disabled / reserved features | D-UNR | needs a simulation coverage database; otherwise use FPV / formal coverage (`check_cov`) of D-FPV*; no skill yet — manual |
| C8 — more than one asynchronous clock domain | D-CDC | separate tool / flow; FPV still runs per synchronous domain; no skill yet — manual |
| S — spec diagnostic-coverage / fault-detection requirement | D-FSV | functional check of the safety mechanism itself stays in D-FPV*; no skill yet — manual |
| P — power domains / isolation / retention | D-LPV | no skill yet — manual |
| Y — data must not leak to / must only reach given outputs | D-SPV | no skill yet — manual |
| Any IP (optional pre-flight) | D-SLINT | structural lint before formal bring-up; no skill yet — manual |

- Parameter-dependent features always carry a configuration entry in the config matrix (Section 6) regardless of outcome.

## 5. Complexity Gate (after the primary decision)

- Score the feature with `complexity_rubric.md`.
- LOW / MEDIUM → keep the outcome.
- HIGH → keep the formal outcome AND record the abstraction / black-box / bounded-proof plan; mark "hybrid candidate".
- VERY HIGH, or a rubric override rule fires → change the outcome to D-SIM (or "D-FPV* bounded bug-hunt + D-SIM sign-off" = hybrid) with the reason.
- Valid D-SIM / hybrid reasons (cite the spec item):
  - deep memories without an acceptable abstraction (memory content is the property)
  - long latencies / bounds beyond the practical proof depth
  - analog / mixed-signal behaviour
  - software / firmware-driven sequences
  - huge state (wide arithmetic, large caches, many outstanding transactions) without a proof-accelerator model
  - spec gives no bound / no reference behaviour (also a spec gap)

## 6. Configuration Matrix Rules

- One row per spec parameter / configuration option: name, spec §, legal range, default, values to run.
- Values to run per parameter: spec default, minimum, maximum, and every value that enables / disables a feature (one value per value class).
- Cross only parameters the spec couples (shared feature or dependent range); otherwise sweep one at a time around the default.
- Default / reset-value context: IP defaults and, if the user gives one, SoC-context values (sources only from the spec or the user).
- Each run configuration becomes a `<cfg_dir>` in the downstream skills.

## 7. Run Order (default)

- 0. (optional) D-SLINT pre-flight.
- 1. D-CONN → `formal-connectivity`.
- 2. D-CSR → `formal-csr`.
- 3. D-FPV1 / D-FPV2 / D-FPV3 → `formal-fpv` (one environment per path; combinations allowed).
- 4. D-XPROP → `formal-xprop`.
- 5. Manual apps in this order when selected: D-SEC, D-CDC, D-FSV, D-LPV, D-SPV, D-UNR (UNR last; it needs coverage from earlier runs / simulation).
- 6. `formal-traceability` (consolidated across all app outputs).
- 7. `formal-vplan` (NOW / LATER / NOT NEEDED).
- 8. `param-spec-audit` (always last).
- D-SIM items are handed to the simulation owner in parallel; list them in the report.
