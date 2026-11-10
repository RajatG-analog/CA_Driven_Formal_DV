# Traceability CSV Format — Column Definitions & Examples (formal-connectivity)

- Used by SKILL.md "Traceability (MANDATORY)"; the mandatory rule, spec-only rule and completeness check live in SKILL.md.
- Placeholders: `<mode_A>`..`<mode_D>` modes (spec priority `<mode_A>` > `<mode_B>` > `<mode_C>` > `<mode_D>`), `<sel_A>[i]` per-channel mode select, `<src_bus>`, `<dst_bus>`, `<src_sel>`, `<SEL_W>`, `<N_CH>`, `<N_SRC>`, `<top_module>`.
- Pinmux instance: see `resources/pinmux_worked_example.md`.

## File 1: `req_extraction.csv`

**Columns:**
```
SPEC_ID,PDF_Section,Category,Requirement_Text,Formally_Verifiable,Notes
```

**Column definitions:**

| Column | Description | Values |
|--------|-------------|--------|
| SPEC_ID | Unique requirement ID | `CONN-001`, `CONN-002`, ... |
| PDF_Section | Spec section reference | `3.2.1`, `Table 4`, `Figure 5` |
| Category | Requirement category (see table below) | `MUX_DATA`, `DEMUX_DATA`, `CTRL`, etc. |
| Requirement_Text | Verbatim or paraphrased spec text (double-quoted if commas) | `"When <src_sel>=3, source 3 routed to <dst_bus>"` |
| Formally_Verifiable | Can this be verified by connectivity checking? | `YES`, `ASSUME`, `NO` |
| Notes | Additional context | `Spec gap`, `Priority override`, etc. |

**Connectivity-specific categories:**

| Category | Description | Example |
|----------|-------------|---------|
| `MUX_DATA` | Input data path mux routing | `<src_bus>` → `<dst_bus>` |
| `DEMUX_DATA` | Output data path demux routing | `<dst_in_bus>` → `<src_out_bus>` |
| `CTRL` | Control signal routing | `<src_sel>` → mux select / `<ctrl_bus>` |
| `FEEDBACK` | Feedback/status path | `<fb_in_bus>` → output |
| `ISOLATION` | Mode isolation / no-leakage | `<mode_A>` active → `<mode_B>` output isolated |
| `DEFAULT` | Default output values | No mode active → default routing / `<DEFAULT_PARAM>` |
| `PRIORITY` | Mode priority / override | `<sel_A>` overrides all other modes |
| `PARAM` | Parameterization constraint | `<N_CH>` range, `<CTRL_W>` values |
| `INTEG` | Integration / assumption | External interface constraints |

**Formally_Verifiable values:**
- `YES` — directly verifiable as a CONNECTION row (positive, `c_df_`, `c_pri_` or expected-CEX `neg_`)
- `ASSUME` — becomes an assumption or operating condition (not a connectivity check)
- `NO` — not formally verifiable (timing, analog, performance, etc.)

**Example rows:**
```csv
SPEC_ID,PDF_Section,Category,Requirement_Text,Formally_Verifiable,Notes
CONN-001,3.2.1,MUX_DATA,"When <src_sel>[<SEL_W>-1:0]=0 and no mode select active: <src_bus>[0] routed to <dst_bus>[0]",YES,Default mux path
CONN-002,3.2.1,MUX_DATA,"When <src_sel>[<SEL_W>-1:0]=1: <src_bus>[1] routed to <dst_bus>[0]",YES,Source 1 selected
CONN-010,3.2.3,CTRL,"<src_sel>[i*<SEL_W>+:<SEL_W>] selects 1-of-<N_SRC> sources for channel i",YES,Unused select bits per spec
CONN-020,3.3,ISOLATION,"When <sel_A>[i]=1: <mode_D> output for channel i must be at default",YES,Mode isolation
CONN-030,3.5,FEEDBACK,"<fb_in_bus>[i] routed to <dst_bus>[i] when <sel_A>[i]=1",YES,Feedback path
CONN-040,3.1,PARAM,"<N_CH> parameter range: 1 to <N_CH_MAX>",ASSUME,Design parameterization
CONN-050,3.4,PRIORITY,"<sel_A> overrides <sel_B> overrides <sel_C> overrides <mode_D>",YES,Mux cascade priority
```

