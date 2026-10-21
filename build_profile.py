#!/usr/bin/env python3
"""Preserve the supplied Moyu profile, add service-only supplemental routing."""
import json
from pathlib import Path
import re
ROOT=Path(__file__).resolve().parent

def compose(base,sources):
    sections={m[1]:m[2] for m in re.finditer(r'^\[([^\]]+)\]\n(.*?)(?=^\[|\Z)',base,re.M|re.S)}
    sections['server_local']='\n# 请在 QX 本地添加自己的节点；本公开配置不包含节点凭据。\n\n'
    sections['server_remote']='\n# 已移除原模板的临时免费节点订阅；如有自己的订阅，可在设备内添加。\n\n'
    policy=sections['policy']
    # Keep original groups and alternatives. Only change empty regional defaults
    # for a single self-hosted node, and expose a manual default node selector.
    policy=policy.replace('static=声田音乐, 美国节点,','static=声田音乐, 默认代理, 美国节点,')
    policy=policy.replace('static=国际媒体, 台湾节点,','static=国际媒体, 默认代理, 台湾节点,')
    policy=re.sub(r'^url-latency-benchmark=美国节点,.*$',
        'static=美国节点, 默认代理, proxy, server-tag-regex=(?i)(美|us|states|american)',policy,flags=re.M)
    policy+='\n# 新增：默认节点选择及业务分流。墨鱼原有专用规则仍优先匹配。\n'
    policy+='static=默认代理, proxy, direct, server-tag-regex=.*\n'
    aliases={'🍏 苹果服务':'苹果服务','📺 欧美流媒体':'国际媒体','🎌 亚洲流媒体':'国际媒体',
             '🌍 非中国':'全球加速','🐟 漏网之鱼':'兜底分流','🛑 广告拦截':'reject',
             '🏠 私有网络':'direct','🔒 国内服务':'direct','Ⓜ️ 微软服务':'direct',
             '🎮 Steam':'direct','🖥️ PC 游戏':'direct','🎯 主机游戏':'direct'}
    names=list(dict.fromkeys([x['policy'] for x in sources]+['🐟 漏网之鱼']))
    for name in names:
        first=aliases.get(name,'默认代理')
        choices=list(dict.fromkeys([first,'默认代理','direct','reject']))
        policy+='static='+name+', '+', '.join(choices)+'\n'
    sections['policy']=policy+'\n'
    filters=sections['filter_remote']
    marker='https://raw.githubusercontent.com/ConnersHua/RuleGo/master/Surge/Ruleset/Proxy.list'
    if filters.count(marker)!=1:raise ValueError('Expected original Moyu global rule anchor')
    addition=('# 新增：仅补充业务服务，位于墨鱼专用规则之后、全球加速/国内兜底之前。\n'
        'https://raw.githubusercontent.com/yeepZhang/qx-rules/main/supplemental.list, tag=补充业务分流, update-interval=86400, opt-parser=false, enabled=true\n\n')
    sections['filter_remote']=filters.replace(marker,addition+marker)
    header=('# 墨鱼原配置 + 补充业务分流（无节点公开版）\n'
        '# 基础作者：ddgksf2013；基础版本：2026/10/11 V272\n'
        '# 来源：https://ddgksf2013.top/Profile/QuantumultX.conf\n'
        '# 原净化/重写/任务/DNS/MITM 设置及启用状态保持原样。\n'
        '# 导入前备份节点和本机 MITM 证书；导入后添加自己的节点。\n'
        '# 默认代理中选择节点；关闭分流匹配优化；按需要在设备开启重写与 MITM。\n'
        '# 只用一个美国节点时，声田音乐/国际媒体/美国节点默认使用默认代理。\n'
        '# 保留其他地区组供后续扩展，无对应地区节点时不要选择空组。\n\n')
    return header+''.join('['+name+']\n'+value for name,value in sections.items())

def main():
    base=(ROOT/'upstream/moyu.conf').read_text(encoding='utf-8')
    sources=json.loads((ROOT/'sources.json').read_text())
    output=compose(base,sources)
    (ROOT/'QuantumultX.conf').write_text(output,encoding='utf-8')
    print('Generated Moyu-first public profile:',len(output.encode()),'bytes')

if __name__=='__main__':main()
