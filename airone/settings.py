from copy import deepcopy

from airone.settings_common import Common


class Dev(Common):
    DEBUG = True

    # Local development convenience: derive externally-visible link hosts from
    # the request when ALLOWED_HOSTS has no concrete hostname. Never enable
    # this in production (reset-link poisoning, CWE-640).
    CANONICAL_URL_FALLBACK = True


class Prd(Common):
    pass


class DRFSpectacularExcludeCustomView(Common):
    SPECTACULAR_SETTINGS = deepcopy(Common.SPECTACULAR_SETTINGS)
    SPECTACULAR_SETTINGS["PREPROCESSING_HOOKS"].append("airone.spectacular.exclude_customview_hook")
