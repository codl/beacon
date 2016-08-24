import random

def genid(length = 8):
    """
    Generates a random unique ID of specified length

    >>> import random
    >>> random.seed(0)
    >>> genid()
    'UoNWq.fw'
    >>> genid(16)
    'vpYQTiumBXYcw7h7'
    """
    ALLOWED_CHARS="-_.23456789abcdefghijkmnopqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ"
    return ''.join([random.choice(ALLOWED_CHARS) for _ in range(length)])
