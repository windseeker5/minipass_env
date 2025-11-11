#!/usr/bin/env python3
"""
Minipass Logo Auto-Generator
Uses Google AI Studio API to automatically generate logos
"""

import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai
from PIL import Image
import requests

# Load environment variables
load_dotenv()

class MinipassLogoGenerator:
    def __init__(self):
        self.api_key = os.getenv('GOOGLE_AI_API_KEY')
        if not self.api_key:
            raise ValueError("GOOGLE_AI_API_KEY not found in .env file")

        # Configure Google AI
        genai.configure(api_key=self.api_key)

        self.output_dir = Path(__file__).parent / 'generated_logos'
        self.output_dir.mkdir(exist_ok=True)

        print(f"✅ Google AI API configured")
        print(f"📁 Output directory: {self.output_dir}")

    def get_prompts(self):
        """Return all logo generation prompts"""
        return {
            'variation_b_pixelated_i': {
                'prompt': """Create a minimalist logo wordmark for "minipass" written in lowercase letters. Use a bold, modern sans-serif font similar to Inter Bold with clean letterforms. The first letter 'i' should be constructed from small, evenly-spaced pixel squares arranged in a geometric grid pattern, creating a subtle digital/technological effect. The dot of the 'i' should also be pixelated to match. All other letters should be solid. Color: solid dark blue #2563eb on pure white background. Professional, clean SaaS brand aesthetic. Vector-quality, ultra-sharp edges. Similar to Stripe logo's minimalist approach. No gradients, no shadows, just pixel grid on the 'i' and solid fills for other letters.""",
                'priority': 1
            },
            'variation_a_pixelated_p': {
                'prompt': """Create a minimalist logo wordmark for "minipass" written in lowercase letters. Use a bold, modern sans-serif font similar to Inter Bold with clean, geometric letterforms. The letter 'p' in the word "pass" should be subtly constructed from small pixel squares or dots arranged in a grid pattern, creating a digital/QR code aesthetic effect. All other letters should be solid and clean. Use solid dark blue color #2563eb. Place the logo on a pure white background. Professional tech startup aesthetic with crisp, vector-style edges. The design should be simple, scalable, and inspired by Stripe's minimalist logo philosophy. Ultra-clean typography, no shadows, no gradients, just solid blue pixels for the 'p' and solid blue for other letters.""",
                'priority': 2
            },
            'variation_c_pixelated_m': {
                'prompt': """Create a minimalist logo wordmark for "minipass" written in lowercase letters. Use a bold, modern sans-serif font similar to DM Sans Bold. The letter 'm' should have a subtle pixelated or geometric grid texture applied to it, with small square pixels visible within the letterform, referencing digital technology and QR codes. All other letters should be solid and clean. Use solid dark blue color #2563eb on pure white background. Modern, trustworthy, professional SaaS brand aesthetic. Vector-style with crisp typography. The pixel effect should be subtle and sophisticated, not overly decorative. Inspired by minimalist tech logos like Stripe.""",
                'priority': 3
            },
            'pwa_icon_circular': {
                'prompt': """Create a bold, minimalist circular app icon featuring the letters "MP" (for MiniPass) in white, centered on a solid dark blue #2563eb circular background. Use a modern, bold sans-serif font (Inter Bold or similar). The letters should be large, clean, and highly readable. The icon should work at small sizes from 48px to 512px. Place the circular icon on a square canvas with adequate white padding around the circle (20% padding). Professional, clean design for a Progressive Web App icon. Vector-quality, simple, memorable. The design should be minimal and crisp.""",
                'priority': 4
            }
        }

    def generate_with_gemini_imagen(self, prompt, output_file, variation_name):
        """
        Attempt to generate image using Google's Imagen model
        """
        print(f"\n{'='*70}")
        print(f"🎨 Generating: {variation_name}")
        print(f"{'='*70}")

        try:
            # Try to use Imagen through the API
            # Note: This requires proper Imagen API access

            # First, let's try listing available models
            print("📋 Checking available models...")
            available_models = []
            for model in genai.list_models():
                available_models.append(model.name)
                if 'imagen' in model.name.lower() or 'image' in model.name.lower():
                    print(f"   ✅ Found: {model.name}")

            # Try to find an image generation model
            image_models = [m for m in available_models if 'imagen' in m.lower()]

            if image_models:
                print(f"\n🚀 Using model: {image_models[0]}")
                model = genai.GenerativeModel(image_models[0])

                # Generate image
                response = model.generate_content(prompt)

                # Save the image
                if hasattr(response, 'image'):
                    response.image.save(output_file)
                    print(f"✅ Generated successfully: {output_file}")
                    return True
                else:
                    print(f"⚠️  Response doesn't contain image data")
                    return False
            else:
                print("\n⚠️  No Imagen models found in your API access")
                print("📋 Available models:")
                for model_name in available_models[:5]:
                    print(f"   - {model_name}")

                # Fallback: Use Gemini to enhance the prompt
                print("\n💡 Alternative: Using Gemini to create enhanced prompt for manual generation...")
                return self.generate_enhanced_prompt(prompt, variation_name)

        except Exception as e:
            print(f"❌ Error: {str(e)}")
            print("\n💡 Attempting alternative method...")
            return self.generate_enhanced_prompt(prompt, variation_name)

    def generate_enhanced_prompt(self, original_prompt, variation_name):
        """
        Use Gemini to create an even better prompt for manual image generation
        """
        try:
            model = genai.GenerativeModel('gemini-pro')

            enhancement_request = f"""You are an expert in AI image generation prompts.
            Improve and optimize this logo generation prompt for best results with image generation AI:

            Original prompt:
            {original_prompt}

            Create an enhanced version that:
            1. Is more specific about typography and letterforms
            2. Includes technical specifications (resolution, format)
            3. Uses keywords that work well with image generation AI
            4. Maintains the core concept but adds clarity

            Return ONLY the improved prompt, nothing else."""

            response = model.generate_content(enhancement_request)
            enhanced_prompt = response.text

            # Save enhanced prompt to file
            prompt_file = self.output_dir / f"{variation_name}_ENHANCED_PROMPT.txt"
            with open(prompt_file, 'w') as f:
                f.write(f"ENHANCED PROMPT FOR: {variation_name}\n")
                f.write("="*70 + "\n\n")
                f.write(enhanced_prompt)
                f.write("\n\n" + "="*70 + "\n")
                f.write("ORIGINAL PROMPT:\n")
                f.write(original_prompt)

            print(f"✅ Enhanced prompt saved to: {prompt_file}")
            print(f"\n📝 Enhanced Prompt Preview:")
            print(f"{enhanced_prompt[:200]}...")

            return False  # Still need manual generation

        except Exception as e:
            print(f"❌ Enhancement failed: {str(e)}")
            return False

    def generate_all(self):
        """Generate all logo variations"""
        print("\n" + "="*70)
        print("🚀 MINIPASS AUTOMATIC LOGO GENERATOR")
        print("="*70)

        prompts = self.get_prompts()
        sorted_prompts = sorted(prompts.items(), key=lambda x: x[1]['priority'])

        success_count = 0
        total = len(sorted_prompts)

        for name, data in sorted_prompts:
            output_file = self.output_dir / f"{name}.png"

            if self.generate_with_gemini_imagen(data['prompt'], output_file, name):
                success_count += 1

            # Small delay between requests
            time.sleep(2)

        print("\n" + "="*70)
        print(f"📊 SUMMARY")
        print("="*70)
        print(f"✅ Successfully generated: {success_count}/{total}")
        print(f"📁 Check output folder: {self.output_dir}")

        if success_count < total:
            print("\n💡 TIP: Use the enhanced prompts saved in the output folder")
            print("   Copy them to Google AI Studio web interface for manual generation")

        print("="*70 + "\n")

def main():
    try:
        generator = MinipassLogoGenerator()
        generator.generate_all()
    except Exception as e:
        print(f"\n❌ Fatal Error: {str(e)}")
        print("\nPlease check:")
        print("1. GOOGLE_AI_API_KEY is set in .env file")
        print("2. API key has proper permissions")
        print("3. You have access to Imagen API")
        sys.exit(1)

if __name__ == "__main__":
    main()
