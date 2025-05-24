from django.db import models

class Dispute(models.Model):
    """Handle disputes and claims"""
    DISPUTE_TYPES = [
        ('damage', 'Damage Claim'),
        ('delay', 'Delay Complaint'),
        ('service', 'Service Quality'),
        ('pricing', 'Pricing Dispute'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('investigating', 'Under Investigation'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]
    
    request = models.ForeignKey(Request, on_delete=models.CASCADE)
    raised_by = models.ForeignKey(User, on_delete=models.CASCADE)
    dispute_type = models.CharField(max_length=20, choices=DISPUTE_TYPES)
    description = models.TextField()
    evidence = models.JSONField(null=True)  # URLs to evidence files
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True)
    resolution_notes = models.TextField(blank=True)
    compensation_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    
    def __str__(self):
        return f"Dispute #{self.id} - {self.dispute_type}"
