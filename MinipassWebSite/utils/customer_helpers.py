import sqlite3
import bcrypt
import json
import logging
import re
import subprocess
from datetime import datetime



CUSTOMERS_DB = "customers.db"
RESERVED_SUBDOMAINS = {"www", "admin", "api", "app", "mail"}

def init_customers_db():
    with sqlite3.connect(CUSTOMERS_DB) as conn:
        cur = conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            subdomain TEXT UNIQUE NOT NULL,
            app_name TEXT NOT NULL,
            plan TEXT NOT NULL,
            admin_password TEXT NOT NULL,
            port INTEGER NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            deployed INTEGER DEFAULT 0,
            email_address TEXT,
            email_password TEXT,
            forwarding_email TEXT,
            email_created TEXT,
            email_status TEXT DEFAULT 'pending',
            organization_name TEXT,
            billing_frequency TEXT DEFAULT 'monthly',
            subscription_start_date TEXT,
            subscription_end_date TEXT,
            stripe_price_id TEXT,
            stripe_checkout_session_id TEXT,
            stripe_customer_id TEXT,
            stripe_subscription_id TEXT,
            payment_amount INTEGER,
            currency TEXT DEFAULT 'cad',
            subscription_status TEXT DEFAULT 'active'
        )
        """)
        
        # Create processed events table for idempotency
        cur.execute("""
        CREATE TABLE IF NOT EXISTS processed_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id TEXT UNIQUE NOT NULL,
            event_type TEXT NOT NULL,
            processed_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # Create promo codes table
        cur.execute("""
        CREATE TABLE IF NOT EXISTS promo_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            plan TEXT NOT NULL DEFAULT 'pro',
            tier INTEGER NOT NULL DEFAULT 2,
            billing_frequency TEXT NOT NULL DEFAULT 'annual',
            max_uses INTEGER NOT NULL DEFAULT 1,
            uses_count INTEGER NOT NULL DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            expires_at TEXT,
            notes TEXT,
            redeemed_by_subdomain TEXT,
            redeemed_at TEXT
        )
        """)
        conn.commit()


def subdomain_taken(subdomain):
    if subdomain in RESERVED_SUBDOMAINS:
        return True
    with sqlite3.connect(CUSTOMERS_DB) as conn:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM customers WHERE subdomain = ?", (subdomain,))
        return cur.fetchone() is not None


def get_next_available_port(base_port=9100):
    with sqlite3.connect(CUSTOMERS_DB) as conn:
        cur = conn.cursor()
        cur.execute("SELECT MAX(port) FROM customers")
        row = cur.fetchone()
        return base_port if row[0] is None else row[0] + 1







