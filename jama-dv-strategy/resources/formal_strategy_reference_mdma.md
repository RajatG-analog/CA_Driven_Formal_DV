# Reference Example — Formal DV Strategy (ADIP MDMA, Jama export)

- Source: `/home/rgulghan/MDMA_Formal_Verification_reference.doc` (Jama "Export to Word", 14 pages).
- Use this as the style and depth reference for a FORMAL-only DV strategy (CSR App + Connectivity App). Do not copy MDMA names into another IP.
- Content below is a structural summary; read the source file for full detail.

## Jama Structure Observed

- One Jama text item per section; each item has its own ID (`ADTL-TXT-<n>`, `GID-<n>`):

| Section | Jama item (MDMA) |
|---------|------------------|
| Goal | ADTL-TXT-1482 |
| Scope / Objectives | ADTL-TXT-1483 |
| Methodology | ADTL-TXT-1484 |
| Stimulus Strategy | ADTL-TXT-1485 |
| Checker Strategy | ADTL-TXT-1486 |
| Coverage Strategy | ADTL-TXT-1487 |
| DV Sign Off | ADTL-TXT-1488 |
| Directory Structure | ADTL-TXT-1489 |

- No separate "Testbench Structure" item; the formal environment (checker binding, constraints) is described inside Methodology and Checker Strategy.

## Patterns to Reuse

- Goal: one numbered goal per formal app (CSR, Connectivity), each naming the tool, the register domains / path groups, and the configurations; a final numeric goal (100% proven, 0 falsified, 0 undetermined).
- Scope / Objectives: split per app; per app numbered groups (register domain, or path group: bus decode, bus master channels, datapath, peripheral IO, control / status, clock / reset, configuration coverage), each a list of "Verify ..." bullets naming concrete fields / signals.
- Methodology: per app a numbered flow (source → CSV → bind / load → constraints → prove → coverage) and the run steps (analyze, elaborate with parameters, clock, reset, constraints, load, prove, coverage), plus a Tools table (tool → purpose).
- Stimulus Strategy (formal): state that stimulus is implicit and exhaustive; list every constraint as a table `Assumption | Signal | Value | Rationale`, grouped (bus protocol, engine isolation, external interface quiescence). For Connectivity: all inputs free, conditions per CSV row, no global assumptions.
- Checker Strategy: per app a table `Aspect | Details` (checker, approach, binding, specification source, property generation) and a table `Property type | What it proves`.
- Coverage Strategy: coverage type, scope (COI of all assertions), per configuration, numeric target with exclusions.
- DV Sign Off: measurable bullets per app (100% proven, coverage %, disabled covers documented).

## Gaps in the Reference (fix in new documents)

- Requirement source: CSR goal and objectives cite the Yoda register map; per this skill set the spec register table is the requirement source (Yoda / CSV only as generated collateral, cross-checked by `param-spec-audit`).
- Isolation constraints (stopat + assume 0 on internal engine signals) are RTL-derived; record each with a spec reason or as a limitation, and add covers proving the registers are still reachable.
- Run steps are titled "Simulation Flow" but are Jasper TCL steps; title them "Run Flow (TCL)" / "Run Flow (adsim sim.setup)".
- Connectivity "Coverage" step only lists `check_cov -measure`; also state the coverage types and the per-configuration report.
- Negative / default-value connectivity checks are not listed; add them (see `formal-connectivity`).
- Directory Structure item is empty; always fill it.
- Section numbering is inconsistent (heading numbers, list item "10."); use the template numbering.
- No Testbench Structure section; for formal, write it as "Formal Environment Structure" (tasks, checker bindings, configurations).
- No spec citations (`§` / page) on requirements; add them.
