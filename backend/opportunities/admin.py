from django.contrib import admin

from .models import Department, Opportunity


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'code')
    search_fields = ('name', 'code')


@admin.register(Opportunity)
class OpportunityAdmin(admin.ModelAdmin):
    list_display = ('title', 'faculty_name', 'department', 'status', 'application_deadline')
    list_filter = ('status', 'department', 'research_area')
    search_fields = ('title', 'research_area', 'faculty_name', 'department')
