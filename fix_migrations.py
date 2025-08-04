#!/usr/bin/env python3
"""
Script to fix Django migration issues by checking and resolving dependency problems.
"""

import os
import sys
import django
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).resolve().parent))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.apps import apps
from django.db import connection
from django.db.migrations.loader import MigrationLoader
from django.db.migrations.exceptions import NodeNotFoundError

def check_migrations():
    """Check for migration issues and report them."""
    print("Checking migrations...")
    
    try:
        loader = MigrationLoader(connection)
        loader.build_graph()
        print("✓ Migration graph built successfully!")
        return True
    except NodeNotFoundError as e:
        print(f"✗ Migration dependency error: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False

def list_all_migrations():
    """List all migrations in the project."""
    print("\nListing all migrations by app:")
    
    for app_config in apps.get_app_configs():
        if app_config.path.startswith(str(Path(__file__).parent / 'apps')):
            app_label = app_config.label
            migrations_dir = Path(app_config.path) / 'migrations'
            
            if migrations_dir.exists():
                migration_files = sorted([
                    f.stem for f in migrations_dir.glob('*.py')
                    if f.stem != '__init__'
                ])
                
                if migration_files:
                    print(f"\n{app_label}:")
                    for migration in migration_files:
                        print(f"  - {migration}")

def check_migration_dependencies():
    """Check each app's migration dependencies."""
    print("\nChecking migration dependencies:")
    
    issues = []
    
    for app_config in apps.get_app_configs():
        if app_config.path.startswith(str(Path(__file__).parent / 'apps')):
            app_label = app_config.label
            migrations_dir = Path(app_config.path) / 'migrations'
            
            if migrations_dir.exists():
                for migration_file in sorted(migrations_dir.glob('*.py')):
                    if migration_file.stem != '__init__':
                        try:
                            # Read the migration file
                            content = migration_file.read_text()
                            
                            # Look for dependencies
                            if 'dependencies = [' in content:
                                start = content.find('dependencies = [')
                                end = content.find(']', start) + 1
                                deps_section = content[start:end]
                                
                                # Extract dependencies
                                import ast
                                try:
                                    # Parse the dependencies list
                                    deps_str = deps_section.split('=', 1)[1].strip()
                                    dependencies = ast.literal_eval(deps_str)
                                    
                                    for dep in dependencies:
                                        if isinstance(dep, tuple) and len(dep) == 2:
                                            dep_app, dep_migration = dep
                                            
                                            # Check if dependency exists
                                            dep_app_config = apps.get_app_config(dep_app)
                                            dep_migrations_dir = Path(dep_app_config.path) / 'migrations'
                                            dep_file = dep_migrations_dir / f"{dep_migration}.py"
                                            
                                            if not dep_file.exists():
                                                issues.append({
                                                    'app': app_label,
                                                    'migration': migration_file.stem,
                                                    'missing_dep': f"{dep_app}.{dep_migration}"
                                                })
                                                print(f"✗ {app_label}.{migration_file.stem} depends on missing {dep_app}.{dep_migration}")
                                            else:
                                                print(f"✓ {app_label}.{migration_file.stem} -> {dep_app}.{dep_migration}")
                                except:
                                    pass
                        except Exception as e:
                            print(f"Error reading {migration_file}: {e}")
    
    return issues

def suggest_fixes(issues):
    """Suggest fixes for migration issues."""
    if not issues:
        print("\n✓ No migration dependency issues found!")
        return
    
    print("\nSuggested fixes:")
    for issue in issues:
        print(f"\nIssue: {issue['app']}.{issue['migration']} depends on missing {issue['missing_dep']}")
        print("Possible solutions:")
        print("1. Check if the dependency migration file exists but has a different name")
        print("2. Run 'python manage.py makemigrations' to create missing migrations")
        print("3. Reset migrations for the affected app (use with caution)")

def main():
    """Main function to run migration checks."""
    print("Django Migration Fixer")
    print("=" * 50)
    
    # Check if migrations can be loaded
    can_load = check_migrations()
    
    # List all migrations
    list_all_migrations()
    
    # Check dependencies
    issues = check_migration_dependencies()
    
    # Suggest fixes
    suggest_fixes(issues)
    
    if not can_load:
        print("\n⚠️  Migration loader failed. You may need to:")
        print("1. Delete migration files and recreate them")
        print("2. Reset the database migration history")
        print("3. Fix dependency issues manually")
    
    print("\n" + "=" * 50)
    print("Migration check complete!")

if __name__ == "__main__":
    main()