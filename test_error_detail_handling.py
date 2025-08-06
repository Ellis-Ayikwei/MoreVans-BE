"""
Test script to demonstrate how ErrorDetail objects work with the new validation system
"""

from rest_framework import serializers
from rest_framework.exceptions import ErrorDetail

# This is what happens when you raise ValidationError like this:
def test_validation_error_structure():
    """
    Demonstrating the new ValidationError structure
    """
    
    # OLD WAY (broken):
    # raise ValidationError({"detail": "message", "code": "code"}, code="field")
    # Results in: [ErrorDetail("message", "code"), ErrorDetail("code", "code")]
    
    # NEW WAY (working):
    # raise ValidationError("message", code="code") 
    # Results in: [ErrorDetail("message", "code")]
    
    print("=== ErrorDetail Structure ===")
    
    # Simulate what our serializer now creates
    error = ErrorDetail("User account is disabled.", code="inactive_account")
    
    print(f"Error object: {error}")
    print(f"Error string: {str(error)}")
    print(f"Error code: {error.code}")
    print(f"Has code attribute: {hasattr(error, 'code')}")
    print(f"Is dict: {isinstance(error, dict)}")
    
    print("\n=== View Handling Logic ===")
    
    # This is how our view now handles it
    if hasattr(error, 'code'):
        error_code = error.code
        error_detail = str(error)
        print(f"✅ Successfully extracted - Code: {error_code}, Detail: {error_detail}")
    elif isinstance(error, dict):
        error_code = error.get("code")
        error_detail = error.get("detail", "Authentication failed")
        print(f"✅ Dict fallback - Code: {error_code}, Detail: {error_detail}")
    else:
        print("❌ Could not handle error type")

if __name__ == "__main__":
    test_validation_error_structure()