# Step 3 — CSR Map CSV Format Reference (formal-csr)

- Used by SKILL.md Step 3 (and Step 5 for protection rows).
- Source: `jasper_csr_userguide.pdf` (2025.09) — Keywords table, Access Types, Attribute Reference — and `jasper_command_reference.pdf` (`check_csr`).
- Official example CSV: `/cad/adi/apps/cadence/jasper/2025.09-p002/doc/example_jasper_apps/CSR/uart_top_JasperCSR.csv`.
- Every value in the CSV comes from the spec register table; placeholders: `<ip>`, `<REG>`, `<FIELD>`, `<prot_expr>`, `<top_module>`.

## 1. Keyword Cell Positions

- A keyword is recognised in the first non-empty cell of a row ("cell n").
- Rows whose first non-empty cell is not a keyword (e.g. a header row `,,NAME,SIZE,...`) are not keyword rows; the official example uses such header rows.
- `#` in any cell: that cell and all cells to its right are a comment.

| Keyword | Cells after the keyword |
|---------|-------------------------|
| `DATA_WIDTH` | n+1 default data width (default 8); before all CSR rows, or per CSR size |
| `ADDR_OFFSET` | n+1 offset added to every register address; once, before all CSR rows |
| `ADDR_WIDTH` | n+1 address width; backward compatibility / IP-XACT; must match the checker `ADDR_WIDTH` parameter |
| `ALIAS` | n+1 short name, n+2 long name to replace (name macro, not address aliasing); before all CSR rows |
| `DEFAULT_RESET_SIGNAL` | n+1 active-low reset signal/expression for all following CSRs (workbook level, may be redefined) |
| `CSR` | n+1 EMPTY, n+2 name, n+3 size, n+4 byte address, n+5 access type, n+6 reset value, n+7 description |
| `FIELD` | n-1 EMPTY (cell before the keyword), n+1 name, n+2 end bit (MSB), n+3 start bit (LSB), n+4 access type, n+5 reset value, n+6 description |
| `ATTR` | n+1 attribute name, n+1+i attribute value i; applies to the last preceding CSR row or last preceding FIELD row |
| `REGISTER_MAP` / `REGISTER_MAP_END` | n+1 name; groups registers (IP-XACT memoryMap) |
| `ADDR_BLOCK` / `ADDR_BLOCK_END` | n+1 name, n+2 base address, n+3 last address, n+4 width, n+5 address unit bits (default 8) |
| `INDIRECT_ADDR_MAP` / `INDIRECT_ADDR_MAP_END` | windowed CSRs; needs `ATTR,ACCESSED_BY,<index_csr>,<data_csr>` |

- Reset value cells accept any valid Verilog expression (project rule: sized literals, e.g. `32'h0000_0830`).
- FIELD reset overrides CSR reset; both blank = register has no reset value.
- Reset precedence for a field: field `RESET_VALUE_EXPRESSION` > FIELD reset cell > CSR `RESET_VALUE_EXPRESSION` > CSR reset cell.

## 2. RIGHT / WRONG Rows

```
RIGHT: CSR,,<REG>,32,0x0000_0010,RW,32'h0000_0000,<desc>
RIGHT: ,FIELD,<FIELD>,7,0,RW,8'h00,<desc>
RIGHT: ,ATTR,MODIFIED_WRITE_VALUE,oneToClear
WRONG: FIELD,,<FIELD>,7,0,RW,8'h00,<desc>     # name cell empty, all columns shift
WRONG: REG,,<REG>,32,...                       # REG is not a keyword
WRONG: CSR,<REG>,32,...                        # missing empty cell n+1
WRONG: CSR,,<REG NAME>,32,...                  # names must be legal Verilog identifiers (no spaces, /, [ ])
```

- If the address column of the spec is a word index, convert to the byte address the checker `addr`/`PADDR` carries (spec defines the addressing); record the conversion in a `#` comment.

## 3. Attributes by Level (UG ATTR keyword)

