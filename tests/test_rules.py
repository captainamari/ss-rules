import hashlib
import io
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import update_sources
from scripts.check import check_cases, check_regex_cases, node_members
from scripts.rules import ROOT, checked_rule, first_match, groups_from, read_json, render, safe_path, sections, verify_sources


class RoutingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text, cls.rules, cls.groups, cls.report = render()

    def test_real_service_regressions(self):
        for case in read_json(ROOT / "tests/routing-cases.json"):
            with self.subTest(name=case["name"]):
                self.assertEqual(check_cases(self.rules, [case]), [])

    def test_region_name_boundaries(self):
        self.assertEqual(check_regex_cases(self.groups, read_json(ROOT / "tests/node-cases.json")), [])

    def test_no_implicit_country_selection(self):
        regions = read_json(ROOT / "rules/order.json")["region_groups"]
        matches, ambiguous = node_members(self.groups, ["节点 A"], regions)
        self.assertTrue(all(not names for names in matches.values()))
        self.assertEqual(ambiguous, {})
        for name in regions:
            self.assertEqual(self.groups[name]["options"]["policy-select-name"], "REJECT")

    def test_ambiguous_node_is_reported(self):
        regions = read_json(ROOT / "rules/order.json")["region_groups"]
        _, ambiguous = node_members(self.groups, ["香港-日本 中转"], regions)
        self.assertEqual(set(ambiguous["香港-日本 中转"]), {"香港节点", "日本节点"})

    def test_ai_groups_have_no_direct_choice_in_graph(self):
        def leaves(name):
            if name not in self.groups:
                return {name}
            return set().union(*(leaves(n) for n in self.groups[name]["members"]))
        for name in ["ChatGPT", "Claude", "Google AI", "其他 AI", "Apple 智能"]:
            self.assertNotIn("DIRECT", leaves(name))

    def test_generated_file_has_no_private_remote_dependency_or_mitm(self):
        parsed = sections(self.text)
        self.assertNotIn("MITM", parsed)
        self.assertNotIn("URL Rewrite", parsed)
        self.assertEqual(parsed["Proxy"], [])
        self.assertFalse(any(line.startswith("update-url") for line in parsed["General"]))
        self.assertFalse(any(line.startswith(("RULE-SET,", "DOMAIN-SET,")) for line in parsed["Rule"]))

    def test_runtime_file_equals_offline_build(self):
        self.assertEqual((ROOT / "Shadowrocket.conf").read_text(encoding="utf-8"), self.text)

    def test_ipv6_rules_use_correct_type(self):
        self.assertTrue(any(r.kind == "IP-CIDR6" for r in self.rules))
        self.assertFalse(any(r.kind == "IP-CIDR" and ":" in r.value for r in self.rules))

    def test_no_resolve_does_not_guess_an_address(self):
        rule = checked_rule("IP-CIDR", "192.168.1.0/24", "DIRECT", ("no-resolve",))
        self.assertFalse(rule.matches(domain="internal.example"))
        self.assertTrue(rule.matches(ip="192.168.1.3"))

    def test_suffix_has_a_label_boundary(self):
        rule = checked_rule("DOMAIN-SUFFIX", "example.com", "PROXY")
        self.assertTrue(rule.matches(domain="a.example.com"))
        self.assertFalse(rule.matches(domain="notexample.com"))
        self.assertFalse(rule.matches(domain="example.com.evil"))

    def test_removed_shared_ip_and_keyword_shortcuts(self):
        self.assertFalse(any(r.kind == "DOMAIN-KEYWORD" for r in self.rules))
        self.assertFalse(any(r.value == "208.54.0.0/16" for r in self.rules))
        self.assertFalse(any(r.policy == "券商" and r.kind.startswith("IP-") for r in self.rules))
        self.assertFalse(any(r.kind == "DOMAIN-SUFFIX" and r.value == "livekit.cloud" for r in self.rules))

    def test_final_is_unique_and_last(self):
        self.assertEqual([r.kind for r in self.rules].count("FINAL"), 1)
        self.assertEqual(self.rules[-1].text(), "FINAL,默认代理")


class InvalidConfigurationTests(unittest.TestCase):
    def test_unknown_group_reference(self):
        with self.assertRaisesRegex(ValueError, "Undefined group"):
            groups_from("[Proxy Group]\nAI = select,Typo")

    def test_invalid_selected_option(self):
        with self.assertRaisesRegex(ValueError, "Invalid default"):
            groups_from("[Proxy Group]\nAI = select,PROXY,policy-select-name=US")

    def test_group_cycle(self):
        with self.assertRaisesRegex(ValueError, "cycle"):
            groups_from("[Proxy Group]\nA = select,B\nB = select,A")

    def test_duplicate_section(self):
        with self.assertRaisesRegex(ValueError, "Duplicate section"):
            sections("[Rule]\nFINAL,PROXY\n[Rule]\nFINAL,DIRECT")

    def test_invalid_regex(self):
        with self.assertRaises(re.error):
            groups_from("[Proxy Group]\nUS = select,REJECT,policy-regex-filter=[")

    def test_proxy_credentials_rejected(self):
        with self.assertRaisesRegex(ValueError, "credentials"):
            groups_from("[Proxy]\nexample = ss,example.invalid,443\n[Proxy Group]\nA = select,PROXY")

    def test_unsupported_rule_is_not_silently_accepted(self):
        with self.assertRaisesRegex(ValueError, "Unsupported rule"):
            checked_rule("URL-REGEX", ".*", "PROXY")

    def test_cidr_without_no_resolve_rejected(self):
        with self.assertRaisesRegex(ValueError, "no-resolve"):
            checked_rule("IP-CIDR", "10.0.0.0/8", "DIRECT")

    def test_parent_path_rejected(self):
        with self.assertRaisesRegex(ValueError, "escapes"):
            safe_path(ROOT, "../outside")


class MutationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "repo"
        shutil.copytree(ROOT, self.root, ignore=shutil.ignore_patterns(".git", ".local", "__pycache__"))
        self.addCleanup(self.tmp.cleanup)

    def test_source_tampering_detected(self):
        with (self.root / "vendor/lingjing/Google.list").open("a") as f:
            f.write("\nDOMAIN,unexpected.example\n")
        with self.assertRaisesRegex(ValueError, "snapshot changed"):
            verify_sources(self.root)

    def test_new_vendor_file_must_be_locked(self):
        (self.root / "vendor/unlocked.list").write_text("DOMAIN,example.com\n")
        with self.assertRaisesRegex(ValueError, "Untracked"):
            verify_sources(self.root)

    def test_google_before_youtube_is_caught_by_route_regression(self):
        file = self.root / "rules/order.json"
        order = read_json(file)
        google = next(e for e in order["rules"] if e["path"] == "vendor/lingjing/Google.list")
        order["rules"].remove(google)
        index = next(i for i, e in enumerate(order["rules"]) if e["path"] == "vendor/blackmatrix7/YouTube.list")
        order["rules"].insert(index, google)
        file.write_text(json.dumps(order))
        _, rules, _, _ = render(self.root)
        self.assertEqual(first_match(rules, domain="youtubei.googleapis.com").policy, "Google")
        self.assertTrue(check_cases(rules, [{"name": "YouTube API", "domain": "youtubei.googleapis.com", "policy": "YouTube"}]))

    def test_conflicting_personal_overrides_fail(self):
        for filename in ["personal-direct.list", "personal-proxy.list"]:
            (self.root / "rules" / filename).write_text("DOMAIN,example.com\n")
        with self.assertRaisesRegex(ValueError, "Conflicting personal"):
            render(self.root)

    def test_personal_override_has_priority(self):
        (self.root / "rules/personal-direct.list").write_text("DOMAIN,api.anthropic.com\n")
        _, rules, _, _ = render(self.root)
        self.assertEqual(first_match(rules, domain="api.anthropic.com").policy, "DIRECT")
        self.assertEqual(first_match(rules, domain="claude.ai").policy, "Claude")

    def test_personal_suffix_cannot_hide_conflicting_exact_override(self):
        (self.root / "rules/personal-direct.list").write_text("DOMAIN-SUFFIX,example.com\n")
        (self.root / "rules/personal-proxy.list").write_text("DOMAIN,api.example.com\n")
        with self.assertRaisesRegex(ValueError, "shadows"):
            render(self.root)

    def test_unknown_rule_policy_fails(self):
        file = self.root / "rules/order.json"
        order = read_json(file)
        order["rules"][4]["policy"] = "Undefined policy"
        file.write_text(json.dumps(order))
        with self.assertRaisesRegex(ValueError, "Undefined rule policy"):
            render(self.root)

    def test_stale_generated_output_fails_cli(self):
        with (self.root / "Shadowrocket.conf").open("a") as f:
            f.write("# local edit\n")
        result = subprocess.run([sys.executable, "scripts/build.py", "--check"], cwd=self.root, capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn("stale", result.stderr)

    def test_missing_required_region_fails_cli(self):
        inventory = self.root / "names.txt"
        inventory.write_text("香港 01\n")
        result = subprocess.run([sys.executable, "scripts/check.py", "--nodes", str(inventory), "--require-group", "美国节点"], cwd=self.root, capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn("no candidates", result.stderr)

    def test_update_stages_without_mutating_active_inputs(self):
        before = (self.root / "sources.json").read_bytes()
        data = b"# candidate\nDOMAIN,example.com\n"
        with patch.object(update_sources, "ROOT", self.root), patch.object(update_sources, "urlopen", side_effect=lambda *a, **kw: io.BytesIO(data)):
            staged = update_sources.stage("lingjing", "a" * 40)
        self.assertEqual((self.root / "sources.json").read_bytes(), before)
        self.assertEqual((staged / "vendor/lingjing/AI.list").read_bytes(), data)
        candidate = read_json(staged / "sources.json")
        row = next(s for s in candidate["sources"] if s["local"].endswith("AI.list"))
        self.assertEqual(row["sha256"], hashlib.sha256(data).hexdigest())

    def test_failed_download_leaves_active_inputs_intact(self):
        before = (self.root / "sources.json").read_bytes()
        with patch.object(update_sources, "ROOT", self.root), patch.object(update_sources, "urlopen", side_effect=OSError("network failure")):
            with self.assertRaises(OSError):
                update_sources.stage("lingjing", "a" * 40)
        self.assertEqual((self.root / "sources.json").read_bytes(), before)
        self.assertFalse((self.root / ".local").exists())


if __name__ == "__main__":
    unittest.main()
