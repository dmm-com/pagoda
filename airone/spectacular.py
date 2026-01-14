# These methods are used for filtering API endpoints to generate
# OpenAPI schema using drf-spectacular.
# (c.f. https://drf-spectacular.readthedocs.io/en/latest/settings.html)


def exclude_customview_hook(endpoints):
    """This excludes API endpoints of custom-view's and api_v1's ones.

    custom_view endpoints are excluded because they are optional and not always necessary.
    api_v1 endpoints are excluded because they are legacy APIs that use APIView without
    serializer_class, which causes DRF Spectacular to fail schema generation.
    This includes /api/v1/, /group/api/v1/, /role/api/v1/, etc.
    """
    result = []
    for path, path_regex, method, callback in endpoints:
        if "/custom/" not in path and "/api/v1/" not in path:
            result.append((path, path_regex, method, callback))
    return result
