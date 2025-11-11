#!/usr/bin/env python3
"""
Minipass Logo Auto-Generator - WORKING VERSION
Uses Google Imagen API correctly to generate logos
"""

import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai

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
        print(f"📁 Output directory: {self.output_dir}\n")

    def get_prompts(self):
        """Return all logo generation prompts"""
        return {
            'variation_b_pixelated_i': {
                'prompt': """Professional minimalist logo: the word "minipass" in lowercase, bold modern sans-serif font like Inter Bold. The first letter 'i' is made of small pixel squares in a grid pattern. The dot above 'i' is also pixelated. All other letters are solid. Solid dark blue color #2563eb on white background. Clean, vector-style, ultra-sharp edges, no gradients, no shadows. Stripe-inspired minimalism.""",
                'priority': 1
            },
            'variation_a_pixelated_p': {
                'prompt': """Professional minimalist logo: the word "minipass" in lowercase, bold Inter Bold font. The letter 'p' in "pass" is made of small pixel squares in grid pattern, resembling QR code aesthetic. All other letters solid. Solid dark blue #2563eb on white background. Clean tech startup style, vector-sharp, no shadows, no gradients. Simple and scalable.""",
                'priority': 2
            },
            'variation_c_pixelated_m': {
                'prompt': """Professional minimalist logo: the word "minipass" in lowercase, bold DM Sans Bold font. The letter 'm' has subtle pixelated grid texture with small squares. All other letters solid. Solid dark blue #2563eb on white. Modern SaaS aesthetic, vector-crisp, professional. Inspired by Stripe logo minimalism.""",
                'priority': 3
            },
            'pwa_icon_circular': {
                'prompt': """Bold minimalist app icon: white letters "MP" centered on solid dark blue #2563eb circular background. Modern bold sans-serif font, very readable. Circle on square white canvas with 20% padding. Professional PWA icon, vector-quality, simple, clean.""",
                'priority': 4
            }
        }

    def generate_image(self, prompt, output_file, variation_name):
        """Generate image using Imagen API"""
        print(f"🎨 Generating: {variation_name}")
        print(f"   Prompt: {prompt[:80]}...")

        try:
            # Use the correct Imagen model
            # Try different models in order of preference
            models_to_try = [
                'imagen-4.0-fast-generate-001',  # Fastest
                'imagen-4.0-generate-001',        # Standard
                'gemini-2.5-flash-image',         # Gemini with image generation
            ]

            for model_name in models_to_try:
                try:
                    print(f"   Trying model: {model_name}")

                    model = genai.ImageGenerationModel(model_name)

                    # Generate the image
                    response = model.generate_images(
                        prompt=prompt,
                        number_of_images=1,
                        aspect_ratio='1:1',  # Square for logos
                        safety_filter_level='block_some'
                    )

                    if response and response.images:
                        # Save the first image
                        image = response.images[0]
                        image._pil_image.save(output_file)
                        print(f"   ✅ SUCCESS! Saved to: {output_file.name}\n")
                        return True

                except AttributeError:
                    # This model doesn't support ImageGenerationModel, try next
                    continue
                except Exception as e:
                    if '404' in str(e):
                        continue
                    print(f"   ⚠️  Error with {model_name}: {str(e)}")
                    continue

            # If we get here, none of the models worked with ImageGenerationModel
            # Try alternative method using GenerativeModel
            return self.generate_with_generative_model(prompt, output_file, variation_name)

        except Exception as e:
            print(f"   ❌ Error: {str(e)}\n")
            return False

    def generate_with_generative_model(self, prompt, output_file, variation_name):
        """Try using GenerativeModel with image-capable models"""
        try:
            # Try Gemini models with image generation
            models_to_try = [
                'gemini-2.5-flash-image',
                'gemini-2.0-flash-exp-image-generation',
            ]

            for model_name in models_to_try:
                try:
                    print(f"   Trying GenerativeModel: {model_name}")

                    model = genai.GenerativeModel(model_name)

                    # Generate image using generate_content
                    response = model.generate_content(prompt)

                    # Check if response contains image data
                    if hasattr(response, '_result') and hasattr(response._result, 'candidates'):
                        for candidate in response._result.candidates:
                            if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                                for part in candidate.content.parts:
                                    if hasattr(part, 'inline_data'):
                                        # Found image data!
                                        import base64
                                        from PIL import Image
                                        import io

                                        image_data = base64.b64decode(part.inline_data.data)
                                        image = Image.open(io.BytesIO(image_data))
                                        image.save(output_file)
                                        print(f"   ✅ SUCCESS! Saved to: {output_file.name}\n")
                                        return True

                except Exception as e:
                    if '404' in str(e):
                        continue
                    print(f"   ⚠️  Error: {str(e)}")
                    continue

            print(f"   ⚠️  Could not generate with available methods\n")
            return False

        except Exception as e:
            print(f"   ❌ Error in alternative method: {str(e)}\n")
            return False

    def generate_all(self):
        """Generate all logo variations"""
        print("="*70)
        print("🚀 MINIPASS AUTOMATIC LOGO GENERATOR")
        print("="*70 + "\n")

        prompts = self.get_prompts()
        sorted_prompts = sorted(prompts.items(), key=lambda x: x[1]['priority'])

        success_count = 0
        total = len(sorted_prompts)

        for name, data in sorted_prompts:
            output_file = self.output_dir / f"{name}.png"

            if self.generate_image(data['prompt'], output_file, name):
                success_count += 1

            # Small delay between requests to avoid rate limiting
            time.sleep(3)

        print("="*70)
        print(f"📊 GENERATION COMPLETE")
        print("="*70)
        print(f"✅ Successfully generated: {success_count}/{total} logos")
        print(f"📁 Location: {self.output_dir}")

        if success_count > 0:
            print(f"\n🎉 Check your logos in the 'generated_logos' folder!")

        if success_count < total:
            print(f"\n⚠️  {total - success_count} logo(s) failed to generate")
            print("💡 You may need to generate these manually in Google AI Studio web interface")
            print("   Use the prompts from: logo_generation_prompts.md")

        print("="*70 + "\n")

        return success_count

def main():
    try:
        generator = MinipassLogoGenerator()
        success_count = generator.generate_all()

        if success_count == 0:
            print("⚠️  No logos were generated automatically.")
            print("\nPlease use Google AI Studio web interface:")
            print("1. Go to: https://aistudio.google.com/")
            print("2. Click on Imagen or image generation")
            print("3. Use prompts from: logo_generation_prompts.md")
            print("4. Download and save to: generated_logos/")
            sys.exit(1)

    except Exception as e:
        print(f"\n❌ Fatal Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
