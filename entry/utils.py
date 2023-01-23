from entry.settings import CONFIG


def get_sort_order(sort_order_request):
    if sort_order_request == CONFIG.TEMPLATE_CONFIG["SORT_ORDER"]["name"]:
        return "name"
    elif sort_order_request == CONFIG.TEMPLATE_CONFIG["SORT_ORDER"]["name_reverse"]:
        return "-name"
    elif sort_order_request == CONFIG.TEMPLATE_CONFIG["SORT_ORDER"]["time"]:
        return "updated_time"
    elif sort_order_request == CONFIG.TEMPLATE_CONFIG["SORT_ORDER"]["time_reverse"]:
        return "-updated_time"
    else:
        return CONFIG.DEFAULT_LIST_SORT_ORDER
