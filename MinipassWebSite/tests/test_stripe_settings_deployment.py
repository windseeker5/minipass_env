"""
Unit tests for Stripe subscription settings deployment functions.
Tests the migration from environment variables to database settings.
"""

import unittest
import sqlite3
import tempfile
import os
import sys

# Add parent directory to path to import utils
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.deploy_helpers import set_stripe_subscription_settings_to_database


class TestStripeSettingsDeployment(unittest.TestCase):
    """Test Stripe subscription settings database functions"""

    def setUp(self):
        """Create a temporary database for testing"""
        self.temp_db = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.db')
        self.db_path = self.temp_db.name
        self.temp_db.close()

        # Create Setting table
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE setting (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key VARCHAR(100) UNIQUE NOT NULL,
                value TEXT
            )
        """)
        conn.commit()
        conn.close()

    def tearDown(self):
        """Remove temporary database"""
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)

    def test_set_stripe_subscription_settings_insert(self):
        """Test inserting Stripe settings into empty database"""
        # Setup test data
        stripe_customer_id = 'cus_test123'
        stripe_subscription_id = 'sub_test456'
        payment_amount = '7200'
        renewal_date = '2026-11-22T19:36:23'
        tier = 2
        billing_frequency = 'monthly'

        # Call function
        set_stripe_subscription_settings_to_database(
            self.db_path,
            stripe_customer_id,
            stripe_subscription_id,
            payment_amount,
            renewal_date,
            tier,
            billing_frequency
        )

        # Verify all 6 settings were inserted
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM setting")
        count = cursor.fetchone()[0]
        self.assertEqual(count, 6, "Should have 6 Stripe settings")

        # Verify each setting has correct value
        settings_to_check = {
            'STRIPE_CUSTOMER_ID': stripe_customer_id,
            'STRIPE_SUBSCRIPTION_ID': stripe_subscription_id,
            'PAYMENT_AMOUNT': payment_amount,
            'SUBSCRIPTION_RENEWAL_DATE': renewal_date,
            'MINIPASS_TIER': str(tier),
            'BILLING_FREQUENCY': billing_frequency
        }

        for key, expected_value in settings_to_check.items():
            cursor.execute("SELECT value FROM setting WHERE key = ?", (key,))
            result = cursor.fetchone()
            self.assertIsNotNone(result, f"Setting {key} should exist")
            self.assertEqual(result[0], expected_value, f"Setting {key} should have correct value")

        conn.close()

    def test_set_stripe_subscription_settings_update(self):
        """Test updating existing Stripe settings"""
        # Insert initial settings
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO setting (key, value) VALUES (?, ?)",
                      ('STRIPE_CUSTOMER_ID', 'cus_old123'))
        cursor.execute("INSERT INTO setting (key, value) VALUES (?, ?)",
                      ('MINIPASS_TIER', '1'))
        conn.commit()
        conn.close()

        # Update with new values
        new_customer_id = 'cus_new456'
        new_tier = 3

        set_stripe_subscription_settings_to_database(
            self.db_path,
            new_customer_id,
            'sub_new789',
            '12000',
            '2026-12-01T00:00:00',
            new_tier,
            'annual'
        )

        # Verify settings were updated, not duplicated
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM setting WHERE key = 'STRIPE_CUSTOMER_ID'")
        count = cursor.fetchone()[0]
        self.assertEqual(count, 1, "Should only have one STRIPE_CUSTOMER_ID row")

        cursor.execute("SELECT value FROM setting WHERE key = 'STRIPE_CUSTOMER_ID'")
        value = cursor.fetchone()[0]
        self.assertEqual(value, new_customer_id, "Customer ID should be updated")

        cursor.execute("SELECT value FROM setting WHERE key = 'MINIPASS_TIER'")
        tier_value = cursor.fetchone()[0]
        self.assertEqual(tier_value, str(new_tier), "Tier should be updated")

        conn.close()

    def test_stripe_settings_with_empty_values(self):
        """Test creating settings with empty values for beta testers"""
        # Call function with empty values
        set_stripe_subscription_settings_to_database(
            self.db_path,
            '',  # Empty customer ID
            '',  # Empty subscription ID
            '',  # Empty payment amount
            '',  # Empty renewal date
            '',  # Empty tier (passed as empty string)
            ''   # Empty billing frequency
        )

        # Verify settings were created
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM setting")
        count = cursor.fetchone()[0]
        self.assertEqual(count, 6, "Should have 6 settings even with empty values")

        # Verify all values are empty
        cursor.execute("SELECT value FROM setting WHERE key = 'STRIPE_CUSTOMER_ID'")
        value = cursor.fetchone()[0]
        self.assertEqual(value, '', "Customer ID should be empty for beta tester")

        cursor.execute("SELECT value FROM setting WHERE key = 'MINIPASS_TIER'")
        tier_value = cursor.fetchone()[0]
        self.assertEqual(tier_value, '', "Tier should be empty for beta tester")

        conn.close()

    def test_env_file_without_stripe_data(self):
        """Test that .env file generation doesn't include customer-specific Stripe data"""
        # This test simulates the .env file generation
        # We check that the template doesn't contain customer-specific variables

        # Read the deploy_helpers.py file to verify .env generation
        deploy_helpers_path = os.path.join(os.path.dirname(__file__), '..', 'utils', 'deploy_helpers.py')
        with open(deploy_helpers_path, 'r') as f:
            content = f.read()

        # Find the env_content section (around line 623)
        # Verify customer-specific Stripe data is NOT in the template
        self.assertNotIn('STRIPE_CUSTOMER_ID={stripe_data', content,
                        ".env template should not contain STRIPE_CUSTOMER_ID from stripe_data")
        self.assertNotIn('MINIPASS_TIER={tier}', content,
                        ".env template should not contain MINIPASS_TIER variable")
        self.assertNotIn('BILLING_FREQUENCY={billing_frequency}', content,
                        ".env template should not contain BILLING_FREQUENCY variable")

        # Verify shared API key IS present
        self.assertIn('STRIPE_SECRET_KEY={parent_env_vars', content,
                     ".env template should contain STRIPE_SECRET_KEY API key")

    def test_docker_compose_without_tier_vars(self):
        """Test that docker-compose.yml doesn't include tier environment variables"""
        # Read the deploy_helpers.py file to verify docker-compose generation
        deploy_helpers_path = os.path.join(os.path.dirname(__file__), '..', 'utils', 'deploy_helpers.py')
        with open(deploy_helpers_path, 'r') as f:
            content = f.read()

        # Find docker-compose generation sections
        # Verify tier-related env vars are NOT in the template

        # Count occurrences - we want to make sure the environment variables section
        # doesn't contain these (they may appear in comments)
        lines = content.split('\n')
        in_compose_section = False
        compose_lines = []

        for line in lines:
            if 'compose_content = textwrap.dedent' in line:
                in_compose_section = True
            elif in_compose_section:
                compose_lines.append(line)
                if '""")' in line and in_compose_section:
                    in_compose_section = False

        compose_content = '\n'.join(compose_lines)

        # These should NOT be in the environment section
        self.assertNotIn('- ADMIN_EMAIL={admin_email}', compose_content,
                        "docker-compose should not contain ADMIN_EMAIL env var")
        self.assertNotIn('- TIER={tier}', compose_content,
                        "docker-compose should not contain TIER env var")
        self.assertNotIn('- BILLING_FREQUENCY={billing_frequency}', compose_content,
                        "docker-compose should not contain BILLING_FREQUENCY env var")

        # These SHOULD still be in production mode
        self.assertIn('VIRTUAL_HOST={app_name}.minipass.me', compose_content,
                     "docker-compose should contain VIRTUAL_HOST for nginx proxy")


if __name__ == '__main__':
    unittest.main()
