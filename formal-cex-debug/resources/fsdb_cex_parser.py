#!/usr/bin/env python3
"""
FSDB CEX Parser — Verdi NPI (pynpi) based waveform reader for
formal counter-example debug.

Usage:
    python3 fsdb_cex_parser.py --fsdb <file> --list-signals [--scope <path>]
    python3 fsdb_cex_parser.py --fsdb <file> --signals <s1,s2,...> [--start T] [--end T]
    python3 fsdb_cex_parser.py --fsdb <file> --transitions <signal> [--start T] [--end T]
    python3 fsdb_cex_parser.py --fsdb <file> --trace <signal> --rtl-dir <path> [--depth N]
    python3 fsdb_cex_parser.py --fsdb <file> --summary

Requires:
    VERDI_HOME set to Verdi installation path
    LD_LIBRARY_PATH includes $VERDI_HOME/share/NPI/lib/linux64
    sys.path includes $VERDI_HOME/share/NPI/python/pynpi
"""

import argparse
import json
import os
import re
import sys

def setup_npi():
    """Add pynpi to path and import."""
    verdi_home = os.environ.get("VERDI_HOME")
    if not verdi_home:
        print("ERROR: VERDI_HOME not set", file=sys.stderr)
        sys.exit(1)

    npi_python = os.path.join(verdi_home, "share", "NPI", "python", "pynpi")
    if npi_python not in sys.path:
        sys.path.insert(0, npi_python)

    npi_lib = os.path.join(verdi_home, "share", "NPI", "lib", "linux64")
    ld_path = os.environ.get("LD_LIBRARY_PATH", "")
    if npi_lib not in ld_path:
        os.environ["LD_LIBRARY_PATH"] = npi_lib + ":" + ld_path

    try:
        import pynpi.npisys as npisys
        import pynpi.waveform as waveform
        return npisys, waveform
    except ImportError as e:
        print(f"ERROR: Cannot import pynpi: {e}", file=sys.stderr)
        print(f"  Check: {npi_python}", file=sys.stderr)
        sys.exit(1)


def open_fsdb(waveform_mod, fsdb_path):
    """Open FSDB file and return the database handle."""
    if not os.path.exists(fsdb_path):
        print(f"ERROR: File not found: {fsdb_path}", file=sys.stderr)
        sys.exit(1)
    db = waveform_mod.open(fsdb_path)
    if db is None:
        print(f"ERROR: Cannot open FSDB: {fsdb_path}", file=sys.stderr)
        sys.exit(1)
    return db


def get_time_info(db):
    """Return start time, end time, timescale."""
    return {
        "start_time": db.min_time(),
        "end_time": db.max_time(),
        "timescale": db.timescale_str(),
    }


def list_signals(db, scope="", max_depth=2):
    """List all signals under a scope."""
    results = []
    scopes = db.get_scopes(scope, depth=max_depth)
    for sc in scopes:
        signals = db.get_signals(sc.path)
        for sig in signals:
            results.append({
                "path": sig.path,
                "width": sig.width,
                "type": str(sig.type),
                "scope": sc.path,
            })
    return results


def get_signal_values(db, signal_names, start_time=None, end_time=None):
    """Get value changes for multiple signals."""
    if start_time is None:
        start_time = db.min_time()
    if end_time is None:
        end_time = db.max_time()

    results = {}
    for name in signal_names:
        changes = db.get_signal_changes(name, start_time, end_time)
        results[name] = [{"time": t, "value": v} for t, v in changes]
    return results


def get_signal_at_time(db, signal_name, time):
    """Get signal value at a specific time."""
    return db.get_signal_value_at_time(signal_name, time)


def get_transitions(db, signal_name, start_time=None, end_time=None):
    """Get all transitions for a signal."""
    if start_time is None:
        start_time = db.min_time()
    if end_time is None:
        end_time = db.max_time()

    changes = db.get_signal_changes(signal_name, start_time, end_time)
    transitions = []
    for i in range(len(changes) - 1):
        t_from, v_from = changes[i]
        t_to, v_to = changes[i + 1]
        transitions.append({
            "time": t_to,
            "from": v_from,
            "to": v_to,
        })
    return transitions


def find_clock_period(db, clk_name):
    """Detect clock period from transitions."""
    changes = db.get_signal_changes(clk_name)
    rising_edges = []
    for i in range(len(changes) - 1):
        if changes[i][1] == "0" and changes[i + 1][1] == "1":
            rising_edges.append(changes[i + 1][0])
    if len(rising_edges) >= 2:
        return rising_edges[1] - rising_edges[0]
    return None


def build_cycle_table(db, signal_names, clk_name, start_time=None, end_time=None):
    """Build cycle-by-cycle signal value table aligned to clock rising edges."""
    if start_time is None:
        start_time = db.min_time()
    if end_time is None:
        end_time = db.max_time()

    clk_changes = db.get_signal_changes(clk_name, start_time, end_time)
    rising_edges = []
    for i in range(len(clk_changes) - 1):
        if clk_changes[i][1] == "0" and clk_changes[i + 1][1] == "1":
            rising_edges.append(clk_changes[i + 1][0])

    table = []
    for cycle, edge_time in enumerate(rising_edges):
        row = {"cycle": cycle, "time": edge_time}
        for sig in signal_names:
            row[sig] = db.get_signal_value_at_time(sig, edge_time)
        table.append(row)
    return table


