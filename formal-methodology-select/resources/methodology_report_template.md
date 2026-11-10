# Methodology Report Template (`<out_dir>/<ip>_formal_methodology.md`)

- Used by `formal-methodology-select` Step 5.
- Every decision row cites the spec (`§<x.y>` / page) and the decision-tree node that fired (e.g. `Q4→D-FPV2`).
- Optional HTML (`<ip>_formal_methodology.html`) only when the user asks (Upfront Q11); same content, generated locally (no external rendering services).
- `spec_gaps.md` format is in Section 10 of this template.

## 1. Header

- IP / top: `<ip>` / `<top_module>` (top name: spec or `binding-only` from RTL)
- Spec: `<file / Jama ID>` rev `<rev>`; inventory: `spec_inventory.md`
- Upfront answers: Q1–Q14 table (copy)
- Status: DRAFT → APPROVED by `<user>` on `<date>` (Step 6)

## 2. Executive Summary

- Features in scope: `<N>`; formal `<n1>`; simulation / hybrid `<n2>`; out of scope `<n3>`
- Apps selected: `<D-CONN, D-CSR, D-FPV1, …>`
- Skills to run (order): `<list>`
- Manual (no skill yet): `<D-SEC / D-UNR / D-CDC / …>`
- Open spec gaps: `<count>` (`<k>` blocking)

## 3. Feature → Class → App → Skill Matrix

| Feature ID | Feature | Primary class | Overlays | Tree path | Outcome | Skill / flow | Complexity | Spec § | Notes |
|------------|---------|---------------|----------|-----------|---------|--------------|------------|--------|-------|
| F-001 | `<pinmux routing>` | C1 | C6 | Q1→D-CONN | D-CONN | `formal-connectivity` | LOW | §`<x.y>` | — |
| F-002 | `<register map>` | C2 | — | Q2→D-CSR | D-CSR | `formal-csr` | LOW | §`<x.y>` | field effects → F-003 |
| F-003 | `<control FSM>` | C3 | C6 | Q5→D-FPV1 | D-FPV1 | `formal-fpv` Path 1 | MEDIUM | §`<x.y>` | — |
| F-004 | `<SRAM + ECC>` | C4 | S | Q4→D-FPV2 | D-FPV2 (+D-FSV manual) | `formal-fpv` Path 2 | HIGH | §`<x.y>` | abstraction plan §5 |
| F-005 | `<firmware boot>` | C10 | — | Q0→D-SIM | D-SIM | simulation | — | §`<x.y>` | reason: SW-driven sequence |

## 4. Complexity Ratings

- Row format and scores per `complexity_rubric.md` Section 5; list overrides and `?` dimensions.

## 5. Abstraction / Black-Box Plan

| Feature ID | Abstracted item | Method | Reason | Coverage lost | Reachability covers |
|------------|-----------------|--------|--------|---------------|---------------------|
| F-004 | `<data RAM>` | memory model / `-abstract_ram` | K2 = 3 | `<content of unused addresses>` | `<cov_* list>` |

## 6. Run Order

| Order | Outcome(s) | Skill / flow | Features | Depends on | Status |
|-------|------------|--------------|----------|------------|--------|
| 1 | D-CONN | `formal-connectivity` | F-001 | — | PLANNED |
| 2 | D-CSR | `formal-csr` | F-002 | — | PLANNED |
| 3 | D-FPV1 / D-FPV2 / D-FPV3 | `formal-fpv` | F-003, F-004 | filelist | PLANNED |
| 4 | D-XPROP | `formal-xprop` | all outputs | FPV clocks / resets | PLANNED |
| 5 | D-SEC / D-CDC / D-FSV / D-LPV / D-SPV / D-UNR | manual (no skill yet) | `<list>` | `<list>` | PLANNED / NOT SELECTED |
| 6 | — | `formal-traceability` (consolidated) | all | runs 1–5 | PLANNED |
| 7 | — | `formal-vplan` | all | `req_extraction.csv` | NOW / LATER / NOT NEEDED |
| 8 | — | `param-spec-audit` | all parameters | runs 1–5 | PLANNED (last) |

## 7. Configuration Matrix

| `<cfg_dir>` | `<PARAM_A>` | `<PARAM_B>` | Context (IP / SoC) | Reason (value class) | Used by outcomes | Spec § |
|-------------|-------------|-------------|--------------------|----------------------|------------------|--------|
| default | `<def>` | `<def>` | IP | spec default | all | §`<x.y>` |
| `<cfg_min>` | `<min>` | `<def>` | IP | minimum | D-FPV1, D-CONN | §`<x.y>` |

## 8. Hand-Off Packages (pre-filled answers for downstream upfront questions)

| Skill | Features | Pre-filled answers | Still to ask in that skill |
|-------|----------|--------------------|----------------------------|
| `formal-connectivity` | F-001 | spec, sections, top, configs, defaults context, run flow | `<list>` |
| `formal-csr` | F-002 | spec, register sections, bus protocol, protection, bus-error behaviour | `<list>` |
| `formal-fpv` | F-003, F-004 | spec, path decision (Step 0 = this report), features, clocks, resets, configs, ABVIP protocols | `<list>` |
| `formal-xprop` | outputs | top, clocks, resets, filelist | `<list>` |

## 9. Simulation / Hybrid and Out-of-Scope Items

| Feature ID | Outcome | Reason (rubric / spec) | Recommended activity | Owner |
|------------|---------|------------------------|----------------------|-------|
| F-005 | D-SIM | SW-driven sequence §`<x.y>` | directed / UVM test | `<owner or TBD>` |

## 10. Spec Gaps (`spec_gaps.md` format)

| GAP ID | Spec § | Question | Impact (features / outcomes blocked) | Blocking? | Status |
|--------|--------|----------|--------------------------------------|-----------|--------|
| GAP-001 | §`<x.y>` | `<bound for "eventually ack"?>` | F-003 bounded liveness | yes | OPEN / ANSWERED by `<who>` on `<date>` |

## 11. Open Questions (non-gap decisions for the user)

| # | Question | Options | Default if unanswered |
|---|----------|---------|-----------------------|
| OQ-1 | `<hybrid for F-004?>` | formal bounded + sim / formal only | formal bounded + sim |

## 12. Approval Record

- Plan approved: yes / changes requested (`<changes>`)
- vPlan: NOW / LATER / NOT NEEDED
- Manual apps acknowledged: `<list>`
