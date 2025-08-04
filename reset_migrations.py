#!/usr/bin/env python3
"""
Script to generate SQL commands to reset Django migration state.
This is useful when migration files exist but the database thinks they don't.
"""

import os
from pathlib import Path

def generate_reset_sql():
    """Generate SQL commands to reset migration state."""
    
    print("-- SQL Commands to Reset Django Migration State")
    print("-- WARNING: Only run these if you understand the implications!")
    print("-- This will mark all migrations as not applied.")
    print("-- Make sure to backup your database first!")
    print()
    
    # Generate SQL to show current migration state
    print("-- First, check current migration state:")
    print("SELECT * FROM django_migrations ORDER BY app, name;")
    print()
    
    # Generate SQL to delete specific problematic migrations
    print("-- If you need to reset specific migrations:")
    print("-- Delete the problematic CommonItems migrations:")
    print("DELETE FROM django_migrations WHERE app = 'CommonItems' AND name = '0003_alter_commonitem_options_alter_itembrand_options_and_more';")
    print("DELETE FROM django_migrations WHERE app = 'CommonItems' AND name = '0004_alter_vehiclesize_options_alter_vehicletype_options_and_more';")
    print()
    
    # Generate SQL to reset all migrations for an app
    print("-- Or reset all CommonItems migrations:")
    print("-- DELETE FROM django_migrations WHERE app = 'CommonItems';")
    print()
    
    # List all apps that might need resetting
    apps_dir = Path('apps')
    app_names = []
    
    for app_dir in sorted(apps_dir.iterdir()):
        if app_dir.is_dir() and not app_dir.name.startswith('__'):
            migrations_dir = app_dir / 'migrations'
            if migrations_dir.exists() and any(migrations_dir.glob('*.py')):
                app_names.append(app_dir.name)
    
    print("-- To reset ALL app migrations (use with extreme caution):")
    for app_name in app_names:
        print(f"-- DELETE FROM django_migrations WHERE app = '{app_name}';")
    
    print()
    print("-- After deleting migration records, you can re-apply migrations with:")
    print("-- python manage.py migrate --fake")
    print("-- or")
    print("-- python manage.py migrate --fake-initial")

def generate_migration_commands():
    """Generate Django management commands to fix migrations."""
    
    print("\n" + "="*60)
    print("Django Management Commands to Fix Migrations")
    print("="*60)
    print()
    
    print("# Option 1: Fake the specific migration that's causing issues")
    print("python manage.py migrate CommonItems 0002_initial --fake")
    print("python manage.py migrate CommonItems 0003_alter_commonitem_options_alter_itembrand_options_and_more --fake")
    print("python manage.py migrate CommonItems 0004_alter_vehiclesize_options_alter_vehicletype_options_and_more --fake")
    print()
    
    print("# Option 2: Show current migration state")
    print("python manage.py showmigrations CommonItems")
    print()
    
    print("# Option 3: Reset all migrations for CommonItems (if database is empty)")
    print("python manage.py migrate CommonItems zero")
    print("python manage.py migrate CommonItems --fake-initial")
    print()
    
    print("# Option 4: If you need to recreate migrations")
    print("# First, backup and remove migration files (except __init__.py)")
    print("# Then:")
    print("python manage.py makemigrations CommonItems")
    print("python manage.py migrate CommonItems --fake-initial")

def main():
    """Main function."""
    print("Migration Reset Helper")
    print("=====================")
    print()
    print("This script generates commands to help fix Django migration issues.")
    print()
    
    generate_reset_sql()
    generate_migration_commands()
    
    print("\n" + "="*60)
    print("IMPORTANT NOTES:")
    print("="*60)
    print("1. Always backup your database before running these commands")
    print("2. The --fake flag tells Django to mark migrations as applied without running them")
    print("3. Only use --fake if the database schema already matches the migration")
    print("4. If you're starting fresh, you might want to drop and recreate the database")

if __name__ == "__main__":
    main()