def insert_customer(email, subdomain, app_name, plan, password, port,
                   email_address=None, forwarding_email=None, email_status='pending', organization_name=None,
                   billing_frequency='monthly', subscription_start_date=None, subscription_end_date=None,
                   stripe_price_id=None, stripe_checkout_session_id=None,
                   stripe_customer_id=None, stripe_subscription_id=None,
                   payment_amount=None, currency='cad', subscription_status='active'):
    """
    Insert a new customer into the database.

    Args:
        email: Customer email
        subdomain: Customer subdomain
        app_name: App name
        plan: Subscription plan (basic/pro/ultimate)
        password: Admin password
        port: Port number
        email_address: Email address created for customer
        forwarding_email: Email forwarding destination
        email_status: Email setup status
        organization_name: Organization name
        billing_frequency: 'monthly' or 'annual'
        subscription_start_date: Subscription start date (ISO format)
        subscription_end_date: Subscription end date (ISO format)
        stripe_price_id: Stripe Price ID used
        stripe_checkout_session_id: Stripe Checkout Session ID
        stripe_customer_id: Stripe Customer ID (cus_xxx)
        stripe_subscription_id: Stripe Subscription ID (sub_xxx)
        payment_amount: Payment amount in cents
        currency: Currency code (default 'cad')
        subscription_status: Subscription status (default 'active')
    """
    with sqlite3.connect(CUSTOMERS_DB) as conn:
        cur = conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            subdomain TEXT UNIQUE NOT NULL,
            app_name TEXT NOT NULL,
            plan TEXT NOT NULL,
            admin_password TEXT NOT NULL,
            port INTEGER NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            deployed INTEGER DEFAULT 0,
            email_address TEXT,
            email_password TEXT,
            forwarding_email TEXT,
            email_created TEXT,
            email_status TEXT DEFAULT 'pending',
            organization_name TEXT,
            billing_frequency TEXT DEFAULT 'monthly',
            subscription_start_date TEXT,
            subscription_end_date TEXT,
            stripe_price_id TEXT,
            stripe_checkout_session_id TEXT,
            stripe_customer_id TEXT,
            stripe_subscription_id TEXT,
            payment_amount INTEGER,
            currency TEXT DEFAULT 'cad',
            subscription_status TEXT DEFAULT 'active'
        )
        """)

        cur.execute("""
        INSERT INTO customers (email, subdomain, app_name, plan, admin_password, port, created_at, deployed,
                             email_address, email_password, forwarding_email, email_status, organization_name,
                             billing_frequency, subscription_start_date, subscription_end_date,
                             stripe_price_id, stripe_checkout_session_id, stripe_customer_id, stripe_subscription_id,
                             payment_amount, currency, subscription_status)
        VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            email,
            subdomain,
            app_name,
            plan,
            bcrypt.hashpw(password.encode(), bcrypt.gensalt()),  # Hashed password for security
            port,
            datetime.utcnow().isoformat(),
            email_address,
            password,  # Use same password for email
            forwarding_email,
            email_status,
            organization_name,
            billing_frequency,
            subscription_start_date,
            subscription_end_date,
            stripe_price_id,
            stripe_checkout_session_id,
            stripe_customer_id,
            stripe_subscription_id,
            payment_amount,
            currency,
            subscription_status
        ))

        conn.commit()


def update_customer_email_status(subdomain, email_address, email_status, email_created=None):
    """
    Updates the email status and details for a customer.
    
    Args:
        subdomain (str): Customer's subdomain
        email_address (str): The email address that was created
        email_status (str): Status of email creation ('success', 'failed', 'pending')
        email_created (str): Timestamp when email was created (optional)
    """
    with sqlite3.connect(CUSTOMERS_DB) as conn:
        cur = conn.cursor()
        
        if email_created is None:
            email_created = datetime.utcnow().isoformat()
        
        cur.execute("""
        UPDATE customers 
        SET email_address = ?, email_status = ?, email_created = ?
        WHERE subdomain = ?
        """, (email_address, email_status, email_created, subdomain))
        
        conn.commit()


def update_customer_deployment_status(subdomain, deployed=True):
    """
    Updates the deployment status for a customer.
    
    Args:
        subdomain (str): Customer's subdomain
        deployed (bool): Deployment status (True for deployed, False for not deployed)
    """
    with sqlite3.connect(CUSTOMERS_DB) as conn:
        cur = conn.cursor()
        
        deployed_value = 1 if deployed else 0
        
        cur.execute("""
        UPDATE customers 
        SET deployed = ?
        WHERE subdomain = ?
        """, (deployed_value, subdomain))
        
        conn.commit()


def get_customer_by_subdomain(subdomain):
    """
    Retrieves customer information by subdomain.
    
    Args:
        subdomain (str): Customer's subdomain
        
    Returns:
        dict: Customer information or None if not found
    """
    with sqlite3.connect(CUSTOMERS_DB) as conn:
        conn.row_factory = sqlite3.Row  # Enable dict-like access
        cur = conn.cursor()
        cur.execute("SELECT * FROM customers WHERE subdomain = ?", (subdomain,))
        row = cur.fetchone()
        return dict(row) if row else None


def get_customers_with_email_status(status):
    """
    Retrieves customers filtered by email status.
    
    Args:
        status (str): Email status to filter by
        
    Returns:
        list: List of customer dictionaries
    """
    with sqlite3.connect(CUSTOMERS_DB) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM customers WHERE email_status = ?", (status,))
        rows = cur.fetchall()
        return [dict(row) for row in rows]


def is_event_processed(event_id):
    """
    Check if a Stripe event has already been processed.
    
    Args:
        event_id (str): Stripe event ID
        
    Returns:
        bool: True if event was already processed, False otherwise
    """
    with sqlite3.connect(CUSTOMERS_DB) as conn:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM processed_events WHERE event_id = ?", (event_id,))
        return cur.fetchone() is not None


