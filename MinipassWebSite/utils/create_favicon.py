#!/usr/bin/env python3
"""
Script to convert mp-bar-only.png to various favicon formats
"""
from PIL import Image
import os

# Paths
input_image = "static/image/mp-bar-only.png"
output_dir = "static/image"

# Create output directory if it doesn't exist
os.makedirs(output_dir, exist_ok=True)

# Load the original image
print(f"Loading image: {input_image}")
img = Image.open(input_image)
print(f"Original size: {img.size}")

# Convert to RGBA if not already
if img.mode != 'RGBA':
    img = img.convert('RGBA')

# Common favicon sizes
sizes = [
    (16, 16),    # Classic favicon
    (32, 32),    # Standard favicon
    (48, 48),    # Windows
    (64, 64),    # Windows
    (128, 128),  # Chrome Web Store
    (180, 180),  # Apple touch icon
    (192, 192),  # Android
    (512, 512),  # High res
]

# Generate PNG favicons of different sizes
print("\nGenerating PNG favicons...")
for size in sizes:
    resized = img.resize(size, Image.Resampling.LANCZOS)
    output_path = f"{output_dir}/favicon-{size[0]}x{size[1]}.png"
    resized.save(output_path, 'PNG')
    print(f"  Created: {output_path}")

# Create the main favicon.png (32x32)
print("\nCreating main favicon.png (32x32)...")
favicon_32 = img.resize((32, 32), Image.Resampling.LANCZOS)
favicon_32.save(f"{output_dir}/favicon.png", 'PNG')
print(f"  Created: {output_dir}/favicon.png")

# Create favicon.ico with multiple sizes (16x16 and 32x32)
print("\nCreating favicon.ico with multiple sizes...")
icon_sizes = [(16, 16), (32, 32), (48, 48)]
icon_images = [img.resize(size, Image.Resampling.LANCZOS) for size in icon_sizes]
icon_images[0].save(
    f"{output_dir}/favicon.ico",
    format='ICO',
    sizes=icon_sizes
)
print(f"  Created: {output_dir}/favicon.ico")

# Create Apple touch icon (180x180)
print("\nCreating apple-touch-icon.png...")
apple_icon = img.resize((180, 180), Image.Resampling.LANCZOS)
apple_icon.save(f"{output_dir}/apple-touch-icon.png", 'PNG')
print(f"  Created: {output_dir}/apple-touch-icon.png")

print("\n✅ All favicons created successfully!")
print("\nGenerated files:")
print("  - favicon.ico (multi-size)")
print("  - favicon.png (32x32)")
print("  - favicon-*.png (various sizes)")
print("  - apple-touch-icon.png (180x180)")
