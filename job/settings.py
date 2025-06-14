from typing import Any

from airone.lib.settings import Settings

CONFIG: Any = Settings(
    {
        "MAX_LIST_VIEW": 50,
        "MAX_LIST_NAV": 10,
        "RECENT_SECONDS": 3600,
        "RESCHEDULING_DELAY_SECONDS": 1,
    }
)
