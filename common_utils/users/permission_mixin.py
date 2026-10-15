from rest_framework.permissions import BasePermission


class ExplicitPermission(BasePermission):
    """
    Highly flexible permission checker for custom key-based authorization.
    Supports single keys, lists (OR logic), and dicts (AND/OR logic).
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        if getattr(request.user, "is_deleted", False) or not request.user.is_active:
            self.message = "Your account has been deactivated. Please contact an administrator."
            return False

        if request.user.is_superuser:
            return True
        permission_map = getattr(view, 'permission_map', {})

        action = getattr(view, "action", request.method.lower())		        
        action_requirement = permission_map.get(action)		
        

        if not action_requirement:
            return True

        required_keys = []
        require_all = False

        if isinstance(action_requirement, str):
            required_keys = [action_requirement]
        elif isinstance(action_requirement, list):
            required_keys = action_requirement
        elif isinstance(action_requirement, dict):
            required_keys = action_requirement.get("permissions", [])
            require_all = action_requirement.get("require_all", False)

        if not required_keys:
            return False

        user_keys = set(request.user.roles.filter(is_active=True)
                        .values_list('permissions__key', flat=True)
                        .distinct())

        if require_all:
            return all(key in user_keys for key in required_keys)
        else:
            return any(key in user_keys for key in required_keys)
