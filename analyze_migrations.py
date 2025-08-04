#!/usr/bin/env python3
"""
Script to analyze Django migration files and identify dependency issues.
"""

import os
import re
from pathlib import Path

def extract_migration_info(file_path):
    """Extract migration class name and dependencies from a migration file."""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Extract class name
    class_match = re.search(r'class\s+(\w+)\s*\(.*Migration.*\):', content)
    class_name = class_match.group(1) if class_match else None
    
    # Extract dependencies
    deps_match = re.search(r'dependencies\s*=\s*\[(.*?)\]', content, re.DOTALL)
    dependencies = []
    
    if deps_match:
        deps_str = deps_match.group(1)
        # Find all tuples in dependencies
        tuple_pattern = r'\(\s*[\'"](\w+)[\'"]\s*,\s*[\'"]([^\'\"]+)[\'"]\s*\)'
        for match in re.finditer(tuple_pattern, deps_str):
            app_name, migration_name = match.groups()
            dependencies.append((app_name, migration_name))
    
    return class_name, dependencies

def analyze_app_migrations(app_path):
    """Analyze all migrations in an app."""
    migrations_dir = app_path / 'migrations'
    if not migrations_dir.exists():
        return {}
    
    migrations = {}
    for file_path in sorted(migrations_dir.glob('*.py')):
        if file_path.name != '__init__.py':
            try:
                class_name, deps = extract_migration_info(file_path)
                migrations[file_path.stem] = {
                    'file': file_path,
                    'class': class_name,
                    'dependencies': deps
                }
            except Exception as e:
                print(f"Error reading {file_path}: {e}")
    
    return migrations

def check_all_apps():
    """Check all apps for migration issues."""
    apps_dir = Path('apps')
    all_migrations = {}
    
    # First pass: collect all migrations
    for app_dir in sorted(apps_dir.iterdir()):
        if app_dir.is_dir() and not app_dir.name.startswith('__'):
            app_name = app_dir.name
            migrations = analyze_app_migrations(app_dir)
            if migrations:
                all_migrations[app_name] = migrations
    
    # Second pass: check dependencies
    issues = []
    for app_name, migrations in all_migrations.items():
        for migration_name, migration_info in migrations.items():
            for dep_app, dep_migration in migration_info['dependencies']:
                # Check if dependency exists
                if dep_app not in all_migrations:
                    issues.append({
                        'type': 'missing_app',
                        'app': app_name,
                        'migration': migration_name,
                        'missing': f"{dep_app} (entire app)"
                    })
                elif dep_migration not in all_migrations[dep_app]:
                    issues.append({
                        'type': 'missing_migration',
                        'app': app_name,
                        'migration': migration_name,
                        'missing': f"{dep_app}.{dep_migration}"
                    })
    
    return all_migrations, issues

def print_report(all_migrations, issues):
    """Print a detailed report of migrations and issues."""
    print("Django Migration Analysis Report")
    print("=" * 60)
    
    # Print all migrations by app
    print("\nMigrations by App:")
    for app_name, migrations in sorted(all_migrations.items()):
        print(f"\n{app_name}:")
        for migration_name in sorted(migrations.keys()):
            deps = migrations[migration_name]['dependencies']
            print(f"  - {migration_name}")
            if deps:
                for dep_app, dep_migration in deps:
                    print(f"      → depends on: {dep_app}.{dep_migration}")
    
    # Print issues
    print("\n" + "=" * 60)
    print("Issues Found:")
    if not issues:
        print("✓ No migration dependency issues found!")
    else:
        for issue in issues:
            print(f"\n✗ {issue['app']}.{issue['migration']}")
            print(f"  Missing dependency: {issue['missing']}")

def main():
    """Main function."""
    all_migrations, issues = check_all_apps()
    print_report(all_migrations, issues)
    
    if issues:
        print("\n" + "=" * 60)
        print("Recommended Actions:")
        print("1. Check if migration files were renamed or deleted")
        print("2. Ensure all apps are properly installed in INSTALLED_APPS")
        print("3. Run 'python manage.py makemigrations' to create missing migrations")
        print("4. Consider resetting migrations if the database is empty")

if __name__ == "__main__":
    main()