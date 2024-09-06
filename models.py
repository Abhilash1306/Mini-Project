from django.db import models
from django.contrib.auth.models import User

class BusPass(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Accepted', 'Accepted'),
        ('Rejected', 'Rejected')
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100)
    pass_id = models.CharField(max_length=20, unique=True)
    user_class = models.CharField(max_length=50)
    college = models.CharField(max_length=100)
    from_place = models.CharField(max_length=100)
    to_place = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    payment = models.OneToOneField('Payment', on_delete=models.CASCADE, null=True, blank=True)

class Payment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    transaction_id = models.CharField(max_length=100)
    upi_id = models.CharField(max_length=100)
    payment_date = models.DateTimeField(auto_now_add=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)  # Added default value
