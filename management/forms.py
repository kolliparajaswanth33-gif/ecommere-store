from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

from store.models import Product, Coupon, PaymentSettings
from .models import EmployeeProfile


User = get_user_model()


class EmployeeForm(forms.ModelForm):
    """Creates or updates the employee profile and its login account together."""

    username = forms.CharField(max_length=150)
    email = forms.EmailField()
    temporary_password = forms.CharField(
        label="Temporary password",
        widget=forms.PasswordInput(render_value=False),
        required=True,
        help_text="The employee should change this after their first login.",
    )

    class Meta:
        model = EmployeeProfile
        fields = [
            "full_name", "employee_id", "username", "email", "phone", "date_of_birth",
            "gender", "address", "joining_date", "department", "designation", "role",
            "temporary_password", "profile_photo", "emergency_contact", "emergency_phone",
            "is_employed",
        ]
        widgets = {
            "date_of_birth": forms.DateInput(attrs={"type": "date"}),
            "joining_date": forms.DateInput(attrs={"type": "date"}),
            "address": forms.Textarea(attrs={"rows": 3}),
            "profile_photo": forms.ClearableFileInput(attrs={"accept": "image/*"}),
        }

    def __init__(self, *args, actor, **kwargs):
        self.actor = actor
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields["username"].initial = self.instance.user.username
            self.fields["email"].initial = self.instance.user.email
            self.fields["temporary_password"].required = False
            self.fields["temporary_password"].help_text = "Leave blank to keep the current password."
        if not self.actor.is_superuser:
            self.fields["role"].choices = [(EmployeeProfile.Role.STAFF, "Staff")]
        elif self.instance.pk and self.instance.role == EmployeeProfile.Role.OWNER:
            self.fields["role"].disabled = True

    def clean_username(self):
        username = self.cleaned_data["username"].strip()
        users = User.objects.filter(username__iexact=username)
        if self.instance.pk:
            users = users.exclude(pk=self.instance.user_id)
        if users.exists():
            raise forms.ValidationError("This username is already in use.")
        return username

    def clean_email(self):
        email = self.cleaned_data["email"].strip()
        users = User.objects.filter(email__iexact=email)
        if self.instance.pk:
            users = users.exclude(pk=self.instance.user_id)
        if users.exists():
            raise forms.ValidationError("This email address is already in use.")
        return email

    def clean_temporary_password(self):
        password = self.cleaned_data.get("temporary_password")
        if password:
            candidate = User(username=self.cleaned_data.get("username", ""), email=self.cleaned_data.get("email", ""))
            validate_password(password, candidate)
        return password

    def clean_role(self):
        role = self.cleaned_data["role"]
        if not self.actor.is_superuser and role != EmployeeProfile.Role.STAFF:
            raise forms.ValidationError("Managers can only create and manage Staff accounts.")
        if role == EmployeeProfile.Role.OWNER:
            raise forms.ValidationError("Owner accounts are created through Django administration only.")
        if role == EmployeeProfile.Role.MANAGER and not self.instance.pk and EmployeeProfile.objects.filter(role=role).exists():
            raise forms.ValidationError("Only one Manager can exist.")
        return role

    def save(self, commit=True):
        profile = super().save(commit=False)
        if profile.pk:
            user = profile.user
        else:
            user = User()
        user.username = self.cleaned_data["username"]
        user.email = self.cleaned_data["email"]
        password = self.cleaned_data.get("temporary_password")
        if password:
            user.set_password(password)
        if commit:
            user.save()
            profile.user = user
            profile.save()
            self.save_m2m()
        return profile


# ============================================================
# PRODUCT FORM
# ============================================================

class ProductForm(forms.ModelForm):

    class Meta:
        model = Product

        fields = [
            "name",
            "description",
            "price",
            "stock",
            "image",
            "image_url",
        ]

        widgets = {

            "name": forms.TextInput(
                attrs={
                    "placeholder": "Enter product name"
                }
            ),

            "description": forms.Textarea(
                attrs={
                    "placeholder": "Enter product description",
                    "rows": 4
                }
            ),

            "price": forms.NumberInput(
                attrs={
                    "placeholder": "Enter price",
                    "step": "0.01",
                    "min": "0"
                }
            ),

            "stock": forms.NumberInput(
                attrs={
                    "placeholder": "Enter stock quantity",
                    "min": "0"
                }
            ),

            "image": forms.ClearableFileInput(
                attrs={
                    "accept": "image/*"
                }
            ),

            "image_url": forms.URLInput(
                attrs={
                    "placeholder": "https://example.com/image.jpg"
                }
            ),
        }

    def clean(self):

        cleaned_data = super().clean()

        image = cleaned_data.get("image")
        image_url = cleaned_data.get("image_url")

        # New product
        if not self.instance.pk:

            if not image and not image_url:

                raise forms.ValidationError(
                    "Please upload an image OR enter an image URL."
                )

            if image and image_url:

                raise forms.ValidationError(
                    "Please use either an uploaded image OR "
                    "an image URL, not both."
                )

        # Existing product
        else:

            if image and image_url:

                raise forms.ValidationError(
                    "Please use either an uploaded image OR "
                    "an image URL, not both."
                )

        return cleaned_data