def mark_event_processed(event_id, event_type):
    """
    Mark a Stripe event as processed to prevent duplicate handling.

    Args:
        event_id (str): Stripe event ID
        event_type (str): Type of Stripe event
    """
    with sqlite3.connect(CUSTOMERS_DB) as conn:
        cur = conn.cursor()
        cur.execute("""
        INSERT OR IGNORE INTO processed_events (event_id, event_type, processed_at)
        VALUES (?, ?, ?)
        """, (event_id, event_type, datetime.utcnow().isoformat()))
        conn.commit()


def update_customer_plan(subdomain, plan=None, billing_frequency=None, payment_amount=None,
                         subscription_end_date=None, stripe_price_id=None, subscription_status=None):
    """Update plan-related fields for a customer (all args optional).

    Args:
        subdomain (str): Customer's subdomain
        plan (str|None): New plan key (basic/pro/ultimate)
        billing_frequency (str|None): 'monthly' or 'annual'
        payment_amount (int|None): Amount in cents
        subscription_end_date (str|None): ISO date string
        stripe_price_id (str|None): Stripe Price ID
        subscription_status (str|None): Subscription status string
    """
    updates = []
    params = []

    if plan is not None:
        updates.append("plan = ?")
        params.append(plan)
    if billing_frequency is not None:
        updates.append("billing_frequency = ?")
        params.append(billing_frequency)
    if payment_amount is not None:
        updates.append("payment_amount = ?")
        params.append(payment_amount)
    if subscription_end_date is not None:
        updates.append("subscription_end_date = ?")
        params.append(subscription_end_date)
    if stripe_price_id is not None:
        updates.append("stripe_price_id = ?")
        params.append(stripe_price_id)
    if subscription_status is not None:
        updates.append("subscription_status = ?")
        params.append(subscription_status)

    if not updates:
        return

    params.append(subdomain)
    with sqlite3.connect(CUSTOMERS_DB) as conn:
        cur = conn.cursor()
        cur.execute(f"UPDATE customers SET {', '.join(updates)} WHERE subdomain = ?", tuple(params))
        conn.commit()


def update_customer_stripe_ids(subdomain, stripe_customer_id=None, stripe_subscription_id=None):
    """
    Update Stripe Customer and Subscription IDs for a customer.

    Args:
        subdomain (str): Customer's subdomain
        stripe_customer_id (str, optional): Stripe Customer ID (cus_xxx)
        stripe_subscription_id (str, optional): Stripe Subscription ID (sub_xxx)
    """
    with sqlite3.connect(CUSTOMERS_DB) as conn:
        cur = conn.cursor()

        # Build dynamic update query based on which IDs are provided
        updates = []
        params = []

        if stripe_customer_id is not None:
            updates.append("stripe_customer_id = ?")
            params.append(stripe_customer_id)

        if stripe_subscription_id is not None:
            updates.append("stripe_subscription_id = ?")
            params.append(stripe_subscription_id)

        if updates:
            params.append(subdomain)
            query = f"UPDATE customers SET {', '.join(updates)} WHERE subdomain = ?"
            cur.execute(query, tuple(params))
            conn.commit()


def get_customer_by_stripe_subscription_id(stripe_subscription_id):
    """
    Retrieve customer information by Stripe Subscription ID.

    Args:
        stripe_subscription_id (str): Stripe Subscription ID

    Returns:
        dict: Customer information or None if not found
    """
    with sqlite3.connect(CUSTOMERS_DB) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM customers WHERE stripe_subscription_id = ?", (stripe_subscription_id,))
        row = cur.fetchone()
        return dict(row) if row else None


def get_customer_by_stripe_session_id(stripe_checkout_session_id):
    """
    Retrieve customer information by Stripe Checkout Session ID.

    Args:
        stripe_checkout_session_id (str): Stripe Checkout Session ID

    Returns:
        dict: Customer information or None if not found
    """
    with sqlite3.connect(CUSTOMERS_DB) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM customers WHERE stripe_checkout_session_id = ?", (stripe_checkout_session_id,))
        row = cur.fetchone()
        return dict(row) if row else None


