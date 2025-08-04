#!/bin/bash

# Django Migration Fix Script
# This script provides various options to fix Django migration issues

echo "Django Migration Fix Script"
echo "=========================="
echo ""
echo "This script will help fix migration issues in your Django project."
echo "Make sure you have:"
echo "1. Activated your virtual environment"
echo "2. Set up your database connection"
echo "3. Backed up your database (if it contains important data)"
echo ""
echo "Press Enter to continue or Ctrl+C to cancel..."
read

# Function to run Django commands
run_django_command() {
    echo "Running: $1"
    python manage.py $1
    if [ $? -ne 0 ]; then
        echo "Command failed. Make sure your virtual environment is activated and Django is installed."
        exit 1
    fi
}

echo ""
echo "Choose an option:"
echo "1. Show current migration status"
echo "2. Fix CommonItems migration issue (fake migrations)"
echo "3. Reset all migrations (WARNING: Only for empty databases)"
echo "4. Apply all migrations normally"
echo "5. Check for migration conflicts"
echo ""
read -p "Enter your choice (1-5): " choice

case $choice in
    1)
        echo ""
        echo "Showing migration status..."
        run_django_command "showmigrations"
        ;;
    
    2)
        echo ""
        echo "Fixing CommonItems migration issue..."
        echo "This will mark the migrations as applied without running them."
        echo ""
        
        # First, try to fake up to migration 0002
        echo "Step 1: Faking migration up to 0002_initial..."
        run_django_command "migrate CommonItems 0002_initial --fake"
        
        # Then fake the problematic migration
        echo ""
        echo "Step 2: Faking the problematic migration 0003..."
        run_django_command "migrate CommonItems 0003_alter_commonitem_options_alter_itembrand_options_and_more --fake"
        
        # Finally, fake the last migration
        echo ""
        echo "Step 3: Faking migration 0004..."
        run_django_command "migrate CommonItems 0004_alter_vehiclesize_options_alter_vehicletype_options_and_more --fake"
        
        echo ""
        echo "CommonItems migrations have been marked as applied."
        echo "Now applying all other migrations..."
        run_django_command "migrate"
        ;;
    
    3)
        echo ""
        echo "WARNING: This will reset all migrations!"
        echo "Only use this if your database is empty or you don't care about the data."
        read -p "Are you sure? (yes/no): " confirm
        
        if [ "$confirm" = "yes" ]; then
            echo ""
            echo "Resetting all migrations..."
            
            # Get all app names
            apps=$(find apps -maxdepth 1 -type d -name "[!_]*" -exec basename {} \; | sort)
            
            for app in $apps; do
                echo "Resetting $app..."
                run_django_command "migrate $app zero --fake" 2>/dev/null || true
            done
            
            echo ""
            echo "All migrations reset. Now applying migrations with --fake-initial..."
            run_django_command "migrate --fake-initial"
        else
            echo "Operation cancelled."
        fi
        ;;
    
    4)
        echo ""
        echo "Applying all migrations normally..."
        run_django_command "migrate"
        ;;
    
    5)
        echo ""
        echo "Checking for migration conflicts..."
        run_django_command "makemigrations --check --dry-run"
        ;;
    
    *)
        echo "Invalid choice. Exiting."
        exit 1
        ;;
esac

echo ""
echo "Done! Check the output above for any errors."
echo ""
echo "If you still have issues:"
echo "1. Check that all apps are in INSTALLED_APPS in settings.py"
echo "2. Make sure all migration files are present"
echo "3. Consider deleting migration records from django_migrations table"
echo "4. As a last resort, delete all migration files (except __init__.py) and recreate them"