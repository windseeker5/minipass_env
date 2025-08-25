# Migration Plan: Pass to Passport System
## Version 3.0 - Final Plan

---

## Executive Summary
Migration of 17 users with remaining hockey sessions from prototype Pass system to production Passport system.

---

## Migration Overview

### Scope
- **Users to migrate**: 17 friends/testers
- **Total sessions to preserve**: 39 remaining games
- **Target database**: Fresh/empty production database
- **Target activity**: "Hockey du midi LHGI - 2025 / 2026"
- **Passport type**: "Remplacant"

### Key Principles
- Simple, clean migration (prototype → production)
- Preserve only essential data (remaining uses)
- Generate new QR codes for all users
- No historical data preservation needed

---

## Database Structure Comparison

### Old System (Pass)
```sql
Table: pass
- id (primary key)
- pass_code (unique QR code)
- user_name
- user_email
- phone_number
- games_remaining (sessions left)
- sold_amt (price paid)
- paid_ind (payment status)
- paid_date
- activity (text field)
- notes
```

### New System (Passport)
```sql
Table: user
- id (primary key)
- name
- email
- phone_number

Table: passport
- id (primary key)
- pass_code (unique QR code)
- user_id (foreign key)
- activity_id (foreign key)
- passport_type_id (foreign key)
- uses_remaining (sessions left)
- sold_amt
- paid (boolean)
- paid_date
- notes
```

---

## Migration Data Summary

### Users with Remaining Sessions
| Name | Email | Remaining | Amount Paid |
|------|-------|-----------|-------------|
| Bobby Lebel | bobby.lebel2@outlook.fr | 5 | $0.00 |
| Marco Vigneau-Henry | MARCO.VIGNEAU-HENRY@TELUS.COM | 3 | $50.00 |
| Dominic Blanchette | dblanchet@structuresgb.com | 3 | $50.00 |
| Dave Gagnon | dave.gagnon@gagnonimage.com | 3 | $50.00 |
| David-Olivier Marmen | david-olivier.r.marmen@desjardins.com | 3 | $50.00 |
| Pierre-Luc Boulet | pierre-luc.boulet@mnp.ca | 3 | $50.00 |
| Samuel Gendreau | gendro_68@hotmail.com | 3 | $50.00 |
| Gérald Chénard | gchenard@telus.net | 3 | $38.00 |
| Paul-Aimé Leblanc | leblancpaulaime@gmail.com | 2 | $50.00 |
| Kathleen Fournier Slater | kath.fslater@gmail.com | 2 | $50.00 |
| Stéphane D'Astous | ledas38@hotmail.com | 2 | $50.00 |
| Samuel Turbide | turbide9@gmail.com | 2 | $50.00 |
| Eric Leblanc | ericleblanclr3@gmail.com | 2 | $50.00 |
| Steven Belanger | steven.belanger@rimouski.ca | 1 | $50.00 |
| Jonathan Brisson | jonathanbrisson12@hotmail.com | 1 | $50.00 |
| Luc Massé | lucmasse1972@gmail.com | 1 | $50.00 |
| Thomas Dubé-Nadal | tomdubnad@gmail.com | 1 | $0.00 |

**Total**: 17 users, 39 remaining sessions

---

## Migration Process

### Phase 1: Pre-Migration Setup (Manual)
1. **Backup** old database (already completed: `lhgi_prod_database_backup_20250824_021538.db`)
2. **Clear/flush** new production database via admin settings
3. **Create activity** in new system:
   - Name: "Hockey du midi LHGI - 2025 / 2026"
   - Note the `activity_id` (likely = 1)
4. **Create passport type**:
   - Name: "Remplacant"
   - Type: "substitute"
   - Link to activity
   - Note the `passport_type_id` (likely = 1)

### Phase 2: Run Migration Script
1. **Configure script** with:
   - Old database path
   - New database path
   - Activity ID
   - Passport Type ID
2. **Execute** migration script (see `migrate_pass_to_passport.py`)
3. **Verify** migration success

### Phase 3: Post-Migration
1. **Generate report** of new pass codes
2. **Send communications** to users with new QR codes
3. **Test** one user login
4. **Archive** old database

---

## Data Mapping Rules

### User Creation
- `user.name` ← `pass.user_name`
- `user.email` ← `pass.user_email.lower()` (normalized)
- `user.phone_number` ← `pass.phone_number`

### Passport Creation
- `passport.pass_code` ← Generate new unique code
- `passport.user_id` ← Newly created user ID
- `passport.activity_id` ← Pre-created activity ID
- `passport.passport_type_id` ← Pre-created passport type ID
- `passport.uses_remaining` ← `pass.games_remaining`
- `passport.sold_amt` ← `pass.sold_amt`
- `passport.paid` ← `pass.paid_ind`
- `passport.paid_date` ← `pass.paid_date`
- `passport.notes` ← "Migrated from 2024-2025 season. Had X uses remaining."

---

## Validation Queries

Run these after migration to verify success:

```sql
-- Check user count (should be 17)
SELECT COUNT(*) FROM user;

-- Check passport count (should be 17)
SELECT COUNT(*) FROM passport;

-- Check total remaining uses (should be 39)
SELECT SUM(uses_remaining) FROM passport;

-- List all migrated users with their remaining uses
SELECT u.name, u.email, p.uses_remaining, p.pass_code
FROM user u
JOIN passport p ON u.id = p.user_id
ORDER BY p.uses_remaining DESC;
```

---

## What Gets Lost (Acceptable)
- ❌ Old QR codes (all invalidated)
- ❌ Redemption history (28 past usage records)
- ❌ Original creation dates
- ❌ Admin tracking (who created original passes)

## What Gets Preserved (Critical)
- ✅ User information (name, email, phone)
- ✅ Remaining sessions (games_remaining → uses_remaining)
- ✅ Payment information (amount, status, date)
- ✅ Special cases noted (free passes, different pricing)

---

## Risk Assessment
- **Risk Level**: MINIMAL 🟢
- **Rollback Strategy**: Re-flush database and retry
- **User Impact**: Minimal (friends/testers, understanding audience)
- **Data Loss Risk**: None (keeping backup of old database)
- **Execution Time**: ~1 hour total

---

## Communication Template

### Email to Users (Post-Migration)
```
Subject: Your Hockey du midi Pass - System Upgrade

Hi [Name],

Great news! We've upgraded our pass system to serve you better.

Your new digital pass is attached with [X] remaining sessions for the 2025/2026 season.

The old QR code from previous emails won't work anymore - please use this new one.

Questions? Just reply to this email.

See you on the ice!
```

---

## Success Criteria
- [ ] All 17 users successfully migrated
- [ ] All 39 remaining sessions preserved
- [ ] Payment information accurately transferred
- [ ] New QR codes generated for all users
- [ ] Migration notes added to each passport
- [ ] Validation queries return expected results
- [ ] Test user can successfully log in

---

## Files
- **Migration Script**: `/test/migrate_pass_to_passport.py`
- **Old Database**: `lhgi_prod_database_backup_20250824_021538.db`
- **New Database**: `instance/minipass.db`
- **Migration Log**: Will be generated at `/test/migration_report.csv`

---

*Document created: 2025-01-24*
*Migration planned for prototype → production transition*