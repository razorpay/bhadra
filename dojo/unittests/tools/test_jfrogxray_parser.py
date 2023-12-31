from django.test import TestCase
from dojo.models import Test
from dojo.tools.jfrogxray.parser import JFrogXrayParser, decode_cwe_number


class TestJfrogJFrogXrayParser(TestCase):

    def test_parse_file_with_one_vuln(self):
        testfile = open("dojo/unittests/scans/jfrogxray/one_vuln.json")
        parser = JFrogXrayParser()
        findings = parser.get_findings(testfile, Test())
        testfile.close()
        self.assertEqual(1, len(findings))
        item = findings[0]
        self.assertEqual("debian:stretch:libx11", item.component_name)
        self.assertEqual("2:1.6.4-3", item.component_version)
        self.assertEqual("CVE-2018-14600", item.cve)
        self.assertEqual(787, item.cwe)

    def test_parse_file_with_many_vulns(self):
        testfile = open("dojo/unittests/scans/jfrogxray/many_vulns.json")
        parser = JFrogXrayParser()
        findings = parser.get_findings(testfile, Test())
        testfile.close()
        self.assertEqual(3, len(findings))

    def test_parse_file_with_many_vulns2(self):
        testfile = open("dojo/unittests/scans/jfrogxray/many_vulns2.json")
        parser = JFrogXrayParser()
        findings = parser.get_findings(testfile, Test())
        testfile.close()
        self.assertEqual(2, len(findings))
        item = findings[0]
        self.assertEqual("pip", item.component_name)
        self.assertEqual("9.0.1", item.component_version)
        item = findings[1]
        self.assertEqual("ubuntu:bionic:linux", item.component_name)
        self.assertEqual("4.15.0-88.88", item.component_version)
        self.assertEqual("CVE-2020-14386", item.cve)
        self.assertEqual(787, item.cwe)
        self.assertEqual("AV:L/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:H", item.cvssv3)

    def test_decode_cwe_number(self):
        with self.subTest(val="CWE-1234"):
            self.assertEqual(1234, decode_cwe_number("CWE-1234"))
        with self.subTest(val=""):
            self.assertEqual(0, decode_cwe_number(""))
        with self.subTest(val="cwe-1"):
            self.assertEqual(1, decode_cwe_number("cwe-1"))
