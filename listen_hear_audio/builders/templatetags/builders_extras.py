from decimal import Decimal, ROUND_HALF_UP

from django import template

register = template.Library()


@register.filter
def apply_markup(price, markup_pct):
    """Return price with markup_pct percentage applied.

    Usage: {{ package.starting_price|apply_markup:markup_pct }}
    Returns the original price when markup_pct is 0 or falsy.
    """
    if not markup_pct:
        return price
    try:
        price = Decimal(str(price))
        pct = Decimal(str(markup_pct))
        result = price * (1 + pct / 100)
        return result.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    except Exception:
        return price
