from django.db import models, JSONField

class InsuranceProfile(models.Model):
    COVERAGE_LEVELS = [
        ('basic', 'Basic Coverage'),
        ('standard', 'Standard Coverage'),
        ('comprehensive', 'Comprehensive Coverage'),
        ('premium', 'Premium Coverage')
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    
    # Insurance Details
    coverage_level = models.CharField(max_length=20, choices=COVERAGE_LEVELS, default='basic')
    max_coverage_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Policy Details
    policy_number = models.CharField(max_length=50, unique=True)
    insurance_provider = models.CharField(max_length=100)
    
    # Validity
    valid_from = models.DateField()
    valid_until = models.DateField()
    
    # Additional Coverage Options
    additional_coverages = JSONField(null=True, help_text="Additional insurance options")
    
    def __str__(self):
        return f"Insurance Profile for {self.user}"