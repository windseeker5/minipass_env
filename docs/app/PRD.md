# Minipass Product Requirements Document (PRD)
**Version:** 1.4
**Date:** August 28, 2025 | **Updated:** January 31, 2026
**Product Owner:** Ken Dresdell
**Target Launch:** November 15, 2025 | **Status:** Production - 2 Live Customers

---

## 1. Executive Summary

**Minipass** is a SaaS PWA (Progressive Web App) that provides end-to-end activities management for organizations. It streamlines registrations, payments, digital pass distribution, and activity tracking while offering comprehensive financial reporting and customer feedback collection.

### Vision Statement
To simplify organizational operations and optimize revenue through an automated, secure, and user-friendly digital platform that manages the complete activity lifecycle.

### Success Metrics
- **Launch Goal:** 2 production customers live ✅ **ACHIEVED** (LHGI charity foundation + hockey coach)
- **Official Launch:** November 15, 2025 (automated Stripe provisioning active)
- **User Adoption:** 80% digital pass redemption rate
- **Financial Impact:** Customers report significant time savings and revenue improvements
- **User Satisfaction:** Production customers praise ease of use, email customization, and financial reporting
- **Production Validation:** ✅ Successfully managing real-world operations with automated provisioning ready

---

## 2. Product Overview

### 2.1 Problem Statement
**Primary Market - Activity Managers:** Small business owners and activity managers who organize recurring activities (sports leagues, fitness classes, workshops, tournaments) currently struggle with fragmented manual processes. They use Excel spreadsheets for registrations, handle bank transfers manually, track payments in multiple systems, and manage attendance through paper lists or basic apps.

**Secondary Market - Small Business Loyalty Programs:** Small service businesses (coffee shops, salons, local services) rely on outdated paper punch cards for customer loyalty programs. These businesses miss opportunities for upfront revenue, struggle to track loyalty redemptions, and provide poor customer experience with easily-lost paper cards.

### 2.2 Solution
Minipass provides a unified digital platform serving both markets:

**For Activity Managers:**
- Create activities (e.g., "Monday Night Hockey", "September Golf Tournament")
- Define passport types within each activity (e.g., "Substitute Pass", "Season Pass")
- Generate automatic web-based registration forms
- Process payments and automatically issue digital passports
- Track attendance through QR code scanning or manual redemption

**For Small Business Loyalty Programs:**
- Create loyalty activities (e.g., "Coffee Shop Loyalty Program")
- Define passport types for bulk purchases (e.g., "10 Coffees for $50", "5 Haircuts for $200")
- Generate upfront revenue through pre-paid service packages
- Track redemptions digitally, eliminating paper punch cards
- Build customer retention through convenient mobile access

### 2.3 Value Proposition
**For Activity Managers:**
- Eliminate Excel chaos and manual payment reconciliation
- Automatic email payment matching saves hours of administrative work
- Professional automated participant communication builds trust and reduces support requests
- Clear financial visibility with real-time KPI dashboards
- Never manually send payment confirmations or activity updates

**For Small Businesses (Loyalty):**
- Generate upfront cash flow through pre-paid packages
- Eliminate paper cards and manual tracking
- Automatic payment processing for email transfers
- Professional customer communication improves brand perception
- Reduce customer service inquiries with clear transaction history

**For All Participants/Customers:**
- Easy online purchase with immediate confirmation
- Beautiful, professional email communications with complete transaction history
- Mobile access to digital passports with QR codes
- Always know exactly what you've purchased, paid for, and used
- Never lose track of your sessions or credits

---

## 3. Critical Project Constraints

### 3.1 **Infrastructure & Budget Constraints** 💰
- **Deployment Model:** One Docker container per customer on shared VPS infrastructure
- **Starting Budget:** Minimal server specifications with pay-as-you-grow scaling
- **Resource Limits:** Each container must be lightweight and efficient
- **Cost Optimization:** Prioritize features that don't require expensive third-party services

### 3.2 **Technical Development Constraints** ⚙️
- **Python-First Policy:** All business logic, data processing, and server operations in Python
- **JavaScript Minimization:** Use JavaScript only for essential UI interactions, keep code minimal
- **Simplicity Mandate:** Choose simple solutions over complex ones every time
- **Framework Constraint:** Stick with Flask + Tabler.io, avoid adding heavy dependencies

### 3.3 **Performance Constraints** 🚀
- **Speed is Critical:** Every feature must be optimized for fast response times
- **Memory Efficiency:** Low RAM usage is mandatory for multi-tenant deployment
- **Startup Speed:** Containers must start quickly for good customer experience

---

## 4. Target Users

### Primary Users (Activity Managers)
- **Amateur Sports League Organizers** (Priority 1) - Hockey leagues, soccer clubs, tennis groups
- **Fitness & Recreation Activity Leaders** (Priority 1) - Ski lessons, kitesurf sessions, gymnastics classes
- **Individual Coaches & Instructors** (Priority 1) - Yoga teachers, dance instructors, running coaches
- **Tournament & Event Organizers** (Priority 2) - Golf tournaments, competitions, workshops
- **Community Group Coordinators** (Priority 3) - Local clubs, hobby groups, meetups

### Primary Users (Small Business Loyalty Programs)
- **Coffee Shops & Cafes** (Priority 1) - Independent coffee roasters, local cafes
- **Personal Services** (Priority 1) - Hair salons, barber shops, massage therapists
- **Local Food Services** (Priority 2) - Bakeries, lunch spots, food trucks
- **Specialty Retail** (Priority 2) - Bike shops with services, local bookstores with events
- **Professional Services** (Priority 3) - Car washes, dry cleaners, small repair shops

### Secondary Users (Customers/Participants)
- Sports league players and substitutes
- Lesson participants and students
- Loyalty program customers
- Tournament competitors
- Community group members

### User Personas
#### Persona 1: "Marc the Hockey League Organizer"
- Manages Monday night amateur hockey league
- Currently uses Excel + bank transfers + WhatsApp groups
- Needs to track who paid, who's playing, substitute management
- Wants professional system without complexity

#### Persona 2: "Sophie the Ski Instructor"
- Runs weekend ski lessons and private sessions
- Manages both season passes and drop-in lessons
- Struggles with payment tracking and attendance
- Values mobile-friendly solution for mountain use

#### Persona 3: "Carlos the Coffee Shop Owner"
- Runs independent coffee shop with paper punch cards
- Wants to generate upfront revenue and improve customer retention
- Struggles with lost punch cards and manual tracking
- Needs simple system that customers can use easily

### Activity Examples
**Activity Management:**
- "Monday Night Hockey", "Saturday Yoga Class", "Weekly Tennis League"
- "Winter Ski Lessons 2025", "Summer Golf Tournament"
- "Kitesurf Workshop Sept 15", "Gymnastics Competition"

**Loyalty Programs:**
- "Coffee Shop Rewards", "Salon Package Deals", "Bakery Loyalty Program"
- "Car Wash Packages", "Massage Therapy Bundles"

---

## 4. Core Features & Requirements

### 4.1 MVP Features (Launch Priority)

#### A. Digital Passport Management ⭐ CRITICAL
- **Create Passports:** Generate digital passports with QR codes
- **Distribute Passports:** Send via email/SMS automatically
- **Track Passports:** Real-time status monitoring (sent, opened, redeemed)
- **Redeem Passports:** QR code scanning interface
- **Passport Templates:** Customizable passport designs
- **Custom Payment Instructions:** Per passport type payment instruction customization

#### B. Registration System ⭐ CRITICAL
- **Registration Forms:** Customizable form builder
- **Automated Confirmations:** Email/SMS notifications
- **Capacity Management:** Limit attendees per activity
- **Waitlist Management:** Automatic notification system

#### C. **AUTOMATIC PAYMENT MATCHING** ⭐ KILLER FEATURE
- **Email Payment Monitoring:** Monitor designated email address for incoming e-transfers/interact payments
- **Automatic Matching:** Match payment amount + sender email to pending registrations
- **Auto-Status Update:** Automatically mark registrations as "PAID" without manual intervention
- **Payment Logging:** Complete audit trail of all matched payments with timestamps
- **Reconciliation Dashboard:** Show matched vs unmatched payments for easy oversight

#### D. **AUTOMATED PARTICIPANT COMMUNICATION** ⭐ CRITICAL
- **Professional Email Design:** Beautiful, branded email templates for all participant communications
- **Real-time Updates:** Automatic emails sent for every status change (payment received, passport issued, redemption, etc.)
- **Transaction History:** Complete transaction table in every email showing:
  - Purchase date and details
  - Payment confirmation date
  - Redemption history with dates
  - Remaining sessions/credits
- **QR Code Integration:** Every communication includes participant's current passport with QR code
- **Activity Details:** Clear information about the specific activity, dates, and requirements

#### D-1. **PROFESSIONAL EMAIL COMMUNICATION SYSTEM** ⭐ ENHANCED ✅ IMPLEMENTED (All Tiers)
- **6 Customizable Email Templates:** Complete email communication suite for every customer touchpoint
  - **newPass** - Digital pass creation/purchase confirmation with welcome message
  - **paymentReceived** - Payment processing confirmation with transaction details
  - **latePayment** - Payment reminder for unpaid signups with clear call-to-action
  - **signup** - Registration confirmation with activity details
  - **redeemPass** - Pass redemption notification with remaining balance
  - **survey_invitation** - Survey request emails with one-click participation
- **Per-Activity Customization:** Each activity can have unique branded email templates
  - Customize subject lines, titles, intro text, body content, conclusions
  - HTML-supported content with security sanitization (Bleach library)
  - Custom call-to-action text and URLs (for newPass and survey templates)
  - **QR Code Toggle:** ⭐ NEW (Jan 2026) - Option to disable QR codes in email templates
  - **Custom Payment Email:** ⭐ NEW (Jan 2026) - Separate email address for payment instructions
- **Advanced Visual Branding:** Professional brand customization capabilities
  - **3-Tier Hero Image System:**
    1. Custom uploaded hero images (highest priority)
    2. Original template defaults (pristine versions)
    3. Activity image fallback (smart customization detection)
  - **LRU Caching:** Performance-optimized hero image loading
  - **Activity Logo Integration:** Unique logo per activity for owner card
  - **Historical Preservation:** Logos and customizations preserved across updates
  - **Base64 Email Embedding:** Optimized inline image delivery
