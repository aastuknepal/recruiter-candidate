from drf_spectacular.utils import extend_schema
from common_utils.users.permission_mixin import ExplicitPermission

from apps.setup.models import (
    Configuration,
)
from apps.setup.serializers import (
    ConfigurationSerializer,
)
from common_utils.pagination.default_pagination import CustomDefaultPagination
from common_utils.views.base_views import AbstractViewSet
from common_utils.filtersets.filterset_backend import CustomFilterBackend


@extend_schema(tags=["Setup-Configuration"])
class ConfigurationViewSet(AbstractViewSet):
    queryset = Configuration.objects.all().order_by("id")
    serializer_class = ConfigurationSerializer
    pagination_class = CustomDefaultPagination
    permission_classes = [ExplicitPermission]
    permission_map = {
        "list": "setup.view.configurations",
        "retrieve": "setup.view.configurations",
        "create": "setup.edit.configurations",
        "update": "setup.edit.configurations",
        "partial_update": "setup.edit.configurations",
    }