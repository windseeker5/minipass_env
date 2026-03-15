# Minipass Design System Reference

**Version:** 1.1
**Last Updated:** January 31, 2026
**Purpose:** Master template for all page redesigns to ensure consistency

## Table of Contents
1. [Overview](#overview)
2. [Reference Pages](#reference-pages)
3. [Page Title Component](#page-title-component)
4. [Search Bar Component](#search-bar-component)
5. [GitHub-Style Filter Component](#github-style-filter-component)
6. [Table Component](#table-component)
7. [Empty State Component](#empty-state-component)
8. [Flash Message Component](#flash-message-component)
9. [CSS Files to Include](#css-files-to-include)
10. [JavaScript Behavior](#javascript-behavior)
11. [Mobile Responsiveness Rules](#mobile-responsiveness-rules)
12. [Complete Page Template](#complete-page-template)
13. [Form Action Buttons](#form-action-buttons)
14. [Pagination Component](#pagination-component)
15. [Photo Normalization Tool](#section-15--photo-normalization-tool)
16. [Organization Avatar with Success Badge](#section-16--organization-avatar-with-success-badge)

---

## Overview

This document defines the standard UI patterns used throughout Minipass. The **Activity Dashboard** (`templates/activity_dashboard.html`) and **Passports** page serve as the reference implementations.

### When to Use This Document
- When converting any existing page to the new design
- When creating new list/table pages
- When implementing search functionality
- When adding filter buttons to tables

### Key Principles
- **Consistency:** All pages should look and behave the same way
- **Mobile-First:** Always test on mobile (375px width)
- **No Hover Effects on Tables:** Per project constraints
- **Plain White Cards:** No gradients or fancy effects

---

## Backend Data Requirements

**CRITICAL:** The backend must pass specific data structures to the template for filter counts to work correctly.

### Required: `statistics` Dictionary

The backend route MUST calculate and pass a `statistics` dict containing TOTAL counts from the database (NOT filtered page results).

```python
# Example from list_passports() in app.py (lines 3728-3743)
# Query ALL items from database first
all_passports = Passport.query.all()
all_passports_count = Passport.query.count()

# Calculate statistics using ALL items (not filtered results)
paid_passports = len([p for p in all_passports if p.paid])
unpaid_passports = len([p for p in all_passports if not p.paid])
active_passports = len([p for p in all_passports if p.uses_remaining > 0 or not p.paid])

# Create statistics dict
statistics = {
    'total_passports': all_passports_count,
    'paid_passports': paid_passports,
    'unpaid_passports': unpaid_passports,
    'active_passports': active_passports,
}

# Pass to template
return render_template("passports.html",
                     passports=filtered_passports,  # Filtered results for display
                     statistics=statistics,          # Total counts for filter buttons
                     current_filters={...})
```

### For Activities Page:

```python
# Example structure for activities
all_activities = Activity.query.all()

statistics = {
    'total_activities': len(all_activities),
    'active_activities': len([a for a in all_activities if a.status == 'active']),
    'inactive_activities': len([a for a in all_activities if a.status == 'inactive']),
    'draft_activities': len([a for a in all_activities if a.status == 'draft'])
}
```

### Why This Matters:

**WRONG:** Using filtered page results for counts
```jinja
<!-- This will show different counts depending on current filter - WRONG! -->
<span>({{ activities|selectattr('status', 'equalto', 'active')|list|length }})</span>
```

**CORRECT:** Using backend statistics
```jinja
<!-- This always shows total count from database - CORRECT! -->
<span>({{ statistics.active_activities }})</span>
```

### Required: `current_filters` Dictionary

Must pass current filter state to template:

```python
current_filters = {
    'q': search_query,           # Search term
    'status': status_filter,     # Current status filter
    'show_all': show_all_param   # Whether "All" is selected
}
```

---

## Reference Pages

### Master Templates (Copy These)
1. **Activity Dashboard:** `templates/activity_dashboard.html` (lines 1071-1220)
   - Search bar implementation
   - GitHub filter buttons
   - Responsive table layout

2. **Passports Page:** `templates/passports.html`
   - Another perfect implementation
   - Same patterns and styles

### What Makes These Perfect
- Clean, consistent styling
- Perfect mobile responsiveness
- GitHub-style embedded filters
- Enhanced search with Ctrl+K shortcut
- Keyboard hints that hide on mobile
- Proper table column hiding on smaller screens

---

## Page Title Component

### Visual Example
```
🔴 Activity Passport
```

### HTML Structure
```html
<h2 class="mt-4 mb-3">
  <i class="ti ti-activity-heartbeat me-2" style="color: #e03131;"></i>Activity Passport
</h2>
```

### Rules
- Use `<h2>` for page section titles
- Include a Tabler icon with `me-2` margin
- Color the icon (common: `#e03131` red, `#206bc4` blue)
- Keep title concise (2-3 words max)
- **Remove possessive words like "Your"** - use "Activity Passport" not "Your Activity Passport"

### Common Icons
- `ti-activity-heartbeat` - Activities, Passports
- `ti-user-check` - Signups
- `ti-clipboard-check` - Surveys
- `ti-chart-bar` - Reports
- `ti-list` - General lists

---

## Search Bar Component

### Visual Features
- Large rounded search input
- Search icon on the left
- **Ctrl+K keyboard hint on desktop (hidden on mobile)**
- Character counter (shows when typing)
- Clear button (×) when there's text
- Pink glow effect when Ctrl+K is pressed
- Blue pulse animation while searching

### HTML Structure
```html
<!-- Enhanced Dynamic Search -->
<form method="GET" action="{{ url_for('your_route_name') }}" class="mb-4" id="dynamicSearchForm">
  <div class="input-icon position-relative">
    <span class="input-icon-addon">
      <i class="ti ti-search fs-3"></i>
    </span>
    <input type="text"
           name="q"
           id="enhancedSearchInput"
           class="form-control form-control-lg shadow-sm"
           placeholder="Start typing to search"
           value="{{ request.args.get('q', '') }}"
           style="padding-right: 100px; border-radius: 0.5rem;"
           autocomplete="off"
           data-bs-toggle="false">
    <div class="position-absolute end-0 top-50 translate-middle-y me-3 d-flex align-items-center gap-2">
      <small id="searchCharCounter" class="text-muted" style="font-size: 0.75rem; display: none;"></small>
      <!-- IMPORTANT: Keyboard hints hidden on mobile with d-none d-md-inline -->
      <kbd id="searchKbdHint" class="text-muted d-none d-md-inline">Ctrl</kbd>
      <kbd class="text-muted d-none d-md-inline">K</kbd>
      <button id="searchClearBtn" type="button" class="btn btn-link p-0 border-0" style="display: none; width: 24px; height: 24px;" aria-label="Clear search">
        <i class="ti ti-x" style="font-size: 18px; color: #6c757d;"></i>
      </button>
    </div>
  </div>
</form>
```

### Critical Details
- **Keyboard hints:** Use `d-none d-md-inline` to hide on mobile
- **Form control:** Must have `form-control-lg` for proper size
- **Border radius:** `border-radius: 0.5rem` for rounded corners
- **Padding right:** `padding-right: 100px` to make room for controls
- **IDs must match:** `enhancedSearchInput`, `searchCharCounter`, `searchKbdHint`, `searchClearBtn`

### JavaScript Requirements
- Must implement Ctrl+K keyboard shortcut
- Character counter updates as you type
- Clear button appears/disappears dynamically
- Pink glow effect on Ctrl+K press
- Blue pulse while AJAX search is running

---

## GitHub-Style Filter Component

### Visual Features
- Light gray background (#f6f8fa)
- Rounded container (6px border-radius)
- Buttons side-by-side with subtle dividers
- Active button: white background with border
- Inactive buttons: gray background
- Hover effect: darker gray
- Icons with labels and counts

### EXACT HTML Structure from Passports Page

**IMPORTANT:** Use this EXACT HTML including all inline styles. Do NOT simplify or use CSS classes alone.

```html
<!-- Main Table -->
<div class="card main-table-card" style="margin-top: 1.5rem !important;">
  <div class="card-header">
    <div class="d-flex justify-content-center align-items-center w-100">
      <!-- Filter Buttons -->
      <div class="github-filter-group" role="group" aria-label="Filter buttons" style="display: inline-flex; align-items: center; background: #f6f8fa; border: 1px solid #d1d5da; border-radius: 6px; padding: 0;">
        <a href="{{ url_for('list_passports', status='active') }}"
           class="github-filter-btn {% if current_filters.status == 'active' and not current_filters.show_all %}active{% endif %}"
           style="{% if current_filters.status == 'active' and not current_filters.show_all %}background: #ffffff; color: #24292e; font-weight: 600; border: 1px solid #d1d5da; margin: -1px; z-index: 1; border-radius: 6px; box-shadow: 0 1px 0 rgba(27,31,35,0.04);{% else %}background: rgba(0, 0, 0, 0.03); color: #586069; margin: 0; border-right: 1px solid transparent; background-clip: padding-box; background-image: linear-gradient(to right, transparent 0%, transparent 100%), linear-gradient(180deg, transparent 20%, #d1d5da 20%, #d1d5da 80%, transparent 80%); background-size: 100% 100%, 1px 100%; background-position: center, right center; background-repeat: no-repeat;{% endif %} padding: 5px 12px; font-size: 14px; line-height: 20px; text-decoration: none; display: inline-flex; align-items: center; white-space: nowrap; position: relative;">
          Active <span style="opacity: 0.6; margin-left: 4px;">({{ statistics.active_passports|default(0) }})</span>
        </a>
        <a href="{{ url_for('list_passports', payment_status='unpaid') }}"
           class="github-filter-btn {% if current_filters.payment_status == 'unpaid' %}active{% endif %}"
           style="{% if current_filters.payment_status == 'unpaid' %}background: #ffffff; color: #24292e; font-weight: 600; border: 1px solid #d1d5da; margin: -1px; z-index: 1; border-radius: 6px; box-shadow: 0 1px 0 rgba(27,31,35,0.04);{% else %}background: rgba(0, 0, 0, 0.03); color: #586069; margin: 0; border-right: 1px solid transparent; background-clip: padding-box; background-image: linear-gradient(to right, transparent 0%, transparent 100%), linear-gradient(180deg, transparent 20%, #d1d5da 20%, #d1d5da 80%, transparent 80%); background-size: 100% 100%, 1px 100%; background-position: center, right center; background-repeat: no-repeat;{% endif %} padding: 5px 12px; font-size: 14px; line-height: 20px; text-decoration: none; display: inline-flex; align-items: center; white-space: nowrap; position: relative;">
          Unpaid <span style="opacity: 0.6; margin-left: 4px;">({{ statistics.unpaid_passports|default(0) }})</span>
        </a>
        <a href="{{ url_for('list_passports', show_all='true') }}"
           class="github-filter-btn {% if current_filters.show_all %}active{% endif %}"
           style="{% if current_filters.show_all %}background: #ffffff; color: #24292e; font-weight: 600; border: 1px solid #d1d5da; margin: -1px; z-index: 1; border-radius: 6px; box-shadow: 0 1px 0 rgba(27,31,35,0.04);{% else %}background: rgba(0, 0, 0, 0.03); color: #586069; margin: 0; border-right: 1px solid transparent; background-clip: padding-box; background-image: linear-gradient(to right, transparent 0%, transparent 100%), linear-gradient(180deg, transparent 20%, #d1d5da 20%, #d1d5da 80%, transparent 80%); background-size: 100% 100%, 1px 100%; background-position: center, right center; background-repeat: no-repeat;{% endif %} padding: 5px 12px; font-size: 14px; line-height: 20px; text-decoration: none; display: inline-flex; align-items: center; white-space: nowrap; position: relative;">
          All <span style="opacity: 0.6; margin-left: 4px;">({{ statistics.total_passports|default(0) }})</span>
        </a>
      </div>
    </div>
  </div>
  <div class="table-responsive">
    <!-- Table goes here -->
  </div>
</div>
```

### Filter Active State Logic

**CRITICAL:** The conditional logic determines which filter has the white background (active state).

#### Pattern for Each Filter:

**First Filter (Active):**
```jinja
{% if current_filters.status == 'active' and not current_filters.show_all %}active{% endif %}
```
- Active when `status='active'` parameter AND NOT showing all
- This is usually the default when no parameters are set

**Second Filter (by category, e.g., Unpaid):**
```jinja
{% if current_filters.payment_status == 'unpaid' %}active{% endif %}
```
- Active when specific parameter is set

**Third Filter (All):**
```jinja
{% if current_filters.show_all %}active{% endif %}
```
- Active when `show_all='true'` parameter is set
- Links to base URL with `show_all='true'`

#### Common Mistake:
**WRONG:** Setting "All" active when there's no status
```jinja
{% if not current_filters.status %}active{% endif %}  <!-- This makes All and Active both active! -->
```

**CORRECT:** Using explicit `show_all` parameter
```jinja
{% if current_filters.show_all %}active{% endif %}
```

---

### ⚠️ CRITICAL WARNING: DO NOT MODIFY CONDITIONAL LOGIC

**This is where bugs happen. Read this carefully.**

#### Common Mistake That Causes Bugs

Developers often try to "simplify" or "improve" the filter conditionals by using logic like:

```jinja
<!-- WRONG - DON'T DO THIS -->
{% if current_filters.status == 'active' or not current_filters.status %}active{% endif %}
```

This seems logical at first: "show Active if status is 'active' OR if no status is set".

**BUT IT CREATES A CRITICAL BUG:**

1. When user clicks "All", the URL is `/activities?show_all=true`
2. This means `current_filters.status` is empty/None (no status parameter)
3. So BOTH "Active" (because of `not current_filters.status` being true) AND "All" (because of `show_all=true`) will have white backgrounds simultaneously!

#### Why The Design System Pattern Works

The passport page backend (app.py lines 3673-3674) sets a DEFAULT status:

```python
if not status and not payment_status and show_all_param != "true":
    status = "active"
```

This means:
- When you load `/activities` with NO parameters, backend sets `status='active'` automatically
- When you load `/activities?show_all=true`, backend does NOT set a default (show_all is true)
- So you DON'T need `or not current_filters.status` logic in the template

**THE RULE:**

✅ **DO:** Copy the exact conditionals from the design system
❌ **DON'T:** Try to simplify or improve them
❌ **DON'T:** Use `or not current_filters.status` logic
❌ **DON'T:** Think you know better than the pattern

**When in doubt:** Copy-paste from `templates/passports.html` directly.

---

### Filter Count Source

**CRITICAL:** Counts MUST come from `statistics` dict passed by backend.

```jinja
<!-- CORRECT - uses backend statistics -->
<span style="opacity: 0.6; margin-left: 4px;">({{ statistics.active_passports|default(0) }})</span>

<!-- WRONG - uses filtered page results -->
<span>({{ passports|selectattr('paid', 'equalto', true)|list|length }})</span>
```

### Styling Rules
- **DO NOT** simplify the inline styles - copy them exactly
- All the complex inline styles are REQUIRED for proper GitHub appearance
- Active button styling comes from the conditional inline styles
- Inactive buttons use the gradient divider technique in inline styles

---

## Search Component JavaScript Requirements

### Complete Implementation

The search component requires JavaScript for these features:
1. **Ctrl+K keyboard shortcut** to focus search
2. **Character counter** showing typed characters
3. **Clear (X) button** visibility logic
4. **Auto-search debounce** (500ms delay after typing stops)
5. **Mobile keyboard hint hiding** when focused

### Full JavaScript Code (from passports.html lines 324-361)

```javascript
document.addEventListener('DOMContentLoaded', function() {
    // Initialize search component
    if (window.SearchComponent) {
        window.SearchComponent.init({
            formId: 'dynamicSearchForm',
            inputId: 'enhancedSearchInput',
            preserveParams: ['payment_status', 'status'] // Adjust based on your page
        });
    }

    // Initialize filter component
    if (window.FilterComponent) {
        window.FilterComponent.init({
            filterClass: 'github-filter-btn',
            mode: 'server',
            preserveScrollPosition: true,
            enableSearchPreservation: true
        });
    }

    // Validation for debugging
    console.log('🎫 Page loaded');
    console.log('🔧 Global dropdown fix available:', typeof window.dropdownFix !== 'undefined');
    console.log('📊 Bootstrap available:', typeof bootstrap !== 'undefined');
    console.log('🔍 Dropdown toggles found:', document.querySelectorAll('[data-bs-toggle="dropdown"]').length);

    // Debug: Check if Bootstrap is properly loaded
    if (typeof bootstrap === 'undefined') {
        console.error('Bootstrap is not loaded! Dropdown functionality may not work.');
    } else {
        console.log('Bootstrap is loaded. Dropdown functionality should work.');
    }
});
```

### Search Component Features Breakdown

**SearchComponent.init()** handles:
- **Ctrl+K shortcut**: Focuses search input when Ctrl+K is pressed
- **Character counter**: Shows "X chars" in gray text while typing
- **Clear button**: Shows when length > 0, hides when empty
- **Auto-search**: Submits form 500ms after typing stops (if length >= 3 or === 0)
- **Keyboard hint hiding**: Hides "Ctrl K" badges when focused

**FilterComponent.init()** handles:
- **Server-side filtering**: Links submit to backend routes
- **Scroll position preservation**: Maintains scroll after filter change
- **Search preservation**: Keeps search query when switching filters

### Required HTML Elements

For the JavaScript to work, your search HTML must have these IDs:

```html
<form method="GET" action="{{ url_for('your_list_route') }}" class="mb-4" id="dynamicSearchForm">
  <div class="input-icon position-relative">
    <span class="input-icon-addon">
      <i class="ti ti-search fs-3"></i>
    </span>
    <input type="text"
           name="q"
           id="enhancedSearchInput"
           class="form-control form-control-lg shadow-sm"
           placeholder="Start typing to search"
           value="{{ current_filters.q or '' }}"
           style="padding-right: 100px; border-radius: 0.5rem;"
           autocomplete="off"
           data-bs-toggle="false">
    <div class="position-absolute end-0 top-50 translate-middle-y me-3 d-flex align-items-center gap-2">
      <small id="searchCharCounter" class="text-muted" style="font-size: 0.75rem; display: none;"></small>
      <kbd id="searchKbdHint" class="text-muted d-none d-md-inline">Ctrl</kbd>
      <kbd class="text-muted d-none d-md-inline">K</kbd>
      <button id="searchClearBtn" type="button" class="btn btn-link p-0 border-0" style="display: none; width: 24px; height: 24px;" aria-label="Clear search">
        <i class="ti ti-x" style="font-size: 18px; color: #6c757d;"></i>
      </button>
    </div>
  </div>
</form>
```

### Critical IDs Required:
- `id="dynamicSearchForm"` - Form element for auto-submission
- `id="enhancedSearchInput"` - Input field for all event listeners
- `id="searchCharCounter"` - Character counter display
- `id="searchKbdHint"` - Keyboard hint (first kbd element)
- `id="searchClearBtn"` - Clear button that appears when typing

### Required CSS Files:
```html
<link rel="stylesheet" href="{{ url_for('static', filename='css/search-component.css') }}?v=1.0">
```

This CSS file contains the SearchComponent global object and all related styles.

---

## 🚨 CRITICAL: Search + Filter Integration

**IMPORTANT:** This section documents the CORRECT way to implement search combined with filters. The Activity Dashboard bug (November 2025) was caused by not following this pattern.

### The Correct Pattern: Server-Side Filtering ONLY

**✅ DO THIS:**
- Filter buttons are `<a href="{{ url_for(...) }}">` links (server-side navigation)
- Search form submits to server (GET request)
- SearchComponent preserves filter params when searching
- FilterComponent uses `mode: 'server'`
- Backend calculates statistics from ALL records
- Backend provides default filter

**❌ NEVER DO THIS:**
- Filter buttons with `onclick="filterFunction()"` (AJAX)
- Hybrid AJAX + server-side approaches
- Client-side filtering with JavaScript
- Calculating filter counts from filtered page results

### Why Server-Side Only?

**The Bug We Fixed (November 2025):**
Activity Dashboard used hybrid AJAX filtering:
- Search form → server-side (form submit)
- Filter buttons → client-side (JavaScript onclick)
- Result: Search didn't preserve filter state
- User searched "cay" → saw 3 results instead of 1

**After Fix:**
- Both search and filters → server-side
- Search preserves filter in URL params
- Filters show correct counts
- Results are always accurate

### Complete Implementation Guide

#### Step 1: Backend Route Setup

```python
@app.route('/your-page')
def your_list_page():
    # 1. Get filter and search parameters
    filter_param = request.args.get('filter', '')
    show_all_param = request.args.get('show_all', '')
    q = request.args.get('q', '').strip()

    # 2. Default to 'active' filter if no filter specified (unless showing all)
    if not filter_param and show_all_param != "true":
        filter_param = "active"

    # 3. Query ALL records first (for statistics)
    all_items = YourModel.query.all()

    # 4. Build filtered query
    query = YourModel.query

    # 5. Apply filter
    if filter_param == 'active':
        query = query.filter(
            db.or_(
                YourModel.uses_remaining > 0,
                YourModel.paid == False
            )
        )
    elif filter_param == 'unpaid':
        query = query.filter_by(paid=False)
    elif filter_param == 'paid':
        query = query.filter_by(paid=True)
    # else: show_all == "true" - no filter

    # 6. Apply search
    if q:
        from models import User
        query = query.join(User).filter(
            db.or_(
                User.name.ilike(f"%{q}%"),
                User.email.ilike(f"%{q}%"),
                YourModel.code.ilike(f"%{q}%")
            )
        )

    # 7. Get filtered results
    filtered_items = query.order_by(YourModel.created_dt.desc()).all()

    # 8. Calculate statistics from ALL items (NOT filtered)
    total_count = len(all_items)
    active_count = len([i for i in all_items if i.uses_remaining > 0 or not i.paid])
    unpaid_count = len([i for i in all_items if not i.paid])

    statistics = {
        'total_items': total_count,
        'active_items': active_count,
        'unpaid_items': unpaid_count,
    }

    # 9. Determine show_all state
    show_all = show_all_param == "true"

    # 10. Pass to template
    return render_template("your_page.html",
                         items=filtered_items,
                         statistics=statistics,
                         current_filters={
                             'q': q,
                             'filter': filter_param,
                             'show_all': show_all
                         })
```

#### Step 2: Frontend Filter Buttons

**CRITICAL:** Use EXACT HTML from Passports page - do NOT simplify!

```html
<div class="github-filter-group" role="group" aria-label="Filter buttons" style="display: inline-flex; align-items: center; background: #f6f8fa; border: 1px solid #d1d5da; border-radius: 6px; padding: 0;">
  <!-- Active Filter -->
  <a href="{{ url_for('your_list_page', filter='active') }}"
     class="github-filter-btn {% if current_filters.filter == 'active' and not current_filters.show_all %}active{% endif %}"
     style="{% if current_filters.filter == 'active' and not current_filters.show_all %}background: #ffffff; color: #24292e; font-weight: 600; border: 1px solid #d1d5da; margin: -1px; z-index: 1; border-radius: 6px; box-shadow: 0 1px 0 rgba(27,31,35,0.04);{% else %}background: rgba(0, 0, 0, 0.03); color: #586069; margin: 0; border-right: 1px solid transparent; background-clip: padding-box; background-image: linear-gradient(to right, transparent 0%, transparent 100%), linear-gradient(180deg, transparent 20%, #d1d5da 20%, #d1d5da 80%, transparent 80%); background-size: 100% 100%, 1px 100%; background-position: center, right center; background-repeat: no-repeat;{% endif %} padding: 5px 12px; font-size: 14px; line-height: 20px; text-decoration: none; display: inline-flex; align-items: center; white-space: nowrap; position: relative;">
    Active <span style="opacity: 0.6; margin-left: 4px;">({{ statistics.active_items|default(0) }})</span>
  </a>

  <!-- Unpaid Filter -->
  <a href="{{ url_for('your_list_page', filter='unpaid') }}"
     class="github-filter-btn {% if current_filters.filter == 'unpaid' %}active{% endif %}"
     style="{% if current_filters.filter == 'unpaid' %}background: #ffffff; color: #24292e; font-weight: 600; border: 1px solid #d1d5da; margin: -1px; z-index: 1; border-radius: 6px; box-shadow: 0 1px 0 rgba(27,31,35,0.04);{% else %}background: rgba(0, 0, 0, 0.03); color: #586069; margin: 0; border-right: 1px solid transparent; background-clip: padding-box; background-image: linear-gradient(to right, transparent 0%, transparent 100%), linear-gradient(180deg, transparent 20%, #d1d5da 20%, #d1d5da 80%, transparent 80%); background-size: 100% 100%, 1px 100%; background-position: center, right center; background-repeat: no-repeat;{% endif %} padding: 5px 12px; font-size: 14px; line-height: 20px; text-decoration: none; display: inline-flex; align-items: center; white-space: nowrap; position: relative;">
    Unpaid <span style="opacity: 0.6; margin-left: 4px;">({{ statistics.unpaid_items|default(0) }})</span>
  </a>

  <!-- All Filter -->
  <a href="{{ url_for('your_list_page', show_all='true') }}"
     class="github-filter-btn {% if current_filters.show_all %}active{% endif %}"
     style="{% if current_filters.show_all %}background: #ffffff; color: #24292e; font-weight: 600; border: 1px solid #d1d5da; margin: -1px; z-index: 1; border-radius: 6px; box-shadow: 0 1px 0 rgba(27,31,35,0.04);{% else %}background: rgba(0, 0, 0, 0.03); color: #586069; margin: 0; border-right: 1px solid transparent; background-clip: padding-box; background-image: linear-gradient(to right, transparent 0%, transparent 100%), linear-gradient(180deg, transparent 20%, #d1d5da 20%, #d1d5da 80%, transparent 80%); background-size: 100% 100%, 1px 100%; background-position: center, right center; background-repeat: no-repeat;{% endif %} padding: 5px 12px; font-size: 14px; line-height: 20px; text-decoration: none; display: inline-flex; align-items: center; white-space: nowrap; position: relative;">
    All <span style="opacity: 0.6; margin-left: 4px;">({{ statistics.total_items|default(0) }})</span>
  </a>
</div>
```

#### Step 3: JavaScript Initialization

```javascript
document.addEventListener('DOMContentLoaded', function() {
    // Initialize search component with filter preservation
    if (window.SearchComponent) {
        window.SearchComponent.init({
            formId: 'dynamicSearchForm',
            inputId: 'enhancedSearchInput',
            preserveParams: ['filter']  // ← Preserves filter when searching
        });
    }

    // Initialize filter component for server-side filtering
    if (window.FilterComponent) {
        window.FilterComponent.init({
            filterClass: 'github-filter-btn',
            mode: 'server',  // ← CRITICAL: Must be 'server'
            preserveScrollPosition: true,
            enableSearchPreservation: true  // ← Known limitation: doesn't work yet
        });
    }
});
```

### Known Limitations

1. **Search Preservation**: Search query is cleared when clicking filter buttons
   - **Workaround**: User must retype search after changing filter
   - **Future Enhancement**: Will be fixed in future update
   - **Impact**: Minor UX inconvenience, doesn't affect functionality

### Troubleshooting: Wrong Search Results

**Symptom:**
User searches "cay" and sees 3 results when only 1 active passport exists.

**Root Cause:**
One of these issues:
1. Filter buttons using `onclick` instead of `href`
2. Backend defaulting to wrong filter ('all' instead of 'active')
3. Backend filter logic is incorrect
4. Filter counts calculated from filtered results instead of ALL records

**How to Fix:**
1. Check filter buttons: Must be `<a href="{{ url_for(...) }}">` NOT `onclick`
2. Check backend default: Must default to 'active' not 'all'
3. Check filter logic: Active should be `(uses_remaining > 0 OR paid == False)`
4. Check statistics: Must calculate from `all_items` not `filtered_items`

**Example of Wrong Implementation:**
```python
# ❌ WRONG - defaults to 'all' and applies filter
filter_param = request.args.get('filter', 'all')
if filter_param == 'all':
    query = query.filter(db.or_(...))  # This is NOT showing all!
```

**Correct Implementation:**
```python
# ✅ CORRECT - defaults to 'active', 'all' shows truly all
filter_param = request.args.get('filter', '')
show_all = request.args.get('show_all', '')
if not filter_param and show_all != "true":
    filter_param = "active"

if filter_param == 'active':
    query = query.filter(db.or_(...))
# No else clause - when show_all='true', no filter applied
```

### Testing Checklist

After implementing search + filters, verify:
- [ ] Load page → "Active" filter is selected by default
- [ ] Search "cay" → Shows correct number of active results
- [ ] Click "Unpaid" → URL changes to `?filter=unpaid`
- [ ] Results update to show only unpaid items
- [ ] Filter counts remain static (don't change based on search)
- [ ] Click "All" → URL changes to `?show_all=true`
- [ ] Shows all records
- [ ] Browser back button works correctly
- [ ] No JavaScript errors in console

---

## Table Component

### Desktop vs Mobile Behavior

**Desktop (≥768px):**
- All columns visible
- User avatar on left
- Full user email shown
- Dropdown shows "Actions" text

**Mobile (<768px):**
- Columns hide using `d-none d-md-table-cell`
- User column shows only name
- Activity logo replaces user avatar
- Uses remaining column shows as single number
- Dropdown shows icon only

### HTML Structure
```html
<div class="table-responsive">
  <table class="table table-hover">
    <thead>
      <tr>
        <th>User</th>
        <!-- Mobile: Shows # column -->
        <th class="d-md-none text-center">#</th>
        <!-- Desktop columns (hidden on mobile) -->
        <th class="d-none d-md-table-cell">Activity</th>
        <th class="d-none d-lg-table-cell">Passport Type</th>
        <th class="d-none d-md-table-cell text-center">Amount</th>
        <th class="d-none d-lg-table-cell text-center">Status</th>
        <th class="d-none d-md-table-cell text-center">Uses Remaining</th>
        <th class="d-none d-md-table-cell">Created</th>
        <th class="text-center">Actions</th>
      </tr>
    </thead>
    <tbody>
      {% for item in items %}
      <tr>
        <!-- User Column: Always visible -->
        <td style="vertical-align: middle;">
          <div class="d-flex align-items-center">
            <!-- Desktop: User Gravatar -->
            <img src="..." class="rounded-circle me-3 user-avatar d-none d-md-block" alt="Avatar">
            <!-- Mobile: Activity Logo -->
            <img src="..." class="rounded-circle me-3 user-avatar d-md-none" alt="Activity">
            <div>
              <div class="fw-bold">{{ user.name }}</div>
              <!-- Email only on desktop -->
              <div class="text-muted small d-none d-md-block">{{ user.email }}</div>
            </div>
          </div>
        </td>

        <!-- Mobile: Uses/Count Column -->
        <td class="d-md-none text-center" style="vertical-align: middle;">
          <span class="fw-bold" style="color: #6c757d;">{{ count }}</span>
        </td>

        <!-- Desktop: Full Details -->
        <td class="d-none d-md-table-cell" style="vertical-align: middle;">...</td>

        <!-- Actions Column: Always visible -->
        <td class="text-center" style="vertical-align: middle;">
          <div class="dropdown d-inline-block">
            <a href="#" class="btn btn-outline-secondary dropdown-toggle" data-bs-toggle="dropdown">
              <!-- Desktop: Show text -->
              <span class="d-none d-md-inline">Actions</span>
              <!-- Mobile: Show icon -->
              <i class="ti ti-menu-2 d-md-none"></i>
            </a>
            <div class="dropdown-menu dropdown-menu-end">
              <!-- Dropdown items -->
            </div>
          </div>
        </td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
</div>
```

### Column Visibility Classes

| Class | Behavior |
|-------|----------|
| No class | Always visible |
| `d-none d-md-table-cell` | Hidden on mobile, visible on tablet+ |
| `d-none d-lg-table-cell` | Hidden until large screens |
| `d-md-none` | Visible only on mobile |

### Table Styling Rules
- **NO hover effects:** Per CLAUDE.md constraints
- **Plain white cards:** `background-color: #fff !important;`
- **Vertical align:** All cells use `style="vertical-align: middle;"`
- **Text alignment:** Center numerical data, left-align text

### Badge Styling
```html
<!-- Paid -->
<span class="badge bg-green-lt text-green-lt-fg">Paid</span>

<!-- Unpaid -->
<span class="badge bg-yellow-lt text-yellow-lt-fg">Unpaid</span>

<!-- Active -->
<span class="badge bg-blue-lt text-blue-lt-fg">Active</span>
```

---

## Avatar Styling Rules

### User Avatars vs Activity Avatars

**CRITICAL DISTINCTION:**
- **User avatars**: Always circular (`rounded-circle`)
- **Activity avatars**: Always square with rounded corners (`rounded`)

This distinction helps users instantly understand the visual hierarchy:
- **Circular = Person** (user identity)
- **Square = Brand** (activity/organization identity)

### Desktop View (≥768px)
- Show user gravatar avatars
- Always use `rounded-circle` class
- Standard size: 40px × 40px

### Mobile View (<768px)
- Show activity logo/image instead of user avatar
- Always use `rounded` class (NOT `rounded-circle`)
- Standard size: 30px × 30px
- Use `object-fit: cover` to maintain aspect ratio

### HTML Pattern for Tables

```html
<td style="vertical-align: middle;">
  <div class="d-flex align-items-center">
    <!-- Desktop: User Gravatar (circular) -->
    <img src="https://www.gravatar.com/avatar/..."
         class="rounded-circle me-3 user-avatar d-none d-md-block"
         alt="Avatar">

    <!-- Mobile: Activity Logo (square with rounded corners) -->
    {% if activity.logo_filename %}
      <img src="{{ url_for('static', filename='uploads/activity_images/' + activity.logo_filename) }}"
           class="rounded me-3 user-avatar d-md-none"
           alt="{{ activity.name }}"
           style="width: 30px; height: 30px; object-fit: cover;">
    {% else %}
      <!-- Fallback: Activity initial in square container -->
      <div class="rounded me-3 d-md-none bg-light d-flex align-items-center justify-content-center"
           style="width: 30px; height: 30px; font-size: 10px; color: #6c757d;">
        {{ activity.name[0] if activity and activity.name else 'A' }}
      </div>
    {% endif %}

    <div>
      <div class="fw-bold">{{ user.name }}</div>
      <div class="text-muted small d-none d-md-block">{{ user.email }}</div>
    </div>
  </div>
</td>
```

### Why This Matters

1. **Universal Standards**: Circular avatars are the web standard for people, square logos are standard for brands
2. **Instant Recognition**: Users can immediately distinguish personal vs organizational context
3. **Visual Consistency**: Matches the passport card design where activity logos are square
4. **Design System Coherence**: Maintains consistency with other Minipass UI elements

### Reference Implementation

See `templates/passports.html` (lines 100-111) and `templates/signups.html` (lines 91-102) for complete working examples.

---

## Empty State Component

### Overview

Empty states (also called "zero states" or "blank states") are the UI shown when a table or list has no data to display. **Never leave tables completely empty** - always provide clear guidance and next actions for users.

### When to Use Empty States

Empty states appear in two distinct scenarios:

| Scenario | When It Occurs | User Needs |
|----------|----------------|------------|
| **First-Time Empty** | User hasn't created any data yet in the database | Guidance on how to create first item |
| **Zero Results** | Search or filter returned no matches | Ability to clear filters or adjust search |

### Reference Implementation

**MASTER TEMPLATE:** The Surveys page (`templates/surveys.html`) demonstrates the perfect empty state pattern. Use this as your reference when implementing empty states on other pages.

---

### Visual Structure

Empty states consist of three core components arranged vertically in a centered container:

```
┌─────────────────────────────────────────┐
│                                         │
│              [ICON]                     │  ← Tabler icon, 48px, colored
│                                         │
│        Primary Message                  │  ← Bold, 18px
│     Secondary explanation text          │  ← Regular, 14px, muted
│                                         │
│          [Action Link/Button]           │  ← Context-specific CTA
│                                         │
└─────────────────────────────────────────┘
```

---

### HTML Structure

#### First-Time Empty State Template

Use this when the database table is completely empty (no records exist):

```html
<div class="empty-state-container text-center py-5">
  <!-- Icon -->
  <div class="empty-state-icon mb-3">
    <i class="ti ti-{icon-name}" style="font-size: 48px; color: {icon-color};"></i>
  </div>

  <!-- Primary Message -->
  <h3 class="empty-state-title mb-2">No {items} yet</h3>

  <!-- Secondary Explanation -->
  <p class="empty-state-description text-muted mb-3">
    {Explain what this section does and when data will appear here}
  </p>

  <!-- Optional: Create Action Button (only if user can create items) -->
  <a href="{{ url_for('create_{item}') }}" class="btn btn-primary">
    <i class="ti ti-plus me-1"></i>Create {Item}
  </a>
</div>
```

#### Zero Results Empty State Template

Use this when search or filters return no matches (but data exists in database):

```html
<div class="empty-state-container text-center py-5">
  <!-- Icon -->
  <div class="empty-state-icon mb-3">
    <i class="ti ti-search" style="font-size: 48px; color: #6c757d;"></i>
  </div>

  <!-- Primary Message -->
  <h3 class="empty-state-title mb-2">No {items} match your filters</h3>

  <!-- Secondary Explanation -->
  <p class="empty-state-description text-muted mb-3">
    Try adjusting your search or filter criteria to find what you're looking for.
  </p>

  <!-- Clear Filters Link -->
  <a href="{{ url_for('list_{items}', show_all='true') }}" class="btn btn-link">
    Clear all filters
  </a>
</div>
```

---

### CSS Styling

Add these styles to `static/minipass.css`:

```css
/* Empty State Styles */
.empty-state-container {
  min-height: 300px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem 1rem;
}

.empty-state-icon {
  opacity: 0.6;
}

.empty-state-title {
  color: #1e293b;
  font-weight: 600;
  font-size: 18px;
  margin-bottom: 0.5rem;
}

.empty-state-description {
  color: #64748b;
  font-size: 14px;
  max-width: 400px;
  line-height: 1.5;
  margin-left: auto;
  margin-right: auto;
}

/* Mobile responsiveness */
@media (max-width: 768px) {
  .empty-state-container {
    padding: 2rem 1rem;
  }

  .empty-state-icon i {
    font-size: 36px !important;
  }

  .empty-state-title {
    font-size: 16px;
  }

  .empty-state-description {
    font-size: 13px;
  }
}
```

---

### Backend Requirements

The backend route must distinguish between "first-time empty" and "zero results" by passing flags to the template:

```python
@app.route("/your-list-page")
def list_items():
    # ... existing query and filter logic ...

    # 1. Check if table is completely empty
    total_count = YourModel.query.count()
    is_first_time_empty = total_count == 0

    # 2. Check if filters returned no results
    is_zero_results = len(filtered_items) == 0 and not is_first_time_empty

    return render_template("your_page.html",
                         items=filtered_items,
                         is_first_time_empty=is_first_time_empty,
                         is_zero_results=is_zero_results,
                         statistics=statistics,
                         current_filters=current_filters)
```

---

### Template Integration Pattern

Use this conditional structure in your template to show the appropriate empty state:

```jinja2
<!-- Main Table Card -->
<div class="card main-table-card">
  <div class="card-header">
    <!-- Filter buttons here (if applicable) -->
  </div>

  {% if is_first_time_empty %}
    <!-- First-Time Empty State -->
    <div class="empty-state-container text-center py-5">
      <div class="empty-state-icon mb-3">
        <i class="ti ti-activity" style="font-size: 48px; color: #e03131;"></i>
      </div>
      <h3 class="empty-state-title mb-2">No activities yet</h3>
      <p class="empty-state-description text-muted mb-3">
        Activities are the core of your organization. Create your first activity to start managing signups.
      </p>
      <a href="{{ url_for('create_activity') }}" class="btn btn-primary">
        <i class="ti ti-plus me-1"></i>Create Activity
      </a>
    </div>

  {% elif is_zero_results %}
    <!-- Zero Results Empty State -->
    <div class="empty-state-container text-center py-5">
      <div class="empty-state-icon mb-3">
        <i class="ti ti-search" style="font-size: 48px; color: #6c757d;"></i>
      </div>
      <h3 class="empty-state-title mb-2">No activities match your filters</h3>
      <p class="empty-state-description text-muted mb-3">
        Try adjusting your search or filter criteria.
      </p>
      <a href="{{ url_for('list_activities', show_all='true') }}" class="btn btn-link">
        Clear all filters
      </a>
    </div>

  {% else %}
    <!-- Normal Table View -->
    <div class="table-responsive">
      <table class="table">
        <!-- Table headers and rows -->
      </table>
    </div>
  {% endif %}
</div>
```

---

### Icon and Color Guidelines

Use icons and colors that match each page's existing branding:

| Page | Icon | Color | Example |
|------|------|-------|---------|
| **Activities** | `ti-activity-heartbeat` | `#e03131` (red) | Activity branding |
| **Signups** | `ti-user-check` | `#206bc4` (blue) | User-focused |
| **Passports** | `ti-ticket` | `#ae3ec9` (purple) | Passport branding |
| **Surveys** | `ti-clipboard-check` | `#fab005` (yellow) | Survey icon |
| **Inbox Payments** | `ti-mail` | `#20c997` (teal) | Email/payment |
| **Contacts** | `ti-users` | `#fab005` (amber) | People/users |
| **Financial** | `ti-chart-bar` | `#099268` (green) | Money/growth |
| **Zero Results** | `ti-search` | `#6c757d` (gray) | Universal search |

---

### Content Writing Guidelines

#### Primary Message (Title)
- Keep it short: 2-4 words
- Use "No {items} yet" for first-time empty
- Use "No {items} match your filters" for zero results
- Examples:
  - ✅ "No activities yet"
  - ✅ "No passports match your filters"
  - ❌ "You don't have any activities" (too verbose)
  - ❌ "There are no results" (too generic)

#### Secondary Description
- 1-2 sentences maximum
- Explain why the state is empty OR what action to take
- Keep tone friendly and helpful
- Examples for first-time:
  - ✅ "Activities are created when you add your first program or event."
  - ✅ "Passports are automatically generated when signups are completed and paid."
  - ❌ "This is where activities would appear if you had any." (not helpful)
- Examples for zero results:
  - ✅ "Try adjusting your search or filter criteria."
  - ✅ "No matches found. Try clearing your filters or using different search terms."

#### Call-to-Action
- Use "Create {Item}" button for first-time empty (only if users can create items)
- Use "Clear all filters" link for zero results
- Omit CTA if users can't directly create items (e.g., Passports are auto-generated)

---

### Common Mistakes to Avoid

#### ❌ DON'T

- **Don't show just an empty table:**
  ```html
  <!-- WRONG: Empty table structure with no guidance -->
  <table class="table">
    <thead><!-- headers --></thead>
    <tbody><!-- nothing --></tbody>
  </table>
  ```

- **Don't use generic "No data" messages:**
  ```html
  <!-- WRONG: Too generic and unhelpful -->
  <p>No data found</p>
  <p>No entries</p>
  ```

- **Don't mix up first-time vs zero-results states:**
  ```python
  # WRONG: Shows "Clear filters" when database is empty
  is_empty = len(filtered_items) == 0  # This doesn't distinguish!
  ```

- **Don't forget the icon:**
  ```html
  <!-- WRONG: Text-only empty state lacks visual interest -->
  <div>
    <h3>No activities</h3>
    <p>Create your first activity</p>
  </div>
  ```

#### ✅ DO

- **Always include an icon:**
  ```html
  <div class="empty-state-icon mb-3">
    <i class="ti ti-activity" style="font-size: 48px; color: #e03131;"></i>
  </div>
  ```

- **Distinguish between scenarios:**
  ```python
  # CORRECT: Check total count vs filtered count
  total_count = YourModel.query.count()
  is_first_time_empty = total_count == 0
  is_zero_results = len(filtered_items) == 0 and not is_first_time_empty
  ```

- **Provide actionable next steps:**
  ```html
  <!-- For zero results: -->
  <a href="{{ url_for('route', show_all='true') }}" class="btn btn-link">
    Clear all filters
  </a>

  <!-- For first-time: -->
  <a href="{{ url_for('create_route') }}" class="btn btn-primary">
    <i class="ti ti-plus me-1"></i>Create Item
  </a>
  ```

---

### Testing Checklist

When implementing empty states, verify:

#### Visual Testing
- [ ] Icon displays at 48px (36px on mobile)
- [ ] Icon color matches page branding
- [ ] Primary message is bold and clear (18px desktop, 16px mobile)
- [ ] Secondary description is muted gray (#64748b)
- [ ] CTA button/link is properly styled
- [ ] Empty state is vertically centered in card
- [ ] Minimum height of 300px maintained
- [ ] Layout looks good on mobile (375px width)
- [ ] Layout looks good on desktop (1920px width)

#### Functional Testing
- [ ] First-time empty state shows when database table has ZERO records
- [ ] Zero-results empty state shows when search/filter returns no matches
- [ ] Normal table view shows when data exists and matches filters
- [ ] "Clear all filters" link correctly navigates to unfiltered view
- [ ] "Create new" buttons link to correct creation routes
- [ ] Empty state disappears when data is added
- [ ] Switching between filters shows correct empty state type

#### Content Testing
- [ ] Primary message follows "No {items} yet" or "No {items} match" pattern
- [ ] Secondary description is helpful and actionable
- [ ] Tone is friendly, not technical or error-focused
- [ ] CTA text is clear ("Create Activity", not just "Create")
- [ ] Icon choice makes sense for the content type

#### Consistency Testing
- [ ] All pages use identical CSS classes (`.empty-state-container`, etc.)
- [ ] Icon sizes are consistent (48px desktop, 36px mobile)
- [ ] Color choices match page branding
- [ ] CTA patterns are consistent (button for create, link for clear filters)
- [ ] Message structure is consistent across pages

---

### Reference Examples

#### Example 1: Activities Page

**Scenario:** First-time empty (no activities created)

```html
<div class="empty-state-container text-center py-5">
  <div class="empty-state-icon mb-3">
    <i class="ti ti-activity-heartbeat" style="font-size: 48px; color: #e03131;"></i>
  </div>
  <h3 class="empty-state-title mb-2">No activities yet</h3>
  <p class="empty-state-description text-muted mb-3">
    Activities are the core of your organization. Create your first activity to start managing signups and passports.
  </p>
  <a href="{{ url_for('create_activity') }}" class="btn btn-primary">
    <i class="ti ti-plus me-1"></i>Create Activity
  </a>
</div>
```

#### Example 2: Passports Page

**Scenario:** Zero results (search returned no matches)

```html
<div class="empty-state-container text-center py-5">
  <div class="empty-state-icon mb-3">
    <i class="ti ti-search" style="font-size: 48px; color: #6c757d;"></i>
  </div>
  <h3 class="empty-state-title mb-2">No passports match your filters</h3>
  <p class="empty-state-description text-muted mb-3">
    Try adjusting your search or filter criteria.
  </p>
  <a href="{{ url_for('list_passports', show_all='true') }}" class="btn btn-link">
    Clear all filters
  </a>
</div>
```

#### Example 3: Contacts Page

**Scenario:** First-time empty (contacts auto-generated from signups)

```html
<div class="empty-state-container text-center py-5">
  <div class="empty-state-icon mb-3">
    <i class="ti ti-users" style="font-size: 48px; color: #fab005;"></i>
  </div>
  <h3 class="empty-state-title mb-2">No contacts yet</h3>
  <p class="empty-state-description text-muted mb-3">
    Contacts are automatically created when users sign up for activities. They'll appear here once you have signups.
  </p>
  <!-- Note: No CTA button since contacts are auto-generated -->
</div>
```

---

### Why This Pattern Works

#### User Experience Benefits
1. **Clear Guidance** - Users understand why they see nothing and what to do next
2. **Reduced Confusion** - No wondering if the app is broken or still loading
3. **Faster Onboarding** - New users immediately know how to get started
4. **Better Search UX** - Clear feedback when filters return no results
5. **Professional Appearance** - Matches industry-leading SaaS tools (Stripe, Linear, Notion, GitHub)

#### Implementation Benefits
1. **Consistency** - Same pattern across all 7+ pages
2. **Reusable CSS** - Single `.empty-state-container` class for all pages
3. **Easy Maintenance** - Update one pattern, change appears everywhere
4. **Design System Integration** - Fully documented and standardized

#### Business Benefits
1. **Lower Support Load** - Users don't get confused or stuck
2. **Better Conversion** - New users know how to start using features
3. **Competitive Advantage** - Better UX than basic "No data" messages
4. **Scalability** - Pattern works for any new list/table pages added in future

---

## Modal Component

### Desktop Modal Design Standard

**CRITICAL:** Use Tabler.io's DEFAULT modal styling. Do NOT add custom CSS that overrides Tabler's beautiful defaults.

**Tabler.io Default Modal Styling:**
- **Modal Status Bar:** 2px colored bar at top (`.modal-status`)
- **Modal Body:** Pure white background (`#ffffff`)
- **Modal Footer:** Light gray background (`#f6f8fb` via CSS variable `--tblr-bg-surface-tertiary`)
- **Backdrop:** Semi-transparent with blur effect

### Visual Specifications (Tabler.io Defaults)

| Element | Styling |
|---------|---------|
| **Backdrop** | `rgba(0, 0, 0, 0.5)` with `backdrop-filter: blur(4px)` |
| **Modal Status** | 2px colored bar at top, uses `--tblr-secondary` or status colors |
| **Modal Body** | Pure white `#ffffff` background (Tabler default) |
| **Modal Footer** | Light gray `#f6f8fb` background (Tabler's `--tblr-bg-surface-tertiary`) |
| **Border Radius** | `8px` on modal-content container |

### HTML Structure

```html
<div class="modal fade" id="exampleModal" tabindex="-1">
  <div class="modal-dialog modal-sm modal-dialog-centered">
    <div class="modal-content">
      <!-- Status bar (colored top stripe) - ALWAYS INCLUDE -->
      <div class="modal-status bg-danger"></div>

      <!-- Main content area - WHITE BACKGROUND (Tabler default) -->
      <div class="modal-body text-center py-4">
        <i class="ti ti-check icon mb-2 text-primary" style="font-size: 2rem;"></i>
        <h3>Modal Title</h3>
        <div class="text-muted">Modal description text goes here</div>
      </div>

      <!-- Footer area - LIGHT GRAY BACKGROUND (Tabler default) -->
      <div class="modal-footer">
        <button type="button" class="btn btn-link w-100" data-bs-dismiss="modal">Cancel</button>
        <button type="button" class="btn btn-primary w-100">Confirm Action</button>
      </div>
    </div>
  </div>
</div>
```

### CSS Requirements

**DO NOT add custom modal CSS.** Tabler.io handles everything perfectly by default.

**Only exception - maintain this in `base.html` if needed for modal functionality:**
```css
.modal-content {
  pointer-events: auto !important; /* Ensure modal content is clickable */
}
```

### Critical Rules

**DO:**
- ✅ Use Tabler.io's default modal styling (no custom CSS)
- ✅ Always include `.modal-status` bar at top of modal
- ✅ Use `modal-sm` class for confirmation modals
- ✅ Use `modal-dialog-centered` for better UX
- ✅ Let Tabler's CSS variables handle backgrounds

**DON'T:**
- ❌ NEVER add custom background colors to `.modal-body` or `.modal-footer`
- ❌ NEVER use `!important` to force white backgrounds on modal elements
- ❌ NEVER override Tabler's CSS variables for modals
- ❌ NEVER add inline styles or custom CSS to modal elements

### Common Modal Types

#### Confirmation Modal (Example: Redeem Session)
- Small size (`modal-sm`)
- Centered vertically
- Status bar with danger color (`.modal-status.bg-danger`)
- Icon at top
- Title (H3)
- Description text (muted)
- Two action buttons (Cancel + Confirm)

#### Form Modal
- Regular or large size (`modal-lg`)
- White body for form fields (Tabler default)
- Light gray footer for form actions (Tabler default)
- Validation feedback in body

#### Info/Alert Modal
- Small to regular size
- Status indicator stripe at top (`.modal-status.bg-primary` or `.bg-success`)
- Centered content
- Single action button

### Mobile Behavior

Modals on mobile (<768px) maintain the SAME Tabler defaults as desktop:
- White modal body
- Light gray modal footer
- Visible status bar
- Backdrop blur effect

**Testing Checklist:**
- [ ] Modal status bar visible (2px colored bar at top)
- [ ] Modal-body is white on desktop (1920x1080)
- [ ] Modal-body is white on mobile (375x667)
- [ ] Modal-footer is light gray (#f6f8fb) on both views
- [ ] Backdrop has blur effect on both views
- [ ] No custom CSS overriding Tabler defaults
- [ ] Buttons are clickable on both mobile and desktop

---

## 🚨 CRITICAL: Mobile Modal Z-Index Fix

### The Problem (Discovered November 2025)

**Symptoms on Mobile (<768px):**
- Modal appears gray/washed out instead of white
- Modal buttons are not clickable
- Backdrop appears ON TOP of modal instead of behind it
- Playwright error: "modal-backdrop intercepts pointer events"

**Desktop (≥992px) Works Fine:**
- Modal displays with white background
- Buttons are clickable
- Backdrop properly behind modal

### Root Cause

**The issue ONLY exists on mobile** because of mobile-specific CSS in `static/minipass.css`:

```css
@media (max-width: 991px) {
  .minipass-main {
    z-index: 1;  /* ← THIS BREAKS MODALS */
  }

  .page-wrapper,
  .page-body {
    z-index: 1;  /* ← THIS BREAKS MODALS */
  }
}
```

**Why This Breaks Modals:**

1. Bootstrap 5 / Tabler.io modal z-index stack:
   - Modal backdrop: `z-index: 1050` (root stacking context)
   - Modal: `z-index: 1055` (root stacking context)

2. When parent containers have `z-index: 1` + `position: relative`, they create NEW stacking contexts

3. Modals are embedded in page content (inside `.minipass-main` → `.page-wrapper` → `.page-body`)

4. Even though modal has `z-index: 1055`, it's trapped inside containers with `z-index: 1`

5. Result: Backdrop (z-index 1050 in root) appears ABOVE modal containers (z-index 1 in root)

### Why Desktop Worked

Desktop CSS (≥992px) does NOT have `z-index: 1` on these containers, so modals work perfectly.

**The bug was mobile-specific** because someone added `z-index: 1` only in the mobile media query.

### The Fix

**File: `static/minipass.css` (lines 1945-1961)**

**REMOVE** the `z-index: 1` declarations from mobile CSS:

```css
@media (max-width: 991px) {
  .minipass-main {
    display: flex;
    flex-direction: column;
    height: 100vh;
    margin-left: 0;
    overflow: hidden;
    position: relative;
    /* z-index: 1 ← REMOVED - was breaking modals */
    padding-bottom: 80px;
  }

  .page-wrapper,
  .page-body {
    position: relative;
    /* z-index: 1 ← REMOVED - was breaking modals */
  }
}
```

### Why This Works

By removing `z-index: 1` from parent containers:
- Parent containers no longer create stacking contexts
- Modal and backdrop both exist in root stacking context
- Bootstrap's default z-index values work correctly:
  - Backdrop: z-index 1050
  - Modal: z-index 1055
- Modal appears ABOVE backdrop as intended

### Testing After Fix

**Mobile (375x667):**
- ✅ Modal displays with white background
- ✅ Dark blurred backdrop BEHIND modal
- ✅ Buttons are fully clickable
- ✅ No gray/washed out appearance

**Desktop (1920x1080):**
- ✅ Modal continues to work (no regression)
- ✅ White background maintained
- ✅ Buttons clickable

### Important Notes

1. **Desktop and mobile MUST use the same z-index rules** - Do NOT add mobile-specific z-index to page containers

2. **Tabler.io defaults are sufficient** - No custom z-index needed on containers

3. **The original `z-index: 1` was added** to keep content below sidebar (z-index 1040), but it broke modals (z-index 1050-1055)

4. **If you see modal issues on mobile**, check for z-index on parent containers in mobile media queries

### Verification Checklist

After any modal-related changes, verify:
- [ ] No `z-index` declarations on `.minipass-main` in mobile CSS
- [ ] No `z-index` declarations on `.page-wrapper` or `.page-body` in mobile CSS
- [ ] Test modal on mobile (375px): white background, clickable buttons
- [ ] Test modal on desktop (1920px): no regressions
- [ ] No `!important` declarations in modal CSS (use Tabler defaults)

---

## ⚠️ CRITICAL WARNING: Do Not Override Tabler Modal Defaults

### The Correct Approach: Use Tabler Defaults

Tabler.io provides beautiful modal styling out of the box:
- **Modal Body:** White background (Tabler default)
- **Modal Footer:** Light gray `#f6f8fb` (Tabler's `--tblr-bg-surface-tertiary`)
- **Modal Status:** 2px colored bar at top

**DO NOT add custom CSS like this:**

```css
/* ❌ WRONG - Do NOT add this */
.modal-body {
  background-color: #ffffff !important;
}

.modal-footer {
  background-color: #ffffff !important;
}

.modal-content,
.modal-dialog .modal-content {
  --tblr-bg-surface: #ffffff !important;
  background-color: #ffffff !important;
}
```

**WHY THIS IS WRONG:**
- Overrides Tabler's beautiful default light gray footer
- Removes the visual distinction between modal body and footer
- Makes the modal status bar invisible or barely visible
- Breaks Tabler's carefully designed modal appearance

### What Happened (Historical Context)

In `base.html` (lines 55-84), there was a "CRITICAL FIX" that forced ALL modal elements to white backgrounds with `!important`. This completely overrode Tabler.io's defaults and made modals look wrong.

**The fix:** Remove all that custom CSS and let Tabler handle everything.

**WHY THIS MATTERS:**
- Tabler.io's defaults are beautiful and well-tested
- Custom overrides break the design system
- The status bar becomes invisible when everything is white
- The footer loses its visual distinction when forced to white

---

## Flash Message Component

### Overview

Flash messages (also called "toast notifications" or "alerts") provide immediate feedback to users after actions. Minipass uses a standardized flash message system with 5 distinct types, consistent styling, and smooth animations.

**Key Features:**
- Fixed overlay position (centered, top of viewport)
- Auto-dismiss with progress bar (5-second default)
- Gradient backgrounds with subtle animations
- Tabler Icons for visual consistency
- Accessibility compliant (ARIA live regions)
- Mobile responsive

### Flash Message Types

| Type | Category | Background Color | Icon | Use Case |
|------|----------|------------------|------|----------|
| **Success** | `success` | Green gradient `#10b981` → `#059669` | `ti-circle-check` | Action completed successfully |
| **Error** | `error` | Red gradient `#ef4444` → `#dc2626` | `ti-alert-circle` | Action failed, error occurred |
| **Warning** | `warning` | Orange gradient `#f59e0b` → `#d97706` | `ti-alert-triangle` | Caution, potential issue |
| **Info** | `info` | Blue gradient `#3b82f6` → `#2563eb` | `ti-info-circle` | Informational message |
| **Tier Limit** | `tier_limit` | Yellow `#fef3c7` with dark text | (no icon) | Subscription tier upgrade prompt |

### Python Usage

Flash messages are triggered from Flask routes using the `flash()` function:

```python
from flask import flash

# Success message
flash("Payment received successfully!", "success")

# Error message
flash("Unable to process request. Please try again.", "error")

# Warning message
flash("Your session will expire in 5 minutes.", "warning")

# Info message
flash("New feature available in settings.", "info")

# Tier limit message (special upgrade prompt)
flash("Survey feature requires Professional tier. Upgrade to unlock.", "tier_limit")
```

### HTML Structure (from base.html)

The flash message system is implemented in `templates/base.html` as a fixed overlay:

```html
{% with messages = get_flashed_messages(with_categories=true) %}
  {% if messages %}
    <div class="flash-alert-overlay" id="flashAlertOverlay">
      <div class="flash-alert-container">
        {% for category, message in messages %}
          <div class="flash-alert alert alert-{{ 'success' if category == 'success' else 'danger' if category == 'error' else 'warning' if category == 'warning' else 'tier-limit' if category == 'tier_limit' else 'info' }}"
               role="alert" aria-live="polite" aria-atomic="true">
            <!-- Progress bar for auto-dismiss -->
            <div class="flash-alert-progress"></div>

            <!-- Icon container (except tier_limit) -->
            {% if category != 'tier_limit' %}
            <div class="alert-icon-container">
              {% if category == 'success' %}
                <i class="ti ti-circle-check alert-icon"></i>
              {% elif category == 'error' %}
                <i class="ti ti-alert-circle alert-icon"></i>
              {% elif category == 'warning' %}
                <i class="ti ti-alert-triangle alert-icon"></i>
              {% else %}
                <i class="ti ti-info-circle alert-icon"></i>
              {% endif %}
            </div>
            {% endif %}

            <!-- Message content -->
            <div class="alert-content">
              <div class="alert-title">
                {% if category == 'success' %}Success{% elif category == 'error' %}Error{% elif category == 'warning' %}Warning{% elif category == 'tier_limit' %}Upgrade Available{% else %}Info{% endif %}
              </div>
              <div class="alert-message">{{ message }}</div>
            </div>

            <!-- Close button -->
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
          </div>
        {% endfor %}
      </div>
    </div>
  {% endif %}
{% endwith %}
```

### CSS Styling

The flash message styles are embedded in `base.html` within the `<style>` block:

```css
/* Container positioning */
.flash-alert-overlay {
  position: fixed;
  top: 1rem;
  left: 50%;
  transform: translateX(-50%);
  z-index: 9999;
  pointer-events: none;
}

.flash-alert-container {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  pointer-events: auto;
}

/* Base alert styling */
.flash-alert {
  display: flex;
  align-items: flex-start;
  padding: 1rem 1.25rem;
  border-radius: 0.75rem;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.15);
  min-width: 320px;
  max-width: 480px;
  position: relative;
  overflow: hidden;
}

/* Progress bar for auto-dismiss */
.flash-alert-progress {
  position: absolute;
  bottom: 0;
  left: 0;
  height: 3px;
  background: rgba(255, 255, 255, 0.5);
  animation: progressBar 5s linear forwards;
}

@keyframes progressBar {
  from { width: 100%; }
  to { width: 0%; }
}

/* Color schemes with gradients */
.flash-alert.alert-success {
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.95) 0%, rgba(5, 150, 105, 0.95) 100%);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.flash-alert.alert-danger {
  background: linear-gradient(135deg, rgba(239, 68, 68, 0.95) 0%, rgba(220, 38, 38, 0.95) 100%);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.flash-alert.alert-warning {
  background: linear-gradient(135deg, rgba(245, 158, 11, 0.95) 0%, rgba(217, 119, 6, 0.95) 100%);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.flash-alert.alert-info {
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.95) 0%, rgba(37, 99, 235, 0.95) 100%);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

/* Tier limit - special yellow variant */
.flash-alert.alert-tier-limit {
  background: linear-gradient(135deg, rgba(254, 243, 199, 0.98) 0%, rgba(253, 230, 138, 0.98) 100%);
  color: #92400e;
  border: 1px solid rgba(217, 119, 6, 0.3);
}

/* Icon styling */
.alert-icon-container {
  margin-right: 0.75rem;
  flex-shrink: 0;
}

.alert-icon {
  font-size: 1.5rem;
  opacity: 0.9;
}

/* Content styling */
.alert-title {
  font-weight: 600;
  margin-bottom: 0.25rem;
  line-height: 1.3;
}

.alert-message {
  font-size: 0.875rem;
  line-height: 1.4;
  opacity: 0.9;
}
```

### JavaScript Behavior

The flash message system includes JavaScript for animations and auto-dismiss:

```javascript
document.addEventListener('DOMContentLoaded', function() {
  const flashOverlay = document.getElementById('flashAlertOverlay');
  if (!flashOverlay) return;

  const alerts = flashOverlay.querySelectorAll('.flash-alert');

  alerts.forEach((alert, index) => {
    // Staggered entrance animation
    setTimeout(() => {
      alert.classList.add('show');
    }, index * 120);

    // Auto-dismiss after 5 seconds
    const progressBar = alert.querySelector('.flash-alert-progress');
    if (progressBar) {
      setTimeout(() => {
        alert.classList.remove('show');
        setTimeout(() => alert.remove(), 300);

        // Remove overlay when all alerts dismissed
        if (flashOverlay.querySelectorAll('.flash-alert').length <= 1) {
          setTimeout(() => flashOverlay.remove(), 300);
        }
      }, 5000);
    }
  });
});
```

### Accessibility Features

- **ARIA live regions:** `role="alert"` and `aria-live="polite"` for screen reader announcements
- **Dismissible:** Close button with `aria-label="Close"`
- **Color contrast:** All text meets WCAG AA contrast requirements
- **Keyboard accessible:** Close button is focusable and actionable

### Mobile Responsiveness

On mobile devices (< 768px):
- Alert width adjusts to `min-width: 280px`
- Font sizes reduce slightly for better fit
- Maintains centered positioning

```css
@media (max-width: 768px) {
  .flash-alert {
    min-width: 280px;
    max-width: calc(100vw - 2rem);
  }

  .flash-alert .alert-title {
    font-size: 0.9rem;
  }

  .flash-alert .alert-message {
    font-size: 0.8rem;
  }
}
```

### Best Practices

**DO:**
- ✅ Use `success` for completed actions (form submitted, payment processed)
- ✅ Use `error` for failures that require user attention
- ✅ Use `warning` for caution messages (session expiring, data will be lost)
- ✅ Use `info` for neutral informational messages
- ✅ Use `tier_limit` only for subscription upgrade prompts
- ✅ Keep messages concise (1-2 sentences)

**DON'T:**
- ❌ Don't show multiple flash messages at once (unless truly necessary)
- ❌ Don't use flash messages for validation errors (use inline validation instead)
- ❌ Don't use flash messages for confirmations that require user action (use modals)
- ❌ Don't add emojis to flash messages (icons are built-in)

### Testing Checklist

- [ ] Success message shows green gradient with checkmark icon
- [ ] Error message shows red gradient with alert-circle icon
- [ ] Warning message shows orange gradient with alert-triangle icon
- [ ] Info message shows blue gradient with info-circle icon
- [ ] Tier limit message shows yellow with dark text (no icon)
- [ ] Progress bar animates and auto-dismisses after 5 seconds
- [ ] Close button works to dismiss immediately
- [ ] Messages are readable on mobile (375px width)
- [ ] Screen reader announces message content

---

## CSS Files to Include

### Required CSS Files (In Order)
```html
<!-- 1. Global Dropdown Fix -->
<link href="{{ url_for('static', filename='css/dropdown-fix.css') }}?v=4.0" rel="stylesheet">

<!-- 2. Search Component -->
<link href="{{ url_for('static', filename='css/search-component.css') }}?v=1.0" rel="stylesheet">

<!-- 3. Filter Component -->
<link href="{{ url_for('static', filename='css/filter-component.css') }}?v=1.0" rel="stylesheet">
```

### What Each File Does
- **dropdown-fix.css:** Fixes z-index issues and mobile dropdown auto-flip for Bootstrap dropdowns in tables
- **search-component.css:** Pink glow, loading animations, search styling
- **filter-component.css:** GitHub-style filter buttons, active states

### Mobile Dropdown Auto-Flip Behavior

**CRITICAL FIX:** The `dropdown-fix.css` file automatically handles dropdown positioning on mobile devices.

**How It Works:**
- Bootstrap's Popper.js automatically detects when a dropdown would be cut off by the mobile navigation bar
- Popper.js adds `data-popper-placement="top-end"` attribute and positions the dropdown upward
- Our CSS allows Popper.js to control positioning by NOT forcing `top: 100%` on dropdowns with Popper positioning

**No JavaScript Required:**
- Previously required custom JavaScript to add `dropup` class
- Now handled automatically by Bootstrap's built-in Popper.js
- Works on **all pages** with Action dropdowns in tables (passports, signups, activity dashboard, payment matches, etc.)

**Technical Details:**
The CSS uses `:not([data-popper-placement])` selectors to only apply default positioning to non-Popper dropdowns:
```css
/* Only force downward positioning for dropdowns WITHOUT Popper.js */
.dropdown-menu:not([data-popper-placement]) {
    top: 100%;
    left: 0;
}

/* Dropdowns WITH Popper.js get automatic smart positioning */
.dropdown-menu[data-popper-placement] {
    /* Let Popper.js handle all positioning */
}
```

**This fix applies globally to:**
- Passports page table Action buttons
- Signups page table Action buttons
- Activity dashboard passport table Action buttons
- Payment matches table Action buttons
- Any other table with dropdown Action buttons

### Mobile Z-Index Fix
If you experience mobile menu layering issues, ensure this CSS is in `static/minipass.css`:

```css
@media (max-width: 991px) {
  .minipass-main {
    display: flex;
    flex-direction: column;
    height: 100vh;
    margin-left: 0;
    overflow: hidden;
    position: relative;
    z-index: 1;  /* Ensures content stays below mobile menu */
  }
}
```

---

## JavaScript Behavior

### Search Functionality

**Required Features:**
1. Ctrl+K keyboard shortcut to focus search
2. Pink glow effect on Ctrl+K press
3. Character counter (shows after 1 character)
4. Clear button (shows when text exists)
5. Blue pulse animation during AJAX search
6. Hide keyboard hints on mobile

**JavaScript Template:**
```javascript
document.addEventListener('DOMContentLoaded', function() {
  const searchInput = document.getElementById('enhancedSearchInput');
  const searchClearBtn = document.getElementById('searchClearBtn');
  const searchCharCounter = document.getElementById('searchCharCounter');
  const kbdHint = document.getElementById('searchKbdHint');

  // Ctrl+K shortcut
  document.addEventListener('keydown', function(e) {
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
      e.preventDefault();
      searchInput.focus();

      // Add pink glow effect
      searchInput.classList.add('search-glow-active');
      setTimeout(() => {
        searchInput.classList.remove('search-glow-active');
      }, 800);
    }
  });

  // Character counter
  searchInput.addEventListener('input', function() {
    const length = this.value.length;

    if (length > 0) {
      searchCharCounter.textContent = `${length} character${length !== 1 ? 's' : ''}`;
      searchCharCounter.style.display = 'inline';
      searchClearBtn.style.display = 'inline-flex';
      kbdHint.style.display = 'none';
    } else {
      searchCharCounter.style.display = 'none';
      searchClearBtn.style.display = 'none';
      // Only show kbd hint on desktop
      if (window.innerWidth >= 768) {
        kbdHint.style.display = 'inline';
      }
    }
  });

  // Clear button
  searchClearBtn.addEventListener('click', function() {
    searchInput.value = '';
    searchInput.dispatchEvent(new Event('input'));
    searchInput.focus();
  });

  // Hide kbd hints on mobile
  function updateKbdVisibility() {
    if (window.innerWidth < 768) {
      kbdHint.style.display = 'none';
    } else if (searchInput.value.length === 0) {
      kbdHint.style.display = 'inline';
    }
  }

  window.addEventListener('resize', updateKbdVisibility);
  updateKbdVisibility();
});
```

### Filter Functionality

```javascript
function filterPassports(filterType) {
  // Remove active from all
  document.querySelectorAll('.github-filter-btn').forEach(btn => {
    btn.classList.remove('active');
  });

  // Add active to clicked
  document.getElementById('filter-' + filterType).classList.add('active');

  // Get all table rows
  const rows = document.querySelectorAll('tbody tr');

  rows.forEach(row => {
    const isPaid = row.dataset.paid === 'true';
    const isActive = row.dataset.active === 'true';

    let show = false;
    if (filterType === 'all') {
      show = true;
    } else if (filterType === 'active') {
      show = isActive || !isPaid;
    } else if (filterType === 'unpaid') {
      show = !isPaid;
    }

    row.style.display = show ? '' : 'none';
  });

  // Update URL with filter parameter
  const url = new URL(window.location);
  url.searchParams.set('passport_filter', filterType);
  window.history.pushState({}, '', url);
}
```

---

## Flash Messages Component

### Overview

Flash messages are the **ONLY** way to display success, error, warning, and info messages to users across the entire application. They provide consistent feedback for user actions.

### Visual Features
- Centered overlay at the top of the page
- Semi-transparent dark backdrop
- Icon indicating message type (success, error, warning, info)
- Title and message text
- Animated progress bar at bottom
- Auto-dismissible after 5 seconds
- Manual dismiss button (X)

### Message Categories

| Category | Color | Icon | Use Case |
|----------|-------|------|----------|
| **success** | Green | `ti-check-circle` | Successful operations (save, delete, create) |
| **error** | Red | `ti-alert-circle` | Failed operations, validation errors |
| **warning** | Yellow | `ti-alert-triangle` | Caution messages, confirmations needed |
| **info** | Blue | `ti-info-circle` | Informational messages |

### Backend Usage (Python/Flask)

**ALWAYS use Flask's `flash()` function:**

```python
from flask import flash, redirect, url_for

# Success message
flash("✅ All settings saved successfully!", "success")

# Error message
flash("❌ Error saving settings: Invalid email format", "error")

# Warning message
flash("⚠️ This action cannot be undone", "warning")

# Info message
flash("ℹ️ Your changes have been queued for processing", "info")

# Always redirect after flash
return redirect(url_for("your_route_name"))
```

### Frontend Implementation

Flash messages are automatically rendered by `base.html` (lines 355-395). **No custom JavaScript or HTML is needed in individual templates.**

The base template structure:
```html
{% with messages = get_flashed_messages(with_categories=true) %}
  {% if messages %}
    <div class="flash-alert-overlay" id="flashAlertOverlay">
      <div class="flash-alert-container">
        {% for category, message in messages %}
          <div class="flash-alert alert alert-{{ 'success' if category == 'success' else 'danger' if category == 'error' else 'warning' if category == 'warning' else 'info' }} alert-dismissible">
            <div class="d-flex">
              <div class="alert-icon-container">
                {% if category == 'success' %}
                  <i class="ti ti-check-circle alert-icon"></i>
                {% elif category == 'error' %}
                  <i class="ti ti-alert-circle alert-icon"></i>
                {% elif category == 'warning' %}
                  <i class="ti ti-alert-triangle alert-icon"></i>
                {% else %}
                  <i class="ti ti-info-circle alert-icon"></i>
                {% endif %}
              </div>
              <div class="flex-fill">
                <div class="alert-title">{{ category|title }}</div>
                <div class="alert-message">{{ message }}</div>
              </div>
              <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
            <div class="flash-alert-progress"></div>
          </div>
        {% endfor %}
      </div>
    </div>
  {% endif %}
{% endwith %}
```

### CSS Styling

Flash message styles are defined in `base.html` (lines 139-150). **Do not override these styles.**

Key CSS variables:
- Success: Uses Bootstrap's `alert-success` class
- Error: Uses Bootstrap's `alert-danger` class
- Warning: Uses Bootstrap's `alert-warning` class
- Info: Uses Bootstrap's `alert-info` class

### Critical Rules

**DO:**
- ✅ Always use `flash()` function in backend routes
- ✅ Always redirect after calling `flash()`
- ✅ Use emojis for visual emphasis (✅, ❌, ⚠️, ℹ️)
- ✅ Keep messages concise (1-2 sentences max)
- ✅ Use appropriate category (success, error, warning, info)

**DON'T:**
- ❌ NEVER create custom toast notifications
- ❌ NEVER use JavaScript to show success/error messages
- ❌ NEVER use AJAX without proper flash message handling
- ❌ NEVER use alert(), confirm(), or browser dialogs
- ❌ NEVER return JSON responses with custom notification systems

### Common Mistake: AJAX with Custom Toasts

**WRONG - Custom Toast Notifications:**
```javascript
// ❌ DON'T DO THIS
fetch('/save-settings', {
    method: 'POST',
    body: formData
})
.then(response => response.json())
.then(data => {
    showToast('success', data.message);  // WRONG!
});
```

**CORRECT - Standard Flask Flash:**
```python
# ✅ DO THIS
@app.route("/save-settings", methods=["POST"])
def save_settings():
    try:
        # Save logic here
        db.session.commit()
        flash("✅ Settings saved successfully!", "success")
        return redirect(url_for("settings"))
    except Exception as e:
        flash(f"❌ Error: {str(e)}", "error")
        return redirect(url_for("settings"))
```

### Example: Settings Page Fix (November 2025)

**Problem:** Settings page used AJAX with custom Bootstrap toast notifications in the top-right corner, requiring double-click to save.

**Solution:** Removed AJAX, simplified to standard Flask form submission with flash messages.

**Before:**
```javascript
// Custom toast notification (WRONG)
function showToast(type, message) {
    const toast = document.createElement('div');
    toast.className = `toast bg-${type}`;
    // ... custom toast creation code
}
```

**After:**
```python
# Standard Flash message (CORRECT)
@app.route("/admin/unified-settings", methods=["POST"])
def unified_settings():
    # ... save logic
    flash("✅ All settings saved successfully!", "success")
    return redirect(url_for("unified_settings"))
```

**Result:**
- Single-click save works
- Consistent flash message across entire app
- Simpler, more maintainable code

### Testing Checklist

When implementing flash messages, verify:
- [ ] Message appears centered at top of page
- [ ] Correct icon and color for category
- [ ] Title shows category name (Success, Error, etc.)
- [ ] Message text is clear and concise
- [ ] Progress bar animates over 5 seconds
- [ ] Auto-dismisses after 5 seconds
- [ ] Manual dismiss button (X) works
- [ ] Works on mobile and desktop

---

## Mobile Responsiveness Rules

### Breakpoints
- **Mobile:** <768px
- **Tablet:** 768px - 991px
- **Desktop:** ≥992px

### Common Patterns

#### Show on Desktop Only
```html
<span class="d-none d-md-inline">Desktop Text</span>
```

#### Show on Mobile Only
```html
<i class="d-md-none ti ti-icon"></i>
```

#### Table Columns
```html
<!-- Desktop only column -->
<th class="d-none d-md-table-cell">Column</th>
<td class="d-none d-md-table-cell">Data</td>

<!-- Mobile only column -->
<th class="d-md-none">#</th>
<td class="d-md-none">123</td>
```

### Mobile Checklist
When implementing on mobile, verify:
- [ ] Keyboard hints (Ctrl+K) are hidden
- [ ] Table columns collapse correctly
- [ ] Actions dropdown shows icon instead of text
- [ ] User email is hidden
- [ ] Activity logo replaces user avatar
- [ ] GitHub filters remain centered
- [ ] Search input is properly sized (16px font to prevent zoom)

---

## Complete Page Template

### Full HTML Example
```html
{% extends "base.html" %}

{% block title %}Your Page Title{% endblock %}

{% block content %}
<!-- CSS Imports -->
<link rel="stylesheet" href="{{ url_for('static', filename='css/dropdown-fix.css') }}?v=4.0">
<link rel="stylesheet" href="{{ url_for('static', filename='css/search-component.css') }}?v=1.0">
<link rel="stylesheet" href="{{ url_for('static', filename='css/filter-component.css') }}?v=1.0">

<div class="container-xl">
  <div class="row">
    <div class="col-12">

      <!-- Page Title -->
      <h2 class="mt-4 mb-3">
        <i class="ti ti-your-icon me-2" style="color: #206bc4;"></i>Your Page Title
      </h2>

      <!-- Enhanced Search -->
      <form method="GET" action="{{ url_for('your_route') }}" class="mb-4" id="dynamicSearchForm">
        <div class="input-icon position-relative">
          <span class="input-icon-addon">
            <i class="ti ti-search fs-3"></i>
          </span>
          <input type="text"
                 name="q"
                 id="enhancedSearchInput"
                 class="form-control form-control-lg shadow-sm"
                 placeholder="Start typing to search"
                 value="{{ request.args.get('q', '') }}"
                 style="padding-right: 100px; border-radius: 0.5rem;"
                 autocomplete="off"
                 data-bs-toggle="false">
          <div class="position-absolute end-0 top-50 translate-middle-y me-3 d-flex align-items-center gap-2">
            <small id="searchCharCounter" class="text-muted" style="font-size: 0.75rem; display: none;"></small>
            <kbd id="searchKbdHint" class="text-muted d-none d-md-inline">Ctrl</kbd>
            <kbd class="text-muted d-none d-md-inline">K</kbd>
            <button id="searchClearBtn" type="button" class="btn btn-link p-0 border-0" style="display: none; width: 24px; height: 24px;">
              <i class="ti ti-x" style="font-size: 18px; color: #6c757d;"></i>
            </button>
          </div>
        </div>
      </form>

      <!-- Table with Filters -->
      <div id="your-filters" class="scroll-anchor"></div>
      <div class="card main-table-card" style="margin-top: 1.5rem !important;">
        <div class="card-header">
          <div class="d-flex justify-content-center align-items-center w-100">
            <div class="github-filter-group" role="group" aria-label="Filter buttons">
              <a href="#" onclick="filterData('active'); return false;" class="github-filter-btn active" id="filter-active">
                <i class="ti ti-activity"></i>Active <span class="filter-count">({{ active_count }})</span>
              </a>
              <a href="#" onclick="filterData('all'); return false;" class="github-filter-btn" id="filter-all">
                <i class="ti ti-list"></i>All <span class="filter-count">({{ total_count }})</span>
              </a>
            </div>
          </div>
        </div>
        <div class="table-responsive">
          <table class="table table-hover">
            <thead>
              <tr>
                <th>User</th>
                <th class="d-none d-md-table-cell">Details</th>
                <th class="text-center">Actions</th>
              </tr>
            </thead>
            <tbody>
              {% for item in items %}
              <tr>
                <td style="vertical-align: middle;">
                  <div class="d-flex align-items-center">
                    <img src="..." class="rounded-circle me-3 d-none d-md-block" alt="Avatar">
                    <div>
                      <div class="fw-bold">{{ item.name }}</div>
                      <div class="text-muted small d-none d-md-block">{{ item.email }}</div>
                    </div>
                  </div>
                </td>
                <td class="d-none d-md-table-cell" style="vertical-align: middle;">
                  {{ item.details }}
                </td>
                <td class="text-center" style="vertical-align: middle;">
                  <div class="dropdown">
                    <a href="#" class="btn btn-outline-secondary dropdown-toggle" data-bs-toggle="dropdown">
                      <span class="d-none d-md-inline">Actions</span>
                      <i class="ti ti-menu-2 d-md-none"></i>
                    </a>
                    <div class="dropdown-menu dropdown-menu-end">
                      <a href="#" class="dropdown-item">Edit</a>
                      <a href="#" class="dropdown-item text-danger">Delete</a>
                    </div>
                  </div>
                </td>
              </tr>
              {% endfor %}
            </tbody>
          </table>
        </div>
      </div>

    </div>
  </div>
</div>

<script>
// Copy JavaScript from "JavaScript Behavior" section above
// Include: Ctrl+K shortcut, character counter, clear button, filter function
</script>

{% endblock %}
```

---

## Checklist for New Pages

When implementing this design on a new page, verify:

### HTML Structure
- [ ] Page title with icon (remove "Your" prefix)
- [ ] Search bar with all components (icon, input, Ctrl+K hints, counter, clear button)
- [ ] GitHub filter group with active state
- [ ] Table with proper responsive classes
- [ ] Actions dropdown with text/icon toggle

### CSS Includes
- [ ] dropdown-fix.css loaded
- [ ] search-component.css loaded
- [ ] filter-component.css loaded
- [ ] No custom styles that override component CSS

### JavaScript
- [ ] Ctrl+K keyboard shortcut working
- [ ] Pink glow effect on Ctrl+K
- [ ] Character counter updates
- [ ] Clear button shows/hides
- [ ] Keyboard hints hide on mobile
- [ ] Filter buttons toggle active class
- [ ] Filter function updates table visibility

### Mobile Testing
- [ ] Test on 375px width (iPhone SE size)
- [ ] Ctrl+K hints hidden
- [ ] Table columns hide/show correctly
- [ ] Actions show icon only
- [ ] Search input doesn't cause zoom (16px font)
- [ ] GitHub filters stay centered
- [ ] Mobile menu doesn't show content through it

### Desktop Testing
- [ ] Test on 1920px width
- [ ] All table columns visible
- [ ] Ctrl+K shortcut works
- [ ] Hover states working on filters
- [ ] Dropdowns positioned correctly

---

## Common Mistakes to Avoid

### ❌ DON'T
- Add custom CSS that overrides component styles
- Use different class names for similar components
- Add hover effects to tables
- Use gradients on white cards
- Forget to hide Ctrl+K hints on mobile
- Mix different table responsive patterns
- Add inline styles to filter buttons

### ✅ DO
- Use the exact HTML structure from this document
- Copy-paste component code blocks
- Test on mobile (375px) and desktop (1920px)
- Use the same CSS classes across all pages
- Keep keyboard hints hidden on mobile with `d-none d-md-inline`
- Follow the vertical-align: middle pattern for all table cells
- Reference activity_dashboard.html when in doubt

---

## Common Implementation Errors

### Error 1: Filter Counts Are Dynamic (Change When Clicking)

**Symptom**: Filter counts show "0" after clicking a filter button

**Wrong Implementation**:
```html
<!-- WRONG: Filters current page results -->
<span>({{ activities|selectattr('status', 'equalto', 'active')|list|length }})</span>
```

**Root Cause**: Using Jinja filters on the page's filtered results instead of backend statistics

**Correct Implementation**:
```html
<!-- CORRECT: Uses statistics from backend -->
<span>({{ statistics.active_activities|default(0) }})</span>
```

**Fix Checklist**:
1. ✅ Backend queries ALL records before filtering
2. ✅ Backend calculates statistics dict from ALL records
3. ✅ Backend passes both `filtered_items` and `statistics` to template
4. ✅ Template uses `statistics.xxx` for filter counts
5. ✅ Template uses `filtered_items` for table display

---

### Error 2: "All" Filter Never Gets Active State

**Symptom**: Clicking "All" doesn't show it as active (no white background)

**Wrong Implementation**:
```html
<!-- WRONG: show_all parameter not set in link -->
<a href="{{ url_for('list_items') }}"
   class="github-filter-btn {% if current_filters.show_all %}active{% endif %}">
```

**Root Cause**: The conditional checks for `current_filters.show_all` but the link doesn't set this parameter

**Correct Implementation - Option 1** (Add parameter to link):
```html
<a href="{{ url_for('list_items', show_all='true') }}"
   class="github-filter-btn {% if current_filters.show_all %}active{% endif %}">
```

**Correct Implementation - Option 2** (Change conditional logic):
```html
<a href="{{ url_for('list_items') }}"
   class="github-filter-btn {% if not current_filters.status and not current_filters.payment_status %}active{% endif %}">
```

**Choose Option 1** if you want explicit `show_all='true'` in URL
**Choose Option 2** if you want clean URL like `/activities` when showing all

---

### Error 3: Clear (X) Button Not Appearing

**Symptom**: Typing in search doesn't show the clear button

**Root Cause**: Missing or incorrect JavaScript initialization

**Debug Checklist**:
1. ✅ Check `search-component.css` is loaded
2. ✅ Verify `window.SearchComponent` exists (check browser console)
3. ✅ Confirm `SearchComponent.init()` is called on DOMContentLoaded
4. ✅ Check element ID is exactly `searchClearBtn`
5. ✅ Verify button has `style="display: none;"` initially
6. ✅ Test in browser console: `document.getElementById('searchClearBtn')`

**Quick Test**:
```javascript
// In browser console:
console.log(typeof window.SearchComponent); // Should show "object" not "undefined"
console.log(document.getElementById('searchClearBtn')); // Should show button element
```

**Fix**: Ensure this CSS file is loaded BEFORE your page's `<script>` section:
```html
<link rel="stylesheet" href="{{ url_for('static', filename='css/search-component.css') }}?v=1.0">
```

---

### Error 4: GitHub Filter Buttons Have Black Borders

**Symptom**: Filter buttons show ugly black borders instead of GitHub-style subtle dividers

**Wrong Implementation**:
```html
<!-- WRONG: Simplified classes without inline styles -->
<a href="..." class="github-filter-btn">Active</a>
```

**Correct Implementation**:
```html
<!-- CORRECT: Full inline styles from passport page -->
<a href="{{ url_for('list_items', status='active') }}"
   class="github-filter-btn {% if current_filters.status == 'active' %}active{% endif %}"
   style="{% if current_filters.status == 'active' %}background: #ffffff; color: #24292e; font-weight: 600; border: 1px solid #d1d5da; margin: -1px; z-index: 1; border-radius: 6px; box-shadow: 0 1px 0 rgba(27,31,35,0.04);{% else %}background: rgba(0, 0, 0, 0.03); color: #586069; margin: 0; border-right: 1px solid transparent; background-clip: padding-box; background-image: linear-gradient(to right, transparent 0%, transparent 100%), linear-gradient(180deg, transparent 20%, #d1d5da 20%, #d1d5da 80%, transparent 80%); background-size: 100% 100%, 1px 100%; background-position: center, right center; background-repeat: no-repeat;{% endif %} padding: 5px 12px; font-size: 14px; line-height: 20px; text-decoration: none; display: inline-flex; align-items: center; white-space: nowrap; position: relative;">
  <i class="ti ti-activity" style="font-size: 16px; margin-right: 4px;"></i>Active <span style="opacity: 0.6; margin-left: 4px;">({{ statistics.active_items }})</span>
</a>
```

**Key Point**: The inline styles are NOT optional - they create the GitHub appearance

---

### Error 5: Search Requires Pressing Enter

**Symptom**: Typing doesn't trigger search automatically

**Root Cause**: Auto-search logic not implemented or debounce not working

**Fix**: Ensure `SearchComponent.init()` is called with correct parameters:
```javascript
if (window.SearchComponent) {
    window.SearchComponent.init({
        formId: 'dynamicSearchForm',
        inputId: 'enhancedSearchInput',
        preserveParams: ['status', 'payment_status'] // Adjust to your filters
    });
}
```

The `SearchComponent` handles auto-search with 500ms debounce automatically.

---

### Error 6: Mobile "#" Column Makes Avatars Too Narrow

**Symptom**: On mobile, user avatars are squeezed

**Root Cause**: Having a mobile-only column that wasn't in the original design

**Fix**: Remove the mobile "#" column if it's not essential:
```html
<!-- REMOVE THIS: -->
<th class="d-md-none text-center">#</th>

<!-- AND REMOVE CORRESPONDING DATA CELL: -->
<td class="d-md-none text-center" style="vertical-align: middle;">
  <span class="fw-bold" style="color: #6c757d;">{{ count }}</span>
</td>
```

**Note**: The passport page does have this column and it works. Only remove if it's causing layout issues on your specific page.

---

## Verification Checklist

Use this checklist when implementing or reviewing a page conversion:

### Backend Requirements ✅
- [ ] Route queries ALL records before applying filters
- [ ] Statistics dict calculated from ALL records (not filtered results)
- [ ] Both `statistics` and `filtered_items` passed to template
- [ ] `current_filters` dict passed with all active filter states

**Example Backend Code**:
```python
# 1. Query ALL records first
all_items = YourModel.query.all()
all_items_count = YourModel.query.count()

# 2. Calculate statistics from ALL
active_items = len([i for i in all_items if i.status == 'active'])
inactive_items = len([i for i in all_items if i.status == 'inactive'])

statistics = {
    'total_items': all_items_count,
    'active_items': active_items,
    'inactive_items': inactive_items,
}

# 3. Apply filters for display
query = YourModel.query
if status_filter:
    query = query.filter_by(status=status_filter)
filtered_items = query.all()

# 4. Pass both to template
return render_template('your_page.html',
                     items=filtered_items,
                     statistics=statistics,
                     current_filters={'status': status_filter, ...})
```

### Frontend HTML Requirements ✅
- [ ] CSS files loaded in correct order (dropdown-fix, search-component, filter-component)
- [ ] Search form has `id="dynamicSearchForm"`
- [ ] Search input has `id="enhancedSearchInput"`
- [ ] Clear button has `id="searchClearBtn"` and `style="display: none;"`
- [ ] Keyboard hints have `d-none d-md-inline` classes
- [ ] Filter buttons use FULL inline styles from passport (not simplified)
- [ ] Filter counts use `{{ statistics.xxx }}` not Jinja filters
- [ ] Filter active state conditionals match link parameters
- [ ] Table uses responsive classes (`d-none d-md-table-cell`, etc.)
- [ ] Mobile view tested at 375px width

### JavaScript Requirements ✅
- [ ] `SearchComponent.init()` called with correct IDs
- [ ] `FilterComponent.init()` called with correct class
- [ ] `preserveParams` array includes all your filter parameters
- [ ] Console logs show no errors
- [ ] Ctrl+K shortcut focuses search
- [ ] Character counter appears when typing
- [ ] Clear button appears when typing
- [ ] Auto-search triggers after 500ms
- [ ] Search submits with 3+ characters or 0 characters

### Behavioral Testing ✅
- [ ] **Filter counts remain static** when clicking different filters
- [ ] **"All" filter shows active state** when clicked
- [ ] **Clear button appears** when typing in search
- [ ] **Auto-search works** without pressing Enter (500ms delay)
- [ ] **Keyboard shortcut Ctrl+K** focuses search
- [ ] **Mobile keyboard hints hide** when focused
- [ ] **Mobile view** shows correct columns at 375px width
- [ ] **Desktop view** shows all columns at 1920px width
- [ ] **Filter buttons** have GitHub-style appearance (no black borders)
- [ ] **Search preserves** active filter when typing

### Cross-Reference Testing ✅
- [ ] Compare behavior to `templates/passports.html`
- [ ] Filter counts match behavior in passport page
- [ ] Search behavior matches passport page
- [ ] Filter button styling matches passport page
- [ ] Mobile layout matches passport page

---

## Getting Help

### If Something Doesn't Work
1. Compare your code to `templates/activity_dashboard.html` (lines 1071-1220)
2. Check that all three CSS files are loaded in the correct order
3. Verify IDs match exactly (`enhancedSearchInput`, `searchKbdHint`, etc.)
4. Test JavaScript in browser console for errors
5. Check mobile view at 375px width

### Claude Code Sessions
When starting a new Claude Code session to convert a page:
1. Have Claude read this document first: `docs/DESIGN_SYSTEM.md`
2. Point Claude to the reference page: `templates/activity_dashboard.html`
3. Specify which page to convert
4. Claude will have all context needed to implement correctly

---

## Form Action Buttons

All form submit buttons follow a consistent color convention based on the action type.

### Button Color Convention

| Action Type | Color | Class | Examples |
|-------------|-------|-------|----------|
| **Save / Update / Create** | Green | `btn-success` | Update Activity, Save Settings, Create Passport, Save Changes |
| **Login / Send / Navigate** | Blue | `btn-primary` | Login, Send Invitations |
| **Delete / Destructive** | Red | `btn-danger` | Delete record |
| **Modal confirmations** | Blue | `btn-primary` | Yes Redeem, Yes Approve (keep as-is) |

### Usage Rules

1. **Save/Create/Update forms** always use `btn-success` (green). This includes any form that persists data: creating records, updating settings, saving templates, recording income/expenses.
2. **Login and send actions** use `btn-primary` (blue). Authentication and communication actions are not save operations.
3. **Destructive actions** use `btn-danger` (red). Any action that permanently removes data.
4. **Modal confirmation buttons** use `btn-primary` (blue). These are action confirmations within modals (e.g., Redeem, Approve & Create) and are distinct from form save operations.
5. **Cancel buttons** use `btn-outline-secondary` for a low-emphasis style.

### Reference

```html
<!-- Save/Create/Update form button -->
<button type="submit" class="btn btn-success">
  <i class="ti ti-check me-1"></i>Save Changes
</button>

<!-- Cancel button -->
<a href="{{ url_for('dashboard') }}" class="btn btn-outline-secondary">Cancel</a>

<!-- Login/Send action button -->
<button type="submit" class="btn btn-primary">
  <i class="ti ti-send me-1"></i>Send Invitations
</button>

<!-- Destructive action button -->
<button type="submit" class="btn btn-danger">
  <i class="ti ti-trash me-1"></i>Delete
</button>
```

---

## Pagination Component

### Overview
All tables in Minipass use standardized server-side pagination with Tabler.io styling for consistency and performance.

### Visual Components
- Entry counter on the left: "Showing 1 to 10 of 247 entries"
- Pagination controls on the right with smart ellipsis
- Previous/Next buttons with chevron icons
- Active page highlighted in blue
- Compact size (`pagination-sm`) for table footers

### HTML Structure

```html
<div class="card-footer d-flex justify-content-between align-items-center">
  <span class="text-muted">Showing 1 to 10 of 247 entries</span>
  <nav aria-label="Page navigation">
    <ul class="pagination pagination-sm mb-0">
      <li class="page-item">
        <a class="page-link" href="...">
          <i class="ti ti-chevron-left"></i>
        </a>
      </li>
      <li class="page-item active">
        <span class="page-link">1</span>
      </li>
      <li class="page-item">
        <a class="page-link" href="...">2</a>
      </li>
      <li class="page-item disabled">
        <span class="page-link">…</span>
      </li>
      <li class="page-item">
        <a class="page-link" href="...">50</a>
      </li>
      <li class="page-item">
        <a class="page-link" href="...">
          <i class="ti ti-chevron-right"></i>
        </a>
      </li>
    </ul>
  </nav>
</div>
```

### Using the Pagination Macro

**Step 1: Backend (Python)**
```python
@app.route("/your-page")
def your_page():
    page = request.args.get('page', 1, type=int)
    per_page = 10  # Use 10 for user data, 50 for logs

    pagination = YourModel.query.paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )
    items = pagination.items

    current_filters = {'filter1': request.args.get('filter1', '')}

    return render_template('your_template.html',
                         items=items,
                         pagination=pagination,
                         current_filters=current_filters)
```

**Step 2: Template (Jinja2)**
```jinja2
{% from 'macros/pagination.html' import render_pagination %}

{# After your table #}
</table>
</div>

{# Add pagination #}
{{ render_pagination(pagination, current_filters, items) }}
```

### Multi-Table Pagination

For pages with multiple paginated tables (e.g., Activity Dashboard), use custom page parameters:

**Backend:**
```python
@app.route("/activity-dashboard/<int:activity_id>")
def activity_dashboard(activity_id):
    passport_page = request.args.get('passport_page', 1, type=int)
    signup_page = request.args.get('signup_page', 1, type=int)
    per_page = 10

    passport_pagination = Passport.query.filter_by(
        activity_id=activity_id
    ).paginate(page=passport_page, per_page=per_page, error_out=False)

    signup_pagination = Signup.query.filter_by(
        activity_id=activity_id
    ).paginate(page=signup_page, per_page=per_page, error_out=False)

    current_filters = {
        'q': request.args.get('q', ''),
        'passport_page': passport_page,
        'signup_page': signup_page
    }

    return render_template('activity_dashboard.html',
                         passport_pagination=passport_pagination,
                         signup_pagination=signup_pagination,
                         current_filters=current_filters)
```

**Template:**
```jinja2
{# Passport table pagination #}
{{ render_pagination(passport_pagination,
    {'q': current_filters.q, 'signup_page': current_filters.signup_page},
    passes,
    page_param='passport_page') }}

{# Signup table pagination #}
{{ render_pagination(signup_pagination,
    {'q': current_filters.q, 'passport_page': current_filters.passport_page},
    signups,
    page_param='signup_page') }}
```

### Pagination Standards

**Items Per Page:**
- **10 items**: User-facing data (Passports, Activities, Signups, Surveys)
- **50 items**: Transaction logs (Activity Log, Payments)

**Tabler Classes:**
- `pagination` - Base pagination class
- `pagination-sm` - Compact size for tables
- `page-item` - Individual page button
- `page-link` - Clickable link
- `active` - Current page (blue highlight)
- `disabled` - Non-clickable items (Previous on page 1, ellipsis)

**Required Icons:**
- Previous: `<i class="ti ti-chevron-left"></i>`
- Next: `<i class="ti ti-chevron-right"></i>`

### Mobile Responsiveness

**CSS (in minipass.css):**
```css
@media (max-width: 767px) {
  /* Hide page numbers on mobile, keep Previous/Next */
  .pagination .page-item:not(:first-child):not(:last-child) {
    display: none;
  }

  /* Touch-friendly button sizing */
  .pagination .page-link {
    min-width: 44px;
    min-height: 44px;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  /* Stack pagination on mobile */
  .card-footer {
    flex-direction: column;
    gap: 0.5rem;
  }
}
```

**Mobile Behavior:**
- Page numbers hidden on screens < 767px
- Only Previous/Next buttons shown
- Touch-friendly 44px minimum button size
- Entry counter and controls stack vertically

### Smart Ellipsis Logic

Instead of showing all page numbers (1 2 3 4 5 6 7 8 9 10 ... 247), use smart ellipsis:

**Examples:**
- Page 1 of 50: `< 1 2 3 ... 50 >`
- Page 5 of 50: `< 1 ... 4 5 6 ... 50 >`
- Page 50 of 50: `< 1 ... 48 49 50 >`

**Implementation:**
```python
# In pagination macro
pagination.iter_pages(left_edge=1, right_edge=1, left_current=1, right_current=2)
```

### Filter State Preservation

Always preserve filter state when paginating:

**Backend:**
```python
current_filters = {
    'q': request.args.get('q', ''),
    'status': request.args.get('status', ''),
    'activity': request.args.get('activity', '')
}
```

**Template:**
```jinja2
{# URL generation automatically includes all current_filters #}
{{ render_pagination(pagination, current_filters, items) }}
```

### Accessibility

**Requirements:**
- `<nav aria-label="Page navigation">` wrapper
- `aria-label="Previous"` on Previous button
- `aria-label="Next"` on Next button
- Use `<span>` for disabled states (not `<a disabled>`)
- Keyboard navigable (links are naturally accessible)

### Examples in Codebase

**Good Examples:**
- `templates/passports.html` - Standard table pagination
- `templates/activity_log.html` - Transaction log pagination (50/page)
- `templates/signups.html` - User data pagination (10/page)
- `templates/activity_dashboard.html` - Multi-table pagination

**Pagination Macro:**
- `templates/macros/pagination.html` - Reusable macro for all pages

### Common Mistakes to Avoid

❌ **DON'T:**
- Use client-side JavaScript pagination
- Show all page numbers (1 2 3 4 5 6 7 8 9 10 ...)
- Forget to preserve filter state
- Use custom CSS styling
- Fetch all records with `.all()` then paginate in template
- Use `page` parameter for multi-table pagination (causes conflicts)

✅ **DO:**
- Use server-side pagination with `.paginate()`
- Use smart ellipsis for large page counts
- Preserve all filters in pagination URLs
- Use Tabler default classes only
- Paginate at database level for performance
- Use custom page parameters (`passport_page`, `signup_page`) for multiple tables

### Macro Parameters

The `render_pagination` macro accepts:
- `pagination` (required): Flask-SQLAlchemy pagination object
- `current_filters` (optional): Dict of query parameters to preserve
- `items` (optional): Current page items for accurate entry counter
- `page_param` (optional): Name of page parameter (default: 'page')

**Example with all parameters:**
```jinja2
{{ render_pagination(
    pagination=passport_pagination,
    current_filters={'q': search_query, 'status': status_filter},
    items=passports,
    page_param='passport_page'
) }}
```

---

---

## Section 15 — Photo Normalization Tool

**Reference implementation:** `templates/activity_form.html` (Cover Photo field)

This is the standard image picker used everywhere you need a user to provide a photo. It combines:
- 100×100 thumbnail preview with red-X remove button
- Click to expand a side panel with Search (Unsplash) / Upload toggle
- On upload: automatic crop modal (Cropper.js, drag/zoom, 16:9 aspect)
- On confirm: client-side JPEG compression (92% quality, max 1200×675)
- On save (server-side): PIL resize + JPEG 85% via `_save_optimized_image()`

**Never use a plain `<input type="file">` for image fields. Always use this tool.**

---

### ⛔ CRITICAL — COPY THE RECIPE EXACTLY. DO NOT MODIFY ANY CLASS.

The HTML in §15.2 is the **canonical recipe**. Every class, every attribute, every style must be copied verbatim. One wrong class breaks the entire visual.

**The most common mistake that WILL break the layout:**

```html
<!-- ❌ WRONG — -sm breaks the input-group flex row, button drops to next line -->
<input type="text" class="form-control form-control-sm" ...>
<button type="button" class="btn btn-primary btn-sm">

<!-- ✅ CORRECT — exact classes from §15.2, no size variants ever -->
<input type="text" class="form-control" ...>
<button type="button" class="btn btn-primary">
```

**Rule: The search panel input-group requires ALL children to use the same size variant. The correct variant is the DEFAULT (no `-sm`, no `-lg`). Never deviate.**

---

### ⛔ CRITICAL — CSS SPECIFICITY: never add a page-level `.form-control { width: 100% }` rule in a modal container

If your modal container has a CSS class with a rule like:

```css
/* ❌ This kills input-group layout — width:1% override from Bootstrap is defeated */
.my-modal-content .form-control { width: 100%; }
```

This has the **same specificity** as Bootstrap's `.input-group > .form-control { width: 1% }`. Since it appears later in the stylesheet, it wins — forcing the input to full width and pushing the button to the next line.

**Fix: add a restoration rule immediately after your `.form-control` rule:**

```css
.my-modal-content .form-control { width: 100%; }       /* general rule */
.my-modal-content .input-group > .form-control { width: 1%; }  /* restore input-group */
```

This was the cause of the search button appearing below the input in the email template modals (`email-template-customization.css`, `template-form-single-column`). The fix was adding the second line.

---

### ⛔ CRITICAL — TIMING: always call `initPhotoNormalizer()` AFTER the HTML is in the live DOM

If the widget HTML is **cloned into a modal** via `innerHTML =` (e.g. a dynamic template system), `initPhotoNormalizer()` must be called **after** the clone, not at `DOMContentLoaded`. The function captures element references at call time — calling it before the clone means it captures the hidden originals, not the visible copies.

```javascript
// ❌ WRONG — called at DOMContentLoaded before the clone
document.addEventListener('DOMContentLoaded', () => {
  initPhotoNormalizer({ wrapperId: 'myWrapper', ... });
});

// ✅ CORRECT — called immediately after innerHTML is set
container.innerHTML = templateHTML;   // clone first
initPhotoNormalizer({ wrapperId: 'myWrapper', ... });  // then init
```

---

### 15.1 — Dependencies (already global — nothing to add)

**Cropper.js CSS/JS and `photo-normalizer.js` are loaded globally in `base.html`.**
No per-page imports needed. The `initPhotoNormalizer()` function is available on every page.

---

### 15.2 — Widget HTML (inline in your form)

Adapt `FIELD_NAME`, `DEST_FOLDER`, `EXISTING_FILENAME` to your context.

```html
<!-- Photo Normalization Tool Widget -->
<div class="mb-3">
  <label class="form-label">Cover Photo</label>

  <div class="d-flex align-items-stretch rounded bg-secondary-lt overflow-hidden"
       style="border: 1px solid rgba(98,105,118,0.2); width: fit-content; max-width: 100%;">

    <!-- Left: Thumbnail — always visible, click to open options panel -->
    <div class="position-relative flex-shrink-0 d-flex flex-column align-items-center justify-content-center"
         style="width: 100px; min-height: 100px; cursor: pointer;" id="coverPhotoWrapper">
      {% if existing_filename %}
        <img id="coverThumbnail"
             src="{{ url_for('static', filename='uploads/DEST_FOLDER/' + existing_filename) }}"
             class="rounded" style="width: 100px; height: 100px; object-fit: cover;">
        <span class="position-absolute top-0 end-0 badge bg-danger rounded-circle p-2"
              style="cursor: pointer;" id="deleteImageBtn">
          <i class="ti ti-x text-white" style="font-size: 14px;"></i>
        </span>
      {% else %}
        <div id="coverThumbnail" class="d-flex flex-column align-items-center justify-content-center"
             style="width: 100px; height: 100px;">
          <i class="ti ti-photo text-muted fs-2"></i>
          <small class="text-muted">Add photo</small>
        </div>
      {% endif %}
    </div>

    <!-- Right: Options panel — hidden by default, toggled on thumbnail click -->
    <div id="imageOptions" class="flex-grow-1 p-2"
         style="display: none; border-left: 1px solid rgba(98,105,118,0.2);">
      <!-- Source toggle: Search ↔ Upload -->
      <div class="d-flex align-items-center gap-2 mb-3">
        <small class="text-muted fw-medium">
          <i class="ti ti-world-search" style="font-size:13px;"></i> Search
        </small>
        <label class="form-check form-switch mb-0">
          <input class="form-check-input" type="checkbox" id="sourceToggle" role="switch">
        </label>
        <small class="text-muted">
          <i class="ti ti-upload" style="font-size:13px;"></i> Upload
        </small>
      </div>

      <!-- Search tab -->
      <div id="searchWebContent">
        <div class="input-group">
          <input type="text" id="imageDescription" class="form-control" placeholder="e.g., Hockey, Yoga">
          <button type="button" id="searchImagesBtn" class="btn btn-primary">
            <i class="ti ti-search"></i>
          </button>
        </div>
      </div>

      <!-- Upload tab -->
      <div id="uploadContent" style="display: none;">
        <input type="file" name="upload_image" class="form-control" id="uploadInput" accept="image/*">
      </div>
    </div>

  </div>

  <!-- Hidden: tracks which already-saved file is selected (cleared on new upload) -->
  <input type="hidden" name="selected_image_filename" id="selectedImageFilename"
         value="{{ existing_filename or '' }}">
</div>
```

---

### 15.3 — Crop Modal HTML (place in `{% block modals %}`)

```html
<!-- Photo Normalization — Crop Modal -->
<div class="modal modal-blur fade" id="cropModal" tabindex="-1" aria-hidden="true">
  <div class="modal-dialog modal-lg modal-dialog-centered" role="document">
    <div class="modal-content">
      <div class="modal-header">
        <h5 class="modal-title">
          <i class="ti ti-crop me-2"></i>Adjust Cover Photo
        </h5>
        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
      </div>
      <div class="modal-body p-0" style="background:#1a1a2e;">
        <div style="max-height:60vh; overflow:hidden; display:flex; align-items:center; justify-content:center;">
          <img id="cropImage" src="" alt="Crop preview"
               style="display:block; max-width:100%; max-height:60vh;">
        </div>
        <div class="p-3 text-center">
          <small class="text-muted">
            <i class="ti ti-arrows-move me-1"></i>Drag to reposition
            <span class="mx-2">|</span>
            <i class="ti ti-zoom-in me-1"></i>Pinch or scroll to zoom
          </small>
        </div>
      </div>
      <div class="modal-footer">
        <button type="button" class="btn btn-outline-secondary" data-bs-dismiss="modal">
          <i class="ti ti-x me-1"></i>Cancel
        </button>
        <button type="button" class="btn btn-primary" id="cropConfirmBtn">
          <i class="ti ti-check me-1"></i>Use Photo
        </button>
      </div>
    </div>
  </div>
</div>

<!-- Unsplash image picker modal (required — the tool handles all JS internally) -->
<div class="modal modal-blur fade" id="unsplashModal" tabindex="-1" role="dialog" aria-hidden="true">
  <div class="modal-dialog modal-lg modal-dialog-centered" role="document">
    <div class="modal-content">
      <div class="modal-header">
        <h5 class="modal-title">Select an Image</h5>
        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
      </div>
      <div class="modal-body">
        <div id="unsplashImages" class="row g-3"></div>
        <div class="d-flex justify-content-between mt-3" style="display:none!important;">
          <button type="button" id="prevPageBtn" class="btn btn-outline-secondary" disabled>
            <i class="ti ti-chevron-left me-1"></i>Previous
          </button>
          <button type="button" id="nextPageBtn" class="btn btn-outline-secondary">
            Next<i class="ti ti-chevron-right ms-1"></i>
          </button>
        </div>
      </div>
    </div>
  </div>
</div>
```

---

### 15.4 — JavaScript: call `initPhotoNormalizer()` (in `{% block scripts %}`)

The shared factory is in `static/js/photo-normalizer.js` (loaded globally via `base.html`).
**Never copy-paste the old IIFE.** Call the factory instead:

```javascript
// Cover photo — 16:9 crop, Unsplash search enabled
var coverPhotoNormalizer = initPhotoNormalizer({
  // Required — upload/crop
  wrapperId:      'coverPhotoWrapper',
  uploadInputId:  'uploadInput',
  cropModalId:    'cropModal',
  cropImageId:    'cropImage',
  confirmBtnId:   'cropConfirmBtn',
  // Optional — options panel + toggle
  optionsPanelId: 'imageOptions',
  hiddenInputId:  'selectedImageFilename',   // set to filename on Unsplash pick; cleared on upload
  sourceToggleId: 'sourceToggle',
  searchPanelId:  'searchWebContent',
  uploadPanelId:  'uploadContent',
  // Optional — Unsplash search (tool handles all JS internally)
  searchInputId:    'imageDescription',
  searchBtnId:      'searchImagesBtn',
  unsplashModalId:  'unsplashModal',
  unsplashImagesId: 'unsplashImages',
  prevPageBtnId:    'prevPageBtn',
  nextPageBtnId:    'nextPageBtn',
  // Crop/compression
  aspectRatio:    16 / 9,   // NaN for free crop
  maxWidth:       1200,
  maxHeight:      675,
  objectFit:      'cover',
  placeholderLabel: 'Add photo',
});
```

**Config reference:**

| Option | Type | Default | Purpose |
|--------|------|---------|---------|
| `wrapperId` | string | required | Thumbnail `<div>` element ID |
| `uploadInputId` | string | required | `<input type="file">` element ID |
| `cropModalId` | string | required | Crop modal element ID |
| `cropImageId` | string | required | `<img>` inside crop modal |
| `confirmBtnId` | string | required | "Use Photo" button ID |
| `optionsPanelId` | string | null | Side options panel (shown/hidden on thumbnail click) |
| `hiddenInputId` | string | null | Set to filename on Unsplash pick; cleared on new upload |
| `sourceToggleId` | string | null | Search↔Upload checkbox toggle |
| `searchPanelId` | string | null | Search panel element ID |
| `uploadPanelId` | string | null | Upload panel element ID |
| `searchInputId` | string | null | Unsplash: text input for the search query |
| `searchBtnId` | string | null | Unsplash: button that triggers the search |
| `unsplashModalId` | string | null | Unsplash: modal showing the image grid |
| `unsplashImagesId` | string | null | Unsplash: `<div>` container for the image grid |
| `prevPageBtnId` | string | null | Unsplash: Previous page button ID |
| `nextPageBtnId` | string | null | Unsplash: Next page button ID |
| `aspectRatio` | number | NaN | Cropper aspect ratio (NaN = free) |
| `maxWidth` | number | 1200 | Max canvas width for compression |
| `maxHeight` | number | 800 | Max canvas height for compression |
| `quality` | number | 0.92 | JPEG quality (0–1) |
| `objectFit` | string | 'cover' | CSS object-fit for thumbnail |
| `placeholderLabel` | string | 'Add photo' | Text shown in empty state |
| `src` | string | null | Pre-populate thumbnail on init |
| `onConfirm` | function | null | Called with `(blob, objectUrl)` after crop confirmed **or** Unsplash pick |
| `onDelete` | function | null | Called when red-X delete badge is clicked |

**Public API returned:**

```javascript
coverPhotoNormalizer.setThumbnail(src);   // show image src as thumbnail
coverPhotoNormalizer.reset(src);          // reset: if src → thumbnail, else → placeholder
```

---

### 15.5 — Server-side: reuse `_save_optimized_image()` (`app.py:904`)

This helper handles all uploads. Call it in your route instead of saving raw bytes:

```python
# app.py:904
def _save_optimized_image(file_stream, dest_folder, prefix="upload", max_size=(1200, 800)):
    """Save uploaded image: resize to max dimensions, convert to JPEG quality=85.
    - Converts RGBA/palette to RGB with white background
    - Resizes with LANCZOS resampling (no upscaling)
    - Saves as JPEG quality=85, optimize=True
    Returns: filename (str)
    """
```

**Usage in a route:**

```python
upload_file = request.files.get('upload_image')
if upload_file and upload_file.filename:
    dest = os.path.join(current_app.root_path, 'static', 'uploads', 'activity_images')
    filename = _save_optimized_image(upload_file.stream, dest, prefix="activity")
    # filename is now e.g. "activity_a3f9b12c4d.jpg"
```

---

### 15.6 — Compression summary

| Stage | Tool | Format | Quality | Max size |
|-------|------|--------|---------|----------|
| Browser crop | Cropper.js → `canvas.toBlob()` | JPEG | 92% | 1200 × 675 |
| Server save | PIL `img.thumbnail()` + `img.save()` | JPEG | 85% | 1200 × 800 |
| Unsplash download | PIL (same as above) | JPEG | 85% | 1200 × 800 |

**Rule:** A 5 MB photo uploaded by a user will exit the pipeline as a ≤ 200 KB JPEG. This protects VPS performance and prevents page load slowness.

---

### 15.7 — Checklist when adding this tool to a new page

- [ ] Add widget HTML (§15.2) — update IDs, `DEST_FOLDER`, and `existing_filename`
- [ ] Add crop modal + Unsplash modal HTML (§15.3) into `{% block modals %}`
- [ ] Call `initPhotoNormalizer({...})` in `{% block scripts %}` (§15.4) with all element IDs — **no Unsplash JS to write**
- [ ] In your Flask route: use `_save_optimized_image()` instead of saving raw bytes; handle both `upload_image` (file upload) and `selected_image_filename` (Unsplash pick)

---

## Version History

**v1.0 - October 27, 2025**
- Initial design system documentation
- Based on Activity Dashboard and Passports pages
- Includes search, filters, and table components
- Mobile responsiveness patterns documented
- Complete code examples provided

**v1.5 - February 28, 2026**
- Added §15 critical warnings: NO `-sm` size classes in the search panel (breaks `input-group` flex row)
- Added §15 critical timing rule: `initPhotoNormalizer()` must be called AFTER `innerHTML =` clone, not at DOMContentLoaded
- Added §15 CSS specificity rule: page-level `.form-control { width:100% }` defeats Bootstrap's `input-group > .form-control { width:1% }` — must add restoration rule for `input-group` children
- These rules discovered while implementing email template hero images

**v1.4 - February 28, 2026**
- Moved Unsplash search/render/pagination logic fully into `photo-normalizer.js`
- Added 6 new config options: `searchInputId`, `searchBtnId`, `unsplashModalId`, `unsplashImagesId`, `prevPageBtnId`, `nextPageBtnId`
- `onConfirm` callback now fires on both crop confirmation and Unsplash image selection
- Removed all page-specific Unsplash JS from `activity_form.html` and `activity_dashboard.html`
- §15.3 updated: Unsplash modal is now standard (not optional)
- §15.4 updated: full config table with all 6 new Unsplash options
- §15.7 updated: checklist — no Unsplash JS to write, just pass IDs

**v1.3 - February 28, 2026**
- Refactored Photo Normalization Tool JS into shared `static/js/photo-normalizer.js`
- Cropper.js + photo-normalizer.js now loaded globally via `base.html`
- §15.1 updated: no per-page imports needed
- §15.4 updated: documents `initPhotoNormalizer()` API instead of copy-paste IIFE
- §15.7 updated: checklist simplified (3 steps instead of 5)

**v1.2 - February 28, 2026**
- Added Section 15: Photo Normalization Tool
- Documents the cover photo crop/compress/search component from `activity_form.html`
- Includes full HTML, JS, server-side helper, and reuse checklist

---

## Section 16 — Organization Avatar with Success Badge

**Template:** `templates/signup_confirmation.html`
**Use when:** Post-signup or post-payment confirmation screens — any "you're all set" page.

### What it looks like

A 100×100px square with rounded corners (the org logo or a colored fallback letter), with a small green circle badge overlapping the bottom-right corner. The badge animates in with a scale+fade after a short delay.

### HTML Structure

```html
<div class="logo-container">
  {% if settings.get('LOGO_FILENAME') %}
  <img src="{{ url_for('static', filename='uploads/' + settings['LOGO_FILENAME']) }}"
       alt="{{ settings.get('ORG_NAME', 'Organization') }}"
       class="organization-logo">
  {% else %}
  <div class="organization-logo-fallback"
       style="background: {{ placeholder_color(settings.get('ORG_NAME', activity.name)) }};">
    {{ placeholder_letter(settings.get('ORG_NAME', activity.name)) }}
  </div>
  {% endif %}

  <div class="success-badge">
    <i class="ti ti-check"></i>
  </div>
</div>
```

### Required CSS

```css
.logo-container {
  position: relative;
  width: 100px;
  height: 100px;
  margin: 0 auto 2rem;
}

.organization-logo {
  width: 100px;
  height: 100px;
  object-fit: contain;
  border-radius: 12px;
}

.organization-logo-fallback {
  width: 100px;
  height: 100px;
  border-radius: 12px;
  color: #fff;
  font-weight: 700;
  font-size: 3.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
}

.success-badge {
  position: absolute;
  bottom: -8px;
  right: -8px;
  width: 35px;
  height: 35px;
  background-color: #22c55e;
  border-radius: 50%;
  border: 3px solid #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  animation: badgeFadeIn 0.3s ease 0.4s backwards;
}

.success-badge i {
  font-size: 1.25rem;
  color: white;
}

@keyframes badgeFadeIn {
  0% { transform: scale(0.5); opacity: 0; }
  100% { transform: scale(1); opacity: 1; }
}

@media (prefers-reduced-motion: reduce) {
  .success-badge { animation: none; }
}
```

### Jinja2 Helpers

- `placeholder_color(name)` — deterministic background color from org/activity name
- `placeholder_letter(name)` — first letter of the name, uppercased

Both are registered as Jinja2 globals in `app.py`.

### Conditional Message Pattern (signup_confirmation.html)

```html
{% if signup.payment_method == 'stripe' and signup.paid %}
  <h1 class="thank-you-title">Paiement reçu!</h1>
  <p class="thank-you-message">Votre passeport a été envoyé à<br>
    <strong>{{ signup.user.email }}</strong></p>
{% elif signup.payment_method == 'stripe' and not signup.paid %}
  <h1 class="thank-you-title">Merci!</h1>
  <p class="thank-you-message">Votre paiement est en cours de traitement.<br>
    Vous recevrez un courriel de confirmation à<br>
    <strong>{{ signup.user.email }}</strong></p>
{% else %}
  <h1 class="thank-you-title">Merci!</h1>
  <p class="thank-you-message">Les prochaines étapes ont été envoyées à<br>
    <strong>{{ signup.user.email }}</strong></p>
{% endif %}
```

### Routes that use this template

| Route | Function |
|-------|----------|
| `/signup/thank-you/<id>` | `signup_thank_you` (Interac flow) |
| `/signup/stripe-success` | `stripe_success` (Stripe flow) |

---

**v1.4 - March 3, 2026**
- Added Section 16: Organization Avatar with Success Badge
- Documents the unified confirmation page pattern (`signup_confirmation.html`)
- Replaces two separate templates (`signup_thank_you.html`, `stripe_success.html`)

---

**This document is the single source of truth for UI consistency across Minipass. When in doubt, refer to the reference pages and this guide.**
