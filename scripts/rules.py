"""Small, offline compiler for the deliberately limited rule syntax used here.

This is not a Shadowrocket emulator. DNS, GeoIP databases, tunnels, certificates,
client-selected policies and service availability require device verification.
SPDX-License-Identifier: GPL-2.0-only
"""
from __future__ import annotations

import hashlib
import ipaddress
import json
import re
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILTINS = {"DIRECT", "PROXY", "REJECT"}
DOMAIN_TYPES = {"DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD"}
IP_TYPES = {"IP-CIDR", "IP-CIDR6"}
UPSTREAM_TYPES = DOMAIN_TYPES | IP_TYPES | {"USER-AGENT", "URL-REGEX", "IP-ASN"}


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def safe_path(root: Path, value: str) -> Path:
    path = (root / value).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError(f"Path escapes repository: {value}")
    return path


def active_lines(text: str):
    for number, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if line and not line.startswith("#"):
            yield number, line


def verify_sources(root: Path = ROOT):
    spec = read_json(root / "sources.json")
    if spec.get("schema") != 1:
        raise ValueError("Unsupported sources schema")
    seen = set()
    for source in spec["sources"]:
        path = source["local"]
        if path in seen or not path.startswith("vendor/"):
            raise ValueError(f"Duplicate or invalid vendor path: {path}")
        seen.add(path)
        if not re.fullmatch(r"[0-9a-f]{40}", source["revision"]):
            raise ValueError(f"Source must pin a full commit: {path}")
        digest = hashlib.sha256(safe_path(root, path).read_bytes()).hexdigest()
        if digest != source["sha256"]:
            raise ValueError(f"Upstream snapshot changed without lock update: {path}")
    actual = {p.relative_to(root).as_posix() for p in (root / "vendor").rglob("*") if p.is_file()}
    if actual != seen:
        raise ValueError(f"Untracked/missing vendor snapshots: {actual ^ seen}")


def sections(text: str):
    result = {}
    current = None
    for number, line in active_lines(text):
        if line.startswith("[") and line.endswith("]"):
            current = line[1:-1]
            if current in result:
                raise ValueError(f"Duplicate section: {current}")
            result[current] = []
        elif current is None:
            raise ValueError(f"Line {number} is outside a section")
        else:
            result[current].append(line)
    return result


def groups_from(text: str):
    data = sections(text)
    if data.get("Proxy"):
        raise ValueError("Proxy credentials belong in the client, not this repository")
    result = {}
    for line in data.get("Proxy Group", []):
        name, sep, rhs = line.partition("=")
        name = name.strip()
        if not sep or not name or name in result or name in BUILTINS:
            raise ValueError(f"Invalid/duplicate group: {name}")
        tokens = [s.strip() for s in rhs.split(",")]
        kind = tokens.pop(0)
        if kind not in {"select", "url-test", "fallback"}:
            raise ValueError(f"Unsupported group type: {kind}")
        members, options = [], {}
        for token in tokens:
            if not token:
                raise ValueError(f"Empty group item: {name}")
            if "=" in token:
                key, value = token.split("=", 1)
                if key in options or not value:
                    raise ValueError(f"Duplicate/empty option in {name}: {key}")
                if key not in {"policy-select-name", "policy-regex-filter", "url", "interval", "timeout", "tolerance"}:
                    raise ValueError(f"Unsupported group option in {name}: {key}")
                options[key] = value
            else:
                members.append(token)
        if len(set(members)) != len(members):
            raise ValueError(f"Duplicate members: {name}")
        if "policy-regex-filter" in options:
            re.compile(options["policy-regex-filter"])
        default = options.get("policy-select-name")
        if default is not None and default not in members:
            raise ValueError(f"Invalid default member of {name}: {default}")
        if kind == "select" and not members:
            raise ValueError(f"Manual selector requires an explicit default: {name}")
        if kind != "select":
            if not options.get("url", "").startswith("https://"):
                raise ValueError(f"Automatic test needs an HTTPS URL: {name}")
            for key in ["interval", "timeout", "tolerance"]:
                if not options.get(key, "").isdigit():
                    raise ValueError(f"Invalid {key}: {name}")
            if int(options["interval"]) <= 0 or int(options["timeout"]) <= 0:
                raise ValueError(f"Test intervals must be positive: {name}")
        result[name] = {"type": kind, "members": members, "options": options}
    for name, group in result.items():
        for member in group["members"]:
            if member not in result and member not in BUILTINS:
                raise ValueError(f"Undefined group reference: {name} -> {member}; use a name regex for nodes")
    done = set()

    def visit(name, stack):
        if name in BUILTINS or name in done:
            return
        if name in stack:
            raise ValueError(f"Group cycle: {' -> '.join(stack + [name])}")
        for child in result[name]["members"]:
            visit(child, stack + [name])
        done.add(name)

    for name in result:
        visit(name, [])
    return result


