#!/usr/bin/env python3
"""Validate configuration and routing fixtures; optionally check names-only node inventory."""
import argparse
import ipaddress
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.rules import ROOT, active_lines, first_match, read_json, render


def check_cases(rules, cases):
    failures = []
    for case in cases:
        request = {k: case[k] for k in ("domain", "ip", "country") if k in case}
        matched = first_match(rules, **request)
        if matched.policy != case["policy"]:
            failures.append(f"{case['name']}: expected {case['policy']}, got {matched.policy} ({matched.origin})")
    return failures


def node_members(groups, names, region_groups):
    matches = {}
    for name in region_groups:
        pattern = re.compile(groups[name]["options"]["policy-regex-filter"])
        matches[name] = [n for n in names if pattern.search(n)]
    ambiguous = {n: [g for g, members in matches.items() if n in members] for n in names}
    ambiguous = {n: gs for n, gs in ambiguous.items() if len(gs) > 1}
    return matches, ambiguous


def check_regex_cases(groups, cases):
    failures = []
    for case in cases:
        matches, _ = node_members(groups, [case["name"]], list(case["groups_under_test"]))
        actual = sorted(name for name, nodes in matches.items() if nodes)
        if actual != sorted(case["expected"]):
            failures.append(f"Node regex {case['name']}: expected {case['expected']}, got {actual}")
    return failures


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--nodes", type=Path, help="UTF-8 file: one node display name per line; no credentials")
    parser.add_argument("--require-group", action="append", default=[], help="Fail if this region has no candidate; repeatable")
    parser.add_argument("--explain", metavar="DOMAIN", help="Explain first static match, without DNS requests")
    parser.add_argument("--ip", help="Known destination IP for the static explanation")
    parser.add_argument("--country", help="Caller-supplied two-letter GeoIP fixture, not a real lookup")
    args = parser.parse_args()
    try:
        text, rules, groups, report = render()
        if (ROOT / "Shadowrocket.conf").read_text(encoding="utf-8") != text:
            raise ValueError("Generated configuration is stale; run scripts/build.py")
        regions = read_json(ROOT / "rules/order.json")["region_groups"]
        for name in regions:
            group = groups[name]
            if group["type"] != "select" or group["options"].get("policy-select-name") != "REJECT":
                raise ValueError(f"Region must initially be an explicit manual REJECT selector: {name}")
        cases = read_json(ROOT / "tests/routing-cases.json")
        failures = check_cases(rules, cases)
        regex_cases = read_json(ROOT / "tests/node-cases.json")
        failures += check_regex_cases(groups, regex_cases)
        if failures:
            raise ValueError("\n".join(failures))
        print(f"OK: {len(groups)} groups, {len(rules)} rules, {len(cases)} routing cases, {len(regex_cases)} node-name cases")
        if args.require_group and not args.nodes:
            raise ValueError("--require-group needs --nodes")
        if args.nodes:
            names = [line for _, line in active_lines(args.nodes.read_text(encoding="utf-8"))]
            if not names or len(set(names)) != len(names):
                raise ValueError("Node inventory must be nonempty and contain unique display names")
            if any("://" in n or re.search(r"(?i)(password|token|secret)\s*=", n) for n in names):
                raise ValueError("Use display names only; do not pass subscriptions or credentials")
            matches, ambiguous = node_members(groups, names, regions)
            for name, nodes in matches.items():
                print(f"{name}: {len(nodes)} candidate(s)" + (" — keep unselected" if not nodes else ""))
            if ambiguous:
                raise ValueError("Ambiguous region labels: " + "; ".join(f"{n}: {','.join(gs)}" for n, gs in ambiguous.items()))
            for name in args.require_group:
                if name not in matches:
                    raise ValueError(f"Unknown region group: {name}")
                if not matches[name]:
                    raise ValueError(f"Required region has no candidates: {name}")
            print("Names checked only; verify actual group membership, exit IP and service access in the client.")
        if args.ip:
            ipaddress.ip_address(args.ip)
        if args.country and not re.fullmatch(r"[A-Z]{2}", args.country):
            raise ValueError("--country must be an uppercase two-letter code")
        if args.explain or args.ip:
            matched = first_match(rules, domain=args.explain or "", ip=args.ip, country=args.country)
            print(f"MATCH: {matched.text()}\nSOURCE: {matched.origin}")
            print("Static Rule match only; tunnel bypass, live DNS/GeoIP and saved client choices are outside this model.")
        return 0
    except (ValueError, KeyError, OSError, StopIteration) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
