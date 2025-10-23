"""
Exception classes for the Pagoda plugin system.

These exceptions provide a hierarchy for handling various error conditions
that can occur during plugin development and execution.
"""


class PagodaError(Exception):
    """Base exception for all Pagoda-related errors"""

    pass


class PluginError(PagodaError):
    """Base exception for plugin-related errors"""

    pass


class PluginLoadError(PluginError):
    """Exception raised when plugin loading fails"""

    pass


class PluginValidationError(PluginError):
    """Exception raised when plugin validation fails"""

    pass


class PluginSecurityError(PluginError):
    """Exception raised when plugin security constraints are violated"""

    pass


class InterfaceError(PagodaError):
    """Exception raised when interface implementation issues occur"""

    pass


class AuthenticationError(PagodaError):
    """Exception raised when authentication fails"""

    pass


class AuthorizationError(PagodaError):
    """Exception raised when authorization fails"""

    pass


class DataAccessError(PagodaError):
    """Exception raised when data access operations fail"""

    pass


class HookExecutionError(PagodaError):
    """Exception raised when hook execution fails"""

    pass
