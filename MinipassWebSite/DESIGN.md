---
name: minipass
description: The arena after the lights go down. A dark page where real product screens and the five logo colors are the only light.
colors:
  logo-orange: "#F46F1C"
  logo-rose: "#E31A5A"
  logo-prune: "#9F1574"
  logo-violet: "#5A2692"
  logo-bleu: "#103B99"
  rose-light: "#EC2D6A"
  prune-light: "#C0359A"
  violet-light: "#8A5CD4"
  bleu-light: "#4C78E6"
  rose-deep: "#C4144D"
  newsletter-rose: "#C8164F"
  ground: "#110E18"
  panel: "#1A1623"
  panel-raised: "#221D2D"
  line: "#2D2839"
  line-strong: "#3F3850"
  text: "#F3F1F7"
  muted: "#ADA7BC"
  faint: "#9790A6"
  white: "#FFFFFF"
  button-hover: "#E9E5F2"
  success: "#4ADE80"
  error: "#FF7A9C"
typography:
  display:
    fontFamily: "MP Montserrat, Montserrat, Helvetica Neue, Arial, sans-serif"
    fontSize: "clamp(38px, 4.6vw, 60px)"
    fontWeight: 800
    lineHeight: 1.04
    letterSpacing: "-0.025em"
  headline:
    fontFamily: "MP Montserrat, Montserrat, Helvetica Neue, Arial, sans-serif"
    fontSize: "clamp(30px, 3.4vw, 42px)"
    fontWeight: 800
    lineHeight: 1.1
    letterSpacing: "-0.02em"
  headline-sm:
    fontFamily: "MP Montserrat, Montserrat, Helvetica Neue, Arial, sans-serif"
    fontSize: "clamp(28px, 3vw, 36px)"
    fontWeight: 800
    lineHeight: 1.15
    letterSpacing: "-0.02em"
  title:
    fontFamily: "MP Montserrat, Montserrat, Helvetica Neue, Arial, sans-serif"
    fontSize: "20px"
    fontWeight: 700
    lineHeight: 1.15
  quote:
    fontFamily: "MP Montserrat, Montserrat, Helvetica Neue, Arial, sans-serif"
    fontSize: "clamp(19px, 2.1vw, 27px)"
    fontWeight: 600
    lineHeight: 1.42
    letterSpacing: "-0.01em"
  numeral:
    fontFamily: "MP Montserrat, Montserrat, Helvetica Neue, Arial, sans-serif"
    fontSize: "50px"
    fontWeight: 800
    lineHeight: 1
    letterSpacing: "-0.03em"
    fontFeature: "tnum"
  lead:
    fontFamily: "MP Inter, Inter, system-ui, -apple-system, Segoe UI, sans-serif"
    fontSize: "19px"
    fontWeight: 400
    lineHeight: 1.6
  body:
    fontFamily: "MP Inter, Inter, system-ui, -apple-system, Segoe UI, sans-serif"
    fontSize: "16px"
    fontWeight: 400
    lineHeight: 1.6
  body-sm:
    fontFamily: "MP Inter, Inter, system-ui, -apple-system, Segoe UI, sans-serif"
    fontSize: "15.5px"
    fontWeight: 400
    lineHeight: 1.6
  button:
    fontFamily: "MP Inter, Inter, system-ui, -apple-system, Segoe UI, sans-serif"
    fontSize: "16px"
    fontWeight: 600
    lineHeight: 1
  label:
    fontFamily: "MP Inter, Inter, system-ui, -apple-system, Segoe UI, sans-serif"
    fontSize: "12px"
    fontWeight: 700
    lineHeight: 1.3
    letterSpacing: "0.1em"
rounded:
  xs: "7px"
  sm: "10px"
  md: "12px"
  lg: "16px"
  xl: "20px"
  xxl: "24px"
  pill: "999px"
spacing:
  hairline: "1px"
  gap: "18px"
  gutter-mobile: "20px"
  panel-pad: "30px"
  gutter: "32px"
  head-gap: "52px"
  section-mobile: "68px"
  section: "104px"
  container: "1180px"
