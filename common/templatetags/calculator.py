from django import template

register = template.Library()


@register.filter
def divmod(dividend: int, divisor: int) -> int:
    return dividend % divisor
