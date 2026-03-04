from django.views.generic import DetailView
from django.views.generic import ListView

from .models import BlogPost


class BlogListView(ListView):
    model = BlogPost
    template_name = "blog/blog_list.html"
    context_object_name = "posts"
    paginate_by = 10

    def get_queryset(self):
        queryset = BlogPost.objects.filter(published=True).select_related('author').prefetch_related('tags')
        tag = self.request.GET.get("tag")
        if tag:
            queryset = queryset.filter(tags__name__in=[tag])
        return queryset


class BlogDetailView(DetailView):
    model = BlogPost
    template_name = "blog/blog_detail.html"
    context_object_name = "post"

    def get_queryset(self):
        # Allow staff to preview unpublished posts
        if self.request.user.is_staff:
            return BlogPost.objects.all().select_related('author').prefetch_related('tags')
        return BlogPost.objects.filter(published=True).select_related('author').prefetch_related('tags')
