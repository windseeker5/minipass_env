import sqlite3
import bcrypt
import os
import subprocess
from .logging_config import (
    setup_subscription_logger, log_subprocess_call, log_subprocess_result,
    log_operation_start, log_operation_end, log_file_operation, log_validation_check
)

# Initialize subscription logger
logger = setup_subscription_logger()


def is_production_environment():
    """
    Detect if running on production VPS or local development machine.

    Detection method: Check if 'minipass_env_proxy' Docker network exists.
    - Production VPS: Has this network (created by nginx-proxy setup)
    - Local dev: Doesn't have this network

    Returns:
        bool: True if production VPS, False if local development
    """
    try:
        result = subprocess.run(
            ["docker", "network", "ls", "--filter", "name=minipass_env_proxy", "--format", "{{.Name}}"],
            capture_output=True,
            text=True,
            timeout=5
        )
        is_prod = "minipass_env_proxy" in result.stdout
        return is_prod
    except Exception as e:
        logger.warning(f"⚠️ Could not detect environment (assuming local): {e}")
        return False  # Default to local/safe mode if can't detect



def insert_admin_user(db_path, email, password):
    import sqlite3
    import bcrypt

    log_operation_start(logger, "Insert Admin User", db_path=db_path, email=email)
    
    logger.info(f"🔐 Inserting admin: {email} into {db_path}")
    log_file_operation(logger, "Connecting to database", db_path)

    try:
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        logger.info(f"🔑 Password hashed successfully for {email}")

        conn = sqlite3.connect(db_path)
        cur = conn.cursor()

        # Create Admin table if it doesn't exist
        logger.info("📋 Creating/verifying Admin table structure")
        cur.execute("""
        CREATE TABLE IF NOT EXISTS Admin (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash BLOB NOT NULL
        )
        """)
        log_validation_check(logger, "Admin table structure", True, "Table created/verified successfully")

        # Remove old admin if present
        logger.info("🧹 Removing existing admin users")
        cur.execute("DELETE FROM Admin")
        deleted_count = cur.rowcount
        logger.info(f"   🗑️ Removed {deleted_count} existing admin users")

        # Insert new admin user
        logger.info(f"➕ Inserting new admin user: {email}")
        cur.execute("""
        INSERT INTO Admin (email, password_hash)
        VALUES (?, ?)
        """, (email, hashed))
        
        if cur.rowcount == 1:
            log_validation_check(logger, f"Admin user {email} inserted", True, "1 row inserted successfully")
        else:
            log_validation_check(logger, f"Admin user {email} inserted", False, f"Expected 1 row, got {cur.rowcount}")

        conn.commit()
        conn.close()
        
        log_operation_end(logger, "Insert Admin User", success=True)
        
    except Exception as e:
        error_msg = f"Failed to insert admin user: {str(e)}"
        logger.error(f"❌ {error_msg}")
        log_operation_end(logger, "Insert Admin User", success=False, error_msg=error_msg)
        raise


