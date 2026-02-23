#!/usr/bin/env python3
"""One-time script: registers LHGI in customers.db as a normal customer row.
Run with default path for local dev, or set CUSTOMERS_DB env var for VPS."""

import sqlite3
import bcrypt
import os

DB_PATH = os.environ.get(
    "CUSTOMERS_DB",
    "/home/kdresdell/Documents/DEV/minipass_env/MinipassWebSite/customers.db"
)

placeholder_hash = bcrypt.hashpw(b"RESET_REQUIRED", bcrypt.gensalt())

with sqlite3.connect(DB_PATH) as conn:
    cur = conn.cursor()
    cur.execute("""
        INSERT OR IGNORE INTO customers
          (email, subdomain, app_name, plan, admin_password, port, deployed,
           email_address, email_password, forwarding_email, email_status,
           organization_name, billing_frequency, subscription_status, created_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        "lhgi@jfgoulet.com",
        "lhgi",
        "lhgi",
        "ultimate",
        placeholder_hash,
        8889,
        1,
        "lhgi@minipass.me",  # NOT lhgi_app@minipass.me — special original case
        None,                 # email_password unknown; use "Reset Password" on dashboard
        None,                 # no forwarding
        "success",
        "LHGI",
        "annual",
        "active",
        "2024-01-01T00:00:00"
    ))
    if cur.rowcount:
        print("✓ LHGI added to customers.db successfully.")
    else:
        print("⚠ LHGI already existed — no change made.")
