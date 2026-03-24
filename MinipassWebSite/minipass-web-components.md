# Minipass Design System

> Source of truth for typography, colors, and buttons across minipass.me.
> The index page is the reference. Every page must conform to these standards.

---

## Brand Colors

| Name | Hex | RGB | Role |
|------|-----|-----|------|
| **Burnt Sienna** | `#E8794E` | `rgb(232, 121, 78)` | Primary accent -- buttons, labels, links, hover states |
| **Voodoo** | `#483550` | `rgb(72, 53, 80)` | Secondary -- nav active, social icons, outline buttons, newsletter bg |

### Supporting Colors

| Name | Hex | Role |
|------|-----|------|
| Dark heading | `#0E1A35` | Page titles (h1) |
| Heading 2 | `#262729` | Section headings (h2), via `var(--color-headings-2)` |
| Body text | `#2d3748` | Paragraph text |
| Muted text | `#6B7280` | Subtitles, secondary descriptions |
| Light muted | `#8492AF` | Team card descriptions, tertiary text |

---

## Typography

**Font family:** Rubik, sans-serif (site-wide)

### Hierarchy

| Level | Element | Weight | Size | Color | CSS class |
|-------|---------|--------|------|-------|-----------|
| **Page title** | `h1` | 700 (fw-bold) | `display-4` (~50px) | `#0E1A35` | `display-4 fw-bold` |
| **Section heading** | `h2` | 500 | 32/38/48px responsive | `#262729` | `section-title__heading` |
| **Story heading** | `h2` | 700 (fw-bold) | 28px | `#E8794E` | `fw-bold` + inline style |
| **Section label** | `h6` | 500 | 18px | `#E8794E` | `section-title__sub-heading text-bittersweet text-uppercase` |
| **Body text** | `p` | 400 | 16px | `#2d3748` | line-height: 1.7 |
| **CTA text** | `p` | 600 | 26px | `#2d3748` | inline style |

### Section Label (h6)

Used above section headings as small uppercase accent text.

```html
<h6 class="section-title__sub-heading text-bittersweet text-uppercase mb-3">
  LABEL TEXT
</h6>
```

The `section-title__sub-heading` class provides: font-size 18px, font-weight 500, letter-spacing normal.
The `text-bittersweet` class provides: color #E8794E.

**Do NOT** use inline `style="color: #E8794E; font-weight: 600; letter-spacing: 2px;"` -- use the classes above.

### Story/Accent Heading (h2)

Used on narrative pages (about, etc.) for section titles that are colored accents.

```html
<h2 class="fw-bold mb-4" style="color: #E8794E; font-size: 28px;">
  Heading text
</h2>
```

### Body Text

```html
<p style="font-size: 16px; font-weight: 400; line-height: 1.7; color: #2d3748;">
  Paragraph content
</p>
```

---

## Button System

### Philosophy

Two brand colors. One shape. Everywhere.
- Border-radius: **8px** on ALL buttons
- Transition: **`all 0.2s ease`** on ALL hover states

---

### Primary Button (Burnt Sienna)

**Use for:** ALL main CTAs -- M'abonner, S'abonner, Je m'abonne, submit forms, subscribe, pricing.

| Property | Value |
|----------|-------|
| Background | `#E8794E` (Burnt Sienna) |
| Text color | `#ffffff` |
| Border | `#E8794E` |
| Border-radius | `8px` |

**Hover:**
| Property | Value |
|----------|-------|
| Background | `#d4683d` |
| Border | `#c96138` |
| Box-shadow | `0 0 0 0.2rem rgba(232, 121, 78, 0.5)` (on focus) |

**HTML (large):**
```html
<a class="btn btn--lg-2 btn-bittersweet text-white">Label</a>
```

**HTML (medium/nav):**
```html
<a class="btn btn--medium-4 btn-bittersweet text-white">Label</a>
```

**CSS class:** `btn-bittersweet`

---

### Secondary Button (Voodoo)

**Use for:** Supporting actions -- Voir les forfaits, back/cancel.

| Property | Value |
|----------|-------|
| Background | `#483550` (Voodoo) |
| Text color | `#ffffff` |
| Border | `#483550` |
| Border-radius | `8px` |

**Hover:**
| Property | Value |
|----------|-------|
| Background | `#5a4363` |
| Border | `#5a4363` |

**HTML (large):**
```html
<a class="btn btn--lg-2 btn-slate text-white">Label</a>
```

**CSS class:** `btn-slate`

---

### Ghost / Outline Button (Voodoo)

**Use for:** Low-emphasis actions on light backgrounds -- Voir tous les articles, blog links.

| Property | Value |
|----------|-------|
| Background | `transparent` |
| Text color | `#483550` (Voodoo) |
| Border | `2px solid #483550` |
| Border-radius | `8px` |

**Hover:**
| Property | Value |
|----------|-------|
| Background | `#483550` |
| Text color | `#ffffff` |

**HTML:**
```html
<a class="btn fw-semibold"
   style="border:2px solid #483550; color:#483550; background:transparent;
          padding:10px 28px; border-radius:8px; transition: background 0.2s ease, color 0.2s ease;"
   onmouseover="this.style.background='#483550';this.style.color='#fff';"
   onmouseout="this.style.background='transparent';this.style.color='#483550';">
  Label
</a>
```

---

## Social Icons

### Footer Contact Icons

Default: Voodoo (`#483550`). Hover: Burnt Sienna (`#E8794E`).

```css
.footer-contact-icon { color: #483550; transition: color 0.2s ease; }
li:hover .footer-contact-icon { color: #E8794E; }
```

### Team Member Social Icons

Same pattern as footer -- Voodoo default, Burnt Sienna on hover.

```css
.social-group a { color: #483550; transition: color 0.2s ease; }
.social-group a:hover { color: #E8794E; }
```

---

## Navigation

| State | Text color | Underline |
|-------|-----------|-----------|
| Default | `#7a7189` | none |
| Hover | `#483550` (Voodoo) | Burnt Sienna `#E8794E`, 2px |
| Active page | `#483550` (Voodoo), weight 600 | Burnt Sienna `#E8794E`, 2px |

Nav CTA button: `btn-bittersweet` (Burnt Sienna).

---

## Usage Map

| Page | Element | Class / Style |
|------|---------|---------------|
| index.html hero | "Decouvrir" (video) | `btn-bittersweet` |
| index.html hero | "Voir les forfaits" | `btn-slate` (Voodoo) |
| index.html pricing x3 | "M'abonner" | `btn-bittersweet` |
| index.html newsletter | "Je m'abonne" | `btn-bittersweet` |
| index.html blog | "Voir tous les articles" | Ghost outline (Voodoo) |
| base.html nav | "S'abonner" | `btn-bittersweet` |
| about.html CTA | "S'abonner" | `btn-bittersweet` |
| about.html labels | h6 section labels | `section-title__sub-heading text-bittersweet text-uppercase` |
| about.html headings | h2 story headings | `fw-bold` + `color: #E8794E; font-size: 28px` |
| about.html social | Team member icons | Voodoo default, Burnt Sienna hover |
