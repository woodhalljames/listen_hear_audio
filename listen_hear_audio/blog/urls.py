from django.urls import path

from .views import BlogDetailView
from .views import BlogListView

app_name = "blog"

urlpatterns = [
    path("", BlogListView.as_view(), name="post_list"),
    path("<slug:slug>/", BlogDetailView.as_view(), name="post_detail"),
]
