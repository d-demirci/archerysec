# -*- coding: utf-8 -*-
#                    _
#     /\            | |
#    /  \   _ __ ___| |__   ___ _ __ _   _
#   / /\ \ | '__/ __| '_ \ / _ \ '__| | | |
#  / ____ \| | | (__| | | |  __/ |  | |_| |
# /_/    \_\_|  \___|_| |_|\___|_|   \__, |
#                                     __/ |
#                                    |___/
# Copyright (C) 2017 Anand Tiwari
#
# Email:   anandtiwarics@gmail.com
# Twitter: @anandtiwarics
#
# This file is part of ArcherySec Project.

import hashlib
import json
import uuid
from datetime import datetime

from dashboard.views import trend_update
from staticscanners.models import StaticScanResultsDb, StaticScansDb
from utility.email_notify import email_sch_notify

vul_col = ""
Target = ""
VulnerabilityID = ""
PkgName = ""
InstalledVersion = ""
FixedVersion = ""
Title = ""
Description = ""
Severity = ""
References = ""


def gitlabsca_report_json(data, project_id, scan_id):
    """

    :param data:
    :param project_id:
    :param scan_id:
    :return:
    """
    date_time = datetime.now()

    vul_col = ""

    vuln = data["vulnerabilities"]

    for vuln_data in vuln:

        try:
            name = vuln_data["message"]
        except Exception:
            name = "Not Found"

        try:
            description = vuln_data["description"]
        except Exception:
            description = "Not Found"

        # try:
        #     cve = vuln_data["cve"]
        # except Exception:
        #     cve = "Not Found"

        # try:
        #     scanner = vuln_data["scanner"]
        # except Exception:
        #     scanner = "Not Found"

        # try:
        #     location = vuln_data["location"]
        # except Exception:
        #     location = "Not Found"

        # try:
        #     identifiers = vuln_data["identifiers"]
        # except Exception:
        #     identifiers = "Not Found"

        try:
            severity = vuln_data["severity"]
        except Exception:
            severity = "Not Found"

        try:
            file = vuln_data["location"]["file"]
        except Exception:
            file = "Not Found"

        if severity == "Critical":
            vul_col = "critical"

        elif severity == "High":
            vul_col = "danger"

        elif severity == "Medium":
            vul_col = "warning"

        elif severity == "Low":
            vul_col = "info"

        elif severity == "Unknown":
            severity = "Low"
            vul_col = "info"

        elif severity == "Everything else":
            severity = "Low"
            vul_col = "info"

        vul_id = uuid.uuid4()

        dup_data = str(name) + str(severity) + str(file)

        duplicate_hash = hashlib.sha256(dup_data.encode("utf-8")).hexdigest()

        match_dup = StaticScanResultsDb.objects.filter(dup_hash=duplicate_hash).values(
            "dup_hash"
        )
        lenth_match = len(match_dup)

        if lenth_match == 0:
            duplicate_vuln = "No"

            false_p = StaticScanResultsDb.objects.filter(
                false_positive_hash=duplicate_hash
            )
            fp_lenth_match = len(false_p)

            if fp_lenth_match == 1:
                false_positive = "Yes"
            else:
                false_positive = "No"

            save_all = StaticScanResultsDb(
                vuln_id=vul_id,
                date_time=date_time,
                scan_id=scan_id,
                project_id=project_id,
                title=name,
                description=description,
                fileName=file,
                severity=severity,
                severity_color=vul_col,
                vuln_status="Open",
                dup_hash=duplicate_hash,
                vuln_duplicate=duplicate_vuln,
                false_positive=false_positive,
                scanner="Gitlabsca",
            )
            save_all.save()

        else:
            duplicate_vuln = "Yes"

            save_all = StaticScanResultsDb(
                vuln_id=vul_id,
                date_time=date_time,
                scan_id=scan_id,
                project_id=project_id,
                title=name,
                description=description,
                fileName=file,
                severity=severity,
                severity_color=vul_col,
                vuln_status="Duplicate",
                dup_hash=duplicate_hash,
                vuln_duplicate=duplicate_vuln,
                false_positive="Duplicate",
                scanner="Gitlabsca",
            )
            save_all.save()

    all_findbugs_data = StaticScanResultsDb.objects.filter(
        scan_id=scan_id, false_positive="No"
    )

    duplicate_count = StaticScanResultsDb.objects.filter(
        scan_id=scan_id, vuln_duplicate="Yes"
    )

    total_vul = len(all_findbugs_data)
    total_critical = len(all_findbugs_data.filter(severity="Critical"))
    total_high = len(all_findbugs_data.filter(severity="High"))
    total_medium = len(all_findbugs_data.filter(severity="Medium"))
    total_low = len(all_findbugs_data.filter(severity="Low"))
    total_duplicate = len(duplicate_count.filter(vuln_duplicate="Yes"))

    StaticScansDb.objects.filter(scan_id=scan_id).update(
        date_time=date_time,
        total_vul=total_vul,
        critical_vul=total_critical,
        high_vul=total_high,
        medium_vul=total_medium,
        low_vul=total_low,
        total_dup=total_duplicate,
        scanner="Gitlabsca",
    )
    trend_update()
    subject = "Archery Tool Scan Status - GitLab Dependency Report Uploaded"
    message = (
        "GitLab Dependency Scanner has completed the scan "
        "  %s <br> Total: %s <br>High: %s <br>"
        "Medium: %s <br>Low %s"
        % (Target, total_vul, total_high, total_medium, total_low)
    )

    email_sch_notify(subject=subject, message=message)


parser_header_dict = {
    "gitlabsca_scan": {
        "displayName": "Gitlab Dependancy Scanner",
        "dbtype": "StaticScans",
        "dbname": "Gitlabsca",
        "type": "JSON",
        "parserFunction": gitlabsca_report_json,
        "icon": "/static/tools/gitlab.png"
    }
}
