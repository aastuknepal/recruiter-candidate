from rest_framework import serializers
from apps.users.models import Permissions


class PermissionSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = Permissions
        fields = ("id", "name", "key", "module", "description")
