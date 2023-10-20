import hashlib
import json
from urllib.parse import urlparse
from dojo.models import Endpoint, Finding

SEVERITY = {
    "HIGH":"High",
    "LOW":"Low",
    "MODERATE":"Medium",
    "CRITICAL":"Critical",
    "INFO":"Informational"
}

PRIORITY = {
    "CRITICAL":"P0",
    "HIGH":"P1",
    "MODERATE":"P1",
    "LOW":"P2",
    "INFO":"P2"
}

class dependabotParser(object):
    """
    dependabot
    """
    def get_scan_types(self):
        return ["Dependabot Scan"]

    def get_label_for_scan_types(self, scan_type):
        return "Dependabot Scan"

    def get_description_for_scan_types(self, scan_type):
        return "Dependabot report file can be imported in JSON format (option --json)."

    def get_findings(self, file, test):
        data = json.load(file)
        url = ""

        try:
            vulnerability = data['findings']
        except (KeyError, StopIteration):
            return

        result = []
        for item in vulnerability:
            active = True
            verified = False
            is_mitigated = False
            isFixed = False

            if "permalink" in item:
                url = item["permalink"]
            if "dismisser" in item and item["dismisser"] != "":
                active = False
                verified = True
                is_mitigated = True
            if "isFixed" in item:
                isFixed = item['isFixed']
                if isFixed:
                    active = False
                    verified = True
                    is_mitigated = True

            finding = Finding(title = item["packageSummary"],
                            test = test,
                            priority = PRIORITY[item["severity"]],
                            url = url,
                            description = item["description"],
                            severity = SEVERITY[item["severity"]],
                            date = item["createdDate"],
                            sourcefile = item["packagePath"],
                            component_name = item["packageName"],
                            created = item["runDate"],
                            repository = item["repository"],
                            dismissed_date = item["dismissedAt"],
                            dismisser = item["dismisser"],
                            bu=item["bu"] if "bu" in item else "NA",
                            package_ecosystem = item["packageEcosystem"],
                            fixed_version = item["fixedVersion"],
                            vulnerable_version = item["vulnVersion"],
                            unique_id_from_tool = item["alertID"],
                            references = url,
                            active = active,
                            verified = verified,
                            is_mitigated = is_mitigated,
                            static_finding = True,
                            dynamic_finding = False)
            result.append(finding)

        return result
