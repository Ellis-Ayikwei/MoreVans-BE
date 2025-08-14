from django.db import models
from apps.Basemodel.models import Basemodel
from django.utils.translation import gettext_lazy as _


class Bid(Basemodel):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("accepted", "Accepted"),
        ("rejected", "Rejected"),
        ("expired", "Expired"),
    ]

    job = models.ForeignKey(
        "Job.Job", on_delete=models.CASCADE, related_name="bids", null=True, blank=True
    )
    provider = models.ForeignKey(
        "Provider.ServiceProvider", on_delete=models.CASCADE, null=True, blank=True
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    message = models.TextField(blank=True)
    counter_offer = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    estimated_completion_time = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = _("Bid")
        verbose_name_plural = _("Bids")
        ordering = ["-created_at"]
        managed = True

    def __str__(self):
        return f"Bid of {self.amount} for {self.job}"

    def accept(self):
        """Accept this bid"""
        if self.status == "pending":
            self.status = "accepted"
            self.save()
            self.job.accept_bid(self)
            return True
        return False

    def reject(self):
        """Reject this bid"""
        if self.status == "pending":
            self.status = "rejected"
            self.save()
            return True
        return False

    def make_counter_offer(self, amount):
        """Make a counter offer for this bid"""
        if self.status == "pending":
            self.counter_offer = amount
            self.save()
            return True
        return False