@dataclass(frozen=True)
class Rule:
    kind: str
    value: str
    policy: str
    options: tuple[str, ...] = ()
    origin: str = ""

    def text(self):
        values = [self.kind, self.policy] if self.kind == "FINAL" else [self.kind, self.value, self.policy]
        return ",".join(values + list(self.options))

def checked_rule(kind, value, policy, options=(), origin=""):
    if not policy or any(ch in policy for ch in ",\n"):
        raise ValueError(f"Invalid policy: {origin}")
    if kind in DOMAIN_TYPES:
        value = value.lower().rstrip(".")
        if not value or not re.fullmatch(r"[a-z0-9_.-]+", value) or value.startswith("."):
            raise ValueError(f"Invalid domain/keyword {value}: {origin}")
        if kind != "DOMAIN-KEYWORD" and (".." in value or any(not label or label.startswith("-") or label.endswith("-") for label in value.split("."))):
            raise ValueError(f"Invalid domain labels: {value}")
        if options:
            raise ValueError(f"Domain rules do not take extra fields: {origin}")
    elif kind in IP_TYPES:
        network = ipaddress.ip_network(value, strict=True)
        kind = "IP-CIDR6" if network.version == 6 else "IP-CIDR"
        value = str(network)
        if tuple(options) != ("no-resolve",):
            raise ValueError(f"IP rules must explicitly use no-resolve: {origin}")
    elif kind == "GEOIP":
        if not re.fullmatch(r"[A-Z]{2}", value) or options:
            raise ValueError(f"Invalid GEOIP rule: {origin}")
    elif kind == "FINAL":
        if value or options:
            raise ValueError(f"Invalid FINAL rule: {origin}")
    else:
        raise ValueError(f"Unsupported rule type {kind}: {origin}")
    return Rule(kind, value, policy, tuple(options), origin)


def parse_routed(line, origin=""):
    fields = [f.strip() for f in line.split(",")]
    if fields[0] == "FINAL" and len(fields) == 2:
        return checked_rule("FINAL", "", fields[1], origin=origin)
    if len(fields) < 3:
        raise ValueError(f"Malformed routed rule: {origin}: {line}")
    return checked_rule(*fields[:3], options=fields[3:], origin=origin)


