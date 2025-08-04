# Django Migration Fix Guide

## Problem Description

You're encountering a `NodeNotFoundError` for the CommonItems app:
```
django.db.migrations.exceptions.NodeNotFoundError: Migration CommonItems.0004_alter_vehiclesize_options_alter_vehicletype_options_and_more dependencies reference nonexistent parent node ('CommonItems', '0003_alter_commonitem_options_alter_itembrand_options_and_more')
```

## Root Cause

This error typically occurs when:
1. The migration files exist on disk but Django's migration history in the database is out of sync
2. Migrations were applied and then the files were modified or renamed
3. The database was copied from another environment with different migration history

## Solution Steps

### Step 1: Verify Migration Files Exist

First, confirm that all migration files are present:
```bash
ls -la apps/CommonItems/migrations/
```

You should see:
- `0001_initial.py`
- `0002_initial.py`
- `0003_alter_commonitem_options_alter_itembrand_options_and_more.py`
- `0004_alter_vehiclesize_options_alter_vehicletype_options_and_more.py`

✅ **Status**: All files are present and have correct syntax.

### Step 2: Fix the Migration Issue

Run these commands in your virtual environment:

```bash
# Activate your virtual environment first
source /home/ellis_1/MoreVans-BE/venv/bin/activate

# Option 1: Fake the migrations (recommended)
python manage.py migrate CommonItems 0002_initial --fake
python manage.py migrate CommonItems 0003_alter_commonitem_options_alter_itembrand_options_and_more --fake
python manage.py migrate CommonItems 0004_alter_vehiclesize_options_alter_vehicletype_options_and_more --fake

# Then apply all other migrations
python manage.py migrate
```

### Step 3: If Step 2 Doesn't Work

Try these alternatives:

#### Option A: Reset and Reapply (if database is empty)
```bash
python manage.py migrate CommonItems zero
python manage.py migrate CommonItems --fake-initial
python manage.py migrate
```

#### Option B: Database Surgery (advanced)
1. Access your database and run:
```sql
-- Check current migration state
SELECT * FROM django_migrations WHERE app = 'CommonItems';

-- Remove problematic entries
DELETE FROM django_migrations WHERE app = 'CommonItems' AND name = '0003_alter_commonitem_options_alter_itembrand_options_and_more';
DELETE FROM django_migrations WHERE app = 'CommonItems' AND name = '0004_alter_vehiclesize_options_alter_vehicletype_options_and_more';
```

2. Then fake the migrations:
```bash
python manage.py migrate CommonItems --fake
```

### Step 4: Verify All Apps

After fixing CommonItems, check all other apps:
```bash
python manage.py showmigrations
```

If you see any unapplied migrations (marked with `[ ]`), run:
```bash
python manage.py migrate
```

## Files Created to Help

1. **`analyze_migrations.py`** - Analyzes migration dependencies without Django
2. **`reset_migrations.py`** - Generates SQL commands to reset migrations
3. **`fix_all_migrations.sh`** - Interactive script to fix migrations
4. **`migration_fix_commands.txt`** - List of commands to run

## Prevention

To avoid this issue in the future:
1. Always use version control for migration files
2. Don't modify migration files after they've been applied
3. Use `--fake` flag carefully and only when you're sure the database schema matches
4. Keep migration history synchronized across all environments

## Additional Notes

- The analysis shows all migration files are present and have correct dependencies
- The only non-Django dependency is on `auth.0012_alter_user_first_name_max_length` in the User app, which is normal
- All migration files compile without syntax errors

If you continue to have issues after following these steps, the problem might be:
1. Database connection issues
2. Permissions problems
3. Corrupted migration history in the database

In such cases, consider starting with a fresh database if possible.