from django.db import models

# Create your models here.
DISCOUNT_TYPES = [
    ("flat", "Flat Discount"),
    ("percentage", "Percentage Discount"),
]
discount_type = models.CharField(
    max_length=20,
    choices=DISCOUNT_TYPES,
)