def compile_rules(root=ROOT):
    verify_sources(root)
    plan = read_json(root / "rules/order.json")
    if plan.get("schema") != 1:
        raise ValueError("Unsupported rule-order schema")
    result, seen, suffixes, keywords = [], {}, {}, []
    report = {"skipped": {}, "duplicates": [], "cross_policy_duplicates": [], "shadowed": []}
    for entry in plan["rules"]:
        mode = entry["mode"]
        if mode not in {"domains", "network", "strict", "domain-set"}:
            raise ValueError(f"Unknown transform mode: {mode}")
        for number, line in active_lines(safe_path(root, entry["path"]).read_text(encoding="utf-8")):
            origin = f"{entry['path']}:{number}"
            if line in entry.get("exclude", []):
                key = entry["path"] + ":exclude"
                report["skipped"][key] = report["skipped"].get(key, 0) + 1
                continue
            fields = [f.strip() for f in line.split(",")]
            if mode == "domain-set":
                fields = ["DOMAIN-SUFFIX" if line.startswith(".") else "DOMAIN", line.lstrip(".")]
            if len(fields) < 2:
                raise ValueError(f"Malformed source rule: {origin}")
            kind, value, *options = fields
            allowed = DOMAIN_TYPES | IP_TYPES if mode in {"strict", "network"} else {"DOMAIN", "DOMAIN-SUFFIX"}
            if mode == "network":
                allowed -= {"DOMAIN-KEYWORD"}
            if kind not in allowed:
                if mode == "strict" or kind not in UPSTREAM_TYPES:
                    raise ValueError(f"Unsupported source rule {kind}: {origin}")
                key = entry["path"] + ":" + kind
                report["skipped"][key] = report["skipped"].get(key, 0) + 1
                continue
            rule = checked_rule(kind, value, entry["policy"], options, origin)
            if rule.kind in {"DOMAIN", "DOMAIN-SUFFIX"}:
                labels = rule.value.split(".")
                covering = [suffixes[s] for i in range(len(labels)) if (s := ".".join(labels[i:])) in suffixes]
                covering += [r for r in keywords if r.value in rule.value]
                for earlier in covering:
                    if earlier.policy == rule.policy:
                        continue
                    if earlier.origin.startswith("rules/personal-") and origin.startswith("rules/personal-"):
                        raise ValueError(f"Conflicting personal overrides: {earlier.origin} shadows {origin}")
                    if earlier.kind == rule.kind and earlier.value == rule.value:
                        continue  # Reported as an exact duplicate below.
                    report["shadowed"].append({"earlier": earlier.text(), "later": rule.text(), "kept": earlier.origin, "covered": origin})
            key = (rule.kind, rule.value, rule.options)
            if key in seen:
                earlier = seen[key]
                item = {"rule": rule.text(), "kept": earlier.origin, "omitted": origin}
                if earlier.policy != rule.policy:
                    if entry["path"].startswith("rules/personal-"):
                        raise ValueError(f"Conflicting personal overrides: {earlier.origin} / {origin}")
                    report["cross_policy_duplicates"].append(item)
                else:
                    report["duplicates"].append(item)
                continue
            seen[key] = rule
            if rule.kind == "DOMAIN-SUFFIX":
                suffixes.setdefault(rule.value, rule)
            elif rule.kind == "DOMAIN-KEYWORD":
                keywords.append(rule)
            result.append(rule)
    result += [parse_routed(line, "rules/order.json:tail") for line in plan["tail"]]
    if [i for i, r in enumerate(result) if r.kind == "FINAL"] != [len(result) - 1]:
        raise ValueError("Exactly one FINAL must appear at the end")
    return result, report


def render(root=ROOT):
    base = (root / "config/base.conf").read_text(encoding="utf-8")
    if base.count("# @RULES@") != 1:
        raise ValueError("Expected exactly one rule insertion marker")
    groups = groups_from(base)
    rules, report = compile_rules(root)
    lines, last_path = [], None
    for rule in rules:
        if rule.policy not in groups and rule.policy not in BUILTINS:
            raise ValueError(f"Undefined rule policy: {rule.policy}: {rule.origin}")
        path = rule.origin.split(":")[0]
        if path != last_path:
            lines.extend(["", "# Source: " + path])
            last_path = path
        lines.append(rule.text())
    output = base.replace("# @RULES@", "\n".join(lines).strip())
    parsed = sections(output)
    if set(parsed) != {"General", "Proxy", "Proxy Group", "Rule", "Host"}:
        raise ValueError("Unexpected config sections; MITM/rewrite are intentionally absent")
    if any(line.startswith(("RULE-SET,", "DOMAIN-SET,")) for line in parsed["Rule"]):
        raise ValueError("Generated file must be self-contained")
    if any(line.startswith("update-url") for line in parsed["General"]):
        raise ValueError("Private repository must not expose unauthenticated update URLs")
    report["rule_count"] = len(rules)
    return output, rules, groups, report
