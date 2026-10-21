# Quantumult X 远程分流规则

本仓库仅托管公开分流规则及转换程序，不包含节点凭据、私人订阅地址或完整设备配置。

## 订阅地址

合并规则（推荐）：

https://raw.githubusercontent.com/yeepZhang/qx-rules/main/rules.list

包含全部 92 个来源规则集，保留原业务策略和顺序。将下面一行放入 Quantumult X 的 `[filter_remote]`：

```ini
https://raw.githubusercontent.com/yeepZhang/qx-rules/main/rules.list, tag=完整业务分流, update-interval=86400, opt-parser=false, enabled=true
```

主配置需定义匹配的中文策略组，个人例外保留在 `[filter_local]`，并设置 `final, 🐟 漏网之鱼`。不要给合并资源设置 force-policy，否则会覆盖所有业务分类。关闭“分流匹配优化”，以匹配记录验证实际行为。

分类文件位于 `categories/`，需要时也可单独引用；不要同时订阅合并文件和全套分类文件。

## 自动更新

GitHub Actions 每天 UTC 20:23（北京时间次日 04:23）更新，也可在 Actions → Update QX rules → Run workflow 手动触发。执行顺序：测试 → 下载同一上游 Git 提交的全部规则 → 转换/校验 → 单次 Git 提交发布。无需配置个人令牌或节点 Secrets，使用仓库内置 GITHUB_TOKEN。

QX 每 86400 秒检查资源更新；GitHub 调度和客户端刷新均可能延迟。若公开仓库连续 60 天没有活动，GitHub 可能禁用定时工作流，届时在 Actions 页面重新启用。仓库更新不等于设备已更新，可在 QX 手动刷新。

下载失败、空规则、未知表达式、条数下降超过 30% 或增长超过 100% 默认终止，不推送。审查确认上游大幅变化合理后，可在手动触发时勾选 accept_size_change。不要为绕过未知转换错误而跳过规则。

所有输出通过一个 Git 提交发布，合并文件避免分类之间下载版本不同。失败运行不会更新远端已有规则。规则回滚可使用 Git revert 恢复旧版本；如需暂时固定旧快照，在 Raw URL 中把 main 替换为对应提交 SHA，然后暂停自动更新或在问题解决后恢复 main。

## 本地执行

Python 3.9+ 与 curl，无第三方 Python 依赖：

```sh
python3 -m unittest discover -s tests -v
python3 build_rules.py
```

离线生成（需自行准备同一提交的原始 .list 文件）：

```sh
python3 build_rules.py --raw-dir /path/to/raw --commit 上游完整40位提交号
```

sources.json 定义来源、domain/ipcidr 类型和业务策略。新增分类时，也要在自己的 QX 主配置添加对应策略组；规则内容更新不要求重新导入主配置。

## 转换与范围

上游为 MetaCubeX/meta-rules-dat 的同源文本 .list，省掉 MRS 二进制解码步骤。精确域名转 host，+. 域名转 host-suffix；IPv4/IPv6 转 ip-cidr/ip6-cidr。未知表达式导致失败。

顺序：私有网络 → 广告 → 具体业务 → 宽泛平台 → 国内域名 → 非中国域名 → 业务 IP → 国内 IP。个人例外、节点绕行和 final 属于设备主配置，不由本仓库发布。源 YAML 的 no-resolve 参数没有直接复制，IP 匹配按 QX 原生语义执行。

manifest.json 记录上游提交、每类数量和内容哈希、合并文件哈希。转换程序不访问任何节点配置。静态规则检查不能替代 QX 设备上的导入、连接和匹配验证。

来源与许可：

- https://github.com/MetaCubeX/meta-rules-dat
- https://github.com/crossutility/Quantumult-X/blob/master/sample.conf
- https://ddgksf2013.top/Profile/QuantumultX.conf （设备配置结构参考）
- https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule

保留上游 GPL-3.0 许可证于 LICENSE；源文本可按 manifest.json 中固定提交的 URL 取得。