components:
  button-primary:
    backgroundColor: "{colors.white}"
    textColor: "{colors.ground}"
    typography: "{typography.button}"
    rounded: "{rounded.md}"
    padding: "0 24px"
    height: "50px"
  button-primary-hover:
    backgroundColor: "{colors.button-hover}"
    textColor: "{colors.ground}"
  button-line:
    backgroundColor: "transparent"
    textColor: "{colors.white}"
    typography: "{typography.button}"
    rounded: "{rounded.md}"
    padding: "0 24px"
    height: "50px"
  button-compact:
    backgroundColor: "{colors.white}"
    textColor: "{colors.ground}"
    rounded: "{rounded.md}"
    padding: "0 18px"
    height: "42px"
  feature-panel:
    backgroundColor: "{colors.panel}"
    textColor: "{colors.text}"
    rounded: "{rounded.lg}"
    padding: "30px 28px 28px"
  plan-card:
    backgroundColor: "{colors.panel}"
    textColor: "{colors.text}"
    rounded: "{rounded.xl}"
    padding: "30px"
  plan-card-popular:
    backgroundColor: "{colors.panel-raised}"
    textColor: "{colors.text}"
    rounded: "{rounded.xl}"
    padding: "30px"
  billing-toggle:
    backgroundColor: "{colors.panel}"
    textColor: "{colors.muted}"
    rounded: "{rounded.pill}"
    padding: "4px"
  billing-toggle-active:
    backgroundColor: "{colors.white}"
    textColor: "{colors.ground}"
    rounded: "{rounded.pill}"
    padding: "9px 18px"
  badge:
    backgroundColor: "{colors.rose-deep}"
    textColor: "{colors.white}"
    typography: "{typography.label}"
    rounded: "{rounded.pill}"
    padding: "6px 10px"
  input-field:
    backgroundColor: "{colors.ground}"
    textColor: "{colors.white}"
    rounded: "11px"
    padding: "0 14px"
    height: "48px"
  input-on-color:
    backgroundColor: "{colors.white}"
    textColor: "{colors.ground}"
    rounded: "{rounded.md}"
    padding: "0 18px"
    height: "52px"
  post-card:
    backgroundColor: "{colors.panel}"
    textColor: "{colors.text}"
    rounded: "{rounded.lg}"
    padding: "22px 24px 26px"
  dialog-signup:
    backgroundColor: "{colors.panel-raised}"
    textColor: "{colors.text}"
    rounded: "22px"
    width: "480px"
  nav-link:
    textColor: "{colors.muted}"
  nav-link-active:
    textColor: "{colors.white}"
---

# Design System: minipass

## Overview

**Creative North Star: "Aréna de nuit"**

The arena after the lights go down. The ground is a near-black violet, and nothing on it glows except two things: the real product screens and the five colors of the logo. Color is never paint here; it is light. It lands on three words of the headline, a short stroke at the top of a feature panel, a big step numeral, a small list marker, and once per page, a full band from rose to violet. Everything else is quiet neutrals and 1px hairlines.

The density is calm and generous: one idea per section, sections separated by a hairline and 104px of air, content held in a 1180px column. Titles speak in Montserrat at heavy weights with tight tracking; everything you read speaks in Inter, the same face the minipass app uses, so the page and the product screens share a voice. There is one calm button style, solid white, with a hairline ghost beside it. It refuses the white SaaS template with a split hero and a row of identical cards: panels vary in width, the steps sit in one bordered strip, and proof comes from real captures.

This dark world is the marketing surface. Reading pages (guides, blog articles, subscription policies) are planned to use a light variant of the same system: same fonts, same components, same exact logo colors, on a white ground. That variant is not built yet and has no tokens; see Colors.

**Key Characteristics:**
- Near-black violet ground with two tonal steps for panels, separated by 1px hairlines.
- The five logo colors appear only as light: headline words, 4px top strokes, step numerals, list markers, one gradient band.
- Montserrat 800 for titles, numerals and prices; Inter for all running text and controls.
- One button language: solid white primary, hairline ghost secondary, 12px corners.
- Real app captures are the only imagery, and the only things that cast real shadows.

## Colors

A violet-black night with five logo hues used as points of light, never as surfaces.

