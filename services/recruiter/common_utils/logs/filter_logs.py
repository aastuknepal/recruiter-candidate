from django.db.models import F
from django_filters import rest_framework as filterset

from apps.users.models import ActivityLog, ChangeLog

class ChangeLogFilterSet(filterset.FilterSet):
    
    model_name = filterset.CharFilter(field_name="model_name", lookup_expr="icontains")

    class Meta:
        model = ChangeLog
        fields = ['model_name'] 

    CUSTOM_FIELD_MAPPINGS = {
        
        "user": {
            "filter_field": "user_name_sort",
            "filter_method": "filter_user",
            "annotate": lambda qs: qs.annotate(
                user_name_sort=F("user__username")
            ),
    }
    }

    def filter_user(self, queryset, name, value):
        return queryset.filter(user__username__icontains=value)

    def annotate_for_sorting(self, queryset, field_name):
        if field_name in self.CUSTOM_FIELD_MAPPINGS:
            return self.CUSTOM_FIELD_MAPPINGS[field_name]["annotate"](queryset)
        return queryset


class ActivityLogFilterSet(filterset.FilterSet):
    
    activity_type = filterset.CharFilter(field_name="activity_type", lookup_expr="icontains")
    ip_address = filterset.CharFilter(field_name="ip_address", lookup_expr="icontains")

    class Meta:
        model = ActivityLog
        fields = ["activity_type", "ip_address"] 

    CUSTOM_FIELD_MAPPINGS = {
        
        "user": {
            "filter_field": "user_name_sort",
            "filter_method": "filter_user",
            "annotate": lambda qs: qs.annotate(user_name_sort=F("user__username")),
        },
    }


    def filter_user(self, queryset, name, value):
        return queryset.filter(user__username__icontains=value)

    def annotate_for_sorting(self, queryset, field_name):
        if field_name in self.CUSTOM_FIELD_MAPPINGS:
            return self.CUSTOM_FIELD_MAPPINGS[field_name]["annotate"](queryset)
        return queryset