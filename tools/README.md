# DMARC Report Analyzer

A simple Python tool to analyze DMARC XML reports from email providers (Google, Outlook, etc.) and generate readable Markdown reports with AI-powered recommendations.

## What are DMARC Reports?

DMARC reports are sent by email providers (like Gmail, Outlook) to help you understand:
- Whether your emails are passing authentication checks (SPF and DKIM)
- Which IPs are sending emails on behalf of your domain
- Why your emails might be going to spam/junk folders

## Features

- **Parse DMARC reports** from `.xml.gz`, `.zip`, and `.xml` files
- **Generate readable Markdown reports** with:
  - Summary statistics (pass/fail rates)
  - Authentication results (SPF, DKIM)
  - Detailed record breakdown
  - Visual indicators (✅ pass, ❌ fail)
- **AI-powered analysis** using Google Gemini:
  - Explains what the results mean in simple terms
  - Provides specific recommendations to improve email deliverability
  - Suggests DMARC policy changes

## Installation

1. **Create a virtual environment and install dependencies:**
   ```bash
   cd tools
   python -m venv venv
   ./venv/bin/pip install -r requirements.txt
   ```

   Or on Windows:
   ```bash
   cd tools
   python -m venv venv
   venv\Scripts\pip install -r requirements.txt
   ```

2. **Set up Google Gemini API key (optional, but recommended):**
   - Get a free API key from: https://aistudio.google.com/app/apikey
   - Copy `.env.example` to `.env`:
     ```bash
     cp .env.example .env
     ```
   - Edit `.env` and add your API key:
     ```
     GEMINI_API_KEY=your_actual_api_key_here
     ```

## Usage

1. **Place your DMARC report files** in the `tools/` directory (they're usually named like `google.com!yourdomain.com!timestamp.zip`)

2. **Run the analyzer:**
   ```bash
   cd tools
   ./venv/bin/python dmarc_analyzer.py
   ```

   Or on Windows:
   ```bash
   cd tools
   venv\Scripts\python dmarc_analyzer.py
   ```

3. **View the reports:**
   - Reports are saved in `tools/reports/` folder
   - Each report file is named: `[original_filename]_report.md`
   - Open them with any text editor or Markdown viewer

## Understanding Your Reports

### Key Metrics

- **DKIM (DomainKeys Identified Mail):** Verifies that your email wasn't altered in transit
- **SPF (Sender Policy Framework):** Verifies that the sending server is authorized to send email for your domain
- **Pass Rate:** Percentage of emails that passed authentication
  - ✅ 100% = Perfect! All emails authenticated
  - ⚠️ 90-99% = Good, but some issues to investigate
  - ❌ <90% = Needs attention to avoid spam folders

### DMARC Policy Settings

Your current policy is: **p=none**
- `none` = Monitor only (no action taken on failed emails)
- `quarantine` = Failed emails go to spam/junk
- `reject` = Failed emails are rejected completely

**Recommendation for beginners:** Keep it at `none` until you have 100% pass rates, then consider moving to `quarantine`.

## Improving Email Deliverability

Based on your reports, here are common actions to take:

1. **If you see failures:**
   - Check your DNS records (SPF, DKIM, DMARC)
   - Ensure your email server is properly configured
   - Look at the AI recommendations in each report

2. **If you have 100% pass rates but still going to spam:**
   - Consider moving from `p=none` to `p=quarantine`
   - Ensure you have proper email authentication set up
   - Check your email content and sending practices

3. **Monitor your source IPs:**
   - Make sure all IPs in the reports are authorized to send on your behalf
   - Unknown IPs might indicate unauthorized use of your domain

## Troubleshooting

**No reports generated?**
- Make sure you have `.xml.gz`, `.zip`, or `.xml` files in the `tools/` directory
- Check that the files are valid DMARC reports

**AI analysis not working?**
- Make sure you installed the dependencies: `pip install -r requirements.txt`
- Check that your `.env` file has a valid `GEMINI_API_KEY`
- The tool will still work without AI, just won't have the recommendations section

**Need help understanding the results?**
- Read the AI analysis section in each report
- Look at the summary statistics first (pass rates)
- Focus on records that show ❌ failures

## Example Output

```
📧 Processing: google.com!minipass.me!1760400000!1760486399.zip
   🤖 Generating AI analysis...
   ✅ Report saved: tools/reports/google.com!minipass.me!1760400000!1760486399_report.md
   ✅ All 10 messages passed authentication!
```

## Files

- `dmarc_analyzer.py` - Main analysis script
- `requirements.txt` - Python dependencies
- `.env.example` - Example API key configuration
- `reports/` - Generated Markdown reports (created automatically)

## License

Free to use for personal and commercial projects.
