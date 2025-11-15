"""
Serializer mixins and base classes for plugin development.

These serializers provide common functionality and patterns for
plugin API endpoints, including validation, field handling,
and integration with host application data models.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, cast

from rest_framework import serializers
from rest_framework.serializers import ModelSerializer, Serializer

logger = logging.getLogger(__name__)


class PluginSerializerMixin:
    """Base mixin for plugin serializers

    Provides common functionality for plugin serializers including:
    - Plugin context integration
    - Standardized validation patterns
    - Error handling enhancements
    - Metadata injection

    Usage:
        class MyModelSerializer(PluginSerializerMixin, ModelSerializer):
            plugin_id = "my-plugin"

            class Meta:
                model = MyModel
                fields = '__all__'
    """

    plugin_id: Optional[str] = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._setup_plugin_context()

    def _setup_plugin_context(self):
        """Setup plugin context for the serializer"""
        # Get plugin context from request if available
        request = getattr(self, "context", {}).get("request")  # type: ignore[attr-defined]
        if request and hasattr(request, "plugin_context"):
            self.plugin_context = request.plugin_context
        else:
            self.plugin_context = self._get_default_plugin_context()

    def _get_default_plugin_context(self) -> Dict[str, Any]:
        """Get default plugin context

        Returns:
            Default plugin context dictionary
        """
        return {
            "plugin_id": self.plugin_id or "unknown",
            "serializer_class": self.__class__.__name__,
        }

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced validation with plugin context

        Args:
            attrs: Attributes to validate

        Returns:
            Validated attributes

        Raises:
            ValidationError: If validation fails
        """
        attrs = super().validate(attrs)  # type: ignore[misc]

        # Add plugin-specific validation
        attrs = self.validate_plugin_data(attrs)

        # Log validation success for monitoring
        plugin_id = self.plugin_context.get("plugin_id", "unknown")
        logger.debug(f"Plugin {plugin_id} serializer validation successful")

        return attrs

    def validate_plugin_data(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        """Plugin-specific validation logic

        Override this method to add custom validation logic
        specific to your plugin.

        Args:
            attrs: Attributes to validate

        Returns:
            Validated attributes

        Raises:
            ValidationError: If validation fails
        """
        # Default implementation does nothing
        return attrs

    def to_representation(self, instance: Any) -> Dict[str, Any]:
        """Convert model instance to representation with plugin metadata

        Args:
            instance: Model instance to serialize

        Returns:
            Serialized representation
        """
        data = super().to_representation(instance)  # type: ignore[misc]

        # Add plugin metadata if requested
        if self._should_include_plugin_metadata():
            data["_plugin_meta"] = {
                "plugin_id": self.plugin_context.get("plugin_id"),
                "serializer": self.__class__.__name__,
            }

        return cast(Dict[str, Any], data)

    def _should_include_plugin_metadata(self) -> bool:
        """Check if plugin metadata should be included

        Returns:
            True if metadata should be included
        """
        request = getattr(self, "context", {}).get("request")  # type: ignore[attr-defined]
        if request:
            return request.GET.get("include_plugin_meta", "").lower() in ("true", "1", "yes")
        return False

    def create(self, validated_data: Dict[str, Any]) -> Any:
        """Create instance with plugin context

        Args:
            validated_data: Validated data for creation

        Returns:
            Created instance
        """
        # Add plugin context to creation if supported by model
        meta = getattr(self, "Meta", None)  # type: ignore[attr-defined]
        if meta and hasattr(meta.model, "created_by_plugin"):
            validated_data["created_by_plugin"] = self.plugin_context.get("plugin_id")

        # Log creation for monitoring
        plugin_id = self.plugin_context.get("plugin_id", "unknown")
        model_name = meta.model.__name__ if meta else "Unknown"
        logger.info(f"Plugin {plugin_id} creating new {model_name}")

        return super().create(validated_data)  # type: ignore[misc]

    def update(self, instance: Any, validated_data: Dict[str, Any]) -> Any:
        """Update instance with plugin context

        Args:
            instance: Instance to update
            validated_data: Validated data for update

        Returns:
            Updated instance
        """
        # Add plugin context to update if supported by model
        if hasattr(instance, "updated_by_plugin"):
            validated_data["updated_by_plugin"] = self.plugin_context.get("plugin_id")

        # Log update for monitoring
        plugin_id = self.plugin_context.get("plugin_id", "unknown")
        logger.info(f"Plugin {plugin_id} updating {instance.__class__.__name__} {instance.pk}")

        return super().update(instance, validated_data)  # type: ignore[misc]


class PluginModelSerializer(PluginSerializerMixin, ModelSerializer):
    """Base model serializer for plugins

    Combines PluginSerializerMixin with ModelSerializer to provide
    a complete base class for plugin model serializers.

    Usage:
        class MyModelSerializer(PluginModelSerializer):
            plugin_id = "my-plugin"

            class Meta:
                model = MyModel
                fields = ['id', 'name', 'description']
    """

    def get_field_names(self, declared_fields, info):
        """Get field names with plugin-specific filtering

        Args:
            declared_fields: Declared fields
            info: Model info

        Returns:
            List of field names
        """
        field_names = super().get_field_names(declared_fields, info)

        # Apply plugin-specific field filtering
        return self.filter_fields_for_plugin(field_names)

    def filter_fields_for_plugin(self, field_names: List[str]) -> List[str]:
        """Filter fields based on plugin configuration

        Override this method to customize which fields are exposed
        by your plugin's serializers.

        Args:
            field_names: Original field names

        Returns:
            Filtered field names
        """
        # Default implementation returns all fields
        return field_names


class PluginValidationMixin:
    """Validation mixin for plugin serializers

    Provides additional validation utilities commonly needed
    by plugin serializers.

    Usage:
        class MySerializer(PluginValidationMixin, PluginModelSerializer):
            def validate_custom_field(self, value):
                return self.validate_not_empty(value, "Custom field")
    """

    def validate_not_empty(self, value: Any, field_name: str) -> Any:
        """Validate that a field is not empty

        Args:
            value: Field value to validate
            field_name: Name of the field for error messages

        Returns:
            Validated value

        Raises:
            ValidationError: If value is empty
        """
        if not value or (isinstance(value, str) and not value.strip()):
            raise serializers.ValidationError(f"{field_name} cannot be empty")
        return value

    def validate_string_length(
        self, value: str, field_name: str, min_length: int = 1, max_length: int = 255
    ) -> str:
        """Validate string length

        Args:
            value: String value to validate
            field_name: Name of the field for error messages
            min_length: Minimum allowed length
            max_length: Maximum allowed length

        Returns:
            Validated string

        Raises:
            ValidationError: If length is invalid
        """
        if not isinstance(value, str):
            raise serializers.ValidationError(f"{field_name} must be a string")

        if len(value) < min_length:
            raise serializers.ValidationError(
                f"{field_name} must be at least {min_length} characters long"
            )

        if len(value) > max_length:
            raise serializers.ValidationError(
                f"{field_name} must be no more than {max_length} characters long"
            )

        return value

    def validate_unique_in_plugin(self, value: Any, field_name: str, queryset) -> Any:
        """Validate that a value is unique within plugin scope

        Args:
            value: Value to check for uniqueness
            field_name: Name of the field for error messages
            queryset: Queryset to check against

        Returns:
            Validated value

        Raises:
            ValidationError: If value is not unique
        """
        # Filter queryset by plugin if supported
        plugin_id = getattr(self, "plugin_context", {}).get("plugin_id")
        if plugin_id and hasattr(queryset.model, "created_by_plugin"):
            queryset = queryset.filter(created_by_plugin=plugin_id)

        # Check for existing instance (exclude current instance in updates)
        if hasattr(self, "instance") and self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.filter(**{field_name: value}).exists():
            raise serializers.ValidationError(
                f"{field_name} '{value}' already exists in this plugin"
            )

        return value


class PluginListSerializer(PluginSerializerMixin, Serializer):
    """Base list serializer for plugin endpoints

    Provides common functionality for list-based plugin endpoints
    that don't correspond to a specific model.

    Usage:
        class MyListSerializer(PluginListSerializer):
            items = PluginModelSerializer(many=True)
            total_count = serializers.IntegerField()
    """

    def to_representation(self, data):
        """Convert list data to representation

        Args:
            data: List data to serialize

        Returns:
            Serialized representation
        """
        if isinstance(data, dict):
            # If data is already a dict, use parent implementation
            return super().to_representation(data)

        # If data is a list or queryset, wrap it in a standard format
        return {
            "items": data,
            "count": len(data) if hasattr(data, "__len__") else None,
            "plugin_id": self.plugin_context.get("plugin_id"),
        }


class PluginErrorSerializer(Serializer):
    """Standardized error response serializer for plugins

    Provides consistent error response format across all plugins.

    Usage:
        # In exception handlers or error responses
        error_data = {
            'error_code': 'PLUGIN_VALIDATION_ERROR',
            'message': 'Validation failed',
            'details': {'field': ['This field is required']}
        }
        serializer = PluginErrorSerializer(data=error_data)
        return Response(serializer.data, status=400)
    """

    error_code = serializers.CharField(max_length=100)
    message = serializers.CharField()
    details = serializers.DictField(required=False)
    plugin_id = serializers.CharField(max_length=100, required=False)
    timestamp = serializers.DateTimeField(required=False)

    def to_representation(self, instance):
        """Convert error data to representation

        Args:
            instance: Error data instance

        Returns:
            Standardized error representation
        """
        data = super().to_representation(instance)

        # Add timestamp if not provided
        if "timestamp" not in data or not data["timestamp"]:
            data["timestamp"] = datetime.now().isoformat()

        return data
