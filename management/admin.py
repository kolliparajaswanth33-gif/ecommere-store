from django.contrib import admin
from .models import EmployeeProfile


@admin.register(EmployeeProfile)
class EmployeeProfileAdmin(admin.ModelAdmin):
    list_display = ("full_name", "employee_id", "role", "department", "is_employed")
    list_filter = ("role", "is_employed", "department")
    search_fields = ("full_name", "employee_id", "user__username", "user__email")
    readonly_fields = ("created_at", "updated_at")
