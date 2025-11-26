from copy import deepcopy

from airone.settings_common import Common


class Dev(Common):
    DEBUG = True


class Prd(Common):
    pass


class DRFSpectacularExcludeCustomView(Common):
    SPECTACULAR_SETTINGS = deepcopy(Common.SPECTACULAR_SETTINGS)
    SPECTACULAR_SETTINGS["PREPROCESSING_HOOKS"].append("airone.spectacular.exclude_customview_hook")  # type: ignore
