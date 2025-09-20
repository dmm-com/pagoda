"""
Authentication and Authorization Interface.

This interface defines how plugins can interact with the host application's
authentication and authorization system.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class AuthInterface(ABC):
    """Interface for authentication and authorization services

    Host applications must implement this interface to provide authentication
    and authorization services to plugins.
    """

    @abstractmethod
    def get_current_user_info(self, request) -> Dict[str, Any]:
        """Get current user information from request

        Args:
            request: HTTP request object

        Returns:
            Dictionary containing user information with at least:
            - username: str
            - is_authenticated: bool
            - is_staff: bool (optional)
            - is_superuser: bool (optional)
            - email: str (optional)
            - groups: List[str] (optional)

        Example:
            {
                "id": 123,
                "username": "john_doe",
                "email": "john@example.com",
                "is_authenticated": True,
                "is_staff": False,
                "is_superuser": False,
                "groups": ["editors", "reviewers"]
            }
        """
        pass

    @abstractmethod
    def check_user_permission(self, user, permission: str) -> bool:
        """Check if user has specific permission

        Args:
            user: User object or user identifier
            permission: Permission string to check

        Returns:
            True if user has permission, False otherwise
        """
        pass

    @abstractmethod
    def get_user_groups(self, user) -> List[str]:
        """Get user's group names

        Args:
            user: User object or user identifier

        Returns:
            List of group names the user belongs to
        """
        pass

    @abstractmethod
    def authenticate_token(self, token: str) -> Optional[Any]:
        """Authenticate user by token

        Args:
            token: Authentication token

        Returns:
            User object if token is valid, None otherwise
        """
        pass

    def has_object_permission(self, user, obj, permission: str) -> bool:
        """Check if user has permission on specific object

        Args:
            user: User object or user identifier
            obj: Object to check permission on
            permission: Permission string to check

        Returns:
            True if user has permission, False otherwise

        Note:
            Default implementation returns False.
            Host applications should override this for object-level permissions.
        """
        return False

    def get_user_roles(self, user) -> List[str]:
        """Get user's role names

        Args:
            user: User object or user identifier

        Returns:
            List of role names the user has

        Note:
            Default implementation returns empty list.
            Host applications can override this if they have role systems.
        """
        return []
