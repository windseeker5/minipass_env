# Minipass Product Reference

**Status:** Production - 2 Live Customers | **Owner:** Ken Dresdell
**Last Updated:** February 2026

---

## Executive Summary

**Minipass** is a SaaS platform that provides end-to-end activities management for organizations. It manages registrations, payments, digital pass distribution, activity tracking, financial reporting, and customer feedback collection. Deployed as one Docker container per customer on shared VPS infrastructure.

**Two markets served with one unified interface:**
- **Activity Managers** — Sports leagues, fitness classes, coaching, tournaments
- **Small Business Loyalty Programs** — Coffee shops, salons, service businesses

**Production customers:** LHGI (charity foundation/hockey league) and a hockey coach (personal training).

---

## Feature Inventory

### A. Digital Passport Management
- Create digital passports with QR codes
- Distribute via email automatically
- Track status: sent, opened, redeemed
- QR code scanning interface for redemption
- Custom payment instructions per passport type
- Passport templates with customizable designs

### B. Registration System
- Customizable registration forms (auto-generated per activity)
- **Dual signup workflow** (Feb 2026): payment-first OR approval-first mode
- Automated email confirmations on registration
- Capacity management with attendee limits
- Handles large volumes (5,000+ participants, duplicate name handling)

### C. Automatic Payment Matching (Killer Feature)
- Monitors designated email address for incoming e-transfers/Interac payments
- Automatically matches payment amount + sender email to pending registrations
- Auto-updates registration status to "PAID"
- Complete audit trail with timestamps
- Zero manual intervention required

### D. Payment Inbox & Management Dashboard
- Centralized inbox for all incoming e-transfer payment emails
- Status indicators: MATCHED, NO_MATCH, MANUAL_PROCESSED
- Smart deduplication (eliminates duplicate emails)
- Search/filter by sender name, amount, status
- Archive unmatched payments for clean inbox
- **Create passport from unmatched payment** (Jan 2026) — one-click workflow
- Pagination (50 items/page)

### E. Stripe Credit Card Payments (Feb 2026)
- Accept credit card payments directly through signup forms
- Customer configures Stripe API keys in Settings
- Integrated with dual signup workflow
- Guide available at minipass.me/guides

### F. Email Communication System (7 Templates)
- **7 customizable email templates:**
  1. `newPass` — Digital pass creation/purchase confirmation
  2. `paymentReceived` — Payment processing confirmation
  3. `latePayment` — Payment reminder for unpaid signups
  4. `signup` — Registration confirmation
  5. `redeemPass` — Pass redemption notification with remaining balance
  6. `survey_invitation` — Survey request with one-click participation
  7. 7th template added Feb 2026
- Per-activity customization (subject, title, intro, body, conclusion, CTA)
- HTML content with Bleach security sanitization
- **3-tier hero image system:** Custom upload > Template default > Activity image fallback
- Activity logo integration per activity
- LRU caching for hero image performance
- QR code toggle — option to disable QR codes in emails (Jan 2026)
- Custom payment email address — separate from org email (Jan 2026)
- Live preview, test email sending, reset to defaults
- Premailer CSS inlining for email client compatibility
- Mobile-responsive templates

### G. KPI Dashboard
- Activity overview cards: Revenue, Passports Created, Active Passports, Pending Sign-ups, Payment Status, Survey Scores
- Real-time updates as payments are matched
- Revenue summaries by date range
- **Activity cards are clickable** on dashboard (Feb 2026), "Manage" button removed

### H. Financial Management Suite
- **Custom fiscal year configuration** (Jan 2026) — configurable start month (1-12)
- **Dual accounting standards:**
  - Cash Basis: Cash Received, Cash Paid, Net Cash Flow
  - Accrual Basis: Accounts Receivable, Accounts Payable
- Income tracking: passport sales + custom income entries (sponsorship, donations, vendor fees, merchandise, services)
- Expense management with categories (COGS, Staff, Venue, Equipment, Insurance, Marketing, Travel, Supplies, Other)
- Receipt/document uploads (PDF, JPG, PNG) with modal viewing
- Payment status tracking (pending/received/cancelled for income; unpaid/paid/cancelled for expenses)
- Payment method recording (e-transfer, cash, cheque, credit_card, other)
- Due date management for unpaid bills
- **Activity-level financial breakdown** with expandable accordion view
- **Financial report integrated into activity page** (Feb 2026) — based on SQL accounting views, single source of truth
- CSV export compatible with QuickBooks, Xero, Sage, Wave, FreshBooks
- Period filtering: Month, Quarter, Year, Custom Range, All-Time
- Desktop: sliding drawer | Mobile: bottom modal

### I. User Contacts Export
- Full contact directory: name, email, phone, passport count, revenue, last activity date
- Email opt-out status badges (GDPR/CAN-SPAM compliance)
- Dynamic search (Ctrl+K shortcut), GitHub-style filters
- Gravatar integration for avatars
- CSV export for CRM/marketing tools
- Responsive: full table desktop, compact mobile

### J. Activity Location Management
- **Dual geocoding:** Google Maps API (primary) + Nominatim/OpenStreetMap (fallback)
- Address validation and auto-formatting
- Coordinate extraction (lat/lng) for map links
- Shareable Google Maps / Apple Maps links
- Canadian address optimization
- **Simplified location workflow** (Feb 2026)

