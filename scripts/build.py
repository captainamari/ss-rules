#!/usr/bin/env python3
"""Build a self-contained Shadowrocket.conf using only locked local inputs."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.rules import ROOT, render


def main():
    try:
        text, _, _, report = render()
        output = ROOT / "Shadowrocket.conf"
        output.write_text(text, encoding="utf-8")
        report_path = ROOT / ".local/build-report.json"
        report_path.parent.mkdir(exist_ok=True)
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"OK: {report['rule_count']} rules; {len(report['duplicates'])} same-policy duplicates removed; "
              f"{len(report['cross_policy_duplicates'])} exact overlaps resolved by declared order; "
              f"{len(report['shadowed'])} broader cross-policy matches recorded for review")
        return 0
    except (ValueError, KeyError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