- **Advanced Technical Features:**
  - **Live Preview:** Real-time template preview with actual activity context
  - **Test Email Sending:** Send test emails before deployment
  - **Reset to Defaults:** One-click reset for individual templates with pristine restoration
  - **Premailer CSS Inlining:** Automatic CSS inlining for email client compatibility
  - **Mobile-Responsive:** All templates optimized for desktop and mobile
- **Available in ALL Tiers:** Email customization included from $10/month Starter plan
- **Integration:** Seamlessly integrates organization email, name, and payment inbox details

#### E. Payment Integration ⭐ CRITICAL
- **Payment Processing:** Credit card and digital wallet support (secondary to email payments)
- **Payment Tracking:** Transaction history and status
- **Refund Management:** Automated refund processing
- **Payment Reporting:** Revenue summaries by activity

#### E-1. **PAYMENT INBOX & MANAGEMENT DASHBOARD** ⭐ ENHANCED ✅ IMPLEMENTED (All Tiers)
- **Payment Inbox:** Centralized dashboard for all incoming e-transfer payment emails
  - Real-time tracking of matched and unmatched payments
  - Status indicators: MATCHED, NO_MATCH, MANUAL_PROCESSED
  - Payment deduplication system (eliminates duplicate emails)
- **Intelligent Matching:** View payment matching results
  - Sender name, email, amount, and payment date
  - Matched passport ID and match reasoning
  - Complete audit trail for all transactions
  - Email received date tracking
- **Search & Filter:**
  - Filter by status (No Match, Matched, All)
  - Search by sender name or amount
  - Pagination support (50 items per page)
- **Payment Actions:**
  - Archive unmatched payments for clean inbox
  - View full payment details and history
  - Manual processing workflow for edge cases
  - **Create Passport from Payment:** ⭐ NEW (Jan 2026) - Streamlined workflow to create passport directly from unmatched payment
- **User Interface:**
  - GitHub-style filter buttons for status
  - Responsive table design for desktop and mobile
  - Clear visual indicators for action items
- **Available in ALL Tiers:** Payment inbox management from $10/month Starter plan

#### F. **USER CONTACTS EXPORT** ⭐ ENHANCED ✅ IMPLEMENTED (All Tiers)
- **User Contact Directory:** Comprehensive user list with engagement metrics for marketing/CRM
  - Full contact information: Name, email, phone
  - Engagement data: Passport count, revenue generated, activities participated
  - Last activity date for recency tracking
  - **Email opt-out status** with clear badges (Yes/No) for GDPR/CAN-SPAM compliance
- **Search & Filter:**
  - **Dynamic Search:** Real-time search by name, email, or phone
  - **Keyboard Shortcut:** Ctrl+K for quick search access
  - **GitHub-Style Filters:** Active users vs All users toggle
  - **Search Preservation:** Filter state maintained across searches
- **CSV Export for Marketing/CRM:**
  - Export filtered user list with all metadata
  - Format: `user_contacts_{filter}_{date}.csv`
  - Compatible with major CRM tools and marketing platforms
  - Preserves search filters in export filename
- **User Interface:**
  - **Responsive Table Design:**
    - Desktop: Full detail columns (email, phone, activities)
    - Tablet: Simplified view with key metrics
    - Mobile: Compact inline view with name + revenue
  - **Gravatar Integration:** User avatars for visual identification
  - **Status Badges:** Color-coded opt-out indicators
- **Summary Metrics:** Total users, active users, total revenue overview
- **Available in ALL Tiers:** User contact export from $10/month Starter plan

#### F-1. **KPI DASHBOARD** ⭐ CRITICAL
- **Activity Overview Cards:** Clear KPI cards for each activity showing:
  - Total Revenue per activity
  - Passports Created count
  - Active Passports count
  - Pending Sign-ups (awaiting approval)
  - Payment Status (paid vs pending)
  - Survey Response Rate and Satisfaction Scores
- **Real-time Updates:** Dashboard updates automatically as payments are matched
- **Financial Summaries:** Revenue summaries by date range

#### G. **COMPREHENSIVE FINANCIAL MANAGEMENT SUITE** ⭐ MAJOR UPGRADE ✅ IMPLEMENTED (All Tiers)
- **Custom Fiscal Year Configuration:** ⭐ NEW (Jan 2026) - Configurable financial year start date
  - Set fiscal year start month (1-12) per organization
  - Aligns reporting periods with organizational accounting calendar
  - Affects all financial reports and period calculations
- **Dual Accounting Standards Support:** Professional-grade accounting
  - **Cash Basis Accounting** (Primary):
    - Cash Received: Actual deposits and payments received
    - Cash Paid: Actual expenses and bills paid
    - Net Cash Flow: Bank reconciliation and liquidity management
  - **Accrual Basis Accounting** (Secondary):
    - Accounts Receivable (AR): Unpaid invoices and pending income
    - Accounts Payable (AP): Unpaid bills and pending expenses
    - Revenue/expense recognition when earned/incurred
- **Complete Income & Expense Tracking:** Unified financial dashboard for all business transactions
  - **Passport Sales:** Automatic tracking from registration system
  - **Other Income:** Add custom income entries (sponsorship, donations, vendor fees, merchandise, services)
  - **Expense Management:** Full expense tracking with receipt uploads
  - **Payment Status Tracking:**
    - Income: pending, received, cancelled
    - Expenses: unpaid, paid, cancelled
  - **Payment Method Recording:** e-transfer, cash, cheque, credit_card, other
  - **Due Date Management:** Track unpaid bills and payment deadlines
- **Activity-Level Financial Breakdown:**
  - Expandable accordion view grouped by activity
  - Detailed transaction listing with dates, categories, amounts
  - Individual activity profit/loss calculations
  - Cash flow analysis per activity
- **Summary KPIs:** High-level financial performance metrics
  - **Cash Received:** Total actual deposits
  - **Cash Paid:** Total actual payments
  - **Net Cash Flow:** Bank reconciliation metric
  - **Accounts Receivable:** Unpaid invoices total
  - **Accounts Payable:** Unpaid bills total
  - **Mobile Carousel:** KPI cards with dot navigation on mobile
- **Receipt & Document Management:**
  - Upload receipts for income and expenses (PDF, JPG, PNG)
  - View/preview receipts directly in modal (images and PDFs)
  - Download option for all receipts
  - Receipt storage tied to transactions
- **Transaction Management:**
  - **Add/Edit Income:** Date, category, amount, notes, payment status, payment method, receipt upload
  - **Add/Edit Expenses:** Date, category, amount, description, payment status, due date, payment method, receipt upload
  - **Delete Transactions:** Confirmation modal for safety
  - **Category System:**
    - Income: Ticket Sales, Sponsorship, Donations, Vendor Fees, Service Income, Merchandise, Other
    - Expenses: COGS, Staff, Venue, Equipment Rental, Insurance, Marketing, Travel, Supplies, Other
- **CSV Export for Accounting:**
  - Universal CSV format compatible with QuickBooks, Xero, Sage, Wave, FreshBooks
  - Format: `financial_report_{period}.csv`
  - All transactions with activity breakdown
  - Includes payment status and method for cash flow analysis
- **Period Filtering:** Month, Quarter, Year, Custom Date Range, All-Time reporting
- **User Interface:**
  - **Desktop:** Sliding drawer from right side for transaction entry
  - **Mobile:** Bottom modal for touch-friendly data entry
  - **Responsive Design:** Full functionality across all devices
  - **Real-time Updates:** Cursor tracking with spinner during save
- **Available in ALL Tiers:** Complete financial management from $10/month Starter plan
- **Production Validated:** Successfully deployed for customers managing significant annual revenue

#### G-1. **ACTIVITY LOCATION MANAGEMENT** ⭐ NEW FEATURE ✅ IMPLEMENTED (All Tiers)
- **Geolocation Services:** Professional location management for activities
  - **Dual Geocoding Providers:**
    - Google Maps API (primary): High-accuracy geocoding with formatted addresses
    - Nominatim/OpenStreetMap (fallback): Free, no API key required
  - **Address Validation:** Automatic address correction and formatting
  - **Coordinate Extraction:** Latitude/longitude for mapping integration
  - **Location Data Storage:**
    - location_address_raw: What admin typed
    - location_address_formatted: Geocoded/corrected address
    - location_coordinates: "lat,lng" for shareable map links
  - **Shareable Map Links:** One-click Google Maps/Apple Maps integration
  - **Canadian Address Optimization:** Biased geocoding results for Canadian locations
- **Use Cases:**
  - Professional address display in activity details
  - Shareable location links for participants
  - Map integration for signup forms
  - Location-based activity discovery (future enhancement)
- **Available in ALL Tiers:** Location services included from $10/month Starter plan

#### H. **AUTOMATED SURVEY SYSTEM** ⭐ HIGH PRIORITY ✅ FULLY IMPLEMENTED (Professional & Enterprise Tiers)
- **Survey Template Library:** Reusable survey templates for repeatable feedback collection
  - **Pre-Built Templates:**
    - "Post-Activity Feedback" (English)
    - "Sondage d'Activité - Simple" (French)
  - **Custom Template Creation:** Build reusable question sets for any activity type
  - **Template Management:** Create, edit, delete, and organize templates
- **True 3-Click Survey Deployment:**
  1. Select survey template from library
  2. Customize name/description for specific activity
  3. Send invitations to participants
- **Survey Lifecycle Management:**
  - **Create Survey:** Deploy survey from template for specific activity
  - **Target Audience:** Select passport type or send to all participants
  - **Send Invitations:** Automated email invitations via email template system
  - **Close Survey:** End response collection when complete
  - **Reopen Survey:** Allow additional responses if needed
  - **Export Results:** CSV export for analysis
  - **Delete Survey:** Clean up completed surveys
- **Response Tracking & Analytics:**
  - Individual response tokens for anonymous tracking
  - Completion status (completed/pending)
  - Response timestamps (invited, started, completed)
  - IP address and user agent capture for authenticity
  - Results dashboard with aggregated statistics
- **Question Types:** Flexible JSON-based question format for various response types
- **CSV Export:** Export all survey responses with complete data
  - Format: `survey_{survey_name}_{date}.csv`
