from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Address


# ============================================================
# REGISTER FORM
# ============================================================

class RegisterForm(UserCreationForm):

    email = forms.EmailField(
        required=True,
        label="Email address",
        widget=forms.EmailInput(
            attrs={
                "placeholder": "Enter your email",
                "autocomplete": "email",
                "class": "form-control",
            }
        ),
    )

    class Meta:

        model = User

        fields = (
            "username",
            "email",
            "password1",
            "password2",
        )

        widgets = {

            "username": forms.TextInput(
                attrs={
                    "placeholder": "Enter username",
                    "autocomplete": "username",
                    "class": "form-control",
                }
            ),

        }


# ============================================================
# ADDRESS FORM
# ============================================================

class AddressForm(forms.ModelForm):

    class Meta:

        model = Address

        fields = [
            "full_name",
            "phone",
            "house_no",
            "street",
            "landmark",
            "city",
            "district",
            "state",
            "pincode",
            "is_default",
        ]

        widgets = {

            "full_name": forms.TextInput(
                attrs={
                    "placeholder": "Full name",
                    "class": "form-control",
                }
            ),

            "phone": forms.TextInput(
                attrs={
                    "placeholder": "10-digit mobile number",
                    "class": "form-control",
                    "inputmode": "numeric",
                    "maxlength": "10",
                }
            ),

            "house_no": forms.TextInput(
                attrs={
                    "placeholder": "House / Door number",
                    "class": "form-control",
                }
            ),

            "street": forms.TextInput(
                attrs={
                    "placeholder": "Street / Area",
                    "class": "form-control",
                }
            ),

            "landmark": forms.TextInput(
                attrs={
                    "placeholder": "Nearby landmark (optional)",
                    "class": "form-control",
                }
            ),

            "city": forms.TextInput(
                attrs={
                    "placeholder": "Village / City",
                    "class": "form-control",
                }
            ),

            "district": forms.TextInput(
                attrs={
                    "placeholder": "District",
                    "class": "form-control",
                }
            ),

            "state": forms.TextInput(
                attrs={
                    "placeholder": "State",
                    "class": "form-control",
                }
            ),

            "pincode": forms.TextInput(
                attrs={
                    "placeholder": "6-digit PIN code",
                    "class": "form-control",
                    "inputmode": "numeric",
                    "maxlength": "6",
                }
            ),

            "is_default": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                }
            ),
        }

    # --------------------------------------------------------
    # PHONE VALIDATION
    # --------------------------------------------------------

    def clean_phone(self):

        phone = self.cleaned_data.get(
            "phone",
            ""
        ).strip()

        if not phone.isdigit():

            raise forms.ValidationError(
                "Mobile number must contain numbers only."
            )

        if len(phone) != 10:

            raise forms.ValidationError(
                "Please enter a valid 10-digit mobile number."
            )

        return phone

    # --------------------------------------------------------
    # PINCODE VALIDATION
    # --------------------------------------------------------

    def clean_pincode(self):

        pincode = self.cleaned_data.get(
            "pincode",
            ""
        ).strip()

        if not pincode.isdigit():

            raise forms.ValidationError(
                "PIN code must contain numbers only."
            )

        if len(pincode) != 6:

            raise forms.ValidationError(
                "Please enter a valid 6-digit PIN code."
            )

        return pincode


# ============================================================
# CHECKOUT ADDRESS FORM
# ============================================================

class CheckoutAddressForm(forms.ModelForm):

    class Meta:

        model = Address

        fields = [
            "full_name",
            "phone",
            "house_no",
            "street",
            "landmark",
            "city",
            "district",
            "state",
            "pincode",
        ]

        widgets = {

            "full_name": forms.TextInput(
                attrs={
                    "placeholder": "Full name",
                    "class": "form-control",
                }
            ),

            "phone": forms.TextInput(
                attrs={
                    "placeholder": "10-digit mobile number",
                    "class": "form-control",
                    "inputmode": "numeric",
                    "maxlength": "10",
                }
            ),

            "house_no": forms.TextInput(
                attrs={
                    "placeholder": "House / Door number",
                    "class": "form-control",
                }
            ),

            "street": forms.TextInput(
                attrs={
                    "placeholder": "Street / Area",
                    "class": "form-control",
                }
            ),

            "landmark": forms.TextInput(
                attrs={
                    "placeholder": "Nearby landmark (optional)",
                    "class": "form-control",
                }
            ),

            "city": forms.TextInput(
                attrs={
                    "placeholder": "Village / City",
                    "class": "form-control",
                }
            ),

            "district": forms.TextInput(
                attrs={
                    "placeholder": "District",
                    "class": "form-control",
                }
            ),

            "state": forms.TextInput(
                attrs={
                    "placeholder": "State",
                    "class": "form-control",
                }
            ),

            "pincode": forms.TextInput(
                attrs={
                    "placeholder": "6-digit PIN code",
                    "class": "form-control",
                    "inputmode": "numeric",
                    "maxlength": "6",
                }
            ),
        }

    # --------------------------------------------------------
    # PHONE VALIDATION
    # --------------------------------------------------------

    def clean_phone(self):

        phone = self.cleaned_data.get(
            "phone",
            ""
        ).strip()

        if not phone.isdigit():

            raise forms.ValidationError(
                "Mobile number must contain numbers only."
            )

        if len(phone) != 10:

            raise forms.ValidationError(
                "Please enter a valid 10-digit mobile number."
            )

        return phone

    # --------------------------------------------------------
    # PINCODE VALIDATION
    # --------------------------------------------------------

    def clean_pincode(self):

        pincode = self.cleaned_data.get(
            "pincode",
            ""
        ).strip()

        if not pincode.isdigit():

            raise forms.ValidationError(
                "PIN code must contain numbers only."
            )

        if len(pincode) != 6:

            raise forms.ValidationError(
                "Please enter a valid 6-digit PIN code."
            )

        return pincode