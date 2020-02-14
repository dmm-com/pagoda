from django import template

register = template.Library()


@register.filter
def divmod(dividend, divisor):
    return dividend % divisor
