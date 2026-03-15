# Minipass Email Template System - Complete Guide

**Version:** 3.0 (Hybrid URL Model)
**Last Updated:** 2026-02-19
**Purpose:** Comprehensive developer guide for the complete email template system (backend + frontend)

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Component Architecture](#component-architecture)
3. [Workflow 1: Creating/Modifying Templates (Backend)](#workflow-1-creatingmodifying-templates-backend)
4. [Workflow 2: Per-Activity Customization (Frontend)](#workflow-2-per-activity-customization-frontend)
5. [Workflow 3: Reset to Defaults](#workflow-3-reset-to-defaults)
6. [Hero Image Resolution System](#hero-image-resolution-system)
7. [Email Sending Pipeline (Production)](#email-sending-pipeline-production)
8. [Database Schema & File Storage](#database-schema--file-storage)
9. [Key Code References](#key-code-references)
10. [Appendix: Issues & Troubleshooting](#appendix-issues--troubleshooting)

---

## System Overview

### Purpose

Minipass has **6 pre-built email templates** that are sent automatically to users. The system has two layers:

1. **Backend Layer**: Master templates that developers modify, compile, and deploy
2. **Frontend Layer**: Per-activity customization interface for activity managers

### The Six Email Templates

| Template Key | Display Name | Trigger Event |
|--------------|--------------|---------------|
| `newPass` | New Pass Created | When a digital pass is created for a user |
| `paymentReceived` | Payment Received | When payment is confirmed |
| `latePayment` | Late Payment Reminder | When payment is overdue |
| `signup` | Signup Confirmation | When user registers for an activity |
| `redeemPass` | Pass Redeemed | When user uses their pass |
| `survey_invitation` | Survey Invitation | When survey is sent to user |

### Key Concept: Three Template Versions

Each template exists in **three states**:

1. **Master** (`templateName/`) - Source files that developers edit
2. **Compiled** (`templateName_compiled/`) - Production templates with embedded images (what the app uses)
3. **Original** (`templateName_original/`) - Pristine compiled version (used when users click "Reset to Default")

---

## Component Architecture

### Directory Structure

```
/templates/email_templates/
├── compileEmailTemplate.py          # ⚙️ Compilation script
├── email-hero-images/               # 🎨 AI-designed hero images (ready to use)
│   ├── signup.png
│   ├── New_passport_created.png
│   ├── payment_received.png
│   ├── passport_redeemed.png
│   ├── late_payment_notice.png
│   └── survey.png
│
├── signup/                          # 📝 MASTER (developers edit this)
│   ├── index.html
│   └── good-news.png
├── signup_compiled/                 # ✅ COMPILED (app uses this)
│   ├── index.html
│   └── inline_images.json
├── signup_original/                 # 💾 ORIGINAL (pristine defaults)
│   ├── index.html
│   └── inline_images.json
│
├── newPass/                         # 📝 MASTER
│   ├── index.html
│   ├── hero_new_pass.png
│   ├── logo.png
│   └── ticket.png
├── newPass_compiled/                # ✅ COMPILED
├── newPass_original/                # 💾 ORIGINAL
│
├── paymentReceived/                 # 📝 MASTER
├── paymentReceived_compiled/        # ✅ COMPILED
├── paymentReceived_original/        # 💾 ORIGINAL
│
├── redeemPass/                      # 📝 MASTER
├── redeemPass_compiled/             # ✅ COMPILED
├── redeemPass_original/             # 💾 ORIGINAL
│
├── latePayment/                     # 📝 MASTER
├── latePayment_compiled/            # ✅ COMPILED
├── latePayment_original/            # 💾 ORIGINAL
│
├── survey_invitation/               # 📝 MASTER
├── survey_invitation_compiled/      # ✅ COMPILED
└── survey_invitation_original/      # 💾 ORIGINAL

/config/
└── email_defaults.json              # 📄 Default text for all templates

/static/uploads/
├── {activity_id}_{template}_hero.png    # Custom hero images (per activity/template)
├── {activity_id}_owner_logo.png         # Organization logos (per activity, shared across templates)
└── activity_images/
    └── {activity_image_filename}        # Activity images (fallback hero)
```

### Architecture Layers

```
┌─────────────────────────────────────────────────────────────────┐
│                     DEVELOPER LAYER (Backend)                    │
│  - Master templates (HTML + images)                             │
│  - Compilation script (compileEmailTemplate.py)                 │
│  - Default text config (email_defaults.json)                    │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                   ┌────────▼────────┐
                   │  COMPILATION    │
                   │  (Base64 encode)│
                   └────────┬────────┘
                            │
┌───────────────────────────▼─────────────────────────────────────┐
│                    PRODUCTION LAYER (Files)                      │
│  - Compiled templates (_compiled folders)                       │
│  - Original templates (_original folders)                       │
│  - Inline images JSON (base64 encoded)                          │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                   ┌────────▼────────┐
                   │   Flask App     │
                   │   (app.py)      │
                   └────────┬────────┘
                            │
┌───────────────────────────▼─────────────────────────────────────┐
│                 CUSTOMIZATION LAYER (Frontend)                   │
│  - Per-activity customization UI                                │
│  - Database storage (activity.email_templates JSON)             │
│  - File uploads (custom heroes, owner logos)                    │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                   ┌────────▼────────┐
                   │ Email Rendering │
                   │  & Sending      │
                   └─────────────────┘
```

---

## Workflow 1: Creating/Modifying Templates (Backend)

This workflow is for **developers** who want to improve the master email templates.

### Step 1: Update Default Text (Optional)

**File:** `config/email_defaults.json`

**Current Status:** Defaults are in French

**Structure:**
```json
{
    "newPass": {
        "subject": "Votre passeport numérique est prêt",
        "title": "Votre passeport est prêt",
        "intro_text": "<p>Bonjour <strong>{{ pass_data.user.name }}</strong>,</p>...",
        "conclusion_text": "<p>Merci de faire partie de cette aventure...</p>",
        "cta_text": "Voir mon passeport",
        "cta_url": "https://minipass.me/my-passes"
    },
    ...
}
```

**Fields:**
- `subject` - Email subject line (plain text)
- `title` - Main heading in email (plain text)
- `intro_text` - Opening paragraph (HTML + Jinja2 variables)
- `conclusion_text` - Closing paragraph (HTML + Jinja2 variables)
- `cta_text` - Call-to-action button text
- `cta_url` - Call-to-action button URL

**Jinja2 Variables Available:**

For pass-related templates (`newPass`, `paymentReceived`, `redeemPass`, `latePayment`):
- `{{ pass_data.user.name }}` - User's name
- `{{ pass_data.activity.name }}` - Activity name
- `{{ pass_data.sold_amt }}` - Price paid
- `{{ pass_data.uses_remaining }}` - Sessions remaining
- `{{ pass_data.paid }}` - Payment status (boolean)
- `{{ pass_data.activity.location_address_formatted }}` - Location

For signup template:
- `{{ user_name }}` - User name
- `{{ activity_name }}` - Activity name
- `{{ activity.location_address_formatted }}` - Location

For survey invitation:
- `{{ activity_name }}` - Activity name
- `{survey_url}` - Dynamic survey URL (placeholder)

### Step 2: Update Hero Images

**Available AI-designed images:** `templates/email_templates/email-hero-images/`

**To replace hero images:**
```bash
cd /home/kdresdell/Documents/DEV/minipass_env/app/templates/email_templates/

# Update newPass hero
cp email-hero-images/New_passport_created.png newPass/hero_new_pass.png

# Update signup hero
cp email-hero-images/signup.png signup/good-news.png

# Update paymentReceived hero
cp email-hero-images/payment_received.png paymentReceived/currency-dollar.png

# Update redeemPass hero
cp email-hero-images/passport_redeemed.png redeemPass/hand-rock.png

# Update latePayment hero
cp email-hero-images/late_payment_notice.png latePayment/thumb-down.png

# Update survey_invitation hero
cp email-hero-images/survey.png survey_invitation/sondage.png
```

**Image Requirements:**
- Must be in master template folder
- Referenced in `index.html` with matching filename
- Supported formats: PNG, JPG, GIF
- Keep optimized (< 500KB recommended)
- Hero images auto-cropped during compilation (white background removed)

### Step 3: Update HTML Template (Advanced)

**Location:** `templates/email_templates/{templateName}/index.html`

**Template Structure:**
- Responsive email design (table-based layout for email client compatibility)
- Inline CSS (required for email clients)
- Jinja2 templating for dynamic content
- Image references (converted to CID during compilation)

**Key Sections:**
- Hero image section
- Title section
- Intro text section
- Transaction table (showing passport details)
- QR code section
- Conclusion text section
- Footer section

### Step 4: Compile Templates

**Script:** `compileEmailTemplate.py`

**Two Modes:**

#### Development Mode (Default)
Updates `_compiled` only, preserves `_original` (pristine defaults)

```bash
cd /home/kdresdell/Documents/DEV/minipass_env/app/templates/email_templates/

# Compile single template
python compileEmailTemplate.py newPass

# Compile all templates
for t in signup newPass paymentReceived redeemPass latePayment survey_invitation; do
    python compileEmailTemplate.py "$t"
done
```

**Use when:**
- Testing/developing templates locally
- Iterating on design
- Don't want to affect pristine defaults

#### Production Deployment Mode
Updates BOTH `_compiled` AND `_original` (pristine defaults that users see when they click "Reset")

```bash
# Compile with --update-original flag
python compileEmailTemplate.py newPass --update-original

# Compile all for production deployment
for t in signup newPass paymentReceived redeemPass latePayment survey_invitation; do
    python compileEmailTemplate.py "$t" --update-original
done
```

**Use when:**
- Deploying improved templates to production
- You want customers to see new design when clicking "Reset"
- Updating pristine defaults for all activities

**What the compilation script does:**
1. Reads `index.html` from master folder
2. Finds all image references (e.g., `<img src="hero_new_pass.png">`)
3. Preprocesses hero images:
   - Detects white background (RGB > 250)
   - Auto-crops to content (removes white borders)
   - NO padding added (clean crop only)
4. Converts images to base64 encoded strings
5. Replaces hero/logo image paths with Jinja2 URL variables (`{{ hero_image_url }}`, `{{ owner_logo_url }}`) — images are served from hosted Flask routes when the email is opened, not embedded as MIME attachments
6. Writes compiled HTML to `{templateName}_compiled/index.html`
7. Writes base64 image data to `{templateName}_compiled/inline_images.json` — used by the `/hero-image/` Flask route for Priority 2 (default hero) fallback; not used for MIME email attachments
8. If `--update-original` used: ALSO updates `{templateName}_original/` folder

**Hero Image Preprocessing:**

The script automatically detects and preprocesses hero images:
```python
# Hero images identified by name
is_hero_image = any(hero_name in filename.lower()
                  for hero_name in ['hero', 'good-news', 'currency-dollar',
                                   'hand-rock', 'thumb-down', 'sondage'])

if is_hero_image:
    # Auto-crop white background, NO padding
    img_processed = process_hero_image(asset_path, padding=0)
```

**Output Example (Development):**
```
🚀 Email Template Compiler v3.0 - Starting compilation...
📧 Starting compilation of 'newPass'
🛠️  MODE: Development (compiled only, original preserved)
📂 Source path: /path/to/newPass
📂 Target path: /path/to/newPass_compiled
🖼️  Processing 4 images
🎨 Preprocessing hero image (auto-crop, NO padding)...
   📐 Cropped from (1024, 1024) to (846, 767) (removed white background)
✅ Successfully preprocessed and embedded 483062 bytes for hero_new_pass
💾 Writing HTML to: /path/to/newPass_compiled/index.html
✅ Verified HTML written: 6842 bytes
💾 Writing images JSON to: /path/to/newPass_compiled/inline_images.json
✅ Verified JSON written: 245632 bytes
ℹ️  Skipping original update (use --update-original to deploy new pristine defaults)
🎉 SUCCESS: Compiled 'newPass' → 'newPass_compiled' with 4 embedded images
```

**Output Example (Production with --update-original):**
```
🚀 Email Template Compiler v3.0 - Starting compilation...
📧 Starting compilation of 'newPass'
🔄 MODE: Production Deployment (updating pristine original)
⚠️  WARNING: Will update pristine original - customers will see this when resetting!
📂 Original path: /path/to/newPass_original
🎨 Preprocessing hero image (auto-crop, NO padding)...
   📐 Cropped from (1024, 1024) to (846, 767) (removed white background)
✅ Successfully preprocessed and embedded 483062 bytes for hero_new_pass
💾 Updating original (pristine) files...
✅ Updated original (pristine) files - customers will see this when resetting
🎉 SUCCESS: Compiled 'newPass' → 'newPass_compiled' AND updated 'newPass_original' (pristine)
✅ Pristine original updated - deploy to production!
```

### Step 5: Test Changes

1. **Restart Flask server** (if not in debug mode)
2. **Test via application:**
   - Navigate to `/activity/<activity_id>/email-templates`
   - Customize a template
   - Use "Preview" or "Send Test Email"
3. **Verify email rendering** in inbox

---

## Workflow 2: Per-Activity Customization (Frontend)

This workflow is for **activity managers** who want to customize email templates for their specific activity.

### Frontend URL

```
/activity/<activity_id>/email-templates
```

Example: `http://localhost:5000/activity/1/email-templates`

### User Interface

**Template Cards Grid:** Shows all 6 templates as cards with:
- Mini hero image preview
- Placeholder text lines
- Mini owner card (for pass templates)
- Template name
- Status badge ("Custom" or "Default")
- "Customize" button
- "Reset" button

### Customization Modal

**Triggered by:** Clicking "Customize" button on any template card

**Form Fields:**
- **Subject Line** (plain text input)
- **Title** (plain text input)
- **Intro Text** (TinyMCE rich text editor)
- **Conclusion Text** (TinyMCE rich text editor)
- **Hero Image Upload** (file input with preview)
- **Owner Logo Upload** (file input, shown only for first template, shared across all)

**Actions:**
- **Preview** - Opens new tab with rendered email (unsaved changes)
- **Send Test** - Sends actual email to test address (unsaved changes)
- **Save** - Saves customizations to database and file system

### Save Process

**Frontend (JavaScript):**
```javascript
// Collect form data
const formData = new FormData();
formData.append('single_template', templateType);
formData.append(`${templateType}_subject`, subject);
formData.append(`${templateType}_title`, title);
formData.append(`${templateType}_intro_text`, introText);
formData.append(`${templateType}_conclusion_text`, conclusionText);
formData.append(`${templateType}_hero_image`, heroImageFile);
formData.append(`${templateType}_owner_logo`, ownerLogoFile);

// Send to backend
fetch(`/activity/${activityId}/email-templates/save`, {
    method: 'POST',
    body: formData
});
```

**Backend Route:** `app.py:7719-8100` (`save_email_templates()`)

**Backend Process:**
1. Validates admin session
2. Processes hero image uploads:
   - Saves as `static/uploads/{activity_id}_{template_type}_hero.png`
   - Resizes to match template dimensions (calls `resize_hero_image()`)
3. Processes owner logo upload:
   - Saves as `static/uploads/{activity_id}_owner_logo.png`
   - Shared across all templates
4. Sanitizes text content (removes dangerous HTML)
5. Updates `activity.email_templates` JSON column
6. Marks SQLAlchemy JSON field as modified (`flag_modified()`)
7. Commits to database
8. Returns JSON response (AJAX) or redirects (form submit)

**File Storage Naming:**
- Hero images: `static/uploads/{activity_id}_{template_type}_hero.png`
- Owner logo: `static/uploads/{activity_id}_owner_logo.png` (shared)

**Database Storage:**
```python
activity.email_templates = {
    "newPass": {
        "subject": "Custom Subject",
        "title": "Custom Title",
        "intro_text": "<p>Custom intro...</p>",
        "conclusion_text": "<p>Custom conclusion...</p>",
        "hero_image": "1_newPass_hero.png",
        "activity_logo": "1_owner_logo.png"
    },
    ...
}
```

### Preview Feature

**Route:** `app.py:8262+` (`email_preview_live()`)

**Process:**
1. Accepts form data with unsaved changes
2. Temporarily saves uploaded hero image (if any)
3. Renders compiled email template with changes
4. Returns HTML for preview in new tab
5. **Does NOT save to database**

### Test Email Feature

**Route:** `app.py:8591+` (`test_email_template()`)

**Process:**
1. Accepts form data with unsaved changes
2. Renders compiled template with changes
3. Sends actual email to specified test address
4. **Does NOT save to database**

---

## Workflow 3: Reset to Defaults

This workflow restores a template to its pristine default state.

### User Action

1. User clicks "Reset to Default" button on template card
2. Confirmation modal appears: "Reset [Template Name] to default values?"
3. User clicks "Reset" button
4. Loading spinner appears
5. Page reloads with success message
6. Template card shows "Default" badge
7. Hero image reverts to original template default

### Backend Process

**Route:** `app.py:8102-8199` (`reset_email_template()`)

**Step-by-step execution:**

#### Step 1: Validate Request
```python
activity = Activity.query.get_or_404(activity_id)
data = request.get_json()
template_type = data['template_type']

valid_templates = ['newPass', 'paymentReceived', 'latePayment',
                   'signup', 'redeemPass', 'survey_invitation']
if template_type not in valid_templates:
    return jsonify({'success': False}), 400
```

#### Step 2: Clear Database Customizations
```python
if template_type in activity.email_templates:
    template_data = activity.email_templates[template_type]

    # Clear customizable fields
    fields_to_reset = ['subject', 'title', 'intro_text', 'conclusion_text',
                       'hero_image', 'activity_logo']
    for field in fields_to_reset:
        if field in template_data:
            del template_data[field]

    # Remove entire template entry if empty
    if not template_data:
        del activity.email_templates[template_type]
```

**Result:** Template will fall back to defaults from `config/email_defaults.json`

#### Step 3: Delete Physical Hero Image File
```python
import os
hero_file_path = f"static/uploads/{activity_id}_{template_type}_hero.png"
if os.path.exists(hero_file_path):
    os.remove(hero_file_path)
    print(f"✅ Deleted custom hero image file: {hero_file_path}")
```

**Result:** Custom hero image removed from disk

#### Step 4: Delete Owner Logo (newPass Only)
```python
owner_logo_path = f"static/uploads/{activity_id}_owner_logo.png"
if template_type == 'newPass' and os.path.exists(owner_logo_path):
    os.remove(owner_logo_path)
    print(f"✅ Deleted custom owner logo file: {owner_logo_path}")
```

**Why newPass only?** Owner logo is shown in first template's customization form, so it's deleted only when resetting that template.

#### Step 5: Restore Original Compiled Template
```python
import shutil
original_dir = f"templates/email_templates/{template_type}_original"
compiled_dir = f"templates/email_templates/{template_type}_compiled"

if os.path.exists(original_dir):
    # Delete compiled folder
    if os.path.exists(compiled_dir):
        shutil.rmtree(compiled_dir)
    # Copy original to compiled
    shutil.copytree(original_dir, compiled_dir)
    print(f"✅ Restored original template files: {original_dir} → {compiled_dir}")
```

**Why this matters:**
- Restores pristine HTML and inline_images.json
- Ensures email rendering uses default template structure
- This is the "nuclear option" - complete template restoration

#### Step 6: Commit Database Changes
```python
from sqlalchemy.orm.attributes import flag_modified
flag_modified(activity, 'email_templates')
db.session.commit()
```

**Critical:** Must flag JSON field as modified for SQLAlchemy to detect changes

#### Step 7: Return Success Response
```python
flash('Template reset to defaults successfully!', 'success')

return jsonify({
    'success': True,
    'message': f'Template "{template_type}" has been reset to default values'
})
```

### Reset Summary

**Files Deleted:**
1. `static/uploads/{activity_id}_{template_type}_hero.png`
2. `static/uploads/{activity_id}_owner_logo.png` (newPass only)
3. `templates/email_templates/{template_type}_compiled/` (entire folder)

**Files Restored:**
1. `templates/email_templates/{template_type}_compiled/` (copied from `_original`)

**Database Changes:**
1. Removed custom fields from `activity.email_templates[template_type]`
2. Deleted template entry if no data remains

**Result:**
- Template reverts to pristine defaults
- Text content from `config/email_defaults.json`
- Hero image from `{template}_original/inline_images.json`
- Compiled HTML from `{template}_original/index.html`

---

## Hero Image Resolution System

When rendering an email template, the system determines which hero image to use based on a **three-tier priority hierarchy**.

### Priority Order (Highest to Lowest)

#### Priority 1: Custom Uploaded Hero ⭐

**Location:** `static/uploads/{activity_id}_{template_type}_hero.png`

**When used:**
- User uploaded a custom hero image via customization tool
- File exists on disk

**Code:** `utils.py:136-151`
```python
custom_hero_path = f"static/uploads/{activity.id}_{template_type}_hero.png"
if os.path.exists(custom_hero_path):
    with open(custom_hero_path, "rb") as f:
        hero_data = f.read()
        return hero_data, True, False  # is_custom=True
```

**Visual indicator:** Template card shows "Custom" badge

**When cleared:** User clicks "Reset to Default"

---

#### Priority 2: Original Template Default 📦

**Location:** `templates/email_templates/{template}_original/inline_images.json`

**When used:**
- No custom hero image exists (Priority 1 not available)
- Template is in default state

**Code:** `utils.py:152-156`
```python
template_hero_data = get_template_default_hero(template_type)
if template_hero_data:
    return template_hero_data, False, True  # is_template_default=True
```

**Image resolution:** `utils.py:58-118` (`get_template_default_hero()`)
```python
# Map template to original folder
template_map = {
    'newPass': 'newPass_original',
    'paymentReceived': 'paymentReceived_original',
    ...
}

# Load inline_images.json from ORIGINAL template
json_path = f'templates/email_templates/{original_folder}/inline_images.json'
with open(json_path, 'r') as f:
    compiled_images = json.load(f)

# Map to hero key
hero_key_map = {
    'newPass': 'hero_new_pass',
    'paymentReceived': 'currency-dollar',
    'latePayment': 'thumb-down',
    'signup': 'good-news',
    'redeemPass': 'hand-rock',
    'survey_invitation': 'sondage'
}

hero_key = hero_key_map.get(template_type)
hero_base64 = compiled_images[hero_key]
return base64.b64decode(hero_base64)
```

**Visual indicator:** Template card shows "Default" badge

**These are the pristine images included in the original templates**

---

#### Priority 3: Activity Image (Conditional Fallback) 🎯

**Location:** `static/uploads/{activity.image_filename}` or `static/uploads/activity_images/{activity.image_filename}`

**When used:**
- No custom hero exists (Priority 1 not available)
- No original template default loaded (Priority 2 failed)
- **AND template has active customizations** (key condition!)

**Code:** `utils.py:158-188`
```python
# Only use if template has active customizations
if activity and activity.image_filename:
    has_customizations = False
    if activity.email_templates and template_type in activity.email_templates:
        template_data = activity.email_templates[template_type]
        customizable_fields = ['subject', 'title', 'intro_text',
                               'conclusion_text', 'hero_image', 'activity_logo']
        has_customizations = any(field in template_data and template_data[field]
                                for field in customizable_fields)

    # Only use activity image if template was customized
    if has_customizations:
        activity_image_paths = [
            f"static/uploads/{activity.image_filename}",
            f"static/uploads/activity_images/{activity.image_filename}"
        ]

        for activity_image_path in activity_image_paths:
            if os.path.exists(activity_image_path):
                with open(activity_image_path, "rb") as f:
                    return f.read(), False, False
```

**Important conditions:**
1. Activity must have an image file
2. Template must have active customizations in database
3. This prevents showing activity image after reset

**Visual indicator:** Template card shows "Custom" badge

**Why this exists:** When user customizes a template but doesn't upload a hero, use activity image instead of leaving it blank

---

### Priority System Examples

#### Example 1: Fresh Activity (Never Customized)
```
User hasn't touched email templates yet
Result: Priority 2 (Original Template Default)
Hero: templates/email_templates/newPass_original/inline_images.json → hero_new_pass
Badge: "Default"
```

#### Example 2: User Uploads Custom Hero
```
User clicks Customize → Uploads hero.jpg → Saves
Result: Priority 1 (Custom Uploaded Hero)
Hero: static/uploads/1_newPass_hero.png
Badge: "Custom"
```

#### Example 3: User Customizes Text But No Hero
```
User clicks Customize → Changes title → Saves (no hero upload)
Result: Priority 3 (Activity Image Fallback)
Hero: static/uploads/activity_images/hockey_league.png
Badge: "Custom"
Reason: Template has customizations, so show activity branding
```

#### Example 4: User Resets After Customization
```
User had uploaded hero → Clicks Reset to Default
Result: Priority 2 (Original Template Default)
Hero: templates/email_templates/newPass_original/inline_images.json → hero_new_pass
Badge: "Default"
Reason: Reset deleted custom hero file AND database customizations
```

### Why This Complexity?

**Problem:** Users expect different behavior in different contexts:
1. **Default state:** Show professional template defaults
2. **Customizing:** Show activity branding if no hero uploaded
3. **After reset:** Show pristine defaults, NOT activity image

**Solution:** Three-tier priority with conditional fallback

**Key insight:** Priority 3 checks for `has_customizations` to avoid showing activity image after reset

---

## Email Sending Pipeline (Production)

This is the complete flow when an email is triggered in production.

**Image delivery model:** Hybrid. QR code is embedded as CID (must always display — functional
element). Hero image and owner logo are served via hosted Flask URLs (decorative — loaded when
the email client opens the email). This reduces email size from ~30–50 KB to ~8–10 KB.

### Trigger Event

Examples:
- New pass created → `send_new_pass_email(passport, user)`
- Payment received → `send_payment_received_email(passport, user)`
- Pass redeemed → `send_pass_redeemed_email(passport, user)`

### Step 1: Build Email Context

**Function:** `utils.py:3223-3273` (`get_email_context()`)

```python
from utils import get_email_context

base_context = {
    'user_name': user.name,
    'pass_code': passport.pass_code,
    'owner_html': '...',  # Generated HTML block
    'history_html': '...'  # Generated HTML block
}

context = get_email_context(
    activity=passport.activity,
    template_type='newPass',
    base_context=base_context
)
```

**What it does:**
1. Starts with base context (event-specific data)
2. Loads defaults from `config/email_defaults.json`
3. Overlays activity customizations from `activity.email_templates` JSON
4. Preserves protected blocks (`owner_html`, `history_html`)
5. Sets `hero_image_url` → `https://{site_url}/activity/{activity.id}/hero-image/{template_type}`
6. Sets `owner_logo_url` → `https://{site_url}/owner-logo?activity_id={activity.id}`
7. Returns merged context for template rendering

**Image URL resolution:** Hero and logo URLs point to Flask routes that apply the 3-tier priority
system when the email client fetches the image at open time (not at send time).

### Step 2: Render Compiled Template

```python
from flask import render_template

html = render_template(
    'email_templates/newPass_compiled/index.html',
    **context
)
```

**Template location:** Uses `_compiled` folder (not master)

**Image rendering in template:**
- `{{ hero_image_url }}` → resolved to hosted `/hero-image/` route URL
- `{{ owner_logo_url }}` → resolved to hosted `/owner-logo` route URL
- `cid:qr_code` → remains as CID reference (resolved at MIME build time)

### Step 3: Send Email

**Function:** `utils.py:2090+` (`send_email()`)

```python
from utils import send_email

send_email(
    subject=context['subject'],
    to_email=user.email,
    html_body=html,
    inline_images={'qr_code': qr_data},
    use_hosted_images=True
)
```

**Hybrid delivery via `use_hosted_images=True`:**
- Hero and logo are **not** attached as MIME parts — they load from hosted URLs when email opens
- QR code is **still** attached as CID inline (functional element — must always display)

### Complete Flow Diagram

```
┌────────────────────────────────────────────────────────────────┐
│  Trigger Event (e.g., new pass created)                        │
└────────────────────────┬───────────────────────────────────────┘
                         │
                         ▼
┌────────────────────────────────────────────────────────────────┐
│  Build Base Context (pass data, user data, owner HTML, etc.)   │
└────────────────────────┬───────────────────────────────────────┘
                         │
                         ▼
┌────────────────────────────────────────────────────────────────┐
│  get_email_context()                                           │
│  - Load defaults from config/email_defaults.json               │
│  - Overlay activity customizations from DB                     │
│  - Set hero_image_url → /activity/{id}/hero-image/{type}       │
│  - Set owner_logo_url → /owner-logo?activity_id={id}           │
└────────────────────────┬───────────────────────────────────────┘
                         │
                         ▼
┌────────────────────────────────────────────────────────────────┐
│  Render Compiled Template                                      │
│  - Use {template}_compiled/index.html                          │
│  - Jinja2 resolves {{ hero_image_url }}, {{ owner_logo_url }}  │
│  - cid:qr_code remains as CID reference                        │
└────────────────────────┬───────────────────────────────────────┘
                         │
                         ▼
┌────────────────────────────────────────────────────────────────┐
│  Send Email (SMTP) — use_hosted_images=True                    │
│  - Subject from context                                        │
│  - HTML body from rendered template                            │
│  - QR code attached as CID (only MIME image attachment)        │
│  - Hero/logo load from hosted URLs when email is opened        │
└────────────────────────────────────────────────────────────────┘
```

### Image Delivery Summary

| Image | Method | Reason |
|-------|--------|--------|
| QR code | CID inline attachment | Functional — must display in all clients |
| Hero image | Hosted URL (`/activity/{id}/hero-image/{type}`) | Decorative — 3-tier priority resolved at fetch time |
| Owner logo | Hosted URL (`/owner-logo?activity_id={id}`) | Decorative — letter fallback if no logo uploaded |

---

## Database Schema & File Storage

### Database: activity Table

**Column:** `email_templates` (JSON, nullable)

**Structure:**
```json
{
  "newPass": {
    "subject": "Your Digital Pass is Ready!",
    "title": "Welcome to Hockey League!",
    "intro_text": "<p>Your digital pass has been created...</p>",
    "conclusion_text": "<p>See you on the ice!</p>",
    "hero_image": "1_newPass_hero.png",
    "activity_logo": "1_owner_logo.png"
  },
  "paymentReceived": {
    "subject": "Payment Confirmed",
    ...
  },
  ...
}
```

**Storage Rules:**
- Only stores CUSTOMIZED values
- Empty/null fields fall back to defaults from `config/email_defaults.json`
- Images stored as filenames (actual files in `static/uploads/`)
- JSON field must be flagged as modified for SQLAlchemy to detect changes

**SQLAlchemy Gotcha:**
```python
# ❌ WRONG - SQLAlchemy won't detect change
activity.email_templates['newPass']['subject'] = 'New Subject'
db.session.commit()  # Nothing happens!

# ✅ CORRECT - Must flag as modified
activity.email_templates['newPass']['subject'] = 'New Subject'
from sqlalchemy.orm.attributes import flag_modified
flag_modified(activity, 'email_templates')
db.session.commit()  # Now it saves!
```

### File System Storage

#### Custom Hero Images (Template-Specific)

**Location:** `static/uploads/{activity_id}_{template_type}_hero.png`

**Examples:**
- `static/uploads/1_newPass_hero.png`
- `static/uploads/1_signup_hero.png`
- `static/uploads/1_survey_invitation_hero.png`

**Lifecycle:**
- Created when user uploads custom hero image
- Deleted when user clicks "Reset to Default"
- Resized to match template dimensions on upload

#### Owner Logo (Shared Across Templates)

**Location:** `static/uploads/{activity_id}_owner_logo.png`

**Example:**
- `static/uploads/1_owner_logo.png`

**Lifecycle:**
- Created when user uploads logo
- Overwrites existing file (no versioning)
- Deleted when resetting `newPass` template (first template with global settings)

#### Default Hero Images (Pristine)

**Location:** `templates/email_templates/{template}_original/inline_images.json`

**Examples:**
- `templates/email_templates/newPass_original/inline_images.json`
- `templates/email_templates/signup_original/inline_images.json`

**Format:** Base64-encoded images in JSON
```json
{
  "hero_new_pass": "iVBORw0KGgoAAAANS...",
  "currency-dollar": "iVBORw0KGgoAAAANS...",
  ...
}
```

**Current role:** Used exclusively by the `/activity/{id}/hero-image/{type}` Flask route for
**Priority 2 fallback** — when no custom hero has been uploaded, the route reads this file and
serves the default hero image. These files are **not** read during email sending; hero images
load from the hosted route URL when the email client opens the message.

---

## Key Code References

### Flask Routes (app.py)

| Route | Line | Function | Purpose |
|-------|------|----------|---------|
| `/activity/<id>/email-templates` | 7667-7713 | `email_template_customization()` | Display customization interface |
| `/activity/<id>/email-templates/save` | 7719-8100 | `save_email_templates()` | Save template customizations |
| `/activity/<id>/email-templates/reset` | 8102-8199 | `reset_email_template()` | Reset template to defaults |
| `/activity/<id>/hero-image/<type>` | 8546-8588 | `get_hero_image()` | Serve hero image (3-tier priority) |
| `/activity/<id>/email-preview-live` | 8262+ | `email_preview_live()` | Live preview with unsaved changes |
| `/activity/<id>/email-test` | 8591+ | `test_email_template()` | Send test email with unsaved changes |

### Utility Functions (utils.py)

| Function | Line | Purpose |
|----------|------|---------|
| `get_activity_hero_image()` | 123-189 | Resolve hero image (3-tier priority) |
| `get_template_default_hero()` | 58-118 | Load pristine default hero from original template |
| `get_email_context()` | 3223-3273 | Merge activity customizations with defaults |
| `resize_hero_image()` | TBD | Resize uploaded hero to template dimensions |
| `send_email()` | 2090+ | Send email with inline images |

### Configuration Files

| File | Purpose |
|------|---------|
| `config/email_defaults.json` | Default text for all templates (subject, title, intro, conclusion, CTA) |
| `templates/email_templates/compileEmailTemplate.py` | Compilation script (convert master → compiled) |

### Template Files

| Location | Purpose |
|----------|---------|
| `templates/email_templates/{template}/` | Master template (developers edit) |
| `templates/email_templates/{template}_compiled/` | Compiled template (app uses) |
| `templates/email_templates/{template}_original/` | Pristine defaults (reset uses) |
| `templates/email_template_customization.html` | Frontend customization UI |

### Upload Files

| Location | Purpose |
|----------|---------|
| `static/uploads/{activity_id}_{template}_hero.png` | Custom hero images (per activity/template) |
| `static/uploads/{activity_id}_owner_logo.png` | Owner logos (per activity, shared across templates) |
| `static/uploads/activity_images/{filename}` | Activity images (fallback hero) |

---

## Appendix: Issues & Troubleshooting

### Known Issues

#### Issue 1: User Confusion About Reset Scope

**Problem:** "Reset to Default" button is ambiguous - users don't know what will be reset

**Recommendation:**
- Add informative tooltip explaining what reset does
- Show preview of default before resetting
- Display warning: "This will remove custom text, images, and restore original template"

#### Issue 2: No Visual Feedback for Hero Image Source

**Problem:** Users can't see the difference between:
- Custom uploaded hero
- Original template default hero
- Activity image fallback

**Recommendation:**
Add visual indicators to show hero image source:
```html
<span v-if="has_custom_hero" class="badge bg-blue">
    <i class="ti ti-upload"></i> Custom Hero
</span>
<span v-else-if="using_activity_image" class="badge bg-yellow">
    <i class="ti ti-photo"></i> Activity Image
</span>
<span v-else class="badge bg-gray">
    <i class="ti ti-template"></i> Default
</span>
```

#### Issue 3: Owner Logo Deletion Tied to newPass Reset

**Problem:** Owner logo is shared across all templates, but deleted only when resetting `newPass`

**Recommendation:**
- Option A: Never auto-delete owner logo (require separate action)
- Option B: Show warning: "This will also reset the organization logo for all templates"
- Option C: Add separate "Reset Logo" button outside individual templates

#### Issue 4: No Undo for Reset

**Problem:** Reset permanently deletes custom content with no backup or recovery option

**Recommendation:**
Add backup before reset:
```python
backup_dir = f"static/uploads/backups/{activity_id}/"
os.makedirs(backup_dir, exist_ok=True)

if os.path.exists(hero_file_path):
    import shutil
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f"{backup_dir}{template_type}_hero_{timestamp}.png"
    shutil.copy2(hero_file_path, backup_path)
    os.remove(hero_file_path)
```

### Security Considerations

#### Current Security Measures ✅

1. **Admin Authentication Required**
   ```python
   if "admin" not in session:
       return redirect(url_for("login"))
   ```

2. **HTML Sanitization**
   ```python
   from utils import ContentSanitizer
   subject = ContentSanitizer.sanitize_html(request.form.get('subject'))
   ```

3. **File Upload Validation**
   - Only accepts image/* mime types
   - Files saved with controlled naming pattern

4. **CSRF Protection**
   ```javascript
   headers: {
       'X-CSRFToken': '{{ csrf_token() }}'
   }
   ```

5. **Path Traversal Prevention**
   ```python
   valid_templates = ['newPass', 'paymentReceived', 'latePayment',
                      'signup', 'redeemPass', 'survey_invitation']
   if template_type not in valid_templates:
       return jsonify({'success': False})
   ```

#### Potential Security Issues ⚠️

1. **No File Size Limits**

**Fix:**
```python
MAX_HERO_SIZE = 5 * 1024 * 1024  # 5MB
if len(hero_file.read()) > MAX_HERO_SIZE:
    return jsonify({'success': False, 'message': 'File too large'})
```

2. **No File Type Validation Beyond MIME**

**Fix:**
```python
from PIL import Image
try:
    img = Image.open(hero_file)
    img.verify()  # Verify it's a real image
except:
    return jsonify({'success': False, 'message': 'Invalid image file'})
```

### Common Troubleshooting

#### Issue: Compilation fails with "File not found"

**Solution:**
- Verify you're in correct directory: `cd /templates/email_templates/`
- Check template folder exists
- Ensure `index.html` exists in master template folder

#### Issue: Images not showing in emails

**Solution:**
- Run compilation script again
- Verify images are in master template folder
- Check image filenames match references in `index.html`
- Ensure `inline_images.json` was created in `_compiled` folder

#### Issue: Changes not reflected in sent emails

**Solution:**
- Verify you compiled templates after making changes
- Check Flask is using `_compiled` folder (not master)
- Restart Flask server if in production mode
- Clear browser cache if testing via web preview

#### Issue: Jinja2 variables not rendering

**Solution:**
- Check variable names match what's available in template context
- Verify syntax: `{{ variable_name }}`
- Review email sending code to ensure variables are passed

#### Issue: Reset doesn't restore original template

**Solution:**
- Verify `{template}_original` folder exists
- Check folder contains `index.html` and `inline_images.json`
- Ensure Flask has write permissions to `_compiled` folder
- Check server logs for error messages

#### Issue: Custom hero not showing after upload

**Solution:**
- Verify file was saved to `static/uploads/{activity_id}_{template}_hero.png`
- Check file permissions (should be readable by Flask)
- Clear browser cache (add cache-busting parameter to image URL)
- Verify `activity.email_templates[template_type]['hero_image']` was saved

---

**End of Guide**

For questions or issues with the email template system:
- Review this guide first
- Check server logs for error messages
- Test each workflow step individually
- Verify file permissions and paths

**Developer Contact:** kdresdell@gmail.com
**Documentation Updates:** Edit this file and commit to repo
