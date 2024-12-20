from src.core.constants import SPECIAL_KEYS

def is_special_key(key:str) -> bool:
    """
    Returns ``True`` if the key is special.
    :param key: The string representing the keyboard key.
    :return:
    """
    return key in SPECIAL_KEYS

def get_actual_key(key:str) -> str:
    """
    Returns the actual key that the special keyboard key represents.

    Raises a ``ValueError`` if the key doesn't match a special keyboard key.
    :param key: The string representing the keyboard key.
    :raise ValueError:
    :return:
    """
    if key not in SPECIAL_KEYS:
        message = "The key: " + key, " is not a special key or is not registered as it."
        raise ValueError(message)
    return SPECIAL_KEYS[key]


def get_special_key(key:str) -> str:
    """
    Returns the special key of the current key.
    Raises a ``ValueError`` if the key doesn't match a special keyboard key.
    :param key: The string representing the keyboard key.
    :raise ValueError:
    :return:
    """
    if key not in SPECIAL_KEYS.values():
        message = "The key: " + key, " doesn't contain a special key."
        raise ValueError(message)

    special_key_values = list(SPECIAL_KEYS.values())
    special_key_keys = list(SPECIAL_KEYS.keys())
    return special_key_keys[special_key_values.index(key)]
