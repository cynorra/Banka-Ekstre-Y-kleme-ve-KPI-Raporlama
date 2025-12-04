from django.db import models
from django.contrib.auth.models import User
import hashlib

class Transaction(models.Model):
    TRANSACTION_TYPES = (
        ('credit', 'Gelir'),
        ('debit', 'Gider'),
    )

    user = models.ForeignKey(User, on_delete = models.CASCADE, related_name = 'transactions')
    date = models.DateField()
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    currency = models.CharField(max_length=3, default='TRY')
    description = models.CharField(max_length=255)
    category = models.CharField(max_length=100, blank=True, null=True)
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)

    # Duplicate önleme
    unique_hash = models.CharField(max_length=64, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # tekli kayıt yapılırsa hash oluşturulsun
        if not self.unique_hash:
            raw_string = f"{self.user.id}{self.date}{self.amount}{self.description}"
            self.unique_hash = hashlib.sha256(raw_string.encode('utf-8')).hexdigest()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} - {self.description} ({self.amount})"
    