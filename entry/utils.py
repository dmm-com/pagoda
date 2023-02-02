from entry.settings import CONFIG


def get_sort_order(sort_order_request):
    if sort_order_request == CONFIG.TEMPLATE_CONFIG["SORT_ORDER"]["name"]:
        return "name"
    elif sort_order_request == CONFIG.TEMPLATE_CONFIG["SORT_ORDER"]["name_reverse"]:
        return "-name"
    elif sort_order_request == CONFIG.TEMPLATE_CONFIG["SORT_ORDER"]["updated_time"]:
        return "updated_time"
    elif sort_order_request == CONFIG.TEMPLATE_CONFIG["SORT_ORDER"]["updated_time_reverse"]:
        return "-updated_time"
    elif sort_order_request == CONFIG.TEMPLATE_CONFIG["SORT_ORDER"]["created_time"]:
        return "created_time"
    elif sort_order_request == CONFIG.TEMPLATE_CONFIG["SORT_ORDER"]["created_time_reverse"]:
        return "-created_time"
    else:
        return get_sort_order(CONFIG.DEFAULT_LIST_SORT_ORDER)
