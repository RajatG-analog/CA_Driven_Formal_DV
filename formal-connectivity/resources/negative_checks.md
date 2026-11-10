# Step 6b — Negative Scenario Checks: Category Details (formal-connectivity)

- Used by SKILL.md Step 6b; the default-value rules (SPEC ONLY), the no-`ILLEGAL` rule and the naming convention live in SKILL.md.
- This flow uses NO SVA: every check is a `check_conn` CSV CONNECTION row.
  - Default / isolation / select-exclusivity / leakage → POSITIVE `c_df_` rows in `<cfg_dir>/spec_default_connections.csv`.
  - Priority winner / release → POSITIVE `c_pri_` rows in `<cfg_dir>/spec_mode_priority.csv`.
  - Negative (expected-CEX) → intentionally WRONG `neg_` rows in `<cfg_dir>/spec_negative_tests.csv`.
- Placeholders (take real names, widths, encodings and defaults from the spec ONLY):
  - `<N_CH>` channel/IO count, `<N_SRC>` sources per channel, `<SEL_W>` spec select-group width per channel
  - `<mode_hi>` / `<mode_lo>` modes with spec priority `<mode_hi>` > `<mode_lo>`; `<sel_hi>` / `<sel_lo>` their per-channel selects
  - `<sel_mode>` select of the mode that owns an output
  - `<src_bus>` source data bus, `<dst_bus>` destination bus, `<src_sel>` per-channel source select
  - `<src_hi>` / `<src_lo>` sources of `<mode_hi>` / `<mode_lo>`
  - `<lo_out_bus>` output owned by `<mode_lo>`, `<src_out_bus>` per-source output (demux side)
  - `<DEFAULT_PARAM>` spec default/isolated value (IP-level literal or SoC-context parameter value)
- Signal names below are illustrative.
- For a pinmux instance of these categories see `resources/pinmux_worked_example.md`.

## Principle — constant-source CONNECTION rows replace value/isolation assertions

- The conn user guide allows a CONNECTION source to be a constant value (e.g. `1'b0`, `1'b1`).
- A row `CONNECTION,c_df_<x>,,<const>,,<out>` + `COND_EXPR` proves `<out> == <const>` whenever the condition holds.
- If the output equals the spec constant under that condition, no other source can leak onto it.
  - Therefore one `c_df_` row covers isolation, select exclusivity, default value and leakage for that output/condition.
- The constant MUST be the spec default (see SKILL.md Step 6b "Default / Isolated Values").
  - IP-level default → literal (`1'b0`, `1'b1`).
  - SoC-context default → the spec default parameter value of the config being run (`<DEFAULT_PARAM>` value per config).
  - Set of allowed values → one config per allowed value, each with its own `c_df_` row for that value.
  - "Don't care" → no `c_df_` row; rely on the expected-CEX `neg_` rows.
- Generic form:
```
TOGGLE_CHECKS
CONNECTION,c_df_<mode>_ch0,,1'b0,,<dst_bus>[0]
,COND_EXPR,"!(<sel_mode>[0])"
TOGGLE_CHECKS_END
```

## Category 1 — Mode Isolation (CRITICAL, highest priority)

- When one mode is active, outputs owned by OTHER inactive modes MUST be at the spec default.
- For each channel `i` and each (active_mode, isolated_output) pair defined by the spec:
  - `<mode_hi>` active → `<lo_out_bus>` at default
  - `<mode_hi>` active → every other lower-mode output at default
  - `<mode_lo>` active → outputs owned by other modes at default (where the spec defines isolation)
  - Exclude spec-defined pass-through paths (e.g. a bridge from one mode into another) from the COND_EXPR
