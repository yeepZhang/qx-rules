# 墨鱼原配置 + 业务分流补充

以 ddgksf2013 的 Quantumult X 配置为主，保留原功能，只补充业务分流。公开配置不含个人节点、私人订阅或 MITM 证书。

## 配置地址

https://raw.githubusercontent.com/yeepZhang/qx-rules/main/QuantumultX.conf

在 QX 中通过 URL 导入。先备份原有节点和本机证书；导入后添加自己的节点，在“默认代理”中选中它。关闭“分流匹配优化”，更新所有分流和重写资源。需要解密的功能仍须在本机生成/信任 MITM 证书，并开启对应开关。

只更新远程资源不会恢复以前被省略的主配置内容；从旧精简版迁移，需要重新导入本配置一次。以后日常规则更新不需要重新导入。

## 保留哪些墨鱼功能

基础快照：墨鱼 V272，2026/10/11，原文存放在 upstream/moyu.conf，原作者 ddgksf2013。

- 全部 18 项远程重写，原链接、参数和 enabled 状态均保留：去开屏、哔哩、Spotify、彩云、知乎、YouTube、微博、高德、网易云、闲鱼、Safari 搜索、豆瓣、Google 重定向、小红书、百度网盘两项、微信链接解锁、BoxJS。
- 流媒体解锁查询、节点纯净度详情两项交互任务。
- 原 12 组远程分流，原参数和相对顺序均保留：误杀修正、广告、微信、Google Voice、AI、GitHub、Spotify、国际媒体、哔哩、Apple、全球加速、国内网站。
- 原 general、DNS、filter_local、MITM、rewrite_local、http_backend 内容原样保留，包括原 UDP 拦截、DNS alias 和本地规则。
- 原业务组和地区组保留。为适配单个自建美国节点，声田音乐、国际媒体、美国节点的默认候选改为“默认代理”；其他地区组可供以后扩展，没有对应节点时不要手动选择空组。

唯一移除的原订阅是临时免费节点订阅，符合只使用自己节点的要求。原作者历史日志未复制进生成配置；来源和作者标注保留。

## 补充分流如何工作

当前配置引用：

https://raw.githubusercontent.com/yeepZhang/qx-rules/main/supplemental.list

放置顺序：

1. 墨鱼原有专用规则（误杀修正、广告、微信、Google Voice、AI、GitHub、Spotify、国际媒体、哔哩、Apple）。
2. 补充业务规则（从原 YAML 的 92 个来源中取 85 个服务规则集）。
3. 墨鱼原有全球加速、国内网站规则。
4. 最终匹配仍由原主配置中的 final/兜底分流处理。本地规则优先级按 QX 运行设置执行。

补充列表排除 category-ads-all、private、private-ip、geolocation-cn、cn、cn-ip、geolocation-!cn，共 7 个通用源。广告和国内外兜底由墨鱼负责，不再添加另一套。

重合域名优先使用墨鱼原有规则：例如命中墨鱼 Spotify 就使用“声田音乐”，命中墨鱼国际媒体就使用“国际媒体”。补充分类只接管未被这些专用规则覆盖的请求。保留了全部 31 个扩展业务策略组，但不是每个组都会有独立命中；这是墨鱼优先的预期行为。

旧 `rules.list`（全量 92 个源）以及 categories/ 仍保留供兼容旧客户端和检查。新版主配置只引用 supplemental.list；请不要额外再订阅全量 rules.list，否则会重复引入通用规则。

## 更新

GitHub Actions 每天 UTC 20:23（北京时间次日 04:23）运行。也可在 Actions → Update QX rules → Run workflow 手动触发。使用仓库内置 GITHUB_TOKEN，无需提供节点或个人令牌。

每次执行测试，下载同一上游提交的全部文本，转换并检查数量，再一次 Git 提交发布。supplemental.list、rules.list、categories 和 manifest 同批更新。QX 补充分流每天检查更新；墨鱼资源使用原作者配置的更新周期。实际执行时刻可能受 GitHub 和 iOS 调度影响。

下载失败、空规则、未知表达式、数量下降超过 30% 或增长超过 100% 时不发布。只有人工确认合理变化后，才在手动运行时勾选 accept_size_change。公开仓库连续 60 天无活动时 GitHub 可能禁用定时工作流，需在 Actions 页面重新启用。

墨鱼主配置结构以仓库内快照为准，不会未经核对自动跟随作者修改整个主配置；它引用的远程规则/脚本仍直接跟随作者更新。将来升级基础快照时应重新运行保留性测试并核查变更。

## 本地维护

依赖 Python 3.9+、curl，无第三方 Python 包：

```sh
python3 -m unittest discover -s tests -v
python3 build_rules.py
python3 build_profile.py
```

sources.json 管理新增业务源和策略；build_profile.py 保留墨鱼原功能并生成公开配置。修改节点和证书仅在设备本地进行。自动生成会覆盖仓库 QuantumultX.conf，修改主配置结构应修改生成器或经过审查的基础快照。

manifest.json 保存上游 SHA、每类条数/哈希、完整与补充列表的条数/哈希。Git 提交可用于回滚；也可将资源 URL 的 main 换成历史提交 SHA 暂时固定版本。

转换语义：精确域名→host，+.域名→host-suffix，IPv4/IPv6→ip-cidr/ip6-cidr。源 YAML 的 no-resolve 未直接复制。设备匹配和脚本可用性需要在 QX 中验证，静态测试不代表节点、流媒体解锁或所有净化脚本实测成功。

## 来源

- 墨鱼原配置：https://ddgksf2013.top/Profile/QuantumultX.conf
- 公开规则：https://github.com/MetaCubeX/meta-rules-dat
- QX 官方示例：https://github.com/crossutility/Quantumult-X/blob/master/sample.conf
- GitHub 调度说明：https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule

原作者署名保留。LICENSE 为规则仓库上游 GPL-3.0 许可证；其源文本可通过 manifest 中的固定提交 URL 取得。
