#!/usr/bin/env python3
"""
Generic Formal Verification VPlan Generator Template
=====================================================
Generates Cadence vManager-compatible .vplanx (gzip XML) from assertion definitions.

Usage:
  1. Copy this template to your FPV env directory
  2. Edit the CONFIGURATION section below with your IP details
  3. Populate the assertion lists in the DATA section
  4. Run: python3 gen_vplanx.py

Output:
  <IP_NAME>_VPLAN.xml    — human-readable XML
  <IP_NAME>_VPLAN.vplanx — gzip-compressed (for vManager)
"""

import uuid
import gzip
import os
from datetime import datetime

# ============================================================================
# CONFIGURATION — Edit these for your IP
# ============================================================================
IP_NAME       = "MY_IP"                    # e.g., "ADIP_SRAM_Controller"
OWNER         = "engineer"                 # e.g., "rgulghan"
OUTPUT_DIR    = "."                        # Directory for output files
TOOL_VERSION  = "23.09"
# ============================================================================


def uid():
    """Generate a random UUID for XML id attributes."""
    return str(uuid.uuid4())


def xml_escape(text):
    """Escape XML special characters in attribute values."""
    return (text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;"))


def attr(name, value):
    """Create a single XML attribute element."""
    return f"""<attribute>
    <name>{name}</name>
    <value>{value}</value>
</attribute>"""


def metrics_port(name, kind, details, impl_note="", owner=None, creator=None, planned=False):
    """
    Create a metricsPort XML element (leaf item in vplan).

    Args:
        name:      Display name / assertion label
        kind:      "CHECK" | "COVERAGE" | "TESTCASE"
        details:   Human-readable description (XML-escaped)
        impl_note: SVA expression or implementation guidance (XML-escaped)
        owner:     Owner name (defaults to global OWNER)
        creator:   Creator name (defaults to global OWNER)
        planned:   True for assumptions (assumePlanned=true)
    """
    owner = owner or OWNER
    creator = creator or OWNER
    attrs = [attr("metrics_port_kind", kind), attr("creator", creator)]
    if details:
        attrs.append(attr("details", details))
    if impl_note:
        attrs.append(attr("implementation_note", impl_note))
    attrs.append(attr("owner", owner))
    attrs_str = "\n".join(attrs)
    ap = "true" if planned else "false"
    return f"""                        <metricsPort id="{uid()}">
                            <name>{name}</name>
                            <attributes>
{attrs_str}
                            </attributes>
                            <assumePlanned>{ap}</assumePlanned>
                        </metricsPort>"""


def section_start(name, creator=None, indent=2):
    """Open a section element with name and creator attribute."""
    creator = creator or OWNER
    sp = "    " * indent
    return f"""{sp}<section id="{uid()}">
{sp}    <name>{name}</name>
{sp}    <attributes>
{sp}        <attribute>
{sp}            <name>creator</name>
{sp}            <value>{creator}</value>
{sp}        </attribute>
{sp}    </attributes>
{sp}    <subElements>"""


def section_end(indent=2):
    """Close a section element."""
    sp = "    " * indent
    return f"""{sp}    </subElements>
{sp}</section>"""


def build_section(section_name, items, indent=3, planned=False):
    """
    Build a complete section with metricsPort entries.

    Args:
        section_name: Display name for the section
        items:        List of tuples: (name, kind, details, impl_note)
        indent:       Nesting depth
        planned:      Whether items are assumptions (assumePlanned=true)
    Returns:
        List of XML lines
    """
    lines = []
    lines.append(section_start(section_name, indent=indent))
    for item in items:
        name, kind, details, impl_note = item[:4]
        lines.append(metrics_port(name, kind, details, impl_note, planned=planned))
    lines.append(section_end(indent=indent))
    return lines


def generate_vplanx(sections_config):
    """
    Generate the complete vplanx XML.

    Args:
        sections_config: List of top-level section dicts:
            {
                "name": "Formal Assertions",
                "subsections": [
                    {
                        "name": "Protocol Checks",
                        "items": [(name, kind, details, impl_note), ...],
                        "planned": False
                    },
                    ...
                ]
            }
    Returns:
        XML string
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = []
    lines.append('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>')
    lines.append('<vplanx:plan xmlns:vplanx="http://www.cadence.com/vplanx">')
    lines.append(f'''    <metaData id="{uid()}">
        <name>{IP_NAME}</name>
        <attributes>
            <attribute>
                <name>owner</name>
                <value>{OWNER}</value>
            </attribute>
            <attribute>
                <name>creator</name>
                <value>{OWNER}</value>
            </attribute>
            <attribute>
                <name>path_usage</name>
                <value>RELATIVE_TO_VPLAN</value>
            </attribute>
        </attributes>
        <planId>{uid()}</planId>
        <sourceTool>vManager Planner</sourceTool>
        <toolVersion>{TOOL_VERSION}</toolVersion>
        <schemaVersion>1.0</schemaVersion>
        <buildTime>{now}</buildTime>
    </metaData>''')
    lines.append('    <rootElements>')

    for top_section in sections_config:
        lines.append(section_start(top_section["name"], indent=2))
        for sub in top_section.get("subsections", []):
            planned = sub.get("planned", False)
            lines.extend(build_section(sub["name"], sub["items"], indent=3, planned=planned))
        lines.append(section_end(indent=2))

    lines.append('    </rootElements>')
    lines.append('</vplanx:plan>')
    return "\n".join(lines)


def write_vplanx(xml_content, output_dir=None):
    """Write XML and gzip-compressed .vplanx files."""
    output_dir = output_dir or OUTPUT_DIR
    os.makedirs(output_dir, exist_ok=True)
    xml_path = os.path.join(output_dir, f"{IP_NAME}_VPLAN.xml")
    vplanx_path = os.path.join(output_dir, f"{IP_NAME}_VPLAN.vplanx")

    with open(xml_path, "w") as f:
        f.write(xml_content)

    with open(xml_path, "rb") as f_in:
        with gzip.open(vplanx_path, "wb") as f_out:
            f_out.write(f_in.read())

    return xml_path, vplanx_path


# ============================================================================
# DATA — Populate these lists with your IP's assertions
# ============================================================================
# Each item is a tuple: (label, kind, details, implementation_note)
#
# kind: "CHECK" for assertions/assumptions, "COVERAGE" for covers/CSR/coverage
#
# Example:
#   ("ast_reset_check", "CHECK",
#    "After reset, output must be zero.",
#    "SVA: @(posedge clk) !rstn |-> out == 0")

# -- Assertions: group by feature --
protocol_checks = [
    # ("ast_example", "CHECK", "Description here", "SVA: expression here"),
]

datapath_checks = [
]

control_checks = [
]

interrupt_checks = [
]

xprop_checks = [
]

scoreboard_checks = [
]

# -- Assumptions --
dft_assumptions = [
]

protocol_assumptions = [
]

# -- CSR Registers --
csr_registers = [
    # ("REG_NAME (0xOFF)", "COVERAGE", "CSR check: description", "Backdoor CSR checker ..."),
]

# -- Coverage --
coverage_items = [
    ("Stimuli Coverage", "COVERAGE",
     "Formal stimuli coverage: input combinations explored by proof engine.",
     "check_cov -init -type {stimuli coi proof bound}"),
    ("COI Coverage", "COVERAGE",
     "Cone-of-Influence coverage: RTL signals within the proof cone.",
     "Generated by JasperGold COI analysis."),
    ("Proof Coverage", "COVERAGE",
     "Proof coverage: depth and completeness of bounded proofs.",
     "Generated by JasperGold proof engine."),
    ("Bound Coverage", "COVERAGE",
     "Bound coverage: depth achieved for bounded proofs.",
     "Generated by JasperGold bound analysis."),
]

# ============================================================================
# ASSEMBLY — Build the section hierarchy
# ============================================================================
SECTIONS = [
    {
        "name": "Formal Assertions",
        "subsections": [
            {"name": "Protocol Checks",    "items": protocol_checks},
            {"name": "Datapath Checks",    "items": datapath_checks},
            {"name": "Control Checks",     "items": control_checks},
            {"name": "Interrupt and Status","items": interrupt_checks},
            {"name": "X-Propagation",      "items": xprop_checks},
            {"name": "Scoreboard",         "items": scoreboard_checks},
        ]
    },
    {
        "name": "Assumptions and Constraints",
        "subsections": [
            {"name": "DFT and Reset Constraints",  "items": dft_assumptions,      "planned": True},
            {"name": "Protocol Constraints",        "items": protocol_assumptions, "planned": True},
        ]
    },
    {
        "name": "CSR Verification",
        "subsections": [
            {"name": "Register Map", "items": csr_registers},
        ]
    },
    {
        "name": "Coverage",
        "subsections": [
            {"name": "Formal Coverage", "items": coverage_items},
        ]
    },
]


# ============================================================================
# MAIN
# ============================================================================
if __name__ == "__main__":
    # Filter out empty subsections
    for sec in SECTIONS:
        sec["subsections"] = [s for s in sec["subsections"] if s["items"]]
    SECTIONS = [s for s in SECTIONS if s["subsections"]]

    xml = generate_vplanx(SECTIONS)
    xml_path, vplanx_path = write_vplanx(xml)

    # Summary
    total = 0
    for sec in SECTIONS:
        for sub in sec["subsections"]:
            count = len(sub["items"])
            total += count
            print(f"  {sub['name']}: {count}")
    print(f"  TOTAL: {total}")
    print(f"  XML:    {xml_path}")
    print(f"  VPLANX: {vplanx_path}")
