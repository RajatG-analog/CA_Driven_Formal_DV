# Multi-Clock Designs — Clock and Reset Setup (formal-fpv, Step 4)

- Sources (only these; docs win over this file):
  - AN = `/cad/adi/apps/cadence/jasper/2025.09-p002/doc/AN_clocking_management.pdf` (January 2022), page numbers as printed
  - CR = `/cad/adi/apps/cadence/jasper/2025.09-p002/doc/jasper_command_reference.pdf` (2025.09), page numbers as printed (`clock` p707-715, `get_clock_info` p876, `reset` p1222-1239, `sanity_check` p1248)
  - PA = `/cad/adi/apps/cadence/jasper/2025.09-p002/doc/proof_accelerators/jasper_model_frequency_jitter.pdf`
- SPEC-ONLY:
  - clock names, edges, ratios, phase, gating, mux selects, sync/async relation and the reset per domain come from the spec / Q5 / Q6
  - RTL is read only for the port / hierarchy names used in `clock` / `reset`
  - missing ratio, phase, edge, relation or reset-domain mapping → `spec_gaps.md` + ask the user; never take it from RTL or from `clock -infer`

## Tool Model (what FPV assumes)
- Formal analysis is always done with respect to the fastest clock; all Jasper clocks are synchronous to the fastest clock and are divided by or shifted against it (AN p4).
- Declare the fastest clock as the reference / primary clock (AN p4).
- By default logic is clocked on the posedge of the fastest clock; `-both_edges` for posedge + negedge flops (AN p4).
- At least one of `clock <clk>`, `clock -none`, `clock -infer` (or the Clock Viewer) is required before `prove` / `visualize` (AN p4; CR p708).
- `clock -infer` output must be reviewed for complex clocking (AN p4); in this skill it is an audit aid only, the declaration comes from the spec.
- Clock arguments are a signal or `~signal`, never an expression; VHDL negedge: `clock {not <clk>}` unless elaborated with `-mode verilog` (CR p708).
- Undriven inputs change on the posedge of the fastest clock by default (`clock -rate -default`, CR p710); rate each slower-domain input to its spec clock.

## Decision Bullets
- Count the spec clocks (Q5); for each pair record: same frequency / integer ratio / non-integer ratio / phase / asynchronous / gated / muxed / derived.
- Identify the fastest spec clock → first `clock` command.
- Synchronous relation with a spec ratio → `-factor` (+ `-phase`) (rows 2-5 below).
- Asynchronous relation:
  - FPV of the logic inside each domain: fixed spec ratio first; range-based clocks (`-from -to`) or the frequency-jitter PA only as a later step (AN p10; PA p4-5)
  - metastability / synchronizer correctness is NOT analysed by FPV (AN p13) → D-CDC hand-off (Jasper CDC App, `jasper_cdc_userguide.pdf`; no skill yet — manual per `formal-methodology-select`) and record it in `verification_plan.md`
- Inputs belonging to a slower domain → `clock -rate <inputs> <clk>` (AN p8-9; CR p710).
- Clock mux → one run (task / `<cfg_dir>`) per spec mode with the select fixed by `assume -env` (AN p11).
- After declaration: audit with `clock -analyze`, `clock -list configuration`, `get_clock_info`, `sanity_check -analyze all` (see "Audit").

## Case Table

