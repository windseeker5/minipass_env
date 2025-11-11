#!/usr/bin/env python3
"""
Minipass Logo Generator
Generates final logo variations using AI image generation APIs
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class LogoGenerator:
    def __init__(self):
        self.google_ai_key = os.getenv('GOOGLE_AI_API_KEY')
        self.output_dir = Path(__file__).parent / 'generated_logos'
        self.output_dir.mkdir(exist_ok=True)

        # Logo prompts
        self.prompts = {
            'variation_a_pixelated_p': """Create a minimalist logo wordmark for "minipass" written in lowercase letters. Use a bold, modern sans-serif font similar to Inter Bold with clean, geometric letterforms. The letter 'p' in the word "pass" should be subtly constructed from small pixel squares or dots arranged in a grid pattern, creating a digital/QR code aesthetic effect. All other letters should be solid and clean. Use solid dark blue color #2563eb. Place the logo on a pure white background. Professional tech startup aesthetic with crisp, vector-style edges. The design should be simple, scalable, and inspired by Stripe's minimalist logo philosophy. Ultra-clean typography, no shadows, no gradients, just solid blue pixels for the 'p' and solid blue for other letters.""",

            'variation_b_pixelated_i': """Create a minimalist logo wordmark for "minipass" written in lowercase letters. Use a bold, modern sans-serif font similar to Inter Bold with clean letterforms. The first letter 'i' should be constructed from small, evenly-spaced pixel squares arranged in a geometric grid pattern, creating a subtle digital/technological effect. The dot of the 'i' should also be pixelated to match. All other letters should be solid. Color: solid dark blue #2563eb on pure white background. Professional, clean SaaS brand aesthetic. Vector-quality, ultra-sharp edges. Similar to Stripe logo's minimalist approach. No gradients, no shadows, just pixel grid on the 'i' and solid fills for other letters.""",

            'variation_c_pixelated_m': """Create a minimalist logo wordmark for "minipass" written in lowercase letters. Use a bold, modern sans-serif font similar to DM Sans Bold. The letter 'm' should have a subtle pixelated or geometric grid texture applied to it, with small square pixels visible within the letterform, referencing digital technology and QR codes. All other letters should be solid and clean. Use solid dark blue color #2563eb on pure white background. Modern, trustworthy, professional SaaS brand aesthetic. Vector-style with crisp typography. The pixel effect should be subtle and sophisticated, not overly decorative. Inspired by minimalist tech logos like Stripe.""",

            'pwa_icon_circular': """Create a bold, minimalist circular app icon featuring the letters "MP" (for MiniPass) in white, centered on a solid dark blue #2563eb circular background. Use a modern, bold sans-serif font (Inter Bold or similar). The letters should be large, clean, and highly readable. The icon should work at small sizes from 48px to 512px. Place the circular icon on a square canvas with adequate white padding around the circle (20% padding). Professional, clean design for a Progressive Web App icon. Vector-quality, simple, memorable. The design should be minimal and crisp.""",

            'pwa_icon_square': """Create a square app icon with rounded corners featuring bold white letters "MP" centered on a solid dark blue #2563eb background. Modern sans-serif font, clean and readable. The square should have subtly rounded corners (20% radius). White letters on blue background. Icon should be optimized for display at multiple sizes (192px, 512px). Professional, minimal PWA app icon design. Ultra-clean, no shadows, no gradients, just solid blue background with white typography."""
        }

    def generate_with_manual_instructions(self):
        """Provide manual generation instructions"""
        print("\n" + "="*70)
        print("🎨 MINIPASS LOGO GENERATION - MANUAL MODE")
        print("="*70)
        print("\n⚠️  Automated API generation requires additional setup.")
        print("    For fastest results, use the manual generation method below:\n")

        print("📋 OPTION 1: Google AI Studio (Web Interface)")
        print("-" * 70)
        print("1. Go to: https://aistudio.google.com/")
        print("2. Click on 'Imagen' or image generation model")
        print("3. Use the prompts from: logo_generation_prompts.md")
        print("4. Generate each variation (A, B, C)")
        print("5. Download high-resolution PNG files")
        print("6. Save to:", self.output_dir)

        print("\n📋 OPTION 2: Alternative AI Tools")
        print("-" * 70)
        print("• DALL-E 3 (ChatGPT Plus): https://chat.openai.com/")
        print("• Midjourney: https://midjourney.com/")
        print("• Leonardo.ai: https://leonardo.ai/ (free tier available)")
        print("• Ideogram: https://ideogram.ai/ (excellent for text in images)")

        print("\n💡 RECOMMENDED: Ideogram.ai")
        print("-" * 70)
        print("Ideogram is particularly good at rendering text in logos.")
        print("It's free and produces high-quality results for wordmarks.")

        print("\n📝 Quick Start:")
        print("-" * 70)
        print("1. Open: https://ideogram.ai/")
        print("2. Sign up (free)")
        print("3. Copy prompt from logo_generation_prompts.md")
        print("4. Paste into Ideogram")
        print("5. Generate and download")

        print("\n✅ PROMPTS READY:")
        print("-" * 70)
        for name, prompt in self.prompts.items():
            print(f"\n{name}:")
            print(f"   {prompt[:100]}...")

        print("\n" + "="*70)
        print("💾 Save generated images to:")
        print(f"   {self.output_dir}")
        print("="*70 + "\n")

    def try_google_imagen(self, prompt, output_filename):
        """
        Attempt to use Google's Imagen API
        Note: Requires Vertex AI setup, not just AI Studio API key
        """
        print(f"\n🔄 Attempting to generate: {output_filename}")

        # Check if we have the API key
        if not self.google_ai_key:
            print("❌ No Google AI API key found in .env file")
            return False

        # Note: Google's image generation (Imagen) requires Vertex AI
        # The standard AI Studio API key is for Gemini (text generation)
        print("⚠️  Google AI Studio API key is for Gemini (text), not Imagen (images)")
        print("    Imagen requires Vertex AI setup with Google Cloud project")
        print("    Falling back to manual generation instructions...")

        return False

    def generate_all_logos(self):
        """Main generation function"""
        print("\n" + "="*70)
        print("🚀 MINIPASS LOGO GENERATOR")
        print("="*70)
        print(f"\n📁 Output directory: {self.output_dir}")
        print(f"📊 Total variations to generate: {len(self.prompts)}")

        # Try automated generation
        automated_success = False
        for name, prompt in self.prompts.items():
            output_file = self.output_dir / f"{name}.png"
            if self.try_google_imagen(prompt, output_file):
                automated_success = True
            else:
                break

        # If automated fails, provide manual instructions
        if not automated_success:
            self.generate_with_manual_instructions()

        print("\n✨ NEXT STEPS:")
        print("-" * 70)
        print("1. Generate logos using one of the methods above")
        print("2. Save images to:", self.output_dir)
        print("3. Review all variations")
        print("4. Select the best one for final use")
        print("5. Export in required sizes (see logo_generation_prompts.md)")
        print("\n" + "="*70 + "\n")

def main():
    """Main entry point"""
    generator = LogoGenerator()
    generator.generate_all_logos()

if __name__ == "__main__":
    main()
