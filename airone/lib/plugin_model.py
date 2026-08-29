from dataclasses import dataclass

from django.conf import settings
from pagoda_plugin_sdk.models import PluginSchema


@dataclass
class PluginSchemaConfig:
    """Data class for managing plugin model structure configuration"""

    plugin_id: str
    schema: dict[str, PluginSchema]

    # This reserved models has expected model name for each Plugins
    # (This is seems to be AdaptedEntity of obsoleted CustomView)
    # schema = None

    reserved_models = []


#    reserved_models = [
#        {"name": "データセンタ"},
#        {"name": "フロア"},
#        {"name": "ラック"},
#        {"name": "アプライアンス"},
#    ]


class PluginSchemaRegistry:
    # This allows user to modify Model names that are registered at PluginSchemaConfig
    _custom_modelname_aliases: dict[str, list[tuple[str, list[str]]]] = {}

    def registry(cls):
        config = getattr(settings, "PLUGIN_MODEL_ALIASES", {})
