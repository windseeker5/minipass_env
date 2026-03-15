# Multilingual Strategy for Minipass — Options & Best Practices

**Date:** February 2026
**Status:** Evaluation / Research — No implementation yet

---

## Your Current State

| Surface | Language | How text is handled |
|---------|----------|-------------------|
| Admin UI (dashboard, settings, etc.) | English | Hardcoded in 75 templates + 186 `flash()` calls |
| Public pages (signup form, thank-you) | English | Hardcoded, `lang="en"` |
| Email templates (7 types) | French | Variable-driven via `email_defaults.json` + per-activity overrides |
| Survey templates | French | One hardcoded French template |
| i18n library installed | None | No Flask-Babel, no gettext, nothing |

You have a **split-language app** — common for Canadian SaaS targeting Quebec orgs. The good news: your email template system is already variable-driven (Jinja2 + JSON defaults + per-activity overrides), which is 90% of the architecture you'd need.

---

## What Other Companies Do

**Small Canadian SaaS (your category):** Most ship in one language, then add the second pragmatically. The common pattern:

1. **Phase 1:** Launch in primary language. Focus on product-market fit. *(You're past this.)*
2. **Phase 2:** Add second language for **customer-facing surfaces only** (emails, signup forms, public pages). Leave admin UI in primary language.
3. **Phase 3:** If demand exists, internationalize admin UI with Flask-Babel.

**Key insight:** For B2B SaaS like Minipass, your *admins* (activity managers) are few and can handle English. Your *end users* (participants receiving emails, filling signup forms) are many and care about language. **Prioritize end-user surfaces.**

---

## Your 3 Options — From Simplest to Most Complete

### Option 1: "Email-Only Bilingual" (MVP)

**Effort:** 1-2 days | **Risk:** Very low | **Impact:** High

What you do:
- Add a `language` field to the Activity model (`'en'` or `'fr'`, default `'fr'`)
- Create `email_defaults_en.json` alongside the existing French one
- When sending emails, load defaults based on the activity's language setting
- Add a language dropdown in the Activity settings page

What you DON'T touch:
- Admin UI stays English
- No Flask-Babel needed
- No `.po` files, no `_()` wrapping, no compilation step

**Why this works:** Your email template system already loads defaults from JSON and overlays per-activity customizations. You're just adding a language dimension to the JSON lookup. Your existing architecture supports this naturally.

**Best for:** Getting bilingual emails shipped fast with near-zero risk.

---

### Option 2: "Public Pages + Emails" (Recommended sweet spot)

**Effort:** 3-5 days | **Risk:** Low | **Impact:** High

Everything from Option 1, plus:
- Make signup form, thank-you page, and QR scan page bilingual
- Use a simple JSON translation approach (`lang/en.json`, `lang/fr.json`) with a `_()` helper
- Add a `language` field to the User model too
- Detect language from browser `Accept-Language` header for anonymous visitors

What you DON'T touch:
- Admin UI stays English
- Still no Flask-Babel (simple JSON dictionary is enough for ~50 public-facing strings)

**Best for:** Full bilingual experience for end users without touching the admin interface.

---

### Option 3: "Full Flask-Babel" (Professional, Scalable)

**Effort:** 5-10 days | **Risk:** Medium | **Impact:** Complete

- Install Flask-Babel
- Wrap all 186 `flash()` calls with `_()`
- Wrap all hardcoded strings in 75 templates with `{{ _('...') }}`
- Extract → translate → compile `.po` files
- Use `force_locale()` to send emails in the recipient's language
- Add language toggle to admin navbar

**Risk factors:**
- Touching every template and every flash message = high regression risk
- Every future feature requires maintaining both languages
- `.po` file workflow adds friction: extract → update → edit → compile for every batch of changes

**Best for:** If you have paying customers demanding a French admin UI.

---

## Risk Analysis

| Risk | Severity | Applies to |
|------|----------|-----------|
| **Regression from touching all files** | High | Option 3 only |
| **Maintenance burden** (every new feature needs 2 translations) | Medium | Options 2 & 3 |
| **String concatenation breaks** (French word order differs from English) | Medium | Options 2 & 3 |
| **Mixed-language UX** (missing one translation = jarring) | Medium | Options 2 & 3 |
| **User-generated content stays monolingual** (activity names, custom email text) | Low | All options |
| **Performance impact** | Negligible | All options |

---

## Language Selection — How Should Users Choose?

For your app, the right strategy depends on the user type:

| User type | Strategy | Why |
|-----------|----------|-----|
| **Email recipients** (participants) | Store `language` on User or Activity model | Admin sets it once, all emails respect it |
| **Admin UI** (activity managers) | Session cookie + browser detection fallback | Simple toggle in navbar, persists per session |
| **Public pages** (signup form) | Inherit from Activity's language setting | The signup page URL already has the activity context |

**Skip URL prefixes** (`/en/dashboard`, `/fr/dashboard`). Your app is an authenticated SaaS dashboard, not a public website. URL-based language adds complexity with zero benefit for your use case.

---

## Recommendation

**Start with Option 1** (email-only bilingual). Here's why it fits your situation:

1. Your 2 production customers (LHGI, hockey coach) are Quebec-based — French emails are correct for them
2. But future customers may need English emails — Option 1 makes this a per-activity setting
3. It builds on your existing `email_defaults.json` architecture — natural evolution, not a rewrite
4. Risk is near-zero: you're adding a JSON file and a model field, not refactoring 75 templates
5. It's shippable in 1-2 days

Then if demand proves it, move to Option 2 (public pages) later. Option 3 (full Flask-Babel) only if a paying customer specifically needs a French admin panel.

---

## Technical Reference

### Flask-Babel — How It Works (if needed later)

Flask-Babel (v4.0.0) is the standard i18n library for Flask. It wraps Python's `babel` library and the GNU `gettext` system:

- **String translation** via `gettext()` / `_()` functions
- **Date/time/number/currency formatting** per locale
- **Jinja2 integration** (auto-injects `_()` into templates)
- **Locale selection** (browser detection, session, user profile)

#### The Translation Workflow (4 steps)

**Step 1 — Mark strings:**
```python
# Python
flash(_('Signup not found.'), 'error')
```
```html
<!-- Jinja2 -->
<h1>{{ _('Dashboard') }}</h1>
```

**Step 2 — Extract:**
```bash
pybabel extract -F babel.cfg -k lazy_gettext -o messages.pot .
```

**Step 3 — Initialize or update:**
```bash
pybabel init -i messages.pot -d translations -l fr    # new language
pybabel update -i messages.pot -d translations         # update existing
```

**Step 4 — Compile:**
```bash
pybabel compile -d translations
```

#### Directory structure
```
app/
  translations/
    fr/
      LC_MESSAGES/
        messages.po    (human-editable translations)
        messages.mo    (compiled binary, used at runtime)
    en/
      LC_MESSAGES/
        messages.po
        messages.mo
  babel.cfg
```

#### Key function: `force_locale()`

Critical for your use case — renders content in a different language than the user's current locale:
```python
# User browses UI in English, but email sends in French
with force_locale('fr'):
    html = render_template('email_template.html', **context)
```

### Alternative Approaches

| Approach | Pros | Cons | Best for |
|----------|------|------|----------|
| **JSON dictionary files** | Dead simple, no compilation, hot-reloadable | No auto-extraction, no pluralization, manual maintenance | MVP with 2 languages, small team |
| **Database-driven** | Editable via admin UI, fits per-tenant customization | Performance overhead, no standard tooling, overkill for 2 languages | User-generated translatable content only |
| **Hybrid (JSON emails + Flask-Babel UI)** | Best of both worlds, builds on existing architecture | Two systems to maintain | Most practical for Minipass |

---

## Sources

- [Flask-Babel 4.0.0 Official Documentation](https://python-babel.github.io/flask-babel/)
- [Miguel Grinberg — The Flask Mega-Tutorial Part XIII: I18n and L10n](https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-xiii-i18n-and-l10n)
- [Phrase — Flask App Tutorial on Internationalization](https://phrase.com/blog/posts/flask-app-tutorial-i18n/)
- [PetersPython — Building a Multilanguage Flask Website](https://www.peterspython.com/en/blog/building-a-multilanguage-flask-website-with-flask-babel)
- [Paddle — SaaS International Expansion Challenges](https://www.paddle.com/blog/saas-international-expansion)
- [Smartling — i18n Benefits and Best Practices](https://www.smartling.com/blog/i18n)
- [Crowdin — Complete i18n Guide](https://crowdin.com/blog/complete-i18n-guide)
