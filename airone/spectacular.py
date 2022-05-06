# These methods are used for filtering API endpoints to generate
# OpenAPI schema using drf-spectacular.
# (c.f. https://drf-spectacular.readthedocs.io/en/latest/settings.html)

def exclude_customview_hook(endpoints):
    """This excludes API endpoints of custom-view's ones. Because it's not always
    necessary to generage custom-view's OpenAPI schema.
    """
    result = []
    for (path, path_regex, method, callback) in endpoints:
        if "/custom/" not in path:
            result.append((path, path_regex, method, callback))
    return result


def filter_apiv2_hook(endpoints):
    """This excludes API endpoints for AirOne API(v1). React views refer to only
    AirOne API(v2). So it's not necessary to generate API(v1)'s OpenAPI schema.
    """
    result = []
    for (path, path_regex, method, callback) in endpoints:
        if "/api/v2/" in path:
            result.append((path, path_regex, method, callback))
    return result