- **Participant Experience:**
  - Ultra-simple survey forms designed for quick completion
  - Mobile-responsive design for on-the-go responses
  - One-click participation from email invitation
- **Actionable Insights:** Help activity managers improve pricing, scheduling, location, and service quality
- **Available in Professional & Enterprise Tiers:** Advanced feedback collection for growing businesses

#### I. **AI ANALYTICS CHATBOT** ⭐ MAJOR UPGRADE ✅ PRODUCTION READY (Professional & Enterprise Tiers)
- **Natural Language Business Intelligence:** Ask questions about activity data in plain English
  - Conversational interface for non-technical users
  - No SQL knowledge required - just ask naturally
  - Instant insights from your business data
  - Conversational AI support (greetings, help, thanks)
- **Multi-Provider AI System with Advanced Failover:** Five AI providers with intelligent routing
  - **Google Gemini (Primary):**
    - gemini-2.5-flash: 500 RPD (Default model)
    - gemini-2.0-flash-exp: 1,500 RPD, 15 RPM, 1M TPM
    - gemini-2.0-flash: 1,500 RPD
    - gemini-1.5-flash: 1,500 RPD
    - gemini-1.5-flash-8b: 1,500 RPD (fastest)
  - **Groq (Automatic Fallback):**
    - llama-3.3-70b-versatile: 14,400 RPD, 30 RPM (29x more capacity!)
    - llama-3.1-8b-instant: Fast lightweight model
  - **Anthropic Claude:** Optional provider (feature flag enabled)
  - **OpenAI:** Optional provider (feature flag enabled)
  - **Ollama:** Local/self-hosted open-source option
  - **Combined Free Tier Capacity:** ~15,900 requests/day with automatic failover
  - **Provider Selection:** Users can choose preferred AI provider via dropdown
- **Advanced Budget & Cost Management:** ⭐ NEW FEATURE
  - **Daily Budget Limits:** Configurable daily spending caps (default $10)
  - **Monthly Budget Limits:** Configurable monthly spending caps (default $100)
  - **Cost Tracking:** Per-query cost calculations and monitoring
  - **Budget Enforcement:** Automatic shutoff when limits reached
  - **Environment Variable Configuration:** Flexible budget settings
- **Intelligent Query Processing:**
  - **Natural Language to SQL:** Automatic database query generation
  - **Intent Detection:** Recognizes query types (aggregation, list, comparison, visualization)
  - **Entity Extraction:** Identifies dates, activities, numbers, emails from questions
  - **Query Optimization:** Efficient SQL generation for fast responses
- **Security & Safety Features:** ⭐ NEW FEATURE
  - **SQL Keyword Filtering:**
    - Allowed: SELECT, FROM, WHERE, GROUP BY, ORDER BY, HAVING, LIMIT
    - Blocked: DELETE, DROP, INSERT, UPDATE, ALTER, CREATE, TRUNCATE
  - **Query Length Limits:** Maximum 2000 characters
  - **Result Row Limits:** Maximum 1000 rows per query
  - **Conversation Timeouts:** 24-hour conversation expiration
  - **Response Sanitization:** Secure output processing
- **Data Analysis Capabilities:**
  - User data queries (names, emails, registration dates)
  - Activity performance metrics (revenue, attendance, trends)
  - Financial analytics (revenue by month, expenses, profitability)
  - Signup and passport data (paid vs unpaid, active passes, redemptions)
  - Survey response analysis (feedback trends, satisfaction scores)
- **Business Intelligence Examples:**
  - "Give me the list of people who haven't paid for Monday RK activity"
  - "Show me the substitute users who came the most to Monday RK activity"
  - "What's my best performing activity this month?"
  - "Which customers have the most credits remaining?"
  - "Show me revenue by month"
  - "Who has the highest participation rate?"
- **User Interface:**
  - **Claude.ai-inspired design:** Light theme with professional aesthetics
  - **Large search box:** Prominent input for empty state
  - **Model selection:** Choose AI provider directly in search interface
  - **Example questions:** Interactive guidance for new users
  - **Message history:** Timestamped conversation with SQL transparency
  - **Chart rendering:** Data visualization for trends and comparisons
  - **Sparkle icon:** Blue-to-pink gradient branding
  - **Status LED:** Real-time API connectivity indicator
- **Transparency & Tracking:**
  - **SQL Display:** View generated queries for learning and verification
  - **Token Usage Monitoring:** Track API token consumption per query
  - **Cost Tracking:** Per-query cost calculations
  - **Response Time:** Performance metrics displayed
  - **Query Logging:** Complete audit trail with execution history
- **Data Privacy & Security:**
  - All queries processed securely
  - No data stored externally
  - Admin session validation
  - Question length limits (max 2000 chars)
  - SQL injection prevention
  - Response sanitization
- **Production Validated:** Successfully deployed with live customers for real business intelligence
- **Available in Professional & Enterprise Tiers:** Advanced analytics for data-driven decision making

#### J. **ADMIN PERSONALIZATION** ⭐ NEW FEATURE ✅ IMPLEMENTED (All Tiers)
- **Personal Information Management:**
  - First name and last name fields
  - Full name display throughout interface
  - Personalized welcome messages
  - Display name for greetings
- **Custom Avatar Upload:**
  - Upload custom profile pictures
  - Avatar storage and management
  - Fallback to Gravatar integration
  - Professional profile customization
- **User Experience Enhancement:**
  - Personalized dashboard greetings
  - Professional admin profile appearance
  - Improved multi-admin environments
- **Available in ALL Tiers:** Admin personalization from $10/month Starter plan

#### K. **COMPLETE DATA OWNERSHIP** ⭐ HIGH PRIORITY ✅ IMPLEMENTED (All Tiers)
- **SQLite Database Export:** Users can download their complete database at any time
- **No Vendor Lock-in:** Full data portability ensures users are never trapped
- **Backup & Restore System:** Generate, download, upload, and restore database backups
- **Automated Backups:** Daily backup generation for data protection
- **Data Transparency:** Users own their data completely, can migrate to any solution
- **One-Click Download:** Instant database download from Settings page

### 4.2 Phase 2 Features (Professional & Enterprise Tiers)

#### L. Advanced Survey System
- **Customer Surveys:** Post-activity feedback collection
- **Activity Evaluations:** Performance rating system
- **Survey Builder:** Custom question types and logic
- **Response Analytics:** Trend analysis and insights

#### M. Comprehensive Financial Management (Beyond Basic Reporting)
- **Advanced Forecasting:** Revenue prediction and trend analysis
- **Multi-Currency Support:** International activity management
- **Tax Preparation:** Advanced export for accounting software integration

#### N. Enhanced Analytics
- **Customer Journey Analytics:** Registration to redemption flow
- **Predictive Insights:** Demand forecasting
- **Comparative Analysis:** Activity performance comparison

---

## 5. User Stories

### Activity Manager Stories
```
As an activity manager, I want to:
- Create an activity (e.g., "Monday Night Hockey") with multiple passport types so that I can serve different participant needs
- Generate automatic registration forms so that participants can sign up and pay online
- See a clear dashboard with KPI cards for each activity showing: revenue, passports created, active passports, pending sign-ups, and survey feedback
- Have email payments automatically matched to registrations so I never have to manually check Excel sheets again
- ✅ Ask questions about my data in plain English (e.g., "Who hasn't paid for Monday hockey?") and get instant answers [IMPLEMENTED - AI Analytics with Gemini + Groq + Anthropic + OpenAI + Ollama]
- Send professional surveys to participants with just 3 clicks using pre-built templates so I can improve my activities
- Get feedback on pricing, scheduling, and location without the hassle of creating surveys from scratch
- ✅ Add activity locations with automatic geocoding so participants can find venues easily [IMPLEMENTED - Google Maps + OpenStreetMap]
- ✅ Track both cash flow and accrual accounting metrics so I can manage my business finances professionally [IMPLEMENTED - Dual Accounting Standards]
- ✅ Download my complete database at any time so I own my data and am never locked into the platform [IMPLEMENTED - Backup & Restore]
- ✅ Export my financial data to CSV so I can import it into QuickBooks/Xero for accounting [IMPLEMENTED - Financial Report Export]
- ✅ Export my user contact list for marketing campaigns and CRM tools [IMPLEMENTED - User Contacts Export]
- Track who has paid and who hasn't with automatic updates so that I can follow up only when needed
- Scan QR codes or manually redeem passports so that I can track attendance efficiently
- Use an interface so simple that I can teach it to anyone in minutes
- Access all features without switching between different modes or interfaces
```

### Small Business Owner Stories (Loyalty Programs)
```
As a small business owner, I want to:
- Create a loyalty program (e.g., "Coffee Shop Rewards") with package deals so that I can generate upfront revenue
- Let customers buy loyalty packages online so that I don't handle cash or track paper cards
- Have email payments for loyalty packages automatically processed so I don't manually reconcile transactions
- Send simple surveys to my loyalty customers to understand what they like and how to improve
- Use pre-built survey templates designed for small businesses so I don't waste time creating surveys
- Redeem customer purchases quickly at point of sale so that service remains fast
- See KPI dashboard showing package sales, redemptions, revenue, and customer satisfaction without complexity
- Use the same simple interface whether managing loyalty programs or activities
- Replace paper punch cards with a professional digital solution that customers love and provides me business insights
```

### Customer/Participant Stories
```
As a customer/participant, I want to:
- Register and pay online easily so that I don't have to deal with bank transfers, cash, or paper cards
- Send email payments (Interac e-Transfer) and have them automatically processed
- Receive beautiful, professional email confirmations immediately after every transaction
- See my complete transaction history in every email (purchase date, payment date, redemption dates)
- Access my digital passport with QR code on my phone so I don't need to print anything
- Always know exactly how many sessions/credits I have remaining
- Receive automatic updates when I attend activities so I can track my participation
- Feel confident that I'm dealing with a professional, trustworthy system
- Use the same simple system whether buying hockey league access or coffee shop loyalty packages
- Find activity locations easily with map links
```

---

## 6. Technical Requirements & Constraints

