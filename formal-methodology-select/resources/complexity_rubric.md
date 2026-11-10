# Formal-Friendliness / Complexity Rubric

- Used by `formal-methodology-select` Step 4 and the complexity gate of `decision_tree.md` Section 5.
- Inputs come from the SPEC inventory only (storage sizes, widths, depths, bounds, parameter ranges); RTL flop counts are not used.
- Thresholds below are DEFAULT HEURISTICS of this skill, not tool limits; the user may override them (record overrides in the report).
- Unknown value in the spec → score the dimension 3 (worst case), mark `?`, and add a spec gap.

## 1. Dimensions (score 0–3 each)

| # | Dimension | 0 | 1 | 2 | 3 |
|---|-----------|---|---|---|---|
| K1 | Storage state from spec (feature registers + counters + FIFO / buffer bits, excluding large memories) | ≤ 64 bits | ≤ 512 bits | ≤ 4 Kbit | > 4 Kbit or `?` |
| K2 | Memory depth (entries of the largest RAM / ROM / FIFO in the feature) | none | ≤ 16 | ≤ 256 (abstraction advised) | > 256 (abstraction mandatory) or `?` |
| K3 | Latency / bound (deepest spec "within N" / pipeline latency, in cycles of the fastest clock) | ≤ 16 | ≤ 64 | ≤ 256 | > 256, unbounded, or not stated |
| K4 | Counter / timer width needing full range (spec terminal count) | none or ≤ 8 bits | ≤ 16 bits | ≤ 24 bits (counter abstraction advised) | > 24 bits |
| K5 | Abstraction / black-box need | none | `stopat` / cut of a few signals | black box of sub-blocks or memory abstraction | analog / macro model needed or behaviour behind a black box is the property |
| K6 | Parameter sweep count (run configurations from the config matrix) | 1 | 2–3 | 4–8 | > 8 |
| K7 | Datapath arithmetic (multiply / divide / CRC width) | none | ≤ 8 bits | ≤ 32 bits (proof-accelerator model advised) | > 32 bits |
| K8 | Concurrency (independent interfaces / initiators / outstanding transactions) | 1 | 2 | 3–4 | > 4 |

## 2. Rating

| Total (K1–K8) | Rating | Meaning | Default action |
|---------------|--------|---------|----------------|
| 0–5 | LOW | formal-friendly | full unbounded proof expected |
| 6–10 | MEDIUM | formal with care | full proof expected; plan covers + engine / ProofGrid time |
| 11–15 | HIGH | formal with mandatory abstraction | record abstraction plan; bounded sign-off allowed with spec-derived depth; hybrid candidate |
| ≥ 16 | VERY HIGH | not formal-friendly as a whole | D-SIM or hybrid (formal bug-hunt on sub-features + simulation sign-off) |

## 3. Override Rules (change the outcome regardless of total)

- K2 = 3 AND K3 = 3 → VERY HIGH (deep memory with long latency).
- K5 = 3 because analog / mixed-signal behaviour is the property → D-OOS or D-SIM with an AMS model.
- Behaviour defined only by a software / firmware sequence → D-SIM.
- K3 "not stated" for a liveness requirement → spec gap; the property is blocked until the bound is given (no invented bound).
- Any `?` dimension → rating is provisional; report it as "provisional — pending GAP-NNN".

## 4. Abstraction Options to Record (look up syntax in the installed docs)

| Situation | Option | Document |
|-----------|--------|----------|
| Large RAM where content is not the property | `elaborate -abstract_ram`, black box with `elaborate -bbox_m` | `jasper_command_reference.pdf` |
| RAM / FIFO content matters | memory / FIFO models | `proof_accelerators/jasper_model_ram.pdf`, `jasper_model_mpram.pdf`, `jasper_model_mem.pdf`, `jasper_model_fifo.pdf` |
| End-to-end data integrity | scoreboard | `proof_accelerators/jasper_scoreboard_3.pdf` |
| Wide multiply / divide | arithmetic models | `proof_accelerators/jasper_model_multiplier.pdf`, `jasper_model_divider.pdf` |
| Cut a signal / drive as free input | `stopat`, `abstract` | `jasper_command_reference.pdf` |
| Engine choice for hard properties | Proof Orchestration / manual engine guidelines | `jasper_engine_selection.pdf` |

- Every abstraction is recorded with: what is abstracted, why, which spec features lose coverage, which covers prove the remaining reachability.

## 5. Report Row Format

| Feature ID | K1 | K2 | K3 | K4 | K5 | K6 | K7 | K8 | Total | Rating | Override | Abstraction plan | Spec evidence |
|------------|----|----|----|----|----|----|----|----|-------|--------|----------|------------------|---------------|
| F-001 | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 0 | 2 | LOW | — | none | §3.2, §4.1 |