## File 2: `formal_traceability.csv`

**Columns:**
```
SPEC_ID,Property_Type,Property_Label,Property_File,Bind_Target,Config,Status
```

**Column definitions:**

| Column | Description | Values |
|--------|-------------|--------|
| SPEC_ID | References `req_extraction.csv` SPEC_ID | `CONN-001` |
| Property_Type | Type of formal property | `CONNECTION`, `NEG`, `TOGGLE`, `ASSUME` |
| Property_Label | CONNECTION name from the CSV | `c_id_src0_ch0`, `c_df_<A>_ch0`, `neg_cross_ch0_to_ch1` |
| Property_File | CSV file containing the row | `spec_input_data_path.csv`, `spec_default_connections.csv`, `spec_negative_tests.csv` |
| Bind_Target | Module the property applies to (top module for connectivity) | `<top_module>` |
| Config | Which parameter configs this applies to | `ALL`, `cfg_default`, `cfg_max` |
| Status | Mapping status | `MAPPED`, `UNMAPPED`, `WAIVED`, `INFRA` |

**Property_Type values for connectivity:**
- `CONNECTION` — a positive CONNECTION row in a check_conn CSV (data path, `c_df_` default/isolation, `c_pri_` priority) — must PROVE
- `NEG` — an intentionally wrong CONNECTION row in `spec_negative_tests.csv` — must give a CEX
- `TOGGLE` — a toggle cover generated from TOGGLE_CHECKS … TOGGLE_CHECKS_END (reachability / anti-vacuity)
- `ASSUME` — an operating condition or constraint

**Status values:**
- `MAPPED` — requirement has a corresponding property that verifies it
- `UNMAPPED` — requirement identified but no property written yet (gap)
- `WAIVED` — requirement waived with justification (e.g., not applicable to this IP)
- `INFRA` — infrastructure property not directly from spec (e.g., toggle cover)

**Example rows:**
```csv
SPEC_ID,Property_Type,Property_Label,Property_File,Bind_Target,Config,Status
CONN-001,CONNECTION,c_id_src0_ch0,spec_input_data_path.csv,<top_module>,ALL,MAPPED
CONN-001,CONNECTION,c_id_src0_ch1,spec_input_data_path.csv,<top_module>,ALL,MAPPED
CONN-002,CONNECTION,c_id_src1_ch0,spec_input_data_path.csv,<top_module>,ALL,MAPPED
CONN-010,CONNECTION,c_cp_srcsel_ch0_b0,spec_control_path.csv,<top_module>,ALL,MAPPED
CONN-020,CONNECTION,c_df_<D>_ch0,spec_default_connections.csv,<top_module>,ALL,MAPPED
CONN-030,CONNECTION,c_id_fb_ch0,spec_feedback_path.csv,<top_module>,ALL,MAPPED
CONN-050,CONNECTION,c_pri_<A>_over_<B>_ch0,spec_mode_priority.csv,<top_module>,ALL,MAPPED
CONN-050,NEG,neg_pri_<B>_over_<A>_ch0,spec_negative_tests.csv,<top_module>,ALL,MAPPED
CONN-001,TOGGLE,<toggle cover name reported by JG>,spec_input_data_path.csv,<top_module>,ALL,INFRA
```

- **One SPEC_ID may map to MANY properties.**
- For example, `CONN-001` (source 0 routed to destination for each channel) maps to `<N_CH>` CONNECTION rows (one per channel).
- Each mapping gets its own row in `formal_traceability.csv`.