| # | Case (from the spec) | Documented TCL | Notes | Source |
|---|----------------------|----------------|-------|--------|
| 1 | Single clock, posedge | `clock clk` | `clock -none` for a purely combinational design | AN p5; CR p707 |
| 1b | Single clock, negedge | `clock ~clk` | VHDL: `clock {not clk}` | AN p5; CR p708 |
| 2 | Both edges of one clock | `clock clk -both_edges` | may impact performance; CR: use only when the tool prompts at `prove` / `visualize` | AN p5; CR p709 |
| 3 | 2 clocks, same frequency | `clock clk1 clk2` | — | AN p5 |
| 4 | 2 sync clocks, integer ratio (clk1 = 4 x clk2) | `clock clk1 clk2 4 1` or `clock clk1` + `clock clk2 -factor 4` | 4 = factor, 1 = phase: both tick together right after reset | AN p6; CR p709, p711 |
| 5 | 2 clocks with phase / inverted | `clock clk` + `clock clk1 -factor 2` + `clock clk2 -factor 2 -phase 2` | derived clock has its first posedge at the Nth posedge of the fastest clock (default 1); clk1 / clk2 inverted to each other | AN p6; CR p711 |
| 5b | Slower clock posedge on fast negedge | `clock clk1` + `clock clk2 -factor 2 -phase 2` | INFO ICK016: tool auto-declares `-both_edges`; no impact if nothing samples on negedge | AN p6-7 |
| 6 | Non-integer ratio (clk1 = 3/2 x clk2) | `clock clk1 -factor 2` + `clock clk2 -factor 3` (optionally `-phase 1` each) | fractional ratios → very fast system clock, possibly poor performance | AN p7 |
| 7 | Non-uniform duty cycle | `clock clk -pattern 0100 -both_edges` | `-both_edges` mandatory; no `~clk` with `-pattern`; a patterned clock cannot be a base clock; inputs not rated by default → `clock -rate <in> <clk>` | AN p7-8; CR p711-712 |
| 8 | Asynchronous clocks, ratio range (e.g. 1:1, 1:2, 2:1) | `clock clk_a -from 1 -to 2 -both_edges` + `clock clk_b -from 1 -to 2 -both_edges` | equals one proof per valid factor / phase; no change between cycles; `-both_edges` mandatory; `clock -rate -default` not supported; increases complexity significantly → start with fixed factors | AN p10; CR p712 |
| 8b | Asynchronous clocks, jitter around a nominal ratio | wrapper instantiates DUV + `jasper_model_frequency_jitter` (drives the slow clock); declare only the fast clock; `task -link <jitter_PA_inst_MODEL_FREQUENCY_JITTER> -to <task>` | parameters `RATIO_LOW` / `RATIO_MEDIAN` / `RATIO_HIGH` / `RECOVERY_CYCLE` from the spec | PA p3-5 |
| 9 | Gated clock (ICG / latch gating) | declare the primary clock only: `clock clk` | tool propagates the primary clock through gating logic; complex gating → `clock -analyze` / Clock Viewer; gated clocks with an undriven signal and no defined clock are reported as issues | AN p11 |
| 10 | Clock mux | `clock clk1 clk2` + `assume -env {clk_sel == 1'b0}` | one selection per run; one run per spec mode | AN p11 |
| 11 | Divided / derived clock at a DUT input port | `clock clk` + `clock clk_div -factor <N>` (spec N) | same form as row 4 | AN p6; CR p711 |
| 11b | Divided / derived clock generated inside the DUT | declare the primary input clock; check `clock -analyze` Status (defined / undefined / propagated) for the internal clock | AN / CR do not state that an internal divider is propagated automatically → if reported undefined, record a spec-gap / finding and ask | CR p713-714 |
| 12 | Inputs changing on a slower clock or on one edge | `clock -rate inA clk1` + `clock -rate inB clk2`; both edges of a slow clock: `clock fast_clk` + `clock fast_clk slow_clk 4 1 -both_edges` + `clock -rate inA slow_clk` | falling edge only: rate on `~clk`; rated signals must be free inputs or env stopats; rating with a slower sampler can hide traces | AN p8-9; CR p710 |
| 13 | Free-running clock-enable (flop enable, not a clock) | no dedicated section in AN / CR | not confirmable in the docs as a clock case; treat the enable as an input of its clock domain; if the spec says it changes only on a clock, use `clock -rate <en> <clk>` (row 12) | — |

- `-both_edges` with `clock_1 clock_tcl_list` applies to the listed (derived) clock(s) (CR p709).
- `-phase` semantics: with a primary clock declared, first posedge at the Nth posedge of the primary clock; without, between cycles N and N+1 (CR p711).
- Change factor / phase of a declared clock: `clock -clear` then re-declare; `clock -remove <clk>` uses the declared polarity (CR p712-713).
- Clock domains built from the clock tree can be reassigned with `clock -domain -signal_list <sigs> [-target_domain <id>]`; list with `clock -domain -list` (CR p715).

## Resets per Domain
- Reset is always global; one `reset` command lists the reset pins of all domains (noncumulative by default; each `reset` runs an implicit clear) (CR p1223).
- Pin-constraint list, active level from the spec (CR p1225):

