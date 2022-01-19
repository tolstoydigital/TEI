import unittest
import urllib
import urllib.request
import re
from lxml import etree
import re
import os
import requests
from io import StringIO

class Tolstoy_fiction_and_essays_test(unittest.TestCase):
    def setUp(self):
        self.tests_dir = os.getcwd()
        schema = requests.get('https://tei-c.org/release/xml/tei/custom/schema/relaxng/tei_all.rng').text
        schema = schema.replace('<?xml version="1.0" encoding="utf-8"?>', '<?xml version="1.0"?>', 1)
        relaxng_doc = etree.parse(StringIO(schema))
        self.tei_relaxng = etree.RelaxNG(relaxng_doc)
        self.xml = os.listdir(os.path.join(self.tests_dir, "TEI/fiction_and_essays/"))
        self.checked_xml = []
       
        os.chdir(os.path.join(self.tests_dir, "TEI/fiction_and_essays/"))

        for file in self.xml:        
            try:
                tree = etree.parse(file)
                self.checked_xml.append(file)
            except etree.XMLSyntaxError as err:
                 print(err)
    
    def test_tei(self):
        for file in self.checked_xml:

            with self.subTest(file=file):
                tree = etree.parse(file)
                try:
                    tree = etree.parse(file)

                    result = self.tei_relaxng.assert_(tree)
                except AssertionError as err:
                    print(file, 'TEI validation error:', err)
