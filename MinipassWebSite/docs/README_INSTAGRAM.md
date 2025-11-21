# Instagram Photo Updater

This script automatically fetches your latest 6 Instagram posts and updates the footer gallery on your MiniPass website.

## Quick Start

### 1. Install Dependencies (First Time Only)

```bash
cd /home/kdresdell/Documents/DEV/minipass_env/MinipassWebSite
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Instagram Credentials

Edit the `.env` file and replace the placeholder values with your actual Instagram credentials:

```bash
# Instagram Configuration (for update_instagram_photos.py script)
INSTAGRAM_USERNAME=your_actual_instagram_username
INSTAGRAM_PASSWORD=your_actual_instagram_password
```

**Important Security Notes:**
- Never commit your `.env` file with real credentials to git
- Make sure `.env` is in your `.gitignore` file
- Use a strong, unique password for your Instagram account

### 3. Run the Script

Whenever you want to update your website's Instagram photos:

```bash
cd /home/kdresdell/Documents/DEV/minipass_env/MinipassWebSite
source venv/bin/activate
python update_instagram_photos.py
```

The script will:
1. Login to your Instagram account
2. Fetch your latest 6 posts
3. Download and process the images (crop to square, resize, optimize)
4. Save them as `insta-1.png` through `insta-6.png` in `static/image/home-3/`
5. Your website will immediately show the updated photos

**Typical runtime:** 30-60 seconds

## Features

- ✅ Automatic square cropping (center crop)
- ✅ Optimized image size (400x400px)
- ✅ PNG format for web compatibility
- ✅ Rounded corners applied via CSS
- ✅ Progress feedback during execution
- ✅ Error handling and helpful messages

## Troubleshooting

### "Login error: fail status"
- Double-check your username and password in `.env`
- Make sure you don't have any extra spaces in the credentials
- Try logging into Instagram via web browser to verify credentials work

### "Two-factor authentication is enabled"
If you have 2FA enabled on Instagram:

**Option 1 (Recommended):**
- Temporarily disable 2FA on Instagram
- Run the script
- Re-enable 2FA after updating photos

**Option 2 (Advanced):**
- Use session file persistence (see instaloader documentation)
- This requires additional configuration

### "No images were downloaded"
- Check that your Instagram account has at least 6 public posts
- Private accounts should work if you're using your own credentials
- Very new accounts might have rate limiting

### Script runs but images don't update on website
- Hard refresh your browser (Ctrl+Shift+R or Cmd+Shift+R)
- Clear browser cache
- Check that files were actually created: `ls -la static/image/home-3/insta-*.png`

## How Often Should I Run This?

Run the script whenever you want to update the photos displayed on your website footer. Common schedules:
- **Weekly:** If you post to Instagram regularly
- **Monthly:** If you post less frequently
- **After major posts:** When you have new content you want to feature

There's no automatic scheduling - you have full control over when photos update.

## Technical Details

### What Gets Updated
- Files: `static/image/home-3/insta-1.png` through `insta-6.png`
- Image specifications: 400x400px, PNG format, optimized
- CSS: Rounded corners (8px border-radius) already applied

### What Doesn't Change
- Website HTML/CSS structure
- Instagram account settings
- Your actual Instagram posts

### Dependencies
- `instaloader` - Instagram API wrapper
- `Pillow` - Image processing
- `python-dotenv` - Environment variable management

### File Structure
```
MinipassWebSite/
├── update_instagram_photos.py    # Main script
├── .env                           # Instagram credentials (KEEP PRIVATE!)
├── requirements.txt               # Python dependencies
├── static/
│   ├── css/
│   │   └── main.css              # Rounded corners CSS
│   └── image/
│       └── home-3/
│           ├── insta-1.png       # Updated by script
│           ├── insta-2.png       # Updated by script
│           ├── insta-3.png       # Updated by script
│           ├── insta-4.png       # Updated by script
│           ├── insta-5.png       # Updated by script
│           └── insta-6.png       # Updated by script
└── templates/
    └── base.html                  # Instagram gallery HTML
```

## Support

If you encounter issues:
1. Check this troubleshooting guide
2. Verify your Instagram credentials in `.env`
3. Make sure you're using the virtual environment (`source venv/bin/activate`)
4. Check that all dependencies are installed (`pip list | grep -E "instaloader|Pillow"`)

## Future Enhancements (Optional)

If you later decide you want automation, you could:
- Add a Flask admin panel button to trigger updates
- Set up a cron job to run automatically
- Implement the official Instagram API with OAuth

But for now, the manual script approach keeps things simple and reliable!