### Primary
- **Logo Bars** (logo-orange, logo-rose, logo-prune, logo-violet, logo-bleu): the exact brand-sheet hues. Used for the logo bars wherever the logo appears, on any ground, and as the stops of the newsletter gradient. Never altered, never lifted.
- **Arena Orange** (logo-orange, used as is): bright enough on the dark ground, so it doubles as its own light version. First headline word, first step numeral, feature stroke.
- **Signal Rose** (rose-light): the lead accent. Second headline word, emphasis inside the testimonial, list markers in pricing, the popular plan's ring, blog category labels, the "-50 %" saving in the billing toggle.

### Secondary
- **Night Violet** (violet-light): third headline word, third step numeral, feature stroke. Reads as the cool end of the glow.
- **Prune Glow** (prune-light) and **Rink Blue** (bleu-light): feature-panel strokes only. They complete the five-color set; they do not carry text.

### Tertiary
- **Deep Rose** (rose-deep): solid fill for small uppercase badges ("Populaire", savings) where white text needs a darker rose behind it.
- **Band Rose** (newsletter-rose): the first stop of the newsletter band, `linear-gradient(100deg, newsletter-rose, logo-prune 55%, logo-violet)`.

### Neutral
- **Arena Night** (ground): the page, input wells, the dark text on white buttons. Also the `theme-color`.
- **Bench** (panel): feature panels, plan cards, post cards, the billing toggle track.
- **Raised Bench** (panel-raised): the popular plan, the mobile menu, the signup dialog, toasts, post-image placeholders.
- **Hairline** (line): section dividers, panel borders, the header border once scrolled.
- **Strong Hairline** (line-strong): ghost-button rings, input borders, hover borders, the language chip.
- **Ice** (text): primary text. Pure white (white) is reserved for buttons, active nav, and hover states.
- **Muted** (muted): leads, panel copy, nav links at rest, secondary labels.
- **Faint** (faint): fine print, copyright, price notes, placeholders.
- **Status** (success, error): help text under fields and toast dots only.

### Variant: Paper (reading pages)
Guides, blog articles and policies keep the dark header, a dark title band (`.page-head`) and the dark footer, and set their reading area on paper (`.paper`). Paper redefines the same token names locally, so every component works on it unchanged: ground #FFFFFF, panel #F7F6FA, panel-raised #EFEDF4, line #E6E3EC, line-strong #CFCAD9, text #17141F, muted #56516A, faint #6B6680. Accents darken for text on white: rose #C4144D (links, category labels, list markers), violet #5A2692. On paper the primary button inverts to ink with white text; inside the gradient band it stays white. Long text uses `.prose` (17.5px Inter, 1.75 line height, 72ch). Callouts are a tinted rose panel with a full hairline, never a side stripe. The About page stays fully dark.

### Named Rules
**The Only Light Rule.** Logo colors appear as light on the dark ground: words, strokes, numerals, markers. They never fill a panel or a button. The single exception is the newsletter band, once per page.

**The Exact Bars Rule.** The logo bars always use the five exact brand hexes, in order orange, rose, prune, violet, blue, on any ground. The lifted versions exist only for type and strokes on dark.

## Typography

**Display Font:** Montserrat, self-hosted variable file, weights 600 to 800 (with Helvetica Neue, Arial)
**Body Font:** Inter, self-hosted variable file (with system-ui)

**Character:** Montserrat at 800 with negative tracking gives the titles a scoreboard weight; Inter keeps the reading side identical to the product the visitor is about to use.

### Hierarchy
- **Display** (800, clamp(38px, 4.6vw, 60px), 1.04, -0.025em): the hero headline only, with its three lit words.
- **Headline** (800, clamp(30px, 3.4vw, 42px), 1.1, -0.02em): section titles, max width 680px.
- **Headline small** (800, clamp(28px, 3vw, 36px)): headings inside the newsletter band and the blog head.
- **Title** (700, 17px to 21px, 1.15): panel, plan, step and post titles (steps and plans 21px, features 20px, posts 19px at 1.3).
- **Quote** (600, clamp(19px, 2.1vw, 27px), 1.42): the testimonial, set in the display face, with key figures in Signal Rose.
- **Numeral** (800, 50px to 52px, 1, tabular): step numbers and prices; the signup price uses 40px.
- **Lead** (Inter 400, 19px; 17px on mobile, max 34ch): the hero sentence, in Muted.
- **Body** (Inter 400, 16px, 1.6): default; panel copy steps down to 15.5px and lists to 14.5px, max 62ch to 75ch.
- **Label** (Inter 700, 11.5px to 12.5px, 0.08em to 0.14em, uppercase): badges and blog category tags.

