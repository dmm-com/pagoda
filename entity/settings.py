from airone.lib.settings import Settings

CONFIG = Settings(
    {
        "DASHBOARD_NUM_ITEMS": 7,
        "MAX_LIST_ENTITIES": 30,
        # An import preview runs synchronously, so it must stay short enough not to
        # occupy a request worker for long. Larger files can still be imported; the
        # user just has to skip the preview.
        "MAX_IMPORT_PREVIEW_ROWS": 2000,
    }
)
