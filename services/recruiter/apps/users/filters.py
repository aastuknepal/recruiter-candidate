from django_filters import rest_framework as filterset
from apps.users.models import User, Roles
from django.db.models import Q, F, Value
from django.db.models.functions import Concat, Coalesce


class UserFilterSet(filterset.FilterSet):
    username = filterset.CharFilter(lookup_expr="icontains")

    class Meta:
        model = User
        fields = ["username"]

    CUSTOM_FIELD_MAPPINGS = {
        "full_name": {
            "filter_field": "full_name_sort",
            "annotate": lambda qs: qs.annotate(
                full_name_sort=Concat(
                    Coalesce("first_name", Value("")),
                    Value(" "),
                    Coalesce("middle_name", Value("")),
                    Value(" "),
                    Coalesce("last_name", Value("")),
                )
            ),
        },
    }

    def annotate_for_sorting(self, queryset, field_name):
        # Apply annotation for a given custom field
        if field_name in self.CUSTOM_FIELD_MAPPINGS:
            return self.CUSTOM_FIELD_MAPPINGS[field_name]["annotate"](queryset)
        return queryset


class RoleFilterSet(filterset.FilterSet):
    name = filterset.CharFilter(lookup_expr="icontains")

    class Meta:
        model = Roles
        fields = ["name"]

