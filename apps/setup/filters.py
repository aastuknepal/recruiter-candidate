from django_filters import rest_framework as filterset
from apps.setup.models import (
    BloodGroup,
    ComponentType,
    ExternalBloodBank,
    Camp,
    Hospital,
    BagType,
    CheckList,
    DonationType,
    DonorType,
    TestType,
    TestMethod,
    TestResultOption,
)
from django.db.models import Q, F


class BloodGroupFilter(filterset.FilterSet):
    name = filterset.CharFilter(lookup_expr="icontains")

    class Meta:
        model = BloodGroup
        fields = ["name"]


class ComponentTypeFilter(filterset.FilterSet):
    name = filterset.CharFilter(lookup_expr="icontains")
    code = filterset.CharFilter(lookup_expr="icontains")

    class Meta:
        model = ComponentType
        fields = ["name", "code"]


class BagTypeFilter(filterset.FilterSet):
    name = filterset.CharFilter(lookup_expr="icontains")

    class Meta:
        model = BagType
        fields = ["name"]


class DonorTypeFilter(filterset.FilterSet):
    name = filterset.CharFilter(lookup_expr="icontains")

    class Meta:
        model = DonorType
        fields = ["name"]


class DonationTypeFilter(filterset.FilterSet):
    name = filterset.CharFilter(lookup_expr="icontains")

    class Meta:
        model = DonationType
        fields = ["name"]


class CheckListFilter(filterset.FilterSet):
    name = filterset.CharFilter(lookup_expr="icontains")

    class Meta:
        model = CheckList
        fields = ["name"]


class TestTypeFilter(filterset.FilterSet):
    name = filterset.CharFilter(lookup_expr="icontains")
    code = filterset.CharFilter(lookup_expr="icontains")

    class Meta:
        model = TestType
        fields = ["name", "code"]


class TestMethodFilter(filterset.FilterSet):
    name = filterset.CharFilter(lookup_expr="icontains")

    class Meta:
        model = TestMethod
        fields = ["name"]


class TestResultOptionFilter(filterset.FilterSet):
    name = filterset.CharFilter(lookup_expr="icontains")

    class Meta:
        model = TestResultOption
        fields = ["name"]


class ExternalBloodBankFilter(filterset.FilterSet):
    name = filterset.CharFilter(lookup_expr="icontains")
    license_number = filterset.CharFilter(lookup_expr="icontains")

    class Meta:
        model = ExternalBloodBank
        fields = ["name", "license_number"]


class CampFilter(filterset.FilterSet):
    name = filterset.CharFilter(lookup_expr="icontains")
    location = filterset.CharFilter(lookup_expr="icontains")

    class Meta:
        model = Camp
        fields = ["name", "location"]


class HospitalFilter(filterset.FilterSet):
    name = filterset.CharFilter(lookup_expr="icontains")

    class Meta:
        model = Hospital
        fields = ["name"]
