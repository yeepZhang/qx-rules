import json
from pathlib import Path
import re
import unittest
import build_profile
ROOT=Path(__file__).resolve().parents[1]
def section(s,name):
    return re.search(r'^\['+name+r'\]\n(.*?)(?=^\[|\Z)',s,re.M|re.S)[1]
def active(s):
    return [x.strip() for x in s.splitlines() if x.strip() and not x.lstrip().startswith(('#',';'))]
class ProfileTests(unittest.TestCase):
    def setUp(self):
        self.base=(ROOT/'upstream/moyu.conf').read_text()
        self.output=build_profile.compose(self.base,json.loads((ROOT/'sources.json').read_text()))
    def test_original_features_preserved_exactly(self):
        for name in ['general','dns','task_local','rewrite_local','rewrite_remote','http_backend','mitm','filter_local']:
            self.assertEqual(section(self.base,name),section(self.output,name),name)
    def test_all_original_filters_preserved_in_order(self):
        old=active(section(self.base,'filter_remote'));new=active(section(self.output,'filter_remote'))
        self.assertEqual([x for x in new if x in old],old)
        self.assertEqual(len(old),12)
        self.assertEqual(len(new),13)
        insertion=next(i for i,l in enumerate(new) if 'supplemental.list' in l)
        self.assertGreater(insertion,next(i for i,l in enumerate(new) if 'tag=苹果服务' in l))
        self.assertLess(insertion,next(i for i,l in enumerate(new) if 'tag=全球加速' in l))
    def test_no_nodes_or_free_subscription(self):
        self.assertEqual(active(section(self.output,'server_local')),[])
        self.assertEqual(active(section(self.output,'server_remote')),[])
        self.assertNotIn('Ruk1ng001',self.output)
        self.assertNotIn('password=',self.output)
    def test_policy_references_resolve(self):
        policies=active(section(self.output,'policy'))
        names={l.split('=',1)[1].split(',')[0].strip() for l in policies}
        for l in active(section(self.output,'filter_remote')):
            match=re.search(r'force-policy=([^,]+)',l)
            if match:self.assertIn(match[1].strip(),names|{'direct','proxy','reject'})
        for i in json.loads((ROOT/'sources.json').read_text()):self.assertIn(i['policy'],names)
        for name in ['声田音乐','国际媒体','美国节点']:
            self.assertTrue(any(l.startswith('static='+name+', 默认代理,') for l in policies))