def get_all_customers():
    """
    Fetch all customers for admin view.

    Returns:
        list: List of customer dictionaries ordered by creation date (newest first)
    """
    with sqlite3.connect(CUSTOMERS_DB) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("""
            SELECT subdomain, email, app_name, plan, port, deployed,
                   email_address, email_password, email_status, created_at,
                   subscription_status, admin_password, organization_name
            FROM customers
            ORDER BY created_at DESC
        """)
        rows = cur.fetchall()
        return [dict(row) for row in rows]


def update_customer_password(subdomain, new_password):
    """
    Update a customer's admin password.

    Args:
        subdomain (str): Customer's subdomain
        new_password (str): New plaintext password (will be hashed)

    Returns:
        bool: True if update succeeded, False otherwise
    """
    with sqlite3.connect(CUSTOMERS_DB) as conn:
        cur = conn.cursor()
        hashed = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt())
        cur.execute("""
            UPDATE customers
            SET admin_password = ?, email_password = ?
            WHERE subdomain = ?
        """, (hashed, new_password, subdomain))
        conn.commit()
        return cur.rowcount > 0


def validate_promo_code(code):
    """
    Read-only check of a promo code. Does NOT mark the code as used.

    Args:
        code (str): Promo code to validate

    Returns:
        dict: {valid, plan, tier, billing_frequency, error}
    """
    with sqlite3.connect(CUSTOMERS_DB) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM promo_codes WHERE code = ?", (code.upper(),))
        row = cur.fetchone()

    if not row:
        return {"valid": False, "error": "Code invalide"}

    row = dict(row)

    if row["uses_count"] >= row["max_uses"]:
        return {"valid": False, "error": "Code déjà utilisé"}

    if row["expires_at"]:
        now = datetime.utcnow().isoformat()
        if now > row["expires_at"]:
            return {"valid": False, "error": "Code expiré"}

    return {
        "valid": True,
        "plan": row["plan"],
        "tier": row["tier"],
        "billing_frequency": row["billing_frequency"],
        "error": None
    }


def redeem_promo_code(code, subdomain):
    """
    Atomically mark a promo code as used (race-condition safe).

    Args:
        code (str): Promo code to redeem
        subdomain (str): The subdomain that is redeeming the code

    Returns:
        bool: True if successfully redeemed, False if already used or invalid
    """
    now = datetime.utcnow().isoformat()
    with sqlite3.connect(CUSTOMERS_DB) as conn:
        cur = conn.cursor()
        cur.execute("""
            UPDATE promo_codes
            SET uses_count = uses_count + 1,
                redeemed_by_subdomain = ?,
                redeemed_at = ?
            WHERE code = ? AND uses_count < max_uses
        """, (subdomain, now, code.upper()))
        conn.commit()
        return cur.rowcount > 0


def get_all_promo_codes():
    """
    Fetch all promo codes for admin view.

    Returns:
        list: List of promo code dictionaries ordered by creation date (newest first)
    """
    with sqlite3.connect(CUSTOMERS_DB) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM promo_codes ORDER BY created_at DESC")
        rows = cur.fetchall()
        return [dict(row) for row in rows]


def create_promo_code(code, plan='pro', tier=2, billing_frequency='annual',
                      max_uses=1, expires_at=None, notes=None):
    """
    Insert a new promo code into the database.

    Args:
        code (str): The promo code (will be uppercased)
        plan (str): Subscription plan
        tier (int): Tier level
        billing_frequency (str): 'monthly' or 'annual'
        max_uses (int): Maximum number of uses
        expires_at (str|None): Expiry date in ISO format, or None for no expiry
        notes (str|None): Optional notes about this code

    Returns:
        bool: True if created successfully, False if code already exists
    """
    try:
        with sqlite3.connect(CUSTOMERS_DB) as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO promo_codes (code, plan, tier, billing_frequency, max_uses, expires_at, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (code.upper(), plan, tier, billing_frequency, max_uses, expires_at, notes))
            conn.commit()
            return True
    except sqlite3.IntegrityError:
        return False


