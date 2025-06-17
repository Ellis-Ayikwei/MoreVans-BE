from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

from apps.Contract.models import ContractAgreement


class ServiceReview(models.Model):
    contract = models.OneToOneField(ContractAgreement, on_delete=models.CASCADE)

    # Ratings
    overall_rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        validators=[MinValueValidator(1.0), MaxValueValidator(5.0)],
    )

    # Detailed Ratings
    punctuality_rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        validators=[MinValueValidator(1.0), MaxValueValidator(5.0)],
    )
    service_quality_rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        validators=[MinValueValidator(1.0), MaxValueValidator(5.0)],
    )

    # Review Details
    review_text = models.TextField(null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)

    objects: models.Manager = models.Manager()

    class Meta:
        db_table = "service_review"
        managed = True
