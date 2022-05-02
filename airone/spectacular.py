def exclude_customview_hook(endpoints):
    result = []
    for (path, path_regex, method, callback) in endpoints:
        if "/custom/" not in path:
            result.append((path, path_regex, method, callback))
    return result


def filter_apiv2_hook(endpoints):
    result = []
    for (path, path_regex, method, callback) in endpoints:
        if "/api/v2/" in path:
            result.append((path, path_regex, method, callback))
    return result
