---
name: formal-methodology-select
description: Spec-only front door for formal verification of a new IP (JasperGold 2025.09) — read the whole spec, build a cited feature / interface / clock / memory / FSM / register / parameter / latency / error / test-mode inventory, classify every feature, walk a per-feature decision tree to pick the Jasper app (Connectivity, CSR, FPV Path 1/2/3, X-Prop, SEC, UNR, CDC, FSV/LPV/SPV/Superlint) or recommend simulation / hybrid, rate formal complexity, write a methodology report (feature→app→skill matrix, run order, config matrix, spec gaps, open questions), get approval and route to formal-connectivity, formal-csr, formal-fpv, formal-xprop, formal-traceability, formal-vplan and param-spec-audit. Use when a new IP spec arrives and the DV / formal methodology is not yet known, or the user asks which formal app / methodology fits an IP or feature.
---

# Formal Methodology Select Skill — Spec-Driven App Selection and Routing (Spec-Only)

**Resource loading (MANDATORY):**
- `resources/...` paths are relative to this skill's directory (the directory containing this SKILL.md).
- Resources are NOT preloaded. At each step that says "Read `resources/<file>`", open that file with View BEFORE writing any output for the step.
- Never write the inventory, classification, decision, rating or report from memory when a resource file exists for it.
- The decision tree is self-contained in `resources/decision_tree.md`; `formal-fpv-complete.md` is NOT needed at runtime.

| Step | Resource file (read when reaching the step) |
|------|---------------------------------------------|
| Step 1 — spec inventory | `resources/spec_inventory_template.md` |
| Step 2 — feature classification (Section 1) | `resources/decision_tree.md` |
| Step 3 — per-feature decision, overlays, config matrix, run order (Sections 2–4, 6, 7) | `resources/decision_tree.md` |
| Step 4 — complexity rating + gate (with `decision_tree.md` Section 5) | `resources/complexity_rubric.md` |
| Step 5 — methodology report + `spec_gaps.md` | `resources/methodology_report_template.md` |

## When to Use
- Activate when:
  - A new IP spec arrives and the DV / formal methodology is not yet decided
  - The user asks which Jasper app / formal methodology fits an IP or a feature
  - The user asks whether a feature should be verified with formal, simulation or both
  - `formal-fpv` Step 0 finds no methodology report (it runs this skill first)
- Hand off instead:
  - Methodology already approved (report exists) → go directly to the routed skill
  - CEX debug → `formal-cex-debug`

## Upfront Questions (ASK ONCE, BEFORE ANY WORK — MANDATORY)
- Ask ALL of these in ONE question round (AskUserQuestions) before Step 0.
- Do not re-ask later; reuse the answers in every step and pass them to the routed skills (hand-off packages, Step 6).
- If an answer is "not known yet", continue and mark the dependent output as TODO.

| # | Question | Options / format | Used in |
|---|----------|------------------|---------|
| Q1 | Spec source (+ revision) | PDF / Jama / md path | all steps |
| Q2 | Additional documents | protocol standards, integration guide, SoC spec, none | Step 1 |
| Q3 | IP name and top module (optional) | `<ip>`, `<top_module>` or "not known" | report, hand-off |
| Q4 | RTL filelist (optional; compile / names only) | path to `filelist.f` or none | hand-off |
| Q5 | Scope | whole spec / listed features or sections | Step 1–3 |
| Q6 | Parameter configurations | known list (`<cfg_dir>`: `<PARAM>=<VAL>`) / derive from spec | Step 3 config matrix |
| Q7 | Default / reset-value context | IP defaults / SoC-context values / both | config matrix, hand-off |
| Q8 | Verification goal | formal sign-off / formal bug-hunt / formal + simulation hybrid | Step 4 gate |
| Q9 | Existing simulation environment / coverage database | path or none | D-SIM hand-off, D-UNR |
| Q10 | Apps available / licensed (if known) | Connectivity, CSR, FPV, X-Prop, SEC, UNR, CDC, FSV, LPV, SPV, Superlint / not known | Step 3 |
| Q11 | Report format | md / md + HTML | Step 5 |
| Q12 | Downstream run flow defaults | A. TCL / B. adsim / C. both; adsim block name; GUI / batch | hand-off |
| Q13 | SoC context for the final param audit | SoC RTL glob / SoC CSV / not available | Step 6 |
| Q14 | Output / formal directory | e.g. `$ADIP_BLOCKS_ROOT/<ip>/dv/formal/<formal_dir>` | all outputs |

- Only spec-gap questions are asked later (Step 5), and the plan approval + vPlan timing round (Step 6).

## Inputs Required

