import json
import logging

from dojo.models import Endpoint, Finding
PINGSAFE_SEVERITIES = {
    "CRITICAL": "Critical",
    "HIGH": "High",
    "MEDIUM": "Medium",
    "LOW": "Low",
    "UNKNOWN": "Info",
}
PINGSAFE_PRIORITIES = {
    "Highest": "P0",
    "High": "P1",
    "Medium": "P2",
    "Low": "P3"
} 
class PingsafeParser:
    def get_scan_types(self):
        return ["Pingsafe Scan"]

    def get_label_for_scan_types(self, scan_type):
        return "Pingsafe Scan"

    def get_description_for_scan_types(self, scan_type):
        return "Import Pingsafe scan report."

    def create_findings(self, data, test):
        items = list()
        for id,issueDetails in data.items():
            status = issueDetails['isClosed']
            if status == "yes":
                active = False
                is_mitigated = True
            else:
                active = True
                is_mitigated = False


            priority = PINGSAFE_PRIORITIES["High"]
            severity = PINGSAFE_SEVERITIES[issueDetails['severity']]
            
            
            finding = Finding(
                    test=test,
                    title=issueDetails['title'],
                    severity=severity,
                    priority=priority,
                    description=issueDetails['description'],
                    static_finding=True,
                    dynamic_finding=False,
                    vuln_id_from_tool=id,
                    unique_id_from_tool=id,
                    active = active,
                    is_mitigated = is_mitigated,
                    false_p=False,
                    duplicate=False,
                    out_of_scope=False,
                    mitigated=None
                )
            items.append(finding)
        return items
    
    def get_findings(self, scan_file, test):

        scan_data = scan_file.read()

        try:
            data = json.loads(str(scan_data, 'utf-8'))
        except:
            data = json.loads(scan_data)

        # Legacy format is empty
        if data is None:
            return list()
    
        items = self.create_findings(data,test)
        return items
