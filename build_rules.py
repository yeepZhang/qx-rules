#!/usr/bin/env python3
"""Generate public Quantumult X rules from a single upstream commit. No secrets needed."""
import argparse
import concurrent.futures
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile
from rules_core import convert, ordered, check_size, load_sources, fetch, digest, validate_rules

ROOT=Path(__file__).resolve().parent
GENERAL_SOURCES={'category-ads-all','private','private-ip','cn','cn-ip','geolocation-cn','geolocation-!cn'}

def generate(root, raw, commit, accept=False):
    if not re.fullmatch(r'[0-9a-f]{40}',commit):raise ValueError('Invalid upstream SHA')
    sources=load_sources(root/'sources.json')
    previous=json.loads((root/'manifest.json').read_text()) if (root/'manifest.json').exists() else {}
    old=previous.get('sources',{})
    if set(old)-{i['name'] for i in sources} and not accept:raise ValueError('Source removal requires explicit review')
    combined=[];supplement=[];metadata={};total=0;supplement_count=0;supplement_sources=0
    valid={i['policy'] for i in sources}
    with tempfile.TemporaryDirectory(prefix='.stage-',dir=root) as directory:
        stage=Path(directory);(stage/'categories').mkdir()
        for item in ordered(sources):
            name=item['name'];data=(raw/(name+'.list')).read_bytes()
            lines=convert(data.decode('utf-8-sig'),item['kind'],item['policy'])
            validate_rules(lines,valid)
            count=len(lines);check_size(name,count,old.get(name,{}).get('count'),accept)
            metadata[name]={'url':item['url'].replace('/meta/geo/','/'+commit+'/geo/'),
                'count':count,'sha256':digest(data),'policy':item['policy']}
            (stage/'categories'/(name+'.list')).write_text('\n'.join(lines)+'\n',encoding='utf-8')
            combined.extend(['# '+name]+lines);total+=count
            if name not in GENERAL_SOURCES:
                supplement.extend(['# '+name]+lines)
                supplement_count+=count;supplement_sources+=1
        text='\n'.join(combined)+'\n'
        (stage/'rules.list').write_text(text,encoding='utf-8')
        supplement_text='\n'.join(supplement)+'\n'
        (stage/'supplemental.list').write_text(supplement_text,encoding='utf-8')
        manifest={'upstream_commit':commit,'source_count':len(sources),'rule_count':total,
            'business_policy_count':len(valid|{'🐟 漏网之鱼'}),'rules_sha256':digest(text.encode()),'sources':metadata,
            'supplemental_source_count':supplement_sources,'supplemental_rule_count':supplement_count,
            'supplemental_sha256':digest(supplement_text.encode()),'supplemental_excluded_sources':sorted(GENERAL_SOURCES)}
        (stage/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        # Validate the entire batch before changing generated outputs.
        # Remote publication happens later in ONE git commit; failed workflow steps never push.
        if (root/'categories').exists():shutil.rmtree(root/'categories')
        os.replace(stage/'categories',root/'categories')
        os.replace(stage/'rules.list',root/'rules.list')
        os.replace(stage/'supplemental.list',root/'supplemental.list')
        os.replace(stage/'manifest.json',root/'manifest.json')
    return manifest

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--raw-dir',type=Path,help='local raw snapshot (requires --commit)')
    p.add_argument('--commit',help='upstream SHA for local snapshot')
    p.add_argument('--accept-size-change',action='store_true',help='allow reviewed large changes')
    args=p.parse_args()
    try:
        if args.raw_dir:
            if not args.commit:p.error('--raw-dir requires --commit')
            info=generate(ROOT,args.raw_dir,args.commit,args.accept_size_change)
        else:
            commit=json.loads(fetch('https://api.github.com/repos/MetaCubeX/meta-rules-dat/commits/meta'))['sha']
            if not re.fullmatch(r'[0-9a-f]{40}',commit):raise ValueError('Invalid upstream SHA')
            sources=load_sources(ROOT/'sources.json')
            with tempfile.TemporaryDirectory(prefix='.download-',dir=ROOT) as directory:
                raw=Path(directory)
                def download(item):
                    url=item['url'].replace('/meta/geo/','/'+commit+'/geo/')
                    (raw/(item['name']+'.list')).write_bytes(fetch(url))
                with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:list(pool.map(download,sources))
                info=generate(ROOT,raw,commit,args.accept_size_change)
        print(f"Generated {info['source_count']} sources / {info['rule_count']} rules; upstream {info['upstream_commit']}")
    except (ValueError,OSError,KeyError) as e:
        print(f'Build failed; do not publish: {e}',file=sys.stderr);sys.exit(1)

if __name__=='__main__':main()