def delete_promo_code(code: str) -> bool:
    """Delete a promo code by code string. Returns True if deleted."""
    with sqlite3.connect(CUSTOMERS_DB) as conn:
        cur = conn.execute("DELETE FROM promo_codes WHERE code = ?", (code.upper(),))
        conn.commit()
    return cur.rowcount > 0


def update_promo_code(code: str, plan: str, tier: int, billing_frequency: str,
                      max_uses: int, expires_at, notes) -> bool:
    """Update editable fields of a promo code. Returns True if found + updated."""
    with sqlite3.connect(CUSTOMERS_DB) as conn:
        cur = conn.execute(
            """UPDATE promo_codes
               SET plan=?, tier=?, billing_frequency=?, max_uses=?, expires_at=?, notes=?
               WHERE code=?""",
            (plan, tier, billing_frequency, max_uses, expires_at, notes, code.upper())
        )
        conn.commit()
    return cur.rowcount > 0


# ── Docker container helpers ───────────────────────────────────────────────────

def _is_production():
    """Thin wrapper so we can import lazily and avoid circular deps."""
    from utils.deploy_helpers import is_production_environment
    return is_production_environment()


def _resolve_container_name(subdomain):
    """Return the Docker container name for a subdomain.

    New containers are named minipass_{subdomain}. Legacy containers
    (e.g. lhgi) use just the subdomain as their name. We probe for the
    new name first and fall back to the bare subdomain.
    """
    new_name = f"minipass_{subdomain}"
    probe = subprocess.run(
        ['docker', 'inspect', '--format', '{{.Name}}', new_name],
        capture_output=True, text=True, timeout=5
    )
    if probe.returncode == 0:
        return new_name
    return subdomain


def get_container_admins(subdomain):
    """Return a list of admin dicts from the customer's Docker container.

    In local dev (no production containers present) returns two mock admins so
    the full UI/flow can be tested without any Docker containers.
    """
    if not re.match(r'^[a-zA-Z0-9-]+$', subdomain):
        raise ValueError("Invalid subdomain")

    if not _is_production():
        logging.info(f"[DEV MODE] Returning mock admins for {subdomain}")
        return [
            {"id": 1, "email": "admin@example.com", "first_name": "Test", "last_name": "Admin"},
            {"id": 2, "email": "owner@example.com", "first_name": "Owner", "last_name": "User"},
        ]

    container_name = _resolve_container_name(subdomain)
    script = (
        "import sqlite3, json; "
        "conn = sqlite3.connect('instance/minipass.db'); "
        "rows = conn.execute('SELECT id, email, first_name, last_name FROM admin').fetchall(); "
        "print(json.dumps([{'id':r[0],'email':r[1],'first_name':r[2],'last_name':r[3]} for r in rows])); "
        "conn.close()"
    )
    result = subprocess.run(
        ['docker', 'exec', container_name, 'python', '-c', script],
        capture_output=True, text=True, timeout=10
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "Container not reachable")
    return json.loads(result.stdout.strip())


def reset_container_admin_password(subdomain, admin_email, new_password):
    """Reset a specific admin's bcrypt password inside a customer's Docker container.

    In local dev mode this is a no-op (returns True) so email can still be
    tested without any Docker containers.
    """
    if not re.match(r'^[a-zA-Z0-9-]+$', subdomain):
        raise ValueError("Invalid subdomain")

    if not _is_production():
        logging.info(f"[DEV MODE] Skipping docker exec password reset for {subdomain}/{admin_email}")
        return True

    container_name = _resolve_container_name(subdomain)
    script = (
        "import bcrypt, sqlite3, sys; "
        f"email = {repr(admin_email)}; "
        f"new_pw = {repr(new_password)}; "
        "hashed = bcrypt.hashpw(new_pw.encode(), bcrypt.gensalt()).decode(); "
        "conn = sqlite3.connect('instance/minipass.db'); "
        "rows = conn.execute('UPDATE admin SET password_hash=? WHERE email=?', (hashed, email)).rowcount; "
        "conn.commit(); conn.close(); "
        "sys.exit(0 if rows > 0 else 1)"
    )
    result = subprocess.run(
        ['docker', 'exec', container_name, 'python', '-c', script],
        capture_output=True, text=True, timeout=15
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"Reset failed (admin not found or container error): {result.stderr.strip()}"
        )
    return True
