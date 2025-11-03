#!/usr/bin/env python3
"""
DMARC Report Analyzer
Analyzes DMARC XML reports from email providers (Google, Outlook, etc.)
and generates readable Markdown reports with AI-powered recommendations.
"""

import os
import gzip
import zipfile
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
import json

try:
    import google.generativeai as genai
    from dotenv import load_dotenv
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("⚠️  Google Gemini not available. Install with: pip install google-generativeai python-dotenv")


class DMARCReportAnalyzer:
    """Analyzes DMARC XML reports and generates summaries."""

    def __init__(self, use_ai: bool = True):
        self.use_ai = use_ai and GEMINI_AVAILABLE

        if self.use_ai:
            load_dotenv()
            api_key = os.getenv('GEMINI_API_KEY')
            if api_key:
                genai.configure(api_key=api_key)
                self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
                print("✓ Google Gemini AI enabled for analysis\n")
            else:
                self.use_ai = False
                print("⚠️  GEMINI_API_KEY not found in .env file. AI analysis disabled.\n")

    def extract_xml_from_file(self, filepath: str) -> str:
        """Extract XML content from .xml.gz or .zip files."""
        filepath = Path(filepath)

        if filepath.suffix == '.gz':
            with gzip.open(filepath, 'rt', encoding='utf-8') as f:
                return f.read()
        elif filepath.suffix == '.zip':
            with zipfile.ZipFile(filepath, 'r') as z:
                # Get the first XML file in the zip
                xml_files = [f for f in z.namelist() if f.endswith('.xml')]
                if xml_files:
                    with z.open(xml_files[0]) as f:
                        return f.read().decode('utf-8')
        elif filepath.suffix == '.xml':
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()

        raise ValueError(f"Unsupported file format: {filepath.suffix}")

    def parse_dmarc_report(self, xml_content: str) -> Dict[str, Any]:
        """Parse DMARC XML report into structured data."""
        root = ET.fromstring(xml_content)

        # Extract report metadata
        metadata = {}
        report_meta = root.find('report_metadata')
        if report_meta is not None:
            metadata['org_name'] = report_meta.findtext('org_name', 'Unknown')
            metadata['email'] = report_meta.findtext('email', 'Unknown')
            metadata['report_id'] = report_meta.findtext('report_id', 'Unknown')

            date_range = report_meta.find('date_range')
            if date_range is not None:
                begin = int(date_range.findtext('begin', '0'))
                end = int(date_range.findtext('end', '0'))
                metadata['date_begin'] = datetime.fromtimestamp(begin).strftime('%Y-%m-%d %H:%M:%S')
                metadata['date_end'] = datetime.fromtimestamp(end).strftime('%Y-%m-%d %H:%M:%S')

        # Extract published policy
        policy = {}
        policy_pub = root.find('policy_published')
        if policy_pub is not None:
            policy['domain'] = policy_pub.findtext('domain', 'Unknown')
            policy['adkim'] = policy_pub.findtext('adkim', 'r')
            policy['aspf'] = policy_pub.findtext('aspf', 'r')
            policy['p'] = policy_pub.findtext('p', 'none')
            policy['sp'] = policy_pub.findtext('sp', 'none')
            policy['pct'] = policy_pub.findtext('pct', '100')

        # Extract records
        records = []
        for record in root.findall('record'):
            rec_data = {}

            # Row data
            row = record.find('row')
            if row is not None:
                rec_data['source_ip'] = row.findtext('source_ip', 'Unknown')
                rec_data['count'] = int(row.findtext('count', '0'))

                policy_eval = row.find('policy_evaluated')
                if policy_eval is not None:
                    rec_data['disposition'] = policy_eval.findtext('disposition', 'none')
                    rec_data['dkim_result'] = policy_eval.findtext('dkim', 'unknown')
                    rec_data['spf_result'] = policy_eval.findtext('spf', 'unknown')

            # Identifiers
            identifiers = record.find('identifiers')
            if identifiers is not None:
                rec_data['envelope_to'] = identifiers.findtext('envelope_to', 'N/A')
                rec_data['envelope_from'] = identifiers.findtext('envelope_from', 'Unknown')
                rec_data['header_from'] = identifiers.findtext('header_from', 'Unknown')

            # Auth results
            auth_results = record.find('auth_results')
            if auth_results is not None:
                # DKIM
                dkim = auth_results.find('dkim')
                if dkim is not None:
                    rec_data['dkim_domain'] = dkim.findtext('domain', 'Unknown')
                    rec_data['dkim_selector'] = dkim.findtext('selector', 'Unknown')
                    rec_data['dkim_auth_result'] = dkim.findtext('result', 'unknown')

                # SPF
                spf = auth_results.find('spf')
                if spf is not None:
                    rec_data['spf_domain'] = spf.findtext('domain', 'Unknown')
                    rec_data['spf_scope'] = spf.findtext('scope', 'Unknown')
                    rec_data['spf_auth_result'] = spf.findtext('result', 'unknown')

            records.append(rec_data)

        return {
            'metadata': metadata,
            'policy': policy,
            'records': records
        }

    def calculate_statistics(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate statistics from the report."""
        records = report_data['records']

        total_messages = sum(rec['count'] for rec in records)

        dkim_pass = sum(rec['count'] for rec in records if rec.get('dkim_result') == 'pass')
        spf_pass = sum(rec['count'] for rec in records if rec.get('spf_result') == 'pass')

        dkim_fail = sum(rec['count'] for rec in records if rec.get('dkim_result') == 'fail')
        spf_fail = sum(rec['count'] for rec in records if rec.get('spf_result') == 'fail')

        both_pass = sum(rec['count'] for rec in records
                       if rec.get('dkim_result') == 'pass' and rec.get('spf_result') == 'pass')

        unique_ips = len(set(rec['source_ip'] for rec in records))

        return {
            'total_messages': total_messages,
            'dkim_pass': dkim_pass,
            'dkim_fail': dkim_fail,
            'dkim_pass_rate': (dkim_pass / total_messages * 100) if total_messages > 0 else 0,
            'spf_pass': spf_pass,
            'spf_fail': spf_fail,
            'spf_pass_rate': (spf_pass / total_messages * 100) if total_messages > 0 else 0,
            'both_pass': both_pass,
            'both_pass_rate': (both_pass / total_messages * 100) if total_messages > 0 else 0,
            'unique_ips': unique_ips
        }

    def generate_markdown_report(self, report_data: Dict[str, Any], stats: Dict[str, Any],
                                filename: str) -> str:
        """Generate a Markdown report from the parsed data."""
        md = []

        # Header
        md.append(f"# DMARC Report Analysis: {filename}\n")
        md.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        md.append("---\n")

        # Metadata
        metadata = report_data['metadata']
        md.append("## Report Information\n")
        md.append(f"- **From:** {metadata.get('org_name', 'Unknown')} ({metadata.get('email', 'Unknown')})")
        md.append(f"- **Report ID:** {metadata.get('report_id', 'Unknown')}")
        md.append(f"- **Period:** {metadata.get('date_begin', 'Unknown')} to {metadata.get('date_end', 'Unknown')}")
        md.append("")

        # Policy
        policy = report_data['policy']
        md.append("## Your Published DMARC Policy\n")
        md.append(f"- **Domain:** {policy.get('domain', 'Unknown')}")
        md.append(f"- **Policy:** {policy.get('p', 'none')} (what to do with failed emails)")
        md.append(f"- **DKIM Alignment:** {policy.get('adkim', 'r')} ({'relaxed' if policy.get('adkim') == 'r' else 'strict'})")
        md.append(f"- **SPF Alignment:** {policy.get('aspf', 'r')} ({'relaxed' if policy.get('aspf') == 'r' else 'strict'})")
        md.append(f"- **Percentage:** {policy.get('pct', '100')}% of emails subject to policy")
        md.append("")

        # Summary Statistics
        md.append("## Summary Statistics\n")
        md.append(f"📊 **Total Messages Reported:** {stats['total_messages']}")
        md.append(f"🌐 **Unique Source IPs:** {stats['unique_ips']}")
        md.append("")

        # Authentication Results
        md.append("### Authentication Results\n")

        # DKIM
        dkim_status = "✅" if stats['dkim_pass_rate'] == 100 else "⚠️" if stats['dkim_pass_rate'] >= 90 else "❌"
        md.append(f"{dkim_status} **DKIM Authentication:**")
        md.append(f"  - Passed: {stats['dkim_pass']} ({stats['dkim_pass_rate']:.1f}%)")
        if stats['dkim_fail'] > 0:
            md.append(f"  - Failed: {stats['dkim_fail']} ({100 - stats['dkim_pass_rate']:.1f}%)")
        md.append("")

        # SPF
        spf_status = "✅" if stats['spf_pass_rate'] == 100 else "⚠️" if stats['spf_pass_rate'] >= 90 else "❌"
        md.append(f"{spf_status} **SPF Authentication:**")
        md.append(f"  - Passed: {stats['spf_pass']} ({stats['spf_pass_rate']:.1f}%)")
        if stats['spf_fail'] > 0:
            md.append(f"  - Failed: {stats['spf_fail']} ({100 - stats['spf_pass_rate']:.1f}%)")
        md.append("")

        # Both
        both_status = "✅" if stats['both_pass_rate'] == 100 else "⚠️" if stats['both_pass_rate'] >= 90 else "❌"
        md.append(f"{both_status} **Both DKIM & SPF Passed:** {stats['both_pass']} ({stats['both_pass_rate']:.1f}%)")
        md.append("")

        # Detailed Records
        md.append("## Detailed Records\n")

        for i, rec in enumerate(report_data['records'], 1):
            md.append(f"### Record {i}\n")
            md.append(f"- **Source IP:** {rec.get('source_ip', 'Unknown')}")
            md.append(f"- **Message Count:** {rec.get('count', 0)}")
            md.append(f"- **Envelope From:** {rec.get('envelope_from', 'Unknown')}")
            md.append(f"- **Header From:** {rec.get('header_from', 'Unknown')}")
            if rec.get('envelope_to', 'N/A') != 'N/A':
                md.append(f"- **Envelope To:** {rec.get('envelope_to', 'N/A')}")
            md.append("")

            # Policy evaluation
            dkim_eval = rec.get('dkim_result', 'unknown')
            spf_eval = rec.get('spf_result', 'unknown')
            dkim_icon = "✅" if dkim_eval == 'pass' else "❌"
            spf_icon = "✅" if spf_eval == 'pass' else "❌"

            md.append("**Policy Evaluation:**")
            md.append(f"- {dkim_icon} DKIM: `{dkim_eval.upper()}`")
            md.append(f"- {spf_icon} SPF: `{spf_eval.upper()}`")
            md.append(f"- Disposition: `{rec.get('disposition', 'none')}`")
            md.append("")

            # Authentication details
            md.append("**Authentication Details:**")
            if 'dkim_domain' in rec:
                md.append(f"- DKIM Domain: {rec.get('dkim_domain', 'N/A')}")
                md.append(f"- DKIM Selector: {rec.get('dkim_selector', 'N/A')}")
                md.append(f"- DKIM Result: `{rec.get('dkim_auth_result', 'unknown').upper()}`")
            if 'spf_domain' in rec:
                md.append(f"- SPF Domain: {rec.get('spf_domain', 'N/A')}")
                md.append(f"- SPF Result: `{rec.get('spf_auth_result', 'unknown').upper()}`")
            md.append("")

        return "\n".join(md)

    def get_ai_analysis(self, report_data: Dict[str, Any], stats: Dict[str, Any]) -> str:
        """Get AI-powered analysis and recommendations using Google Gemini."""
        if not self.use_ai:
            return None

        prompt = f"""
You are an email deliverability expert analyzing DMARC reports. Based on the following report data, provide:

1. A brief summary (2-3 sentences) of the email authentication status
2. Key findings (bullet points)
3. Specific recommendations to improve email deliverability and avoid spam/junk folders
4. Explanation of what the policy settings mean and whether they should be changed

Report Statistics:
- Total Messages: {stats['total_messages']}
- DKIM Pass Rate: {stats['dkim_pass_rate']:.1f}%
- SPF Pass Rate: {stats['spf_pass_rate']:.1f}%
- Both Pass Rate: {stats['both_pass_rate']:.1f}%
- Unique Source IPs: {stats['unique_ips']}

Current DMARC Policy:
{json.dumps(report_data['policy'], indent=2)}

Record Details:
{json.dumps(report_data['records'], indent=2)}

Provide actionable, beginner-friendly advice formatted in Markdown.
"""

        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"❌ AI analysis failed: {str(e)}"

    def process_report_file(self, filepath: str, output_dir: str = None) -> str:
        """Process a single DMARC report file and generate a markdown report."""
        filepath = Path(filepath)

        if output_dir is None:
            output_dir = filepath.parent / 'reports'
        else:
            output_dir = Path(output_dir)

        output_dir.mkdir(exist_ok=True)

        print(f"📧 Processing: {filepath.name}")

        # Extract and parse XML
        try:
            xml_content = self.extract_xml_from_file(filepath)
            report_data = self.parse_dmarc_report(xml_content)
            stats = self.calculate_statistics(report_data)
        except Exception as e:
            print(f"   ❌ Error parsing file: {e}")
            return None

        # Generate markdown report
        markdown = self.generate_markdown_report(report_data, stats, filepath.name)

        # Add AI analysis if enabled
        if self.use_ai:
            print("   🤖 Generating AI analysis...")
            ai_analysis = self.get_ai_analysis(report_data, stats)
            if ai_analysis:
                markdown += "\n---\n\n## AI Analysis & Recommendations\n\n"
                markdown += ai_analysis

        # Save report
        output_file = output_dir / f"{filepath.stem.replace('.xml', '')}_report.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(markdown)

        print(f"   ✅ Report saved: {output_file}")

        # Print summary
        if stats['both_pass_rate'] == 100:
            print(f"   ✅ All {stats['total_messages']} messages passed authentication!")
        else:
            print(f"   ⚠️  {stats['total_messages']} messages: {stats['both_pass_rate']:.1f}% passed both checks")

        print()
        return str(output_file)


def main():
    """Main entry point."""
    print("=" * 70)
    print("DMARC Report Analyzer")
    print("=" * 70)
    print()

    # Initialize analyzer
    use_ai = GEMINI_AVAILABLE
    analyzer = DMARCReportAnalyzer(use_ai=use_ai)

    # Find all report files in current directory
    current_dir = Path(__file__).parent
    report_files = []

    for pattern in ['*.xml.gz', '*.zip', '*.xml']:
        report_files.extend(current_dir.glob(pattern))

    # Filter to only DMARC report files (exclude our script)
    report_files = [f for f in report_files if 'dmarc_analyzer' not in f.name]

    if not report_files:
        print("❌ No DMARC report files found in the current directory.")
        print("   Looking for: *.xml.gz, *.zip, or *.xml files")
        return

    print(f"Found {len(report_files)} report file(s) to process:\n")

    # Process each report
    processed = 0
    for report_file in sorted(report_files):
        output_file = analyzer.process_report_file(report_file)
        if output_file:
            processed += 1

    print("=" * 70)
    print(f"✅ Processed {processed}/{len(report_files)} reports successfully")
    print(f"📁 Reports saved in: {current_dir / 'reports'}/")
    print("=" * 70)


if __name__ == '__main__':
    main()