| Level | Valid attributes |
|-------|------------------|
| CSR instance (once, e.g. at the start of the first worksheet) | `ACCESS_PRIORITY`, `BUS_LATENCIES`, `BUS_READ_CHECK`, `BUS_READ_LATENCY`, `BUS_WRITE_CHECK`, `BUS_WRITE_LATENCY`, `TEST_OPTION` |
| REGISTER_MAP | `REMAP_STATE` |
| ADDR_BLOCK | `BUS_READ_CHECK`, `RESERVED` (also `BUS_WRITE_ENABLE`, `BUS_READ_ENABLE` per their sections) |
| INDIRECT_ADDR_MAP | `ACCESSED_BY` |
| CSR (register) | `ACCESS_PRIORITY`, `BUS_LATENCIES`, `BUS_READ_CHECK`, `BUS_READ_ENABLE`, `BUS_READ_LATENCY`, `BUS_WRITE_CHECK`, `BUS_WRITE_ENABLE`, `BUS_WRITE_LATENCY`, `DIRECT_READ`, `DIRECT_WRITE`, `MODIFIED_WRITE_VALUE`, `READ_MASKED_BY`, `RESET_MASK`, `RESET_SIGNAL`, `REGISTER_ALIAS_FOR`, `TEST_OPTION`, `WRITE_MASKED_BY`, `RESET_VALUE_EXPRESSION` |
| FIELD | `ACCESS_PRIORITY`, `BUS_LATENCIES`, `BUS_READ_CHECK`, `BUS_READ_ENABLE`, `BUS_READ_LATENCY`, `BUS_WRITE_CHECK`, `BUS_WRITE_ENABLE`, `BUS_WRITE_LATENCY`, `DIRECT_READ`, `DIRECT_WRITE`, `FIELD_ALIAS_FOR`, `MODIFIED_WRITE_VALUE`, `RESET_SIGNAL`, `WRITE_VALUE_CONSTRAINT`, `TEST_OPTION`, `RESET_VALUE_EXPRESSION` |

## 4. Attribute Values (UG Attribute Reference)

| Attribute | Format / values |
|-----------|-----------------|
| `BUS_READ_CHECK` | `read_forbidden`/`rf`, `read_one`/`r1`, `read_zero`/`rz`, `read_undefined`/`ru`, `read_constant`/`rc` (applies to WO, RW, RO) |
| `BUS_WRITE_CHECK` | `write_no_effect`/`wne`, `write_forbidden`/`wf`, `write_reset`/`wr`, `write_once`/`wo`, `write_pulse,ACTIVE_HIGH\|ACTIVE_LOW`, `write_undefined`/`wu` |
| `TEST_OPTION` | `assume_bus_constraint`/`asm` (default), `assert_bus_constraint`/`ast` — for read_forbidden, write_forbidden, write_reset, WRITE_VALUE_CONSTRAINT |
| `BUS_WRITE_ENABLE` | `<expr>` — bus writes update the shadow only when true; creates `COV_BUS_WRITE_ENABLE_CHANGED` |
| `BUS_READ_ENABLE` | `<expr>,read_zero\|read_one\|read_undefined` — read data compared to shadow only when true; second value = expected read when false; creates `COV_BUS_READ_ENABLE_CHANGED` |
| `DIRECT_WRITE` | `<enable>,<data>[,<latency>[,<modified_write_value>]]` — register/field level; first matching row wins; equal latencies; creates `COV_DIRECT_WRITE_CHANGED` (enable must not be a literal) |
| `DIRECT_READ` | `<enable>,<data>[,<latency>]` — `1'b1` enable = continuous compare; creates `COV_DIRECT_READ_CHANGED` |
| `MODIFIED_WRITE_VALUE` | `oneToClear`, `oneToSet`, `oneToToggle`, `zeroToClear`, `zeroToSet`, `zeroToToggle`, `clear`, `set` (bus writes only) |
| `WRITE_VALUE_CONSTRAINT` | field level: `write_as_read,true\|false`, `use_enumerated_values,<v1>,<v2>,...`, `minimum,<v>`, `maximum,<v>` |
| `ACCESS_PRIORITY` | ≥ 2 of `bus_read`, `bus_read_action`, `direct_read`, `bus_write`, `direct_write`; missing ones appended in default order `bus_read, bus_read_action, direct_read, bus_write, direct_write` |
| `BUS_WRITE_LATENCY` / `BUS_READ_LATENCY` | `<cycles>` (default 0) |
| `BUS_LATENCIES` | `<write_latency>,<read_latency>` |
| `RESET_SIGNAL` | `<active_low_expr>`; creates `COV_RESET_CHANGED` |
| `RESET_MASK` | `<mask>` — 1 = bit has a known reset value |
| `RESET_VALUE_EXPRESSION` | `<expr>` — e.g. `<pkg>.<PARAM>` or hierarchical module parameter |
| `READ_MASKED_BY` / `WRITE_MASKED_BY` | `<value or register>` |
| `REGISTER_ALIAS_FOR` | `<aliased CSR>` (same width, reset, field ranges) |
| `FIELD_ALIAS_FOR` | `<CSR>,<FIELD>` (initial release; not with REGISTER_ALIAS_FOR or DIRECT_WRITE) |

- Shadow references: `${<REG>.<FIELD>}` (or `${<MAP>.<BLOCK>.<REG>.<FIELD>}` when not unique).
- Hierarchical signal references must start with the top module name.

