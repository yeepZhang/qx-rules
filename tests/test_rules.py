import unittest
import rules_core as update

class ConversionTests(unittest.TestCase):
    def test_exact_suffix_and_wildcard(self):
        self.assertEqual(update.convert('a.example\n+.example.com\n*.wild.example\n','domain','AI'),
            ['host, a.example, AI','host-suffix, example.com, AI','host-wildcard, *.wild.example, AI'])
    def test_ip(self):
        self.assertEqual(update.convert('1.2.3.0/24\n2001:db8::/32\n','ipcidr','P'),
            ['ip-cidr, 1.2.3.0/24, P','ip6-cidr, 2001:db8::/32, P'])
    def test_bad_input_rejected(self):
        for data in ('<html>Oops</html>', 'regexp:.*', 'example.com, direct', '', '# empty'):
            with self.assertRaises(ValueError): update.convert(data,'domain','P')
    def test_duplicate_removed(self):
        self.assertEqual(len(update.convert('+.example.com\n+.example.com\n','domain','P')),1)
    def test_size_guard(self):
        with self.assertRaises(ValueError): update.check_size('x',10,100,False)
        update.check_size('x',10,100,True)
    def test_priority(self):
        items=[{'name':n,'kind':k} for n,k in [('cn-ip','ipcidr'),('google','domain'),('youtube','domain'),('private-ip','ipcidr'),('cn','domain'),('category-ads-all','domain'),('cloudflare-ip','ipcidr')]]
        names=[i['name'] for i in update.ordered(items)]
        self.assertLess(names.index('private-ip'),names.index('category-ads-all'))
        self.assertLess(names.index('youtube'),names.index('google'))
        self.assertLess(names.index('google'),names.index('cloudflare-ip'))
        self.assertEqual(names[-1],'cn-ip')

if __name__=='__main__': unittest.main()
