#!/usr/bin/env python3
"""
Stripe Logo Upload Script
Uploads the Minipass logo to Stripe and configures branding settings.

This script will:
1. Upload the logo file to Stripe
2. Update account branding settings with the logo and business name
"""

import stripe
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Stripe
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

def upload_logo(logo_path):
    """
    Upload logo file to Stripe.

    Args:
        logo_path: Path to the logo file

    Returns:
        File object from Stripe
    """
    print(f"Uploading logo from: {logo_path}")

    with open(logo_path, 'rb') as f:
        # Upload file to Stripe
        stripe_file = stripe.File.create(
            file=f,
            purpose='business_logo'  # Specify this is for business branding
        )

    print(f"✅ Logo uploaded successfully!")
    print(f"   File ID: {stripe_file.id}")
    print(f"   URL: {stripe_file.url}")

    return stripe_file

def update_branding(logo_file_id, business_name):
    """
    Update Stripe account branding settings.

    Args:
        logo_file_id: Stripe File ID of the uploaded logo
        business_name: Business name to display on checkout
    """
    print(f"\nUpdating branding settings...")
    print(f"   Business Name: {business_name}")
    print(f"   Logo File ID: {logo_file_id}")

    # Update account settings
    account = stripe.Account.modify(
        os.getenv('STRIPE_ACCOUNT_ID', 'self'),  # 'self' refers to your own account
        settings={
            'branding': {
                'logo': logo_file_id,
                'primary_color': None,  # Keep default colors as requested
                'secondary_color': None
            }
        },
        business_profile={
            'name': business_name
        }
    )

    print(f"✅ Branding settings updated successfully!")

    return account

def main():
    """Main execution function."""

    # Configuration
    LOGO_PATH = '/home/kdresdell/mp-logo-regular.png'
    BUSINESS_NAME = 'MiniPass - Simplified Activity Management'

    print("=" * 60)
    print("Stripe Branding Configuration Script")
    print("=" * 60)

    # Verify logo file exists
    if not os.path.exists(LOGO_PATH):
        print(f"❌ Error: Logo file not found at {LOGO_PATH}")
        return

    # Verify Stripe API key is set
    if not stripe.api_key:
        print("❌ Error: STRIPE_SECRET_KEY not found in environment variables")
        print("   Please ensure your .env file contains STRIPE_SECRET_KEY")
        return

    try:
        # Step 1: Upload logo
        print("\n[Step 1/2] Uploading logo to Stripe...")
        logo_file = upload_logo(LOGO_PATH)

        # Step 2: Update branding
        print("\n[Step 2/2] Updating account branding...")
        account = update_branding(logo_file.id, BUSINESS_NAME)

        print("\n" + "=" * 60)
        print("✅ SUCCESS! Your Stripe checkout is now branded!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Visit your Stripe Dashboard to verify: https://dashboard.stripe.com/settings/branding")
        print("2. Test your checkout flow to see the branded page")
        print("3. The branding will appear on:")
        print("   - Checkout pages")
        print("   - Payment links")
        print("   - Customer portal")
        print("   - Invoice PDFs")
        print("   - Email receipts")

    except stripe.error.StripeError as e:
        print(f"\n❌ Stripe API Error: {e.user_message}")
        print(f"   Details: {str(e)}")
    except Exception as e:
        print(f"\n❌ Unexpected Error: {str(e)}")

if __name__ == '__main__':
    main()
