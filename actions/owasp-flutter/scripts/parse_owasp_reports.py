#!/usr/bin/env python3
"""Aggregate the four OWASP scanner JSON reports into one status file for the security gate.

Usage: parse_owasp_reports.py <project_path> <output_dir>

Reads owasp_m*_scan.json files produced by the M1/M2/M5/M9 scanners, counts
CRITICAL/HIGH findings as blocking and MEDIUM/LOW as informational, copies the
raw reports into <output_dir>, and writes <output_dir>/status-owasp.json in the
uniform gate-status format: {"name", "blocking", "info", "note"}.
"""
import json
import os
import shutil
import sys

REPORTS = {
    "owasp_m1_secrets_scan.json": "M1 secrets",
    "owasp_m2_dependencies_scan.json": "M2 dependencies",
    "owasp_m5_network_scan.json": "M5 network",
    "owasp_m9_storage_scan.json": "M9 storage",
}
BLOCKING_SEVERITIES = {"CRITICAL", "HIGH"}


def main() -> None:
    project = sys.argv[1] if len(sys.argv) > 1 else "."
    outdir = sys.argv[2] if len(sys.argv) > 2 else "secscan"
    os.makedirs(outdir, exist_ok=True)

    total_blocking = 0
    total_info = 0
    parts = []
    missing = []

    for fname, label in REPORTS.items():
        path = os.path.join(project, fname)
        if not os.path.exists(path):
            missing.append(label)
            continue
        try:
            with open(path) as fh:
                data = json.load(fh)
        except (OSError, ValueError):
            missing.append(label + " (unreadable)")
            continue

        blocking = 0
        info = 0
        for finding in data.get("findings", []):
            severity = str(finding.get("severity", "")).upper()
            if severity in BLOCKING_SEVERITIES:
                blocking += 1
            else:
                info += 1
        total_blocking += blocking
        total_info += info
        parts.append(f"{label}: {blocking}/{info}")
        shutil.copy(path, outdir)

    note = "blocking/info per scanner — " + ", ".join(parts) if parts else "no reports produced"
    if missing:
        note += " | did not run: " + ", ".join(missing)

    status = {
        "name": "OWASP Mobile M1/M2/M5/M9",
        "blocking": total_blocking,
        "info": total_info,
        "note": note,
    }
    with open(os.path.join(outdir, "status-owasp.json"), "w") as fh:
        json.dump(status, fh, indent=2)
    print(json.dumps(status, indent=2))


if __name__ == "__main__":
    main()
