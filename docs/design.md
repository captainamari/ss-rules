# 设计与取舍

修改日期：2026-11-12。基线：LingJingMaster/Shadowrocket-Rules @ `091d94e826ae2973bc0884aec53b97ec94949bac`。

## 规则层次

`rules/order.json` 是优先级的唯一来源。构建时把各份名单转换为带策略的行，内嵌到根目录 `Shadowrocket.conf`，客户端不需要理解该 JSON。

顺序为个人例外、局域网、个人服务、HTTPDNS、明确的国内域名、各 AI 专用规则、YouTube、邮件、银行/券商、开发服务、Telegram、通用 Google/Microsoft、Apple 推送/Apple、国内名单、GEOIP CN、FINAL。

专用规则先于通用规则。YouTube 的 `googlevideo.com`、`youtubei.googleapis.com` 不应被 Google 通用分类抢走；Google AI 与普通 Google 分开；Apple 智能/邮件/推送先于 Apple；GitHub Copilot 先于 GitHub。

## 与基线的差异

| 基线行为 | 本版本 |
|---|---|
| 地区默认直接选美国/日本/香港 | 未知节点库存时默认 PROXY；地区选择器显式初始 REJECT，用户选真实成员后启用 |
| 地区组自动测速、容差 0 | 地区组为手动 select；另有可选自动测速组，容差 100ms，减少微小延迟波动引起的切换 |
| US、单字“美/港”等宽匹配 | 国家代码按字母边界匹配，保留明确中文地区名/旗帜；不推断节点真实地理位置 |
| Google 在 YouTube 之前 | 专用服务在通用服务之前 |
| AI 服务集中在一个组 | ChatGPT、Claude、Google AI、其他 AI、Apple 智能分别选择出口 |
| 大量关键词、User-Agent、URL 正则 | 上游通用名单只采用 DOMAIN/DOMAIN-SUFFIX，局域网和 Telegram 另保留 CIDR；每种省略都有构建报告 |
| 远程实时加载多份名单 | 固定提交的本地快照和校验值，生成完整文件，适配私有仓库 |
| 广泛 WebRTC/QUIC 阻断 | 日用配置允许 QUIC，不按通话端口统一拒绝；不支持 UDP 的代理仍 REJECT，避免静默直连 |
| Apple CDN/银行域名存在旁路 | 旁路仅保留局域网和系统联网检测，公共服务重新由规则决定 |
| Google URL 改写与 MITM | 均移除；不需要安装解密证书 |

## 默认出口与故障行为

所有默认海外策略都最终指向客户端 PROXY，因此不依赖美国等地区组有成员。PROXY 的节点与客户端设置仍由用户控制。固定出口时应选择地区组中的具体节点，并检查客户端全局自动切换设置。

地区组只有 REJECT 这个显式初始成员，加上由名称正则筛选的动态节点；REJECT 是一个明确的未启用状态。配置语法静态检查无法证明某版本客户端的订阅作用域、过滤结果、持久化选项和界面状态，首次导入必须检查实际成员和选中项。

select 列表不提供自动故障转移。默认没有配置跨地区重试，也不会在代理失败后转为 DIRECT。用户以后需要自动回退时，应先确定服务可接受的地区范围，再配置有实际成员的 fallback 组，并测试“连接成功但服务不可用”这种探测地址无法发现的失败。

银行默认直连、券商默认跟随 PROXY 都只是可调整的初始选择，不代表账户或地区资格判断。券商名单中旧的共享云 IP 网段未整体迁入；直接连接 IP 的客户端可能落入 GEOIP/FINAL。若实际交易客户端需要指定 IP，先从连接记录确认，再在个人规则添加最小范围，例如 IPv4 /32。

## 规则覆盖边界

- 丢弃上游 DOMAIN-KEYWORD，避免 `google` 匹配包含该字符串的无关网站、`claude` 匹配无关域名。自有 strict 名单仍可显式使用关键词，但应注意匹配范围。
- User-Agent 和 URL-REGEX 不进入生成文件，避免依赖 HTTPS 解密才能看到的字段。
- `www.sc.com/hk/` 的路径规则替换为 `www.sc.com` 主机规则，会影响该主机的所有地区路径；需要更细粒度时不应误称为已支持按 HTTPS 路径分流。
- 不把整个 `livekit.cloud` 当作 ChatGPT，不沿用 ChatGPT 的旧单 IP 规则，也不把所有 `www.bing.com` 访问都归为 Copilot。语音使用新的共享域名时先查日志，再补精确主机规则。
- 移除原作者针对一个 S3 桶、一个大段美国运营商 IP 的个人网络例外；保留为上游参考，不自动施加给 Jesse。
- 从香港银行/券商分类中排除 AppDynamics 和通用分析服务的共享主机。它们走后续分类，不代表银行核心连接丢失。
- Google/Apple/Microsoft 上游仍可能包含共享平台域名，域名分类不能识别同一主机内部的 App 身份。新增例外应优先使用精确主机，避免整个 CDN 后缀归给单一应用。
- 已排除上游对整个 akadns.net、edgesuite.net、b/g.akamaiedge.net、azureedge.net 的宽泛服务归类，保留可识别的具体服务主机。gvt1.com/gvt2.com 是共享 Google 分发域名，归入 Google，避免离线地图/通用下载被整体算作 YouTube。
- Microsoft 自身的 update/download 子域名保留在 Microsoft 组，不采用后续国内通用名单的 DIRECT；构建报告会记录这类有意的覆盖。
- YouTube 翻译补充保留 `translate.googleapis.com`、`translate-pa.googleapis.com`，会同时影响其他调用者，不能做到同域名按调用 App 区分。
- `DOMAIN-SUFFIX,cn` 是国内名单的启发式规则，不代表域名后缀可以证明服务器地区；有不同需求时使用个人例外。

## DNS 与协议兼容性

保留通过 PROXY 访问的 DoH，以及直连域名使用系统 DNS 的日用折中。HTTPDNS 策略组默认 DIRECT，不阻断国内 App 自带的解析服务；改变 HTTPDNS 组只影响名单里的已知主机，并不控制所有 DoH/HTTPDNS 端点，也不等于没有 DNS 泄露。

IPv6 暂沿用上游的关闭设置，生成的 CIDR 规则会规范化 IPv6 类型，便于后续启用时使用；这不等于在整个操作系统禁用 IPv6。启用前要验证节点 IPv6、DNS AAAA、直连与代理路径。

QUIC 默认允许，WebRTC 端口不统一阻断。若某节点不支持 UDP，配置明确 REJECT；应用可能回退到 TCP，也可能失败。需要语音时选择实际支持相关协议的节点，而不是把失败回退设为直连。IPv6、WebRTC、DNS 的真实流向必须通过设备验证。

## 快照和构建

`vendor/` 是未改写的上游原文；`sources.json` 记录 repo/path/revision/SHA-256。自有拆分名单带修改日期。正常构建不联网，固定快照变动但锁未更新会失败。仓库不包含测试套件或自动测试工作流。

普通域名名单与 DOMAIN-SET 格式分别解析：DOMAIN-SET 中前导 `.` 转为 DOMAIN-SUFFIX，无前导点转为 DOMAIN。上游错误地统一写为 IP-CIDR 的 IPv6 条目会转换为 IP-CIDR6；所有采用的 IP 条目必须保留 no-resolve。

脚本不是完整 Shadowrocket 解析器，遇到不认识的上游类型会失败。已知但不采用的类型按声明模式省略；生成后在手机导入并观察实际访问情况即可。
