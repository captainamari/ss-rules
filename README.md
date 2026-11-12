# ss-rules

Shadowrocket 分流配置。按服务匹配规则，再由对应策略组选择出口；节点和订阅在客户端添加。

## 导入配置

使用 Shadowrocket 的扫码功能扫描下方二维码：

<img src="docs/assets/config-qr.png" width="270" height="270" alt="Shadowrocket 配置导入二维码" />

也可在「配置」页添加以下地址，下载后设为当前配置：

```text
https://raw.githubusercontent.com/captainamari/ss-rules/main/Shadowrocket.conf
```

[打开配置直链](https://raw.githubusercontent.com/captainamari/ss-rules/main/Shadowrocket.conf)

1. 添加自己的节点或订阅，在首页选中可用节点。
2. 导入配置，将全局路由设为「配置」。
3. 大部分海外服务默认跟随「默认代理」，初始使用客户端当前选中的节点（`PROXY`）。
4. 如需指定地区，先在对应地区组选择实际节点，再让服务组使用该地区组。

配置已包含全部规则，并设置了更新地址。仓库配置更新后，可在客户端更新该配置。

## 策略组

| 服务组 | 默认出口 | 覆盖范围 |
|---|---|---|
| ChatGPT、Claude | 默认代理 | 两个服务分别选择出口 |
| Google AI | 默认代理 | Gemini、AI Studio、NotebookLM 等 |
| 其他 AI | 默认代理 | Copilot、OpenRouter、Perplexity 等 |
| Apple 智能 | 默认代理 | Apple Intelligence、Siri 等 |
| YouTube | 默认代理 | 视频、API、图片和相关翻译接口 |
| 开发服务 | 默认代理 | GitHub、GitLab、Atlassian、PyPI、npm、Docker |
| Google、Microsoft、Telegram、邮件 | 默认代理 | 各服务独立选择 |
| Apple | DIRECT | Apple 通用服务 |
| Apple 推送 | 默认代理 | 推送连接，可切换直连 |
| 香港银行 | DIRECT | 银行域名，可选择固定代理 |
| 券商 | 默认代理 | 券商域名，可选择香港或美国出口 |
| 个人服务 | 默认代理 | tools.xuzz.me、stocks.watchpoint.space |
| HTTPDNS | DIRECT | 名单中的 HTTPDNS 服务，可选代理或 REJECT |
| 国内服务、局域网 | DIRECT | 国内域名、GEOIP CN 和本地网络 |
| 其他请求 | 默认代理 | 未命中前面规则的请求 |

美国、日本、香港和台湾组按节点名称筛选。地区名称不代表配置自带节点，也不能证明节点的实际出口位置。地区组初始选中 `REJECT`；有可用成员时手动选定节点，没有成员时不使用该组。

服务组和地区组采用手动选择，不会自动跨地区重试或失败直连。`自动测速` 仅在被选用时生效，其候选节点可能来自不同国家；需要固定出口时选择具体节点。

## 分流与网络设置

- 规则从上到下匹配，个人例外先于服务分类，AI、YouTube 等专用规则先于 Google、Microsoft、Apple 等通用规则。
- 代理域名使用经代理访问的 DoH，直连域名使用系统 DNS。
- IPv6 关闭，QUIC 允许；代理不支持 UDP 时拒绝相应流量。
- 域名规则按主机匹配，不能区分同一域名下的调用 App 或 HTTPS 路径。共享域名的规则会影响其他使用者。
- 局域网和系统联网检测使用旁路设置；需要排查实际出口时查看客户端的连接记录。

## 定制配置

| 需求 | 修改位置 |
|---|---|
| 临时更换服务出口 | 客户端中的对应策略组 |
| 默认出口、地区筛选、DNS、协议设置 | [config/base.conf](config/base.conf) |
| 指定域名直连 | [rules/personal-direct.list](rules/personal-direct.list) |
| 指定域名走默认代理 | [rules/personal-proxy.list](rules/personal-proxy.list) |
| 个人网站使用可切换策略组 | [rules/personal-services.list](rules/personal-services.list) |
| 补充某个服务的域名 | [rules/](rules/) 下的对应名单 |
| 名单对应的策略、匹配顺序 | [rules/order.json](rules/order.json) |

名单只填写匹配条件，出口由 `rules/order.json` 指定：

```ini
DOMAIN,api.example.com
DOMAIN-SUFFIX,example.org
```

`DOMAIN` 匹配完整主机名；`DOMAIN-SUFFIX` 匹配域名及其子域名。不要把同一目标同时放入个人直连和个人代理名单。

地区筛选通过 `policy-regex-filter` 匹配节点名称。订阅命名不同，可调整正则；少量自建节点也可使用精确名称，如 `^我的美国节点01$`。

修改源文件后，用 Python 3.10+ 生成完整配置：

```bash
python3 scripts/build.py
```

将源文件和生成的 `Shadowrocket.conf` 一起提交，再在客户端更新配置。`vendor/` 保存上游规则，版本记录在 `sources.json`。

## 来源与许可

规则来源：[LingJingMaster/Shadowrocket-Rules](https://github.com/LingJingMaster/Shadowrocket-Rules)、[blackmatrix7/ios_rule_script](https://github.com/blackmatrix7/ios_rule_script)。

许可与署名见 [NOTICE.md](NOTICE.md)、[LICENSE](LICENSE) 和 [MIT 声明](LICENSES/LingJingMaster-MIT.txt)。
