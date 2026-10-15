from attr import attrs
from django.db import transaction
from rest_framework import serializers
from apps.users.models import User, Roles, Permissions
from common_utils.serializers.base_serializer import DynamicFieldsModelSerializer
from common_utils.validators.regex import name_validator, phone_validator, username_validator, password_validator
from .role_serializers import RoleSerializer


class UserSerializer(DynamicFieldsModelSerializer):
    role_ids = serializers.PrimaryKeyRelatedField(
        queryset=Roles.objects.all(),
        write_only=True,
        required=False,
        many=True,
    )
    role = RoleSerializer(many=True, read_only=True, source="roles")
    confirm_password = serializers.CharField(write_only=True, required=False)
    actions = serializers.SerializerMethodField(read_only=True)
    first_name = serializers.CharField(
        max_length=50,
        validators=[name_validator]
    )
    middle_name = serializers.CharField(
        max_length=50,
        required=False,
        allow_blank=True,
        allow_null=True,
        validators=[name_validator]
    )
    created_by = serializers.SerializerMethodField(read_only=True)
    last_name = serializers.CharField(
        max_length=50,
        validators=[name_validator]
    )
    phone = serializers.CharField(
        max_length=15,
        validators=[phone_validator]
    )
    username = serializers.CharField(
        max_length=50,
        validators=[username_validator]
    )
    current_password = serializers.CharField(
        write_only=True, required=False, allow_blank=True)
    new_password = serializers.CharField(
        write_only=True, required=False, allow_blank=True)

    password = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        validators=[password_validator]
    )

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "first_name",
            "middle_name",
            "last_name",
            "full_name",
            "phone",
            "email",
            "password",
            "confirm_password",
            "current_password",
            "new_password",
            "role",
            "role_ids",
            "actions",
            "is_deleted",
            "is_active",
            "created_by",

        )
        extra_kwargs = {
            "email": {"required": True},
            "first_name": {"required": True},
            "last_name": {"required": True},
            "is_deleted": {"read_only": True},
            "is_active": {"read_only": True},
        }

    def to_internal_value(self, data):
        if hasattr(data, 'copy'):
            data = data.copy()

        role_data = data.get("role") or data.get("role_id")
        if role_data:
            if isinstance(role_data, list):
                data["role_ids"] = [r.get("id") if isinstance(
                    r, dict) else r for r in role_data]
            elif isinstance(role_data, dict):
                data["role_ids"] = [role_data.get("id")]
            else:
                data["role_ids"] = [role_data]
        elif "role" in data or "role_id" in data or "role_ids" in data:
            data["role_ids"] = []
        return super().to_internal_value(data)

    def get_actions(self, obj) -> list[dict]:
        request = self.context.get("request", None)
        if not request or not request.user.is_authenticated:
            return []

        user = request.user
        actions = []

        if user.has_perm("users.edit"):
            actions.append({"name": "Edit", "emit": "onEdit", "class": ""})

        if user.has_perm("users.activate_deactivate"):
            if obj.is_active:
                actions.append(
                    {"name": "Deactivate", "emit": "onDeactivate", "class": "text-red-500"}
                )
            else:
                actions.append(
                    {"name": "Activate", "emit": "onActivate", "class": "text-green-500"}
                )

        return actions

    def get_created_by(self, obj):
        return obj.created_by.username if obj.created_by else None

    def validate(self, attrs):
        request = self.context.get("request")
        user = request.user if request else None
        instance = getattr(self, "instance", None)

        password = attrs.get("password")
        current_password = attrs.get("current_password")
        new_password = attrs.get("new_password")
        confirm_password = attrs.get("confirm_password")

        if not any([password, current_password, new_password, confirm_password]):
            return attrs

        if user and instance and user != instance:
            if password:
                if password != confirm_password:
                    raise serializers.ValidationError({
                        "confirm_password": "Passwords do not match."
                    })
            return attrs

        if user and instance and user == instance:
            if not current_password:
                raise serializers.ValidationError({
                    "current_password": "Current password is required."
                })

            if not user.check_password(current_password):
                raise serializers.ValidationError({
                    "current_password": "Incorrect current password."
                })

            if not new_password:
                raise serializers.ValidationError({
                    "new_password": "New password is required."
                })

            if new_password != confirm_password:
                raise serializers.ValidationError({
                    "confirm_password": "Passwords do not match."
                })

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        role_ids = validated_data.pop("role_ids", None)
        password = validated_data.pop("password", None)
        validated_data.pop("confirm_password", None)
        validated_data.pop("current_password", None)
        validated_data.pop("new_password", None)

        user = User.objects.create_user(**validated_data)
        if password:
            user.set_password(password)
            user.save()

        if role_ids is not None:
            user.roles.set(role_ids)

        return user

    @transaction.atomic
    def update(self, instance, validated_data):
        roles = validated_data.pop("role_ids", None)

        password = validated_data.pop("password", None)
        current_password = validated_data.pop("current_password", None)
        new_password = validated_data.pop("new_password", None)
        validated_data.pop("confirm_password", None)

        instance = super().update(instance, validated_data)

        if password:
            instance.set_password(password)
            instance.save()

        elif current_password and new_password:
            instance.set_password(new_password)
            instance.save()

        request = self.context.get("request")
        if roles is not None and request and request.user != instance:
            instance.roles.set(roles)

        return instance


class SelfDetailFetchSerializer(serializers.ModelSerializer):
    role = RoleSerializer(many=True, read_only=True, source="roles")
    permissions = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "first_name",
            "middle_name",
            "last_name",
            "full_name",
            "phone",
            "email",
            "is_superuser",
            "role",
            "permissions",
        )

    def get_permissions(self, obj):
        if obj.is_superuser:
            return list(Permissions.objects.values_list("key", flat=True))

        return list(obj.roles.filter(is_active=True)
                    .values_list('permissions__key', flat=True)
                    .distinct())
