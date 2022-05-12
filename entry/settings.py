from airone.lib.settings import Settings

CONFIG = Settings(
    {
        "MAX_LIST_ENTRIES": 100,
        "MAX_LIST_REFERRALS": 50,
        "TEMPLATE_CONFIG": {
            "MAX_LABEL_STRING": 45,
        },
        "MAX_HISTORY_COUNT": 10,
        "MAX_QUERY_SIZE": 249,  # '.*' + '[aA]'*249 + '.*' = 1000
        "EMPTY_SEARCH_CHARACTER": "\\",
        "EMPTY_SEARCH_CHARACTER_CODE": chr(165),
        "AND_SEARCH_CHARACTER": "&",
        "OR_SEARCH_CHARACTER": "|",
        "ESCAPE_CHARACTERS": [
            "(",
            ")",
            "<",
            '"',
            "{",
            "[",
            "#",
            "~",
            "@",
            "+",
            "*",
            ".",
            "?",
        ],
        "ESCAPE_CHARACTERS_REFERRALS_ENTRY": [
            "$",
            "(",
            "^",
            "|",
            "[",
            "+",
            "*",
            ".",
            "?",
            "\\",
        ],
        "ESCAPE_CHARACTERS_ENTRY_LIST": [
            "$",
            "(",
            "^",
            "\\",
            "|",
            "[",
            "+",
            "*",
            ".",
            "?",
        ],
        "TIME_FORMAT": "%Y-%m-%dT%H:%M:%S",
    }
)
