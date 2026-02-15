# GIMP Quick Guide - Professional Photo Enhancement

## **Method 1: The Fast Auto-Fix (Start Here)**

1. **Open your photo in GIMP**

2. **Auto White Balance**
   - `Colors → Auto → White Balance`
   - This fixes color temperature instantly

3. **Auto Normalize**
   - `Colors → Auto → Normalize`
   - This stretches contrast automatically

4. **Manual Brightness-Contrast Touch-up**
   - `Colors → Brightness-Contrast`
   - **Contrast:** +20 to +30
   - **Brightness:** +10 to +15

5. **Sharpen**
   - `Filters → Enhance → Sharpen (Unsharp Mask)`
   - **Radius:** 1.5
   - **Amount:** 0.6
   - Click OK

**Done!** This should get you 80% there.

---

## **Method 2: Manual Control (Better Results)**

1. **Open photo in GIMP**

2. **Levels (Most Important!)**
   - `Colors → Levels`
   - **Input Levels:** Drag the RIGHT slider (white point) left to around 240-245
   - **Mid slider:** Move slightly left (to around 1.10-1.20)
   - This adds "pop" and brightness

3. **Curves (for pros)**
   - `Colors → Curves`
   - Create a slight S-curve:
     - Click middle of line, drag UP slightly
     - Click bottom quarter, drag DOWN slightly
   - This adds contrast while keeping shadows

4. **Saturation**
   - `Colors → Hue-Saturation`
   - **Saturation:** +12 to +18
   - Makes colors more vibrant like the professional photos

5. **Sharpen**
   - `Filters → Enhance → Sharpen (Unsharp Mask)`
   - **Radius:** 1.5-2.0
   - **Amount:** 0.5-0.7
   - **Threshold:** 0

6. **Optional: Vignette (subtle)**
   - `Filters → Light and Shadow → Vignette`
   - **Soften:** Check this box
   - **Radius:** 1.5
   - This draws focus to the face

---

## **Bonus: DaVinci Resolve Method** 
(Since you have it - actually faster!)

1. Import photo to Media Pool
2. Drag to timeline
3. Go to **Color** tab
4. **Auto Color Balance** button (magic wand icon)
5. Manual adjustments in **Primaries**:
   - **Contrast:** +15 to +25
   - **Pivot:** 0.5
   - **Saturation:** 105-110
   - **Lift** (shadows): Slightly towards blue if photo is too warm
   - **Gamma** (mids): Push slightly right to brighten
6. Export as image

---

## **Quick Values Summary for Your Photos:**

For the two left photos to match the right ones:

| Adjustment | Value |
|------------|-------|
| Brightness | +10 to +15 |
| Contrast | +20 to +30 |
| Saturation | +12 to +18 |
| Sharpen Radius | 1.5-2.0 |
| Sharpen Amount | 0.5-0.7 |

---

## **Pro Tips**

- **Export Quality:** Save as high-quality JPEG (quality 90-95) for web use
- **Consistency:** Use the same adjustments on all photos for a uniform look
- **Before/After:** Use `View → Toggle Selection` in GIMP to compare before/after
- **Batch Processing:** For multiple photos, save your adjustments as a preset
- **File Naming:** Keep originals! Save edited versions with suffix like `_enhanced.jpg`

---

## **Troubleshooting Common Issues**

**Photo looks too orange/yellow:**
- `Colors → Color Temperature` → Move slider towards blue (-5 to -15)

**Face is too dark:**
- Use `Colors → Curves` and lift the shadows (bottom left of curve)

**Photo looks washed out after adjustments:**
- Reduce saturation slightly or add more contrast

**Edges look "crunchy" after sharpening:**
- Lower the Amount value in Unsharp Mask
- Or increase the Threshold slightly

---

Created for website team photos enhancement project.
