# VPS Ubuntu — Update & Upgrade

## Run this every week

```bash
sudo apt update && sudo apt upgrade -y && sudo apt autoremove -y
```

## Reboot if needed

```bash
cat /var/run/reboot-required   # if this file exists, reboot
sudo reboot
```

## If packages are held back

```bash
sudo apt full-upgrade -y
```

## Restart Docker after upgrading

```bash
docker-compose down && docker-compose up -d
```
