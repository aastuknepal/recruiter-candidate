from common_utils.models.mixins import BaseAuditModelMixin, BaseTimeStampModelMixin, SoftDeleteModelMixin
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    """
    Custom manager for User model where username is the unique identifier.
    """

    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError("The Username field must be set")
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(username, password, **extra_fields)


class Permissions(BaseTimeStampModelMixin):
    name = models.CharField(max_length=255)
    key = models.CharField(
        max_length=255, unique=True)  # e.g. 'donor.view'
    description = models.TextField(blank=True, null=True)
    module = models.CharField(max_length=100)  # For grouping in UI

    class Meta:
        db_table = 'permissions'
        verbose_name = 'Permission'
        verbose_name_plural = 'Permissions'

    def __str__(self):
        return self.name


class Roles(BaseTimeStampModelMixin, SoftDeleteModelMixin):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    permissions = models.ManyToManyField(
        Permissions, related_name='roles', blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'roles'
        verbose_name = 'Role'
        verbose_name_plural = 'Roles'

    def __str__(self):
        return self.name


class User(AbstractBaseUser, BaseTimeStampModelMixin, BaseAuditModelMixin, SoftDeleteModelMixin):
    """
    Custom User model using AbstractBaseUser.
    Decoupled from Django's built-in Group/Permission models.
    """
    class GenderChoices(models.TextChoices):
        MALE = "MALE", "Male"
        FEMALE = "FEMALE", "Female"
        OTHER = "OTHER", "Other"
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True, null=True, blank=True)
    first_name = models.CharField(max_length=150)
    middle_name = models.CharField(max_length=150, blank=True, null=True)
    last_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=15,  null=True, blank=True)
    gender = models.CharField(
        max_length=20,
        choices=GenderChoices.choices,
        null=True,
        blank=True,
    )

    # Custom Permission System
    roles = models.ManyToManyField(Roles, related_name='users', blank=True)

    # Auth Management
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    last_login = models.DateTimeField(null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    class Meta:
        db_table = 'users'

    @property
    def full_name(self) -> str:
        if self.middle_name:
            full_name = f"{self.first_name} {self.middle_name} {self.last_name}"
        else:
            full_name = f"{self.first_name} {self.last_name}"
        return full_name.strip() if full_name.strip() != "" else self.username

    def has_explicit_perm(self, perm_key: str) -> bool:
        if self.is_superuser:
            return True
        return self.roles.filter(is_active=True, permissions__key=perm_key).exists()

    def has_perm(self, perm, obj=None):
        return self.is_active and self.has_explicit_perm(perm)

    def has_module_perms(self, app_label):
        return self.is_active and self.is_staff


# =============================================================================
# LOGGING MODELS
# =============================================================================

class ActivityLog(BaseTimeStampModelMixin):
    """
    Model to log user activities
    """

    user = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL
    )
    email_or_username = models.CharField(
        max_length=255,
        blank=True,
        help_text="Used when user is not yet authenticated (e.g., failed login)",
    )
    activity_type = models.CharField(
        max_length=50, help_text="Type of activity performed"
    )

    # Context
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, null=True)
    path = models.CharField(
        max_length=500, blank=True, null=True
    )  # e.g., /api/auth/login/
    http_method = models.CharField(
        max_length=10, blank=True, null=True
    )  # GET, POST, etc.

    # Optional: success/failure metadata
    is_successful = models.BooleanField(default=True)
    failure_reason = models.CharField(
        max_length=100, blank=True
    )  # e.g., "Invalid credentials"

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["activity_type", "-created_at"]),
            models.Index(fields=["ip_address", "-created_at"]),
        ]
        db_table = "activity_log"

    def __str__(self):
        user_display = (
            self.user.username if self.user else self.email_or_username or "Anonymous"
        )
        return f"{user_display} - {self.activity_type} ({self.created_at.strftime('%Y-%m-%d %H:%M')})"


class ErrorLog(BaseTimeStampModelMixin):
    """
    Model to log server errors occurred
    """

    error_message = models.TextField()
    model_name = models.CharField(max_length=255, blank=True, null=True)
    user = models.ForeignKey(
        User, blank=True, null=True, on_delete=models.DO_NOTHING
    )
    path = models.CharField(max_length=500, blank=True, null=True)
    method = models.CharField(max_length=10, blank=True, null=True)
    view_name = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        ordering = ["-created_at"]
        db_table = "error_log"


class ChangeLog(models.Model):
    """
    Model to log changes made to other models
    """

    ACTION_CHOICES = (
        ("Create", "Create"),
        ("Update", "Update"),
        ("Delete", "Delete"),
    )
    user = models.ForeignKey(
        User,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="change_logs",
        db_column="user_id",
    )
    model_name = models.CharField(max_length=100)
    object_id = models.CharField(max_length=100)
    action = models.CharField(
        max_length=10, blank=True, null=True, choices=ACTION_CHOICES
    )
    # This will store a JSON object like:
    # {"diagnosis": {"old": "Flu", "new": "Common Cold"}}
    changed_fields = models.JSONField(blank=True, null=True)

    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]
        db_table = "change_log"
