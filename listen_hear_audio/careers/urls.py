from django.urls import path

from .views import CareersListView, JobDetailView, apply_for_job

app_name = "careers"

urlpatterns = [
    path("", CareersListView.as_view(), name="job_list"),
    path("<slug:slug>/", JobDetailView.as_view(), name="job_detail"),
    path("<slug:slug>/apply/", apply_for_job, name="apply"),
]
