from django import forms

from store.models import Product, Coupon, PaymentSettings


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