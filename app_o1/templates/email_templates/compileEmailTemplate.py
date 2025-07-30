import os
import re
import json
import base64
import sys


def compile_email_template_to_folder(template_name: str):
    source_dir = os.path.abspath(template_name)
    target_dir = os.path.abspath(f"{template_name}_compiled")
    os.makedirs(target_dir, exist_ok=True)

    source_html_path = os.path.join(source_dir, "index.html")
    target_html_path = os.path.join(target_dir, "index.html")
    inline_images_path = os.path.join(target_dir, "inline_images.json")

    with open(source_html_path, "r", encoding="utf-8") as f:
        html = f.read()

    cid_map = {}

    # Match <img src="..."> tags
    matches = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', html)

    for match in matches:
        asset_path = os.path.join(source_dir, os.path.basename(match))

        if os.path.exists(asset_path):
            cid = os.path.splitext(os.path.basename(asset_path))[0]

            with open(asset_path, "rb") as img_file:
                img_bytes = img_file.read()
                img_base64 = base64.b64encode(img_bytes).decode("utf-8")
                cid_map[cid] = img_base64

            # Replace img src with cid:...
            html = html.replace(match, f"cid:{cid}")
        else:
            print(f"⚠️ Not found: {asset_path}")

    with open(target_html_path, "w", encoding="utf-8") as f:
        f.write(html)

    with open(inline_images_path, "w", encoding="utf-8") as f:
        json.dump(cid_map, f, indent=2)

    print(f"✅ Compiled '{template_name}' → '{template_name}_compiled' with {len(cid_map)} embedded image(s).")




# 🟢 Run with folder argument or fallback to "test"
if __name__ == "__main__":
    folder = sys.argv[1] if len(sys.argv) > 1 else "test"
    print(f"> Compiling email template from folder: {folder}")
    compile_email_template_to_folder(folder)