```tcl
reset -expression {~<rst1_n> ~<rst2_n>}
# same effect without -expression: reset {~<rst1_n> ~<rst2_n>}
```

- Only constant pin constraints are supported (`rst`, `~rst`, `a==1'b1`, ...) (CR p1225).
- Reset analysis runs until register values stop changing or 100 iterations; `-max_iterations N -clock <clk>` counts the iterations on a declared or propagated clock — use the slowest spec domain clock when its reset needs N slow cycles (spec value) (CR p1225).
- Range-based clocks: reset analysis uses the fastest possible factor N (CR p712).
- Reset sequencing between domains (spec ordering / staged release) → `reset -sequence <file>` (CR p1222); the sequence comes from the spec.
- Embedded SVA assumptions are not used in reset analysis unless the design is elaborated with `-global_embedded_assumes` (CR p1223).
- `-non_resettable_regs 0|1` only if the spec states the power-up value (CR p1225).
- Audit (CR p1238-1239; p1248):
  - `reset -analyze -synchronous -list signal` → compare the reported async / sync reset signals with the spec reset list (Q6)
  - `reset -analyze -list flop` → flops per reset; flops of a spec domain attached to another domain's reset = finding
  - `sanity_check -analyze simple_reset`
- Properties: `default disable iff` with the reset of the property's own domain (SKILL.md Step 6).

## SVA-Level Clock Rules
- One clock per property: one props module per spec clock domain with its own `default clocking`; no mixed-clock sequences or properties (Cadence SVA 6.0 lecture, slide 146, 177).
- Formal is cycle based (no delta cycles), so a clock hand-off inside a property can differ from simulation; check crossings per "CDC Note" (slide 177).
- Property edge = design edge (posedge unless the spec defines a negedge domain); never use the clock signal inside a property expression (slide 39–43).
- Details: `resources/sva_coding_rules.md` R9; guard PF-45.

## CDC Note
- FPV treats all clocks as synchronous and ignores metastability (AN p13).
- Plan per synchronous domain: properties inside one domain (or between spec-synchronous clocks) run in FPV with rows 1-12.
- Asynchronous crossings (synchronizers, async FIFOs, handshakes): structural / metastability checks → D-CDC (Jasper CDC App, `jasper_cdc_userguide.pdf`; no skill yet — manual); record the hand-off in `verification_plan.md`.
- End-to-end data through an async crossing may still be checked in FPV with a spec ratio (row 4 / 6), range (row 8) or jitter PA (row 8b); report the clock assumption with the result.

## Audit (after `clock` and `reset`, before `prove`)

```tcl
clock -analyze
clock -list configuration
get_clock_info -fastest_clocks
sanity_check -analyze all
reset -analyze -synchronous -list signal
```

- `clock -analyze [-include_latches]`: report per clocking signal with Name, Status (defined / undefined / propagated), Type (simple, AND-gated tree, ...), number of SVA / design flops, drivers (CR p713-714).
- `clock -list configuration`: full configuration incl. phase, periods, patterns, rated inputs (CR p714).
- `get_clock_info -gui` (Clock Viewer), `-fastest_clocks`, `-csv <file>`, `<declared_clock> -list {flop latch load connected_driver}` (CR p876; AN p11-12).
- `sanity_check -analyze (simple_clk | inactive_clk | gated_clk | complex_clk | simple_reset | all)`; iterate until no problematic signals; intended constant clocks: `sanity_check -waiver -add <sig> -type inactive_clk` (AN p13; CR p1248).
- Every clocking signal not in the spec clock list, every undefined clock and every reset mismatch → record in `verification_plan.md` / `spec_gaps.md`; do not silently add a clock.

## Checklist
- [ ] Fastest spec clock declared first; every spec clock declared with spec ratio / phase / edge
- [ ] Slower-domain inputs rated with `clock -rate`
- [ ] Async relations: fixed spec ratio first; range / jitter only as a later step; CDC hand-off recorded
- [ ] Clock mux: one run per spec mode with `assume -env` on the select
- [ ] All spec resets in one `reset` list; `-max_iterations -clock` if a slow domain needs it
- [ ] `clock -analyze`, `sanity_check -analyze all`, `reset -analyze` compared with the spec; findings recorded
