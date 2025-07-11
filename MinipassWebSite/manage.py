import os
import sqlite3
import docker
import shutil

CUSTOMERS_DB = "customers.db"
DEPLOYED_FOLDER = "../deployed"

def load_customers():
    conn = sqlite3.connect(CUSTOMERS_DB)
    cursor = conn.cursor()
    cursor.execute("SELECT id, subdomain, email, port FROM customers")
    rows = cursor.fetchall()
    conn.close()
    return rows

def delete_customer_from_db(subdomain):
    conn = sqlite3.connect(CUSTOMERS_DB)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM customers WHERE subdomain = ?", (subdomain,))
    conn.commit()
    conn.close()

def remove_deployed_folder(subdomain):
    path = os.path.join(DEPLOYED_FOLDER, subdomain)
    if os.path.exists(path):
        shutil.rmtree(path)
        print(f"🗑️ Deleted folder: {path}")
    else:
        print(f"⚠️ Folder not found: {path}")



def remove_docker_container(subdomain):
    client = docker.from_env()
    target = None

    # 🔍 Try to match container name (e.g., minipass_rocco)
    for container in client.containers.list(all=True):
        if subdomain in container.name:
            target = container
            break

    # 🔁 If not found by name, match by image tag (e.g., rocco-flask-app)
    if not target:
        for container in client.containers.list(all=True):
            tags = container.image.tags
            if tags and any(f"{subdomain}-flask-app" in tag for tag in tags):
                target = container
                break

    if target:
        print(f"🛑 Stopping and removing container '{target.name}' (image: {target.image.tags[0] if target.image.tags else 'unknown'})...")
        try:
            target.stop(timeout=5)
            target.remove(force=True, v=True)
            print("✅ Docker container removed.")
        except Exception as e:
            print(f"❌ Error removing container: {e}")
    else:
        print(f"⚠️ No Docker container found for '{subdomain}'")










def main():
    customers = load_customers()
    if not customers:
        print("ℹ️ No customers found.")
        return

    print("📋 Customers:")
    for idx, (cid, subdomain, email, port) in enumerate(customers, 1):
        print(f"{idx}. {subdomain}.minipass.me | Port: {port} | Email: {email}")

    try:
        choice = int(input("\n🔎 Enter the number of the customer you want to delete: "))
        selected = customers[choice - 1]
    except (ValueError, IndexError):
        print("❌ Invalid choice.")
        return

    _, subdomain, email, port = selected
    confirm = input(f"\n❗ Are you sure you want to delete '{subdomain}.minipass.me'? Type YES to confirm: ")
    if confirm.strip().upper() != "YES":
        print("❌ Aborted.")
        return

    print(f"\n🚧 Deleting customer '{subdomain}'...")
    remove_docker_container(subdomain)
    remove_deployed_folder(subdomain)
    delete_customer_from_db(subdomain)
    print(f"✅ Customer '{subdomain}' fully deleted.")

if __name__ == "__main__":
    main()
