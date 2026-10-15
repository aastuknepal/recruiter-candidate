from django.contrib import admin
from django.contrib.auth.models import Group
from .models import User, Roles, Permissions, ActivityLog, ErrorLog, ChangeLog

# Unregister standard Group model to completely remove it from Site Administration
try:
    admin.site.unregister(Group)
except admin.sites.NotRegistered:
    pass

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_superuser', 'is_active')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    list_filter = ('is_staff', 'is_superuser', 'is_active')
    filter_horizontal = ('roles',)

@admin.register(Roles)
class RolesAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'is_active')
    search_fields = ('name', 'description')
    list_filter = ('is_active',)
    filter_horizontal = ('permissions',)

@admin.register(Permissions)
class PermissionsAdmin(admin.ModelAdmin):
    list_display = ('name', 'key', 'module')
    search_fields = ('name', 'key', 'module')
    list_filter = ('module',)

@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'email_or_username', 'activity_type', 'ip_address', 'is_successful', 'created_at')
    list_filter = ('activity_type', 'is_successful', 'created_at')
    search_fields = ('email_or_username', 'activity_type', 'ip_address', 'failure_reason')

@admin.register(ErrorLog)
class ErrorLogAdmin(admin.ModelAdmin):
    list_display = ('error_message', 'model_name', 'user', 'path', 'method', 'created_at')
    list_filter = ('model_name', 'method', 'created_at')
    search_fields = ('error_message', 'path', 'view_name')

@admin.register(ChangeLog)
class ChangeLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'model_name', 'object_id', 'action', 'timestamp')
    list_filter = ('action', 'model_name', 'timestamp')
    search_fields = ('model_name', 'object_id')
