from rest_framework import serializers
from apps.job_listings.models import JobListing


class JobListingSerializer(serializers.ModelSerializer):
    class Meta:
        model  = JobListing
        fields = '__all__'
        read_only_fields = ['job_id', 'created_at', 'updated_at']
