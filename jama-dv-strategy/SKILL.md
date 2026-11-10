---
name: jama-dv-strategy
description: Write an IP DV Strategy document from the spec with fixed sections (Goal, Scope/Objectives, Testbench Structure, Methodology, Stimulus, Checker, Coverage, DV Sign-off, Directory Structure), review it with the user, and optionally publish it to Jama as one item per section. Use when the user asks for a DV strategy, verification strategy, or a Jama DV strategy page.
---
# Jama DV Strategy

## Resource Loading

| When | File |
|------|------|
| Step 3 (write the document) | `resources/dv_strategy_template.md` |
| Step 3, if Q16 = formal or hybrid (style and depth reference) | `resources/formal_strategy_reference_mdma.md` |
| Step 5 (publish to Jama) | installed `jama-editor` skill (load it with the Skill tool) |

## Rules

- SPEC-ONLY: features, requirements, interfaces, parameters, defaults and bounds come from the spec (and documents the user names). RTL is used only for module and port names, if at all.
- No invented facts: any item the spec or the user does not give is written as `TBD — <what is needed, owner>` and listed in Open Items.
- Every requirement-level statement cites its source: `[§<x.y>, p<N>]`.
- Bullet-point structure in every section; tables for matrices.
- Formal content comes from the approved `*_formal_methodology.md` (`formal-methodology-select`) if it exists; otherwise ask whether to run that skill first.
- Do not write to Jama before the user approves the document (Step 4).
- Credentials: never read, print or store Jama credentials; if a Jama call returns 401/403, ask the user to fix the connection via `/mcp`.

## Upfront Questions (ask once, before Step 1)

| Q | Question | Options / default |
|---|----------|-------------------|
| Q1 | Spec source and revision | path / Jama item ID |
| Q2 | Additional documents (SoC spec, integration guide, previous-IP strategy) | list / none |
| Q3 | IP name, top module, IP version | text |
| Q4 | Verification levels in scope | block / subsystem / SoC / all |
| Q5 | Methodologies in use | UVM sim, UVM Express, formal (JasperGold), AMS/DMS, emulation, GLS |
| Q6 | Simulator and flow | adsim + Xcelium (default) / VCS / other |
| Q7 | VIPs available (protocol, vendor, version) | list / unknown |
| Q8 | Reuse: existing testbench, models, sequences | path / none |
| Q9 | Formal methodology report available? | path / run `formal-methodology-select` / not applicable |
| Q10 | Coverage targets (code: block/expression/toggle/FSM; functional) | default 100% functional, ≥95% code with waivers / user values |
| Q11 | Sign-off milestones and gates | e.g. DV0.5 / DV0.9 / DV1.0 / project-specific |
| Q12 | Repository root and DV directory convention | default `$ADIP_BLOCKS_ROOT/<ip>/dv/` |
| Q13 | Output | markdown only / markdown + Jama |
| Q14 | Jama target (if Q13 = Jama) | project ID + parent folder/item ID; item type for sections |
| Q15 | Owners / reviewers per section | names / TBD |
| Q16 | Strategy type | simulation / formal / hybrid |
| Q17 | Existing Jama section items to update (e.g. `ADTL-TXT-<n>` per section) | IDs / none (create new) |

## Procedure

### Step 1 — Read the spec

- Extract (with `§` / page): features, interfaces and protocols, clocks and resets, parameters and legal ranges, register map summary, interrupts, power modes, error handling, performance / latency numbers, safety / security requirements.
- Write `dv_strategy/<ip>_spec_inventory.md` (one row per feature: ID, feature, spec ref, interface, notes).
- Write `dv_strategy/<ip>_open_items.md` for missing or contradictory spec content.

### Step 2 — Assign methodology per feature

- For each feature choose: simulation (UVM), formal (app per the formal report), both, AMS/DMS, GLS, SoC-level, or out of scope; give a one-line reason.
- Use the formal report's D-* outcomes where they exist; do not change them without telling the user.
- Result is the Feature × Methodology matrix used in Sections 4–7.

### Step 3 — Write the document

- Fill `resources/dv_strategy_template.md` → `dv_strategy/<ip>_dv_strategy.md`, Status: DRAFT.
- The nine mandatory sections, in this order:
  1. Goal
  2. Scope / Objectives
  3. Testbench Structure
  4. Methodology
  5. Stimulus Strategy
  6. Checker Strategy
  7. Coverage Strategy
  8. DV Sign-off
  9. Directory Structure
- Plus: Revision History, References, Open Items (appendix).
- Every spec feature from Step 1 appears in at least one of Sections 5, 6 and 7, or in Scope as out of scope with a reason.
- Formal / hybrid strategy (Q16), following the reference example:
  - Goal and Scope split per formal app; Scope groups list concrete "Verify ..." bullets per register domain or path group, per configuration.
  - Section 3 becomes "Formal Environment Structure": tasks, checker bindings, configurations, black boxes.
  - Section 4: per-app flow (spec → CSV / properties → bind / load → constraints → prove → coverage), Run Flow (TCL) and Run Flow (adsim `sim.setup`), Tools table.
  - Section 5: "implicit exhaustive stimulus"; every constraint in a table `Assumption | Signal | Value | Rationale (spec §)`; Connectivity: all inputs free, conditions per CSV row.
  - Section 6: per app `Aspect | Details` table and `Property type | What it proves` table; list negative and default-value checks.
  - Avoid the reference gaps listed in `resources/formal_strategy_reference_mdma.md` (Yoda as requirement source, RTL-derived isolation without reason, empty Directory Structure, missing spec citations).

### Step 4 — Review with the user

- Self-check against the Quality Checklist; fix failures.
- Show: section list, Feature × Methodology matrix, Open Items count, TBD count.
- Ask: approve / edit / regenerate a section. On approve set `Status: APPROVED by <user> on <date>`.

### Step 5 — Publish to Jama (only if Q13 = Jama and approved)

- Load the `jama-editor` skill and follow its create / fetch-inspect-patch flow.
- Check the connection first (list projects or get the parent item); on 401/403 stop and ask the user to fix it via `/mcp`.
- Structure under the Q14 parent:
  - one folder or set item `<IP> DV Strategy v<rev>`
  - one child item per section (nine sections + Open Items), name `<n>. <Section>`, description = section content converted to HTML (tables as HTML tables).
- If the items already exist (Q17, e.g. `ADTL-TXT-1482..1489` style): fetch, show the diff, update only after the user confirms.
- Optional: relate Scope / Coverage items to the spec requirement items when the user gives their IDs.
- Record created / updated item IDs in `dv_strategy/<ip>_jama_items.md`.

## Output Files

- `dv_strategy/<ip>_spec_inventory.md`
- `dv_strategy/<ip>_dv_strategy.md`
- `dv_strategy/<ip>_open_items.md`
- `dv_strategy/<ip>_jama_items.md` (if published)

## Quality Checklist

- [ ] All nine sections present, in order, bullet-point form
- [ ] Every requirement statement has a `[§x.y, pN]` citation
- [ ] Every spec feature is covered in Stimulus, Checker or Coverage, or marked out of scope with a reason
- [ ] Feature × Methodology matrix complete; formal rows match the approved formal report
- [ ] Testbench Structure names every interface, agent / VIP, model, scoreboard and the reference model source
- [ ] Coverage targets numeric, with the waiver policy
- [ ] Sign-off criteria measurable (pass rate, coverage %, bug trend, formal proof status, review)
- [ ] Directory Structure matches Q12
- [ ] Every unknown is `TBD` and in Open Items
- [ ] No Jama write before approval
