<div align="center">

# 🚀 ss-rules

**扫码导入 · 图标分流 · 按服务选出口**

日常只选一条默认线路；有特殊需求，再给某个 App 单独选地区。

<img src="docs/assets/config-qr.png" width="280" height="280" alt="使用 Shadowrocket 扫码导入 ss-rules 配置" />

**用 Shadowrocket 扫码，按提示导入配置。**

[📄 推荐配置](https://raw.githubusercontent.com/captainamari/ss-rules/main/Shadowrocket.conf) · [📦 完整备用版](https://raw.githubusercontent.com/captainamari/ss-rules/main/Shadowrocket-full.conf) · [🎛 怎么选分流](#routing)

</div>

## 📲 三步开始

需要已安装 Shadowrocket，并准备好自己的节点或订阅。本配置负责分流，不提供节点。

1. **添加节点**：在 Shadowrocket 首页导入自己的订阅，选中一条可用节点。
2. **扫码导入**：扫描上方二维码，等待远程规则集下载完成，在「配置」页确认 `Shadowrocket.conf` 已设为使用中（✔️）。
3. **开启连接**：首页「全局路由」选择「配置」，打开连接开关。

**做到这里即可日常使用，不需要逐个设置服务组。** 国内服务和普通 Apple 服务默认直连，海外服务默认跟随首页选中的节点。

| 配置 | 适合的使用方式 |
|---|---|
| `Shadowrocket.conf`（推荐） | 小主配置＋本仓库远程规则集，扫码默认导入这一版 |
| `Shadowrocket-full.conf`（备用） | 全部规则内嵌，下载后不需要额外拉取规则集 |

两版使用相同的策略组和分流顺序。若远程规则下载失败，先恢复网络后重新下载，或手动导入完整备用版；不会自动切换版本。


<details>
<summary>📋 正在用同一台手机浏览？复制地址导入</summary>

复制以下地址，打开 Shadowrocket →「配置」→ 右上角 `+` → 粘贴并下载，再设为使用中：

```text
https://raw.githubusercontent.com/captainamari/ss-rules/main/Shadowrocket.conf
```

二维码使用 Shadowrocket 的配置导入协议；如果扫码工具没有唤起配置导入，使用上面的地址即可。

</details>

<a id="routing"></a>

## 🎛 想怎么用，就怎么选

在 Shadowrocket **首页下拉**，或点节点列表上方的**指示牌图标**，进入「代理分组」。找对应图标，点选出口即可。

| 我想…… | 在界面中这样选 |
|---|---|
| 📱 继续使用首页选中的节点 | **🚀 默认代理 → 📱 跟随首页**，初始就是这个选项 |
| ⚡ 让配置帮我挑低延迟线路 | **🚀 默认代理 → ⚡ 自动测速** |
| 🇯🇵 日常代理流量都走日本 | **🚀 默认代理 → 🇯🇵 日本自动** |
| 🤖 只让 ChatGPT 走美国 | **🤖 ChatGPT → 🇺🇸 美国自动**，其他服务不变 |
| 🎬 YouTube 走香港 | **🎬 YouTube → 🇭🇰 香港自动** |
| 📌 给某个服务固定一条线路 | 先在 **🖐 手动选择** 中选节点，再让该服务选择 **🖐 手动选择** |
| 🏦 香港银行使用本地网络 | **🏦 香港银行 → 🎯 直接连接**，初始就是这个选项 |
| 📈 盈透等券商固定一条线路 | 先在 **🖐 手动选择** 中选节点，再将 **📈 券商服务** 选为 **🖐 手动选择** |
| 🐟 没有单独分类的网站换出口 | 调整 **🐟 其他流量** |
| ↩️ 取消某个服务的单独设置 | 把该服务重新选为 **🚀 默认代理** |

**国旗组只使用你已有的对应地区节点。** 没有该地区的节点时，使用「📱 跟随首页」或「🖐 手动选择」。节点名称用于归类，不代表已经验证了实际出口地区或服务可用性。

## 🧭 看懂几个图标

| 界面选项 | 含义 |
|---|---|
| 🚀 默认代理 | 大部分海外服务共用的出口，改这里即可一起换线 |
| 📱 跟随首页 | 使用首页选中的节点；在首页换节点，这里也跟着变 |
| 🖐 手动选择 | 从已有节点中选一条；所有引用这个组的服务共用这条线路 |
| ⚡ 自动测速 | 从已有节点中自动选择低延迟线路，可能跨地区 |
| 🇭🇰 香港自动 · 🇹🇼 台湾自动 · 🇯🇵 日本自动 · 🇺🇸 美国自动 | 仅在对应地区内自动选择线路 |
| 🎯 直接连接 | 使用本地网络，不经过代理 |
| ⛔ 禁止连接 | 拦截该组流量 |

自动组每 10 分钟测速，延迟改善超过 100ms 时才换线。需要保持同一个出口时，使用「🖐 手动选择」，并关闭客户端全局自动切换；不要把自动组中的临时点选当作固定线路。

<details>
<summary>🗂 查看全部服务和默认出口</summary>

| 策略组 | 默认选择 | 覆盖范围 |
|---|---|---|
| 🤖 ChatGPT | 🚀 默认代理 | ChatGPT、OpenAI |
| 🧠 Claude | 🚀 默认代理 | Claude、Anthropic |
| ✨ Google AI | 🚀 默认代理 | Gemini、AI Studio、NotebookLM 等 |
| 🧩 其他 AI | 🚀 默认代理 | Copilot、OpenRouter、Perplexity 等 |
| 🍎 Apple 智能 | 🚀 默认代理 | Apple Intelligence、Siri 等 |
| 🎬 YouTube | 🚀 默认代理 | 视频、API、图片和相关翻译接口 |
| 🔎 Google | 🚀 默认代理 | Google 通用服务 |
| 💻 开发服务 | 🚀 默认代理 | GitHub、GitLab、Atlassian、PyPI、npm、Docker |
| ✈️ Telegram | 🚀 默认代理 | Telegram |
| 🪟 Microsoft | 🚀 默认代理 | Microsoft 通用服务 |
| 📮 邮件服务 | 🚀 默认代理 | 名单中的邮件服务 |
| 🍏 Apple 服务 | 🎯 直接连接 | Apple 通用服务 |
| 🔔 Apple 推送 | 🚀 默认代理 | Apple 推送连接 |
| 🏦 香港银行 | 🎯 直接连接 | 名单中的香港银行 |
| 📈 券商服务 | 🚀 默认代理 | 盈透 IBKR、富途/moomoo、长桥、老虎等 |
| 🇨🇳 国内服务 | 🎯 直接连接 | 国内域名及 GEOIP CN |
| 🐟 其他流量 | 🚀 默认代理 | 未命中其他规则的请求 |
| 🧰 应用内 DNS | 🎯 直接连接 | 名单中的 HTTPDNS 服务，日常无需调整 |

局域网默认直连。规则按顺序匹配，个人例外优先于服务分类，AI、YouTube 等专用分类先于 Google、Microsoft、Apple 通用分类。

</details>

<details>
<summary>💡 常见问题：节点为空、某个 App 不通、更新配置</summary>

**地区组没有节点？** 检查订阅是否已有该地区节点，以及节点名称是否包含旗帜、地区名或国家代码。暂时使用「📱 跟随首页」或在「🖐 手动选择」中选实际节点；分组不会生成新的节点。

**测速正常，某个服务仍然打不开？** 测速只判断探测地址的连接情况，不判断服务是否支持这个出口。进入该服务组更换节点或地区；需要语音、通话时，节点也要支持相应协议。

**想让 ChatGPT 固定美国，同时 YouTube 自动选香港？** 先在「🖐 手动选择」中选自己的美国节点；将「🤖 ChatGPT」选为「🖐 手动选择」，将「🎬 YouTube」选为「🇭🇰 香港自动」。

**更改「🚀 默认代理」为什么没影响某个 App？** 该 App 如果已单独选择地区或手动组，就不会跟随默认代理。将它重新选为「🚀 默认代理」即可。

**怎样更新？** 在「配置」页更新当前使用的配置，再确认它处于使用中。推荐版会引用对应版本的远程名单，可在配置的「规则集 URL」中检查下载状态；完整备用版更新后仍是完整单文件。节点订阅单独在首页更新。

**盈透如何分流？** 官网、Client Portal、IBKR 域名，以及官方列出的 `ibllc.com`、`ibllc.com.cn` 交易网关域名都归入「📈 券商服务」。可在连接记录中查看实际命中结果；直接连接 IP、未经过可识别域名的流量，需要根据记录补充对应 IP 规则。


**这些设置会影响手机网络的哪些部分？** 代理域名使用经代理访问的 DoH，直连域名使用系统 DNS；IPv6 关闭，QUIC 允许。代理不支持 UDP 时拒绝相关流量。域名规则不能区分同一主机下不同 App 或 HTTPS 路径。

</details>

<details>
<summary>🛠 进阶：定制自己的域名、策略和节点筛选</summary>

| 需求 | 修改位置 |
|---|---|
| 默认出口、图标名称、地区筛选、DNS | [config/base.conf](config/base.conf) |
| 指定域名直连 | [rules/personal-direct.list](rules/personal-direct.list) |
| 指定域名走默认代理 | [rules/personal-proxy.list](rules/personal-proxy.list) |
| 补充盈透域名 | [rules/interactive-brokers.list](rules/interactive-brokers.list) |
| 补充某个服务的域名 | [rules/](rules/) 下的对应名单 |
| 名单对应的策略和匹配顺序 | [rules/order.json](rules/order.json) |

名单只填写匹配条件，出口由 `rules/order.json` 指定：

```ini
DOMAIN,api.example.com
DOMAIN-SUFFIX,example.org
```

`DOMAIN` 匹配完整主机名；`DOMAIN-SUFFIX` 匹配域名及其子域名。不要将同一目标同时放入个人直连和个人代理名单。修改组名时，要同步修改所有组引用及 `rules/order.json` 中的策略名称，包括 emoji。

地区节点通过 `policy-regex-filter` 匹配名称。按需调整筛选表达式，或者直接在「🖐 手动选择」中挑选不符合命名规则的节点。

修改源文件后，用 Python 3.10+ 一次生成两种配置和远程名单：

```bash
python3 scripts/build.py
```

将源文件、`Shadowrocket.conf`、`Shadowrocket-full.conf` 和生成的 `rulesets/` 一起提交，再在客户端更新配置。

`rulesets/<版本>/` 是生成结果，请修改 `rules/` 等源文件后重新生成。每个版本的名单保持不变，构建会保留旧版本，供尚未更新配置的客户端使用；不要直接修改或删除已发布的版本目录。

两版共用 `config/base.conf`；它的 `update-url` 决定发布地址，完整备用版会自动使用同目录下的 `Shadowrocket-full.conf`。Fork 后先修改这个地址，再生成文件。

`vendor/` 保存上游规则，版本记录在 `sources.json`。

</details>

## 📚 来源与许可

规则来源：[LingJingMaster/Shadowrocket-Rules](https://github.com/LingJingMaster/Shadowrocket-Rules)、[blackmatrix7/ios_rule_script](https://github.com/blackmatrix7/ios_rule_script)。客户端操作参考：[Shadowrocket 使用说明](https://github.com/LOWERTOP/Shadowrocket)。

许可与署名见 [NOTICE.md](NOTICE.md)、[LICENSE](LICENSE) 和 [MIT 声明](LICENSES/LingJingMaster-MIT.txt)。
