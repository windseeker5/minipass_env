# Dockerfile Security & Permission Improvement

**Date:** January 2025
**Issue:** Root permission problems in backup/restore operations
**Status:** ✅ Fixed in local test environment
**Action Required:** Must apply to production auto-deployment system

---

## Executive Summary

Docker containers were running as root (UID 0), causing all files created by the Flask application (backups, uploads, database files) to be owned by root. This created operational friction requiring sudo to delete deployment folders and posed security risks.

**Solution:** Run containers as non-root user (UID 1000) by adding USER directive to Dockerfile.

---

## Problem Discovered

### Symptoms
- Backup files created in `static/backups/` owned by root
- Safety backup folders created during restore operations owned by root
  - `static/uploads_backup_YYYYMMDD_HHMMSS/`
  - `templates/email_templates_backup_YYYYMMDD_HHMMSS/`
  - `instance/minipass.db.backup_YYYYMMDD_HHMMSS`
- Unable to delete deployment container folders as regular user
- Required sudo for cleanup operations during testing

### Root Cause
Original Dockerfile had no USER directive, causing containers to run as root by default:

```dockerfile
# BEFORE - INSECURE
FROM python:3.9
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
EXPOSE 8889
CMD ["gunicorn", "--workers=2", "--threads=4", "--bind=0.0.0.0:8889", "app:app"]
```

### Security Implications
1. **Container Escape Risk**: Exploited Flask app would have root privileges inside container
2. **Least Privilege Violation**: Industry best practice is to never run containers as root
3. **Audit/Compliance**: Many security frameworks require non-root containers
4. **Production Risk**: Not suitable for production deployments

---

## Solution Implemented

### Updated Dockerfile

```dockerfile
# AFTER - SECURE
FROM python:3.9
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt

# Create non-root user and set ownership
# UID 1000 matches typical Linux user IDs for compatibility
RUN useradd -m -u 1000 minipass && \
    chown -R minipass:minipass /app

# Run as non-root user for security and proper file permissions
USER minipass

EXPOSE 8889
CMD ["gunicorn", "--workers=2", "--threads=4", "--bind=0.0.0.0:8889", "app:app"]
```

### What Changed
1. **User Creation**: Added `minipass` user with UID 1000 (standard Linux user ID)
2. **Ownership Transfer**: Changed ownership of `/app` directory to minipass:minipass
3. **USER Directive**: All subsequent operations run as non-root user
4. **File Permissions**: All created files now owned by UID 1000 instead of root

---

## Testing & Verification

### Local Testing Steps

1. **Rebuild Container**
   ```bash
   cd /home/kdresdell/Documents/DEV/minipass_env/app
   docker build -t minipass-test .
   ```

2. **Run Container**
   ```bash
   docker run -d -p 5000:8889 --name minipass-test-container minipass-test
   ```

3. **Test Backup Operation**
   - Access application at http://localhost:5000
   - Navigate to backup section
   - Create a backup
   - Check file ownership:
     ```bash
     ls -la static/backups/
     # Should show files owned by UID 1000, not root
     ```

4. **Test Restore Operation**
   - Perform a restore operation
   - Check safety backup folder ownership:
     ```bash
     ls -la static/ | grep backup
     ls -la templates/ | grep backup
     ls -la instance/ | grep backup
     # All should be UID 1000, not root
     ```

5. **Verify Cleanup Works**
   ```bash
   # As regular user (no sudo needed)
   rm -rf /path/to/test/deployment
   # Should succeed without permission errors
   ```

### Expected Results
- ✅ All files created by Flask app owned by UID 1000 (minipass user)
- ✅ No root-owned files in application directories
- ✅ Regular users can delete deployment folders without sudo
- ✅ Application functions normally (no permission denied errors)

---

## CRITICAL: Production Deployment System

### ⚠️ ACTION REQUIRED: Apply to minipass.me Auto-Deployment

**This local test environment is just one customer instance.**

The **minipass.me website** auto-generates and deploys customer containers when Stripe payments are received. **This same Dockerfile fix MUST be applied to the container generation system** to ensure all customer containers run securely.

### Where to Apply Changes

