import docker

client = docker.from_env()

# 🧩 Find containers whose image name includes '-flask-app'
targets = []
for c in client.containers.list(all=True):
    image_tags = c.image.tags
    if image_tags and any("-flask-app" in tag for tag in image_tags):
        targets.append(c)

if not targets:
    print("ℹ️ No '*-flask-app' containers found.")
else:
    for container in targets:
        print(f"🛑 Stopping {container.name} (image: {container.image.tags[0]})...")
        try:
            container.stop(timeout=5)
        except Exception as e:
            print(f"⚠️  Error stopping {container.name}: {e}")

        print(f"🗑️ Removing {container.name}...")
        try:
            container.remove(force=True, v=True)
        except Exception as e:
            print(f"⚠️  Error removing {container.name}: {e}")

# ♻️ Prune unused Docker resources
print("🧹 Pruning unused images and volumes...")
pruned_images = client.images.prune()
pruned_volumes = client.volumes.prune()

print(f"🧹 Images pruned: {pruned_images.get('ImagesDeleted', [])}")
print(f"🧹 Volumes pruned: {pruned_volumes.get('VolumesDeleted', [])}")
print("✅ Done.")

