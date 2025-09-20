import logging
from importlib import import_module
from pathlib import Path

from .registry import plugin_registry

logger = logging.getLogger(__name__)


def discover_plugins():
    """Auto-discover installed plugins

    This function detects plugins using the following methods:
    1. Detection of external plugins from entry points
    2. Detection of sample plugins from plugin_samples directory
    """
    logger.info("Starting plugin discovery...")

    # 外部パッケージからプラグインを発見
    discover_external_plugins()

    # サンプルプラグインを発見
    discover_sample_plugins()

    discovered_plugins = plugin_registry.get_all_plugins()
    logger.info(f"Plugin discovery completed. Found {len(discovered_plugins)} plugins.")


def discover_external_plugins():
    """Discover plugins from external packages

    Uses the 'airone.plugins' group in entry points to discover
    plugins installed as external packages.
    """
    try:
        # Import pkg_resources (planned migration to importlib.metadata in the future)
        import pkg_resources

        for entry_point in pkg_resources.iter_entry_points("airone.plugins"):
            try:
                plugin_class = entry_point.load()
                plugin_registry.register(plugin_class)
                logger.info(f"Loaded external plugin: {entry_point.name}")
            except Exception as e:
                logger.error(f"Failed to load external plugin {entry_point.name}: {e}")

    except ImportError:
        # If pkg_resources is not available
        logger.debug("pkg_resources not available, skipping external plugin discovery")


def discover_sample_plugins():
    """Discover sample plugins

    Discover and register sample plugins from the plugin_examples directory.
    Sample plugins are used for development and testing purposes.
    """
    # Identify project root directory
    base_dir = Path(__file__).parent.parent.parent  # airone/airone/plugins -> airone/
    examples_dir = base_dir / "plugin_examples"

    if not examples_dir.exists():
        logger.debug(f"Plugin examples directory not found: {examples_dir}")
        return

    logger.debug(f"Discovering sample plugins in: {examples_dir}")

    for plugin_dir in examples_dir.iterdir():
        if plugin_dir.is_dir() and not plugin_dir.name.startswith("."):
            try:
                load_example_plugin(plugin_dir)
            except Exception as e:
                logger.error(f"Failed to load example plugin {plugin_dir.name}: {e}")


def load_example_plugin(plugin_dir: Path):
    """Load an example plugin

    Args:
        plugin_dir: Path to the plugin directory
    """
    plugin_name = plugin_dir.name

    # For plugin_examples structure: airone-hello-world-plugin/airone_hello_world_plugin/plugin.py
    # Convert plugin directory name to module name
    module_dir_name = plugin_name.replace("-", "_")
    plugin_module_path = plugin_dir / module_dir_name / "plugin.py"

    if not plugin_module_path.exists():
        logger.warning(f"Plugin module not found: {plugin_module_path}")
        return

    # Add plugin directory to path temporarily
    import sys

    plugin_path = str(plugin_dir)
    path_added = False
    if plugin_path not in sys.path:
        sys.path.insert(0, plugin_path)
        path_added = True

    try:
        # Import plugin module
        # e.g., airone_hello_world_plugin.plugin
        module_name = f"{module_dir_name}.plugin"
        plugin_module = import_module(module_name)

        # Find plugin class
        for attr_name in dir(plugin_module):
            attr = getattr(plugin_module, attr_name)
            if (
                isinstance(attr, type)
                and hasattr(attr, "id")
                and attr_name.endswith("Plugin")
                and attr_name != "Plugin"
            ):  # Exclude base class
                plugin_registry.register(attr)
                logger.info(f"Loaded example plugin: {plugin_name}")
                return

        logger.warning(f"No plugin class found in {module_name}")

    except ImportError as e:
        logger.error(f"Failed to import example plugin module {module_name}: {e}")
    except Exception as e:
        logger.error(f"Error loading example plugin {plugin_name}: {e}")
    finally:
        # Remove from path if we added it
        if path_added and plugin_path in sys.path:
            sys.path.remove(plugin_path)


def ensure_plugin_examples_in_path():
    """Add plugin_examples directory to Python path

    Add the plugin_examples directory to sys.path to enable
    importing of example plugins.
    """
    import sys

    base_dir = Path(__file__).parent.parent.parent
    examples_dir = str(base_dir / "plugin_examples")

    if examples_dir not in sys.path:
        sys.path.insert(0, examples_dir)
        logger.debug(f"Added to Python path: {examples_dir}")


# Set path on module load
ensure_plugin_examples_in_path()
