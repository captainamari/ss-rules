#!/usr/bin/env python3
"""Build the main profile, versioned rulesets and complete backup profile offline."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.rules import ROOT, render, safe_path


def main():
    try:
        outputs, _, _, report = render()
        # Never overwrite a published version with different bytes or delete an
        # older version: installed profiles can still reference those URLs.
        for name, content in outputs.items():
            path = safe_path(ROOT, name)
            if name.startswith("rulesets/") and path.exists() and path.read_bytes() != content.encode("utf-8"):
                raise ValueError(f"Published ruleset content differs: {name}")
        for name, content in outputs.items():
            path = safe_path(ROOT, name)
            path.parent.mkdir(parents=True, exist_ok=True)
            temporary = path.with_name(path.name + ".tmp")
            temporary.write_text(content, encoding="utf-8")
            temporary.replace(path)
        report_path = ROOT / ".local/build-report.json"
        report_path.parent.mkdir(exist_ok=True)
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"OK: {report['rule_count']} rules; {report['ruleset_count']} versioned lists; "
              f"{report['main_rule_count']} main entries; version {report['ruleset_version']}")
        for name in ("Shadowrocket.conf", "Shadowrocket-full.conf"):
            print(f"{name}: {len(outputs[name].encode('utf-8')):,} bytes")
        return 0
    except (ValueError, KeyError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
