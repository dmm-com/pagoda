import logging

from django.conf import settings

from .registry import plugin_registry

logger = logging.getLogger(__name__)


def discover_plugins():
    """Auto-discover installed plugins

    Detects plugins from external packages using entry points.
    """
    logger.info("Starting plugin discovery...")

    # 外部パッケージからプラグインを発見
    discover_external_plugins()

    discovered_plugins = plugin_registry.get_all_plugins()
    logger.info(f"Plugin discovery completed. Found {len(discovered_plugins)} plugins.")


def discover_external_plugins():
    """Discover plugins from external packages

    Uses the 'airone.plugins' group in entry points to discover
    plugins installed as external packages. Only loads plugins
    specified in ENABLED_PLUGINS setting.
    """
    try:
        # Import pkg_resources (planned migration to importlib.metadata in the future)
        import pkg_resources

        enabled_plugins = getattr(settings, "ENABLED_PLUGINS", [])
        if not enabled_plugins:
            logger.info("No plugins specified in ENABLED_PLUGINS, skipping plugin discovery")
            return

        for entry_point in pkg_resources.iter_entry_points("pagoda.plugins"):
            if entry_point.name in enabled_plugins:
                try:
                    plugin_class = entry_point.load()
                    plugin_registry.register(plugin_class)
                    logger.info(f"Loaded external plugin: {entry_point.name}")
                except Exception as e:
                    logger.error(f"Failed to load external plugin {entry_point.name}: {e}")
            else:
                logger.debug(f"Skipping plugin {entry_point.name} (not in enabled list)")

    except ImportError:
        # If pkg_resources is not available
        logger.debug("pkg_resources not available, skipping external plugin discovery")