### Named Rules
**The Two Voices Rule.** Montserrat is for titles, numerals, prices, the quote and the wordmark; Inter is for everything read or clicked. Never set Montserrat below 600: the shipped file stops there.

## Layout

A single 1180px column with 32px side gutters (20px below 860px). Sections stack with 104px vertical padding (68px on mobile) and a 1px hairline on top of each, so the page reads as a series of lit rooms. Section heads sit left-aligned above content with a 52px gap (34px on mobile).

The hero is a two-column grid (text 1fr, stage 1.04fr, 32px gap), text vertically centered, the animated stage capped at 620px and pushed to the right edge, with a soft rose-to-violet radial glow behind it. Below 860px it stacks, both buttons go full width, and the glow moves below the text.

Grids use 18px gaps. Features use a three-column grid where the payment-matching panel spans two columns, so the row is never a set of equal cards. The three steps share one bordered strip divided by hairlines instead of three separate cards. Pricing is three columns aligned to the top. Everything collapses to one column at 860px; the nav turns into a menu at 960px.

## Elevation & Depth

Depth is tonal first: Arena Night, then Bench, then Raised Bench, each edged with a 1px hairline. Shadows are reserved for things that float above the page: real product captures, the popular plan, the mobile menu and toasts. They are long, soft and dark, always offset downward with a negative spread, never a hard edge.

### Shadow Vocabulary
- **Capture lift** (`box-shadow: 0 20px 40px -20px rgba(0,0,0,.7)`): app screenshots inside panels.
- **Hero window** (`box-shadow: 0 34px 70px -24px rgba(0,0,0,.7), 0 0 0 1px rgba(255,255,255,.06)`): the browser window in the hero stage; the 3D phone gets a matching double drop-shadow filter.
- **Popular ring** (`box-shadow: 0 0 0 1px #EC2D6A, 0 30px 80px -40px rgba(227,26,90,.6)`): the one highlighted plan; a rose glow under it.
- **Float** (`box-shadow: 0 16px 28px -14px rgba(0,0,0,.6)`; toasts use `0 20px 40px -16px`): mobile menu panel and toasts.
- **Hero glow** (`radial-gradient(closest-side, rgba(227,26,90,.20), rgba(90,38,146,.15) 52%, transparent 76%)`): atmosphere behind the hero stage, not a shadow.

### Named Rules
**The Hairline Rule.** Panels separate from the ground with a 1px line and a tonal step, never a shadow. A shadow means the thing is a real screen or is floating above the page.

## Shapes

Soft, consistent corners that grow with the size of the surface: 7px for the language chip, 10px for the menu trigger and social chips, 11px to 12px for buttons, inputs, captures and toasts, 16px for feature and post panels, 20px for the steps strip, plans and the included list, 22px for the signup dialog, 24px for the newsletter band, and full pills for the billing toggle and badges. Avatars are circles. Feature strokes are 64px by 4px bars hanging from the top edge with only their bottom corners rounded (3px), echoing a single logo bar. List markers are 7px squares with 2px corners, also in the language of the bars.

## Components

### Buttons
Calm and solid; there is one way to press.
- **Shape:** gently rounded (12px), 50px tall, 24px side padding, Inter 600 16px.
- **Primary:** white fill, Arena Night text. Hover shifts to a lavender-white; active presses down 1px. The video button carries a small dark disc with a white play triangle.
- **Ghost (line):** transparent with a 1.5px inset ring in Strong Hairline, white text; hover turns the ring white.
- **Compact:** 42px tall, 18px padding, in the header.
- **Disabled:** 50% opacity, not-allowed cursor.
- **Focus:** a 2px white outline offset 3px, site-wide.

