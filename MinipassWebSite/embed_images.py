#!/usr/bin/env python3
"""Embed images as base64 in deployment email template"""
import base64

# Read base64 strings
with open('/tmp/welcom4_base64.txt', 'r') as f:
    welcom4_b64 = f.read().strip()

with open('/tmp/thumb_youtube_base64.txt', 'r') as f:
    youtube_b64 = f.read().strip()

# Read template
with open('templates/emails/deployment_ready.html', 'r') as f:
    html = f.read()

# Replace hero image with base64
html = html.replace('src="cid:welcom4.jpg"', f'src="data:image/jpeg;base64,{welcom4_b64}"')

# Replace YouTube thumbnail with base64
html = html.replace('src="cid:youtube-thumbnail.jpg"', f'src="data:image/jpeg;base64,{youtube_b64}"')

# Write updated template
with open('templates/emails/deployment_ready.html', 'w') as f:
    f.write(html)

print("✅ Embedded both images as base64 data URIs in deployment_ready.html")
