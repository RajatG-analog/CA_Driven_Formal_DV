# Worked example (adip_pinmux) — formal-connectivity

- IP-specific illustration of the generic rules in SKILL.md and the other resources files.
- Reference only: for any other IP take names, widths, priorities, defaults and counts from that IP's spec.
- Placeholder mapping used in this example:

| Generic placeholder | adip_pinmux name |
|---------------------|------------------|
| `<top_module>` | `adip_pinmux_top` |
| `<N_CH>` | `NUMBER_OF_IO` (configs 1 / 8 / 32 IOs) |
| `<N_SRC>` | `MAX_PERIPH` (8 peripherals) |
| `<CTRL_W>` | `IO_CTRL_W` |
| Modes, priority `<mode_hi>` > `<mode_lo>` | Test > ESS > GPIO > Peripheral |
| `<sel_A>`..`<sel_C>` | `test_select`, `ess_select`, `gpio_select` |
| `<src_sel>` (`<SEL_W>` = 4) | `peripheral_source_select` |
| `<src_bus>` / `<dst_bus>` | `peripheral_input_bus` / `gpio_output_signal_bus` |
| `<src_out_bus>` / `<dst_in_bus>` | `peripheral_output_bus` / `gpio_input_signal_bus` |
| `<ctrl_bus>` | `peripheral_control_bus` |
| `<DEFAULT_PARAM>` | `PERIPHERAL_OUT_DEFAULT` |
| `cfg_min` / `cfg_default` / `cfg_max` | `cfg_1io` / `cfg_8io` / `cfg_32io` |

## Index math (Step 5 / Pitfall 1)

```
WRONG: peripheral_control_bus[i*8+P+w]
RIGHT: peripheral_control_bus[(i*8+P)*W+w]

WRONG: peripheral_source_select[i*3+:3]
RIGHT: peripheral_source_select[i*4+2:i*4]  (4-bit groups, not 3)
```

## Priority masking (Step 6) — `spec_mode_priority.csv`

- Winner, release (positive), low-mode output default (`c_df_`), masked (negative, in `spec_negative_tests.csv`):
```
TOGGLE_CHECKS
CONNECTION,c_pri_test_over_gpio_io0,,test_input_bus[0],,gpio_output_signal_bus[0]
,COND_EXPR,"test_select[0] && gpio_select[0]"
CONNECTION,c_pri_release_test_to_gpio_io0,,gpio_input_bus[0],,gpio_output_signal_bus[0]
,COND_EXPR,"!(test_select[0]) && !(ess_select[0]) && gpio_select[0]"
CONNECTION,c_df_gpio_during_test_io0,,1'b0,,gpio_output_bus[0]
,COND_EXPR,"test_select[0] && gpio_select[0]"
TOGGLE_CHECKS_END
```
- `c_df_gpio_during_test_io0` source `1'b0` is illustrative; use the spec default for `gpio_output_bus`.
```
TOGGLE_CHECKS
# NEGATIVE TEST CASES - ALL rows INTENTIONALLY WRONG - each must give a CEX
CONNECTION,neg_pri_gpio_over_test_io0,,gpio_input_bus[0],,gpio_output_signal_bus[0]
,COND_EXPR,"test_select[0] && gpio_select[0]"
TOGGLE_CHECKS_END
```

## Default / isolation checks (Step 6b) — `spec_default_connections.csv`

- Reference: `/proj/adip_digital/rgulghan/adip/adip_digital/adip_pinmux/dv/formal/formal_pinmux/1_io/peri_8/spec_default_connections.csv`.
- Mode isolation and select exclusivity as constant-source CONNECTION rows (excerpt from the reference):
```
#Enable toggle checks
TOGGLE_CHECKS
CONNECTION,c_df_test_0,,1'b0,,test_output_bus[0]
,COND_EXPR,"!(test_select[0])"
CONNECTION,c_df_ess_0,,1'b0,,ess_output_bus[0]
,COND_EXPR,"!(ess_select[0])"
CONNECTION,c_df_gpio_0,,1'b0,,gpio_output_bus[0]
,COND_EXPR,"ess_select[0] || !(gpio_select[0])"
CONNECTION,c_df_periph_0_1,,1'b0,,peripheral_output_bus[1]
,COND_EXPR,"!(ess_peripheral_select[0]) && (!(peripheral_source_select[0]) || peripheral_source_select[1] || peripheral_source_select[2])"
TOGGLE_CHECKS_END
```
- `c_df_periph_0_1`: peripheral 1 output is at default whenever the 3-bit select of IO 0 is not 1 (bit-wise expansion) and the ESS-peripheral pass-through is off.
- Source `1'b0` is the spec default used in that reference config; for SoC-context defaults use the `PERIPHERAL_OUT_DEFAULT` value of the config being run.

