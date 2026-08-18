from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q


class EmployeeProfile(models.Model):
    """Employment and role details for a management account."""

    class Role(models.TextChoices):
        OWNER = "owner", "Owner"
        MANAGER = "manager", "Manager"
        STAFF = "staff", "Staff"

    class Gender(models.TextChoices):
        MALE = "male", "Male"
        FEMALE = "female", "Female"
        OTHER = "other", "Other"
        PREFER_NOT_TO_SAY = "prefer_not_to_say", "Prefer not to say"

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="employee_profile")
    employee_id = models.CharField(max_length=40, unique=True)
    full_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=30)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=20, choices=Gender.choices)
    address = models.TextField()
    joining_date = models.DateField()
    department = models.CharField(max_length=100)
    designation = models.CharField(max_length=100)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.STAFF)
    profile_photo = models.ImageField(upload_to="employees/", blank=True, null=True)
    emergency_contact = models.CharField(max_length=150)
    emergency_phone = models.CharField(max_length=30)
    is_employed = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["full_name", "employee_id"]
        constraints = [
            # This protects the rule even if records are created outside the UI.
            models.UniqueConstraint(fields=["role"], condition=Q(role="manager"), name="management_exactly_one_manager"),
        ]

    def clean(self):
        super().clean()
        # A ModelForm assigns the new user after validating this profile.
        if not self.user_id:
            return
        if self.role == self.Role.OWNER and not self.user.is_superuser:
            raise ValidationError({"role": "Only a Django superuser can be an Owner."})
        if self.role != self.Role.OWNER and self.user.is_superuser:
            raise ValidationError({"role": "A superuser account must use the Owner role."})

    def save(self, *args, **kwargs):
        # Employee accounts must be able to authenticate, but do not make them superusers.
        self.clean()
        self.user.is_staff = True
        self.user.is_active = self.is_employed
        self.user.save(update_fields=["is_staff", "is_active"])
        super().save(*args, **kwargs)

    @property
    def is_owner(self):
        return self.role == self.Role.OWNER

    @property
    def is_manager(self):
        return self.role == self.Role.MANAGER

    def __str__(self):
        return f"{self.full_name} ({self.employee_id})"
