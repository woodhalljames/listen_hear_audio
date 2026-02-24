from .models import SiteConfiguration


def business_info(request):
    """Make site configuration available to all templates."""
    return {
        "business_info": SiteConfiguration.load(),
    }
