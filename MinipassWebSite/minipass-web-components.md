# Minipass Web Components — Design System

> Single source of truth for all interactive UI components on minipass.me.
> Every button on the site must use one of these patterns. No exceptions.

---

## Button System

### Philosophy

One primary color. One secondary color. One shape. Everywhere.
- Border-radius: **8px** on ALL buttons — no pills, no sharp squares
- Transition: **`all 0.2s ease`** on ALL hover states
- Font: **15px, weight 500**

---

## Primary Button

**Use for:** The single most important action on any page — S'abonner, M'abonner, Je m'abonne, submit forms.

| Property | Value |
|----------|-------|
| Background | `#17A85A` (green — Niagara) |
| Text color | `#ffffff` |
| Border | none |
| Border-radius | `8px` |
| Height (large) | `56px` |
| Height (medium) | `42px` |
| Min-width (large) | `180px` |
| Min-width (medium) | `158px` |
| Font size | `15px` |
| Font weight | `500` |

**Hover effect:**
| Property | Value |
|----------|-------|
| Background | `#128f4c` (darker green) |
| Box-shadow | `0 4px 16px rgba(23, 168, 90, 0.35)` |
| Transition | `all 0.2s ease` |

**HTML class (large):**
```html
<a class="btn btn--lg-2 btn-niagara text-white">Label</a>
```

**HTML class (medium/nav):**
```html
<a class="btn btn--medium-4 btn-niagara text-white">Label</a>
```

**CSS class used:** `btn-niagara` + `shadow--niagara` (optional glow on CTAs)

---

## Secondary Button

**Use for:** Supporting actions — Voir les forfaits, Voir les articles, back/cancel actions.

| Property | Value |
|----------|-------|
| Background | `#262729` (near-black — Shark) |
| Text color | `#ffffff` |
| Border | none |
| Border-radius | `8px` |
| Height (large) | `56px` |
| Height (medium) | `42px` |

**Hover effect:**
| Property | Value |
|----------|-------|
| Background | `#3a3b3d` (slightly lighter) |
| Box-shadow | `0 4px 16px rgba(0, 0, 0, 0.25)` |
| Transition | `all 0.2s ease` |

**HTML class (large):**
```html
<a class="btn btn--lg-2 btn-shark text-white">Label</a>
```

**CSS class used:** `btn-shark`

---

## Ghost / Outline Button

**Use for:** Low-emphasis actions on colored backgrounds — blog links, contact links.

| Property | Value |
|----------|-------|
| Background | `transparent` |
| Text color | `#17A85A` |
| Border | `2px solid #17A85A` |
| Border-radius | `8px` |

**Hover effect:**
| Property | Value |
|----------|-------|
| Background | `#17A85A` |
| Text color | `#ffffff` |
| Transition | `all 0.2s ease` |

**HTML example:**
```html
<a class="btn fw-semibold" style="border:2px solid #17A85A; color:#17A85A; background:transparent; padding:10px 28px;">
  Label
</a>
```

---

## Rules — What NOT to Do

| ❌ Don't | ✅ Do instead |
|----------|--------------|
| Use `rounded-50` on any button | Use default `8px` from `.btn` class |
| Use `btn-bittersweet` for CTAs | Use `btn-niagara` (green is the primary CTA color) |
| Use orange for subscribe/pay actions | Orange is for video/demo/awareness only |
| Different button colors per pricing tier | ALL pricing tiers use the same primary (green) button |
| Inline `border-radius: 50px` | Remove it — the base `.btn` handles it |

---

## Color Reference

| Name | Hex | Role |
|------|-----|------|
| Niagara (green) | `#17A85A` | Primary button, all CTAs |
| Niagara hover | `#128f4c` | Primary button hover |
| Shark (dark) | `#262729` | Secondary button |
| Shark hover | `#3a3b3d` | Secondary button hover |
| Bittersweet (orange) | `#F7931E` | Video/demo CTA only — NOT for subscribe |

---

## Usage Map — Current Site

| Page | Button | Correct class |
|------|--------|---------------|
| index.html hero | "Découvrir" (video) | `btn-bittersweet` ← orange OK here (it's a video CTA) |
| index.html hero | "Voir les forfaits" | `btn-shark` |
| index.html pricing ×3 | "M'abonner" | `btn-niagara` ✓ |
| base.html nav | "S'abonner" | `btn-niagara` (consider changing from shark) |
| about.html | "S'abonner" | `btn-niagara` ✓ |
| guides.html | "Nous contacter" | `btn-niagara` ✓ |
| blog/guides | Filter chips | `.filter-btn` 8px ✓ |
| index.html newsletter | "Je m'abonne" | inline 8px ✓ |
