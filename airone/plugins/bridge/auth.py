"""
AirOne Authentication Bridge

Implements pagoda_core.interfaces.AuthInterface with AirOne-specific logic.
"""

import logging
from typing import Any, Dict, List, Optional

from django.contrib.auth import get_user_model
from pagoda_plugin_sdk.interfaces import AuthInterface

User = get_user_model()
logger = logging.getLogger(__name__)


class AirOneAuthBridge(AuthInterface):
    """AirOne-specific implementation of AuthInterface

    This bridge connects pagoda-core's authentication interface to AirOne's
    user management system, providing plugins with access to AirOne's
    authentication and authorization functionality.
    """

    def get_current_user_info(self, request) -> Dict[str, Any]:
        """Get current user information from AirOne request

        Args:
            request: Django HTTP request object

        Returns:
            Dictionary containing user information
        """
        user = getattr(request, "user", None)

        if not user or not user.is_authenticated:
            return {
                "username": "anonymous",
                "is_authenticated": False,
                "is_staff": False,
                "is_superuser": False,
            }

        try:
            return {
                "id": user.id,
                "username": user.username,
                "email": getattr(user, "email", ""),
                "first_name": getattr(user, "first_name", ""),
                "last_name": getattr(user, "last_name", ""),
                "is_authenticated": True,
                "is_staff": user.is_staff,
                "is_superuser": user.is_superuser,
                "date_joined": user.date_joined.isoformat()
                if hasattr(user, "date_joined") and user.date_joined
                else None,
                "last_login": user.last_login.isoformat()
                if hasattr(user, "last_login") and user.last_login
                else None,
                "groups": list(user.groups.values_list("name", flat=True))
                if hasattr(user, "groups")
                else [],
            }
        except Exception as e:
            logger.error(f"Error getting user info: {e}")
            return {
                "username": str(user),
                "is_authenticated": True,
                "is_staff": False,
                "is_superuser": False,
            }

    def check_user_permission(self, user, permission: str) -> bool:
        """Check if user has specific permission in AirOne

        Args:
            user: User object or user identifier
            permission: Permission string to check

        Returns:
            True if user has permission, False otherwise
        """
        if not user:
            return False

        try:
            if hasattr(user, "has_perm"):
                return bool(user.has_perm(permission))

            # Handle user ID case
            if isinstance(user, (int, str)):
                try:
                    user_obj = User.objects.get(id=user)
                    return bool(user_obj.has_perm(permission))
                except User.DoesNotExist:
                    return False

            return False
        except Exception as e:
            logger.error(f"Error checking user permission: {e}")
            return False

    def get_user_groups(self, user) -> List[str]:
        """Get user's group names in AirOne

        Args:
            user: User object or user identifier

        Returns:
            List of group names the user belongs to
        """
        if not user:
            return []

        try:
            if hasattr(user, "groups"):
                return list(user.groups.values_list("name", flat=True))

            # Handle user ID case
            if isinstance(user, (int, str)):
                try:
                    user_obj = User.objects.get(id=user)
                    return list(user_obj.groups.values_list("name", flat=True))
                except User.DoesNotExist:
                    return []

            return []
        except Exception as e:
            logger.error(f"Error getting user groups: {e}")
            return []

    def authenticate_token(self, token: str) -> Optional[Any]:
        """Authenticate user by token in AirOne

        Args:
            token: Authentication token

        Returns:
            User object if token is valid, None otherwise
        """
        if not token:
            return None

        try:
            # Try to use Django REST Framework token authentication
            from rest_framework.authtoken.models import Token

            try:
                token_obj = Token.objects.get(key=token)
                return token_obj.user
            except Token.DoesNotExist:
                pass

            # Add other token authentication methods here if needed
            # (JWT, custom tokens, etc.)

            return None
        except ImportError:
            # DRF token authentication not available
            logger.debug("DRF token authentication not available")
            return None
        except Exception as e:
            logger.error(f"Error authenticating token: {e}")
            return None

    def has_object_permission(self, user, obj, permission: str) -> bool:
        """Check if user has permission on specific object in AirOne

        Args:
            user: User object or user identifier
            obj: Object to check permission on
            permission: Permission string to check

        Returns:
            True if user has permission, False otherwise
        """
        if not user or not obj:
            return False

        try:
            # AirOne-specific object-level permission logic
            # This would integrate with AirOne's ACL system

            # For now, just check if user is staff/superuser for object access
            if hasattr(user, "is_superuser") and user.is_superuser:
                return True

            if hasattr(user, "is_staff") and user.is_staff:
                return True

            # Add AirOne-specific ACL logic here
            # e.g., check entry ownership, entity permissions, etc.

            return False
        except Exception as e:
            logger.error(f"Error checking object permission: {e}")
            return False

    def get_user_roles(self, user) -> List[str]:
        """Get user's role names in AirOne

        Args:
            user: User object or user identifier

        Returns:
            List of role names the user has
        """
        try:
            # AirOne might have a role system
            # For now, return basic roles based on Django user flags
            roles = []

            if hasattr(user, "is_superuser") and user.is_superuser:
                roles.append("superuser")
            elif hasattr(user, "is_staff") and user.is_staff:
                roles.append("staff")
            else:
                roles.append("user")

            # Add AirOne-specific role logic here if available

            return roles
        except Exception as e:
            logger.error(f"Error getting user roles: {e}")
            return []
