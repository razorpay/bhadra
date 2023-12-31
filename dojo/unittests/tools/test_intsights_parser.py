from django.test import TestCase
from dojo.models import Test
from dojo.tools.intsights.parser import IntSightsParser


class TestIntSightsParser(TestCase):
    def test_intsights_parser_with_no_vuln_has_no_findings_json(self):
        with self.assertRaises(ValueError):
            testfile = open("dojo/unittests/scans/intsights/intsights_zero_vul.json")
            parser = IntSightsParser()
            findings = parser.get_findings(testfile, Test())

    def test_intsights_parser_with_no_vuln_has_no_findings_csv(self):
        with self.assertRaises(ValueError):
            testfile = open("dojo/unittests/scans/intsights/intsights_zero_vuln.csv")
            parser = IntSightsParser()
            findings = parser.get_findings(testfile, Test())

    def test_intsights_parser_with_one_critical_vuln_has_one_findings_json(self):
        testfile = open("dojo/unittests/scans/intsights/intsights_one_vul.json")
        parser = IntSightsParser()
        findings = parser.get_findings(testfile, Test())
        testfile.close()

        self.assertEqual(1, len(findings))

        finding = list(findings)[0]

        self.assertEqual('5c80dbf83b4a3900078b6be6', finding.unique_id_from_tool)
        self.assertEqual('HTTP headers weakness in initech.com web server', finding.title)
        self.assertEqual('Critical', finding.severity)
        self.assertEqual("https://dashboard.intsights.com/#/threat-command/alerts?search=5c80dbf83b4a3900078b6be6",
                          finding.references)

    def test_intsights_parser_with_one_critical_vuln_has_one_findings_csv(self):
        testfile = open("dojo/unittests/scans/intsights/intsights_one_vuln.csv")
        parser = IntSightsParser()
        findings = parser.get_findings(testfile, Test())
        testfile.close()
        self.assertEqual(1, len(findings))

        finding = list(findings)[0]

        self.assertEqual("mn7xy83finmmth4ja363rci9", finding.unique_id_from_tool)
        self.assertEqual("HTTP headers weakness in company-domain.com web server", finding.title)

    def test_intsights_parser_with_many_vuln_has_many_findings_json(self):
        testfile = open("dojo/unittests/scans/intsights/intsights_many_vul.json")
        parser = IntSightsParser()
        findings = parser.get_findings(testfile, Test())
        testfile.close()
        self.assertEqual(3, len(findings))

    def test_intsights_parser_with_many_vuln_has_many_findings_csv(self):
        testfile = open("dojo/unittests/scans/intsights/intsights_many_vuln.csv")
        parser = IntSightsParser()
        findings = parser.get_findings(testfile, Test())
        testfile.close()
        self.assertEqual(9, len(findings))

    def test_intsights_parser_invalid_text_with_error_csv(self):
        with self.assertRaises(ValueError):
            testfile = open("dojo/unittests/scans/intsights/intsights_invalid_file.txt")
            parser = IntSightsParser()
            findings = parser.get_findings(testfile, Test())

    def test_intsights_parser_empty_with_error_json(self):
        with self.assertRaises(ValueError):
            testfile = open("dojo/unittests/scans/intsights/empty_with_error.json")
            parser = IntSightsParser()
            findings = parser.get_findings(testfile, Test())
