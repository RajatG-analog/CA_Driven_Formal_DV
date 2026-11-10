# HTML Report Generation (MANDATORY) — Full Specification (formal-connectivity)

- Used by SKILL.md "HTML Report Generation (MANDATORY)".
- Placeholders: `<N_CH>` channel/IO count, `<N_SRC>` sources per channel, `<CTRL_W>` control bits per source, `<src_bus>`, `<dst_bus>`, `<dst_in_bus>`, `<src_out_bus>`, `<src_sel>`, configs `cfg_min` / `cfg_default` / `cfg_max`.
- Pinmux instance (helper names, verify functions, card colors per IO count): see `resources/pinmux_worked_example.md`.
- After connectivity verification completes, generate a publishable HTML report suite that documents the methodology, results, and per-config verification details.
- Create a Python script `scripts/gen_conn_report.py` that produces this suite.

The report suite consists of **4 HTML page types**:

## Page 1: `index.html` — Landing Page

- The landing page provides an at-a-glance dashboard of all configurations.

**Required content:**
- **Header:** IP name, report title, generation timestamp
- **Summary chips:** Total assertions across all configs, total pass count, number of configs, number of CSV categories
- **Per-config cards** (one clickable card per config): config name, parameters (e.g. `<N_CH>`, `<N_SRC>`, `<CTRL_W>`), assertion count, overall PASS/FAIL badge. Cards link to per-config detail reports.
- **CSV categories grid:** Icons and labels for each CSV category (e.g., Input Data Path, Output Data Path, Control Path, Feedback, Defaults, Priority, Negative)

**Card color scheme by config:**
- `cfg_min`: Red gradient (`#e74c3c → #c0392b`)
- `cfg_default`: Blue gradient (`#2980b9 → #2471a3`)
- `cfg_max`: Green gradient (`#27ae60 → #1e8449`)

## Page 2: `csv_generation_methodology.html` — How CSVs Were Generated

- Documents the CSV generation approach for reproducibility and review.

**Required sections:**

1. **Overview:** What tool/script generated the CSVs, parameterization approach, total assertion counts per config shown in config grid cards
2. **Generation Workflow:** Visual step flow (Spec Analysis → Script Generation → CSV Output → VPlan Mapping → Formal Proof)
3. **CSV Categories & Assertion Counts:** Table with columns: #, CSV File, Category (color-tagged), cfg_min count, cfg_default count, cfg_max count, Verification Target description
4. **Index Mapping Formulas:** Color-labeled formula blocks for each path type (formulas from the spec):
   - Data path: `<src_bus>[bit] → <dst_bus>[ch]`, `ch = bit / <N_SRC>`
   - Control path: multi-level index math (channel, source, control_bit, dst)
   - Output demux: `<dst_in_bus>[ch] → <src_out_bus>[bit]`
   - Select encoding: `<src_sel>` bit allocation and binary encoding
5. **Generator Helper Functions:** Table of the generator's helper functions (e.g. one per select-encoding / mode / path type, plus `conn()`, `cond()`) with purpose and output examples
6. **Regeneration Commands:** Code blocks showing how to re-run the generator for each config
7. **Benefits:** Comparison table of manual vs automated approach

## Page 3: `mapping_verification_methodology.html` — Independent Verification

- Documents the independent cross-check script (`verify_mapping.py`) that validates all CSV index math against spec formulas.
- This is N-version programming applied to formal verification infrastructure.

**Required sections:**

1. **Purpose:** Why an independent verifier is needed (two independent implementations of the same spec formulas)
2. **Results summary grid:** Per-config cards showing total checks and pass count
3. **Verification Architecture:** Visual flow (CSV Files → CSV Parser → Spec Formula Engine → HTML Report)
4. **Script Components:** Table of functions: CSV parser (`extract_connections()`), index extractor (`extract_index()`), check engine (`check()`), report generator (`generate_html_report()`)
5. **Per-CSV Verification Functions:** One `verify_<category>()` function per CSV category, each stating what it checks, e.g.:
   - `verify_input_data_path()` — channel index from `bit / <N_SRC>`; 1:1 for per-channel mode paths
   - `verify_output_data_path()` — demux channel index; 1:1 for per-channel mode outputs
   - `verify_control_path()` — channel + dst index (2 checks per source conn); 1:1 for others
   - `verify_defaults()` — source is the spec default; condition channel matches `bit / <N_SRC>`
   - `verify_priority()` — channel match + ctrl bit match for control; 1:1 for data
   - `verify_feedback()` — feedback channel index; 1:1 per mode
