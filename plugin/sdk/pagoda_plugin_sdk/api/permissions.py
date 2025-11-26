"""
Permission classes for plugin API views.

These permission classes provide standardized authorization patterns
that work with different host applications while maintaining security
and flexibility.
"""

import logging
from typing import Any, Optional

from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView

logger = logging.getLogger(__name__)


class PluginPermission(BasePermission):
    """Base permission class for plugin API endpoints

    This class provides a standardized framework for implementing
    permissions in plugins while maintaining compatibility with
    different host applications.

    The permission system works at two levels:
    1. View-level permissions (has_permission) - Check if user can access the view
    2. Object-level permissions (has_object_permission) - Check if user can access specific objects

    Usage:
        class MyPluginPermission(PluginPermission):
            def check_view_permission(self, user, view):
                return user.is_active and user.is_authenticated

            def check_object_permission(self, user, obj, permission):
                # Custom object permission logic
                return True

        class MyAPIView(PluginAPIView):
            permission_classes = [MyPluginPermission]
    """

    # Default permission mappings for different actions
    action_permission_map = {
        "list": "read",
        "retrieve": "read",
        "create": "write",
        "update": "write",
        "partial_update": "write",
        "destroy": "delete",
    }

    def has_permission(self, request: Request, view: APIView) -> bool:
        """Check view-level permissions

        Args:
            request: The request object
            view: The view being accessed

        Returns:
            True if permission is granted, False otherwise
        """
        # Basic authentication check
        if not request.user or not request.user.is_authenticated:
            logger.debug("Permission denied: User not authenticated")
            return False

        # Check if user is active
        if not getattr(request.user, "is_active", True):
            logger.debug(f"Permission denied: User {request.user} is not active")
            return False

        # Custom view permission check
        return self.check_view_permission(request.user, view, request)

    def has_object_permission(self, request: Request, view: APIView, obj: Any) -> bool:
        """Check object-level permissions

        Args:
            request: The request object
            view: The view being accessed
            obj: The object being accessed

        Returns:
            True if permission is granted, False otherwise
        """
        # Basic checks first
        if not self.has_permission(request, view):
            return False

        # Determine required permission based on action
        action = getattr(view, "action", None)
        action_key = action if isinstance(action, str) else "read"
        required_permission = self.action_permission_map.get(action_key, "read")

        # Custom object permission check
        return self.check_object_permission(request.user, obj, required_permission, request, view)

    def check_view_permission(self, user: Any, view: APIView, request: Request) -> bool:
        """Check if user has permission to access the view

        Override this method to implement custom view-level permission logic.

        Args:
            user: The user requesting access
            view: The view being accessed
            request: The request object

        Returns:
            True if permission is granted, False otherwise
        """
        # Default implementation allows all authenticated active users
        return True

    def check_object_permission(
        self, user: Any, obj: Any, permission: str, request: Request, view: APIView
    ) -> bool:
        """Check if user has permission to access the specific object

        Override this method to implement custom object-level permission logic.

        Args:
            user: The user requesting access
            obj: The object being accessed
            permission: Required permission ('read', 'write', 'delete')
            request: The request object
            view: The view being accessed

        Returns:
            True if permission is granted, False otherwise
        """
        # Default implementation allows all authenticated active users
        return True


class PluginACLPermission(PluginPermission):
    """ACL-based permission class for plugins

    This permission class integrates with host application ACL systems
    through a standardized interface. It provides methods to check
    permissions while remaining agnostic to the specific ACL implementation.

    Usage:
        class MyACLPermission(PluginACLPermission):
            def get_acl_checker(self, request, view):
                # Return host application's ACL checker
                return request.user.acl_checker
    """

    def check_object_permission(
        self, user: Any, obj: Any, permission: str, request: Request, view: APIView
    ) -> bool:
        """Check object permission using ACL system

        Args:
            user: The user requesting access
            obj: The object being accessed
            permission: Required permission ('read', 'write', 'delete')
            request: The request object
            view: The view being accessed

        Returns:
            True if permission is granted, False otherwise
        """
        # Get ACL checker from host application
        acl_checker = self.get_acl_checker(request, view)
        if not acl_checker:
            logger.warning("No ACL checker available, falling back to default permission")
            return bool(super().check_object_permission(user, obj, permission, request, view))

        # Check permission using ACL system
        try:
            return bool(acl_checker.check_permission(user, obj, permission))
        except Exception as e:
            logger.error(f"ACL permission check failed: {e}")
            return False

    def get_acl_checker(self, request: Request, view: APIView) -> Optional[Any]:
        """Get ACL checker from host application

        Override this method to return the appropriate ACL checker
        for your host application.

        Args:
            request: The request object
            view: The view being accessed

        Returns:
            ACL checker object or None
        """
        # Default implementation returns None
        # Subclasses should override this to provide actual ACL integration
        return None


class IsPluginAuthenticated(BasePermission):
    """Simple authentication-only permission for plugins

    This permission class only checks if the user is authenticated
    and active. It's useful for endpoints that don't require
    complex authorization logic.
    """

    def has_permission(self, request: Request, view: APIView) -> bool:
        """Check if user is authenticated and active

        Args:
            request: The request object
            view: The view being accessed

        Returns:
            True if user is authenticated and active
        """
        return (
            request.user
            and request.user.is_authenticated
            and getattr(request.user, "is_active", True)
        )


class IsPluginOwner(BasePermission):
    """Permission class to check if user owns the object

    This permission class checks if the requesting user is the owner
    of the object being accessed. It looks for common ownership fields
    like 'created_user', 'owner', or 'user'.
    """

    owner_fields = ["created_user", "owner", "user"]

    def has_object_permission(self, request: Request, view: APIView, obj: Any) -> bool:
        """Check if user owns the object

        Args:
            request: The request object
            view: The view being accessed
            obj: The object being accessed

        Returns:
            True if user owns the object
        """
        if not request.user or not request.user.is_authenticated:
            return False

        # Check common ownership fields
        for field in self.owner_fields:
            if hasattr(obj, field):
                owner = getattr(obj, field)
                if owner == request.user:
                    return True

        return False


class IsPluginAdminOrOwner(IsPluginOwner):
    """Permission class for admin users or object owners

    This permission class allows access if the user is either:
    1. An admin/superuser, or
    2. The owner of the object
    """

    def has_permission(self, request: Request, view: APIView) -> bool:
        """Check if user is admin or passes basic auth checks

        Args:
            request: The request object
            view: The view being accessed

        Returns:
            True if user has permission
        """
        if not request.user or not request.user.is_authenticated:
            return False

        # Allow admins/superusers
        if getattr(request.user, "is_superuser", False):
            return True

        # Allow if user is active
        return getattr(request.user, "is_active", True)

    def has_object_permission(self, request: Request, view: APIView, obj: Any) -> bool:
        """Check if user is admin or owns the object

        Args:
            request: The request object
            view: The view being accessed
            obj: The object being accessed

        Returns:
            True if user has permission
        """
        if not request.user or not request.user.is_authenticated:
            return False

        # Allow admins/superusers
        if getattr(request.user, "is_superuser", False):
            return True

        # Check ownership
        return super().has_object_permission(request, view, obj)