### 6.1 **CRITICAL PERFORMANCE CONSTRAINTS** ⚠️
**Infrastructure Reality:** Multi-tenant Docker deployment on low-spec VPS servers
- **RAM Constraint:** Each customer container must operate in < 512MB RAM
- **CPU Constraint:** Minimal CPU usage, optimized for shared resources
- **Storage Constraint:** Container size < 1GB per customer
- **Scaling Model:** One Docker container per customer organization
- **Budget Reality:** Start with minimal server specs, scale up as revenue grows

### 6.2 **MANDATORY TECHNICAL PRINCIPLES** 🎯
**Python-First Architecture:**
- **Primary Rule:** Use Python for ALL business logic, data processing, and server-side operations
- **JavaScript Minimization:** Use JavaScript ONLY when absolutely required for UI interactions
- **Complexity Constraint:** Any JavaScript code must be < 10 lines when possible, maximum 50 lines per function
- **Framework Choice:** Leverage Flask's simplicity - avoid heavy frameworks or libraries
- **Database Operations:** All queries and data processing in Python, never in JavaScript

**Extreme UI/UX Simplicity:**
- **Kid-Friendly Interface:** UI must be so intuitive that children can operate it
- **Single Unified Interface:** One UI serves both activity management and loyalty programs
- **No Mode Switching:** No separate interfaces for different use cases
- **Visual Clarity:** Large, clear buttons and text, obvious visual hierarchy
- **Minimal Clicks:** Maximum 3 clicks to complete any core action

**Automatic Payment Processing:**
- **Email Monitoring:** Real-time monitoring of designated email addresses for incoming payments
- **Pattern Recognition:** Automatic matching of payment amounts and sender emails to registrations
- **Zero Manual Intervention:** Payment matching happens automatically in background
- **Audit Trail:** Complete logging of all automatic payment matches

### 6.3 Architecture
- **Backend:** Flask (Python) with minimal dependencies
- **Frontend:** Server-side rendered HTML with Tabler.io CSS + minimal JavaScript
- **Database:** SQLite per customer container (single-tenant, portable, fast)
- **Authentication:** Simple session-based auth (avoid JWT overhead)
- **File Storage:** Local filesystem storage (avoid S3 costs/complexity in MVP)
- **AI Integration:** External LLM API for natural language data queries (Professional/Enterprise tiers)
- **Data Portability:** SQLite database export functionality for complete data ownership
- **Multi-tenant Model:** Organization-based architecture with per-tenant configuration
  - Organization model for customer isolation
  - Per-organization email configuration (SMTP, branding)
  - Automatic failover for organization email
  - One Docker container per customer organization

### 6.3.1 **Automated Customer Provisioning** ✅ IMPLEMENTED
- **Stripe Webhook Integration:** Automatic container deployment on subscription payment
  - Listen for Stripe `checkout.session.completed` and `customer.subscription.created` events
  - Validate webhook signatures for security
  - Extract customer information (email, organization name, plan tier)
- **Container Orchestration:**
  - Automatic Docker container creation for new customers
  - Subdomain assignment (e.g., `customer.minipass.me`)
  - Initial database setup with migrations
  - Organization configuration (email settings, branding defaults)
- **Onboarding Flow:**
  1. Customer selects plan on marketing website
  2. Completes Stripe checkout (organization name, subdomain, email)
  3. Payment processed and webhook triggered
  4. System automatically provisions Docker container
  5. Database initialized with admin account
  6. Welcome email sent with:
     - Subdomain URL (e.g., `https://lhgi.minipass.me`)
     - Initial login credentials
     - Getting started video link (2-3 minutes)
     - Direct link to first activity setup
- **Infrastructure Automation:**
  - Nginx reverse proxy configuration update
  - SSL certificate provisioning via Let's Encrypt
  - Container health monitoring setup
  - Automatic backup schedule initialization
- **Validation & Error Handling:**
  - Subdomain availability check
  - Email format validation
  - Duplicate customer detection
  - Rollback mechanism for failed provisioning
  - Admin notification for manual intervention when needed
- **Zero Manual Intervention:** Complete hands-off customer onboarding from payment to ready-to-use system

### 6.4 Performance Requirements
- **Container Startup:** < 10 seconds cold start
- **Memory Usage:** < 400MB RAM per customer container under normal load
- **Response Time:** < 500ms for all pages (server-side rendered)
- **Database Queries:** < 100ms average query time
- **Concurrent Users:** 20 simultaneous users per container maximum

### 6.5 Integrations
- **Payment Gateway:** Stripe (primary), PayPal (secondary)
- **Email Service:** SendGrid or AWS SES
- **SMS Service:** Twilio
- **QR Code Generation:** Python QR library
- **AI/LLM Services:** ✅ **MAJOR UPGRADE - 5 PROVIDERS**
  - **Google Gemini API (Primary):**
    - Models: gemini-2.5-flash (500 RPD), gemini-2.0-flash-exp (1,500 RPD), gemini-2.0-flash (1,500 RPD), gemini-1.5-flash (1,500 RPD), gemini-1.5-flash-8b (1,500 RPD)
    - Natural language to SQL generation
    - Conversational AI responses
    - Feature flag: CHATBOT_ENABLE_GEMINI
  - **Groq API (Automatic Fallback):**
    - Models: llama-3.3-70b-versatile (14,400 RPD, 30 RPM), llama-3.1-8b-instant
    - 29x more capacity than Gemini 2.5
    - Seamless failover for reliability
    - Feature flag: CHATBOT_ENABLE_GROQ
  - **Anthropic Claude (Optional):**
    - Premium AI capabilities
    - Feature flag: CHATBOT_ENABLE_ANTHROPIC
  - **OpenAI (Optional):**
    - GPT model support
    - Feature flag: CHATBOT_ENABLE_OPENAI
  - **Ollama (Optional):**
    - Local/self-hosted open-source models
    - Feature flag: CHATBOT_ENABLE_OLLAMA
  - **Provider Manager:** Automatic failover chain with health monitoring
  - **Budget Tracking:** Daily/monthly cost limits with usage monitoring
  - **Security Controls:** SQL keyword filtering, query length limits, result row limits
- **Geolocation Services:** ✅ **NEW INTEGRATION**
  - **Google Maps Geocoding API (Primary):**
    - High-accuracy address validation
    - Professional address formatting
    - Canadian location optimization
    - Coordinate extraction for mapping
  - **Nominatim/OpenStreetMap (Fallback):**
    - Free geocoding service (no API key required)
    - Rate limited to 1 request/second
    - Address component extraction
    - Backup for Google Maps
  - **Feature:** Activity location management with automatic geocoding
- **Analytics:** Google Analytics integration
- **Security Libraries:**
  - Bleach: HTML sanitization for user-generated content
  - Premailer: CSS inlining for email templates
  - Bcrypt: Password hashing
  - Flask-WTF: CSRF protection

### 6.6 Performance Requirements
- **Page Load Time:** < 3 seconds
- **Mobile Responsiveness:** 100% mobile-friendly
- **Uptime:** 99.5% availability
- **Concurrent Users:** Support 100 simultaneous users per organization

### 6.7 Security Requirements
- **Data Encryption:** All data encrypted in transit and at rest
- **Payment Compliance:** PCI DSS compliance through payment processor
- **Authentication:** Multi-factor authentication for admin users
- **Data Privacy:** GDPR/CCPA compliance features
  - Email opt-out functionality
  - Complete data export capabilities
  - User data deletion support
- **SQL Injection Prevention:** Parameterized queries and keyword filtering
- **XSS Protection:** HTML sanitization with Bleach library

---

## 7. Success Metrics & KPIs

### Business Metrics
- **Customer Acquisition:** 10 organizations in first month
- **Monthly Recurring Revenue (MRR):** $500 by month 1, $2,000 by month 3
- **Customer Retention:** 90% month-over-month retention
- **Average Revenue Per User (ARPU):** $25/month average (mix of plans)
- **Plan Distribution Target:** 60% Starter, 30% Professional, 10% Enterprise

### Product Metrics
- **Automatic Payment Matching:** 95% of email payments automatically matched without manual intervention
- **Participant Communication:** 100% of status changes trigger automatic professional emails
- **AI Chatbot Usage:** ✅ **IMPLEMENTED** - 60% of Professional+ users ask at least 5 questions per month about their data
- **AI Query Accuracy:** ✅ **IMPLEMENTED** - 90% of natural language queries return accurate, useful results
- **AI System Reliability:** ✅ **IMPLEMENTED** - 99.9% uptime with multi-provider fallback (Gemini → Groq → Anthropic → OpenAI → Ollama)
- **AI Rate Limit Handling:** ✅ **IMPLEMENTED** - Zero downtime from rate limits due to automatic failover
- **Data Export Usage:** ✅ **IMPLEMENTED** - 30% of users export their database within first 6 months (demonstrates data ownership trust)
- **Financial Export Adoption:** ✅ **NEW METRIC** - Target 50% of Professional+ customers export financial data monthly for accounting
- **User Contacts Export Usage:** ✅ **NEW METRIC** - Target 40% of customers export user contacts for marketing/CRM
- **Location Services Usage:** ✅ **NEW METRIC** - Target 70% of activities have geocoded locations within 3 months
- **Survey Response Rate:** 60% response rate on surveys (industry average is 10-15% for small businesses)
- **Survey Deployment:** 80% of Professional+ customers send at least one survey per activity
- **User Interface Usability:** 90% of new users complete first activity setup without support
- **Activity Utilization:** 80% of purchased activity slots actively used
- **Passport Redemption Rate:** 80% of issued passports are redeemed
- **Payment Processing:** 95% successful payment rate (including email transfers)
- **User Satisfaction:** 4.5+ rating on feedback surveys
- **Support Request Reduction:** 70% fewer participant inquiries due to clear automated communication
- **Feature Adoption:** ✅ **EXCEEDED** - 90%+ of Professional+ customers use advanced reporting features (AI Analytics, Financial Export, User Export)
- **Business Improvement:** Customers report average 15% improvement in activity satisfaction after using survey insights
- **Time Savings:** Average 5+ hours saved per week on payment reconciliation, participant communication, and feedback collection
- **Production Scale:** ✅ **VALIDATED** - Successfully managing customers with $300K+ annual revenue

### Production Customer Validation
**Status:** 2 live production customers successfully deployed and operating

