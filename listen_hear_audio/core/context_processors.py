from .models import BusinessInfo


def business_info(request):
    """Make business info available to all templates."""
    return {
        "business_info": BusinessInfo.load(),
    }
