# ss-rules

Jesse 的 Shadowrocket 自用分流配置，基于 [LingJingMaster/Shadowrocket-Rules](https://github.com/LingJingMaster/Shadowrocket-Rules) 调整。采用“服务规则 → 服务策略组 → 节点”的结构，专用服务优先于通用分类。

**使用根目录的 [Shadowrocket.conf](Shadowrocket.conf)。规则已完整内嵌，节点和订阅在 Shadowrocket 客户端添加。**

## 扫码下载

<img src="docs/assets/config-qr.png" width="270" height="270" alt="扫码打开 Shadowrocket.conf 的 GitHub 下载页面" />

用手机相机扫码，在浏览器登录有权访问本仓库的 GitHub 账号，下载配置后导入 Shadowrocket。

也可直接打开：[配置下载页面](https://github.com/captainamari/ss-rules/blob/main/Shadowrocket.conf)。

当前仓库为私有仓库，二维码指向需要登录的下载页面，无法供 Shadowrocket 匿名扫码拉取。它不包含访问令牌。之后若调整仓库访问方式，再相应更新二维码。

## 首次使用

1. 下载 `Shadowrocket.conf`，保存到“文件”或 iCloud Drive。
2. 在 Shadowrocket 中从文件导入，或通过系统分享交给 Shadowrocket，设为当前使用的配置。
3. 添加自己的节点/订阅，在首页选中一条可用节点，将全局路由设为“配置”。
4. 默认代理和大部分海外服务跟随 `PROXY`，即客户端当前选定的代理。
5. 要使用地区组时，先进入该组查看实际成员，将初始的 `REJECT` 切换为真实节点，再让服务组选择这个地区组。

地区组按节点名称筛选，不保证你拥有对应地区节点，也不判断实际出口所在地。没有成员的地区组保持不用。配置没有自动跨地区或失败直连回退。

配置不依赖私有远程规则链接，也不设置 `update-url`。更新后重新下载、导入完整文件即可；节点订阅仍由客户端管理。不要导入 `vendor/` 中的原始参考配置。

## 默认服务策略

| 服务组 | 初始出口 | 说明 |
|---|---|---|
| ChatGPT、Claude | 默认代理 | 分别选择出口 |
| Google AI | 默认代理 | Gemini、AI Studio、NotebookLM 等，优先于普通 Google |
| 其他 AI、Apple 智能 | 默认代理 | Copilot、OpenRouter、Perplexity 与 Apple 智能分别归组 |
| YouTube | 默认代理 | 专用规则优先，包含视频流、API 和图片域名 |
| 开发服务 | 默认代理 | GitHub/GitLab/Atlassian/PyPI/npm/Docker，可选自动测速 |
| Google、Microsoft、Telegram、邮件 | 默认代理 | 分别手动切换 |
| Apple | DIRECT | 智能、邮件和推送先于普通 Apple |
| Apple 推送 | 默认代理 | 可手动改为 DIRECT |
| 香港银行 | DIRECT | 可手动选择固定代理 |
| 券商 | 默认代理 | 需要香港出口时显式选择 |
| 个人服务 | 默认代理 | tools.xuzz.me、stocks.watchpoint.space，可在组中切直连 |
| HTTPDNS | DIRECT | 默认兼容国内 App，可选代理或 REJECT |
| 国内服务、局域网 | DIRECT | 最后由 GEOIP CN 补充 |
| 未匹配请求 | 默认代理 | FINAL 兜底 |

`select` 是手动选择列表，不会按选项顺序自动重试。默认代理和 AI 组没有 DIRECT 选项；个人例外规则仍可改变某域名的行为。

`自动测速` 仅在手动选用时参与出口选择，候选可能来自不同国家。需要固定出口的服务应选择具体节点，同时留意客户端的全局自动切换设置。

## 定制规则

| 需求 | 修改位置 |
|---|---|
| 临时换出口 | 客户端中的服务策略组 |
| 默认选项、地区正则、DNS | `config/base.conf` |
| 个人域名强制直连 | `rules/personal-direct.list` |
| 个人域名强制走默认代理 | `rules/personal-proxy.list` |
| 个人网站交给可切换组 | `rules/personal-services.list` |
| 增加 AI 域名 | `rules/chatgpt.list`、`claude.list`、`google-ai.list` 等 |
| 调整规则优先级和过滤方式 | `rules/order.json` |
| 查看上游版本 | `sources.json` |

名单只填写匹配条件，策略在 `rules/order.json` 中指定。例如：

```ini
DOMAIN,api.example.com
DOMAIN-SUFFIX,example.org
```

个人直连、个人代理规则先于服务分类；不要将同一目标放进相互冲突的个人名单。局域网/系统旁路属于另一层机制，仅修改规则不能强制接管已排除隧道的流量。

地区正则识别旗帜、明确中文地区名和带边界的国家代码，避免 `US` 匹配 `AUS` 或 `RUS`。订阅命名不同，可调整 `config/base.conf` 中的 `policy-regex-filter`。只有少量自建节点时，也可用精确名称，如 `^我的美国节点01$`。

## 生成完整配置

需要 Python 3.10+，无第三方依赖。修改配置源文件或名单后执行：

```bash
python3 scripts/build.py
```

将源文件和重新生成的 `Shadowrocket.conf` 一起提交，再在手机导入。生成过程离线运行，保留基本的格式、引用和来源完整性检查；仓库不包含测试目录或自动测试工作流。

`.local/build-report.json` 记录构建时省略的规则和重叠项，不提交到仓库。实际分流情况直接查看 Shadowrocket 的连接记录：目标域名/IP、命中规则、服务组选择和具体节点。

## 上游更新

上游规则固定到提交和 SHA-256，使用时不会自动拉取变化。下面的工具只下载候选快照：

```bash
python3 scripts/update_sources.py --source blackmatrix7 --revision 完整的40位提交SHA
```

1. 对照输出的 `.local/upstream-...` 目录审查名单及许可证变化。
2. 将决定采用的快照和候选 `sources.json` 一起复制回对应位置。
3. 更新 LingJing 来源时，手工核对自有 AI 派生名单；工具不会覆盖定制。
4. 运行 `python3 scripts/build.py`，查看差异后提交，重新导入手机。

出现问题可导入上一提交的完整配置，重新确认客户端保存的策略选项。设计差异见 [docs/design.md](docs/design.md)。

## 来源与许可

保留 [LingJingMaster/Shadowrocket-Rules](https://github.com/LingJingMaster/Shadowrocket-Rules) 的 MIT 声明，并收录 [blackmatrix7/ios_rule_script](https://github.com/blackmatrix7/ios_rule_script) 的固定规则快照。组合配置和新增代码按 GPL-2.0 发布，来源声明见 [NOTICE.md](NOTICE.md)、[LICENSE](LICENSE) 和 [LICENSES/LingJingMaster-MIT.txt](LICENSES/LingJingMaster-MIT.txt)。
