# Traceability CSV Format — Column Definitions & Examples (formal-csr)

- Used by SKILL.md "Traceability (MANDATORY)"; the mandatory rule, spec-only rule and completeness check live in SKILL.md.
- Value sets align with the `formal-traceability` skill (`Formally_Verifiable=CSR`, Status `CSR`).
- Placeholders: `<REG>`, `<FIELD>`, `<top_module>`, `<CSR_INST>`, `<x.y>` spec section.

## File 1: `req_extraction.csv`

**Columns:**
```
SPEC_ID,PDF_Section,Category,Requirement_Text,Formally_Verifiable,Notes
```

**Column definitions:**

| Column | Description | Values |
|--------|-------------|--------|
| SPEC_ID | Unique requirement ID | `CSR-001`, `CSR-002`, ... |
| PDF_Section | Spec section / table of the register map | `5.3.2`, `Table 12` (never `RTL`, `Yoda`, `IP-XACT`) |
| Category | Requirement category | see below |
| Requirement_Text | Spec text (double-quoted if it contains commas) | `"<REG> @0x10, 32-bit, RW, reset 0x0000_0000"` |
| Formally_Verifiable | How it is verified | `CSR`, `YES`, `ASSUME`, `NO` |
| Notes | Context | `Spec gap`, `Coverage gap — key assumed open (user request)`, ... |

**CSR-specific categories:**

| Category | Description | Example |
|----------|-------------|---------|
| `REG` | Register: address, width, register access/reset | `<REG>` @0x10 RW reset 0 |
| `FIELD` | Field: bits, access, reset | `<REG>.<FIELD>[7:0]` RW reset 8'h00 |
| `SEC` | Write/read protection condition | `<REG>` writable only when `<LOCK>.<LOCK_EN>`=0 |
| `HWUPD` | HW-updated status / W1C set source | `<STAT>.<ERR>` set by `<err_in>` |
| `PRIORITY` | HW vs SW same-cycle order | HW set wins over SW clear |
| `RESET` | Parameter / signal dependent reset, soft reset | `<CFG>.<DIV>` reset = `<PARAM>` |
| `RESERVED` | Reserved fields / addresses and their read value | bits [31:2] read 0 |
| `PARAM` | Configuration range affecting the map | `<PARAM>` 1..8 |

**Formally_Verifiable values:**
- `CSR` — verified by Jasper CSR app properties generated from the CSV row(s)
- `YES` — needs an additional SVA (outside this skill; use formal-fpv)
- `ASSUME` — operating condition / generated constraint (forbidden access, write-value constraint, user-requested key assumption)
- `NO` — not formally verifiable, or SPEC GAP (Notes `Spec gap — awaiting spec update`)

**Example rows:**
```csv
SPEC_ID,PDF_Section,Category,Requirement_Text,Formally_Verifiable,Notes
CSR-001,<x.y.1>,REG,"<CTRL> @0x0000, 32-bit, RW, reset 32'h0000_0000",CSR,
CSR-002,<x.y.1>,FIELD,"<CTRL>.<EN>[0] RW reset 0",CSR,
CSR-003,<x.y.1>,FIELD,"<CTRL>.<START>[1] write 1 generates a one-cycle pulse",CSR,write_pulse
CSR-005,<x.y.1>,SEC,"<CTRL> writes ignored while <LOCK>.<LOCK_EN>=1",CSR,BUS_WRITE_ENABLE
CSR-011,<x.y.2>,HWUPD,"<STAT>.<ERR>[0] set by <err_in>, cleared by writing 1",CSR,DIRECT_WRITE + oneToClear
CSR-012,<x.y.2>,FIELD,"<STAT>.<BUSY>[1] RO status",NO,Spec gap — update condition not stated; read_undefined
CSR-030,<x.y.4>,RESET,"<CFG>.<DIV> reset value = parameter <PARAM>",CSR,RESET_VALUE_EXPRESSION
```

## File 2: `formal_traceability.csv`

**Columns:**
```
SPEC_ID,Property_Type,Property_Label,Property_File,Bind_Target,Config,Status
```

**Column definitions:**

| Column | Description | Values |
|--------|-------------|--------|
| SPEC_ID | References `req_extraction.csv` | `CSR-002` |
| Property_Type | Kind of property | `ASSERT`, `COVER`, `ASSUME` |
| Property_Label | Property name exactly as reported by JG for the CSR task | copy from `report` / Property Table (contains `AST_RESET_VALUE`, `AST_DATA_INTEGRITY`, `COV_BUS_WRITE_ENABLE_CHANGED`, ...) |
| Property_File | CSR map CSV (or bind/TCL for assumptions) | `<ip>_csr_map.csv` |
| Bind_Target | Checker instance | `<CSR_INST>` |
| Config | Parameter configs | `ALL`, `<cfg_dir>` |
| Status | Mapping status | `CSR`, `MAPPED`, `UNMAPPED`, `WAIVED`, `INFRA` |

- Do not invent property names: fill Property_Label after `check_csr -load` from the generated property list (names are tool-generated per instance/register/field).
- Unified vs partitioned mode changes the names — record the mode used in the Notes of the sign-off.

**Example rows (labels illustrative — copy the real names from JG):**
```csv
SPEC_ID,Property_Type,Property_Label,Property_File,Bind_Target,Config,Status
CSR-002,ASSERT,<generated name containing <CTRL>/<EN> and AST_RESET_VALUE>,<ip>_csr_map.csv,<CSR_INST>,ALL,CSR
CSR-002,ASSERT,<generated name containing <CTRL>/<EN> and AST_BUS_READ_AFTER_BUS_WRITE>,<ip>_csr_map.csv,<CSR_INST>,ALL,CSR
CSR-005,COVER,<generated name containing COV_BUS_WRITE_ENABLE_CHANGED>,<ip>_csr_map.csv,<CSR_INST>,ALL,CSR
CSR-011,COVER,<generated name containing COV_DIRECT_WRITE_CHANGED>,<ip>_csr_map.csv,<CSR_INST>,ALL,CSR
CSR-012,ASSERT,-,<ip>_csr_map.csv,<CSR_INST>,ALL,UNMAPPED
```

- One SPEC_ID maps to MANY properties (one row each).
- Every CSR/FIELD row of the CSV must be reachable from at least one SPEC_ID (`# CSR-nnn` comment on the CSV row).
