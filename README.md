# ss-rules

Jesse 的 Shadowrocket 自用分流配置，基于 [LingJingMaster/Shadowrocket-Rules](https://github.com/LingJingMaster/Shadowrocket-Rules) 调整。保留“服务规则 → 服务策略组 → 节点”的结构，修正规则覆盖关系，并提供可离线重建、检查和回滚的配置。

**直接使用根目录的 [Shadowrocket.conf](Shadowrocket.conf)。这是完整配置，规则已内嵌，不需要访问私有仓库的远程规则链接。** 节点和订阅仍然在 Shadowrocket 客户端添加。

## 首次使用

1. 在已登录 GitHub 的设备上下载根目录 `Shadowrocket.conf`，保存到“文件”或 iCloud Drive。
2. 在 Shadowrocket 中从文件导入，或通过系统分享交给 Shadowrocket；设为当前使用的配置。文件导入入口随客户端版本可能不同。
3. 添加你自己的节点/订阅，在首页选中一条确认可用的节点，将全局路由设为“配置”。
4. 默认代理和大部分海外服务最初跟随 `PROXY`，即客户端当前选定的代理。配置不假定你有某个地区的节点，也不保证当前节点的实际出口地区。
5. 如果要用地区组，**先进入美国/日本/香港/台湾节点组，查看实际成员，并把初始的 `REJECT` 切换为一条真实节点**；再让服务组选择这个地区组。空组保持不用。
6. 按 [设备验收表](docs/verification.md) 检查网页、附件上传、语音、视频及实际命中规则。

地区组使用名称正则收集候选，初始选项为 `REJECT`，防止没有节点时误以为指定地区已可用。请以客户端实际显示的成员为准。配置没有自动跨地区或失败直连回退。

仓库是私有的：普通 Raw URL 无法供未认证的客户端长期下载。这里不配置 `update-url`，不在 URL 中放 GitHub token。更新后重新下载、导入完整文件即可，既有节点订阅仍由客户端管理。不要导入 `vendor/` 中的原始参考配置。

## 默认服务策略

| 服务组 | 初始出口 | 使用方式 |
|---|---|---|
| ChatGPT、Claude | 默认代理 | 两个独立组；需要固定出口时手动选地区组中的具体节点 |
| Google AI | 默认代理 | Gemini、AI Studio、NotebookLM 等，优先于普通 Google |
| 其他 AI、Apple 智能 | 默认代理 | Copilot、OpenRouter、Perplexity 与 Apple 智能分别归组 |
| YouTube | 默认代理 | 专用规则优先于 Google，包含视频流、API 和图片域名 |
| 开发服务 | 默认代理 | GitHub/GitLab/Atlassian/PyPI/npm/Docker，可选自动测速 |
| Google、Microsoft、Telegram、邮件 | 默认代理 | 分别手动切换 |
| Apple | DIRECT | Apple 智能、邮件和推送规则先于普通 Apple |
| Apple 推送 | 默认代理 | 可按实测手动改为 DIRECT |
| 香港银行 | DIRECT | 可手动选择固定代理；不由配置判断账户权限 |
| 券商 | 默认代理 | 未假设香港节点存在；需要香港出口时显式选择 |
| 个人服务 | 默认代理 | 已加入 tools.xuzz.me、stocks.watchpoint.space，可在组中切直连 |
| HTTPDNS | DIRECT | 默认兼容国内 App；可选择代理或 REJECT，不宣称完整防泄露 |
| 国内服务、局域网 | DIRECT | 专用服务规则先行，最后由 GEOIP CN 补充 |
| 未匹配请求 | 默认代理 | 由最后一条 FINAL 兜底 |

`select` 是手动选择列表，不是按排列顺序自动重试。默认代理不提供 DIRECT，AI 服务组也没有隐式直连选项。直接修改个人例外规则仍可改变某域名的行为。

`自动测速` 仅在手动选用时参与服务出口选择，候选可能来自不同国家。它探测普通 HTTPS 地址，**不能判断 AI 服务可用性或实际带宽**。对需要固定出口的服务，不建议选它；同时检查客户端是否开启了全局自动切换/回退。

## 修改哪里

| 需求 | 修改位置 |
|---|---|
| 临时换出口 | Shadowrocket 服务策略组 |
| 修改默认选项、候选项、地区正则、DNS | `config/base.conf` |
| 个人域名强制直连 | `rules/personal-direct.list` |
| 个人域名强制跟随默认代理 | `rules/personal-proxy.list` |
| 个人网站交给一个可切换组 | `rules/personal-services.list` |
| 增加 AI 服务域名 | `rules/chatgpt.list`、`claude.list`、`google-ai.list` 等 |
| 修改规则优先级或上游过滤方式 | `rules/order.json` |
| 查看上游版本与内容校验值 | `sources.json` |
| 排查具体域名为何归入某组 | `python3 scripts/check.py --explain 域名` |

名单里填写匹配条件，不重复写策略。例如把服务加入 ChatGPT 组时，在 `rules/chatgpt.list` 增加：

```ini
DOMAIN,api.example.com
```

个人规则优先于服务规则；`personal-direct.list` 又在 `personal-proxy.list` 前面。不要把同一目标同时放进相互冲突的个人规则。局域网/系统旁路是另一层机制，不能仅靠 `[Rule]` 将已经排除隧道的流量强制交给代理。

## 本地构建与检查

只需要 Python 3.10+，无第三方依赖，不在构建或 CI 中请求订阅或外部规则。

```bash
python3 scripts/build.py
python3 scripts/build.py --check
python3 scripts/check.py
python3 -m unittest discover -s tests -v
```

修改源文件后重新生成并一同提交 `Shadowrocket.conf`。不要只改生成文件；CI 会检查其与源文件是否一致。

构建报告写入忽略提交的 `.local/build-report.json`：包含省略的规则类型、同策略重复项、按声明顺序保留的跨策略完全相同匹配项，以及较早宽规则覆盖后续不同策略的情况。后者可能是专用服务覆盖国内通用名单的预期结果，也可能需要调整；个人直连/代理名单互相冲突会直接报错。先匹配者获胜，自动去重不会把后面的规则提升优先级。

```bash
python3 scripts/check.py --explain youtubei.googleapis.com
python3 scripts/check.py --explain unknown.example --country CN
python3 scripts/check.py --ip 149.154.167.51
```

解释器只检查本项目支持的规则子集。`--country` 是你提供的测试条件，不会查询 GeoIP；解释器也不会执行 DNS、隧道旁路或模拟客户端已保存的选项。

## 校验自己的节点名称

在本地创建 `.local/nodes.txt`，每行只写一个显示名称，例如：

```text
[US] Los Angeles 01
[HK] Hong Kong 01
[JP] Tokyo 01
```

```bash
python3 scripts/check.py --nodes .local/nodes.txt
python3 scripts/check.py --nodes .local/nodes.txt --require-group 美国节点
```

第一条报告各地区匹配数量；第二条在美国组没有候选时返回非零退出码。匹配多个地区的名字会报错，需要依据实际出口改名或调整表达式。**只检查名称，不检查节点是否在线、订阅是否被组纳入或出口是否真实位于该地区。** 不要把订阅链接、服务器密码或节点连接串放进名称文件。

地区正则优先识别旗帜、明确的中文地区和带边界的国家代码。`US` 不会匹配 `AUS` 或 `RUS`。未知命名不会被猜成某个国家。自建节点只有少量时，可以将该地区的筛选式改成精确名称，如 `^我的美国节点01$`；仍需在客户端选中该节点。

## 上游更新

所有引用均已固定到提交和 SHA-256，使用时不会突然加载上游主分支的新规则。更新工具只下载到候选目录，不自动覆盖当前配置：

```bash
python3 scripts/update_sources.py --source blackmatrix7 --revision 完整的40位提交SHA
```

1. 查看命令输出的 `.local/upstream-...` 目录，对照现有 `vendor/blackmatrix7/` 逐文件审查差异及许可证变化。
2. 将确认采用的该批快照和候选 `sources.json` 一起复制回相应位置。不要只改校验值来掩盖未知来源的修改。
3. 更新 LingJing 上游时，手工核对自有的 `rules/*ai*.list`、`chatgpt.list`、`claude.list` 等派生名单；工具不会覆盖你的定制。
4. 重建、检查、查看差异后提交。GitHub Actions 在 main 推送时运行相同的离线检查，不上传 artifacts、不自动提交或合并。
5. 在客户端导入新完整配置，重新确认策略选择，执行设备验收。出现回归可导入上一提交的完整配置。

详细设计差异见 [docs/design.md](docs/design.md)，能力边界和验收见 [docs/verification.md](docs/verification.md)。

## 来源与许可

保留 [LingJingMaster/Shadowrocket-Rules](https://github.com/LingJingMaster/Shadowrocket-Rules) 的 MIT 声明，并收录 [blackmatrix7/ios_rule_script](https://github.com/blackmatrix7/ios_rule_script) 的固定规则快照。组合后的配置和本仓库新增代码按 GPL-2.0 发布；各来源声明保留，详见 [NOTICE.md](NOTICE.md)、[LICENSE](LICENSE) 和 [LICENSES/LingJingMaster-MIT.txt](LICENSES/LingJingMaster-MIT.txt)。