6. **CSV Parsing Logic:** How `extract_connections()` handles the 2-line CONNECTION/COND_EXPR pattern
7. **Check Breakdown by CSV:** Table with per-CSV check counts across all configs
8. **Usage & Regeneration:** Command examples and script location

## Page 4: `mapping_verification_report_<cfg>.html` — Per-Config Detail Report

- One report per configuration with per-assertion verification results.

**Required sections:**

1. **Header:** IP name, generation timestamp, config directory path, parameter chips (e.g. `<N_CH>`, `<N_SRC>`, `<CTRL_W>`)
2. **Summary grid:** 5 metric cards:
   - Overall status (PASS/FAIL)
   - Total checks count
   - Pass count
   - Fail count
   - Pass rate with progress bar
3. **Mapping Formulas:** Reference formulas box (data path, control path, output demux)
4. **Per-CSV sections:** One collapsible/colored section per CSV file, each containing:
   - Section header with CSV filename, color-coded by category, check count badge
   - Results table with columns: Assertion name, Test description, Expected value, Actual value, Computation detail, PASS/FAIL status
   - Color coding: PASS = green (`#27ae60`), FAIL = red (`#e74c3c`)

**Per-assertion table row format:**
```
| Assertion      | Test                                    | Expected | Actual | Detail                                          | Status |
|----------------|-----------------------------------------|----------|--------|-------------------------------------------------|--------|
| c_id_0         | Data path: <src_bus>[0] -> channel      | 0        | 0      | bit 0 / <N_SRC> = ch 0, remainder 0 = source 0  | PASS   |
```

## HTML Styling Requirements

- All report pages MUST use a consistent visual style:

**Color palette:**
- Page background: Dark gradient (`#0f0c29 → #302b63 → #24243e`)
- Header: Purple gradient (`#667eea → #764ba2`)
- Cards: White (`#ffffff`) with `box-shadow: 0 4px 15px rgba(0,0,0,0.08)`
- Table header: Dark slate (`#2c3e50`)
- Alternating rows: `#fafbfc` / white
- Hover: `#e8f4fd`

**Category color tags (inline badges):**
- Data In: Red (`#e74c3c`)
- Demux Out: Green (`#27ae60`)
- Control: Blue (`#2980b9`)
- Bridge: Purple (`#8e44ad`)
- Defaults: Orange (`#e67e22`)
- Priority: Yellow (`#f39c12`)
- Feedback: Teal (`#1abc9c`)
- Negative: Gray (`#95a5a6`)

**Typography:**
- Font: `'Segoe UI', Arial, sans-serif`
- Code blocks: Dark background (`#1e1e2e → #2d2d44`), monospace, with syntax highlighting classes (`.kw` purple, `.fn` blue, `.str` green, `.cm` gray italic)

- **Navigation:** Each methodology page has nav links to the other pages (index, csv_generation, mapping_verification)

## Report Generator Script

Create `scripts/gen_conn_report.py` that:
1. Reads the connectivity CSV files to extract assertion names, sources, destinations, conditions
2. Runs independent index mapping verification (spec formula cross-check)
3. Generates all 4 HTML page types
4. Supports parameterized configs via command-line args

```
Usage: python3 gen_conn_report.py --configs <cfg1_dir> <cfg2_dir> ... \
         --outdir <report_dir> \
         --ip_name <IP_NAME> \
         --n_src <N_SRC> --ctrl_w <CTRL_W>
```

## Report Output Files

```
fpv_env/reports/
├── index.html                              Landing page (all configs)
├── csv_generation_methodology.html         CSV generation methodology
├── mapping_verification_methodology.html   Mapping verification methodology
├── mapping_verification_report_<cfg_min>.html      Per-config detail (cfg_min)
├── mapping_verification_report_<cfg_default>.html  Per-config detail (cfg_default)
├── mapping_verification_report_<cfg_max>.html      Per-config detail (cfg_max)
└── <ip>_param_audit.html                   Param/default audit (param-spec-audit, run last)
```

## Publishing

- After generation, copy reports to a web-accessible location:
```
cp fpv_env/reports/*.html /proj_nobackup/<project>/public_html/<ip>/mapping_reports/
```

- Reports are then accessible at:
  - `https://www.adbldesign.analog.com/proj_nobackup/<project>/public_html/<ip>/mapping_reports/`
