#!/usr/bin/env python3
"""
DMARC Failure Analysis Tool
Analyzes all DMARC reports to identify failure patterns and create action plan.
"""

import os
import zipfile
import gzip
import xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict
from datetime import datetime

def extract_xml(filepath):
    """Extract XML from .zip or .gz file."""
    filepath = Path(filepath)

    if filepath.suffix == '.gz':
        with gzip.open(filepath, 'rt', encoding='utf-8') as f:
            return f.read()
    elif filepath.suffix == '.zip':
        with zipfile.ZipFile(filepath, 'r') as z:
            xml_files = [f for f in z.namelist() if f.endswith('.xml')]
            if xml_files:
                with z.open(xml_files[0]) as f:
                    return f.read().decode('utf-8')
    elif filepath.suffix == '.xml':
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    return None

def parse_dmarc_report(xml_content):
    """Parse DMARC XML and extract key information."""
    root = ET.fromstring(xml_content)

    # Get report metadata
    report_meta = root.find('report_metadata')
    org_name = report_meta.findtext('org_name', 'Unknown') if report_meta is not None else 'Unknown'
    report_id = report_meta.findtext('report_id', 'Unknown') if report_meta is not None else 'Unknown'

    date_range = report_meta.find('date_range') if report_meta is not None else None
    if date_range is not None:
        begin = int(date_range.findtext('begin', '0'))
        end = int(date_range.findtext('end', '0'))
        date_begin = datetime.fromtimestamp(begin).strftime('%Y-%m-%d')
        date_end = datetime.fromtimestamp(end).strftime('%Y-%m-%d')
    else:
        date_begin = date_end = 'Unknown'

    # Parse records
    results = {
        'org': org_name,
        'date_begin': date_begin,
        'date_end': date_end,
        'total_messages': 0,
        'passed': 0,
        'failed': 0,
        'failures': []
    }

    for record in root.findall('record'):
        row = record.find('row')
        identifiers = record.find('identifiers')
        auth_results = record.find('auth_results')

        if row is None or identifiers is None:
            continue

        count = int(row.findtext('count', '0'))
        results['total_messages'] += count

        policy_eval = row.find('policy_evaluated')
        dkim_result = policy_eval.findtext('dkim', 'unknown') if policy_eval is not None else 'unknown'
        spf_result = policy_eval.findtext('spf', 'unknown') if policy_eval is not None else 'unknown'

        header_from = identifiers.findtext('header_from', 'Unknown')
        envelope_from = identifiers.findtext('envelope_from', 'Unknown')
        envelope_to = identifiers.findtext('envelope_to', 'Unknown')

        if dkim_result == 'pass' and spf_result == 'pass':
            results['passed'] += count
        else:
            results['failed'] += count

            # Get detailed auth results
            spf_domain = 'N/A'
            spf_auth_result = 'N/A'
            dkim_domain = 'N/A'
            dkim_auth_result = 'N/A'

            if auth_results is not None:
                spf = auth_results.find('spf')
                if spf is not None:
                    spf_domain = spf.findtext('domain', 'N/A')
                    spf_auth_result = spf.findtext('result', 'N/A')

                dkim = auth_results.find('dkim')
                if dkim is not None:
                    dkim_domain = dkim.findtext('domain', 'N/A')
                    dkim_auth_result = dkim.findtext('result', 'N/A')

            results['failures'].append({
                'count': count,
                'header_from': header_from,
                'envelope_from': envelope_from,
                'envelope_to': envelope_to,
                'source_ip': row.findtext('source_ip', 'Unknown'),
                'dkim_result': dkim_result,
                'spf_result': spf_result,
                'spf_domain': spf_domain,
                'spf_auth_result': spf_auth_result,
                'dkim_domain': dkim_domain,
                'dkim_auth_result': dkim_auth_result
            })

    return results

