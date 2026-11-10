# Path 1 — Bind-File Custom SVA (formal-fpv)

- Used by SKILL.md Step 2 when Step 0 selects Path 1 (control logic, FSMs, timers, interrupt controllers, GPIO, control port, TRU, PLIC).
- Also used for the control-feature props of Path 2 / Path 3 environments.
- Source: `formal-fpv-complete.md` Part B.5 Approach A (bind file).
- Spec-only: every `<...>` value comes from the spec or a spec parameter; RTL is used only for port / hierarchy names (binding-only).

## File Layout
- `props/<ip>_assumptions.sv` — `asm_*` (spec AoU, operating mode, static config)
- `props/<ip>_<feature>_props.sv` — one module per spec feature: `ast_*` + `cov_*`
- `props/<ip>_props_bind.sv` — one `bind` per props module
- Compile order: RTL filelist → assumptions → props modules → bind file.

## Props Module Template

```systemverilog
//------------------------------------------------------------------------------
// File        : <ip>_<feature>_props.sv
// Spec        : <spec name> rev <rev>, section <sec>
// Purpose     : <feature> assertions and covers (spec-derived)
// Binding-only: port names taken from <top_module> port list (no behaviour from RTL)
//------------------------------------------------------------------------------
module <ip>_<feature>_props #(
  parameter int <PARAM> = <SPEC_DEFAULT>          // spec <sec>: legal <lo..hi>
) (
  input logic              <clk>,
  input logic              <rst_n>,
  input logic [<W>-1:0]    <sig_a>,
  input logic              <sig_b>
);
  default clocking cb @(posedge <clk>); endclocking
  default disable iff (!<rst_n>);
  // Bounds from the spec (no invented values)
  localparam int SPEC_<NNN>_BOUND = <spec expression>;   // SPEC-<NNN>
  // SPEC-<NNN> | <sec> | <requirement text>
  ast_<CAT><NN>_<desc>: assert property (<antecedent> |-> <consequent>);
  // SPEC-<NNN> | <sec> | bounded response — only if the spec excludes overlapping <req> and one-to-one pairing;
  // otherwise aux_ helper template + no-ack-without-req check (resources/sva_coding_rules.md R1)
  ast_<CAT><NN>_<desc>_bnd: assert property (<req> |-> ##[1:SPEC_<NNN>_BOUND] <ack>);
  // SPEC-<NNN> | <sec> | reset value (async reset form; sync: |=>)
  ast_R<NN>_<sig>_rst: assert property (disable iff (1'b0) !<rst_n> |-> <sig_a> == <SPEC_DEFAULT>);
  // Scenario cover: a sequence, never an implication (resources/sva_coding_rules.md R7)
  cov_<CAT><NN>_<desc>: cover property (<spec scenario sequence>);
  // Optional feature (spec: present only if <PARAM> = 1)
  generate if (<PARAM> == 1) begin : g_<feature>
    // SPEC-<NNN> | <sec> | ...
    ast_<CAT><NN>_<desc>_opt: assert property (<...>);
  end endgenerate
endmodule
```

## Bind File Template

```systemverilog
// <ip>_props_bind.sv — bind spec-derived props to the module owning the spec interface
bind <top_module> <ip>_<feature>_props #(
  .<PARAM> (<PARAM>)                 // pass the DUT parameter, never a copied literal
) u_<feature>_props (
  .<clk>   (<clk>),
  .<rst_n> (<rst_n>),
  .<sig_a> (<sig_a>),
  .<sig_b> (<sig_b>)
);
```

- Bind to the module that owns the spec interface; prefer port connections.
- A required signal not visible at the bind scope: retarget the bind or ask the user; never copy or re-derive RTL logic.
- Spec-derived helper code is allowed: `aux_` prefix, SPEC_ID comment, listed in the file header (`resources/sva_coding_rules.md` R10).

## Assumptions (spec AoU only)

```systemverilog
module <ip>_assumptions (input logic <clk>, input logic <rst_n>, input logic <cfg_sig>, ...);
  default clocking cb @(posedge <clk>); endclocking
  default disable iff (!<rst_n>);
  // SPEC-<NNN> | AoU <sec> | "<cfg> shall not change while <enable> = 1"
  asm_CFG01_static: assume property (<enable> |-> $stable(<cfg_sig>));
  // SPEC-<NNN> | <sec> | functional mode only (scope limitation, recorded in verification_plan.md)
  asm_MODE01_func: assume property (<test_mode> == 1'b0);
  // reachability cover for every forced value class
  cov_CFG01_cfg_val_<k>: cover property (<cfg_sig> == <SPEC_LEGAL_VALUE_k>);
endmodule
```

## Category Checklist per Feature

| Category | Assertion content (from the spec) | Cover content |
|----------|-----------------------------------|---------------|
| FSM (spec state diagram) | per spec state: observable outputs; per spec transition: condition → next observable behaviour; illegal transition never observed; stay-in-state per spec state and exit condition (`resources/sva_coding_rules.md` R6) | every spec state, every spec transition |
| Timer / counter | load / reload value, decrement or increment step, expiry event, wrap or saturate per spec | expiry, reload, boundary values |
| Interrupt controller | status set on spec event, sticky until spec clear, mask, `irq` = spec function of status and enable, priority order | each source, each masked case, simultaneous sources |
| Control / status | write side effects, read-back per spec, error responses for illegal access | each mode, each error |
| GPIO / pad control | direction, output value, input sampling, per-pin independence (all pins) | each pin mode |
| Negative | disabled / masked / lower-priority / restricted path never affects the output | the competing request is present |
| Default / reset | reset values and idle / unselected outputs (IP or SoC context, Q8) | reset release then idle |

## Path 1 TCL Additions
- No wrapper: `elaborate -top <top_module>`.
- Analyze the props and bind files after the RTL filelist (see `resources/tcl_template.md`).
