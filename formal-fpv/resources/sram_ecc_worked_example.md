# Worked Example — Memory Controller with ECC (EXAMPLE ONLY, formal-fpv)

- Illustrates how Path 2 (+ Path 1 control props) maps a memory-controller spec to properties.
- EXAMPLE ONLY: not a requirement list. Every entry applies only if the IP's own spec states it; every number, bound, encoding and register name comes from that spec.
- Rewritten from the legacy SRAM checklist (archived legacy file `skills/formal-fpv/archive/instructions_legacy.md`, "Ideal Assertion Checklist"; do not load) with RTL-derived items removed:
  - removed: internal-signal equations ("access = htrans[1] & hsel & hready"), RTL wiring checks (`err[1] == one_error`), fixed liveness-bound table, "start with `##[1:128]` and widen"
  - kept: spec-level behaviours expressed at the DUT boundary or at spec-defined interfaces

## Example IP Shape (assumed spec content)
- AHB5-Lite subordinate data port; APB4 configuration port; SRAM macro (data + parity lanes); SECDED ECC; optional ROM region; initialization engine; interrupt and status registers; test mode.

## Step 0 Outcome (example)
- P1 no (sequential), P2 no (single data port), P3 yes (end-to-end data integrity through storage + ECC) → **Path 2**.
- P4 yes (APB register map) → register reset / access to `formal-csr`; functional register effects stay in FPV (Path 1 bind props).
- X/Z on outputs → `formal-xprop`.

## Environment (example)
- Wrapper: DUT + `cdn_abvip_ahb5_lite_wrapper` (`VERIFY_BLK = 2`, `ACTIVE_SLAVES = 32'h1`, SLAVE0 range = spec memory map) + `cdn_abvip_apb4_master` (APB slave DUT).
- SRAM behavioral model from the macro datasheet (read latency, byte / lane write enables); ROM model with unconstrained contents (if the spec defines a ROM region).
- ECC reference model from the spec code definition (H-matrix / parity equations), with its own round-trip sanity covers.
- Error injection: free XOR mask on model read data, number of flipped bits limited to the spec error classes (0 / 1 / 2).
- Scoreboards: write path (accepted full-word write data → macro write data) and read path (reference-corrected data → bus read data), `MAX_PENDING` = spec maximum outstanding.
- Symbolic address for "read returns last write" (`resources/path2_wrapper_scoreboard.md`).

## Feature → Property Map (example; SPEC_IDs are placeholders)

| Feature (spec) | Assertions (spec-derived) | Covers |
|----------------|---------------------------|--------|
| ECC encode | stored parity == reference-model parity for written data (per parity bit); parity behaviour when ECC disabled as the spec states | each parity bit toggles |
| ECC decode | 0 errors → data unchanged; 1 error → corrected data == written data; 2 errors → spec detection flag; bypass mode per spec | each error class injected |
| ECC error response | per spec error-response configuration: error class → bus error response or not; spec two-cycle AHB error response | each class × each configuration |
| ECC status / capture / counter | status set on the spec event; capture of address / data / parity on the spec "first error" rule; counter increment, saturation and clear per spec | saturation reached, clear while error |
| Bus data port | read data == reference-corrected data on a spec-valid read; no macro write without a spec-valid write; write address == bus address mapping from the spec; wait-state bound from the spec | back-to-back read / write, each size |
| Partial writes (if specified) | written byte lanes take the bus data, other lanes keep the previous contents (memory-semantics SVA with the symbolic address) | each byte / halfword lane |
| Memory regions (if specified) | write to a spec read-only region → spec error response; read allowed; access during initialization → spec response | each region |
| Initialization engine | start conditions per spec (register / pin), progress, completion flag, abort behaviour, handshake per spec; all bounds from the spec | start, abort, completion |
| Interrupt / status | `irq` = spec function of status and enables; sticky until the spec clear; no interrupt when all sources disabled | each source, simultaneous sources |
| Test mode (if in scope) | spec test-mode data / parity access behaviour; or a scope assumption that test mode is off (recorded) | each test-mode access |
| Reset / defaults | output and status reset values (IP or SoC context, Q8) | reset release then idle |
| Negative | masked error class gives no error response; disabled interrupt never asserts; no write-back after an uncorrectable error only if the spec says so | the masked condition occurs |

## Example Properties (illustrative syntax)

```systemverilog
// SPEC-<NNN> | <sec> | "A single-bit error shall be corrected on read"
ast_E02_sec_corrected: assert property (
  rd_valid_sym && (inj_bits == 1) |-> ##SPEC_RD_LAT hrdata == last_wdata_sym
);
// SPEC-<NNN> | <sec> | "HREADYOUT shall not stay low longer than <N> cycles"
localparam int SPEC_NNN_BOUND = <N from spec>;
ast_B05_ready_bound: assert property (!hreadyout |-> ##[1:SPEC_NNN_BOUND] hreadyout);
// Reachability of the error classes allowed by the injection constraint
cov_E00_inj_0: cover property (rd_valid_sym && inj_bits == 0);
cov_E01_inj_1: cover property (rd_valid_sym && inj_bits == 1);
cov_E02_inj_2: cover property (rd_valid_sym && inj_bits == 2);
```

- `rd_valid_sym`, `last_wdata_sym`, `inj_bits` are wrapper-level helper signals built from spec-defined interface events and the symbolic address — not RTL internals.

## Configurations (example)
- One `<cfg_dir>` per spec value class: ECC enabled / disabled, ROM region present / absent, minimum / maximum memory size allowed by the spec.
- IP-level defaults and SoC-context values (Q8) as separate `<cfg_dir>`s; confirmed by `param-spec-audit`.
