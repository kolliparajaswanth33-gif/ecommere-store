from datetime import date

from django.contrib.auth import get_user_model
from django.contrib.staticfiles import finders
from django.db import IntegrityError
from django.db import transaction
from django.test import TestCase
from django.urls import reverse

from .models import EmployeeProfile


User = get_user_model()


def create_profile(username, role, *, superuser=False):
    user = User.objects.create_user(
        username=username,
        email=f"{username}@example.com",
        password="A-secure-test-password-123!",
        is_superuser=superuser,
        is_staff=superuser,
    )
    return EmployeeProfile.objects.create(
        user=user,
        employee_id=f"EMP-{username}",
        full_name=username.title(),
        phone="9876543210",
        date_of_birth=date(1990, 1, 1),
        gender=EmployeeProfile.Gender.OTHER,
        address="Test address",
        joining_date=date(2026, 1, 1),
        department="Operations",
        designation="Test role",
        role=role,
        emergency_contact="Test contact",
        emergency_phone="9876543211",
    )


class EmployeeManagementTests(TestCase):
    def test_password_toggle_is_available_on_all_password_surfaces(self):
        asset_path = finders.find("store/js/password-toggle.js")
        self.assertIsNotNone(asset_path)
        with open(asset_path, encoding="utf-8") as asset:
            script = asset.read()
        self.assertIn('input[type="password"]', script)
        self.assertIn('input.type = isHidden ? "text" : "password"', script)
        self.assertIn("MutationObserver", script)

        self.assertContains(self.client.get(reverse("store:login")), "password-toggle.js")
        self.assertContains(self.client.get(reverse("store:register")), "password-toggle.js")
        self.assertContains(self.client.get(reverse("management:login")), "password-toggle.js")

        owner = create_profile("password-owner", EmployeeProfile.Role.OWNER, superuser=True)
        self.client.force_login(owner.user)
        self.assertContains(self.client.get(reverse("management:add_employee")), "password-toggle.js")
        self.assertContains(self.client.get(reverse("admin:password_change")), "password-toggle.js")

    def test_database_allows_only_one_manager(self):
        create_profile("manager-one", EmployeeProfile.Role.MANAGER)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                create_profile("manager-two", EmployeeProfile.Role.MANAGER)

    def test_owner_can_create_manager_with_hashed_password(self):
        owner = create_profile("owner", EmployeeProfile.Role.OWNER, superuser=True)
        self.client.force_login(owner.user)
        response = self.client.post(reverse("management:add_employee"), {
            "full_name": "First Manager", "employee_id": "EMP-MANAGER",
            "username": "first-manager", "email": "manager@example.com",
            "phone": "9876543210", "date_of_birth": "1990-01-01", "gender": "other",
            "address": "Office", "joining_date": "2026-01-01", "department": "Sales",
            "designation": "Manager", "role": "manager", "temporary_password": "A-secure-password-123!",
            "emergency_contact": "Contact", "emergency_phone": "9876543211", "is_employed": "on",
        })
        self.assertRedirects(response, reverse("management:employees"))
        manager = EmployeeProfile.objects.get(employee_id="EMP-MANAGER")
        self.assertTrue(manager.user.check_password("A-secure-password-123!"))
        self.assertNotEqual(manager.user.password, "A-secure-password-123!")

    def test_manager_cannot_view_or_edit_manager_account(self):
        owner = create_profile("owner", EmployeeProfile.Role.OWNER, superuser=True)
        manager = create_profile("manager", EmployeeProfile.Role.MANAGER)
        self.client.force_login(manager.user)
        response = self.client.get(reverse("management:employees"))
        self.assertNotContains(response, owner.full_name)
        response = self.client.get(reverse("management:edit_employee", args=[manager.id]))
        self.assertRedirects(response, reverse("management:employees"))

    def test_staff_cannot_manage_employees(self):
        staff = create_profile("staff", EmployeeProfile.Role.STAFF)
        self.client.force_login(staff.user)
        response = self.client.get(reverse("management:employees"))
        self.assertRedirects(response, reverse("management:dashboard"), fetch_redirect_response=False)