#### Customer 1: LHGI (Ligue hockey Gagnon Image)
- **Industry:** Charity Foundation & Hockey League Organization
- **Use Case:** Multi-activity management (hockey games, charity events, fundraising activities)
- **Key Metrics:**
  - Managing multiple activities with diverse participant groups
  - Significant user/participant base across various programs
  - Revenue management for charity fundraising operations
- **Feature Adoption:**
  - Email customization for professional branded communications
  - Financial reporting for charity transparency and accounting
  - Payment inbox for streamlined donation and registration processing
  - User contact management for donor and participant outreach
  - Location services for event venue sharing
- **Customer Feedback:**
  - Reports significant time savings on administrative tasks
  - Improved revenue tracking and financial transparency
  - Praised ease of use and intuitive interface
  - Values professional email templates for charity communications

#### Customer 2: Hockey Coach (Personal Training & Coaching)
- **Industry:** Individual Sports Coaching & Training
- **Use Case:** Private coaching sessions and group training programs
- **Key Metrics:**
  - Managing training programs with individual students
  - Revenue management for coaching services
  - Multiple training activities (different skill levels, age groups)
- **Feature Adoption:**
  - Digital pass management for session tracking
  - Payment matching for automated client billing
  - Financial reporting for business management
  - Email templates for professional client communication
  - Dual accounting for cash flow and accrual tracking
- **Customer Feedback:**
  - Reports improved revenue tracking and client management
  - Time savings on payment reconciliation and client communication
  - Ease of use allows focus on coaching rather than administration
  - Values mobile-friendly interface for on-the-go management

#### Key Learnings from Production Deployment
- **Email Customization:** Both customers heavily customize email templates for brand consistency
- **Financial Reporting:** Critical feature for both non-profit and small business use cases
- **Dual Accounting:** Appreciated by business-savvy users for comprehensive financial tracking
- **Time Savings:** Customers report significant reduction in administrative overhead
- **Ease of Use:** Non-technical users successfully manage all features without training
- **Mobile Usage:** Both customers frequently access platform from mobile devices
- **Payment Automation:** E-transfer matching eliminates manual reconciliation work
- **Location Services:** Venue sharing via map links appreciated for event communication

### Technical Metrics
- **Container Memory Usage:** < 400MB RAM average, < 512MB peak
- **Container Startup Time:** < 10 seconds cold start
- **Page Load Speed:** < 500ms server response time
- **Database Query Performance:** < 100ms average
- **Container Size:** < 1GB per customer deployment
- **CPU Usage:** < 20% on shared VPS environment

---

## 8. Launch Timeline

### Development Phase (Completed ✅)
- [x] Core registration system
- [x] Digital pass creation and management
- [x] Payment integration (Stripe)
- [x] Email notification system (6 customizable templates with 3-tier hero system)
- [x] QR code generation and redemption
- [x] Financial reporting suite with dual accounting standards
- [x] User contact export for CRM/marketing with email opt-out
- [x] Payment inbox and management dashboard
- [x] AI analytics chatbot (5-provider system with budget management)
- [x] Survey template system with 3-click deployment
- [x] Complete data ownership (backup & restore)
- [x] Activity location management (Google Maps + OpenStreetMap)
- [x] Admin personalization (names, avatars)

### Testing & Refinement Phase (Completed ✅)
- [x] Production deployment with 2 live customers
- [x] LHGI (charity foundation) - successfully operating
- [x] Hockey coach - successfully managing training programs
- [x] Bug fixes and performance optimization based on real usage
- [x] Mobile responsiveness validated across devices
- [x] Security validation in production environment

### Production Launch Preparation (In Progress)
- [x] Multi-tenant Docker deployment infrastructure
- [x] Automated customer provisioning via Stripe webhooks
- [x] Customer onboarding workflow and documentation
- [ ] Marketing website final updates
- [ ] Launch day monitoring and support preparation
- [ ] Customer acquisition campaigns ready

### **Official Launch: November 15, 2025** 🚀
- **Status:** Production-Ready with 2 Live Customers
- **Automated Provisioning:** Stripe integration active for instant customer onboarding
- **Infrastructure:** Scalable VPS with container orchestration ready
- **Support:** Documentation, video tutorials, and support channels prepared
- **Go-to-Market:** Marketing materials and acquisition strategy finalized

### Post-Launch Strategy
- **Week 1-2:** Monitor system performance and customer onboarding flow
- **Month 1:** Target 10 new customers through marketing campaigns
- **Month 2-3:** Gather feedback, iterate on features, optimize conversion
- **Ongoing:** Scale infrastructure based on customer growth (every 10 new customers)

---

## 9. Pricing Strategy

### Activity-Based Tiered Model

**Starter:** $10/month
- **Activity Limit:** 1 active activity
- **Passports:** Unlimited passports per activity
- **Core Features:** (All Included ✅)
  - Digital pass management with QR codes
  - Automatic payment matching (e-transfer)
  - Payment inbox & management dashboard
  - **6 Customizable Email Templates** (newPass, paymentReceived, latePayment, signup, redeemPass, survey_invitation)
  - **Email customization** per activity (hero images, logos, branding, 3-tier priority system)
  - **Dual accounting standards** (cash basis + accrual basis with AR/AP)
  - **Complete financial management suite** (income, expenses, receipts, CSV export)
  - **User contact export** for CRM/marketing with email opt-out tracking
  - **Activity location management** (Google Maps + OpenStreetMap geocoding)
  - **Admin personalization** (names, custom avatars)
  - Automated participant communication
  - KPI dashboard with activity metrics
  - Complete data ownership (backup & restore)
  - Registration forms and capacity management
- **Support:** Email support
- **Best For:** Individual coaches, single-activity organizers, small loyalty programs

**Professional:** $35/month
- **Activity Limit:** Up to 10 active activities
- **Passports:** Unlimited passports per activity
- **All Starter Features Plus:**
  - **Automated survey system** (template library, 3-click deployment, CSV export)
  - **AI Analytics Chatbot** (Gemini + Groq + Anthropic + OpenAI + Ollama)
    - 5 AI provider options with automatic failover
    - Budget management and cost tracking
    - Conversational AI support
    - Security controls and query logging
  - Enhanced reporting & analytics
  - Priority support
  - Custom branding options
- **Support:** Priority email + chat support
- **Best For:** Multi-activity managers, growing sports leagues, expanding coaching businesses

**Enterprise:** $50/month
- **Activity Limit:** Up to 100 active activities
- **Passports:** Unlimited passports per activity
- **All Professional Features Plus:**
  - Full feature access with no limitations
  - **AI Analytics Chatbot** with higher usage limits
  - Advanced financial forecasting (planned)
  - Multi-currency support (planned)
  - Dedicated account manager
  - API access (planned)
  - White-label options (planned)
- **Support:** Dedicated support with priority response
- **Best For:** Large organizations, multi-location businesses, enterprise deployments

### Pricing Philosophy
- **Activity-Focused:** Customers pay based on the number of activities they manage, not passport volume
- **Unlimited Passports:** No restrictions on passport generation per activity
- **Predictable Costs:** Organizations know exactly what they'll pay based on their activity portfolio
- **Growth-Friendly:** Easy to upgrade as business scales

### Business Rules & Limits
**Activity Definition:** An activity is a managed event or service (e.g., "Monday Night Hockey", "September Golf Tournament") that can have multiple passport types within it (e.g., "Season Pass", "Substitute Pass").

**Activity Limit Enforcement:**
- Customers cannot create more activities than their plan allows
- Attempting to exceed limit triggers upgrade prompt
- No automatic upgrades - customer must explicitly choose new plan

**Activity Lifecycle Management:**
- Activities can be ongoing (weekly hockey) or seasonal (winter ski lessons)
- Seasonal activities count toward limit when active
- Different passport types within same activity (regular members vs substitutes) don't count as separate activities

**No Free Trial:** Customers must pay to access the system - no trial period offered

---

## 10. Competitive Advantages

### 10.1 **Automatic Payment Matching - Unique Differentiator**
**The Problem Solved:** Currently, activity managers receive email transfers, then manually check Excel sheets to match payments to registrations - a time-consuming, error-prone process.

**Minipass Solution:** Monitors designated email addresses and automatically matches incoming payments to the correct person and activity without any manual intervention.

**Competitive Advantage:** No other platform offers this level of automated payment reconciliation for email transfers/Interac e-Transfer, which is the dominant payment method for small Canadian activities.

### 10.2 **Extreme Simplicity**
- **Kid-Friendly Interface:** While competitors build complex enterprise solutions, Minipass focuses on intuitive design
- **Single Unified Platform:** Serves both activity management and loyalty programs without mode switching
- **Lightweight Architecture:** Fast, efficient containers vs. heavy enterprise platforms

### 10.3 **Professional Communication Suite - Enterprise Quality at SMB Pricing** ✅ ENHANCED
- **6 Customizable Email Templates:** Complete lifecycle communication (newPass, paymentReceived, latePayment, signup, redeemPass, survey_invitation)
  - Available in $10/month Starter plan (competitors charge $99+/month for email customization)
  - Per-activity customization with hero images and logos
  - **3-Tier Hero Image System:** Custom uploads → Template defaults → Activity images
  - **LRU Caching:** Performance-optimized image loading
  - Live preview and test email functionality
- **Automated Communication:** Beautiful, professional emails sent automatically for every transaction and status change
- **Complete Transaction History:** Every email includes full transaction table showing purchase, payment, and redemption history
- **Visual Branding:** Hero image upload, activity logos, custom CTAs - typically only in enterprise plans
- **Advanced Email Rendering:** Premailer CSS inlining, Bleach HTML sanitization, MIME multipart with embedded images
- **QR Code Integration:** Participants always have access to their current passport with QR code
- **Trust Building:** Professional communication reduces support requests and builds customer confidence
- **Transparency:** Participants always know exactly what they've purchased, paid for, and used
- **Competitive Edge:** Most competitors offer generic templates or charge extra for customization; Minipass includes full customization at all tiers

### 10.4 **Dual Accounting Standards - Professional-Grade Finance** ⭐ NEW ADVANTAGE
- **Cash Basis + Accrual Basis:** Available in $10/month Starter plan (competitors charge $99+/month for accrual accounting)
  - Cash flow tracking (Cash Received, Cash Paid, Net Cash Flow)
  - Accrual accounting (Accounts Receivable, Accounts Payable)
  - Bank reconciliation support
  - Unpaid invoice and bill tracking