| Input | Description | Example |
|-------|-------------|---------|
| **Spec** | IP specification — the ONLY requirement source | `<ip>_spec.pdf` |
| **Additional docs** | Protocol standards / integration guide referenced by the spec | `AMBA APB4` |
| **RTL filelist** | Optional; compile / top-name only for the hand-off | `filelist.f` |
| **Output dir** | Where the methodology collateral is written | `<formal_dir>/methodology/` |

**SPEC-ONLY PRINCIPLE (MANDATORY):**
- The specification is the ONE AND ONLY source for features, interfaces, clocks / resets, memories, FSMs, registers, parameters, datapaths, latencies, error / safety behaviour and test modes.
- RTL is optional and read ONLY for:
  - the filelist / compile dependencies passed to the routed skills
  - the top-level module name and port names needed for the hand-off (record "binding-only")
- NEVER:
  - classify a feature, pick an app or rate complexity from RTL structure, RTL flop counts, RTL comments or RTL FSM encodings
  - add a feature, state, bound or parameter value that the spec does not state
  - use Yoda `.yda` or generated IP-XACT as the register requirement source
- Spec missing or ambiguous → log the item in `spec_gaps.md` and ASK the user. Do not fill it from RTL.
- Deriving expectations from the design under test makes verification circular (RTL bugs become "expected" behaviour).

**TOOL DOCUMENTATION (MANDATORY):**
- For Jasper app capabilities and command syntax, always refer to the installed Cadence docs at `/cad/adi/apps/cadence/jasper/2025.09-p002/doc`.
- Docs win over memory and over examples in this skill.
- Consult (all files below exist in the installed doc directory):

| Outcome / topic | User guide | Official example |
|-----------------|------------|------------------|
| FPV app flow, apps overview | `jasper_apps_userguide.pdf` | `example_jasper_apps/FPV/` |
| All TCL commands (`analyze`, `elaborate -abstract_ram` / `-bbox_m`, `stopat`, `abstract`, `check_conn`, `check_csr`, `check_xprop`, `check_unr`) | `jasper_command_reference.pdf` | — |
| D-CONN — Connectivity App | `jasper_conn_userguide.pdf` | `example_jasper_apps/CONN/` |
| D-CSR — CSR App | `jasper_csr_userguide.pdf` | `example_jasper_apps/CSR/` |
| D-XPROP — X-Prop App | `jasper_xprop_userguide.pdf` | `example_jasper_apps/XPROP/` |
| D-SEC — Sequential Equivalence Checking App (incl. clock-gating sign-off) | `jasper_sec_userguide.pdf` | `example_jasper_apps/SEC/` |
| D-UNR — Coverage Unreachability App (needs a simulation coverage database) | `jasper_unr_userguide.pdf` | `example_jasper_apps/UNR/` |
| Formal coverage (`check_cov`) | `jasper_cov_userguide.pdf` | `example_jasper_apps/COV/` |
| D-CDC — CDC App | `jasper_cdc_userguide.pdf`, `jasper_cdc_reference.pdf` | `example_jasper_apps/CDC/` |
| D-SLINT — Superlint | `jasper_superlint_userguide.pdf`, `jasper_superlint_reference.pdf` | `example_jasper_apps/Superlint/` |
| D-FSV — Functional Safety | `jasper_fsv_userguide.pdf` | `example_jasper_apps/FSV/` |
| D-LPV — Low Power | `jasper_lpv_userguide.pdf` | `example_jasper_apps/LPV/` |
| D-SPV — Security Path | `jasper_spv_userguide.pdf` | `example_jasper_apps/SPV/` |
| Engines / hard properties | `jasper_engine_selection.pdf` | — |
| Proof accelerators (scoreboard, memory, FIFO, arithmetic models) | `proof_accelerators/jasper_scoreboard_3.pdf`, `jasper_model_ram.pdf`, `jasper_model_mpram.pdf`, `jasper_model_mem.pdf`, `jasper_model_fifo.pdf`, `jasper_model_multiplier.pdf`, `jasper_model_divider.pdf` | `example_jasper_apps/proof_accelerators/` |
| Browsable HTML docs | `HTML/` | — |

**KEY PRINCIPLES:**
- Decide per FEATURE, not per IP; one IP normally uses several apps.
- Every decision row cites the spec section and the decision-tree node that fired.
- Overlays (X-Prop, SEC, UNR, CDC, FSV, LPV, SPV) are added on top of the primary outcome; they never replace it.
- Outcomes without a skill (D-SEC, D-UNR, D-CDC, D-FSV, D-LPV, D-SPV, D-SLINT) are marked "no skill yet — manual" in the report.
- Simulation / hybrid is a valid outcome only with a written reason from the rubric or the spec.

---

## Step-by-Step Procedure

### Step 0: Setup and Spec Text Extraction
- Create the output directory (Q14) if it does not exist; temp files go to `.tmp/` with a timestamp.
- PDF spec:

