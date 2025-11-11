import sqlite3
import bcrypt
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
            payment_amount INTEGER,
            currency TEXT DEFAULT 'cad',
            subscription_status TEXT DEFAULT 'active'
        )
        """)

        cur.execute("""
        INSERT INTO customers (email, subdomain, app_name, plan, admin_password, port, created_at, deployed,
                             email_address, email_password, forwarding_email, email_status, organization_name,
                             billing_frequency, subscription_start_date, subscription_end_date,
                             stripe_price_id, stripe_checkout_session_id, payment_amount, currency, subscription_status)
        VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
