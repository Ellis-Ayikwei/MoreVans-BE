from django.db import models

from apps.Basemodel.models import Basemodel
from apps.Bidding.models import Bid
from apps.Request.models import Request


class ContractAgreement(Basemodel):
    AGREEMENT_STATUS = [
        ("draft", "Draft"),
        ("pending", "Pending Signatures"),
        ("active", "Active"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]

    # Core Agreement Details
    logistics_request = models.OneToOneField(Request, on_delete=models.CASCADE)
    selected_bid = models.OneToOneField(Bid, on_delete=models.CASCADE)

    # Contract Terms
    insurance_coverage = models.DecimalField(
        max_digits=10, decimal_places=2, help_text="Insurance value"
    )
    cancellation_policy = models.JSONField(help_text="Cancellation and refund terms")

    # Signatures and Verification
    customer_signed = models.BooleanField(default=False)
    provider_signed = models.BooleanField(default=False)

    # Status Tracking
    status = models.CharField(max_length=20, choices=AGREEMENT_STATUS, default="draft")

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    agreement_start_date = models.DateTimeField(null=True)
    agreement_end_date = models.DateTimeField(null=True)

    objects: models.Manager = models.Manager()

    class Meta:
        db_table = "contract_agreement"
        managed = True
