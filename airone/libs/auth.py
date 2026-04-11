"""
AirOne Authentication Utilities for Plugins

Provides authentication and user management utilities for external plugins.
"""

from typing import Any, Dict

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractBaseUser, AnonymousUser

User = get_user_model()


def get_current_user_info(user: AbstractBaseUser | AnonymousUser) -> Dict[str, Any]:
    """Get current user information

    Provides safe access to user information for plugins.

    Args:
        user: Django User instance from request

    Returns:
        Dictionary containing user information
    """
    if not user or not user.is_authenticated:
        return {
            "username": "anonymous",
            "is_authenticated": False,
            "is_staff": False,
            "is_superuser": False,
        }

    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "is_authenticated": True,
        "is_staff": user.is_staff,
        "is_superuser": user.is_superuser,
        "date_joined": user.date_joined.isoformat() if user.date_joined else None,
        "last_login": user.last_login.isoformat() if user.last_login else None,
    }


def check_user_permission(user: AbstractBaseUser | AnonymousUser, permission: str) -> bool:
    """Check if user has specific permission

    Args:
        user: Django User instance
        permission: Permission string to check

    Returns:
        True if user has permission, False otherwise
    """
    if not user or not user.is_authenticated:
        return False

    return user.has_perm(permission)


def get_user_groups(user: AbstractBaseUser | AnonymousUser) -> list[str]:
    """Get user's group names

    Args:
        user: Django User instance

    Returns:
        List of group names the user belongs to
    """
    if not user or not user.is_authenticated:
        return []

    return list(user.groups.values_list("name", flat=True))
