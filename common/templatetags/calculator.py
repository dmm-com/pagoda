from django import template

register = template.Library()


@register.filter  # type: ignore[misc]
def divmod(dividend: int, divisor: int) -> int:
    return dividend % divisor