def trace_signal_rtl(signal_name, rtl_dir, depth=3):
    """
    Parse RTL files to find the driver chain for a signal.
    Returns a list of driver entries: {signal, file, line, expression, deps}.
    """
    drivers = []
    current_signal = signal_name.split(".")[-1]
    visited = set()

    for d in range(depth):
        if current_signal in visited:
            break
        visited.add(current_signal)

        found = False
        for root, _, files in os.walk(rtl_dir):
            for fname in files:
                if not fname.endswith((".sv", ".v", ".svh", ".vh")):
                    continue
                fpath = os.path.join(root, fname)
                with open(fpath, "r", errors="replace") as f:
                    lines = f.readlines()
                for i, line in enumerate(lines):
                    stripped = line.strip()
                    pat_assign = rf"\bassign\s+{re.escape(current_signal)}\b"
                    pat_nba = rf"\b{re.escape(current_signal)}\s*<="
                    pat_ba = rf"\b{re.escape(current_signal)}\s*="

                    if (re.search(pat_assign, stripped) or
                        re.search(pat_nba, stripped) or
                        (re.search(pat_ba, stripped) and
                         "==" not in stripped and "!=" not in stripped)):

                        rhs = stripped.split("<=")[-1] if "<=" in stripped else stripped.split("=")[-1]
                        rhs = rhs.strip().rstrip(";")

                        dep_signals = re.findall(r'\b([a-zA-Z_]\w*)\b', rhs)
                        dep_signals = [s for s in dep_signals if s not in (
                            "assign", "if", "else", "begin", "end", "case",
                            "endcase", "always", "posedge", "negedge",
                            "logic", "wire", "reg", "input", "output",
                        )]

                        context_start = max(0, i - 3)
                        context_end = min(len(lines), i + 4)
                        context = "".join(lines[context_start:context_end])

                        drivers.append({
                            "signal": current_signal,
                            "file": os.path.relpath(fpath, rtl_dir),
                            "line": i + 1,
                            "expression": stripped,
                            "context": context,
                            "dependencies": dep_signals,
                        })
                        if dep_signals:
                            current_signal = dep_signals[0]
                        found = True
                        break
                if found:
                    break
            if found:
                break
        if not found:
            drivers.append({
                "signal": current_signal,
                "file": "NOT_FOUND",
                "line": 0,
                "expression": "",
                "context": "",
                "dependencies": [],
            })
            break

    return drivers


def cex_summary(db, clk_name=None):
    """Print a summary of the CEX waveform."""
    info = get_time_info(db)
    result = {
        "start_time": info["start_time"],
        "end_time": info["end_time"],
        "timescale": info["timescale"],
    }

    if clk_name:
        period = find_clock_period(db, clk_name)
        if period:
            result["clock_period"] = period
            duration = info["end_time"] - info["start_time"]
            result["total_cycles"] = duration // period

    all_signals = db.get_signals()
    result["total_signals"] = len(all_signals)

    scopes = db.get_scopes("", depth=1)
    result["top_scopes"] = [s.path for s in scopes]

    return result


def main():
    parser = argparse.ArgumentParser(description="FSDB CEX Parser for formal debug")
    parser.add_argument("--fsdb", required=True, help="Path to FSDB file")
    parser.add_argument("--list-signals", action="store_true", help="List all signals")
    parser.add_argument("--scope", default="", help="Scope filter for signal listing")
    parser.add_argument("--signals", help="Comma-separated signal names for value extraction")
    parser.add_argument("--transitions", help="Signal name for transition listing")
    parser.add_argument("--trace", help="Signal name for RTL backward trace")
    parser.add_argument("--rtl-dir", help="RTL directory for backward trace")
    parser.add_argument("--depth", type=int, default=3, help="Trace depth (default: 3)")
    parser.add_argument("--start", type=int, help="Start time")
    parser.add_argument("--end", type=int, help="End time")
    parser.add_argument("--clock", help="Clock signal name")
    parser.add_argument("--cycle-table", action="store_true", help="Build cycle-by-cycle table")
    parser.add_argument("--summary", action="store_true", help="Print CEX summary")
    parser.add_argument("--format", choices=["json", "text"], default="json", help="Output format")
    args = parser.parse_args()

    npisys, waveform_mod = setup_npi()
    npisys.init([""])
    db = open_fsdb(waveform_mod, args.fsdb)

    try:
        if args.summary:
            result = cex_summary(db, args.clock)
            print(json.dumps(result, indent=2))

        elif args.list_signals:
            signals = list_signals(db, args.scope)
            print(json.dumps(signals, indent=2))

        elif args.signals:
            sig_names = [s.strip() for s in args.signals.split(",")]
            if args.cycle_table and args.clock:
                table = build_cycle_table(db, sig_names, args.clock, args.start, args.end)
                print(json.dumps(table, indent=2))
            else:
                values = get_signal_values(db, sig_names, args.start, args.end)
                print(json.dumps(values, indent=2))

        elif args.transitions:
            trans = get_transitions(db, args.transitions, args.start, args.end)
            print(json.dumps(trans, indent=2))

        elif args.trace:
            if not args.rtl_dir:
                print("ERROR: --rtl-dir required for --trace", file=sys.stderr)
                sys.exit(1)
            drivers = trace_signal_rtl(args.trace, args.rtl_dir, args.depth)
            print(json.dumps(drivers, indent=2))

        else:
            parser.print_help()

    finally:
        db.close()
        npisys.end()


if __name__ == "__main__":
    main()
