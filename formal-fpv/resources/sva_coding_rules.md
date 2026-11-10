# SVA Coding Rules — Formal-Friendly, Spec-Only (formal-fpv)

- Used by SKILL.md Step 5 (assumptions), Step 6 (assertions) and Step 7 (covers); checked at CP1 / CP2 (`resources/pitfalls.md` PF-41..PF-46) and Gate 4b G8 (`resources/execution_flow_45.md`).
- Source: Cadence SVA 6.0 lecture (paraphrased; slide = printed slide number). Jasper switches: installed command reference (`analyze`, `elaborate`).
- Spec-only stays in force: every bound, state name, latency and expected value comes from the spec or a spec parameter; RTL gives binding names only.
- Liveness policy is unchanged (SKILL.md "Liveness policy"): bounded only, no `s_eventually`; nothing in this file relaxes it.
- Signal names below are generic placeholders (`<req>`, `<gnt>`, `<out>`, ...).

## R1 Overlapping Triggers and One-to-One Pairing
- A level-held or repeated trigger starts a new check copy every cycle; one response can satisfy all open copies (Cadence SVA 6.0 lecture, slide 50, 135–136).
- Therefore `<req> |-> ##[<MIN>:<MAX>] <gnt>` proves only "some grant in the window", not "one grant per request", and never catches a grant without a request (slide 134–136).
- Decision rule:
  - spec forbids a new `<req>` until the response (no overlap) and does not require pairing → the plain bounded form is allowed; add an assertion of the no-overlap rule (or a spec-cited assumption if it is an input rule)
  - spec allows overlap, requires one response per request, or limits outstanding requests → `aux_` helper code + simple Boolean checks (slide 136–138), plus "no grant without outstanding request"
- Counter template (unbounded wait not allowed by policy: combine with the window template or a spec bound):

```systemverilog
// SPEC-<NNN> | <sec> | one <gnt> per <req>; at most SPEC_MAX_OUT outstanding
localparam int AUX_W = $clog2(SPEC_MAX_OUT + 2);   // smallest width that still shows overflow
logic [AUX_W-1:0] aux_out_cnt;                     // spec model, not copied from RTL
always_ff @(posedge <clk> or negedge <rst_n>)
  if (!<rst_n>)              aux_out_cnt <= '0;
  else if (<req> && !<gnt>)  aux_out_cnt <= aux_out_cnt + 1'b1;
  else if (<gnt> && !<req>)  aux_out_cnt <= aux_out_cnt - 1'b1;
ast_P01_no_gnt_wo_req: assert property (<gnt> |-> aux_out_cnt != 0);  // add "|| <req>" only if the spec allows a same-cycle grant
ast_P02_max_out:       assert property (aux_out_cnt <= SPEC_MAX_OUT);
cov_P01_max_out:       cover property (aux_out_cnt == SPEC_MAX_OUT);
```

- Window template (response between SPEC_MIN_LAT and SPEC_MAX_LAT cycles, SPEC_MIN_LAT ≥ 1, SPEC_MAX_LAT ≥ 2; bit k = request issued k+1 cycles ago, still open):

```systemverilog
logic [SPEC_MAX_LAT-1:0] aux_pend, aux_pend_nxt;
logic                    aux_hit;                  // this <gnt> retires an open request
always_comb begin
  aux_pend_nxt = aux_pend;
  aux_hit      = 1'b0;
  for (int k = SPEC_MAX_LAT-1; k >= SPEC_MIN_LAT-1; k--)
    if (<gnt> && !aux_hit && aux_pend_nxt[k]) begin
      aux_pend_nxt[k] = 1'b0;                      // retire the oldest request only
      aux_hit         = 1'b1;
    end
end
always_ff @(posedge <clk> or negedge <rst_n>)
  if (!<rst_n>) aux_pend <= '0;
  else          aux_pend <= {aux_pend_nxt[SPEC_MAX_LAT-2:0], <req>};
ast_P03_max_lat:     assert property (aux_pend[SPEC_MAX_LAT-1] |-> <gnt>);
ast_P04_no_spurious: assert property (<gnt> |-> aux_hit);
```

## R2 Stuck Outputs — Equality Form and Both Output Values
- A one-direction implication (`<cond> |=> <out>`) still passes when `<out>` is tied to the active value (slide 57, 234).
- Prefer the equality form for a spec function: `ast_<CAT><NN>: assert property (<out> == $past(<f(in)>));` (slide 57, 234); otherwise add the reverse property (`<out> |-> $past(<f(in)>)`).
- `$past` in the first cycle after reset samples reset-time values: exclude that cycle only as the spec reset behaviour allows (e.g. a spec-derived `aux_` "past valid" flag).
- Cover both values of every checked output: `cover property (<out> == 1'b0)` and `cover property (<out> == 1'b1)` (multi-bit: each spec value class).

## R3 Weak by Default — Open-Ended Consequents
- From the 2009 LRM on, `assert` / `assume` are weak by default and `cover` / `restrict` strong; under 2005 everything is strong (slide 110–111).
- A weak consequent with an open end never fails when the ending event never comes: `[*]`, `[+]`, `##[*]`, `##[+]`, `$`-ended ranges, `[->N]`, `[=N]`, `until` (slide 76–77, 110, 189).
- Rule: no such term in a consequent; express the spec bound instead (`##[1:<SPEC_BOUND>]`, `[*<lo>:<SPEC_BOUND>]`).
- Only if a bounded rewrite is impractical: `(<seq>) intersect 1'b1[*1:<SPEC_BOUND>]` (slide 152), listed as a bounded exception in the G8 evidence.
- `s_until`, `s_eventually`, `strong(...)` with an open end are unbounded liveness → not allowed (policy).
- Spec gives no bound → spec gap; do not invent one (SKILL.md Step 6).

