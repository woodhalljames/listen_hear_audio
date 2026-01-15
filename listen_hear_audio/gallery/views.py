from django.views.generic import ListView
from django.http import JsonResponse
from django.template.loader import render_to_string
from .models import GalleryImage
from taggit.models import Tag


class GalleryView(ListView):
    """Gallery page with infinite scroll and lazy loading"""
    model = GalleryImage
    template_name = 'gallery/gallery.html'
    context_object_name = 'images'
    paginate_by = 20  # Load 20 images at a time

    def get_queryset(self):
        """Get all images ordered chronologically"""
        return GalleryImage.objects.all().prefetch_related('tags').select_related()

    def get_context_data(self, **kwargs):
        """Add all tags to context for filter buttons"""
        context = super().get_context_data(**kwargs)

        # Get all unique tags used in gallery
        context['all_tags'] = Tag.objects.filter(
            taggit_taggeditem_items__content_type__model='galleryimage'
        ).distinct().order_by('name')

        return context

    def render_to_response(self, context, **response_kwargs):
        """Return JSON for AJAX requests, HTML for regular requests"""
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            images = context['images']
            html = render_to_string('gallery/_gallery_items.html', {'images': images})

            return JsonResponse({
                'html': html,
                'has_next': context['page_obj'].has_next() if context.get('page_obj') else False
            })

        return super().render_to_response(context, **response_kwargs)