```tcsh
mkdir -p .tmp
set ts = `date +%Y-%m-%d_%H%M%S`
set spec_txt = ".tmp/<ip>_spec_${ts}.txt"
pdfinfo <spec.pdf>
pdftotext -layout <spec.pdf> "${spec_txt}"
wc -l "${spec_txt}"
```

- Read `${spec_txt}` with View in consecutive `offset` / `limit` chunks until the last line; do not skip sections or appendices.
- Tables, state diagrams, timing diagrams and block diagrams: also read those pages with pdfMarkdown (max 5 pages per call).
- Jama spec: export with the Jama skills (`jama-to-docs` / `jama-editor` fetch); md spec: read directly.
- Repeat for every additional document (Q2) that the spec references for required behaviour.

### Step 1: Full Spec Read and Inventory
- Read `resources/spec_inventory_template.md` and create `<out_dir>/spec_inventory.md` from it.
- Extract, with a citation per row:
  - features, interfaces / protocols (+ revision, DUT role)
  - clocks, resets, clock domains, ratios, gating, reset sequencing
  - memories / FIFOs / buffers (depth × width, protection)
  - FSMs / state diagrams (spec state names, transitions, outputs)
  - registers (offset, fields, access, reset, protection, HW update, bus-error behaviour)
  - parameters / configurations (range, default, affected features, static or not)
  - datapaths / transformations, latency / timing requirements (bounds)
  - error handling and safety items, test / scan / debug modes, power / security items, assumptions of use
- Fill the reading log (inventory Section 14) for every section; the inventory is complete only when every section is marked read.
- Every missing value → `NOT STATED` + `GAP-NNN` in `spec_gaps.md`.

### Step 2: Feature Classification
- Read `resources/decision_tree.md` Section 1.
- Assign one primary class (C1 connectivity, C2 CSR, C3 control / FSM, C4 datapath / data integrity, C5 interconnect / arbitration, C10 not formal-friendly) and all overlay tags (C6 X-sensitive, C7 config-equivalence, C8 CDC, C9 reachability / dead code, S safety, P power, Y security) per feature.
- Split a feature when parts fall into different classes (e.g. register table → C2, the function the fields control → C3).
- Record the spec evidence for every class and tag.

### Step 3: Per-Feature Decision
- Read `resources/decision_tree.md` Sections 2–4, 6 and 7.
- Walk Q0–Q6 per feature; the first YES gives the primary outcome; record the tree path (e.g. `Q0→Q1→Q2→Q3→Q4→D-FPV2`).
- Apply every overlay of Section 4.
- Apps not available (Q10) → keep the outcome, mark "app not available" and list the alternative (other app or D-SIM).
- Build the configuration matrix (Section 6) from the parameter inventory and Q6 / Q7.
- Derive the run order (Section 7).

### Step 4: Formal-Friendliness / Complexity Rating
- Read `resources/complexity_rubric.md`.
- Score K1–K8 per feature from the spec inventory only; `?` for unknown values (scored 3, provisional, with a gap).
- Apply override rules, then the complexity gate (`decision_tree.md` Section 5):
  - HIGH → keep the formal outcome, write the abstraction / black-box / bounded-proof plan
  - VERY HIGH or override → D-SIM or hybrid with the reason
- Q8 = formal bug-hunt → HIGH features stay formal with a bounded run; Q8 = formal sign-off → HIGH features need the abstraction plan approved in Step 6.

### Step 5: Methodology Report, Spec Gaps and Open Questions
- Read `resources/methodology_report_template.md`.
- Write `<out_dir>/<ip>_formal_methodology.md`:
  - executive summary, feature → class → app → skill matrix, complexity ratings, abstraction plan
  - run order, configuration matrix, hand-off packages, simulation / hybrid / out-of-scope items
  - open questions, approval record (DRAFT)
- Write `<out_dir>/spec_gaps.md` (template Section 10).
- HTML (only if Q11 = md + HTML): generate `<ip>_formal_methodology.html` locally from the md; no external rendering services.
- Ask the open spec-gap questions in one round (AskUserQuestions); update the report with the answers (blocking gaps first).

### Step 6: Approval and Routing
- Ask in ONE round (AskUserQuestions):
  - approve the plan (matrix, run order, config matrix, abstraction plan) / request changes
  - vPlan timing: NOW / LATER / NOT NEEDED
  - acknowledge the manual outcomes (no skill yet)
- Record the answers in the report (Approval Record); status → APPROVED.
- Route in this order, only for outcomes present in the approved report; pass the hand-off package (pre-filled upfront answers + feature list + spec sections + config matrix) to each skill:

| Order | Outcome | Skill | Path (relative to `/proj/adip_digital/rgulghan/workareas/wrk_rgulghan/Handoff/`) |
|-------|---------|-------|------------------------------|
| 1 | D-CONN | `formal-connectivity` | `skills/formal-connectivity/SKILL.md` |
| 2 | D-CSR | `formal-csr` | `skills/formal-csr/SKILL.md` |
| 3 | D-FPV1 / D-FPV2 / D-FPV3 | `formal-fpv` (Step 0 consumes this report) | `skills/formal-fpv/SKILL.md` |
| 4 | D-XPROP | `formal-xprop` | `skills/formal-xprop/instructions.md` |
| 5 | D-SEC / D-CDC / D-FSV / D-LPV / D-SPV / D-UNR / D-SLINT | manual (no skill yet) — list docs + spec items in the report | — |
| 6 | all | `formal-traceability` (consolidated across all app outputs) | `skills/formal-traceability/SKILL.md` |
| 7 | all | `formal-vplan` (NOW → run; LATER → pending item; NOT NEEDED → skip) | `skills/formal-vplan/SKILL.md` |
| 8 | all | `param-spec-audit` (always last) | `skills/param-spec-audit/SKILL.md` |

- Routed skills ask only the upfront questions the hand-off package leaves open; they confirm the pre-filled answers in their single upfront round.
- Routed skills keep their own CEX debug (`formal-cex-debug`) and per-run traceability; their optional vPlan and final param-audit steps are deferred to orders 7 and 8 here (one run across all apps).
- After each routed skill: update the Run Order status (DONE / BLOCKED + reason) in the report.
- D-SIM items: hand the list (feature, reason, spec §) to the simulation owner; record in the report.

---

## Integrations with Sibling Skills

| Skill | Path | When | Interface |
|-------|------|------|-----------|
| `formal-connectivity` | `skills/formal-connectivity/SKILL.md` | D-CONN features | hand-off package: paths, conditions, defaults, configs |
| `formal-csr` | `skills/formal-csr/SKILL.md` | D-CSR features | register sections, bus protocol, protection, bus-error behaviour |
| `formal-fpv` | `skills/formal-fpv/SKILL.md` | D-FPV1/2/3 features | this report replaces its Step 0 decision; Q3 path confirmation pre-filled |
| `formal-xprop` | `skills/formal-xprop/instructions.md` | D-XPROP overlay | top, outputs in scope, clocks / resets, filelist |
| `formal-cex-debug` | `skills/formal-cex-debug/SKILL.md` | inside routed skills | — |
| `formal-traceability` | `skills/formal-traceability/SKILL.md` | order 6 | inventory + `req_extraction.csv` from routed skills, results |
| `formal-vplan` | `skills/formal-vplan/SKILL.md` | order 7 (NOW) | spec + `req_extraction.csv` |
| `param-spec-audit` | `skills/param-spec-audit/SKILL.md` | order 8 (last) | parameter inventory, config matrix, SoC context (Q13), DV dirs |

- Paths are relative to `/proj/adip_digital/rgulghan/workareas/wrk_rgulghan/Handoff/`.

## Output Files

```
<out_dir>/
├── spec_inventory.md               — Step 1 cited inventory + reading log
├── <ip>_formal_methodology.md      — Steps 2–6 report (matrix, ratings, run order, config matrix, hand-offs, approval)
├── <ip>_formal_methodology.html    — optional (Q11)
└── spec_gaps.md                    — GAP-NNN open questions and answers (shared with routed skills)
```

## Reference
- Decision tree: `resources/decision_tree.md` (self-contained port and extension of the Part B app-selection framework).
- Jasper docs: `/cad/adi/apps/cadence/jasper/2025.09-p002/doc`.
- adsim formal reference: `adsim` skill, `resources/formal.md`.

## Quality Checklist

### Spec
- [ ] Upfront questions asked once; answers recorded in the report
- [ ] Every spec section and referenced document read; reading log complete
- [ ] Every inventory row cites the spec; no feature, bound or value taken from RTL
- [ ] Every missing value is `NOT STATED` with a `GAP-NNN` entry

### Decisions
- [ ] Every feature has a primary class, overlay tags and spec evidence
- [ ] Every feature has a tree path and an outcome (or an explicit gap)
- [ ] Overlays applied to every feature; manual outcomes marked "no skill yet — manual"
- [ ] Every D-SIM / hybrid outcome has a written reason
- [ ] Complexity scored K1–K8 from the spec; overrides and `?` listed; abstraction plan for HIGH

### Report and Routing
- [ ] Matrix, run order, config matrix, hand-off packages, spec gaps and open questions present
- [ ] Plan approved (Step 6); vPlan timing recorded
- [ ] Routed in order: connectivity → CSR → FPV → X-Prop → manual apps → traceability → vPlan → param audit
- [ ] Run Order status updated after every routed skill
