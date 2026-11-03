from copy import deepcopy

from airone.settings_common import LITE, Common, ensure_secure_secret_key


class Dev(Common):
    DEBUG = True


class Prd(Common):
    @classmethod
    def setup(cls) -> None:
        super().setup()
        # A public or missing signing key makes every value Django signs
        # forgeable, so production fails fast instead of booting with one.
        # Dev, tests and lite mode keep the local fallback for convenience.
        if not LITE:
            ensure_secure_secret_key(cls.SECRET_KEY)


class DRFSpectacularExcludeCustomView(Common):
    SPECTACULAR_SETTINGS = deepcopy(Common.SPECTACULAR_SETTINGS)
    SPECTACULAR_SETTINGS["PREPROCESSING_HOOKS"].append("airone.spectacular.exclude_customview_hook")