### Chips
- **Billing toggle:** a pill track in Bench with a hairline border; the selected option becomes a white pill with dark text. The saving reads in Signal Rose.
- **Badge:** small uppercase label on Deep Rose, white text, pill shape.
- **Language chip:** 13px Inter 600, Strong Hairline border, 7px corners; hover goes white.

### Cards / Containers
- **Feature panel:** Bench, hairline border, 16px corners, 30px top padding, a 64px by 4px stroke in one logo color at the top-left. Hover strengthens the border. One panel per row may span two columns and hold a real capture.
- **Steps strip:** one container with a hairline border and 20px corners, split into three cells by hairlines; each cell opens with a 52px Montserrat numeral lit in orange, rose, then violet.
- **Plan card:** Bench, 20px corners, 30px padding. The popular plan rises to Raised Bench with a Signal Rose ring and glow, and is the only plan with a white primary button; the others use ghost buttons.
- **Post card:** Bench, 16px corners, a 16:9 image that scales 3% on hover; posts without an image show the five logo bars on a faint rose glow.
- **Newsletter band:** the one full-color surface, a rose to prune to violet gradient at 100 degrees, 24px corners, 52px padding, with a white input and white button.

### Inputs / Fields
- **Style:** 48px tall, Arena Night well, Strong Hairline border, 11px corners, white text, Faint placeholder. On the newsletter band, inputs invert to white with dark text.
- **Focus:** the border turns white; no glow.
- **Help / Error:** 13px help text below, green for valid, soft pink for errors.

### Navigation
Sticky header, 76px tall, translucent Arena Night with blur; a hairline appears once scrolled. Links are Inter 15px in Muted, white on hover, white and 600 for the current page. A language chip and a compact white button sit at the right. Below 960px the links fold into a hairline-ringed menu button that opens a Raised Bench panel.

### Logo
Five right-aligned bars stacked above each other at the left of the lowercase wordmark, Montserrat 700, white on dark. Bar widths 0.57, 0.92, 0.70, 0.99, 0.57em, each 0.17em tall, in the exact brand colors.

### Hero Stage
The approved animated hero: real app captures (desktop window and a 3D phone) on which a payment arrives and is matched on a loop. It is included as is; the page only sets its three headline-word colors and darkens its shadows for the night ground.

### Dialogs
Video and signup open as native dialogs over a blurred, 78% black backdrop, rising 10px into place with the house ease. The signup dialog is Raised Bench with a rose-to-violet tinted header holding the plan and price. A round translucent close button sits top right.

### Motion
One ease for everything, `cubic-bezier(.16, 1, .3, 1)`: 0.2s for color and background, 0.25s for borders, 0.3s for movement, 0.35s for dialogs, 0.6s for the post-image zoom. Smooth scrolling and dialog motion switch off under reduced motion.

## Do's and Don'ts

### Do:
- **Do** use the five exact logo hexes for the logo bars on every ground, in the brand order.
- **Do** let logo color appear only as light: lit headline words, the 4px top stroke, step numerals, 7px list markers.
- **Do** separate surfaces with a 1px hairline and a tonal step (ground, panel, panel-raised).
- **Do** keep to two buttons: solid white primary and hairline ghost, 12px corners, 50px tall.
- **Do** set titles, numerals and prices in Montserrat 800 with negative tracking, and everything read or clicked in Inter.
- **Do** show real app captures only, lifted with the long soft capture shadow.
- **Do** vary panel widths in a grid so a row is never three identical cards.
- **Do** build reading pages on the planned light variant: same fonts, components and logo colors on white.

### Don't:
- **Don't** fill buttons or panels with a logo color; the newsletter band is the single colored surface.
- **Don't** lighten, recolor, outline or shadow the logo bars, or write the name other than "minipass" in lowercase.
- **Don't** use drawn or stock imagery, or redraw the app UI; captures come from the running app.
- **Don't** set Montserrat lighter than 600 or use it for body copy.
- **Don't** put shadows on resting panels; a shadow means a real screen or a floating layer.
