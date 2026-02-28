import os
import shutil
import sqlite3
import subprocess

# Project root (same anchor as deploy_helpers.py line 602)
_BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

# Absolute path so this works regardless of CWD
CUSTOMERS_DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "customers.db"))

MAILSERVER_CONTAINER = "mailserver"


def _run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, check=False)


def delete_customer_complete(subdomain: str) -> list:
    """
    Perform a complete teardown of a customer deployment.

    Returns a list of dicts: {"step": str, "status": str, "message": str}
    Status values: "ok" | "warning" (skipped/already gone) | "error" (failed)
    Never raises — all exceptions are caught and recorded as step results.
    """
    results = []

    def record(name, status, message):
        results.append({"step": name, "status": status, "message": message})

    # --- Fetch email_address BEFORE DB deletion ---
    email_address = None
    try:
        conn = sqlite3.connect(CUSTOMERS_DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT email_address FROM customers WHERE subdomain = ?", (subdomain,))
        row = cursor.fetchone()
        if row:
            email_address = row[0]
        conn.close()
    except Exception:
        pass  # Non-fatal; email steps will handle the None case

    # Step 1 — Stop & remove container
    container_name = f"minipass_{subdomain}"
    try:
        _run(["docker", "stop", container_name])
        rm = _run(["docker", "rm", "-f", "-v", container_name])
        if rm.returncode == 0:
            record("Stop & remove container", "ok",
                   f"Container '{container_name}' stopped and removed.")
        else:
            record("Stop & remove container", "warning",
                   f"Container not found or already gone: {rm.stderr.strip() or rm.stdout.strip()}")
    except Exception as e:
        record("Stop & remove container", "error", str(e))

    # Step 2 — Remove Docker image
    image_name = f"{subdomain}-flask-app"
    try:
        rmi = _run(["docker", "rmi", "-f", image_name])
        if rmi.returncode == 0:
            record("Remove Docker image", "ok", f"Image '{image_name}' removed.")
        else:
            record("Remove Docker image", "warning",
                   f"Image not found or already gone: {rmi.stderr.strip() or rmi.stdout.strip()}")
    except Exception as e:
        record("Remove Docker image", "error", str(e))

    # Step 3 — Delete deployed directory
    deploy_path = os.path.join(_BASE_DIR, "deployed", subdomain)
    try:
        if os.path.exists(deploy_path):
            shutil.rmtree(deploy_path)
            record("Delete deployed directory", "ok", f"Removed '{deploy_path}'.")
        else:
            record("Delete deployed directory", "warning",
                   f"Directory not found: '{deploy_path}'")
    except Exception as e:
        record("Delete deployed directory", "error", str(e))

    # Step 4 — Remove nginx vhost config
    vhost_path = os.path.join(_BASE_DIR, "vhost.d", f"{subdomain}.minipass.me_location")
    try:
        if os.path.exists(vhost_path):
            os.remove(vhost_path)
            record("Remove nginx vhost config", "ok", f"Removed '{vhost_path}'.")
        else:
            record("Remove nginx vhost config", "warning",
                   f"File not found: '{vhost_path}'")
    except Exception as e:
        record("Remove nginx vhost config", "error", str(e))

    # Step 5 — Delete mail account
    if email_address:
        try:
            result = _run([
                "docker", "exec", MAILSERVER_CONTAINER,
                "setup", "email", "del", email_address,
            ])
            if result.returncode == 0:
                record("Delete mail account", "ok",
                       f"Mail account '{email_address}' deleted.")
            else:
                record("Delete mail account", "warning",
                       f"Mail deletion warning: {result.stderr.strip() or result.stdout.strip()}")
        except Exception as e:
            record("Delete mail account", "error", str(e))
    else:
        record("Delete mail account", "warning",
               "No email address associated with this customer; skipped.")

    # Step 6 — Remove mail forward config directory
    if email_address:
        forward_dir = os.path.join(_BASE_DIR, "config", "user-patches", email_address)
        try:
            if os.path.exists(forward_dir):
                shutil.rmtree(forward_dir)
                record("Remove mail forward config", "ok",
                       f"Removed '{forward_dir}'.")
            else:
                record("Remove mail forward config", "warning",
                       f"Forward config dir not found: '{forward_dir}'")
        except Exception as e:
            record("Remove mail forward config", "error", str(e))
    else:
        record("Remove mail forward config", "warning",
               "No email address; forward config removal skipped.")

    # Step 7 — Delete DB record
    try:
        conn = sqlite3.connect(CUSTOMERS_DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM customers WHERE subdomain = ?", (subdomain,))
        if cursor.fetchone()[0] > 0:
            cursor.execute("DELETE FROM customers WHERE subdomain = ?", (subdomain,))
            conn.commit()
            record("Delete DB record", "ok",
                   f"Customer '{subdomain}' removed from database.")
        else:
            record("Delete DB record", "warning",
                   f"No database record found for '{subdomain}'.")
        conn.close()
    except Exception as e:
        record("Delete DB record", "error", str(e))

    # Step 8 — Prune dangling images
    try:
        result = _run(["docker", "image", "prune", "-f"])
        if result.returncode == 0:
            record("Prune dangling images", "ok",
                   result.stdout.strip() or "Dangling images pruned.")
        else:
            record("Prune dangling images", "warning",
                   result.stderr.strip() or "Nothing to prune or prune skipped.")
    except Exception as e:
        record("Prune dangling images", "error", str(e))

    return results