## 5. Address Structures

**Reserved addresses (registers) — UG "Verification for Reserved Registers" (initial release):**
```
ADDR_BLOCK,<blk>,0x0000,0x00ff,
,ATTR,RESERVED,undefined_registers,
,ATTR,BUS_READ_CHECK,read_zero,
CSR,,<REG>,32,0x0010,RW,32'h0000_0000,<desc>
ADDR_BLOCK_END,
```
- `RESERVED`: `undefined_registers`/`undefined` or `all_registers`/`all`; `BUS_READ_CHECK`: `read_zero`, `read_one`, `read_constant`.
- Checks run in task `CSR_RESERVED_CHECKS` — copy the CSR task assumptions into it.
- Use only when the spec defines the read value of reserved addresses.

**Reserved fields (unassigned bits):**
- Preferred: declare each spec RESERVED field explicitly with the spec behaviour (`RO` reset 0, `RZ`, ...).
- Alternative: `check_csr -load ... -unassigned_field_checks constant` (read constant undefined value) or `zero` (read zero) — initial release.

**Secure / remapped maps:**
```
REGISTER_MAP,<map>
ATTR,REMAP_STATE,JDA:EXPRESSION,<spec_state_expr>,
CSR,,<REG>,32,0x08,RW
,FIELD,<FIELD>,1,0,RW
REGISTER_MAP_END
```
- `JDA:SECURE` / `JDA:NON_SECURE` need `jasper_csr_extended_checker` with `wr_secure` / `rd_secure`.

**Windowed (indirect) CSRs:**
```
INDIRECT_ADDR_MAP
ATTR,ACCESSED_BY,<INDEX_REG>,<DATA_REG>
CSR,,<IREG>,8,0x01,RW,8'h00
INDIRECT_ADDR_MAP_END
```
- The address cell of each CSR inside the block is the index value.

## 6. Generic Worked Example (placeholders — values from the spec)

```
# <ip> CSR map — source: <spec name> rev <r>, §<x.y> (SPEC ONLY)
DATA_WIDTH,32
ADDR_OFFSET,0
# CSR-001: <CTRL> spec §<x.y.1>
CSR,,<CTRL>,32,0x0000,RW,32'h0000_0000,<desc>
ATTR,BUS_WRITE_ENABLE,${<LOCK>.<LOCK_EN>} == 1'b0
,FIELD,<EN>,0,0,RW,1'b0,<desc>                         # CSR-002
,FIELD,<START>,1,1,RW,1'b0,<desc>                      # CSR-003 self-clearing pulse (access type to pair with write_pulse: not stated in UG — confirm on first run)
,ATTR,BUS_WRITE_CHECK,write_pulse,ACTIVE_HIGH
,FIELD,<RESERVED_31_2>,31,2,RO,30'h0,<desc>            # CSR-004 spec: reserved, reads 0
# CSR-010: <STAT> spec §<x.y.2>
CSR,,<STAT>,32,0x0004,RW,32'h0000_0000,<desc>
,FIELD,<ERR>,0,0,RW,1'b0,<desc>                        # CSR-011 W1C, HW sets on <err_in>
,ATTR,MODIFIED_WRITE_VALUE,oneToClear
,ATTR,DIRECT_WRITE,<top_module>.<err_in>,1'b1
,ATTR,ACCESS_PRIORITY,bus_write,direct_write           # spec: HW set wins over SW clear
,FIELD,<BUSY>,1,1,RO,1'b0,<desc>                       # CSR-012 spec gives no update condition
,ATTR,BUS_READ_CHECK,read_undefined                    # SPEC GAP logged
# CSR-020: <LOCK> spec §<x.y.3>
CSR,,<LOCK>,32,0x0008,RW,32'h0000_0000,<desc>
,FIELD,<LOCK_EN>,0,0,RW,1'b0,<desc>                    # CSR-021 write-once lock
,ATTR,BUS_WRITE_CHECK,write_once
# CSR-030: <CFG> spec §<x.y.4> — reset from parameter <PARAM> (spec)
CSR,,<CFG>,32,0x000C,RW,,<desc>
,FIELD,<DIV>,7,0,RW,,<desc>
,ATTR,RESET_VALUE_EXPRESSION,<pkg>.<PARAM>
```
- `<top_module>.<err_in>` is a spec-named top-level input; if the spec names no observable set source, use `read_undefined` and log a spec gap.
- `ACCESS_PRIORITY,bus_write,direct_write`: direct_write applied after bus_write in the same cycle (HW set wins) — use only the order the spec states.
- Check the parse with `check_csr -list field -instance <inst> -register <STAT>` before proving.
