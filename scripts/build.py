#!/usr/bin/env python3
"""Build a self-contained Shadowrocket.conf using only locked local inputs."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.rules import ROOT, render


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Fail if the committed output is stale")
    args = parser.parse_args()
    try:
        text, _, _, report = render()
        output = ROOT / "Shadowrocket.conf"
        if args.check:
            if not output.exists() or output.read_text(encoding="utf-8") != text:
                raise ValueError("Shadowrocket.conf is stale; run python3 scripts/build.py")
        else:
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
