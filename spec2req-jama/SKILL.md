---
name: spec2req-jama
description: "Extract atomic requirements from any specification document (HTML, PDF, Markdown) and import them into Jama as a structured hierarchy of folders and requirements with hyperlinked source traceability."
keywords: spec specification requirements atomic jama import extract traceability hierarchy
---

# Spec-to-Requirements Jama Importer

Extract atomic requirements from a specification document and import
them into Jama as a structured folder/requirement hierarchy with
hyperlinked source traceability.

## Overview

This skill automates the end-to-end flow of:

1. Parsing a specification document to identify sections and requirements
2. Decomposing every requirement into **atomic** form (one testable assertion each)
3. Extracting requirement metadata (ID, name, description, source keys)
4. Resolving source document keys to Jama item IDs via the REST API
5. Creating a folder-per-section hierarchy in Jama
6. Populating each folder with atomic requirement items containing HTML descriptions and hyperlinked sources
7. **Completeness review** — second pass as reviewer: re-reading the entire specification to verify every behavioral clause, constraint, and interface definition is covered by at least one atomic requirement, and resolving all gaps before sign-off

## Atomicity Rules

Every requirement produced by this skill **must** be atomic. An atomic
requirement contains exactly **one independently testable assertion**
that maps 1:1 to a single test case.

### Definition

A requirement is atomic when **all** of the following hold:

1. **Single assertion** — the description makes exactly one "shall"
   statement about one observable behavior or property.
2. **One stimulus, one response** — there is one input condition /
   stimulus and one expected outcome to verify.
3. **Independently testable** — a DV engineer can write one focused
   test case that passes or fails on this requirement alone, without
   coupling to other requirements.

### Decomposition Triggers

If a draft requirement exhibits **any** of the following, it **must**
be split before import:

| Trigger | Example (WRONG) | Fix |
|---------|-----------------|-----|
| Multiple "shall" clauses joined by "and" / "also" | "The IP shall support Mode A **and** Mode B" | Split into one req per mode |
| Enumerated list of independent behaviors | "shall support: (a) write, (b) read, (c) erase" | One req per behavior |
| Separate trigger and clear conditions | "flag shall assert on X **and** auto-clear on Y" | (a) assert condition, (b) clear condition |
| Behavior + preservation constraint | "shall reset protocol logic **without affecting** system config" | (a) reset behavior, (b) config preservation |
| Bit-field layout + access type combined | "32-bit register with fields … and read-only output" | (a) bit-field layout, (b) read-only constraint |
| Multiple protocol modes as one item | "shall operate at 100 kHz, 400 kHz, and 1 MHz" | One req per speed grade |
| Signal list + conformance statement | "shall conform to spec X and provide signals A, B, C" | Keep as one req only if the signal list IS the spec definition; split if behavioral constraints are mixed in |

### Naming Convention — Sequential Numbering

All requirements use **sequential three-digit numbering** within
their container, ordered by folder:

```
XX-REQ-001: Counter Bit Width
XX-REQ-002: Initial Counter Load Value
...
XX-REQ-065: Enable Domain Crossing Signal
```

**Do NOT use letter suffixes** (e.g., `XX-REQ-011a/b/c`). When
splitting a composite requirement, assign each child the next
available sequential number. If insertion creates a gap, renumber
all subsequent items to close the gap.

When decomposing during initial extraction, simply assign sequential
numbers as you go — there is no need to preserve the spec's original
numbering scheme.

### Requirement Title Rules

- **No signal or parameter names in titles.** Titles must describe the
  function or purpose, not reference a specific RTL identifier.
- Signal names belong only in the description body (as plain text).

| Title (WRONG) | Title (CORRECT) |
|----------------|-----------------|
| `XX-REQ-004: mode_sel Protocol Selection Input` | `XX-REQ-004: Dual-Mode Protocol Selection Input` |
| `XX-REQ-050: soft_resetb Reset Input` | `XX-REQ-050: Secondary Soft Reset Input` |
| `XX-REQ-013: wait_cycles Configuration` | `XX-REQ-013: Bus Wait Cycle Configuration` |

### Formatting Constraints

- **Plain text everywhere** — do NOT use `<code>` tags in requirement
  descriptions. RTL signal names, parameter names, register names, and
  all other technical identifiers must appear in the same font as the
  surrounding description text.
- **No colored or styled text** — all text must be default black with
  no inline `style`, `color`, or `font` attributes.
