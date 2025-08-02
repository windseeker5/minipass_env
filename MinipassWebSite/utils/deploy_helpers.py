import sqlite3
import bcrypt
import os
import subprocess
from shutil import copytree
from .logging_config import (
    setup_subscription_logger, log_subprocess_call, log_subprocess_result,
    log_operation_start, log_operation_end, log_file_operation, log_validation_check
)

# Initialize subscription logger
logger = setup_subscription_logger()



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







def deploy_customer_container(app_name, admin_email, admin_password, plan, port, organization_name=None):
    import os, shutil, subprocess, textwrap

    log_operation_start(logger, "Deploy Customer Container", 
                       app_name=app_name, 
                       admin_email=admin_email, 
                       plan=plan, 
                       port=port, 
                       organization_name=organization_name)

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

        # Step 2: Copy app template
        logger.info(f"📦 Step 1: Copying app plan '{plan}' from {source_dir} → {target_dir}")
        log_file_operation(logger, f"Copying app template for plan {plan}", f"{source_dir} → {target_dir}")
        shutil.copytree(source_dir, target_dir)
        
        # Verify copy was successful
        if os.path.exists(target_dir):
            log_validation_check(logger, "App template copied successfully", True, f"Target directory created: {target_dir}")
        else:
            log_validation_check(logger, "App template copied successfully", False, "Target directory not found after copy")
            log_operation_end(logger, "Deploy Customer Container", success=False, error_msg="App template copy failed")
            return False

        # Step 3: Setup database
        db_path = os.path.join(target_dir, "instance", "minipass.db")
        logger.info(f"🔐 Step 2: Setting up database at {db_path}")
        
        insert_admin_user(db_path, admin_email, admin_password)
        set_organization_name(db_path, organization_name)
        
        # Verify database was created
        if os.path.exists(db_path):
            log_validation_check(logger, "Database setup completed", True, f"Database file exists: {db_path}")
        else:
            log_validation_check(logger, "Database setup completed", False, "Database file not found after setup")

        # Step 4: Generate docker-compose.yml
        compose_path = os.path.join(deploy_dir, "docker-compose.yml")
        logger.info(f"🐳 Step 3: Writing docker-compose.yml to {compose_path}")

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

              # ✅ NGINX reverse proxy support
              - VIRTUAL_HOST={app_name}.minipass.me
              - VIRTUAL_PORT=5000
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

        log_file_operation(logger, "Writing docker-compose.yml", compose_path, f"Container name: minipass_{app_name}")
        with open(compose_path, "w") as f:
            f.write(compose_content)
            
        # Verify compose file was written
        if os.path.exists(compose_path):
            log_validation_check(logger, "Docker compose file created", True, f"File written: {compose_path}")
        else:
            log_validation_check(logger, "Docker compose file created", False, "Compose file not found after write")

        # Step 5: Deploy the container
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
        
        # Step 6: Verify container is running
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
