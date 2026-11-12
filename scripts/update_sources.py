#!/usr/bin/env python3
"""Stage upstream snapshots at an explicit commit; never overwrite live inputs automatically."""
import argparse
import hashlib
import json
import re
import sys
import tempfile
from pathlib import Path
from urllib.request import urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.rules import ROOT, read_json, safe_path


def stage(source, revision):
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ValueError("Use an explicit 40-character commit SHA, not a moving branch")
    manifest = read_json(ROOT / "sources.json")
    selected = [s for s in manifest["sources"] if s["source"] == source]
    if not selected:
        raise ValueError("Unknown source")
    payloads = []
    for item in selected:
        url = f"https://raw.githubusercontent.com/{item['repository']}/{revision}/{item['path']}"
        with urlopen(url, timeout=30) as response:
            data = response.read(2_000_001)
        if len(data) > 2_000_000 or not data or b"<html" in data[:300].lower():
            raise ValueError(f"Invalid/oversized snapshot: {item['path']}")
        data.decode("utf-8", errors="strict")
        item["revision"] = revision
        item["sha256"] = hashlib.sha256(data).hexdigest()
        payloads.append((item["local"], data))
    stage_root = ROOT / ".local"
    stage_root.mkdir(exist_ok=True)
    target = Path(tempfile.mkdtemp(prefix=f"upstream-{source}-{revision[:8]}-", dir=stage_root))
    for path, data in payloads:
        dest = safe_path(target, path)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
    (target / "sources.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return target


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, choices=["lingjing", "blackmatrix7"])
    parser.add_argument("--revision", required=True)
    args = parser.parse_args()
    try:
        target = stage(args.source, args.revision)
        print(f"Staged at {target.relative_to(ROOT)}; active files were not changed.")
        print("Review vendor diffs and source license changes; then copy reviewed snapshots and sources.json into the repository.")
        print("Manually reconcile rules/*.list derived from AI lists; rebuild and review the diff before committing.")
        return 0
    except (ValueError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