- **Connection traceability per atomic requirement** — every atomic
  requirement must cite the specific source spec items that justify
  **that** assertion, not the parent composite's full source list.
  The footer label is **"Connection:"**, not "Source:".

### Genericization Rules

Requirement descriptions **must not** contain implementation-specific
names. All register, signal, clock, reset, and parameter names must
be replaced with generic functional descriptions.

#### Name Categories to Genericize

| Category | Examples (WRONG) | Generic Form (CORRECT) |
|----------|-----------------|----------------------|
| Registers | REG_A, REG_B, STATUS | control register, configuration register, status register |
| Parameters | DATA_WIDTH, INIT_VAL, EN_DEFAULT | data width parameter, initial value parameter, default enable parameter |
| Output signals | ip_out_a, ip_out_b | primary output, secondary output |
| Input signals | mode_sel | mode selection input |
| Internal signals | sync_en | enable synchronization signal |
| Clocks | bus_clk, func_clk, gated_clk | bus clock, functional clock, gated bus clock |
| Resets | sys_rstn, func_rstn | system reset input, functional reset input |
| Bus signals | bus_sel | bus select signal |
| Bit fields | REG_A[5], STATUS[1] | (remove entirely; describe behaviorally) |

#### Workflow for Genericization

1. **Inventory** — Before extraction, scan the spec for ALL register,
   signal, clock, reset, and parameter names. Build a complete list.
2. **Map** — Define a generic functional description for each name.
3. **Apply** — During extraction, use only generic descriptions in
   requirement bodies. Never use the implementation name.

This prevents multi-pass remediation where each pass discovers a new
category of specific names that the previous pass missed.

### Inclusive Language

Use inclusive terminology in all requirements:

| Term (WRONG) | Term (CORRECT) |
|--------------|----------------|
| master | initiator |
| slave | target |
| whitelist | allowlist |
| blacklist | blocklist |

## Signal and Register Definition Requirements

Each register, signal, parameter, clock, and reset referenced in
behavioral requirements **must** have exactly **one** atomic
definition requirement. Definitions are created in a **canonical
folder** — never duplicated across multiple folders.

### Canonical Folder Assignment

| Definition Type | Canonical Folder |
|----------------|-----------------|
| Configuration parameters | Configuration Parameters |
| Clock inputs | Clock Architecture |
| Reset inputs | Reset Architecture |
| Output signals (reset, interrupt, wakeup) | Output Signals |
| Input signals (halt, debug) | Operating Modes or Debug |
| Internal CDC signals | CDC Architecture |
| Status/control registers | The folder where the register's primary behavior is defined |

### One Definition per Item — No Duplicates

Each register/signal/parameter gets **exactly one** definition
requirement across the entire container. Behavioral requirements in
other folders reference it generically (e.g., "the control register")
without redefining it. This prevents the duplication problem where
Phase 2 creates per-folder copies that Phase 5 must delete.

### When a Definition Requirement Is Needed

