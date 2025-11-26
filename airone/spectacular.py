# These methods are used for filtering API endpoints to generate
# OpenAPI schema using drf-spectacular.
# (c.f. https://drf-spectacular.readthedocs.io/en/latest/settings.html)


def exclude_customview_hook(endpoints):
    """This excludes API endpoints of custom-view's ones. Because it's not always
    necessary to generage custom-view's OpenAPI schema.
    """
    result = []
    for path, path_regex, method, callback in endpoints:
        if "/custom/" not in path:
            result.append((path, path_regex, method, callback))
    return result
