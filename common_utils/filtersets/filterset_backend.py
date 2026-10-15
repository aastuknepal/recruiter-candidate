import json
from django.core.exceptions import ValidationError
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters


class CustomFilterBackend(filters.BaseFilterBackend):
    """
    Custom filter backend that supports dynamic filtering and sorting via JSON parameters
    with support for custom field mappings and annotations.

    Features:
    - Dynamic filtering via 'filters' JSON parameter
    - Dynamic sorting via 'sorters' JSON parameter
    - Support for custom field mappings (e.g., dot notation like 'donor.phone')
    - Support for computed/annotated fields (e.g., full_name from first+middle+last)

    Usage in ViewSets:
    ------------------
    class MyViewSet(viewsets.ModelViewSet):
        queryset = MyModel.objects.all()
        serializer_class = MySerializer
        filter_backends = [CustomFilterBackend]
        filterset_class = MyFilterSet

    Usage in FilterSets:
    -------------------
    class MyFilterSet(filterset.FilterSet):
        # Standard filters
        name = filterset.CharFilter(lookup_expr="icontains")

        class Meta:
            model = MyModel
            fields = ["name"]

        # Custom field mappings for filtering and sorting
        CUSTOM_FIELD_MAPPINGS = {
            "donor.phone": {
                "filter_field": "donor_phone_sort",      # Field name for sorting (required)
                "filter_method": "filter_donor_phone",    # Method name for filtering (optional)
                "annotate": lambda qs: qs.annotate(       # Annotation lambda (required for sorting)
                    donor_phone_sort=F("donor__phone")
                ),
            },
            "full_name": {
                "filter_field": "full_name_sort",
                "filter_method": "filter_full_name",
                "annotate": lambda qs: qs.annotate(
                    full_name_sort=Concat(
                        Coalesce("first_name", Value("")),
                        Value(" "),
                        Coalesce("last_name", Value("")),
                    )
                ),
            },
        }

        # Define filter methods referenced in CUSTOM_FIELD_MAPPINGS
        def filter_donor_phone(self, queryset, name, value):
            return queryset.filter(donor__phone__icontains=value)

        def filter_full_name(self, queryset, name, value):
            # Reuse annotation from CUSTOM_FIELD_MAPPINGS
            queryset = self.CUSTOM_FIELD_MAPPINGS["full_name"]["annotate"](queryset)
            return queryset.filter(full_name_sort__icontains=value)

        # Required for sorting custom fields
        def annotate_for_sorting(self, queryset, field_name):
            if field_name in self.CUSTOM_FIELD_MAPPINGS:
                return self.CUSTOM_FIELD_MAPPINGS[field_name]["annotate"](queryset)
            return queryset

    Frontend Usage:
    --------------
    # Filtering
    GET /api/items/?filters=[{"field":"donor.phone","type":"like","value":"9840"}]

    # Sorting
    GET /api/items/?sorters=[{"field":"full_name","dir":"asc"}]

    # Combined
    GET /api/items/?filters=[...]&sorters=[...]

    Notes:
    ------
    - Filter field names from frontend must match either Meta.fields or CUSTOM_FIELD_MAPPINGS keys
    - Sort field names from frontend must match CUSTOM_FIELD_MAPPINGS keys for custom fields
    - The 'filter_method' in CUSTOM_FIELD_MAPPINGS is optional (only needed if you want filtering)
    - The 'filter_field' is used for sorting and must match the annotation field name
    - Annotations are applied before sorting to ensure computed fields can be sorted
    """

    def filter_queryset(self, request, queryset, view):
        """Apply Django filters, custom filters, and sorting to the queryset."""
        # Apply standard Django filters first
        queryset = DjangoFilterBackend().filter_queryset(request, queryset, view)

        filter_param = request.query_params.get("filters")
        sort_param = request.query_params.get("sorters")

        if not filter_param and not sort_param:
            return queryset
        
        #parse json param converts json to python dict and also validates if its a valid json, if not it raises validation error
        filters_list = self._parse_json_param(filter_param, "filters")
        sorters_list = self._parse_json_param(sort_param, "sorters")

        filterset_class = getattr(view, "filterset_class", None)

        # Process filters
        filter_data = self._build_filter_data(
            filters_list, filterset_class, request.GET, queryset
        )
        queryset = self._apply_filters(queryset, filter_data, filterset_class, request)

        # Process sorting
        sort_fields = self._build_sort_fields(sorters_list)
        queryset = self._apply_annotations(queryset, sort_fields, filterset_class)
        queryset = self._apply_sorting(queryset, sort_fields, filterset_class)

        return queryset

    def _parse_json_param(self, param, param_name):
        """Parse and validate JSON parameter."""
        if not param:
            return []

        try:
            parsed = json.loads(param)
            if not isinstance(parsed, list):
                raise ValidationError(f"{param_name.capitalize()} must be a list")
            return parsed
        except json.JSONDecodeError:
            raise ValidationError(f"Invalid JSON format for {param_name}")

    def _build_filter_data(
        self, filters_list, filterset_class, request_params, queryset
    ):
        """Build filter data dictionary from filters list."""
        if not filters_list or not filterset_class:
            return {}

        filter_data = {}
        filterset_fields = filterset_class.Meta.fields
        standard_params = {
            k: v for k, v in request_params.items() if k in filterset_fields
        }

        for filter_item in filters_list:
            if not self._is_valid_filter_item(
                filter_item, filterset_fields, standard_params, filterset_class
            ):
                continue

            field_name = filter_item["field"]
            value = filter_item["value"]

            filter_data[field_name] = value

        return filter_data

    def _is_valid_filter_item(self, filter_item, filterset_fields, standard_params, filterset_class):
        """Check if filter item is valid and should be processed."""
        if not isinstance(filter_item, dict):
            return False

        field_name = filter_item.get("field")
        value = filter_item.get("value")
        filter_type = filter_item.get("type")

        if not all([field_name, value, filter_type]):
            return False

        # Build valid fields from both Meta.fields and CUSTOM_FIELD_MAPPINGS
        valid_fields = set(filterset_fields)
        if filterset_class and hasattr(filterset_class, "CUSTOM_FIELD_MAPPINGS"):
            valid_fields.update(filterset_class.CUSTOM_FIELD_MAPPINGS.keys())

        if field_name not in valid_fields:
            return False

        if field_name in standard_params:
            return False

        return True

    def _get_mapped_field_name(self, field_name, filterset_class):
        """Get the mapped filter field name for custom fields."""
        if not hasattr(filterset_class, "CUSTOM_FIELD_MAPPINGS"):
            return field_name

        custom_mappings = filterset_class.CUSTOM_FIELD_MAPPINGS
        if field_name in custom_mappings:
            return custom_mappings[field_name]["filter_field"]

        return field_name

    # Support custom filter methods
    def _apply_filters(self, queryset, filter_data, filterset_class, request):
        """Apply filters to the queryset."""
        if not filter_data:
            return queryset

        if filterset_class:
            # Separate standard filters from custom mapped filters
            standard_filters = {}
            custom_filters = {}

            for field_name, value in filter_data.items():
                if (
                    hasattr(filterset_class, "CUSTOM_FIELD_MAPPINGS")
                    and field_name in filterset_class.CUSTOM_FIELD_MAPPINGS
                ):
                    custom_filters[field_name] = value
                else:
                    standard_filters[field_name] = value

            # Apply standard filters via filterset
            if standard_filters:
                filterset = filterset_class(
                    data=standard_filters, queryset=queryset, request=request
                )
                if not filterset.is_valid():
                    raise ValidationError(filterset.errors)
                queryset = filterset.qs

            # Apply custom filters via their methods
            if custom_filters:
                filterset_instance = filterset_class(queryset=queryset, request=request)
                for field_name, value in custom_filters.items():
                    mapping = filterset_class.CUSTOM_FIELD_MAPPINGS[field_name]
                    if "filter_method" in mapping:
                        method_name = mapping["filter_method"]
                        if hasattr(filterset_instance, method_name):
                            filter_method = getattr(filterset_instance, method_name)
                            queryset = filter_method(queryset, field_name, value)

            return queryset

        # Fallback: apply basic Q filters
        filter_query = Q()
        for field, value in filter_data.items():
            filter_query &= Q(**{field: value})
        return queryset.filter(filter_query)

    def _build_sort_fields(self, sorters_list):
        """Build list of sort fields from sorters list."""
        sort_fields = []
        for sort_item in sorters_list:
            if not isinstance(sort_item, dict):
                continue

            field_name = sort_item.get("field")
            if not field_name:
                continue

            direction = "-" if sort_item.get("dir", "").upper() == "DESC" else ""
            sort_fields.append(f"{direction}{field_name}")

        return sort_fields

    def _apply_annotations(self, queryset, sort_fields, filterset_class):
        """Apply annotations for custom sortable fields."""
        if not sort_fields or not filterset_class:
            return queryset

        if not hasattr(filterset_class, "CUSTOM_FIELD_MAPPINGS"):
            return queryset

        filterset_instance = filterset_class()
        if not hasattr(filterset_instance, "annotate_for_sorting"):
            return queryset

        for sort_field in sort_fields:
            clean_field = sort_field.lstrip("-")
            queryset = filterset_instance.annotate_for_sorting(queryset, clean_field)

        return queryset

    def _apply_sorting(self, queryset, sort_fields, filterset_class):
        """Apply sorting to the queryset with field name mapping."""
        if not sort_fields:
            return queryset

        mapped_sort_fields = []
        for sort_field in sort_fields:
            direction = "-" if sort_field.startswith("-") else ""
            clean_field = sort_field.lstrip("-")

            # Map custom fields to their annotated field names
            mapped_field = self._get_mapped_field_name(clean_field, filterset_class)
            mapped_sort_fields.append(f"{direction}{mapped_field}")

        return queryset.order_by(*mapped_sort_fields)