- **Professional Financial Management:** Features typically only in QuickBooks/Xero ($30-50/month)
- **Payment Status Tracking:** Track payment methods, due dates, and payment history
- **Competitive Edge:** Most activity platforms lack comprehensive accounting or charge separately for financial features

### 10.5 **Effortless Customer Feedback**
- **Pre-Built Survey Templates:** Small activity managers get professional survey tools they would never build themselves
- **3-Click Survey Deployment:** While competitors require complex survey setup, Minipass makes it effortless
- **Participant-Friendly Design:** Ultra-simple surveys ensure high response rates
- **Business Intelligence:** Provides actionable insights for pricing, scheduling, and service improvements that small businesses desperately need but rarely get
- **No Additional Tools:** Built into the platform rather than requiring separate survey services

### 10.6 **AI-Powered Business Intelligence for Non-Technical Users** ✅ MAJOR UPGRADE
- **Natural Language Analytics:** Users can ask questions about their business in plain English instead of learning complex reporting tools
- **5-Provider Reliability:** Google Gemini + Groq + Anthropic + OpenAI + Ollama with automatic failover
  - **Gemini Models:** 500-1,500 RPD across 5 different models
  - **Groq Llama 3.3 70B:** 14,400 RPD (29x more than Gemini 2.5)
  - **Combined Free Tier Capacity:** ~15,900 requests/day with zero downtime
  - **Budget Management:** Daily/monthly spending limits with cost tracking
  - **Security Controls:** SQL keyword filtering, query limits, conversation timeouts
- **Instant Insights:** Get immediate answers to business questions without technical expertise
- **Natural Language to SQL:** Automatic query generation from conversational questions
- **Conversational AI:** Greetings, help, and natural conversation support
- **SQLite Integration:** Simple database structure makes AI queries fast and accurate
- **Business Optimization:** Non-technical users can discover insights they would never find in traditional dashboards
- **No Additional Learning Curve:** Chat interface requires zero training vs. complex analytics platforms
- **Production Validated:** Successfully deployed with pilot customers for real business intelligence
- **Cost-Free Implementation:** Leverages free tiers of multiple providers (no ongoing AI costs)

### 10.7 **Complete Data Ownership & Trust** ✅ IMPLEMENTED
- **No Vendor Lock-in:** Users can export their complete SQLite database at any time
- **Data Transparency:** Complete ownership and control of all business data
- **Backup & Restore System:** Generate, download, upload, and restore database backups with one click
- **Automated Daily Backups:** Automatic backup generation for data protection
- **Migration Freedom:** Users never feel trapped or worried about losing their data
- **Trust Building:** Data portability demonstrates confidence in product value
- **Competitive Differentiation:** While most SaaS platforms trap user data, Minipass liberates it

### 10.8 **Complete Financial Management Suite at Every Tier** ✅ ENHANCED
- **All-in-One Financial System:** Available in $10/month Starter plan (competitors charge $50-99/month)
  - **Dual accounting standards** (cash + accrual)
  - Income tracking (passport sales + custom income entries)
  - Expense management with categorization
  - Receipt/document uploads (PDF, images)
  - Accounts Receivable and Accounts Payable tracking
  - Payment status and method recording
  - Due date management
  - CSV export for accounting software
- **Universal Accounting Integration:** Works with QuickBooks, Xero, Sage, Wave, FreshBooks
- **Activity-Level Financial Breakdown:** Detailed transaction visibility and profit/loss per activity
- **Bank Reconciliation:** Net cash flow tracking for accurate financial management
- **Mobile-Optimized:** Desktop drawer + mobile modal for on-the-go financial management
- **Marketing/CRM Export:** User contact list with engagement metrics (email, phone, passport count, revenue)
- **Email Opt-Out Tracking:** GDPR/CAN-SPAM compliant contact management
- **Production-Scale Validated:** Successfully managing significant annual revenue customers
- **Time Savings:** Eliminates manual data entry for accounting and marketing
- **Competitive Edge:** Most activity management platforms lack comprehensive financial tools or charge separately

### 10.9 **Payment Intelligence Dashboard** ✅ ENHANCED
- **Payment Inbox:** Centralized view of all incoming e-transfer emails
- **Smart Deduplication:** Automatically eliminates duplicate payment emails
- **Status Tracking:** MATCHED, NO_MATCH, MANUAL_PROCESSED with clear visual indicators
- **Search & Filter:** Find payments instantly by name, amount, or status
- **Action Items:** Focus on unmatched payments that need attention
- **Audit Trail:** Complete payment history with match reasoning and email received dates
- **Competitive Edge:** No other platform offers this level of payment inbox intelligence for e-transfers

### 10.10 **Activity Location Services** ⭐ NEW ADVANTAGE
- **Dual Geocoding Providers:** Google Maps API + Nominatim/OpenStreetMap fallback
- **Professional Address Formatting:** Automatic address validation and correction
- **Shareable Map Links:** One-click Google Maps/Apple Maps integration for participants
- **Coordinate Extraction:** Latitude/longitude storage for mapping features
- **Canadian Optimization:** Biased geocoding for accurate Canadian address results
- **Available in ALL Tiers:** Location services from $10/month Starter plan
- **Competitive Edge:** Most competitors lack integrated location services or charge extra for mapping features

### 10.11 **Instant Customer Onboarding with Zero Friction** ✅ ENHANCED
- **Stripe Automated Provisioning:** Customer goes from payment to ready-to-use system in minutes
  - Choose plan → Pay → Automatic container deployment → Welcome email → Start using
  - No manual setup, no waiting for sales calls, no configuration complexity
- **Subdomain Provisioning:** Each customer gets their own branded subdomain (e.g., `lhgi.minipass.me`)
- **SSL Certificates:** Automatic Let's Encrypt SSL for secure connections
- **Database Initialization:** Pre-configured with migrations and admin account
- **Welcome Experience:** Beautiful onboarding email with video tutorial and direct links
- **Competitive Edge:** Most SaaS platforms require manual setup or sales demos; Minipass is instant

### 10.12 **Market Position & Competitive Landscape**
- **Underserved Market:** Focuses on small activity managers ignored by enterprise solutions
- **Disruptive Pricing:** $10 starter includes features competitors charge $50-99/month for
  - Email customization (6 templates with branding): Free at all tiers vs. $30-50/month add-on
  - Dual accounting standards (cash + accrual): Included vs. $20-40/month add-on
  - Financial management suite: Included vs. $20-40/month add-on
  - Payment inbox: Included vs. manual reconciliation or separate tool
  - User contact export: Included vs. locked behind enterprise plans
  - Location services: Included vs. $10-20/month add-on
- **Canadian Payment Methods:** Built specifically for Interac e-Transfer workflows (dominant in Canadian small business)
- **Complete Automation:** While competitors require manual work, Minipass automates:
  - Payment matching and reconciliation
  - Participant communication (6 email types)
  - Financial data export for accounting
  - Customer onboarding and provisioning
  - Survey deployment and collection
  - Address geocoding and validation
- **Enterprise Features at SMB Pricing:** Features typically only in $99+/mo solutions:
  - AI analytics chatbot with 5 providers (Professional $35/month)
  - Dual accounting standards (Starter $10/month)
  - Complete financial management (Starter $10/month)
  - Email customization (Starter $10/month)
  - Automated provisioning (all tiers)
  - Location services (all tiers)
- **Production Proven:** 2 live customers successfully operating, ready for scale

---

## 11. Risks & Mitigation

### High Risk
**Competition from established players**
- *Mitigation:* Focus on SMB market, emphasize ease of use and quick setup

**Technical complexity of payment integration**
- *Mitigation:* Use proven payment processors, implement comprehensive testing

### Medium Risk
**Customer adoption challenges**
- *Mitigation:* Provide excellent onboarding, offer setup assistance

**Mobile compatibility issues**
- *Mitigation:* Extensive mobile testing, progressive web app approach

### Low Risk
**Scalability concerns**
- *Mitigation:* Cloud-native architecture, monitoring and auto-scaling

---

## 11. Next Steps

1. **Validate Assumptions:** Conduct 5 customer interviews to validate problem/solution fit
2. **Technical Planning:** Create detailed technical architecture and database schema
3. **Design System:** Create UI mockups and user flow diagrams
4. **Development Sprint Planning:** Break down features into 1-week development sprints
5. **Pilot Customer Recruitment:** Identify and reach out to 3-5 potential pilot customers

## 12. Development Principles & Guidelines

### 12.1 **Code Architecture Rules** 📋
**Python-First Development:**
- All business logic, data validation, and processing in Python
- Use Flask's templating system for dynamic HTML generation
- Database operations exclusively in Python (SQLAlchemy/raw SQL)
- Form handling and validation in Python using Flask-WTF

**Minimal JavaScript Policy:**
- JavaScript ONLY for: form enhancements, basic UI interactions, QR code scanning
- Maximum 10 lines per JavaScript function when possible
- Use vanilla JavaScript, avoid jQuery or heavy libraries
- Server-side rendering preferred over client-side dynamic content

**Performance-First Decisions:**
- Choose simple over complex solutions every time
- Optimize for memory usage and startup speed
- Use SQLite for single-tenant containers
- Avoid unnecessary HTTP requests and API calls

### 12.2 **Technology Stack Justification**
- **Flask:** Lightweight, minimal overhead, fast startup
- **Tabler.io:** CSS-only framework, no JavaScript dependencies
- **SQLite:** No separate database server, embedded, fast for single-tenant
- **Jinja2:** Server-side templating reduces client-side complexity
- **Python stdlib:** Use built-in libraries when possible

### 12.3 **CRITICAL: AI Coding Assistant Guidelines** ⚠️

**FOR ANY AI CODING ASSISTANT (INCLUDING CLAUDE CODE):**

**Mandatory JavaScript Constraints:**
- **DEFAULT RULE:** Always try Python/Flask solution first before considering JavaScript
- **JavaScript ONLY for:** Basic form validation, QR code scanning, simple UI interactions
- **Maximum JavaScript Function Size:** 10 lines preferred, 25 lines absolute maximum
- **No JavaScript Frameworks:** No jQuery, React, Vue, Angular - vanilla JavaScript only when required
- **No Complex JavaScript Logic:** No business logic, data processing, or API calls in JavaScript
- **One Bug Fix = One Change:** Never refactor surrounding code when fixing a bug