1. A register is used in behavioral requirements (e.g., "when the
   control register enable bit is set") but no requirement defines
   what the register IS, its width, or access type.
2. An I/O signal is referenced in behavioral requirements (e.g.,
   "the reset output") but no requirement defines its direction,
   width, or clock domain.
3. A configurable parameter is used in behavioral logic without a
   requirement stating it exists and what it controls.

### When a Definition Requirement Is NOT Needed

- The signal is a well-known standard interface signal whose meaning
  is universally understood from the protocol spec (e.g., standard
  bus handshake signals).
- The signal was already defined by a definition requirement in its
  canonical folder.

### Definition Requirement Description Pattern

Use generic functional descriptions — no implementation names:

```html
<p>The [component] shall provide a [width/type] [input/output/parameter]
[generic description] [purpose clause]. [Additional context about role,
domain, or constraints].</p>
<br><br>
<p><strong>Connection:</strong> <a href="...">PROJ-SPEC-NNNN</a></p>
```

### Examples

| Canonical Folder | Definition Requirement | What It Defines |
|-----------------|----------------------|-----------------|
| Configuration Parameters | "shall provide a control register for IP enable, mode selection, and lock control" | Control register |
| Configuration Parameters | "shall provide a configuration register that holds the programmable threshold value" | Configuration register |
| Output Signals | "shall provide a 1-bit primary output as a single-cycle pulse in the functional clock domain" | Primary output signal |
| Operating Modes | "shall accept a 1-bit mode selection input from the system controller" | Mode selection input |
| CDC Architecture | "shall provide an internal enable synchronization signal that propagates enable across clock domains" | CDC enable signal |

### Post-Import Deduplication Audit

After import, verify no register/signal/parameter is defined more
than once across the container:

```python
from collections import defaultdict
title_groups = defaultdict(list)
for item in all_items:
    suffix = title_suffix(item["name"]).lower()
    title_groups[suffix].append(item)
for key, group in title_groups.items():
    if len(group) > 1:
        print(f"DUPLICATE: {key} — {len(group)} instances")
```

If duplicates are found, keep the instance in the canonical folder
and delete the rest, then renumber to close gaps.

## Prerequisites

This skill depends on the installed **jama-editor** skill for API
access (`~/.config/chipagents/auto/skills/jama-editor/scripts/client.py`,
override with env `JAMA_EDITOR_SCRIPTS`). All pre-flight checks from
that skill apply here.

- Source rule: requirements come from the specification only. RTL,
  Yoda or register CSVs are never a requirement source.

### 1. Jama API Credentials

Existence check only — never read, grep or print the credential file:

```tcsh
test -f ~/.config/jama/config.toml
echo $status
```

- `0` = present. Otherwise ask the user to configure Jama (`/mcp` or
  the jama-editor setup); never ask for credentials in chat.
- Connection check: Jama MCP `search_items` on a known key (read-only).

### 2. Python Runtime

```tcsh
which uv
```

### 3. User-Provided Inputs

Before starting, collect these from the user:

| Input | Description | Example |
|-------|-------------|---------|
| **Specification file** | Path to the document containing requirements | `docs/my_ip_spec.html` |
| **Jama project ID** | Target Jama project | `982` |
| **Parent container ID** | Jama item ID under which to create the hierarchy | `11694800` |
| **Jama base URL** | Instance URL (usually default) | `https://analog.jamacloud.com` |
| **Requirement prefix** | Name prefix for `REQ_PREFIX` | `MDMA-REQ` |
| **Import approval** | User approves the dry-run report before any Jama write | yes / no |

## Workflow

### Phase 0: Build the Name Inventory and Generic Mapping

**Before** parsing requirements, scan the specification to build a
complete inventory of all implementation-specific names. This
prevents multi-pass remediation.

#### Steps

1. Scan the spec for all register names, signal names, clock names,
   reset names, parameter names, and bit-field references.
2. For each name, assign a generic functional description (see
   Genericization Rules table above).
3. For each name, assign a canonical folder where its definition
   requirement will live.
4. Record the mapping in a Python dict for use during extraction:

```python
GENERIC_MAP = {
    "REG_A": "control register",
    "REG_B": "configuration register",
    "STATUS": "status register",
    "ip_out_a": "primary output",
    "ip_out_b": "secondary output",
    "mode_sel": "mode selection input",
    "bus_clk": "bus clock",
    "func_clk": "functional clock",
    "DATA_WIDTH": "data width parameter",
    # ... all names from the spec
}
```

5. Check for inclusive language violations (master→initiator,
   slave→target) and add to the map.

### Phase 1: Parse the Specification

Read the specification document and extract a structured list of
sections and requirements.

#### Supported Input Formats

| Format | Tools to Use |
|--------|-------------|
| HTML | `View`, `searchInFile`, `GrepTool` |
| PDF | `View`, `queryFileWithEmbeddings`, `pdfMarkdown` |
| Markdown | `View`, `searchInFile` |

#### What to Extract

For each **section**:
- Section title (used as folder name)
- Section description (1-sentence summary, used as folder description)

For each **requirement** within a section:
- Sequential requirement number (assigned in folder order)
- Requirement name/title (no signal names — describe function)
- Full description as HTML using **only generic names** from the
  GENERIC_MAP (no implementation-specific identifiers; no `<code>` tags)
- List of source document keys (e.g., `PROJ-SPEC-1234`)

#### Extraction Guidelines

1. **View the entire document first** to understand its structure (sections, tables, requirement format)
2. **Identify the requirement ID pattern** — look for consistent prefixes like `XX-REQ-NNN`
3. **Identify the source key pattern** — look for document keys like `PROJ-TYPE-NNNN`
4. **Map each requirement to its section** by document structure (headings, table grouping, etc.)
5. **Preserve HTML formatting** in descriptions — convert lists to `<ul>/<ol>`, but do NOT use `<code>` tags anywhere in requirement text
6. **Decompose every requirement during extraction** — do not defer atomicity to a later step. Apply the decomposition triggers from the Atomicity Rules section as you extract each requirement. If the spec text contains a composite statement, split it into multiple atomic requirements immediately.
7. **Apply genericization during extraction** — replace every implementation-specific name with its generic description from GENERIC_MAP as you write each requirement. Never defer genericization to a remediation pass.
8. **Apply inclusive language** — replace master/slave with initiator/target as you extract.
9. **Create one definition requirement per register/signal/parameter** — place it in the canonical folder only. Do not duplicate definitions across folders.

#### Atomicity During Extraction

For each requirement found in the specification:

1. Count the number of independent "shall" assertions
2. Check for enumerated lists of independent behaviors
3. Check for combined trigger/clear or behavior/preservation patterns
4. If **any** decomposition trigger fires → split into N atomic children, each getting the next sequential number
5. Assign each child only the source specs that justify **that specific** assertion

**Example**: The spec says:
> "The IP shall support a configurable 7-bit target address via targetAddr[6:0]. The IP shall respond only to matching addresses."

This has two independent assertions → extract as:
- `XX-REQ-028: Configurable 7-bit Address Input` — configurable address input
- `XX-REQ-029: Address Filtering` — respond only to matching, ignore others

Note: Generic descriptions used ("address input", not "targetAddr[6:0]").

### Phase 2: Build the Import Data Structure

Organize extracted data into the section/requirement hierarchy.
Use `scripts/import_requirements.py` as a template — copy it to
`.tmp/` with a timestamp and populate the `SECTIONS` list.

Each section entry follows this structure:

```python
SECTIONS = [
    ("Section Title",                          # folder name
     "<p>Brief section description.</p>",      # folder description HTML
     [
         ("XX-REQ-001: Requirement Name",      # requirement name
          "<p>The IP shall ...</p>",            # body HTML, no footer
          ["KEY-1", "KEY-2"]),                  # Connection keys; footer added by script
         # ... more requirements
     ]),
    # ... more sections
]
```

### Phase 2.5: Atomicity Validation Gate

Before proceeding to source resolution and Jama import, **every
requirement in the SECTIONS list must pass the atomicity checklist**.
This is a mandatory gate — do not skip it.

#### Validation Procedure

For each requirement in every section, verify:

| # | Check | Pass Criteria |
|---|-------|---------------|
| 1 | Single "shall" | Description contains exactly one "shall" assertion |
| 2 | No conjunction of independent behaviors | No "and shall", "shall also", "additionally shall" joining independent behaviors |
| 3 | No enumerated behavior lists | No `<ul>` or `<ol>` where each item is an independently testable behavior |
| 4 | No mixed trigger/clear | Does not combine an assertion condition with a separate clear/reset condition |
| 5 | No behavior + preservation | Does not combine "do X" with "without affecting Y" as independently testable claims |
| 6 | One stimulus → one response | A DV engineer can write exactly one test: apply stimulus, check one outcome |
| 7 | Source specificity | Source links cite only specs that justify THIS assertion, not a superset |

#### What to Do When Validation Fails

1. Identify which decomposition trigger fired
2. Split the requirement into N atomic children with the next sequential numbers (no letter suffixes); renumber the rest
3. Assign each child its specific source subset
4. Replace the original entry in SECTIONS with the N children
5. Re-validate the children

#### Automated Validation Helper

The import script runs `validate_atomicity()` and the Phase 5 audit
(`audit()`) on SECTIONS before any Jama access:

```tcsh
uv run .tmp/import_reqs_<ts>.py --dry-run
```

- Audit findings (numbering, duplicates, identifiers in titles/bodies
  from GENERIC_MAP, inclusive language, forbidden HTML, missing
  Connection keys) block the import.
- Atomicity warnings block the import until reviewed; after each
  warning is split or confirmed, run with `--accept-warnings`.
- Show the dry-run report to the user and get approval before import.

### Phase 3: Resolve Source Document Keys

Before creating Jama items, resolve all unique source document keys
to Jama item IDs using the REST API:

```python
resp = requests.get(
    f"{JAMA_URL}/rest/v1/abstractitems",
    headers=headers,
    params={"documentKey": doc_key, "project": PROJECT_ID}
)
data = resp.json().get("data", [])
if data:
    key_to_id[doc_key] = data[0]["id"]
```

Then generate hyperlinks in the format:

```html
<a href="https://analog.jamacloud.com/perspective.req#/items/{ITEM_ID}?projectId={PROJECT_ID}">{DOC_KEY}</a>
```

### Phase 4: Create the Jama Hierarchy

For each section:
1. Create a **folder** under the parent container
2. For each requirement in the section, create a **requirement** item under the folder

The template imports from the jama-editor scripts directory:

```python
sys.path.insert(0, str(JAMA_EDITOR_SCRIPTS))
from client import (set_project_id, create_folder, create_requirement,
                    _get_auth_token)
from setup_jama import get_jama_url
from jama_utils import get_session
```

- Created folder / requirement IDs are written to
  `spec2req_import_result.json` (`--out` to change).

### Phase 5: Verify and Audit

After import, run a comprehensive audit:

#### 5a. Summary Table

```
| Section               | Folder ID  | Reqs |
|-----------------------|------------|------|
| Clock Architecture    | 11800123   | 4    |
| Counter Operation     | 11800456   | 6    |
| ...                   | ...        | ...  |
```

#### 5b. Deduplication Check

Verify no register/signal/parameter title appears more than once.
If duplicates exist, keep the canonical-folder instance and delete
the rest. Renumber to close gaps.

#### 5c. Genericization Audit

The script audit covers GENERIC_MAP names automatically; additionally
scan all items for implementation-specific names using the full
pattern list (registers, signals, clocks, resets, parameters,
bit-fields). Exclude false positives where common English words
(e.g., "load" as a verb) match a register name pattern.

#### 5d. Inclusive Language Audit

Scan all items for "master", "slave", "whitelist", "blacklist".

#### 5e. Numbering Verification

Confirm sequential numbering XX-REQ-001..NNN with no gaps.

### Phase 6: Completeness Review

After Phase 5 audit passes, perform a **second pass as reviewer**:
re-read the entire specification section-by-section and verify that
every behavioral clause, constraint, and interface definition is
covered by at least one atomic requirement in Jama.

This is a **mandatory gate before sign-off**. Phase 5 only checks
quality of existing requirements; Phase 6 checks that nothing was
missed.

#### 6a. Traceability Matrix

Build a matrix mapping every spec section/clause to the requirement(s)
that cover it. Process every section in document order:

| Spec Clause | Covering Requirement(s) | Status |
|-------------|------------------------|--------|
| §N.N [clause title] | XX-REQ-NNN | COVERED |
| §N.N [clause title] | — | **GAP** |
| §N.N [clause title] | XX-REQ-NNN (partial) | **PARTIAL** |
| §N.N [clause title] | (diagram only) | **IMPLICIT** |

Record every behavioral statement, constraint, register definition,
signal interface, and protocol rule as a separate row. Do not skip
sections that appear descriptive — they may contain normative
constraints.

#### 6b. Finding Classifications

| Classification | Definition | Action |
|---------------|------------|--------|
| **GAP** | Spec clause has zero covering requirements | Extract new atomic requirement(s), assign next sequential #, import |
| **ORPHAN** | Requirement has no traceable spec clause | Link to correct clause, or remove if derived from assumption |
| **PARTIAL** | Clause is only half-covered — one or more assertions missing | Decompose further: split existing req or add missing child assertion |
| **IMPLICIT** | Behavior implied by diagram/table but not stated in text | Flag for spec author clarification; create provisional req marked "pending spec update" |

#### 6c. Review Procedure

1. Re-read every section of the specification using `View` /
   `queryFileWithEmbeddings` / `pdfMarkdown` as appropriate.
2. For each behavioral clause, search the imported requirement set
   for a matching assertion.
3. Record the clause → requirement mapping in the traceability matrix.
4. Flag any clause with zero covering requirements as a **GAP**.
5. Flag any requirement whose Connection footer does not point to a
   real spec clause as an **ORPHAN**.
6. Flag any clause where the covering requirement addresses only part
   of the stated behavior as **PARTIAL**.
7. Flag any behavior visible only in timing diagrams or tables (not
   prose) as **IMPLICIT** and request spec text confirmation.
8. For each GAP/PARTIAL: extract new atomic requirements, apply all
   Phase 0–2 rules (atomicity, genericization, inclusive language),
   and import via `scripts/import_requirements.py` (new SECTIONS only).
9. For each ORPHAN: either link to the correct spec clause by updating
   the Connection footer, or delete and renumber.
10. Re-run Phase 5 audit on all newly added requirements.
11. Repeat until the traceability matrix shows 100% COVERED with
    zero ORPHANs.

#### 6d. Sign-Off Criteria

- Every spec clause has at least one covering requirement → **COVERED**
- No requirement exists without a traceable spec clause → **0 ORPHANs**
- All newly added requirements pass Phase 5 audit → **AUDIT CLEAN**
- IMPLICIT items either resolved by spec update or explicitly accepted
  as provisional

#### Common Gap Root Causes

| Root Cause | Description | Prevention |
|------------|-------------|------------|
| Conjunction child dropped | A composite was split but one child assertion was silently omitted during script population | Run `validate_atomicity()` before import; Phase 6 catches survivors |
| Section misidentified as informative | A descriptive section heading led to skipping normative constraints inside it | Treat every spec section as normative unless explicitly labelled "informative" or "non-normative" |
| Preservation constraint missed | A "without affecting X" or "without driving Y" clause was not extracted as a separate requirement | Grep spec for "without" and "shall not" to find preservation constraints |
| Visual-only behavior | A behavior is specified only in a timing diagram, waveform, or table — not in prose | Run `pdfMarkdown` on all diagram and table pages; never rely on text extraction alone for PDFs |
| Multi-clause sentence | A single sentence contains two or more independent "shall" statements separated by punctuation rather than "and" | Read each sentence in full; count clause boundaries, not just "and" |
| Default / reset value omitted | A register default or reset value is stated in a table but no requirement captures it | Cross-reference every register table row against the requirement set |

## HTML Description Format

### Requirement Body

Use standard HTML for requirement descriptions. Do NOT use `<code>`
tags — all text including signal names, parameters, and register
names must be plain text in the same font as surrounding content.

```html
<p>The [component] shall [action verb] [object] [conditions].</p>
<ul>
<li><strong>Condition A:</strong> description</li>
<li><strong>Condition B:</strong> description</li>
</ul>
```

**Forbidden HTML elements in descriptions:**

| Tag | Why Forbidden | Use Instead |
|-----|--------------|-------------|
| `<code>` | Applies monospace font to signal/parameter names | Plain text |
| `<font color=...>` | Adds colored text | Remove; use default black |
| `<span style="color:...">` | Adds colored text via inline style | Remove; use default black |

### Connection Traceability Footer

Append the connection field after a 2-line spacer:

```html
<br><br>
<p><strong>Connection:</strong> <a href="...">KEY-1</a>, <a href="...">KEY-2</a></p>
```

### Assembling Full Description

```python
def make_description(body_html, source_keys, key_to_id, project_id, jama_url):
    """Build a complete requirement description with hyperlinked connections."""
    links = []
    for key in source_keys:
        if key in key_to_id:
            url = (f"{jama_url}/perspective.req"
                   f"#/items/{key_to_id[key]}?projectId={project_id}")
            links.append(f'<a href="{url}">{key}</a>')
        else:
            links.append(key)
    conn_html = ", ".join(links)
    return (body_html
            + "<br><br>"
            + f"<p><strong>Connection:</strong> {conn_html}</p>")
```

## Script Reference

### `scripts/import_requirements.py`

Template import script. Copy to `.tmp/` and populate with extracted data:

```tcsh
mkdir -p .tmp
set tmp_file = ".tmp/import_reqs_`date +%Y-%m-%d_%H%M%S`.py"
echo "${tmp_file}"
```

Use the Edit tool to write the populated script, then run:

```tcsh
cd <workspace_root> && uv run ${tmp_file}
```

The template handles:
- Atomicity validation and offline audit (`--dry-run`)
- OAuth authentication (via jama-editor client; credentials never printed)
- Batch document key → item ID resolution
- Folder + requirement creation
- Progress reporting

### Customization Points

When populating the template, modify these constants:

| Constant | Description |
|----------|-------------|
| `PARENT_ID` | Jama container ID to create hierarchy under |
| `PROJECT_ID` | Jama project ID |
| `REQ_PREFIX` | Requirement name prefix (e.g. `MDMA-REQ`) |
| `GENERIC_MAP` | Phase 0 name → generic description map (used by the audit) |
| `ALL_DOC_KEYS` | Extra source keys (keys in SECTIONS are collected automatically) |
| `SECTIONS` | List of `(title, description, [(name, body_html, [keys])])` tuples; the script appends the Connection footer |

## Post-Import Operations

### Rename Folders

To remove numbering prefixes or rename sections:

```python
from client import rename_item
rename_item(folder_id, "New Name Without Number")
```

### Add Traceability Links

Create "Traces To" or "Derives From" relationships between imported
requirements and upstream/downstream items:

```python
from client import create_traces_to_link, create_derives_from_link

create_traces_to_link(stakeholder_req_id, system_req_id)
create_derives_from_link(child_req_id, parent_req_id)
```

### Update Descriptions

To fix or amend a requirement after import:

```python
from client import update_description
update_description(item_id, "<p>Updated description...</p>")
```

### Inserting Requirements and Renumbering

When adding or removing requirements, renumber all subsequent items
to maintain sequential numbering with no gaps:

```python
# After deleting item at position N, renumber N+1..max down by 1
for item_id, old_num, new_num in renumber_list:
    item = fetch(item_id)
    old_name = item["fields"]["name"]
    new_name = re.sub(
        rf'^XX-REQ-{old_num:03d}:',
        f'XX-REQ-{new_num:03d}:',
        old_name)
    item["fields"]["name"] = new_name
    put(item)
```

**Note:** The Jama REST API cannot reliably reorder siblings — new
items always appear at the end of the folder. The user must manually
drag items to the correct position in the Jama UI.

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| `WARNING: KEY not found` | Document key doesn't exist in project | Verify key spelling; check correct project ID |
| `401 Unauthorized` | Expired token or invalid credentials | Re-run; if it persists ask the user to update the Jama credentials (never request them in chat) |
| `400 Bad Request` | Malformed HTML or missing fields | Check HTML for unclosed tags |
| Timeout | Too many API calls | Increase `--timeout` on `uv run`; split into batches |
| New item at wrong position | Jama API ignores `sortOrder` for ordering | Manual drag in Jama UI; API cannot reorder siblings |
| PUT returns 400 on rename | Full item payload required | GET item first, modify `fields.name`, PUT entire item back |

## Example End-to-End Session

```
User: Import requirements from docs/my_ip_spec.html into Jama project 982,
      container 11694800

Agent:
Phase 0: Build Name Inventory
  - Scan spec → find 8 registers, 6 signals, 2 clocks, 2 resets, 3 parameters
  - Build GENERIC_MAP with 21 entries
  - Check inclusive language → replace 2 "slave" occurrences with "target"
  - Assign canonical folders for each definition requirement

Phase 1: Parse Specification
  - View docs/my_ip_spec.html to understand structure
  - Extract 16 sections with 40 spec-level requirements

Phase 2: Build Import Data
  - Decompose composites → 40 spec reqs become 65 atomic requirements
  - Apply genericization → all 65 descriptions use GENERIC_MAP names only
  - Create 11 definition requirements in canonical folders (one per register/signal)
  - Assign sequential numbering: XX-REQ-001..065

Phase 3: Resolve Source Keys
  - Collect 30 unique document keys, resolve all 30 to Jama item IDs

Phase 4: Import
  - Copy scripts/import_requirements.py to .tmp/import_reqs_<ts>.py
  - Populate SECTIONS list with all 65 atomic requirements
  - Run validate_atomicity() — 0 warnings, all pass
  - Run: uv run .tmp/import_reqs_<ts>.py
  - Created 16 folders, 65 requirements, 30/30 connections resolved

Phase 5: Verify and Audit
  - Deduplication check: 0 duplicates found
  - Genericization audit: 0 implementation-specific names found
    (3 false positives: "load" as verb — excluded)
  - Inclusive language audit: 0 violations
  - Numbering: XX-REQ-001..065 sequential, no gaps

Phase 6: Completeness Review
  - Re-read specification section-by-section ([N] sections total)
  - Built traceability matrix: [N] requirements mapped to [N] spec clauses
  - Found [N] GAPs: clauses with zero covering requirements
  - Found [N] PARTIALs: clauses where one or more assertions were missing
  - Found 0 ORPHANs
  - Resolution: extracted [N] new atomic requirements to close all gaps;
    applied Phase 0–2 rules (atomicity, genericization, inclusive language)
  - Re-ran Phase 5 audit on all new requirements → 0 violations
  - Final traceability matrix: [N]/[N] sections COVERED, 0 ORPHANs
  - Sign-off criteria met
```
