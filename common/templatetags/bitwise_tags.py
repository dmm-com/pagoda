from typing import Any

from django import template

register = template.Library()


@register.filter
def bitwise_and(value: Any, arg: Any) -> int | bool:
    return value and arg and int(value) & int(arg)


@register.filter
def isin(obj: dict[str, Any], entries: Any) -> bool:
    return entries.filter(id=obj["id"]).exists()


@register.filter
def get_item(dict_val: dict[str, Any], key: str) -> Any:
    return dict_val.get(key)
