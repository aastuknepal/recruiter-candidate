from django.db import transaction
from rest_framework import serializers
from apps.setup.models import (
    Configuration,
)
from common_utils.serializers.base_serializer import DynamicFieldsModelSerializer


class ConfigurationSerializer(DynamicFieldsModelSerializer):
    actions = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Configuration
        fields = [
            "id",
            "name",
            "display_name",
            "description",
            "config_type",
            "value",
            "actions",
        ]

    def get_actions(self, obj):
        request = self.context.get("request", None)
        if not request or not request.user.is_authenticated:
            return []
        user = request.user
        actions = []

        # Edit action
        if user.is_superuser or user.has_explicit_perm("setup.edit.configurations"):
            actions.append({"name": "Edit", "emit": "onEdit", "class": ""})
        return actions
