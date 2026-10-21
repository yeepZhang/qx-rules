"""Public rule conversion utilities; no node/subscription/config access."""
import hashlib
import ipaddress
import json
import re
import subprocess
from urllib.parse import urlsplit
REPO = 'https://raw.githubusercontent.com/MetaCubeX/meta-rules-dat/'
PROXY = '默认代理'
NODE = '美国自建'
BUILTINS = {'direct', 'reject'}


def digest(data):
    return hashlib.sha256(data).hexdigest()

def convert(text, kind, policy):
    result = []
    for number, raw in enumerate(text.splitlines(), 1):
        value = raw.strip()
        if not value or value.startswith(('#', '//')):
            continue
        if kind == 'ipcidr':
            try:
                net = ipaddress.ip_network(value, strict=True)
            except ValueError as e:
                raise ValueError(f'Invalid CIDR at line {number}: {value}') from e
            rule = 'ip-cidr' if net.version == 4 else 'ip6-cidr'
            value = str(net)
        elif kind == 'domain':
            rule = 'host'
            if value.startswith('+.'):
                rule, value = 'host-suffix', value[2:]
            elif '*' in value or '?' in value:
                rule = 'host-wildcard'
            if not value or not re.fullmatch(r'[a-zA-Z0-9_*?.-]+', value) or value.startswith('.') or '..' in value:
                raise ValueError(f'Unsupported domain expression at line {number}: {value}')
        else:
            raise ValueError(f'Unsupported behavior: {kind}')
        result.append(f'{rule}, {value}, {policy}')
    result = list(dict.fromkeys(result))
    if not result:
        raise ValueError('Empty ruleset')
    return result

def check_size(name, new, old, accept):
    if new <= 0:
        raise ValueError(f'{name}: empty ruleset')
    if old and not accept and (new < old * 0.7 or new > old * 2):
        raise ValueError(f'{name}: suspicious size change {old} -> {new}; review and use --accept-size-change if intended')

def ordered(items):
    # Stable sort: keep source order within each tier. Specific domains precede
    # broad platform lists and IP ranges; private IPs must remain first.
    broad = {'google', 'apple', 'microsoft', 'aws', 'azure', 'cloudflare', 'amazon'}
    def rank(item):
        n = item['name']
        if n in {'private', 'private-ip'}: return 0
        if n == 'category-ads-all': return 1
        if n == 'cn-ip': return 8
        if item['kind'] == 'ipcidr': return 7
        if n in {'geolocation-cn', 'cn'}: return 5
        if n == 'geolocation-!cn': return 6
        if n in broad: return 4
        return 2
    return sorted(items, key=rank)

def load_sources(path):
    items = json.loads(path.read_text())
    names = set()
    for item in items:
        n, p, url = item['name'], item['policy'], item['url']
        if not re.fullmatch(r'[a-z0-9_!@.-]+', n) or n in names or n in {'.', '..'}:
            raise ValueError(f'Unsafe or duplicate source name: {n}')
        if not p or any(c in p for c in ',\r\n=') or p in BUILTINS | {PROXY, NODE}:
            raise ValueError('Invalid policy name')
        if not url.startswith(REPO + 'meta/geo/') or not url.endswith('.list') or '..' in url:
            raise ValueError(f'Unsupported source URL for {n}')
        if item['kind'] not in {'domain', 'ipcidr'}:
            raise ValueError(f'Unsupported source type for {n}')
        names.add(n)
    if not items:
        raise ValueError('No sources')
    return items

def fetch(url):
    parts = urlsplit(url)
    if parts.scheme != 'https' or parts.hostname not in {'raw.githubusercontent.com', 'api.github.com'}:
        raise ValueError('Unexpected download host')
    process = subprocess.run(['curl', '--fail', '--silent', '--show-error', '--location',
        '--proto', '=https', '--proto-redir', '=https', '--connect-timeout', '15',
        '--max-time', '90', '--retry', '2', url], capture_output=True)
    if process.returncode:
        raise ValueError(f'Download failed: {parts.path} (curl {process.returncode})')
    if len(process.stdout) > 30_000_000:
        raise ValueError('Download exceeds 30 MB limit')
    return process.stdout

def validate_rules(lines, valid):
    for line in lines:
        parts = [x.strip() for x in line.split(',')]
        if len(parts) != 3 or parts[0] not in {'host', 'host-suffix', 'host-wildcard', 'host-keyword', 'ip-cidr', 'ip6-cidr'}:
            raise ValueError(f'Invalid rule: {line}')
        if parts[2] not in valid: raise ValueError(f'Unknown policy in rule: {line}')
        if parts[0] in {'ip-cidr', 'ip6-cidr'}:
            net = ipaddress.ip_network(parts[1], strict=True)
            if (net.version == 6) != (parts[0] == 'ip6-cidr'):
                raise ValueError('IP version mismatch')
        elif not re.fullmatch(r'[a-zA-Z0-9_*?.-]+', parts[1]):
            raise ValueError('Unsafe domain rule')