# ============================================================
# COUPON FORM
# ============================================================

class CouponForm(forms.ModelForm):

    class Meta:

        model = Coupon

        fields = [
            "code",
            "discount_type",
            "discount_value",
            "minimum_order_amount",
            "max_uses",
            "start_date",
            "end_date",
            "is_active",
        ]

        widgets = {

            "code": forms.TextInput(
                attrs={
                    "placeholder": "Example: SAVE100",
                }
            ),

            "discount_type": forms.Select(),

            "discount_value": forms.NumberInput(
                attrs={
                    "placeholder": "Enter discount value",
                    "step": "0.01",
                    "min": "0"
                }
            ),

            "minimum_order_amount": forms.NumberInput(
                attrs={
                    "placeholder": "Example: 500",
                    "step": "0.01",
                    "min": "0"
                }
            ),

            "max_uses": forms.NumberInput(
                attrs={
                    "placeholder": "0 = Unlimited",
                    "min": "0"
                }
            ),

            "start_date": forms.DateInput(
                attrs={
                    "type": "date"
                }
            ),

            "end_date": forms.DateInput(
                attrs={
                    "type": "date"
                }
            ),

            "is_active": forms.CheckboxInput(),
        }

    # --------------------------------------------------------
    # COUPON CODE
    # --------------------------------------------------------

    def clean_code(self):

        code = self.cleaned_data.get("code")

        if not code:

            raise forms.ValidationError(
                "Coupon code is required."
            )

        return code.strip().upper()

    # --------------------------------------------------------
    # COUPON VALIDATION
    # --------------------------------------------------------

    def clean(self):

        cleaned_data = super().clean()

        discount_type = cleaned_data.get(
            "discount_type"
        )

        discount_value = cleaned_data.get(
            "discount_value"
        )

        minimum_order_amount = cleaned_data.get(
            "minimum_order_amount"
        )

        max_uses = cleaned_data.get(
            "max_uses"
        )

        start_date = cleaned_data.get(
            "start_date"
        )

        end_date = cleaned_data.get(
            "end_date"
        )

        # Discount value
        if discount_value is not None:

            if discount_value <= 0:

                raise forms.ValidationError(
                    "Discount value must be greater than 0."
                )

        # Percentage discount
        if (
            discount_type == "percentage"
            and discount_value is not None
        ):

            if discount_value > 100:

                raise forms.ValidationError(
                    "Percentage discount cannot be greater than 100%."
                )

        # Minimum order amount
        if minimum_order_amount is not None:

            if minimum_order_amount < 0:

                raise forms.ValidationError(
                    "Minimum order amount cannot be negative."
                )

        # Maximum uses
        if max_uses is not None:

            if max_uses < 0:

                raise forms.ValidationError(
                    "Maximum uses cannot be negative."
                )

        # Date validation
        if start_date and end_date:

            if end_date < start_date:

                raise forms.ValidationError(
                    "End date cannot be before start date."
                )

        return cleaned_data


# ============================================================
# PAYMENT SETTINGS FORM
# ============================================================

class PaymentSettingsForm(forms.ModelForm):

    class Meta:

        model = PaymentSettings

        fields = [
            "upi_id",
            "qr_code",
            "upi_enabled",
            "cod_enabled",
            "payment_instructions",
        ]

        widgets = {

            "upi_id": forms.TextInput(
                attrs={
                    "placeholder": "example@upi"
                }
            ),

            "qr_code": forms.ClearableFileInput(
                attrs={
                    "accept": "image/*"
                }
            ),

            "upi_enabled": forms.CheckboxInput(),

            "cod_enabled": forms.CheckboxInput(),

            "payment_instructions": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": (
                        "Enter payment instructions..."
                    )
                }
            ),
        }
