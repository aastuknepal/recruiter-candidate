from django.urls import path
from apps.profiles.views import CandidateProfileView

urlpatterns = [
    path('me/', CandidateProfileView.as_view(), name='candidate-profile-me'),
]
