from .models import SiteConfiguration
from listen_hear_audio.products.models import Category


def business_info(request):
    """Make site configuration available to all templates."""
    return {
        "business_info": SiteConfiguration.load(),
        "nav_categories": Category.objects.filter(show_in_catalog=True).order_by('display_order', 'name'),
    }
