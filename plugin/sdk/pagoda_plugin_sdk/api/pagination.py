"""
Pagination classes for plugin API views.

These pagination classes provide standardized pagination patterns
for plugin API endpoints, ensuring consistent behavior across
different plugins and host applications.
"""

import logging
from collections import OrderedDict
from typing import Any, Dict, Optional, cast

from rest_framework.pagination import LimitOffsetPagination, PageNumberPagination
from rest_framework.response import Response

logger = logging.getLogger(__name__)


class PluginPagination(LimitOffsetPagination):
    """Standard pagination class for plugin API endpoints

    Provides limit/offset based pagination with reasonable defaults
    and plugin-specific enhancements.

    Features:
    - Configurable default and maximum limits
    - Plugin context in pagination metadata
    - Performance monitoring hooks
    - Consistent response format

    Usage:
        class MyPluginViewSet(PluginViewSet):
            pagination_class = PluginPagination
    """

    default_limit = 100
    limit_query_param = "limit"
    offset_query_param = "offset"
    max_limit = 1000

    def get_paginated_response(self, data: Any) -> Response:
        """Return a paginated style response with plugin enhancements

        Args:
            data: The serialized page data

        Returns:
            Response object with pagination metadata
        """
        # Get plugin context if available
        plugin_context = self._get_plugin_context()

        response_data = OrderedDict(
            [
                ("count", self.count),
                ("next", self.get_next_link()),
                ("previous", self.get_previous_link()),
                ("results", data),
            ]
        )

        # Add plugin context to metadata
        if plugin_context:
            response_data["plugin_meta"] = {
                "plugin_id": plugin_context.get("plugin_id"),
                "pagination_info": {
                    "limit": self.limit,
                    "offset": self.offset,
                    "total_pages": self._get_total_pages(),
                    "current_page": self._get_current_page(),
                },
            }

        return Response(response_data)

    def _get_plugin_context(self) -> Optional[Dict[str, Any]]:
        """Get plugin context from request if available

        Returns:
            Plugin context dictionary or None
        """
        request = getattr(self, "request", None)
        if request and hasattr(request, "plugin_context"):
            return cast(Optional[Dict[str, Any]], request.plugin_context)
        return None

    def _get_total_pages(self) -> int:
        """Calculate total number of pages

        Returns:
            Total number of pages
        """
        if self.count == 0 or self.limit == 0:
            return 0
        return int((self.count + self.limit - 1) // self.limit)

    def _get_current_page(self) -> int:
        """Calculate current page number (1-based)

        Returns:
            Current page number
        """
        if self.limit == 0:
            return 1
        return int((self.offset // self.limit) + 1)

    def paginate_queryset(self, queryset, request, view=None):
        """Paginate a queryset with performance monitoring

        Args:
            queryset: The queryset to paginate
            request: The request object
            view: The view being used

        Returns:
            Paginated queryset page
        """
        # Store request for use in get_paginated_response
        self.request = request

        # Log pagination metrics for performance monitoring
        plugin_id = getattr(view, "plugin_id", "unknown") if view else "unknown"
        logger.debug(
            f"Plugin {plugin_id} paginating queryset with limit={self.limit}, offset={self.offset}"
        )

        return super().paginate_queryset(queryset, request, view)


class PluginPageNumberPagination(PageNumberPagination):
    """Page number based pagination for plugins

    Alternative pagination style using page numbers instead of offset/limit.
    Some plugins or use cases may prefer this style.

    Features:
    - Page-based navigation
    - Plugin context in metadata
    - Configurable page size
    - Performance monitoring

    Usage:
        class MyPluginViewSet(PluginViewSet):
            pagination_class = PluginPageNumberPagination
    """

    page_size = 50
    page_size_query_param = "page_size"
    max_page_size = 500

    def get_paginated_response(self, data: Any) -> Response:
        """Return a paginated style response with plugin enhancements

        Args:
            data: The serialized page data

        Returns:
            Response object with pagination metadata
        """
        # Get plugin context if available
        plugin_context = self._get_plugin_context()

        response_data = OrderedDict(
            [
                ("count", self.page.paginator.count),
                ("next", self.get_next_link()),
                ("previous", self.get_previous_link()),
                ("results", data),
            ]
        )

        # Add plugin context to metadata
        if plugin_context:
            response_data["plugin_meta"] = {
                "plugin_id": plugin_context.get("plugin_id"),
                "pagination_info": {
                    "page_size": self.page_size,
                    "current_page": self.page.number,
                    "total_pages": self.page.paginator.num_pages,
                    "has_next": self.page.has_next(),
                    "has_previous": self.page.has_previous(),
                },
            }

        return Response(response_data)

    def _get_plugin_context(self) -> Optional[Dict[str, Any]]:
        """Get plugin context from request if available

        Returns:
            Plugin context dictionary or None
        """
        request = getattr(self, "request", None)
        if request and hasattr(request, "plugin_context"):
            return cast(Optional[Dict[str, Any]], request.plugin_context)
        return None

    def paginate_queryset(self, queryset, request, view=None):
        """Paginate a queryset with performance monitoring

        Args:
            queryset: The queryset to paginate
            request: The request object
            view: The view being used

        Returns:
            Paginated queryset page
        """
        # Store request for use in get_paginated_response
        self.request = request

        # Log pagination metrics for performance monitoring
        plugin_id = getattr(view, "plugin_id", "unknown") if view else "unknown"
        page_size = self.get_page_size(request)
        logger.debug(f"Plugin {plugin_id} paginating queryset with page_size={page_size}")

        return super().paginate_queryset(queryset, request, view)


class PluginNoPagination:
    """No pagination class for plugins

    Disables pagination for endpoints that need to return all results.
    Use with caution on large datasets.

    Usage:
        class MyPluginViewSet(PluginViewSet):
            pagination_class = PluginNoPagination
    """

    def paginate_queryset(self, queryset, request, view=None):
        """Return None to disable pagination

        Args:
            queryset: The queryset (not paginated)
            request: The request object
            view: The view being used

        Returns:
            None (disables pagination)
        """
        # Log warning for large querysets
        if hasattr(queryset, "count"):
            count = queryset.count()
            if count > 1000:
                plugin_id = getattr(view, "plugin_id", "unknown") if view else "unknown"
                logger.warning(
                    f"Plugin {plugin_id} is returning {count} items without pagination. "
                    "Consider enabling pagination for better performance."
                )

        return None