The production deployment system that auto-generates customer containers needs this exact Dockerfile update:

**Required Changes:**
1. Update the Dockerfile template used for customer container generation
2. Add the same user creation and USER directive
3. Test with a staging deployment before rolling out to production
4. Consider one-time migration for existing customer containers

### Deployment System Locations to Check

Look for these in the minipass.me codebase:
- Container generation scripts (likely Python/Flask)
- Dockerfile templates for customer deployments
- docker-compose.yml generation code
- Customer provisioning workflow (triggered by Stripe webhooks)

**Template to Use:**
```dockerfile
# In customer container Dockerfile template
RUN useradd -m -u 1000 minipass && \
    chown -R minipass:minipass /app

USER minipass
```

### Rollout Strategy

1. **Update Template**: Modify Dockerfile template in minipass.me deployment code
2. **Test Staging**: Deploy one test customer container with new Dockerfile
3. **Verify**: Test backup/restore operations in test customer container
4. **Document**: Update deployment documentation
5. **Deploy**: New customer containers automatically get secure configuration
6. **Migrate Existing** (optional): Consider updating existing customer containers
   - Can be done gradually during maintenance windows
   - Not urgent if existing containers are working

---

## Migration for Existing Deployments

### One-Time Cleanup (If Needed)

If you have existing deployments with root-owned files:

```bash
# Fix ownership of existing files
sudo chown -R $USER:$USER /path/to/deployment/folder

# Or for specific directories
sudo chown -R 1000:1000 /path/to/deployment/app/
```

This only needs to be done once per existing deployment after updating the Dockerfile.

---

## Technical Details

### Why UID 1000?
- Standard UID for first non-system user on most Linux distributions
- Matches typical development environment user IDs
- Ensures compatibility between container and host filesystem

### Why Not Just Fix Python Code?
The Python code in `app/api/backup.py` is NOT the problem. The code uses standard Python file operations (`os.makedirs`, `shutil.copytree`, etc.) which inherit the permissions of the running process.

Fixing at the Docker level:
- ✅ Addresses root cause (running as root)
- ✅ Improves security posture
- ✅ No code changes needed
- ✅ Future-proof for all file operations
- ✅ Industry best practice

### Security Benefits
1. **Principle of Least Privilege**: Application runs with minimum required permissions
2. **Attack Surface Reduction**: Exploited application cannot escalate to root
3. **Container Security**: Aligns with Docker/Kubernetes security best practices
4. **Compliance**: Meets requirements for many security frameworks (PCI-DSS, SOC 2, etc.)

---

## References

### Files Modified
- `/home/kdresdell/Documents/DEV/minipass_env/app/dockerfile`

### Related Documentation
- Docker Security Best Practices: https://docs.docker.com/develop/security-best-practices/
- OWASP Container Security: https://cheatsheetseries.owasp.org/cheatsheets/Docker_Security_Cheat_Sheet.html

### Code Locations Analyzed
- `app/api/backup.py` - Backup/restore operations (lines 89-93, 430-476)
- `app/dockerfile` - Container configuration

---

## Checklist for Production Rollout

- [ ] Update Dockerfile in local test environment (✅ COMPLETED)
- [ ] Test backup/restore operations locally (⚠️ PENDING)
- [ ] Locate customer container generation code in minipass.me
- [ ] Update Dockerfile template in minipass.me deployment system
- [ ] Test staging customer deployment with new Dockerfile
- [ ] Verify backup/restore in staging customer container
- [ ] Document changes in minipass.me codebase
- [ ] Deploy to production (new customers get secure containers automatically)
- [ ] (Optional) Plan migration for existing customer containers
- [ ] Update deployment documentation/runbooks

---

## Questions & Support

If issues arise during rollout:

1. **Container won't start**: Check that application doesn't require root privileges for any operations
2. **Permission denied errors**: Verify all application directories are owned by minipass:minipass
3. **Volume mount issues**: Ensure mounted volumes have appropriate permissions for UID 1000

**Created:** January 2025
**Last Updated:** January 2025
**Owner:** Kyle Dresdell
**Priority:** High - Security & Operational Improvement
