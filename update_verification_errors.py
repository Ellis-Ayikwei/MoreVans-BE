#!/usr/bin/env python3
"""
Script to update verification error responses in authentication views
"""

import re


def update_verification_errors():
    """Update verification error responses in views.py"""

    # Read the file
    with open("apps/Authentication/views.py", "r", encoding="utf-8") as f:
        content = f.read()

    # Pattern to match the old verification error response
    old_pattern = r'# Check if account requires further verification\s+if hasattr\(user, "requires_verification"\) and user\.requires_verification:\s+return Response\(\s+{\s+"detail": "Account requires verification\. Please check your email\."\s+},\s+status=status\.HTTP_403_FORBIDDEN,\s+\)'

    # New replacement
    new_replacement = """# Check if account requires further verification
            if hasattr(user, "requires_verification") and user.requires_verification:
                return get_verification_required_response(user)"""

    # Replace all occurrences
    updated_content = re.sub(
        old_pattern, new_replacement, content, flags=re.MULTILINE | re.DOTALL
    )

    # Also update the account locked response
    old_locked_pattern = r'# Check if account is locked due to too many failed attempts\s+if is_account_locked\(user\.email\):\s+return Response\(\s+{\s+"detail": "Account temporarily locked\. Try again later or reset your password\."\s+},\s+status=status\.HTTP_403_FORBIDDEN,\s+\)'

    new_locked_replacement = """# Check if account is locked due to too many failed attempts
            if is_account_locked(user.email):
                return get_account_locked_response(user.email)"""

    updated_content = re.sub(
        old_locked_pattern,
        new_locked_replacement,
        updated_content,
        flags=re.MULTILINE | re.DOTALL,
    )

    # Write back to file
    with open("apps/Authentication/views.py", "w", encoding="utf-8") as f:
        f.write(updated_content)

    print("✅ Updated verification error responses in views.py")


if __name__ == "__main__":
    update_verification_errors()
