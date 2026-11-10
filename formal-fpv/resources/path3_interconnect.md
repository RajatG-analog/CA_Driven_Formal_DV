# Path 3 — Interconnect / Crossbar Three-Pillar Approach (formal-fpv)

- Used by SKILL.md Step 2 when Step 0 selects Path 3 (multiple initiators AND multiple targets: bus fabric, crossbar, matrix).
- Source: `formal-fpv-complete.md` Part B.2 (methodology); Jasper / ABVIP syntax from the installed docs and ABVIP sources only.
- Spec-only: initiator / target lists, memory map, access-control matrix, arbitration scheme, remap modes and fairness bounds come from the spec.

## Pillars

| Pillar | Purpose | Implementation |
|--------|---------|----------------|
| 1 — Protocol | protocol-legal stimulus and protocol checks on every port | one ABVIP instance per fabric port |
| 2 — Data integrity | data from initiator i reaches target j unchanged (and back) | `jasper_scoreboard_3` per spec-legal i→j path (see `resources/path2_wrapper_scoreboard.md`) |
| 3 — Fabric rules | decode, arbitration, access control, bounded fairness, remap, default slave | hand-written SVA (bind or in the wrapper) |

## Pillar 1 — ABVIP per Port
- Fabric initiator-side port (fabric acts as subordinate towards the initiator): ABVIP in slave-verification role (AHB5-Lite wrapper `VERIFY_BLK = 2`).
- Fabric target-side port (fabric acts as manager towards the target): ABVIP in master-verification role (`VERIFY_BLK = 0`).
- Additional ABVIP components exist in `ahb5/rtl/` (`cdn_abvip_ahb5_decoder.sv`, `cdn_abvip_ahb5_slave2master_mux.sv`, monitors); their use for a fabric must follow the ABVIP user guide / examples — not verified in this skill.
- Address ranges (`SLAVEn_ADDRESS_START/END`, `ACTIVE_SLAVES`) from the spec memory map, per configuration (Q7).
- Disable an ABVIP check only with a spec statement that the feature is unsupported; record each disabled check.

## Pillar 2 — Scoreboards and Task Isolation
- One scoreboard per spec-legal initiator→target path (write data) and target→initiator path (read data).
- Isolation tasks (verification decomposition, not a spec assumption):
  - per initiator i: `task -create init_<i> -copy_all -source_task <embedded>`, then in that task assume all OTHER initiators idle (e.g. `htrans == IDLE`)
  - run the scoreboards of initiator i in task `init_<i>`
- Isolation hides contention → contention is verified in the main task (all initiators free) by Pillar 3 SVA; record this split in `verification_plan.md`.

## Pillar 3 — SVA Categories (from the spec)

| Category | Example form (spec-derived) |
|----------|-----------------------------|
| Decode | `<i>_req && <i>_addr inside {[<T_j_BASE>:<T_j_END>]} \|-> <sel_j>` (memory map per spec) |
| Default / unmapped | unmapped address → spec default-slave error response |
| Single-requester grant | sole requester for target j is granted within the spec bound |
| Contention grant validity | granted initiator is one of the current requesters and allowed by the spec matrix |
| Access restriction | spec-forbidden i→j pair: `<i>` never granted to `<j>`; spec error response returned |
| Priority / arbitration | spec scheme (fixed / round-robin): higher-priority requester wins; bounded fairness `##[1:<SPEC_BOUND>]` |
| Remap | per spec remap mode: decode follows the remapped map (separate task per remap mode) |
| Response routing | response / read data return only to the initiator that owns the transfer |
| Negative | a non-granted initiator never drives target j: `<gnt_k_j> && <k>_valid \|-> <target_j_addr> == <k>_addr` (spec address-phase timing); no transfer reaches j without a grant |

## Assumptions (interconnect-specific, spec-only)
- No-collision / address-disjoint assumptions only if the spec states them as AoU; otherwise they hide arbitration bugs.
- Remap input: pin per task to each spec remap mode (`task -create remap_<m> ...`); the default-only remap makes remap assertions vacuous.
- Static configuration (memory map registers, priority registers) only per spec "static during operation" statements, each with value covers.

## Covers
- every legal i→j pair (write and read), every forbidden pair attempt, simultaneous requests for one target, back-to-back transfers from different initiators, each remap mode, each fairness bound reached.

## Path 3 Checklist
- [ ] One ABVIP per port with the correct role and spec memory map
- [ ] Scoreboard per spec-legal path; isolation tasks documented; contention verified in the main task
- [ ] Decode, access restriction, arbitration, fairness (bounded), remap, response routing SVA present
- [ ] No-collision assumption absent unless spec AoU
- [ ] Covers for every legal / forbidden pair