def main():
    dmarc_reports_dir = Path(__file__).parent.parent / 'email_monitoring' / 'dmarc_reports'

    print('=' * 80)
    print('📊 COMPREHENSIVE DMARC FAILURE ANALYSIS')
    print('=' * 80)
    print()

    # Find all report files
    report_files = []
    for pattern in ['*.xml.gz', '*.zip', '*.xml']:
        report_files.extend(dmarc_reports_dir.glob(pattern))

    # Exclude the analyzer script itself
    report_files = [f for f in report_files if 'analyzer' not in f.name]

    if not report_files:
        print(f'❌ No DMARC report files found in {dmarc_reports_dir}/')
        return

    print(f'Found {len(report_files)} DMARC report(s) to analyze\n')

    # Analyze all reports
    all_results = []
    total_messages = 0
    total_passed = 0
    total_failed = 0
    failure_patterns = defaultdict(lambda: {'count': 0, 'details': []})

    for report_file in sorted(report_files):
        try:
            xml_content = extract_xml(report_file)
            if xml_content:
                results = parse_dmarc_report(xml_content)
                all_results.append(results)

                total_messages += results['total_messages']
                total_passed += results['passed']
                total_failed += results['failed']

                # Categorize failures
                for failure in results['failures']:
                    pattern_key = failure['header_from']
                    failure_patterns[pattern_key]['count'] += failure['count']
                    failure_patterns[pattern_key]['details'].append({
                        'date': results['date_begin'],
                        'org': results['org'],
                        'envelope_from': failure['envelope_from'],
                        'envelope_to': failure['envelope_to'],
                        'spf_domain': failure['spf_domain'],
                        'spf_result': failure['spf_auth_result'],
                        'dkim_domain': failure['dkim_domain'],
                        'dkim_result': failure['dkim_auth_result']
                    })
        except Exception as e:
            print(f'⚠️  Error processing {report_file.name}: {e}')

    # Print summary
    print('=' * 80)
    print('📈 OVERALL STATISTICS')
    print('=' * 80)
    print(f'Total Messages:     {total_messages}')
    print(f'Passed:             {total_passed} ({total_passed/total_messages*100:.1f}%)' if total_messages > 0 else 'Passed: 0')
    print(f'Failed:             {total_failed} ({total_failed/total_messages*100:.1f}%)' if total_messages > 0 else 'Failed: 0')
    print()

    # Print failure patterns
    if failure_patterns:
        print('=' * 80)
        print('🔴 FAILURE PATTERNS BY HEADER FROM DOMAIN')
        print('=' * 80)
        print()

        for pattern, data in sorted(failure_patterns.items(), key=lambda x: x[1]['count'], reverse=True):
            print(f'❌ Header From: {pattern}')
            print(f'   Failed Messages: {data["count"]}')
            print(f'   Occurrences: {len(data["details"])}')
            print()

            # Show unique details
            unique_spf_domains = set(d['spf_domain'] for d in data['details'])
            unique_dkim_domains = set(d['dkim_domain'] for d in data['details'])

            print(f'   SPF Domains checked: {", ".join(unique_spf_domains)}')
            print(f'   DKIM Domains checked: {", ".join(unique_dkim_domains)}')
            print()

            # Show sample failures
            print('   Recent failures:')
            for detail in data['details'][:3]:
                print(f'     - {detail["date"]} ({detail["org"]}): SPF={detail["spf_result"]}, DKIM={detail["dkim_result"]}')
            print()

    # Generate action plan
    print('=' * 80)
    print('🎯 ACTION PLAN TO ACHIEVE 100% PASS RATE')
    print('=' * 80)
    print()

    if 'mail.minipass.me' in failure_patterns:
        print('🔧 ISSUE #1: Emails sent with "mail.minipass.me" domain')
        print()
        print('   ROOT CAUSE:')
        print('   - Some emails use "mail.minipass.me" in Header From instead of "minipass.me"')
        print('   - DKIM signature is for "minipass.me" domain → signature verification fails')
        print('   - SPF record is for "minipass.me" domain → SPF lookup fails')
        print()
        print('   LIKELY SOURCES:')
        print('   - System emails (root@mail.minipass.me, postmaster@mail.minipass.me)')
        print('   - Mail server hostname in From header')
        print('   - Default sender address in Postfix configuration')
        print()
        print('   FIX:')
        print('   1. Check Postfix configuration:')
        print('      docker exec mailserver postconf myhostname myorigin mydomain')
        print()
        print('   2. Set correct origin domain:')
        print('      docker exec mailserver postconf -e "myorigin = minipass.me"')
        print()
        print('   3. Check for system email aliases:')
        print('      docker exec mailserver cat /etc/aliases')
        print()
        print('   4. Update any scripts/cron jobs sending with wrong domain')
        print()
        print('   VERIFICATION:')
        print('   - Wait 24-48 hours for new DMARC reports')
        print('   - Run: python scripts/fetch_dmarc_reports.py')
        print('   - Check pass rate increases to 100%')
        print()

    if not failure_patterns:
        print('✅ NO FAILURES FOUND - EMAIL SYSTEM IS 100% COMPLIANT!')
        print()
        print('   Current configuration is optimal. Maintain by:')
        print('   - Running daily DMARC report fetches')
        print('   - Monitoring pass rates weekly')
        print('   - Keeping DKIM keys rotated annually')
        print()

    print('=' * 80)
    print('📋 MONITORING RECOMMENDATIONS')
    print('=' * 80)
    print()
    print('1. DAILY: Run DMARC report fetcher')
    print('   python scripts/fetch_dmarc_reports.py')
    print()
    print('2. WEEKLY: Check pass rate trends')
    print('   python scripts/analyze_dmarc_failures.py')
    print()
    print('3. MONTHLY: Review DMARC policy')
    print('   - Currently: "none" (monitor only)')
    print('   - Target: "quarantine" (95%+ pass rate for 30 days)')
    print('   - Goal: "reject" (99%+ pass rate for 90 days)')
    print()
    print('4. QUARTERLY: Rotate DKIM keys')
    print('   - Generate new key pair')
    print('   - Update DNS records')
    print('   - Update mail server configuration')
    print()
    print('=' * 80)
    print('✅ Analysis complete')
    print('=' * 80)

if __name__ == '__main__':
    main()