## R4 Formal-Friendly Coding
- Repetition on the right side of an implication is very costly in an assumption; keep assumptions to Booleans or short fixed sequences (slide 129).
- Do not stack open-ended or wide-range terms; keep ranges as small as the spec allows (slide 129, 152).
- Prefer small `aux_` helper code (flags, counters, shift registers) over long dense sequences (slide 140–141).
- Use the smallest helper width the spec bound needs, not `int` (slide 138).
- Break long sequences into named sequences without a clock; they inherit the property clock (slide 145–146).

## R5 Cycles In Between
- `<a> ##N <b>` and `<a> ##1 <b> ##1 <c>` say nothing about the cycles between or outside the named terms (slide 71, 84).
- State every in-between condition the spec gives:
  - exact latency, no early response: `<req> |=> !<ack>[*<SPEC_LAT>-1] ##1 <ack>`
  - condition held during a bounded wait: `<start> |=> <busy> throughout (##[0:<SPEC_BOUND>-1] <done>)` (slide 153)
  - mutually exclusive phases: write each term with the other spec signals' values

## R6 FSM Stay-in-State Form
- Transition checks alone miss a wrong move when the transition condition is false; add a stay property per spec state and exit condition (slide 49).
- Form (spec state names; state observable only via spec outputs or a user-supplied mapping, binding-only — SKILL.md Step 6):
  - `ast_F<NN>_stay_<SPEC_STATE>: assert property ((<obs_state> == <SPEC_STATE>) && !<spec_exit_cond> |=> (<obs_state> == <SPEC_STATE>));`
- Output-per-state checks do not detect a wrong state; keep both kinds (slide 49).

## R7 Cover Style — No Implication Inside a Cover
- Under the 2012 LRM, `cover property (<a> |=> <b>)` also succeeds on traces where `<a>` never occurs (slide 101–104).
- Rule: no `|->` / `|=>` in any `cover`; cover the sequence: `cover property (<a> ##1 <b>)` or `cover sequence (<a> ##1 <b>)` (slide 102–103).
- Jasper `elaborate` uses witness cover semantics by default (`-witness_cover_property`; `-lrm_cover_property` selects LRM semantics — command reference `elaborate`); the rule still applies so the cover means the same in every tool and LRM mode.
- Keep each `cover` statement on one line so the CP1 grep (PF-41) sees it.

## R8 Split Properties — Discouraged Constructs
- Formal decomposes the problem and proves separate properties in parallel; one property per spec rule is easier to debug and to cover (slide 208–209, 212, 215).

| Construct | Problem (slide) | Use instead |
|-----------|-----------------|-------------|
| property `if (...) ... else ...` | branch coverage unclear, cannot run in parallel (207–209) | one implication per branch |
| property `and` | one result for several rules (211–213) | separate `assert` per operand |
| property `or` | hard to see which operand held (214–216) | sequence `or` inside one implication, or split per spec case |
| property `iff` | two directions in one result (217–218) | two implications |
| `nexttime[N]` / `s_nexttime[N]` | several forms to remember (218–222) | `##N` |
| `until` / `s_until` / `until_with` | weak / strong / overlap variants (189, 197) | bounded sequence form (R3) |

## R9 Clocking
- Use the design edge: posedge unless the spec defines a negedge domain; a negedge property clock adds proof work (slide 43, 180).
- Never use the clock signal inside the property expression; values are sampled before the edge (slide 39–41).
- One clock per property; one `default clocking` per props module and spec domain; no mixed-clock sequences or properties (slide 146, 177).
- Formal has no delta cycles; clock hand-off in multi-clock properties differs from simulation; async crossings → CDC (slide 177; `resources/clocking_multi_clock.md` "CDC Note").
- `@(posedge <clk> iff <qual>)` suspends evaluation, it is not an abort; use it only when the spec defines qualified sampling (slide 179).

## R10 Helper (`aux_`) Code Policy
- Helper code is the recommended remedy for overlap, counting, one-shot and window checks (slide 133–141).
- Allowed: synthesizable `aux_*` flags, counters and shift registers inside the props module, each with a `// SPEC-<NNN>` comment; the file header lists every `aux_` signal.
- Forbidden: copying or re-deriving RTL logic, encodings or internal signals into helper code; helper code embedded in the RTL (slide 133).
- Helper code models the spec, so a mismatch with RTL is a finding, never a reason to edit the helper.

## R11 Simulation-Only Items and LRM Mode
| Item | Formal meaning (slide) | Rule |
|------|------------------------|------|
| Deferred immediate assertions (`assert #0`, `assert final`) | not needed, formal is cycle based (29) | use concurrent properties |
| Action blocks / `$display` on assert or cover | simulation reporting only (95, 170) | do not rely on them for results |
| `.triggered` / `.ended` | depends on simulation scheduling (161) | not used in props |
| `restrict property` | same as `assume` in formal, ignored in simulation (15) | use `assume` with a spec citation |
| `assume` in simulation | becomes an assertion (127) | keep assumptions valid for simulation reuse |

- Default strength and cover meaning depend on the LRM mode (slide 110–111, 115).
- Record the `analyze` language switch in `verification_plan.md` "Methodology" (`resources/tcl_template.md` Notes): per the command reference, `-sv` = `-sv05` = IEEE 1800-2005; `-sv09` / `-sv12` / `-sv17` select 2009 / 2012 / 2017.
- In 2009+ modes sequences are weakly embedded in assert / assume and strongly in cover by default (command reference, SVA support status); R3 applies in every mode.
