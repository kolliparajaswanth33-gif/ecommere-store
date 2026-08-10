import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):

    help = "Create or reset the owner admin account"

    def handle(self, *args, **options):

        username = os.environ.get(
            "DJANGO_ADMIN_USERNAME"
        )

        password = os.environ.get(
            "DJANGO_ADMIN_PASSWORD"
        )

        email = os.environ.get(
            "DJANGO_ADMIN_EMAIL",
            "",
        )

        if not username or not password:

            self.stdout.write(
                self.style.WARNING(
                    "Admin credentials are not configured."
                )
            )

            return

        User = get_user_model()

        user, created = User.objects.get_or_create(
            username=username
        )

        user.email = email

        user.is_staff = True

        user.is_superuser = True

        user.is_active = True

        user.set_password(password)

        user.save()

        if created:

            self.stdout.write(
                self.style.SUCCESS(
                    f"Admin '{username}' created successfully."
                )
            )

        else:

            self.stdout.write(
                self.style.SUCCESS(
                    f"Admin '{username}' password reset successfully."
                )
            )