- Write one `c_df_` row per output bit; COND_EXPR = the spec condition where the output must be at default:
```
TOGGLE_CHECKS
CONNECTION,c_df_<lo>_ch0,,<DEFAULT_PARAM>,,<lo_out_bus>[0]
,COND_EXPR,"!(<sel_lo>[0]) || <sel_hi>[0]"
CONNECTION,c_df_<B>_ch0,,1'b0,,<B_out_bus>[0]
,COND_EXPR,"!(<sel_B>[0])"
TOGGLE_CHECKS_END
```

## Category 2 — Select Decode Exclusivity

- When `<src_sel>` chooses source p on channel `i`, every OTHER source output q != p on that channel MUST be at its spec default.
- One `c_df_` row per (channel, source q); COND_EXPR = "`<src_sel>` group of channel i != q" (plus any spec-defined mode gating):
```
TOGGLE_CHECKS
CONNECTION,c_df_src1_ch0,,1'b0,,<src_out_bus>[1]
,COND_EXPR,"<src_sel>[<SEL_W>-1:0] != 'd1"
TOGGLE_CHECKS_END
```
- Expand the condition bit-wise (as in the pinmux reference CSV) if the spec defines the select per bit.

## Category 3 — Cross-Channel Isolation

- Signals from channel `i` must NEVER appear on channel `j` outputs (`i != j`).
- Covered positively: each channel's own CONNECTION rows (`c_id_` / `c_od_`) prove the destination follows ITS source; a cross-wired path fails them.
- Proven non-vacuous by expected-CEX rows in `spec_negative_tests.csv` (ch i source → ch j destination under ch j's condition):
```
TOGGLE_CHECKS
CONNECTION,neg_cross_ch0_to_ch1,,<src_bus>[0],,<dst_bus>[1]
,COND_EXPR,"<src_sel>[<SEL_W>+:<SEL_W>] == 'd0"
TOGGLE_CHECKS_END
```
- **PRACTICAL APPROACH** (representative pairs only, not O(N²)):
  - ch0 vs ch1 (adjacent, catches off-by-one in generate index)
  - ch0 vs ch(<N_CH>-1) (first vs last, catches boundary errors)
  - ch k vs ch k+1 for one mid-range k (catches mid-array errors)

## Category 4 — Default Output Values

- When NO mode is active, outputs must be at the spec-defined default routing / value.
- Default routing (spec default source) → positive CONNECTION row from that source:
```
TOGGLE_CHECKS
CONNECTION,c_df_route_src0_ch0,,<src_bus>[0],,<dst_bus>[0]
,COND_EXPR,"!(<sel_hi>[0]) && !(<sel_lo>[0]) && <src_sel>[<SEL_W>-1:0] == 'd0"
TOGGLE_CHECKS_END
```
- Default value (constant) → `c_df_` row with the spec constant as source (see Principle).

## Category 5 — No Signal Leakage Through Disabled Path

- A deselected mux input must NOT affect the output.
- Covered by the positive rows: if `<dst_bus>[i]` equals the selected source (or the spec constant) under the condition, a deselected input cannot leak.
- Non-vacuity: an expected-CEX row from the deselected source to the destination under the same condition.

## Category 6 — Negative (Expected-CEX) Tests — `spec_negative_tests.csv`

- Every row is an intentionally WRONG CONNECTION; EVERY row must produce a CEX.
- A CEX proves the checker distinguishes right from wrong (not vacuous).
- A `neg_` row that PROVES is a finding (checker vacuous, or spec/RTL issue) → `formal-cex-debug` flow.
- Categories (one or more rows each):
  - Wrong channel mapping: ch i source → ch j destination
  - Wrong source under a select value: source q while `<src_sel>` selects p
  - Wrong mode source: another mode's source under this mode's condition
  - Reversed priority: low source → destination while high is active
  - Non-default value on an isolated output: e.g. `1'b1` when spec default is `1'b0`
- File header comment (mandatory):
```
#Enable toggle checks
TOGGLE_CHECKS
# NEGATIVE TEST CASES - ALL rows INTENTIONALLY WRONG - each must give a CEX
CONNECTION,neg_cross_ch0_to_ch1,,<src_bus>[0],,<dst_bus>[1]
,COND_EXPR,"<src_sel>[<SEL_W>+:<SEL_W>] == 'd0"
CONNECTION,neg_sel_src1_under_src0_ch0,,<src_bus>[1],,<dst_bus>[0]
,COND_EXPR,"<src_sel>[<SEL_W>-1:0] == 'd0"
CONNECTION,neg_mode_<lo>_src_in_<hi>_ch0,,<src_lo>[0],,<dst_bus>[0]
,COND_EXPR,"<sel_hi>[0] && !(<sel_lo>[0])"
CONNECTION,neg_pri_<lo>_over_<hi>_ch0,,<src_lo>[0],,<dst_bus>[0]
,COND_EXPR,"<sel_hi>[0] && <sel_lo>[0]"
CONNECTION,neg_default_<lo>_ch0,,1'b1,,<lo_out_bus>[0]
,COND_EXPR,"!(<sel_lo>[0])"
TOGGLE_CHECKS_END
```
- Load: the negative CSV gives CEXs by design; a CEX can mark a regression config FAIL (adsim error pattern).
  - Load it in a SEPARATE `check_conn` task / config, or keep it out of regression configs.
  - ASK the user which configs run the negatives; keep the load line commented elsewhere.

## Parameterized Generation

- Add generation of `c_df_` and `neg_` rows to `gen_conn_csv.py`:
```python
def gen_default_and_negative_rows(n_ch, n_src, sel_w, default):
    """Return (default_rows, negative_rows) as CSV lines; names/conditions from spec."""
    dflt, neg = [], []
    for i in range(n_ch):
        # Category 2: select exclusivity -> c_df_ per unselected source output
        for q in range(n_src):
            dflt.append(f"CONNECTION,c_df_src{q}_ch{i},,{default},,<src_out_bus>[{i*n_src+q}]")
            dflt.append(f",COND_EXPR,\"<src_sel>[{i*sel_w}+:{sel_w}] != 'd{q}\"")
        # Category 6: wrong source under select value 0 -> expected CEX
        if n_src > 1:
            neg.append(f"CONNECTION,neg_sel_src1_under_src0_ch{i},,<src_bus>[{i*n_src+1}],,<dst_bus>[{i}]")
            neg.append(f",COND_EXPR,\"<src_sel>[{i*sel_w}+:{sel_w}] == 'd0\"")
    # Category 3: cross-channel (representative pairs only)
    pairs = []
    if n_ch > 1:
        pairs.append((0, 1))
    if n_ch > 2:
        pairs.append((0, n_ch - 1))
    if n_ch > 4:
        pairs.append((n_ch // 2, n_ch // 2 + 1))
    for i, j in pairs:
        neg.append(f"CONNECTION,neg_cross_ch{i}_to_ch{j},,<src_bus>[{i*n_src}],,<dst_bus>[{j}]")
        neg.append(f",COND_EXPR,\"<src_sel>[{j*sel_w}+:{sel_w}] == 'd0\"")
    wrap = lambda rows: ["TOGGLE_CHECKS"] + rows + ["TOGGLE_CHECKS_END"]
    return wrap(dflt), wrap(neg)
```
- Verify every computed index against the spec formulas (SKILL.md Pitfall 1).

## Expected Row Counts (per channel)

- Mode isolation `c_df_`: one per output bit owned by a mode that has an isolation condition
- Select exclusivity `c_df_`: `<N_SRC>` (one per source output; condition = "not selected")
- Default routing: one per output in the default (no-mode) state
- Priority: per (hi, lo) pair one `c_pri_` winner + one `c_pri_release_` + one `neg_pri_`
- Negative `neg_`: at least one per Category 6 sub-category, plus cross-channel representative pairs
- Total = (per-channel sum) × `<N_CH>` + cross-channel pairs.
- Measured pinmux numbers: see `resources/pinmux_worked_example.md`.
