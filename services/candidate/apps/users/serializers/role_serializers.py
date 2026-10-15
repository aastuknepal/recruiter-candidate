from rest_framework import serializers
from apps.users.models import Roles, Permissions
from apps.users.serializers.permission_serializers import PermissionSerializer


class PermissionLinkSerializer(serializers.Serializer):
    """
    Accepts only the `id` from the incoming permission objects.
    All other fields (key, name, module, etc.) are silently ignored.
    """
    id = serializers.PrimaryKeyRelatedField(queryset=Permissions.objects.all())


class RoleSerializer(serializers.ModelSerializer):
    permissions_ids = PermissionLinkSerializer(
        many=True, write_only=True, required=False)

    permissions = PermissionSerializer(
        many=True, read_only=True
    )

    class Meta:
        model = Roles
        fields = ["id", "name", "description",
                  "permissions_ids", "permissions", "is_active"]

    def to_internal_value(self, data):
        data = data.copy()
        if "permissions" in data and "permissions_ids" not in data:
            data["permissions_ids"] = data.pop("permissions")
        return super().to_internal_value(data)

    def _extract_permissions(self, permissions_data):
        """Resolve list of {'id': <Permissions instance>} → queryset-able list."""
        return [item["id"] for item in permissions_data]

    def create(self, validated_data):
        permissions_data = validated_data.pop("permissions_ids", [])
        role = Roles.objects.create(**validated_data)
        role.permissions.set(self._extract_permissions(permissions_data))
        return role

    def update(self, instance, validated_data):
        permissions_data = validated_data.pop("permissions_ids", None)
        instance = super().update(instance, validated_data)
        if permissions_data is not None:
            instance.permissions.set(
                self._extract_permissions(permissions_data))
        return instance
