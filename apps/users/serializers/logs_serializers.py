from django.db import transaction
from rest_framework import serializers
from apps.users.models import User, ChangeLog, ErrorLog, ActivityLog
from common_utils.serializers.base_serializer import DynamicFieldsModelSerializer


class ChangeLogSerializer(DynamicFieldsModelSerializer):
    user = serializers.CharField(source="user.full_name", read_only=True)
    changes = serializers.SerializerMethodField()
    timestamp = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    actions = serializers.SerializerMethodField()
    sql_action = serializers.CharField(read_only=True, source="action")

    class Meta:
        model = ChangeLog
        fields = [
            "id",
            "user",
            "model_name",
            "object_id",
            "sql_action",
            "changes",
            "timestamp",
            "actions",
        ]

    def get_changes(self, obj):
        # skip the harde deleted objects
        if obj.action == "delete":
            return "Deleted object."
        
        data = obj.changed_fields
        if not data or not isinstance(data, dict):
            return f"{obj.action} operation performed."

        lines = []
        for field, values in data.items():
            name = field.replace("_", " ").title()
            old = values.get("old") if values.get("old") is not None else "None"
            new = values.get("new") if values.get("new") is not None else "None"
            lines.append(f"{name}: {old} to {new}")
        return " | ".join(lines)

    def get_actions(self, obj):
        actions = []
        actions.append({"name": "View", "emit": "onView", "class": ""})
        return actions

class ErrorLogSerializer(DynamicFieldsModelSerializer):
    user = serializers.CharField(source="user.full_name", read_only=True)
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    actions = serializers.SerializerMethodField()
    class Meta:
        model = ErrorLog
        fields = [
            "id",
            "user",
            "model_name",
            "error_message",
            "path",
            "method",
            "view_name",
            "created_at",
            "actions"
        ]

    def get_actions(self, obj):
        actions = []
        actions.append({"name": "View", "emit": "onView", "class": ""})
        return actions

class ActivityLogSerializer(DynamicFieldsModelSerializer):
    user = serializers.CharField(source="user.full_name", read_only=True)
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    class Meta:
        model = ActivityLog
        fields = [
            "id",
            "user",
            "email_or_username",
            "activity_type",
            "ip_address",
            "user_agent",
            "path",
            "http_method",
            "is_successful",
            "failure_reason",
            "created_at",
        ]

