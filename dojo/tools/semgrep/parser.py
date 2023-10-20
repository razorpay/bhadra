from asyncio.log import logger
import json

from dojo.models import Finding


class SemgrepParser(object):

    def get_scan_types(self):
        return ["Semgrep JSON Report"]

    def get_label_for_scan_types(self, scan_type):
        return scan_type  # no custom label for now

    def get_description_for_scan_types(self, scan_type):
        return "Import Semgrep output (--json)"

    def get_findings(self, filename, test):
        data = json.load(filename)
        location=""
        dupes = dict()

        for item in data["findings"]:
            active = True
            verified = False
            is_mitigated = False
            if(item["status"] != "unresolved"):
                active = False
                is_mitigated = True
            finding = Finding(
                test=test,
                title=item["rule"] if "rule" in item else "NA",
                url=item["ruleurl"] if "ruleurl" in item else "NA",
                severity=self.convert_severity(item["severity"] if "severity" in item else "Info"),
                description="Description: " + item["ruledesc"] if "ruledesc" in item else "NA" +
                "\n" + "Identified rule: " + item["rule"] if "rule" in item else "NA"+
                "\n" + "Location: <a href=\"" + location+"\">"+item["location"] if "location" in item else "NA"+"</a>"+
                "\n" + "Policy: " + item["policy"] if "policy" in item else "NA"+
                "\n" + "Branch: " + item["branch"] if "branch" in item else "NA" +
                "\n" + "Category: " + item["category"] if "category" in item else "NA",
                file_path=item["location"] if "location" in item else "NA",
                static_finding=True,
                dynamic_finding=False,
                vuln_id_from_tool=item["finding_id"] if "finding_id" in item else "NA",
                unique_id_from_tool=item["finding_id"] if "finding_id" in item else "NA",
                nb_occurences=1,
                bu=item["bu"] if "bu" in item else "NA",
                active=active,
                is_mitigated=is_mitigated,
                priority=self.get_priority(item["severity"] if "severity" in item else "low")
            )

            

            # manage references from metadata
            if 'ruleurl' in item:
                finding.references = "\n" + item["ruleurl"]

            # manage mitigation from metadata
            if 'fix' in item:
                finding.mitigation = item["fix"]
            elif 'fix_regex' in item:
                finding.mitigation = "\n".join([
                    "**You can automaticaly apply this regex:**",
                    "\n```\n",
                    json.dumps(item["fix_regex"]),
                    "\n```\n",
                ])

            dupe_key = finding.title + finding.file_path + str(item["line"] if "line" in item else "NA") + finding.unique_id_from_tool

            if dupe_key in dupes:
                find = dupes[dupe_key]
                find.nb_occurences += 1
            else:
                dupes[dupe_key] = finding

        return list(dupes.values())

    def convert_severity(self, val):
        if "low" == val:
            return "Low"
        elif "medium" == val:
            return "Medium"
        elif "high" == val:
            return "High"
        else:
            return "Info"

    def get_priority(self,val):
        if "low" == val:
            return "P2"
        elif "medium" == val:
            return "P1"
        elif "high" == val:
            return "P0"
        else:
            return "P2"