**Preferred Solutions Examples:**
- **Form Handling:** Use Flask-WTF and server-side validation, NOT client-side JavaScript validation
- **Dynamic Content:** Use Jinja2 templating with server-side data, NOT JavaScript DOM manipulation
- **Data Display:** Server-side HTML generation, NOT JavaScript table libraries
- **User Feedback:** Flash messages with Flask, NOT JavaScript modals or notifications
- **Payment Processing:** Server-side with Stripe, NOT JavaScript payment widgets

**Forbidden Approaches:**
- ❌ Enterprise-grade JavaScript solutions for simple problems
- ❌ JavaScript libraries for tasks Python can handle
- ❌ Client-side data processing when server-side is possible
- ❌ Complex JavaScript state management
- ❌ JavaScript-based routing or navigation
- ❌ Refactoring working code when fixing unrelated bugs

**Bug Fix Protocol:**
1. **Minimal Change Principle:** Fix only the specific issue, don't improve surrounding code
2. **Python-First:** If bug is in JavaScript, consider if it can be moved to Python instead
3. **Test Isolation:** Ensure fix doesn't affect other working features
4. **Documentation:** Explain why each change is necessary

### 12.4 **Resource Optimization Strategy**
- **Memory:** Lazy loading, efficient data structures, connection pooling
- **CPU:** Minimize complex computations, cache frequently accessed data
- **Disk:** Compress static files, optimize database schemas
- **Network:** Minimize external API calls, batch operations

---

## 13. Questions for Discussion

1. Should we prioritize mobile-first development or responsive web design for the scanning interface?
2. What's our approach for handling different time zones for activities that might span regions?
3. How do we handle seasonal activities that go dormant - do they still count against activity limits during off-season?
4. Should the UI differentiate between "activity management" and "loyalty program" modes, or keep one unified interface?
5. What level of passport customization should we offer in MVP (logos, colors, fields)?
6. How should we handle partial redemptions (e.g., someone has a 10-session pass, uses 3 sessions)?
7. Should the activity manager be able to issue refunds directly, or should that require admin approval?
8. For loyalty programs, should we support percentage discounts or only pre-paid packages?
9. How do we market to both activity managers AND small business owners - one website or separate positioning?
10. Should small businesses be able to set expiration dates on loyalty packages?

### Market Expansion Considerations
- **Dual Market Strategy:** The same platform serves activity managers and loyalty programs with identical technical requirements
- **Cross-Selling Opportunity:** A yoga instructor could use it for both class management AND loyalty packages
- **Marketing Challenge:** Need to communicate value to two different buyer personas with different pain points
- **UI Design:** Interface should be intuitive for both use cases without feeling cluttered

---

## 14. Operations & Support Strategy

### 14.1 **Customer Onboarding Process**
**Automated Container Deployment:**
1. Customer subscribes via main Flask website landing page
2. Collects: Organization name, desired subdomain, primary email (3-4 questions total)
3. Automated validation: Check subdomain availability, email format
4. Automated container deployment triggered upon successful validation
5. Beautiful welcome email sent with: subdomain URL, initial credentials, "getting started" video link
6. Video Onboarding: 2-3 minute maximum video showing basic system operation

**Design Principle:** Onboarding should be so intuitive that customers don't need the video, but it's there as a safety net.

### 14.2 **Customer Support Strategy**
**Support Philosophy:** Prevent issues rather than fix them - focus on bug-free, high-performance system.

**Support Channels:**
- **Primary:** Chat-based support (Microsoft Teams, Discord, or similar messaging platform)
- **Secondary:** Video/voice support available for complex issues
- **Self-Service:** Comprehensive library of short, engaging tutorial videos
- **Documentation:** Simple, visual guides for all core features

**Support Materials:**
- Multiple tutorial videos showing real-world usage scenarios
- Step-by-step visual guides for common tasks
- FAQ section based on actual customer questions

### 14.3 **Performance Monitoring & Infrastructure**
**Current Monitoring:** Custom Python scripts monitoring VPS performance and container health

**Scaling Triggers:** Evaluate CPU, RAM, and disk upgrades after every 10 new customers

**Health Monitoring Needs:**
- Container startup/crash detection
- Memory usage per customer container
- Database performance metrics
- Email delivery success rates
- Payment processing success rates

### 14.4 **Error Handling & Logging**
**User-Facing Errors:**
- Friendly error messages in the dashboard with clear next steps
- Color-coded status indicators for payment issues, email problems
- Complete audit trail of all transactions and system events

**Technical Logging:**
- All errors logged in user's dashboard for transparency
- Payment failures: Clear status with actionable information
- Email issues: Automatic bounce-back notifications to user's email
- System errors: Logged but presented in user-friendly language

**Error Recovery:**
- Automatic retry mechanisms for temporary failures
- Clear escalation path for issues requiring manual intervention
- User notification for any issue that affects their service

---

## Document Version History

### Version 1.4 - January 31, 2026
**Update: January 2026 Feature Additions & UI Standardization**

This update documents new features implemented in January 2026, focusing on financial flexibility, email customization enhancements, and payment workflow improvements.

#### 🆕 **NEW FEATURES**

1. **Custom Fiscal Year Configuration** (All Tiers)
   - Configurable financial year start month (1-12)
   - Aligns reporting periods with organizational accounting calendar
   - Added to Section 4.1 (G) - Financial Management Suite

2. **QR Code Toggle for Email Templates** (All Tiers)
   - Option to disable QR codes in email templates
   - Useful for activities where QR scanning is not needed
   - Added to Section 4.1 (D-1) - Email Communication System

3. **Custom Payment Email Address** (All Tiers)
   - Separate email address for payment instructions
   - Allows different payment routing than organization email
   - Added to Section 4.1 (D-1) - Email Communication System

4. **Create Passport from Unmatched Payment** (All Tiers)
   - Streamlined workflow to create passport directly from payment inbox
   - One-click passport creation for unmatched e-transfer payments
   - Added to Section 4.1 (E-1) - Payment Inbox

#### 🎨 **UI STANDARDIZATION**

1. **Flash Message Standardization**
   - Standardized to 4 types: success (green), error (red), warning (orange), info (blue)
   - Plus special tier-limit variant (yellow) for subscription prompts
   - Removed inconsistent emoji usage
   - Added Tabler Icons: `ti-circle-check`, `ti-alert-circle`, `ti-alert-triangle`, `ti-info-circle`
   - Gradient backgrounds with progress bar auto-dismiss
   - Documented in Design System v1.1

#### 🐛 **BUG FIXES** (Not PRD Material - Documented for Reference)

- Fixed timezone issues across multiple pages
- Fixed revenue display alignment with official financial reports
- Improved auto-complete duplicate removal for passport name/email/phone fields
- Fixed AR/AP filtering logic

---

### Version 1.3 - November 23, 2025
**Major Update: Enhanced Features & New Capabilities Documentation**

This update comprehensively documents all implemented features based on codebase analysis, including several major new features and significant enhancements not previously documented.

#### 🆕 **COMPLETELY NEW FEATURES ADDED TO PRD**

1. **Activity Location Management** (All Tiers)
   - Dual geocoding providers (Google Maps + Nominatim/OpenStreetMap)
   - Address validation and formatting
   - Coordinate extraction for mapping
   - Shareable map links
   - Canadian address optimization
   - Added to Section 4.1 (G-1)

2. **Dual Accounting Standards** (All Tiers)
   - Cash basis accounting (Cash Received, Cash Paid, Net Cash Flow)
   - Accrual basis accounting (Accounts Receivable, Accounts Payable)
   - Bank reconciliation support
   - Payment status and method tracking
   - Due date management
   - Enhanced Section 4.1 (G)

3. **Admin Personalization** (All Tiers)
   - First name and last name fields
   - Custom avatar uploads
   - Personalized greetings
   - Professional profile management
   - Added to Section 4.1 (J)

4. **Custom Payment Instructions** (All Tiers)
   - Per passport type payment instruction customization
   - Added to Section 4.1 (A)

#### 📈 **MAJOR ENHANCEMENTS TO EXISTING FEATURES**

1. **Email Template System** (Section 4.1 D-1)
   - Documented 3-tier hero image priority system
   - LRU caching for performance optimization
   - Pristine original template preservation
   - Premailer CSS inlining
   - Bleach HTML sanitization
   - Base64 email embedding optimization

2. **AI Analytics Chatbot** (Section 4.1 I)
   - Expanded from 3 to 5 AI providers
   - Added Anthropic Claude and OpenAI support
   - 7+ model options across providers
   - Budget management (daily/monthly limits)
   - Security keyword filtering
   - Conversational AI capabilities
   - Feature flags for each provider
   - Cost tracking and monitoring

3. **Financial Management Suite** (Section 4.1 G)
   - Dual accounting standards documentation
   - Payment status tracking (pending/received/cancelled for income, unpaid/paid/cancelled for expenses)
   - Payment method recording
   - Due date management
   - Accounts Receivable/Payable tracking
   - Bank reconciliation metrics

4. **User Contact Export** (Section 4.1 F)
   - Email opt-out tracking for GDPR/CAN-SPAM compliance
   - Gravatar integration
   - Enhanced responsive design details

5. **Payment Inbox** (Section 4.1 E-1)
   - Email received date tracking
   - Enhanced audit trail details

#### 🔧 **TECHNICAL ARCHITECTURE UPDATES**

1. **Integrations** (Section 6.5)
   - Added geolocation services (Google Maps + Nominatim)
   - Expanded AI/LLM services to 5 providers
   - Added security libraries (Bleach, Premailer)
   - Budget management for AI services

2. **Security Requirements** (Section 6.7)
   - Email opt-out functionality
   - SQL injection prevention details
   - XSS protection with Bleach
   - AI chatbot security controls

#### 🏆 **COMPETITIVE ADVANTAGES UPDATES**

1. **New Advantage:** Dual Accounting Standards (Section 10.4)
   - Professional-grade finance at $10/month
   - Cash + accrual basis accounting
   - Features typically in $99+/month solutions

