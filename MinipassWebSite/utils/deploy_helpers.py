import sqlite3
import bcrypt
import os
import subprocess
from shutil import copytree



def insert_admin_user(db_path, email, password):
    import sqlite3
    import bcrypt

    print(f"🔐 Inserting admin: {email} into {db_path}")
    print(f"🔑 Raw password: {password}")

    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())  # no decode()

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # ✅ Define password_hash as BLOB
    cur.execute("""
    CREATE TABLE IF NOT EXISTS Admin (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password_hash BLOB NOT NULL
    )
    """)

    # 🧹 Remove old admin if present
    cur.execute("DELETE FROM Admin")

    # ✅ Insert password hash as binary
    cur.execute("""
    INSERT INTO Admin (email, password_hash)
    VALUES (?, ?)
    """, (email, hashed))

    conn.commit()
    conn.close()


def set_organization_name(db_path, organization_name):
    """
    Sets the organization name in the app's database.
    
    Args:
        db_path (str): Path to the app's database
        organization_name (str): Organization name to set
    """
    if not organization_name or not organization_name.strip():
        print("⚠️ No organization name provided, skipping organization setup")
        return
    
    print(f"🏢 Setting organization name: {organization_name} in {db_path}")
    
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    # Create or update organization table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS Organization (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Remove existing organization if present
    cur.execute("DELETE FROM Organization")
    
    # Insert new organization
    cur.execute("""
    INSERT INTO Organization (name)
    VALUES (?)
    """, (organization_name.strip(),))
    
    conn.commit()
    conn.close()
    print(f"✅ Organization name set to: {organization_name}")
    
    
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
    from .deploy_helpers import insert_admin_user

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

    # ✅ Plan-to-folder mapping
    plan_folder_map = {
        "basic": "app_o1",
        "pro": "app_o2",
        "ultimate": "app_o3"
    }
    source_folder = plan_folder_map.get(plan.lower(), "app_o1")
    source_dir = os.path.join(base_dir, source_folder)
    target_dir = os.path.join(base_dir, "deployed", app_name, "app")
    os.makedirs(os.path.dirname(target_dir), exist_ok=True)

    print(f"📦 Copying app plan '{plan}' from {source_dir} → {target_dir}")
    shutil.copytree(source_dir, target_dir)

    # 🔐 Insert admin user and set organization name
    db_path = os.path.join(target_dir, "instance", "dev_database.db")
    insert_admin_user(db_path, admin_email, admin_password)
    set_organization_name(db_path, organization_name)

    # 🐳 Write docker-compose.yml
    compose_path = os.path.join(base_dir, "deployed", app_name, "docker-compose.yml")

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

    with open(compose_path, "w") as f:
        f.write(compose_content)

    # 🚀 Deploy the container
    deploy_dir = os.path.join(base_dir, "deployed", app_name)
    try:
        result = subprocess.run(
            ["docker-compose", "up", "-d"],
            cwd=deploy_dir,
            capture_output=True,
            text=True,
            check=True
        )
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Deployment failed:\n{e.stderr}")
        return False
