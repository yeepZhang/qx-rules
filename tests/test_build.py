import json
from pathlib import Path
import tempfile
import unittest
import build_rules

class BuildTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.items=[{'name':'openai','kind':'domain','policy':'🤖 AI 服务','url':'https://raw.githubusercontent.com/MetaCubeX/meta-rules-dat/meta/geo/geosite/openai.list'}]
        (self.root/'sources.json').write_text(json.dumps(self.items))
        self.raw=self.root/'raw';self.raw.mkdir()
        (self.raw/'openai.list').write_text('+.openai.com\nchatgpt.com\n')
    def run_build(self,**kw):
        return build_rules.generate(self.root,self.raw,'a'*40,**kw)
    def test_output_without_any_node_file(self):
        self.run_build()
        self.assertEqual((self.root/'rules.list').read_text().splitlines()[-2:],['host-suffix, openai.com, 🤖 AI 服务','host, chatgpt.com, 🤖 AI 服务'])
        self.assertTrue((self.root/'categories/openai.list').is_file())
        info=json.loads((self.root/'manifest.json').read_text())
        self.assertEqual(info['rule_count'],2)
        self.assertEqual(info['source_count'],1)
    def test_invalid_source_leaves_old_output(self):
        self.run_build();old=(self.root/'rules.list').read_bytes()
        (self.raw/'openai.list').write_text('<html>error</html>')
        with self.assertRaises(ValueError):self.run_build()
        self.assertEqual(old,(self.root/'rules.list').read_bytes())
    def test_shrink_guard(self):
        self.run_build();old=(self.root/'rules.list').read_bytes()
        (self.raw/'openai.list').write_text('chatgpt.com\n')
        with self.assertRaises(ValueError):self.run_build()
        self.assertEqual(old,(self.root/'rules.list').read_bytes())
        self.run_build(accept=True)
    def test_bad_commit_rejected(self):
        with self.assertRaises(ValueError):build_rules.generate(self.root,self.raw,'oops')
    def test_repeat_is_deterministic(self):
        self.run_build();old=(self.root/'manifest.json').read_bytes()
        self.run_build()
        self.assertEqual(old,(self.root/'manifest.json').read_bytes())

if __name__=='__main__':unittest.main()
