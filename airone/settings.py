from copy import deepcopy

from airone.settings_common import Common


class Dev(Common):
    pass


class Prd(Common):
    pass


class DRFSpectacularCustomView(Common):
    SPECTACULAR_SETTINGS = deepcopy(Common.SPECTACULAR_SETTINGS)
    SPECTACULAR_SETTINGS["PREPROCESSING_HOOKS"].remove("airone.spectacular.exclude_customview_hook")
