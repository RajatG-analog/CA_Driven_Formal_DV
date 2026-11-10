# <IP> DV Strategy

- Document: `<ip>_dv_strategy.md`, revision `<rev>`
- Status: DRAFT
- Spec: `<spec name>`, revision `<spec rev>`
- Owners / reviewers: `<names | TBD>`

## Revision History

| Rev | Date | Author | Change |
|-----|------|--------|--------|
| 0.1 | `<date>` | `<author>` | Initial draft from spec `<rev>` |

## 1. Goal

- What DV must demonstrate for this IP release (one to three bullets, e.g. "all spec features of `<ip>` v`<x>` verified at block level before RTL freeze").
- Target milestone(s) and the integration context (standalone IP / SoC `<name>`).
- Quality target: bug-free at the sign-off gate defined in Section 8.

## 2. Scope / Objectives

- In scope:
  - Features (from the spec inventory): `<feature ID — name [§x.y]>`
  - Configurations / parameters: `<param — values to verify [§x.y]>`
  - Verification levels: `<block | subsystem | SoC>`
- Out of scope (with reason and owner): analog behaviour, physical timing, DFT/ATE, features verified at SoC level, etc.
- Objectives (measurable):
  - every in-scope feature has stimulus, a checker and coverage
  - coverage targets of Section 7 met
  - formal sign-off items of Section 4 proven or bounded with a recorded bound
- Assumptions and dependencies: spec revision, VIP availability, model delivery, RTL drops.

## 3. Testbench Structure

- Block diagram (text or draw.io reference): DUT, interfaces, agents, models, scoreboard, coverage collector, register model.
- Components:

| Component | Type | Interface / protocol | Active / passive | Source (VIP / reuse / new) |
|-----------|------|----------------------|------------------|----------------------------|
| `<agent>` | UVM agent / VIP | `<APB/AHB/AXI/...>` | active | `<vendor, version>` |
| `<model>` | reference model | — | — | written from spec `[§x.y]` |
| `<scoreboard>` | scoreboard | — | — | new |
| `<ral>` | register model | — | — | generated from `<register source>` |

- Clocks and resets: domains, frequencies / ratios and reset sequencing from the spec.
- Configuration objects and the parameter-configuration matrix.
- Formal environments (if any): one line per environment (connectivity / CSR / FPV path / X-prop), pointing to the formal report.

## 4. Methodology

- Approach: `<constrained-random UVM | UVM Express | directed | formal | hybrid>`.
- Simulator and flow: `<adsim + Xcelium | ...>`, regression manager `<vManager | ...>`.
- Feature × Methodology matrix:

| Feature ID | Feature | Sim | Formal (app / path) | Other (AMS, GLS, SoC) | Reason |
|------------|---------|-----|---------------------|-----------------------|--------|
| F1 | `<name>` | Y | D-CSR | — | `<reason>` |

- GLS / power-aware / AMS plan if applicable; otherwise "not applicable" with reason.
- Bug tracking: `<Jira project>`; triage process.

## 5. Stimulus Strategy

- Per interface: sequences / sequence library, legal ranges and constraints (from spec), error injection.
- Per feature: basic, corner, error and stress scenarios; concurrency / back-pressure; reset during traffic; low-power entry/exit.
- Test list summary (name — feature IDs — type: directed / random / formal).
- Configuration sweep: values per parameter (default, min, max, each feature-enabling value).

## 6. Checker Strategy

- Scoreboard / reference-model checks: what is compared, at which interface, ordering rules.
- Protocol checkers: VIP / ABVIP assertions per interface.
- Assertions (SVA): interface, control, FSM, interrupt, reset-value checks; bind location.
- Register checks: reset values, access types, protection (sim RAL and/or formal CSR app).
- Error / negative checks: illegal accesses, error responses, default-value checks.
- End-of-test checks: no outstanding transactions, empty queues, no unexpected interrupts.

## 7. Coverage Strategy

- Functional coverage: covergroups per feature / interface / register; crosses (only spec-coupled items); assertion covers.
- Code coverage: block, expression, toggle, FSM; scope (DUT only) and exclusions.
- Formal coverage: `check_cov` stimuli / COI / proof core per formal environment.
- Targets:

| Metric | Target | Waiver policy |
|--------|--------|---------------|
| Functional | `<100%>` | reviewed waiver per bin |
| Code (block / expression / toggle / FSM) | `<≥95% each>` | reviewed exclusion file |
| Assertion / cover | 100% proven or hit | reviewed |

- Coverage-to-feature mapping in the vPlan (`formal-vplan` / vManager vplanx).

## 8. DV Sign-off

| Gate | Criteria |
|------|----------|
| `<DV0.5>` | TB complete, smoke tests pass, vPlan reviewed |
| `<DV0.9>` | all tests written, ≥`<x>`% pass, coverage ≥`<y>`%, no open critical bugs |
| `<DV1.0>` | 100% regression pass over `<N>` seeds, coverage targets met or waived, formal properties proven / bounded, all bugs closed or deferred with agreement, reviews signed |

- Required reviews: vPlan, coverage waivers, formal sign-off, final report.
- Deliverables: regression report, coverage report, formal results, traceability matrix, open-bug list.

## 9. Directory Structure

```text
$ADIP_BLOCKS_ROOT/<ip>/dv/
├── tb/            testbench top, env, agents, scoreboard, models
├── tests/         test classes / test list
├── seq/           sequence library
├── sva/           assertions and bind files
├── cov/           covergroups, coverage exclusions
├── ral/           register model
├── vplan/         verification plan
├── formal/        formal environments (<formal_dir>/<cfg_dir>)
├── sim/           sim.setup, run scripts
└── docs/          DV strategy, reports
```

- Adjust to the repository convention given by the user (Q12).

## References

- `<spec name, rev>`
- `<other documents>`

## Appendix — Open Items

| ID | Item | Section | Needed from | Status |
|----|------|---------|-------------|--------|
| OI-1 | `<missing spec content>` | `<n>` | `<owner>` | open |
