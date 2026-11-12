# Third-party notices

This repository combines adapted configuration and rule data with an offline build tool.
The combined distribution and new code are provided under GPL-2.0-only (see LICENSE).

## LingJingMaster/Shadowrocket-Rules

- Source: https://github.com/LingJingMaster/Shadowrocket-Rules
- Baseline commit: 091d94e826ae2973bc0884aec53b97ec94949bac
- Copyright (c) 2026 Ling_Jing.
- MIT license is retained verbatim in LICENSES/LingJingMaster-MIT.txt.
- Original reference files are preserved under vendor/lingjing/.
- Adaptations dated 2026-11-12 are documented in docs/design.md and the derived rule-file headers.
- The upstream repository attributes portions of its rule data to blackmatrix7/ios_rule_script and iab0x00/ProxyRules; upstream source comments are retained.

## blackmatrix7/ios_rule_script

- Source: https://github.com/blackmatrix7/ios_rule_script
- Snapshot commit: 0b6897dc17e0c513d25449c935a9694818e32f0c
- Upstream GPL version 2 license is retained verbatim as LICENSE.
- Copyright and source/author notices in the individual files are retained under vendor/blackmatrix7/.
- sources.json records the exact repository paths, revisions and SHA-256 digests.

Generated Shadowrocket.conf combines selected rules from these snapshots and the editable local rules.
Complete corresponding inputs and generation scripts are included. Generated rule sections identify
their source paths; omitted rule types and duplicate handling are documented in docs/design.md.
No claim of affiliation with upstream authors or the Shadowrocket developer is made.
