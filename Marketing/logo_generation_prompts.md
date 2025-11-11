# Minipass Final Logo Generation Prompts

## 🎯 Logo Concept: Minimal Precision
**Style:** Clean, professional wordmark with subtle pixel element
**Color:** Solid dark blue #2563eb (RGB: 37, 99, 235)
**Typography:** Bold, modern sans-serif (Inter Bold or DM Sans Bold style)
**Aesthetic:** Stripe-inspired minimalism with subtle tech reference

---

## 📝 Main Logo Prompts (Test All 3 Variations)

### Variation A: Pixelated "p" in "pass"

```
Create a minimalist logo wordmark for "minipass" written in lowercase letters. Use a bold, modern sans-serif font similar to Inter Bold with clean, geometric letterforms. The letter 'p' in the word "pass" should be subtly constructed from small pixel squares or dots arranged in a grid pattern, creating a digital/QR code aesthetic effect. All other letters should be solid and clean. Use solid dark blue color #2563eb. Place the logo on a pure white background. Professional tech startup aesthetic with crisp, vector-style edges. The design should be simple, scalable, and inspired by Stripe's minimalist logo philosophy. Ultra-clean typography, no shadows, no gradients, just solid blue pixels for the 'p' and solid blue for other letters.
```

---

### Variation B: Pixelated "i" (first letter)

```
Create a minimalist logo wordmark for "minipass" written in lowercase letters. Use a bold, modern sans-serif font similar to Inter Bold with clean letterforms. The first letter 'i' should be constructed from small, evenly-spaced pixel squares arranged in a geometric grid pattern, creating a subtle digital/technological effect. The dot of the 'i' should also be pixelated to match. All other letters should be solid. Color: solid dark blue #2563eb on pure white background. Professional, clean SaaS brand aesthetic. Vector-quality, ultra-sharp edges. Similar to Stripe logo's minimalist approach. No gradients, no shadows, just pixel grid on the 'i' and solid fills for other letters.
```

---

### Variation C: Pixelated "m" (first letter)

```
Create a minimalist logo wordmark for "minipass" written in lowercase letters. Use a bold, modern sans-serif font similar to DM Sans Bold. The letter 'm' should have a subtle pixelated or geometric grid texture applied to it, with small square pixels visible within the letterform, referencing digital technology and QR codes. All other letters should be solid and clean. Use solid dark blue color #2563eb on pure white background. Modern, trustworthy, professional SaaS brand aesthetic. Vector-style with crisp typography. The pixel effect should be subtle and sophisticated, not overly decorative. Inspired by minimalist tech logos like Stripe.
```

---

## 📱 PWA Icon Prompt

```
Create a bold, minimalist circular app icon featuring the letters "MP" (for MiniPass) in white, centered on a solid dark blue #2563eb circular background. Use a modern, bold sans-serif font (Inter Bold or similar). The letters should be large, clean, and highly readable. The icon should work at small sizes from 48px to 512px. Place the circular icon on a square canvas with adequate white padding around the circle (20% padding). Professional, clean design for a Progressive Web App icon. Vector-quality, simple, memorable. The design should be minimal and crisp.
```

---

## 🎨 Alternative PWA Icon (Square with Rounded Corners)

```
Create a square app icon with rounded corners featuring bold white letters "MP" centered on a solid dark blue #2563eb background. Modern sans-serif font, clean and readable. The square should have subtly rounded corners (20% radius). White letters on blue background. Icon should be optimized for display at multiple sizes (192px, 512px). Professional, minimal PWA app icon design. Ultra-clean, no shadows, no gradients, just solid blue background with white typography.
```

---

## 📋 Generation Instructions

### Using Google AI Studio (Web Interface):
1. Go to https://aistudio.google.com/
2. Select "Imagen" or image generation model
3. Paste each prompt above
4. Generate 2-3 variations of each to compare
5. Download high-resolution PNG files

### Using the API (Python Script):
Run the `generate_logos.py` script included in this folder:
```bash
cd /home/kdresdell/Documents/DEV/minipass_env/Marketing
python generate_logos.py
```

---

## ✅ Quality Checklist

After generation, verify each logo:
- [ ] Text is perfectly legible at 50px width
- [ ] Pixel effect is subtle and professional (not toy-like)
- [ ] Color is exactly #2563eb (not lighter or darker)
- [ ] Background is pure white (transparent PNG preferred)
- [ ] No unwanted shadows, outlines, or effects
- [ ] Typography is clean and bold
- [ ] Scales well from favicon to billboard size
- [ ] Looks professional next to Stripe, Linear, Vercel logos

---

## 📏 Export Specifications

**Main Logo:**
- Format: PNG with transparent background
- Width: 2000px minimum (high resolution)
- Height: Auto (maintain aspect ratio)
- Color space: sRGB
- File name: `minipass_logo_final.png`

**PWA Icons:**
- Format: PNG
- Sizes needed: 192x192px, 512x512px
- Color space: sRGB
- File names: `minipass_pwa_icon_192.png`, `minipass_pwa_icon_512.png`

---

## 🎯 Selection Criteria

Choose the winning logo based on:
1. **Readability** - Clear at all sizes
2. **Professionalism** - Trustworthy and stable feeling
3. **Memorability** - Subtle pixel element creates interest
4. **Scalability** - Works from 16px favicon to large prints
5. **Brand Alignment** - Communicates simplicity + technology
6. **Timelessness** - Won't feel dated in 2-3 years

---

**Recommended:** Start with Variation B (pixelated 'i') - it's likely the most balanced option, as the 'i' is simpler and the pixel effect will be most subtle and elegant.