### K. Survey System (Professional & Enterprise tiers)
- Pre-built templates (English + French)
- Custom template creation
- 3-click deployment: select template > customize > send invitations
- Target by passport type or all participants
- Response tracking with anonymous tokens
- Results dashboard with aggregated statistics
- CSV export of responses
- Survey lifecycle: create > send > close > reopen > export > delete

### L. AI Analytics Chatbot (Professional & Enterprise tiers)
- Natural language to SQL — ask questions in plain English
- **5 AI providers with automatic failover:**
  - Google Gemini (primary): 5 models, 500-1,500 RPD each
  - Groq (fallback): llama-3.3-70b, 14,400 RPD
  - Anthropic Claude (optional)
  - OpenAI (optional)
  - Ollama (local/self-hosted, optional)
- Combined ~15,900 free requests/day
- Budget management: daily/monthly spending caps with cost tracking
- Security: SQL keyword filtering, query length limits (2000 chars), result row limits (1000), 24h conversation timeouts
- Claude.ai-inspired UI with model selection, example questions, message history, chart rendering

### M. Admin & Settings
- Admin personalization: first/last name, custom avatar upload, Gravatar fallback
- **Password reset/change in Settings** (Feb 2026)
- Organization email configuration (SMTP, branding)
- Custom payment email address
- Stripe API key configuration
- Fiscal year start month
- QR code toggle for emails
- Feature flags for AI providers

### N. Data Ownership & Backup
- SQLite database export (one-click download)
- Backup & restore system (generate, download, upload, restore)
- Automated daily backups
- Full data portability, no vendor lock-in

### O. Signup Page
- **Redesigned signup page** (Feb 2026) — improved desktop/mobile experience
- Interac logo with better payment indications
- Default cover photos and org logos when none uploaded

---

## Technical Architecture

### Stack
| Layer | Technology |
|-------|-----------|
| Backend | Flask (Python), minimal dependencies |
| Frontend | Server-side rendered HTML, Jinja2 + Tabler.io CSS |
| Database | SQLite per customer (single-tenant, portable) |
| Auth | Session-based (no JWT) |
| File Storage | Local filesystem |
| Deployment | Docker container per customer, nginx reverse proxy |
| SSL | Let's Encrypt (automatic) |
| Email | SMTP with Premailer CSS inlining, Bleach sanitization, Base64 embedded images |

### Key Models (models.py)
| Model | Purpose |
|-------|---------|
| `Admin` | Admin users with auth |
| `User` | Participants/customers |
| `Activity` | Activities (hockey leagues, loyalty programs, etc.) |
| `PassportType` | Types of passes within an activity |
| `Passport` | Individual digital passes with QR codes |
| `Signup` | Registration records |
| `Redemption` | Pass usage/scan records |
| `EbankPayment` | Incoming e-transfer payment emails |
| `Income` / `Expense` | Financial transaction records |
| `Setting` | Organization settings (key-value) |
| `Survey` / `SurveyTemplate` / `SurveyResponse` | Survey system |
| `QueryLog` | AI chatbot query audit trail |
| `EmailLog` | Email sending history |
| `ReminderLog` | Payment reminder tracking |
| `AdminActionLog` | Admin action audit trail |

### Integrations
| Service | Purpose |
|---------|---------|
| Stripe | Credit card payments, customer provisioning |
| SMTP (org email) | Automated participant communication |
| Google Maps API | Primary geocoding for activity locations |
| Nominatim/OpenStreetMap | Fallback geocoding (free, no API key) |
| Google Gemini | Primary AI provider for chatbot |
| Groq | Fallback AI provider for chatbot |
| Anthropic / OpenAI / Ollama | Optional AI providers |
| Bleach | HTML sanitization |
| Premailer | CSS inlining for emails |
| Bcrypt | Password hashing |
| Flask-WTF | CSRF protection |

### Deployment Model
- One Docker container per customer organization
- Automated Stripe webhook provisioning: payment > container deploy > subdomain > SSL > welcome email
- Subdomains: `{customer}.minipass.me`
- Nginx reverse proxy with automatic SSL
- Container constraints: <512MB RAM, <1GB disk, <10s cold start

### Performance Targets
- Page response: <500ms (server-side rendered)
- Database queries: <100ms average
- Container memory: <400MB normal, <512MB peak
- Concurrent users: 20 per container

---

## Pricing Tiers

| Feature | Starter ($10/mo) | Professional ($35/mo) | Enterprise ($50/mo) |
|---------|:-:|:-:|:-:|
| Active activities | 1 | 10 | 100 |
| Passports per activity | Unlimited | Unlimited | Unlimited |
| Payment matching | Yes | Yes | Yes |
| 7 email templates | Yes | Yes | Yes |
| Financial management | Yes | Yes | Yes |
| User contacts export | Yes | Yes | Yes |
| Location services | Yes | Yes | Yes |
| Data ownership/backup | Yes | Yes | Yes |
| Stripe payments | Yes | Yes | Yes |
| Survey system | - | Yes | Yes |
| AI analytics chatbot | - | Yes | Yes |

---

## Production Customers

### LHGI (Ligue hockey Gagnon Image)
- Charity foundation + hockey league
- Multi-activity management, significant user base
- Uses: email customization, financial reporting, payment inbox, user contacts, location services

### Hockey Coach
- Individual sports coaching & training
- Multiple programs (skill levels, age groups)
- Uses: digital passes, payment matching, financial reporting, email templates, dual accounting