2. **New Advantage:** Activity Location Services (Section 10.10)
   - Dual geocoding providers
   - Professional address formatting
   - Shareable map links
   - Canadian optimization

3. **Enhanced:** AI-Powered Business Intelligence (Section 10.6)
   - 5-provider reliability
   - Budget management
   - Security controls
   - Conversational AI

4. **Enhanced:** Email Communication System (Section 10.3)
   - 3-tier hero image system
   - Advanced email rendering
   - Performance optimization

5. **Enhanced:** Financial Management Suite (Section 10.8)
   - Dual accounting standards
   - Bank reconciliation
   - Payment tracking

#### 📊 **SUCCESS METRICS UPDATES**

- Added location services usage metric (70% adoption target)
- Enhanced AI system reliability metrics (5-provider fallback)
- Updated production customer validation with location services feedback

#### 📅 **USER STORIES UPDATES**

- Added location management user stories
- Added dual accounting user stories
- Updated AI chatbot stories with 5-provider system

#### 🔍 **KEY TECHNICAL DISCOVERIES DOCUMENTED**

- 3-tier hero image system with LRU caching
- Dual geocoding with automatic fallback
- 5-provider AI system with feature flags
- Dual accounting standards implementation
- Email opt-out compliance features
- Payment status and method tracking
- Admin personalization system

---

### Version 1.2 - November 7, 2025
**Major Update: Production Launch Ready - Complete Feature Suite & Live Customers**

This update reflects the transition from pilot deployment to production launch readiness, with 2 live customers successfully operating and comprehensive feature enhancements across the platform.

#### 🚀 **Production Status & Launch Preparation**
- **Official Launch Date:** November 15, 2025
- **Live Customers:** 2 production customers (LHGI charity foundation + hockey coach)
- **Automated Provisioning:** Stripe webhook integration for instant customer onboarding
- **Infrastructure:** Multi-tenant Docker deployment with automated SSL and subdomain provisioning
- **Status:** Production-ready, validated with real-world operations

#### ✅ **New Features Implemented (All Tiers Unless Noted)**

1. **Professional Email Communication System** (All Tiers)
   - 6 customizable email templates (newPass, paymentReceived, latePayment, signup, redeemPass, survey_invitation)
   - Per-activity customization (subject, title, body, intro, conclusion, CTA)
   - Hero image upload and activity logo integration
   - Live preview and test email functionality
   - HTML-supported content with security sanitization
   - Reset to defaults capability
   - **Available from $10/month Starter plan** (competitors charge $30-50/month extra)

2. **Payment Inbox & Management Dashboard** (All Tiers)
   - Centralized payment inbox for e-transfer emails
   - Matched/unmatched payment tracking with status indicators
   - Smart deduplication system
   - Search and filter by sender, amount, status
   - Archive workflow for clean inbox management
   - Payment audit trail with match reasoning
   - Pagination support (50 items/page)

3. **Complete Financial Management Suite** (All Tiers)
   - Unified income/expense tracking dashboard
   - Receipt/document uploads (PDF, JPG, PNG) with modal viewing
   - Category system (7 income types, 9 expense types)
   - Activity-level financial breakdown with accordion view
   - CSV export for QuickBooks, Xero, Sage, Wave, FreshBooks
   - Period filtering (Month, Quarter, Year, Custom, All-Time)
   - Mobile-responsive (desktop drawer + mobile modal)
   - Real-time KPI cards (Total Revenue, Total Expenses, Net Income)

4. **User Contact Management & Export** (All Tiers)
   - Comprehensive user directory with engagement metrics
   - Dynamic search with Ctrl+K keyboard shortcut
   - GitHub-style filter buttons (Active vs All users)
   - Gravatar integration for user avatars
   - Email opt-out status tracking
   - CSV export for CRM/marketing tools
   - Responsive design (desktop/tablet/mobile optimized)
   - Engagement data: passport count, revenue, activities, last activity date

5. **Enhanced Survey System** (Professional & Enterprise)
   - Survey template library (reusable question sets)
   - Pre-built templates (English & French)
   - True 3-click deployment workflow
   - Survey lifecycle management (create, send, close, reopen, delete)
   - Response tracking with tokens and timestamps
   - Results dashboard with aggregated statistics
   - CSV export of survey responses
   - Target audience selection (passport type or all participants)

6. **AI Analytics Chatbot Enhancements** (Professional & Enterprise)
   - Multi-provider system: Google Gemini + Groq + Ollama
   - Provider selection dropdown in UI
   - Claude.ai-inspired interface design
   - Interactive example questions for guidance
   - SQL display for transparency
   - Chart rendering for data visualization
   - Status LED for API connectivity
   - Intent detection (aggregation, list, comparison, visualization)
   - Entity extraction (dates, activities, numbers, emails)
   - Token usage and cost tracking
   - Query logging with complete audit trail

7. **Automated Customer Provisioning**
   - Stripe webhook integration for subscription payments
   - Automatic Docker container deployment
   - Subdomain provisioning (e.g., `customer.minipass.me`)
   - SSL certificate automation via Let's Encrypt
   - Database initialization with migrations
   - Welcome email with credentials and video tutorial
   - Zero manual intervention onboarding

#### 📊 **Production Customer Validation**

**Customer 1: LHGI (Ligue hockey Gagnon Image)**
- Charity foundation and hockey league organization
- Managing multiple activities with diverse participant groups
- Heavy adoption of email customization and financial reporting
- Reports significant time savings and improved transparency

**Customer 2: Hockey Coach (Personal Training)**
- Individual sports coaching and training programs
- Managing training sessions with different skill levels
- Values mobile-friendly interface and payment automation
- Reports improved client management and revenue tracking

**Key Learnings:**
- Email customization critical for brand consistency
- Financial reporting essential for both non-profit and small business
- Customers report significant administrative time savings
- Non-technical users successfully manage all features without training
- Mobile usage is frequent and important

#### 🎯 **Pricing & Feature Distribution Updates**
- **Clarified Tier Structure:** All core features (email customization, financial suite, payment inbox, user export) available in $10/month Starter
- **Professional & Enterprise:** Survey system and AI chatbot reserved for higher tiers
- **Disruptive Pricing:** Features typically costing $50-99/month in competitors available at $10/month

#### 🏆 **Competitive Advantages Added**
- **Professional Communication Suite:** 6 customizable emails at all tiers vs $30-50/month add-on from competitors
- **Complete Financial Suite:** All-in-one financial management from $10/month
- **Payment Intelligence Dashboard:** Unique e-transfer inbox management
- **Instant Customer Onboarding:** Stripe auto-provisioning vs manual setup/sales demos
- **Market Position:** Enterprise features at SMB pricing ($10-50 vs $99+/month)

#### 🔧 **Technical Architecture Enhancements**
- Multi-tenant organization model with per-tenant configuration
- Enhanced database models: Organization, Expense, ChatConversation, ChatMessage
- Receipt storage system with file uploads
- Email template compilation and rendering system
- Provider manager for AI with health monitoring
- Webhook handling for Stripe events

#### 📈 **Success Metrics Updates**
- Launch goal achieved: 2 production customers live
- Production validation: Managing real-world revenue and operations
- Feature adoption: Email customization heavily used by all customers
- Time savings: Significant reduction in administrative overhead reported
- Customer feedback: Ease of use and professional communication praised

#### 📅 **Launch Timeline Updated**
- Development phase: Completed ✅
- Testing & refinement: Completed with 2 live customers ✅
- Production launch preparation: In progress
- **Official launch: November 15, 2025** 🚀

---

### Version 1.1 - October 20, 2025
**Major Update: Production Deployment & Feature Implementation**

This update reflects significant progress from pilot customer deployments and real-world validation with customers managing $300K+ annual revenue.

#### Features Moved from Phase 2 to MVP (Now Implemented):

1. **AI Data Chatbot** ✅
   - Implemented with dual-provider architecture (Google Gemini + Groq)
   - 15,900+ requests/day capacity with automatic failover
   - Natural language to SQL query generation
   - Production validated with pilot customers
   - Free tier implementation (zero ongoing AI costs)

2. **Complete Data Ownership** ✅
   - Full SQLite database export capability
   - Backup & restore system with one-click downloads
   - Automated daily backups
   - Upload and restore external backups

3. **Enhanced Financial Reporting** ✅
   - Comprehensive income and expense tracking by activity
   - CSV export for universal accounting software compatibility (QuickBooks, Xero, Sage, Wave, FreshBooks)
   - Receipt/document management with viewing
   - Period filtering (Month, Quarter, Year, Custom, All-Time)
   - Mobile-responsive design
   - Validated with $300K+ revenue customer

4. **User Contacts Export** ✅ NEW
   - User contact list with engagement metrics
   - CSV export for marketing/CRM integration
   - Advanced filtering (period, activity, engagement sort)
   - Email opt-out management
   - Shows: Total users, active users, revenue, passports per user

#### Technical Implementation Details Added:

- **AI/LLM Integrations:**
  - Google Gemini 2.0 Flash Exp: 1,500 RPD, 15 RPM, 1M TPM (Primary)
  - Groq Llama 3.3 70B: 14,400 RPD, 30 RPM (Automatic Fallback)
  - Provider manager with health monitoring
  - Budget tracking system
  - Query logging with token usage

- **Navigation Updates:**
  - New "Reports" section with 4 submenu items
  - Payments, Users, Financial, AI Analytics (Beta)

#### Success Metrics Updated:

- Added AI system reliability metrics (99.9% uptime)
- Added financial export adoption targets (50% of Professional+ monthly)
- Added user contacts export targets (40% of customers)
- Updated feature adoption (90%+ using advanced reporting)
- Validated production scale ($300K+ revenue customers)

#### Competitive Advantages Strengthened:

- New section: Professional Financial & Contact Management
- Emphasized dual-provider AI reliability (unique in market)
- Cost-free AI implementation using free tiers
- Enterprise features at SMB pricing ($10-50/month vs $99+)

#### Production Validation:

- Successfully deployed to pilot customers
- Managing customers with $300K+ annual revenue
- Real-world validation of all MVP features
- Field testing drives continuous improvement

---

### Version 1.0 - August 28, 2025
**Initial Release**

Original PRD defining MVP features, Phase 2 roadmap, and go-to-market strategy.

---

*This PRD continues to evolve based on customer feedback and market validation results.*