def set_organization_name(db_path, organization_name):
    """
    Sets the organization name in the app's database.
    
    Args:
        db_path (str): Path to the app's database
        organization_name (str): Organization name to set
    """
    if not organization_name or not organization_name.strip():
        logger.info("⚠️ No organization name provided, skipping organization setup")
        return
    
    log_operation_start(logger, "Set Organization Name", db_path=db_path, organization_name=organization_name)
    
    try:
        logger.info(f"🏢 Setting organization name: {organization_name} in {db_path}")
        log_file_operation(logger, "Connecting to database for organization setup", db_path)
        
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        
        # Create organization table if it doesn't exist
        logger.info("📋 Creating/verifying Organization table structure")
        cur.execute("""
        CREATE TABLE IF NOT EXISTS Organization (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        log_validation_check(logger, "Organization table structure", True, "Table created/verified successfully")
        
        # Remove existing organization if present
        logger.info("🧹 Removing existing organization entries")
        cur.execute("DELETE FROM Organization")
        deleted_count = cur.rowcount
        logger.info(f"   🗑️ Removed {deleted_count} existing organization entries")
        
        # Insert new organization
        logger.info(f"➕ Inserting organization: {organization_name.strip()}")
        cur.execute("""
        INSERT INTO Organization (name)
        VALUES (?)
        """, (organization_name.strip(),))
        
        if cur.rowcount == 1:
            log_validation_check(logger, f"Organization {organization_name} inserted", True, "1 row inserted successfully")
        else:
            log_validation_check(logger, f"Organization {organization_name} inserted", False, f"Expected 1 row, got {cur.rowcount}")
        
        conn.commit()
        conn.close()
        
        log_operation_end(logger, "Set Organization Name", success=True)
        
    except Exception as e:
        error_msg = f"Failed to set organization name: {str(e)}"
        logger.error(f"❌ {error_msg}")
        log_operation_end(logger, "Set Organization Name", success=False, error_msg=error_msg)
        raise
    
    
def update_docker_compose_org_name(compose_content, organization_name):
    """
    Updates the docker-compose content to include the organization name.
    
    Args:
        compose_content (str): The docker-compose content
        organization_name (str): Organization name
        
    Returns:
        str: Updated docker-compose content
    """
    if organization_name and organization_name.strip():
        # Update the ORG_NAME environment variable
        lines = compose_content.split('\n')
        for i, line in enumerate(lines):
            if 'ORG_NAME=' in line:
                lines[i] = f"          - ORG_NAME={organization_name.strip()}"
                break
        return '\n'.join(lines)
    return compose_content







def deploy_customer_container(app_name, admin_email, admin_password, plan, port, organization_name=None, tier=1, billing_frequency='monthly'):
    import os, shutil, subprocess, textwrap

    # Map tier to activity limits for logging
    tier_limits = {1: 1, 2: 15, 3: 100}
    activity_limit = tier_limits.get(tier, 1)

    log_operation_start(logger, "Deploy Customer Container",
                       app_name=app_name,
                       admin_email=admin_email,
                       plan=plan,
                       tier=tier,
                       billing_frequency=billing_frequency,
                       activity_limit=activity_limit,
                       port=port,
                       organization_name=organization_name)

    # Detect environment (production VPS vs local dev)
    is_production = is_production_environment()
    env_label = "PRODUCTION (VPS)" if is_production else "LOCAL (Development)"
    logger.info(f"🌍 Environment: {env_label}")

    logger.info(f"📊 Tier Configuration:")
    logger.info(f"   Plan: {plan}")
    logger.info(f"   Tier: {tier}")
    logger.info(f"   Activity Limit: {activity_limit}")
    logger.info(f"   Billing: {billing_frequency}")

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

    # Plan-to-folder mapping - now using single 'app' folder for all plans
    plan_folder_map = {
        "basic": "app",
        "pro": "app",
        "ultimate": "app"
    }
    source_folder = plan_folder_map.get(plan.lower(), "app")
    source_dir = os.path.join(base_dir, source_folder)
    target_dir = os.path.join(base_dir, "deployed", app_name, "app")
    deploy_dir = os.path.join(base_dir, "deployed", app_name)
    
    logger.info(f"📂 Base directory: {base_dir}")
    logger.info(f"📋 Plan '{plan}' mapped to source folder: {source_folder}")
    logger.info(f"📂 Source directory: {source_dir}")
    logger.info(f"📂 Target directory: {target_dir}")
    logger.info(f"📂 Deploy directory: {deploy_dir}")

    try:
        # Step 1: Create target directory structure
        log_file_operation(logger, "Creating target directory structure", os.path.dirname(target_dir))
        os.makedirs(os.path.dirname(target_dir), exist_ok=True)
        
        # Verify source directory exists
        if not os.path.exists(source_dir):
            error_msg = f"Source directory does not exist: {source_dir}"
            log_validation_check(logger, "Source directory exists", False, error_msg)
            log_operation_end(logger, "Deploy Customer Container", success=False, error_msg=error_msg)
            return False
        else:
            log_validation_check(logger, "Source directory exists", True, f"Found: {source_dir}")

        # Step 2: Clone app repository from GitHub
        git_repo_url = "git@github.com:windseeker5/dpm.git"
        logger.info(f"📦 Step 1: Cloning app repository for plan '{plan}' → {target_dir}")
        log_file_operation(logger, f"Cloning app repository for plan {plan}", f"{git_repo_url} → {target_dir}")

        # Execute git clone
        git_clone_cmd = ["git", "clone", git_repo_url, target_dir]
        log_subprocess_call(logger, git_clone_cmd, "Cloning app repository from GitHub")

        try:
            clone_result = subprocess.run(
                git_clone_cmd,
                capture_output=True,
                text=True,
                check=True
            )
            log_subprocess_result(logger, clone_result, "Repository clone completed")
        except subprocess.CalledProcessError as e:
            error_msg = f"Git clone failed: {e.stderr if e.stderr else str(e)}"
            logger.error(f"❌ {error_msg}")
            log_validation_check(logger, "Repository cloned successfully", False, error_msg)
            log_operation_end(logger, "Deploy Customer Container", success=False, error_msg=error_msg)
            return False

        # Verify clone was successful
        if os.path.exists(target_dir) and os.path.exists(os.path.join(target_dir, ".git")):
            log_validation_check(logger, "Repository cloned successfully", True, f"Target directory created: {target_dir}")
        else:
            log_validation_check(logger, "Repository cloned successfully", False, "Target directory or .git folder not found after clone")
            log_operation_end(logger, "Deploy Customer Container", success=False, error_msg="Repository clone verification failed")
            return False

        # Step 3: Generate .env file with tier-specific configuration
        logger.info(f"⚙️  Step 2a: Creating .env file with tier {tier} configuration")
        env_path = os.path.join(target_dir, ".env")

        # Get API keys from parent environment (from main .env in base_dir)
        parent_env_path = os.path.join(base_dir, ".env")
        parent_env_vars = {}
        if os.path.exists(parent_env_path):
            with open(parent_env_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        parent_env_vars[key.strip()] = value.strip()

        env_content = textwrap.dedent(f"""\
        # Auto-generated deployment configuration for {app_name}
        # Generated on deployment

        # Tier Configuration
        MINIPASS_TIER={tier}
        BILLING_FREQUENCY={billing_frequency}

        # Google Maps API Configuration
        GOOGLE_MAPS_API_KEY={parent_env_vars.get('GOOGLE_MAPS_API_KEY', '')}

        # Google AI (Gemini) API Configuration
        GOOGLE_AI_API_KEY={parent_env_vars.get('GOOGLE_AI_API_KEY', '')}

        # Groq API Configuration
        GROQ_API_KEY={parent_env_vars.get('GROQ_API_KEY', '')}

        # Unsplash API Configuration
        UNSPLASH_ACCESS_KEY={parent_env_vars.get('UNSPLASH_ACCESS_KEY', '')}

        # Chatbot Configuration
        CHATBOT_ENABLE_GEMINI=true
        CHATBOT_ENABLE_GROQ=true
        CHATBOT_ENABLE_OLLAMA=false
        CHATBOT_DAILY_BUDGET_CENTS=1000
        CHATBOT_MONTHLY_BUDGET_CENTS=10000
        """)

        log_file_operation(logger, "Writing .env file", env_path)
        with open(env_path, "w") as f:
            f.write(env_content)

        log_validation_check(logger, ".env file created", os.path.exists(env_path), f"File written: {env_path}")

        # Step 4: Install dependencies (required for migrations)
        logger.info(f"📦 Step 2b: Installing application dependencies")
        requirements_path = os.path.join(target_dir, "requirements.txt")

        if os.path.exists(requirements_path):
            pip_install_cmd = ["pip", "install", "-r", requirements_path]
            log_subprocess_call(logger, pip_install_cmd, "Installing Python dependencies")

            try:
                pip_result = subprocess.run(
                    pip_install_cmd,
                    cwd=target_dir,
                    capture_output=True,
                    text=True,
                    check=True
                )
                log_subprocess_result(logger, pip_result, "Dependencies installation completed")
                log_validation_check(logger, "Dependencies installed", True, "All packages installed successfully")
            except subprocess.CalledProcessError as e:
                error_msg = f"Dependency installation failed: {e.stderr if e.stderr else str(e)}"
                logger.error(f"❌ {error_msg}")
                if e.stdout:
                    logger.error(f"📤 Pip stdout: {e.stdout}")
                log_validation_check(logger, "Dependencies installed", False, error_msg)
                log_operation_end(logger, "Deploy Customer Container", success=False, error_msg=error_msg)
                return False
        else:
            logger.warning(f"⚠️ requirements.txt not found at {requirements_path}")

        # Step 5: Initialize database schema
        logger.info(f"🗄️  Step 2c: Initializing database schema")

        # Create instance directory
        instance_dir = os.path.join(target_dir, "instance")
        os.makedirs(instance_dir, exist_ok=True)
        log_file_operation(logger, "Creating instance directory", instance_dir)

        # Run Flask database migrations to create schema
        db_path = os.path.join(instance_dir, "minipass.db")
        logger.info(f"   Running flask db upgrade to create database schema")

        migrate_cmd = ["flask", "db", "upgrade"]
        log_subprocess_call(logger, migrate_cmd, "Running database migrations")

        try:
            migrate_result = subprocess.run(
                migrate_cmd,
                cwd=target_dir,
                capture_output=True,
                text=True,
                check=True,
                env={**os.environ, "FLASK_APP": "app.py"}
            )
            log_subprocess_result(logger, migrate_result, "Database migrations completed")
            log_validation_check(logger, "Database schema created", True, "Flask migrations ran successfully")
        except subprocess.CalledProcessError as e:
            error_msg = f"Database migration failed: {e.stderr if e.stderr else str(e)}"
            logger.error(f"❌ {error_msg}")
            if e.stdout:
                logger.error(f"📤 Migration stdout: {e.stdout}")
            log_validation_check(logger, "Database schema created", False, error_msg)
            log_operation_end(logger, "Deploy Customer Container", success=False, error_msg=error_msg)
            return False

        # Verify database file was created
        if os.path.exists(db_path):
            log_validation_check(logger, "Database file created", True, f"Database exists: {db_path}")
        else:
            log_validation_check(logger, "Database file created", False, "Database file not found after migrations")
            log_operation_end(logger, "Deploy Customer Container", success=False, error_msg="Database file not created")
            return False

        # Step 6: Configure admin user and organization
        logger.info(f"🔐 Step 2d: Configuring admin user and organization")
        
        insert_admin_user(db_path, admin_email, admin_password)
        set_organization_name(db_path, organization_name)
        
        # Verify database was created
        if os.path.exists(db_path):
            log_validation_check(logger, "Database setup completed", True, f"Database file exists: {db_path}")
        else:
            log_validation_check(logger, "Database setup completed", False, "Database file not found after setup")

        # Step 7: Generate docker-compose.yml (production vs local)
        compose_path = os.path.join(deploy_dir, "docker-compose.yml")
        logger.info(f"🐳 Step 3: Writing docker-compose.yml to {compose_path}")

        if is_production:
            # PRODUCTION: Use nginx reverse proxy with external network
            logger.info("   📝 Generating PRODUCTION docker-compose.yml (nginx reverse proxy)")
            compose_content = textwrap.dedent(f"""\
            version: '3.8'

            services:
              flask-app:
                container_name: minipass_{app_name}
                build:
                  context: ./app

                volumes:
                  - ./app:/app
                  - ./app/instance:/app/instance
                environment:
                  - FLASK_ENV=dev
                  - ADMIN_EMAIL={admin_email}
                  - ADMIN_PASSWORD={admin_password}
                  - ORG_NAME={organization_name or app_name}

                  # ✅ Tier Configuration (CRITICAL for activity limits!)
                  - TIER={tier}
                  - BILLING_FREQUENCY={billing_frequency}

                  # ✅ NGINX reverse proxy support
                  - VIRTUAL_HOST={app_name}.minipass.me
                  - VIRTUAL_PORT=8889
                  - LETSENCRYPT_HOST={app_name}.minipass.me
                  - LETSENCRYPT_EMAIL=kdresdell@gmail.com

                restart: unless-stopped
                networks:
                  - proxy

            networks:
              proxy:
                external:
                  name: minipass_env_proxy
            """)
        else:
            # LOCAL: Direct port mapping, no external network
            logger.info("   📝 Generating LOCAL docker-compose.yml (direct port mapping)")
            logger.info(f"   🌐 App will be accessible at: http://localhost:{port}")
            compose_content = textwrap.dedent(f"""\
            version: '3.8'

            services:
              flask-app:
                container_name: minipass_{app_name}
                build:
                  context: ./app

                ports:
                  - "{port}:8889"

                volumes:
                  - ./app:/app
                  - ./app/instance:/app/instance
                environment:
                  - FLASK_ENV=dev
                  - ADMIN_EMAIL={admin_email}
                  - ADMIN_PASSWORD={admin_password}
                  - ORG_NAME={organization_name or app_name}

                  # ✅ Tier Configuration (CRITICAL for activity limits!)
                  - TIER={tier}
                  - BILLING_FREQUENCY={billing_frequency}

                restart: unless-stopped
            """)

        log_file_operation(logger, "Writing docker-compose.yml", compose_path, f"Container name: minipass_{app_name}")
        with open(compose_path, "w") as f:
            f.write(compose_content)
            
        # Verify compose file was written
        if os.path.exists(compose_path):
            log_validation_check(logger, "Docker compose file created", True, f"File written: {compose_path}")
        else:
            log_validation_check(logger, "Docker compose file created", False, "Compose file not found after write")

        # Step 8: Deploy the container
        logger.info(f"🚀 Step 4: Deploying container in {deploy_dir}")
        command = ["docker-compose", "up", "-d"]
        log_subprocess_call(logger, command, f"Deploying container for {app_name}")

        result = subprocess.run(
            command,
            cwd=deploy_dir,
            capture_output=True,
            text=True,
            check=True
        )
        log_subprocess_result(logger, result, f"Container deployment completed for {app_name}")

        # Step 9: Verify container is running
        verify_command = ["docker", "ps", "--filter", f"name=minipass_{app_name}", "--format", "table {{.Names}}\t{{.Status}}"]
        log_subprocess_call(logger, verify_command, f"Verifying container status for {app_name}")
        
        verify_result = subprocess.run(verify_command, capture_output=True, text=True)
        log_subprocess_result(logger, verify_result, f"Container status check completed for {app_name}")
        
        if verify_result.returncode == 0 and f"minipass_{app_name}" in verify_result.stdout:
            log_validation_check(logger, f"Container minipass_{app_name} is running", True, "Container found in docker ps output")
        else:
            log_validation_check(logger, f"Container minipass_{app_name} is running", False, "Container not found in docker ps output")

        log_operation_end(logger, "Deploy Customer Container", success=True)
        return True
        
    except subprocess.CalledProcessError as e:
        error_msg = f"Docker deployment failed: {e.stderr if e.stderr else str(e)}"
        logger.error(f"❌ {error_msg}")
        if e.stdout:
            logger.error(f"📤 Stdout: {e.stdout}")
        log_operation_end(logger, "Deploy Customer Container", success=False, error_msg=error_msg)
        return False
    except Exception as e:
        error_msg = f"Unexpected error during deployment: {str(e)}"
        logger.error(f"❌ {error_msg}")
        log_operation_end(logger, "Deploy Customer Container", success=False, error_msg=error_msg)
        return False