## Negative tests (Step 6b) — `spec_negative_tests.csv`

- Reference: `/proj/adip_digital/rgulghan/adip/adip_digital/adip_pinmux/dv/formal/formal_pinmux/8_io/peri_8/spec_negative_tests.csv`.
- Excerpt (every row must give a CEX):
```
#Enable toggle checks
TOGGLE_CHECKS
# NEGATIVE TEST CASES - ALL rows INTENTIONALLY WRONG - each must give a CEX
#--- Wrong pad mapping (pad 0 input routed to pad 1 output) ---
CONNECTION,neg_wrong_pad_map,,peripheral_input_bus[0],,gpio_output_signal_bus[1]
,COND_EXPR,"!(test_select[1]) && !(ess_select[1]) && !(gpio_select[1]) && !(peripheral_source_select[8]) && !(peripheral_source_select[9]) && !(peripheral_source_select[10])"
#--- Wrong peripheral source (peripheral 0 condition, peripheral 1 data) ---
CONNECTION,neg_wrong_periph_src,,peripheral_input_bus[1],,gpio_output_signal_bus[0]
,COND_EXPR,"!(test_select[0]) && !(ess_select[0]) && !(gpio_select[0]) && !(peripheral_source_select[0]) && !(peripheral_source_select[1]) && !(peripheral_source_select[2])"
#--- Wrong mode source (GPIO input under peripheral mode) ---
CONNECTION,neg_gpio_in_periph_mode,,gpio_input_bus[0],,gpio_output_signal_bus[0]
,COND_EXPR,"!(test_select[0]) && !(ess_select[0]) && !(gpio_select[0]) && !(peripheral_source_select[0]) && !(peripheral_source_select[1]) && !(peripheral_source_select[2])"
#--- Reversed priority (ESS over Test; spec: Test > ESS) ---
CONNECTION,neg_ess_over_test,,ess_input_bus[0],,gpio_output_signal_bus[0]
,COND_EXPR,"test_select[0] && ess_select[0]"
#--- Wrong default value (1'b1 instead of 1'b0) ---
CONNECTION,neg_wrong_default,,1'b1,,test_output_bus[0]
,COND_EXPR,"!(test_select[0])"
TOGGLE_CHECKS_END
```
- Measured row counts in the references: 1_io/peri_8 `spec_default_connections.csv` = 11 CONNECTION rows; 8_io/peri_8 `spec_negative_tests.csv` = 12 CONNECTION rows.
- Mode isolation pairs: Test → peripheral/GPIO/ESS outputs at default; ESS → peripheral output at default (except the ess_peripheral path); GPIO → peripheral output at default; Peripheral → GPIO output at default.

## Traceability rows

```csv
SPEC_ID,PDF_Section,Category,Requirement_Text,Formally_Verifiable,Notes
CONN-001,3.2.1,MUX_DATA,"When peripheral_source_select[2:0]=0 and gpio_select=0 and ess_select=0 and test_select=0: peripheral_input_bus[0] routed to gpio_output_signal_bus[0]",YES,Default mux path
CONN-050,3.4,PRIORITY,"test_select overrides ess_select overrides gpio_select overrides peripheral mode",YES,Mux cascade priority
```
```csv
SPEC_ID,Property_Type,Property_Label,Property_File,Bind_Target,Config,Status
CONN-001,CONNECTION,c_id_periph0_io0,spec_input_data_path.csv,adip_pinmux_top,ALL,MAPPED
CONN-020,CONNECTION,c_df_periph_0_1,spec_default_connections.csv,adip_pinmux_top,ALL,MAPPED
CONN-001,NEG,neg_wrong_periph_src,spec_negative_tests.csv,adip_pinmux_top,ALL,MAPPED
```

## Waiver scaling (Step 7)

- cfg_1io: ~44 waivers
- cfg_8io: ~353 waivers
- cfg_32io: ~179,329 waivers (mostly expression waivers in mux primitives)

## HTML report specifics

- Config card colors: IO=1 red, IO=8 blue, IO=32 green.
- Generator helper functions: `pss()`, `mp()`, `mg()`, `me()`, `mt()`, `conn()`, `cond()`.
- Verify functions: `verify_input_data_path()`, `verify_output_data_path()`, `verify_control_path()`, `verify_ess_bridge()`, `verify_defaults()`, `verify_priority()`, `verify_test_feedback()` (pad index from `bit / MAX_PERIPH`).
- Spec gap example (Pitfall 5): ESS interface not documented in the pinmux spec.
