#!/usr/bin/env python3
"""
Instagram Photo Updater for MiniPass Website
============================================

This script fetches the latest 6 photos from your Instagram account
and updates the footer gallery on the website.

Usage:
    python update_instagram_photos.py

Requirements:
    - INSTAGRAM_USERNAME and INSTAGRAM_PASSWORD in .env file
    - instaloader and Pillow packages installed
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import instaloader
from PIL import Image
import shutil

# Load environment variables
load_dotenv()

# Configuration
INSTAGRAM_USERNAME = os.getenv('INSTAGRAM_USERNAME')
INSTAGRAM_PASSWORD = os.getenv('INSTAGRAM_PASSWORD')
TARGET_DIR = Path(__file__).parent / 'static' / 'image' / 'home-3'
TEMP_DIR = Path(__file__).parent / 'temp_instagram'
NUM_PHOTOS = 6
IMAGE_SIZE = 400  # Square dimension in pixels

def validate_credentials():
    """Check if Instagram credentials are configured."""
    if not INSTAGRAM_USERNAME or not INSTAGRAM_PASSWORD:
        print("❌ Error: Instagram credentials not found!")
        print("\nPlease add the following to your .env file:")
        print("INSTAGRAM_USERNAME=your_username")
        print("INSTAGRAM_PASSWORD=your_password")
        sys.exit(1)
    print(f"✓ Found credentials for @{INSTAGRAM_USERNAME}")

def create_temp_directory():
    """Create temporary directory for downloads."""
    if TEMP_DIR.exists():
        shutil.rmtree(TEMP_DIR)
    TEMP_DIR.mkdir(parents=True)
    print(f"✓ Created temporary directory: {TEMP_DIR}")

def download_instagram_photos():
    """Download latest photos from Instagram."""
    print(f"\n🔐 Logging into Instagram as @{INSTAGRAM_USERNAME}...")

    # Create Instaloader instance
    loader = instaloader.Instaloader(
        download_videos=False,
        download_video_thumbnails=False,
        download_geotags=False,
        download_comments=False,
        save_metadata=False,
        compress_json=False,
        dirname_pattern=str(TEMP_DIR)
    )

    try:
        # Login to Instagram
        loader.login(INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD)
        print("✓ Successfully logged in!")

        # Get profile
        print(f"\n📸 Fetching latest {NUM_PHOTOS} posts...")
        profile = instaloader.Profile.from_username(loader.context, INSTAGRAM_USERNAME)

        # Download posts
        downloaded_images = []
        post_count = 0

        for post in profile.get_posts():
            if post_count >= NUM_PHOTOS:
                break

            try:
                # Download the post
                loader.download_post(post, target=str(TEMP_DIR / f"post_{post_count}"))

                # Find the downloaded image file
                post_dir = TEMP_DIR / f"post_{post_count}"
                image_files = list(post_dir.glob('*.jpg')) + list(post_dir.glob('*.png'))

                if image_files:
                    downloaded_images.append(image_files[0])
                    post_count += 1
                    print(f"  ✓ Downloaded post {post_count}/{NUM_PHOTOS}")

            except Exception as e:
                print(f"  ⚠ Warning: Could not download post {post_count + 1}: {e}")
                continue

        if len(downloaded_images) < NUM_PHOTOS:
            print(f"\n⚠ Warning: Only found {len(downloaded_images)} posts (expected {NUM_PHOTOS})")

        return downloaded_images

    except instaloader.exceptions.BadCredentialsException:
        print("❌ Error: Invalid Instagram credentials!")
        print("Please check your username and password in .env file")
        sys.exit(1)
    except instaloader.exceptions.TwoFactorAuthRequiredException:
        print("❌ Error: Two-factor authentication is enabled!")
        print("\nOptions:")
        print("1. Temporarily disable 2FA on Instagram")
        print("2. Use session file (see instaloader documentation)")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error downloading photos: {e}")
        sys.exit(1)

def process_and_save_images(image_paths):
    """Process images and save to target directory."""
    print(f"\n🎨 Processing images...")

    for idx, image_path in enumerate(image_paths, start=1):
        try:
            # Open image
            img = Image.open(image_path)

            # Convert to RGB if necessary (handle RGBA, etc.)
            if img.mode != 'RGB':
                img = img.convert('RGB')

            # Crop to square (center crop)
            width, height = img.size
            min_dimension = min(width, height)
            left = (width - min_dimension) / 2
            top = (height - min_dimension) / 2
            right = (width + min_dimension) / 2
            bottom = (height + min_dimension) / 2
            img = img.crop((left, top, right, bottom))

            # Resize to target size
            img = img.resize((IMAGE_SIZE, IMAGE_SIZE), Image.Resampling.LANCZOS)

            # Save as PNG
            output_path = TARGET_DIR / f"insta-{idx}.png"
            img.save(output_path, 'PNG', optimize=True)

            print(f"  ✓ Processed and saved insta-{idx}.png")

        except Exception as e:
            print(f"  ❌ Error processing image {idx}: {e}")
            continue

def cleanup_temp_directory():
    """Remove temporary directory."""
    if TEMP_DIR.exists():
        shutil.rmtree(TEMP_DIR)
    print(f"\n🧹 Cleaned up temporary files")

def main():
    """Main execution function."""
    print("=" * 60)
    print("Instagram Photo Updater for MiniPass Website")
    print("=" * 60)

    # Validate setup
    validate_credentials()

    if not TARGET_DIR.exists():
        print(f"❌ Error: Target directory not found: {TARGET_DIR}")
        sys.exit(1)

    try:
        # Create temp directory
        create_temp_directory()

        # Download photos
        image_paths = download_instagram_photos()

        if not image_paths:
            print("❌ Error: No images were downloaded")
            cleanup_temp_directory()
            sys.exit(1)

        # Process and save
        process_and_save_images(image_paths)

        # Cleanup
        cleanup_temp_directory()

        print("\n" + "=" * 60)
        print("✅ Successfully updated Instagram photos!")
        print(f"   {len(image_paths)} photos saved to {TARGET_DIR}")
        print("=" * 60)
        print("\nYour website footer will now show the updated photos.")

    except KeyboardInterrupt:
        print("\n\n⚠ Operation cancelled by user")
        cleanup_temp_directory()
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        cleanup_temp_directory()
        sys.exit(1)

if __name__ == '__main__':
    main()
